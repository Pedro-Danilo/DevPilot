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
from pathlib import Path
from typing import Any

from devpilot_core.approval.service import ApprovalService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.testing import TestImpactAnalyzerV2, TestImpactV2Options

from .governed_job_capability_registry import GovernedJobCapabilityRegistry
from .governed_jobs import GovernedJobFramework, GovernedJobPolicyBlock, GovernedJobStore
from .governed_job_operations import GovernedJobOperationalMetadataStore

QUALITY_PROFILE_PATH = Path('.devpilot/quality/ui_quality_operation_profiles.json')
QUALITY_RUNTIME_ROOT = Path('outputs/runtime/uoc009_quality')
FULL_REGRESSION_CONFIRMATION = 'RUN FULL REGRESSION'
QUALITY_GATE_PROFILES = ('fast','full','ci','release','industrial','hardening')


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
class QualityOperationProfile:
    operation_id: str
    label: str
    capability_id: str
    kind: str
    risk_class: str
    requires_approval: bool
    supports_cancel: bool
    timeout_seconds: int
    allowed_keys: tuple[str, ...]


class QualityOperationProfileRegistry:
    def __init__(self, root: Path, path: Path = QUALITY_PROFILE_PATH) -> None:
        self.root = Path(root).resolve(); self.path = self.root / path
        self._payload: dict[str, Any] | None = None
        self._profiles: dict[str, QualityOperationProfile] | None = None

    def _load(self) -> None:
        if self._payload is not None and self._profiles is not None:
            return
        payload = json.loads(self.path.read_text(encoding='utf-8'))
        self._payload = payload
        self._profiles = {str(x['operation_id']): QualityOperationProfile(
            operation_id=str(x['operation_id']), label=str(x['label']), capability_id=str(x['capability_id']),
            kind=str(x['kind']), risk_class=str(x['risk_class']), requires_approval=bool(x['requires_approval']),
            supports_cancel=bool(x['supports_cancel']), timeout_seconds=int(x['timeout_seconds']),
            allowed_keys=tuple(str(k) for k in x.get('allowed_keys', [])),
        ) for x in payload.get('operations', [])}

    @property
    def payload(self) -> dict[str, Any]:
        self._load()
        assert self._payload is not None
        return self._payload

    def require(self, operation_id: str) -> QualityOperationProfile:
        self._load()
        assert self._profiles is not None
        try: return self._profiles[operation_id]
        except KeyError as exc: raise ValueError(f'Unknown UOC-009 quality operation: {operation_id}') from exc

    def list(self) -> list[dict[str, Any]]:
        return [dict(x) for x in self.payload.get('operations', [])]


class QualityRuntimeStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve(); self.runtime = self.root / QUALITY_RUNTIME_ROOT
        self.plans = self.runtime / 'plans'; self.results = self.runtime / 'results'

    def save_plan(self, job_id: str, payload: dict[str, Any]) -> Path:
        path=self.plans/f'{job_id}.json'; _atomic_json(path,payload); return path
    def load_plan(self, job_id: str) -> dict[str, Any]:
        return json.loads((self.plans/f'{job_id}.json').read_text(encoding='utf-8'))
    def save_result(self, job_id: str, payload: dict[str, Any]) -> Path:
        path=self.results/f'{job_id}.json'; _atomic_json(path,payload); return path
    def list_results(self) -> list[Path]:
        return sorted(self.results.glob('job_*.json')) if self.results.exists() else []


