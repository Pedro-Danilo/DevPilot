from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from devpilot_core.workspace.project_entry_contracts import ProjectEntryContractService

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def git_blob_sha(rel: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"HEAD:{rel.replace('\\\\', '/')}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    return hashlib.sha256(completed.stdout.replace(b"\r\n", b"\n")).hexdigest()


def fixture_payload(target_root: Path) -> dict:
    payload = load("evals/fixtures/gsdlc_03_a_inventory_sales_intake.valid.json")
    payload["target_root"] = str(target_root)
    return payload


def forbidden_key_present(value, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return any(str(k).lower() in forbidden or forbidden_key_present(v, forbidden) for k, v in value.items())
    if isinstance(value, list):
        return any(forbidden_key_present(v, forbidden) for v in value)
    return False


def test_project_intake_catalog_and_plan_schemas_are_registered_and_valid() -> None:
    pairs = [
        ("docs/schemas/project_intake.schema.json", "evals/fixtures/gsdlc_03_a_inventory_sales_intake.valid.json"),
        ("docs/schemas/technology_catalog.schema.json", ".devpilot/workspaces/technology_catalog.json"),
    ]
    for schema_rel, instance_rel in pairs:
        schema = load(schema_rel)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(load(instance_rel))

    plan_schema = load("docs/schemas/project_creation_plan.schema.json")
    Draft202012Validator.check_schema(plan_schema)

    catalog = load("docs/schemas/schema_catalog.json")
    ids = {item["schema_id"] for item in catalog["schemas"]}
    assert {
        "SCHEMA-DEVPL-GSDLC-03-A-PROJECT-INTAKE-V1",
        "SCHEMA-DEVPL-GSDLC-03-A-TECHNOLOGY-CATALOG-V1",
        "SCHEMA-DEVPL-GSDLC-03-A-PROJECT-CREATION-PLAN-V1",
    } <= ids


def test_reference_inventory_sales_case_is_declarative_and_not_real_pilot() -> None:
    fixture = load("evals/fixtures/gsdlc_03_a_inventory_sales_intake.valid.json")
    assert fixture["project_id"] == "inventory-sales-local-concept"
    assert fixture["stack"] == {
        "frontend": "react-typescript",
        "backend": "fastapi-python",
        "database": "sqlite",
    }
    material = json.dumps(fixture).replace("\\\\", "\\").lower()
    assert "devpilot_workspaces\\inventory-sales-local" not in material
    assert "devpilot_e2e_evaluation" in material


def test_supported_create_intake_builds_stable_side_effect_free_plan(tmp_path: Path) -> None:
    allowed = tmp_path / "evaluation"
    allowed.mkdir()
    target = allowed / "worktrees" / "inventory-sales-local-concept"
    service = ProjectEntryContractService(ROOT, allowed_roots=(allowed,))
    payload = fixture_payload(target)

    before = sorted(str(p.relative_to(allowed)) for p in allowed.rglob("*"))
    validated = service.validate_intake(payload)
    assert validated.ok, validated.to_dict()
    first = service.build_creation_plan(payload)
    second = service.build_creation_plan(payload)
    assert first.ok and second.ok
    plan = first.data["plan"]
    assert plan == second.data["plan"]
    assert plan["plan_hash"] == second.data["plan"]["plan_hash"]
    assert plan["planning_only"] is True and plan["execution_enabled"] is False
    assert plan["safety"] == {
        "local_first": True,
        "deny_by_default": True,
        "dry_run_default": True,
        "writes_performed": False,
        "network_used": False,
        "external_api_used": False,
        "arbitrary_shell_used": False,
        "pilot_workspace_accessed": False,
        "credentials_included": False,
    }
    Draft202012Validator(load("docs/schemas/project_creation_plan.schema.json")).validate(plan)
    after = sorted(str(p.relative_to(allowed)) for p in allowed.rglob("*"))
    assert after == before
    assert not target.exists()


def test_unknown_and_ambiguous_stack_fail_closed(tmp_path: Path) -> None:
    allowed = tmp_path / "evaluation"
    allowed.mkdir()
    payload = fixture_payload(allowed / "new-project")
    unsupported = copy.deepcopy(payload)
    unsupported["stack"]["backend"] = "unknown-backend"
    result = ProjectEntryContractService(ROOT, allowed_roots=(allowed,)).validate_intake(unsupported)
    assert not result.ok
    assert "PROJECT_INTAKE_UNSUPPORTED_OR_AMBIGUOUS_STACK" in {item.id for item in result.findings}

    catalog = load(".devpilot/workspaces/technology_catalog.json")
    catalog["profiles"].append(copy.deepcopy(catalog["profiles"][0]))
    custom = tmp_path / "ambiguous-catalog.json"
    custom.write_text(json.dumps(catalog), encoding="utf-8")
    result = ProjectEntryContractService(ROOT, allowed_roots=(allowed,), catalog_path=custom).validate_intake(payload)
    assert not result.ok
    assert "PROJECT_INTAKE_UNSUPPORTED_OR_AMBIGUOUS_STACK" in {item.id for item in result.findings}


def test_path_traversal_outside_root_platform_overlap_and_collision_are_blocked(tmp_path: Path) -> None:
    allowed = tmp_path / "evaluation"
    allowed.mkdir()
    service = ProjectEntryContractService(ROOT, allowed_roots=(allowed,))

    traversal = fixture_payload(allowed / "a" / ".." / "b")
    result = service.validate_intake(traversal)
    assert not result.ok and "PROJECT_INTAKE_TRAVERSAL_BLOCKED" in {item.id for item in result.findings}

    outside = fixture_payload(tmp_path / "outside" / "project")
    result = service.validate_intake(outside)
    assert not result.ok and "PROJECT_INTAKE_ALLOWED_ROOT_BLOCKED" in {item.id for item in result.findings}

    platform_overlap = fixture_payload(ROOT / "nested-project")
    result = service.validate_intake(platform_overlap)
    assert not result.ok and "PROJECT_INTAKE_PLATFORM_OVERLAP_BLOCKED" in {item.id for item in result.findings}

    collision = allowed / "collision"
    collision.mkdir()
    (collision / "existing.txt").write_text("existing", encoding="utf-8")
    result = service.validate_intake(fixture_payload(collision))
    assert not result.ok and "PROJECT_INTAKE_TARGET_COLLISION_BLOCKED" in {item.id for item in result.findings}


def test_symlink_escape_is_blocked_when_platform_supports_symlinks(tmp_path: Path) -> None:
    allowed = tmp_path / "evaluation"
    allowed.mkdir()
    real = allowed / "real"
    real.mkdir()
    link = allowed / "link"
    try:
        link.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is not available in this environment")
    result = ProjectEntryContractService(ROOT, allowed_roots=(allowed,)).validate_intake(fixture_payload(link / "project"))
    assert not result.ok
    assert "PROJECT_INTAKE_SYMLINK_BLOCKED" in {item.id for item in result.findings}


def test_open_existing_requires_existing_directory(tmp_path: Path) -> None:
    allowed = tmp_path / "evaluation"
    allowed.mkdir()
    payload = fixture_payload(allowed / "missing")
    payload["entry_mode"] = "OPEN_EXISTING"
    result = ProjectEntryContractService(ROOT, allowed_roots=(allowed,)).validate_intake(payload)
    assert not result.ok and "PROJECT_INTAKE_OPEN_TARGET_MISSING" in {item.id for item in result.findings}


def test_secret_material_and_free_form_command_fields_are_blocked(tmp_path: Path) -> None:
    allowed = tmp_path / "evaluation"
    allowed.mkdir()
    service = ProjectEntryContractService(ROOT, allowed_roots=(allowed,))
    payload = fixture_payload(allowed / "new")
    payload["password"] = "do-not-accept"
    result = service.validate_intake(payload)
    assert not result.ok and "PROJECT_INTAKE_SECRET_FIELD_BLOCKED" in {item.id for item in result.findings}

    payload = fixture_payload(allowed / "new2")
    payload["command"] = "echo unsafe"
    result = service.validate_intake(payload)
    assert not result.ok and "PROJECT_INTAKE_FREE_FORM_COMMAND_BLOCKED" in {item.id for item in result.findings}


def test_import_git_remote_credentials_fail_and_remote_plan_remains_disabled_by_default(tmp_path: Path) -> None:
    allowed = tmp_path / "evaluation"
    allowed.mkdir()
    service = ProjectEntryContractService(ROOT, allowed_roots=(allowed,))

    bad = fixture_payload(allowed / "remote-bad")
    bad["entry_mode"] = "IMPORT_GIT"
    bad["git_source"] = {"kind": "remote-url", "location": "https://user:password@example.invalid/repo.git"}
    result = service.validate_intake(bad)
    assert not result.ok
    assert "PROJECT_INTAKE_GIT_CREDENTIAL_MATERIAL_BLOCKED" in {item.id for item in result.findings}
    serialized = json.dumps(result.to_dict())
    assert "user:password" not in serialized and "password@example" not in serialized

    good = fixture_payload(allowed / "remote-good")
    good["entry_mode"] = "IMPORT_GIT"
    good["git_source"] = {"kind": "remote-url", "location": "https://example.invalid/repo.git"}
    result = service.build_creation_plan(good)
    assert result.ok, result.to_dict()
    plan = result.data["plan"]
    clone = [item for item in plan["typed_operations"] if item["operation_id"] == "git.clone.remote"]
    assert len(clone) == 1
    assert clone[0]["network_required"] is True and clone[0]["approval_required"] is True
    assert plan["execution_enabled"] is False
    assert plan["network"]["runtime_network_used"] is False
    assert plan["network"]["remote_git_disabled_by_default"] is True



def test_import_git_local_source_is_policy_bounded_and_distinct_from_target(tmp_path: Path) -> None:
    allowed = tmp_path / "evaluation"
    allowed.mkdir()
    source = allowed / "source-repo"
    source.mkdir()
    target = allowed / "target-repo"
    service = ProjectEntryContractService(ROOT, allowed_roots=(allowed,))

    good = fixture_payload(target)
    good["entry_mode"] = "IMPORT_GIT"
    good["git_source"] = {"kind": "local-path", "location": str(source)}
    result = service.build_creation_plan(good)
    assert result.ok, result.to_dict()
    assert any(item["operation_id"] == "git.import.local" for item in result.data["plan"]["typed_operations"])

    collision = fixture_payload(source)
    collision["entry_mode"] = "IMPORT_GIT"
    collision["git_source"] = {"kind": "local-path", "location": str(source)}
    result = service.validate_intake(collision)
    assert not result.ok
    assert "PROJECT_INTAKE_GIT_SOURCE_TARGET_COLLISION_BLOCKED" in {item.id for item in result.findings}

    outside = fixture_payload(target)
    outside["entry_mode"] = "IMPORT_GIT"
    outside["git_source"] = {"kind": "local-path", "location": str(tmp_path / "outside-source")}
    result = service.validate_intake(outside)
    assert not result.ok
    assert "PROJECT_INTAKE_GIT_LOCAL_ALLOWED_ROOT_BLOCKED" in {item.id for item in result.findings}

def test_technology_catalog_contains_only_typed_operation_metadata() -> None:
    catalog = load(".devpilot/workspaces/technology_catalog.json")
    assert catalog["safety"]["arbitrary_shell_allowed"] is False
    assert catalog["safety"]["silent_network_allowed"] is False
    assert catalog["safety"]["pilot_workspace_access_allowed"] is False
    assert len(catalog["typed_operations"]) >= 8
    assert not forbidden_key_present(catalog, {"command", "command_line", "shell", "shell_text", "script", "argv"})
    ids = {item["operation_id"] for item in catalog["typed_operations"]}
    assert {"git.init", "python.venv.create", "workspace.register", "git.clone.remote"} <= ids


def test_historical_execution_and_ui_contracts_are_not_rewritten() -> None:
    assert git_blob_sha("src/devpilot_core/workspace/bootstrap.py") == "4d61defeecaf79a1831d9d5db03cfb4ade4b2b2ab25c6ccd7438b9be13ae8c9c"
    assert git_blob_sha("src/devpilot_core/repo/git_adapter.py") == "a03c8dd12807d4f9d5d078b0ae8fb7cfb6173d2adfef266ad017529d4c5395d1"
    assert git_blob_sha(".devpilot/plugins/plugin_permission_model.json") == "579cba87d13d47c5dd51335ab053fc8d3bbf985f4c7c289e22cf95f487e7ceca"
    assert git_blob_sha(".devpilot/interfaces/ui_route_contract_registry.json") == "7dc90c8e6e151adde051463d963eaeae4c373a4c181c3ed98d6f5d4af206ff2d"
    assert git_blob_sha(".devpilot/identity/auth_ui_route_contract_registry.json") == "ab74b1c48128badafd099656b26a67465e21d80625c891a3e160b5cafd179c36"


def test_03_a_source_has_no_runtime_execution_or_pilot_dependency() -> None:
    source = (ROOT / "src/devpilot_core/workspace/project_entry_contracts.py").read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "os.system" not in source
    assert "shell=True" not in source
    assert "DevPilot_Workspaces\\\\inventory-sales-local" not in source
    report = load("docs/audits/DEVPL_GSDLC_03_A_PROJECT_INTAKE_CONTRACT_REPORT.json")
    assert report["writes_performed"] is False
    assert report["network_used"] is False
    assert report["external_api_used"] is False
    assert report["pilot_workspace_accessed"] is False
    assert report["s0_open"] == 0 and report["s1_open"] == 0


def test_03_a_historical_contract_sweep_is_complete() -> None:
    sweep = load("docs/audits/devpl_gsdlc_03_a_historical_contract_sweep.json")
    assert sweep["unclassified_total"] == 0
    classes = {item["classification"] for item in sweep["contracts"]}
    assert {"historical-freeze", "current-active", "successor-needed"} <= classes
    assert sweep["historical_assertions_rewritten"] is False
    assert sweep["pilot_workspace_accessed"] is False


def test_03_a_project_state_and_tcr_preserve_closed_a_and_authorize_b_successor() -> None:
    state = load(".devpilot/project_state.json")
    assert state["gsdlc_03_a_status"] == "closed/PASS"
    assert state["gsdlc_03_a_validation_mode"] == "cumulative-selective"
    assert state["gsdlc_03_a_full_regression_executed"] is False
    assert state["gsdlc_03_a_pilot_workspace_accessed"] is False
    assert state["gsdlc_03_b_authorized"] is True
    assert state["gsdlc_03_b_execution_authorized_by_owner"] is True
    assert state["gsdlc_03_c_authorized"] is False

    v1 = load(".devpilot/testing/test_contract_registry.json")
    v2 = load(".devpilot/testing/test_contract_registry_v2.json")
    assert any(item["contract_id"] == "devpl-gsdlc-03-a-project-intake-contracts" for item in v1["contracts"])
    assert any(item["contract_id"] == "devpl-gsdlc-03-a-project-intake-contracts" for item in v2["contracts"])
    assert v1["contracts_total"] == len(v1["contracts"])
    assert v2["contracts_total"] == len(v2["contracts"])
