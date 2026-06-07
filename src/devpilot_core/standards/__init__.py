"""Standards registry package for DevPilot Local.

FUNC-SPRINT-04 introduces local discovery of MIPSoftware and MIASI stored
inside docs/standards. The package is intentionally deterministic and
local-first: it does not call external services and does not require API keys.
"""

from .catalog import REQUIRED_PROJECT_ARTIFACTS, REQUIRED_STANDARDS
from .registry import StandardsRegistry, build_standards_status_result

__all__ = [
    "REQUIRED_PROJECT_ARTIFACTS",
    "REQUIRED_STANDARDS",
    "StandardsRegistry",
    "build_standards_status_result",
]
