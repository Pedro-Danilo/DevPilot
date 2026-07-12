from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.sensitive_capabilities.models import SensitiveCapabilityOptions
from devpilot_core.sensitive_capabilities.validator import ConnectorWriteAdrValidator


class SensitiveCapabilityAdrGate:
    """Quality gate for POST-H-034 sensitive capability ADR boundaries.

    POST-H-034-A initially validates connector.write only. The gate is designed
    to grow across POST-H-034-B/E while preserving current no-go flags by
    default.
    """

    def __init__(self, root: Path, *, options: SensitiveCapabilityOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SensitiveCapabilityOptions()

    def run(self) -> CommandResult:
        return ConnectorWriteAdrValidator(self.root, options=self.options).validate()
