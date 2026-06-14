from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.policy import PolicyEngine, PolicyRequest, SecretGuard

_DIFF_GIT_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$")
_HUNK_RE = re.compile(r"^@@")
_RISKY_CODE_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("PATCH_RISKY_SHELL_TRUE", r"shell\s*=\s*True", "Added code enables shell=True."),
    ("PATCH_RISKY_OS_SYSTEM", r"\bos\.system\s*\(", "Added code calls os.system."),
    ("PATCH_RISKY_EVAL", r"\beval\s*\(", "Added code calls eval."),
    ("PATCH_RISKY_EXEC", r"\bexec\s*\(", "Added code calls exec."),
    ("PATCH_RISKY_PICKLE_LOADS", r"\bpickle\.loads\s*\(", "Added code calls pickle.loads."),
)


@dataclass
class PatchFileChange:
    """One file-level change parsed from a unified diff.

    This model is intentionally compact and JSON-serializable. It captures the
    minimum evidence required by FUNC-SPRINT-15 without applying the patch.
    """

    old_path: str | None = None
    new_path: str | None = None
    added_lines: int = 0
    deleted_lines: int = 0
    hunks: int = 0
    is_new_file: bool = False
    is_deleted_file: bool = False
    is_binary: bool = False
    added_line_samples: list[str] = field(default_factory=list)

    @property
    def path(self) -> str:
        return self.new_path or self.old_path or "<unknown>"

    def to_dict(self) -> dict[str, Any]:
        return {
            "old_path": self.old_path,
            "new_path": self.new_path,
            "path": self.path,
            "added_lines": self.added_lines,
            "deleted_lines": self.deleted_lines,
            "hunks": self.hunks,
            "is_new_file": self.is_new_file,
            "is_deleted_file": self.is_deleted_file,
            "is_binary": self.is_binary,
            "added_line_samples": self.added_line_samples,
        }


