from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from devpilot_core.workspace.project_bootstrap_execution import BootstrapExecutionInput, ProjectBootstrapExecutor

ROOT = Path(__file__).resolve().parents[1]


def intake(target: Path, *, mode: str = "CREATE_NEW", source: Path | None = None) -> dict:
    payload = json.loads((ROOT / "evals/fixtures/gsdlc_03_a_inventory_sales_intake.valid.json").read_text(encoding="utf-8"))
    payload["project_id"] = "gsdlc03d-fixture"
    payload["project_name"] = "GSDLC 03-D Fixture"
    payload["target_root"] = str(target)
    payload["entry_mode"] = mode
    payload.pop("git_source", None)
    if mode == "IMPORT_GIT":
        payload["git_source"] = {"kind": "local-path", "location": str(source)}
    return payload


def plan(mode: str, *, venv: bool = False) -> dict:
    p = {
        "schema_id": "SCHEMA-DEVPL-GSDLC-03-B-BOOTSTRAP-PLAN-V1",
        "project_id": "gsdlc03d-fixture",
        "entry_mode": mode,
        "plan_hash": "a" * 64,
        "directories": [],
        "files": [],
        "git_operations": [],
        "venv": {"required": venv, "relative_path": ".venv"},
        "dependency_jobs": [],
        "workspace_registration": {"operation_id": "workspace.register"},
        "network": {"required_by_plan": False},
        "approval": {"required_for_execute": True},
    }
    if mode == "CREATE_NEW":
        p["directories"] = [
            {"relative_path": "src"},
            {"relative_path": "docs"},
        ]
        p["files"] = [
            {"relative_path": ".gitignore", "template_id": "common.gitignore"},
            {"relative_path": "README.md", "template_id": "common.readme"},
            {"relative_path": ".devpilot/project.yaml", "template_id": "devpilot.project-metadata"},
        ]
        p["git_operations"] = [{"operation_id": "git.init"}]
    elif mode == "IMPORT_GIT":
        p["git_operations"] = [{"operation_id": "git.import.local"}]
    return p


def execute(root: Path, payload: dict, p: dict, *, fault_stage: str | None = None):
    return ProjectBootstrapExecutor(ROOT, allowed_roots=(root,)).execute(
        BootstrapExecutionInput(
            intake=payload,
            bootstrap_plan=p,
            plan_hash=p["plan_hash"],
            preimage_hash="b" * 64,
            approval_id="apr-test",
            actor_id="owner.local",
            role_at_decision="owner",
            fault_stage=fault_stage,
            dependency_mode="defer-network",
        )
    )


