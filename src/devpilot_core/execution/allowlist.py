from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from devpilot_core.cli_models import Finding, Severity

from .models import CommandAllowlistEntry

DEFAULT_ALLOWLIST_RELATIVE_PATH = Path(".devpilot/execution/command_allowlist.json")


def _python_aliases() -> tuple[str, ...]:
    aliases = {"python", "python.exe", "python3", "python3.exe", "python3.11", "python3.12", "py", "py.exe"}
    executable_name = Path(sys.executable).name
    if executable_name:
        aliases.add(executable_name)
    return tuple(sorted(aliases))


DEFAULT_ALLOWLIST: dict[str, Any] = {
    "schema_version": "1.0",
    "created_by": "FUNC-SPRINT-31",
    "description": "Local command allowlist for SafeSubprocessRunner. It is intentionally narrow and local-first.",
    "commands": [
        {
            "command_id": "python.pytest",
            "executable": "python",
            "executable_aliases": list(_python_aliases()),
            "args_prefix": ["-m", "pytest"],
            "max_timeout_seconds": 120,
            "description": "Allow controlled pytest invocation as prerequisite for tests.run.",
        },
        {
            "command_id": "git.apply.check",
            "executable": "git",
            "executable_aliases": ["git", "git.exe"],
            "args_prefix": ["apply", "--check"],
            "max_timeout_seconds": 30,
            "description": "Allow read-only patch applicability checks with git apply --check; never applies patches.",
        }
    ],
}


@dataclass(frozen=True)
class AllowlistMatch:
    """Result of matching command arguments against the local allowlist."""

    allowed: bool
    entry: CommandAllowlistEntry | None
    finding: Finding | None = None


class CommandAllowlist:
    """Load and evaluate the local SafeSubprocessRunner command allowlist."""

    def __init__(self, root: Path, *, path: str | Path | None = None) -> None:
        self.root = root.resolve()
        self.path = self._resolve_path(path or DEFAULT_ALLOWLIST_RELATIVE_PATH)
        self.entries = self._load_entries()

    def match(self, args: Sequence[str]) -> AllowlistMatch:
        if not args:
            return AllowlistMatch(
                allowed=False,
                entry=None,
                finding=Finding(
                    id="SAFE_SUBPROCESS_EMPTY_COMMAND",
                    message="SafeSubprocessRunner blocked an empty command.",
                    severity=Severity.BLOCK,
                ),
            )
        executable_name = Path(str(args[0])).name
        remaining = tuple(str(item) for item in args[1:])
        for entry in self.entries:
            aliases = {entry.executable, *entry.executable_aliases}
            if executable_name not in aliases:
                continue
            if len(remaining) < len(entry.args_prefix):
                continue
            if tuple(remaining[: len(entry.args_prefix)]) == entry.args_prefix:
                return AllowlistMatch(allowed=True, entry=entry)
        return AllowlistMatch(
            allowed=False,
            entry=None,
            finding=Finding(
                id="SAFE_SUBPROCESS_COMMAND_NOT_ALLOWLISTED",
                message="SafeSubprocessRunner blocked a command that is not in the local allowlist.",
                severity=Severity.BLOCK,
                metadata={
                    "executable": executable_name,
                    "args_prefix_attempted": list(remaining[:3]),
                    "allowlist_path": self.relative_path,
                    "commands_total": len(self.entries),
                },
            ),
        )

    @property
    def relative_path(self) -> str:
        try:
            return str(self.path.relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(self.path).replace("\\", "/")

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.relative_path,
            "commands_total": len(self.entries),
            "commands": [entry.to_dict() for entry in self.entries],
            "fallback_used": not self.path.exists(),
        }

    def _resolve_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()

    def _load_entries(self) -> list[CommandAllowlistEntry]:
        payload = DEFAULT_ALLOWLIST
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    payload = loaded
            except json.JSONDecodeError:
                payload = DEFAULT_ALLOWLIST
        entries: list[CommandAllowlistEntry] = []
        for item in payload.get("commands", []):
            if isinstance(item, dict):
                entry = CommandAllowlistEntry.from_dict(item)
                if entry.command_id and entry.executable and entry.args_prefix:
                    entries.append(entry)
        if not entries:
            entries = [CommandAllowlistEntry.from_dict(item) for item in DEFAULT_ALLOWLIST["commands"]]
        return entries
