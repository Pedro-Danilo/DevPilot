from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import SecretGuard
from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry
from devpilot_core.validators.artifact import extract_headings, normalize_heading
from devpilot_core.validators.frontmatter import parse_frontmatter_text, validate_frontmatter_document

from .artifact_draft_service import ArtifactDraftApplicationService
from .artifact_import_service import ArtifactImportApplicationService
from .artifact_lifecycle_service import ArtifactLifecycleService, ArtifactState
from .workspace_documents_service import WorkspaceDocumentsApplicationService
from .workspace_edit_execution_service import WorkspaceEditExecutionApplicationService
from .workspace_edit_plan_service import WorkspaceEditPlanApplicationService, ZERO_SHA256

_REVIEW_ID = re.compile(r"^arev_[0-9a-f]{32}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
DEFAULT_REVIEW_ROOT = Path("outputs/artifact_reviews/gsdlc_04_d")


class ArtifactReviewApplicationService:
    """GSDLC-04-D review/promote facade composed over UOC-004/UOC-005.

    Runtime review records are evidence/state only. Source mutation remains owned
    exclusively by WorkspaceEditExecutionApplicationService. This facade resolves
    validators from ArtifactProfile/lifecycle policy, produces navigable findings,
    binds an immutable plan/diff, and freezes only an already approval-bound apply.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        documents: WorkspaceDocumentsApplicationService,
        drafts: ArtifactDraftApplicationService,
        imports: ArtifactImportApplicationService,
        plans: WorkspaceEditPlanApplicationService,
        executions: WorkspaceEditExecutionApplicationService,
        review_root: Path = DEFAULT_REVIEW_ROOT,
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.documents = documents
        self.drafts = drafts
        self.imports = imports
        self.plans = plans
        self.executions = executions
        self.lifecycle = ArtifactLifecycleService(self.platform_root)
        self.profiles = ArtifactProfileRegistry(self.platform_root)
        self.secret_guard = SecretGuard(self.platform_root)
        self.review_root = self.platform_root / review_root
        self._lock = threading.RLock()

    def start_import(self, *, import_id: str, actor: str, actor_role: str, session_principal: str) -> CommandResult:
        got = self.imports.get(import_id=import_id)
        if not got.ok:
            return self._dependency("artifact review start", got, "GSDLC04D_IMPORT_DRAFT_REQUIRED_BLOCK")
        source = dict(got.data["import"])
        if str(source.get("lifecycle_state")) != ArtifactState.DRAFT.value:
            return self._block("artifact review start", "GSDLC04D_IMPORT_STATE_BLOCK", "Only a DRAFT import can enter review.")
        artifact = deepcopy(source["artifact"])
        return self._start(
            source_kind="IMPORT",
            source_ref=str(import_id),
            artifact=artifact,
            relative_path=str(source["relative_path"]),
            content=str(source["normalized_content"]),
            base_sha=str(source.get("destination_preimage_sha256") or ZERO_SHA256),
            actor=actor,
            actor_role=actor_role,
            session_principal=session_principal,
        )

    def start_document(self, *, document_id: str, actor: str, actor_role: str, session_principal: str) -> CommandResult:
        got = self.drafts.get(document_id=document_id)
        if not got.ok:
            return self._dependency("artifact review start", got, "GSDLC04D_MANUAL_DRAFT_REQUIRED_BLOCK")
        draft = (got.data or {}).get("draft")
        source = (got.data or {}).get("source") or {}
        if not isinstance(draft, dict) or not draft.get("active"):
            return self._block("artifact review start", "GSDLC04D_MANUAL_DRAFT_REQUIRED_BLOCK", "An active persisted manual DRAFT is required.")
        revision_sha = str(draft.get("current_revision_sha256") or "")
        revision = next((x for x in draft.get("revisions", []) if str(x.get("revision_sha256")) == revision_sha), None)
        if not isinstance(revision, dict):
            return self._block("artifact review start", "GSDLC04D_DRAFT_REVISION_BLOCK", "Current draft revision is unavailable.")
        content = str(revision.get("content") or "")
        relative_path = str(source.get("relative_path") or "")
        base_sha = str(source.get("sha256") or "")
        lifecycle = self.lifecycle.create_draft(
            artifact_id=f"artifact_{hashlib.sha256((document_id+'|'+revision_sha).encode()).hexdigest()[:24]}",
            relative_path=relative_path,
            content=content,
            source_type="MANUAL",
            base_commit=self._base_commit(),
            actor=actor,
            actor_role=actor_role,
            session_principal=session_principal,
            reviewer=actor,
            reviewer_role=actor_role,
            source_label="Manual editor DRAFT",
            source_reference=f"document:{document_id};revision:{revision_sha}",
        )
        if not lifecycle.ok:
            return self._dependency("artifact review start", lifecycle, "GSDLC04D_MANUAL_LIFECYCLE_BLOCK")
        return self._start(
            source_kind="MANUAL",
            source_ref=str(document_id),
            artifact=deepcopy(lifecycle.data["artifact"]),
            relative_path=relative_path,
            content=content,
            base_sha=base_sha,
            actor=actor,
            actor_role=actor_role,
            session_principal=session_principal,
        )


    def start_runtime_draft(
        self,
        *,
        source_kind: str,
        source_ref: str,
        artifact: dict[str, Any],
        relative_path: str,
        content: str,
        base_sha: str,
        actor: str,
        actor_role: str,
        session_principal: str,
    ) -> CommandResult:
        """GSDLC-05-E successor entry point for a server-persisted runtime DRAFT.

        The caller must supply an ArtifactLifecycleService DRAFT record created
        from authenticated UI input. This method intentionally delegates to the
        same 04-D validation/plan pipeline; it does not create a second writer.
        """
        if str(artifact.get("state") or "") != ArtifactState.DRAFT.value:
            return self._block("artifact review start", "GSDLC05E_RUNTIME_DRAFT_STATE_BLOCK", "Only a server-authoritative DRAFT may enter the pre-code review pipeline.")
        return self._start(
            source_kind=str(source_kind or "").upper(),
            source_ref=str(source_ref or ""),
            artifact=deepcopy(artifact),
            relative_path=relative_path,
            content=content,
            base_sha=base_sha,
            actor=actor,
            actor_role=actor_role,
            session_principal=session_principal,
        )

    def get(self, *, review_id: str) -> CommandResult:
        path = self._record_path(review_id)
        if path is None or not path.is_file():
            return self._block("artifact review status", "GSDLC04D_REVIEW_NOT_FOUND_BLOCK", "Artifact review id is invalid or unavailable.")
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return self._block("artifact review status", "GSDLC04D_REVIEW_CORRUPT_BLOCK", "Artifact review runtime record is unreadable.")
        return CommandResult("artifact review status", True, ExitCode.PASS, "Artifact review loaded.", data={"review": record}, findings=[])

    def freeze(self, *, review_id: str, execution_id: str, actor: str, actor_role: str, session_principal: str) -> CommandResult:
        got = self.get(review_id=review_id)
        if not got.ok:
            return got
        record = deepcopy(got.data["review"])
        if record.get("status") == "FROZEN":
            return CommandResult("artifact review freeze", True, ExitCode.PASS, "Artifact is already frozen; idempotent result returned.", data={"review": record}, findings=[Finding("GSDLC04D_FREEZE_IDEMPOTENT_PASS", "Frozen artifact already matches this review record.", Severity.INFO)])
        if record.get("status") != "APPROVAL_REQUIRED":
            return self._block("artifact review freeze", "GSDLC04D_FREEZE_STATE_BLOCK", "Freeze is allowed only after validation/plan reached APPROVAL_REQUIRED.")
        execution = self.executions.get_execution(execution_id=execution_id)
        if not execution.ok:
            return self._dependency("artifact review freeze", execution, "GSDLC04D_EXECUTION_REQUIRED_BLOCK")
        exe = dict(execution.data.get("execution") or {})
        plan = record["plan"]
        if exe.get("status") != "applied" or exe.get("plan_id") != plan.get("plan_id") or exe.get("plan_hash") != plan.get("plan_hash"):
            return self._block("artifact review freeze", "GSDLC04D_EXECUTION_BINDING_BLOCK", "Freeze requires the exact successfully applied immutable plan.")
        if str(exe.get("actor") or "") != actor:
            return self._block("artifact review freeze", "GSDLC04D_EXECUTION_ACTOR_BLOCK", "Freeze actor must match the approval-bound execution actor.")
        target = self._target(str(record["relative_path"]))
        if target is None or not target.is_file():
            return self._block("artifact review freeze", "GSDLC04D_APPLIED_SOURCE_MISSING_BLOCK", "Applied artifact source is unavailable.")
        current_sha = hashlib.sha256(target.read_bytes()).hexdigest()
        if current_sha != str(plan["document"]["proposed_sha256"]):
            return self._block("artifact review freeze", "GSDLC04D_POST_APPLY_DRIFT_BLOCK", "Artifact content drifted after apply; approval cannot be reused.", metadata={"expected": plan["document"]["proposed_sha256"], "current": current_sha})

        approved = self.lifecycle.transition(record["artifact"], target_state=ArtifactState.APPROVED, actor=actor, actor_role=actor_role)
        if not approved.ok:
            return self._dependency("artifact review freeze", approved, "GSDLC04D_APPROVED_TRANSITION_BLOCK")
        frozen = self.lifecycle.transition(approved.data["artifact"], target_state=ArtifactState.FROZEN, actor=actor, actor_role=actor_role)
        if not frozen.ok:
            return self._dependency("artifact review freeze", frozen, "GSDLC04D_FROZEN_TRANSITION_BLOCK")
        record["artifact"] = frozen.data["artifact"]
        record["status"] = "FROZEN"
        record["execution_id"] = execution_id
        record["approval_id"] = exe.get("approval_id")
        record["approved_sha256"] = current_sha
        record["approval_valid"] = True
        git_context = self._git_context(str(record["relative_path"]))
        record["freeze_record"] = {
            "review_id": review_id, "artifact_id": record["artifact"]["artifact_id"],
            "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"], "execution_id": execution_id,
            "approval_id": exe.get("approval_id"), "approved_sha256": current_sha,
            "actor": actor, "actor_role": actor_role, "session_principal": session_principal,
            "frozen_at": _now(), "source_write_engine": "WorkspaceEditExecutionApplicationService",
            "git_branch": git_context.get("branch"), "git_head": git_context.get("head"),
            "secrets_exposed": False, "network_used": False, "external_api_used": False,
        }
        record["updated_at"] = _now()
        self._write_record(record)
        self._sync_source_record(record)
        return CommandResult("artifact review freeze", True, ExitCode.PASS, "Approval-bound artifact apply was verified and the exact approved hash was frozen.", data={"review":record,"freeze_record":record["freeze_record"]}, findings=[Finding("GSDLC04D_FREEZE_PASS", "APPROVED/FROZEN transition is bound to exact apply, approval and hash.", Severity.INFO, path=record["relative_path"])])

    def reconcile(self, *, review_id: str, actor: str, actor_role: str, session_principal: str) -> CommandResult:
        got = self.get(review_id=review_id)
        if not got.ok:
            return got
        record = deepcopy(got.data["review"])
        if record.get("status") not in {"APPROVED", "FROZEN", "REVALIDATION_REQUIRED"}:
            return self._block("artifact review reconcile", "GSDLC04E_RECONCILE_STATE_BLOCK", "External reconciliation applies only to APPROVED/FROZEN artifacts or an already invalidated review.")
        if record.get("status") == "REVALIDATION_REQUIRED":
            return CommandResult("artifact review reconcile", True, ExitCode.PASS, "Artifact already requires revalidation; idempotent reconciliation returned.", data={"review": record, "reconciliation": record.get("reconciliation") or {}}, findings=[Finding("GSDLC04E_RECONCILE_IDEMPOTENT_PASS", "REVALIDATION_REQUIRED is preserved without reverting external state.", Severity.INFO, path=record.get("relative_path"))])

        relative_path = str(record["relative_path"])
        target = self._target(relative_path)
        if target is None:
            return self._block("artifact review reconcile", "GSDLC04E_RECONCILE_PATH_BLOCK", "Governed artifact target escapes the active workspace.")

        git_before = self._git_context(relative_path)
        detected_path: str | None = None
        if target.is_file():
            change_kind = "modified"
            try:
                content = target.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                return self._block("artifact review reconcile", "GSDLC04E_EXTERNAL_ENCODING_BLOCK", "External artifact is no longer valid UTF-8 text and cannot be reconciled automatically.")
        else:
            detected_path = self._find_exact_rename(relative_path, str(record.get("approved_sha256") or record["artifact"].get("content_hash") or ""))
            if detected_path:
                renamed_target = self._target(detected_path)
                if renamed_target is None or not renamed_target.is_file():
                    return self._block("artifact review reconcile", "GSDLC04E_RENAME_TARGET_BLOCK", "Detected rename target is unavailable or outside the workspace.")
                try:
                    content = renamed_target.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    return self._block("artifact review reconcile", "GSDLC04E_EXTERNAL_ENCODING_BLOCK", "Renamed artifact is not valid UTF-8 text.")
                change_kind = "renamed"
            else:
                content = None
                change_kind = "deleted"

        result = self.lifecycle.reconcile_external_change(
            record["artifact"], change_kind=change_kind, current_content=content,
            actor=actor, actor_role=actor_role, session_principal=session_principal,
            detected_relative_path=detected_path,
        )
        if not result.ok:
            return self._dependency("artifact review reconcile", result, "GSDLC04E_RECONCILIATION_BLOCK")

        record["artifact"] = result.data["artifact"]
        record["status"] = record["artifact"]["state"]
        summary = dict((result.data or {}).get("summary") or {})
        drift = bool(summary.get("drift_detected"))
        if drift:
            record["approval_valid"] = False
            record["approval_invalidated_reason"] = f"external-{change_kind}"
        git_after = self._git_context(detected_path or relative_path)
        freeze = dict(record.get("freeze_record") or {})
        branch_at_freeze = freeze.get("git_branch")
        branch_now = git_after.get("branch")
        record["reconciliation"] = {
            "status": "REVALIDATION_REQUIRED" if drift else "UNCHANGED",
            "change_kind": summary.get("change_kind", "unchanged"),
            "original_relative_path": relative_path,
            "detected_relative_path": detected_path,
            "previous_approved_sha256": record.get("approved_sha256"),
            "current_normalized_sha256": record["artifact"].get("content_hash"),
            "approval_valid": record.get("approval_valid", False),
            "auto_reverted": False,
            "hidden_merge": False,
            "git_branch_at_freeze": branch_at_freeze,
            "git_branch_current": branch_now,
            "branch_changed": bool(branch_at_freeze and branch_now and branch_at_freeze != branch_now),
            "git_head_current": git_after.get("head"),
            "git_status_porcelain": git_before.get("status_porcelain"),
            "git_diff": git_after.get("diff"),
            "source_provenance": deepcopy(record["artifact"].get("provenance") or {}),
            "checked_at": _now(),
            "source_mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
        }
        record["updated_at"] = _now()
        self._write_record(record)
        self._sync_source_record(record)
        message = "External drift detected; approval invalidated and artifact moved to REVALIDATION_REQUIRED." if drift else "No external content drift detected; frozen approval remains valid."
        return CommandResult("artifact review reconcile", True, ExitCode.PASS, message, data={"review": record, "reconciliation": record["reconciliation"]}, findings=result.findings)

    def _git_context(self, relative_path: str) -> dict[str, Any]:
        root = self.documents.context_resolver.resolve().effective_workspace_root.resolve()
        def run(args: list[str], timeout: int = 8) -> subprocess.CompletedProcess[str]:
            return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=timeout, check=False)
        head = run(["rev-parse", "HEAD"])
        branch = run(["branch", "--show-current"])
        status = subprocess.run(["git", "-C", str(root), "status", "--porcelain=v1", "-z", "--", relative_path], capture_output=True, timeout=8, check=False)
        diff = run(["diff", "--no-ext-diff", "--unified=3", "--", relative_path])
        diff_text = diff.stdout if diff.returncode == 0 else ""
        status_text = status.stdout.decode("utf-8", errors="replace").replace("\x00", "\n").strip() if status.returncode == 0 else ""
        target = root / relative_path
        if not diff_text and target.is_file() and status_text.startswith("??"):
            noindex = subprocess.run(["git", "-C", str(root), "diff", "--no-ext-diff", "--no-index", "--unified=3", "--", os.devnull, str(target)], capture_output=True, text=True, timeout=8, check=False)
            if noindex.returncode in {0, 1}:
                diff_text = noindex.stdout
        return {
            "head": head.stdout.strip() if head.returncode == 0 else None,
            "branch": branch.stdout.strip() if branch.returncode == 0 else None,
            "status_porcelain": status_text,
            "diff": diff_text[-24000:],
        }

    def _find_exact_rename(self, original_relative_path: str, approved_sha256: str) -> str | None:
        if not _SHA.fullmatch(approved_sha256):
            return None
        context = self.documents.context_resolver.resolve()
        root = context.effective_workspace_root.resolve()
        original = Path(original_relative_path)
        candidates: list[str] = []
        for suffix in {original.suffix.lower(), ".md", ".json"}:
            if suffix not in {".md", ".json"}:
                continue
            for path in root.rglob(f"*{suffix}"):
                try:
                    rel = path.resolve().relative_to(root).as_posix()
                except (OSError, ValueError):
                    continue
                if rel == original_relative_path or any(part in {".git", ".devpilot"} for part in Path(rel).parts):
                    continue
                try:
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                except OSError:
                    continue
                if digest == approved_sha256:
                    candidates.append(rel)
                    if len(candidates) > 1:
                        return None
        return candidates[0] if len(candidates) == 1 else None

    def _start(self, *, source_kind: str, source_ref: str, artifact: dict[str, Any], relative_path: str, content: str, base_sha: str, actor: str, actor_role: str, session_principal: str) -> CommandResult:
        command="artifact review start"
        if not actor.strip() or not actor_role.strip() or actor.strip()!=session_principal.strip():
            return self._block(command,"GSDLC04D_SESSION_ACTOR_BINDING_BLOCK","Authenticated actor/session binding is required.")
        to_validating=self.lifecycle.transition(artifact,target_state=ArtifactState.VALIDATING,actor=actor,actor_role=actor_role)
        if not to_validating.ok: return self._dependency(command,to_validating,"GSDLC04D_VALIDATING_TRANSITION_BLOCK")
        artifact=to_validating.data["artifact"]
        findings, validation = self._validate(relative_path=relative_path, content=content, validators=list(artifact.get("validators") or []))
        blocking=any(x["severity"] in {"fail","block","error"} for x in findings)
        transitioned=self.lifecycle.transition(artifact,target_state=ArtifactState.FINDINGS if blocking else ArtifactState.READY_FOR_REVIEW,actor=actor,actor_role=actor_role,findings_present=blocking)
        if not transitioned.ok: return self._dependency(command,transitioned,"GSDLC04D_VALIDATION_TRANSITION_BLOCK")
        artifact=transitioned.data["artifact"]
        if blocking:
            record=self._record(source_kind,source_ref,artifact,relative_path,content,base_sha,findings,validation,None)
            record["status"]="FINDINGS"; self._write_record(record); self._sync_source_record(record)
            return CommandResult(command,False,ExitCode.BLOCK,"Artifact validation produced blocking findings; no plan/approval was created.",data={"review":record},findings=[Finding(x["id"],x["message"],Severity(x["severity"]),path=relative_path,metadata=x.get("metadata") or {}) for x in findings])
        approval_transition=self.lifecycle.transition(artifact,target_state=ArtifactState.APPROVAL_REQUIRED,actor=actor,actor_role=actor_role)
        if not approval_transition.ok: return self._dependency(command,approval_transition,"GSDLC04D_APPROVAL_ROLE_BLOCK")
        artifact=approval_transition.data["artifact"]
        plan_result=self.plans.plan_artifact(relative_path=relative_path,document_sha_before=base_sha,proposed_content=content,artifact_id=str(artifact["artifact_id"]))
        if not plan_result.ok: return self._dependency(command,plan_result,"GSDLC04D_PLAN_BLOCK")
        plan=deepcopy(plan_result.data["plan"])
        record=self._record(source_kind,source_ref,artifact,relative_path,content,base_sha,findings,validation,plan)
        record["status"]="APPROVAL_REQUIRED"; self._write_record(record); self._sync_source_record(record)
        return CommandResult(command,True,ExitCode.PASS,"Artifact validation passed; immutable diff/plan is approval-ready.",data={"review":record,"plan":plan},findings=[Finding("GSDLC04D_REVIEW_READY_PASS","Artifact is APPROVAL_REQUIRED with exact immutable plan/diff.",Severity.INFO,path=relative_path)])

    def _validate(self, *, relative_path: str, content: str, validators: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        found: list[dict[str, Any]]=[]
        def add(fid: str,msg: str,severity: str,line: int|None=None,section: str|None=None,metadata:dict[str,Any]|None=None):
            found.append({"id":fid,"message":msg,"severity":severity,"line":line,"section":section,"metadata":metadata or {}})
        profile=self.profiles.select(Path(relative_path))
        details={"profile_id":profile.id,"validators":validators,"validator_results":[]}
        if "secret-guard" in validators:
            decision=self.secret_guard.scan_text(content,subject=relative_path)
            ok=decision.effect.value!="block"; details["validator_results"].append({"validator":"secret-guard","status":"PASS" if ok else "BLOCK"})
            if not ok: add("GSDLC04D_SECRET_VALIDATION_BLOCK","SecretGuard detected secret-like content.","block")
        if relative_path.lower().endswith(".json"):
            try: json.loads(content); details["validator_results"].append({"validator":"json-syntax","status":"PASS"})
            except json.JSONDecodeError as exc: add("GSDLC04D_JSON_SYNTAX_BLOCK","JSON syntax is invalid.","block",line=exc.lineno,metadata={"column":exc.colno}); details["validator_results"].append({"validator":"json-syntax","status":"BLOCK"})
            if "json-schema" in validators: details["validator_results"].append({"validator":"json-schema","status":"NOT-APPLICABLE","reason":"No schema binding is declared by ArtifactProfile for this target."})
        else:
            doc=parse_frontmatter_text(content,path=Path(relative_path)); headings=extract_headings(doc.body)
            if "frontmatter" in validators:
                fm=validate_frontmatter_document(doc,root=None,strict=False); details["validator_results"].append({"validator":"frontmatter","status":"PASS" if fm.ok else "BLOCK"})
                for x in fm.findings:
                    sev="block" if x.severity in {Severity.FAIL,Severity.BLOCK,Severity.ERROR} else "warning"
                    add(f"GSDLC04D_{x.id}",x.message,sev,line=1,metadata=x.metadata)
            if "artifact-profile" in validators:
                missing=[]
                for expected in profile.required_headings:
                    norm=normalize_heading(expected); match=next((h for h in headings if norm in h.normalized),None)
                    if match is None:
                        missing.append(expected); add("GSDLC04D_REQUIRED_SECTION_BLOCK",f"Required section is missing: {expected}","block",section=expected,metadata={"profile_id":profile.id})
                details["validator_results"].append({"validator":"artifact-profile","status":"PASS" if not missing else "BLOCK","missing_required":missing})
        details["findings_total"]=len(found); details["blocking_findings_total"]=sum(1 for x in found if x["severity"] in {"fail","block","error"})
        return found,details

    def _record(self, source_kind:str, source_ref:str, artifact:dict[str,Any], relative_path:str, content:str, base_sha:str, findings:list[dict[str,Any]], validation:dict[str,Any], plan:dict[str,Any]|None) -> dict[str,Any]:
        seed=f"{artifact['artifact_id']}|{artifact['content_hash']}|{base_sha}|{source_kind}|{source_ref}"
        review_id=f"arev_{hashlib.sha256(seed.encode()).hexdigest()[:32]}"
        now=_now()
        return {"schema_id":"devpilot.gsdlc04d.artifact_review_record.v1","review_id":review_id,"source_kind":source_kind,"source_ref":source_ref,"workspace_id":self.documents.context_resolver.resolve().active_workspace_id,"artifact":artifact,"relative_path":relative_path,"content_sha256":hashlib.sha256(content.encode()).hexdigest(),"base_sha256":base_sha,"findings":findings,"validation":validation,"plan":plan,"approval_valid":False,"source_mutations_performed":False,"created_at":now,"updated_at":now,"network_used":False,"external_api_used":False,"secrets_exposed":False}

    def _record_path(self, review_id:str) -> Path|None:
        if not _REVIEW_ID.fullmatch(str(review_id or "")): return None
        context=self.documents.context_resolver.resolve(); wid=str(context.active_workspace_id or "")
        if not wid: return None
        return self.review_root/wid/f"{review_id}.json"

    def _write_record(self, record:dict[str,Any]) -> None:
        path=self._record_path(str(record["review_id"]));
        if path is None: raise RuntimeError("Review record path unavailable")
        with self._lock:
            path.parent.mkdir(parents=True,exist_ok=True); temp=path.with_suffix(".tmp")
            temp.write_text(json.dumps(record,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8"); temp.replace(path)

    def _sync_source_record(self, record:dict[str,Any]) -> None:
        # GSDLC-04-C import records are frozen historical DRAFT evidence. 04-D
        # keeps successor lifecycle/review state in its own runtime record and
        # never rewrites the strict 04-C schema merely to represent promotion.
        return None

    def _target(self,relative_path:str)->Path|None:
        context=self.documents.context_resolver.resolve(); root=context.effective_workspace_root.resolve(); target=(root/relative_path).resolve()
        try: target.relative_to(root)
        except ValueError:return None
        return target

    def _base_commit(self)->str:
        import subprocess
        root=self.documents.context_resolver.resolve().effective_workspace_root
        try:
            cp=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],capture_output=True,text=True,timeout=5,check=False)
            value=cp.stdout.strip(); return value if re.fullmatch(r"[0-9a-f]{40}",value) else "0"*40
        except Exception:return "0"*40

    @staticmethod
    def _block(command:str,fid:str,msg:str,metadata:dict[str,Any]|None=None)->CommandResult:
        return CommandResult(command,False,ExitCode.BLOCK,msg,data={"summary":{"source_mutations_performed":False}},findings=[Finding(fid,msg,Severity.BLOCK,metadata=metadata or {})])

    @staticmethod
    def _dependency(command:str,result:CommandResult,fid:str)->CommandResult:
        return CommandResult(command,False,ExitCode.BLOCK,result.message,data={"dependency":result.to_dict()},findings=[*result.findings,Finding(fid,result.message,Severity.BLOCK)])


def _now()->str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