def init_git(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "devpilot-test@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "DevPilot Test"], cwd=path, check=True)


def commit_all(path: Path, message: str = "fixture") -> None:
    subprocess.run(["git", "add", "--all"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=path, check=True, capture_output=True)


def git_clean(path: Path) -> bool:
    cp = subprocess.run(["git", "status", "--porcelain=v1", "-z"], cwd=path, capture_output=True, check=True)
    return not [x for x in cp.stdout.split(b"\0") if x]


def test_create_executes_typed_local_transaction_and_leaves_git_clean(tmp_path: Path) -> None:
    target = tmp_path / "create"
    p = plan("CREATE_NEW")
    result = execute(tmp_path, intake(target), p)
    assert result.ok, result.to_dict()
    execution = result.data["execution"]
    assert execution["status"] == "PASS"
    assert execution["writes_outside_workspace"] == 0
    assert execution["network_used"] is False
    assert target.is_dir()
    assert (target / ".devpilot/project.yaml").is_file()
    assert (target / ".devpilot/workspace-registration.json").is_file()
    assert (target / ".devpilot/bootstrap-execution.json").is_file()
    assert git_clean(target)
    assert [row["stage"] for row in execution["stages"]] == [
        "target-root", "structure-templates", "git", "venv",
        "dependency-jobs", "workspace-metadata", "workspace-register", "verify",
    ]


@pytest.mark.parametrize("fault_stage", ["structure-templates", "git", "venv", "dependency-jobs", "workspace-register"])
def test_create_fault_injection_rolls_back_created_target(tmp_path: Path, fault_stage: str) -> None:
    target = tmp_path / f"fault-{fault_stage}"
    p = plan("CREATE_NEW", venv=fault_stage == "venv")
    result = execute(tmp_path, intake(target), p, fault_stage=fault_stage)
    assert not result.ok
    execution = result.data["execution"]
    assert execution["status"] == "ROLLED-BACK"
    assert execution["rollback"]["rollback_ok"] is True
    assert execution["writes_outside_workspace"] == 0
    assert not target.exists()


def test_open_registers_existing_git_without_dirtying_or_changing_source_files(tmp_path: Path) -> None:
    target = tmp_path / "open"
    init_git(target)
    readme = target / "README.md"
    readme.write_text("existing\n", encoding="utf-8")
    commit_all(target)
    before = readme.read_bytes()
    p = plan("OPEN_EXISTING")
    result = execute(tmp_path, intake(target, mode="OPEN_EXISTING"), p)
    assert result.ok, result.to_dict()
    assert readme.read_bytes() == before
    assert git_clean(target)
    assert (target / ".devpilot/workspace-registration.json").is_file()


def test_open_fault_rollback_restores_git_exclude_and_removes_created_metadata(tmp_path: Path) -> None:
    target = tmp_path / "open-fault"
    init_git(target)
    (target / "README.md").write_text("existing\n", encoding="utf-8")
    commit_all(target)
    exclude = target / ".git/info/exclude"
    before = exclude.read_bytes()
    p = plan("OPEN_EXISTING")
    result = execute(tmp_path, intake(target, mode="OPEN_EXISTING"), p, fault_stage="workspace-register")
    assert not result.ok
    assert result.data["execution"]["rollback"]["rollback_ok"] is True
    assert exclude.read_bytes() == before
    assert not (target / ".devpilot").exists()
    assert git_clean(target)


def test_import_local_clones_without_network_and_keeps_git_clean(tmp_path: Path) -> None:
    source = tmp_path / "source"
    init_git(source)
    (source / "README.md").write_text("source\n", encoding="utf-8")
    commit_all(source)
    target = tmp_path / "imported"
    p = plan("IMPORT_GIT")
    result = execute(tmp_path, intake(target, mode="IMPORT_GIT", source=source), p)
    assert result.ok, result.to_dict()
    assert (target / "README.md").read_text(encoding="utf-8") == "source\n"
    assert result.data["execution"]["network_used"] is False
    assert git_clean(target)


def test_remote_import_execution_remains_blocked(tmp_path: Path) -> None:
    target = tmp_path / "remote"
    payload = intake(target, mode="IMPORT_GIT")
    payload["git_source"] = {"kind": "remote-url", "location": "https://example.invalid/repo.git"}
    p = plan("IMPORT_GIT")
    p["git_operations"] = [{"operation_id": "git.clone.remote"}]
    result = execute(tmp_path, payload, p)
    assert not result.ok
    assert any(f.id == "PROJECT_BOOTSTRAP_REMOTE_GIT_DISABLED" for f in result.findings)
    assert not target.exists()


def test_api_owner_approval_bound_create_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient
    from devpilot_core.application import AuthApplicationService
    from devpilot_core.identity.auth_store import LocalAuthStore
    from devpilot_core.interfaces.api.app import create_app

    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(tmp_path))
    runtime = tmp_path / "auth-runtime"
    store = LocalAuthStore(runtime)
    auth = AuthApplicationService(runtime, store=store)
    client = TestClient(create_app(ROOT, api_token="legacy-token-test", auth_service=auth))
    password = "A-very-long-local-password-123"
    created = client.post(
        "/api/v1/auth/bootstrap/owner",
        json={"username": "owner", "display_name": "Owner", "password": password},
        headers={"origin": "http://127.0.0.1:5173"},
    )
    assert created.status_code == 201
    headers = {
        "origin": "http://127.0.0.1:5173",
        "X-DevPilot-CSRF": str(client.cookies.get("devpilot_csrf") or ""),
    }

    target = tmp_path / "api-create"
    payload = intake(target)
    dry = client.post("/api/v1/project-entry/dry-run", json={"intake": payload}, headers=headers)
    assert dry.status_code == 200, dry.text
    dry_data = dry.json()["data"]["dry_run"]
    plan_hash = dry_data["plan_hash"]
    preimage_hash = dry_data["preimage_hash"]

    approval = client.post(
        "/api/v1/project-entry/execution-approval-request",
        json={
            "intake": payload,
            "expected_plan_hash": plan_hash,
            "expected_preimage_hash": preimage_hash,
            "reason": "GSDLC-03-D acceptance",
            "ttl_minutes": 30,
        },
        headers=headers,
    )
    assert approval.status_code == 200, approval.text
    approval_id = approval.json()["data"]["approval"]["approval_id"]

    before = client.post(
        "/api/v1/project-entry/execute",
        json={
            "intake": payload,
            "expected_plan_hash": plan_hash,
            "expected_preimage_hash": preimage_hash,
            "approval_id": approval_id,
        },
        headers=headers,
    )
    assert before.status_code == 403
    assert not target.exists()

    approved = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json={"reason": "Owner approves exact reviewed bootstrap"},
        headers=headers,
    )
    assert approved.status_code == 200, approved.text

    executed = client.post(
        "/api/v1/project-entry/execute",
        json={
            "intake": payload,
            "expected_plan_hash": plan_hash,
            "expected_preimage_hash": preimage_hash,
            "approval_id": approval_id,
            "dependency_mode": "defer-network",
        },
        headers=headers,
    )
    assert executed.status_code == 200, executed.text
    execution = executed.json()["data"]["execution"]
    assert execution["status"] == "PASS"
    assert execution["network_used"] is False
    assert execution["writes_outside_workspace"] == 0
    assert execution["verification"]["git_clean"] is True
    assert target.is_dir()


