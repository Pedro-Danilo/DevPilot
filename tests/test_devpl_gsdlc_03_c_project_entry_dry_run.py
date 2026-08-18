from __future__ import annotations

import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

from devpilot_core.workspace.project_entry_dry_run import ProjectEntryDryRunService

ROOT=Path(__file__).resolve().parents[1]

def intake(target:Path,mode:str='CREATE_NEW',source:Path|None=None)->dict:
    payload=json.loads((ROOT/'evals/fixtures/gsdlc_03_a_inventory_sales_intake.valid.json').read_text(encoding='utf-8'))
    payload['project_id']='gsdlc03c-fixture';payload['project_name']='GSDLC 03-C Fixture';payload['target_root']=str(target);payload['entry_mode']=mode;payload.pop('git_source',None)
    if mode=='IMPORT_GIT': payload['git_source']={'kind':'local-path','location':str(source)}
    return payload

def fake_plan(service:ProjectEntryDryRunService, monkeypatch, mode:str, target:Path, source:Path|None=None):
    plan={'schema_id':'SCHEMA-DEVPL-GSDLC-03-B-BOOTSTRAP-PLAN-V1','entry_mode':mode,'plan_hash':'a'*64,'directories':[],'files':[],'git_operations':[],'venv':{'required':False},'dependency_jobs':[],'workspace_registration':{'operation_id':'workspace.register'},'network':{'required_by_plan':False},'approval':{'required_for_execute':True}}
    class R:
        ok=True;exit_code=0;findings=[];data={'bootstrap_plan':plan,'discovery':{'target':{'collision_state':'absent'},'git':{}}}
        def to_dict(self):return {}
    monkeypatch.setattr(service.planning,'build_bootstrap_plan',lambda payload:R())

def test_create_dry_run_is_zero_write_and_schema_valid(tmp_path:Path,monkeypatch):
    target=tmp_path/'new';service=ProjectEntryDryRunService(ROOT);fake_plan(service,monkeypatch,'CREATE_NEW',target)
    before=list(tmp_path.rglob('*')); result=service.dry_run(intake=intake(target)); assert result.ok
    dry=result.data['dry_run']; assert dry['entry_mode']=='CREATE_NEW';assert dry['safety']['writes_performed'] is False;assert dry['safety']['network_used'] is False;assert dry['execution']['enabled'] is False;assert not target.exists();assert list(tmp_path.rglob('*'))==before
    Draft202012Validator(json.loads((ROOT/'docs/schemas/project_entry_dry_run.schema.json').read_text())).validate(dry)

def test_open_preimage_change_blocks_revalidation(tmp_path:Path,monkeypatch):
    target=tmp_path/'open';target.mkdir();f=target/'README.md';f.write_text('one',encoding='utf-8');service=ProjectEntryDryRunService(ROOT);fake_plan(service,monkeypatch,'OPEN_EXISTING',target)
    first=service.dry_run(intake=intake(target,'OPEN_EXISTING'));assert first.ok;dry=first.data['dry_run'];f.write_text('two',encoding='utf-8')
    second=service.revalidate(intake=intake(target,'OPEN_EXISTING'),expected_plan_hash=dry['plan_hash'],expected_preimage_hash=dry['preimage_hash']);assert not second.ok;assert second.data['preimage_match'] is False

def test_local_import_preimage_uses_git_and_never_writes_target(tmp_path:Path,monkeypatch):
    source=tmp_path/'source';source.mkdir();subprocess.run(['git','init'],cwd=source,check=True,capture_output=True);subprocess.run(['git','config','user.email','devpilot@example.invalid'],cwd=source,check=True);subprocess.run(['git','config','user.name','DevPilot Test'],cwd=source,check=True);(source/'README.md').write_text('fixture',encoding='utf-8');subprocess.run(['git','add','README.md'],cwd=source,check=True);subprocess.run(['git','commit','-m','fixture'],cwd=source,check=True,capture_output=True)
    target=tmp_path/'target';service=ProjectEntryDryRunService(ROOT);fake_plan(service,monkeypatch,'IMPORT_GIT',target,source);result=service.dry_run(intake=intake(target,'IMPORT_GIT',source));assert result.ok;payload=result.data['dry_run']['preimage']['payload'];assert payload['git']['is_git'] is True;assert payload['git']['dirty'] is False;assert not target.exists()

