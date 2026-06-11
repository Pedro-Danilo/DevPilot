from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Sequence

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy.path_guard import PathGuard
from devpilot_core.policy.secrets import SecretGuard

from .allowlist import CommandAllowlist
from .models import SafeSubprocessReport

DEFAULT_MAX_OUTPUT_CHARS = 4000


class SafeSubprocessRunner:
    """Execute local allowlisted commands without shell and with audit evidence.

    FUNC-SPRINT-31 introduces this runner as a prerequisite for `tests.run`.
    It intentionally does not expose arbitrary command execution. All calls are
    constrained by command allowlist, workspace-root cwd, timeout, output
    truncation and SecretGuard redaction.
    """

    def __init__(
        self,
        root: Path,
        *,
        allowlist: CommandAllowlist | None = None,
        max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
    ) -> None:
        self.root = root.resolve()
        self.allowlist = allowlist or CommandAllowlist(self.root)
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()
        self.max_output_chars = max(256, int(max_output_chars))

    def run(
        self,
        args: Sequence[str] | str,
        *,
        cwd: str | Path = ".",
        timeout_seconds: int | None = None,
    ) -> CommandResult:
        """Run a command if it passes all local execution controls."""

        normalized = self._normalize_args(args)
        if normalized is None:
            return self._blocked(
                "SAFE_SUBPROCESS_ARGS_NOT_LIST",
                "SafeSubprocessRunner requires a list/tuple of command arguments; shell strings are blocked.",
                metadata={"shell_string_blocked": True},
            )
        if _contains_shell_tokens(normalized):
            return self._blocked(
                "SAFE_SUBPROCESS_SHELL_TOKEN_BLOCKED",
                "SafeSubprocessRunner blocked shell metacharacters in command arguments.",
                metadata={"args_preview": normalized[:5]},
            )

        cwd_result = self._resolve_cwd(cwd)
        if isinstance(cwd_result, CommandResult):
            return cwd_result
        resolved_cwd = cwd_result

        allowlist_match = self.allowlist.match(normalized)
        if not allowlist_match.allowed or allowlist_match.entry is None:
            return CommandResult(
                command="execution safe-subprocess",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="SafeSubprocessRunner blocked command before execution.",
                data={
                    "summary": self._summary(executed=False, blocked=True, command_allowed=False),
                    "request": {"args": normalized, "cwd": _relative(resolved_cwd, self.root)},
                    "allowlist": self.allowlist.to_dict(),
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                findings=[allowlist_match.finding] if allowlist_match.finding else [],
            )

        effective_timeout = int(timeout_seconds or allowlist_match.entry.max_timeout_seconds)
        if effective_timeout <= 0 or effective_timeout > allowlist_match.entry.max_timeout_seconds:
            return self._blocked(
                "SAFE_SUBPROCESS_TIMEOUT_INVALID",
                "SafeSubprocessRunner blocked an invalid or excessive timeout.",
                metadata={
                    "timeout_seconds": effective_timeout,
                    "max_timeout_seconds": allowlist_match.entry.max_timeout_seconds,
                    "command_id": allowlist_match.entry.command_id,
                },
            )

        started = time.monotonic()
        try:
            completed = subprocess.run(
                list(normalized),
                cwd=resolved_cwd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                shell=False,
                check=False,
            )
            duration_ms = int((time.monotonic() - started) * 1000)
            stdout, stdout_truncated, stdout_redactions = self._redact_and_truncate(completed.stdout or "")
            stderr, stderr_truncated, stderr_redactions = self._redact_and_truncate(completed.stderr or "")
            report = SafeSubprocessReport(
                command_id=allowlist_match.entry.command_id,
                args=tuple(normalized),
                cwd=_relative(resolved_cwd, self.root),
                returncode=completed.returncode,
                duration_ms=duration_ms,
                timed_out=False,
                stdout=stdout,
                stderr=stderr,
                stdout_truncated=stdout_truncated,
                stderr_truncated=stderr_truncated,
                redactions=stdout_redactions + stderr_redactions,
                max_output_chars=self.max_output_chars,
            )
            ok = completed.returncode == 0
            return CommandResult(
                command="execution safe-subprocess",
                ok=ok,
                exit_code=ExitCode.PASS if ok else ExitCode.FAIL,
                message="Safe subprocess completed successfully." if ok else "Safe subprocess completed with non-zero exit code.",
                data={
                    "summary": self._summary(
                        executed=True,
                        blocked=False,
                        command_allowed=True,
                        returncode=completed.returncode,
                        timed_out=False,
                        redactions=report.redactions,
                        duration_ms=duration_ms,
                    ),
                    "execution": report.to_dict(),
                    "allowlist": self.allowlist.to_dict(),
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                findings=[
                    Finding(
                        id="SAFE_SUBPROCESS_PASS" if ok else "SAFE_SUBPROCESS_NON_ZERO_EXIT",
                        message="Allowlisted command executed under SafeSubprocessRunner." if ok else "Allowlisted command returned non-zero exit code.",
                        severity=Severity.INFO if ok else Severity.FAIL,
                        metadata={"command_id": allowlist_match.entry.command_id, "returncode": completed.returncode},
                    )
                ],
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.monotonic() - started) * 1000)
            stdout, stdout_truncated, stdout_redactions = self._redact_and_truncate(_coerce_timeout_output(exc.stdout))
            stderr, stderr_truncated, stderr_redactions = self._redact_and_truncate(_coerce_timeout_output(exc.stderr))
            report = SafeSubprocessReport(
                command_id=allowlist_match.entry.command_id,
                args=tuple(normalized),
                cwd=_relative(resolved_cwd, self.root),
                returncode=None,
                duration_ms=duration_ms,
                timed_out=True,
                stdout=stdout,
                stderr=stderr,
                stdout_truncated=stdout_truncated,
                stderr_truncated=stderr_truncated,
                redactions=stdout_redactions + stderr_redactions,
                max_output_chars=self.max_output_chars,
            )
            return CommandResult(
                command="execution safe-subprocess",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Safe subprocess timed out and was blocked.",
                data={
                    "summary": self._summary(
                        executed=True,
                        blocked=True,
                        command_allowed=True,
                        timed_out=True,
                        redactions=report.redactions,
                        duration_ms=duration_ms,
                    ),
                    "execution": report.to_dict(),
                    "allowlist": self.allowlist.to_dict(),
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                findings=[
                    Finding(
                        id="SAFE_SUBPROCESS_TIMEOUT",
                        message="Allowlisted command exceeded its timeout and was terminated.",
                        severity=Severity.BLOCK,
                        metadata={"command_id": allowlist_match.entry.command_id, "timeout_seconds": effective_timeout},
                    )
                ],
            )
        except OSError as exc:
            return CommandResult(
                command="execution safe-subprocess",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Safe subprocess failed to start due to an operating system error.",
                data={
                    "summary": self._summary(executed=False, blocked=False, command_allowed=True),
                    "request": {"args": normalized, "cwd": _relative(resolved_cwd, self.root)},
                    "allowlist": self.allowlist.to_dict(),
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                findings=[
                    Finding(
                        id="SAFE_SUBPROCESS_OS_ERROR",
                        message=str(exc),
                        severity=Severity.ERROR,
                        metadata={"command_id": allowlist_match.entry.command_id},
                    )
                ],
            )

    def _normalize_args(self, args: Sequence[str] | str) -> list[str] | None:
        if isinstance(args, str):
            return None
        try:
            normalized = [str(item) for item in args]
        except TypeError:
            return None
        if not normalized or any(item.strip() == "" for item in normalized):
            return None
        return normalized

    def _resolve_cwd(self, cwd: str | Path) -> Path | CommandResult:
        decision = self.path_guard.evaluate(cwd, action="execute")
        if decision.effect.value in {"block", "deny"}:
            return CommandResult(
                command="execution safe-subprocess",
                ok=False,
                exit_code=ExitCode.BLOCK if decision.effect.value == "block" else ExitCode.FAIL,
                message="SafeSubprocessRunner blocked cwd before execution.",
                data={
                    "summary": self._summary(executed=False, blocked=True, command_allowed=False),
                    "request": {"cwd": str(cwd)},
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                findings=[decision.to_finding()],
            )
        candidate = Path(cwd)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()

    def _redact_and_truncate(self, value: str) -> tuple[str, bool, int]:
        redacted = self.secret_guard.redact(value)
        text = str(redacted.value)
        truncated = len(text) > self.max_output_chars
        if truncated:
            text = text[: self.max_output_chars] + "\n[TRUNCATED]"
        return text, truncated, redacted.redactions

    def _blocked(self, finding_id: str, message: str, *, metadata: dict[str, object] | None = None) -> CommandResult:
        return CommandResult(
            command="execution safe-subprocess",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="SafeSubprocessRunner blocked command before execution.",
            data={
                "summary": self._summary(executed=False, blocked=True, command_allowed=False),
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "preliminary": True,
            },
            findings=[Finding(id=finding_id, message=message, severity=Severity.BLOCK, metadata=metadata or {})],
        )

    def _summary(
        self,
        *,
        executed: bool,
        blocked: bool,
        command_allowed: bool,
        returncode: int | None = None,
        timed_out: bool = False,
        redactions: int = 0,
        duration_ms: int | None = None,
    ) -> dict[str, object]:
        return {
            "executed": executed,
            "blocked": blocked,
            "command_allowed": command_allowed,
            "returncode": returncode,
            "timed_out": timed_out,
            "redactions": redactions,
            "duration_ms": duration_ms,
            "runner": "SafeSubprocessRunner",
            "preliminary": True,
        }


def _contains_shell_tokens(args: list[str]) -> bool:
    shell_tokens = {"&&", "||", ";", "|", ">", "<", "`", "$()"}
    return any(arg in shell_tokens for arg in args)


def _coerce_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/") or "."
    except ValueError:
        return str(path).replace("\\", "/")
