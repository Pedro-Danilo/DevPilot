from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest

_DEFAULT_SAFE_GIT_TIMEOUT_SECONDS = 60
_MIN_SAFE_GIT_TIMEOUT_SECONDS = 5
_MAX_SAFE_GIT_TIMEOUT_SECONDS = 300
_GIT_TIMEOUT_ENV = "DEVPILOT_GIT_TIMEOUT_SECONDS"
_GIT_TIMEOUT_EXIT_CODE = 124
_DEFAULT_LOG_LIMIT = 20
_MAX_LOG_LIMIT = 200
_DEFAULT_DIFF_FILE_LIMIT = 200
_MAX_DIFF_FILE_LIMIT = 1000


@dataclass(frozen=True)
class GitCommandResult:
    """Raw result of a whitelisted read-only Git command.

    GitAdapter never uses shell execution and never exposes write-capable Git
    operations such as add, commit, checkout, reset, merge, rebase, tag -a or
    push. Dynamic commands such as `git log -n <limit>` are validated by
    explicit builders before reaching subprocess.
    """

    args: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    timeout_seconds: int | None = None

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "args": list(self.args),
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "timed_out": self.timed_out,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(frozen=True)
class GitStatusSnapshot:
    """Normalized, JSON-serializable Git status snapshot."""

    is_git_repo: bool
    branch: str | None
    short_status: list[str] = field(default_factory=list)
    diff_stat: str = ""
    staged_diff_stat: str = ""
    counts: dict[str, int] = field(default_factory=dict)
    git_root: str | None = None
    git_available: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_git_repo": self.is_git_repo,
            "git_available": self.git_available,
            "branch": self.branch,
            "git_root": self.git_root,
            "short_status": self.short_status,
            "diff_stat": self.diff_stat,
            "staged_diff_stat": self.staged_diff_stat,
            "counts": self.counts,
        }


@dataclass(frozen=True)
class GitBranchInfo:
    name: str
    commit: str | None
    upstream: str | None
    current: bool
    remote: bool
    last_commit_at: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "commit": self.commit,
            "upstream": self.upstream,
            "current": self.current,
            "remote": self.remote,
            "last_commit_at": self.last_commit_at,
        }


@dataclass(frozen=True)
class GitTagInfo:
    name: str
    commit: str | None
    created_at: str | None
    subject: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "commit": self.commit,
            "created_at": self.created_at,
            "subject": self.subject,
        }


@dataclass(frozen=True)
class GitCommitInfo:
    commit: str
    short_commit: str
    author_name: str | None
    author_email: str | None
    authored_at: str | None
    subject: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "commit": self.commit,
            "short_commit": self.short_commit,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "authored_at": self.authored_at,
            "subject": self.subject,
        }


@dataclass(frozen=True)
class GitDiffFile:
    path: str
    change_type: str
    scope: str
    insertions: int | None = None
    deletions: int | None = None
    previous_path: str | None = None
    risk_level: str = "low"
    risk_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "path": self.path,
            "change_type": self.change_type,
            "scope": self.scope,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "risk_level": self.risk_level,
            "risk_reasons": list(self.risk_reasons),
        }
        if self.previous_path is not None:
            data["previous_path"] = self.previous_path
        return data


