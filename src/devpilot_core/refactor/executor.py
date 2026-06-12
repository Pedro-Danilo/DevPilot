from __future__ import annotations

import json
import shutil
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.changes import ChangeSet, ChangeSetFile, RollbackManager, RollbackPlanPreview, build_changeset_id, file_fingerprint
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.execution import CommandAllowlist, SafeSubprocessRunner
from devpilot_core.policy import PolicyEngine, PolicyRequest, SecretGuard, redact_sensitive_data
from devpilot_core.refactor.planner import RefactorPlanner


@dataclass(frozen=True)
class RefactorExecutorConfig:
    """Execution configuration for sandboxed refactors.

    Purpose:
        Keep Sprint 43 execution bounded and explicit. The executor supports
        only deterministic, mechanical transformations inside an isolated
        sandbox. It does not accept arbitrary shell commands or semantic code
        generation.
    """

    target: str
    plan_id: str
    approval_id: str | None = None
    run_tests: bool = False
    test_profile: str = "smoke"
    tests_approval_id: str | None = None
    cleanup: bool = False
    timeout_seconds: int = 30
    max_files: int = 50


class RefactorExecutor:
    """Execute a reviewed refactor plan only inside a sandbox workspace.

    Purpose:
        FUNC-SPRINT-43 converts a safe-refactor plan into controlled sandbox
        changes. It is intentionally narrow: the first executable operation is
        a deterministic Python text normalization pass for `.py` files.

    Functioning:
        The executor validates the target and plan id, enforces scoped approval
        through PolicyEngine, copies the workspace to `outputs/sandbox`, applies
        mechanical normalization only inside the sandbox, emits a ChangeSet,
        creates a rollback plan with RollbackManager and optionally runs fixed
        sandbox pytest profiles with a separate tests.run approval.

    Integration:
        Exposed through `python -m devpilot_core refactor sandbox ...`. It
        depends on RefactorPlanner, PolicyEngine, ChangeSet, RollbackManager and
        SafeSubprocessRunner without adding external dependencies.

    PASS:
        A scoped approval is valid, sandbox changes are deterministic, the
        productive workspace remains unchanged, ChangeSet and rollback plan are
        generated, and optional sandbox tests pass.

    BLOCK:
        Missing/wrong approval, unknown plan id, ambiguous target, target outside
        root, no deterministic changes, productive workspace mutation, rollback
        plan failure or unsupported test profile.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.sandbox_root = self.root / "outputs" / "sandbox"
        self.secret_guard = SecretGuard()

    def sandbox(
        self,
        *,
        target: str | Path,
        plan_id: str,
        approval_id: str | None,
        run_tests: bool = False,
        test_profile: str = "smoke",
        tests_approval_id: str | None = None,
        cleanup: bool = False,
        timeout_seconds: int = 30,
    ) -> CommandResult:
        config = RefactorExecutorConfig(
            target=str(target),
            plan_id=str(plan_id),
            approval_id=approval_id,
            run_tests=run_tests,
            test_profile=test_profile,
            tests_approval_id=tests_approval_id,
            cleanup=cleanup,
            timeout_seconds=timeout_seconds,
        )
        target_rel, target_path, target_error = self._resolve_target(config.target)
        if target_error is not None:
            return target_error

        plan_result = RefactorPlanner(self.root).plan(target_rel, goal="Sprint 43 sandbox execution", include_code_review=False)
        if not plan_result.ok:
            return CommandResult(
                command="refactor sandbox",
                ok=False,
                exit_code=plan_result.exit_code,
                message="Refactor sandbox blocked because the safe refactor plan did not pass.",
                data={"summary": self._base_summary(target_rel, config.plan_id, sandbox_created=False), "plan": _safe_result_summary(plan_result)},
                findings=plan_result.findings,
            )
        plan_step = _find_plan_step(plan_result, config.plan_id)
        if plan_step is None:
            return CommandResult(
                command="refactor sandbox",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Refactor sandbox blocked an unknown or ambiguous plan id.",
                data={"summary": self._base_summary(target_rel, config.plan_id, sandbox_created=False), "available_plan_ids": _plan_ids(plan_result)},
                findings=[Finding("REFACTOR_SANDBOX_PLAN_ID_INVALID", "The requested plan_id is not present in the deterministic RefactorPlanner output.", Severity.BLOCK, path=target_rel, metadata={"plan_id": config.plan_id})],
            )

        subject = _approval_subject(config.plan_id, target_rel)
        execution_policy = PolicyEngine(self.root).evaluate(
            PolicyRequest(
                action="execute",
                path="outputs/sandbox",
                dry_run=False,
                approval_id=config.approval_id,
                tool_id="refactor.sandbox",
                subject=subject,
                metadata={"sprint": "FUNC-SPRINT-43", "component": "RefactorExecutor", "plan_id": config.plan_id, "target": target_rel},
            )
        )
        if not execution_policy.ok:
            return CommandResult(
                command="refactor sandbox",
                ok=False,
                exit_code=execution_policy.exit_code,
                message="Refactor sandbox blocked because scoped approval is missing or invalid.",
                data={"summary": {**self._base_summary(target_rel, config.plan_id, sandbox_created=False), "approval_required": True, "approval_subject": subject}, "policy": execution_policy.to_dict()},
                findings=execution_policy.findings,
            )

        test_policy: CommandResult | None = None
        if config.run_tests:
            test_policy = PolicyEngine(self.root).evaluate(
                PolicyRequest(
                    action="execute",
                    path="outputs/sandbox",
                    dry_run=False,
                    approval_id=config.tests_approval_id,
                    tool_id="tests.run",
                    subject=f"sandbox:{config.test_profile}",
                    metadata={"sprint": "FUNC-SPRINT-43", "component": "RefactorExecutor", "test_profile": config.test_profile},
                )
            )
            if not test_policy.ok:
                return CommandResult(
                    command="refactor sandbox",
                    ok=False,
                    exit_code=test_policy.exit_code,
                    message="Refactor sandbox blocked optional tests because tests.run approval is missing or invalid.",
                    data={
                        "summary": {
                            **self._base_summary(target_rel, config.plan_id, sandbox_created=False),
                            "run_tests_requested": True,
                            "tests_executed": False,
                            "tests_approval_required": True,
                        },
                        "tests_policy": test_policy.to_dict(),
                    },
                    findings=test_policy.findings,
                )

        target_paths = self._candidate_files(target_path, limit=config.max_files)
        if not target_paths:
            return CommandResult(
                command="refactor sandbox",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Refactor sandbox blocked because the target has no supported Python files.",
                data={"summary": self._base_summary(target_rel, config.plan_id, sandbox_created=False)},
                findings=[Finding("REFACTOR_SANDBOX_NO_SUPPORTED_FILES", "Only workspace-local .py files are supported by the initial RefactorExecutor.", Severity.BLOCK, path=target_rel)],
            )

        sandbox_id = _new_sandbox_id()
        sandbox_dir = self.sandbox_root / sandbox_id
        workspace_dir = sandbox_dir / "workspace"
        allowlist_path = sandbox_dir / "command_allowlist.json"
        before = _fingerprints(self.root, target_paths)
        productive_before = dict(before)
        cleanup_result: dict[str, Any] | None = None

        try:
            self._prepare_sandbox(workspace_dir)
            _write_runtime_allowlist(allowlist_path)
            changed_paths = self._apply_mechanical_refactor(workspace_dir=workspace_dir, target_paths=target_paths)
            after = _fingerprints(workspace_dir, target_paths)
            productive_after = _fingerprints(self.root, target_paths)
            workspace_unchanged = productive_before == productive_after
            changeset_files = _changeset_files(target_paths=changed_paths, before=before, after=after)
            changeset = ChangeSet(
                changeset_id=build_changeset_id(patch_rel=f"refactor:{config.plan_id}:{target_rel}", sandbox_id=sandbox_id, files=changeset_files),
                source_patch=f"refactor:{config.plan_id}",
                sandbox_id=sandbox_id,
                sandbox_workspace=_relative(workspace_dir, self.root),
                files=tuple(changeset_files),
                tests_requested=config.run_tests,
                tests_result_summary=None,
                rollback_plan=RollbackPlanPreview(
                    available=True,
                    strategy="rollback-manager-local-backup",
                    notes=(
                        "FUNC-SPRINT-43 creates an explicit rollback plan from the sandbox ChangeSet.",
                        "Rollback execution remains approval-gated and non-mutating until future restore semantics are implemented.",
                    ),
                ),
                metadata={
                    "sprint": "FUNC-SPRINT-43",
                    "component": "RefactorExecutor",
                    "plan_id": config.plan_id,
                    "plan_step_title": str(plan_step.get("title") or ""),
                    "operation": "normalize_python_trailing_whitespace_and_final_newline",
                    "network_used": False,
                    "external_api_used": False,
                    "raw_source_emitted": False,
                },
            )

            rollback_result = RollbackManager(self.root).create_plan_from_changeset(
                changeset.to_dict(),
                source=f"refactor-sandbox:{sandbox_id}",
                persist=True,
                backup=True,
            )

            tests_result: CommandResult | None = None
            if config.run_tests:
                tests_result = self._run_sandbox_tests(
                    workspace_dir=workspace_dir,
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

            findings: list[Finding] = [Finding("REFACTOR_SANDBOX_POLICY_PASS", "Scoped approval and policy checks allowed sandbox refactor execution.", Severity.INFO, path=target_rel)]
            if not workspace_unchanged:
                findings.append(Finding("REFACTOR_SANDBOX_PRODUCTIVE_WORKSPACE_CHANGED", "Refactor sandbox detected changes in productive workspace target files; this must never happen.", Severity.BLOCK, path=target_rel))
            if not changed_paths:
                findings.append(Finding("REFACTOR_SANDBOX_NO_DETERMINISTIC_CHANGES", "The selected plan produced no deterministic mechanical changes in sandbox.", Severity.BLOCK, path=target_rel))
            else:
                findings.append(Finding("REFACTOR_SANDBOX_CHANGESET_CREATED", "Refactor sandbox produced a ChangeSet from deterministic mechanical changes.", Severity.INFO, path=target_rel, metadata={"changed_files": len(changed_paths)}))
            if rollback_result.ok:
                findings.append(Finding("REFACTOR_SANDBOX_ROLLBACK_PLAN_CREATED", "RollbackManager created a rollback plan for the sandbox ChangeSet.", Severity.INFO, path=rollback_result.data.get("point", {}).get("plan_path")))
            else:
                findings.extend(_prefixed_findings(rollback_result.findings, "REFACTOR_SANDBOX_ROLLBACK_"))
            if tests_result is not None:
                if tests_result.ok:
                    findings.append(Finding("REFACTOR_SANDBOX_TESTS_PASS", "Sandbox tests completed successfully after refactor execution.", Severity.INFO, metadata={"profile": config.test_profile}))
                else:
                    severity = Severity.BLOCK if tests_result.exit_code == ExitCode.BLOCK else Severity.FAIL
                    findings.append(Finding("REFACTOR_SANDBOX_TESTS_FAILED", "Sandbox tests did not pass after refactor execution.", severity, metadata={"profile": config.test_profile, "source_exit_code": int(tests_result.exit_code)}))
            if config.cleanup:
                cleanup_result = self.cleanup(sandbox_id).data.get("summary", {})
                if not bool(cleanup_result.get("removed")):
                    findings.append(Finding("REFACTOR_SANDBOX_CLEANUP_FAILED", "Sandbox cleanup was requested but the sandbox directory was not removed.", Severity.BLOCK, path=_relative(sandbox_dir, self.root)))

            exit_code = exit_code_for_findings(findings)
            summary = {
                **self._base_summary(target_rel, config.plan_id, sandbox_created=True),
                "sandbox_id": sandbox_id,
                "sandbox_workspace": _relative(workspace_dir, self.root),
                "approval_subject": subject,
                "productive_workspace_unchanged": workspace_unchanged,
                "changed_files": len(changed_paths),
                "changeset_id": changeset.changeset_id,
                "changeset_files": len(changeset.files),
                "rollback_plan_created": rollback_result.ok,
                "rollback_id": (rollback_result.data or {}).get("summary", {}).get("rollback_id"),
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
                    "plan": {"summary": (plan_result.data or {}).get("summary", {}), "selected_step": plan_step},
                    "policy": _safe_result_summary(execution_policy),
                    "tests_policy": _safe_result_summary(test_policy),
                    "changeset": changeset.to_dict(),
                    "rollback": _safe_result_summary(rollback_result),
                    "rollback_point": (rollback_result.data or {}).get("point"),
                    "tests": _safe_result_summary(tests_result),
                    "cleanup": cleanup_result,
                    "notes": [
                        "FUNC-SPRINT-43 RefactorExecutor is implemented-initial and limited to deterministic mechanical Python text normalization.",
                        "The productive workspace is never modified by refactor sandbox.",
                        "Semantic refactors, AST rewrites and productive apply remain future work.",
                    ],
                }
            )
            return CommandResult(
                command="refactor sandbox",
                ok=exit_code == ExitCode.PASS,
                exit_code=exit_code,
                message="Refactor sandbox completed successfully." if exit_code == ExitCode.PASS else "Refactor sandbox completed with findings.",
                data=data,
                findings=findings,
            )
        except Exception as exc:  # defensive CLI boundary
            return CommandResult(
                command="refactor sandbox",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Refactor sandbox failed with an unexpected error.",
                data={"summary": self._base_summary(target_rel, config.plan_id, sandbox_created=sandbox_dir.exists()), "sandbox_id": sandbox_id},
                findings=[Finding("REFACTOR_SANDBOX_UNEXPECTED_ERROR", str(exc), Severity.ERROR, path=target_rel)],
            )

    def cleanup(self, sandbox_id: str) -> CommandResult:
        sandbox_id = str(sandbox_id).strip()
        candidate = (self.sandbox_root / sandbox_id).resolve()
        try:
            candidate.relative_to(self.sandbox_root.resolve())
        except ValueError:
            return CommandResult(
                command="refactor sandbox cleanup",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Refactor sandbox cleanup blocked a path outside outputs/sandbox.",
                data={"summary": {"removed": False, "sandbox_id": sandbox_id, "preliminary": True}},
                findings=[Finding("REFACTOR_SANDBOX_CLEANUP_OUTSIDE_ROOT", "Sandbox cleanup path escapes outputs/sandbox.", Severity.BLOCK)],
            )
        if not candidate.exists():
            return CommandResult(
                command="refactor sandbox cleanup",
                ok=True,
                exit_code=ExitCode.PASS,
                message="Refactor sandbox cleanup found no directory to remove.",
                data={"summary": {"removed": False, "already_absent": True, "sandbox_id": sandbox_id, "preliminary": True}},
                findings=[Finding("REFACTOR_SANDBOX_CLEANUP_ALREADY_ABSENT", "Sandbox directory is already absent.", Severity.INFO)],
            )
        shutil.rmtree(candidate)
        return CommandResult(
            command="refactor sandbox cleanup",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Refactor sandbox cleanup removed the sandbox directory.",
            data={"summary": {"removed": True, "sandbox_id": sandbox_id, "path": _relative(candidate, self.root), "preliminary": True}},
            findings=[Finding("REFACTOR_SANDBOX_CLEANUP_PASS", "Sandbox directory was removed.", Severity.INFO, path=_relative(candidate, self.root))],
        )

    def _resolve_target(self, target: str) -> tuple[str, Path, CommandResult | None]:
        if not str(target).strip():
            return "", self.root, CommandResult(
                command="refactor sandbox",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Refactor sandbox requires --target.",
                data={"summary": self._base_summary("", "", sandbox_created=False)},
                findings=[Finding("REFACTOR_SANDBOX_TARGET_REQUIRED", "Provide --target for sandbox refactor execution.", Severity.BLOCK)],
            )
        policy = PolicyEngine(self.root).evaluate(
            PolicyRequest(action="read", path=str(target), dry_run=True, tool_id=None, subject=str(target), metadata={"sprint": "FUNC-SPRINT-43", "component": "RefactorExecutor", "note": "target read validation is non-mutating and must not consume refactor.sandbox approval"})
        )
        if not policy.ok:
            return _display_path(Path(target), self.root), self.root, CommandResult(
                command="refactor sandbox",
                ok=False,
                exit_code=policy.exit_code,
                message="Refactor sandbox blocked by target path policy.",
                data={"summary": self._base_summary(str(target), "", sandbox_created=False), "policy": policy.to_dict()},
                findings=policy.findings,
            )
        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = self.root / target_path
        target_path = target_path.resolve()
        display = _display_path(target_path, self.root)
        try:
            target_path.relative_to(self.root)
        except ValueError:
            return display, target_path, CommandResult(
                command="refactor sandbox",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Refactor sandbox blocked a target outside workspace root.",
                data={"summary": self._base_summary(str(target), "", sandbox_created=False)},
                findings=[Finding("REFACTOR_SANDBOX_TARGET_OUTSIDE_ROOT", "Target path escapes the DevPilot workspace root.", Severity.BLOCK, path=display)],
            )
        if not target_path.exists():
            return display, target_path, CommandResult(
                command="refactor sandbox",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Refactor sandbox target does not exist.",
                data={"summary": self._base_summary(display, "", sandbox_created=False)},
                findings=[Finding("REFACTOR_SANDBOX_TARGET_NOT_FOUND", "Target path does not exist.", Severity.FAIL, path=display)],
            )
        return display, target_path, None

    def _candidate_files(self, target: Path, *, limit: int) -> list[str]:
        paths: list[Path]
        if target.is_file():
            paths = [target]
        else:
            paths = sorted(path for path in target.rglob("*.py") if path.is_file())
        result: list[str] = []
        for path in paths:
            rel = _display_path(path, self.root)
            if _is_excluded(rel):
                continue
            result.append(rel)
            if len(result) >= max(1, min(limit, 250)):
                break
        return result

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

    def _apply_mechanical_refactor(self, *, workspace_dir: Path, target_paths: list[str]) -> list[str]:
        changed: list[str] = []
        for rel in target_paths:
            target = _safe_child(workspace_dir, rel)
            if not target.exists() or target.suffix.lower() != ".py":
                continue
            original = target.read_text(encoding="utf-8", errors="ignore")
            decision = self.secret_guard.scan_text(original, subject=rel)
            if decision.effect.value in {"block", "deny"}:
                # Do not copy or transform secret-like source text into new evidence.
                continue
            newline = "\r\n" if "\r\n" in original else "\n"
            lines = original.splitlines()
            normalized_lines = [line.rstrip(" \t") for line in lines]
            normalized = newline.join(normalized_lines)
            if normalized:
                normalized += newline
            elif original:
                normalized = newline
            if normalized != original:
                target.write_text(normalized, encoding="utf-8")
                changed.append(rel)
        return changed

    def _run_sandbox_tests(self, *, workspace_dir: Path, test_profile: str, timeout_seconds: int, allowlist_path: Path) -> CommandResult:
        profile_args = {
            "smoke": ["-q", "tests/fixtures/smoke_pytest_project"],
            "unit": ["-q", "tests/test_cli_core.py", "tests/test_policy_engine.py"],
        }
        if test_profile not in profile_args:
            return CommandResult(
                command="refactor sandbox tests",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Refactor sandbox blocked an unsupported sandbox test profile.",
                data={"summary": {"profile": test_profile, "supported_profiles": sorted(profile_args), "preliminary": True}},
                findings=[Finding("REFACTOR_SANDBOX_TEST_PROFILE_UNSUPPORTED", "Only fixed sandbox test profiles are supported.", Severity.BLOCK, metadata={"profile": test_profile})],
            )
        return SafeSubprocessRunner(self.root, allowlist=CommandAllowlist(self.root, path=allowlist_path)).run(
            [sys.executable, "-m", "pytest", *profile_args[test_profile]],
            cwd=workspace_dir,
            timeout_seconds=timeout_seconds,
        )

    @staticmethod
    def _base_summary(target: str, plan_id: str, *, sandbox_created: bool) -> dict[str, Any]:
        return {
            "target": target,
            "plan_id": plan_id,
            "sandbox_created": sandbox_created,
            "refactor_applied_to_productive_workspace": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_scope": "outputs/sandbox and .devpilot/rollback metadata only",
            "preliminary": True,
        }


def _write_runtime_allowlist(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "created_by": "FUNC-SPRINT-43",
        "description": "Runtime-only refactor sandbox allowlist. It allows fixed pytest profiles only after tests.run approval.",
        "commands": [
            {
                "command_id": "python.pytest.refactor-sandbox",
                "executable": "python",
                "executable_aliases": [Path(sys.executable).name, "python", "python.exe", "python3", "python3.exe", "py", "py.exe"],
                "args_prefix": ["-m", "pytest"],
                "max_timeout_seconds": 120,
                "description": "Allow fixed pytest profiles inside the refactor sandbox workspace.",
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _new_sandbox_id() -> str:
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return f"refactor-sandbox-{timestamp}-{uuid.uuid4().hex[:8]}"


def _approval_subject(plan_id: str, target_rel: str) -> str:
    return f"refactor:{plan_id}:{target_rel}"


def _find_plan_step(plan_result: CommandResult, plan_id: str) -> dict[str, Any] | None:
    for item in (plan_result.data or {}).get("plan", []):
        if isinstance(item, dict) and item.get("step_id") == plan_id:
            return item
    return None


def _plan_ids(plan_result: CommandResult) -> list[str]:
    return [str(item.get("step_id")) for item in (plan_result.data or {}).get("plan", []) if isinstance(item, dict) and item.get("step_id")]


def _fingerprints(root: Path, target_paths: list[str]) -> dict[str, dict[str, Any] | None]:
    return {path: file_fingerprint(root / path) for path in target_paths}


def _changeset_files(*, target_paths: list[str], before: dict[str, dict[str, Any] | None], after: dict[str, dict[str, Any] | None]) -> list[ChangeSetFile]:
    files: list[ChangeSetFile] = []
    for path in target_paths:
        before_fp = before.get(path)
        after_fp = after.get(path)
        if before_fp is None and after_fp is not None:
            action = "add"
        elif before_fp is not None and after_fp is None:
            action = "delete"
        else:
            action = "modify"
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


def _safe_child(root: Path, rel: str) -> Path:
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Refactor sandbox target escapes workspace: {rel}") from exc
    return candidate


def _is_excluded(rel: str) -> bool:
    parts = Path(rel).parts
    return any(part in {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "outputs", ".devpilot"} for part in parts[:-1])


def _prefixed_findings(findings: list[Finding], prefix: str) -> list[Finding]:
    return [Finding(id=f"{prefix}{finding.id}", message=finding.message, severity=finding.severity, path=finding.path, metadata=finding.metadata) for finding in findings]


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