def test_approval_preview_is_typed_and_not_requested(tmp_path:Path,monkeypatch):
    target=tmp_path/'new';service=ProjectEntryDryRunService(ROOT);fake_plan(service,monkeypatch,'CREATE_NEW',target);dry=service.dry_run(intake=intake(target)).data['dry_run'];preview=dry['approval_preview'];assert preview['preview_only'] is True;assert preview['request_created'] is False;assert preview['actor_authority']=='human-session';assert 'command' not in json.dumps(preview).lower()

def test_current_api_rbac_ui_successors_are_synchronized():
    api=json.loads((ROOT/'.devpilot/interfaces/api_route_contract_registry.json').read_text());rbac=json.loads((ROOT/'.devpilot/identity/server_rbac_policy_catalog.json').read_text());ui=json.loads((ROOT/'.devpilot/interfaces/ui_route_contract_registry.json').read_text())
    for rid in ['api.project-entry.dry-run','api.project-entry.revalidate']:
        assert any(r['route_id']==rid for r in api['routes']);assert any(r['route_id']==rid and r['human_session_required'] and not r['legacy_token_allowed'] for r in rbac['route_policies'])
    assert any(r['route_id']=='ui.project-entry-dry-run' and r['path']=='/project/entry' for r in ui['routes'])

def test_03b_historical_snapshots_remain_100_api_and_10_ui():
    api=json.loads((ROOT/'.devpilot/interfaces/api_route_contract_registry_gsdlc03b_at_close.json').read_text());rbac=json.loads((ROOT/'.devpilot/identity/server_rbac_policy_catalog_gsdlc03b_at_close.json').read_text());ui=json.loads((ROOT/'.devpilot/interfaces/ui_route_contract_registry_gsdlc03b_at_close.json').read_text());assert len(api['routes'])==100;assert len(rbac['route_policies'])==100;assert len(ui['routes'])==10


def test_remote_import_is_plan_only_and_never_contacts_network(tmp_path:Path,monkeypatch):
    target=tmp_path/'remote-target';service=ProjectEntryDryRunService(ROOT)
    plan={'schema_id':'SCHEMA-DEVPL-GSDLC-03-B-BOOTSTRAP-PLAN-V1','entry_mode':'IMPORT_GIT','plan_hash':'b'*64,'directories':[],'files':[],'git_operations':[{'operation_id':'git.clone.remote'}],'venv':{'required':False},'dependency_jobs':[],'workspace_registration':{'operation_id':'workspace.register'},'network':{'required_by_plan':True,'remote_git_disabled_by_default':True},'approval':{'required_for_execute':True}}
    class R:
        ok=True;exit_code=0;findings=[];data={'bootstrap_plan':plan,'discovery':{'target':{'collision_state':'absent'},'git':{'source':'https://example.invalid/repo.git'}}}
        def to_dict(self):return {}
    monkeypatch.setattr(service.planning,'build_bootstrap_plan',lambda payload:R())
    payload=intake(target,'IMPORT_GIT');payload['git_source']={'kind':'remote-url','location':'https://example.invalid/repo.git'}
    result=service.dry_run(intake=payload);assert result.ok;dry=result.data['dry_run'];assert dry['preimage']['payload']['source_kind']=='remote-url';assert dry['preimage']['payload']['network_contacted'] is False;assert dry['safety']['network_used'] is False;assert dry['safety']['remote_git_contacted'] is False;assert dry['execution']['enabled'] is False;assert not target.exists()


def test_project_entry_ui_requires_target_and_reports_403_as_policy_not_token() -> None:
    view=(ROOT/'ui/web/src/pages/ProjectEntryDryRunView.ts').read_text(encoding='utf-8')
    client=(ROOT/'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    assert "form.noValidate=true" in view
    assert "Ruta destino / workspace es obligatoria" in view
    assert "PROJECT_INTAKE_TARGET_REQUIRED" in (ROOT/'src/devpilot_core/workspace/project_entry_contracts.py').read_text(encoding='utf-8')
    assert "Solicitud bloqueada por una política, validación o autorización de DevPilot." in client
    assert "token local faltante o inválido" not in client
