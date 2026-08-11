from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from devpilot_core.approval.service import ApprovalService
from devpilot_core.docs_governance.validator import DocumentationGovernanceValidator
from devpilot_core.quality import QualityGate, QualityGateOptions
from devpilot_core.release_candidate import ReleaseCandidateVerificationProfile
from devpilot_core.testing import TestContractRegistry, TestContractRegistryV2Validator, TestImpactAnalyzerV2, TestImpactV2Options
from devpilot_core.validators.readiness import build_strict_readiness_result

from .governed_job_capability_registry import GovernedJobCapabilityRegistry
from .governed_jobs import GovernedJobFramework
from .governed_job_operations import GovernedJobOperationsApplicationService
from .quality_operations import FULL_REGRESSION_CONFIRMATION, QualityOperationProfileRegistry, QualityRuntimeStore


def _result_dict(result: Any) -> dict[str,Any]:
    return result.to_dict() if hasattr(result,'to_dict') else dict(result)


def _approval_ok(root: Path, approval_id: str, capability_id: str, operation_id: str) -> bool:
    result=ApprovalService(root).show(approval_id)
    if not result.ok: return False
    a=result.data.get('approval',{})
    return a.get('status')=='approved' and not a.get('expired') and a.get('tool_id')==capability_id.removeprefix('cli.') and a.get('action')=='execute' and a.get('subject')==operation_id


def _pytest_summary(xml_path: Path, returncode: int) -> dict[str,Any]:
    passed=failed=errors=skipped=0
    try:
        root=ET.parse(xml_path).getroot(); suites=[root] if root.tag=='testsuite' else list(root.findall('testsuite'))
        tests=sum(int(s.attrib.get('tests','0')) for s in suites); failed=sum(int(s.attrib.get('failures','0')) for s in suites); errors=sum(int(s.attrib.get('errors','0')) for s in suites); skipped=sum(int(s.attrib.get('skipped','0')) for s in suites); passed=max(0,tests-failed-errors-skipped)
    except Exception: pass
    return {'passed':passed,'failed':failed,'errors':errors,'skipped':skipped,'returncode':returncode}


def _focused_files(root: Path, profile_id: str) -> list[str]:
    d=json.loads((root/'.devpilot/testing/test_contract_registry_v2.json').read_text(encoding='utf-8'))
    p=next((x for x in d.get('profiles',[]) if x.get('profile_id')==profile_id),None)
    if not p: raise ValueError('Unknown TCR profile id')
    critical=set(p.get('criticalities',[])); execution=set(p.get('execution_profiles',[])); files=[]
    for c in d.get('contracts',[]):
        if critical and c.get('criticality') not in critical: continue
        if execution and c.get('execution_profile') not in execution: continue
        for f in c.get('test_files',[]):
            if isinstance(f,str) and f.startswith('tests/') and (root/f).is_file(): files.append(f)
    return sorted(set(files))


