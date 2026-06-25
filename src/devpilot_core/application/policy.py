from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest

from .dtos import ApplicationRequest
from .operation_catalog import ApplicationOperationCatalogBuilder

POST_H_007_D_CREATED_BY = "POST-H-007-D"
APPLICATION_BOUNDARY_POLICY_REPORT_ID = "devpilot-application-boundary-policy"


class InterfaceClient(str, Enum):
    """Known ApplicationService boundary clients.

    Unknown local/testing clients are deliberately treated as `internal` for
    backward compatibility, while public clients (`api` and `ui`) remain strict.
    """

    CLI = "cli"
    API = "api"
    UI = "ui"
    AUTOMATION = "automation"
    INTERNAL = "internal"


PUBLIC_INTERFACE_CLIENTS = {InterfaceClient.API.value, InterfaceClient.UI.value}
INTERNAL_COMPATIBLE_CLIENTS = {InterfaceClient.CLI.value, InterfaceClient.INTERNAL.value}


@dataclass(frozen=True)
class ApplicationBoundaryPolicyRule:
    """Declarative per-operation guardrail used before ApplicationService dispatch."""

    operation_id: str
    allowed_clients: tuple[str, ...]
    policy_required: bool
    dry_run_default: bool
    writes_files: bool
    risk_level: str
    exposed_to: tuple[str, ...] = field(default_factory=tuple)
    source: str = "application-operation-catalog"
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def sensitive(self) -> bool:
        return self.policy_required or self.writes_files or self.risk_level in {"high", "critical"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "allowed_clients": list(self.allowed_clients),
            "policy_required": self.policy_required,
            "dry_run_default": self.dry_run_default,
            "writes_files": self.writes_files,
            "risk_level": self.risk_level,
            "sensitive": self.sensitive,
            "exposed_to": list(self.exposed_to),
            "source": self.source,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ApplicationBoundaryPolicyDecision:
    """Result of evaluating an ApplicationRequest against interface guardrails."""

    allowed: bool
    client: str
    normalized_client: str
    operation_id: str
    rule: ApplicationBoundaryPolicyRule | None
    policy_checked: bool = False
    policy_result: CommandResult | None = None
    findings: tuple[Finding, ...] = field(default_factory=tuple)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "client": self.client,
            "normalized_client": self.normalized_client,
            "operation_id": self.operation_id,
            "policy_checked": self.policy_checked,
            "reason": self.reason,
            "rule": self.rule.to_dict() if self.rule else None,
            "policy_result": self.policy_result.to_dict() if self.policy_result else None,
            "findings": [finding.to_dict() for finding in self.findings],
        }

    def to_command_result(self) -> CommandResult:
        return CommandResult(
            command="application boundary policy",
            ok=self.allowed,
            exit_code=ExitCode.PASS if self.allowed else ExitCode.BLOCK,
            message="Application boundary policy allowed the request." if self.allowed else "Application boundary policy blocked the request.",
            data={
                "summary": {
                    "operation": self.operation_id,
                    "client": self.client,
                    "normalized_client": self.normalized_client,
                    "allowed": self.allowed,
                    "policy_checked": self.policy_checked,
                    "reason": self.reason,
                    "dry_run_guardrail_applied": any(finding.id == "APPLICATION_BOUNDARY_DRY_RUN_REQUIRED" for finding in self.findings),
                    "interface_guardrail_applied": any(finding.id == "APPLICATION_BOUNDARY_OPERATION_NOT_ALLOWED" for finding in self.findings),
                    "preliminary": True,
                },
                "decision": self.to_dict(),
            },
            findings=list(self.findings),
        )


