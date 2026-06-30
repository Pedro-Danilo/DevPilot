from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.approval.policy import ApprovalPolicyChecker, ApprovalPolicyInput
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.identity import IdentityRegistry, RbacCheckInput
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.policy.decisions import PolicyDecision, PolicyEffect

from .sandbox_policy import DEFAULT_CONNECTOR_REGISTRY_PATH, DEFAULT_SANDBOX_POLICY_PATH, ConnectorSandboxPolicyOptions, ConnectorSandboxPolicyValidator

CONNECTOR_POLICY_EXPOSURE_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-CONNECTOR-POLICY-EXPOSURE-REPORT-V1"
DEFAULT_CONNECTOR_POLICY_EXPOSURE_REPORT_JSON = Path("outputs/reports/connector_policy_exposure_report.json")
DEFAULT_CONNECTOR_POLICY_EXPOSURE_REPORT_MD = Path("outputs/reports/connector_policy_exposure_report.md")

_READ_ONLY_SIDE_EFFECTS = {"none", "read", "report"}
_HIGH_RISK_LEVELS = {"high", "critical"}
_ALLOWED_RUNTIME_MODES = {"validate", "dry-run", "replay"}
_CONNECTOR_BINDING_RULES = ("connector.validate", "connector.replay", "connector.write_future")


@dataclass(frozen=True)
class ConnectorPolicyBindingRequest:
    """Request contract for POST-H-018-D connector Policy/Approval/RBAC checks."""

    connector_id: str = "local.docs"
    operation: str = "list_sources"
    mode: str = "validate"
    actor_id: str | None = None
    role_at_decision: str | None = None
    approval_id: str | None = None
    input_payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class ConnectorPolicyBindingOptions:
    """Local paths and output options for connector exposure reporting."""

    policy_path: Path | str = DEFAULT_SANDBOX_POLICY_PATH
    registry_path: Path | str = DEFAULT_CONNECTOR_REGISTRY_PATH
    output_json: Path | str = DEFAULT_CONNECTOR_POLICY_EXPOSURE_REPORT_JSON
    output_markdown: Path | str = DEFAULT_CONNECTOR_POLICY_EXPOSURE_REPORT_MD
    write_report: bool = False


