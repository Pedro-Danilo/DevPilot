from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.policy import PathGuard, PolicyEffect, SecretGuard

_DEFAULT_EXCLUDED_DIRS = (".git", ".venv", "__pycache__", ".pytest_cache", "outputs")
_REVIEWABLE_SUFFIXES = {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt", ".cfg", ".ini", ".example"}
_TEXT_RULES: tuple[tuple[str, str, Severity, str], ...] = (
    ("CODE_REVIEW_SHELL_TRUE", r"shell\s*=\s*True", Severity.FAIL, "shell=True detected."),
    ("CODE_REVIEW_OS_SYSTEM", r"\bos\.system\s*\(", Severity.FAIL, "os.system detected."),
    ("CODE_REVIEW_EVAL", r"\beval\s*\(", Severity.FAIL, "eval() detected."),
    ("CODE_REVIEW_EXEC", r"\bexec\s*\(", Severity.FAIL, "exec() detected."),
    ("CODE_REVIEW_PICKLE_LOADS", r"\bpickle\.loads\s*\(", Severity.WARNING, "pickle.loads detected; validate trusted input."),
    ("CODE_REVIEW_TODO", r"(?i)\b(todo|fixme)\b", Severity.WARNING, "TODO/FIXME marker detected."),
)


@dataclass(frozen=True)
class ReviewedFile:
    """Summary of one file inspected by CodeReviewEngine."""

    path: str
    suffix: str
    size_bytes: int
    findings: int = 0
    lines: int = 0
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "suffix": self.suffix,
            "size_bytes": self.size_bytes,
            "lines": self.lines,
            "findings": self.findings,
            "reasons": self.reasons,
        }


@dataclass(frozen=True)
class CodeReviewConfig:
    """Configuration for deterministic local code review."""

    max_files: int = 1000
    max_file_bytes: int = 256_000
    excluded_dirs: tuple[str, ...] = _DEFAULT_EXCLUDED_DIRS


