from __future__ import annotations

import json
import re
import shutil
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.changes import ChangeSet, ChangeSetFile, RollbackPlanPreview, build_changeset_id, file_fingerprint
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.execution import CommandAllowlist, SafeSubprocessRunner
from devpilot_core.policy import PolicyEngine, PolicyRequest, redact_sensitive_data
from devpilot_core.review.patch_preflight import PatchPreflightEngine
from devpilot_core.review.patch_review import PatchFileChange, PatchReviewEngine, parse_unified_diff


@dataclass(frozen=True)
class PatchSandboxConfig:
    """Configuration for FUNC-SPRINT-41 sandbox patch application."""

    patch_file: str
    run_tests: bool = False
    test_profile: str = "smoke"
    approval_id: str | None = None
    cleanup: bool = False
    timeout_seconds: int = 30


class PatchSandboxManager:
    """Apply a patch to a controlled sandbox copy and emit a ChangeSet.

    Purpose:
        Prove patch behavior outside the productive workspace and produce an
        auditable ChangeSet before any future real apply flow exists.

    Functioning:
        Runs PatchPreflightEngine first, copies the workspace to
        `outputs/sandbox/<sandbox_id>/workspace`, applies the patch in that copy
        through SafeSubprocessRunner with a runtime-only allowlist, computes
        before/after hashes for patch target files, optionally runs a fixed
        pytest profile inside the sandbox, and returns a CommandResult.

    Integration:
        Exposed by `python -m devpilot_core patch sandbox --patch-file ...`.
        The sandbox path is runtime output and must not be packaged in release
        ZIPs.

    PASS:
        Patch applies only in sandbox, productive workspace fingerprint remains
        unchanged, and ChangeSet metadata is generated without raw secrets.

    BLOCK:
        Preflight security block, path escape, failed sandbox policy, productive
        workspace mutation, unsafe subprocess block, missing approval for
        optional sandbox test execution, or cleanup failure.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.sandbox_root = self.root / "outputs" / "sandbox"

    def apply(
        self,
        *,
        patch_file: str | Path,
        run_tests: bool = False,
        test_profile: str = "smoke",
        approval_id: str | None = None,
        cleanup: bool = False,
        timeout_seconds: int = 30,
    ) -> CommandResult:
        config = PatchSandboxConfig(
            patch_file=str(patch_file),
            run_tests=run_tests,
            test_profile=test_profile,
            approval_id=approval_id,
            cleanup=cleanup,
            timeout_seconds=timeout_seconds,
        )
        patch_rel, patch_path, resolve_result = self._resolve_patch_file(config.patch_file)
        if resolve_result is not None:
            return resolve_result

        patch_text = patch_path.read_text(encoding="utf-8")
        target_changes = parse_unified_diff(patch_text)
        if not target_changes:
            return CommandResult(
                command="patch sandbox",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Patch sandbox blocked a patch without detectable file changes.",
                data={"summary": self._base_summary(patch_rel, sandbox_created=False)},
                findings=[Finding("PATCH_SANDBOX_NO_FILE_CHANGES", "No file changes were detected in the patch.", Severity.BLOCK, path=patch_rel)],
            )

        preflight = PatchPreflightEngine(self.root).check(patch_file=patch_rel, approval_id=None, timeout_seconds=min(config.timeout_seconds, 30))
        if not preflight.ok:
            return CommandResult(
                command="patch sandbox",
                ok=False,
                exit_code=preflight.exit_code,
                message="Patch sandbox blocked because patch preflight did not pass.",
                data={
                    "summary": {**self._base_summary(patch_rel, sandbox_created=False), "preflight_ok": preflight.ok, "preflight_exit_code": int(preflight.exit_code)},
                    "preflight": _safe_result_summary(preflight),
                },
                findings=[_clone_finding(finding, prefix="PATCH_SANDBOX_PREFLIGHT_") for finding in preflight.findings],
            )

        sandbox_policy = PolicyEngine(self.root).evaluate(
            PolicyRequest(
                action="sandbox_apply",
                path="outputs/sandbox",
                dry_run=False,
                tool_id="patch.sandbox",
                approval_id=None,
                subject=patch_rel,
                metadata={"sprint": "FUNC-SPRINT-41", "component": "PatchSandboxManager", "approval_note": "sandbox apply itself is isolated; approval_id is reserved for optional tests.run"},
            )
        )
        if not sandbox_policy.ok:
            return CommandResult(
                command="patch sandbox",
                ok=False,
                exit_code=sandbox_policy.exit_code,
                message="Patch sandbox blocked by PolicyEngine before sandbox creation.",
                data={"summary": self._base_summary(patch_rel, sandbox_created=False), "policy": sandbox_policy.to_dict()},
                findings=sandbox_policy.findings,
            )

        test_policy_result: CommandResult | None = None
        if config.run_tests:
            test_policy_result = PolicyEngine(self.root).evaluate(
                PolicyRequest(
                    action="execute",
                    path="outputs/sandbox",
                    dry_run=False,
                    tool_id="tests.run",
                    approval_id=config.approval_id,
                    subject=f"sandbox:{config.test_profile}",
                    metadata={"sprint": "FUNC-SPRINT-41", "component": "PatchSandboxManager", "test_profile": config.test_profile},
                )
            )
            if not test_policy_result.ok:
                return CommandResult(
                    command="patch sandbox",
                    ok=False,
                    exit_code=test_policy_result.exit_code,
                    message="Patch sandbox blocked test execution because tests.run approval is missing or invalid.",
                    data={
                        "summary": {
                            **self._base_summary(patch_rel, sandbox_created=False),
                            "run_tests_requested": True,
                            "tests_executed": False,
                            "approval_required": True,
                        },
                        "tests_policy": test_policy_result.to_dict(),
                    },
                    findings=test_policy_result.findings,
                )

        sandbox_id = _new_sandbox_id()
        sandbox_dir = self.sandbox_root / sandbox_id
        workspace_dir = sandbox_dir / "workspace"
        allowlist_path = sandbox_dir / "command_allowlist.json"
        target_paths = _target_paths(target_changes)
        productive_before = _productive_fingerprint(self.root, target_paths)
        before = _sandbox_fingerprints(self.root, target_paths)
        cleanup_result: dict[str, Any] | None = None

        try:
            self._prepare_sandbox(workspace_dir)
            _write_runtime_allowlist(allowlist_path)
            apply_result = SafeSubprocessRunner(self.root, allowlist=CommandAllowlist(self.root, path=allowlist_path)).run(
                ["git", "apply", _subprocess_path(patch_path)],
                cwd=workspace_dir,
                timeout_seconds=config.timeout_seconds,
            )
            after = _sandbox_fingerprints(workspace_dir, target_paths)
            productive_after = _productive_fingerprint(self.root, target_paths)
            workspace_unchanged = productive_before == productive_after
            changeset_files = _build_changeset_files(target_paths=target_paths, before=before, after=after, patch_changes=target_changes)
            effective_changes = _effective_changes(changeset_files)
            python_fallback_result: CommandResult | None = None
            if not effective_changes:
                python_fallback_result = _apply_unified_diff_with_python(
                    patch_text=patch_text,
                    workspace_dir=workspace_dir,
                    patch_rel=patch_rel,
                )
                if python_fallback_result.ok:
                    after = _sandbox_fingerprints(workspace_dir, target_paths)
                    productive_after = _productive_fingerprint(self.root, target_paths)
                    workspace_unchanged = productive_before == productive_after
                    changeset_files = _build_changeset_files(target_paths=target_paths, before=before, after=after, patch_changes=target_changes)
                    effective_changes = _effective_changes(changeset_files)
            changeset = ChangeSet(
                changeset_id=build_changeset_id(patch_rel=patch_rel, sandbox_id=sandbox_id, files=changeset_files),
                source_patch=patch_rel,
                sandbox_id=sandbox_id,
                sandbox_workspace=_relative(workspace_dir, self.root),
                files=tuple(changeset_files),
                tests_requested=config.run_tests,
                tests_result_summary=None,
                rollback_plan=RollbackPlanPreview(
                    available=False,
                    strategy="future-rollback-manager",
                    notes=(
                        "FUNC-SPRINT-41 emits rollback metadata only; executable rollback belongs to FUNC-SPRINT-42.",
                        "Before/after hashes are generated from sandbox files, not from productive workspace mutations.",
                    ),
                ),
                metadata={
                    "preflight_exit_code": int(preflight.exit_code),
                    "sandbox_policy_exit_code": int(sandbox_policy.exit_code),
                    "network_used": False,
                    "external_api_used": False,
                    "raw_patch_emitted": False,
                },
            )

            tests_result: CommandResult | None = None
            if config.run_tests and apply_result.ok:
                tests_result = self._run_sandbox_tests(
                    workspace_dir=workspace_dir,
                    sandbox_id=sandbox_id,
                    test_profile=config.test_profile,
                    timeout_seconds=min(config.timeout_seconds, 120),
                    allowlist_path=allowlist_path,
                )
                changeset = ChangeSet(
                    changeset_id=changeset.changeset_id,
                    source_patch=changeset.source_patch,
                    sandbox_id=changeset.sandbox_id,
                    sandbox_workspace=changeset.sandbox_workspace,
                    files=changeset.files,
                    tests_requested=True,
                    tests_result_summary=_safe_result_summary(tests_result),
                    rollback_plan=changeset.rollback_plan,
                    metadata=changeset.metadata,
                )

            findings = _apply_findings(apply_result, patch_rel)
            if python_fallback_result is not None:
                findings.extend(_python_fallback_findings(python_fallback_result, patch_rel))
            if not workspace_unchanged:
                findings.append(
                    Finding(
                        "PATCH_SANDBOX_PRODUCTIVE_WORKSPACE_CHANGED",
                        "Patch sandbox detected changes in productive workspace target files; this must never happen.",
                        Severity.BLOCK,
                        path=patch_rel,
                    )
                )
            if tests_result is not None:
                findings.extend(_test_findings(tests_result, config.test_profile))
            if not changeset.files:
                findings.append(Finding("PATCH_SANDBOX_CHANGESET_EMPTY", "Sandbox patch apply did not produce a file-level ChangeSet.", Severity.BLOCK, path=patch_rel))
            if not effective_changes:
                findings.append(
                    Finding(
                        "PATCH_SANDBOX_NO_EFFECTIVE_CHANGES",
                        "Patch sandbox did not produce target file hash or size changes after git apply and deterministic fallback.",
                        Severity.BLOCK,
                        path=patch_rel,
                    )
                )
            if config.cleanup:
                cleanup_result = self.cleanup(sandbox_id).data.get("summary", {})
                if not bool(cleanup_result.get("removed")):
                    findings.append(Finding("PATCH_SANDBOX_CLEANUP_FAILED", "Sandbox cleanup was requested but the sandbox directory was not removed.", Severity.BLOCK, path=_relative(sandbox_dir, self.root)))
            if not findings:
                findings.append(Finding("PATCH_SANDBOX_PASS", "Patch applied in sandbox and ChangeSet was generated.", Severity.INFO, path=patch_rel))

            exit_code = exit_code_for_findings(findings)
            ok = exit_code == ExitCode.PASS
            summary = {
                **self._base_summary(patch_rel, sandbox_created=True),
                "sandbox_id": sandbox_id,
                "sandbox_workspace": _relative(workspace_dir, self.root),
                "preflight_ok": preflight.ok,
                "patch_applied_in_sandbox": apply_result.ok,
                "productive_workspace_unchanged": workspace_unchanged,
                "changeset_id": changeset.changeset_id,
                "changeset_files": len(changeset.files),
                "effective_changes": len(effective_changes),
                "run_tests_requested": config.run_tests,
                "tests_executed": tests_result is not None,
                "tests_ok": tests_result.ok if tests_result is not None else None,
                "cleanup_requested": config.cleanup,
                "cleanup_removed": cleanup_result.get("removed") if cleanup_result else False,
                "findings_total": len(findings),
                "blocking_findings": sum(1 for finding in findings if finding.severity == Severity.BLOCK),
                "failing_findings": sum(1 for finding in findings if finding.severity in {Severity.FAIL, Severity.ERROR}),
            }
            data = redact_sensitive_data(
                {
                    "summary": summary,
                    "preflight": _safe_result_summary(preflight),
                    "policy": _safe_result_summary(sandbox_policy),
                    "sandbox_apply": _safe_result_summary(apply_result),
                    "python_fallback": _safe_result_summary(python_fallback_result),
                    "changeset": changeset.to_dict(),
                    "tests": _safe_result_summary(tests_result) if tests_result else None,
                    "cleanup": cleanup_result,
                    "notes": [
                        "FUNC-SPRINT-41 PatchSandbox is implemented-initial and writes only under outputs/sandbox.",
                        "The productive workspace is never patched by this command.",
                        "ChangeSet contains metadata and hashes, not raw patch or file contents.",
                        "Executable rollback belongs to FUNC-SPRINT-42.",
                        "Optional test execution is fixed-profile and approval-gated when requested.",
                    ],
                }
            )
            return CommandResult(
                command="patch sandbox",
                ok=ok,
                exit_code=exit_code,
                message="Patch sandbox completed successfully." if ok else "Patch sandbox completed with findings.",
                data=data,
                findings=findings,
            )
        except Exception as exc:  # defensive boundary for CLI stability
            return CommandResult(
                command="patch sandbox",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Patch sandbox failed with an unexpected error.",
                data={"summary": self._base_summary(patch_rel, sandbox_created=sandbox_dir.exists()), "sandbox_id": sandbox_id},
                findings=[Finding("PATCH_SANDBOX_UNEXPECTED_ERROR", str(exc), Severity.ERROR, path=patch_rel)],
            )

    def cleanup(self, sandbox_id: str) -> CommandResult:
        """Remove one sandbox directory under outputs/sandbox."""

        sandbox_id = str(sandbox_id).strip()
        candidate = (self.sandbox_root / sandbox_id).resolve()
        try:
            candidate.relative_to(self.sandbox_root.resolve())
        except ValueError:
            return CommandResult(
                command="patch sandbox cleanup",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Patch sandbox cleanup blocked a path outside outputs/sandbox.",
                data={"summary": {"removed": False, "sandbox_id": sandbox_id, "preliminary": True}},
                findings=[Finding("PATCH_SANDBOX_CLEANUP_OUTSIDE_ROOT", "Sandbox cleanup path escapes outputs/sandbox.", Severity.BLOCK)],
            )
        if not candidate.exists():
            return CommandResult(
                command="patch sandbox cleanup",
                ok=True,
                exit_code=ExitCode.PASS,
                message="Patch sandbox cleanup found no directory to remove.",
                data={"summary": {"removed": False, "already_absent": True, "sandbox_id": sandbox_id, "preliminary": True}},
                findings=[Finding("PATCH_SANDBOX_CLEANUP_ALREADY_ABSENT", "Sandbox directory is already absent.", Severity.INFO)],
            )
        shutil.rmtree(candidate)
        return CommandResult(
            command="patch sandbox cleanup",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Patch sandbox cleanup removed the sandbox directory.",
            data={"summary": {"removed": True, "sandbox_id": sandbox_id, "path": _relative(candidate, self.root), "preliminary": True}},
            findings=[Finding("PATCH_SANDBOX_CLEANUP_PASS", "Sandbox directory was removed.", Severity.INFO, path=_relative(candidate, self.root))],
        )

    def _resolve_patch_file(self, patch_file: str) -> tuple[str, Path, CommandResult | None]:
        if not str(patch_file).strip():
            return "", self.root, CommandResult(
                command="patch sandbox",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Patch sandbox requires --patch-file.",
                data={"summary": self._base_summary("", sandbox_created=False)},
                findings=[Finding("PATCH_SANDBOX_PATCH_FILE_REQUIRED", "Patch sandbox requires a patch file source.", Severity.BLOCK)],
            )
        policy = PolicyEngine(self.root).evaluate(
            PolicyRequest(
                action="read",
                path=str(patch_file),
                dry_run=True,
                tool_id="patch.sandbox",
                subject=str(patch_file),
                metadata={"sprint": "FUNC-SPRINT-41", "component": "PatchSandboxManager"},
            )
        )
        if not policy.ok:
            return _display_path(Path(patch_file), self.root), self.root, CommandResult(
                command="patch sandbox",
                ok=False,
                exit_code=policy.exit_code,
                message="Patch sandbox blocked by policy before reading patch file.",
                data={"summary": self._base_summary(str(patch_file), sandbox_created=False), "policy": policy.to_dict()},
                findings=policy.findings,
            )
        candidate = Path(patch_file)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return str(candidate), candidate, CommandResult(
                command="patch sandbox",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Patch sandbox blocked a patch file outside workspace root.",
                data={"summary": self._base_summary(str(patch_file), sandbox_created=False)},
                findings=[Finding("PATCH_SANDBOX_PATCH_FILE_OUTSIDE_ROOT", "Patch file path escapes the DevPilot workspace root.", Severity.BLOCK)],
            )
        if not candidate.exists() or not candidate.is_file():
            return _display_path(candidate, self.root), candidate, CommandResult(
                command="patch sandbox",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Patch sandbox could not find the patch file.",
                data={"summary": self._base_summary(_display_path(candidate, self.root), sandbox_created=False)},
                findings=[Finding("PATCH_SANDBOX_PATCH_FILE_NOT_FOUND", "Patch file does not exist or is not a file.", Severity.FAIL, path=_display_path(candidate, self.root))],
            )
        return _display_path(candidate, self.root), candidate, None

    def _prepare_sandbox(self, workspace_dir: Path) -> None:
        workspace_dir.parent.mkdir(parents=True, exist_ok=False)
        ignore = shutil.ignore_patterns(
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "*.egg-info",
            "outputs",
            "*.zip",
            ".DS_Store",
            "Thumbs.db",
            "devpilot.db",
            "devpilot.db-*",
        )
        shutil.copytree(self.root, workspace_dir, ignore=ignore, symlinks=False)

    def _run_sandbox_tests(self, *, workspace_dir: Path, sandbox_id: str, test_profile: str, timeout_seconds: int, allowlist_path: Path) -> CommandResult:
        profile_args = {
            "smoke": ["-q", "tests/fixtures/smoke_pytest_project"],
            "unit": ["-q", "tests/test_cli_core.py", "tests/test_policy_engine.py"],
        }
        if test_profile not in profile_args:
            return CommandResult(
                command="patch sandbox tests",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Patch sandbox blocked an unsupported sandbox test profile.",
                data={"summary": {"profile": test_profile, "supported_profiles": sorted(profile_args), "preliminary": True}},
                findings=[Finding("PATCH_SANDBOX_TEST_PROFILE_UNSUPPORTED", "Only fixed sandbox test profiles are supported.", Severity.BLOCK, metadata={"profile": test_profile})],
            )
        return SafeSubprocessRunner(self.root, allowlist=CommandAllowlist(self.root, path=allowlist_path)).run(
            [sys.executable, "-m", "pytest", *profile_args[test_profile]],
            cwd=workspace_dir,
            timeout_seconds=timeout_seconds,
        )

    @staticmethod
    def _base_summary(patch_rel: str, *, sandbox_created: bool) -> dict[str, Any]:
        return {
            "source": patch_rel,
            "sandbox_created": sandbox_created,
            "patch_applied_to_productive_workspace": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_scope": "outputs/sandbox only",
            "preliminary": True,
        }


def _subprocess_path(path: Path) -> str:
    """Return a path representation that Git can consume cross-platform."""

    if sys.platform == "win32":
        return path.resolve().as_posix()
    return str(path.resolve())


def _new_sandbox_id() -> str:
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return f"patch-sandbox-{timestamp}-{uuid.uuid4().hex[:8]}"


def _write_runtime_allowlist(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "created_by": "FUNC-SPRINT-41",
        "description": "Runtime-only sandbox allowlist. It is generated under outputs/sandbox and is not a global DevPilot allowlist.",
        "commands": [
            {
                "command_id": "git.apply.sandbox",
                "executable": "git",
                "executable_aliases": ["git", "git.exe"],
                "args_prefix": ["apply"],
                "max_timeout_seconds": 30,
                "description": "Allow applying a reviewed patch only inside the sandbox workspace controlled by PatchSandboxManager.",
            },
            {
                "command_id": "python.pytest.sandbox",
                "executable": "python",
                "executable_aliases": [Path(sys.executable).name, "python", "python.exe", "python3", "python3.exe", "py", "py.exe"],
                "args_prefix": ["-m", "pytest"],
                "max_timeout_seconds": 120,
                "description": "Allow fixed pytest profiles inside the sandbox workspace when approval is valid.",
            },
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _target_paths(changes: list[PatchFileChange]) -> list[str]:
    paths: list[str] = []
    for change in changes:
        for value in (change.old_path, change.new_path):
            if value and value != "/dev/null" and value not in paths:
                paths.append(value)
    return paths


def _sandbox_fingerprints(root: Path, target_paths: list[str]) -> dict[str, dict[str, Any] | None]:
    return {path: file_fingerprint(root / path) for path in target_paths}


def _productive_fingerprint(root: Path, target_paths: list[str]) -> dict[str, dict[str, Any] | None]:
    return _sandbox_fingerprints(root, target_paths)


def _build_changeset_files(
    *,
    target_paths: list[str],
    before: dict[str, dict[str, Any] | None],
    after: dict[str, dict[str, Any] | None],
    patch_changes: list[PatchFileChange],
) -> list[ChangeSetFile]:
    action_by_path: dict[str, str] = {}
    for change in patch_changes:
        path = change.path
        if change.is_new_file:
            action_by_path[path] = "add"
        elif change.is_deleted_file:
            action_by_path[path] = "delete"
        else:
            action_by_path[path] = "modify"
    files: list[ChangeSetFile] = []
    for path in target_paths:
        before_fp = before.get(path)
        after_fp = after.get(path)
        action = action_by_path.get(path)
        if action is None:
            if before_fp is None and after_fp is not None:
                action = "add"
            elif before_fp is not None and after_fp is None:
                action = "delete"
            elif before_fp != after_fp:
                action = "modify"
            else:
                action = "unchanged"
        files.append(
            ChangeSetFile(
                path=path,
                action=action,
                before_sha256=before_fp.get("sha256") if before_fp else None,
                after_sha256=after_fp.get("sha256") if after_fp else None,
                before_size_bytes=before_fp.get("size_bytes") if before_fp else None,
                after_size_bytes=after_fp.get("size_bytes") if after_fp else None,
            )
        )
    return files



_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _effective_changes(files: list[ChangeSetFile]) -> list[ChangeSetFile]:
    return [item for item in files if item.before_sha256 != item.after_sha256 or item.before_size_bytes != item.after_size_bytes]


def _apply_unified_diff_with_python(*, patch_text: str, workspace_dir: Path, patch_rel: str) -> CommandResult:
    """Apply a small, text-only unified diff deterministically inside sandbox.

    This fallback is intentionally narrow. It is used only after the normal
    preflight has passed and the `git apply` sandbox subprocess produced no
    effective file changes. It keeps Sprint 41 cross-platform without enabling
    productive workspace mutation.
    """

    try:
        file_patches = _parse_text_file_patches(patch_text)
        if not file_patches:
            return CommandResult(
                command="patch sandbox python-fallback",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Python patch fallback did not find text hunks to apply.",
                data={"summary": {"applied": False, "files_total": 0, "preliminary": True}},
                findings=[Finding("PATCH_SANDBOX_FALLBACK_NO_TEXT_HUNKS", "No text hunks were found for deterministic fallback.", Severity.BLOCK, path=patch_rel)],
            )
        applied_files: list[str] = []
        for file_patch in file_patches:
            target = _sandbox_target_path(workspace_dir, file_patch["path"])
            original_text = target.read_text(encoding="utf-8") if target.exists() else ""
            newline = "\r\n" if "\r\n" in original_text else "\n"
            original_lines = original_text.splitlines()
            patched_lines = _apply_hunks_to_lines(original_lines, file_patch["hunks"], file_patch["path"])
            if file_patch["deleted"]:
                if target.exists():
                    target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(newline.join(patched_lines) + newline, encoding="utf-8")
            applied_files.append(file_patch["path"])
        return CommandResult(
            command="patch sandbox python-fallback",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Python patch fallback applied text hunks inside sandbox.",
            data={"summary": {"applied": True, "files_total": len(applied_files), "files": applied_files, "preliminary": True}},
            findings=[Finding("PATCH_SANDBOX_PYTHON_FALLBACK_APPLIED", "Deterministic Python fallback applied text hunks inside sandbox.", Severity.INFO, path=patch_rel)],
        )
    except Exception as exc:  # defensive boundary; caller converts to BLOCK if still no changes
        return CommandResult(
            command="patch sandbox python-fallback",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Python patch fallback could not apply the patch inside sandbox.",
            data={"summary": {"applied": False, "preliminary": True}},
            findings=[Finding("PATCH_SANDBOX_PYTHON_FALLBACK_FAILED", str(exc), Severity.BLOCK, path=patch_rel)],
        )


def _parse_text_file_patches(patch_text: str) -> list[dict[str, Any]]:
    patches: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_hunk: dict[str, Any] | None = None
    for raw_line in patch_text.splitlines():
        diff_match = re.match(r"^diff --git a/(.+?) b/(.+)$", raw_line)
        if diff_match:
            if current is not None:
                if current_hunk is not None:
                    current["hunks"].append(current_hunk)
                patches.append(current)
            current = {
                "old_path": _normalize_patch_path(diff_match.group(1)),
                "new_path": _normalize_patch_path(diff_match.group(2)),
                "path": _normalize_patch_path(diff_match.group(2)),
                "deleted": False,
                "hunks": [],
            }
            current_hunk = None
            continue
        if current is None:
            continue
        if raw_line.startswith("--- "):
            current["old_path"] = _normalize_patch_path(raw_line[4:].strip())
            if current.get("path") in {None, "/dev/null"}:
                current["path"] = current["old_path"]
            continue
        if raw_line.startswith("+++ "):
            current["new_path"] = _normalize_patch_path(raw_line[4:].strip())
            if current["new_path"] != "/dev/null":
                current["path"] = current["new_path"]
            continue
        if raw_line.startswith("deleted file mode"):
            current["deleted"] = True
            continue
        hunk_match = _HUNK_HEADER_RE.match(raw_line)
        if hunk_match:
            if current_hunk is not None:
                current["hunks"].append(current_hunk)
            current_hunk = {"old_start": int(hunk_match.group(1)), "lines": []}
            continue
        if current_hunk is not None:
            if raw_line.startswith((" ", "+", "-", "\\")):
                current_hunk["lines"].append(raw_line)
    if current is not None:
        if current_hunk is not None:
            current["hunks"].append(current_hunk)
        patches.append(current)
    return [patch for patch in patches if patch.get("path") and patch.get("path") != "/dev/null" and patch.get("hunks")]


def _apply_hunks_to_lines(original_lines: list[str], hunks: list[dict[str, Any]], path: str) -> list[str]:
    patched: list[str] = []
    cursor = 0
    for hunk in hunks:
        old_index = max(0, int(hunk["old_start"]) - 1)
        if old_index < cursor:
            raise ValueError(f"Overlapping hunk while applying {path}")
        patched.extend(original_lines[cursor:old_index])
        cursor = old_index
        for raw_line in hunk["lines"]:
            if raw_line.startswith("\\"):
                continue
            marker = raw_line[:1]
            value = raw_line[1:]
            if marker == " ":
                if cursor >= len(original_lines) or original_lines[cursor] != value:
                    raise ValueError(f"Context mismatch while applying {path}")
                patched.append(original_lines[cursor])
                cursor += 1
            elif marker == "-":
                if cursor >= len(original_lines) or original_lines[cursor] != value:
                    raise ValueError(f"Deletion mismatch while applying {path}")
                cursor += 1
            elif marker == "+":
                patched.append(value)
        
    patched.extend(original_lines[cursor:])
    return patched


def _normalize_patch_path(value: str | None) -> str | None:
    if value is None:
        return None
    raw = value.strip().replace("\\", "/")
    if raw in {"/dev/null", "dev/null"}:
        return "/dev/null"
    if raw.startswith("a/") or raw.startswith("b/"):
        raw = raw[2:]
    return raw


def _sandbox_target_path(workspace_dir: Path, relative_path: str) -> Path:
    target = (workspace_dir / relative_path).resolve()
    try:
        target.relative_to(workspace_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"Patch target escapes sandbox workspace: {relative_path}") from exc
    return target


def _python_fallback_findings(result: CommandResult, patch_rel: str) -> list[Finding]:
    if result.ok:
        return [Finding("PATCH_SANDBOX_PYTHON_FALLBACK_APPLIED", "Deterministic Python fallback applied text hunks after git apply produced no effective ChangeSet.", Severity.INFO, path=patch_rel)]
    return [Finding("PATCH_SANDBOX_PYTHON_FALLBACK_BLOCKED", "Deterministic Python fallback could not apply text hunks inside sandbox.", Severity.BLOCK, path=patch_rel, metadata={"fallback_exit_code": int(result.exit_code)})]


def _apply_findings(result: CommandResult, patch_rel: str) -> list[Finding]:
    if result.ok:
        return [Finding("PATCH_SANDBOX_APPLY_PASS", "Patch was applied inside sandbox workspace only.", Severity.INFO, path=patch_rel)]
    severity = Severity.BLOCK if result.exit_code == ExitCode.BLOCK else Severity.FAIL
    return [
        Finding(
            "PATCH_SANDBOX_APPLY_FAILED" if severity == Severity.FAIL else "PATCH_SANDBOX_APPLY_BLOCKED",
            "Patch could not be applied inside sandbox workspace.",
            severity,
            path=patch_rel,
            metadata={"source_command": result.command, "source_exit_code": int(result.exit_code)},
        )
    ]


def _test_findings(result: CommandResult, profile: str) -> list[Finding]:
    if result.ok:
        return [Finding("PATCH_SANDBOX_TESTS_PASS", "Sandbox tests completed successfully.", Severity.INFO, metadata={"profile": profile})]
    severity = Severity.BLOCK if result.exit_code == ExitCode.BLOCK else Severity.FAIL
    return [Finding("PATCH_SANDBOX_TESTS_FAILED", "Sandbox tests did not pass.", severity, metadata={"profile": profile, "source_exit_code": int(result.exit_code)})]


def _clone_finding(finding: Finding, *, prefix: str) -> Finding:
    return Finding(id=f"{prefix}{finding.id}", message=finding.message, severity=finding.severity, path=finding.path, metadata=finding.metadata)


def _safe_result_summary(result: CommandResult | None) -> dict[str, Any] | None:
    if result is None:
        return None
    severities = [finding.severity for finding in result.findings]
    return redact_sensitive_data(
        {
            "command": result.command,
            "ok": result.ok,
            "exit_code": int(result.exit_code),
            "message": result.message,
            "summary": (result.data or {}).get("summary", {}),
            "findings_total": len(result.findings),
            "blocking_findings": sum(1 for severity in severities if severity == Severity.BLOCK),
            "failing_findings": sum(1 for severity in severities if severity in {Severity.FAIL, Severity.ERROR}),
            "warnings_total": sum(1 for severity in severities if severity == Severity.WARNING),
        }
    )


def _display_path(path: Path, root: Path) -> str:
    candidate = path if path.is_absolute() else root / path
    try:
        return str(candidate.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(candidate).replace("\\", "/")


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
