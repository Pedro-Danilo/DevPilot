from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from devpilot_core.approval.service import ApprovalCliInput, ApprovalService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest, SecretGuard, configured_external_workspace_roots
from devpilot_core.repo.git_adapter import GitAdapter
from devpilot_core.schemas import SchemaValidator
from devpilot_core.story_execution import StoryExecutionStatus, StoryExecutionStore, StoryExecutionTransitionError
from devpilot_core.repo.governed_git_mutation import (
    GovernedGitMutationAdapter,
    validate_author_email,
    validate_author_name,
    validate_branch_name,
    validate_commit_message,
)

from .ui_workspace_context import UiWorkspaceContextResolver
from .validation_service import ValidationApplicationService
from .workspace_documents_service import ALLOWED_EXTENSIONS, WorkspaceDocumentsApplicationService

CONTROL_ROOT_ENV = "DEVPILOT_UOC006_CONTROL_ROOT"
PLAN_TTL_SECONDS = 1800
MAX_PLAN_FILES = 20
MAX_STORY_PLAN_FILES = 32
MAX_TOTAL_BYTES = 2_097_152
STAGE_ACTION = "git.workspace_stage"
COMMIT_ACTION = "git.workspace_commit"
BRANCH_ACTION = "git.workspace_branch_create"
STAGE_TOOL = "git.workspace.stage"
COMMIT_TOOL = "git.workspace.commit"
BRANCH_TOOL = "git.workspace.branch_create"


