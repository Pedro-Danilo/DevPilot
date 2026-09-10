from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application.story_quality_gate import StoryQualityGateApplicationService
from devpilot_core.cli_models import CommandResult, ExitCode


def ok(data):
    return CommandResult('mock', True, ExitCode.PASS, 'PASS', data=data)


def make_service(tmp_path: Path, *, statuses=None, agent_escalates=False):
    plans = {
        'plan-a': {
            'test_plan_id':'plan-a','test_plan_hash':'hash-a','status':'APPROVED','story_execution_id':'exec-1','story_id':'story-1',
            'test_impact_report_hash':'impact-a','source_change_plan_id':'scp-a','source_change_plan_hash':'scp-hash-a',
            'changed_paths':['src/a.py'], 'full_regression_signal':{'execution_authorized':False},
        },
        'plan-b': {
            'test_plan_id':'plan-b','test_plan_hash':'hash-b','status':'APPROVED','story_execution_id':'exec-1','story_id':'story-1',
            'test_impact_report_hash':'impact-b','source_change_plan_id':'scp-b','source_change_plan_hash':'scp-hash-b',
            'changed_paths':['src/a.py'], 'full_regression_signal':{'execution_authorized':False},
        },
    }
    state = {'statuses': statuses or {'test':'PASS','build':'PASS','lint':'PASS'}, 'created': []}
    def load_plan(*, test_plan_id): return ok({'story_test_plan': plans[test_plan_id]})
    def list_jobs(*, test_plan_id):
        sts = state['statuses']
        jobs=[{
            'job_id':f'{test_plan_id}-{kind}-1','story_validation_kind':kind,'story_validation_status':status,
            'story_test_plan_id':test_plan_id,'story_test_plan_hash':plans[test_plan_id]['test_plan_hash'],
            'created_at':'2026-09-09T00:00:00Z','artifact_refs':['x.json'] if status=='PASS' else [],
        } for kind,status in sorted(sts.items())]
        return ok({'jobs':jobs})
    def create_jobs(**kwargs):
        state['created'].append(kwargs)
        return list_jobs(test_plan_id=kwargs['test_plan_id'])
    def agent(**kwargs):
        dec={'model_route_granted_permission': True if agent_escalates else False,'tool_executed': True if agent_escalates else False}
        return ok({'proposal':{'proposal_id':'proposal-1','tool_intent':{'tool_id':'story.source-change.propose'},'tool_execution_decision':dec}})
    svc=StoryQualityGateApplicationService(tmp_path, story_test_plan_loader=load_plan, validation_jobs_lister=list_jobs, validation_jobs_creator=create_jobs, agent_proposal_creator=agent)
    return svc,state


def test_required_validation_fail_and_pending_never_commit_ready(tmp_path):
    for bad in ('FAIL','ERROR','RUNNING'):
        svc,_=make_service(tmp_path / bad, statuses={'test':bad,'build':'PASS','lint':'PASS'})
        res=svc.evaluate(test_plan_id='plan-a',test_plan_hash='hash-a',actor='dev',actor_role='developer')
        assert res.ok
        report=res.data['story_quality_report']
        assert report['decision']=='BLOCK' and report['commit_ready'] is False
        assert any(f['severity']=='S1' and f['blocking'] for f in report['findings'])


def test_all_required_jobs_pass_produces_deterministic_pass_and_hash(tmp_path):
    svc,_=make_service(tmp_path)
    a=svc.evaluate(test_plan_id='plan-a',test_plan_hash='hash-a',actor='dev',actor_role='developer').data['story_quality_report']
    b=svc.evaluate(test_plan_id='plan-a',test_plan_hash='hash-a',actor='dev',actor_role='developer').data['story_quality_report']
    assert a['decision']=='PASS' and a['commit_ready'] is True
    assert a['inputs_hash']==b['inputs_hash'] and a['report_hash']==b['report_hash'] and a['report_id']==b['report_id']
    assert a['policy']['full_regression'] is False


def test_s0_s1_cannot_be_waived_and_agent_cannot_approve(tmp_path):
    svc,_=make_service(tmp_path)
    finding=svc.record_finding(test_plan_id='plan-a',test_plan_hash='hash-a',origin='security',severity='S1',message='critical',actor='dev',actor_role='developer').data['quality_finding']
    report=svc.evaluate(test_plan_id='plan-a',test_plan_hash='hash-a',actor='dev',actor_role='developer').data['story_quality_report']
    blocked=svc.request_waiver(report_id=report['report_id'],report_hash=report['report_hash'],finding_id=finding['finding_id'],reason='no',ttl_minutes=30,actor='dev',actor_role='developer')
    assert not blocked.ok and blocked.exit_code==ExitCode.BLOCK

    svc2,_=make_service(tmp_path/'s2')
    f2=svc2.record_finding(test_plan_id='plan-a',test_plan_hash='hash-a',origin='review',severity='S2',message='review gap',actor='dev',actor_role='developer').data['quality_finding']
    r2=svc2.evaluate(test_plan_id='plan-a',test_plan_hash='hash-a',actor='dev',actor_role='developer').data['story_quality_report']
    req=svc2.request_waiver(report_id=r2['report_id'],report_hash=r2['report_hash'],finding_id=f2['finding_id'],reason='bounded exception',ttl_minutes=30,actor='dev',actor_role='developer').data['quality_waiver']
    assert not svc2.decide_waiver(waiver_id=req['waiver_id'],decision='APPROVE',actor='agent-1',actor_role='owner',authority_source='agent-runtime').ok
    assert not svc2.decide_waiver(waiver_id=req['waiver_id'],decision='APPROVE',actor='dev',actor_role='owner').ok
    assert svc2.decide_waiver(waiver_id=req['waiver_id'],decision='APPROVE',actor='owner2',actor_role='owner').ok