def test_sensitive_action_catalog_enables_only_exact_owner_api_ui_bootstrap() -> None:
    catalog = json.loads((ROOT / ".devpilot/approval/sensitive_action_catalog.json").read_text(encoding="utf-8"))
    action = next(row for row in catalog["actions"] if row["action_id"] == "filesystem.project_bootstrap_execute")
    assert action["status"] == "implemented-initial-gsdlc-03-d"
    assert action["requires_approval"] is True
    assert action["requires_rbac_role"] == "owner"
    assert action["executable"] is True
    assert action["source_mutation_allowed"] is True
    assert action["allowed_interfaces"] == ["api", "ui"]
    assert {"cli", "agent", "remote"}.issubset(set(action["blocked_interfaces"]))


def test_03c_historical_route_snapshots_remain_102_api_and_11_ui() -> None:
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry_gsdlc03c_at_close.json").read_text(encoding="utf-8"))
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog_gsdlc03c_at_close.json").read_text(encoding="utf-8"))
    ui = json.loads((ROOT / ".devpilot/interfaces/ui_route_contract_registry_gsdlc03c_at_close.json").read_text(encoding="utf-8"))
    assert len(api["routes"]) == 102
    assert len(rbac["route_policies"]) == 102
    assert len(ui["routes"]) == 11
    current_api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    current_rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    assert len(current_api["routes"]) == 104
    assert len(current_rbac["route_policies"]) == 104


def test_git_execution_successor_is_explicitly_re_adjudicated_for_03d() -> None:
    catalog = json.loads((ROOT / ".devpilot/workspaces/bootstrap_execution_compatibility_gsdlc03d.json").read_text(encoding="utf-8"))
    successor = catalog["execution_successor"]
    assert catalog["historical_declared_git_minimum_version"] == "2.40"
    assert catalog["planning_successor_effective_git_minimum_version"] == "2.33.0"
    assert successor["tool_id"] == "git"
    assert successor["effective_minimum_version"] == "2.33.0"
    assert successor["network_execution_allowed"] is False
    assert successor["remote_git_execution_allowed"] is False
    assert "commit-local" in successor["required_capabilities"]


def test_approved_execution_uses_authenticated_decision_binding_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient
    from devpilot_core.application import AuthApplicationService
    from devpilot_core.identity.auth_store import LocalAuthStore
    from devpilot_core.interfaces.api.app import create_app

    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(tmp_path))
    runtime = tmp_path / "auth-runtime"
    store = LocalAuthStore(runtime)
    auth = AuthApplicationService(runtime, store=store)
    client = TestClient(create_app(ROOT, api_token="legacy-token-test", auth_service=auth))
    created = client.post(
        "/api/v1/auth/bootstrap/owner",
        json={"username": "owner", "display_name": "Owner", "password": "A-very-long-local-password-123"},
        headers={"origin": "http://127.0.0.1:5173"},
    )
    assert created.status_code == 201
    headers = {
        "origin": "http://127.0.0.1:5173",
        "X-DevPilot-CSRF": str(client.cookies.get("devpilot_csrf") or ""),
    }
    payload = intake(tmp_path / "binding-create")
    dry = client.post("/api/v1/project-entry/dry-run", json={"intake": payload}, headers=headers).json()["data"]["dry_run"]
    request = client.post(
        "/api/v1/project-entry/execution-approval-request",
        json={
            "intake": payload,
            "expected_plan_hash": dry["plan_hash"],
            "expected_preimage_hash": dry["preimage_hash"],
            "reason": "binding test",
            "ttl_minutes": 30,
        },
        headers=headers,
    )
    assert request.status_code == 200
    approval_id = request.json()["data"]["approval"]["approval_id"]
    decided = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json={"reason": "authenticated owner decision"},
        headers=headers,
    )
    assert decided.status_code == 200
    record = decided.json()["data"]["approval"]
    binding = record["metadata"]["authenticated_approval_binding"]
    assert binding["role_at_decision"] == "owner"
    assert binding["actor_id"] == record["decided_by"]
    assert binding["allowed"] is True