class CodeReviewEngine:
    """Static dry-run code review engine for DevPilot Local.

    Purpose:
        Provide a first local review pass over source/config/docs without
        modifying files or invoking external tools.

    Functioning:
        Walks a target file or directory, enforces PathGuard, scans reviewable
        text files with deterministic rules and detects secret-like content via
        SecretGuard. It never emits raw file contents.

    Integration:
        Exposed by CLI command `code-review`. Results can be persisted as
        reports, events and SQLite history through the CLI layer.

    PASS:
        Target remains inside workspace, review emits JSON, and no fail/block
        findings are detected.

    BLOCK:
        Target outside workspace, denied path, secret-like content or unreadable
        target.

    Risks:
        This preliminary engine is not a full SAST, type checker, linter,
        dependency scanner or semantic code reviewer.
    """

    def __init__(self, root: Path, *, config: CodeReviewConfig | None = None) -> None:
        self.root = root.resolve()
        self.config = config or CodeReviewConfig()
        self.secret_guard = SecretGuard()

    def review(self, target: str | Path = ".") -> CommandResult:
        policy = PathGuard(self.root).evaluate(target, action="read")
        if policy.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            finding = Finding(policy.rule_id, policy.reason, Severity.BLOCK, path=policy.subject)
            return CommandResult(
                command="code-review",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Code review blocked by path policy.",
                data={"summary": {"target": str(target).replace("\\", "/"), "dry_run": True}},
                findings=[finding],
            )
        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = self.root / target_path
        target_path = target_path.resolve()
        if not target_path.exists():
            return CommandResult(
                command="code-review",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Code review target does not exist.",
                data={"summary": {"target": _display_path(target_path, self.root), "dry_run": True}},
                findings=[Finding("CODE_REVIEW_TARGET_NOT_FOUND", "Target path does not exist.", Severity.FAIL, path=_display_path(target_path, self.root))],
            )

        files = self._candidate_files(target_path)
        findings: list[Finding] = []
        reviewed: list[ReviewedFile] = []
        for path in files:
            file_findings = self._review_file(path)
            findings.extend(file_findings)
            reviewed.append(
                ReviewedFile(
                    path=_display_path(path, self.root),
                    suffix=path.suffix.lower(),
                    size_bytes=path.stat().st_size,
                    lines=_safe_count_lines(path),
                    findings=len(file_findings),
                    reasons=sorted({finding.id for finding in file_findings}),
                )
            )
            if len(reviewed) >= self.config.max_files:
                findings.append(Finding("CODE_REVIEW_FILE_LIMIT_REACHED", "Code review reached configured max_files limit.", Severity.WARNING, metadata={"max_files": self.config.max_files}))
                break

        exit_code = exit_code_for_findings(findings)
        ok = exit_code == ExitCode.PASS
        summary = {
            "target": _display_path(target_path, self.root),
            "files_reviewed": len(reviewed),
            "findings_total": len(findings),
            "blocking_findings": sum(1 for finding in findings if finding.severity == Severity.BLOCK),
            "failing_findings": sum(1 for finding in findings if finding.severity == Severity.FAIL),
            "dry_run": True,
            "files_modified": 0,
        }
        return CommandResult(
            command="code-review",
            ok=ok,
            exit_code=exit_code,
            message="Code review passed in dry-run mode." if ok else "Code review completed with findings.",
            data={
                "summary": summary,
                "files": [item.to_dict() for item in reviewed],
                "preliminary": True,
                "notes": [
                    "FUNC-SPRINT-15 code review is deterministic and local-only.",
                    "Raw file contents are never emitted in review output.",
                ],
            },
            findings=findings or [Finding("CODE_REVIEW_PASS", "Code review completed without fail/block findings.", Severity.INFO)],
        )

    def _candidate_files(self, target: Path) -> list[Path]:
        if target.is_file():
            return [target] if _is_reviewable(target) and target.stat().st_size <= self.config.max_file_bytes else []
        candidates: list[Path] = []
        for path in sorted(target.rglob("*")):
            if _is_inside_excluded_dir(path, self.root, self.config.excluded_dirs):
                continue
            if path.is_file() and _is_reviewable(path) and path.stat().st_size <= self.config.max_file_bytes:
                candidates.append(path)
        return candidates

    def _review_file(self, path: Path) -> list[Finding]:
        rel = _display_path(path, self.root)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            return [Finding("CODE_REVIEW_FILE_READ_FAILED", str(exc), Severity.WARNING, path=rel)]
        findings: list[Finding] = []
        redaction = self.secret_guard.redact(text)
        if redaction.changed:
            findings.append(Finding("CODE_REVIEW_SECRET_LIKE_CONTENT", "Secret-like content detected and not emitted.", Severity.BLOCK, path=rel, metadata={"redactions": redaction.redactions}))
        for line_number, line in enumerate(text.splitlines(), start=1):
            for finding_id, pattern, severity, message in _TEXT_RULES:
                if re.search(pattern, line):
                    findings.append(Finding(finding_id, message, severity, path=rel, metadata={"line": line_number}))
        if path.suffix.lower() == ".py":
            findings.extend(_python_ast_findings(text, rel))
        return findings


def _python_ast_findings(text: str, path: str) -> list[Finding]:
    try:
        ast.parse(text)
    except SyntaxError as exc:
        return [Finding("CODE_REVIEW_PYTHON_SYNTAX_ERROR", "Python syntax error detected.", Severity.FAIL, path=path, metadata={"line": exc.lineno or 0})]
    return []


def _is_reviewable(path: Path) -> bool:
    return path.suffix.lower() in _REVIEWABLE_SUFFIXES or path.name.startswith(".env")


def _is_inside_excluded_dir(path: Path, root: Path, excluded_dirs: tuple[str, ...]) -> bool:
    try:
        parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return True
    return any(part in excluded_dirs for part in parts[:-1] if part)


def _safe_count_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    except OSError:
        return 0


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
