from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest

_SAFE_GIT_TIMEOUT_SECONDS = 8


@dataclass(frozen=True)
class GitCommandResult:
    """Raw result of a whitelisted read-only Git command.

    FUNC-SPRINT-14 deliberately exposes only a tiny subset of Git operations.
    The adapter never uses shell execution and never exposes write-capable
    commands such as add, commit, checkout, reset, merge, rebase, tag or push.
    """

    args: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "args": list(self.args),
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
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


class GitAdapter:
    """Read-only Git adapter for DevPilot Local.

    Purpose:
        Provide safe visibility into repository state for future repo-analysis,
        patch review and code review flows.

    Functioning:
        Executes a fixed allowlist of Git commands using subprocess without
        shell. It does not mutate the working tree or Git history.

    Integration:
        Used by CLI command `git-status` and future repo agents. It also checks
        the workspace path through PolicyEngine before running Git.

    PASS:
        Can report branch, short status and diff stats without modifying files.

    BLOCK:
        Path outside workspace, missing path policy, unsafe command request or
        write-capable Git operation.

    Risks:
        This is a first read-only adapter. It does not implement advanced Git
        parsing, submodule auditing, LFS inspection or remote metadata analysis.
    """

    _ALLOWED_COMMANDS: tuple[tuple[str, ...], ...] = (
        ("rev-parse", "--is-inside-work-tree"),
        ("rev-parse", "--show-toplevel"),
        ("branch", "--show-current"),
        ("status", "--short"),
        ("diff", "--stat"),
        ("diff", "--cached", "--stat"),
    )

    def __init__(self, root: Path, *, git_executable: str | None = None) -> None:
        self.root = root.resolve()
        self.git_executable = git_executable or shutil.which("git")

    def status(self) -> CommandResult:
        """Return a normalized read-only Git status result."""

        policy_result = PolicyEngine(self.root).evaluate(PolicyRequest(action="read", path="."))
        if not policy_result.ok:
            return CommandResult(
                command="git-status",
                ok=False,
                exit_code=policy_result.exit_code,
                message="Git status blocked by policy.",
                data={"policy": policy_result.data},
                findings=policy_result.findings,
            )

        if not self.git_executable:
            snapshot = GitStatusSnapshot(
                is_git_repo=False,
                branch=None,
                git_available=False,
                counts={"entries_total": 0, "modified": 0, "added": 0, "deleted": 0, "renamed": 0, "untracked": 0, "staged": 0},
            )
            return CommandResult(
                command="git-status",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Git executable was not found in PATH.",
                data={"summary": snapshot.to_dict(), "commands_executed": []},
                findings=[Finding(id="GIT_EXECUTABLE_NOT_FOUND", message="Git is not available in PATH.", severity=Severity.FAIL)],
            )

        commands: list[GitCommandResult] = []
        inside = self._run_allowed(("rev-parse", "--is-inside-work-tree"))
        commands.append(inside)
        if not inside.ok or inside.stdout.strip().lower() != "true":
            snapshot = GitStatusSnapshot(
                is_git_repo=False,
                branch=None,
                counts={"entries_total": 0, "modified": 0, "added": 0, "deleted": 0, "renamed": 0, "untracked": 0, "staged": 0},
            )
            return CommandResult(
                command="git-status",
                ok=True,
                exit_code=ExitCode.PASS,
                message="Workspace is not a Git repository; read-only Git status skipped.",
                data={"summary": snapshot.to_dict(), "commands_executed": [cmd.to_dict() for cmd in commands]},
                findings=[Finding(id="GIT_REPOSITORY_NOT_FOUND", message="No Git repository was detected at the workspace root.", severity=Severity.WARNING)],
            )

        git_root_result = self._run_allowed(("rev-parse", "--show-toplevel"))
        branch_result = self._run_allowed(("branch", "--show-current"))
        status_result = self._run_allowed(("status", "--short"))
        diff_result = self._run_allowed(("diff", "--stat"))
        staged_diff_result = self._run_allowed(("diff", "--cached", "--stat"))
        commands.extend([git_root_result, branch_result, status_result, diff_result, staged_diff_result])

        short_status = [line for line in status_result.stdout.splitlines() if line.strip()]
        counts = _count_short_status(short_status)
        git_root = _display_path(Path(git_root_result.stdout.strip()), self.root) if git_root_result.ok and git_root_result.stdout.strip() else None
        snapshot = GitStatusSnapshot(
            is_git_repo=True,
            branch=branch_result.stdout.strip() or None,
            short_status=short_status,
            diff_stat=diff_result.stdout.strip(),
            staged_diff_stat=staged_diff_result.stdout.strip(),
            counts=counts,
            git_root=git_root,
            git_available=True,
        )
        findings = [Finding(id="GIT_STATUS_READ_ONLY_PASS", message="Git status was collected using read-only commands.", severity=Severity.INFO)]
        if counts.get("untracked", 0) > 0:
            findings.append(Finding(id="GIT_UNTRACKED_FILES_PRESENT", message="Untracked files are present.", severity=Severity.WARNING, metadata={"count": counts["untracked"]}))
        if counts.get("modified", 0) > 0 or counts.get("staged", 0) > 0:
            findings.append(Finding(id="GIT_WORKTREE_CHANGES_PRESENT", message="Working tree changes are present.", severity=Severity.WARNING, metadata=counts))

        return CommandResult(
            command="git-status",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Git status collected in read-only mode.",
            data={"summary": snapshot.to_dict(), "commands_executed": [cmd.to_dict() for cmd in commands]},
            findings=findings,
        )

    def _run_allowed(self, args: tuple[str, ...]) -> GitCommandResult:
        if args not in self._ALLOWED_COMMANDS:
            raise ValueError(f"Unsafe or unsupported git command: {' '.join(args)}")
        completed = subprocess.run(
            [self.git_executable or "git", *args],
            cwd=self.root,
            text=True,
            capture_output=True,
            timeout=_SAFE_GIT_TIMEOUT_SECONDS,
            check=False,
        )
        return GitCommandResult(args=args, exit_code=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)


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


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/") or "."
    except ValueError:
        return str(path).replace("\\", "/")