def test_execution_and_rollback_schemas_validate_generated_evidence(tmp_path: Path) -> None:
    from jsonschema import Draft202012Validator

    target = tmp_path / "schema-create"
    success = execute(tmp_path, intake(target), plan("CREATE_NEW"))
    assert success.ok
    execution_schema = json.loads((ROOT / "docs/schemas/project_bootstrap_execution.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(execution_schema)
    Draft202012Validator(execution_schema).validate(success.data["execution"])

    rollback_target = tmp_path / "schema-rollback"
    failed = execute(tmp_path, intake(rollback_target), plan("CREATE_NEW"), fault_stage="git")
    assert not failed.ok
    rollback_schema = json.loads((ROOT / "docs/schemas/project_bootstrap_rollback.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(rollback_schema)
    Draft202012Validator(rollback_schema).validate(failed.data["execution"]["rollback"])


def test_execution_compatibility_schema_validates_scoped_successor() -> None:
    from jsonschema import Draft202012Validator

    schema = json.loads((ROOT / "docs/schemas/bootstrap_execution_compatibility_gsdlc03d.schema.json").read_text(encoding="utf-8"))
    instance = json.loads((ROOT / ".devpilot/workspaces/bootstrap_execution_compatibility_gsdlc03d.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(instance)


def test_execute_route_rbac_is_owner_only_and_legacy_token_is_not_human_authority() -> None:
    catalog = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    row = next(
        item for item in catalog["route_policies"]
        if item["path"] == "/api/v1/project-entry/execute" and item["method"] == "POST"
    )
    assert row["human_session_required"] is True
    assert row["legacy_token_allowed"] is False
    assert row["allowed_roles"] == ["owner"]


def test_create_repeated_execution_is_fail_closed_and_preserves_first_workspace(tmp_path: Path) -> None:
    target = tmp_path / "repeat-create"
    payload = intake(target)
    p = plan("CREATE_NEW")
    first = execute(tmp_path, payload, p)
    assert first.ok
    before = (target / "README.md").read_bytes()
    second = execute(tmp_path, payload, p)
    assert not second.ok
    assert (target / "README.md").read_bytes() == before
    assert git_clean(target)


def test_stale_create_preimage_blocks_execution_without_executor_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient
    from devpilot_core.application import AuthApplicationService
    from devpilot_core.identity.auth_store import LocalAuthStore
    from devpilot_core.interfaces.api.app import create_app

    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(tmp_path))
    runtime = tmp_path / "auth-runtime"
    store = LocalAuthStore(runtime)
    auth = AuthApplicationService(runtime, store=store)
    client = TestClient(create_app(ROOT, api_token="legacy-token-test", auth_service=auth))
    assert client.post(
        "/api/v1/auth/bootstrap/owner",
        json={"username": "owner", "display_name": "Owner", "password": "A-very-long-local-password-123"},
        headers={"origin": "http://127.0.0.1:5173"},
    ).status_code == 201
    headers = {"origin": "http://127.0.0.1:5173", "X-DevPilot-CSRF": str(client.cookies.get("devpilot_csrf") or "")}
    target = tmp_path / "stale-create"
    payload = intake(target)
    dry = client.post("/api/v1/project-entry/dry-run", json={"intake": payload}, headers=headers).json()["data"]["dry_run"]
    request = client.post(
        "/api/v1/project-entry/execution-approval-request",
        json={"intake": payload, "expected_plan_hash": dry["plan_hash"], "expected_preimage_hash": dry["preimage_hash"], "reason": "stale test"},
        headers=headers,
    )
    assert request.status_code == 200
    approval_id = request.json()["data"]["approval"]["approval_id"]
    assert client.post(f"/api/v1/approvals/{approval_id}/approve", json={"reason": "approve exact preimage"}, headers=headers).status_code == 200
    target.mkdir()
    marker = target / "external-preimage-marker.txt"
    marker.write_text("created after approval\n", encoding="utf-8")
    result = client.post(
        "/api/v1/project-entry/execute",
        json={"intake": payload, "expected_plan_hash": dry["plan_hash"], "expected_preimage_hash": dry["preimage_hash"], "approval_id": approval_id},
        headers=headers,
    )
    assert result.status_code == 403
    assert marker.read_text(encoding="utf-8") == "created after approval\n"
    assert sorted(p.name for p in target.iterdir()) == ["external-preimage-marker.txt"]
