from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.guided_sdlc.step_action_advisor import AdvisorContext, ExecutionModeAdvisor
from devpilot_core.miasi.applicability import MIASIApplicabilityEvaluator
from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry
from devpilot_core.validators.artifact import extract_headings, normalize_heading
from devpilot_core.validators.frontmatter import parse_frontmatter_text, validate_frontmatter_document

from .artifact_lifecycle_service import ArtifactLifecycleService, ArtifactState
from .artifact_review_service import ArtifactReviewApplicationService
from .workspace_documents_service import WorkspaceDocumentsApplicationService
from .workspace_edit_plan_service import ZERO_SHA256
from .workspace_edit_execution_service import WorkspaceEditExecutionApplicationService

CATALOG = Path('.devpilot/gsdlc/pre_code_wizard_catalog.json')
STORE_ROOT = Path('outputs/pre_code_wizard/gsdlc_05_e')
_SHA = re.compile(r'^[0-9a-f]{64}$')


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PreCodeWizardApplicationService:
    """Server-authoritative GSDLC-05-E manual/import pre-code vertical slice.

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

    def save_draft(self, *, stage_id: str, content: str, mode: str, actor: str, actor_role: str, session_principal: str, effective_roles: list[str], workspace_scopes: list[str]) -> CommandResult:
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
        if normalized_mode not in {'MANUAL','IMPORT'}:
            return self._block(command,'GSDLC05E_MODE_BLOCK','Only MANUAL/IMPORT are available in GSDLC-05-E.')
        content=str(content or '')
        if not content.strip():return self._block(command,'GSDLC05E_EMPTY_DRAFT_BLOCK','Draft content is required.')
        state=self._load_state(workspace_id)
        current=self._current_stage(state)
        if current is None:
            return self._block(command,'GSDLC05E_ALREADY_READY_BLOCK','Pre-code wizard is already complete.')
        if current['stage_id'] != stage_id:
            return self._block(command,'GSDLC05E_STAGE_SKIP_BLOCK','Mandatory pre-code stages cannot be skipped.',metadata={'requested_stage':stage_id,'current_stage':current['stage_id']})
        target=(workspace_root/str(stage['relative_path'])).resolve()
        try: target.relative_to(workspace_root.resolve())
        except ValueError:return self._block(command,'GSDLC05E_TARGET_SCOPE_BLOCK','Pre-code artifact escaped the active workspace.')
        if not target.parent.is_dir() or target.parent.is_symlink():
            return self._block(command,'GSDLC05E_TARGET_PARENT_BLOCK','The project bootstrap must provide the governed document parent directory before authoring.',metadata={'relative_path':stage['relative_path']})
        base_sha=_sha_bytes(target.read_bytes()) if target.is_file() else ZERO_SHA256
        artifact_id='precode_'+hashlib.sha256(f"{workspace_id}|{stage_id}|{_sha_bytes(content.encode())}".encode()).hexdigest()[:24]
        draft=self.lifecycle.create_draft(
            artifact_id=artifact_id,relative_path=str(stage['relative_path']),content=content,source_type=normalized_mode,
            base_commit=self._base_commit(workspace_root),actor=actor,actor_role=actor_role,session_principal=session_principal,
            reviewer=actor,reviewer_role=actor_role,source_label=f'GSDLC-05-E {normalized_mode} browser DRAFT',
            source_reference=f'pre-code:{workspace_id}:{stage_id}:{normalized_mode.lower()}',
        )
        if not draft.ok:return draft
        row=self._stage_state(state,stage_id)
        row.update({'status':'DRAFT','mode':normalized_mode,'content':content,'content_sha256':_sha_bytes(content.encode()),'base_sha256':base_sha,'artifact':draft.data['artifact'],'review_id':None,'plan_id':None,'plan_hash':None,'diff':None,'execution_id':None,'approval_id':None,'approved_sha256':None,'updated_at':_now()})
        state['status']='IN_PROGRESS'; state['updated_at']=_now(); self._write_state(workspace_id,state)
        return self._pass(command,'GSDLC05E_DRAFT_SAVED_PASS','Server-authoritative DRAFT persisted outside managed source; source mutation remains false.',{'stage':self._public_stage(row,stage),'source_mutations_performed':False})

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
        return {'schema_id':'devpilot.gsdlc05e.pre_code_projection.v1','profile_id':self.catalog['profile_id'],'readiness_semantics':self.catalog.get('readiness_semantics'),'workspace_id':workspace_id,'status':state.get('status','NOT_STARTED'),'current_stage_id':current['stage_id'] if current else None,'current_stage_order':current['order'] if current else None,'stages':[self._public_stage(self._stage_state(state,x['stage_id']),x) for x in self._stages],'advisor':advisor_payload,'miasi':miasi,'readiness':readiness,'transition_trace_ref':f'outputs/pre_code_wizard/gsdlc_05_e/{workspace_id}/transition_trace.jsonl','server_authoritative':True,'normal_user_powershell_required':0,'external_operator_project_writes':0,'network_used':False,'external_api_used':False,'model_execution_used':False,'agent_execution_used':False,'rag_execution_used':False}

    def _readiness_payload(self,state:dict[str,Any],workspace_id:str,workspace_root:Path,*,miasi:dict[str,Any]|None=None)->dict[str,Any]:
        blockers=[]; artifacts=[]
        miasi=miasi or self._miasi_payload(workspace_id)
        if str(miasi.get('gate_status') or 'BLOCK').upper()!='PASS':
            blockers.append({'stage_id':'miasi-applicability','status':str(miasi.get('status') or 'REVIEW_REQUIRED'),'reason':'MIASI gate must PASS before Guided Pre-code readiness can PASS','reason_codes':list(miasi.get('reason_codes') or [])})
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
        try:
            return self.miasi.evaluate_workspace(workspace_id, {'artifacts': []}).to_payload()
        except Exception:
            # Fail closed without surfacing parser/filesystem internals to the browser.
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
        return {'schema_id':'devpilot.gsdlc05e.pre_code_state.v1','workspace_id':workspace_id,'profile_id':self.catalog['profile_id'],'status':'NOT_STARTED','stages':{x['stage_id']:{'stage_id':x['stage_id'],'status':'MISSING','mode':None,'content_sha256':None,'base_sha256':None,'artifact':None,'review_id':None,'plan_id':None,'plan_hash':None,'diff':None,'execution_id':None,'approval_id':None,'approved_sha256':None,'findings':[],'validation':{},'updated_at':None} for x in self._stages},'created_at':_now(),'updated_at':_now(),'completed_at':None}

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
        return {'stage_id':stage['stage_id'],'order':stage['order'],'label':stage['label'],'relative_path':stage['relative_path'],'profile_id':stage['profile_id'],'advisor_step':stage['advisor_step'],'allowed_modes':list(stage['allowed_modes']),'status':row.get('status'),'mode':row.get('mode'),'content_sha256':row.get('content_sha256'),'review_id':row.get('review_id'),'plan_id':row.get('plan_id'),'plan_hash':row.get('plan_hash'),'diff':row.get('diff'),'execution_id':row.get('execution_id'),'approval_id':row.get('approval_id'),'approved_sha256':row.get('approved_sha256'),'findings':list(row.get('findings') or []),'validation':dict(row.get('validation') or {})}
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
