from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.miasi import MIASIApplicabilityEvaluator

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def state(*artifacts: tuple[str, str]):
    return {"artifacts": [{"artifact_id": a, "lifecycle": s, "source_ref": None, "fingerprint": None} for a, s in artifacts]}


def context(project_ai, *, caps=(), risk="low", features=(), review="NOT_REQUIRED"):
    return {
        "schema_id":"SCHEMA-DEVPL-MIASI-APPLICABILITY-CONTEXT-V1","schema_version":"1.0","workspace_id":"ws-test",
        "project":{"declared_ai_usage":project_ai,"capabilities":list(caps),"risk_level":risk,"evidence_refs":["fixture:project"]},
        "features":list(features),"risk_review_status":review,"evidence_refs":["fixture:05-c"]
    }


def ready_base(extra=()):
    rows=[("miasi-agent-card","FROZEN"),("miasi-tool-card","APPROVED"),("miasi-policy-card","FROZEN"),("miasi-eval-card","APPROVED"),("miasi-observability-card","FROZEN")]
    rows.extend(extra); return state(*rows)


def test_05_c_policy_is_fail_closed_and_traced_to_miasi_sources():
    policy=load('.devpilot/miasi/applicability_policy.json')
    assert policy['agent_execution_enabled'] is False and policy['rag_execution_enabled'] is False
    assert policy['critical_risk_review_required'] is True
    assert {'SEM-RBAC-001','SEM-APPROVAL-SCOPE-001','SEM-NO-GO-GUARD-001'} <= set(policy['required_semantic_rule_ids'])
    assert all(len(row['source_sha256'])==64 for row in policy['source_refs'])


def test_05_c_non_ai_is_not_applicable_with_pass_gate():
    result=MIASIApplicabilityEvaluator(ROOT).evaluate(context(False),state_payload=state())
    assert result.status=='NOT_APPLICABLE' and result.gate_status=='PASS'
    assert result.required_controls==() and result.agent_execution_allowed is False


def test_05_c_ai_project_is_applicable_when_required_controls_ready():
    result=MIASIApplicabilityEvaluator(ROOT).evaluate(context(True,caps=('llm','tool_calling'),risk='medium'),state_payload=ready_base())
    assert result.status=='APPLICABLE' and result.gate_status=='PASS'
    assert not result.missing_controls and result.policy_binding['ready'] is True
    assert result.agent_execution_allowed is False and result.rag_execution_allowed is False


def test_05_c_ambiguous_fails_closed():
    result=MIASIApplicabilityEvaluator(ROOT).evaluate(context(None),state_payload=state())
    assert result.status=='REVIEW_REQUIRED' and result.gate_status=='BLOCK'
    assert any(x['code']=='MIASI_APPLICABILITY_REVIEW_REQUIRED' for x in result.blockers)


def test_05_c_missing_card_blocks_applicable_project():
    result=MIASIApplicabilityEvaluator(ROOT).evaluate(context(True,caps=('agent',),risk='medium'),state_payload=state(('miasi-agent-card','FROZEN')))
    assert result.status=='APPLICABLE' and result.gate_status=='BLOCK'
    assert {'Tool','Policy','Eval','Observability'} <= set(result.missing_controls)


def test_05_c_rag_and_memory_add_specialized_controls():
    result=MIASIApplicabilityEvaluator(ROOT).evaluate(context(True,caps=('rag','memory'),risk='medium'),state_payload=ready_base((('miasi-rag-card','APPROVED'),('miasi-memory-card','FROZEN'))))
    kinds={x['kind'] for x in result.required_controls}
    assert {'RAG','Memory'} <= kinds and result.gate_status=='PASS'


def test_05_c_critical_risk_requires_governed_review_even_with_cards():
    st=ready_base((('miasi-human-approval-card','FROZEN'),))
    blocked=MIASIApplicabilityEvaluator(ROOT).evaluate(context(True,caps=('agent',),risk='critical',review='PENDING'),state_payload=st)
    assert blocked.gate_status=='BLOCK' and 'MIASI_RISK_ESCALATED_CRITICAL' in blocked.reason_codes
    passed=MIASIApplicabilityEvaluator(ROOT).evaluate(context(True,caps=('agent',),risk='critical',review='APPROVED'),state_payload=st)
    assert passed.gate_status=='PASS'


def test_05_c_feature_reevaluation_non_ai_to_ai():
    ev=MIASIApplicabilityEvaluator(ROOT)
    before=ev.evaluate(context(False),state_payload=state())
    feature={"feature_id":"search-assistant","declared_ai_usage":True,"capabilities":["llm"],"risk_level":"medium","evidence_refs":["feature:change"]}
    after=ev.evaluate(context(False,features=(feature,)),state_payload=ready_base())
    assert before.status=='NOT_APPLICABLE' and after.status=='APPLICABLE'
    assert 'MIASI_FEATURE_EVOLUTION_NON_AI_TO_AI' in after.reason_codes


def test_05_c_project_status_ui_contract_maps_miasi_without_new_route():
    source=(ROOT/'ui/web/src/pages/ProjectStatusView.ts').read_text(encoding='utf-8')
    assert 'renderMiasi' in source and 'MIASI · Aplicabilidad y controles' in source
    assert 'Faltan controles' in source and 'AGENT/RAG permanecen no ejecutables' in source
    assert 'innerHTML' not in source
    ui=load('.devpilot/interfaces/ui_route_contract_registry.json')
    route=next(r for r in ui['routes'] if r['route_id']=='ui.project-status')
    assert route['miasi_applicability_indicator'] is True
    api=load('.devpilot/interfaces/api_route_contract_registry.json')
    api_route=next(r for r in api['routes'] if r['route_id']=='api.guided-sdlc.project-status')
    assert api_route['miasi_applicability_projection'] is True


