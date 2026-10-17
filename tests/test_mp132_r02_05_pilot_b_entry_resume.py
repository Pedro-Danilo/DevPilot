"""R02-05: verify B0 identity and server-authoritative recovery, without pilot writes."""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path
import pytest
from devpilot_core.workspace.runtime_project_context import (
    activate_project_runtime_context, bind_persisted_project_runtime,
    ALLOWED_ROOTS_ENV, GUIDED_REGISTRY_ENV, UI_ACTIVE_ROOT_ENV,
)
from devpilot_core.application.guided_sdlc_service import GuidedSDLCApplicationService

ROOT = Path(__file__).resolve().parents[1]

def make_project(path: Path, project_id: str) -> None:
    path.mkdir(parents=True)
    (path / '.devpilot').mkdir()
    (path / '.devpilot/project.yaml').write_text(
        f"schema_version: '1.0'\nproject_id: {project_id}\nproject_name: {project_id}\ntechnology_decision_status: deferred-to-architecture\n", encoding='utf-8')
    (path / '.devpilot/workspace-registration.json').write_text(json.dumps({
        'schema_id': 'devpilot.gsdlc03d.workspace_registration.v1',
        'workspace_id': project_id, 'project_id': project_id, 'root_path': str(path.resolve()),
        'status': 'registered-local', 'registration_scope': 'target-local',
        'network_allowed': False, 'external_api_allowed': False,
    }), encoding='utf-8')
    subprocess.run(['git', 'init', '-q'], cwd=path, check=True)
    subprocess.run(['git', 'config', 'user.email', 'fixture@example.invalid'], cwd=path, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Fixture'], cwd=path, check=True)
    subprocess.run(['git', 'add', '--', '.devpilot/project.yaml', '.devpilot/workspace-registration.json'], cwd=path, check=True)
    subprocess.run(['git', 'commit', '-qm', 'neutral fixture'], cwd=path, check=True)

@pytest.mark.skipif(shutil.which('git') is None, reason='git missing')
def test_two_workspace_restart_server_authority_and_no_project_mutation(tmp_path: Path, monkeypatch) -> None:
    platform=tmp_path/'platform'; (platform/'.devpilot/gsdlc').mkdir(parents=True)
    shutil.copy2(ROOT/'.devpilot/gsdlc/workflow_transition_catalog.json', platform/'.devpilot/gsdlc/workflow_transition_catalog.json')
    first=tmp_path/'workspaces/inventory-sales-local-greenfield'
    pilot=tmp_path/'workspaces/pilot-b-wellness'
    make_project(first, 'inventory-sales-local-greenfield'); make_project(pilot, 'pilot-b-wellness')
    before=subprocess.run(['git', 'status', '--porcelain'], cwd=pilot, capture_output=True, text=True, check=True).stdout
    activate_project_runtime_context(platform, first, allowed_roots=(first,pilot))
    result=activate_project_runtime_context(platform, pilot, allowed_roots=(first,pilot))
    assert result['engineering_state_created'] is True and result['project_source_mutations']==0
    registry=platform/'outputs/runtime/active_workspace_registry.json'
    payload=json.loads(registry.read_text())
    assert payload['active_workspace_id']=='pilot-b-wellness'
    assert {x['workspace_id'] for x in payload['workspaces']}=={'inventory-sales-local-greenfield','pilot-b-wellness'}
    stored=registry.read_bytes()
    for name in (ALLOWED_ROOTS_ENV, GUIDED_REGISTRY_ENV, UI_ACTIVE_ROOT_ENV): monkeypatch.delenv(name, raising=False)
    # Each context manager models a new foreground API server session.
    for _ in range(2):
        binding=bind_persisted_project_runtime(platform)
        try:
            assert Path(binding.applied[UI_ACTIVE_ROOT_ENV])==pilot.resolve()
            projection=GuidedSDLCApplicationService(platform).project_status_primary(workspace_id=None,observed_at_utc='2026-10-16T16:00:00Z')
            assert projection.ok is True, projection.to_dict()
            assert projection.data['project_status']['project_id']=='pilot-b-wellness'
            assert projection.data['read_only'] is True
        finally: binding.restore()
    assert registry.read_bytes()==stored
    assert before==subprocess.run(['git','status','--porcelain'],cwd=pilot,capture_output=True,text=True,check=True).stdout==''
    again=activate_project_runtime_context(platform, pilot, allowed_roots=(first,pilot))
    assert again['engineering_state_created'] is False

@pytest.mark.skipif(shutil.which('git') is None, reason='git missing')
def test_external_root_rejected_by_pathguard(tmp_path:Path) -> None:
    platform=tmp_path/'platform';platform.mkdir()
    pilot=tmp_path/'other-root/pilot-b-wellness';make_project(pilot,'pilot-b-wellness')
    with pytest.raises(RuntimeError, match='blocked'):
        activate_project_runtime_context(platform,pilot,allowed_roots=(tmp_path/'allowed',))
    assert not (platform/'outputs/runtime/active_workspace_registry.json').exists()

def test_home_is_server_labelled_and_never_promotes_from_browser_state() -> None:
    s=(ROOT/'ui/web/src/components/ProjectHomeEntryPanel.ts').read_text()
    assert 'projectStatus()' in s and 'scope.has(workspaceId)' in s
    assert 'read_only === true' in s and 'actor_neutral === true' in s
    assert 'data-server-active-project' in s or 'dataset.serverActiveProject' in s
    assert 'recover_project_context=server-active' in s
    assert "GSDLC-03-E · inicio de proyecto" not in s
    assert 'activateProjectJourney(' not in s

def test_entry_is_business_first_neutral_and_no_demo_defaults() -> None:
    s=(ROOT/'ui/web/src/pages/ProjectEntryDryRunView.ts').read_text()
    assert "inputField('Project ID','project-id','')" in s
    assert "inputField('Nombre','project-name','')" in s
    assert "'deferred-to-architecture'" in s
    assert "'mock-no-api'" in s and 'businessNeedValue.length<20' in s
    assert 'projectEntryB0Note' in s and 'appendProjectStatusCta' in s


def test_active_pointer_and_contract_historical_scope() -> None:
    p=json.loads((ROOT/'.devpilot/project_state.json').read_text())
    r=json.loads((ROOT/'.devpilot/docs_governance/source_registry.json').read_text())
    assert p['current_micro_sprint']==r['current_micro_sprint']=='MP132-R02-05/PILOT-B-ENTRY-RESUME'
    assert p['next_micro_sprint']==r['next_micro_sprint']=='R02_06_NOT_AUTHORIZED'
    assert p['current_phase']==r['current_phase']=='DEVPL-MP-SUCCESSOR-132/R02-PRODUCT-DEFINITION'
    assert len(r['documents'])==r['summary']['documents_total'] >= 1752  # R02-05 historical minimum; later ADRs are additive
    assert p['external_api_allowed'] is False
