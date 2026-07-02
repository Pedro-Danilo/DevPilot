"""Explicit CLI command handler modules for POST-H-006 migrations.

The package contains small, domain-oriented handlers that build
``CommandResult`` instances without printing, dispatching or dynamically loading
code. ``src/devpilot_core/cli.py`` remains the public parser/UX boundary while
micro-sprints migrate implementation logic incrementally.
"""

from .workspace import handle_workspace_bootstrap, handle_workspace_init, handle_workspace_status
from .validation import handle_validate_scope

__all__ = [
    "handle_validate_scope",
    "handle_workspace_bootstrap",
    "handle_workspace_init",
    "handle_workspace_status",
]
