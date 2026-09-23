from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from devpilot_core.application.guided_sdlc_service import GuidedSDLCApplicationService
from devpilot_core.workspace.runtime_project_context import (
    ALLOWED_ROOTS_ENV,
    GUIDED_REGISTRY_ENV,
    UI_ACTIVE_ROOT_ENV,
    activate_project_runtime_context,
    bind_persisted_project_runtime,
)

ROOT = Path(__file__).resolve().parents[1]


def _project(workspace: Path) -> None:
    (workspace / '.devpilot').mkdir(parents=True)
    (workspace / '.devpilot/project.yaml').write_text(
        "schema_version: '1.0'\nproject_id: inventory-sales-local-greenfield\nproject_name: \"Inventory Sales Local Greenfield\"\ntechnology_decision_status: deferred-to-architecture\n",
        encoding='utf-8',
    )
    (workspace / '.devpilot/workspace-registration.json').write_text(json.dumps({
        'schema_id':'devpilot.gsdlc03d.workspace_registration.v1',
        'workspace_id':'inventory-sales-local-greenfield',
        'project_id':'inventory-sales-local-greenfield',
        'root_path':str(workspace.resolve()),
        'status':'registered-local',
        'default_effect':'deny',
        'network_allowed':False,
        'external_api_allowed':False,
        'registration_scope':'target-local',
    }, indent=2) + '\n', encoding='utf-8')
    subprocess.run(['git','init'],cwd=workspace,check=True,capture_output=True)
    subprocess.run(['git','config','user.name','DevPilot Test'],cwd=workspace,check=True)
    subprocess.run(['git','config','user.email','devpilot-test@example.invalid'],cwd=workspace,check=True)
    (workspace/'README.md').write_text('# Greenfield\n',encoding='utf-8')
    subprocess.run(['git','add','.'],cwd=workspace,check=True)
    subprocess.run(['git','commit','-m','initial'],cwd=workspace,check=True,capture_output=True)


def test_runtime_context_activation_materializes_platform_state_without_project_mutation(tmp_path: Path, monkeypatch) -> None:
    if shutil.which('git') is None:
        return
    platform=tmp_path/'platform'; platform.mkdir()
    (platform/'.devpilot/gsdlc').mkdir(parents=True)
    shutil.copy2(ROOT/'.devpilot/gsdlc/workflow_transition_catalog.json', platform/'.devpilot/gsdlc/workflow_transition_catalog.json')
    workspace=tmp_path/'workspaces'/'inventory-sales-local-greenfield'; workspace.mkdir(parents=True)
    _project(workspace)
    before=subprocess.run(['git','status','--porcelain','--untracked-files=all'],cwd=workspace,check=True,capture_output=True,text=True).stdout
    result=activate_project_runtime_context(platform,workspace,allowed_roots=(workspace,))
    assert result['status']=='PASS' and result['engineering_state_created'] is True
    assert result['project_source_mutations']==0
    assert Path(result['runtime_registry_path']).is_file()
    assert Path(result['engineering_state_path']).is_file()
    after=subprocess.run(['git','status','--porcelain','--untracked-files=all'],cwd=workspace,check=True,capture_output=True,text=True).stdout
    assert before==after==''

    monkeypatch.delenv(ALLOWED_ROOTS_ENV,raising=False)
    monkeypatch.delenv(UI_ACTIVE_ROOT_ENV,raising=False)
    monkeypatch.delenv(GUIDED_REGISTRY_ENV,raising=False)
    binding=bind_persisted_project_runtime(platform)
    try:
        assert binding.applied[ALLOWED_ROOTS_ENV]==str(workspace.resolve())
        assert binding.applied[UI_ACTIVE_ROOT_ENV]==str(workspace.resolve())
        assert Path(binding.applied[GUIDED_REGISTRY_ENV]).resolve()==Path(result['runtime_registry_path']).resolve()
        status=GuidedSDLCApplicationService(platform).project_status_primary(workspace_id=None,observed_at_utc='2026-09-22T23:30:00Z')
        assert status.ok is True, status.to_dict()
        assert status.data['workspace_id']=='inventory-sales-local-greenfield'
        assert status.data['project_status']['project_id']=='inventory-sales-local-greenfield'
        assert status.data['ui_state'] not in {'EMPTY','UNKNOWN'}
        assert status.data['read_only'] is True and status.data['mutations_performed'] is False
        assert status.data['project_status']['phase']=='NOT_STARTED'
        assert status.data['project_status']['current_step']=='idea-intake'
    finally:
        binding.restore()



def test_runtime_registry_upserts_without_discarding_other_workspaces(tmp_path: Path) -> None:
    if shutil.which('git') is None:
        return
    platform=tmp_path/'platform'; platform.mkdir()
    (platform/'.devpilot/gsdlc').mkdir(parents=True)
    shutil.copy2(ROOT/'.devpilot/gsdlc/workflow_transition_catalog.json', platform/'.devpilot/gsdlc/workflow_transition_catalog.json')
    workspace=tmp_path/'workspaces'/'inventory-sales-local-greenfield'; workspace.mkdir(parents=True)
    _project(workspace)
    registry=platform/'outputs/runtime/active_workspace_registry.json'; registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps({
        'schema_version':'1.0','created_by':'existing-test','active_workspace_id':'other',
        'defaults':{},'security':{},
        'workspaces':[{'workspace_id':'other','project_id':'other','name':'Other','path':str((tmp_path/'other').resolve())}]
    }, indent=2)+'\n',encoding='utf-8')
    result=activate_project_runtime_context(platform,workspace,allowed_roots=(workspace,))
    assert result['status']=='PASS'
    payload=json.loads(registry.read_text(encoding='utf-8'))
    assert payload['active_workspace_id']=='inventory-sales-local-greenfield'
    assert {row['workspace_id'] for row in payload['workspaces']}=={'other','inventory-sales-local-greenfield'}
    assert payload['created_by']=='existing-test'

def test_standard_api_launcher_loads_persisted_runtime_context_contract() -> None:
    cli=(ROOT/'src/devpilot_core/cli.py').read_text(encoding='utf-8')
    assert 'bind_persisted_project_runtime(root)' in cli
    assert 'runtime_project_context_bound' in cli
    assert 'DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT' not in cli[cli.index('def api_serve_command'):cli.index('def api_token_command')]
