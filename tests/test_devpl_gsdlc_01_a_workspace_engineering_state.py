from __future__ import annotations

import json
import os
from pathlib import Path

import jsonschema
import pytest

from devpilot_core.guided_sdlc import (
    EngineeringLifecycleStatus,
    WorkspaceEngineeringState,
    WorkspaceEngineeringStateConflict,
    WorkspaceEngineeringStateMigrator,
    WorkspaceEngineeringStateRepository,
    WorkspaceEngineeringStateStoreError,
    WorkspaceRegistryBindingResolver,
)
from devpilot_core.guided_sdlc.migration import WorkspaceEngineeringStateMigrationError
from devpilot_core.guided_sdlc.models import MIPSoftwarePhase, WorkspaceEngineeringStateError

ROOT=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((ROOT/"docs/schemas/workspace_engineering_state.schema.json").read_text(encoding="utf-8"))
FIXTURES=ROOT/"tests/fixtures/gsdlc01a"


def load_fixture(name:str)->dict:
    return json.loads((FIXTURES/name).read_text(encoding="utf-8"))


def make_platform(tmp_path:Path, monkeypatch:pytest.MonkeyPatch, *, workspace_id:str="ws-1", external:bool=False):
    platform=tmp_path/"platform"; platform.mkdir(); (platform/".gitignore").write_text("outputs/\n",encoding="utf-8")
    workspace=(tmp_path/"managed") if external else platform
    if external: workspace.mkdir()
    registry_dir=platform/".devpilot/workspaces"; registry_dir.mkdir(parents=True)
    entry={
      "workspace_id":workspace_id,"project_id":"project-1","name":"Test","path":str(workspace) if external else ".",
      "path_mode":"absolute-local" if external else "relative-to-registry-root","status":"active","risk_level":"medium",
      "default_effect":"deny","state_path":".devpilot/devpilot.db","reports_path":"outputs/reports","traces_path":"outputs/traces",
      "secrets_path":".devpilot/providers.yaml","secret_policy":"reference-only","network_allowed":False,"external_api_allowed":False,
      "observability_required":True,"eval_required":True,"registered_at":"2026-08-16T00:00:00Z","updated_at":"2026-08-16T00:00:00Z"
    }
    registry={"schema_version":"1.0","created_by":"FUNC-SPRINT-94","updated_at":"2026-08-16T00:00:00Z","active_workspace_id":workspace_id,
      "defaults":{"deny_unregistered_workspaces":True,"cross_workspace_state_reads":False,"secret_sharing_allowed":False,"portfolio_status_read_only":True},
      "security":{"network_used":False,"external_api_used":False,"shell_used":False,"remote_execution_used":False,"mutations_performed":False,"secrets_read":False},"workspaces":[entry]}
    (registry_dir/"workspace_registry.json").write_text(json.dumps(registry),encoding="utf-8")
    if external: monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS",str(workspace))
    return platform,workspace


def new_state(repo:WorkspaceEngineeringStateRepository, workspace_id:str="ws-1"):
    binding=repo.binding(workspace_id)
    return WorkspaceEngineeringState.new(workspace_id=workspace_id,project_id=binding.project_id,workspace_root_fingerprint=binding.root_fingerprint,created_at_utc="2026-08-16T00:00:00Z")


def test_01_a_schema_accepts_new_revalidation_and_released_fixtures():
    for name in ["workspace_engineering_state_new.valid.json","workspace_engineering_state_revalidation.valid.json","workspace_engineering_state_released.valid.json"]:
        jsonschema.Draft202012Validator(SCHEMA).validate(load_fixture(name))


@pytest.mark.parametrize("field,bad",[("schema_version","9.9"),("workspace_id","../escape"),("sequence",-1),("lifecycle_status","DONE"),("phase","MAGIC")])
def test_01_a_schema_negative_field_type_enum(field,bad):
    payload=load_fixture("workspace_engineering_state_new.valid.json"); payload[field]=bad
    with pytest.raises(jsonschema.ValidationError): jsonschema.Draft202012Validator(SCHEMA).validate(payload)


def test_01_a_lifecycle_vocabulary_covers_new_to_released_and_revalidation():
    values={x.value for x in EngineeringLifecycleStatus}
    assert {"NEW","IN_PROGRESS","READY_FOR_RELEASE","RELEASED","REVALIDATION_REQUIRED"}.issubset(values)
    phases={x.value for x in MIPSoftwarePhase}
    assert {"INTAKE","REQUIREMENTS","IMPLEMENTATION","VERIFICATION","RELEASE","RETIREMENT"}.issubset(phases)


