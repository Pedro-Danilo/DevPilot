from __future__ import annotations

import json
from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from devpilot_core.application import ApplicationService, AuthApplicationService
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.code_workbench import SourceChangeApplicationService
from devpilot_core.story_execution import StoryExecutionState, StoryExecutionStatus, StoryExecutionStore
from devpilot_core.testing.historical_contract_authority import HistoricalContractAuthorityGate

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = {"Origin": "http://127.0.0.1:5173"}
PASSWORD = "A-very-long-local-password-09c"


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "source-change-workspace"
    (root / ".devpilot").mkdir(parents=True)
    (root / "src").mkdir()
    (root / ".devpilot/project.yaml").write_text("project_id: source-change-fixture\nproject_name: Source Change Fixture\nproject_type: software\n", encoding="utf-8")
    (root / "src/app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    (root / "src/util.py").write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(root))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(root))
    monkeypatch.setenv("DEVPILOT_GSDLC09C_CONTROL_ROOT", str(tmp_path / "control-09c"))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)
    StoryExecutionStore(root, workspace_id=root.name).save_state(StoryExecutionState(
        execution_id="story-exec-09c1234567890abcdef1234", workspace_id=root.name, project_id="source-change-fixture",
        story_id="story-09c", story_version="1.0.0", status=StoryExecutionStatus.IN_PROGRESS, sequence=1,
        dor_report_sha256="a"*64, context_pack_id="story-context-09c1234567890abcdef12", context_pack_sha256="b"*64,
        created_at_utc="2026-09-07T10:00:00+00:00", updated_at_utc="2026-09-07T10:01:00+00:00"))
    return root


@pytest.fixture
def runtime(workspace: Path, tmp_path: Path):
    store = LocalAuthStore(tmp_path / "auth09c")
    auth = AuthApplicationService(tmp_path / "auth09c", store=store)
    client = TestClient(create_app(ROOT, api_token="legacy-09c", auth_service=auth))
    response = client.post("/api/v1/auth/bootstrap/owner", json={"username":"owner09c","display_name":"Owner 09C","password":PASSWORD}, headers=ORIGIN)
    assert response.status_code == 201, response.text
    app = ApplicationService(ROOT, approval_auth_store=store)
    return app, client


def _csrf(client: TestClient) -> dict[str, str]:
    return {"Origin": ORIGIN["Origin"], "X-DevPilot-CSRF": str(client.cookies.get("devpilot_csrf") or "")}


def _source(app: ApplicationService, rel: str) -> dict:
    listed = app.story_code_sources(); assert listed.ok, listed.to_dict()
    return next(x for x in listed.data["sources"] if x["relative_path"] == rel)


def _edit_draft(app: ApplicationService, rel: str, content: str) -> dict:
    row = _source(app, rel); src = app.story_code_source_read(source_id=row["source_id"]).data["source"]
    result = app.story_code_draft_save(operation="EDIT", content=content, target_path=rel, source_id=row["source_id"], expected_source_sha256=src["sha256"], expected_revision_sha256=None, actor="local-owner", actor_role="owner")
    assert result.ok, result.to_dict(); return result.data["draft"]


def _create_draft(app: ApplicationService, rel: str, content: str) -> dict:
    result=app.story_code_draft_save(operation="CREATE",content=content,target_path=rel,source_id=None,expected_source_sha256=None,expected_revision_sha256=None,actor="local-owner",actor_role="owner")
    assert result.ok,result.to_dict();return result.data["draft"]


def _plan(app: ApplicationService, drafts: list[dict]) -> dict:
    result=app.story_source_change_plan_create(draft_ids=[d["draft_id"] for d in drafts],actor="local-owner",actor_role="owner")
    assert result.ok,result.to_dict();return result.data["plan"]


def _approve_apply(app: ApplicationService, plan: dict, client: TestClient) -> str:
    req=app.story_source_change_apply_approval_request(plan_id=plan["plan_id"],plan_hash=plan["plan_hash"],actor="local-owner",actor_role="owner",reason="Reviewed exact full diff and Test Impact")
    assert req.ok,req.to_dict(); aid=req.data["approval"]["approval_id"]
    decided=client.post(f"/api/v1/approvals/{aid}/approve",json={"reason":"Human owner approves exact SourceChangePlan"},headers=_csrf(client))
    assert decided.status_code==200,decided.text
    return aid


def _apply(app: ApplicationService, plan: dict, client: TestClient) -> dict:
    aid=_approve_apply(app,plan,client)
    result=app.story_source_change_apply(plan_id=plan["plan_id"],plan_hash=plan["plan_hash"],approval_id=aid,actor="local-owner",actor_role="owner")
    assert result.ok,result.to_dict();return result.data["execution"]


def _approve_rollback(app: ApplicationService, execution_id: str, client: TestClient) -> str:
    req=app.story_source_change_rollback_approval_request(execution_id=execution_id,actor="local-owner",actor_role="owner",reason="Human owner requests exact source rollback")
    assert req.ok,req.to_dict();aid=req.data["approval"]["approval_id"]
    decided=client.post(f"/api/v1/approvals/{aid}/approve",json={"reason":"Human owner approves bounded rollback"},headers=_csrf(client))
    assert decided.status_code==200,decided.text
    return aid