class WorkspaceGitOperationsApplicationService:
    """UOC-006 governed Git write boundary for one registered local workspace.

    UOC-006 deliberately implements a narrow Git subset. The browser supplies
    opaque document ids and structured commit/branch fields only. No arbitrary
    Git arguments or shell strings cross this boundary.

    Supported mutations:
      * exact-file staging after immutable plan + approval;
      * exact staged-set commit after a second approval;
      * local branch-ref creation from the current HEAD after approval.

    Explicit no-go:
      reset --hard, rebase, push/force-push, branch deletion, checkout/switch,
      tag creation, arbitrary paths/args, hooks, remote/network operations.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        context_resolver: UiWorkspaceContextResolver | None = None,
        documents: WorkspaceDocumentsApplicationService | None = None,
        approval_auth_store: LocalAuthStore | None = None,
        source_plan_loader: Callable[..., CommandResult] | None = None,
        story_test_plan_loader: Callable[..., CommandResult] | None = None,
        story_quality_report_loader: Callable[..., CommandResult] | None = None,
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.context_resolver = context_resolver or UiWorkspaceContextResolver(self.platform_root)
        self.documents = documents or WorkspaceDocumentsApplicationService(self.platform_root, context_resolver=self.context_resolver)
        self.approvals = ApprovalService(self.platform_root)
        self.secret_guard = SecretGuard(self.platform_root)
        self.validation = ValidationApplicationService(self.platform_root, enforce_workspace_paths=True)
        self.approval_auth_store = approval_auth_store
        self.source_plan_loader = source_plan_loader
        self.story_test_plan_loader = story_test_plan_loader
        self.story_quality_report_loader = story_quality_report_loader

    # ------------------------------------------------------------------ reads
    def status(self) -> CommandResult:
        context, root, failure = self._workspace("workspace git status")
        if failure is not None:
            return failure
        assert context is not None and root is not None
        read = GitAdapter(root).status()
        diff = GitAdapter(root).diff_report(max_files=200)
        mutation = GovernedGitMutationAdapter(root)
        head = mutation.head()
        branch = mutation.current_branch()
        if not read.ok or not head.ok or not branch.ok:
            return self._dependency_block("workspace git status", read if not read.ok else self._git_failure(head if not head.ok else branch))
        data = {
            "summary": {
                "workspace_id": context.active_workspace_id,
                "branch": branch.stdout.strip() or None,
                "head": head.stdout.strip() or None,
                "read_only": True,
                "mutations_performed": False,
                "governed_git_write_available": True,
                "generic_git_write_available": False,
                "push_enabled": False,
                "reset_hard_enabled": False,
                "rebase_enabled": False,
                "branch_delete_enabled": False,
                "preliminary": True,
            },
            "status": (read.data or {}).get("status") or read.data,
            "diff_report": diff.data if diff.ok else None,
            "ui_workspace_context": context.summary(),
        }
        findings = list(read.findings)
        if diff.ok:
            findings.extend(diff.findings)
        else:
            findings.append(Finding("UOC006_DIFF_ENRICHMENT_WARNING", "Workspace Git status remains usable although bounded diff enrichment failed.", Severity.WARNING))
        return CommandResult("workspace git status", True, ExitCode.PASS, "Workspace Git status collected through typed read-only adapters.", data=data, findings=findings)

    def history(self, *, limit: int = 20) -> CommandResult:
        context, root, failure = self._workspace("workspace git history")
        if failure is not None:
            return failure
        assert context is not None and root is not None
        result = GitAdapter(root).log(limit=max(1, min(int(limit), 50)))
        if not result.ok:
            return result
        data = dict(result.data or {})
        data["uoc006"] = {"workspace_id": context.active_workspace_id, "read_only": True, "preliminary": True}
        return CommandResult("workspace git history", True, ExitCode.PASS, "Workspace Git history collected read-only.", data=data, findings=result.findings)

    def compare(self, *, base_ref: str, head_ref: str) -> CommandResult:
        context, root, failure = self._workspace("workspace git compare")
        if failure is not None:
            return failure
        assert context is not None and root is not None
        try:
            comparison = GovernedGitMutationAdapter(root).compare(base_ref=base_ref, head_ref=head_ref)
        except (ValueError, RuntimeError) as exc:
            return self._block("workspace git compare", "UOC006_COMPARE_BLOCK", str(exc))
        return CommandResult(
            "workspace git compare",
            True,
            ExitCode.PASS,
            "Workspace Git compare collected through bounded immutable refs.",
            data={"summary": {"workspace_id": context.active_workspace_id, "read_only": True, "mutations_performed": False}, "compare": comparison},
            findings=[Finding("UOC006_COMPARE_PASS", "Git compare used only HEAD/immutable hexadecimal object identifiers.", Severity.INFO)],
        )

    # ----------------------------------------------------------- staging/commit
    def plan_commit(
        self,
        *,
        document_ids: list[str],
        commit_message: str,
        author_name: str,
        author_email: str,
    ) -> CommandResult:
        context, root, failure = self._workspace("workspace git commit plan")
        if failure is not None:
            return failure
        assert context is not None and root is not None
        try:
            message = validate_commit_message(commit_message)
            name = validate_author_name(author_name)
            email = validate_author_email(author_email)
        except ValueError as exc:
            return self._block("workspace git commit plan", "UOC006_COMMIT_IDENTITY_BLOCK", str(exc))
        ids = [str(item or "").strip() for item in document_ids if str(item or "").strip()]
        ids = list(dict.fromkeys(ids))
        if not ids or len(ids) > MAX_PLAN_FILES:
            return self._block("workspace git commit plan", "UOC006_PLAN_FILE_COUNT_BLOCK", f"Commit plan requires 1-{MAX_PLAN_FILES} opaque document ids.")

        mutation = GovernedGitMutationAdapter(root)
        head_result, branch_result = mutation.head(), mutation.current_branch()
        if not head_result.ok or not branch_result.ok:
            return self._dependency_block("workspace git commit plan", self._git_failure(head_result if not head_result.ok else branch_result))
        head = head_result.stdout.strip()
        branch = branch_result.stdout.strip()
        if not branch:
            return self._block("workspace git commit plan", "UOC006_DETACHED_HEAD_BLOCK", "Commit planning requires a named local branch; detached HEAD is blocked.")
        try:
            already_staged = mutation.staged_paths()
        except RuntimeError as exc:
            return self._block("workspace git commit plan", "UOC006_STAGED_INVENTORY_BLOCK", str(exc))
        if already_staged:
            return self._block("workspace git commit plan", "UOC006_PREEXISTING_STAGED_BLOCK", "Existing staged paths must be resolved before creating a governed staging plan.", metadata={"staged_paths": already_staged})

        files: list[dict[str, Any]] = []
        total_bytes = 0
        combined_diff: list[str] = []
        for document_id in ids:
            read = self.documents.read_document(document_id)
            if not read.ok:
                return self._dependency_block("workspace git commit plan", read)
            document = dict((read.data or {}).get("document") or {})
            relative = str(document.get("relative_path") or "")
            extension = str(document.get("extension") or "").lower()
            if extension not in ALLOWED_EXTENSIONS:
                return self._block("workspace git commit plan", "UOC006_EXTENSION_BLOCK", "Only allowlisted text documents can enter a Git staging plan.", path=relative)
            content = str(document.get("content") or "")
            secret = self.secret_guard.scan_text(content, subject=relative)
            if secret.effect.value == "block":
                return self._block("workspace git commit plan", "UOC006_SECRET_STAGING_BLOCK", "Secret-like content cannot be staged.", path=relative)
            current_sha = str(document.get("sha256") or "")
            size = int(document.get("size_bytes") or len(content.encode("utf-8")))
            total_bytes += size
            if total_bytes > MAX_TOTAL_BYTES:
                return self._block("workspace git commit plan", "UOC006_PLAN_SIZE_BLOCK", "Selected files exceed the bounded UOC-006 staging budget.", metadata={"maximum_bytes": MAX_TOTAL_BYTES})
            state_result = GitAdapter(root).file_status(relative)
            if not state_result.ok:
                return self._dependency_block("workspace git commit plan", state_result)
            state = dict((state_result.data or {}).get("status") or {})
            if state.get("clean"):
                return self._block("workspace git commit plan", "UOC006_CLEAN_FILE_BLOCK", "A staging plan may include only currently changed allowlisted documents.", path=relative)
            if state.get("staged"):
                return self._block("workspace git commit plan", "UOC006_PRESTAGED_FILE_BLOCK", "A governed plan cannot inherit already staged content.", path=relative)
            if state.get("deleted") or state.get("renamed"):
                return self._block("workspace git commit plan", "UOC006_DELETE_RENAME_BLOCK", "Initial UOC-006 does not stage deleted or renamed paths.", path=relative)
            diff_result = GitAdapter(root).file_diff(relative, base_ref="HEAD", max_bytes=262_144)
            if not diff_result.ok:
                return self._dependency_block("workspace git commit plan", diff_result)
            diff_text = str((diff_result.data or {}).get("diff") or "")
            files.append({
                "document_id": document_id,
                "relative_path": relative,
                "extension": extension,
                "working_sha256": current_sha,
                "size_bytes": size,
                "git_status": state,
                "diff_sha256": _sha_text(diff_text),
            })
            combined_diff.append(f"### {relative}\n{diff_text}")

        core = {
            "kind": "commit",
            "workspace_id": context.active_workspace_id,
            "branch": branch,
            "head_before": head,
            "files": files,
            "commit": {"message": message, "author_name": name, "author_email": email},
            "constraints": {"max_files": MAX_PLAN_FILES, "max_total_bytes": MAX_TOTAL_BYTES, "hooks_executed": False, "push_enabled": False},
        }
        plan_hash = _sha_json(core)
        plan_id = f"gplan_{plan_hash[:32]}"
        plan = {
            "schema_id": "devpilot.post_h_eval_002.uoc_006.git_commit_plan.v1",
            "plan_id": plan_id,
            "plan_hash": plan_hash,
            **core,
            "combined_diff": "\n\n".join(combined_diff),
            "combined_diff_sha256": _sha_text("\n\n".join(combined_diff)),
            "created_at": _now(),
            "expires_at": _future(PLAN_TTL_SECONDS),
            "preliminary": True,
        }
        control = self._control_root(root)
        if control is None:
            return self._block("workspace git commit plan", "UOC006_CONTROL_ROOT_BLOCK", "UOC-006 control root must resolve outside the active workspace.")
        existing = self._read_json(control / "plans" / f"{plan_id}.json")
        if existing and str(existing.get("plan_hash")) != plan_hash:
            return self._block("workspace git commit plan", "UOC006_PLAN_COLLISION_BLOCK", "Existing Git plan id has incompatible content.")
        schema_block = self._schema_block("workspace git commit plan", "WorkspaceGitPlan", plan)
        if schema_block is not None:
            return schema_block
        if not existing:
            self._write_json(control / "plans" / f"{plan_id}.json", plan)
        return CommandResult(
            "workspace git commit plan",
            True,
            ExitCode.PASS,
            "Immutable governed Git staging/commit plan created without mutating index or history.",
            data={"summary": {"plan_id": plan_id, "plan_hash": plan_hash, "files_total": len(files), "mutations_performed": False, "approval_required": True}, "plan": plan},
            findings=[Finding("UOC006_COMMIT_PLAN_PASS", "Git plan is hash-bound to HEAD, branch, exact document ids/content hashes, commit message and identity.", Severity.INFO)],
        )

    def get_plan(self, *, plan_id: str) -> CommandResult:
        context, root, failure = self._workspace("workspace git plan status")
        if failure is not None:
            return failure
        assert root is not None
        plan = self._load_plan(root, plan_id)
        if plan is None:
            return self._block("workspace git plan status", "UOC006_PLAN_NOT_FOUND_BLOCK", "Governed Git plan was not found or is malformed.")
        if _expired(plan.get("expires_at")):
            return self._block("workspace git plan status", "UOC006_PLAN_EXPIRED_BLOCK", "Governed Git plan has expired.")
        return CommandResult("workspace git plan status", True, ExitCode.PASS, "Governed Git plan loaded.", data={"plan": plan}, findings=[])

    def request_stage_approval(self, *, plan_id: str, plan_hash: str, actor: str, reason: str, ttl_minutes: int = 15) -> CommandResult:
        plan_result = self.get_plan(plan_id=plan_id)
        if not plan_result.ok:
            return plan_result
        plan = dict((plan_result.data or {}).get("plan") or {})
        if str(plan.get("plan_hash")) != str(plan_hash or ""):
            return self._block("workspace git stage approval request", "UOC006_PLAN_HASH_MISMATCH_BLOCK", "Stage approval hash does not match immutable Git plan.")
        recheck = self._recheck_commit_plan(plan, require_unstaged=True)
        if not recheck.ok:
            return recheck
        actor = _actor(actor)
        reason = str(reason or "").strip()
        if not reason:
            return self._block("workspace git stage approval request", "UOC006_APPROVAL_REASON_BLOCK", "A human-readable reason is required.")
        scope = self._stage_scope(plan, actor=actor)
        result = self.approvals.request(ApprovalCliInput(tool_id=STAGE_TOOL, action=STAGE_ACTION, subject=plan_id, actor=actor, reason=reason, scope=json.dumps(scope, sort_keys=True), ttl_minutes=max(1, min(int(ttl_minutes), 30)), metadata={"source": "uoc-006", "interface": "ui", "plan_hash": plan_hash}))
        return self._decorate_approval(result, phase="stage", binding_hash=plan_hash)

    def stage(self, *, plan_id: str, plan_hash: str, approval_id: str, actor: str) -> CommandResult:
        plan_result = self.get_plan(plan_id=plan_id)
        if not plan_result.ok:
            return plan_result
        plan = dict((plan_result.data or {}).get("plan") or {})
        if str(plan.get("plan_hash")) != str(plan_hash or ""):
            return self._block("workspace git stage", "UOC006_PLAN_HASH_MISMATCH_BLOCK", "Stage hash does not match immutable Git plan.")
        recheck = self._recheck_commit_plan(plan, require_unstaged=True)
        if not recheck.ok:
            return recheck
        context, root, failure = self._workspace("workspace git stage")
        if failure is not None:
            return failure
        assert root is not None
        actor = _actor(actor)
        policy = PolicyEngine(self.platform_root, allowed_external_roots=configured_external_workspace_roots(), approval_auth_store=self.approval_auth_store).evaluate(
            PolicyRequest(action=STAGE_ACTION, path=str(root), text=str(plan.get("commit", {}).get("message") or ""), dry_run=False, approval_id=str(approval_id or ""), tool_id=STAGE_TOOL, subject=plan_id, actor=actor, role_at_decision="owner", subject_hash=plan_hash, interface="ui", metadata=self._stage_scope(plan, actor=actor))
        )
        if not policy.ok:
            return CommandResult("workspace git stage", False, ExitCode.BLOCK, "Approval/policy binding blocked Git staging.", data={"policy": policy.to_dict()}, findings=policy.findings)
        paths = [str(item["relative_path"]) for item in plan["files"]]
        mutation = GovernedGitMutationAdapter(root)
        executed = mutation.stage_paths(paths)
        if not executed.ok:
            return self._block("workspace git stage", "UOC006_GIT_ADD_BLOCK", "Typed Git staging command failed.", metadata={"stderr": executed.stderr[-1000:]})
        try:
            staged = mutation.staged_paths()
            if sorted(staged) != sorted(paths):
                mutation.unstage_paths(paths)
                return self._block("workspace git stage", "UOC006_STAGED_SET_MISMATCH_BLOCK", "Staged set differs from the approved exact file set.", metadata={"expected": paths, "actual": staged})
            precommit = self._validate_staged(plan, root)
            if not precommit["ok"]:
                mutation.unstage_paths(paths)
                return self._block("workspace git stage", "UOC006_PRECOMMIT_BLOCK", "Staged content failed deterministic UOC-006 pre-commit validation; staging was compensated.", metadata={"checks": precommit["checks"]})
            index_fingerprint = str(precommit["index_fingerprint"])
        except Exception as exc:
            mutation.unstage_paths(paths)
            return self._block("workspace git stage", "UOC006_STAGE_VERIFY_BLOCK", f"Staging verification failed and exact files were unstaged: {exc}")
        stage_execution_id = f"gstage_{_sha_text(plan_hash + '|' + approval_id + '|' + index_fingerprint)[:32]}"
        commit_intent_hash = _sha_json({"plan_hash": plan_hash, "stage_execution_id": stage_execution_id, "head_before": plan["head_before"], "index_fingerprint": index_fingerprint, "commit": plan["commit"]})
        record = {
            "schema_id": "devpilot.post_h_eval_002.uoc_006.git_stage_execution.v1",
            "stage_execution_id": stage_execution_id,
            "status": "staged",
            "plan_id": plan_id,
            "plan_hash": plan_hash,
            "stage_approval_id": approval_id,
            "actor": actor,
            "workspace_id": plan.get("workspace_id"),
            "branch": plan["branch"],
            "head_before": plan["head_before"],
            "files": plan["files"],
            "commit": plan["commit"],
            "index_fingerprint": index_fingerprint,
            "commit_intent_hash": commit_intent_hash,
            "precommit": precommit,
            "created_at": _now(),
            "git_stage": True,
            "git_commit": False,
            "source_content_mutated_by_git": False,
            "push_performed": False,
        }
        control = self._control_root(root)
        assert control is not None
        schema_block = self._schema_block("workspace git stage", "WorkspaceGitExecution", record)
        if schema_block is not None:
            mutation.unstage_paths(paths)
            return schema_block
        self._write_json(control / "records" / f"{stage_execution_id}.json", record)
        return CommandResult("workspace git stage", True, ExitCode.PASS, "Approved exact files were staged and verified.", data={"summary": {"stage_execution_id": stage_execution_id, "files_total": len(paths), "git_stage": True, "git_commit": False}, "stage_execution": record}, findings=[Finding("UOC006_STAGE_PASS", "Git index contains exactly the approval-bound file set and passed pre-commit checks.", Severity.INFO)])

    def request_commit_approval(self, *, stage_execution_id: str, actor: str, reason: str, ttl_minutes: int = 15) -> CommandResult:
        record_result = self.get_execution(execution_id=stage_execution_id)
        if not record_result.ok:
            return record_result
        record = dict((record_result.data or {}).get("execution") or {})
        if record.get("status") != "staged":
            return self._block("workspace git commit approval request", "UOC006_STAGE_STATE_BLOCK", "Commit approval requires a currently staged UOC-006 execution.")
        verify = self._recheck_stage_record(record)
        if not verify.ok:
            return verify
        actor = _actor(actor)
        reason = str(reason or "").strip()
        if not reason:
            return self._block("workspace git commit approval request", "UOC006_APPROVAL_REASON_BLOCK", "A human-readable commit approval reason is required.")
        binding_hash = str(record["commit_intent_hash"])
        scope = self._commit_scope(record, actor=actor)
        result = self.approvals.request(ApprovalCliInput(tool_id=COMMIT_TOOL, action=COMMIT_ACTION, subject=stage_execution_id, actor=actor, reason=reason, scope=json.dumps(scope, sort_keys=True), ttl_minutes=max(1, min(int(ttl_minutes), 30)), metadata={"source": "uoc-006", "interface": "ui", "commit_intent_hash": binding_hash}))
        return self._decorate_approval(result, phase="commit", binding_hash=binding_hash)

    def commit(self, *, stage_execution_id: str, approval_id: str, actor: str) -> CommandResult:
        record_result = self.get_execution(execution_id=stage_execution_id)
        if not record_result.ok:
            return record_result
        stage_record = dict((record_result.data or {}).get("execution") or {})
        if stage_record.get("status") != "staged":
            return self._block("workspace git commit", "UOC006_STAGE_STATE_BLOCK", "Only a current staged execution can be committed.")
        verify = self._recheck_stage_record(stage_record)
        if not verify.ok:
            return verify
        context, root, failure = self._workspace("workspace git commit")
        if failure is not None:
            return failure
        assert root is not None
        actor = _actor(actor)
        binding_hash = str(stage_record["commit_intent_hash"])
        policy = PolicyEngine(self.platform_root, allowed_external_roots=configured_external_workspace_roots(), approval_auth_store=self.approval_auth_store).evaluate(
            PolicyRequest(action=COMMIT_ACTION, path=str(root), text=str(stage_record.get("commit", {}).get("message") or ""), dry_run=False, approval_id=str(approval_id or ""), tool_id=COMMIT_TOOL, subject=stage_execution_id, actor=actor, role_at_decision="owner", subject_hash=binding_hash, interface="ui", metadata=self._commit_scope(stage_record, actor=actor))
        )
        if not policy.ok:
            return CommandResult("workspace git commit", False, ExitCode.BLOCK, "Approval/policy binding blocked Git commit.", data={"policy": policy.to_dict()}, findings=policy.findings)
        mutation = GovernedGitMutationAdapter(root)
        precommit = self._validate_staged(stage_record, root)
        if not precommit["ok"] or precommit["index_fingerprint"] != stage_record["index_fingerprint"]:
            return self._block("workspace git commit", "UOC006_COMMIT_RECHECK_BLOCK", "Staged content changed or failed deterministic pre-commit validation after approval.", metadata={"checks": precommit["checks"]})
        commit_spec = dict(stage_record.get("commit") or {})
        executed = mutation.commit(message=str(commit_spec.get("message") or ""), author_name=str(commit_spec.get("author_name") or ""), author_email=str(commit_spec.get("author_email") or ""))
        if not executed.ok:
            return self._block("workspace git commit", "UOC006_GIT_COMMIT_BLOCK", "Typed Git commit failed; staged content remains for operator review.", metadata={"stderr": executed.stderr[-1500:]})
        head_after_result = mutation.head()
        if not head_after_result.ok:
            return self._block("workspace git commit", "UOC006_POST_COMMIT_HEAD_BLOCK", "Commit completed but post-commit HEAD could not be verified.")
        head_after = head_after_result.stdout.strip()
        expected_paths = sorted(str(item["relative_path"]) for item in stage_record["files"])
        try:
            committed_paths = sorted(mutation.committed_paths(head_after))
            parent = mutation.parent_of(head_after)
            staged_after = mutation.staged_paths()
        except Exception as exc:
            return self._block("workspace git commit", "UOC006_POST_COMMIT_VERIFY_BLOCK", f"Commit completed but postcondition verification failed: {exc}")
        if parent != str(stage_record["head_before"]) or committed_paths != expected_paths or staged_after:
            return self._block("workspace git commit", "UOC006_POST_COMMIT_CONTRACT_BLOCK", "Post-commit parent/files/index do not match the approved commit intent.", metadata={"parent": parent, "expected_parent": stage_record["head_before"], "committed_paths": committed_paths, "expected_paths": expected_paths, "staged_after": staged_after})
        commit_execution_id = f"gcommit_{head_after[:32]}"
        result_record = {
            "schema_id": "devpilot.post_h_eval_002.uoc_006.git_commit_execution.v1",
            "execution_id": commit_execution_id,
            "status": "committed",
            "stage_execution_id": stage_execution_id,
            "plan_id": stage_record["plan_id"],
            "plan_hash": stage_record["plan_hash"],
            "stage_approval_id": stage_record["stage_approval_id"],
            "commit_approval_id": approval_id,
            "actor": actor,
            "workspace_id": stage_record.get("workspace_id"),
            "branch": stage_record["branch"],
            "head_before": stage_record["head_before"],
            "commit": head_after,
            "parent": parent,
            "files": stage_record["files"],
            "committed_paths": committed_paths,
            "commit_identity": commit_spec,
            "index_fingerprint": stage_record["index_fingerprint"],
            "commit_intent_hash": binding_hash,
            "precommit": precommit,
            "created_at": _now(),
            "git_stage": True,
            "git_commit": True,
            "push_performed": False,
            "hooks_executed": False,
        }
        control = self._control_root(root)
        assert control is not None
        schema_block = self._schema_block("workspace git commit", "WorkspaceGitExecution", result_record)
        if schema_block is not None:
            return schema_block
        self._write_json(control / "records" / f"{commit_execution_id}.json", result_record)
        stage_record["status"] = "committed"
        stage_record["commit_execution_id"] = commit_execution_id
        stage_record["commit"] = commit_spec
        self._write_json(control / "records" / f"{stage_execution_id}.json", stage_record)
        return CommandResult("workspace git commit", True, ExitCode.PASS, "Approved staged content was committed with explicit identity and verified postconditions.", data={"summary": {"execution_id": commit_execution_id, "commit": head_after, "parent": parent, "files_total": len(committed_paths), "git_commit": True, "push_performed": False}, "execution": result_record}, findings=[Finding("UOC006_COMMIT_PASS", "Commit parent, exact committed file set and empty staged index match the approved intent.", Severity.INFO)])

    # ------------------------------------------------------------- branches
    def plan_branch_create(self, *, branch_name: str) -> CommandResult:
        context, root, failure = self._workspace("workspace git branch plan")
        if failure is not None:
            return failure
        assert context is not None and root is not None
        try:
            branch = validate_branch_name(branch_name)
        except ValueError as exc:
            return self._block("workspace git branch plan", "UOC006_BRANCH_NAME_BLOCK", str(exc))
        mutation = GovernedGitMutationAdapter(root)
        head, current = mutation.head(), mutation.current_branch()
        if not head.ok or not current.ok:
            return self._block("workspace git branch plan", "UOC006_BRANCH_PREFLIGHT_BLOCK", "Current HEAD/branch could not be read.")
        if mutation.branch_exists(branch):
            return self._block("workspace git branch plan", "UOC006_BRANCH_EXISTS_BLOCK", "Requested branch already exists.")
        try:
            if mutation.staged_paths() or mutation.dirty_paths():
                return self._block("workspace git branch plan", "UOC006_BRANCH_DIRTY_WORKTREE_BLOCK", "Initial governed branch creation requires a clean working tree and index.")
        except RuntimeError as exc:
            return self._block("workspace git branch plan", "UOC006_BRANCH_STATUS_BLOCK", str(exc))
        core = {"kind": "branch-create", "workspace_id": context.active_workspace_id, "branch_name": branch, "head_before": head.stdout.strip(), "current_branch": current.stdout.strip()}
        plan_hash = _sha_json(core)
        plan_id = f"gbranch_{plan_hash[:32]}"
        plan = {"schema_id": "devpilot.post_h_eval_002.uoc_006.git_branch_plan.v1", "plan_id": plan_id, "plan_hash": plan_hash, **core, "created_at": _now(), "expires_at": _future(PLAN_TTL_SECONDS), "preliminary": True}
        control = self._control_root(root)
        if control is None:
            return self._block("workspace git branch plan", "UOC006_CONTROL_ROOT_BLOCK", "UOC-006 control root must resolve outside active workspace.")
        schema_block = self._schema_block("workspace git branch plan", "WorkspaceGitPlan", plan)
        if schema_block is not None:
            return schema_block
        self._write_json(control / "plans" / f"{plan_id}.json", plan)
        return CommandResult("workspace git branch plan", True, ExitCode.PASS, "Controlled local branch creation plan generated without changing refs.", data={"plan": plan, "summary": {"mutations_performed": False, "approval_required": True}}, findings=[Finding("UOC006_BRANCH_PLAN_PASS", "Branch plan is bound to current HEAD and a constrained local branch name.", Severity.INFO)])

    def request_branch_approval(self, *, plan_id: str, plan_hash: str, actor: str, reason: str, ttl_minutes: int = 15) -> CommandResult:
        plan_result = self.get_plan(plan_id=plan_id)
        if not plan_result.ok:
            return plan_result
        plan = dict((plan_result.data or {}).get("plan") or {})
        if plan.get("kind") != "branch-create" or str(plan.get("plan_hash")) != str(plan_hash or ""):
            return self._block("workspace git branch approval request", "UOC006_BRANCH_PLAN_BINDING_BLOCK", "Branch approval request does not match an immutable branch plan.")
        actor = _actor(actor); reason = str(reason or "").strip()
        if not reason:
            return self._block("workspace git branch approval request", "UOC006_APPROVAL_REASON_BLOCK", "A branch approval reason is required.")
        scope = self._branch_scope(plan, actor=actor)
        result = self.approvals.request(ApprovalCliInput(tool_id=BRANCH_TOOL, action=BRANCH_ACTION, subject=plan_id, actor=actor, reason=reason, scope=json.dumps(scope, sort_keys=True), ttl_minutes=max(1, min(int(ttl_minutes), 30)), metadata={"source": "uoc-006", "interface": "ui", "plan_hash": plan_hash}))
        return self._decorate_approval(result, phase="branch-create", binding_hash=plan_hash)

    def create_branch(self, *, plan_id: str, plan_hash: str, approval_id: str, actor: str) -> CommandResult:
        plan_result = self.get_plan(plan_id=plan_id)
        if not plan_result.ok:
            return plan_result
        plan = dict((plan_result.data or {}).get("plan") or {})
        if plan.get("kind") != "branch-create" or str(plan.get("plan_hash")) != str(plan_hash or ""):
            return self._block("workspace git branch create", "UOC006_BRANCH_PLAN_BINDING_BLOCK", "Branch create does not match immutable branch plan.")
        context, root, failure = self._workspace("workspace git branch create")
        if failure is not None:
            return failure
        assert root is not None
        mutation = GovernedGitMutationAdapter(root)
        head = mutation.head()
        if not head.ok or head.stdout.strip() != str(plan["head_before"]):
            return self._block("workspace git branch create", "UOC006_BRANCH_STALE_HEAD_BLOCK", "HEAD changed after branch plan creation.")
        try:
            if mutation.staged_paths() or mutation.dirty_paths():
                return self._block("workspace git branch create", "UOC006_BRANCH_DIRTY_WORKTREE_BLOCK", "Branch create requires a clean worktree/index at execution time.")
        except RuntimeError as exc:
            return self._block("workspace git branch create", "UOC006_BRANCH_STATUS_BLOCK", str(exc))
        actor = _actor(actor)
        policy = PolicyEngine(self.platform_root, allowed_external_roots=configured_external_workspace_roots(), approval_auth_store=self.approval_auth_store).evaluate(PolicyRequest(action=BRANCH_ACTION, path=str(root), text=str(plan["branch_name"]), dry_run=False, approval_id=str(approval_id or ""), tool_id=BRANCH_TOOL, subject=plan_id, actor=actor, role_at_decision="owner", subject_hash=plan_hash, interface="ui", metadata=self._branch_scope(plan, actor=actor)))
        if not policy.ok:
            return CommandResult("workspace git branch create", False, ExitCode.BLOCK, "Approval/policy binding blocked branch creation.", data={"policy": policy.to_dict()}, findings=policy.findings)
        executed = mutation.create_branch(branch_name=str(plan["branch_name"]), expected_head=str(plan["head_before"]))
        if not executed.ok or not mutation.branch_exists(str(plan["branch_name"])):
            return self._block("workspace git branch create", "UOC006_BRANCH_CREATE_BLOCK", "Controlled local branch ref creation failed.", metadata={"stderr": executed.stderr[-1000:]})
        execution_id = f"gbranch_exec_{_sha_text(plan_hash + '|' + approval_id)[:24]}"
        record = {"schema_id": "devpilot.post_h_eval_002.uoc_006.git_branch_execution.v1", "execution_id": execution_id, "status": "branch-created", "plan_id": plan_id, "plan_hash": plan_hash, "approval_id": approval_id, "actor": actor, "branch_name": plan["branch_name"], "head": plan["head_before"], "current_branch_unchanged": True, "checkout_performed": False, "push_performed": False, "created_at": _now()}
        control = self._control_root(root); assert control is not None
        schema_block = self._schema_block("workspace git branch create", "WorkspaceGitExecution", record)
        if schema_block is not None:
            return schema_block
        self._write_json(control / "records" / f"{execution_id}.json", record)
        return CommandResult("workspace git branch create", True, ExitCode.PASS, "Approved local branch ref was created without checkout or push.", data={"execution": record, "summary": {"branch_name": plan["branch_name"], "head": plan["head_before"], "checkout_performed": False, "push_performed": False}}, findings=[Finding("UOC006_BRANCH_CREATE_PASS", "Branch ref creation did not checkout, push or delete refs.", Severity.INFO)])

    # ---------------------------------------------------- GSDLC-10-D story Git
    def plan_story_commit(
        self,
        *,
        quality_report_id: str,
        quality_report_hash: str,
        commit_message: str,
        author_name: str,
        author_email: str,
        actor: str,
        actor_role: str,
        authority_source: str = "human-session",
    ) -> CommandResult:
        """Build an immutable story-bound CommitPlan without mutating Git.

        The plan binds the current COMMIT_READY StoryExecution to the exact
        SourceChangePlan, APPROVED StoryTestPlan and non-stale Quality PASS.
        Git write authority is intentionally *not* granted by this operation.
        """
        command = "story git commit plan"
        role_failure = self._story_human_role(command, actor_role, authority_source, allow_developer=True)
        if role_failure is not None:
            return role_failure
        context, root, failure = self._workspace(command)
        if failure is not None:
            return failure
        assert context is not None and root is not None
        try:
            message = validate_commit_message(commit_message)
            name = validate_author_name(author_name)
            email = validate_author_email(author_email)
        except ValueError as exc:
            return self._story_block(command, "GSDLC10D_COMMIT_IDENTITY_BLOCK", str(exc))

        chain, chain_failure = self._story_chain(
            root=root,
            workspace_id=str(context.active_workspace_id or ""),
            quality_report_id=quality_report_id,
            quality_report_hash=quality_report_hash,
        )
        if chain_failure is not None:
            return chain_failure
        assert chain is not None
        source_plan = chain["source_plan"]
        exact_paths = sorted({str(path).replace("\\", "/") for path in source_plan.get("exact_path_allowlist") or [] if str(path).strip()})
        if not exact_paths or len(exact_paths) > MAX_STORY_PLAN_FILES:
            return self._story_block(command, "GSDLC10D_EXACT_PATH_SET_BLOCK", f"Story CommitPlan requires 1-{MAX_STORY_PLAN_FILES} exact approved paths.")

        mutation = GovernedGitMutationAdapter(root)
        head_result, branch_result = mutation.head(), mutation.current_branch()
        if not head_result.ok or not branch_result.ok:
            return self._story_block(command, "GSDLC10D_GIT_IDENTITY_BLOCK", "Current Git HEAD/branch could not be resolved through the typed adapter.")
        head = head_result.stdout.strip(); branch = branch_result.stdout.strip()
        if not branch:
            return self._story_block(command, "GSDLC10D_DETACHED_HEAD_BLOCK", "Story commit planning requires a named local branch.")
        try:
            staged = sorted(mutation.staged_paths())
            dirty = sorted(mutation.dirty_paths())
        except RuntimeError as exc:
            return self._story_block(command, "GSDLC10D_GIT_INVENTORY_BLOCK", str(exc))
        if staged:
            return self._story_block(command, "GSDLC10D_PREEXISTING_STAGED_BLOCK", "Index must be empty before a story CommitPlan is created.", metadata={"staged_paths": staged})
        if dirty != exact_paths:
            return self._story_block(command, "GSDLC10D_UNEXPECTED_DIRTY_PATH_BLOCK", "Dirty Git path set must equal the approved SourceChangePlan exactly.", metadata={"expected_paths": exact_paths, "actual_dirty_paths": dirty})

        expected_files, expected_failure = self._story_expected_files(source_plan, root)
        if expected_failure is not None:
            return expected_failure
        assert expected_files is not None
        context_pack = StoryExecutionStore(root, workspace_id=str(context.active_workspace_id)).load_context() or {}
        requirement_ids = sorted({str(row.get("target_id") or "") for row in context_pack.get("fragments") or [] if isinstance(row, dict) and row.get("kind") == "requirement" and str(row.get("target_id") or "").strip()})
        quality = chain["quality_report"]
        test_evidence_ids = sorted({str(ref) for job in quality.get("required_job_results") or [] if isinstance(job, dict) for ref in (job.get("artifact_refs") or []) if str(ref).strip()})
        traceability = {
            "requirement_ids": requirement_ids,
            "story_id": chain["story_state"].get("story_id"),
            "story_execution_id": chain["story_state"].get("execution_id"),
            "source_change_plan_id": source_plan.get("plan_id"),
            "source_change_plan_hash": source_plan.get("plan_hash"),
            "story_test_plan_id": chain["story_test_plan"].get("test_plan_id"),
            "story_test_plan_hash": chain["story_test_plan"].get("test_plan_hash"),
            "story_quality_report_id": quality.get("report_id"),
            "story_quality_report_hash": quality.get("report_hash"),
            "test_evidence_ids": test_evidence_ids,
        }
        core = {
            "schema_id": "SCHEMA-DEVPL-GSDLC-10-D-STORY-COMMIT-PLAN-V1",
            "schema_version": "1.0.0",
            "workspace_id": str(context.active_workspace_id),
            "story_execution_id": chain["story_state"].get("execution_id"),
            "story_id": chain["story_state"].get("story_id"),
            "source_change_plan_id": source_plan.get("plan_id"),
            "source_change_plan_hash": source_plan.get("plan_hash"),
            "story_test_plan_id": chain["story_test_plan"].get("test_plan_id"),
            "story_test_plan_hash": chain["story_test_plan"].get("test_plan_hash"),
            "story_quality_report_id": quality.get("report_id"),
            "story_quality_report_hash": quality.get("report_hash"),
            "quality_inputs_hash": quality.get("inputs_hash"),
            "branch": branch,
            "head_before": head,
            "exact_paths": exact_paths,
            "include_paths": exact_paths,
            "exclude_paths": [],
            "files": expected_files,
            "commit": {"message": message, "author_name": name, "author_email": email, "message_editable_before_plan": True},
            "approval": {
                "required": True,
                "required_role": "owner",
                "stage_approval_required": True,
                "commit_approval_required": True,
                "stage_and_commit_separate": True,
                "authority_source": "server-rbac-policy-approval",
                "agent_granted_authority": False,
                "model_route_granted_authority": False,
            },
            "traceability": traceability,
            "safety": {
                "exact_staging_only": True,
                "git_add_all_enabled": False,
                "push_enabled": False,
                "force_push_enabled": False,
                "rebase_enabled": False,
                "reset_hard_enabled": False,
                "shell_enabled": False,
                "full_regression_started": False,
            },
        }
        plan_hash = _sha_json(core)
        plan_id = f"story-commit-plan-{plan_hash[:24]}"
        plan = {**core, "commit_plan_id": plan_id, "commit_plan_hash": plan_hash, "created_at_utc": _now(), "expires_at_utc": _future(PLAN_TTL_SECONDS)}
        schema_block = self._schema_block(command, "GSDLC10DStoryCommitPlan", plan)
        if schema_block is not None:
            return self._story_wrap_schema_block(command, schema_block)
        control = self._story_control_root(root)
        if control is None:
            return self._story_block(command, "GSDLC10D_CONTROL_ROOT_BLOCK", "Story Git control root must resolve outside the active workspace.")
        path = control / "plans" / f"{plan_id}.json"
        existing = self._read_json(path)
        if existing and str(existing.get("commit_plan_hash")) != plan_hash:
            return self._story_block(command, "GSDLC10D_PLAN_COLLISION_BLOCK", "Existing story CommitPlan id has incompatible immutable content.")
        if not existing:
            self._write_json(path, plan)
        return self._story_pass(command, "Immutable story CommitPlan created; Git index/history remain untouched.", {"commit_plan": existing or plan, "idempotent": bool(existing), "mutations_performed": False})

    def get_story_commit_plan(self, *, commit_plan_id: str) -> CommandResult:
        command = "story git commit plan get"
        _, root, failure = self._workspace(command)
        if failure is not None:
            return failure
        assert root is not None
        plan = self._load_story_plan(root, commit_plan_id)
        if plan is None:
            return self._story_block(command, "GSDLC10D_PLAN_NOT_FOUND_BLOCK", "Story CommitPlan was not found or is malformed.")
        if _expired(plan.get("expires_at_utc")):
            return self._story_block(command, "GSDLC10D_PLAN_EXPIRED_BLOCK", "Story CommitPlan has expired.")
        return self._story_pass(command, "Story CommitPlan loaded read-only.", {"commit_plan": plan, "read_only": True, "mutations_performed": False})

    def request_story_stage_approval(self, *, commit_plan_id: str, commit_plan_hash: str, actor: str, actor_role: str, reason: str, ttl_minutes: int = 15, authority_source: str = "human-session") -> CommandResult:
        command = "story git stage approval request"
        role_failure = self._story_human_role(command, actor_role, authority_source, allow_developer=False)
        if role_failure is not None:
            return role_failure
        plan, failure = self._story_plan_exact(commit_plan_id, commit_plan_hash)
        if failure is not None:
            return failure
        assert plan is not None
        recheck = self._recheck_story_plan(plan, require_unstaged=True)
        if not recheck.ok:
            return recheck
        reason = str(reason or "").strip()
        if not reason:
            return self._story_block(command, "GSDLC10D_APPROVAL_REASON_BLOCK", "A human-readable stage approval reason is required.")
        scope = self._story_stage_scope(plan, actor=actor)
        result = self.approvals.request(ApprovalCliInput(tool_id=STAGE_TOOL, action=STAGE_ACTION, subject=commit_plan_id, actor=_actor(actor), reason=reason, scope=json.dumps(scope, sort_keys=True), ttl_minutes=max(1, min(int(ttl_minutes), 30)), metadata={"source":"gsdlc-10-d","interface":"ui","commit_plan_hash":commit_plan_hash,"authority_source":"human-session"}))
        return self._story_decorate_approval(result, phase="stage", binding_hash=commit_plan_hash)

    def stage_story(self, *, commit_plan_id: str, commit_plan_hash: str, approval_id: str, actor: str, actor_role: str, authority_source: str = "human-session") -> CommandResult:
        command = "story git stage"
        role_failure = self._story_human_role(command, actor_role, authority_source, allow_developer=False)
        if role_failure is not None:
            return role_failure
        plan, failure = self._story_plan_exact(commit_plan_id, commit_plan_hash)
        if failure is not None:
            return failure
        assert plan is not None
        recheck = self._recheck_story_plan(plan, require_unstaged=True)
        if not recheck.ok:
            return recheck
        _, root, workspace_failure = self._workspace(command)
        if workspace_failure is not None:
            return workspace_failure
        assert root is not None
        actor = _actor(actor)
        scope = self._story_stage_scope(plan, actor=actor)
        policy = PolicyEngine(self.platform_root, allowed_external_roots=configured_external_workspace_roots(), approval_auth_store=self.approval_auth_store).evaluate(PolicyRequest(action=STAGE_ACTION, path=str(root), text=str(plan.get("commit",{}).get("message") or ""), dry_run=False, approval_id=str(approval_id or ""), tool_id=STAGE_TOOL, subject=commit_plan_id, actor=actor, role_at_decision="owner", subject_hash=commit_plan_hash, interface="ui", metadata=scope))
        if not policy.ok:
            return CommandResult(command, False, ExitCode.BLOCK, "Approval/policy binding blocked exact story staging.", data={"policy":policy.to_dict(),"full_regression_started":False}, findings=policy.findings)
        paths = list(plan["exact_paths"])
        mutation = GovernedGitMutationAdapter(root)
        executed = mutation.stage_paths(paths, max_paths=MAX_STORY_PLAN_FILES)
        if not executed.ok:
            return self._story_block(command, "GSDLC10D_GIT_STAGE_BLOCK", "Typed exact Git staging failed.", metadata={"stderr": executed.stderr[-1200:]})
        validation = self._validate_story_staged(plan, root)
        if not validation["ok"]:
            mutation.unstage_paths(paths, max_paths=MAX_STORY_PLAN_FILES)
            return self._story_block(command, "GSDLC10D_STAGED_VERIFY_BLOCK", "Staged index failed exact story validation; exact staging was compensated.", metadata={"checks": validation["checks"]})
        fingerprint = str(validation["index_fingerprint"])
        stage_execution_id = f"story-stage-{_sha_text(commit_plan_hash+'|'+approval_id+'|'+fingerprint)[:24]}"
        commit_intent_hash = _sha_json({"commit_plan_hash":commit_plan_hash,"stage_execution_id":stage_execution_id,"head_before":plan["head_before"],"index_fingerprint":fingerprint,"commit":plan["commit"]})
        staging_manifest = {
            "schema_id":"DEVPL-GSDLC-10-D-STAGING-MANIFEST-V1",
            "stage_execution_id":stage_execution_id,
            "commit_plan_id":commit_plan_id,
            "commit_plan_hash":commit_plan_hash,
            "stage_approval_id":approval_id,
            "exact_paths":paths,
            "index_fingerprint":fingerprint,
            "checks":validation["checks"],
            "git_stage":True,
            "git_commit":False,
            "git_add_all":False,
            "shell":False,
            "push":False,
            "created_at_utc":_now(),
        }
        record = {
            "schema_id":"DEVPL-GSDLC-10-D-STAGE-EXECUTION-V1",
            "stage_execution_id":stage_execution_id,
            "status":"STAGED",
            "commit_plan_id":commit_plan_id,
            "commit_plan_hash":commit_plan_hash,
            "stage_approval_id":approval_id,
            "actor":actor,
            "actor_role":"owner",
            "workspace_id":plan["workspace_id"],
            "story_execution_id":plan["story_execution_id"],
            "branch":plan["branch"],
            "head_before":plan["head_before"],
            "exact_paths":paths,
            "files":plan["files"],
            "commit":plan["commit"],
            "index_fingerprint":fingerprint,
            "commit_intent_hash":commit_intent_hash,
            "staging_manifest":staging_manifest,
            "created_at_utc":_now(),
            "git_stage":True,"git_commit":False,"push_performed":False,"shell":False,"full_regression_started":False,
        }
        control=self._story_control_root(root); assert control is not None
        self._write_json(control/"records"/f"{stage_execution_id}.json",record)
        self._write_json(control/"evidence"/f"{stage_execution_id}_staging_manifest.json",staging_manifest)
        return self._story_pass(command,"Exact approval-bound story paths were staged and verified.",{"stage_execution":record,"staging_manifest":staging_manifest})

    def request_story_commit_approval(self, *, stage_execution_id: str, actor: str, actor_role: str, reason: str, ttl_minutes: int = 15, authority_source: str = "human-session") -> CommandResult:
        command="story git commit approval request"
        role_failure=self._story_human_role(command,actor_role,authority_source,allow_developer=False)
        if role_failure is not None:return role_failure
        record,failure=self._story_stage_record(stage_execution_id)
        if failure is not None:return failure
        assert record is not None
        verify=self._recheck_story_stage_record(record)
        if not verify.ok:return verify
        reason=str(reason or "").strip()
        if not reason:return self._story_block(command,"GSDLC10D_APPROVAL_REASON_BLOCK","A human-readable commit approval reason is required.")
        actor=_actor(actor); binding_hash=str(record["commit_intent_hash"]); scope=self._story_commit_scope(record,actor=actor)
        result=self.approvals.request(ApprovalCliInput(tool_id=COMMIT_TOOL,action=COMMIT_ACTION,subject=stage_execution_id,actor=actor,reason=reason,scope=json.dumps(scope,sort_keys=True),ttl_minutes=max(1,min(int(ttl_minutes),30)),metadata={"source":"gsdlc-10-d","interface":"ui","commit_intent_hash":binding_hash,"authority_source":"human-session"}))
        return self._story_decorate_approval(result,phase="commit",binding_hash=binding_hash)

    def commit_story(self, *, stage_execution_id: str, approval_id: str, actor: str, actor_role: str, authority_source: str = "human-session") -> CommandResult:
        command="story git commit"
        role_failure=self._story_human_role(command,actor_role,authority_source,allow_developer=False)
        if role_failure is not None:return role_failure
        stage_record,failure=self._story_stage_record(stage_execution_id)
        if failure is not None:return failure
        assert stage_record is not None
        verify=self._recheck_story_stage_record(stage_record)
        if not verify.ok:return verify
        plan_result=self.get_story_commit_plan(commit_plan_id=str(stage_record["commit_plan_id"]))
        if not plan_result.ok:return plan_result
        plan=dict(plan_result.data["commit_plan"])
        # Re-evaluate Quality/TestPlan/SourcePlan/Story immediately before commit.
        chain,chain_failure=self._story_chain(root=self._workspace(command)[1],workspace_id=str(plan["workspace_id"]),quality_report_id=str(plan["story_quality_report_id"]),quality_report_hash=str(plan["story_quality_report_hash"]))
        if chain_failure is not None:return chain_failure
        _,root,workspace_failure=self._workspace(command)
        if workspace_failure is not None:return workspace_failure
        assert root is not None
        actor=_actor(actor); binding_hash=str(stage_record["commit_intent_hash"]); scope=self._story_commit_scope(stage_record,actor=actor)
        policy=PolicyEngine(self.platform_root,allowed_external_roots=configured_external_workspace_roots(),approval_auth_store=self.approval_auth_store).evaluate(PolicyRequest(action=COMMIT_ACTION,path=str(root),text=str(stage_record.get("commit",{}).get("message") or ""),dry_run=False,approval_id=str(approval_id or ""),tool_id=COMMIT_TOOL,subject=stage_execution_id,actor=actor,role_at_decision="owner",subject_hash=binding_hash,interface="ui",metadata=scope))
        if not policy.ok:return CommandResult(command,False,ExitCode.BLOCK,"Approval/policy binding blocked governed story commit.",data={"policy":policy.to_dict(),"full_regression_started":False},findings=policy.findings)
        validation=self._validate_story_staged(plan,root)
        if not validation["ok"] or validation["index_fingerprint"]!=stage_record["index_fingerprint"]:
            return self._story_block(command,"GSDLC10D_COMMIT_RECHECK_BLOCK","Staged content changed after stage approval or no longer matches the exact CommitPlan.",metadata={"checks":validation["checks"]})
        mutation=GovernedGitMutationAdapter(root); spec=dict(plan["commit"])
        executed=mutation.commit(message=str(spec["message"]),author_name=str(spec["author_name"]),author_email=str(spec["author_email"]))
        if not executed.ok:return self._story_block(command,"GSDLC10D_GIT_COMMIT_BLOCK","Typed governed Git commit failed; no push or destructive recovery was attempted.",metadata={"stderr":executed.stderr[-1200:]})
        head_result=mutation.head()
        if not head_result.ok:return self._story_block(command,"GSDLC10D_POST_COMMIT_HEAD_BLOCK","Commit completed but resulting HEAD could not be verified.")
        head_after=head_result.stdout.strip(); expected=sorted(plan["exact_paths"])
        try:
            committed=sorted(mutation.committed_paths(head_after)); parent=mutation.parent_of(head_after); staged_after=mutation.staged_paths(); dirty_after=mutation.dirty_paths()
        except Exception as exc:return self._story_block(command,"GSDLC10D_POST_COMMIT_VERIFY_BLOCK",f"Commit completed but Git postconditions could not be verified: {exc}")
        if parent!=plan["head_before"] or committed!=expected or staged_after or dirty_after:
            return self._story_block(command,"GSDLC10D_POST_COMMIT_CONTRACT_BLOCK","Commit tree, parent or clean-worktree postconditions differ from the approved CommitPlan.",metadata={"parent":parent,"expected_parent":plan["head_before"],"committed_paths":committed,"expected_paths":expected,"staged_after":staged_after,"dirty_after":dirty_after})
        commit_record={
            "schema_id":"SCHEMA-DEVPL-GSDLC-10-D-GIT-COMMIT-RECORD-V1","schema_version":"1.0.0",
            "commit_record_id":f"story-commit-record-{head_after[:24]}","commit_hash":head_after,"parent_hash":parent,
            "workspace_id":plan["workspace_id"],"story_execution_id":plan["story_execution_id"],"story_id":plan["story_id"],
            "commit_plan_id":plan["commit_plan_id"],"commit_plan_hash":plan["commit_plan_hash"],"stage_execution_id":stage_execution_id,
            "stage_approval_id":stage_record["stage_approval_id"],"commit_approval_id":approval_id,"actor":actor,"actor_role":"owner","authority_source":"human-session",
            "message":spec["message"],"author_name":spec["author_name"],"author_email":spec["author_email"],"committed_paths":committed,
            "source_change_plan_id":plan["source_change_plan_id"],"source_change_plan_hash":plan["source_change_plan_hash"],
            "story_test_plan_id":plan["story_test_plan_id"],"story_test_plan_hash":plan["story_test_plan_hash"],
            "story_quality_report_id":plan["story_quality_report_id"],"story_quality_report_hash":plan["story_quality_report_hash"],
            "requirement_ids":list(plan["traceability"]["requirement_ids"]),"test_evidence_ids":list(plan["traceability"]["test_evidence_ids"]),
            "traceability_complete":bool(plan["story_id"] and plan["source_change_plan_id"] and plan["story_test_plan_id"] and plan["story_quality_report_id"]),
            "worktree_clean":True,"index_clean":True,"push_performed":False,"force_push_performed":False,"rebase_performed":False,"reset_hard_performed":False,"shell":False,
            "agent_granted_authority":False,"model_route_granted_authority":False,"full_regression_started":False,"created_at_utc":_now(),
        }
        schema_block=self._schema_block(command,"GSDLC10DGitCommitRecord",commit_record)
        if schema_block is not None:return self._story_wrap_schema_block(command,schema_block)
        trace={
            "schema_id":"DEVPL-GSDLC-10-D-COMMIT-TRACEABILITY-V1","commit_hash":head_after,
            "requirement_ids":commit_record["requirement_ids"],"story_id":plan["story_id"],"story_execution_id":plan["story_execution_id"],
            "source_change_plan_id":plan["source_change_plan_id"],"story_test_plan_id":plan["story_test_plan_id"],"test_evidence_ids":commit_record["test_evidence_ids"],
            "story_quality_report_id":plan["story_quality_report_id"],"commit_record_id":commit_record["commit_record_id"],"traceability_complete":commit_record["traceability_complete"],
        }
        control=self._story_control_root(root); assert control is not None
        execution_id=f"story-commit-{head_after[:24]}"
        execution={"schema_id":"DEVPL-GSDLC-10-D-COMMIT-EXECUTION-V1","execution_id":execution_id,"status":"COMMITTED","commit_record":commit_record,"commit_traceability":trace,"staging_manifest":stage_record["staging_manifest"],"created_at_utc":_now()}
        self._write_json(control/"records"/f"{execution_id}.json",execution)
        self._write_json(control/"evidence"/f"{execution_id}_commit_record.json",commit_record)
        self._write_json(control/"evidence"/f"{execution_id}_commit_traceability.json",trace)
        stage_record["status"]="COMMITTED"; stage_record["commit_execution_id"]=execution_id; stage_record["commit_approval_id"]=approval_id
        self._write_json(control/"records"/f"{stage_execution_id}.json",stage_record)
        store=StoryExecutionStore(root,workspace_id=str(plan["workspace_id"])); state=store.load_state(); transitioned_payload=None
        if state is not None and state.status is StoryExecutionStatus.COMMIT_READY:
            try:
                transitioned=state.transition(StoryExecutionStatus.DONE,actor_id=actor,observed_at_utc=_now()); transitioned_payload=store.save_state(transitioned)
            except StoryExecutionTransitionError:
                transitioned_payload=None
        return self._story_pass(command,"Governed story commit created and verified with exact traceability and a clean worktree.",{"execution":execution,"git_commit_record":commit_record,"commit_traceability":trace,"story_execution_state":transitioned_payload})

    def get_story_git_execution(self, *, execution_id: str) -> CommandResult:
        command="story git execution get"
        _,root,failure=self._workspace(command)
        if failure is not None:return failure
        assert root is not None
        if not str(execution_id).startswith(("story-stage-","story-commit-")):
            return self._story_block(command,"GSDLC10D_EXECUTION_ID_BLOCK","Story Git execution id is not recognized.")
        control=self._story_control_root(root)
        record=self._read_json(control/"records"/f"{execution_id}.json") if control is not None else None
        if record is None:return self._story_block(command,"GSDLC10D_EXECUTION_NOT_FOUND_BLOCK","Story Git execution was not found.")
        return self._story_pass(command,"Story Git execution loaded read-only.",{"execution":record,"read_only":True,"mutations_performed":False})

    def recover_story_commit_ready_context(self) -> CommandResult:
        """Recover current COMMIT_READY bindings server-side without Git authority."""
        command="story git context recover"
        context,root,failure=self._workspace(command)
        if failure is not None:return failure
        assert context is not None and root is not None
        if self.story_quality_report_loader is None or self.story_test_plan_loader is None or self.source_plan_loader is None:
            return self._story_block(command,"GSDLC10D_LOADER_BLOCK","Story Git context dependencies are unavailable.")
        state=StoryExecutionStore(root,workspace_id=str(context.active_workspace_id)).load_state()
        if state is None or state.status is not StoryExecutionStatus.COMMIT_READY:
            return self._story_block(command,"GSDLC10D_COMMIT_READY_BLOCK","Current StoryExecution is not COMMIT_READY.")
        # Search the bounded local Quality store by asking the platform callback
        # for the current story. This callback is intentionally read-only.
        finder=getattr(self,"story_commit_ready_finder",None)
        if not callable(finder):
            return self._story_block(command,"GSDLC10D_CONTEXT_FINDER_BLOCK","Server-side COMMIT_READY finder is unavailable.")
        result=finder(story_execution_id=state.execution_id)
        if not result.ok:return result
        data=dict(result.data or {})
        return self._story_pass(command,"COMMIT_READY Quality/TestPlan/SourcePlan bindings recovered read-only.",{**data,"story_execution_id":state.execution_id,"story_id":state.story_id,"read_only":True,"mutations_performed":False,"git_authority_granted":False,"agent_granted_authority":False,"model_route_granted_authority":False})

    def _story_plan_exact(self, commit_plan_id: str, commit_plan_hash: str) -> tuple[dict[str, Any] | None, CommandResult | None]:
        loaded=self.get_story_commit_plan(commit_plan_id=commit_plan_id)
        if not loaded.ok:return None,loaded
        plan=dict(loaded.data["commit_plan"])
        if str(plan.get("commit_plan_hash"))!=str(commit_plan_hash or ""):
            return None,self._story_block("story git plan recheck","GSDLC10D_PLAN_HASH_MISMATCH_BLOCK","Provided CommitPlan hash is stale or incorrect.")
        core={k:v for k,v in plan.items() if k not in {"commit_plan_id","commit_plan_hash","created_at_utc","expires_at_utc"}}
        if _sha_json(core)!=str(plan.get("commit_plan_hash")):
            return None,self._story_block("story git plan recheck","GSDLC10D_PLAN_TAMPER_BLOCK","Stored CommitPlan immutable hash no longer matches its contents.")
        return plan,None

    def _recheck_story_plan(self, plan: dict[str, Any], *, require_unstaged: bool) -> CommandResult:
        command="story git plan recheck"
        if _expired(plan.get("expires_at_utc")):return self._story_block(command,"GSDLC10D_PLAN_EXPIRED_BLOCK","Story CommitPlan expired before mutation.")
        context,root,failure=self._workspace(command)
        if failure is not None:return failure
        assert context is not None and root is not None
        chain,chain_failure=self._story_chain(root=root,workspace_id=str(context.active_workspace_id),quality_report_id=str(plan["story_quality_report_id"]),quality_report_hash=str(plan["story_quality_report_hash"]))
        if chain_failure is not None:return chain_failure
        mutation=GovernedGitMutationAdapter(root); head=mutation.head(); branch=mutation.current_branch()
        if not head.ok or not branch.ok or head.stdout.strip()!=str(plan["head_before"]) or branch.stdout.strip()!=str(plan["branch"]):
            return self._story_block(command,"GSDLC10D_HEAD_BRANCH_STALE_BLOCK","HEAD or branch changed after CommitPlan creation.")
        try:
            staged=sorted(mutation.staged_paths()); dirty=sorted(mutation.dirty_paths())
        except RuntimeError as exc:return self._story_block(command,"GSDLC10D_GIT_INVENTORY_BLOCK",str(exc))
        if require_unstaged and staged:return self._story_block(command,"GSDLC10D_PREEXISTING_STAGED_BLOCK","Index is no longer empty before exact story staging.",metadata={"staged_paths":staged})
        if dirty!=sorted(plan["exact_paths"]):return self._story_block(command,"GSDLC10D_UNEXPECTED_DIRTY_PATH_BLOCK","Dirty path set drifted from approved CommitPlan.",metadata={"expected_paths":plan["exact_paths"],"actual_dirty_paths":dirty})
        expected_files,expected_failure=self._story_expected_files(chain["source_plan"],root)
        if expected_failure is not None:return expected_failure
        if expected_files!=plan["files"]:return self._story_block(command,"GSDLC10D_SOURCE_CONTENT_STALE_BLOCK","Current source content/state differs from the approved story CommitPlan.")
        return self._story_pass(command,"Story CommitPlan still matches Quality, story state, HEAD and exact dirty paths.",{"stale":False,"mutations_performed":False})

    def _story_chain(self, *, root: Path | None, workspace_id: str, quality_report_id: str, quality_report_hash: str) -> tuple[dict[str, Any] | None, CommandResult | None]:
        command="story git authority chain"
        if root is None or self.source_plan_loader is None or self.story_test_plan_loader is None or self.story_quality_report_loader is None:
            return None,self._story_block(command,"GSDLC10D_LOADER_BLOCK","Story Git authority-chain dependencies are unavailable.")
        qres=self.story_quality_report_loader(report_id=quality_report_id)
        if not qres.ok:return None,self._story_dependency(command,qres,"GSDLC10D_QUALITY_LOAD_BLOCK")
        quality=dict((qres.data or {}).get("story_quality_report") or {})
        if str(quality.get("report_hash"))!=str(quality_report_hash or "") or quality.get("stale") is True or quality.get("decision")!="PASS" or quality.get("commit_ready") is not True:
            return None,self._story_block(command,"GSDLC10D_STALE_QUALITY_BLOCK","Quality Report must be current, exact, PASS and COMMIT_READY immediately before Git authority is evaluated.")
        test_id=str(quality.get("story_test_plan_id") or ""); test_hash=str(quality.get("story_test_plan_hash") or "")
        tres=self.story_test_plan_loader(test_plan_id=test_id)
        if not tres.ok:return None,self._story_dependency(command,tres,"GSDLC10D_TEST_PLAN_LOAD_BLOCK")
        test_plan=dict((tres.data or {}).get("story_test_plan") or {})
        if test_plan.get("status")!="APPROVED" or str(test_plan.get("test_plan_hash"))!=test_hash:
            return None,self._story_block(command,"GSDLC10D_TEST_PLAN_BINDING_BLOCK","Quality Report no longer binds an exact APPROVED StoryTestPlan.")
        source_id=str(test_plan.get("source_change_plan_id") or ""); source_hash=str(test_plan.get("source_change_plan_hash") or "")
        sres=self.source_plan_loader(plan_id=source_id)
        if not sres.ok:return None,self._story_dependency(command,sres,"GSDLC10D_SOURCE_PLAN_LOAD_BLOCK")
        source=dict((sres.data or {}).get("plan") or {})
        if str(source.get("plan_hash"))!=source_hash or str(source.get("story_execution_id"))!=str(test_plan.get("story_execution_id") or ""):
            return None,self._story_block(command,"GSDLC10D_SOURCE_PLAN_BINDING_BLOCK","StoryTestPlan no longer binds the exact SourceChangePlan/story execution.")
        store=StoryExecutionStore(root,workspace_id=workspace_id); state=store.load_state()
        if state is None or state.status is not StoryExecutionStatus.COMMIT_READY or state.execution_id!=str(test_plan.get("story_execution_id") or "") or state.story_id!=str(test_plan.get("story_id") or state.story_id):
            return None,self._story_block(command,"GSDLC10D_COMMIT_READY_BLOCK","Current StoryExecution must be the exact COMMIT_READY story bound to Quality/TestPlan/SourcePlan.")
        return {"quality_report":quality,"story_test_plan":test_plan,"source_plan":source,"story_state":state.to_dict()},None

    def _story_expected_files(self, source_plan: dict[str, Any], root: Path) -> tuple[list[dict[str, Any]] | None, CommandResult | None]:
        command="story git source postimage recheck"
        expected:dict[str,dict[str,Any]]={}
        for change in source_plan.get("changes") or []:
            op=str(change.get("operation") or "").upper(); source=str(change.get("source_path") or "").replace("\\","/"); target=str(change.get("target_path") or "").replace("\\","/")
            if op=="RENAME" and source and source!=target:
                expected[source]={"relative_path":source,"expected_state":"deleted","change_operation":"RENAME_SOURCE","approved_content_sha256":str(change.get("preimage_sha256") or "")}
            if target:
                expected[target]={"relative_path":target,"expected_state":"present","change_operation":op,"approved_content_sha256":str(change.get("postimage_sha256") or "")}
        exact=sorted(str(x).replace("\\","/") for x in source_plan.get("exact_path_allowlist") or [])
        if sorted(expected)!=exact:
            return None,self._story_block(command,"GSDLC10D_SOURCE_PLAN_PATH_BINDING_BLOCK","SourceChangePlan change rows do not resolve exactly to its path allowlist.",metadata={"expected_from_changes":sorted(expected),"allowlist":exact})
        rows=[]
        for rel in exact:
            row=dict(expected[rel]); path=(root/rel).resolve()
            try:path.relative_to(root.resolve())
            except ValueError:return None,self._story_block(command,"GSDLC10D_PATH_ESCAPE_BLOCK","Approved story path escaped active workspace.",path=rel)
            if row["expected_state"]=="deleted":
                if path.exists():return None,self._story_block(command,"GSDLC10D_DELETED_PATH_STALE_BLOCK","Approved rename source unexpectedly exists before staging.",path=rel)
                row["working_content_sha256"]=None
            else:
                if not path.is_file():return None,self._story_block(command,"GSDLC10D_POSTIMAGE_MISSING_BLOCK","Approved source target is missing before staging.",path=rel)
                actual=self._story_semantic_sha(path)
                if actual!=row["approved_content_sha256"]:return None,self._story_block(command,"GSDLC10D_POSTIMAGE_STALE_BLOCK","Current source content does not match approved SourceChangePlan postimage.",path=rel,metadata={"expected":row["approved_content_sha256"],"actual":actual})
                row["working_content_sha256"]=actual
            rows.append(row)
        return rows,None

    def _validate_story_staged(self, plan: dict[str, Any], root: Path) -> dict[str, Any]:
        mutation=GovernedGitMutationAdapter(root); checks=[]; expected=sorted(plan["exact_paths"])
        try:staged=sorted(mutation.staged_paths())
        except Exception as exc:return {"ok":False,"checks":[{"check":"exact_staged_paths","status":"BLOCK","error":str(exc)}],"index_fingerprint":""}
        checks.append({"check":"exact_staged_paths","status":"PASS" if staged==expected else "BLOCK","expected":expected,"actual":staged})
        diff_check=mutation.cached_diff_check(); checks.append({"check":"git_diff_cached_check","status":"PASS" if diff_check.ok else "BLOCK","stderr":diff_check.stderr[-1000:]})
        fingerprints=[]
        for item in plan["files"]:
            rel=str(item["relative_path"]); expected_state=str(item["expected_state"])
            if expected_state=="deleted":
                try:mutation.index_file_bytes(rel); present=True
                except Exception:present=False
                checks.append({"check":"index_deleted","path":rel,"status":"BLOCK" if present else "PASS"})
                fingerprints.append({"path":rel,"sha256":"DELETED"})
            else:
                try:raw=mutation.index_file_bytes(rel)
                except Exception as exc:checks.append({"check":"index_blob","path":rel,"status":"BLOCK","error":str(exc)});continue
                try:text=raw.decode("utf-8-sig").replace("\r\n","\n").replace("\r","\n"); canonical=text.encode("utf-8")
                except UnicodeDecodeError:checks.append({"check":"utf8","path":rel,"status":"BLOCK"});continue
                sha=hashlib.sha256(canonical).hexdigest(); fingerprints.append({"path":rel,"sha256":sha})
                checks.append({"check":"approved_postimage","path":rel,"status":"PASS" if sha==item["approved_content_sha256"] else "BLOCK","expected":item["approved_content_sha256"],"actual":sha})
                eq=mutation.worktree_index_equivalent(rel); checks.append({"check":"git_worktree_index_equivalence","path":rel,"status":"PASS" if eq.ok else "BLOCK","git_exit_code":eq.exit_code})
                secret=self.secret_guard.scan_text(text,subject=rel); checks.append({"check":"secret_guard","path":rel,"status":"PASS" if secret.effect.value!="block" else "BLOCK"})
        ok=all(row.get("status")=="PASS" for row in checks)
        return {"ok":ok,"checks":checks,"index_fingerprint":_sha_json(sorted(fingerprints,key=lambda x:x["path"]))}

    def _recheck_story_stage_record(self, record: dict[str, Any]) -> CommandResult:
        command="story git staged recheck"
        if record.get("status")!="STAGED":return self._story_block(command,"GSDLC10D_STAGE_STATE_BLOCK","Commit approval requires a current STAGED story execution.")
        plan_result=self.get_story_commit_plan(commit_plan_id=str(record["commit_plan_id"]))
        if not plan_result.ok:return plan_result
        plan=dict(plan_result.data["commit_plan"])
        context,root,failure=self._workspace(command)
        if failure is not None:return failure
        assert context is not None and root is not None
        chain,chain_failure=self._story_chain(root=root,workspace_id=str(context.active_workspace_id),quality_report_id=str(plan["story_quality_report_id"]),quality_report_hash=str(plan["story_quality_report_hash"]))
        if chain_failure is not None:return chain_failure
        mutation=GovernedGitMutationAdapter(root); head=mutation.head(); branch=mutation.current_branch()
        if not head.ok or not branch.ok or head.stdout.strip()!=record["head_before"] or branch.stdout.strip()!=record["branch"]:
            return self._story_block(command,"GSDLC10D_STAGED_HEAD_BRANCH_BLOCK","HEAD/branch changed after story staging.")
        validation=self._validate_story_staged(plan,root)
        if not validation["ok"] or validation["index_fingerprint"]!=record["index_fingerprint"]:
            return self._story_block(command,"GSDLC10D_STAGED_CONTENT_DRIFT_BLOCK","Staged content no longer matches the approval-bound index fingerprint.",metadata={"checks":validation["checks"]})
        return self._story_pass(command,"Story staged execution remains exact and Quality-current.",{"stale":False})

    def _story_stage_record(self, execution_id: str) -> tuple[dict[str, Any] | None, CommandResult | None]:
        loaded=self.get_story_git_execution(execution_id=execution_id)
        if not loaded.ok:return None,loaded
        record=dict(loaded.data["execution"])
        if record.get("status")!="STAGED":return None,self._story_block("story git staged record","GSDLC10D_STAGE_STATE_BLOCK","Story stage execution is not currently STAGED.")
        return record,None

    def _load_story_plan(self, root: Path, plan_id: str) -> dict[str, Any] | None:
        if not str(plan_id).startswith("story-commit-plan-"):return None
        control=self._story_control_root(root)
        return self._read_json(control/"plans"/f"{plan_id}.json") if control is not None else None

    def _story_control_root(self, workspace_root: Path) -> Path | None:
        base=self._control_root(workspace_root)
        return (base/"gsdlc10d_story_git") if base is not None else None

    @staticmethod
    def _story_semantic_sha(path: Path) -> str:
        raw=path.read_bytes()
        try:text=raw.decode("utf-8-sig").replace("\r\n","\n").replace("\r","\n")
        except UnicodeDecodeError:return hashlib.sha256(raw).hexdigest()
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _story_human_role(command: str, actor_role: str, authority_source: str, *, allow_developer: bool) -> CommandResult | None:
        if authority_source!="human-session" or authority_source.startswith(("agent","model")):
            return WorkspaceGitOperationsApplicationService._story_block(command,"GSDLC10D_AGENT_MODEL_AUTHORITY_BLOCK","Agent/model route cannot grant stage/commit authority.")
        allowed={"owner","developer"} if allow_developer else {"owner"}
        if actor_role not in allowed:
            return WorkspaceGitOperationsApplicationService._story_block(command,"GSDLC10D_WRONG_ROLE_BLOCK",f"Operation requires {'owner/developer' if allow_developer else 'owner'} authenticated human role.")
        return None

    @staticmethod
    def _story_stage_scope(plan: dict[str, Any], *, actor: str) -> dict[str, Any]:
        return {"actor_id":actor,"role_at_decision":"owner","tool_id":STAGE_TOOL,"action":STAGE_ACTION,"action_id":STAGE_ACTION,"subject":plan["commit_plan_id"],"subject_hash":plan["commit_plan_hash"],"commit_plan_id":plan["commit_plan_id"],"commit_plan_hash":plan["commit_plan_hash"],"story_execution_id":plan["story_execution_id"],"head_before":plan["head_before"],"branch":plan["branch"],"paths":plan["exact_paths"],"interface":"ui","scope_type":"gsdlc10d-story-exact-staging-plan"}

    @staticmethod
    def _story_commit_scope(record: dict[str, Any], *, actor: str) -> dict[str, Any]:
        return {"actor_id":actor,"role_at_decision":"owner","tool_id":COMMIT_TOOL,"action":COMMIT_ACTION,"action_id":COMMIT_ACTION,"subject":record["stage_execution_id"],"subject_hash":record["commit_intent_hash"],"stage_execution_id":record["stage_execution_id"],"commit_plan_id":record["commit_plan_id"],"commit_plan_hash":record["commit_plan_hash"],"story_execution_id":record["story_execution_id"],"head_before":record["head_before"],"branch":record["branch"],"index_fingerprint":record["index_fingerprint"],"paths":record["exact_paths"],"interface":"ui","scope_type":"gsdlc10d-story-exact-commit-intent"}

    @staticmethod
    def _story_decorate_approval(result: CommandResult, *, phase: str, binding_hash: str) -> CommandResult:
        data=dict(result.data or {}); data["gsdlc10d"]={"phase":phase,"binding_hash":binding_hash,"authority_source":"server-rbac-policy-approval","agent_granted_authority":False,"model_route_granted_authority":False,"full_regression_started":False}
        return CommandResult(result.command,result.ok,result.exit_code,result.message,data=data,findings=result.findings)

    @staticmethod
    def _story_pass(command: str, message: str, data: dict[str, Any]) -> CommandResult:
        return CommandResult(command,True,ExitCode.PASS,message,data={**data,"network_used":False,"external_api_used":False,"full_regression_started":False},findings=[Finding("GSDLC10D_PASS",message,Severity.INFO)])

    @staticmethod
    def _story_block(command: str, finding_id: str, message: str, *, path: str | None = None, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command,False,ExitCode.BLOCK,message,data={"mutations_performed":False,"network_used":False,"external_api_used":False,"full_regression_started":False},findings=[Finding(finding_id,message,Severity.BLOCK,path=path,metadata=metadata or {})])

    @staticmethod
    def _story_dependency(command: str, result: CommandResult, code: str) -> CommandResult:
        return CommandResult(command,False,ExitCode.BLOCK,result.message,data=result.data,findings=[*result.findings,Finding(code,"A required GSDLC-10-D authority-chain dependency blocked execution.",Severity.BLOCK)])

    @staticmethod
    def _story_wrap_schema_block(command: str, result: CommandResult) -> CommandResult:
        return CommandResult(command,False,ExitCode.BLOCK,"GSDLC-10-D evidence failed its registered schema.",data={"full_regression_started":False},findings=result.findings)

    # -------------------------------------------------------------- records
    def get_execution(self, *, execution_id: str) -> CommandResult:
        context, root, failure = self._workspace("workspace git execution status")
        if failure is not None:
            return failure
        assert root is not None
        control = self._control_root(root)
        if control is None or not execution_id.startswith(("gstage_", "gcommit_", "gbranch_exec_")):
            return self._block("workspace git execution status", "UOC006_EXECUTION_ID_BLOCK", "Execution id is not a recognized UOC-006 opaque identifier.")
        record = self._read_json(control / "records" / f"{execution_id}.json")
        if not record:
            return self._block("workspace git execution status", "UOC006_EXECUTION_NOT_FOUND_BLOCK", "UOC-006 execution record was not found.")
        return CommandResult("workspace git execution status", True, ExitCode.PASS, "UOC-006 execution record loaded from local control root.", data={"execution": record}, findings=[])

    # -------------------------------------------------------------- internals
    def _workspace(self, command: str):
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or context.active_workspace_root is None:
            return context, None, self._block(command, "UOC006_WORKSPACE_CONTEXT_BLOCK", "UOC-006 requires an explicitly configured valid active workspace.")
        root = context.active_workspace_root.resolve()
        if not (root / ".git").exists():
            return context, root, self._block(command, "UOC006_GIT_REPOSITORY_BLOCK", "Active workspace must be a local Git repository.")
        return context, root, None

    def _control_root(self, workspace_root: Path) -> Path | None:
        raw = os.environ.get(CONTROL_ROOT_ENV, "").strip()
        root = Path(raw).expanduser().resolve() if raw else (self.platform_root / "outputs" / "uoc006_control").resolve()
        try:
            root.relative_to(workspace_root.resolve())
            return None
        except ValueError:
            return root

    def _load_plan(self, root: Path, plan_id: str) -> dict[str, Any] | None:
        if not plan_id.startswith(("gplan_", "gbranch_")):
            return None
        control = self._control_root(root)
        if control is None:
            return None
        return self._read_json(control / "plans" / f"{plan_id}.json")

    def _recheck_commit_plan(self, plan: dict[str, Any], *, require_unstaged: bool) -> CommandResult:
        context, root, failure = self._workspace("workspace git plan recheck")
        if failure is not None:
            return failure
        assert root is not None
        if plan.get("kind") != "commit" or _expired(plan.get("expires_at")):
            return self._block("workspace git plan recheck", "UOC006_PLAN_EXPIRED_BLOCK", "Commit plan is expired or has wrong kind.")
        mutation = GovernedGitMutationAdapter(root)
        head, branch = mutation.head(), mutation.current_branch()
        if not head.ok or not branch.ok or head.stdout.strip() != str(plan.get("head_before")) or branch.stdout.strip() != str(plan.get("branch")):
            return self._block("workspace git plan recheck", "UOC006_HEAD_BRANCH_STALE_BLOCK", "HEAD or current branch changed after Git plan creation.")
        if require_unstaged:
            try:
                staged = mutation.staged_paths()
            except RuntimeError as exc:
                return self._block("workspace git plan recheck", "UOC006_STAGED_INVENTORY_BLOCK", str(exc))
            if staged:
                return self._block("workspace git plan recheck", "UOC006_PREEXISTING_STAGED_BLOCK", "Index is no longer empty before approved staging.", metadata={"staged_paths": staged})
        for item in plan.get("files") or []:
            read = self.documents.read_document(str(item.get("document_id") or ""))
            if not read.ok:
                return self._dependency_block("workspace git plan recheck", read)
            doc = dict((read.data or {}).get("document") or {})
            if str(doc.get("relative_path")) != str(item.get("relative_path")) or str(doc.get("sha256")) != str(item.get("working_sha256")):
                return self._block("workspace git plan recheck", "UOC006_WORKTREE_STALE_BLOCK", "Document path/hash changed after Git plan creation.", path=str(item.get("relative_path")))
        return CommandResult("workspace git plan recheck", True, ExitCode.PASS, "Git plan still matches current HEAD, branch and selected document hashes.", data={"summary": {"plan_id": plan.get("plan_id"), "stale": False}}, findings=[])

    def _validate_staged(self, plan_or_record: dict[str, Any], root: Path) -> dict[str, Any]:
        files = list(plan_or_record.get("files") or [])
        mutation = GovernedGitMutationAdapter(root)
        checks: list[dict[str, Any]] = []
        expected_paths = sorted(str(item.get("relative_path") or "") for item in files)
        try:
            staged_paths = sorted(mutation.staged_paths())
        except Exception as exc:
            return {"ok": False, "checks": [{"check": "staged_paths", "status": "BLOCK", "error": str(exc)}], "index_fingerprint": ""}
        checks.append({"check": "exact_staged_paths", "status": "PASS" if staged_paths == expected_paths else "BLOCK", "expected": expected_paths, "actual": staged_paths})
        diff_check = mutation.cached_diff_check()
        checks.append({"check": "git_diff_cached_check", "status": "PASS" if diff_check.ok else "BLOCK", "stderr": diff_check.stderr[-1000:]})
        fingerprint_rows: list[dict[str, str]] = []
        for item in files:
            relative = str(item["relative_path"])
            try:
                raw = mutation.index_file_bytes(relative)
            except Exception as exc:
                checks.append({"check": "index_blob", "path": relative, "status": "BLOCK", "error": str(exc)})
                continue
            sha = hashlib.sha256(raw).hexdigest()
            fingerprint_rows.append({"path": relative, "sha256": sha})
            equivalence = mutation.worktree_index_equivalent(relative)
            checks.append({
                "check": "git_worktree_index_equivalence",
                "path": relative,
                "status": "PASS" if equivalence.ok else "BLOCK",
                "git_exit_code": equivalence.exit_code,
                "stderr": equivalence.stderr[-1000:],
                "working_sha256": str(item.get("working_sha256") or ""),
                "index_sha256": sha,
            })
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                checks.append({"check": "utf8", "path": relative, "status": "BLOCK"})
                continue
            secret = self.secret_guard.scan_text(text, subject=relative)
            checks.append({"check": "secret_guard", "path": relative, "status": "PASS" if secret.effect.value != "block" else "BLOCK"})
            ext = Path(relative).suffix.lower()
            if ext == ".json":
                try:
                    json.loads(text); status = "PASS"
                except json.JSONDecodeError:
                    status = "BLOCK"
                checks.append({"check": "json_syntax", "path": relative, "status": status})
            if ext == ".md":
                result = ValidationApplicationService(root, enforce_workspace_paths=True).validate_frontmatter(root / relative, strict=False)
                checks.append({"check": "markdown_frontmatter", "path": relative, "status": "PASS" if result.ok else "BLOCK", "finding_ids": [f.id for f in result.findings]})
        ok = all(item.get("status") == "PASS" for item in checks)
        return {"ok": ok, "checks": checks, "index_fingerprint": _sha_json(sorted(fingerprint_rows, key=lambda row: row["path"]))}

    def _recheck_stage_record(self, record: dict[str, Any]) -> CommandResult:
        context, root, failure = self._workspace("workspace git staged recheck")
        if failure is not None:
            return failure
        assert root is not None
        mutation = GovernedGitMutationAdapter(root)
        head, branch = mutation.head(), mutation.current_branch()
        if not head.ok or not branch.ok or head.stdout.strip() != str(record.get("head_before")) or branch.stdout.strip() != str(record.get("branch")):
            return self._block("workspace git staged recheck", "UOC006_STAGED_HEAD_BRANCH_BLOCK", "HEAD/branch changed after approved staging.")
        validation = self._validate_staged(record, root)
        if not validation["ok"] or validation["index_fingerprint"] != record.get("index_fingerprint"):
            return self._block("workspace git staged recheck", "UOC006_STAGED_CONTENT_DRIFT_BLOCK", "Staged content no longer matches approved index fingerprint.", metadata={"checks": validation["checks"]})
        return CommandResult("workspace git staged recheck", True, ExitCode.PASS, "Staged execution remains bound to exact HEAD, branch and index fingerprint.", data={"summary": {"stale": False}}, findings=[])

    @staticmethod
    def _stage_scope(plan: dict[str, Any], *, actor: str) -> dict[str, Any]:
        return {"actor_id": actor, "tool_id": STAGE_TOOL, "action": STAGE_ACTION, "action_id": STAGE_ACTION, "subject": plan["plan_id"], "subject_hash": plan["plan_hash"], "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"], "head_before": plan["head_before"], "branch": plan["branch"], "paths": [item["relative_path"] for item in plan["files"]], "interface": "ui", "scope_type": "uoc006-exact-staging-plan"}

    @staticmethod
    def _commit_scope(record: dict[str, Any], *, actor: str) -> dict[str, Any]:
        return {"actor_id": actor, "tool_id": COMMIT_TOOL, "action": COMMIT_ACTION, "action_id": COMMIT_ACTION, "subject": record["stage_execution_id"], "subject_hash": record["commit_intent_hash"], "stage_execution_id": record["stage_execution_id"], "plan_id": record["plan_id"], "plan_hash": record["plan_hash"], "head_before": record["head_before"], "branch": record["branch"], "index_fingerprint": record["index_fingerprint"], "paths": [item["relative_path"] for item in record["files"]], "interface": "ui", "scope_type": "uoc006-exact-commit-intent"}

    @staticmethod
    def _branch_scope(plan: dict[str, Any], *, actor: str) -> dict[str, Any]:
        return {"actor_id": actor, "tool_id": BRANCH_TOOL, "action": BRANCH_ACTION, "action_id": BRANCH_ACTION, "subject": plan["plan_id"], "subject_hash": plan["plan_hash"], "branch_name": plan["branch_name"], "head_before": plan["head_before"], "interface": "ui", "scope_type": "uoc006-local-branch-create"}

    @staticmethod
    def _decorate_approval(result: CommandResult, *, phase: str, binding_hash: str) -> CommandResult:
        data = dict(result.data or {}); data["uoc006"] = {"phase": phase, "binding_hash": binding_hash, "preliminary": True}
        return CommandResult(result.command, result.ok, result.exit_code, result.message, data=data, findings=result.findings)

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        if not path.is_file(): return None
        try: data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): return None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        temp = Path(name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text); handle.flush(); os.fsync(handle.fileno())
            os.replace(temp, path)
        finally:
            if temp.exists(): temp.unlink()

    def _schema_block(self, command: str, contract: str, payload: dict[str, Any]) -> CommandResult | None:
        result = SchemaValidator(self.platform_root).validate_payload(
            schema=contract,
            payload=payload,
            instance_label=f"in-memory:{contract}",
        )
        if result.ok:
            return None
        return self._block(
            command,
            "UOC006_SCHEMA_BLOCK",
            f"Generated {contract} payload failed its registered schema and was not persisted.",
            metadata={"finding_ids": [finding.id for finding in result.findings]},
        )

    @staticmethod
    def _git_failure(result) -> CommandResult:
        return CommandResult("workspace git dependency", False, ExitCode.BLOCK, "Typed Git dependency failed.", data={"stderr": result.stderr[-1000:]}, findings=[Finding("UOC006_GIT_DEPENDENCY_BLOCK", "Typed Git dependency failed.", Severity.BLOCK)])

    @staticmethod
    def _dependency_block(command: str, result: CommandResult) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, result.message, data=result.data, findings=[*result.findings, Finding("UOC006_DEPENDENCY_BLOCK", "A required governed dependency blocked UOC-006.", Severity.BLOCK)])

    @staticmethod
    def _block(command: str, finding_id: str, message: str, *, path: str | None = None, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"summary": {"mutations_performed": False, "preliminary": True}}, findings=[Finding(finding_id, message, Severity.BLOCK, path=path, metadata=metadata or {})])


def _actor(value: str) -> str:
    return str(value or "local-owner").strip() or "local-owner"


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _future(seconds: int) -> str:
    return datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() + seconds, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _expired(value: Any) -> bool:
    try:
        raw = str(value or "")
        parsed = datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
        if parsed.tzinfo is None: parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed <= datetime.now(timezone.utc)
    except ValueError:
        return True