def test_01_a_revalidation_lifecycle_requires_revalidation_metadata():
    payload=load_fixture("workspace_engineering_state_revalidation.valid.json"); payload["revalidation"]={"status":"NOT_REQUIRED","reason_codes":[]}
    with pytest.raises((WorkspaceEngineeringStateError,ValueError)):
        WorkspaceEngineeringState.from_payload(payload)
    with pytest.raises(jsonschema.ValidationError): jsonschema.Draft202012Validator(SCHEMA).validate(payload)


def test_01_a_deterministic_serialization_and_fingerprint():
    state=WorkspaceEngineeringState.from_payload(load_fixture("workspace_engineering_state_released.valid.json"))
    assert state.canonical_json()==state.canonical_json()
    assert state.fingerprint()==state.fingerprint()
    assert len(state.fingerprint())==64


def test_01_a_migrator_v1_is_idempotent_and_unknown_version_blocks():
    payload=load_fixture("workspace_engineering_state_new.valid.json")
    migrator=WorkspaceEngineeringStateMigrator()
    assert migrator.migrate(payload)==WorkspaceEngineeringState.from_payload(payload).to_payload()
    payload["schema_version"]="2.0"
    with pytest.raises(WorkspaceEngineeringStateMigrationError): migrator.migrate(payload)


def test_01_a_repository_roundtrip_survives_restart(tmp_path,monkeypatch):
    platform,_=make_platform(tmp_path,monkeypatch)
    repo=WorkspaceEngineeringStateRepository(platform)
    state=new_state(repo); path=repo.save(state)
    assert path.relative_to(platform).as_posix()=="outputs/workspaces/ws-1/engineering_state.json"
    restarted=WorkspaceEngineeringStateRepository(platform)
    assert restarted.load("ws-1").to_payload()==state.to_payload()


def test_01_a_optimistic_concurrency_blocks_lost_update(tmp_path,monkeypatch):
    platform,_=make_platform(tmp_path,monkeypatch); repo=WorkspaceEngineeringStateRepository(platform); state=new_state(repo); repo.save(state)
    payload=state.to_payload(); payload.update(sequence=1,updated_at_utc="2026-08-16T00:01:00Z",lifecycle_status="IN_PROGRESS",phase="INTAKE")
    successor=WorkspaceEngineeringState.from_payload(payload)
    with pytest.raises(WorkspaceEngineeringStateConflict): repo.save(successor,expected_sequence=999)
    repo.save(successor,expected_sequence=0)
    assert repo.load("ws-1").sequence==1


def test_01_a_unregistered_workspace_is_denied(tmp_path,monkeypatch):
    platform,_=make_platform(tmp_path,monkeypatch); repo=WorkspaceEngineeringStateRepository(platform)
    with pytest.raises(WorkspaceEngineeringStateStoreError): repo.load("not-registered")


def test_01_a_external_workspace_requires_explicit_allowlist(tmp_path,monkeypatch):
    platform,workspace=make_platform(tmp_path,monkeypatch,external=True)
    monkeypatch.delenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS",raising=False)
    resolver=WorkspaceRegistryBindingResolver(platform)
    with pytest.raises(Exception): resolver.resolve("ws-1")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS",str(workspace))
    resolver=WorkspaceRegistryBindingResolver(platform)
    assert resolver.resolve("ws-1").root==workspace.resolve()


def test_01_a_symlink_workspace_root_is_denied(tmp_path,monkeypatch):
    if not hasattr(os,"symlink"): pytest.skip("symlink unavailable")
    platform,workspace=make_platform(tmp_path,monkeypatch,external=True)
    target=tmp_path/"target"; target.mkdir(); link=tmp_path/"link"
    try: link.symlink_to(target,target_is_directory=True)
    except OSError: pytest.skip("symlink creation not permitted")
    reg=json.loads((platform/".devpilot/workspaces/workspace_registry.json").read_text()); reg["workspaces"][0]["path"]=str(link)
    (platform/".devpilot/workspaces/workspace_registry.json").write_text(json.dumps(reg))
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS",os.pathsep.join([str(workspace),str(link),str(target)]))
    with pytest.raises(Exception): WorkspaceRegistryBindingResolver(platform).resolve("ws-1")


