from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.execution import SafeSubprocessRunner
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.repo.git_adapter import GitAdapter
from devpilot_core.review.patch_review import PatchReviewEngine


@dataclass(frozen=True)
class PatchPreflightConfig:
    """Configuration for the Sprint 40 patch preflight check.

    The first implementation intentionally supports patch files as the source
    of truth for `git apply --check`, because SafeSubprocessRunner currently
    executes allowlisted commands without stdin injection. Inline patch support
    remains available in PatchReviewEngine but is not used for Git apply-check.
    """

    patch_file: str
    approval_id: str | None = None
    timeout_seconds: int = 10


class PatchPreflightEngine:
    """Run a safe patch preflight without applying changes.

    Purpose:
        Combine deterministic patch review, policy checks and `git apply
        --check` applicabilidad checks before future sandbox/apply flows.

    Functioning:
        Reads one patch file inside the workspace, runs PatchReviewEngine,
        blocks immediately on security findings, then invokes `git apply
        --check` through SafeSubprocessRunner. The command uses a narrow
        allowlist and never applies the patch.

    Integration:
        Exposed by `python -m devpilot_core patch check --patch-file ...` and
        declared in MIASI as `patch.check`.

    PASS:
        The patch is review-clean enough for preflight and `git apply --check`
        returns zero without changing the working tree.

    BLOCK:
        Policy/path/security findings, missing patch file, attempted path escape
        or any evidence that the working tree changed during preflight.

    Risks:
        This is a preflight only. It is not sandbox apply, ChangeSet, rollback,
        semantic merge validation or full SAST/SCA.
    """

    def __init__(self, root: Path, *, runner: SafeSubprocessRunner | None = None) -> None:
        self.root = root.resolve()
        self.runner = runner or SafeSubprocessRunner(self.root)

    def check(self, *, patch_file: str | Path, approval_id: str | None = None, timeout_seconds: int = 10) -> CommandResult:
        config = PatchPreflightConfig(patch_file=str(patch_file), approval_id=approval_id, timeout_seconds=timeout_seconds)
        patch_rel, patch_path, policy_result = self._resolve_patch_file(config.patch_file, approval_id=approval_id)
        if policy_result is not None:
            return policy_result

        status_before = GitAdapter(self.root).status()
        review_result = PatchReviewEngine(self.root).review(patch_file=patch_rel)
        review_findings = _prefixed_findings(review_result, source="patch_review")
        blocking_review = any(finding.severity in {Severity.BLOCK, Severity.ERROR} for finding in review_result.findings)
        failing_review = any(finding.severity == Severity.FAIL for finding in review_result.findings)

        apply_result: CommandResult | None = None
        apply_findings: list[Finding] = []
        apply_summary: dict[str, Any] = {
            "executed": False,
            "applies": False,
            "skipped": True,
            "skip_reason": None,
        }

        if blocking_review:
            apply_summary["skip_reason"] = "patch_review_blocked"
            apply_findings.append(
                Finding(
                    "PATCH_PREFLIGHT_APPLY_CHECK_SKIPPED_SECURITY_BLOCK",
                    "git apply --check was skipped because PatchReviewEngine emitted blocking/security findings.",
                    Severity.BLOCK,
                    path=patch_rel,
                )
            )
        else:
            apply_result = self._run_apply_check(patch_rel, timeout_seconds=config.timeout_seconds)
            apply_summary = self._apply_summary(apply_result)
            apply_findings.extend(_apply_findings(apply_result, patch_rel))

        status_after = GitAdapter(self.root).status()
        unchanged = _status_fingerprint(status_before) == _status_fingerprint(status_after)
        integrity_findings: list[Finding] = []
        if not unchanged:
            integrity_findings.append(
                Finding(
                    "PATCH_PREFLIGHT_WORKTREE_CHANGED",
                    "Patch preflight detected working tree changes after the check; this must never happen.",
                    Severity.BLOCK,
                    path=patch_rel,
                )
            )

        findings = [*review_findings, *apply_findings, *integrity_findings]
        if not findings:
            findings.append(Finding("PATCH_PREFLIGHT_PASS", "Patch preflight passed without findings.", Severity.INFO, path=patch_rel))

        exit_code = exit_code_for_findings(findings)
        ok = exit_code == ExitCode.PASS
        summary = {
            "source": patch_rel,
            "patch_review_ok": review_result.ok,
            "patch_review_exit_code": int(review_result.exit_code),
            "review_blocking_findings": sum(1 for finding in review_result.findings if finding.severity == Severity.BLOCK),
            "review_failing_findings": sum(1 for finding in review_result.findings if finding.severity in {Severity.FAIL, Severity.ERROR}),
            "apply_check_executed": bool(apply_summary.get("executed")),
            "applies": bool(apply_summary.get("applies")),
            "apply_check_exit_code": apply_summary.get("returncode"),
            "working_tree_unchanged": unchanged,
            "security_block": blocking_review,
            "applicability_fail": bool(apply_summary.get("executed")) and not bool(apply_summary.get("applies")) and not blocking_review,
            "findings_total": len(findings),
            "blocking_findings": sum(1 for finding in findings if finding.severity == Severity.BLOCK),
            "failing_findings": sum(1 for finding in findings if finding.severity in {Severity.FAIL, Severity.ERROR}),
            "warnings_total": sum(1 for finding in findings if finding.severity == Severity.WARNING),
            "dry_run": True,
            "patch_applied": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "preliminary": True,
        }
        if failing_review and not blocking_review:
            summary["review_fail_without_security_block"] = True

        data: dict[str, Any] = {
            "summary": summary,
            "patch_review": _safe_result_summary(review_result),
            "apply_check": apply_summary,
            "git_status_before": _safe_status_summary(status_before),
            "git_status_after": _safe_status_summary(status_after),
            "notes": [
                "FUNC-SPRINT-40 Patch preflight is dry-run and implemented-initial.",
                "PatchReviewEngine evaluates risks before git apply --check.",
                "git apply --check is executed through SafeSubprocessRunner and an explicit allowlist.",
                "No patch is applied to the workspace productivo; sandbox/apply/rollback belong to later sprints.",
                "Raw patch content and secret values are not emitted.",
            ],
        }
        if apply_result is not None:
            data["apply_check"]["safe_subprocess"] = _safe_result_summary(apply_result)

        message = "Patch preflight passed in dry-run mode." if ok else "Patch preflight completed with findings."
        return CommandResult(command="patch check", ok=ok, exit_code=exit_code, message=message, data=data, findings=findings)

    def _resolve_patch_file(self, patch_file: str, *, approval_id: str | None) -> tuple[str, Path, CommandResult | None]:
        if not patch_file or not str(patch_file).strip():
            return (
                "",
                self.root,
                CommandResult(
                    command="patch check",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message="Patch preflight requires --patch-file.",
                    data={"summary": {"dry_run": True, "patch_applied": False, "preliminary": True}},
                    findings=[Finding("PATCH_PREFLIGHT_PATCH_FILE_REQUIRED", "Patch preflight requires a patch file source.", Severity.BLOCK)],
                ),
            )
        policy = PolicyEngine(self.root, observability_enabled=False).evaluate(
            PolicyRequest(
                action="read",
                path=patch_file,
                dry_run=True,
                tool_id="patch.check",
                approval_id=approval_id,
                subject=patch_file,
                metadata={"sprint": "FUNC-SPRINT-40", "component": "PatchPreflightEngine"},
            )
        )
        if not policy.ok:
            return (
                _display_path(Path(patch_file), self.root),
                self.root,
                CommandResult(
                    command="patch check",
                    ok=False,
                    exit_code=policy.exit_code,
                    message="Patch preflight blocked by policy before reading patch file.",
                    data={"summary": {"dry_run": True, "patch_applied": False, "preliminary": True}, "policy": policy.data},
                    findings=policy.findings,
                ),
            )
        candidate = Path(patch_file)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return (
                str(candidate),
                candidate,
                CommandResult(
                    command="patch check",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message="Patch preflight blocked a patch file outside workspace root.",
                    data={"summary": {"dry_run": True, "patch_applied": False, "preliminary": True}},
                    findings=[Finding("PATCH_PREFLIGHT_PATH_OUTSIDE_ROOT", "Patch file path escapes the DevPilot workspace root.", Severity.BLOCK)],
                ),
            )
        if not candidate.exists() or not candidate.is_file():
            return (
                _display_path(candidate, self.root),
                candidate,
                CommandResult(
                    command="patch check",
                    ok=False,
                    exit_code=ExitCode.FAIL,
                    message="Patch preflight could not find the patch file.",
                    data={"summary": {"source": _display_path(candidate, self.root), "dry_run": True, "patch_applied": False, "preliminary": True}},
                    findings=[Finding("PATCH_PREFLIGHT_FILE_NOT_FOUND", "Patch file does not exist or is not a file.", Severity.FAIL, path=_display_path(candidate, self.root))],
                ),
            )
        return _display_path(candidate, self.root), candidate, None

    def _run_apply_check(self, patch_rel: str, *, timeout_seconds: int) -> CommandResult:
        return self.runner.run(["git", "apply", "--check", patch_rel], cwd=".", timeout_seconds=timeout_seconds)

    @staticmethod
    def _apply_summary(result: CommandResult) -> dict[str, Any]:
        execution = (result.data or {}).get("execution", {})
        summary = (result.data or {}).get("summary", {})
        return {
            "executed": bool(summary.get("executed", False)),
            "applies": bool(result.ok),
            "skipped": False,
            "returncode": execution.get("returncode"),
            "timed_out": bool(execution.get("timed_out", False)),
            "duration_ms": execution.get("duration_ms"),
            "stdout_truncated": bool(execution.get("stdout_truncated", False)),
            "stderr_truncated": bool(execution.get("stderr_truncated", False)),
            "redactions": execution.get("redactions", []),
            "stderr_preview": _bounded_text(execution.get("stderr", "")),
            "stdout_preview": _bounded_text(execution.get("stdout", "")),
        }