def test_01_immutable_plan_contains_full_diff_risk_allowlist_and_test_impact(workspace: Path, runtime) -> None:
    app,client=runtime;draft=_edit_draft(app,"src/app.py","def answer():\n    return 43\n");plan=_plan(app,[draft])
    assert plan["required_approval_role"]=="owner" and plan["risk"]["level"]=="high"
    assert "-    return 42" in plan["full_diff"] and "+    return 43" in plan["full_diff"]
    assert plan["exact_path_allowlist"]==["src/app.py"] and plan["test_impact_preview"]["status"]=="PASS"
    assert (workspace/"src/app.py").read_text(encoding="utf-8").endswith("return 42\n")


def test_02_multifile_dry_run_is_zero_source_mutation(workspace: Path, runtime) -> None:
    app,client=runtime;d1=_edit_draft(app,"src/app.py","def answer():\n    return 44\n");d2=_edit_draft(app,"src/util.py","VALUE = 2\n");plan=_plan(app,[d1,d2])
    before={(p.relative_to(workspace).as_posix()):p.read_bytes() for p in (workspace/"src").glob("*.py")}
    dry=app.story_source_change_dry_run(plan_id=plan["plan_id"],plan_hash=plan["plan_hash"],actor="local-owner",actor_role="owner")
    assert dry.ok and dry.data["source_mutations_performed"] is False
    after={(p.relative_to(workspace).as_posix()):p.read_bytes() for p in (workspace/"src").glob("*.py")}; assert after==before


def test_03_stale_preimage_blocks_before_apply(workspace: Path, runtime) -> None:
    app,client=runtime;plan=_plan(app,[_edit_draft(app,"src/app.py","def answer():\n    return 45\n")])
    (workspace/"src/app.py").write_text("# external\n",encoding="utf-8")
    r=app.story_source_change_plan_recheck(plan_id=plan["plan_id"],plan_hash=plan["plan_hash"])
    assert not r.ok and any(f.id=="GSDLC09C_STALE_PREIMAGE_BLOCK" for f in r.findings)


def test_04_unexpected_create_target_blocks_recheck(workspace: Path, runtime) -> None:
    app,client=runtime;plan=_plan(app,[_create_draft(app,"src/new.py","NEW = True\n")]);(workspace/"src/new.py").write_text("external=True\n",encoding="utf-8")
    r=app.story_source_change_plan_recheck(plan_id=plan["plan_id"],plan_hash=plan["plan_hash"])
    assert not r.ok and any(f.id=="GSDLC09C_UNEXPECTED_TARGET_BLOCK" for f in r.findings)


def test_05_wrong_role_cannot_request_or_execute_source_write(workspace: Path, runtime) -> None:
    app,client=runtime;plan=_plan(app,[_edit_draft(app,"src/app.py","def answer():\n    return 46\n")])
    req=app.story_source_change_apply_approval_request(plan_id=plan["plan_id"],plan_hash=plan["plan_hash"],actor="dev",actor_role="developer",reason="try")
    assert not req.ok and any(f.id=="GSDLC09C_WRONG_APPROVER_ROLE_BLOCK" for f in req.findings)
    execute=app.story_source_change_apply(plan_id=plan["plan_id"],plan_hash=plan["plan_hash"],approval_id="missing",actor="dev",actor_role="developer")
    assert not execute.ok and any(f.id=="GSDLC09C_WRONG_ROLE_BLOCK" for f in execute.findings)


def test_06_approved_multifile_apply_is_exact_and_all_or_nothing(workspace: Path, runtime) -> None:
    app,client=runtime;plan=_plan(app,[_edit_draft(app,"src/app.py","def answer():\n    return 47\n"),_edit_draft(app,"src/util.py","VALUE = 7\n")]);execution=_apply(app,plan,client)
    assert execution["status"]=="applied" and len(execution["changes"])==2
    assert (workspace/"src/app.py").read_text()=="def answer():\n    return 47\n" and (workspace/"src/util.py").read_text()=="VALUE = 7\n"
    manifest=app.story_source_change_apply_manifest(execution_id=execution["execution_id"]);assert manifest.ok and manifest.data["apply_manifest"]["status"]=="applied"


def test_07_fault_injection_restores_all_preimages_without_partial_residue(workspace: Path, runtime) -> None:
    app,client=runtime;plan=_plan(app,[_edit_draft(app,"src/app.py","def answer():\n    return 48\n"),_create_draft(app,"src/new.py","NEW = 48\n")]);aid=_approve_apply(app,plan,client)
    failing=SourceChangeApplicationService(ROOT,context_resolver=app.ui_workspace_context,code_workbench=app.code_workbench,failure_injection_stage="after-change-1",approval_auth_store=app.approval_auth_store)
    r=failing.apply(plan_id=plan["plan_id"],plan_hash=plan["plan_hash"],approval_id=aid,actor="local-owner",actor_role="owner")
    assert not r.ok and r.data["partial_residue"] is False
    assert (workspace/"src/app.py").read_text()=="def answer():\n    return 42\n" and not (workspace/"src/new.py").exists()