class ConnectorPolicyBindingValidator:
    """Bind connector sandbox classifications to PolicyEngine, Approval and RBAC.

    POST-H-018-D remains validation/report-only. It does not execute connector
    adapters, perform connector write, call network, call external APIs, execute
    plugins or mutate external resources. The validator proves that connector
    read-only paths have policy coverage, high/critical risk connectors go
    through RBAC, and any future side-effect/write path is blocked.
    """

    def __init__(self, root: Path, *, options: ConnectorPolicyBindingOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ConnectorPolicyBindingOptions()
        self.policy_engine = PolicyEngine(self.root)
        self.approval_checker = ApprovalPolicyChecker(self.root)
        self.identity_registry = IdentityRegistry(self.root)

    @property
    def policy_path(self) -> Path:
        return _resolve(self.root, self.options.policy_path)

    @property
    def registry_path(self) -> Path:
        return _resolve(self.root, self.options.registry_path)

    def evaluate_request(self, request: ConnectorPolicyBindingRequest) -> CommandResult:
        """Evaluate binding for a single sandbox request and fail closed.

        This method is used by ConnectorSandboxRunner before any replay/dry-run
        evidence is accepted. Expected future-write blocks are required. Missing
        Approval/RBAC on side-effecting or high-risk connector classifications
        is surfaced as a BLOCK for that request.
        """

        policy_validation = self._validate_policy()
        findings: list[Finding] = []
        if not policy_validation.ok:
            findings.extend(policy_validation.findings)
            findings.append(
                Finding(
                    "CONNECTOR_BINDING_POLICY_INVALID",
                    "Connector Policy/Approval/RBAC binding is blocked until the sandbox policy validates.",
                    Severity.BLOCK,
                    path=_rel(self.root, self.policy_path),
                )
            )
            return self._request_result(request, {}, policy_validation, {}, findings)

        policy = self._load_json(self.policy_path)
        connector = _find_connector(policy, request.connector_id)
        if connector is None:
            findings.append(
                Finding(
                    "CONNECTOR_BINDING_CONNECTOR_NOT_REGISTERED",
                    "Connector has no sandbox policy entry; policy binding fails closed.",
                    Severity.BLOCK,
                    metadata={"connector_id": request.connector_id},
                )
            )
            return self._request_result(request, {}, policy_validation, {}, findings)

        evaluation = self._evaluate_connector(connector, request=request, strict_request=True)
        findings.extend(evaluation["findings"])
        return self._request_result(request, connector, policy_validation, evaluation, findings)

    def exposure_report(self, *, actor_id: str | None = None) -> CommandResult:
        """Build an exposure report for all connector policy entries.

        Expected deny/block outcomes for connector.write_future are evidence of
        safety, not report failure. The report fails only when coverage is
        incomplete, future write is not blocked, high-risk RBAC is not evaluated,
        or safety flags imply network/mutation/write capability.
        """

        policy_validation = self._validate_policy()
        findings: list[Finding] = []
        if not policy_validation.ok:
            findings.extend(policy_validation.findings)
            findings.append(
                Finding(
                    "CONNECTOR_EXPOSURE_POLICY_INVALID",
                    "Connector exposure report is blocked until the sandbox policy validates.",
                    Severity.BLOCK,
                    path=_rel(self.root, self.policy_path),
                )
            )
            return self._exposure_result([], {}, policy_validation, findings, reports_written=False)

        policy = self._load_json(self.policy_path)
        connector_entries = [item for item in policy.get("connectors", []) if isinstance(item, dict)]
        exposures: list[dict[str, Any]] = []
        for connector in connector_entries:
            operations = connector.get("operations") if isinstance(connector.get("operations"), list) else []
            operation = str(operations[0] if operations else "validate")
            request = ConnectorPolicyBindingRequest(
                connector_id=str(connector.get("connector_id") or ""),
                operation=operation,
                mode="validate",
                actor_id=actor_id,
                input_payload={"operation": operation, "exposure_report": True},
            )
            evaluation = self._evaluate_connector(connector, request=request, strict_request=False)
            exposure = _public_exposure(connector, evaluation)
            exposures.append(exposure)
            findings.extend(evaluation["findings"])

            if not exposure["policy_coverage"]:
                findings.append(
                    Finding(
                        "CONNECTOR_EXPOSURE_POLICY_COVERAGE_BLOCK",
                        "Connector lacks complete policy coverage.",
                        Severity.BLOCK,
                        metadata={"connector_id": exposure["connector_id"]},
                    )
                )
            if not exposure["write_future_blocked"]:
                findings.append(
                    Finding(
                        "CONNECTOR_EXPOSURE_WRITE_FUTURE_NOT_BLOCKED",
                        "connector.write_future must remain blocked for every connector.",
                        Severity.BLOCK,
                        metadata={"connector_id": exposure["connector_id"]},
                    )
                )
            if exposure["risk_level"] in _HIGH_RISK_LEVELS and not exposure["rbac_evaluated"]:
                findings.append(
                    Finding(
                        "CONNECTOR_EXPOSURE_RBAC_NOT_EVALUATED",
                        "High/critical connector exposure must evaluate RBAC.",
                        Severity.BLOCK,
                        metadata={"connector_id": exposure["connector_id"], "risk_level": exposure["risk_level"]},
                    )
                )
            if exposure["side_effecting"] and not exposure["approval_policy_checked"]:
                findings.append(
                    Finding(
                        "CONNECTOR_EXPOSURE_APPROVAL_NOT_CHECKED",
                        "Side-effecting connector exposure must evaluate ApprovalPolicyChecker.",
                        Severity.BLOCK,
                        metadata={"connector_id": exposure["connector_id"], "side_effect": exposure["side_effect"]},
                    )
                )

        if not any(f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for f in findings):
            findings.append(
                Finding(
                    "CONNECTOR_EXPOSURE_PASS",
                    "Connector exposure report confirms policy coverage, high-risk RBAC evaluation and connector.write_future deny/block.",
                    Severity.INFO,
                    metadata={"connectors_total": len(exposures)},
                )
            )

        result = self._exposure_result(exposures, policy, policy_validation, findings, reports_written=False)
        if self.options.write_report and "report" in result.data:
            reports = self._write_report(result.data["report"])
            data = dict(result.data)
            summary = dict(data.get("summary") or {})
            summary["reports_written"] = True
            summary["output_json"] = reports["json"]
            summary["output_markdown"] = reports["markdown"]
            data["summary"] = summary
            report = dict(data["report"])
            report_summary = dict(report.get("summary") or {})
            report_summary.update({"reports_written": True, "output_json": reports["json"], "output_markdown": reports["markdown"]})
            report["summary"] = report_summary
            data["report"] = report
            data["reports"] = reports
            self._write_report(report)
            result = CommandResult(result.command, result.ok, result.exit_code, result.message, data, result.findings)
        return result

    def _validate_policy(self) -> CommandResult:
        return ConnectorSandboxPolicyValidator(
            self.root,
            options=ConnectorSandboxPolicyOptions(policy_path=self.options.policy_path, registry_path=self.options.registry_path),
        ).validate()

    def _evaluate_connector(
        self,
        connector: dict[str, Any],
        *,
        request: ConnectorPolicyBindingRequest,
        strict_request: bool,
    ) -> dict[str, Any]:
        connector_id = str(connector.get("connector_id") or request.connector_id)
        side_effect = str(connector.get("side_effect") or "unknown").lower()
        risk_level = str(connector.get("risk_level") or "unknown").lower()
        allowed_modes = {str(mode) for mode in connector.get("allowed_modes", []) if isinstance(mode, str)}
        policy_rules = [str(rule) for rule in connector.get("policy_rules", []) if str(rule).strip()]
        side_effecting = side_effect not in _READ_ONLY_SIDE_EFFECTS
        high_risk = risk_level in _HIGH_RISK_LEVELS
        mode_allowed = request.mode in _ALLOWED_RUNTIME_MODES and request.mode in allowed_modes
        policy_coverage = bool(policy_rules) and connector.get("write_allowed") is False and connector.get("mutations_allowed") is False and connector.get("execution_allowed") is False

        findings: list[Finding] = []
        if not policy_coverage:
            findings.append(
                Finding(
                    "CONNECTOR_BINDING_POLICY_COVERAGE_BLOCK",
                    "Connector is missing policy rules or deny-write safety flags.",
                    Severity.BLOCK,
                    metadata={"connector_id": connector_id},
                )
            )
        if strict_request and not mode_allowed:
            findings.append(
                Finding(
                    "CONNECTOR_BINDING_MODE_BLOCKED",
                    "Connector binding rejects modes not allowed by sandbox policy.",
                    Severity.BLOCK,
                    metadata={"connector_id": connector_id, "mode": request.mode, "allowed_modes": sorted(allowed_modes)},
                )
            )

        read_policy = self.policy_engine.evaluate(
            PolicyRequest(
                action="read",
                path="docs",
                text=json.dumps(request.input_payload or {}, ensure_ascii=False, sort_keys=True),
                dry_run=True,
                external_api=False,
                tool_id="connector.sandbox.run",
                subject=f"{connector_id}:{request.operation}:{request.mode}",
                actor=request.actor_id,
                role_at_decision=request.role_at_decision,
                command_id="connector.sandbox.run",
                interface="connector",
                metadata={
                    "component": "ConnectorPolicyBindingValidator",
                    "sprint": "POST-H-018-D",
                    "binding_rule": "connector.validate" if request.mode == "validate" else "connector.replay",
                    "connector_id": connector_id,
                    "operation": request.operation,
                    "mode": request.mode,
                    "side_effect": side_effect,
                    "risk_level": risk_level,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "connector_write_used": False,
                },
            )
        )

        approval_action = "connector.write_execute" if side_effecting else "read"
        approval_decision = self.approval_checker.evaluate(
            ApprovalPolicyInput(
                action=approval_action,
                approval_id=request.approval_id,
                tool_id="connector.write_future" if side_effecting else "connector.sandbox.run",
                subject=f"{connector_id}:{request.operation}:{request.mode}",
                path="connectors",
                actor_id=request.actor_id,
                role_at_decision=request.role_at_decision,
                command_id="connector.sandbox.run",
                tool_call_id="connector.policy.binding",
                metadata={
                    "interface": "connector",
                    "actor_id": request.actor_id,
                    "role_at_decision": request.role_at_decision,
                    "connector_id": connector_id,
                    "side_effect": side_effect,
                    "risk_level": risk_level,
                    "post_h_018_d": True,
                },
            )
        )
        approval_required = bool(approval_decision.metadata.get("approval_required") or side_effecting or connector.get("approval_required"))
        approval_policy_checked = True

        rbac_decision: PolicyDecision | None = None
        rbac_evaluated = bool(high_risk or side_effecting or connector.get("rbac_required"))
        if rbac_evaluated:
            rbac_decision = self.identity_registry.evaluate(
                RbacCheckInput(
                    actor_id=request.actor_id,
                    action="connector.write_execute" if (side_effecting or high_risk) else "read",
                    permission="tool.execute.approve" if (side_effecting or high_risk) else "policy.evaluate",
                    tool_id="connector.write_future" if side_effecting else "connector.sandbox.run",
                    subject=f"{connector_id}:{request.operation}",
                    require_sensitive=True,
                )
            )
            if strict_request and not rbac_decision.ok:
                findings.append(
                    Finding(
                        "CONNECTOR_BINDING_RBAC_DENIED",
                        "RBAC denied the connector sandbox request for this actor.",
                        Severity.BLOCK,
                        metadata={"connector_id": connector_id, **dict(rbac_decision.metadata or {})},
                    )
                )

        write_future_policy = self.policy_engine.evaluate(
            PolicyRequest(
                action="connector.write_execute",
                path="connectors",
                text=json.dumps({"connector_id": connector_id, "operation": request.operation, "future_write": True}, ensure_ascii=False, sort_keys=True),
                dry_run=True,
                external_api=False,
                tool_id="connector.write_future",
                subject=f"{connector_id}:{request.operation}:write_future",
                actor=request.actor_id,
                role_at_decision=request.role_at_decision,
                command_id="connector.sandbox.write_future",
                tool_call_id="connector.write_future.synthetic",
                interface="connector",
                metadata={
                    "component": "ConnectorPolicyBindingValidator",
                    "sprint": "POST-H-018-D",
                    "binding_rule": "connector.write_future",
                    "connector_id": connector_id,
                    "operation": request.operation,
                    "side_effect": side_effect,
                    "risk_level": risk_level,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "connector_write_used": False,
                },
            )
        )
        write_future_blocked = not write_future_policy.ok
        if not write_future_blocked:
            findings.append(
                Finding(
                    "CONNECTOR_BINDING_WRITE_FUTURE_NOT_BLOCKED",
                    "connector.write_future unexpectedly passed PolicyEngine; deny-write invariant is broken.",
                    Severity.BLOCK,
                    metadata={"connector_id": connector_id},
                )
            )
        if strict_request and side_effecting and approval_required and approval_decision.effect == PolicyEffect.BLOCK:
            findings.append(
                Finding(
                    "CONNECTOR_BINDING_APPROVAL_REQUIRED",
                    "Side-effecting connector classification requires ApprovalPolicyChecker approval and remains blocked without a valid approval_id.",
                    Severity.BLOCK,
                    metadata={"connector_id": connector_id, "side_effect": side_effect, "approval_rule_id": approval_decision.rule_id},
                )
            )
        if high_risk and not rbac_evaluated:
            findings.append(
                Finding(
                    "CONNECTOR_BINDING_HIGH_RISK_RBAC_NOT_EVALUATED",
                    "High/critical connector classification must evaluate RBAC.",
                    Severity.BLOCK,
                    metadata={"connector_id": connector_id, "risk_level": risk_level},
                )
            )

        if not findings:
            findings.append(
                Finding(
                    "CONNECTOR_BINDING_PASS",
                    "Connector Policy/Approval/RBAC binding passed for the selected safe sandbox request and future write remained blocked.",
                    Severity.INFO,
                    metadata={"connector_id": connector_id, "mode": request.mode, "write_future_blocked": write_future_blocked},
                )
            )

        return {
            "connector_id": connector_id,
            "operation": request.operation,
            "mode": request.mode,
            "side_effect": side_effect,
            "side_effecting": side_effecting,
            "risk_level": risk_level,
            "high_risk": high_risk,
            "allowed_modes": sorted(allowed_modes),
            "mode_allowed": mode_allowed,
            "policy_rules": policy_rules,
            "binding_rules": list(_CONNECTOR_BINDING_RULES),
            "policy_coverage": policy_coverage,
            "read_policy": _policy_summary(read_policy),
            "approval_policy_checked": approval_policy_checked,
            "approval_required": approval_required,
            "approval_decision": approval_decision.to_dict(),
            "approval_missing_blocks": approval_required and approval_decision.effect == PolicyEffect.BLOCK,
            "rbac_evaluated": rbac_evaluated,
            "rbac_allowed": bool(rbac_decision.ok) if rbac_decision is not None else None,
            "rbac_decision": rbac_decision.to_dict() if rbac_decision is not None else None,
            "write_future_policy": _policy_summary(write_future_policy),
            "write_future_blocked": write_future_blocked,
            "write_future_denied_by": _blocking_rule_ids(write_future_policy),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "connector_write_used": False,
            "remote_execution_used": False,
            "plugin_execution_used": False,
            "findings": findings,
        }

    def _request_result(
        self,
        request: ConnectorPolicyBindingRequest,
        connector: dict[str, Any],
        policy_validation: CommandResult,
        evaluation: dict[str, Any],
        findings: list[Finding],
    ) -> CommandResult:
        blocking = sum(1 for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL})
        ok = blocking == 0
        summary = {
            "created_by": "POST-H-018-D",
            "status": "implemented-initial",
            "preliminary": True,
            "connector_id": request.connector_id,
            "operation": request.operation,
            "mode": request.mode,
            "policy_path": _rel(self.root, self.policy_path),
            "registry_path": _rel(self.root, self.registry_path),
            "policy_valid": policy_validation.ok,
            "binding_rules": list(_CONNECTOR_BINDING_RULES),
            "policy_coverage": bool(evaluation.get("policy_coverage", False)),
            "approval_policy_checked": bool(evaluation.get("approval_policy_checked", False)),
            "approval_required": bool(evaluation.get("approval_required", False)),
            "approval_missing_blocks": bool(evaluation.get("approval_missing_blocks", False)),
            "rbac_evaluated": bool(evaluation.get("rbac_evaluated", False)),
            "rbac_allowed": evaluation.get("rbac_allowed"),
            "write_future_blocked": bool(evaluation.get("write_future_blocked", False)),
            "side_effect": evaluation.get("side_effect") or (connector.get("side_effect") if connector else None),
            "risk_level": evaluation.get("risk_level") or (connector.get("risk_level") if connector else None),
            "blocking_findings_total": blocking,
            "findings_total": len(findings),
            "local_first": True,
            "dry_run": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "connector_write_used": False,
            "remote_execution_used": False,
            "plugin_execution_used": False,
            "secrets_included": False,
        }
        data = {
            "summary": summary,
            "binding": _strip_findings(evaluation),
            "policy_validation": (policy_validation.data or {}).get("summary", {}),
            "notes": [
                "POST-H-018-D evaluates PolicyEngine, ApprovalPolicyChecker and RBAC bindings only; it does not execute connector writes.",
                "connector.write_future is intentionally synthetic and must remain deny/block until a later ADR and backlog explicitly authorize it.",
            ],
        }
        return CommandResult(
            command="connector sandbox binding",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Connector Policy/Approval/RBAC binding passed." if ok else "Connector Policy/Approval/RBAC binding blocked.",
            data=data,
            findings=findings,
        )

    def _exposure_result(
        self,
        exposures: list[dict[str, Any]],
        policy: dict[str, Any],
        policy_validation: CommandResult,
        findings: list[Finding],
        *,
        reports_written: bool,
    ) -> CommandResult:
        blocking = sum(1 for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL})
        ok = blocking == 0
        risk_counts = Counter(item.get("risk_level") for item in exposures)
        side_effect_counts = Counter(item.get("side_effect") for item in exposures)
        high_risk = [item for item in exposures if item.get("risk_level") in _HIGH_RISK_LEVELS]
        side_effecting = [item for item in exposures if item.get("side_effecting")]
        write_blocked = [item for item in exposures if item.get("write_future_blocked")]
        summary = {
            "created_by": "POST-H-018-D",
            "status": "implemented-initial",
            "preliminary": True,
            "policy_path": _rel(self.root, self.policy_path),
            "registry_path": _rel(self.root, self.registry_path),
            "policy_valid": policy_validation.ok,
            "connectors_total": len(exposures),
            "connectors_by_risk": dict(risk_counts),
            "connectors_by_side_effect": dict(side_effect_counts),
            "high_risk_connectors_total": len(high_risk),
            "side_effecting_connectors_total": len(side_effecting),
            "read_only_policy_coverage_total": sum(1 for item in exposures if not item.get("side_effecting") and item.get("policy_coverage")),
            "rbac_evaluated_high_risk_total": sum(1 for item in high_risk if item.get("rbac_evaluated")),
            "approval_checked_side_effecting_total": sum(1 for item in side_effecting if item.get("approval_policy_checked")),
            "write_future_blocked_total": len(write_blocked),
            "policy_coverage_complete": all(item.get("policy_coverage") for item in exposures),
            "all_side_effecting_future_write_blocked": all(item.get("write_future_blocked") for item in side_effecting),
            "all_high_risk_rbac_evaluated": all(item.get("rbac_evaluated") for item in high_risk),
            "binding_rules": list(_CONNECTOR_BINDING_RULES),
            "blocking_findings_total": blocking,
            "findings_total": len(findings),
            "reports_written": reports_written,
            "output_json": None,
            "output_markdown": None,
            "local_first": True,
            "dry_run": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "connector_write_used": False,
            "remote_execution_used": False,
            "plugin_execution_used": False,
            "secrets_included": False,
        }
        report = {
            "schema_version": "1.0",
            "schema_id": CONNECTOR_POLICY_EXPOSURE_REPORT_SCHEMA_ID,
            "report_id": _report_id("connector-policy-exposure"),
            "created_by": "POST-H-018-D",
            "status": "passed" if ok else "blocked",
            "ok": ok,
            "summary": summary,
            "connectors": exposures,
            "policy": {
                "policy_id": policy.get("policy_id") if isinstance(policy, dict) else None,
                "default_mode": policy.get("default_mode") if isinstance(policy, dict) else None,
                "connector_write_enabled": policy.get("connector_write_enabled") if isinstance(policy, dict) else None,
            },
            "safety": _safety(),
            "findings": [finding.to_dict() for finding in findings],
            "preliminary": True,
        }
        data = {"summary": summary, "report": report, "connectors": exposures}
        return CommandResult(
            command="connector sandbox exposure",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Connector Policy/Approval/RBAC exposure report passed." if ok else "Connector Policy/Approval/RBAC exposure report blocked.",
            data=data,
            findings=findings,
        )

    def _write_report(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = _resolve(self.root, self.options.output_json)
        markdown_path = _resolve(self.root, self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(_render_markdown(report), encoding="utf-8")
        return {"json": _rel(self.root, json_path), "markdown": _rel(self.root, markdown_path)}

    def _load_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))


