from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace

from devpilot_core.application.planning_closure_service import PlanningClosureApplicationService
from devpilot_core.application import ApplicationService, ApplicationRequest
from devpilot_core.interfaces.api.routers import planning as planning_router
from devpilot_core.interfaces.api import security as api_security


def roadmap(lifecycle='FROZEN'):
    return {'lifecycle':lifecycle,'version':'1.0.0','content_sha256':'1'*64,'roadmap':{'milestones':[{'id':'mil-foundation','title':'Foundation','trace_links':[{'kind':'requirement','target_id':'REQ-001'},{'kind':'requirement','target_id':'REQ-002'}]}]}}

def backlog(lifecycle='FROZEN', coverage=100.0):
    return {'lifecycle':lifecycle,'version':'1.0.0','content_sha256':'2'*64,'required_requirement_ids':['REQ-001','REQ-002'],'coverage':{'required_coverage_percent':coverage},'backlog':{'backlog_id':'planning-backlog-001','version':'1.0.0','epics':[{'id':'epic-foundation','title':'Foundation','milestone_id':'mil-foundation'}],'stories':[{'id':'story-first','title':'First','epic_id':'epic-foundation','trace_links':[{'kind':'requirement','target_id':'REQ-001'}]},{'id':'story-second','title':'Second','epic_id':'epic-foundation','trace_links':[{'kind':'requirement','target_id':'REQ-002'}]}],'dependencies':[]}}

def sprint(lifecycle='FROZEN', executable=True):
    return {'lifecycle':lifecycle,'version':'1.0.0','content_sha256':'3'*64,'validation':{'executable':executable},'sprint_plan':{'sprint_plan_id':'sprint-plan-001','title':'Sprint 1','selected_stories':[{'story_id':'story-first'},{'story_id':'story-second'}]}}

def service(tmp_path: Path):
    r=SimpleNamespace(configured=False,valid=True,effective_workspace_root=tmp_path,active_workspace_id='fixture')
    resolver=SimpleNamespace(resolve=lambda:r)
    return PlanningClosureApplicationService(tmp_path,context_resolver=resolver)

def test_pre_code_ready_projects_build_roadmap(tmp_path: Path):
    svc=service(tmp_path); svc._pre_code_ready=lambda *_: True
    p=svc._project(tmp_path,'fixture',None,None,None,['owner'])
    assert p['journey_state']=='PRE_CODE_READY' and p['next_action']['label']=='Construir roadmap'

def test_partial_planning_projects_planning_and_visible_blockers(tmp_path: Path):
    svc=service(tmp_path); svc._pre_code_ready=lambda *_: True
    p=svc._project(tmp_path,'fixture',roadmap(),backlog('REVIEW'),None,['owner'])
    assert p['journey_state']=='PLANNING' and any(x['code']=='BACKLOG_FREEZE_REQUIRED' for x in p['blockers'])

def test_frozen_100_percent_planning_projects_implementing_ready(tmp_path: Path):
    svc=service(tmp_path); svc._pre_code_ready=lambda *_: True
    p=svc._project(tmp_path,'fixture',roadmap(),backlog(),sprint(),['owner'])
    assert p['journey_state']=='IMPLEMENTING_READY' and p['required_planning_coverage_percent']==100.0 and not p['blockers']

def test_trace_graph_links_requirement_milestone_epic_story_sprint(tmp_path: Path):
    svc=service(tmp_path); svc._pre_code_ready=lambda *_: True
    p=svc._project(tmp_path,'fixture',roadmap(),backlog(),sprint(),['owner']); kinds={x['kind'] for x in p['trace_graph']['edges']}
    assert {'requirement-to-milestone','milestone-to-epic','epic-to-story','story-to-sprint'} <= kinds
    # Exercise the canonical RoadmapWorkbench persistence shape used by the real browser journey.
    emitted=roadmap(); emitted['planning_state']={'milestones':emitted.pop('roadmap')['milestones']}
    p2=svc._project(tmp_path,'fixture',emitted,backlog(),sprint(),['owner']); kinds2={x['kind'] for x in p2['trace_graph']['edges']}
    assert {'requirement-to-milestone','milestone-to-epic','epic-to-story','story-to-sprint'} <= kinds2

