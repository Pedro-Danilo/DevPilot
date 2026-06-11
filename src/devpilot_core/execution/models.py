from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SafeExecutionStatus(str, Enum):
    """Canonical status values for controlled local command execution."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True)
class CommandAllowlistEntry:
    """One command shape allowed by SafeSubprocessRunner.

    The runner matches commands by executable basename/alias plus an argument
    prefix. Additional suffix arguments are allowed only after the prefix has
    matched, which keeps the first implementation simple and auditable.
    """

    command_id: str
    executable: str
    args_prefix: tuple[str, ...]
    executable_aliases: tuple[str, ...] = field(default_factory=tuple)
    max_timeout_seconds: int = 60
    description: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CommandAllowlistEntry":
        return cls(
            command_id=str(payload.get("command_id", "")).strip(),
            executable=str(payload.get("executable", "")).strip(),
            executable_aliases=tuple(str(item).strip() for item in payload.get("executable_aliases", []) if str(item).strip()),
            args_prefix=tuple(str(item) for item in payload.get("args_prefix", [])),
            max_timeout_seconds=int(payload.get("max_timeout_seconds", 60)),
            description=str(payload.get("description", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "executable": self.executable,
            "executable_aliases": list(self.executable_aliases),
            "args_prefix": list(self.args_prefix),
            "max_timeout_seconds": self.max_timeout_seconds,
            "description": self.description,
        }


@dataclass(frozen=True)
class SafeSubprocessReport:
    """Serializable execution report returned by SafeSubprocessRunner."""

    command_id: str | None
    args: tuple[str, ...]
    cwd: str
    returncode: int | None
    duration_ms: int
    timed_out: bool
    stdout: str
    stderr: str
    stdout_truncated: bool
    stderr_truncated: bool
    redactions: int
    max_output_chars: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "args": list(self.args),
            "cwd": self.cwd,
            "returncode": self.returncode,
            "duration_ms": self.duration_ms,
            "timed_out": self.timed_out,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "stdout_truncated": self.stdout_truncated,
            "stderr_truncated": self.stderr_truncated,
            "redactions": self.redactions,
            "max_output_chars": self.max_output_chars,
        }