def test_agent_route_never_grants_quality_or_source_authority(tmp_path):
    svc,_=make_service(tmp_path, agent_escalates=True)
    f=svc.record_finding(test_plan_id='plan-a',test_plan_hash='hash-a',origin='review',severity='S2',message='fix me',actor='dev',actor_role='developer').data['quality_finding']
    r=svc.evaluate(test_plan_id='plan-a',test_plan_hash='hash-a',actor='dev',actor_role='developer').data['story_quality_report']
    result=svc.plan_remediation(report_id=r['report_id'],report_hash=r['report_hash'],finding_id=f['finding_id'],mode='agent',actor='dev',actor_role='developer',instruction='propose fix',source_id='src-1')
    assert not result.ok and result.exit_code==ExitCode.BLOCK


def test_remediation_retest_requires_successor_plan_and_only_plans_impacted_jobs(tmp_path):
    svc,state=make_service(tmp_path)
    f=svc.record_finding(test_plan_id='plan-a',test_plan_hash='hash-a',origin='review',severity='S2',message='fix me',actor='dev',actor_role='developer').data['quality_finding']
    r=svc.evaluate(test_plan_id='plan-a',test_plan_hash='hash-a',actor='dev',actor_role='developer').data['story_quality_report']
    trace=svc.plan_remediation(report_id=r['report_id'],report_hash=r['report_hash'],finding_id=f['finding_id'],mode='manual',actor='dev',actor_role='developer').data['remediation_trace']
    stale=svc.plan_impacted_retest(trace_id=trace['trace_id'],new_test_plan_id='plan-a',new_test_plan_hash='hash-a',actor='dev',actor_role='developer')
    assert not stale.ok
    planned=svc.plan_impacted_retest(trace_id=trace['trace_id'],new_test_plan_id='plan-b',new_test_plan_hash='hash-b',actor='dev',actor_role='developer')
    assert planned.ok and state['created'][-1]['test_plan_id']=='plan-b'
    tr=planned.data['remediation_trace']
    assert tr['retest']['rerun_everything'] is False and tr['retest']['full_regression'] is False
    done=svc.complete_retest(trace_id=trace['trace_id'],actor='dev',actor_role='developer')
    assert done.ok and done.data['remediation_trace']['status']=='RESOLVED'


def test_quality_inputs_change_marks_report_stale(tmp_path):
    svc,state=make_service(tmp_path)
    report=svc.evaluate(test_plan_id='plan-a',test_plan_hash='hash-a',actor='dev',actor_role='developer').data['story_quality_report']
    state['statuses']['test']='FAIL'
    loaded=svc.get_report(report_id=report['report_id']).data['story_quality_report']
    assert loaded['stale'] is True and loaded['commit_ready'] is False and loaded['decision']=='BLOCK'


def test_registries_routes_and_ui_quality_mapping_are_current(tmp_path):
    root=Path(__file__).resolve().parents[1]
    api=json.loads((root/'.devpilot/interfaces/api_route_contract_registry.json').read_text())
    rbac=json.loads((root/'.devpilot/identity/server_rbac_policy_catalog.json').read_text())
    ui=json.loads((root/'.devpilot/interfaces/ui_route_contract_registry.json').read_text())
    ids={r['route_id'] for r in api['routes'] if r['route_id'].startswith('api.story-quality.')}
    assert len(ids)==9
    assert ids <= {r['route_id'] for r in rbac['route_policies']}
    assert all(not r['source_mutation_allowed'] and not r['remote_execution_allowed'] for r in api['routes'] if r['route_id'] in ids)
    quality=next(r for r in ui['routes'] if r['route_id']=='ui.quality')
    assert ids <= set(quality['allowed_api_routes'])


def test_10_c_project_status_browser_recovery_uses_session_bound_fallback_without_granting_mutation():
    root=Path(__file__).resolve().parents[1]
    main=(root/'ui/web/src/main.ts').read_text(encoding='utf-8')
    client=(root/'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    segment=main.split('async function recoverExplicitProjectStatusContext',1)[1].split('async function recoverExplicitServerProjectContext',1)[0]
    assert 'client.projectStatus()' in segment
    assert 'client.projectStatusSessionRecovery(expectedWorkspaceId)' in segment
    assert 'session.principal.workspace_scopes' in segment
    assert 'scopes.length===1 ? scopes[0] : undefined' in segment
    assert "if (!expectedWorkspaceId) return 'failed'" in segment
    assert 'projectStatusSessionRecovery(workspaceId?: string)' in client
    helper=client.split('async projectStatusSessionRecovery',1)[1].split('async stepActions',1)[0]
    assert "this.authJson<DevPilotApplicationResponse<GuidedSdlcProjectStatusResponseData>>" in helper
    assert "{ method: 'GET' }" in helper
    assert 'this.authHeaders()' not in helper


def test_10_c_project_status_recovery_binds_restored_workspace_to_authenticated_scope():
    root=Path(__file__).resolve().parents[1]
    client=(root/'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    helper=client.split('export function restoreProjectJourneyContextFromProjectStatusRecovery',1)[1].split('export function beginProjectEntryJourney',1)[0]
    assert 'expectedWorkspaceId?: string' in helper
    assert '(!expectedWorkspaceId || workspaceId === expectedWorkspaceId)' in helper
    assert 'data?.read_only === true' in helper
    assert 'data?.actor_neutral === true' in helper
    assert 'data?.mutations_performed === false' in helper
    assert "phase: 'project'" in helper