def test_incomplete_coverage_never_claims_implementing_ready(tmp_path: Path):
    svc=service(tmp_path); svc._pre_code_ready=lambda *_: True
    p=svc._project(tmp_path,'fixture',roadmap(),backlog(coverage=50.0),sprint(),['owner'])
    assert p['journey_state']=='PLANNING' and any(x['code']=='BACKLOG_COVERAGE_REQUIRED' for x in p['blockers'])

def test_planning_projection_is_runtime_only_and_no_external_execution(tmp_path: Path):
    svc=service(tmp_path); svc._pre_code_ready=lambda *_: True
    p=svc._project(tmp_path,'fixture',roadmap(),backlog(),sprint(),['owner'])
    assert p['runtime_only'] and p['source_mutations_performed'] is False and p['network_used'] is False and p['external_api_used'] is False and p['agent_auto_approval'] is False

def test_application_service_exposes_closure_projection():
    root=Path(__file__).resolve().parents[1]; svc=ApplicationService(root)
    r=svc.handle(ApplicationRequest(operation='planning.closure.status',payload={'effective_roles':['owner']},client='test',dry_run=True)).to_dict()
    assert r['ok'] is True and 'planning_closure' in r['data']

def test_http_router_exposes_backlog_sprint_and_closure_successors():
    paths={r.path for r in planning_router.router.routes}
    assert {'/api/v1/planning/backlog','/api/v1/planning/backlog/proposals','/api/v1/planning/sprint','/api/v1/planning/sprint/proposals','/api/v1/planning/closure'} <= paths

def test_security_policy_binds_all_new_planning_routes():
    keys=set(api_security.API_ROUTE_POLICIES.keys())
    assert ('GET','/api/v1/planning/closure') in keys and ('POST','/api/v1/planning/backlog/approve') in keys and ('POST','/api/v1/planning/sprint/freeze') in keys

def test_ui_contains_backlog_sprint_trace_and_rbac_fail_closed():
    root=Path(__file__).resolve().parents[1]; text=(root/'ui/web/src/pages/RoadmapWorkbenchView.ts').read_text(encoding='utf-8')
    for token in ['2 · Backlog','3 · Sprint','Trace graph planning','Solo owner/product-owner','IMPLEMENTING_READY']:
        assert token in text

def test_project_status_integrates_planning_journey():
    root=Path(__file__).resolve().parents[1]; text=(root/'ui/web/src/pages/ProjectStatusView.ts').read_text(encoding='utf-8')
    assert 'Planning Journey' in text and 'planningClosure()' in text and '/planning/roadmap' in text

def test_08_e_rebind_and_exactly_one_full_lifecycle_contract():
    root=Path(__file__).resolve().parents[1]; state=json.loads((root/'.devpilot/project_state.json').read_text())
    assert state['gsdlc_08_e_parent_repo'].startswith('repo_DevPilot_Local_402_')
    assert state['gsdlc_08_e_full_regression_runs_allowed']==1
    status=state['gsdlc_08_e_status']
    if status=='IMPLEMENTED/LOCAL-QUALIFIED/WINDOWS-PENDING':
        assert state['gsdlc_08_e_full_regression_runs']==0
        assert state['gsdlc_08_e_browser_acceptance']=='PENDING-WINDOWS'
    else:
        assert status in {
            'CLOSED/PASS/WINDOWS-VALIDATED',
            'CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY',
        }
        assert state['gsdlc_08_e_full_regression_runs']==1
        assert state['gsdlc_08_e_browser_acceptance']=='PASS'
        assert state['gsdlc_08_e_windows_validation_status'] in {
            'CLOSED/PASS',
            'CLOSED/PASS/COMPOSITE-RECOVERY',
        }
        assert state['gsdlc_08_closure_status'] in {
            'CLOSED/PASS',
            'CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY',
        }
        assert state['gsdlc_program_status'].startswith('closed/GSDLC-08/PASS')
        assert state['gsdlc_current_canonical_repo'].startswith('repo_DevPilot_Local_404_')
