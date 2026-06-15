from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

from .dtos import ApplicationRequest, ApplicationResponse, InterfaceRouteContract, ServiceCapability
from .evals_service import EvaluationApplicationService
from .history_service import HistoryApplicationService
from .miasi_service import MiasiApplicationService
from .model_service import ModelApplicationService
from .observability_service import ObservabilityApplicationService
from .refactor_service import RefactorApplicationService
from .repo_service import RepoApplicationService
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
        self.evals = EvaluationApplicationService(self.root)
        self.repo = RepoApplicationService(self.root)
        self.review = ReviewApplicationService(self.root)
        self.refactor = RefactorApplicationService(self.root)
        self.model = ModelApplicationService(self.root)
        self.history = HistoryApplicationService(self.root)
        self.observability = ObservabilityApplicationService(self.root)

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

    def eval_run(self, *, suite: str = "documentation", case_id: str | None = None) -> CommandResult:
        return self.evals.run_documentation(suite=suite, case_id=case_id)

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

    def trace_report(self, *, limit: int = 20, include_events: bool = True, include_metrics: bool = True) -> CommandResult:
        return self.observability.trace_report(limit=limit, include_events=include_events, include_metrics=include_metrics)

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
                "ui_implemented": False,
                "api_implemented": False,
                "visual_strategy": "web_ui_first",
                "api_local_planned": True,
                "web_ui_local_planned": True,
                "web_ui_real_future": True,
                "desktop_deferred": True,
                "desktop_ready_for_shell": False,
                "web_ready_for_shell": True,
                "external_api_required": False,
                "application_service_v2": True,
                "domain_facades_enabled": True,
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
                "FUNC-SPRINT-65 exposes domain application services for future API local and Web UI integration.",
                "No HTTP server, Web frontend, Desktop shell, network listener or external API dependency is implemented by this sprint.",
                "Future route handlers must call ApplicationService/DomainService methods instead of importing DevPilot Core modules directly.",
                "Operations with side effects remain dry-run/report-only or must later be bound to PolicyEngine and Approval Workflow.",
            ],
        }
        return CommandResult(
            command="app contract",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Application service v2 contract is available for CLI, future API local and Web UI shells; desktop is deferred.",
            data=data,
            findings=[
                Finding(
                    id="APP_CONTRACT_V2_PASS",
                    message="ApplicationService v2 exposes domain facades and serializable route contracts without implementing API/UI.",
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
        "validators.validate_frontmatter": lambda payload: service.validate_frontmatter(str(payload.get("path", "")), strict=bool(payload.get("strict", False))),
        "validators.validate_artifact": lambda payload: service.validate_artifact(str(payload.get("path", "")), strict=bool(payload.get("strict", False))),
        "validators.readiness": lambda payload: service.readiness(strict=bool(payload.get("strict", False))),
        "validation.frontmatter": lambda payload: service.validate_frontmatter(str(payload.get("path", "")), strict=bool(payload.get("strict", False))),
        "validation.artifact": lambda payload: service.validate_artifact(str(payload.get("path", "")), strict=bool(payload.get("strict", False))),
        "validation.readiness": lambda payload: service.readiness(strict=bool(payload.get("strict", False))),
        "validation.gateway": lambda payload: service.validation.gateway(scope=str(payload.get("scope", "all"))),
        "miasi.validate": lambda payload: service.miasi_validate(scope=str(payload.get("scope", "all"))),
        "evals.documentation.run": lambda payload: service.eval_run(suite=str(payload.get("suite", "documentation")), case_id=payload.get("case_id")),
        "repo.inventory": lambda payload: service.repo_inventory(),
        "repo.analyze": lambda payload: service.repo_analyze(target=str(payload.get("target", "."))),
        "review.code": lambda payload: service.code_review(target=str(payload.get("target", "."))),
        "refactor.plan": lambda payload: service.refactor_plan(target=str(payload.get("target", ".")), goal=str(payload.get("goal", "")), include_code_review=bool(payload.get("include_code_review", True))),
        "model.providers": lambda payload: service.model_providers(),
        "observability.trace_report": lambda payload: service.trace_report(limit=int(payload.get("limit", 20)), include_events=bool(payload.get("include_events", True)), include_metrics=bool(payload.get("include_metrics", True))),
        "observability.metrics_summary": lambda payload: service.metrics_summary(category=payload.get("category"), limit=int(payload.get("limit", 50))),
        "history.runs": lambda payload: service.history_list(limit=int(payload.get("limit", 10))),
    }


def _domain_summaries() -> list[dict[str, Any]]:
    return [
        {"domain": "workspace", "service": "WorkspaceApplicationService", "status": "implemented-initial", "side_effects": "read_or_dry_run_plan"},
        {"domain": "validation", "service": "ValidationApplicationService", "status": "implemented", "side_effects": "none_or_explicit_report_by_adapter"},
        {"domain": "miasi", "service": "MiasiApplicationService", "status": "implemented", "side_effects": "none"},
        {"domain": "evals", "service": "EvaluationApplicationService", "status": "implemented-initial", "side_effects": "bounded_local_outputs_for_eval_workdir"},
        {"domain": "repo", "service": "RepoApplicationService", "status": "implemented-initial", "side_effects": "read_only"},
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
        ("repo.analyze", "Run read-only repository analysis.", "none", True, "python -m devpilot_core repo analyze --json"),
        ("review.code", "Run deterministic code review in dry-run mode.", "none", True, "python -m devpilot_core code-review . --json"),
        ("refactor.plan", "Create plan-only safe refactor proposal.", "none", True, "python -m devpilot_core refactor-plan . --json"),
        ("model.providers", "List governed model providers without external API calls.", "none", True, "python -m devpilot_core model providers --json"),
        ("model.health", "Check provider health through governed model router.", "localhost_or_none", True, "python -m devpilot_core model health --provider mock --json"),
        ("model.capabilities", "Build static model capability matrix.", "none", True, "python -m devpilot_core model capabilities --json"),
        ("history.runs", "List local command history from LocalStore.", "none", True, "python -m devpilot_core history list --json"),
        ("observability.trace_report", "Read bounded local trace report.", "none", True, "python -m devpilot_core trace report --json"),
        ("observability.metrics_summary", "Read bounded local metrics summary.", "none", True, "python -m devpilot_core metrics summary --json"),
        ("observability.agentops_status", "Evaluate AgentOps quality gate.", "report_when_adapter_requests_it", True, "python -m devpilot_core agentops status --json"),
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
        ("APP-ROUTE-001", "GET", "/api/v1/workspace/status", "workspace.status", ["Future API local route; not active HTTP in Sprint 65."]),
        ("APP-ROUTE-002", "POST", "/api/v1/validation/frontmatter", "validation.frontmatter", ["Future API local route for Web UI validators."]),
        ("APP-ROUTE-003", "POST", "/api/v1/validation/artifact", "validation.artifact", ["Future API local route for Web UI validators."]),
        ("APP-ROUTE-004", "POST", "/api/v1/validation/readiness", "validation.readiness", ["Future route must keep report writes explicit."]),
        ("APP-ROUTE-005", "GET", "/api/v1/miasi/status", "miasi.validate", ["Read-only MIASI status projection."]),
        ("APP-ROUTE-006", "GET", "/api/v1/repo/inventory", "repo.inventory", ["Read-only repository summary route."]),
        ("APP-ROUTE-007", "POST", "/api/v1/review/code", "review.code", ["Dry-run review route; no mutation."]),
        ("APP-ROUTE-008", "POST", "/api/v1/refactor/plan", "refactor.plan", ["Plan-only route; no patch execution."]),
        ("APP-ROUTE-009", "GET", "/api/v1/model/providers", "model.providers", ["Governed model provider listing; no external API call."]),
        ("APP-ROUTE-010", "GET", "/api/v1/observability/traces", "observability.trace_report", ["Bounded local trace viewer route."]),
        ("APP-ROUTE-011", "GET", "/api/v1/observability/metrics", "observability.metrics_summary", ["Bounded local metric viewer route."]),
        ("APP-ROUTE-012", "GET", "/api/v1/history/runs", "history.runs", ["Bounded LocalStore history route."]),
        ("APP-ROUTE-013", "GET", "/api/v1/application/contract", "app.contract", ["Bootstrap route for future API/Web UI clients."]),
    ]
    return [InterfaceRouteContract(route_id=rid, method=method, path=path, operation=operation, notes=notes) for rid, method, path, operation, notes in route_specs]
