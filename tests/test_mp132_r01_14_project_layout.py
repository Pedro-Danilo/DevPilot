from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from devpilot_core.workspace.environment_discovery import EnvironmentDiscoveryService
from devpilot_core.workspace.project_entry_contracts import stable_sha256
from devpilot_core.workspace.project_layout import ProjectLayoutPlanner

ROOT = Path(__file__).resolve().parents[1]


def fixture(tmp_path: Path):
    allowed = tmp_path / 'workspaces'
    allowed.mkdir()
    target = allowed / 'greenfield'
    intake = {
        'schema_id': 'SCHEMA-DEVPL-GSDLC-13-B-PROJECT-INTAKE-V2', 'schema_version':'2.0',
        'project_id':'greenfield-project', 'project_name':'Greenfield Project',
        'project_type':'agent-assisted-sdlc', 'entry_mode':'CREATE_NEW',
        'target_root':str(target),
        'business_need':'Construir una aplicación para registrar productos y ventas, primero como necesidad de negocio sin escoger un stack.',
        'technology_decision_status':'deferred-to-architecture',
        'stack':{'frontend':'undecided','backend':'undecided','database':'undecided'},
        'standards':['MIPSoftware','MIASI'],
        'provider':{'mode':'mock','provider_id':'mock'},
        'model_policy':{'baseline':'mock-no-api','local_model':'optional-opt-in','external_api':'approval-provenance-only'},
        'project_constraints':{'local_first':True,'cloud_required':False,'operator_project_writes_allowed':False},
        'restrictions':{'arbitrary_shell_allowed':False,'silent_network_allowed':False,'remote_git_execute_allowed':False},
    }
    source = EnvironmentDiscoveryService(ROOT, allowed_roots=(allowed,)).build_bootstrap_plan(intake)
    assert source.ok, source.to_dict()
    return target, intake, source.data['bootstrap_plan'], ProjectLayoutPlanner(ROOT, allowed_roots=(allowed,))


def mutate(plan, fn):
    p = copy.deepcopy(plan)
    fn(p)
    p['plan_hash'] = stable_sha256({k:v for k,v in p.items() if k!='plan_hash'})
    return p


def ids(result):
    return {x.id for x in result.findings}


def test_neutral_plan_is_repeatable_and_read_only(tmp_path):
    target, intake, plan, svc=fixture(tmp_path)
    first=svc.preview(intake=intake, bootstrap_plan=plan)
    second=svc.preview(intake=intake, bootstrap_plan=plan)
    assert first.ok and first.to_dict()==second.to_dict()
    data=first.data['layout']
    assert not target.exists()
    assert data['technology_profile']['profile_id'] is None
    assert data['technology_profile']['status']=='PENDING_ARCHITECTURE'
    assert data['documents']['content_creation']=='LAZY_GOVERNED'
    assert data['scaffold']['execution_enabled'] is False
    assert not data['writes_performed'] and not data['network_used']
    assert len(data['layout_hash'])==64
    assert 'docs/02_architecture' in {r['path'] for r in data['logical_paths']}
    assert not any(r['path'].startswith(('frontend/','backend/')) for r in data['logical_paths'])


def test_plan_is_not_a_second_executor(tmp_path):
    target, intake, plan, svc=fixture(tmp_path)
    assert svc.preview(intake=intake, bootstrap_plan=plan).ok
    assert not target.exists()
    assert not (target/'.git').exists()


def test_premature_stack_is_blocked(tmp_path):
    _, intake, plan, svc=fixture(tmp_path)
    intake['stack']['frontend']='react-typescript'
    assert 'LAYOUT_INTAKE_NOT_AUTHORIZED' in ids(svc.preview(intake=intake,bootstrap_plan=plan))


def test_modified_bootstrap_without_updated_hash_is_blocked(tmp_path):
    _, intake, plan, svc=fixture(tmp_path)
    plan['files'][0]['relative_path']='docs/other.md'
    assert 'LAYOUT_PLAN_HASH_DRIFT' in ids(svc.preview(intake=intake,bootstrap_plan=plan))


