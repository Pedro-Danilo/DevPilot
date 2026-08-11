from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

DEFAULT_TIMEOUT_SECONDS = 60
MAX_PATHS = 20
SAFE_BRANCH_RE = re.compile(r"^(?:feat|fix|docs|chore|test|devpilot)/[a-z0-9][a-z0-9._/-]{1,79}$")
SAFE_OBJECT_RE = re.compile(r"^(?:HEAD|[0-9a-fA-F]{7,40})$")


@dataclass(frozen=True)
class GovernedGitCommandResult:
    args: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


class GovernedGitMutationAdapter:
    """Narrow UOC-006 Git mutation adapter.

    This adapter is intentionally *not* a generic Git command runner. Every
    mutation is represented by a dedicated method with validated inputs and
    shell=False. It supports only the UOC-006 allowlist: stage exact files,
    compensate exact staging, create a local branch ref from the current HEAD,
    and create one commit from an already verified exact index.

    It never exposes reset --hard, rebase, push, force, branch deletion,
    checkout/switch, tag creation, arbitrary args or shell execution.
    """

    def __init__(self, root: Path, *, git_executable: str | None = None, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.root = Path(root).resolve()
        self.git_executable = git_executable or shutil.which("git")
        self.timeout_seconds = max(5, min(int(timeout_seconds), 300))

    def head(self) -> GovernedGitCommandResult:
        return self._run(("rev-parse", "HEAD"))

    def current_branch(self) -> GovernedGitCommandResult:
        return self._run(("branch", "--show-current"))

    def status_porcelain_z(self) -> GovernedGitCommandResult:
        return self._run(("status", "--porcelain=v1", "-z"))

    def staged_paths(self) -> list[str]:
        result = self._run(("diff", "--cached", "--name-only", "-z"))
        if not result.ok:
            raise RuntimeError(result.stderr.strip() or "git diff --cached --name-only failed")
        return _split_z(result.stdout)

    def dirty_paths(self) -> list[str]:
        changed = self._run(("diff", "--name-only", "-z"))
        untracked = self._run(("ls-files", "--others", "--exclude-standard", "-z"))
        if not changed.ok or not untracked.ok:
            raise RuntimeError((changed.stderr or untracked.stderr).strip() or "git dirty path inventory failed")
        return sorted(set(_split_z(changed.stdout) + _split_z(untracked.stdout)))

    def stage_paths(self, paths: Iterable[str]) -> GovernedGitCommandResult:
        validated = validate_paths(paths)
        return self._run(("add", "--", *validated))

    def unstage_paths(self, paths: Iterable[str]) -> GovernedGitCommandResult:
        validated = validate_paths(paths)
        return self._run(("restore", "--staged", "--", *validated))

    def cached_diff_check(self) -> GovernedGitCommandResult:
        return self._run(("diff", "--cached", "--check"))

    def cached_diff(self, *, max_bytes: int = 524_288) -> tuple[GovernedGitCommandResult, str, bool]:
        result = self._run(("diff", "--cached", "--no-ext-diff", "--unified=3"))
        raw = result.stdout.encode("utf-8", errors="replace")
        truncated = len(raw) > max_bytes
        rendered = raw[:max_bytes].decode("utf-8", errors="replace")
        return result, rendered, truncated

    def worktree_index_equivalent(self, relative_path: str) -> GovernedGitCommandResult:
        """Check Git-semantic equivalence between one worktree path and index.

        The check is intentionally delegated to Git (`git diff --quiet`) rather
        than raw-byte equality. Git for Windows can legitimately normalize
        CRLF worktree bytes to LF index bytes through `core.autocrlf`; the
        approved raw worktree SHA-256 is rechecked before staging, while this
        post-stage check proves that no unstaged semantic delta remains.
        `--no-ext-diff` prevents external diff drivers from participating.
        """
        path = validate_relative_path(relative_path)
        return self._run(("diff", "--quiet", "--no-ext-diff", "--", path))

    def index_file_bytes(self, relative_path: str) -> bytes:
        path = validate_relative_path(relative_path)
        result = self._run(("show", f":{path}"), text=False)
        if result.exit_code != 0:
            raise RuntimeError(result.stderr.strip() or f"git show :{path} failed")
        return result.stdout.encode("latin1")

    def commit(self, *, message: str, author_name: str, author_email: str) -> GovernedGitCommandResult:
        message = validate_commit_message(message)
        author_name = validate_author_name(author_name)
        author_email = validate_author_email(author_email)
        env = os.environ.copy()
        env.update({
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_COMMITTER_NAME": author_name,
            "GIT_COMMITTER_EMAIL": author_email,
        })
        # --no-verify is deliberate: arbitrary repository hooks are not part of
        # the UOC-006 typed execution contract. DevPilot performs its own
        # deterministic pre-commit gates before this call.
        return self._run(("-c", "commit.gpgSign=false", "commit", "--no-verify", "-m", message), env=env)

    def create_branch(self, *, branch_name: str, expected_head: str) -> GovernedGitCommandResult:
        branch = validate_branch_name(branch_name)
        head = validate_object(expected_head)
        return self._run(("branch", branch, head))

    def branch_exists(self, branch_name: str) -> bool:
        branch = validate_branch_name(branch_name)
        result = self._run(("show-ref", "--verify", "--quiet", f"refs/heads/{branch}"))
        return result.exit_code == 0

    def committed_paths(self, commit: str = "HEAD") -> list[str]:
        ref = validate_object(commit)
        result = self._run(("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", ref))
        if not result.ok:
            raise RuntimeError(result.stderr.strip() or "git diff-tree failed")
        return _split_z(result.stdout)

    def parent_of(self, commit: str = "HEAD") -> str | None:
        ref = validate_object(commit)
        result = self._run(("rev-parse", f"{ref}^"))
        return result.stdout.strip() if result.ok else None

    def compare(self, *, base_ref: str, head_ref: str, max_bytes: int = 524_288) -> dict[str, object]:
        base = validate_object(base_ref)
        head = validate_object(head_ref)
        names = self._run(("diff", "--name-status", f"{base}..{head}"))
        diff = self._run(("diff", "--no-ext-diff", "--unified=3", f"{base}..{head}"))
        if not names.ok or not diff.ok:
            raise RuntimeError((names.stderr or diff.stderr).strip() or "git compare failed")
        raw = diff.stdout.encode("utf-8", errors="replace")
        truncated = len(raw) > max_bytes
        return {
            "base_ref": base,
            "head_ref": head,
            "files": [line for line in names.stdout.splitlines() if line.strip()],
            "diff": raw[:max_bytes].decode("utf-8", errors="replace"),
            "diff_bytes": len(raw),
            "truncated": truncated,
        }

    def _run(self, args: tuple[str, ...], *, env: dict[str, str] | None = None, text: bool = True) -> GovernedGitCommandResult:
        if not self.git_executable:
            return GovernedGitCommandResult(args=("git", *args), exit_code=127, stdout="", stderr="git executable not found")
        command = (self.git_executable, *args)
        try:
            completed = subprocess.run(
                command,
                cwd=self.root,
                env=env,
                shell=False,
                capture_output=True,
                text=text,
                timeout=self.timeout_seconds,
                check=False,
            )
            if text:
                stdout = completed.stdout or ""
                stderr = completed.stderr or ""
            else:
                stdout = (completed.stdout or b"").decode("latin1")
                stderr = (completed.stderr or b"").decode("utf-8", errors="replace")
            return GovernedGitCommandResult(tuple(str(item) for item in args), int(completed.returncode), stdout, stderr)
        except subprocess.TimeoutExpired as exc:
            out = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else str(exc.stdout or "")
            err = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else str(exc.stderr or "")
            return GovernedGitCommandResult(tuple(str(item) for item in args), 124, out, err, timed_out=True)


def validate_relative_path(value: str) -> str:
    normalized = str(value or "").replace("\\", "/").strip()
    if not normalized or len(normalized) > 4096 or "\x00" in normalized:
        raise ValueError("Git path is empty or malformed")
    if normalized.startswith(("/", "//")) or re.match(r"^[A-Za-z]:", normalized):
        raise ValueError("Absolute Git paths are not allowed")
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} or ":" in part for part in parts):
        raise ValueError("Traversal/ADS-like Git paths are not allowed")
    return normalized


