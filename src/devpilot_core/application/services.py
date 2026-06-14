from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.standards.registry import build_standards_status_result
from devpilot_core.validators.artifact import validate_artifact_file
from devpilot_core.validators.checklist import validate_precode_checklist
from devpilot_core.validators.frontmatter import validate_frontmatter_file
from devpilot_core.validators.readiness import build_readiness_result, build_strict_readiness_result

from .dtos import ApplicationResponse, InterfaceRouteContract, ServiceCapability


def _display_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


class ApplicationService:
    """Application-service facade for CLI, API local and Web UI shells.

    FUNC-SPRINT-18 moves validator orchestration behind an application-service
    boundary so presentation layers do not need to know individual validator
    modules. The service is local-only, deterministic and has no external API
    dependency. It returns CommandResult for backward compatibility and can also
    expose ApplicationResponse DTOs for future UI transports.
    """

    def __init__(self, root: Path, *, enforce_workspace_paths: bool = False) -> None:
        self.root = root.resolve()
        self.enforce_workspace_paths = enforce_workspace_paths

    def validate_frontmatter(self, path: str | Path, *, strict: bool = False) -> CommandResult:
        target = self._resolve_path(path)
        return validate_frontmatter_file(target, root=self.root, strict=strict)

    def validate_artifact(self, path: str | Path, *, strict: bool = False) -> CommandResult:
        target = self._resolve_path(path)
        return validate_artifact_file(target, root=self.root, strict=strict)

    def checklist_pre_code(self, *, strict: bool = True) -> CommandResult:
        return validate_precode_checklist(self.root, strict=strict)

    def readiness(self, *, strict: bool = False) -> CommandResult:
        return build_strict_readiness_result(self.root) if strict else build_readiness_result(self.root)

    def standards_status(self) -> CommandResult:
        return build_standards_status_result(self.root)

    def as_application_response(self, result: CommandResult, *, operation: str | None = None) -> ApplicationResponse:
        return ApplicationResponse.from_command_result(result, operation=operation)

    def application_contract(self) -> CommandResult:
        capabilities = _capabilities()
        routes = _routes()
        data: dict[str, Any] = {
            "summary": {
                "contract": "DevPilotApplicationServiceContract",
                "schema_version": "1.0",
                "capabilities_total": len(capabilities),
                "routes_total": len(routes),
                "ui_implemented": False,
                "visual_strategy": "web_ui_first",
                "api_local_planned": True,
                "web_ui_local_planned": True,
                "web_ui_real_future": True,
                "desktop_deferred": True,
                "desktop_ready_for_shell": False,
                "web_ready_for_shell": True,
                "external_api_required": False,
            },
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
                "FUNC-SPRINT-18 prepares internal contracts only; it does not implement API local or Web UI.",
                "CLI, future API local and Web UI shells must consume DevPilot Core through ApplicationService boundaries.",
                "No server, browser window, IPC channel or frontend build is started by this sprint.",
            ],
        }
        return CommandResult(
            command="app contract",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Application service contract is available for CLI, future API local and Web UI shells; desktop is deferred.",
            data=data,
            findings=[
                Finding(
                    id="APP_CONTRACT_PASS",
                    message="Application services expose serializable DTOs and logical API/Web UI route contracts without implementing UI; desktop is deferred.",
                    severity=Severity.INFO,
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
                # Future UI shells should enable this boundary to reject
                # workspace escapes before invoking lower-level validators. The
                # CLI keeps compatibility with historical absolute-path tests.
                raise ValueError(f"ApplicationService only accepts paths inside the workspace: {_display_path(path)}") from exc
        return candidate


def _capabilities() -> list[ServiceCapability]:
    return [
        ServiceCapability(
            operation="validators.validate_frontmatter",
            description="Validate Markdown frontmatter metadata for one artifact.",
            side_effect="none",
            dry_run_default=True,
            command_equivalent="python -m devpilot_core validate-frontmatter <path> --json",
        ),
        ServiceCapability(
            operation="validators.validate_artifact",
            description="Validate Markdown structure against MIPSoftware/MIASI profiles.",
            side_effect="none",
            dry_run_default=True,
            command_equivalent="python -m devpilot_core validate-artifact <path> --json",
        ),
        ServiceCapability(
            operation="validators.checklist_pre_code",
            description="Evaluate the executable pre-code checklist gate.",
            side_effect="none",
            dry_run_default=True,
            command_equivalent="python -m devpilot_core checklist-pre-code --json",
        ),
        ServiceCapability(
            operation="validators.readiness",
            description="Evaluate readiness gates for pre-code baseline artifacts.",
            side_effect="report_when_cli_requests_it",
            dry_run_default=True,
            command_equivalent="python -m devpilot_core readiness-check --strict --json",
        ),
        ServiceCapability(
            operation="standards.status",
            description="Report local MIPSoftware and MIASI registry status.",
            side_effect="none",
            dry_run_default=True,
            command_equivalent="python -m devpilot_core standards status --json",
        ),
    ]


def _routes() -> list[InterfaceRouteContract]:
    return [
        InterfaceRouteContract(
            route_id="APP-ROUTE-001",
            method="POST",
            path="/application/validators/frontmatter",
            operation="validators.validate_frontmatter",
            notes=["Future API local route for Web UI; not active HTTP in Sprint 64."],
        ),
        InterfaceRouteContract(
            route_id="APP-ROUTE-002",
            method="POST",
            path="/application/validators/artifact",
            operation="validators.validate_artifact",
            notes=["Future API local route for Web UI; not active HTTP in Sprint 64."],
        ),
        InterfaceRouteContract(
            route_id="APP-ROUTE-003",
            method="POST",
            path="/application/validators/readiness",
            operation="validators.readiness",
            notes=["Future shell must keep report writes explicit."],
        ),
        InterfaceRouteContract(
            route_id="APP-ROUTE-004",
            method="GET",
            path="/application/contract",
            operation="app.contract",
            notes=["Used by future API/Web UI bootstrap screens to discover supported capabilities; desktop remains deferred."],
        ),
    ]
