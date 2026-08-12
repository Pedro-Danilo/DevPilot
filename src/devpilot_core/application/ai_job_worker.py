from __future__ import annotations

import argparse
import json
import os
import threading
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from devpilot_core.agents.runtime import AgentRuntime
from devpilot_core.multiagent.coordinator import MultiAgentCoordinator, MultiAgentRunOptions
from devpilot_core.rag.indexer import LocalRagIndexer, RagIndexOptions
from devpilot_core.rag.retriever import LocalRagRetriever, RagQueryOptions

from .ai_operations import AiOperationProfileRegistry, AiRuntimeStore, CANONICAL_RAG_INDEX, MEMORY_DIR, RUNTIME_RAG_INDEX, TARGETS, TASKS
from .governed_job_capability_registry import GovernedJobCapabilityRegistry
from .governed_job_operations import GovernedJobOperationsApplicationService
from .governed_jobs import GovernedJobFramework


def _dict(result: Any) -> dict[str,Any]: return result.to_dict() if hasattr(result,'to_dict') else dict(result)
def _iso(dt: datetime) -> str: return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def _write_memory_receipt(root: Path, *, agent_id: str, workspace_id: str, task_id: str, result: dict[str,Any]) -> str:
    memory_dir=root/MEMORY_DIR; memory_dir.mkdir(parents=True,exist_ok=True); now=datetime.now(timezone.utc); record_id=f'uoc010_{uuid.uuid4().hex[:16]}'
    path=memory_dir/f'{record_id}.json'
    payload={
        'record_id':record_id,'created_at_utc':_iso(now),'updated_at_utc':_iso(now),'agent_id':agent_id,'workspace_id':workspace_id,'memory_type':'session_memory',
        'content_redacted':{'summary':'UOC-010 governed agent execution completed.','task_id':task_id,'result_ok':bool(result.get('ok')),'tags':['uoc010','redacted','opt-in']},
        'source_refs':['docs/post_h_eval_002_uoc_010_manifest.json'],'retention':{'retention_days':14,'expires_at_utc':_iso(now+timedelta(days=14))},
        'policy':{'semantic_memory_enabled':False,'memory_enabled_by_default':False,'export_redacted':True,'counts_as_formal_evidence':False},
        'safety':{'raw_prompt_stored':False,'raw_output_stored':False,'secret_values_stored':False,'external_storage_used':False,'shared_across_workspaces':False},
    }
    path.write_text(json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
    return str(path.relative_to(root)).replace('\\','/')


def run_job(root: Path, job_id: str) -> int:
    registry=GovernedJobCapabilityRegistry(root); framework=GovernedJobFramework(root,registry=registry); ops=GovernedJobOperationsApplicationService(root); profiles=AiOperationProfileRegistry(root); runtime=AiRuntimeStore(root)
    plan=runtime.load_plan(job_id); profile=profiles.require(str(plan['operation_id'])); params=dict(plan.get('parameters',{})); framework.start(job_id); stop=threading.Event()
    def heartbeat() -> None:
        while not stop.wait(5):
            try: ops.record_progress(job_id=job_id,phase='running',progress_percent=20,message='UOC-010 typed worker heartbeat')
            except Exception: return
    thread=threading.Thread(target=heartbeat,daemon=True); thread.start()
    try:
        ops.record_progress(job_id=job_id,phase='running',progress_percent=5,worker_pid=os.getpid(),message=f'UOC-010 {profile.operation_id} started')
        kind=profile.kind; memory_ref=None
        if kind=='rag-index':
            target=TARGETS[str(params['target_id'])]; result=LocalRagIndexer(root,options=RagIndexOptions(target=target,index_path=str(RUNTIME_RAG_INDEX).replace('\\','/'))).build(); payload=_dict(result)
        elif kind=='rag-query':
            index_path=CANONICAL_RAG_INDEX if params['index_source']=='canonical' else RUNTIME_RAG_INDEX
            result=LocalRagRetriever(root,options=RagQueryOptions(query=str(params['query']),index_path=str(index_path).replace('\\','/'),top_k=int(params['top_k']))).query(); payload=_dict(result)
            if not result.ok and any(getattr(f,'id','')=='RAG_QUERY_NO_SOURCES' for f in result.findings):
                payload['uoc010_state']='insufficient-evidence'; payload.setdefault('data',{}).setdefault('summary',{})['insufficient_evidence']=True
        elif kind=='agent-run':
            result=AgentRuntime(root).run(str(params['agent_id']),target=TARGETS[str(params['target_id'])],idea=TASKS[str(params['task_id'])],dry_run=True,provider=str(params['provider_id']),fallback_to_mock=False,timeout_seconds=min(120.0,float(profile.timeout_seconds)))
            payload=_dict(result)
            if params.get('memory_opt_in') and result.ok: memory_ref=_write_memory_receipt(root,agent_id=str(params['agent_id']),workspace_id=str(plan.get('workspace_id') or 'devpilot-local'),task_id=str(params['task_id']),result=payload)
        elif kind=='handoff-run':
            result=MultiAgentCoordinator(root).run(MultiAgentRunOptions(workflow=str(params['workflow_id']),target=TARGETS[str(params['target_id'])],max_steps=int(params['max_steps']),dry_run=True)); payload=_dict(result)
        else: raise RuntimeError(f'Unsupported UOC-010 typed worker kind: {kind}')
        governance={'provider_id':params.get('provider_id'),'external_api_used':False,'network_used':False,'max_turns':params.get('max_turns'),'max_cost_usd':params.get('max_cost_usd',0.0),'tool_execution_mode':'contract-only-dry-run','memory_opt_in':bool(params.get('memory_opt_in',False)),'memory_ref':memory_ref,'memory_counts_as_formal_evidence':False,'supervisor':params.get('supervisor'),'max_steps':params.get('max_steps')}
        result_path=runtime.save_result(job_id,{'schema_id':'SCHEMA-DEVPL-UOC010-AI-JOB-RESULT-V1','job_id':job_id,'operation_id':profile.operation_id,'result':payload,'governance':governance})
        insufficient=payload.get('uoc010_state')=='insufficient-evidence'; ok=bool(payload.get('ok')); exit_code=int(payload.get('exit_code',0 if ok else 1)); status='pass-with-gaps' if insufficient else ('pass' if ok and exit_code==0 else ('error' if exit_code==3 else 'block'))
        ops.record_progress(job_id=job_id,phase='completed',progress_percent=100,message=f'UOC-010 {profile.operation_id} completed: {status}')
        framework.complete(job_id,status=status,result_summary={'operation_id':profile.operation_id,'ok':ok,'exit_code':exit_code,'uoc010_state':payload.get('uoc010_state'),'provider_id':params.get('provider_id'),'memory_opt_in':bool(params.get('memory_opt_in',False)),'memory_ref':memory_ref,'external_api_used':False,'cost_usd':0.0},artifact_refs=[str(result_path.relative_to(root)).replace('\\','/')],evidence_refs=[])
        return 0 if status in {'pass','pass-with-gaps'} else 20
    except Exception as exc:
        framework.complete(job_id,status='error',error=f'{type(exc).__name__}: {exc}'); return 30
    finally:
        stop.set(); thread.join(timeout=1)


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',required=True); p.add_argument('--job-id',required=True); a=p.parse_args(); return run_job(Path(a.repo_root).resolve(),a.job_id)
if __name__=='__main__': raise SystemExit(main())
