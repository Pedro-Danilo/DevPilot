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
from devpilot_core.guided_sdlc.step_action_advisor import AdvisorContext, ExecutionModeAdvisor
from devpilot_core.policy.path_guard import PathGuard
from devpilot_core.miasi.applicability import MIASIApplicabilityEvaluator
from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry
from devpilot_core.validators.artifact import extract_headings, normalize_heading
from devpilot_core.validators.frontmatter import parse_frontmatter_text, validate_frontmatter_document
from devpilot_core.workspace.runtime_project_context import parse_project_yaml_metadata

from .artifact_lifecycle_service import ArtifactLifecycleService, ArtifactState
from .artifact_review_service import ArtifactReviewApplicationService
from .workspace_documents_service import WorkspaceDocumentsApplicationService
from .workspace_edit_plan_service import ZERO_SHA256
from .workspace_edit_execution_service import WorkspaceEditExecutionApplicationService
from .pre_code_semantic_model import (
    build_candidate_model,
    normalize_owner_model,
    prepare_draft_first_model,
    requirement_records,
    semantic_hash,
    unresolved_decisions_for_stage,
    validate_confirmed_model,
    validate_model_for_stage,
    validate_rendered_artifact,
)

CATALOG = Path('.devpilot/gsdlc/pre_code_wizard_catalog.json')
STORE_ROOT = Path('outputs/pre_code_wizard/gsdlc_05_e')
STRUCTURE_RECEIPT_ROOT = Path('outputs/pre_code_wizard/gsdlc_13_c_01')
REQUIRED_DOCUMENT_PARENTS = (
    Path('docs/00_product'),
    Path('docs/01_requirements'),
    Path('docs/02_architecture'),
    Path('docs/02_architecture/adrs'),
    Path('docs/03_security'),
    Path('docs/04_quality'),
)
DERIVATION_MODEL = 'deterministic-semantic-model-template-v3'
DERIVATION_SCHEMA = 'devpilot.gsdlc13c01.deterministic_derivation.v3'
_SHA = re.compile(r'^[0-9a-f]{64}$')


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_text(text: str) -> str:
    return str(text or '').replace('\r\n', '\n').replace('\r', '\n')


def _sha_text(text: str) -> str:
    return _sha_bytes(_canonical_text(text).encode('utf-8'))