def run_job(root: Path, job_id: str) -> int:
    registry=GovernedJobCapabilityRegistry(root); framework=GovernedJobFramework(root,registry=registry); ops=GovernedJobOperationsApplicationService(root); profiles=QualityOperationProfileRegistry(root); runtime=QualityRuntimeStore(root)
    plan=runtime.load_plan(job_id); profile=profiles.require(str(plan['operation_id'])); params=dict(plan.get('parameters',{})); approval_id=str(plan.get('approval_id') or '')
    if profile.requires_approval and not _approval_ok(root,approval_id,profile.capability_id,profile.operation_id):
        framework.complete(job_id,status='block',error='Approval binding is not valid at execution time.'); return 20
    framework.start(job_id); stop=threading.Event()
    def heartbeat() -> None:
        while not stop.wait(5):
            try: ops.record_progress(job_id=job_id,phase='running',progress_percent=15,message='UOC-009 worker heartbeat')
            except Exception: return
    thread=threading.Thread(target=heartbeat,daemon=True); thread.start()
    try:
        ops.record_progress(job_id=job_id,phase='running',progress_percent=5,worker_pid=os.getpid(),message=f'UOC-009 {profile.operation_id} started')
        kind=profile.kind
        if kind=='test-impact': result=TestImpactAnalyzerV2(root,TestImpactV2Options(changed_paths=tuple(params.get('changed_paths',[])))).analyze(); payload=_result_dict(result)
        elif kind=='tcr-v1': payload=_result_dict(TestContractRegistry(root).validate())
        elif kind=='tcr-v2': payload=_result_dict(TestContractRegistryV2Validator(root).validate())
        elif kind=='project-state': payload=_result_dict(TestContractRegistry(root).project_state())
        elif kind=='docs-governance': payload=_result_dict(DocumentationGovernanceValidator(root).run())
        elif kind=='quality-gate': payload=_result_dict(QualityGate(root,options=QualityGateOptions(profile=str(params['profile']),include_pytest=False)).run())
        elif kind=='readiness': payload=_result_dict(build_strict_readiness_result(root))
        elif kind=='release-profile': payload=_result_dict(ReleaseCandidateVerificationProfile(root).inspect())
        elif kind in {'tests-focused','tests-full'}:
            if kind=='tests-full' and params.get('confirmation')!=FULL_REGRESSION_CONFIRMATION: raise RuntimeError('Full regression confirmation drifted after planning.')
            files=_focused_files(root,str(params['tcr_profile'])) if kind=='tests-focused' else []
            junit=runtime.runtime/f'{job_id}.junit.xml'; junit.parent.mkdir(parents=True,exist_ok=True)
            cmd=[sys.executable,'-m','pytest','-q',*files,f'--junitxml={junit}']; cp=subprocess.run(cmd,cwd=str(root),shell=False,timeout=profile.timeout_seconds,check=False)
            summary=_pytest_summary(junit,cp.returncode); payload={'ok':cp.returncode==0,'exit_code':0 if cp.returncode==0 else 1,'command':'typed pytest registry execution','message':'Focused/full pytest completed.','data':{'summary':summary,'selection':{'profile_id':params.get('tcr_profile'),'test_files_total':len(files),'full_regression':kind=='tests-full'}},'findings':[]}
        elif kind=='evidence-package':
            from .quality_operations import QualityOperationsApplicationService
            payload=_result_dict(QualityOperationsApplicationService(root).package_evidence(limit=int(params.get('limit',100))))
        else: raise RuntimeError(f'Unsupported typed worker kind: {kind}')
        result_path=runtime.save_result(job_id,{'schema_id':'SCHEMA-DEVPL-UOC009-QUALITY-JOB-RESULT-V1','job_id':job_id,'operation_id':profile.operation_id,'result':payload})
        ok=bool(payload.get('ok')); exit_code=int(payload.get('exit_code',0 if ok else 1)); status='pass' if ok and exit_code==0 else ('error' if exit_code==3 else 'block')
        ops.record_progress(job_id=job_id,phase='completed',progress_percent=100,message=f'UOC-009 {profile.operation_id} completed: {status}')
        framework.complete(job_id,status=status,result_summary={'operation_id':profile.operation_id,'ok':ok,'exit_code':exit_code,'counts':payload.get('data',{}).get('summary',{})},artifact_refs=[str(result_path.relative_to(root)).replace('\\','/')])
        return 0 if status=='pass' else 20
    except subprocess.TimeoutExpired:
        framework.complete(job_id,status='error',error='Typed worker timeout budget exceeded.'); return 30
    except Exception as exc:
        framework.complete(job_id,status='error',error=f'{type(exc).__name__}: {exc}'); return 30
    finally:
        stop.set(); thread.join(timeout=1)


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',required=True); p.add_argument('--job-id',required=True); a=p.parse_args(); return run_job(Path(a.repo_root).resolve(),a.job_id)
if __name__=='__main__': raise SystemExit(main())
