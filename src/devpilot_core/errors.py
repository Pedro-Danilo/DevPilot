from __future__ import annotations

from dataclasses import dataclass

from .cli_models import ExitCode


@dataclass(frozen=True)
class DevPilotError(Exception):
    """Base exception for controlled DevPilot failures.

    FUNC-SPRINT-01 introduces this class so future commands can fail with
    predictable exit codes instead of leaking raw stack traces to users.
    """

    message: str
    exit_code: ExitCode = ExitCode.ERROR

    def __str__(self) -> str:
        return self.message