class QualityOperationsApplicationService:
    """UOC-009 typed quality/test/release boundary.

    The browser selects operation/profile identifiers only. It never provides
    shell text, pytest paths, arbitrary CLI arguments or executable names.
    """
    def __init__(self, root: Path) -> None:
        self.root=Path(root).resolve(); self.profiles=QualityOperationProfileRegistry(self.root)
        self.capabilities=GovernedJobCapabilityRegistry(self.root); self.jobs=GovernedJobFramework(self.root, registry=self.capabilities)
        self.runtime=QualityRuntimeStore(self.root); self.meta=GovernedJobOperationalMetadataStore(self.root); self.approvals=ApprovalService(self.root)

    def catalog(self) -> CommandResult:
        ops=self.profiles.list(); return self._pass('quality operations catalog','UOC-009 quality operation catalog loaded.',{'operations':ops,'summary':{'operations_total':len(ops),'runtime_enabled_total':len({x['capability_id'] for x in ops if self.capabilities.require(x['capability_id']).execution_enabled}),'arbitrary_shell':False,'free_pytest_args':False,'full_regression_requires_explicit_confirmation':True}})

    def baseline(self) -> CommandResult:
        ps=json.loads((self.root/'.devpilot/project_state.json').read_text(encoding='utf-8'))
        manifests=[]
        for p in sorted((self.root/'docs').glob('post_h_eval_002_uoc_*_manifest.json'))[-6:]:
            try:
                d=json.loads(p.read_text(encoding='utf-8')); manifests.append({'path':str(p.relative_to(self.root)).replace('\\','/'),'sprint':d.get('sprint') or d.get('sprint_id'),'status':d.get('status'),'output_repo':d.get('output_repo')})
            except Exception: continue
        tcr_profiles=sorted(self._tcr_profile_ids())
        return self._pass('quality baseline inspect','Quality baseline metadata loaded.',{'project_state':{'current_repo':ps.get('current_repo'),'last_registered_sprint':ps.get('last_registered_sprint'),'current_micro_sprint':ps.get('current_micro_sprint'),'next_micro_sprint':ps.get('next_micro_sprint')},'manifests':manifests,'selectors':{'tcr_profiles':tcr_profiles,'quality_gate_profiles':list(QUALITY_GATE_PROFILES),'full_regression_confirmation':FULL_REGRESSION_CONFIRMATION},'summary':{'read_only':True,'manifests_total':len(manifests),'tcr_profiles_total':len(tcr_profiles)}})

    def test_impact_plan(self, *, changed_paths: list[str]) -> CommandResult:
        normalized=[]
        for raw in changed_paths:
            value=str(raw).strip().replace('\\','/')
            if not value or value.startswith('/') or ':' in value[:3] or '..' in Path(value).parts:
                return self._block('quality test-impact plan','Test Impact accepts repository-relative paths only.','UOC009_TEST_IMPACT_PATH_BLOCK')
            normalized.append(value)
        if not normalized or len(normalized)>200:
            return self._block('quality test-impact plan','Provide 1..200 repository-relative changed paths.','UOC009_TEST_IMPACT_COUNT_BLOCK')
        result=TestImpactAnalyzerV2(self.root,TestImpactV2Options(changed_paths=tuple(sorted(set(normalized))))).analyze()
        return result

    def plan_job(self, *, operation_id: str, workspace_id: str, parameters: dict[str, Any] | None, idempotency_key: str, approval_id: str | None = None, full_regression_confirmation: str | None = None) -> CommandResult:
        try: profile=self.profiles.require(operation_id)
        except ValueError as exc: return self._block('quality job plan',str(exc),'UOC009_OPERATION_BLOCK')
        parameters=dict(parameters or {})
        if set(parameters)-set(profile.allowed_keys): return self._block('quality job plan','Parameters contain keys not allowed by the typed operation profile.','UOC009_PARAMETERS_BLOCK')
        if operation_id=='quality-gate' and str(parameters.get('profile','')) not in QUALITY_GATE_PROFILES:
            return self._block('quality job plan','Quality gate profile is not registered.','UOC009_QUALITY_PROFILE_BLOCK')
        if operation_id=='focused-tests':
            tcr=str(parameters.get('tcr_profile',''))
            if tcr not in self._tcr_profile_ids(): return self._block('quality job plan','Focused tests require a registered Test Contract Registry v2 profile id.','UOC009_TCR_PROFILE_BLOCK')
        if operation_id=='full-regression':
            confirm=full_regression_confirmation or str(parameters.get('confirmation',''))
            if confirm != FULL_REGRESSION_CONFIRMATION: return self._block('quality job plan',f'Full regression requires exact confirmation: {FULL_REGRESSION_CONFIRMATION}','UOC009_FULL_REGRESSION_CONFIRMATION_BLOCK')
            parameters={'confirmation':FULL_REGRESSION_CONFIRMATION}
        if operation_id=='evidence-package':
            parameters={'limit':max(1,min(int(parameters.get('limit',100)),500))}
        if profile.requires_approval:
            if not approval_id: return self._block('quality job plan','This operation requires an approved Approval Center record before planning.','UOC009_APPROVAL_REQUIRED_BLOCK')
            approval=self._approval_check(approval_id,profile)
            if not approval.ok: return approval
        try:
            handle=self.jobs.plan(capability_id=profile.capability_id,workspace_id=workspace_id or 'devpilot-local',parameters=parameters,idempotency_key=idempotency_key,dry_run=operation_id not in {'focused-tests','full-regression'},timeout_seconds=profile.timeout_seconds,retry_limit=0,approval_binding_id=approval_id)
        except Exception as exc:
            return self._block('quality job plan',f'{type(exc).__name__}: {exc}','UOC009_JOB_PLAN_BLOCK')
        plan={'schema_id':'SCHEMA-DEVPL-UOC009-QUALITY-JOB-PLAN-V1','job_id':handle.record['job_id'],'operation_id':operation_id,'capability_id':profile.capability_id,'parameters':parameters,'approval_id':approval_id,'workspace_id':workspace_id or 'devpilot-local','timeout_seconds':profile.timeout_seconds,'idempotent_replay':handle.idempotent_replay}
        path=self.runtime.save_plan(handle.record['job_id'],plan)
        return self._pass('quality job plan','Governed quality job planned.',{'job':self._public_job(handle.record),'plan':plan,'plan_ref':str(path.relative_to(self.root)).replace('\\','/'),'summary':{'requires_approval':profile.requires_approval,'supports_cancel':profile.supports_cancel,'arbitrary_shell':False}})

    def execute_job(self, *, job_id: str) -> CommandResult:
        try:
            record=self.jobs.store.load(job_id); plan=self.runtime.load_plan(job_id); profile=self.profiles.require(str(plan['operation_id']))
            if profile.requires_approval:
                check=self._approval_check(str(plan.get('approval_id') or ''),profile)
                if not check.ok: return check
            if record['status']=='pending-approval': return self._block('quality job execute','Job is still pending approval.','UOC009_JOB_PENDING_APPROVAL_BLOCK')
            if record['status'] in {'planned','approved'}: self.jobs.queue(job_id)
            elif record['status']!='queued': return self._block('quality job execute',f'Job cannot execute from state {record["status"]}.','UOC009_JOB_STATE_BLOCK')
            cmd=[sys.executable,'-m','devpilot_core.application.quality_job_worker','--repo-root',str(self.root),'--job-id',job_id]
            proc=subprocess.Popen(cmd,cwd=str(self.root),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,shell=False,close_fds=(os.name!='nt'))
            metadata=self.meta.load(job_id)
            metadata.update({'phase':'worker-starting','progress_percent':1,'worker_pid':proc.pid,'worker_started_at':record.get('updated_at'),'reconciled_orphan':False})
            self.meta.save(metadata)
            current=self.jobs.store.load(job_id)
            return self._pass('quality job execute','Typed UOC-009 worker started.',{'job':self._public_job(current),'worker':{'pid':proc.pid,'argv_contract':'fixed-uoc009-worker','shell':False},'summary':{'started':True,'operation_id':profile.operation_id}})
        except Exception as exc:
            return self._block('quality job execute',f'{type(exc).__name__}: {exc}','UOC009_JOB_EXECUTE_BLOCK')

    def package_evidence(self, *, limit: int=100) -> CommandResult:
        limit=max(1,min(int(limit),500)); out=self.root/'outputs/evidence_packages/uoc009_quality'; out.mkdir(parents=True,exist_ok=True)
        stamp=uuid.uuid4().hex[:12]; archive=out/f'quality_evidence_{stamp}.zip'
        result_paths=self.runtime.list_results()[-limit:]
        entries: list[dict[str, Any]]=[]
        candidates: list[tuple[Path,str]]=[]
        for result_path in result_paths:
            candidates.append((result_path,f'results/{result_path.name}'))
            junit=self.runtime.runtime/f'{result_path.stem}.junit.xml'
            if junit.is_file(): candidates.append((junit,f'junit/{junit.name}'))
        for rel in ['.devpilot/project_state.json','docs/post_h_eval_002_uoc_008_manifest.json','docs/post_h_eval_002_uoc_009_manifest.json']:
            source=self.root/rel
            if source.is_file(): candidates.append((source,f'contracts/{Path(rel).name}'))
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as zf:
            for source,arcname in candidates:
                data=source.read_bytes(); zf.writestr(arcname,data); entries.append({'path':arcname,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
            manifest={'schema_id':'devpilot.uoc009.quality_evidence_package.v1','entries':entries,'summary':{'entries_total':len(entries),'results_total':len(result_paths),'source_mutations':False,'network_used':False,'external_api_used':False}}
            zf.writestr('quality_evidence_manifest.json',json.dumps(manifest,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest()
        return self._pass('quality evidence package','Bounded local quality evidence package created.',{'archive_ref':str(archive.relative_to(self.root)).replace('\\','/'),'archive_sha256':archive_sha256,'summary':{'results_total':len(result_paths),'entries_total':len(entries),'source_mutations':False,'network_used':False}})

    def _approval_check(self, approval_id: str, profile: QualityOperationProfile) -> CommandResult:
        result=self.approvals.show(approval_id)
        if not result.ok: return self._block('quality approval check','Approval record was not found.','UOC009_APPROVAL_NOT_FOUND_BLOCK')
        approval=result.data.get('approval',{}) if isinstance(result.data,dict) else {}
        expected_tool=profile.capability_id.removeprefix('cli.')
        if approval.get('status')!='approved' or approval.get('tool_id')!=expected_tool or approval.get('action')!='execute' or approval.get('subject')!=profile.operation_id or approval.get('expired'):
            return self._block('quality approval check','Approval is not an active exact binding for this quality operation.','UOC009_APPROVAL_BINDING_BLOCK')
        return self._pass('quality approval check','Approval binding verified.',{'approval_id':approval_id,'summary':{'approved':True}})

    def _tcr_profile_ids(self) -> set[str]:
        d=json.loads((self.root/'.devpilot/testing/test_contract_registry_v2.json').read_text(encoding='utf-8')); return {str(x.get('profile_id')) for x in d.get('profiles',[]) if x.get('profile_id')}
    def _public_job(self, record: dict[str,Any]) -> dict[str,Any]:
        hidden={'cancel_token_hash','idempotency_key_hash','request_fingerprint'}; return {k:v for k,v in record.items() if k not in hidden}
    def _pass(self, command: str, message: str, data: dict[str,Any]) -> CommandResult:
        return CommandResult(command=command,ok=True,exit_code=ExitCode.PASS,message=message,data=data,findings=[])
    def _block(self, command: str, message: str, finding_id: str) -> CommandResult:
        return CommandResult(command=command,ok=False,exit_code=ExitCode.BLOCK,message=message,data={'summary':{'blocked':True}},findings=[Finding(finding_id,message,Severity.BLOCK)])