class PatchReviewEngine:
    """Dry-run patch review engine for DevPilot Local.

    Purpose:
        Analyze unified diffs/patches without applying them.

    Functioning:
        Reads a patch from text or a local patch file, parses file changes,
        checks target paths through PolicyEngine, scans additions for
        secret-like content, and detects high-risk static code patterns.

    Integration:
        Exposed by CLI command `patch-review`. Results use CommandResult,
        ReportEngine, EventLogger and LocalStore through the CLI layer.

    PASS:
        Clean patches are summarized and never applied.

    BLOCK:
        Patch file outside workspace, denied target path, raw secret-like
        addition or malformed/no-change patch.

    Risks:
        This is a first deterministic review pass. It does not validate whether
        a patch applies cleanly, does not understand all diff formats and is not
        a full SAST/security scanner.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.secret_guard = SecretGuard()

    def review(self, *, patch_file: str | Path | None = None, patch_text: str | None = None) -> CommandResult:
        findings: list[Finding] = []
        source = "inline"
        text = patch_text or ""

        if patch_file:
            patch_path = Path(patch_file)
            source = _display_path(patch_path, self.root)
            policy = PolicyEngine(self.root, observability_enabled=False).evaluate(PolicyRequest(action="read", path=str(patch_file)))
            if not policy.ok:
                return CommandResult(
                    command="patch-review",
                    ok=False,
                    exit_code=policy.exit_code,
                    message="Patch review blocked by policy before reading patch file.",
                    data={"source": source, "policy": policy.data},
                    findings=policy.findings,
                )
            candidate = patch_path if patch_path.is_absolute() else self.root / patch_path
            try:
                text = candidate.read_text(encoding="utf-8")
            except OSError as exc:
                return CommandResult(
                    command="patch-review",
                    ok=False,
                    exit_code=ExitCode.FAIL,
                    message="Patch file could not be read.",
                    data={"source": source},
                    findings=[Finding("PATCH_FILE_READ_FAILED", str(exc), Severity.FAIL, path=source)],
                )

        if not text.strip():
            findings.append(Finding("PATCH_EMPTY", "Patch review requires non-empty patch text or patch file.", Severity.BLOCK))
            return self._result(source=source, text=text, changes=[], findings=findings)

        changes = parse_unified_diff(text)
        if not changes:
            findings.append(Finding("PATCH_NO_FILE_CHANGES", "No file changes were detected in the patch.", Severity.BLOCK, metadata={"source": source}))
            return self._result(source=source, text=text, changes=changes, findings=findings)

        redaction = self.secret_guard.redact(text)
        if redaction.changed:
            findings.append(
                Finding(
                    "PATCH_SECRET_LIKE_CONTENT",
                    "Secret-like content was detected in the patch and must not be applied without remediation.",
                    Severity.BLOCK,
                    metadata={"redactions": redaction.redactions},
                )
            )

        for change in changes:
            self._review_change(change, findings)

        return self._result(source=source, text=text, changes=changes, findings=findings)

    def _review_change(self, change: PatchFileChange, findings: list[Finding]) -> None:
        target_paths = [path for path in (change.old_path, change.new_path) if path and path != "/dev/null"]
        for path in sorted(set(target_paths)):
            policy = PolicyEngine(self.root, observability_enabled=False).evaluate(PolicyRequest(action="read", path=path))
            if not policy.ok:
                findings.append(
                    Finding(
                        "PATCH_TARGET_POLICY_BLOCK",
                        "Patch references a path blocked by PolicyEngine.",
                        Severity.BLOCK,
                        path=path,
                        metadata={"policy_exit_code": int(policy.exit_code)},
                    )
                )
        if change.is_deleted_file:
            findings.append(Finding("PATCH_DELETES_FILE", "Patch deletes a file. Review manually before any future apply flow.", Severity.WARNING, path=change.path))
        if change.is_binary:
            findings.append(Finding("PATCH_BINARY_CHANGE", "Patch contains a binary file marker that cannot be reviewed semantically.", Severity.WARNING, path=change.path))
        for sample in change.added_line_samples:
            for finding_id, pattern, message in _RISKY_CODE_PATTERNS:
                if re.search(pattern, sample):
                    findings.append(Finding(finding_id, message, Severity.FAIL, path=change.path))

    def _result(self, *, source: str, text: str, changes: list[PatchFileChange], findings: list[Finding]) -> CommandResult:
        exit_code = exit_code_for_findings(findings)
        ok = exit_code == ExitCode.PASS
        summary = {
            "source": source,
            "files_changed": len(changes),
            "added_lines": sum(change.added_lines for change in changes),
            "deleted_lines": sum(change.deleted_lines for change in changes),
            "hunks": sum(change.hunks for change in changes),
            "findings_total": len(findings),
            "blocking_findings": sum(1 for finding in findings if finding.severity == Severity.BLOCK),
            "failing_findings": sum(1 for finding in findings if finding.severity == Severity.FAIL),
            "dry_run": True,
            "patch_applied": False,
        }
        return CommandResult(
            command="patch-review",
            ok=ok,
            exit_code=exit_code,
            message="Patch review passed in dry-run mode." if ok else "Patch review completed with findings.",
            data={
                "summary": summary,
                "changes": [change.to_dict() for change in changes],
                "preliminary": True,
                "notes": [
                    "FUNC-SPRINT-15 patch review never applies patches.",
                    "Raw patch content is not emitted in the CommandResult.",
                ],
            },
            findings=findings or [Finding("PATCH_REVIEW_PASS", "Patch review completed without blocking/failing findings.", Severity.INFO)],
        )


def parse_unified_diff(text: str) -> list[PatchFileChange]:
    """Parse a practical subset of unified diff syntax."""

    changes: list[PatchFileChange] = []
    current: PatchFileChange | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        match = _DIFF_GIT_RE.match(line)
        if match:
            if current is not None:
                changes.append(current)
            current = PatchFileChange(old_path=_normalize_diff_path(match.group(1)), new_path=_normalize_diff_path(match.group(2)))
            continue
        if current is None:
            continue
        if line.startswith("--- "):
            current.old_path = _normalize_diff_path(line[4:].strip())
            continue
        if line.startswith("+++ "):
            current.new_path = _normalize_diff_path(line[4:].strip())
            continue
        if line.startswith("new file mode"):
            current.is_new_file = True
            continue
        if line.startswith("deleted file mode"):
            current.is_deleted_file = True
            continue
        if line.startswith("Binary files") or line.startswith("GIT binary patch"):
            current.is_binary = True
            continue
        if _HUNK_RE.match(line):
            current.hunks += 1
            continue
        if line.startswith("+") and not line.startswith("+++"):
            current.added_lines += 1
            if len(current.added_line_samples) < 20:
                redaction = SecretGuard().redact(line[1:])
                current.added_line_samples.append(redaction.value)
            continue
        if line.startswith("-") and not line.startswith("---"):
            current.deleted_lines += 1
            continue
    if current is not None:
        changes.append(current)
    return changes


def _normalize_diff_path(value: str | None) -> str | None:
    if value is None:
        return None
    raw = value.strip().replace("\\", "/")
    if raw in {"/dev/null", "dev/null"}:
        return "/dev/null"
    if raw.startswith("a/") or raw.startswith("b/"):
        raw = raw[2:]
    return raw.strip()


def _display_path(path: str | Path, root: Path) -> str:
    candidate = Path(path)
    try:
        if not candidate.is_absolute():
            return str(candidate).replace("\\", "/")
        return str(candidate.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(candidate).replace("\\", "/")