class ApplicationBoundaryPolicy:
    """Interface-level ApplicationService guardrails for POST-H-007-D.

    The policy is intentionally local and deterministic. It does not replace
    the domain PolicyEngine; it decides whether a client may invoke an
    ApplicationService operation and invokes PolicyEngine for sensitive
    operations before the domain handler runs.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self._rules: dict[str, ApplicationBoundaryPolicyRule] | None = None

    def evaluate(self, request: ApplicationRequest) -> ApplicationBoundaryPolicyDecision:
        operation_id = request.operation.strip()
        client = str(request.client or "cli").strip().lower() or "cli"
        normalized_client = normalize_interface_client(client)
        rules = self.rules()
        rule = rules.get(operation_id)

        if rule is None:
            finding = Finding(
                id="APPLICATION_BOUNDARY_OPERATION_UNDECLARED",
                message="Application operation is not declared in the boundary policy catalog.",
                severity=Severity.BLOCK,
                metadata={"operation": operation_id, "client": client, "normalized_client": normalized_client},
            )
            return ApplicationBoundaryPolicyDecision(
                allowed=False,
                client=client,
                normalized_client=normalized_client,
                operation_id=operation_id,
                rule=None,
                findings=(finding,),
                reason="operation-undeclared",
            )

        findings: list[Finding] = []
        if normalized_client not in rule.allowed_clients:
            findings.append(
                Finding(
                    id="APPLICATION_BOUNDARY_OPERATION_NOT_ALLOWED",
                    message="Application operation is not exposed to this interface client.",
                    severity=Severity.BLOCK,
                    metadata={
                        "operation": operation_id,
                        "client": client,
                        "normalized_client": normalized_client,
                        "allowed_clients": list(rule.allowed_clients),
                        "exposed_to": list(rule.exposed_to),
                    },
                )
            )
            return ApplicationBoundaryPolicyDecision(
                allowed=False,
                client=client,
                normalized_client=normalized_client,
                operation_id=operation_id,
                rule=rule,
                findings=tuple(findings),
                reason="client-not-allowed",
            )

        # Public interfaces must preserve dry-run for sensitive or write-like operations.
        if normalized_client in PUBLIC_INTERFACE_CLIENTS | {InterfaceClient.AUTOMATION.value} and rule.sensitive and not request.dry_run:
            findings.append(
                Finding(
                    id="APPLICATION_BOUNDARY_DRY_RUN_REQUIRED",
                    message="Sensitive ApplicationService operations require dry_run=true for public/automation clients.",
                    severity=Severity.BLOCK,
                    metadata={
                        "operation": operation_id,
                        "client": client,
                        "normalized_client": normalized_client,
                        "risk_level": rule.risk_level,
                        "writes_files": rule.writes_files,
                        "policy_required": rule.policy_required,
                    },
                )
            )
            return ApplicationBoundaryPolicyDecision(
                allowed=False,
                client=client,
                normalized_client=normalized_client,
                operation_id=operation_id,
                rule=rule,
                findings=tuple(findings),
                reason="dry-run-required",
            )

        policy_result: CommandResult | None = None
        policy_checked = False
        if rule.sensitive:
            policy_checked = True
            policy_result = self._policy_engine().evaluate(_policy_request_for_boundary(request, rule, normalized_client))
            if not policy_result.ok:
                findings.extend(policy_result.findings)
                findings.append(
                    Finding(
                        id="APPLICATION_BOUNDARY_POLICY_BLOCKED",
                        message="PolicyEngine blocked a sensitive ApplicationService boundary request.",
                        severity=Severity.BLOCK,
                        metadata={"operation": operation_id, "client": client, "normalized_client": normalized_client},
                    )
                )
                return ApplicationBoundaryPolicyDecision(
                    allowed=False,
                    client=client,
                    normalized_client=normalized_client,
                    operation_id=operation_id,
                    rule=rule,
                    policy_checked=True,
                    policy_result=policy_result,
                    findings=tuple(findings),
                    reason="policy-blocked",
                )

        findings.append(
            Finding(
                id="APPLICATION_BOUNDARY_POLICY_PASS",
                message="Application boundary guardrails allowed the request.",
                severity=Severity.INFO,
                metadata={
                    "operation": operation_id,
                    "client": client,
                    "normalized_client": normalized_client,
                    "policy_checked": policy_checked,
                    "sensitive": rule.sensitive,
                },
            )
        )
        return ApplicationBoundaryPolicyDecision(
            allowed=True,
            client=client,
            normalized_client=normalized_client,
            operation_id=operation_id,
            rule=rule,
            policy_checked=policy_checked,
            policy_result=policy_result,
            findings=tuple(findings),
            reason="allowed",
        )

    def rules(self) -> dict[str, ApplicationBoundaryPolicyRule]:
        if self._rules is None:
            self._rules = self._build_rules()
        return dict(self._rules)

    def report(self) -> dict[str, Any]:
        rules = self.rules()
        clients = [client.value for client in InterfaceClient]
        by_client = {client: sorted(rule.operation_id for rule in rules.values() if client in rule.allowed_clients) for client in clients}
        sensitive = [rule for rule in rules.values() if rule.sensitive]
        public_blocks = [rule.operation_id for rule in rules.values() if InterfaceClient.API.value not in rule.allowed_clients and InterfaceClient.UI.value not in rule.allowed_clients]
        return {
            "report_id": APPLICATION_BOUNDARY_POLICY_REPORT_ID,
            "created_by": POST_H_007_D_CREATED_BY,
            "status": "implemented-initial",
            "schema_version": "1.0",
            "summary": {
                "rules_total": len(rules),
                "clients_total": len(clients),
                "sensitive_operations_total": len(sensitive),
                "sensitive_without_policy_required_total": sum(1 for rule in sensitive if not rule.policy_required and rule.writes_files),
                "api_allowed_total": len(by_client[InterfaceClient.API.value]),
                "ui_allowed_total": len(by_client[InterfaceClient.UI.value]),
                "automation_allowed_total": len(by_client[InterfaceClient.AUTOMATION.value]),
                "publicly_unexposed_operations_total": len(public_blocks),
                "dry_run_default": True,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "preliminary": True,
            },
            "clients": clients,
            "allowed_by_client": by_client,
            "rules": [rule.to_dict() for rule in sorted(rules.values(), key=lambda item: item.operation_id)],
            "notes": [
                "API/UI clients are strict: operations must be explicitly mapped by ApplicationOperationCatalog evidence.",
                "Unknown local/testing clients are normalized to internal for backward compatibility only; they are not public clients.",
                "Sensitive operations invoke PolicyEngine before domain dispatch, using observability_enabled=false to avoid policy-check side effects.",
                "This POST-H-007-D implementation is an initial boundary policy; full CLI registry integration remains POST-H-007-E.",
            ],
        }

    def _build_rules(self) -> dict[str, ApplicationBoundaryPolicyRule]:
        catalog = ApplicationOperationCatalogBuilder(self.root).build_catalog().to_dict()
        rules: dict[str, ApplicationBoundaryPolicyRule] = {}
        for descriptor in catalog.get("operations", []):
            if not isinstance(descriptor, dict):
                continue
            operation_id = str(descriptor.get("operation_id") or "").strip()
            if not operation_id:
                continue
            exposed_to = tuple(sorted(str(item) for item in descriptor.get("exposed_to", []) if str(item).strip()))
            api_routes = descriptor.get("api_routes") if isinstance(descriptor.get("api_routes"), list) else []
            ui_surfaces = descriptor.get("ui_surfaces") if isinstance(descriptor.get("ui_surfaces"), list) else []
            allowed = {InterfaceClient.INTERNAL.value, InterfaceClient.CLI.value}
            if api_routes:
                allowed.add(InterfaceClient.API.value)
            if ui_surfaces:
                allowed.add(InterfaceClient.UI.value)
            writes_files = bool(descriptor.get("writes_files"))
            risk_level = str(descriptor.get("risk_level") or "low").lower()
            policy_required = bool(descriptor.get("policy_required"))
            if not writes_files and risk_level in {"low", "medium"} and not policy_required:
                allowed.add(InterfaceClient.AUTOMATION.value)
            rules[operation_id] = ApplicationBoundaryPolicyRule(
                operation_id=operation_id,
                allowed_clients=tuple(sorted(allowed)),
                policy_required=policy_required,
                dry_run_default=bool(descriptor.get("dry_run_default", True)),
                writes_files=writes_files,
                risk_level=risk_level,
                exposed_to=exposed_to,
                notes=tuple(str(note) for note in descriptor.get("notes", []) if str(note).strip())[:3],
            )
        return rules

    def _policy_engine(self) -> PolicyEngine:
        return PolicyEngine(self.root, observability_enabled=False)


def normalize_interface_client(client: str | InterfaceClient | None) -> str:
    raw = str(client.value if isinstance(client, InterfaceClient) else client or "cli").strip().lower()
    if raw in {item.value for item in InterfaceClient}:
        return raw
    if raw in {"web", "web-ui", "frontend", "browser"}:
        return InterfaceClient.UI.value
    if raw in {"rest", "http", "fastapi", "local-api"}:
        return InterfaceClient.API.value
    if raw in {"script", "scheduler", "ci", "batch"}:
        return InterfaceClient.AUTOMATION.value
    return InterfaceClient.INTERNAL.value


def application_boundary_policy_report(root: Path) -> dict[str, Any]:
    return ApplicationBoundaryPolicy(root).report()


def _policy_request_for_boundary(request: ApplicationRequest, rule: ApplicationBoundaryPolicyRule, normalized_client: str) -> PolicyRequest:
    payload = dict(request.payload or {})
    path = payload.get("target") or payload.get("path") or payload.get("report_id") or None
    if path and rule.operation_id.startswith("reports."):
        path = f"outputs/reports/{path}"
    action = "plan" if rule.writes_files or rule.operation_id.endswith(".plan") else "read"
    return PolicyRequest(
        action=action,
        path=str(path) if path else None,
        text=str(payload.get("text")) if payload.get("text") is not None else None,
        external_api=False,
        estimated_cost_usd=0.0,
        dry_run=True,
        tool_id=rule.operation_id.replace(".", "-"),
        subject=rule.operation_id,
        actor=str(payload.get("actor") or f"{normalized_client}-local"),
        metadata={
            "component": "ApplicationBoundaryPolicy",
            "created_by": POST_H_007_D_CREATED_BY,
            "operation": rule.operation_id,
            "client": normalized_client,
            "request_dry_run": request.dry_run,
            "policy_required": rule.policy_required,
            "risk_level": rule.risk_level,
            "writes_files": rule.writes_files,
        },
    )
