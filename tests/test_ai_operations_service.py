from pathlib import Path
from devpilot_core.application.ai_operations import AiOperationsApplicationService, AiOperationProfileRegistry
ROOT=Path(__file__).resolve().parents[1]

def test_uoc010_catalog_is_four_typed_local_operations() -> None:
    r=AiOperationsApplicationService(ROOT).catalog(); assert r.ok
    assert len(r.data['operations'])==4
    assert r.data['summary']['arbitrary_shell'] is False
    assert r.data['summary']['external_api_enabled'] is False
    assert r.data['summary']['generic_tool_execution'] is False

def test_uoc010_status_exposes_provider_rag_memory_tool_and_handoff_governance() -> None:
    r=AiOperationsApplicationService(ROOT).status(); assert r.ok
    assert r.data['summary']['mock_mandatory'] is True and r.data['summary']['external_api_enabled'] is False
    assert r.data['summary']['memory_enabled_by_default'] is False and r.data['summary']['memory_counts_as_formal_evidence'] is False
    providers={x['provider_id']:x for x in r.data['providers']}; assert providers['mock']['enabled'] is True; assert providers['openai']['external_api'] is True and providers['openai']['enabled'] is False

def test_uoc010_rag_query_plan_is_typed_and_external_provider_is_blocked() -> None:
    s=AiOperationsApplicationService(ROOT)
    r=s.plan_job(operation_id='rag-query',workspace_id='devpilot-local',parameters={'query':'DevPilot local-first','top_k':3,'index_source':'canonical'},idempotency_key='uoc010-rag-query-test'); assert r.ok
    b=s.plan_job(operation_id='agent-run',workspace_id='devpilot-local',parameters={'agent_id':'requirements.agent','task_id':'summarize-gaps','target_id':'requirements','provider_id':'openai','memory_opt_in':False},idempotency_key='uoc010-external-block',approval_id='missing'); assert not b.ok and 'External API' in b.message

def test_uoc010_sensitive_agent_and_runtime_rag_index_require_approval() -> None:
    s=AiOperationsApplicationService(ROOT)
    for operation,params in [('agent-run',{'agent_id':'requirements.agent','task_id':'summarize-gaps','target_id':'requirements','provider_id':'mock','memory_opt_in':False}),('rag-index',{'target_id':'docs'})]:
        r=s.plan_job(operation_id=operation,workspace_id='devpilot-local',parameters=params,idempotency_key=f'uoc010-no-approval-{operation}'); assert not r.ok and 'approval' in r.message.lower()

def test_uoc010_handoff_is_bounded_to_allowlisted_workflow_and_three_steps() -> None:
    s=AiOperationsApplicationService(ROOT)
    r=s.plan_job(operation_id='handoff-run',workspace_id='devpilot-local',parameters={'workflow_id':'repo-review','target_id':'src','max_steps':99},idempotency_key='uoc010-handoff-bounded'); assert r.ok
    assert r.data['plan']['parameters']['max_steps']==3 and r.data['plan']['parameters']['supervisor']=='multiagent.coordinator'
    b=s.plan_job(operation_id='handoff-run',workspace_id='devpilot-local',parameters={'workflow_id':'swarm','target_id':'src','max_steps':2},idempotency_key='uoc010-handoff-block'); assert not b.ok

def test_uoc010_worker_and_service_do_not_accept_arbitrary_shell_or_external_api() -> None:
    source=(ROOT/'src/devpilot_core/application/ai_operations.py').read_text(encoding='utf-8')+(ROOT/'src/devpilot_core/application/ai_job_worker.py').read_text(encoding='utf-8')
    assert 'shell=False' in source and 'shell=True' not in source and 'os.system' not in source
    assert 'External API providers are disabled for UOC-010.' in source
    assert "'max_turns':1" in source or "'max_turns': 1" in source

def test_uoc010_profile_registry_is_lazy() -> None:
    r=AiOperationProfileRegistry(ROOT); assert r._payload is None; assert len(r.list())==4