def validate_paths(paths: Iterable[str]) -> tuple[str, ...]:
    values = tuple(dict.fromkeys(validate_relative_path(item) for item in paths))
    if not values or len(values) > MAX_PATHS:
        raise ValueError(f"Git mutation requires 1-{MAX_PATHS} exact paths")
    return values


def validate_branch_name(value: str) -> str:
    branch = str(value or "").strip().lower()
    if not SAFE_BRANCH_RE.fullmatch(branch):
        raise ValueError("Branch name must use feat/fix/docs/chore/test/devpilot prefix and safe lowercase characters")
    if any(token in branch for token in ("..", "@{", "//")) or branch.endswith(("/", ".", ".lock")):
        raise ValueError("Branch name contains a forbidden Git ref pattern")
    return branch


def validate_object(value: str) -> str:
    ref = str(value or "HEAD").strip()
    if not SAFE_OBJECT_RE.fullmatch(ref):
        raise ValueError("Only HEAD or immutable hexadecimal commit ids are allowed")
    return ref


def validate_commit_message(value: str) -> str:
    message = str(value or "").strip()
    if not 5 <= len(message) <= 200 or "\n" in message or "\r" in message or "\x00" in message:
        raise ValueError("Commit message must be a single 5-200 character line")
    return message


def validate_author_name(value: str) -> str:
    name = str(value or "").strip()
    if not 2 <= len(name) <= 100 or any(ch in name for ch in "\r\n\x00<>"):
        raise ValueError("Author name is invalid")
    return name


def validate_author_email(value: str) -> str:
    email = str(value or "").strip()
    if len(email) > 200 or not re.fullmatch(r"[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+", email):
        raise ValueError("Author email is invalid")
    return email


def _split_z(value: str) -> list[str]:
    return [item.replace("\\", "/") for item in value.split("\x00") if item]
