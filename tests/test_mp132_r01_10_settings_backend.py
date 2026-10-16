from __future__ import annotations

import dataclasses
import sqlite3
from pathlib import Path

import pytest

from devpilot_core.application.persistent_settings import (
    PersistentSettingsStore, SettingsDenied, SettingsConflict,
)
from devpilot_core.application.services import ApplicationService
from devpilot_core.identity.auth_models import AuthenticatedPrincipal, SessionContext


def owner(workspace="w1"):
    p = AuthenticatedPrincipal("actor1", "owner", "Owner", ("owner",), (workspace,))
    s = SessionContext(p, "now", "now", "later", 1000, 0)
    return p, s


def store(tmp_path):
    return PersistentSettingsStore(tmp_path)


def write(t, key="generation.max_output_tokens", value=1024, scope="workspace", scope_id="w1", rev=0, **kwargs):
    p, s = owner()
    return t.apply(scope=scope, scope_id=scope_id, key=key, value=value, expected_revision=rev,
                   principal=p, session=s, approve_write=True, **kwargs)


def test_default_read_no_database(tmp_path):
    t = store(tmp_path)
    result = t.effective(key="generation.max_output_tokens", workspace_id="w1")
    assert result["effective_value"] == 512 and result["origin"] == "builtin"
    assert not t.database.exists()


def test_persist_restart_effective_origin(tmp_path):
    t = store(tmp_path)
    assert write(t)["revision"] == 1
    again = store(tmp_path).effective(key="generation.max_output_tokens", workspace_id="w1")
    assert again["effective_value"] == 1024 and again["origin"] == "workspace:w1" and again["revision"] == 1


def test_platform_workspace_project_order(tmp_path):
    t = store(tmp_path)
    write(t, value=1000, scope="platform", scope_id="platform")
    assert t.effective(key="generation.max_output_tokens", workspace_id="w1")["effective_value"] == 1000
    write(t, value=1400)
    write(t, value=1800, scope="project", scope_id="p1", workspace_id="w1")
    assert t.effective(key="generation.max_output_tokens", workspace_id="w1", project_id="p1")["effective_value"] == 1800
    assert t.effective(key="generation.max_output_tokens", workspace_id="w2")["effective_value"] == 1000
    assert t.effective(key="generation.max_output_tokens", workspace_id="w1", project_id="p2")["effective_value"] == 1400


def test_plan_does_not_mutate(tmp_path):
    t = store(tmp_path)
    plan = t.plan(scope="workspace", scope_id="w1", key="ui.detail_level", value="expert", expected_revision=0)
    assert plan.permitted and not plan.write_performed and not t.database.exists()


def test_revision_conflict_no_new_revision(tmp_path):
    t = store(tmp_path)
    write(t)
    with pytest.raises(SettingsConflict, match="REVISION_CONFLICT"):
        write(t, value=2048, rev=0)
    assert t.effective(key="generation.max_output_tokens", workspace_id="w1")["revision"] == 1


def test_idempotent_same_value_same_revision(tmp_path):
    t = store(tmp_path)
    write(t)
    assert write(t, rev=1)["status"] == "NO_OP"
    assert t.effective(key="generation.max_output_tokens", workspace_id="w1")["revision"] == 1


def test_rollback_is_successor_and_historic_preserved(tmp_path):
    t = store(tmp_path)
    write(t, value=1100)
    write(t, value=2000, rev=1)
    p,s=owner()
    result=t.rollback(scope="workspace",scope_id="w1",key="generation.max_output_tokens",target_revision=1,expected_revision=2,principal=p,session=s,approve_write=True)
    assert result["revision"]==3 and result["value"]==1100
    conn=sqlite3.connect(t.database)
    assert conn.execute("select revision,value_json from setting_versions order by revision").fetchall()==[(1,'1100'),(2,'2000'),(3,'1100')]
    conn.close()


def test_rollback_without_approval_denied(tmp_path):
    t=store(tmp_path);write(t);p,s=owner()
    with pytest.raises(SettingsDenied,match="EXPLICIT_WRITE_APPROVAL_REQUIRED"):
        t.rollback(scope="workspace",scope_id="w1",key="generation.max_output_tokens",target_revision=1,expected_revision=1,principal=p,session=s)

@pytest.mark.parametrize("key,val", [
    ("governance.external_network", "ALLOW"),
    ("governance.tool_execution", "YES"),
    ("generation.default_route", "external"),
    ("generation.max_output_tokens", True),
    ("generation.max_output_tokens", -1),
    ("generation.max_output_tokens", 999999),
    ("secrets.api_key", "abc123"),
    ("provider.api_key_env", "abc123"),
    ("ui.detail_level", {"secret":"abc"}),
])
def test_deny_unsafe_values(tmp_path,key,val):
    t=store(tmp_path)
    with pytest.raises(SettingsDenied):
        t.plan(scope="workspace",scope_id="w1",key=key,value=val,expected_revision=0)
    assert not t.database.exists()