def test_unknown_target_is_blocked(tmp_path):
    _, intake, plan, svc=fixture(tmp_path)
    plan=mutate(plan,lambda o:o.update({'target_root':str(tmp_path/'different')}))
    assert 'LAYOUT_PLAN_INTAKE_DRIFT' in ids(svc.preview(intake=intake,bootstrap_plan=plan))

@pytest.mark.parametrize('relative', ['../escape','docs/../../escape','C:/evil','docs\\..\\evil','/absolute'])
def test_traversal_and_absolute_paths_denied(tmp_path,relative):
    _,intake,plan,svc=fixture(tmp_path)
    plan=mutate(plan,lambda o:o['directories'].append({'relative_path':relative,'absolute_path':str(tmp_path/'escape')}))
    outcome=svc.preview(intake=intake,bootstrap_plan=plan)
    assert not outcome.ok


def test_duplicate_paths_are_denied(tmp_path):
    _, intake, plan, svc=fixture(tmp_path)
    plan=mutate(plan,lambda p:p['files'].append(copy.deepcopy(p['files'][0])))
    assert 'LAYOUT_PREMATURE_TECH_ARTIFACT' in ids(svc.preview(intake=intake,bootstrap_plan=plan))


def test_technology_scaffold_does_not_sneak_in(tmp_path):
    _, intake, plan, svc=fixture(tmp_path)
    plan=mutate(plan,lambda p:p['files'].append({'relative_path':'frontend/package.json','absolute_path':str(Path(intake['target_root'])/'frontend/package.json')}))
    assert 'LAYOUT_PREMATURE_TECH_ARTIFACT' in ids(svc.preview(intake=intake,bootstrap_plan=plan))


def test_deps_venv_network_denied(tmp_path):
    _, intake, plan, svc=fixture(tmp_path)
    for key,change in [('network',lambda p:p['network'].update({'required_by_plan':True})),('venv',lambda p:p['venv'].update({'required':True})),('deps',lambda p:p['dependency_jobs'].append({'job_id':'npm-install'}))]:
        candidate=mutate(plan,change)
        assert 'LAYOUT_PREMATURE_EXECUTION' in ids(svc.preview(intake=intake,bootstrap_plan=candidate))


def test_non_planning_plan_denied(tmp_path):
    _, intake, plan, svc=fixture(tmp_path)
    plan=mutate(plan,lambda p:p.update({'execution_enabled':True}))
    assert 'LAYOUT_APPROVED_PLAN_REQUIRED' in ids(svc.preview(intake=intake,bootstrap_plan=plan))


def test_existing_original_intake_v1_not_confused_with_neutral(tmp_path):
    _, intake, plan, svc=fixture(tmp_path)
    intake['schema_id']='SCHEMA-DEVPL-GSDLC-03-A-PROJECT-INTAKE-V1'
    assert not svc.preview(intake=intake,bootstrap_plan=plan).ok


def test_sync_pointers_leave_legacy_records_untouched():
    registry=json.loads((ROOT/'.devpilot/docs_governance/source_registry.json').read_text())
    state=json.loads((ROOT/'.devpilot/project_state.json').read_text())
    # The active pointer advances with later R01 increments; historical content stays immutable.
    assert registry['current_micro_sprint']==state['current_micro_sprint']
    assert registry['current_micro_sprint'] in {
        'MP132-R01-14/PROJECT-LAYOUT', 'MP132-R01-15/M1-MATURITY-GATE',
        'MP132-R02-01/AUDIT-DOC-DRIFT', 'MP132-R02-02/LOCAL-MODEL-READINESS', 'MP132-R02-03/OLLAMA-REAL-CANDIDATE', 'MP132-R02-04/LM-STUDIO-PARITY', 'MP132-R02-05/PILOT-B-ENTRY-RESUME'
    }
    assert len(registry['documents'])==1752


def test_public_facade_still_exposes_existing_planner():
    source=(ROOT/'src/devpilot_core/application/project_entry_planning_service.py').read_text()
    assert 'def bootstrap_plan(' in source and 'def logical_layout_preview(' in source
