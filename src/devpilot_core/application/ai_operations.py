from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.approval.service import ApprovalService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.providers import ModelProviderKind, ProviderRegistry

from .governed_job_capability_registry import GovernedJobCapabilityRegistry
from .governed_job_operations import GovernedJobOperationalMetadataStore
from .governed_jobs import GovernedJobFramework

AI_PROFILE_PATH = Path('.devpilot/ai/ui_ai_operation_profiles.json')
AI_RUNTIME_ROOT = Path('outputs/runtime/uoc010_ai')
AI_EVIDENCE_ROOT = Path('outputs/evidence_packages/uoc010_ai')
RUNTIME_RAG_INDEX = AI_RUNTIME_ROOT / 'rag/docs_index.json'
CANONICAL_RAG_INDEX = Path('.devpilot/rag/docs_index.json')
MEMORY_DIR = Path('.devpilot/agents/memory')

TARGETS = {
    'docs': 'docs',
    'requirements': 'docs/01_requirements',
    'architecture': 'docs/02_architecture',
    'security': 'docs/03_security',
    'src': 'src',
}
TASKS = {
    'summarize-gaps': 'Summarize the most important gaps in the selected target using only local project context.',
    'review-context': 'Review the selected target and report bounded, evidence-aware observations.',
    'identify-risks': 'Identify material risks in the selected target without proposing destructive actions.',
}


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


@dataclass(frozen=True)
class AiOperationProfile:
    operation_id: str
    label: str
    capability_id: str
    kind: str
    risk_class: str
    requires_approval: bool
    supports_cancel: bool
    timeout_seconds: int
    allowed_keys: tuple[str, ...]


class AiOperationProfileRegistry:
    def __init__(self, root: Path, path: Path = AI_PROFILE_PATH) -> None:
        self.root = Path(root).resolve(); self.path = self.root / path
        self._payload: dict[str, Any] | None = None; self._profiles: dict[str, AiOperationProfile] | None = None

    def _load(self) -> None:
        if self._payload is not None: return
        payload = json.loads(self.path.read_text(encoding='utf-8'))
        self._payload = payload
        self._profiles = {str(x['operation_id']): AiOperationProfile(
            operation_id=str(x['operation_id']), label=str(x['label']), capability_id=str(x['capability_id']), kind=str(x['kind']),
            risk_class=str(x['risk_class']), requires_approval=bool(x['requires_approval']), supports_cancel=bool(x['supports_cancel']),
            timeout_seconds=int(x['timeout_seconds']), allowed_keys=tuple(str(k) for k in x.get('allowed_keys', [])),
        ) for x in payload.get('operations', [])}

    @property
    def payload(self) -> dict[str, Any]: self._load(); assert self._payload is not None; return self._payload
    def list(self) -> list[dict[str, Any]]: return [dict(x) for x in self.payload.get('operations', [])]
    def require(self, operation_id: str) -> AiOperationProfile:
        self._load(); assert self._profiles is not None
        if operation_id not in self._profiles: raise ValueError(f'Unknown UOC-010 AI operation: {operation_id}')
        return self._profiles[operation_id]


class AiRuntimeStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve(); self.runtime = self.root / AI_RUNTIME_ROOT; self.plans = self.runtime / 'plans'; self.results = self.runtime / 'results'
    def save_plan(self, job_id: str, payload: dict[str, Any]) -> Path: path=self.plans/f'{job_id}.json'; _atomic_json(path,payload); return path
    def load_plan(self, job_id: str) -> dict[str, Any]: return json.loads((self.plans/f'{job_id}.json').read_text(encoding='utf-8'))
    def save_result(self, job_id: str, payload: dict[str, Any]) -> Path: path=self.results/f'{job_id}.json'; _atomic_json(path,payload); return path
    def result(self, job_id: str) -> dict[str, Any] | None:
        path=self.results/f'{job_id}.json'; return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None
    def list_results(self) -> list[Path]: return sorted(self.results.glob('job_*.json')) if self.results.exists() else []