def test_policy_floor_always_deny(tmp_path):
    t=store(tmp_path)
    assert write(t,key="governance.external_network",value="DENY")["status"] == "PERSISTED_PLAN_ONLY"
    assert t.effective(key="governance.external_network",workspace_id="w1")["effective_value"] == "DENY"
    assert t.effective(key="governance.external_network",workspace_id="w1")["origin"] == "builtin"


def test_no_execution_on_local_route(tmp_path):
    t=store(tmp_path)
    write(t,key="generation.default_route",value="local")
    assert t.effective(key="generation.default_route",workspace_id="w1")["effective_value"] == "local"
    assert t.effective(key="generation.default_route",workspace_id="w1")["runtime_modified"] is False
    assert not (tmp_path/".devpilot"/"runtime"/"provider_enablement").exists()


def test_owner_and_session_required(tmp_path):
    t=store(tmp_path);p,s=owner()
    fake=dataclasses.replace(p,roles=("viewer",)); viewer=dataclasses.replace(s,principal=fake)
    for pr,session in [(fake,viewer),(p,viewer),(None,None)]:
        with pytest.raises(SettingsDenied):
            t.apply(scope="workspace",scope_id="w1",key="ui.detail_level",value="expert",expected_revision=0,principal=pr,session=session,approve_write=True)
    assert not t.database.exists()


def test_scope_workspaces_and_project(tmp_path):
    t=store(tmp_path);p,s=owner()
    for scope,scope_id,workspace_id in [("workspace","w2",None),("project","p1",None),("project","p1","w2")]:
        with pytest.raises(SettingsDenied):
            t.apply(scope=scope,scope_id=scope_id,key="ui.detail_level",value="expert",expected_revision=0,principal=p,session=s,approve_write=True,workspace_id=workspace_id)
    assert not t.database.exists()


def test_invalid_scope_paths(tmp_path):
    t=store(tmp_path)
    for scope,scope_id in [("workspace","../outside"),("project",""),("platform","other"),("root","root")]:
        with pytest.raises(SettingsDenied):
            t.plan(scope=scope,scope_id=scope_id,key="ui.detail_level",value="expert",expected_revision=0)


def test_empty_state_and_unknown_revision(tmp_path):
    t=store(tmp_path);p,s=owner()
    with pytest.raises(SettingsConflict,match="REVISION_CONFLICT"):
        t.rollback(scope="workspace",scope_id="w1",key="ui.detail_level",target_revision=4,expected_revision=1,principal=p,session=s,approve_write=True)


def test_facade_service_exposes_no_runtime_mutations(tmp_path):
    app=ApplicationService(tmp_path)
    assert app.settings_effective(key="ui.detail_level")["effective_value"] == "guided"
    assert app.settings_persistent_plan(scope="platform",scope_id="platform",key="ui.detail_level",value="expert",expected_revision=0)["permitted"]
    assert not (tmp_path/".devpilot"/"runtime"/"settings").exists()


def test_explicit_approval_required_no_database_created(tmp_path):
    t=store(tmp_path);p,s=owner()
    with pytest.raises(SettingsDenied,match="EXPLICIT_WRITE_APPROVAL_REQUIRED"):
        t.apply(scope="workspace",scope_id="w1",key="ui.detail_level",value="expert",expected_revision=0,principal=p,session=s)
    assert not t.database.exists()


def test_two_independent_writer_instances_conflict(tmp_path):
    import concurrent.futures
    t1=store(tmp_path);t2=store(tmp_path)
    p,s=owner()
    def attempt(t, value):
        try:
            return t.apply(scope="workspace",scope_id="w1",key="generation.max_output_tokens",value=value,expected_revision=0,principal=p,session=s,approve_write=True)["status"]
        except SettingsConflict:
            return "REVISION_CONFLICT"
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(attempt,t1,100),pool.submit(attempt,t2,200)]
        statuses=[f.result() for f in futures]
    assert sorted(statuses)==["PERSISTED_PLAN_ONLY","REVISION_CONFLICT"]
    assert store(tmp_path).effective(key="generation.max_output_tokens",workspace_id="w1")["revision"]==1


def test_documentary_authority_reconciled_without_registry_expansion():
    import json
    repository = Path(__file__).resolve().parents[1]
    registry = json.loads((repository/".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))
    state = json.loads((repository/".devpilot/project_state.json").read_text(encoding="utf-8"))
    assert registry["current_micro_sprint"] == state["current_micro_sprint"]
    assert registry["current_micro_sprint"].startswith(("MP132-R01-", "MP132-R02-01/", "MP132-R02-02/", "MP132-R02-03/", "MP132-R02-04/", "MP132-R02-05/"))  # successor-safe active pointer
    assert len(registry["documents"]) == 1752