class GitAdapter:
    """Read-only Git adapter for DevPilot Local.

    Purpose:
        Provide safe visibility into repository state for repo-analysis, patch
        review, quality gates and future repository agents.

    Functioning:
        Executes a strict allowlist of Git read-only commands using subprocess
        without shell. It does not mutate the working tree, index or history.

    Integration:
        Used by CLI commands `git-status` and `git branches/tags/log/diff-report`.
        Every public method evaluates the workspace path through PolicyEngine
        before reading Git metadata.

    PASS:
        Reports branch/status/diff, branches, tags, recent commits and structured
        diff metadata without modifying repository state.

    BLOCK:
        Path outside workspace, unsafe command request or write-capable Git
        operation.

    Risks:
        This adapter is still read-only and preliminary. It does not inspect
        remotes, submodules, LFS, signatures or repository corruption states.
    """

    _ALLOWED_COMMANDS: tuple[tuple[str, ...], ...] = (
        ("rev-parse", "--is-inside-work-tree"),
        ("rev-parse", "--show-toplevel"),
        ("branch", "--show-current"),
        ("status", "--short"),
        ("diff", "--stat"),
        ("diff", "--cached", "--stat"),
        ("branch", "--all", "--format=%(refname:short)%1f%(objectname:short)%1f%(upstream:short)%1f%(HEAD)%1f%(committerdate:iso8601)"),
        ("tag", "--list", "--format=%(refname:short)%1f%(objectname:short)%1f%(creatordate:iso8601)%1f%(subject)"),
        ("diff", "--name-status"),
        ("diff", "--numstat"),
        ("diff", "--cached", "--name-status"),
        ("diff", "--cached", "--numstat"),
    )

    def __init__(
        self,
        root: Path,
        *,
        git_executable: str | None = None,
        command_timeout_seconds: int | None = None,
    ) -> None:
        self.root = root.resolve()
        self.git_executable = git_executable or shutil.which("git")
        self.command_timeout_seconds = _resolve_git_timeout_seconds(command_timeout_seconds)

    def status(self) -> CommandResult:
        """Return a normalized read-only Git status result."""

        preflight = self._preflight(command="git-status")
        if preflight is not None:
            return preflight

        repo_check, commands = self._repo_check()
        if isinstance(repo_check, CommandResult):
            return repo_check

        git_root_result = self._run_allowed(("rev-parse", "--show-toplevel"))
        branch_result = self._run_allowed(("branch", "--show-current"))
        status_result = self._run_allowed(("status", "--short"))
        commands.extend([git_root_result, branch_result, status_result])

        required_failure = self._required_command_failure(
            command="git-status",
            results=(git_root_result, branch_result, status_result),
            commands=commands,
        )
        if required_failure is not None:
            return required_failure

        # Diff statistics enrich status output but are not required for repo analysis.
        # On large Windows worktrees Git may legitimately need longer than the old
        # fixed eight-second timeout. A timeout here must degrade to a warning, not
        # abort every consumer such as RepoAnalysisAgent or multiagent workflows.
        diff_result = self._run_allowed(("diff", "--stat"))
        staged_diff_result = self._run_allowed(("diff", "--cached", "--stat"))
        commands.extend([diff_result, staged_diff_result])
        optional_failures = [result for result in (diff_result, staged_diff_result) if not result.ok]

        short_status = [line for line in status_result.stdout.splitlines() if line.strip()]
        counts = _count_short_status(short_status)
        git_root = _display_path(Path(git_root_result.stdout.strip()), self.root) if git_root_result.stdout.strip() else None
        snapshot = GitStatusSnapshot(
            is_git_repo=True,
            branch=branch_result.stdout.strip() or None,
            short_status=short_status,
            diff_stat=diff_result.stdout.strip() if diff_result.ok else "",
            staged_diff_stat=staged_diff_result.stdout.strip() if staged_diff_result.ok else "",
            counts=counts,
            git_root=git_root,
            git_available=True,
        )
        findings = [Finding(id="GIT_STATUS_READ_ONLY_PASS", message="Git status was collected using read-only commands.", severity=Severity.INFO)]
        findings.extend(_optional_command_findings(optional_failures, operation="git-status"))
        if counts.get("untracked", 0) > 0:
            findings.append(Finding(id="GIT_UNTRACKED_FILES_PRESENT", message="Untracked files are present.", severity=Severity.WARNING, metadata={"count": counts["untracked"]}))
        if counts.get("modified", 0) > 0 or counts.get("staged", 0) > 0:
            findings.append(Finding(id="GIT_WORKTREE_CHANGES_PRESENT", message="Working tree changes are present.", severity=Severity.WARNING, metadata=counts))

        summary = snapshot.to_dict()
        summary.update(
            {
                "partial": bool(optional_failures),
                "optional_commands_failed_total": len(optional_failures),
                "command_timeout_seconds": self.command_timeout_seconds,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
            }
        )
        return CommandResult(
            command="git-status",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Git status collected in read-only mode." if not optional_failures else "Git status collected with optional diff statistics unavailable.",
            data={"summary": summary, "commands_executed": [cmd.to_dict() for cmd in commands]},
            findings=findings,
        )

    def branches(self) -> CommandResult:
        """Return local/remote branch metadata using read-only Git commands."""

        preflight = self._preflight(command="git branches")
        if preflight is not None:
            return preflight
        repo_check, commands = self._repo_check(command="git branches")
        if isinstance(repo_check, CommandResult):
            return repo_check

        result = self._run_allowed(("branch", "--all", "--format=%(refname:short)%1f%(objectname:short)%1f%(upstream:short)%1f%(HEAD)%1f%(committerdate:iso8601)"))
        commands.append(result)
        failure = self._required_command_failure(command="git branches", results=(result,), commands=commands)
        if failure is not None:
            return failure
        branches = _parse_branches(result.stdout)
        return CommandResult(
            command="git branches",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Git branches collected in read-only mode.",
            data={
                "summary": {
                    "is_git_repo": True,
                    "branches_total": len(branches),
                    "current_branch": next((branch.name for branch in branches if branch.current), None),
                    "remote_branches": sum(1 for branch in branches if branch.remote),
                    "git_available": True,
                    "preliminary": True,
                },
                "branches": [branch.to_dict() for branch in branches],
                "commands_executed": [cmd.to_dict() for cmd in commands],
            },
            findings=[Finding(id="GIT_BRANCHES_READ_ONLY_PASS", message="Git branches were collected using read-only commands.", severity=Severity.INFO)],
        )

    def tags(self) -> CommandResult:
        """Return tag metadata using read-only Git commands."""

        preflight = self._preflight(command="git tags")
        if preflight is not None:
            return preflight
        repo_check, commands = self._repo_check(command="git tags")
        if isinstance(repo_check, CommandResult):
            return repo_check

        result = self._run_allowed(("tag", "--list", "--format=%(refname:short)%1f%(objectname:short)%1f%(creatordate:iso8601)%1f%(subject)"))
        commands.append(result)
        failure = self._required_command_failure(command="git tags", results=(result,), commands=commands)
        if failure is not None:
            return failure
        tags = _parse_tags(result.stdout)
        return CommandResult(
            command="git tags",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Git tags collected in read-only mode.",
            data={
                "summary": {"is_git_repo": True, "tags_total": len(tags), "git_available": True, "preliminary": True},
                "tags": [tag.to_dict() for tag in tags],
                "commands_executed": [cmd.to_dict() for cmd in commands],
            },
            findings=[Finding(id="GIT_TAGS_READ_ONLY_PASS", message="Git tags were collected using read-only commands.", severity=Severity.INFO)],
        )

    def log(self, *, limit: int = _DEFAULT_LOG_LIMIT) -> CommandResult:
        """Return recent commits using a bounded read-only Git log command."""

        preflight = self._preflight(command="git log")
        if preflight is not None:
            return preflight
        if limit <= 0 or limit > _MAX_LOG_LIMIT:
            return CommandResult(
                command="git log",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Git log limit is outside the allowed bounds.",
                data={"summary": {"limit": limit, "max_limit": _MAX_LOG_LIMIT, "preliminary": True}},
                findings=[Finding(id="GIT_LOG_LIMIT_BLOCKED", message="Git log limit must be between 1 and 200.", severity=Severity.BLOCK, metadata={"limit": limit, "max_limit": _MAX_LOG_LIMIT})],
            )
        repo_check, commands = self._repo_check(command="git log")
        if isinstance(repo_check, CommandResult):
            return repo_check

        log_args = self._log_args(limit)
        result = self._run_allowed(log_args)
        commands.append(result)
        failure = self._required_command_failure(command="git log", results=(result,), commands=commands)
        if failure is not None:
            return failure
        commits = _parse_commits(result.stdout)
        return CommandResult(
            command="git log",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Git log collected in read-only mode.",
            data={
                "summary": {"is_git_repo": True, "commits_total": len(commits), "limit": limit, "git_available": True, "preliminary": True},
                "commits": [commit.to_dict() for commit in commits],
                "commands_executed": [cmd.to_dict() for cmd in commands],
            },
            findings=[Finding(id="GIT_LOG_READ_ONLY_PASS", message="Git log was collected using a bounded read-only command.", severity=Severity.INFO, metadata={"limit": limit})],
        )

    def diff_report(self, *, max_files: int = _DEFAULT_DIFF_FILE_LIMIT) -> CommandResult:
        """Return a structured read-only diff report for staged/unstaged changes."""

        preflight = self._preflight(command="git diff-report")
        if preflight is not None:
            return preflight
        if max_files <= 0 or max_files > _MAX_DIFF_FILE_LIMIT:
            return CommandResult(
                command="git diff-report",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Git diff-report max_files is outside the allowed bounds.",
                data={"summary": {"max_files": max_files, "max_limit": _MAX_DIFF_FILE_LIMIT, "preliminary": True}},
                findings=[Finding(id="GIT_DIFF_REPORT_LIMIT_BLOCKED", message="Git diff-report max_files must be between 1 and 1000.", severity=Severity.BLOCK, metadata={"max_files": max_files})],
            )
        repo_check, commands = self._repo_check(command="git diff-report")
        if isinstance(repo_check, CommandResult):
            return repo_check

        status_result = self._run_allowed(("status", "--short"))
        commands.append(status_result)
        required_failure = self._required_command_failure(
            command="git diff-report",
            results=(status_result,),
            commands=commands,
        )
        if required_failure is not None:
            return required_failure

        unstaged_names = self._run_allowed(("diff", "--name-status"))
        unstaged_numstat = self._run_allowed(("diff", "--numstat"))
        staged_names = self._run_allowed(("diff", "--cached", "--name-status"))
        staged_numstat = self._run_allowed(("diff", "--cached", "--numstat"))
        optional_results = (unstaged_names, unstaged_numstat, staged_names, staged_numstat)
        commands.extend(optional_results)
        optional_failures = [result for result in optional_results if not result.ok]

        diff_files = _build_diff_files(
            status_lines=status_result.stdout.splitlines(),
            unstaged_name_status=unstaged_names.stdout if unstaged_names.ok else "",
            unstaged_numstat=unstaged_numstat.stdout if unstaged_numstat.ok else "",
            staged_name_status=staged_names.stdout if staged_names.ok else "",
            staged_numstat=staged_numstat.stdout if staged_numstat.ok else "",
        )
        if not unstaged_names.ok or not staged_names.ok:
            diff_files = _merge_status_fallback_files(
                diff_files,
                status_result.stdout.splitlines(),
                include_unstaged=not unstaged_names.ok,
                include_staged=not staged_names.ok,
            )
        truncated = False
        if len(diff_files) > max_files:
            diff_files = diff_files[:max_files]
            truncated = True
        counts = _diff_counts(diff_files)
        findings = [Finding(id="GIT_DIFF_REPORT_READ_ONLY_PASS", message="Git diff report was collected using read-only commands.", severity=Severity.INFO)]
        findings.extend(_optional_command_findings(optional_failures, operation="git diff-report"))
        if truncated:
            findings.append(Finding(id="GIT_DIFF_REPORT_TRUNCATED", message="Git diff report exceeded max_files and was truncated.", severity=Severity.WARNING, metadata={"max_files": max_files}))
        high_risk = [file for file in diff_files if file.risk_level == "high"]
        if high_risk:
            findings.append(
                Finding(
                    id="GIT_DIFF_HIGH_RISK_PATHS",
                    message="Diff report includes high-risk paths such as secrets, environment or credential files.",
                    severity=Severity.WARNING,
                    metadata={"paths": [file.path for file in high_risk[:20]], "total": len(high_risk)},
                )
            )

        return CommandResult(
            command="git diff-report",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Git diff report collected in read-only mode." if not optional_failures else "Git diff report collected with bounded fallback metadata.",
            data={
                "summary": {
                    "is_git_repo": True,
                    "files_total": len(diff_files),
                    "truncated": truncated,
                    "max_files": max_files,
                    "insertions_total": sum((file.insertions or 0) for file in diff_files),
                    "deletions_total": sum((file.deletions or 0) for file in diff_files),
                    "git_available": True,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                    "partial": bool(optional_failures),
                    "optional_commands_failed_total": len(optional_failures),
                    "command_timeout_seconds": self.command_timeout_seconds,
                    **counts,
                },
                "files": [file.to_dict() for file in diff_files],
                "commands_executed": [cmd.to_dict() for cmd in commands],
            },
            findings=findings,
        )

    def _preflight(self, *, command: str) -> CommandResult | None:
        policy_result = PolicyEngine(self.root, observability_enabled=False).evaluate(PolicyRequest(action="read", path="."))
        if not policy_result.ok:
            return CommandResult(
                command=command,
                ok=False,
                exit_code=policy_result.exit_code,
                message=f"{command} blocked by policy.",
                data={"policy": policy_result.data},
                findings=policy_result.findings,
            )
        if not self.git_executable:
            return CommandResult(
                command=command,
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Git executable was not found in PATH.",
                data={"summary": {"is_git_repo": False, "git_available": False, "preliminary": True}, "commands_executed": []},
                findings=[Finding(id="GIT_EXECUTABLE_NOT_FOUND", message="Git is not available in PATH.", severity=Severity.FAIL)],
            )
        return None

    def _repo_check(self, *, command: str = "git-status") -> tuple[bool, list[GitCommandResult]] | tuple[CommandResult, list[GitCommandResult]]:
        commands: list[GitCommandResult] = []
        inside = self._run_allowed(("rev-parse", "--is-inside-work-tree"))
        commands.append(inside)
        if inside.timed_out:
            return self._required_command_failure(command=command, results=(inside,), commands=commands), commands
        if not inside.ok:
            stderr = inside.stderr.lower()
            if "not a git repository" not in stderr:
                return self._required_command_failure(command=command, results=(inside,), commands=commands), commands
        if not inside.ok or inside.stdout.strip().lower() != "true":
            snapshot = GitStatusSnapshot(
                is_git_repo=False,
                branch=None,
                counts={"entries_total": 0, "modified": 0, "added": 0, "deleted": 0, "renamed": 0, "untracked": 0, "staged": 0},
            )
            return (
                CommandResult(
                    command=command,
                    ok=True,
                    exit_code=ExitCode.PASS,
                    message="Workspace is not a Git repository; read-only Git command skipped.",
                    data={"summary": snapshot.to_dict() | {"preliminary": True, "command_timeout_seconds": self.command_timeout_seconds}, "commands_executed": [cmd.to_dict() for cmd in commands]},
                    findings=[Finding(id="GIT_REPOSITORY_NOT_FOUND", message="No Git repository was detected at the workspace root.", severity=Severity.WARNING)],
                ),
                commands,
            )
        return True, commands

    def _run_allowed(self, args: tuple[str, ...]) -> GitCommandResult:
        if not self._is_read_only_allowed(args):
            raise ValueError(f"Unsafe or unsupported git command: {' '.join(args)}")
        try:
            completed = subprocess.run(
                [self.git_executable or "git", *args],
                cwd=self.root,
                text=True,
                capture_output=True,
                timeout=self.command_timeout_seconds,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = _coerce_subprocess_text(exc.stdout)
            stderr = _coerce_subprocess_text(exc.stderr)
            diagnostic = f"Read-only Git command timed out after {self.command_timeout_seconds} seconds."
            stderr = f"{stderr.rstrip()}\n{diagnostic}".strip()
            return GitCommandResult(
                args=args,
                exit_code=_GIT_TIMEOUT_EXIT_CODE,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
                timeout_seconds=self.command_timeout_seconds,
            )
        except OSError as exc:
            return GitCommandResult(
                args=args,
                exit_code=127,
                stdout="",
                stderr=f"Unable to execute read-only Git command: {exc}",
                timeout_seconds=self.command_timeout_seconds,
            )
        return GitCommandResult(
            args=args,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            timeout_seconds=self.command_timeout_seconds,
        )

    def _required_command_failure(
        self,
        *,
        command: str,
        results: Iterable[GitCommandResult],
        commands: list[GitCommandResult],
    ) -> CommandResult | None:
        failed = [result for result in results if not result.ok]
        if not failed:
            return None
        timed_out = [result for result in failed if result.timed_out]
        finding_id = "GIT_READ_ONLY_COMMAND_TIMEOUT" if timed_out else "GIT_READ_ONLY_COMMAND_FAILED"
        severity = Severity.BLOCK if timed_out else Severity.FAIL
        exit_code = ExitCode.BLOCK if timed_out else ExitCode.FAIL
        message = (
            f"{command} could not complete because a bounded read-only Git command timed out."
            if timed_out
            else f"{command} could not complete because a read-only Git command failed."
        )
        return CommandResult(
            command=command,
            ok=False,
            exit_code=exit_code,
            message=message,
            data={
                "summary": {
                    "is_git_repo": True,
                    "git_available": True,
                    "commands_failed_total": len(failed),
                    "commands_timed_out_total": len(timed_out),
                    "command_timeout_seconds": self.command_timeout_seconds,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                "commands_executed": [item.to_dict() for item in commands],
            },
            findings=[
                Finding(
                    id=finding_id,
                    message=message,
                    severity=severity,
                    metadata={
                        "failed_commands": [list(result.args) for result in failed],
                        "timed_out_commands": [list(result.args) for result in timed_out],
                        "timeout_seconds": self.command_timeout_seconds,
                    },
                )
            ],
        )

    def _is_read_only_allowed(self, args: tuple[str, ...]) -> bool:
        if args in self._ALLOWED_COMMANDS:
            return True
        if len(args) == 5 and args[:3] == ("log", "--date=iso-strict", "--pretty=format:%H%x1f%h%x1f%an%x1f%ae%x1f%ad%x1f%s") and args[3] == "-n":
            return args[4].isdigit() and 1 <= int(args[4]) <= _MAX_LOG_LIMIT
        return False

    @staticmethod
    def _log_args(limit: int) -> tuple[str, ...]:
        return ("log", "--date=iso-strict", "--pretty=format:%H%x1f%h%x1f%an%x1f%ae%x1f%ad%x1f%s", "-n", str(limit))


def _resolve_git_timeout_seconds(explicit: int | None) -> int:
    """Resolve a bounded local Git timeout without introducing config files."""

    if explicit is not None:
        if not isinstance(explicit, int) or isinstance(explicit, bool):
            raise TypeError("command_timeout_seconds must be an integer")
        if not _MIN_SAFE_GIT_TIMEOUT_SECONDS <= explicit <= _MAX_SAFE_GIT_TIMEOUT_SECONDS:
            raise ValueError(
                f"command_timeout_seconds must be between {_MIN_SAFE_GIT_TIMEOUT_SECONDS} "
                f"and {_MAX_SAFE_GIT_TIMEOUT_SECONDS}"
            )
        return explicit

    raw = os.getenv(_GIT_TIMEOUT_ENV, "").strip()
    if not raw:
        return _DEFAULT_SAFE_GIT_TIMEOUT_SECONDS
    try:
        parsed = int(raw)
    except ValueError:
        return _DEFAULT_SAFE_GIT_TIMEOUT_SECONDS
    if not _MIN_SAFE_GIT_TIMEOUT_SECONDS <= parsed <= _MAX_SAFE_GIT_TIMEOUT_SECONDS:
        return _DEFAULT_SAFE_GIT_TIMEOUT_SECONDS
    return parsed


def _coerce_subprocess_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _optional_command_findings(results: Iterable[GitCommandResult], *, operation: str) -> list[Finding]:
    findings: list[Finding] = []
    for result in results:
        if result.timed_out:
            findings.append(
                Finding(
                    id="GIT_OPTIONAL_READ_TIMEOUT",
                    message=f"{operation} continued without optional Git enrichment after a bounded timeout.",
                    severity=Severity.WARNING,
                    metadata={
                        "args": list(result.args),
                        "timeout_seconds": result.timeout_seconds,
                        "fallback_used": True,
                    },
                )
            )
        else:
            findings.append(
                Finding(
                    id="GIT_OPTIONAL_READ_FAILED",
                    message=f"{operation} continued without optional Git enrichment after a read-only command failed.",
                    severity=Severity.WARNING,
                    metadata={
                        "args": list(result.args),
                        "exit_code": result.exit_code,
                        "fallback_used": True,
                    },
                )
            )
    return findings


def _merge_status_fallback_files(
    existing: list[GitDiffFile],
    status_lines: Iterable[str],
    *,
    include_unstaged: bool,
    include_staged: bool,
) -> list[GitDiffFile]:
    """Recover file-level diff metadata from porcelain status when diff enrichment times out."""

    files = {(item.scope, item.path): item for item in existing}
    for line in status_lines:
        if len(line) < 3 or not line.strip():
            continue
        prefix = line[:2]
        raw_path = line[3:].strip()
        if " -> " in raw_path:
            previous_path, raw_path = raw_path.split(" -> ", 1)
            previous_path = _normalize_git_path(previous_path.strip('"'))
        else:
            previous_path = None
        path = _normalize_git_path(raw_path.strip('"'))
        if prefix == "??":
            files[("untracked", path)] = _make_diff_file(path=path, change_type="untracked", scope="untracked")
            continue
        index_status, worktree_status = prefix[0], prefix[1]
        if include_staged and index_status != " ":
            change_type = _change_type_from_status(index_status)
            files[("staged", path)] = _make_diff_file(
                path=path,
                change_type=change_type,
                scope="staged",
                previous_path=previous_path if change_type == "renamed" else None,
            )
        if include_unstaged and worktree_status != " ":
            change_type = _change_type_from_status(worktree_status)
            files[("unstaged", path)] = _make_diff_file(
                path=path,
                change_type=change_type,
                scope="unstaged",
                previous_path=previous_path if change_type == "renamed" else None,
            )
    return sorted(files.values(), key=lambda item: (item.scope, item.path))


def _count_short_status(lines: list[str]) -> dict[str, int]:
    counts = {"entries_total": len(lines), "modified": 0, "added": 0, "deleted": 0, "renamed": 0, "untracked": 0, "staged": 0}
    for line in lines:
        prefix = line[:2]
        if prefix == "??":
            counts["untracked"] += 1
            continue
        index_status = prefix[0]
        worktree_status = prefix[1]
        if index_status != " ":
            counts["staged"] += 1
        if "M" in prefix:
            counts["modified"] += 1
        if "A" in prefix:
            counts["added"] += 1
        if "D" in prefix:
            counts["deleted"] += 1
        if "R" in prefix:
            counts["renamed"] += 1
        if worktree_status == "?":
            counts["untracked"] += 1
    return counts


def _parse_branches(stdout: str) -> list[GitBranchInfo]:
    branches: list[GitBranchInfo] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = (line.split("\x1f") + [""] * 5)[:5]
        name, commit, upstream, marker, last_commit_at = parts
        if not name:
            continue
        branches.append(
            GitBranchInfo(
                name=name,
                commit=commit or None,
                upstream=upstream or None,
                current=marker.strip() == "*",
                remote=name.startswith("remotes/"),
                last_commit_at=last_commit_at or None,
            )
        )
    return branches


def _parse_tags(stdout: str) -> list[GitTagInfo]:
    tags: list[GitTagInfo] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = (line.split("\x1f") + [""] * 4)[:4]
        name, commit, created_at, subject = parts
        if not name:
            continue
        tags.append(GitTagInfo(name=name, commit=commit or None, created_at=created_at or None, subject=subject or None))
    return tags


def _parse_commits(stdout: str) -> list[GitCommitInfo]:
    commits: list[GitCommitInfo] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = (line.split("\x1f") + [""] * 6)[:6]
        commit, short_commit, author_name, author_email, authored_at, subject = parts
        if not commit:
            continue
        commits.append(
            GitCommitInfo(
                commit=commit,
                short_commit=short_commit,
                author_name=author_name or None,
                author_email=author_email or None,
                authored_at=authored_at or None,
                subject=subject,
            )
        )
    return commits


def _build_diff_files(
    *,
    status_lines: Iterable[str],
    unstaged_name_status: str,
    unstaged_numstat: str,
    staged_name_status: str,
    staged_numstat: str,
) -> list[GitDiffFile]:
    files: dict[tuple[str, str], GitDiffFile] = {}
    unstaged_stats = _parse_numstat(unstaged_numstat)
    staged_stats = _parse_numstat(staged_numstat)

    for file in _parse_name_status(unstaged_name_status, scope="unstaged", stats=unstaged_stats):
        files[(file.scope, file.path)] = file
    for file in _parse_name_status(staged_name_status, scope="staged", stats=staged_stats):
        files[(file.scope, file.path)] = file

    for line in status_lines:
        if not line.strip() or not line.startswith("?? "):
            continue
        path = _normalize_git_path(line[3:].strip())
        files[("untracked", path)] = _make_diff_file(path=path, change_type="untracked", scope="untracked")

    return sorted(files.values(), key=lambda item: (item.scope, item.path))


def _parse_name_status(stdout: str, *, scope: str, stats: dict[str, tuple[int | None, int | None]]) -> list[GitDiffFile]:
    files: list[GitDiffFile] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        path: str
        previous_path: str | None = None
        if status.startswith("R") and len(parts) >= 3:
            previous_path = _normalize_git_path(parts[1])
            path = _normalize_git_path(parts[2])
            change_type = "renamed"
        else:
            path = _normalize_git_path(parts[-1])
            change_type = _change_type_from_status(status[:1])
        insertions, deletions = stats.get(path, (None, None))
        files.append(_make_diff_file(path=path, change_type=change_type, scope=scope, insertions=insertions, deletions=deletions, previous_path=previous_path))
    return files


def _parse_numstat(stdout: str) -> dict[str, tuple[int | None, int | None]]:
    stats: dict[str, tuple[int | None, int | None]] = {}
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        insertions = _parse_int_or_none(parts[0])
        deletions = _parse_int_or_none(parts[1])
        path = _normalize_git_path(parts[-1])
        stats[path] = (insertions, deletions)
    return stats


def _parse_int_or_none(value: str) -> int | None:
    return int(value) if value.isdigit() else None


def _change_type_from_status(status: str) -> str:
    return {"A": "added", "D": "deleted", "M": "modified", "R": "renamed", "C": "copied", "T": "type_changed"}.get(status, "changed")


def _make_diff_file(
    *,
    path: str,
    change_type: str,
    scope: str,
    insertions: int | None = None,
    deletions: int | None = None,
    previous_path: str | None = None,
) -> GitDiffFile:
    risk_level, reasons = _risk_for_path(path)
    return GitDiffFile(
        path=path,
        change_type=change_type,
        scope=scope,
        insertions=insertions,
        deletions=deletions,
        previous_path=previous_path,
        risk_level=risk_level,
        risk_reasons=tuple(reasons),
    )


def _risk_for_path(path: str) -> tuple[str, list[str]]:
    lowered = path.lower()
    reasons: list[str] = []
    if any(token in lowered for token in (".env", "secret", "credential", "private", "token", "apikey", "api_key", "id_rsa", ".pem", ".key", ".p12")):
        reasons.append("secret_or_credential_path")
        return "high", reasons
    if any(lowered.endswith(suffix) for suffix in ("pyproject.toml", "requirements.txt", "poetry.lock", "package-lock.json", "package.json", "dockerfile", "docker-compose.yml")):
        reasons.append("dependency_or_runtime_config")
        return "medium", reasons
    if lowered.startswith("docs/"):
        reasons.append("documentation_change")
    if lowered.startswith("tests/"):
        reasons.append("test_change")
    return "low", reasons


def _diff_counts(files: list[GitDiffFile]) -> dict[str, int]:
    return {
        "added_files": sum(1 for file in files if file.change_type == "added"),
        "modified_files": sum(1 for file in files if file.change_type == "modified"),
        "deleted_files": sum(1 for file in files if file.change_type == "deleted"),
        "renamed_files": sum(1 for file in files if file.change_type == "renamed"),
        "untracked_files": sum(1 for file in files if file.change_type == "untracked"),
        "staged_files": sum(1 for file in files if file.scope == "staged"),
        "unstaged_files": sum(1 for file in files if file.scope == "unstaged"),
        "high_risk_files": sum(1 for file in files if file.risk_level == "high"),
        "medium_risk_files": sum(1 for file in files if file.risk_level == "medium"),
    }


def _normalize_git_path(value: str) -> str:
    return value.strip().replace("\\", "/")


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/") or "."
    except ValueError:
        return str(path).replace("\\", "/")
