from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.approval.models import ApprovalRecord, ApprovalStatus
from devpilot_core.approval.service import ApprovalCliInput, ApprovalService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.observability import EventLogger, EventRecord
from devpilot_core.policy import PolicyEngine, PolicyRequest, SecretGuard, configured_external_workspace_roots
from devpilot_core.repo.git_adapter import GitAdapter

from .workspace_documents_service import WorkspaceDocumentsApplicationService
from .workspace_edit_plan_service import WorkspaceEditPlanApplicationService

APPLY_ACTION = "filesystem.workspace_document_apply"
ROLLBACK_ACTION = "filesystem.workspace_document_rollback"
APPLY_TOOL = "workspace.edit.apply"
ROLLBACK_TOOL = "workspace.edit.rollback"
CONTROL_ROOT_ENV = "DEVPILOT_UOC005_CONTROL_ROOT"
DEFAULT_TTL_MINUTES = 15
MAX_TTL_MINUTES = 30


class WorkspaceEditExecutionApplicationService:
    """UOC-005 approval-bound document apply and rollback boundary.

    This service intentionally does not enable the historical generic patch or
    rollback executors. It can only mutate the exact document bound to an
    unexpired immutable UOC-004 edit plan after StrongApprovalBinding through
    PolicyEngine succeeds. Backups and execution records are kept outside the
    active workspace in a bounded control root.

    UOC-005 is an implemented-initial local capability. UOC-006 still owns Git
    staging/commit operations; this service never stages, commits or pushes.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        documents: WorkspaceDocumentsApplicationService | None = None,
        plans: WorkspaceEditPlanApplicationService | None = None,
        approval_auth_store: LocalAuthStore | None = None,
        failure_injection_stage: str | None = None,
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.documents = documents or WorkspaceDocumentsApplicationService(self.platform_root)
        self.plans = plans or WorkspaceEditPlanApplicationService(self.platform_root, documents=self.documents)
        self.approvals = ApprovalService(self.platform_root)
        self.secret_guard = SecretGuard(self.platform_root)
        self.events = EventLogger(self.platform_root)
        self.approval_auth_store = approval_auth_store
        self.failure_injection_stage = str(failure_injection_stage or "").strip() or None

    def request_apply_approval(
        self,
        *,
        plan_id: str,
        plan_hash: str,
        actor: str = "local-owner",
        reason: str,
        ttl_minutes: int = DEFAULT_TTL_MINUTES,
    ) -> CommandResult:
        plan_result = self.plans.get_plan(plan_id=plan_id)
        plan = self._plan_from_result(plan_result)
        if plan is None:
            return self._dependency_block("workspace edit apply approval request", plan_result, "UOC005_PLAN_UNAVAILABLE_BLOCK")
        if str(plan.get("plan_hash")) != str(plan_hash or ""):
            return self._block("workspace edit apply approval request", "UOC005_PLAN_HASH_MISMATCH_BLOCK", "Approval request hash does not match the immutable edit plan.")
        recheck = self.plans.recheck(plan_id=plan_id, plan_hash=plan_hash)
        if not recheck.ok:
            return self._dependency_block("workspace edit apply approval request", recheck, "UOC005_PRE_APPROVAL_RECHECK_BLOCK")
        actor = str(actor or "local-owner").strip() or "local-owner"
        reason = str(reason or "").strip()
        if not reason:
            return self._block("workspace edit apply approval request", "UOC005_APPROVAL_REASON_REQUIRED_BLOCK", "A human-readable reason is required before requesting apply approval.")
        ttl = max(1, min(int(ttl_minutes), MAX_TTL_MINUTES))
        remaining_seconds = max(1, int((_parse_utc(str(plan["expires_at"])) - datetime.now(timezone.utc)).total_seconds()))
        ttl = max(1, min(ttl, max(1, remaining_seconds // 60 or 1)))
        scope = self._apply_scope(plan, actor=actor)
        result = self.approvals.request(
            ApprovalCliInput(
                tool_id=APPLY_TOOL,
                action=APPLY_ACTION,
                subject=plan_id,
                actor=actor,
                reason=reason,
                scope=json.dumps(scope, sort_keys=True),
                ttl_minutes=ttl,
                metadata={"source": "uoc-005", "sprint": "UOC-005", "interface": "ui", "plan_hash": plan_hash},
            )
        )
        return self._decorate_approval_request(result, plan=plan, phase="apply")

    def apply(
        self,
        *,
        plan_id: str,
        plan_hash: str,
        approval_id: str,
        actor: str = "local-owner",
    ) -> CommandResult:
        started = time.perf_counter()
        plan_result = self.plans.get_plan(plan_id=plan_id)
        plan = self._plan_from_result(plan_result)
        if plan is None:
            return self._dependency_block("workspace edit apply", plan_result, "UOC005_PLAN_UNAVAILABLE_BLOCK")
        if str(plan.get("plan_hash")) != str(plan_hash or ""):
            return self._block("workspace edit apply", "UOC005_PLAN_HASH_MISMATCH_BLOCK", "Apply hash does not match the immutable edit plan.")
        recheck = self.plans.recheck(plan_id=plan_id, plan_hash=plan_hash)
        if not recheck.ok:
            return self._dependency_block("workspace edit apply", recheck, "UOC005_PRE_APPLY_RECHECK_BLOCK")
        actor = str(actor or "local-owner").strip() or "local-owner"
        target, workspace_root, relative_path = self._resolve_target(plan)
        if target is None or workspace_root is None:
            return self._block("workspace edit apply", "UOC005_TARGET_SCOPE_BLOCK", "The plan target is no longer an allowed workspace document.", path=relative_path)
        control_root = self._control_root(workspace_root)
        if control_root is None:
            return self._block("workspace edit apply", "UOC005_CONTROL_ROOT_SCOPE_BLOCK", "UOC-005 control root must be outside the active workspace.")

        proposed = str(plan.get("proposed_content") or "")
        policy = PolicyEngine(self.platform_root, allowed_external_roots=configured_external_workspace_roots(), approval_auth_store=self.approval_auth_store).evaluate(
            PolicyRequest(
                action=APPLY_ACTION,
                path=str(target),
                text=proposed,
                dry_run=False,
                approval_id=str(approval_id or "").strip(),
                tool_id=APPLY_TOOL,
                subject=plan_id,
                actor=actor,
                role_at_decision="owner",
                subject_hash=plan_hash,
                interface="ui",
                metadata={
                    **self._apply_scope(plan, actor=actor),
                    "workspace_id": plan.get("workspace_id"),
                    "source_mutation_requested": True,
                    "uoc": "UOC-005",
                },
            )
        )
        if not policy.ok:
            return CommandResult("workspace edit apply", False, ExitCode.BLOCK, "Approval/policy binding blocked document apply.", data={"summary": self._summary(plan, mutations=False), "policy": policy.to_dict()}, findings=policy.findings)

        execution_id = _id("uedit", f"{plan_id}|{plan_hash}|{approval_id}")
        record_path = control_root / "records" / f"{execution_id}.json"
        existing = self._read_record(record_path)
        operation = str(plan.get("document", {}).get("operation") or "modify")
        current_sha = _sha_file(target) if target.is_file() else ("0" * 64)
        if existing and existing.get("status") == "applied" and current_sha == str(plan["document"]["proposed_sha256"]):
            return CommandResult("workspace edit apply", True, ExitCode.PASS, "Approved document apply was already completed; idempotent result returned.", data={"summary": {**self._summary(plan, mutations=True), "execution_id": execution_id, "idempotent": True}, "execution": existing}, findings=[Finding("UOC005_APPLY_IDEMPOTENT_PASS", "Existing successful execution matches the proposed document hash.", Severity.INFO, path=relative_path)])

        base_sha = str(plan["document"]["document_sha_before"])
        if current_sha != base_sha:
            return self._block("workspace edit apply", "UOC005_STALE_APPLY_BLOCK", "Source hash changed immediately before atomic apply.", path=relative_path, metadata={"expected": base_sha, "current": current_sha})

        control_root.mkdir(parents=True, exist_ok=True)
        backup_path = control_root / "backups" / f"{execution_id}-{base_sha[:12]}.bak"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        before_mode = stat.S_IMODE(target.stat().st_mode) if target.is_file() else 0o644
        if operation == "modify":
            shutil.copy2(target, backup_path)
            backup_sha = _sha_file(backup_path)
            if backup_sha != base_sha:
                return self._block("workspace edit apply", "UOC005_BACKUP_INTEGRITY_BLOCK", "Backup hash does not match the immutable base before apply.", path=relative_path)
        else:
            backup_sha = "0" * 64

        self._atomic_write(target, proposed.encode("utf-8"), mode=before_mode)
        post_sha = _sha_file(target)
        post_findings = self._post_validate(plan, target)
        if self.failure_injection_stage == "after-write-before-validation":
            post_findings.append(Finding("GSDLC04D_FAILURE_INJECTION_BLOCK", "Controlled failure injection after atomic write.", Severity.BLOCK, path=relative_path))
        post_ok = post_sha == str(plan["document"]["proposed_sha256"]) and not any(f.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for f in post_findings)

        approval_snapshot = self._approval_snapshot(str(approval_id or ""))
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        record: dict[str, Any] = {
            "schema_id": "devpilot.gsdlc04d.artifact_apply_execution.v1" if operation == "create" else "devpilot.post_h_eval_002.uoc_005.workspace_edit_execution.v1",
            "execution_id": execution_id,
            "status": "applied" if post_ok else "post-validation-blocked",
            "plan_id": plan_id,
            "plan_hash": plan_hash,
            "approval_id": approval_id,
            "approval": approval_snapshot,
            "actor": actor,
            "workspace_id": plan.get("workspace_id"),
            "relative_path": relative_path,
            "document_id": plan["document"]["document_id"],
            "pre_sha256": base_sha,
            "post_sha256": post_sha,
            "proposed_sha256": plan["document"]["proposed_sha256"],
            "backup_sha256": backup_sha,
            "backup_ref": backup_path.relative_to(control_root).as_posix(),
            "evidence_ref": record_path.relative_to(control_root).as_posix(),
            "report_ref": f"reports/{execution_id}.json",
            "trace_event_types": ["workspace.document.apply.completed", "workspace.document.apply.auto_rollback", "workspace.document.rollback.completed"],
            "duration_ms": duration_ms,
            "permissions_mode_before": oct(before_mode),
            "policy": {"status": "PASS", "approval_bound": True, "action": APPLY_ACTION, "tool_id": APPLY_TOOL},
            "post_validation": {"status": "PASS" if post_ok else "BLOCK", "findings": [f.to_dict() for f in post_findings]},
            "applied_at": _now(),
            "rollback": None,
            "source_write": True,
            "git_stage": False,
            "git_commit": False,
            "preliminary": True,
        }
        if operation == "create":
            record["operation"] = "create"

        if not post_ok:
            if operation == "create":
                try:
                    if target.exists(): target.unlink()
                except OSError:
                    pass
                restored_sha = "0" * 64 if not target.exists() else _sha_file(target)
            else:
                self._restore_backup(target, backup_path, mode=before_mode)
                restored_sha = _sha_file(target)
            record["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
            record["status"] = "rolled-back-automatic" if restored_sha == base_sha else "rollback-failed"
            record["rollback"] = {"mode": "automatic-compensating", "restored_sha256": restored_sha, "at": _now(), "reason": "post-validation-block", "integrity_pass": restored_sha == base_sha}
            self._persist_record(control_root, record_path, record)
            self._emit("workspace.document.apply.auto_rollback", record)
            if restored_sha != base_sha:
                return CommandResult(
                    "workspace edit apply",
                    False,
                    ExitCode.ERROR,
                    "Post-validation blocked and compensating rollback failed integrity verification.",
                    data={"summary": {**self._summary(plan, mutations=True), "execution_id": execution_id, "automatic_rollback": True, "rollback_integrity_pass": False, "restored_sha256": restored_sha}, "execution": record},
                    findings=[*post_findings, Finding("UOC005_AUTOMATIC_ROLLBACK_INTEGRITY_BLOCK", "Compensating rollback did not restore the immutable base hash.", Severity.ERROR, path=relative_path, metadata={"expected": base_sha, "restored": restored_sha})],
                )
            return CommandResult(
                "workspace edit apply",
                False,
                ExitCode.BLOCK,
                "Post-validation blocked the approved apply; DevPilot automatically restored the exact backup.",
                data={"summary": {**self._summary(plan, mutations=True), "execution_id": execution_id, "automatic_rollback": True, "restored_sha256": restored_sha}, "execution": record},
                findings=[*post_findings, Finding("UOC005_AUTOMATIC_ROLLBACK_PASS", "Compensating rollback restored the immutable base after post-validation failure.", Severity.INFO, path=relative_path)],
            )

        record["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
        self._persist_record(control_root, record_path, record)
        self._emit("workspace.document.apply.completed", record)
        elapsed_ms = record["duration_ms"]
        return CommandResult(
            "workspace edit apply",
            True,
            ExitCode.PASS,
            "Approved document edit was applied atomically and passed post-validation.",
            data={"summary": {**self._summary(plan, mutations=True), "execution_id": execution_id, "pre_sha256": base_sha, "post_sha256": post_sha, "elapsed_ms": elapsed_ms, "rollback_available_before_commit": True}, "execution": record},
            findings=[*post_findings, Finding("UOC005_APPLY_PASS", "Approval-bound atomic document apply passed.", Severity.INFO, path=relative_path)],
        )

    def get_execution(self, *, execution_id: str) -> CommandResult:
        record_path = self._find_record(execution_id)
        record = self._read_record(record_path) if record_path else None
        if not record:
            return self._block("workspace edit execution status", "UOC005_EXECUTION_NOT_FOUND_BLOCK", "Execution record does not exist in the configured UOC-005 control root.")
        return CommandResult("workspace edit execution status", True, ExitCode.PASS, "UOC-005 execution record loaded.", data={"execution": record, "summary": {"execution_id": execution_id, "status": record.get("status"), "preliminary": True}}, findings=[])

    def request_rollback_approval(
        self,
        *,
        execution_id: str,
        actor: str = "local-owner",
        reason: str,
        ttl_minutes: int = DEFAULT_TTL_MINUTES,
    ) -> CommandResult:
        status = self.get_execution(execution_id=execution_id)
        if not status.ok:
            return status
        record = dict((status.data or {}).get("execution") or {})
        eligibility = self._rollback_eligibility(record)
        if not eligibility.ok:
            return eligibility
        actor = str(actor or "local-owner").strip() or "local-owner"
        reason = str(reason or "").strip()
        if not reason:
            return self._block("workspace edit rollback approval request", "UOC005_APPROVAL_REASON_REQUIRED_BLOCK", "A human-readable reason is required before requesting rollback approval.")
        binding_hash = _rollback_binding_hash(record)
        scope = self._rollback_scope(record, actor=actor, binding_hash=binding_hash)
        result = self.approvals.request(
            ApprovalCliInput(
                tool_id=ROLLBACK_TOOL,
                action=ROLLBACK_ACTION,
                subject=execution_id,
                actor=actor,
                reason=reason,
                scope=json.dumps(scope, sort_keys=True),
                ttl_minutes=max(1, min(int(ttl_minutes), MAX_TTL_MINUTES)),
                metadata={"source": "uoc-005", "sprint": "UOC-005", "interface": "ui", "execution_binding_hash": binding_hash},
            )
        )
        if result.data is None:
            return result
        data = dict(result.data)
        data["uoc005"] = {"phase": "rollback", "execution_id": execution_id, "subject_hash": binding_hash, "preliminary": True}
        return CommandResult(result.command, result.ok, result.exit_code, result.message, data=data, findings=result.findings)

    def rollback(
        self,
        *,
        execution_id: str,
        approval_id: str,
        actor: str = "local-owner",
    ) -> CommandResult:
        status = self.get_execution(execution_id=execution_id)
        if not status.ok:
            return status
        record = dict((status.data or {}).get("execution") or {})
        eligibility = self._rollback_eligibility(record)
        if not eligibility.ok:
            return eligibility
        actor = str(actor or "local-owner").strip() or "local-owner"
        binding_hash = _rollback_binding_hash(record)
        workspace_root = self.documents.context_resolver.resolve().effective_workspace_root
        target = (workspace_root / str(record["relative_path"])).resolve()
        policy = PolicyEngine(self.platform_root, allowed_external_roots=configured_external_workspace_roots(), approval_auth_store=self.approval_auth_store).evaluate(
            PolicyRequest(
                action=ROLLBACK_ACTION,
                path=str(target),
                dry_run=False,
                approval_id=str(approval_id or "").strip(),
                tool_id=ROLLBACK_TOOL,
                subject=execution_id,
                actor=actor,
                role_at_decision="owner",
                subject_hash=binding_hash,
                interface="ui",
                metadata=self._rollback_scope(record, actor=actor, binding_hash=binding_hash),
            )
        )
        if not policy.ok:
            return CommandResult("workspace edit rollback", False, ExitCode.BLOCK, "Approval/policy binding blocked document rollback.", data={"summary": {"execution_id": execution_id, "mutations_performed": False}, "policy": policy.to_dict()}, findings=policy.findings)
        workspace_root = self.documents.context_resolver.resolve().effective_workspace_root
        control_root = self._control_root(workspace_root)
        if control_root is None:
            return self._block("workspace edit rollback", "UOC005_CONTROL_ROOT_SCOPE_BLOCK", "UOC-005 control root must be outside the active workspace.")
        backup_path = (control_root / str(record.get("backup_ref") or "")).resolve()
        try:
            backup_path.relative_to(control_root.resolve())
        except ValueError:
            return self._block("workspace edit rollback", "UOC005_ROLLBACK_BACKUP_SCOPE_BLOCK", "Rollback backup reference escaped the configured control root.")
        if not backup_path.is_file() or _sha_file(backup_path) != str(record["pre_sha256"]):
            return self._block("workspace edit rollback", "UOC005_ROLLBACK_BACKUP_BLOCK", "Rollback backup is missing or failed hash verification.", path=str(record.get("relative_path") or ""))
        mode = int(str(record.get("permissions_mode_before") or "0o644"), 8)
        self._restore_backup(target, backup_path, mode=mode)
        restored_sha = _sha_file(target)
        if restored_sha != str(record["pre_sha256"]):
            return self._block("workspace edit rollback", "UOC005_ROLLBACK_POSTCONDITION_BLOCK", "Rollback did not restore the exact pre-apply SHA-256.", path=str(record.get("relative_path") or ""))
        record["status"] = "rolled-back-manual"
        record["rollback"] = {"mode": "manual-approval-bound", "approval_id": approval_id, "approval": self._approval_snapshot(str(approval_id or "")), "actor": actor, "restored_sha256": restored_sha, "at": _now(), "integrity_pass": True}
        record_path = self._find_record(execution_id)
        assert record_path is not None
        self._persist_record(control_root, record_path, record)
        self._emit("workspace.document.rollback.completed", record)
        return CommandResult(
            "workspace edit rollback",
            True,
            ExitCode.PASS,
            "Approved rollback restored the exact pre-apply document before Git commit.",
            data={"summary": {"execution_id": execution_id, "restored_sha256": restored_sha, "source_mutations_performed": True, "git_stage": False, "git_commit": False, "preliminary": True}, "execution": record},
            findings=[Finding("UOC005_MANUAL_ROLLBACK_PASS", "Approval-bound rollback restored the exact pre-apply hash.", Severity.INFO, path=str(record.get("relative_path") or ""))],
        )

    def _rollback_eligibility(self, record: dict[str, Any]) -> CommandResult:
        execution_id = str(record.get("execution_id") or "")
        if record.get("status") != "applied":
            return self._block("workspace edit rollback eligibility", "UOC005_ROLLBACK_STATE_BLOCK", "Manual rollback is available only for an applied execution that has not already been rolled back.", metadata={"execution_id": execution_id, "status": record.get("status")})
        context = self.documents.context_resolver.resolve()
        target = (context.effective_workspace_root / str(record.get("relative_path") or "")).resolve()
        if not target.is_file() or _sha_file(target) != str(record.get("post_sha256") or ""):
            return self._block("workspace edit rollback eligibility", "UOC005_ROLLBACK_STALE_BLOCK", "Document no longer matches the applied post hash; bounded rollback fails closed.", path=str(record.get("relative_path") or ""))
        git = GitAdapter(context.effective_workspace_root).file_status(str(record.get("relative_path") or ""))
        if not git.ok:
            return self._dependency_block("workspace edit rollback eligibility", git, "UOC005_ROLLBACK_GIT_STATUS_BLOCK")
        state = (git.data or {}).get("status") or {}
        if state.get("staged") or state.get("clean") or not state.get("unstaged"):
            return self._block("workspace edit rollback eligibility", "UOC005_ROLLBACK_AFTER_STAGE_OR_COMMIT_BLOCK", "Manual UOC-005 rollback is allowed only while the document is an unstaged working-tree modification before commit.", path=str(record.get("relative_path") or ""), metadata={"git_status": state})
        return CommandResult("workspace edit rollback eligibility", True, ExitCode.PASS, "Document is eligible for bounded pre-commit rollback.", data={"summary": {"execution_id": execution_id, "git_status": state}}, findings=[])

    def _post_validate(self, plan: dict[str, Any], target: Path) -> list[Finding]:
        proposed = str(plan.get("proposed_content") or "")
        current = target.read_text(encoding="utf-8")
        findings, _ = self.plans._validate_content(
            extension=str(plan["document"]["extension"]),
            relative_path=str(plan["document"]["relative_path"]),
            current_content=current,
            proposed_content=proposed,
        )
        if _sha_file(target) != str(plan["document"]["proposed_sha256"]):
            findings.append(Finding("UOC005_POST_HASH_BLOCK", "Applied document hash does not match the immutable proposal.", Severity.BLOCK, path=str(plan["document"]["relative_path"])))
        return findings

    def _resolve_target(self, plan: dict[str, Any]) -> tuple[Path | None, Path | None, str]:
        relative_path = str(plan.get("document", {}).get("relative_path") or "")
        document_id = str(plan.get("document", {}).get("document_id") or "")
        operation = str(plan.get("document", {}).get("operation") or "modify")
        context = self.documents.context_resolver.resolve()
        target = (context.effective_workspace_root / relative_path).resolve()
        try:
            target.relative_to(context.effective_workspace_root.resolve())
        except ValueError:
            return None, None, relative_path
        if target.is_symlink() or target.parent.is_symlink() or not target.parent.is_dir():
            return None, None, relative_path
        if operation == "create":
            if target.exists():
                return None, None, relative_path
            return target, context.effective_workspace_root.resolve(), relative_path
        read = self.documents.read_document(document_id)
        if not read.ok or not target.is_file():
            return None, None, relative_path
        if str((read.data or {}).get("document", {}).get("relative_path") or "") != relative_path:
            return None, None, relative_path
        return target, context.effective_workspace_root.resolve(), relative_path

    def _control_root(self, workspace_root: Path) -> Path | None:
        raw = os.environ.get(CONTROL_ROOT_ENV, "").strip()
        root = Path(raw).expanduser().resolve() if raw else (self.platform_root / "outputs" / "uoc005_control").resolve()
        try:
            root.relative_to(workspace_root.resolve())
            return None
        except ValueError:
            return root

    def _find_record(self, execution_id: str) -> Path | None:
        if not execution_id.startswith("uedit_"):
            return None
        try:
            workspace_root = self.documents.context_resolver.resolve().effective_workspace_root
        except Exception:
            return None
        control = self._control_root(workspace_root)
        if control is None:
            return None
        path = control / "records" / f"{execution_id}.json"
        return path if path.is_file() else None

    def _apply_scope(self, plan: dict[str, Any], *, actor: str) -> dict[str, Any]:
        document = plan["document"]
        return {
            "actor_id": actor,
            "role_at_decision": "owner",
            "tool_id": APPLY_TOOL,
            "action": APPLY_ACTION,
            "action_id": APPLY_ACTION,
            "subject": plan["plan_id"],
            "subject_hash": plan["plan_hash"],
            "plan_id": plan["plan_id"],
            "plan_hash": plan["plan_hash"],
            "document_id": document["document_id"],
            "document_sha_before": document["document_sha_before"],
            "operation": str(document.get("operation") or "modify"),
            "proposed_sha256": document["proposed_sha256"],
            "workspace_id": plan.get("workspace_id"),
            "interface": "ui",
            "scope_type": "immutable-workspace-document-edit-plan",
        }

    def _rollback_scope(self, record: dict[str, Any], *, actor: str, binding_hash: str) -> dict[str, Any]:
        return {
            "actor_id": actor,
            "role_at_decision": "owner",
            "tool_id": ROLLBACK_TOOL,
            "action": ROLLBACK_ACTION,
            "action_id": ROLLBACK_ACTION,
            "subject": record["execution_id"],
            "subject_hash": binding_hash,
            "execution_id": record["execution_id"],
            "plan_id": record["plan_id"],
            "plan_hash": record["plan_hash"],
            "pre_sha256": record["pre_sha256"],
            "post_sha256": record["post_sha256"],
            "workspace_id": record.get("workspace_id"),
            "interface": "ui",
            "scope_type": "bounded-pre-commit-document-rollback",
        }

    def _decorate_approval_request(self, result: CommandResult, *, plan: dict[str, Any], phase: str) -> CommandResult:
        data = dict(result.data or {})
        data["uoc005"] = {"phase": phase, "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"], "document_sha_before": plan["document"]["document_sha_before"], "preliminary": True}
        return CommandResult(result.command, result.ok, result.exit_code, result.message, data=data, findings=result.findings)

    @staticmethod
    def _plan_from_result(result: CommandResult) -> dict[str, Any] | None:
        return dict((result.data or {}).get("plan") or {}) if result.ok and isinstance((result.data or {}).get("plan"), dict) else None

    @staticmethod
    def _atomic_write(target: Path, payload: bytes, *, mode: int) -> None:
        target.parent.mkdir(parents=False, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=f".{target.name}.uoc005-", suffix=".tmp", dir=str(target.parent))
        temp = Path(name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp, mode)
            os.replace(temp, target)
        finally:
            if temp.exists():
                temp.unlink()

    @classmethod
    def _restore_backup(cls, target: Path, backup: Path, *, mode: int) -> None:
        cls._atomic_write(target, backup.read_bytes(), mode=mode)

    @staticmethod
    def _read_record(path: Path | None) -> dict[str, Any] | None:
        if path is None or not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return data if isinstance(data, dict) else None

    def _approval_snapshot(self, approval_id: str) -> dict[str, Any]:
        shown = self.approvals.show(approval_id)
        raw = dict((shown.data or {}).get("approval") or {}) if shown.ok else {}
        return {
            "approval_id": str(raw.get("approval_id") or approval_id),
            "status": str(raw.get("status") or "unknown"),
            "tool_id": str(raw.get("tool_id") or ""),
            "action": str(raw.get("action") or ""),
            "subject": str(raw.get("subject") or ""),
            "actor": str(raw.get("actor") or ""),
            "reason": str(raw.get("reason") or ""),
            "expires_at": raw.get("expires_at"),
            "decision_at": raw.get("decision_at"),
            "decided_by": raw.get("decided_by"),
        }

    def _persist_record(self, control_root: Path, record_path: Path, record: dict[str, Any]) -> None:
        self._write_record(record_path, record)
        report_path = control_root / str(record.get("report_ref") or f"reports/{record['execution_id']}.json")
        try:
            report_path.resolve().relative_to(control_root.resolve())
        except ValueError as exc:  # pragma: no cover - defensive internal invariant
            raise RuntimeError("UOC-005 report path escaped control root") from exc
        self._write_record(report_path, {"report_schema": "devpilot.post_h_eval_002.uoc_005.workspace_edit_execution_report.v1", "generated_at": _now(), "execution": record})

    @staticmethod
    def _write_record(path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        temp = Path(name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        finally:
            if temp.exists():
                temp.unlink()

    def _emit(self, event_type: str, record: dict[str, Any]) -> None:
        try:
            self.events.emit(EventRecord(event_type=event_type, command="workspace edit execution", status=str(record.get("status") or ""), ok=record.get("status") in {"applied", "rolled-back-manual"}, subject=str(record.get("relative_path") or ""), metadata={"execution_id": record.get("execution_id"), "plan_id": record.get("plan_id"), "approval_id": record.get("approval_id"), "source_mutation": True, "uoc": "UOC-005"}))
        except Exception:
            pass

    @staticmethod
    def _summary(plan: dict[str, Any], *, mutations: bool) -> dict[str, Any]:
        return {"plan_id": plan.get("plan_id"), "plan_hash": plan.get("plan_hash"), "relative_path": plan.get("document", {}).get("relative_path"), "source_mutations_performed": mutations, "git_stage": False, "git_commit": False, "remote_execution_enabled": False, "connector_write_enabled": False, "plugin_execution_enabled": False, "preliminary": True}

    @staticmethod
    def _dependency_block(command: str, result: CommandResult, finding_id: str) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, result.message, data=result.data, findings=[*result.findings, Finding(finding_id, "A required governed dependency blocked UOC-005 execution.", Severity.BLOCK)])

    @staticmethod
    def _block(command: str, finding_id: str, message: str, *, path: str | None = None, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"summary": {"source_mutations_performed": False, "preliminary": True}}, findings=[Finding(finding_id, message, Severity.BLOCK, path=path, metadata=metadata or {})])


def _rollback_binding_hash(record: dict[str, Any]) -> str:
    core = {"execution_id": record.get("execution_id"), "plan_id": record.get("plan_id"), "plan_hash": record.get("plan_hash"), "pre_sha256": record.get("pre_sha256"), "post_sha256": record.get("post_sha256"), "relative_path": record.get("relative_path")}
    return hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:32]}"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
