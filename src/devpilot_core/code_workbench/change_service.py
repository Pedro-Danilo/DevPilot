from __future__ import annotations

import difflib
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

from devpilot_core.approval.service import ApprovalCliInput, ApprovalService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest, configured_external_workspace_roots
from devpilot_core.testing.impact_v2 import TestImpactAnalyzerV2, TestImpactV2Options

from .service import CodeWorkbenchApplicationService

APPLY_ACTION = "filesystem.story_source_change_apply"
ROLLBACK_ACTION = "filesystem.story_source_change_rollback"
APPLY_TOOL = "story.source-change.apply"
ROLLBACK_TOOL = "story.source-change.rollback"
CONTROL_ROOT_ENV = "DEVPILOT_GSDLC09C_CONTROL_ROOT"
ZERO_SHA256 = "0" * 64


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _stable_id(prefix: str, value: Any) -> str:
    return f"{prefix}-{_canonical_sha(value)[:24]}"


class SourceChangeApplicationService:
    """GSDLC-09-C immutable, approval-bound source mutation boundary.

    This service consumes GSDLC-09-B SourceDraftBuffer records and promotes them
    into an immutable multi-file SourceChangePlan. It never exposes shell or
    generic patch execution. Apply is all-or-nothing at the operation boundary:
    every preimage is revalidated, every backup is verified, writes are made by
    bounded atomic replacements, and any mid-flight/postcondition failure causes
    compensating restoration of the complete plan before a BLOCK is returned.

    The capability is preliminary/local-first. Git stage/commit stays out of
    scope and remains owned by later story/quality integration.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        context_resolver,
        code_workbench: CodeWorkbenchApplicationService | None = None,
        approval_auth_store=None,
        failure_injection_stage: str | None = None,
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.context_resolver = context_resolver
        self.code = code_workbench or CodeWorkbenchApplicationService(self.platform_root, context_resolver=context_resolver)
        self.approvals = ApprovalService(self.platform_root)
        self.approval_auth_store = approval_auth_store
        self.failure_injection_stage = str(failure_injection_stage or "").strip() or None

    # ---------- plan ----------
    def create_plan(self, *, draft_ids: list[str], actor: str, actor_role: str) -> CommandResult:
        command = "story source change plan create"
        context, failure = self.code._context(command)
        if failure:
            return failure
        assert context is not None
        if actor_role not in {"owner", "developer"}:
            return self._block(command, "GSDLC09C_PLAN_ROLE_BLOCK", "SourceChangePlan creation requires owner or developer role.")
        ids = [str(x).strip() for x in draft_ids if str(x).strip()]
        if not ids or len(ids) > 32 or len(set(ids)) != len(ids):
            return self._block(command, "GSDLC09C_PLAN_DRAFT_SET_BLOCK", "Plan requires 1-32 unique SourceDraftBuffer identifiers.")

        changes: list[dict[str, Any]] = []
        target_paths: set[str] = set()
        source_paths: set[str] = set()
        full_diff_parts: list[str] = []
        for order, draft_id in enumerate(ids, start=1):
            recheck = self.code.recheck_draft(draft_id)
            if not recheck.ok:
                return self._dependency_block(command, recheck, "GSDLC09C_DRAFT_RECHECK_BLOCK")
            loaded = self.code.get_draft(draft_id)
            if not loaded.ok:
                return self._dependency_block(command, loaded, "GSDLC09C_DRAFT_MISSING_BLOCK")
            draft = dict((loaded.data or {}).get("draft") or {})
            change, error = self._change_from_draft(context.effective_workspace_root, draft, order=order)
            if error:
                return error
            assert change is not None
            target = str(change["target_path"])
            source = str(change.get("source_path") or "")
            if target in target_paths or (source and source in target_paths) or (target in source_paths):
                return self._block(command, "GSDLC09C_PLAN_PATH_COLLISION_BLOCK", "Plan contains colliding source/target paths.", path=target)
            target_paths.add(target)
            if source:
                source_paths.add(source)
            changes.append(change)
            full_diff_parts.append(str(change["unified_diff"]))

        changed_paths = sorted(target_paths | source_paths)
        plan_core = {
            "schema_id": "SCHEMA-DEVPL-GSDLC-09-C-SOURCE-CHANGE-PLAN-V1",
            "schema_version": "1.0.0",
            "workspace_id": str(context.active_workspace_id),
            "story_execution_id": str(changes[0].get("story_execution_id") or "story-execution-unavailable"),
            "draft_ids": ids,
            "changes": changes,
            "exact_path_allowlist": changed_paths,
            "full_diff": "\n".join(full_diff_parts),
            "risk": {"level": "high", "reasons": ["approval-bound-source-write", "multi-file-atomicity", "stale-preimage-protection"]},
            "required_approval_role": "owner",
            "test_impact_preview": self._test_impact_preview(changed_paths),
            "safety": {
                "dry_run_required": True,
                "preimage_revalidation_required": True,
                "approval_required": True,
                "atomic_all_or_nothing": True,
                "generic_patch_enabled": False,
                "shell_enabled": False,
                "git_stage": False,
                "git_commit": False,
                "network_used": False,
                "external_api_used": False,
            },
        }
        plan_id = _stable_id("source-plan", {"workspace_id": plan_core["workspace_id"], "draft_ids": ids, "changes": [{k: c[k] for k in ("operation", "source_path", "target_path", "preimage_sha256", "postimage_sha256", "draft_revision_sha256")} for c in changes]})
        plan = {**plan_core, "plan_id": plan_id, "created_at_utc": _now(), "created_by": actor, "created_by_role": actor_role}
        plan["plan_hash"] = _canonical_sha({k: v for k, v in plan.items() if k != "plan_hash"})
        path = self._plan_path(context.effective_workspace_root, str(context.active_workspace_id), plan_id)
        if path.is_file():
            existing = self._read_json(path)
            if existing and str(existing.get("plan_hash")) == str(plan["plan_hash"]):
                return self._pass(command, "Immutable SourceChangePlan already exists; idempotent result returned.", {"plan": existing, "idempotent": True})
            return self._block(command, "GSDLC09C_IMMUTABLE_PLAN_COLLISION_BLOCK", "Existing SourceChangePlan identifier has different immutable content.")
        self._atomic_json(path, plan)
        return self._pass(command, "Immutable SourceChangePlan created without mutating workspace source.", {"plan": plan, "source_mutations_performed": False})

    def get_plan(self, *, plan_id: str) -> CommandResult:
        command = "story source change plan get"
        context, failure = self.code._context(command)
        if failure:
            return failure
        assert context is not None
        path = self._plan_path(context.effective_workspace_root, str(context.active_workspace_id), plan_id)
        payload = self._read_json(path)
        if payload is None:
            return self._block(command, "GSDLC09C_PLAN_MISSING_BLOCK", "SourceChangePlan does not exist.")
        if not self._plan_hash_valid(payload):
            return self._block(command, "GSDLC09C_PLAN_TAMPER_BLOCK", "Immutable SourceChangePlan hash no longer matches its contents.")
        return self._pass(command, "Immutable SourceChangePlan loaded.", {"plan": payload})

    def recheck(self, *, plan_id: str, plan_hash: str) -> CommandResult:
        command = "story source change plan recheck"
        loaded = self.get_plan(plan_id=plan_id)
        if not loaded.ok:
            return loaded
        plan = dict(loaded.data["plan"])
        if str(plan.get("plan_hash")) != str(plan_hash or ""):
            return self._block(command, "GSDLC09C_PLAN_HASH_MISMATCH_BLOCK", "Provided plan hash does not match immutable SourceChangePlan.")
        context, failure = self.code._context(command)
        if failure:
            return failure
        assert context is not None
        findings = self._preimage_findings(plan, context.effective_workspace_root)
        if findings:
            return CommandResult(command, False, ExitCode.BLOCK, "SourceChangePlan preimage revalidation blocked execution.", data={"plan_id": plan_id, "plan_hash": plan_hash, "source_mutations_performed": False}, findings=findings)
        return self._pass(command, "All SourceChangePlan preimages remain exact and allowlisted.", {"plan_id": plan_id, "plan_hash": plan_hash, "exact_path_allowlist": plan["exact_path_allowlist"], "source_mutations_performed": False})

    def dry_run(self, *, plan_id: str, plan_hash: str, actor: str, actor_role: str) -> CommandResult:
        command = "story source change dry-run"
        if actor_role not in {"owner", "developer"}:
            return self._block(command, "GSDLC09C_DRY_RUN_ROLE_BLOCK", "Dry-run requires owner or developer role.")
        recheck = self.recheck(plan_id=plan_id, plan_hash=plan_hash)
        if not recheck.ok:
            return recheck
        plan = self.get_plan(plan_id=plan_id).data["plan"]
        return self._pass(command, "Dry-run PASS: diff, risk, Test Impact and exact paths reviewed with zero source mutation.", {"plan_id": plan_id, "plan_hash": plan_hash, "full_diff": plan["full_diff"], "risk": plan["risk"], "required_approval_role": plan["required_approval_role"], "test_impact_preview": plan["test_impact_preview"], "exact_path_allowlist": plan["exact_path_allowlist"], "source_mutations_performed": False, "actor": actor})

    # ---------- approval + apply ----------
    def request_apply_approval(self, *, plan_id: str, plan_hash: str, actor: str, actor_role: str, reason: str, ttl_minutes: int = 15) -> CommandResult:
        command = "story source change apply approval request"
        if actor_role != "owner":
            return self._block(command, "GSDLC09C_WRONG_APPROVER_ROLE_BLOCK", "Only owner may request the required source apply approval.")
        recheck = self.recheck(plan_id=plan_id, plan_hash=plan_hash)
        if not recheck.ok:
            return recheck
        plan = self.get_plan(plan_id=plan_id).data["plan"]
        reason = str(reason or "").strip()
        if not reason:
            return self._block(command, "GSDLC09C_APPROVAL_REASON_REQUIRED_BLOCK", "Apply approval requires a human-readable reason.")
        scope = self._apply_scope(plan, actor=actor)
        result = self.approvals.request(ApprovalCliInput(tool_id=APPLY_TOOL, action=APPLY_ACTION, subject=plan_id, actor=actor, reason=reason, scope=json.dumps(scope, sort_keys=True), ttl_minutes=max(1, min(int(ttl_minutes), 30)), metadata={"source": "gsdlc-09-c", "sprint": "GSDLC-09-C", "interface": "ui", "plan_hash": plan_hash}))
        data = dict(result.data or {})
        data["gsdlc09c"] = {"phase": "apply", "plan_id": plan_id, "plan_hash": plan_hash, "required_role": "owner"}
        return CommandResult(result.command, result.ok, result.exit_code, result.message, data=data, findings=result.findings)

    def apply(self, *, plan_id: str, plan_hash: str, approval_id: str, actor: str, actor_role: str) -> CommandResult:
        command = "story source change apply"
        started = time.perf_counter()
        if actor_role != "owner":
            return self._block(command, "GSDLC09C_WRONG_ROLE_BLOCK", "Atomic source apply requires owner role.")
        recheck = self.recheck(plan_id=plan_id, plan_hash=plan_hash)
        if not recheck.ok:
            return recheck
        plan = dict(self.get_plan(plan_id=plan_id).data["plan"])
        context, failure = self.code._context(command)
        if failure:
            return failure
        assert context is not None
        root = context.effective_workspace_root.resolve()
        control = self._control_root(root)
        if control is None:
            return self._block(command, "GSDLC09C_CONTROL_ROOT_SCOPE_BLOCK", "09-C control/evidence root must be outside the active workspace.")
        policy = PolicyEngine(self.platform_root, allowed_external_roots=configured_external_workspace_roots(), approval_auth_store=self.approval_auth_store).evaluate(PolicyRequest(action=APPLY_ACTION, path=str(root), text="\n".join(str(c.get("content") or "") for c in plan["changes"]), dry_run=False, approval_id=str(approval_id or ""), tool_id=APPLY_TOOL, subject=plan_id, actor=actor, role_at_decision="owner", subject_hash=plan_hash, interface="ui", metadata=self._apply_scope(plan, actor=actor)))
        if not policy.ok:
            return CommandResult(command, False, ExitCode.BLOCK, "Policy/RBAC/approval binding blocked source apply.", data={"source_mutations_performed": False, "policy": policy.to_dict()}, findings=policy.findings)
        # Revalidate once more immediately after approval binding and before the first write.
        findings = self._preimage_findings(plan, root)
        if findings:
            return CommandResult(command, False, ExitCode.BLOCK, "Stale preimage detected immediately before atomic execute.", data={"source_mutations_performed": False}, findings=findings)

        execution_id = _stable_id("source-exec", {"plan_id": plan_id, "plan_hash": plan_hash, "approval_id": approval_id})
        record_path = control / "records" / f"{execution_id}.json"
        existing = self._read_json(record_path)
        if existing and existing.get("status") == "applied" and self._postimages_match(existing, root):
            return self._pass(command, "Approved atomic source apply already completed; idempotent result returned.", {"execution": existing, "idempotent": True, "source_mutations_performed": True})

        backup_dir = control / "backups" / execution_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_records: list[dict[str, Any]] = []
        try:
            for change in plan["changes"]:
                backup_records.append(self._backup_change(change, root, backup_dir))
        except Exception as exc:
            return self._block(command, "GSDLC09C_BACKUP_INTEGRITY_BLOCK", f"Backup preparation failed before source mutation: {type(exc).__name__}: {exc}")

        touched: list[str] = []
        apply_error: Exception | None = None
        try:
            for index, change in enumerate(plan["changes"], start=1):
                self._apply_change(change, root)
                touched.extend([p for p in (str(change.get("source_path") or ""), str(change["target_path"])) if p])
                if self.failure_injection_stage in {f"after-change-{index}", "after-first-write" if index == 1 else ""}:
                    raise RuntimeError(f"controlled failure injection after change {index}")
            post_findings = self._postimage_findings(plan, root)
            if post_findings:
                raise RuntimeError("postimage verification failed: " + ",".join(f.id for f in post_findings))
        except Exception as exc:
            apply_error = exc

        if apply_error is not None:
            restored, rollback_findings = self._restore_all(backup_records, root)
            record = self._execution_record(execution_id, plan, approval_id, actor, backup_records, status="rolled-back-automatic" if restored else "rollback-failed", duration_ms=round((time.perf_counter()-started)*1000,2), automatic_rollback=True, error=str(apply_error), rollback_integrity=restored)
            self._atomic_json(record_path, record)
            if not restored:
                return CommandResult(command, False, ExitCode.ERROR, "Atomic apply failed and compensating rollback could not restore exact preimages.", data={"execution": record, "source_mutations_performed": True}, findings=rollback_findings + [Finding("GSDLC09C_PARTIAL_RESIDUE_ERROR", "Compensating rollback integrity failed; partial residue may remain.", Severity.ERROR)])
            return CommandResult(command, False, ExitCode.BLOCK, "Atomic apply failed; compensating rollback restored every exact preimage.", data={"execution": record, "source_mutations_performed": True, "partial_residue": False}, findings=[Finding("GSDLC09C_AUTOMATIC_ROLLBACK_PASS", "All changes were restored after controlled atomic apply failure.", Severity.INFO), Finding("GSDLC09C_APPLY_FAULT_BLOCK", str(apply_error), Severity.BLOCK)])

        record = self._execution_record(execution_id, plan, approval_id, actor, backup_records, status="applied", duration_ms=round((time.perf_counter()-started)*1000,2), automatic_rollback=False, error=None, rollback_integrity=None)
        self._atomic_json(record_path, record)
        manifest_path = control / "evidence" / f"{execution_id}_apply_manifest.json"
        self._atomic_json(manifest_path, self._apply_manifest(record))
        record["apply_manifest_ref"] = manifest_path.relative_to(control).as_posix()
        self._atomic_json(record_path, record)
        return self._pass(command, "Approved SourceChangePlan applied atomically and exact postimages verified.", {"execution": record, "apply_manifest": self._apply_manifest(record), "source_mutations_performed": True, "partial_residue": False})

    # ---------- rollback ----------
    def get_execution(self, *, execution_id: str) -> CommandResult:
        command = "story source change execution get"
        context, failure = self.code._context(command)
        if failure:
            return failure
        assert context is not None
        control = self._control_root(context.effective_workspace_root.resolve())
        if control is None or not str(execution_id).startswith("source-exec-"):
            return self._block(command, "GSDLC09C_EXECUTION_ID_BLOCK", "Invalid source change execution identifier.")
        record = self._read_json(control / "records" / f"{execution_id}.json")
        if record is None:
            return self._block(command, "GSDLC09C_EXECUTION_MISSING_BLOCK", "Source change execution record does not exist.")
        return self._pass(command, "Source change execution loaded.", {"execution": record})

    def request_rollback_approval(self, *, execution_id: str, actor: str, actor_role: str, reason: str, ttl_minutes: int = 15) -> CommandResult:
        command = "story source change rollback approval request"
        if actor_role != "owner":
            return self._block(command, "GSDLC09C_ROLLBACK_WRONG_ROLE_BLOCK", "Only owner may request rollback approval.")
        status = self.get_execution(execution_id=execution_id)
        if not status.ok:
            return status
        record = dict(status.data["execution"])
        eligibility = self._rollback_eligibility(record)
        if not eligibility.ok:
            return eligibility
        reason = str(reason or "").strip()
        if not reason:
            return self._block(command, "GSDLC09C_ROLLBACK_REASON_REQUIRED_BLOCK", "Rollback approval requires a human-readable reason.")
        binding_hash = self._rollback_binding_hash(record)
        scope = self._rollback_scope(record, actor=actor, binding_hash=binding_hash)
        result = self.approvals.request(ApprovalCliInput(tool_id=ROLLBACK_TOOL, action=ROLLBACK_ACTION, subject=execution_id, actor=actor, reason=reason, scope=json.dumps(scope, sort_keys=True), ttl_minutes=max(1,min(int(ttl_minutes),30)), metadata={"source":"gsdlc-09-c","sprint":"GSDLC-09-C","interface":"ui","execution_binding_hash":binding_hash}))
        data = dict(result.data or {}); data["gsdlc09c"]={"phase":"rollback","execution_id":execution_id,"subject_hash":binding_hash,"required_role":"owner"}
        return CommandResult(result.command,result.ok,result.exit_code,result.message,data=data,findings=result.findings)

    def rollback(self, *, execution_id: str, approval_id: str, actor: str, actor_role: str) -> CommandResult:
        command = "story source change rollback"
        if actor_role != "owner":
            return self._block(command, "GSDLC09C_ROLLBACK_WRONG_ROLE_BLOCK", "Manual source rollback requires owner role.")
        status = self.get_execution(execution_id=execution_id)
        if not status.ok:
            return status
        record = dict(status.data["execution"])
        eligibility = self._rollback_eligibility(record)
        if not eligibility.ok:
            return eligibility
        context, failure = self.code._context(command)
        if failure: return failure
        assert context is not None
        root = context.effective_workspace_root.resolve(); control=self._control_root(root)
        assert control is not None
        binding_hash=self._rollback_binding_hash(record)
        policy=PolicyEngine(self.platform_root,allowed_external_roots=configured_external_workspace_roots(),approval_auth_store=self.approval_auth_store).evaluate(PolicyRequest(action=ROLLBACK_ACTION,path=str(root),dry_run=False,approval_id=str(approval_id or ""),tool_id=ROLLBACK_TOOL,subject=execution_id,actor=actor,role_at_decision="owner",subject_hash=binding_hash,interface="ui",metadata=self._rollback_scope(record,actor=actor,binding_hash=binding_hash)))
        if not policy.ok:
            return CommandResult(command,False,ExitCode.BLOCK,"Policy/RBAC/approval binding blocked source rollback.",data={"source_mutations_performed":False,"policy":policy.to_dict()},findings=policy.findings)
        restored, findings=self._restore_all(list(record.get("backups") or []),root)
        if not restored:
            return CommandResult(command,False,ExitCode.ERROR,"Approval-bound rollback failed exact preimage verification.",data={"source_mutations_performed":True},findings=findings)
        record["status"]="rolled-back-manual"; record["rollback"]={"mode":"manual-approval-bound","approval_id":approval_id,"actor":actor,"restored":True,"at":_now(),"source_hash_parity":True}
        record_path=control/"records"/f"{execution_id}.json"; self._atomic_json(record_path,record)
        evidence=self._rollback_evidence(record); evidence_path=control/"evidence"/f"{execution_id}_rollback_evidence.json"; self._atomic_json(evidence_path,evidence)
        record["rollback_evidence_ref"]=evidence_path.relative_to(control).as_posix(); self._atomic_json(record_path,record)
        return self._pass(command,"Approval-bound rollback restored all exact preimages with source hash parity.",{"execution":record,"rollback_evidence":evidence,"source_mutations_performed":True,"source_hash_parity":True})

    def get_apply_manifest(self, *, execution_id: str) -> CommandResult:
        status=self.get_execution(execution_id=execution_id)
        if not status.ok:return status
        return self._pass("story source change apply manifest","Apply manifest projected from immutable execution record.",{"apply_manifest":self._apply_manifest(dict(status.data["execution"]))})

    def get_rollback_evidence(self, *, execution_id: str) -> CommandResult:
        status=self.get_execution(execution_id=execution_id)
        if not status.ok:return status
        record=dict(status.data["execution"])
        if record.get("status")!="rolled-back-manual":return self._block("story source change rollback evidence","GSDLC09C_ROLLBACK_EVIDENCE_STATE_BLOCK","Manual rollback evidence is available only after approved rollback.")
        return self._pass("story source change rollback evidence","Rollback evidence projected from execution record.",{"rollback_evidence":self._rollback_evidence(record)})

    # ---------- helpers ----------
    def _change_from_draft(self, root: Path, draft: dict[str, Any], *, order: int) -> tuple[dict[str, Any] | None, CommandResult | None]:
        op=str(draft.get("operation") or "").upper(); target=str(draft.get("target_path") or ""); source=dict(draft.get("source") or {}); source_path=str(source.get("relative_path") or "")
        target_resolved=self.code._target(root,target,command="story source change plan create")
        if isinstance(target_resolved,CommandResult):return None,target_resolved
        target_abs,target_rel=target_resolved
        if op in {"EDIT","RENAME"}:
            source_resolved=self.code._resolve_source(root,str(source.get("source_id") or ""))
            if isinstance(source_resolved,CommandResult):return None,source_resolved
            source_abs,source_rel=source_resolved; pre_raw=source_abs.read_bytes(); pre_sha=_sha_bytes(pre_raw); pre_text=pre_raw.decode("utf-8-sig")
            if pre_sha!=str(source.get("sha256") or ""):return None,self._block("story source change plan create","GSDLC09C_STALE_PREIMAGE_BLOCK","Draft source preimage changed before plan creation.",path=source_rel)
            source_path=source_rel
        else:
            pre_text=""; pre_sha=ZERO_SHA256
        if op in {"CREATE","RENAME"} and target_abs.exists():return None,self._block("story source change plan create","GSDLC09C_UNEXPECTED_TARGET_BLOCK","Target exists unexpectedly before immutable plan creation.",path=target_rel)
        post_text=str(draft.get("content") or ""); post_sha=_sha_bytes(post_text.encode("utf-8"))
        fromfile=f"a/{source_path or target_rel}"; tofile=f"b/{target_rel}"
        diff="".join(difflib.unified_diff(pre_text.splitlines(keepends=True),post_text.splitlines(keepends=True),fromfile=fromfile,tofile=tofile,n=3))
        return {"order":order,"draft_id":str(draft["draft_id"]),"draft_revision_sha256":str(draft["revision_sha256"]),"story_execution_id":str(draft.get("story_execution_id") or ""),"operation":op,"source_path":source_path or None,"target_path":target_rel,"preimage_sha256":pre_sha,"postimage_sha256":post_sha,"content":post_text,"unified_diff":diff},None

    def _preimage_findings(self, plan: dict[str, Any], root: Path) -> list[Finding]:
        findings: list[Finding]=[]; allowed=set(plan.get("exact_path_allowlist") or [])
        for change in plan.get("changes") or []:
            op=str(change["operation"]); source=str(change.get("source_path") or ""); target=str(change["target_path"])
            if target not in allowed or (source and source not in allowed): findings.append(Finding("GSDLC09C_UNEXPECTED_PATH_BLOCK","Change references path outside exact approved allowlist.",Severity.BLOCK,path=target)); continue
            target_check=self.code._target(root,target,command="story source change recheck")
            if isinstance(target_check,CommandResult): findings.extend(target_check.findings); continue
            target_abs,_=target_check
            if op in {"EDIT","RENAME"}:
                path=(root/source).resolve()
                try:path.relative_to(root)
                except ValueError: findings.append(Finding("GSDLC09C_PATH_ESCAPE_BLOCK","Source escaped workspace root.",Severity.BLOCK,path=source)); continue
                actual=_sha_file(path) if path.is_file() else "missing"
                if actual!=str(change["preimage_sha256"]):findings.append(Finding("GSDLC09C_STALE_PREIMAGE_BLOCK","Source preimage SHA-256 changed after planning.",Severity.BLOCK,path=source,metadata={"expected":change["preimage_sha256"],"actual":actual}))
            if op in {"CREATE","RENAME"} and target_abs.exists():findings.append(Finding("GSDLC09C_UNEXPECTED_TARGET_BLOCK","Planned target now exists.",Severity.BLOCK,path=target))
            if op=="EDIT" and target!=source:findings.append(Finding("GSDLC09C_EDIT_PATH_BLOCK","EDIT target no longer matches source.",Severity.BLOCK,path=target))
        return findings

    def _postimage_findings(self, plan: dict[str, Any], root: Path) -> list[Finding]:
        findings=[]
        for c in plan["changes"]:
            target=root/str(c["target_path"]); actual=_sha_file(target) if target.is_file() else "missing"
            if actual!=str(c["postimage_sha256"]):findings.append(Finding("GSDLC09C_POSTIMAGE_BLOCK","Applied target does not match approved postimage hash.",Severity.BLOCK,path=str(c["target_path"])))
            if c["operation"]=="RENAME" and (root/str(c["source_path"])).exists():findings.append(Finding("GSDLC09C_RENAME_SOURCE_RESIDUE_BLOCK","Rename left the old source path behind.",Severity.BLOCK,path=str(c["source_path"])))
        return findings

    def _backup_change(self, change: dict[str, Any], root: Path, backup_dir: Path) -> dict[str, Any]:
        source=str(change.get("source_path") or ""); target=str(change["target_path"]); op=str(change["operation"])
        record={"operation":op,"source_path":source or None,"target_path":target,"preimage_sha256":str(change["preimage_sha256"]),"postimage_sha256":str(change["postimage_sha256"]),"source_existed":False,"target_existed":False,"source_backup_ref":None,"target_backup_ref":None,"source_mode":None,"target_mode":None}
        for kind, rel in (("source",source),("target",target)):
            if not rel:continue
            path=root/rel
            if path.is_file():
                raw=path.read_bytes(); sha=_sha_bytes(raw); dest=backup_dir/f"{kind}-{_canonical_sha(rel)[:16]}.bak"; dest.write_bytes(raw)
                if _sha_file(dest)!=sha:raise RuntimeError(f"backup hash mismatch: {rel}")
                record[f"{kind}_existed"]=True; record[f"{kind}_backup_ref"]=dest.relative_to(backup_dir.parent.parent).as_posix(); record[f"{kind}_sha256_before"]=sha; record[f"{kind}_mode"]=stat.S_IMODE(path.stat().st_mode)
        if op in {"EDIT","RENAME"} and record.get("source_sha256_before")!=str(change["preimage_sha256"]):raise RuntimeError(f"source preimage changed during backup: {source}")
        if op in {"CREATE","RENAME"} and record.get("target_existed"):raise RuntimeError(f"target unexpectedly existed during backup: {target}")
        return record

    def _apply_change(self, change: dict[str, Any], root: Path) -> None:
        op=str(change["operation"]); source=root/str(change.get("source_path") or change["target_path"]); target=root/str(change["target_path"]); payload=str(change["content"]).encode("utf-8")
        mode=stat.S_IMODE(source.stat().st_mode) if source.is_file() else 0o644
        self._atomic_write(target,payload,mode=mode)
        if op=="RENAME" and source!=target: source.unlink()

    def _restore_all(self, backups: list[dict[str, Any]], root: Path) -> tuple[bool,list[Finding]]:
        findings=[]
        # Restore in reverse; exact path state is derived from source/target existence at preimage.
        for rec in reversed(backups):
            for kind in ("target","source"):
                rel=str(rec.get(f"{kind}_path") or "")
                if not rel:continue
                path=root/rel; existed=bool(rec.get(f"{kind}_existed")); ref=rec.get(f"{kind}_backup_ref")
                try:
                    if existed:
                        backup=self._control_from_root(root)/str(ref); raw=backup.read_bytes(); self._atomic_write(path,raw,mode=int(rec.get(f"{kind}_mode") or 0o644))
                    elif path.exists(): path.unlink()
                except Exception as exc: findings.append(Finding("GSDLC09C_ROLLBACK_IO_ERROR",f"Failed restoring {rel}: {exc}",Severity.ERROR,path=rel))
        # verify every expected pre-state
        for rec in backups:
            for kind in ("source","target"):
                rel=str(rec.get(f"{kind}_path") or "")
                if not rel:continue
                path=root/rel; existed=bool(rec.get(f"{kind}_existed")); expected=str(rec.get(f"{kind}_sha256_before") or "")
                if existed:
                    actual=_sha_file(path) if path.is_file() else "missing"
                    if actual!=expected:findings.append(Finding("GSDLC09C_ROLLBACK_HASH_BLOCK","Rollback did not restore exact preimage hash.",Severity.ERROR,path=rel,metadata={"expected":expected,"actual":actual}))
                elif path.exists():findings.append(Finding("GSDLC09C_PARTIAL_RESIDUE_ERROR","Rollback left a path that did not exist before apply.",Severity.ERROR,path=rel))
        return not any(f.severity in {Severity.FAIL,Severity.BLOCK,Severity.ERROR} for f in findings),findings

    def _execution_record(self, execution_id: str, plan: dict[str, Any], approval_id: str, actor: str, backups: list[dict[str, Any]], *, status: str, duration_ms: float, automatic_rollback: bool, error: str | None, rollback_integrity: bool | None) -> dict[str, Any]:
        return {"schema_id":"SCHEMA-DEVPL-GSDLC-09-C-APPLY-MANIFEST-V1","schema_version":"1.0.0","execution_id":execution_id,"status":status,"plan_id":plan["plan_id"],"plan_hash":plan["plan_hash"],"workspace_id":plan["workspace_id"],"story_execution_id":plan["story_execution_id"],"approval_id":approval_id,"actor":actor,"required_role":"owner","changes":[{k:c[k] for k in ("operation","source_path","target_path","preimage_sha256","postimage_sha256")} for c in plan["changes"]],"exact_path_allowlist":plan["exact_path_allowlist"],"backups":backups,"duration_ms":duration_ms,"automatic_rollback":automatic_rollback,"automatic_rollback_integrity":rollback_integrity,"error":error,"applied_at_utc":_now(),"source_mutations_performed":True,"git_stage":False,"git_commit":False,"network_used":False,"external_api_used":False,"rollback":None}

    def _rollback_eligibility(self, record: dict[str, Any]) -> CommandResult:
        if record.get("status")!="applied":return self._block("story source change rollback eligibility","GSDLC09C_ROLLBACK_STATE_BLOCK","Rollback is allowed only for a currently applied source change execution.")
        context,failure=self.code._context("story source change rollback eligibility")
        if failure:return failure
        assert context is not None
        root=context.effective_workspace_root.resolve()
        if not self._postimages_match(record,root):return self._block("story source change rollback eligibility","GSDLC09C_ROLLBACK_STALE_BLOCK","Workspace no longer matches exact approved postimages; rollback fails closed.")
        return self._pass("story source change rollback eligibility","Execution is eligible for separate approval-bound rollback.",{"execution_id":record["execution_id"],"source_mutations_performed":False})

    def _postimages_match(self, record: dict[str, Any], root: Path) -> bool:
        for c in record.get("changes") or []:
            target=root/str(c["target_path"])
            if not target.is_file() or _sha_file(target)!=str(c["postimage_sha256"]):return False
            if c.get("operation")=="RENAME" and (root/str(c.get("source_path") or "")).exists():return False
        return True

    def _test_impact_preview(self, changed_paths: list[str]) -> dict[str, Any]:
        result=TestImpactAnalyzerV2(self.platform_root,TestImpactV2Options(changed_paths=tuple(changed_paths))).analyze()
        if not result.ok:return {"status":"BLOCK","changed_paths":changed_paths,"findings":[f.to_dict() for f in result.findings]}
        data=dict(result.data or {}); summary=dict(data.get("summary") or {})
        return {"status":"PASS","changed_paths":changed_paths,"matched_contracts_total":summary.get("matched_contracts_total",0),"recommended_tests_total":summary.get("recommended_tests_total",0),"unmatched_paths_total":summary.get("unmatched_paths_total",0),"recommended_tests":data.get("recommended_tests",[]),"recommended_commands":data.get("recommended_commands",[])}

    def _control_root(self, workspace_root: Path) -> Path | None:
        raw=os.environ.get(CONTROL_ROOT_ENV,"").strip(); root=Path(raw).expanduser().resolve() if raw else (self.platform_root/"outputs"/"gsdlc09c_control").resolve()
        try:root.relative_to(workspace_root.resolve()); return None
        except ValueError:return root
    def _control_from_root(self,workspace_root:Path)->Path:
        control=self._control_root(workspace_root)
        if control is None:raise RuntimeError("control root inside workspace")
        return control
    def _plan_root(self,workspace_root:Path,workspace_id:str)->Path:
        safe="".join(c if c.isalnum() or c in "-_" else "-" for c in workspace_id).strip("-") or "workspace"
        return workspace_root/"outputs"/"code_workbench"/"gsdlc_09_c"/safe/"plans"
    def _plan_path(self,workspace_root:Path,workspace_id:str,plan_id:str)->Path:
        if not str(plan_id).startswith("source-plan-") or len(str(plan_id))!=36:return self._plan_root(workspace_root,workspace_id)/"__invalid__.json"
        return self._plan_root(workspace_root,workspace_id)/f"{plan_id}.json"
    @staticmethod
    def _plan_hash_valid(plan:dict[str,Any])->bool:return str(plan.get("plan_hash") or "")==_canonical_sha({k:v for k,v in plan.items() if k!="plan_hash"})
    @staticmethod
    def _read_json(path:Path):
        if not path.is_file():return None
        try:return json.loads(path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError):return None
    @staticmethod
    def _atomic_json(path:Path,payload:dict[str,Any]):
        path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8"); os.replace(tmp,path)
    @staticmethod
    def _atomic_write(target:Path,payload:bytes,*,mode:int):
        target.parent.mkdir(parents=True,exist_ok=True); fd,name=tempfile.mkstemp(prefix=f".{target.name}.gsdlc09c-",suffix=".tmp",dir=str(target.parent)); temp=Path(name)
        try:
            with os.fdopen(fd,"wb") as h:h.write(payload); h.flush(); os.fsync(h.fileno())
            os.chmod(temp,mode); os.replace(temp,target)
        finally:
            if temp.exists():temp.unlink()
    def _apply_scope(self,plan:dict[str,Any],*,actor:str)->dict[str,Any]:return {"actor_id":actor,"role_at_decision":"owner","tool_id":APPLY_TOOL,"action":APPLY_ACTION,"action_id":APPLY_ACTION,"subject":plan["plan_id"],"subject_hash":plan["plan_hash"],"plan_id":plan["plan_id"],"plan_hash":plan["plan_hash"],"workspace_id":plan["workspace_id"],"exact_path_allowlist":plan["exact_path_allowlist"],"interface":"ui","scope_type":"immutable-multifile-source-change-plan"}
    @staticmethod
    def _rollback_binding_hash(record:dict[str,Any])->str:return _canonical_sha({"execution_id":record["execution_id"],"plan_id":record["plan_id"],"plan_hash":record["plan_hash"],"changes":record["changes"],"status":record["status"]})
    def _rollback_scope(self,record:dict[str,Any],*,actor:str,binding_hash:str)->dict[str,Any]:return {"actor_id":actor,"role_at_decision":"owner","tool_id":ROLLBACK_TOOL,"action":ROLLBACK_ACTION,"action_id":ROLLBACK_ACTION,"subject":record["execution_id"],"subject_hash":binding_hash,"execution_id":record["execution_id"],"plan_id":record["plan_id"],"plan_hash":record["plan_hash"],"workspace_id":record["workspace_id"],"exact_path_allowlist":record["exact_path_allowlist"],"interface":"ui","scope_type":"bounded-multifile-source-rollback"}
    @staticmethod
    def _apply_manifest(record:dict[str,Any])->dict[str,Any]:return {k:record.get(k) for k in ("schema_id","schema_version","execution_id","status","plan_id","plan_hash","workspace_id","story_execution_id","approval_id","actor","required_role","changes","exact_path_allowlist","backups","duration_ms","automatic_rollback","automatic_rollback_integrity","source_mutations_performed","git_stage","git_commit","network_used","external_api_used","applied_at_utc")}
    @staticmethod
    def _rollback_evidence(record:dict[str,Any])->dict[str,Any]:return {"schema_id":"SCHEMA-DEVPL-GSDLC-09-C-ROLLBACK-EVIDENCE-V1","schema_version":"1.0.0","execution_id":record["execution_id"],"plan_id":record["plan_id"],"plan_hash":record["plan_hash"],"status":record["status"],"changes":record["changes"],"exact_path_allowlist":record["exact_path_allowlist"],"rollback":record.get("rollback"),"source_hash_parity":bool((record.get("rollback") or {}).get("source_hash_parity")),"network_used":False,"external_api_used":False}
    @staticmethod
    def _pass(command:str,message:str,data:dict[str,Any]):return CommandResult(command,True,ExitCode.PASS,message,data=data,findings=[Finding("GSDLC09C_PASS",message,Severity.INFO)])
    @staticmethod
    def _block(command:str,code:str,message:str,*,path:str|None=None,metadata:dict[str,Any]|None=None):return CommandResult(command,False,ExitCode.BLOCK,message,data=metadata or {},findings=[Finding(code,message,Severity.BLOCK,path=path,metadata=metadata or {})])
    @staticmethod
    def _dependency_block(command:str,result:CommandResult,code:str):return CommandResult(command,False,ExitCode.BLOCK,"Dependency blocked GSDLC-09-C operation.",data={"dependency":result.to_dict()},findings=[Finding(code,"Dependency blocked GSDLC-09-C operation.",Severity.BLOCK),*result.findings])