def _prefixed_findings(result: CommandResult, *, source: str) -> list[Finding]:
    prefixed: list[Finding] = []
    for finding in result.findings:
        if finding.id == "PATCH_REVIEW_PASS":
            continue
        metadata = {"source": source, "source_command": result.command, "source_finding_id": finding.id, **finding.metadata}
        prefixed.append(
            Finding(
                id=f"PATCH_PREFLIGHT_{source.upper()}_{finding.id}",
                message=finding.message,
                severity=finding.severity,
                path=finding.path,
                metadata=metadata,
            )
        )
    return prefixed


def _apply_findings(result: CommandResult, patch_rel: str) -> list[Finding]:
    if result.ok:
        return [Finding("PATCH_PREFLIGHT_APPLY_CHECK_PASS", "git apply --check reported that the patch is applicable without applying it.", Severity.INFO, path=patch_rel)]
    if result.exit_code == ExitCode.BLOCK:
        severity = Severity.BLOCK
        finding_id = "PATCH_PREFLIGHT_APPLY_CHECK_BLOCKED"
        message = "git apply --check was blocked by SafeSubprocessRunner or policy controls."
    elif result.exit_code == ExitCode.ERROR:
        severity = Severity.ERROR
        finding_id = "PATCH_PREFLIGHT_APPLY_CHECK_ERROR"
        message = "git apply --check could not be executed due to an execution error."
    else:
        severity = Severity.FAIL
        finding_id = "PATCH_PREFLIGHT_APPLY_CHECK_FAILED"
        message = "git apply --check reported that the patch is not currently applicable."
    metadata = {
        "source": "safe_subprocess",
        "source_command": result.command,
        "source_exit_code": int(result.exit_code),
        "safe_subprocess_findings": [finding.id for finding in result.findings],
    }
    return [Finding(finding_id, message, severity, path=patch_rel, metadata=metadata)]


