from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def j(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))

def test_uoc010_project_state_preserves_pilot_and_candidate_lifecycle() -> None:
    s=j('.devpilot/project_state.json'); assert s['uoc_010_authorized'] is True; assert s['current_micro_sprint']=='POST-H-EVAL-002-02-B'; assert s['next_micro_sprint']=='POST-H-EVAL-002-02-C'; assert s['uoc_010_implementation_maturity']=='implemented-initial'; assert s['uoc_010_preliminary'] is True; assert s['uoc_010_external_api_enabled'] is False
    assert s['uoc_010_status'] in {'implemented-initial/pending-windows-browser-closure','closed/PASS'}
    if s['uoc_010_status'].startswith('implemented-initial'):
        assert s['current_repo']=='repo_DevPilot_Local_337_POST_H_EVAL_002_UOC_009.zip'; assert s['uoc_011_authorized'] is False
    else:
        assert s['uoc_010_authoritative_baseline']=='repo_DevPilot_Local_338_POST_H_EVAL_002_UOC_010.zip'; assert s['uoc_011_authorized'] is True

def test_uoc010_route_and_four_typed_adapters_preserve_no_go() -> None:
    ui=j('.devpilot/interfaces/ui_route_contract_registry.json'); api=j('.devpilot/interfaces/api_route_contract_registry.json'); jobs=j('.devpilot/interfaces/governed_job_capability_registry.json')
    route=next(x for x in ui['routes'] if x['route_id']=='ui.ai'); assert route['path']=='/ai'; assert all(route[k] is False for k in ('remote_execution_allowed','connector_write_allowed','plugin_execution_allowed','external_api_allowed'))
    expected={'api.ai.operations','api.ai.status','api.ai.jobs.plan','api.ai.jobs.execute','api.ai.jobs.result','api.ai.evidence-package'}; assert expected <= set(route['allowed_api_routes']); assert expected <= {x['route_id'] for x in api['routes']}
    uoc010=[x for x in jobs['capabilities'] if x['runtime'].get('adapter_id')=='uoc010.ai.typed-worker']; assert {x['capability_id'] for x in uoc010}=={'cli.rag.index','cli.rag.query','cli.agent.run','cli.multiagent.run'}; assert all(x['runtime']['execution_enabled'] for x in uoc010); assert jobs['safety']['arbitrary_shell_allowed'] is False

def test_uoc010_manifest_and_profiles_freeze_repo337_without_preauthorizing_uoc011() -> None:
    m=j('docs/post_h_eval_002_uoc_010_manifest.json'); assert m['input_repo']=='repo_DevPilot_Local_337_POST_H_EVAL_002_UOC_009.zip'; assert m['input_repo_sha256']=='4832eb5a058940a40458eea97c93104f4fa9ac05ebf3cadd9874694797d64a24'; assert m['external_api_enabled'] is False; assert m['uoc_011_authorized'] is False if m['status'].startswith('implemented-initial') else True
    p=j('.devpilot/ai/ui_ai_operation_profiles.json'); assert len(p['operations'])==4; assert p['safety']['mock_provider_mandatory'] is True; assert p['safety']['external_api_enabled'] is False; assert p['safety']['memory_counts_as_formal_evidence'] is False; assert p['budgets']['max_agent_turns']==1 and p['budgets']['max_handoff_steps']==3

def test_uoc010_docs_schemas_and_memory_ignore_are_present() -> None:
    for p in ['docs/07_interfaces/rag_agents_tools_handoffs.md','docs/audits/uoc_010_rag_agents_tools_handoffs_report.md','docs/post_h_eval_002_uoc_010_manifest.json','.devpilot/ai/ui_ai_operation_profiles.json','docs/schemas/ai_operation_profiles.schema.json','docs/schemas/ai_operation_parameters.schema.json','docs/schemas/ai_job_plan.schema.json','docs/schemas/ai_job_result.schema.json']:
        assert (ROOT/p).is_file()
    assert '.devpilot/agents/memory/' in (ROOT/'.gitignore').read_text(encoding='utf-8')
