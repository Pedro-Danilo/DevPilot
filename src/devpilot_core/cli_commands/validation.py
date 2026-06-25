from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.validation import ValidationGateway


def handle_validate_scope(root: Path, scope: str) -> CommandResult:
    """Build the result for ``validate docs/contracts/all``.

    The handler intentionally delegates to ``ValidationGateway`` and performs no
    printing, event persistence, dynamic dispatch or side-effect beyond whatever
    the gateway already did before POST-H-006-C. ``cli.py`` remains responsible
    for UX compatibility, optional report writing and observability hooks.
    """

    return ValidationGateway(root).validate_scope(scope)
