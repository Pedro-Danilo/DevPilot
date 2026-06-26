from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest

from .approval_service import ApprovalApplicationService
from .dtos import ApplicationRequest, ApplicationResponse, InterfaceRouteContract, ServiceCapability
from .dto_normalization import normalize_priority_application_request
from .evals_service import EvaluationApplicationService
from .history_service import HistoryApplicationService
from .miasi_service import MiasiApplicationService
from .maturity_service import MaturityApplicationService
from .model_service import ModelApplicationService
from .observability_service import ObservabilityApplicationService
from .policy import ApplicationBoundaryPolicy
from .refactor_service import RefactorApplicationService
from .repo_service import RepoApplicationService
from .reports_service import ReportsApplicationService
from .settings_service import SettingsApplicationService
from .review_service import ReviewApplicationService
from .validation_service import ValidationApplicationService
from .workspace_service import WorkspaceApplicationService


def _display_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


class ApplicationService:
    """Application-service facade for CLI, future API local and Web UI shells.

    FUNC-SPRINT-65 upgrades the earlier validator-only facade into a domain
    facade. It keeps presentation layers away from DevPilot Core internals by
    grouping reusable operations under explicit domain services:

    - workspace
    - validation
    - MIASI
    - evaluations
    - repository
    - review
    - refactor
    - model governance
    - history
    - observability / AgentOps

    The service remains local-only, deterministic by default and dependency-free.
    It does not implement an HTTP server, Web UI or Desktop shell. It exposes
    CommandResult for existing CLI compatibility and ApplicationResponse for the
    future API/Web boundary.
    """

    def __init__(self, root: Path, *, enforce_workspace_paths: bool = False) -> None:
        self.root = root.resolve()
        self.enforce_workspace_paths = enforce_workspace_paths
        self.workspace = WorkspaceApplicationService(self.root)
        self.validation = ValidationApplicationService(self.root, enforce_workspace_paths=enforce_workspace_paths)
        self.miasi = MiasiApplicationService(self.root)
        self.maturity = MaturityApplicationService(self.root)
        self.evals = EvaluationApplicationService(self.root)
        self.repo = RepoApplicationService(self.root)
        self.reports = ReportsApplicationService(self.root)
        self.approvals = ApprovalApplicationService(self.root)
        self.settings = SettingsApplicationService(self.root)
        self.review = ReviewApplicationService(self.root)
        self.refactor = RefactorApplicationService(self.root)
        self.model = ModelApplicationService(self.root)
        self.history = HistoryApplicationService(self.root)
        self.observability = ObservabilityApplicationService(self.root)
        self.boundary_policy = ApplicationBoundaryPolicy(self.root)

    # Backward-compatible validator facade from Sprint 18.
    def validate_frontmatter(self, path: str | Path, *, strict: bool = False) -> CommandResult:
        return self.validation.validate_frontmatter(path, strict=strict)

    def validate_artifact(self, path: str | Path, *, strict: bool = False) -> CommandResult:
        return self.validation.validate_artifact(path, strict=strict)

    def checklist_pre_code(self, *, strict: bool = True) -> CommandResult:
        return self.validation.checklist_pre_code(strict=strict)

    def readiness(self, *, strict: bool = False) -> CommandResult:
        return self.validation.readiness(strict=strict)

    def standards_status(self) -> CommandResult:
        return self.validation.standards_status()

    # Domain shortcuts intended for CLI reuse and future API route handlers.
    def workspace_status(self) -> CommandResult:
        return self.workspace.status()

    def miasi_validate(self, *, scope: str = "all") -> CommandResult:
        return self.miasi.validate(scope=scope)

    def eval_run(self, *, suite: str = "documentation", case_id: str | None = None, write_report: bool = False) -> CommandResult:
        return self.evals.run_documentation(suite=suite, case_id=case_id, write_report=write_report)

    def repo_inventory(self) -> CommandResult:
        return self.repo.inventory()

    def repo_analyze(self, *, target: str | Path = ".") -> CommandResult:
        return self.repo.analyze(target=target)

    def code_review(self, *, target: str | Path = ".") -> CommandResult:
        return self.review.code_review(target=target)

    def refactor_plan(self, *, target: str | Path = ".", goal: str = "", include_code_review: bool = True) -> CommandResult:
        return self.refactor.plan(target=target, goal=goal, include_code_review=include_code_review)

    def model_providers(self) -> CommandResult:
        return self.model.providers()

    def maturity_dashboard(self, *, write_report: bool = False) -> CommandResult:
        return self.maturity.dashboard(write_report=write_report)

    def maturity_dashboard_gate(self, *, write_report: bool = False) -> CommandResult:
        return self.maturity.dashboard_gate(write_report=write_report)

    def settings_workspace(self) -> CommandResult:
        return self.settings.workspace()

    def settings_providers(self, *, prefer_example: bool = False) -> CommandResult:
        return self.settings.providers(prefer_example=prefer_example)

    def settings_policy(self) -> CommandResult:
        return self.settings.policy()

    def settings_status(self) -> CommandResult:
        """Read-only aggregate settings status for POST-H-007-C DTO normalization."""

        steps = [
            ("workspace", self.settings_workspace()),
            ("providers", self.settings_providers()),
            ("policy", self.settings_policy()),
        ]
        findings: list[Finding] = []
        projections: dict[str, Any] = {}
        for step_id, result in steps:
            projections[step_id] = result.to_dict()
            for finding in result.findings:
                metadata = dict(finding.metadata or {})
                metadata.setdefault("settings_step", step_id)
                metadata.setdefault("source_command", result.command)
                findings.append(Finding(finding.id, finding.message, finding.severity, path=finding.path, metadata=metadata))
        codes = {result.exit_code for _, result in steps}
        if ExitCode.ERROR in codes:
            exit_code = ExitCode.ERROR
        elif ExitCode.BLOCK in codes:
            exit_code = ExitCode.BLOCK
        elif ExitCode.FAIL in codes:
            exit_code = ExitCode.FAIL
        else:
            exit_code = ExitCode.PASS
        ok = all(result.ok for _, result in steps)
        summary = {
            "operation": "settings.status",
            "steps_total": len(steps),
            "steps_passed": sum(1 for _, result in steps if result.ok),
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        return CommandResult(
            command="settings status",
            ok=ok,
            exit_code=exit_code,
            message="Settings status aggregate passed." if ok else "Settings status aggregate reported blocking findings.",
            data={"summary": summary, "settings": projections},
            findings=findings,
        )

    def settings_provider_plan(self, *, provider_id: str, changes: dict[str, Any] | None = None, actor: str = "ui-local", reason: str = "Settings UI plan-only provider change") -> CommandResult:
        return self.settings.provider_plan(provider_id=provider_id, changes=changes, actor=actor, reason=reason)

    def approvals_list(self, *, status: str | None = None, tool_id: str | None = None, action: str | None = None, limit: int = 100) -> CommandResult:
        return self.approvals.list(status=status, tool_id=tool_id, action=action, limit=limit)

    def approvals_show(self, *, approval_id: str) -> CommandResult:
        return self.approvals.show(approval_id=approval_id)

    def approvals_request(
        self,
        *,
        tool_id: str,
        action: str,
        subject: str,
        actor: str,
        reason: str,
        scope: str | None = None,
        expires_at: str | None = None,
        ttl_minutes: int = 60,
    ) -> CommandResult:
        return self.approvals.request(tool_id=tool_id, action=action, subject=subject, actor=actor, reason=reason, scope=scope, expires_at=expires_at, ttl_minutes=ttl_minutes)

    def approvals_decide(self, *, approval_id: str, decision: str, actor: str, reason: str) -> CommandResult:
        return self.approvals.decide(approval_id=approval_id, decision=decision, actor=actor, reason=reason)

    def ui_action_dry_run(self, *, action_id: str, payload: dict[str, Any] | None = None) -> CommandResult:
        """Run a UI-launched safe action in dry-run/read-only mode only.

        The UI may trigger only deterministic read/dry-run actions. Critical
        execution actions are evaluated through PolicyEngine and then blocked by
        the Sprint 71 UI contract even when an approval id is supplied; actual
        execution remains CLI/API governed by later explicit workflows.
        """

        action_payload = dict(payload or {})
        normalized = str(action_id or action_payload.get("action_id") or "").strip().lower()
        target = str(action_payload.get("target") or ".")
        goal = str(action_payload.get("goal") or "")
        approval_id = str(action_payload.get("approval_id") or "").strip() or None
        safe_actions = {
            "readiness": ("validation.readiness", lambda: self.readiness(strict=bool(action_payload.get("strict", True))), "readiness-check"),
            "validation.readiness": ("validation.readiness", lambda: self.readiness(strict=bool(action_payload.get("strict", True))), "readiness-check"),
            "code-review": ("review.code", lambda: self.code_review(target=target), "code-review"),
            "review.code": ("review.code", lambda: self.code_review(target=target), "code-review"),
            "refactor-plan": ("refactor.plan", lambda: self.refactor_plan(target=target, goal=goal, include_code_review=bool(action_payload.get("include_code_review", True))), "safe-refactor-plan"),
            "refactor.plan": ("refactor.plan", lambda: self.refactor_plan(target=target, goal=goal, include_code_review=bool(action_payload.get("include_code_review", True))), "safe-refactor-plan"),
        }
        critical_actions = {
            "patch-apply": "patch.apply",
            "patch.apply": "patch.apply",
            "refactor-execute": "refactor.execute",
            "refactor.execute": "refactor.execute",
            "rollback-execute": "rollback.execute",
            "rollback.execute": "rollback.execute",
            "tests-run-execute": "tests.run",
            "tests.run.execute": "tests.run",
            "git-push": "git.push",
            "deploy": "deploy",
        }
        if normalized in safe_actions:
            operation, runner, tool_id = safe_actions[normalized]
            policy_result = PolicyEngine(self.root).evaluate(
                PolicyRequest(
                    action="read",
                    path=target if target else None,
                    dry_run=True,
                    approval_id=approval_id,
                    tool_id=tool_id,
                    subject=operation,
                    metadata={"component": "WebUIActionLauncher", "sprint": "FUNC-SPRINT-71", "api_operation": "ui.actions.dry_run", "ui_dry_run": True},
                )
            )
            if not policy_result.ok:
                return CommandResult(
                    command="ui action dry-run",
                    ok=False,
                    exit_code=policy_result.exit_code,
                    message="PolicyEngine blocked the UI dry-run action.",
                    data={"summary": {"action_id": normalized, "operation": operation, "dry_run": True, "policy_allowed": False, "preliminary": True}, "policy": policy_result.data},
                    findings=policy_result.findings,
                )
            result = runner()
            merged_data = dict(result.data or {})
            merged_data["action_launcher"] = {
                "action_id": normalized,
                "operation": operation,
                "tool_id": tool_id,
                "dry_run": True,
                "critical": False,
                "policy_binding": True,
                "policy_allowed": True,
                "approval_id_provided": bool(approval_id),
                "ui_execution_enabled": False,
                "preliminary": True,
            }
            return CommandResult(command="ui action dry-run", ok=result.ok, exit_code=result.exit_code, message=result.message, data=merged_data, findings=result.findings)

        if normalized in critical_actions:
            tool_id = critical_actions[normalized]
            policy_result = PolicyEngine(self.root).evaluate(
                PolicyRequest(
                    action="execute",
                    path=target if target else None,
                    dry_run=True,
                    approval_id=approval_id,
                    tool_id=tool_id,
                    subject=tool_id,
                    metadata={"component": "WebUIActionLauncher", "sprint": "FUNC-SPRINT-71", "critical_action_requested": True},
                )
            )
            findings = list(policy_result.findings) + [
                Finding(
                    "UI_CRITICAL_ACTION_DISABLED_BLOCK",
                    "The Web UI cannot execute critical actions; use governed CLI/API workflows with explicit approval in future sprints.",
                    Severity.BLOCK,
                    metadata={"action_id": normalized, "tool_id": tool_id, "dry_run": True, "approval_id_provided": bool(approval_id)},
                )
            ]
            return CommandResult(
                command="ui action dry-run",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Critical actions are blocked from the Web UI.",
                data={"summary": {"action_id": normalized, "tool_id": tool_id, "dry_run": True, "critical": True, "policy_binding": True, "policy_allowed": policy_result.ok, "ui_execution_enabled": False, "preliminary": True}, "policy": policy_result.data},
                findings=findings,
            )

        return CommandResult(
            command="ui action dry-run",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Requested UI action is not exposed by the Sprint 71 dry-run contract.",
            data={"summary": {"action_id": normalized, "supported": False, "dry_run": True, "preliminary": True}, "supported_actions": sorted(safe_actions)},
            findings=[Finding("UI_ACTION_NOT_EXPOSED_BLOCK", "The requested action is not exposed by the UI dry-run launcher.", Severity.BLOCK, metadata={"action_id": normalized})],
        )

    def reports_list(self, *, limit: int = 50, severity: str | None = None, status: str | None = None, command: str | None = None) -> CommandResult:
        return self.reports.list_reports(limit=limit, severity=severity, status=status, command=command)

    def reports_read(self, *, report_id: str, format: str = "json", max_chars: int = 20000) -> CommandResult:
        return self.reports.read_report(report_id, format=format, max_chars=max_chars)

    def trace_report(self, *, limit: int = 20, include_events: bool = True, include_metrics: bool = True) -> CommandResult:
        return self.observability.trace_report(limit=limit, include_events=include_events, include_metrics=include_metrics)

    def trace_inspect(self, trace_id: str, *, limit: int = 100) -> CommandResult:
        return self.observability.trace_inspect(trace_id, limit=limit)

    def metrics_summary(self, *, category: str | None = None, limit: int = 50) -> CommandResult:
        return self.observability.metrics_summary(category=category, limit=limit)

    def history_list(self, *, limit: int = 10) -> CommandResult:
        return self.history.list_runs(limit=limit)

    def as_application_response(self, result: CommandResult, *, operation: str | None = None) -> ApplicationResponse:
        return ApplicationResponse.from_command_result(result, operation=operation)

    def handle(self, request: ApplicationRequest) -> ApplicationResponse:
        """Execute a supported ApplicationRequest and return ApplicationResponse.

        This is intentionally a local in-process dispatcher, not an HTTP router.
        Sprint 66/67 can map API endpoints to these operations without allowing
        future UI code to import validators, repo engines, AgentOps or model
        internals directly.
        """

        result = self.execute(request)
        return self.as_application_response(result, operation=request.operation)

    def execute(self, request: ApplicationRequest) -> CommandResult:
        request = normalize_priority_application_request(request)
        operation = request.operation.strip()
        payload = dict(request.payload or {})
        dispatch = _operation_dispatch(self)
        handler = dispatch.get(operation)
        if handler is None:
            return CommandResult(
                command="app execute",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="ApplicationService operation is not exposed by the v2 contract.",
                data={
                    "summary": {
                        "operation": operation,
                        "supported": False,
                        "preliminary": True,
                        "external_api_used": False,
                        "network_used": False,
                    },
                    "supported_operations": sorted(dispatch),
                },
                findings=[
                    Finding(
                        id="APPLICATION_OPERATION_NOT_EXPOSED",
                        message="Requested operation is not part of the ApplicationService v2 contract.",
                        severity=Severity.BLOCK,
                        metadata={"operation": operation},
                    )
                ],
            )

        boundary_decision = self.boundary_policy.evaluate(request)
        if not boundary_decision.allowed:
            return boundary_decision.to_command_result()
        return handler(payload)

    def application_contract(self) -> CommandResult:
        capabilities = _capabilities()
        routes = _routes()
        domains = _domain_summaries()
        data: dict[str, Any] = {
            "summary": {
                "contract": "DevPilotApplicationServiceContract",
                "schema_version": "2.0",
                "capabilities_total": len(capabilities),
                "routes_total": len(routes),
                "domains_total": len(domains),
                "ui_implemented": True,
                "api_implemented": True,
                "api_local_mvp_implemented": True,
                "api_security_implemented": True,
                "api_token_required": True,
                "api_cors_restricted": True,
                "api_cors_wildcard_enabled": False,
                "api_policy_binding_enabled": True,
                "api_security_status": "secured-initial",
                "api_consumed_by_web_ui": True,
                "api_default_host": "127.0.0.1",
                "api_default_port": 8787,
                "api_contract_defined": True,
                "api_contract_version": "v1",
                "openapi_contract_defined": True,
                "openapi_contract_path": "docs/07_interfaces/openapi_v1.json",
                "api_service_mapping_path": "docs/07_interfaces/api_service_mapping.md",
                "visual_strategy": "web_ui_first",
                "api_local_planned": True,
                "web_ui_local_planned": True,
                "web_ui_local_implemented": True,
                "web_ui_status": "implemented-initial",
                "web_ui_path": "ui/web",
                "web_ui_api_only": True,
                "web_ui_read_only": True,
                "web_ui_real_future": True,
                "desktop_deferred": True,
                "desktop_ready_for_shell": False,
                "web_ready_for_shell": True,
                "web_dashboard_ready": True,
                "report_viewer_implemented": True,
                "trace_viewer_implemented": True,
                "report_trace_viewer_status": "implemented-initial",
                "approval_center_implemented": True,
                "approval_center_status": "implemented-initial",
                "dry_run_action_launcher_implemented": True,
                "web_ui_actions_dry_run_only": True,
                "web_ui_critical_actions_blocked": True,
                "settings_ui_implemented": True,
                "settings_ui_status": "implemented-initial",
                "settings_ui_read_only": True,
                "settings_provider_editor_plan_only": True,
                "settings_policy_editor_enabled": False,
                "settings_secrets_redacted": True,
                "web_ui_reports_api_only": True,
                "web_ui_traces_api_only": True,
                "external_api_required": False,
                "application_service_v2": True,
                "domain_facades_enabled": True,
                "phase_f_closed": True,
                "visual_product_mvp_release": True,
                "visual_product_quality_gate": True,
                "visual_product_quality_gate_path": "scripts/visual_product_smoke.py",
                "visual_product_release_manifest_path": "docs/release/release_manifest_visual_mvp.json",
                "phase_f_closure_report_path": "docs/audits/phase_f_visual_product_closure_report.md",
                "web_real_evolution_planned": True,
                "next_phase": "FASE-G-PRODUCTIZACION-RELEASE",
                "next_sprint": "FUNC-SPRINT-74",
                "preliminary": True,
            },
            "domains": domains,
            "capabilities": [capability.to_dict() for capability in capabilities],
            "routes": [route.to_dict() for route in routes],
            "dto_contracts": {
                "request": "ApplicationRequest",
                "response": "ApplicationResponse",
                "capability": "ServiceCapability",
                "route": "InterfaceRouteContract",
            },
            "preliminary": True,
            "notes": [
                "FUNC-SPRINT-73 closes Fase F with a Visual Product Quality Gate, visual MVP release manifest and Web-real evolution decision.",
                "FUNC-SPRINT-72 adds Settings UI for workspace/providers/policy in read-only and provider plan-only mode with secret redaction.",
                "FUNC-SPRINT-71 adds Approval Center and a dry-run Action Launcher; critical execution remains blocked from the Web UI.",
                "FUNC-SPRINT-70 adds Report Viewer and Trace Viewer over local API only; the UI does not read outputs/ directly.",
                "FUNC-SPRINT-69 adds a local Web UI MVP under ui/web that consumes only /api/v1 and remains read-only.",
                "FUNC-SPRINT-65 exposes domain application services for future API local and Web UI integration.",
                "FUNC-SPRINT-66 defines static API Contract v1 and OpenAPI preliminary artifacts without implementing an HTTP server.",
                "FUNC-SPRINT-67 implements the local FastAPI MVP in src/devpilot_core/interfaces/api, still without Web frontend or Desktop shell.",
                "FUNC-SPRINT-68 adds local API security controls: token, restricted CORS, security headers and PolicyEngine binding.",
                "API route handlers call ApplicationService/DomainService methods instead of importing DevPilot Core modules directly.",
                "Operations with side effects remain dry-run/report-only and protected by token/policy gates before future UI consumption.",
            ],
        }
        return CommandResult(
            command="app contract",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Application service v2 contract is available for CLI, secured local API MVP, Web UI viewers, Approval Center, Settings UI and Fase F visual MVP closure; desktop is deferred.",
            data=data,
            findings=[
                Finding(
                    id="APP_CONTRACT_V2_PASS",
                    message="ApplicationService v2 exposes domain facades plus secured local API route contracts, Web UI viewers, Approval Center, Settings UI and Fase F visual MVP closure.",
                    severity=Severity.INFO,
                    metadata={"domains_total": len(domains), "capabilities_total": len(capabilities)},
                )
            ],
        )

    def _resolve_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        if self.enforce_workspace_paths:
            try:
                candidate.relative_to(self.root)
            except ValueError as exc:
                raise ValueError(f"ApplicationService only accepts paths inside the workspace: {_display_path(path)}") from exc
        return candidate


OperationHandler = Callable[[dict[str, Any]], CommandResult]


def _operation_dispatch(service: ApplicationService) -> dict[str, OperationHandler]:
    return {
        "workspace.status": lambda payload: service.workspace_status(),
        "app.contract": lambda payload: service.application_contract(),
        "standards.status": lambda payload: service.standards_status(),
        "validators.validate_frontmatter": lambda payload: service.validate_frontmatter(str(payload.get("path", "")), strict=bool(payload.get("strict", False))),
        "validators.validate_artifact": lambda payload: service.validate_artifact(str(payload.get("path", "")), strict=bool(payload.get("strict", False))),
        "validators.readiness": lambda payload: service.readiness(strict=bool(payload.get("strict", False))),
        "validation.frontmatter": lambda payload: service.validate_frontmatter(str(payload.get("path", "")), strict=bool(payload.get("strict", False))),
        "validation.artifact": lambda payload: service.validate_artifact(str(payload.get("path", "")), strict=bool(payload.get("strict", False))),
        "validation.readiness": lambda payload: service.readiness(strict=bool(payload.get("strict", False))),
        "validation.gateway": lambda payload: service.validation.gateway(scope=str(payload.get("scope", "all"))),
        "validation.docs": lambda payload: service.validation.gateway(scope="docs"),
        "validation.contracts": lambda payload: service.validation.gateway(scope="contracts"),
        "miasi.validate": lambda payload: service.miasi_validate(scope=str(payload.get("scope", "all"))),
        "maturity.dashboard": lambda payload: service.maturity_dashboard(write_report=bool(payload.get("write_report", False))),
        "maturity.dashboard_gate": lambda payload: service.maturity_dashboard_gate(write_report=bool(payload.get("write_report", False))),
        "evals.documentation.run": lambda payload: service.eval_run(suite=str(payload.get("suite", "documentation")), case_id=payload.get("case_id")),
        "repo.inventory": lambda payload: service.repo_inventory(),
        "reports.list": lambda payload: service.reports_list(limit=int(payload.get("limit", 50)), severity=payload.get("severity"), status=payload.get("status"), command=payload.get("command")),
        "reports.read": lambda payload: service.reports_read(report_id=str(payload.get("report_id", "")), format=str(payload.get("format", "json")), max_chars=int(payload.get("max_chars", 20000))),
        "approvals.list": lambda payload: service.approvals_list(status=payload.get("status"), tool_id=payload.get("tool_id"), action=payload.get("action"), limit=int(payload.get("limit", 100))),
        "approvals.show": lambda payload: service.approvals_show(approval_id=str(payload.get("approval_id", ""))),
        "approvals.request": lambda payload: service.approvals_request(tool_id=str(payload.get("tool_id", "")), action=str(payload.get("action", "")), subject=str(payload.get("subject", "")), actor=str(payload.get("actor", "ui-local")), reason=str(payload.get("reason", "Requested from UI.")), scope=payload.get("scope"), expires_at=payload.get("expires_at"), ttl_minutes=int(payload.get("ttl_minutes", 60))),
        "approvals.approve": lambda payload: service.approvals_decide(approval_id=str(payload.get("approval_id", "")), decision="approved", actor=str(payload.get("actor", "ui-local")), reason=str(payload.get("reason", "Approved from UI."))),
        "approvals.deny": lambda payload: service.approvals_decide(approval_id=str(payload.get("approval_id", "")), decision="denied", actor=str(payload.get("actor", "ui-local")), reason=str(payload.get("reason", "Denied from UI."))),
        "ui.actions.dry_run": lambda payload: service.ui_action_dry_run(action_id=str(payload.get("action_id", "")), payload=payload),
        "settings.workspace": lambda payload: service.settings_workspace(),
        "settings.providers": lambda payload: service.settings_providers(prefer_example=bool(payload.get("prefer_example", False))),
        "settings.policy": lambda payload: service.settings_policy(),
        "settings.status": lambda payload: service.settings_status(),
        "settings.providers.plan": lambda payload: service.settings_provider_plan(provider_id=str(payload.get("provider_id", "")), changes=dict(payload.get("changes") or {}), actor=str(payload.get("actor", "ui-local")), reason=str(payload.get("reason", "Settings UI plan-only provider change"))),
        "repo.analyze": lambda payload: service.repo_analyze(target=str(payload.get("target", "."))),
        "review.code": lambda payload: service.code_review(target=str(payload.get("target", "."))),
        "refactor.plan": lambda payload: service.refactor_plan(target=str(payload.get("target", ".")), goal=str(payload.get("goal", "")), include_code_review=bool(payload.get("include_code_review", True))),
        "model.providers": lambda payload: service.model_providers(),
        "observability.trace_report": lambda payload: service.trace_report(limit=int(payload.get("limit", 20)), include_events=bool(payload.get("include_events", True)), include_metrics=bool(payload.get("include_metrics", True))),
        "observability.traces": lambda payload: service.trace_report(limit=int(payload.get("limit", 20)), include_events=bool(payload.get("include_events", True)), include_metrics=bool(payload.get("include_metrics", True))),
        "observability.trace_inspect": lambda payload: service.trace_inspect(str(payload.get("trace_id", "")), limit=int(payload.get("limit", 100))),
        "observability.metrics_summary": lambda payload: service.metrics_summary(category=payload.get("category"), limit=int(payload.get("limit", 50))),
        "history.runs": lambda payload: service.history_list(limit=int(payload.get("limit", 10))),
        "maturity.dashboard": lambda payload: service.maturity_dashboard(write_report=bool(payload.get("write_report", False))),
    }


def _domain_summaries() -> list[dict[str, Any]]:
    return [
        {"domain": "workspace", "service": "WorkspaceApplicationService", "status": "implemented-initial", "side_effects": "read_or_dry_run_plan"},
        {"domain": "validation", "service": "ValidationApplicationService", "status": "implemented", "side_effects": "none_or_explicit_report_by_adapter"},
        {"domain": "miasi", "service": "MiasiApplicationService", "status": "implemented", "side_effects": "none"},
        {"domain": "maturity", "service": "MaturityApplicationService", "status": "implemented-initial", "side_effects": "explicit_outputs_reports_only"},
        {"domain": "evals", "service": "EvaluationApplicationService", "status": "implemented-initial", "side_effects": "bounded_local_outputs_for_eval_workdir"},
        {"domain": "repo", "service": "RepoApplicationService", "status": "implemented-initial", "side_effects": "read_only"},
        {"domain": "reports", "service": "ReportsApplicationService", "status": "implemented-initial", "side_effects": "read_only_redacted_outputs_reports"},
        {"domain": "approvals", "service": "ApprovalApplicationService", "status": "implemented-initial", "side_effects": "approval_store_state_transition_audited"},
        {"domain": "settings", "service": "SettingsApplicationService", "status": "implemented-initial", "side_effects": "read_only_and_provider_plan_only"},
        {"domain": "review", "service": "ReviewApplicationService", "status": "implemented-initial", "side_effects": "dry_run_static_analysis"},
        {"domain": "refactor", "service": "RefactorApplicationService", "status": "implemented-initial", "side_effects": "plan_only"},
        {"domain": "model", "service": "ModelApplicationService", "status": "implemented-initial", "side_effects": "mock_or_local_governed_calls"},
        {"domain": "history", "service": "HistoryApplicationService", "status": "implemented-initial", "side_effects": "read_only"},
        {"domain": "observability", "service": "ObservabilityApplicationService", "status": "implemented-initial", "side_effects": "read_or_dry_run_export"},
    ]


def _capabilities() -> list[ServiceCapability]:
    rows = [
        ("workspace.status", "Report workspace initialization/readiness state.", "none", True, "python -m devpilot_core workspace status --json"),
        ("workspace.init_plan", "Build a workspace initialization plan without writing files.", "none", True, "python -m devpilot_core workspace init --json"),
        ("validators.validate_frontmatter", "Legacy alias: validate Markdown frontmatter metadata for one artifact.", "none", True, "python -m devpilot_core validate-frontmatter <path> --json"),
        ("validators.validate_artifact", "Legacy alias: validate Markdown structure against MIPSoftware/MIASI profiles.", "none", True, "python -m devpilot_core validate-artifact <path> --json"),
        ("validators.checklist_pre_code", "Legacy alias: evaluate the executable pre-code checklist gate.", "none", True, "python -m devpilot_core checklist-pre-code --json"),
        ("validators.readiness", "Legacy alias: evaluate readiness gates for baseline artifacts.", "report_when_adapter_requests_it", True, "python -m devpilot_core readiness-check --strict --json"),
        ("validation.frontmatter", "Validate Markdown frontmatter metadata for one artifact.", "none", True, "python -m devpilot_core validate-frontmatter <path> --json"),
        ("validation.artifact", "Validate Markdown structure against MIPSoftware/MIASI profiles.", "none", True, "python -m devpilot_core validate-artifact <path> --json"),
        ("validation.checklist_pre_code", "Evaluate the executable pre-code checklist gate.", "none", True, "python -m devpilot_core checklist-pre-code --json"),
        ("validation.readiness", "Evaluate readiness gates for baseline artifacts.", "report_when_adapter_requests_it", True, "python -m devpilot_core readiness-check --strict --json"),
        ("validation.gateway", "Run docs/contracts/all validation gateway.", "report_when_adapter_requests_it", True, "python -m devpilot_core validate all --json"),
        ("standards.status", "Report local MIPSoftware and MIASI registry status.", "none", True, "python -m devpilot_core standards status --json"),
        ("miasi.validate", "Validate MIASI executable registries.", "none", True, "python -m devpilot_core miasi validate --json"),
        ("evals.documentation.run", "Run offline deterministic evaluation suite.", "local_eval_workdir", True, "python -m devpilot_core eval run --suite documentation --json"),
        ("repo.inventory", "Build local repository inventory.", "none", True, "python -m devpilot_core repo inventory --json"),
        ("reports.list", "List redacted local evidence reports under outputs/reports.", "none", True, "python -m devpilot_core reports list --json"),
        ("reports.read", "Read one redacted local evidence report by id and format.", "none", True, "python -m devpilot_core reports read <report_id> --json"),
        ("approvals.list", "List local human approval records for Approval Center.", "read_only", True, "python -m devpilot_core approval list --json"),
        ("approvals.show", "Show one local approval record by id.", "read_only", True, "python -m devpilot_core approval show <approval_id> --json"),
        ("approvals.request", "Create an audited local approval request from Approval Center.", "approval_store_write", False, "python -m devpilot_core approval request --tool <tool> --action <action> --subject <subject> --reason <reason> --actor <actor> --json"),
        ("approvals.approve", "Approve one local approval request through controlled transition.", "approval_store_write", False, "python -m devpilot_core approval approve <approval_id> --actor <actor> --reason <reason> --json"),
        ("approvals.deny", "Deny one local approval request through controlled transition.", "approval_store_write", False, "python -m devpilot_core approval deny <approval_id> --actor <actor> --reason <reason> --json"),
        ("ui.actions.dry_run", "Launch safe UI actions in read-only/dry-run mode only.", "dry_run_only", True, "UI Action Launcher: readiness/code-review/refactor-plan"),
        ("settings.workspace", "Read workspace project settings without exposing filesystem writes.", "none", True, "Settings UI: workspace panel"),
        ("settings.providers", "Read provider settings with secret redaction and external providers disabled by default.", "none", True, "Settings UI: providers panel"),
        ("settings.policy", "Read local policy and MIASI policy matrix summaries without editing policy.", "none", True, "Settings UI: policy panel"),
        ("settings.providers.plan", "Create a provider configuration change plan without writing .devpilot/providers.yaml.", "plan_only", True, "Settings UI: provider plan-only editor"),
        ("repo.analyze", "Run read-only repository analysis.", "none", True, "python -m devpilot_core repo analyze --json"),
        ("review.code", "Run deterministic code review in dry-run mode.", "none", True, "python -m devpilot_core code-review . --json"),
        ("refactor.plan", "Create plan-only safe refactor proposal.", "none", True, "python -m devpilot_core refactor-plan . --json"),
        ("model.providers", "List governed model providers without external API calls.", "none", True, "python -m devpilot_core model providers --json"),
        ("model.health", "Check provider health through governed model router.", "localhost_or_none", True, "python -m devpilot_core model health --provider mock --json"),
        ("model.capabilities", "Build static model capability matrix.", "none", True, "python -m devpilot_core model capabilities --json"),
        ("history.runs", "List local command history from LocalStore.", "none", True, "python -m devpilot_core history list --json"),
        ("observability.trace_report", "Read bounded local trace report.", "none", True, "python -m devpilot_core trace report --json"),
        ("observability.trace_inspect", "Inspect one trace id as a span tree.", "none", True, "python -m devpilot_core trace inspect <trace_id> --json"),
        ("observability.metrics_summary", "Read bounded local metrics summary.", "none", True, "python -m devpilot_core metrics summary --json"),
        ("observability.agentops_status", "Evaluate AgentOps quality gate.", "report_when_adapter_requests_it", True, "python -m devpilot_core agentops status --json"),
        ("maturity.dashboard", "Generate the local POST-H maturity dashboard from evidence.", "explicit_outputs_reports_only", True, "python -m devpilot_core maturity dashboard --json"),
        ("maturity.dashboard_gate", "Run the POST-H-002 maturity dashboard quality gate.", "explicit_outputs_reports_only", True, "python -m devpilot_core maturity gate --json"),
    ]
    return [
        ServiceCapability(
            operation=operation,
            description=description,
            side_effect=side_effect,
            dry_run_default=dry_run_default,
            command_equivalent=command_equivalent,
        )
        for operation, description, side_effect, dry_run_default, command_equivalent in rows
    ]


def _routes() -> list[InterfaceRouteContract]:
    route_specs = [
        ("APP-ROUTE-001", "GET", "/api/v1/workspace/status", "workspace.status", ["Active local API MVP route in FUNC-SPRINT-67."]),
        ("APP-ROUTE-002", "POST", "/api/v1/validation/frontmatter", "validation.frontmatter", ["Active local API MVP route for Web UI validators."]),
        ("APP-ROUTE-003", "POST", "/api/v1/validation/artifact", "validation.artifact", ["Active local API MVP route for Web UI validators."]),
        ("APP-ROUTE-004", "POST", "/api/v1/validation/readiness", "validation.readiness", ["Active local API MVP route; report writes remain explicit in lower layers."]),
        ("APP-ROUTE-005", "GET", "/api/v1/miasi/status", "miasi.validate", ["Active read-only MIASI status projection."]),
        ("APP-ROUTE-006", "GET", "/api/v1/repo/inventory", "repo.inventory", ["Active read-only repository summary route."]),
        ("APP-ROUTE-007", "POST", "/api/v1/review/code", "review.code", ["Active dry-run review route; no mutation."]),
        ("APP-ROUTE-008", "POST", "/api/v1/refactor/plan", "refactor.plan", ["Active plan-only route; no patch execution."]),
        ("APP-ROUTE-009", "GET", "/api/v1/model/providers", "model.providers", ["Active governed model provider listing; no external API call."]),
        ("APP-ROUTE-010", "GET", "/api/v1/observability/traces", "observability.trace_report", ["Active bounded local trace viewer route."]),
        ("APP-ROUTE-011", "GET", "/api/v1/observability/metrics", "observability.metrics_summary", ["Active bounded local metric viewer route."]),
        ("APP-ROUTE-012", "GET", "/api/v1/history/runs", "history.runs", ["Active bounded LocalStore history route."]),
        ("APP-ROUTE-013", "GET", "/api/v1/application/contract", "app.contract", ["Active bootstrap route for API/Web UI clients."]),
        ("APP-ROUTE-014", "GET", "/api/v1/standards/status", "standards.status", ["Active standards status route added by FUNC-SPRINT-67."]),
        ("APP-ROUTE-015", "GET", "/api/v1/reports", "reports.list", ["Active Sprint 70 report index route; API reads outputs/reports, UI never reads filesystem."]),
        ("APP-ROUTE-016", "GET", "/api/v1/reports/{report_id}", "reports.read", ["Active Sprint 70 report detail route with redaction and safe basename validation."]),
        ("APP-ROUTE-017", "GET", "/api/v1/traces", "observability.trace_report", ["Active Sprint 70 trace index route; bounded and empty-safe."]),
        ("APP-ROUTE-018", "GET", "/api/v1/traces/{trace_id}", "observability.trace_inspect", ["Active Sprint 70 trace detail route rendered as span tree."]),
        ("APP-ROUTE-019", "GET", "/api/v1/metrics/summary", "observability.metrics_summary", ["Active Sprint 70 metrics summary alias for visual dashboard."]),
        ("APP-ROUTE-020", "GET", "/api/v1/approvals", "approvals.list", ["Active Sprint 71 Approval Center route; lists approval records through ApprovalService."]),
        ("APP-ROUTE-021", "GET", "/api/v1/approvals/{approval_id}", "approvals.show", ["Active Sprint 71 approval detail route with safe local token policy."]),
        ("APP-ROUTE-022", "POST", "/api/v1/approvals/request", "approvals.request", ["Active Sprint 71 audited approval request route; writes only approval store records."]),
        ("APP-ROUTE-023", "POST", "/api/v1/approvals/{approval_id}/approve", "approvals.approve", ["Active Sprint 71 controlled approval transition route."]),
        ("APP-ROUTE-024", "POST", "/api/v1/approvals/{approval_id}/deny", "approvals.deny", ["Active Sprint 71 controlled denial transition route."]),
        ("APP-ROUTE-025", "POST", "/api/v1/actions/dry-run", "ui.actions.dry_run", ["Active Sprint 71 dry-run Action Launcher route; critical actions remain blocked from UI."]),
        ("APP-ROUTE-026", "GET", "/api/v1/settings/workspace", "settings.workspace", ["Active Sprint 72 Settings route; read-only workspace projection."]),
        ("APP-ROUTE-027", "GET", "/api/v1/settings/providers", "settings.providers", ["Active Sprint 72 Settings route; providers are redacted and read-only."]),
        ("APP-ROUTE-028", "GET", "/api/v1/settings/policy", "settings.policy", ["Active Sprint 72 Settings route; policy summary is read-only."]),
        ("APP-ROUTE-029", "POST", "/api/v1/settings/providers/plan", "settings.providers.plan", ["Active Sprint 72 Settings route; provider edits are plan-only and never write files."]),
    ]
    return [InterfaceRouteContract(route_id=rid, method=method, path=path, operation=operation, status="secured-initial", notes=notes) for rid, method, path, operation, notes in route_specs]