class AiOperationsApplicationService:
    """UOC-010 typed local-first RAG/agent/tool/handoff application boundary."""
    def __init__(self, root: Path) -> None:
        self.root=Path(root).resolve(); self.profiles=AiOperationProfileRegistry(self.root); self.capabilities=GovernedJobCapabilityRegistry(self.root)
        self.jobs=GovernedJobFramework(self.root, registry=self.capabilities); self.runtime=AiRuntimeStore(self.root); self.meta=GovernedJobOperationalMetadataStore(self.root); self.approvals=ApprovalService(self.root)

    def catalog(self) -> CommandResult:
        p=self.profiles.payload; ops=self.profiles.list()
        return self._pass('ai operations catalog','UOC-010 AI operation catalog loaded.',{'operations':ops,'selectors':p.get('selectors',{}),'budgets':p.get('budgets',{}),'safety':p.get('safety',{}),'summary':{'operations_total':len(ops),'arbitrary_shell':False,'external_api_enabled':False,'generic_tool_execution':False}})

    def status(self) -> CommandResult:
        providers=ProviderRegistry.load(self.root).to_result(); pdata=providers.data or {}; provider_items=[]
        for item in pdata.get('providers',[]):
            provider_items.append({k:item.get(k) for k in ('provider_id','kind','enabled','default_model','external_api','requires_api_key','endpoint','estimated_cost_per_1k_tokens_usd','status')})
        rag_index=self.root/CANONICAL_RAG_INDEX; rag_meta={}
        if rag_index.is_file():
            try:
                raw=json.loads(rag_index.read_text(encoding='utf-8')); rag_meta={'index_id':raw.get('index_id'),'generated_at_utc':raw.get('generated_at_utc'),'summary':raw.get('summary',{}),'path':str(CANONICAL_RAG_INDEX).replace('\\','/')}
            except Exception: rag_meta={'path':str(CANONICAL_RAG_INDEX),'load_error':True}
        tool_policy=json.loads((self.root/'.devpilot/agents/tool_call_policy.json').read_text(encoding='utf-8'))
        memory_policy=json.loads((self.root/'.devpilot/agents/agent_memory_policy.json').read_text(encoding='utf-8'))
        handoff_policy=json.loads((self.root/'.devpilot/agents/multiagent_handoff_policy.json').read_text(encoding='utf-8'))
        return self._pass('ai status','UOC-010 local AI governance status loaded.',{
            'providers':provider_items,'provider_summary':pdata.get('summary',{}),'rag':{'canonical_index':rag_meta,'runtime_index_exists':(self.root/RUNTIME_RAG_INDEX).is_file()},
            'tool_contract':{'dry_run_first':tool_policy.get('defaults',{}).get('dry_run_first',True),'contract_only':tool_policy.get('defaults',{}).get('contract_only',True),'real_tool_execution_enabled':tool_policy.get('defaults',{}).get('real_tool_execution_enabled',False)},
            'memory':{'memory_enabled_by_default':memory_policy.get('defaults',{}).get('memory_enabled_by_default',False),'semantic_memory_enabled':memory_policy.get('defaults',{}).get('semantic_memory_enabled',False),'retention_days':memory_policy.get('defaults',{}).get('retention_days',14),'counts_as_formal_evidence':False},
            'handoff':{'supervisor_required':handoff_policy.get('defaults',{}).get('supervisor_required',True),'policy_id':handoff_policy.get('policy_id')},
            'summary':{'mock_mandatory':True,'external_api_enabled':False,'external_api_required':False,'local_provider_opt_in':True,'memory_enabled_by_default':False,'memory_counts_as_formal_evidence':False,'generic_tool_execution':False,'supervisor_required':True,'network_used':False}
        })

    def plan_job(self, *, operation_id: str, workspace_id: str, parameters: dict[str, Any] | None, idempotency_key: str, approval_id: str | None=None) -> CommandResult:
        try: profile=self.profiles.require(operation_id)
        except ValueError as exc: return self._block('ai job plan',str(exc),'UOC010_OPERATION_BLOCK')
        params=dict(parameters or {})
        if set(params)-set(profile.allowed_keys): return self._block('ai job plan','Parameters contain keys outside the typed profile.','UOC010_PARAMETERS_BLOCK')
        normalized=self._normalize_parameters(profile,params)
        if isinstance(normalized,CommandResult): return normalized
        if profile.requires_approval:
            if not approval_id: return self._block('ai job plan','This AI operation requires an approved Approval Center record.','UOC010_APPROVAL_REQUIRED_BLOCK')
            check=self._approval_check(approval_id,profile)
            if not check.ok: return check
        try:
            handle=self.jobs.plan(capability_id=profile.capability_id,workspace_id=workspace_id or 'devpilot-local',parameters=normalized,idempotency_key=idempotency_key,dry_run=True,timeout_seconds=profile.timeout_seconds,retry_limit=0,approval_binding_id=approval_id)
        except Exception as exc: return self._block('ai job plan',f'{type(exc).__name__}: {exc}','UOC010_JOB_PLAN_BLOCK')
        plan={'schema_id':'SCHEMA-DEVPL-UOC010-AI-JOB-PLAN-V1','job_id':handle.record['job_id'],'operation_id':operation_id,'capability_id':profile.capability_id,'parameters':normalized,'approval_id':approval_id,'workspace_id':workspace_id or 'devpilot-local','timeout_seconds':profile.timeout_seconds,'idempotent_replay':handle.idempotent_replay,'governance':{'provider_visibility':True,'external_api_allowed':False,'tool_mode':'contract-only','memory_formal_evidence':False}}
        path=self.runtime.save_plan(handle.record['job_id'],plan)
        return self._pass('ai job plan','Governed AI job planned.',{'job':self._public_job(handle.record),'plan':plan,'plan_ref':str(path.relative_to(self.root)).replace('\\','/'),'summary':{'requires_approval':profile.requires_approval,'supports_cancel':profile.supports_cancel,'external_api_allowed':False}})

    def execute_job(self, *, job_id: str) -> CommandResult:
        try:
            record=self.jobs.store.load(job_id); plan=self.runtime.load_plan(job_id); profile=self.profiles.require(str(plan['operation_id']))
            if profile.requires_approval:
                check=self._approval_check(str(plan.get('approval_id') or ''),profile)
                if not check.ok: return check
            if record['status']=='pending-approval': return self._block('ai job execute','Job is pending approval.','UOC010_JOB_PENDING_APPROVAL_BLOCK')
            if record['status'] in {'planned','approved'}: self.jobs.queue(job_id)
            elif record['status']!='queued': return self._block('ai job execute',f'Job cannot execute from state {record["status"]}.','UOC010_JOB_STATE_BLOCK')
            cmd=[sys.executable,'-m','devpilot_core.application.ai_job_worker','--repo-root',str(self.root),'--job-id',job_id]
            proc=subprocess.Popen(cmd,cwd=str(self.root),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,shell=False,close_fds=(os.name!='nt'))
            meta=self.meta.load(job_id); meta.update({'phase':'worker-starting','progress_percent':1,'worker_pid':proc.pid,'worker_started_at':record.get('updated_at'),'reconciled_orphan':False}); self.meta.save(meta)
            return self._pass('ai job execute','Typed UOC-010 local worker started.',{'job':self._public_job(self.jobs.store.load(job_id)),'worker':{'pid':proc.pid,'argv_contract':'fixed-uoc010-worker','shell':False},'summary':{'started':True,'operation_id':profile.operation_id}})
        except Exception as exc: return self._block('ai job execute',f'{type(exc).__name__}: {exc}','UOC010_JOB_EXECUTE_BLOCK')

    def result(self, *, job_id: str) -> CommandResult:
        try: job=self.jobs.store.load(job_id)
        except Exception: return self._block('ai job result','Unknown governed job id.','UOC010_JOB_NOT_FOUND_BLOCK')
        payload=self.runtime.result(job_id)
        return self._pass('ai job result','AI job result projection loaded.',{'job':self._public_job(job),'result':payload,'summary':{'result_available':payload is not None}})

    def package_evidence(self, *, limit: int=100) -> CommandResult:
        limit=max(1,min(int(limit),250)); out=self.root/AI_EVIDENCE_ROOT; out.mkdir(parents=True,exist_ok=True); archive=out/f'ai_evidence_{uuid.uuid4().hex[:12]}.zip'; entries=[]; candidates=[]
        for p in self.runtime.list_results()[-limit:]: candidates.append((p,f'results/{p.name}'))
        for rel in ['.devpilot/project_state.json','docs/post_h_eval_002_uoc_009_manifest.json','docs/post_h_eval_002_uoc_010_manifest.json','.devpilot/ai/ui_ai_operation_profiles.json']:
            p=self.root/rel
            if p.is_file(): candidates.append((p,f'contracts/{Path(rel).name}'))
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as zf:
            for source,arc in candidates:
                data=source.read_bytes(); zf.writestr(arc,data); entries.append({'path':arc,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
            manifest={'schema_id':'devpilot.uoc010.ai_evidence_package.v1','entries':entries,'summary':{'entries_total':len(entries),'source_mutations':False,'network_used':False,'external_api_used':False,'memory_counts_as_formal_evidence':False}}
            zf.writestr('ai_evidence_manifest.json',json.dumps(manifest,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
        return self._pass('ai evidence package','Bounded local AI evidence package created.',{'archive_ref':str(archive.relative_to(self.root)).replace('\\','/'),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'summary':{'entries_total':len(entries),'network_used':False,'external_api_used':False}})

    def record_progress(self, **kwargs: Any) -> CommandResult:
        from .governed_job_operations import GovernedJobOperationsApplicationService
        return GovernedJobOperationsApplicationService(self.root).record_progress(**kwargs)

    def _normalize_parameters(self, profile: AiOperationProfile, params: dict[str,Any]) -> dict[str,Any] | CommandResult:
        selectors=self.profiles.payload.get('selectors',{}); budgets=self.profiles.payload.get('budgets',{})
        if profile.operation_id=='rag-index':
            target=str(params.get('target_id','docs'))
            if target not in selectors.get('rag_targets',[]): return self._block('ai job plan','RAG target id is not allowlisted.','UOC010_RAG_TARGET_BLOCK')
            return {'target_id':target}
        if profile.operation_id=='rag-query':
            query=str(params.get('query','')).strip()
            if not query or len(query)>1000: return self._block('ai job plan','RAG query requires 1..1000 characters.','UOC010_RAG_QUERY_BLOCK')
            source=str(params.get('index_source','canonical')); top=max(1,min(int(params.get('top_k',5)),int(budgets.get('max_query_top_k',10))))
            if source not in selectors.get('rag_index_sources',[]): return self._block('ai job plan','RAG index source is not registered.','UOC010_RAG_SOURCE_BLOCK')
            return {'query':query,'top_k':top,'index_source':source}
        if profile.operation_id=='agent-run':
            agent=str(params.get('agent_id','requirements.agent')); task=str(params.get('task_id','summarize-gaps')); target=str(params.get('target_id','requirements')); provider=str(params.get('provider_id','mock')).lower(); memory=bool(params.get('memory_opt_in',False))
            if agent not in selectors.get('agents',[]) or task not in selectors.get('agent_tasks',[]) or target not in selectors.get('agent_targets',[]): return self._block('ai job plan','Agent/task/target selection is not allowlisted.','UOC010_AGENT_SELECTOR_BLOCK')
            registry=ProviderRegistry.load(self.root); cfg=registry.get(provider)
            if cfg is None: return self._block('ai job plan','Model provider is not registered.','UOC010_PROVIDER_UNKNOWN_BLOCK')
            if cfg.external_api or cfg.kind==ModelProviderKind.API: return self._block('ai job plan','External API providers are disabled for UOC-010.','UOC010_EXTERNAL_PROVIDER_BLOCK')
            if provider!='mock' and (cfg.kind!=ModelProviderKind.LOCAL or not cfg.enabled): return self._block('ai job plan','Local provider must be explicitly enabled and remain localhost-only.','UOC010_LOCAL_PROVIDER_OPT_IN_BLOCK')
            return {'agent_id':agent,'task_id':task,'target_id':target,'provider_id':provider,'memory_opt_in':memory,'max_turns':1,'max_cost_usd':0.0}
        if profile.operation_id=='handoff-run':
            workflow=str(params.get('workflow_id','repo-review')); target=str(params.get('target_id','src')); steps=max(1,min(int(params.get('max_steps',2)),int(budgets.get('max_handoff_steps',3))))
            if workflow not in selectors.get('workflows',[]) or target not in selectors.get('handoff_targets',[]): return self._block('ai job plan','Handoff workflow/target is not allowlisted.','UOC010_HANDOFF_SELECTOR_BLOCK')
            return {'workflow_id':workflow,'target_id':target,'max_steps':steps,'dry_run':True,'supervisor':'multiagent.coordinator'}
        return self._block('ai job plan','Unsupported AI operation.','UOC010_OPERATION_BLOCK')

    def _approval_check(self, approval_id: str, profile: AiOperationProfile) -> CommandResult:
        result=self.approvals.show(approval_id)
        if not result.ok: return self._block('ai approval check','Approval record was not found.','UOC010_APPROVAL_NOT_FOUND_BLOCK')
        a=result.data.get('approval',{}) if isinstance(result.data,dict) else {}; expected=profile.capability_id.removeprefix('cli.')
        if a.get('status')!='approved' or a.get('tool_id')!=expected or a.get('action')!='execute' or a.get('subject')!=profile.operation_id or a.get('expired'):
            return self._block('ai approval check','Approval is not an active exact binding for this AI operation.','UOC010_APPROVAL_BINDING_BLOCK')
        return self._pass('ai approval check','Approval binding verified.',{'approval_id':approval_id,'summary':{'approved':True}})

    def _public_job(self, record: dict[str,Any]) -> dict[str,Any]:
        hidden={'cancel_token_hash','idempotency_key_hash','request_fingerprint'}; return {k:v for k,v in record.items() if k not in hidden}
    def _pass(self, command: str, message: str, data: dict[str,Any]) -> CommandResult: return CommandResult(command=command,ok=True,exit_code=ExitCode.PASS,message=message,data=data,findings=[])
    def _block(self, command: str, message: str, finding_id: str) -> CommandResult: return CommandResult(command=command,ok=False,exit_code=ExitCode.BLOCK,message=message,data={'summary':{'blocked':True}},findings=[Finding(finding_id,message,Severity.BLOCK)])