def _policy_summary(result: CommandResult) -> dict[str, Any]:
    summary = dict((result.data or {}).get("summary", {}))
    summary["ok"] = result.ok
    summary["exit_code"] = int(result.exit_code)
    summary["blocking_rule_ids"] = _blocking_rule_ids(result)
    return summary


def _blocking_rule_ids(result: CommandResult) -> list[str]:
    decisions = (result.data or {}).get("decisions", [])
    blocked = []
    for decision in decisions:
        if isinstance(decision, dict) and decision.get("effect") in {"block", "deny"}:
            blocked.append(str(decision.get("rule_id")))
    return sorted(set(blocked))


def _public_exposure(connector: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
    return {
        "connector_id": evaluation.get("connector_id") or connector.get("connector_id"),
        "status": connector.get("status"),
        "risk_level": evaluation.get("risk_level") or connector.get("risk_level"),
        "side_effect": evaluation.get("side_effect") or connector.get("side_effect"),
        "side_effecting": bool(evaluation.get("side_effecting", False)),
        "allowed_modes": evaluation.get("allowed_modes", []),
        "policy_rules": evaluation.get("policy_rules", []),
        "binding_rules": evaluation.get("binding_rules", []),
        "policy_coverage": bool(evaluation.get("policy_coverage", False)),
        "approval_required": bool(evaluation.get("approval_required", False)),
        "approval_policy_checked": bool(evaluation.get("approval_policy_checked", False)),
        "approval_missing_blocks": bool(evaluation.get("approval_missing_blocks", False)),
        "rbac_evaluated": bool(evaluation.get("rbac_evaluated", False)),
        "rbac_allowed": evaluation.get("rbac_allowed"),
        "write_future_blocked": bool(evaluation.get("write_future_blocked", False)),
        "write_future_denied_by": evaluation.get("write_future_denied_by", []),
        "network_used": False,
        "external_api_used": False,
        "mutations_performed": False,
        "connector_write_used": False,
    }


def _strip_findings(evaluation: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in evaluation.items() if key != "findings"}


def _find_connector(policy: dict[str, Any], connector_id: str) -> dict[str, Any] | None:
    normalized = str(connector_id or "").strip().lower()
    for connector in policy.get("connectors", []):
        if isinstance(connector, dict) and str(connector.get("connector_id") or "").strip().lower() == normalized:
            return connector
    return None


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    lines = [
        "# Connector Policy/Approval/RBAC Exposure Report",
        "",
        f"- Report ID: `{report.get('report_id')}`",
        f"- Generated by: `{report.get('created_by')}`",
        f"- Status: `{report.get('status')}`",
        f"- Connectors total: `{summary.get('connectors_total')}`",
        f"- Connectors by risk: `{summary.get('connectors_by_risk')}`",
        f"- High-risk RBAC evaluated: `{summary.get('rbac_evaluated_high_risk_total')}`",
        f"- Future write blocked: `{summary.get('write_future_blocked_total')}`",
        f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
        "",
        "## Connector exposure",
    ]
    for connector in report.get("connectors", []):
        lines.append(
            f"- `{connector.get('connector_id')}` risk=`{connector.get('risk_level')}` side_effect=`{connector.get('side_effect')}` "
            f"policy_coverage=`{connector.get('policy_coverage')}` rbac_evaluated=`{connector.get('rbac_evaluated')}` write_future_blocked=`{connector.get('write_future_blocked')}`"
        )
    lines.extend(["", "This report is validation-only. It is not permission for connector write, network, external APIs, remote execution or plugin execution.\n"])
    return "\n".join(lines)


def _safety() -> dict[str, Any]:
    return {
        "local_first": True,
        "dry_run": True,
        "network_used": False,
        "external_api_used": False,
        "mutations_performed": False,
        "source_mutations_performed": False,
        "connector_write_used": False,
        "remote_execution_used": False,
        "plugin_execution_used": False,
        "secrets_included": False,
    }


def _report_id(prefix: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{stamp}"


def _resolve(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _rel(root: Path, path: Path | str) -> str:
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return candidate.as_posix()