def _safe_result_summary(result: CommandResult) -> dict[str, Any]:
    severities = [finding.severity for finding in result.findings]
    data_summary = (result.data or {}).get("summary", {})
    return {
        "command": result.command,
        "ok": result.ok,
        "exit_code": int(result.exit_code),
        "message": result.message,
        "summary": data_summary,
        "findings_total": len(result.findings),
        "blocking_findings": sum(1 for severity in severities if severity == Severity.BLOCK),
        "failing_findings": sum(1 for severity in severities if severity in {Severity.FAIL, Severity.ERROR}),
        "warnings_total": sum(1 for severity in severities if severity == Severity.WARNING),
    }


def _safe_status_summary(result: CommandResult) -> dict[str, Any]:
    summary = (result.data or {}).get("summary", {})
    return {
        "ok": result.ok,
        "exit_code": int(result.exit_code),
        "is_git_repo": summary.get("is_git_repo"),
        "git_available": summary.get("git_available"),
        "branch": summary.get("branch"),
        "counts": summary.get("counts", {}),
    }


def _status_fingerprint(result: CommandResult) -> dict[str, Any]:
    summary = (result.data or {}).get("summary", {})
    return {
        "ok": result.ok,
        "is_git_repo": summary.get("is_git_repo"),
        "branch": summary.get("branch"),
        "counts": summary.get("counts", {}),
        "short_status": summary.get("short_status", []),
        "diff_stat": summary.get("diff_stat", ""),
        "staged_diff_stat": summary.get("staged_diff_stat", ""),
    }


def _display_path(path: Path, root: Path) -> str:
    candidate = path if path.is_absolute() else root / path
    try:
        return str(candidate.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(candidate).replace("\\", "/")


def _bounded_text(value: Any, *, limit: int = 500) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[:limit] + "...<truncated>"
