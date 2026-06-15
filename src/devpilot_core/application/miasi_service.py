from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.miasi import MiasiRegistryValidator


class MiasiApplicationService:
    """Application-facing MIASI registry facade."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.validator = MiasiRegistryValidator(self.root)

    def validate(self, *, scope: str = "all") -> CommandResult:
        normalized = scope.strip().lower() or "all"
        if normalized == "all":
            return self.validator.validate_all()
        if normalized == "agents":
            return self.validator.validate_agents()
        if normalized == "tools":
            return self.validator.validate_tools()
        if normalized in {"policy", "policies", "policy-matrix", "policy_matrix"}:
            return self.validator.validate_policy_matrix()
        return self.validator.validate_all()