def test_05_c_historical_miasi_registries_remain_authoritative_inputs():
    assert load('.devpilot/miasi/agent_registry.json')['created_by']=='FUNC-SPRINT-11'
    assert load('.devpilot/miasi/tool_registry.json')['created_by']=='FUNC-SPRINT-11'
    matrix=load('.devpilot/miasi/policy_matrix.json')
    assert any(r['rule_id']=='RBAC_CHECK_SENSITIVE_ACTION_ALLOW' for r in matrix['rules'])
    sem=load('.devpilot/miasi/semantic_rules.json')
    assert next(r for r in sem['semantic_rules'] if r['rule_id']=='SEM-RBAC-001')['critical'] is True


def test_05_c_guided_sdlc_application_service_projects_real_miasi_decision(tmp_path):
    import hashlib, os, shutil
    from devpilot_core.application.guided_sdlc_service import GuidedSDLCApplicationService
    from devpilot_core.guided_sdlc.models import WorkspaceEngineeringState, EngineeringLifecycleStatus, MIPSoftwarePhase
    from devpilot_core.interfaces.api.operator_flow_smoke import OPERATOR_FLOW_RUNTIME_SANDBOX_IGNORE_PATTERNS

    for rel in ['.devpilot', 'docs/06_miasi']:
        source = ROOT / rel
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns(*OPERATOR_FLOW_RUNTIME_SANDBOX_IGNORE_PATTERNS),
        )
    assert not list(tmp_path.rglob('auth.db*'))
    assert not list(tmp_path.rglob('devpilot.db*'))
    # Workspace registry points at '.' so its binding is the temporary platform root.
    fingerprint = hashlib.sha256(os.path.normcase(str(tmp_path.resolve())).encode('utf-8')).hexdigest()
    state = WorkspaceEngineeringState(
        workspace_id='devpilot-local', project_id='devpilot-local', workspace_root_fingerprint=fingerprint,
        lifecycle_status=EngineeringLifecycleStatus.IN_PROGRESS, phase=MIPSoftwarePhase.REQUIREMENTS,
        current_step='requirements', sequence=0, created_at_utc='2026-08-24T00:00:00Z', updated_at_utc='2026-08-24T00:00:00Z',
        git={'head':None,'branch':None,'dirty':None,'fingerprint':None},
        artifacts=tuple({'artifact_id':x,'lifecycle':'FROZEN','source_ref':None,'fingerprint':None} for x in [
            'miasi-agent-card','miasi-tool-card','miasi-policy-card','miasi-eval-card','miasi-observability-card'
        ]), planning=(), quality=(), gates=(), blockers=(), revalidation={'status':'NOT_REQUIRED','reason_codes':[]}, source_fingerprints=(), next_action_ref=None,
    )
    store = tmp_path / 'outputs/workspaces/devpilot-local'
    store.mkdir(parents=True)
    (store / 'engineering_state.json').write_text(json.dumps(state.to_payload(), indent=2), encoding='utf-8')
    ctx = context(True, caps=('llm','tool_calling'), risk='medium')
    ctx['workspace_id'] = 'devpilot-local'
    (store / 'miasi_applicability_context.json').write_text(json.dumps(ctx, indent=2), encoding='utf-8')
    result = GuidedSDLCApplicationService(tmp_path).project_status_primary(workspace_id='devpilot-local', observed_at_utc='2026-08-24T00:00:01Z')
    assert result.ok is True
    miasi = result.data['project_status']['miasi']
    assert miasi['status'] == 'APPLICABLE' and miasi['gate_status'] == 'PASS'
    assert result.data['ui_state'] == 'READY'
    assert miasi['agent_execution_allowed'] is False and miasi['rag_execution_allowed'] is False


def test_05_c_project_status_explicit_context_recovery_is_server_validated_and_bare_route_stays_guarded():
    main=(ROOT/'ui/web/src/main.ts').read_text(encoding='utf-8')
    client=(ROOT/'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    assert "path !== '/project/status' || params.get('recover_project_context') !== 'server-active'" in main
    segment=main.split('async function recoverExplicitProjectStatusContext',1)[1].split('async function recoverExplicitServerProjectContext',1)[0]
    assert 'client.projectStatus()' in segment
    assert 'restoreProjectJourneyContextFromProjectStatusRecovery(response)' in segment
    assert 'projectEntryDryRun' not in segment and 'projectEntryExecute' not in segment
    assert "return journey?.phase === 'project';" in main
    helper=client.split('export function restoreProjectJourneyContextFromProjectStatusRecovery',1)[1].split('export function beginProjectEntryJourney',1)[0]
    for required in [
        'response.ok === true', 'data?.read_only === true', 'data?.actor_neutral === true',
        'data?.network_used === false', 'data?.external_api_used === false',
        'data?.mutations_performed === false', "projectId.toLowerCase() !== 'unknown'",
        "!['EMPTY', 'UNKNOWN'].includes(uiState)", "phase: 'project'",
        'globalThis.sessionStorage?.setItem(PROJECT_JOURNEY_CONTEXT_KEY',
    ]:
        assert required in helper


def test_05_c_historical_04e_document_recovery_contract_is_not_rewritten_by_project_status_recovery():
    client=(ROOT/'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    main=(ROOT/'ui/web/src/main.ts').read_text(encoding='utf-8')
    assert "path !== '/workspace/documents' || params.get('recover_project_context') !== 'server-active'" in client
    historical=main.split('async function recoverExplicitServerProjectContext',1)[1].split('function currentLocationTarget',1)[0]
    assert 'client.settingsWorkspace()' in historical
    assert 'client.workspaceEditExecutionStatus(intent.execution_id)' in historical
    assert 'restoreProjectJourneyContextFromServerRecovery' in historical
