from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.approval.service import ApprovalCliInput, ApprovalService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest, SecretGuard, configured_external_workspace_roots
from devpilot_core.repo.git_adapter import GitAdapter
from devpilot_core.schemas import SchemaValidator
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
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.context_resolver = context_resolver or UiWorkspaceContextResolver(self.platform_root)
        self.documents = documents or WorkspaceDocumentsApplicationService(self.platform_root, context_resolver=self.context_resolver)
        self.approvals = ApprovalService(self.platform_root)
        self.secret_guard = SecretGuard(self.platform_root)
        self.validation = ValidationApplicationService(self.platform_root, enforce_workspace_paths=True)
        self.approval_auth_store = approval_auth_store

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
