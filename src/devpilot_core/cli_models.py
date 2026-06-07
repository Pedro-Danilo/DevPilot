from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Severity levels used by DevPilot findings.

    The enum is intentionally small for FUNC-SPRINT-01. Later sprints can map
    these values to MIPSoftware/MIASI gate severities without changing the CLI
    contract.
    """

    INFO = "info"
    WARNING = "warning"
    FAIL = "fail"
    BLOCK = "block"
    ERROR = "error"


class ExitCode(int, Enum):
    """Stable process exit codes for DevPilot CLI commands."""

    PASS = 0
    FAIL = 1
    BLOCK = 2
    ERROR = 3


@dataclass(frozen=True)
class Finding:
    """A normalized validation or diagnostic finding emitted by a command."""

    id: str
    message: str
    severity: Severity = Severity.INFO
    path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "message": self.message,
            "severity": self.severity.value,
        }
        if self.path is not None:
            data["path"] = self.path
        if self.metadata:
            data["metadata"] = self.metadata
        return data


@dataclass(frozen=True)
class CommandResult:
    """Common output contract for DevPilot CLI commands.

    All future commands should return this object or an object that can be
    adapted to this shape. It separates command execution from presentation,
    making JSON output, human-readable summaries and test assertions consistent.
    """

    command: str
    ok: bool
    exit_code: ExitCode
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "ok": self.ok,
            "exit_code": int(self.exit_code),
            "message": self.message,
            "data": self.data,
            "findings": [finding.to_dict() for finding in self.findings],
        }


def exit_code_for_findings(findings: list[Finding], default_ok: bool = True) -> ExitCode:
    """Derive an exit code from findings using DevPilot severity rules."""

    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS if default_ok else ExitCode.FAIL