class PreCodeWizardApplicationService:
    """Server-authoritative governed pre-code vertical slice.

    GSDLC-13-C extends the historical MANUAL/IMPORT surface with a deterministic
    local/no-API proposal mode for Vision/Scope/Requirements. Human review, diff,
    approval, apply and freeze remain unchanged and server-authoritative.

    Runtime drafts/state live under platform outputs and never write managed source
    until the inherited UOC-005 approval-bound apply executes. The service composes
    ArtifactLifecycle/ArtifactReview and StepActionAdvisor rather than bypassing
    their policies.
    """

    def __init__(self, platform_root: Path, *, documents: WorkspaceDocumentsApplicationService, reviews: ArtifactReviewApplicationService, executions: WorkspaceEditExecutionApplicationService) -> None:
        self.root = Path(platform_root).resolve()
        self.documents = documents
        self.reviews = reviews
        self.executions = executions
        self.lifecycle = ArtifactLifecycleService(self.root)
        self.profiles = ArtifactProfileRegistry(self.root)
        self.advisor = ExecutionModeAdvisor(self.root)
        self.miasi = MIASIApplicabilityEvaluator(self.root)
        self.catalog = self._load_catalog()
        self._stages = sorted((dict(x) for x in self.catalog['stages']), key=lambda x: int(x['order']))
        self._stage_by_id = {str(x['stage_id']): x for x in self._stages}
        self._lock = threading.RLock()

    def status(self, *, effective_roles: list[str], workspace_scopes: list[str]) -> CommandResult:
        context = self._context()
        if isinstance(context, CommandResult): return context
        workspace_id, workspace_root = context
        state = self._load_state(workspace_id)
        projection = self._projection(state, workspace_id, workspace_root, effective_roles, workspace_scopes)
        return self._pass('guided pre-code status', 'GSDLC05E_PRE_CODE_STATUS_PASS', 'Pre-code wizard state projected from server-authoritative runtime state.', {'pre_code': projection})

    def reconcile_structure(self, *, effective_roles: list[str], workspace_scopes: list[str]) -> CommandResult:
        command='guided pre-code reconcile structure'
        context=self._context()
        if isinstance(context,CommandResult): return context
        workspace_id,workspace_root=context
        if 'owner' not in set(effective_roles):
            return self._block(command,'GSDLC13C01_STRUCTURE_OWNER_BLOCK','Owner role is required to reconcile governed document namespaces.')
        if workspace_id not in set(workspace_scopes):
            return self._block(command,'GSDLC13C01_STRUCTURE_SCOPE_BLOCK','Active workspace scope is required to reconcile governed document namespaces.',metadata={'workspace_id':workspace_id})
        return self._reconcile_governed_parents(workspace_id=workspace_id,workspace_root=workspace_root)

    def save_draft(self, *, stage_id: str, content: str, mode: str, actor: str, actor_role: str, session_principal: str, effective_roles: list[str], workspace_scopes: list[str], semantic_model: dict[str, Any] | None = None) -> CommandResult:
        command='guided pre-code save draft'
        context=self._context()
        if isinstance(context,CommandResult): return context
        workspace_id, workspace_root=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        stage=self._stage_by_id.get(str(stage_id))
        if stage is None:return self._block(command,'GSDLC05E_STAGE_UNKNOWN_BLOCK','Unknown pre-code stage.')
        normalized_mode=str(mode or '').upper()
        if normalized_mode not in stage['allowed_modes']:
            return self._block(command,'GSDLC05E_MODE_POLICY_BLOCK','Selected authoring mode is not allowed for the current stage.',metadata={'stage_id':stage_id,'mode':normalized_mode})
        if normalized_mode not in {'MANUAL','IMPORT','DEVPL_MOCK'}:
            return self._block(command,'GSDLC05E_MODE_BLOCK','Only governed MANUAL/IMPORT/DEVPL_MOCK modes are available.')
        state=self._load_state(workspace_id)
        current=self._current_stage(state)
        if current is None:
            return self._block(command,'GSDLC05E_ALREADY_READY_BLOCK','Pre-code wizard is already complete.')
        if current['stage_id'] != stage_id:
            return self._block(command,'GSDLC05E_STAGE_SKIP_BLOCK','Mandatory pre-code stages cannot be skipped.',metadata={'requested_stage':stage_id,'current_stage':current['stage_id']})
        row=self._stage_state(state,stage_id)
        derivation=None
        content=str(content or '')
        plan_invalidated=bool(row.get('plan_id') or row.get('approval_id'))
        if normalized_mode=='DEVPL_MOCK':
            semantic_result=self._ensure_semantic_model(stage_id=stage_id,workspace_id=workspace_id,workspace_root=workspace_root,state=state,submitted=semantic_model)
            if isinstance(semantic_result,CommandResult): return semantic_result
            owner_edit=bool(content.strip()) and str(row.get('mode') or '')=='DEVPL_MOCK' and row.get('status') in {'DRAFT','FINDINGS','APPROVAL_REQUIRED'} and semantic_model is None
            if owner_edit:
                content=_canonical_text(content)
                derivation=deepcopy(row.get('derivation') or {}) if isinstance(row.get('derivation'),dict) else {}
                generated_sha=str(derivation.get('generated_content_sha256') or row.get('content_sha256') or _sha_text(content))
                derivation.update({
                    'schema_id':str(derivation.get('schema_id') or DERIVATION_SCHEMA),
                    'mode':'DEVPL_MOCK','provider':'devpilot-local','model':DERIVATION_MODEL,
                    'network_used':False,'external_api_used':False,'cost_usd':0.0,
                    'generated_content_sha256':generated_sha,
                    'owner_edited':_sha_text(content)!=generated_sha,
                    'owner_edited_content_sha256':_sha_text(content),
                    'semantic_model_sha256':semantic_hash(semantic_result),
                    'semantic_model_schema_id':semantic_result.get('schema_id'),
                    'owner_semantic_reviewed':bool(semantic_result.get('owner_semantic_reviewed')),
                    'owner_review_required':True,'approval_required_before_source_write':True,
                })
            else:
                generated=self._derive_local_proposal(stage_id=stage_id,workspace_id=workspace_id,workspace_root=workspace_root,state=state)
                if isinstance(generated,CommandResult): return generated
                content,derivation=generated
        elif not content.strip():
            return self._block(command,'GSDLC05E_EMPTY_DRAFT_BLOCK','Draft content is required for MANUAL/IMPORT.')
        structure=self._reconcile_governed_parents(workspace_id=workspace_id,workspace_root=workspace_root)
        if not structure.ok:return structure
        target=(workspace_root/str(stage['relative_path'])).resolve()
        try: target.relative_to(workspace_root.resolve())
        except ValueError:return self._block(command,'GSDLC05E_TARGET_SCOPE_BLOCK','Pre-code artifact escaped the active workspace.')
        if not target.parent.is_dir() or target.parent.is_symlink():
            return self._block(command,'GSDLC05E_TARGET_PARENT_BLOCK','The project bootstrap must provide the governed document parent directory before authoring.',metadata={'relative_path':stage['relative_path']})
        base_sha=_sha_bytes(target.read_bytes()) if target.is_file() else ZERO_SHA256
        artifact_id='precode_'+hashlib.sha256(f"{workspace_id}|{stage_id}|{_sha_bytes(content.encode())}".encode()).hexdigest()[:24]
        lifecycle_source='AGENT_ASSISTED' if normalized_mode=='DEVPL_MOCK' else normalized_mode
        draft=self.lifecycle.create_draft(
            artifact_id=artifact_id,relative_path=str(stage['relative_path']),content=content,source_type=lifecycle_source,
            base_commit=self._base_commit(workspace_root),actor=actor,actor_role=actor_role,session_principal=session_principal,
            reviewer=actor,reviewer_role=actor_role,source_label='DevPilot deterministic local proposal / Owner-reviewed' if normalized_mode=='DEVPL_MOCK' else f'GSDLC-05-E {normalized_mode} browser DRAFT',
            source_reference=f'pre-code:{workspace_id}:{stage_id}:{normalized_mode.lower()}',
        )
        if not draft.ok:return draft
        row.update({'status':'DRAFT','mode':normalized_mode,'content':content,'content_sha256':_sha_bytes(content.encode()),'base_sha256':base_sha,'artifact':draft.data['artifact'],'derivation':derivation,'review_id':None,'plan_id':None,'plan_hash':None,'diff':None,'execution_id':None,'approval_id':None,'approved_sha256':None,'findings':[],'validation':{},'updated_at':_now()})
        state['status']='IN_PROGRESS'; state['updated_at']=_now(); self._write_state(workspace_id,state)
        if plan_invalidated:
            self._append_trace(workspace_id,{'event':'DRAFT_REOPENED_AND_PLAN_INVALIDATED','stage_id':stage_id,'actor':actor,'at':_now()})
        return self._pass(command,'GSDLC05E_DRAFT_SAVED_PASS','Server-authoritative DRAFT persisted outside managed source; source mutation remains false.',{'stage':self._public_stage(row,stage),'semantic_model':deepcopy(state.get('semantic_model')) if isinstance(state.get('semantic_model'),dict) else None,'source_mutations_performed':False,'plan_invalidated':plan_invalidated,'structure_reconciliation':structure.data.get('structure_reconciliation')})

    def start_review(self, *, stage_id: str, actor: str, actor_role: str, session_principal: str, effective_roles: list[str]) -> CommandResult:
        command='guided pre-code review'
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,_=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        state=self._load_state(workspace_id); current=self._current_stage(state)
        if current is None or current['stage_id']!=stage_id:return self._block(command,'GSDLC05E_STAGE_SKIP_BLOCK','Only the current mandatory stage can enter review.')
        row=self._stage_state(state,stage_id)
        if row.get('status') not in {'DRAFT','FINDINGS'} or not isinstance(row.get('artifact'),dict):
            return self._block(command,'GSDLC05E_DRAFT_REQUIRED_BLOCK','Save a current-stage DRAFT before validation/review.')
        if str(row.get('mode') or '')=='DEVPL_MOCK':
            model=state.get('semantic_model') if isinstance(state.get('semantic_model'),dict) else None
            semantic_findings=validate_model_for_stage(model or {},stage_id) + validate_rendered_artifact(stage_id,str(row.get('content') or ''),model or {})
            if semantic_findings:
                findings=[Finding('GSDLC13C01_SEMANTIC_QUALITY_BLOCK','Semantic quality gate blocked review before an approval-ready plan could be created.',Severity.BLOCK,metadata={'semantic_findings':semantic_findings})]
                findings.extend(Finding(str(item.get('id') or 'SEMANTIC_QUALITY_DETAIL_BLOCK'),str(item.get('message') or 'Semantic quality finding.'),Severity.BLOCK,metadata={k:v for k,v in item.items() if k not in {'id','message'}}) for item in semantic_findings)
                return CommandResult(command,False,ExitCode.BLOCK,'Semantic quality gate blocked review before an approval-ready plan could be created.',data={},findings=findings)
        # A corrected draft always starts a new lifecycle record; persisted row artifact is DRAFT.
        result=self.reviews.start_runtime_draft(source_kind=str(row.get('mode') or 'MANUAL'),source_ref=f'pre-code:{workspace_id}:{stage_id}',artifact=deepcopy(row['artifact']),relative_path=str(self._stage_by_id[stage_id]['relative_path']),content=str(row.get('content') or ''),base_sha=str(row.get('base_sha256') or ZERO_SHA256),actor=actor,actor_role=actor_role,session_principal=session_principal)
        review=(result.data or {}).get('review') if isinstance(result.data,dict) else None
        if isinstance(review,dict):
            row['review_id']=review.get('review_id'); row['status']=str(review.get('status') or 'FINDINGS'); row['findings']=list(review.get('findings') or []); row['validation']=dict(review.get('validation') or {}); row['updated_at']=_now()
            plan=review.get('plan') if isinstance(review.get('plan'),dict) else None
            if plan:
                row['plan_id']=plan.get('plan_id'); row['plan_hash']=plan.get('plan_hash'); row['diff']=plan.get('diff') or plan.get('unified_diff') or plan.get('preview')
            self._write_state(workspace_id,state)
        return result

    def request_approval(self, *, stage_id: str, actor: str, actor_role: str, session_principal: str, effective_roles: list[str], reason: str) -> CommandResult:
        command='guided pre-code approval request'
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,_=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        state=self._load_state(workspace_id); current=self._current_stage(state)
        if current is None or current['stage_id']!=stage_id:return self._block(command,'GSDLC05E_STAGE_SKIP_BLOCK','Only current stage can request approval.')
        row=self._stage_state(state,stage_id)
        if row.get('status')!='APPROVAL_REQUIRED' or not row.get('plan_id') or not row.get('plan_hash'):
            return self._block(command,'GSDLC05E_APPROVAL_PLAN_REQUIRED_BLOCK','Current stage must pass validation and produce an immutable plan before approval.')
        result=self.executions.request_apply_approval(plan_id=str(row['plan_id']),plan_hash=str(row['plan_hash']),actor=actor,reason=str(reason or 'Approve governed pre-code artifact apply.'),ttl_minutes=30)
        if result.ok:
            approval=(result.data or {}).get('approval') if isinstance(result.data,dict) else None
            approval_id=str((approval or {}).get('approval_id') or (result.data or {}).get('approval_id') or '')
            if not approval_id:
                # ApprovalApplicationService payloads historically expose the record under approval.
                candidates=[v for v in (result.data or {}).values() if isinstance(v,dict) and str(v.get('approval_id') or '')]
                approval_id=str(candidates[0].get('approval_id')) if candidates else ''
            if not approval_id:return self._block(command,'GSDLC05E_APPROVAL_ID_MISSING_BLOCK','Approval store did not return an approval id.')
            row['approval_id']=approval_id; row['updated_at']=_now(); self._write_state(workspace_id,state)
            data=dict(result.data or {}); data['pre_code']={'stage_id':stage_id,'approval_id':approval_id,'plan_id':row['plan_id'],'plan_hash':row['plan_hash']}
            return CommandResult(command,True,ExitCode.PASS,'Approval request is bound to current immutable plan.',data=data,findings=result.findings)
        return result

    def apply(self, *, stage_id: str, actor: str, actor_role: str, session_principal: str, effective_roles: list[str]) -> CommandResult:
        command='guided pre-code apply'
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,_=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        state=self._load_state(workspace_id); current=self._current_stage(state)
        if current is None or current['stage_id']!=stage_id:return self._block(command,'GSDLC05E_STAGE_SKIP_BLOCK','Only current stage can be applied.')
        row=self._stage_state(state,stage_id)
        required=['plan_id','plan_hash','approval_id','review_id']
        if row.get('status')!='APPROVAL_REQUIRED' or any(not row.get(k) for k in required):return self._block(command,'GSDLC05E_APPLY_BINDING_BLOCK','Current stage lacks review/plan/approval binding.')
        result=self.executions.apply(plan_id=str(row['plan_id']),plan_hash=str(row['plan_hash']),approval_id=str(row['approval_id']),actor=actor)
        if result.ok:
            execution=dict((result.data or {}).get('execution') or {}); execution_id=str(execution.get('execution_id') or ((result.data or {}).get('summary') or {}).get('execution_id') or '')
            if not execution_id:return self._block(command,'GSDLC05E_EXECUTION_ID_MISSING_BLOCK','Approved apply returned no execution id.')
            row['execution_id']=execution_id; row['status']='APPLIED'; row['updated_at']=_now(); self._write_state(workspace_id,state)
            data=dict(result.data or {}); data['pre_code']={'stage_id':stage_id,'review_id':row['review_id'],'execution_id':execution_id,'approval_id':row['approval_id']}
            return CommandResult(command,True,ExitCode.PASS,'Approval-bound source apply completed; freeze is the next mandatory action.',data=data,findings=result.findings)
        return result

    def freeze(self, *, stage_id: str, review_id: str, execution_id: str, actor: str, actor_role: str, session_principal: str, effective_roles: list[str], workspace_scopes: list[str]) -> CommandResult:
        command='guided pre-code freeze'
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,workspace_root=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        state=self._load_state(workspace_id); current=self._current_stage(state)
        if current is None or current['stage_id']!=stage_id:return self._block(command,'GSDLC05E_STAGE_SKIP_BLOCK','Only the current mandatory stage can be frozen.')
        row=self._stage_state(state,stage_id)
        if row.get('status') != 'APPLIED':
            return self._block(command,'GSDLC05E_APPLY_REQUIRED_BLOCK','Freeze requires the current stage to have an approved applied execution.')
        if str(row.get('review_id') or '')!=str(review_id or '') or str(row.get('execution_id') or '')!=str(execution_id or ''):
            return self._block(command,'GSDLC05E_REVIEW_BINDING_BLOCK','Freeze review id does not match current stage review.')
        result=self.reviews.freeze(review_id=review_id,execution_id=execution_id,actor=actor,actor_role=actor_role,session_principal=session_principal)
        if not result.ok:return result
        review=dict((result.data or {}).get('review') or {})
        if review.get('status')!='FROZEN':return self._block(command,'GSDLC05E_FREEZE_POSTCONDITION_BLOCK','Artifact review did not reach FROZEN.')
        row.update({'status':'FROZEN','execution_id':execution_id,'approval_id':review.get('approval_id'),'approved_sha256':review.get('approved_sha256'),'artifact':review.get('artifact'),'content':None,'updated_at':_now()})
        self._append_trace(workspace_id,{'event':'STAGE_FROZEN','stage_id':stage_id,'order':current['order'],'actor':actor,'actor_role':actor_role,'relative_path':current['relative_path'],'review_id':review_id,'execution_id':execution_id,'approval_id':review.get('approval_id'),'approved_sha256':review.get('approved_sha256'),'at':_now()})
        next_stage=self._current_stage(state)
        if next_stage is None:
            readiness=self._readiness_payload(state,workspace_id,workspace_root)
            state['status']='PRE_CODE_READY' if readiness['status']=='PASS' else 'BLOCKED'
            state['readiness']=readiness
            state['completed_at']=_now() if readiness['status']=='PASS' else None
        else:
            state['status']='IN_PROGRESS'
        state['updated_at']=_now(); self._write_state(workspace_id,state)
        projection=self._projection(state,workspace_id,workspace_root,effective_roles,workspace_scopes)
        return self._pass(command,'GSDLC05E_STAGE_FROZEN_PASS','Stage frozen through approval-bound apply; wizard advanced without skip.',{'pre_code':projection,'review':review})

    def reopen_c01_for_retest(self, *, actor: str, actor_role: str, session_principal: str, effective_roles: list[str], workspace_scopes: list[str], reason: str) -> CommandResult:
        """Governed runtime-only reset of C-01 for an exact selective retest.

        Preserves managed source bytes and archives the prior runtime state/trace.
        This is intentionally not exposed as a normal-user HTTP route.
        """
        command='guided pre-code reopen C-01 retest'
        context=self._context()
        if isinstance(context,CommandResult): return context
        workspace_id,workspace_root=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        if workspace_id not in set(workspace_scopes):
            return self._block(command,'GSDLC13C01_RETEST_SCOPE_BLOCK','Active workspace scope is required for governed C-01 retest reopen.',metadata={'workspace_id':workspace_id})
        state=self._load_state(workspace_id)
        c01=('product-vision','scope','requirements')
        for stage_id in c01:
            row=self._stage_state(state,stage_id)
            if row.get('status')!='FROZEN':
                return self._block(command,'GSDLC13C01_RETEST_FROZEN_REQUIRED_BLOCK','C-01 retest reopen requires all three prior C-01 stages to be FROZEN.',metadata={'stage_id':stage_id,'status':row.get('status')})
            stage=self._stage_by_id[stage_id]; target=workspace_root/str(stage['relative_path'])
            approved=str(row.get('approved_sha256') or '')
            actual=_sha_bytes(target.read_bytes()) if target.is_file() else ''
            if not _SHA.fullmatch(approved) or actual!=approved:
                return self._block(command,'GSDLC13C01_RETEST_SOURCE_DRIFT_BLOCK','C-01 retest reopen refused because a prior FROZEN source no longer matches its approved bytes.',metadata={'stage_id':stage_id,'approved_sha256':approved or None,'actual_sha256':actual or None})
        current=self._current_stage(state)
        if current is None or current.get('stage_id')!='architecture':
            return self._block(command,'GSDLC13C01_RETEST_BOUNDARY_BLOCK','C-01 retest reopen is allowed only at the post-Requirements boundary before Architecture starts.',metadata={'current_stage_id':current.get('stage_id') if current else None})
        archive_root=self._state_path(workspace_id).parent/'history'
        archive_root.mkdir(parents=True,exist_ok=True)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        state_archive=archive_root/f'c01_before_retest_{stamp}_state.json'
        state_archive.write_text(json.dumps(state,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
        trace_path=self._trace_path(workspace_id)
        trace_archive=None
        if trace_path.is_file():
            trace_archive=archive_root/f'c01_before_retest_{stamp}_trace.jsonl'
            trace_archive.write_bytes(trace_path.read_bytes())
        for stage_id in c01:
            prior=deepcopy(self._stage_state(state,stage_id))
            row=self._stage_state(state,stage_id)
            row.clear(); row.update({
                'stage_id':stage_id,'status':'MISSING','mode':None,'content_sha256':None,
                'base_sha256':prior.get('approved_sha256'),'artifact':None,'derivation':None,
                'review_id':None,'plan_id':None,'plan_hash':None,'diff':None,'execution_id':None,
                'approval_id':None,'approved_sha256':None,'findings':[],'validation':{},'updated_at':_now(),
                'retest_baseline_approved_sha256':prior.get('approved_sha256'),
            })
        state['semantic_model']=None; state['status']='IN_PROGRESS'; state['completed_at']=None; state.pop('readiness',None); state['updated_at']=_now()
        self._write_state(workspace_id,state)
        event={'event':'C01_RETEST_REOPENED','actor':actor,'actor_role':actor_role,'reason':str(reason or 'Selective retest after approved corrective'),'state_archive':str(state_archive.relative_to(self.root)).replace('\\','/'),'trace_archive':str(trace_archive.relative_to(self.root)).replace('\\','/') if trace_archive else None,'project_source_mutations':0,'at':_now()}
        self._append_trace(workspace_id,event)
        return self._pass(command,'GSDLC13C01_RETEST_REOPEN_PASS','C-01 runtime state reopened for an exact selective retest; prior evidence archived and managed project source bytes preserved.',{'workspace_id':workspace_id,'state_archive':event['state_archive'],'trace_archive':event['trace_archive'],'project_source_mutations':0})

    def readiness(self, *, effective_roles: list[str], workspace_scopes: list[str]) -> CommandResult:
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,workspace_root=context
        state=self._load_state(workspace_id); payload=self._readiness_payload(state,workspace_id,workspace_root)
        ok=payload['status']=='PASS'
        return CommandResult('guided pre-code readiness',ok,ExitCode.PASS if ok else ExitCode.BLOCK,'Guided pre-code vertical-slice strict readiness passed.' if ok else 'Guided pre-code vertical-slice strict readiness is blocked.',data={'readiness':payload},findings=[] if ok else [Finding('GSDLC05E_READINESS_STRICT_BLOCK','One or more mandatory wizard stages are not frozen/source-valid.',Severity.BLOCK,metadata={'blockers':payload['blockers']})])

    def _projection(self,state:dict[str,Any],workspace_id:str,workspace_root:Path,effective_roles:list[str],workspace_scopes:list[str])->dict[str,Any]:
        current=self._current_stage(state)
        advisor_payload=None
        miasi=self._miasi_payload(workspace_id)
        if current is not None:
            artifact_status=str(self._stage_state(state,current['stage_id']).get('status') or 'MISSING')
            ctx=AdvisorContext(workspace_id=workspace_id,current_step=str(current['advisor_step']),effective_roles=tuple(effective_roles),workspace_scopes=tuple(workspace_scopes),artifact_readiness='READY' if artifact_status in {'DRAFT','APPROVAL_REQUIRED','FROZEN'} else 'UNKNOWN',miasi_gate_status=str(miasi.get('gate_status') or 'BLOCK'),provider_status='NOT_AVAILABLE',budget_status='NOT_APPLICABLE',active_project_context=True)
            advisor_payload=self.advisor.advise(ctx).to_payload()
        readiness=self._readiness_payload(state,workspace_id,workspace_root,miasi=miasi)
        return {'schema_id':'devpilot.gsdlc05e.pre_code_projection.v1','profile_id':self.catalog['profile_id'],'readiness_semantics':self.catalog.get('readiness_semantics'),'workspace_id':workspace_id,'status':state.get('status','NOT_STARTED'),'current_stage_id':current['stage_id'] if current else None,'current_stage_order':current['order'] if current else None,'stages':[self._public_stage(self._stage_state(state,x['stage_id']),x) for x in self._stages],'semantic_model':deepcopy(state.get('semantic_model')) if isinstance(state.get('semantic_model'),dict) else None,'advisor':advisor_payload,'miasi':miasi,'readiness':readiness,'transition_trace_ref':f'outputs/pre_code_wizard/gsdlc_05_e/{workspace_id}/transition_trace.jsonl','server_authoritative':True,'normal_user_powershell_required':0,'external_operator_project_writes':0,'network_used':False,'external_api_used':False,'model_execution_used':False,'agent_execution_used':False,'rag_execution_used':False,'deterministic_local_derivation_available':bool(current and 'DEVPL_MOCK' in current.get('allowed_modes',[]))}

    def _readiness_payload(self,state:dict[str,Any],workspace_id:str,workspace_root:Path,*,miasi:dict[str,Any]|None=None)->dict[str,Any]:
        blockers=[]; artifacts=[]
        miasi=miasi or self._miasi_payload(workspace_id)
        miasi_gate=str(miasi.get('gate_status') or 'BLOCK').upper()
        miasi_required_now=self._current_stage(state) is None
        if miasi_gate!='PASS' and (miasi_gate!='DEFERRED' or miasi_required_now):
            blockers.append({'stage_id':'miasi-applicability','status':str(miasi.get('status') or 'REVIEW_REQUIRED'),'reason':'MIASI gate must PASS at strict pre-code readiness; before that checkpoint missing context is DEFERRED','reason_codes':list(miasi.get('reason_codes') or [])})
        for stage in self._stages:
            row=self._stage_state(state,stage['stage_id']); target=(workspace_root/stage['relative_path']).resolve(); status=str(row.get('status') or 'MISSING'); actual_sha=_sha_bytes(target.read_bytes()) if target.is_file() else None
            expected=str(row.get('approved_sha256') or '') or None
            profile_ok=False; profile_findings=[]
            if target.is_file():
                try:
                    content=target.read_text(encoding='utf-8'); doc=parse_frontmatter_text(content,path=Path(stage['relative_path'])); fm=validate_frontmatter_document(doc,root=None,strict=True); headings=extract_headings(doc.body); profile=self.profiles.select(Path(stage['relative_path'])); missing=[h for h in profile.required_headings if not any(normalize_heading(h) in x.normalized for x in headings)]; profile_ok=fm.ok and not missing; profile_findings=missing
                except Exception as exc: profile_findings=[str(exc)]
            ok=status=='FROZEN' and bool(expected) and actual_sha==expected and profile_ok
            if not ok:blockers.append({'stage_id':stage['stage_id'],'status':status,'source_exists':target.is_file(),'expected_sha256':expected,'actual_sha256':actual_sha,'profile_ok':profile_ok,'profile_findings':profile_findings})
            artifacts.append({'stage_id':stage['stage_id'],'relative_path':stage['relative_path'],'lifecycle_state':status,'approved_sha256':expected,'actual_sha256':actual_sha,'profile_id':stage['profile_id'],'profile_valid':profile_ok})
        return {'schema_id':'devpilot.gsdlc05e.pre_code_readiness.v1','profile_id':self.catalog['profile_id'],'strict':True,'scope':'guided-pre-code-manual-v1/vertical-slice','status':'PASS' if not blockers else 'BLOCK','pre_code_ready':not blockers,'mandatory_stages_total':len(self._stages),'mandatory_stages_frozen':sum(1 for x in artifacts if x['lifecycle_state']=='FROZEN'),'artifacts':artifacts,'miasi':miasi,'blockers':blockers,'historical_global_readiness_replaced':False,'network_used':False,'external_api_used':False}

    def _miasi_payload(self,workspace_id:str)->dict[str,Any]:
        context_path=self.miasi.context_path(workspace_id)
        if not context_path.is_file():
            try: context_source=context_path.relative_to(self.root).as_posix()
            except ValueError: context_source=str(context_path)
            return {
                'status':'NOT_EVALUATED','gate_status':'DEFERRED',
                'reason_codes':['MIASI_APPLICABILITY_DEFERRED_UNTIL_PRE_CODE'],
                'risk_level':'unknown','project_decision':{},'feature_decisions':[],
                'required_controls':[],'missing_controls':[],'policy_binding':{},'blockers':[],
                'evidence_refs':[],'context_source':context_source,'reevaluation_required':True,
                'agent_execution_allowed':False,'rag_execution_allowed':False,
                'execution_reason_code':'MIASI_EVALUATION_DEFERRED',
                'network_used':False,'external_api_used':False,'model_execution_used':False,
                'agents_executed':False,'rag_executed':False,'source_mutations_performed':False,
                'pre_code_authoritative':False,'blocking_scope':'pre-code-readiness',
            }
        try:
            payload=self.miasi.evaluate_workspace(workspace_id, {'artifacts': []}).to_payload()
            payload.update({'pre_code_authoritative':True,'blocking_scope':'pre-code-readiness'})
            return payload
        except Exception:
            # Once context exists MIASI is authoritative and evaluator failures remain fail-closed.
            return {
                'status':'REVIEW_REQUIRED','gate_status':'BLOCK',
                'reason_codes':['MIASI_APPLICABILITY_EVALUATION_ERROR'],
                'risk_level':'unknown','project_decision':{},'feature_decisions':[],
                'required_controls':[],'missing_controls':[],'policy_binding':{},
                'blockers':[{'code':'MIASI_APPLICABILITY_EVALUATION_ERROR','message':'MIASI applicability could not be evaluated deterministically.'}],
                'evidence_refs':[],'context_source':'unavailable','reevaluation_required':True,
                'agent_execution_allowed':False,'rag_execution_allowed':False,
                'network_used':False,'external_api_used':False,'model_execution_used':False,
                'agents_executed':False,'rag_executed':False,'source_mutations_performed':False,
                'pre_code_authoritative':True,'blocking_scope':'pre-code-readiness',
            }

    def _load_catalog(self)->dict[str,Any]:
        payload=json.loads((self.root/CATALOG).read_text(encoding='utf-8'))
        stages=payload.get('stages')
        if payload.get('schema_id')!='devpilot.gsdlc05e.pre_code_wizard_catalog.v1' or not isinstance(stages,list) or len(stages)!=7:raise ValueError('invalid GSDLC-05-E wizard catalog')
        ids=[x.get('stage_id') for x in stages]; orders=[x.get('order') for x in stages]
        if len(set(ids))!=7 or sorted(orders)!=list(range(1,8)):raise ValueError('wizard catalog stage id/order drift')
        return payload

    def _context(self):
        context=self.documents.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id or context.active_workspace_root is None:
            return self._block('guided pre-code','GSDLC05E_PROJECT_CONTEXT_REQUIRED_BLOCK','An active server-valid project context is required.')
        return str(context.active_workspace_id),context.active_workspace_root.resolve()

    def _initial_state(self,workspace_id:str)->dict[str,Any]:
        return {'schema_id':'devpilot.gsdlc05e.pre_code_state.v1','workspace_id':workspace_id,'profile_id':self.catalog['profile_id'],'status':'NOT_STARTED','semantic_model':None,'stages':{x['stage_id']:{'stage_id':x['stage_id'],'status':'MISSING','mode':None,'content_sha256':None,'base_sha256':None,'artifact':None,'derivation':None,'review_id':None,'plan_id':None,'plan_hash':None,'diff':None,'execution_id':None,'approval_id':None,'approved_sha256':None,'findings':[],'validation':{},'updated_at':None} for x in self._stages},'created_at':_now(),'updated_at':_now(),'completed_at':None}

    def _state_path(self,workspace_id:str)->Path:
        safe=re.sub(r'[^A-Za-z0-9_.-]','_',workspace_id); return self.root/STORE_ROOT/safe/'state.json'
    def _trace_path(self,workspace_id:str)->Path:
        return self._state_path(workspace_id).with_name('transition_trace.jsonl')
    def _load_state(self,workspace_id:str)->dict[str,Any]:
        p=self._state_path(workspace_id)
        if not p.is_file():return self._initial_state(workspace_id)
        try: data=json.loads(p.read_text(encoding='utf-8'))
        except Exception:return self._initial_state(workspace_id)
        return data if data.get('schema_id')=='devpilot.gsdlc05e.pre_code_state.v1' and data.get('workspace_id')==workspace_id else self._initial_state(workspace_id)
    def _write_state(self,workspace_id:str,state:dict[str,Any])->None:
        p=self._state_path(workspace_id); p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix('.tmp')
        with self._lock:
            tmp.write_text(json.dumps(state,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8'); os.replace(tmp,p)
    def _append_trace(self,workspace_id:str,event:dict[str,Any])->None:
        p=self._trace_path(workspace_id); p.parent.mkdir(parents=True,exist_ok=True)
        with self._lock:
            with p.open('a',encoding='utf-8',newline='\n') as f: f.write(json.dumps(event,sort_keys=True,ensure_ascii=False)+'\n')
    def _current_stage(self,state:dict[str,Any])->dict[str,Any]|None:
        for stage in self._stages:
            if str(self._stage_state(state,stage['stage_id']).get('status') or 'MISSING')!='FROZEN':return stage
        return None
    @staticmethod
    def _stage_state(state:dict[str,Any],stage_id:str)->dict[str,Any]: return state['stages'][stage_id]
    @staticmethod
    def _public_stage(row:dict[str,Any],stage:dict[str,Any])->dict[str,Any]:
        return {'stage_id':stage['stage_id'],'order':stage['order'],'label':stage['label'],'relative_path':stage['relative_path'],'profile_id':stage['profile_id'],'advisor_step':stage['advisor_step'],'allowed_modes':list(stage['allowed_modes']),'status':row.get('status'),'mode':row.get('mode'),'content_sha256':row.get('content_sha256'),'base_sha256':row.get('base_sha256'),'draft_content':row.get('content') if row.get('status') in {'DRAFT','FINDINGS','APPROVAL_REQUIRED'} else None,'derivation':dict(row.get('derivation') or {}) if isinstance(row.get('derivation'),dict) else None,'review_id':row.get('review_id'),'plan_id':row.get('plan_id'),'plan_hash':row.get('plan_hash'),'diff':row.get('diff'),'execution_id':row.get('execution_id'),'approval_id':row.get('approval_id'),'approved_sha256':row.get('approved_sha256'),'findings':list(row.get('findings') or []),'validation':dict(row.get('validation') or {})}
    def _ensure_semantic_model(self, *, stage_id: str, workspace_id: str, workspace_root: Path, state: dict[str, Any], submitted: dict[str, Any] | None) -> dict[str, Any] | CommandResult:
        command='guided pre-code semantic model'
        existing=state.get('semantic_model') if isinstance(state.get('semantic_model'),dict) else None
        if stage_id!='product-vision':
            if not existing:
                return self._block(command,'GSDLC13C01_SEMANTIC_MODEL_REQUIRED_BLOCK','A PreCode Semantic Model from Product Vision is required before deterministic downstream generation.')
            if submitted is None:
                return existing
            try:
                updated=normalize_owner_model(existing,submitted)
            except ValueError as exc:
                return self._block(command,'GSDLC13C01_SEMANTIC_MODEL_INPUT_BLOCK',str(exc))
            state['semantic_model']=updated; state['updated_at']=_now(); self._write_state(workspace_id,state)
            self._append_trace(workspace_id,{'event':'SEMANTIC_DECISIONS_UPDATED','stage_id':stage_id,'semantic_model_sha256':updated['semantic_model_sha256'],'actor':'owner','at':_now()})
            return updated
        project_file=workspace_root/'.devpilot/project.yaml'
        if not project_file.is_file():
            return self._block(command,'GSDLC13C01_PROJECT_CONTEXT_BLOCK','Project context is missing; Semantic Model cannot be grounded.')
        metadata=parse_project_yaml_metadata(project_file)
        need=str(metadata.get('business_need') or '').strip()
        constraints=dict(metadata.get('project_constraints') or {}) if isinstance(metadata.get('project_constraints'),dict) else {}
        model_policy=dict(metadata.get('model_policy') or {}) if isinstance(metadata.get('model_policy'),dict) else {}
        project_text=_canonical_text(project_file.read_text(encoding='utf-8'))
        if existing is None:
            candidate=build_candidate_model(workspace_id=workspace_id,business_need=need,source_ref='.devpilot/project.yaml',source_sha256=_sha_text(project_text),constraints=constraints,model_policy=model_policy)
            existing=prepare_draft_first_model(candidate)
            state['semantic_model']=existing; state['status']='IN_PROGRESS'; state['updated_at']=_now(); self._write_state(workspace_id,state)
            self._append_trace(workspace_id,{'event':'SEMANTIC_MODEL_PREPARED_DRAFT_FIRST','semantic_model_sha256':existing['semantic_model_sha256'],'at':_now()})
        if submitted is None:
            return existing
        try:
            updated=normalize_owner_model(existing,submitted)
        except ValueError as exc:
            return self._block(command,'GSDLC13C01_SEMANTIC_MODEL_INPUT_BLOCK',str(exc))
        state['semantic_model']=updated; state['updated_at']=_now(); self._write_state(workspace_id,state)
        self._append_trace(workspace_id,{'event':'SEMANTIC_DECISIONS_UPDATED','stage_id':stage_id,'semantic_model_sha256':updated['semantic_model_sha256'],'actor':'owner','at':_now()})
        return updated

    def _derive_local_proposal(self, *, stage_id: str, workspace_id: str, workspace_root: Path, state: dict[str, Any]) -> tuple[str, dict[str, Any]] | CommandResult:
        command='guided pre-code deterministic local proposal'
        if stage_id not in {'product-vision','scope','requirements'}:
            return self._block(command,'GSDLC13C01_DERIVATION_SCOPE_BLOCK','DEVPL_MOCK derivation is limited to Vision/Scope/Requirements in 13-C-01.')
        project_file=workspace_root/'.devpilot/project.yaml'
        if not project_file.is_file():
            return self._block(command,'GSDLC13C01_PROJECT_CONTEXT_BLOCK','Project context is missing; deterministic proposal cannot be grounded.')
        project_text=_canonical_text(project_file.read_text(encoding='utf-8'))
        metadata=parse_project_yaml_metadata(project_file)
        need=str(metadata.get('business_need') or '').strip()
        name=str(metadata.get('project_name') or metadata.get('project_id') or workspace_id).strip()
        project_id=str(metadata.get('project_id') or workspace_id).strip()
        constraints=dict(metadata.get('project_constraints') or {}) if isinstance(metadata.get('project_constraints'),dict) else {}
        model_policy=dict(metadata.get('model_policy') or {}) if isinstance(metadata.get('model_policy'),dict) else {}
        if len(need)<20:
            return self._block(command,'GSDLC13C01_BUSINESS_NEED_BLOCK','Persisted business need is missing or too short for governed derivation.')
        document_date=self._project_document_date(workspace_root)
        refs=[{'path':'.devpilot/project.yaml','sha256':_sha_text(project_text),'kind':'project-context'}]
        upstream:dict[str,str]={}
        required_upstream=() if stage_id=='product-vision' else (('product-vision',) if stage_id=='scope' else ('product-vision','scope'))
        for source_id in required_upstream:
            source_stage=self._stage_by_id[source_id]
            source_row=self._stage_state(state,source_id)
            if source_row.get('status')!='FROZEN':
                return self._block(command,'GSDLC13C01_PREVIOUS_STAGE_REQUIRED_BLOCK','Required governed upstream stage must be FROZEN before derivation.',metadata={'required_stage':source_id})
            source_path=workspace_root/str(source_stage['relative_path'])
            if not source_path.is_file():
                return self._block(command,'GSDLC13C01_PREVIOUS_SOURCE_MISSING_BLOCK','Frozen upstream source is missing.',metadata={'required_stage':source_id})
            source_bytes=source_path.read_bytes()
            approved_sha=str(source_row.get('approved_sha256') or '')
            actual_sha=_sha_bytes(source_bytes)
            if not _SHA.fullmatch(approved_sha) or actual_sha!=approved_sha:
                return self._block(command,'GSDLC13C01_PREVIOUS_SOURCE_DRIFT_BLOCK','Frozen upstream source no longer matches its approved content hash.',metadata={'required_stage':source_id,'expected_sha256':approved_sha or None,'actual_sha256':actual_sha})
            text=_canonical_text(source_bytes.decode('utf-8'))
            upstream[source_id]=text
            refs.append({'path':str(source_stage['relative_path']),'sha256':_sha_text(text),'approved_sha256':approved_sha,'kind':'frozen-input'})
        semantic_model=state.get('semantic_model') if isinstance(state.get('semantic_model'),dict) else None
        if not semantic_model or semantic_model.get('schema_id')!='devpilot.gsdlc13c01.pre_code_semantic_model.v1':
            return self._block(command,'GSDLC13C01_SEMANTIC_MODEL_REQUIRED_BLOCK','A valid PreCode Semantic Model is required for deterministic generation.')
        canonical_input={
            'generator_version':DERIVATION_MODEL,
            'stage_id':stage_id,
            'workspace_id':workspace_id,
            'project':{
                'project_id':project_id,'project_name':name,'business_need':' '.join(need.split()),
                'document_date':document_date,'project_constraints':constraints,'model_policy':model_policy,
            },
            'semantic_model':semantic_model,
            'upstream':upstream,
        }
        canonical_json=json.dumps(canonical_input,sort_keys=True,separators=(',',':'),ensure_ascii=False)
        content=self._proposal_markdown(
            stage_id=stage_id,workspace_id=workspace_id,project_name=name,business_need=need,
            document_date=document_date,constraints=constraints,model_policy=model_policy,upstream=upstream,semantic_model=semantic_model,
        )
        derivation={
            'schema_id':DERIVATION_SCHEMA,
            'mode':'DEVPL_MOCK','provider':'devpilot-local','model':DERIVATION_MODEL,
            'network_used':False,'external_api_used':False,'cost_usd':0.0,
            'source_refs':refs,'canonical_input_sha256':_sha_bytes(canonical_json.encode('utf-8')),
            'generated_content_sha256':_sha_text(content),
            'semantic_model_sha256':semantic_hash(semantic_model),'semantic_model_schema_id':semantic_model.get('schema_id'),'owner_semantic_reviewed':bool(semantic_model.get('owner_semantic_reviewed')),
            'owner_review_required':True,'approval_required_before_source_write':True,
        }
        return content,derivation

    @staticmethod
    def _business_clauses(text: str) -> list[str]:
        normalized=' '.join(str(text or '').split())
        parts=[x.strip(' .') for x in re.split(r'[;.]|,\s+(?=(?:y\s+)?[A-Za-zÁÉÍÓÚáéíóúÑñ])', normalized) if x.strip(' .')]
        return parts[:10] or [normalized]

    @staticmethod
    def _markdown_section(text: str, heading: str) -> str:
        target=normalize_heading(heading)
        lines=_canonical_text(text).split('\n')
        captured:list[str]=[]; active=False
        for line in lines:
            if line.startswith('## '):
                current=normalize_heading(line[3:].strip())
                if active: break
                active=current==target
                continue
            if active: captured.append(line)
        return '\n'.join(captured).strip()

    @classmethod
    def _semantic_items(cls, text: str, heading: str) -> list[str]:
        section=cls._markdown_section(text,heading)
        if not section:return []
        bullets=[]
        for raw in section.splitlines():
            line=raw.strip()
            if not line:continue
            line=re.sub(r'^(?:[-*+]\s+|\d+[.)]\s+)', '', line).strip()
            line=re.sub(r'^\*\*(?:RF-\d+|RNF-\d+)[^*]*\*\*\s*[—:-]*\s*','',line).strip()
            if line:bullets.append(line.rstrip('.'))
        if bullets:return bullets[:12]
        return cls._business_clauses(section)[:12]

    @staticmethod
    def _clean_scope_capability(value: str) -> str:
        text=' '.join(str(value or '').split()).strip(' .')
        for prefix in ('Incluir la capacidad necesaria para:', 'Incluir la capacidad para:', 'Incluir:'):
            if text.lower().startswith(prefix.lower()):
                text=text[len(prefix):].strip(' .')
                break
        return text

    @staticmethod
    def _constraint_lines(constraints: dict[str,Any], model_policy: dict[str,Any]) -> list[str]:
        local_first=bool(constraints.get('local_first',True))
        cloud_required=bool(constraints.get('cloud_required',False))
        operator_writes=bool(constraints.get('operator_project_writes_allowed',False))
        baseline=str(model_policy.get('baseline') or 'mock-no-api')
        local_model=str(model_policy.get('local_model') or 'optional-opt-in')
        external_api=str(model_policy.get('external_api') or 'approval-provenance-only')
        return [
            f'- Local-first: {"sí" if local_first else "no"}.',
            f'- Cloud obligatorio: {"sí" if cloud_required else "no"}.',
            f'- Escrituras de proyecto por operador externo: {"permitidas" if operator_writes else "no permitidas"}.',
            f'- Baseline de modelos: {baseline}.',
            f'- Modelo local: {local_model}.',
            f'- API externa: {external_api}.',
        ]

    def _proposal_markdown(self, *, stage_id: str, workspace_id: str, project_name: str, business_need: str, document_date: str, constraints: dict[str,Any], model_policy: dict[str,Any], upstream: dict[str,str], semantic_model: dict[str,Any]) -> str:
        doc_id=f"{workspace_id.upper().replace('-', '_')}_{stage_id.upper().replace('-', '_')}"
        title={'product-vision':'Product Vision','scope':'MVP Scope','requirements':'Requirements Specification'}[stage_id]
        front=[
            '---',f'doc_id: "{doc_id}"',f'title: "{title} — {project_name}"','status: "draft"','version: "0.2.0"',
            'owner: "Owner / DevPilot"',f'updated: "{document_date}"','lifecycle_authority: "DevPilot runtime state"','---','',f'# {title}',''
        ]
        active=lambda key:[x for x in semantic_model.get(key) or [] if x.get('status')!='REJECTED']
        actors=active('actors'); outcomes=active('outcomes'); capabilities=active('capabilities')
        open_questions=[x for x in semantic_model.get('open_questions') or [] if x.get('status')!='REJECTED']
        constraint_lines=self._constraint_lines(constraints,model_policy)
        if stage_id=='product-vision':
            actor_text='; '.join(str(x.get('statement') or '') for x in actors)
            outcome_text='; '.join(str(x.get('statement') or '') for x in outcomes)
            body=[
                '## Resumen ejecutivo','',f'**{project_name}** es un producto orientado a {actor_text or 'un actor pendiente de precisión'}. DevPilot deriva este DRAFT desde un Semantic Model interno y gobernado; no fija todavía arquitectura ni stack.','',
                '## Problema','',business_need,'',
                '## Usuario/actor','',*sum(([f'- **{x["id"]}** — {x["statement"]}.',''] for x in actors),[]),
                '## Visión','',f'Permitir que {actor_text or 'el actor principal'} alcance el resultado de negocio identificado: {outcome_text or 'resultado pendiente de precisión'}.','',
                '## Propuesta de valor','',*sum(([f'- **{x["id"]}** — {x["statement"]}.',''] for x in outcomes),[]),
                '## MVP','',*sum(([f'- **{x["id"]}** — {x["statement"]}.',''] for x in capabilities),[]),
                '## Indicadores','',
                '- Las capacidades MVP representadas en este DRAFT pueden revisarse de extremo a extremo por el Owner.','',
                '- Las métricas cuantitativas no se inventan: cualquier umbral no presente en la fuente permanece como decisión gobernada.','',
                '## Local-first','',*constraint_lines,'',
                '## Preguntas abiertas','',
                *([f'- {q["id"]}: {q["statement"]} — decisión: {q.get("decision") or "pendiente no crítica"}.' for q in open_questions] or ['- No quedan preguntas críticas abiertas para este DRAFT.']),'',
                '## Post-MVP','',
                'No se incorporan automáticamente capacidades Post-MVP. Cualquier ampliación requiere una decisión gobernada posterior.','',
            ]
        elif stage_id=='scope':
            body=[
                '## MVP','',*sum(([f'- **{x["id"]}** — In scope: {x["statement"]}.',''] for x in capabilities),[]),
                '## MVP+','',
                '- No se materializan ítems MVP+ por defecto; cualquier ampliación requiere decisión explícita del Owner.','',
                '## Out of scope','',
                '- Capacidades no trazadas a Product Vision FROZEN o al Semantic Model confirmado.','',
                '- Selección de frontend, backend, base de datos o framework antes de Architecture.','',
                '- Cloud obligatorio o API externa obligatoria cuando Project Context no lo autoriza.','',
                '## Criterios','',
                '- Cada ítem In Scope conserva un ID estable y traza a una capability gobernada.','',
                '- El alcance no agrega capacidades no aprobadas y mantiene tecnología diferida hasta Architecture.','',
                '## Restricciones','',*constraint_lines,'',
                '## Dependencies','',
                '- Product Vision debe permanecer FROZEN y con hash aprobado coincidente.','',
                '## Upstream trace','',
                f'- Product Vision FROZEN content SHA-256: {_sha_text(upstream.get("product-vision", ""))}.','',
                '## Open decisions','',
                *([f'- {q["id"]}: {q["statement"]} — decisión: {q.get("decision") or "pendiente"}.' for q in open_questions if q.get('critical')] or ['- No quedan decisiones críticas abiertas para delimitar el MVP.']),'',
                '## Exit criteria','',
                '- Todas las capabilities MVP gobernadas están representadas exactamente una vez y no existe scope drift.','',
            ]
        else:
            records=requirement_records(semantic_model)
            rf=[]
            for rec in records:
                lines=[f'### {rec["id"]}','',f'- **Tipo:** {rec["type"]}.',f'- **Statement:** {rec["statement"]}',f'- **Fuente:** {", ".join(rec["source_capability_ids"])}.']
                if rec.get('owner_decision_context'):
                    lines.append(f'- **Decisión Owner vinculada:** {rec["owner_decision_context"]}')
                lines.extend([f'- **Prioridad:** {rec["priority"]}.',f'- **Criterio de aceptación:** {rec["acceptance_criteria"][0]}',f'- **Método de verificación:** {rec["verification_method"]}.',''])
                rf.extend(lines)
            body=[
                '## Propósito','',f'Definir requisitos verificables del MVP de {project_name}, derivados del Semantic Model gobernado, Scope FROZEN y Product Vision FROZEN.','',
                '## Alcance','',*[f'- {x["id"]}: {x["statement"]}.' for x in capabilities],'',
                '## Requerimientos funcionales del MVP','',*rf,
                '## Requerimientos no funcionales','',
                '- No se fabrican NFR cuantitativos. Los atributos de calidad que requieran métricas se decidirán de forma gobernada antes de convertirse en NFR verificables.','',
                '## Decisiones pendientes','',
                *([f'- {q["id"]}: {q["statement"]} — pendiente antes de approval.' for q in unresolved_decisions_for_stage(semantic_model,'requirements')] or ['- No quedan decisiones críticas pendientes para Requirements.']),'',
                '## Restricciones heredadas','',*constraint_lines,'',
                '## Trazabilidad','',*[f'- {rec["id"]} ← {", ".join(rec["source_capability_ids"])}.' for rec in records],'',
                '## Upstream trace','',
                f'- Product Vision FROZEN content SHA-256: {_sha_text(upstream.get("product-vision", ""))}.',
                f'- MVP Scope FROZEN content SHA-256: {_sha_text(upstream.get("scope", ""))}.','',
                '## Criterios de bloqueo','',
                '- BLOCK si un RF no describe comportamiento observable.','',
                '- BLOCK si falta fuente, prioridad, criterio de aceptación o método de verificación.','',
                '- BLOCK si una decisión crítica permanece abierta o si se introduce arquitectura antes de C-02.','',
            ]
        return '\n'.join(front+body).rstrip()+'\n'

    @staticmethod
    def _project_document_date(workspace_root: Path) -> str:
        manifest=workspace_root/'.devpilot/bootstrap-execution.json'
        if manifest.is_file():
            try:
                payload=json.loads(manifest.read_text(encoding='utf-8'))
                value=str(payload.get('completed_at') or '').strip()
                if re.fullmatch(r'\d{4}-\d{2}-\d{2}.*',value):return value[:10]
            except Exception:
                pass
        try:
            cp=subprocess.run(['git','-C',str(workspace_root),'log','--reverse','-1','--format=%cs'],capture_output=True,text=True,timeout=5,check=False)
            value=cp.stdout.strip()
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):return value
        except Exception:
            pass
        return '1970-01-01'

    def _reconcile_governed_parents(self, *, workspace_id: str, workspace_root: Path) -> CommandResult:
        command='guided pre-code reconcile structure'
        root=workspace_root.resolve()
        guard=PathGuard(root)
        planned:list[tuple[Path,Path]]=[]
        for rel in REQUIRED_DOCUMENT_PARENTS:
            candidate=root/rel
            decision=guard.evaluate(rel,action='create')
            if not decision.ok:
                return self._block(command,'GSDLC13C01_STRUCTURE_PATH_BLOCK','PathGuard rejected a governed document namespace.',metadata={'relative_path':rel.as_posix(),'policy':decision.to_dict()})
            cursor=root
            for part in rel.parts:
                cursor=cursor/part
                if cursor.exists() and cursor.is_symlink():
                    return self._block(command,'GSDLC13C01_STRUCTURE_SYMLINK_BLOCK','Governed document namespace contains a symlink boundary.',metadata={'relative_path':rel.as_posix(),'symlink':str(cursor)})
            if candidate.exists() and not candidate.is_dir():
                return self._block(command,'GSDLC13C01_STRUCTURE_COLLISION_BLOCK','Governed document namespace collides with a non-directory path.',metadata={'relative_path':rel.as_posix()})
            planned.append((rel,candidate))
        before=self._git_status(root)
        if before is None:
            return self._block(command,'GSDLC13C01_STRUCTURE_GIT_STATUS_BLOCK','Git status could not be verified before structural reconciliation.')
        created:list[Path]=[]
        try:
            for rel,candidate in planned:
                if not candidate.exists():
                    candidate.mkdir(parents=True,exist_ok=False)
                    created.append(candidate)
            after=self._git_status(root)
            if after is None or after!=before:
                for candidate in reversed(created):
                    try:candidate.rmdir()
                    except OSError:pass
                return self._block(command,'GSDLC13C01_STRUCTURE_GIT_DRIFT_BLOCK','Structural reconciliation changed Git-observable project content and was rolled back.',metadata={'git_before_clean':before==b'','git_after_clean':after==b'' if after is not None else None})
        except Exception as exc:
            for candidate in reversed(created):
                try:candidate.rmdir()
                except OSError:pass
            return self._block(command,'GSDLC13C01_STRUCTURE_RECONCILIATION_BLOCK','Governed document namespace reconciliation failed closed.',metadata={'error':str(exc)})
        receipt={
            'schema_id':'devpilot.gsdlc13c01.structure_reconciliation.v1','workspace_id':workspace_id,
            'required_directories':[x.as_posix() for x in REQUIRED_DOCUMENT_PARENTS],
            'directories_created':[x.relative_to(root).as_posix() for x in created],
            'operator_project_writes':0,'project_content_files_written':0,
            'git_before_clean':before==b'','git_after_clean':after==b'','git_status_unchanged':True,
            'network_used':False,'external_api_used':False,'status':'PASS','completed_at':_now(),
        }
        receipt_path=self.root/STRUCTURE_RECEIPT_ROOT/re.sub(r'[^A-Za-z0-9_.-]','_',workspace_id)/'structure_reconciliation.json'
        receipt_path.parent.mkdir(parents=True,exist_ok=True)
        tmp=receipt_path.with_suffix('.tmp'); tmp.write_text(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8'); os.replace(tmp,receipt_path)
        receipt['receipt_path']=str(receipt_path.relative_to(self.root)).replace('\\','/')
        return self._pass(command,'GSDLC13C01_STRUCTURE_RECONCILIATION_PASS','Governed document namespaces are available; no project content file or Git-visible mutation was introduced.',{'structure_reconciliation':receipt})

    @staticmethod
    def _git_status(workspace_root: Path) -> bytes | None:
        try:
            cp=subprocess.run(['git','-C',str(workspace_root),'status','--porcelain=v1','-z'],capture_output=True,timeout=5,check=False)
            return cp.stdout if cp.returncode==0 else None
        except Exception:
            return None

    @staticmethod
    def _identity(actor:str,actor_role:str,principal:str,effective_roles:list[str])->CommandResult|None:
        if not actor.strip() or actor.strip()!=principal.strip():return PreCodeWizardApplicationService._block('guided pre-code','GSDLC05E_SESSION_ACTOR_BINDING_BLOCK','Authenticated actor/session binding is required.')
        if actor_role not in effective_roles:return PreCodeWizardApplicationService._block('guided pre-code','GSDLC05E_ROLE_BINDING_BLOCK','Actor role must come from authenticated canonical roles.')
        if actor_role != 'owner':return PreCodeWizardApplicationService._block('guided pre-code','GSDLC05E_AUTHOR_ROLE_BLOCK','Current role cannot author/approve this pre-code stage.',metadata={'role':actor_role})
        return None
    @staticmethod
    def _base_commit(workspace_root:Path)->str:
        import subprocess
        try:
            cp=subprocess.run(['git','-C',str(workspace_root),'rev-parse','HEAD'],capture_output=True,text=True,timeout=5,check=False); v=cp.stdout.strip(); return v if re.fullmatch(r'[0-9a-f]{40}',v) else '0'*40
        except Exception:return '0'*40
    @staticmethod
    def _pass(command:str,fid:str,message:str,data:dict[str,Any])->CommandResult:return CommandResult(command,True,ExitCode.PASS,message,data=data,findings=[Finding(fid,message,Severity.INFO)])
    @staticmethod
    def _block(command:str,fid:str,message:str,metadata:dict[str,Any]|None=None)->CommandResult:return CommandResult(command,False,ExitCode.BLOCK,message,data={},findings=[Finding(fid,message,Severity.BLOCK,metadata=metadata or {})])