def test_08_rename_apply_removes_old_path_and_creates_exact_target(workspace: Path, runtime) -> None:
    app,client=runtime;row=_source(app,"src/util.py");src=app.story_code_source_read(source_id=row["source_id"]).data["source"]
    saved=app.story_code_draft_save(operation="RENAME",content="VALUE = 9\n",target_path="src/helper.py",source_id=row["source_id"],expected_source_sha256=src["sha256"],expected_revision_sha256=None,actor="local-owner",actor_role="owner");assert saved.ok
    execution=_apply(app,_plan(app,[saved.data["draft"]]),client);assert execution["status"]=="applied"
    assert not (workspace/"src/util.py").exists() and (workspace/"src/helper.py").read_text()=="VALUE = 9\n"


def test_09_separate_rollback_approval_restores_create_absence(workspace: Path, runtime) -> None:
    app,client=runtime;execution=_apply(app,_plan(app,[_create_draft(app,"src/generated.py","VALUE=10\n")]),client)
    aid=_approve_rollback(app,execution["execution_id"],client);r=app.story_source_change_rollback(execution_id=execution["execution_id"],approval_id=aid,actor="local-owner",actor_role="owner")
    assert r.ok and r.data["source_hash_parity"] is True and not (workspace/"src/generated.py").exists()


def test_10_multifile_manual_rollback_restores_source_hash_parity(workspace: Path, runtime) -> None:
    before1=(workspace/"src/app.py").read_bytes();before2=(workspace/"src/util.py").read_bytes();app,client=runtime
    execution=_apply(app,_plan(app,[_edit_draft(app,"src/app.py","def answer():\n    return 11\n"),_edit_draft(app,"src/util.py","VALUE = 11\n")]),client)
    aid=_approve_rollback(app,execution["execution_id"],client);r=app.story_source_change_rollback(execution_id=execution["execution_id"],approval_id=aid,actor="local-owner",actor_role="owner")
    assert r.ok and (workspace/"src/app.py").read_bytes()==before1 and (workspace/"src/util.py").read_bytes()==before2
    evidence=app.story_source_change_rollback_evidence(execution_id=execution["execution_id"]);assert evidence.ok and evidence.data["rollback_evidence"]["source_hash_parity"] is True


def test_11_plan_tampering_is_detected(workspace: Path, runtime) -> None:
    app,client=runtime;plan=_plan(app,[_edit_draft(app,"src/app.py","def answer():\n    return 12\n")]);path=workspace/"outputs"/"code_workbench"/"gsdlc_09_c"/workspace.name/"plans"/f"{plan['plan_id']}.json"
    payload=json.loads(path.read_text());payload["exact_path_allowlist"].append("src/unapproved.py");path.write_text(json.dumps(payload),encoding="utf-8")
    r=app.story_source_change_plan_get(plan_id=plan["plan_id"]);assert not r.ok and any(f.id=="GSDLC09C_PLAN_TAMPER_BLOCK" for f in r.findings)


def test_12_generic_patch_shell_and_agent_self_apply_remain_blocked_contracts() -> None:
    catalog={x["action_id"]:x for x in json.loads((ROOT/".devpilot/approval/sensitive_action_catalog.json").read_text())["actions"]}
    assert catalog["patch.apply"]["executable"] is False and catalog["patch.apply"]["source_mutation_allowed"] is False
    for aid in ["filesystem.story_source_change_apply","filesystem.story_source_change_rollback"]:
        assert catalog[aid]["allowed_interfaces"]==["api","ui"] and "agent" in catalog[aid]["blocked_interfaces"] and "cli" in catalog[aid]["blocked_interfaces"]


def test_13_uoc005_historical_freeze_and_authority_registry_are_successor_safe() -> None:
    frozen=json.loads((ROOT/".devpilot/testing/fixtures/uoc005_source_mutation_routes_at_close.json").read_text())
    assert set(frozen["source_mutation_route_ids"])=={"api.workspace.edit-plans.apply","api.workspace.edit-executions.rollback"}
    gate=HistoricalContractAuthorityGate(ROOT).run();assert gate.ok,gate.to_dict();assert gate.data["summary"]["authority_contracts_total"]>=9


def test_14_api_contract_has_exact_11_successor_routes_and_two_source_writes() -> None:
    # historical-freeze: this validates repo410 close-time API authority, not mutable current-active cardinality.
    snapshot=json.loads((ROOT/".devpilot/testing/fixtures/gsdlc_09_c_api_routes_at_close.json").read_text())
    assert snapshot["status"]=="historical-freeze"
    assert snapshot["routes_total_at_close"]==180 and snapshot["gsdlc_09_c_routes_total"]==11
    assert snapshot["source_mutation_routes_total"]==2
    assert {"api.story-source-change.apply","api.story-source-change.rollback"}.issubset(set(snapshot["route_ids"]))