def test_01_a_store_symlink_pivot_is_denied(tmp_path,monkeypatch):
    platform,_=make_platform(tmp_path,monkeypatch); outside=tmp_path/"outside"; outside.mkdir(); parent=platform/"outputs/workspaces"; parent.mkdir(parents=True)
    link=parent/"ws-1"
    try: link.symlink_to(outside,target_is_directory=True)
    except OSError: pytest.skip("symlink creation not permitted")
    repo=WorkspaceEngineeringStateRepository(platform)
    with pytest.raises(WorkspaceEngineeringStateStoreError): repo.state_path("ws-1")


def test_01_a_secret_like_material_is_rejected(tmp_path,monkeypatch):
    platform,_=make_platform(tmp_path,monkeypatch); repo=WorkspaceEngineeringStateRepository(platform); state=new_state(repo)
    payload=state.to_payload(); payload["blockers"]=[{"blocker_id":"b","severity":"S2","reason_code":"Bearer supersecrettokenvalue","source_ref":None}]
    with pytest.raises(WorkspaceEngineeringStateError): WorkspaceEngineeringState.from_payload(payload)


def test_01_a_corrupt_partial_write_does_not_become_new_state(tmp_path,monkeypatch):
    platform,_=make_platform(tmp_path,monkeypatch); repo=WorkspaceEngineeringStateRepository(platform); state=new_state(repo); path=repo.save(state); path.write_text('{"schema_id":',encoding='utf-8')
    with pytest.raises(WorkspaceEngineeringStateStoreError): repo.load("ws-1")


def test_01_a_atomic_write_failure_preserves_previous_record(tmp_path,monkeypatch):
    platform,_=make_platform(tmp_path,monkeypatch); repo=WorkspaceEngineeringStateRepository(platform); original=new_state(repo); path=repo.save(original); before=path.read_bytes()
    payload=original.to_payload(); payload.update(sequence=1,updated_at_utc="2026-08-16T00:01:00Z",lifecycle_status="IN_PROGRESS",phase="INTAKE")
    successor=WorkspaceEngineeringState.from_payload(payload)
    import devpilot_core.guided_sdlc.repository as module
    def boom(src,dst): raise OSError("simulated atomic replace failure")
    monkeypatch.setattr(module.os,"replace",boom)
    with pytest.raises(OSError): repo.save(successor,expected_sequence=0)
    assert path.read_bytes()==before
    assert not list(path.parent.glob("*.tmp"))


def test_01_a_state_contract_has_no_platform_or_runtime_coupling():
    for rel in ["src/devpilot_core/guided_sdlc/models.py","src/devpilot_core/guided_sdlc/repository.py","src/devpilot_core/guided_sdlc/migration.py"]:
        text=(ROOT/rel).read_text(encoding="utf-8")
        assert "project_state.json" not in text
        assert "devpilot.db" not in text
        assert "agent_sessions" not in text
        assert "approval_id" not in text


def test_01_a_default_store_is_gitignored_and_does_not_touch_managed_workspace(tmp_path,monkeypatch):
    platform,workspace=make_platform(tmp_path,monkeypatch,external=True); before=set(workspace.rglob("*")); repo=WorkspaceEngineeringStateRepository(platform); repo.save(new_state(repo)); after=set(workspace.rglob("*"))
    assert before==after
    assert "outputs/" in (platform/".gitignore").read_text()


def test_01_a_approved_backlog_and_governance_successor_fields_are_present():
    backlog=(ROOT/"docs/backlogs/DEVPL-GSDLC-01_guided_sdlc_state_engine_and_project_status_v1_2_0_APPROVED.md").read_text(encoding="utf-8")
    assert 'status: "approved"' in backlog and 'source_git_commit: "3d7fda44d7ab5feefadd2eb4a7b9d20680eb1b5d"' in backlog
    state=json.loads((ROOT/".devpilot/project_state.json").read_text())
    assert state["gsdlc_01_a_status"]=="pass-candidate/pending-owner-adjudication"
    assert state["gsdlc_01_b_authorized"] is False
    assert state["post_h_eval_002_execution_status"]=="paused-before-02-b"
    assert state["gsdlc_runtime_implemented"] is False  # closed GSDLC-00 historical/global flag is not rewritten in 01-A
