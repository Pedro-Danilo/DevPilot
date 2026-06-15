from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.standards.registry import build_standards_status_result
from devpilot_core.validation import ValidationGateway
from devpilot_core.validators.artifact import validate_artifact_file
from devpilot_core.validators.checklist import validate_precode_checklist
from devpilot_core.validators.frontmatter import validate_frontmatter_file
from devpilot_core.validators.readiness import build_readiness_result, build_strict_readiness_result


def _resolve_path(root: Path, path: str | Path, *, enforce_workspace_paths: bool = False) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    if enforce_workspace_paths:
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"ApplicationService only accepts paths inside the workspace: {str(path).replace('\\\\', '/')}") from exc
    return candidate


class ValidationApplicationService:
    """Application-facing validation facade for API/UI-safe reuse.

    Purpose:
        Keep future API local and Web UI clients from importing individual
        validators, readiness gates, Standards Registry or ValidationGateway.

    Functioning:
        Delegates to existing deterministic validators and returns the original
        CommandResult contracts. Optional report writing remains outside this
        service and is handled by CLI/API adapters.

    Integration:
        Composed by ApplicationService v2 and exposed through contract-only
        routes in Sprint 65. No HTTP server or frontend is implemented here.
    """

    def __init__(self, root: Path, *, enforce_workspace_paths: bool = False) -> None:
        self.root = root.resolve()
        self.enforce_workspace_paths = enforce_workspace_paths

    def validate_frontmatter(self, path: str | Path, *, strict: bool = False) -> CommandResult:
        target = _resolve_path(self.root, path, enforce_workspace_paths=self.enforce_workspace_paths)
        return validate_frontmatter_file(target, root=self.root, strict=strict)

    def validate_artifact(self, path: str | Path, *, strict: bool = False) -> CommandResult:
        target = _resolve_path(self.root, path, enforce_workspace_paths=self.enforce_workspace_paths)
        return validate_artifact_file(target, root=self.root, strict=strict)

    def checklist_pre_code(self, *, strict: bool = True) -> CommandResult:
        return validate_precode_checklist(self.root, strict=strict)

    def readiness(self, *, strict: bool = False) -> CommandResult:
        return build_strict_readiness_result(self.root) if strict else build_readiness_result(self.root)

    def standards_status(self) -> CommandResult:
        return build_standards_status_result(self.root)

    def gateway(self, scope: str = "all") -> CommandResult:
        return ValidationGateway(self.root).validate_scope(scope)
