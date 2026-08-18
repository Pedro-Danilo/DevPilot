from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_uoc_002_closure_is_fully_reconciled_before_uoc_003() -> None:
    manifest = load("docs/post_h_eval_002_uoc_002_manifest.json")
    state = load(".devpilot/project_state.json")
    assert manifest["status"] == "closed"
    assert manifest["decision"] == "PASS"
    assert manifest["closed"] is True
    assert manifest["pass_block"]["closure_status"] == "PASS"
    assert not any("browser acceptance pending" in item for item in manifest["known_limits"])
    assert state["uoc_002_closure_continuation_status"] == "closed/PASS"
    assert state["uoc_002_authoritative_baseline"] == "repo_DevPilot_Local_330_POST_H_EVAL_002_UOC_002.zip"


def test_uoc_003_manifest_lifecycle_is_safe() -> None:
    manifest = load("docs/post_h_eval_002_uoc_003_manifest.json")
    if manifest["closed"]:
        assert manifest["status"] == "closed"
        assert manifest["decision"] == "PASS"
        assert manifest["pass_block"]["closure_status"] == "PASS"
        assert manifest["pass_block"]["uoc_004_authorized"] is True
    else:
        assert manifest["status"] == "implemented-initial"
        assert manifest["decision"] == "PENDING-WINDOWS-ACCEPTANCE"
        assert manifest["pass_block"]["uoc_004_authorized"] is False
    assert manifest["scope"]["api_routes"] == 4
    assert manifest["scope"]["precode_artifacts_required"] == 8
    assert manifest["scope"]["job_mode"] == "synchronous-preliminary"
    assert manifest["safety"]["source_write_enabled"] is False
    assert manifest["safety"]["runtime_evidence_only"] is True
    assert manifest["safety"]["arbitrary_shell_allowed"] is False


def test_uoc_003_routes_are_registered_and_policy_bound() -> None:
    registry = load(".devpilot/interfaces/api_route_contract_registry.json")
    route_ids = {entry["route_id"]: entry for entry in registry["routes"]}
    expected = {
        "api.workspace.validations.plan",
        "api.workspace.validations.execute",
        "api.workspace.validations.status",
        "api.workspace.traceability",
    }
    assert expected <= route_ids.keys()
    assert registry["summary"]["routes_total"] == len(registry["routes"])
    assert registry["summary"]["uoc_003_validation_traceability_routes_total"] == 4
    assert all(route_ids[item]["policy_check_required"] for item in expected)
    assert all(not route_ids[item]["external_api_allowed"] for item in expected)
    assert route_ids["api.workspace.validations.execute"]["local_state_mutation_allowed"] is True
    assert route_ids["api.workspace.validations.execute"]["destructive_action_allowed"] is False

    security = (ROOT / "src/devpilot_core/interfaces/api/security.py").read_text(encoding="utf-8")
    for path in (
        "/api/v1/workspace/validations/plan",
        "/api/v1/workspace/validations/execute",
        "/api/v1/workspace/validations/{job_id}",
        "/api/v1/workspace/traceability",
    ):
        assert path in security


def test_uoc_003_openapi_and_ui_route_contracts_are_synchronized() -> None:
    openapi = load("docs/07_interfaces/openapi_v1.json")
    expected_paths = {
        "/api/v1/workspace/validations/plan",
        "/api/v1/workspace/validations/execute",
        "/api/v1/workspace/validations/{job_id}",
        "/api/v1/workspace/traceability",
    }
    assert expected_paths <= openapi["paths"].keys()
    ui_registry = load(".devpilot/interfaces/ui_route_contract_registry.json")
    workspace = next(item for item in ui_registry["routes"] if item["route_id"] == "ui.workspace-documents")
    assert {
        "api.workspace.validations.plan",
        "api.workspace.validations.execute",
        "api.workspace.validations.status",
        "api.workspace.traceability",
    } <= set(workspace["allowed_api_routes"])
    assert "ui/web/src/components/DocumentValidationPanel.ts" in workspace["source_files"]
    assert ui_registry["summary"]["uoc_003_validation_traceability"] is True


def test_uoc_003_feature_flag_and_capabilities_are_enabled_read_only() -> None:
    flags = load(".devpilot/interfaces/ui_operational_console_flags.json")
    flag = next(item for item in flags["feature_flags"] if item["flag_id"] == "uoc.documents.validation_traceability")
    assert flag["enabled"] is True
    assert flag["enabled_by"] == "UOC-003"
    assert flags["safety"]["workspace_validation_source_write_enabled"] is False

    registry = load(".devpilot/interfaces/ui_capability_registry.json")
    capabilities = {item["capability_id"]: item for item in registry["capabilities"]}
    uoc003_read_only = {
        "cli.validate",
        "cli.validate-frontmatter",
        "cli.validate-artifact",
        "cli.miasi.validate",
        "cli.checklist-pre-code",
    }
    for capability_id in uoc003_read_only:
        item = capabilities[capability_id]
        assert item["parity_status"] == "UI-READ-ONLY"
        assert item["application_service"] == "workspace.validations.execute"
        assert item["source_risk_level"] in {"low", "medium", "high", "critical"}
        assert item["supports_cancel"] is False

    # UOC-003 froze readiness as read-only at its own closure. Later UOC-009 is
    # explicitly allowed to promote that same deterministic capability to the
    # typed Quality UI without rewriting the UOC-003 historical manifest.
    readiness = capabilities["cli.readiness-check"]
    assert readiness["parity_status"] in {"UI-READ-ONLY", "UI-NATIVE"}
    if readiness["parity_status"] == "UI-NATIVE":
        assert readiness["application_service"] == "quality.operations"
        assert load(".devpilot/project_state.json")["uoc_009_authorized"] is True
    else:
        assert readiness["application_service"] == "workspace.validations.execute"
    assert readiness["source_risk_level"] in {"low", "medium", "high", "critical"}
    assert readiness["supports_cancel"] is False


def test_uoc_003_schemas_are_catalogued() -> None:
    catalog = load("docs/schemas/schema_catalog.json")
    ids = {item["schema_id"] for item in catalog["schemas"]}
    assert {
        "SCHEMA-DEVPL-WORKSPACE-VALIDATION-PLAN-V1",
        "SCHEMA-DEVPL-WORKSPACE-VALIDATION-JOB-V1",
        "SCHEMA-DEVPL-WORKSPACE-TRACEABILITY-V1",
    } <= ids
    assert catalog["schemas_total"] == len(catalog["schemas"])


def test_uoc_003_testing_and_documentation_governance_are_registered() -> None:
    v1 = load(".devpilot/testing/test_contract_registry.json")
    v2 = load(".devpilot/testing/test_contract_registry_v2.json")
    contract_id = "post-h-eval-002-uoc-003-validation-traceability"
    assert contract_id in {item["contract_id"] for item in v1["contracts"]}
    assert contract_id in {item["contract_id"] for item in v2["contracts"]}
    registry = load(".devpilot/docs_governance/source_registry.json")
    paths = {item["path"] for item in registry["documents"]}
    for path in (
        "docs/post_h_eval_002_uoc_003_manifest.json",
        "docs/audits/uoc_003_validation_traceability_report.md",
        "docs/audits/uoc_003_closure_report.md",
        "docs/schemas/workspace_validation_plan.schema.json",
        "docs/schemas/workspace_validation_job.schema.json",
        "docs/schemas/workspace_traceability.schema.json",
        "tests/test_post_h_eval_002_uoc_003_contracts.py",
    ):
        assert path in paths
    state = load(".devpilot/project_state.json")
    realized = [
        int(key[4:7])
        for key, value in state.items()
        if key.startswith("uoc_")
        and key.endswith("_status")
        and key[4:7].isdigit()
        and str(value).strip().lower().startswith(("implemented", "closed"))
    ]
    latest = max(realized)
    status_key = f"uoc_{latest:03d}_status"
    # The UOC-003 contract freezes UOC lifecycle facts, not the mutable global
    # last_registered_sprint pointer used by later closures/programs.
    assert str(state[status_key]).lower().startswith("closed")
    assert registry["project_state_snapshot"][status_key] == state[status_key]
    assert registry["last_registered_sprint"] == state["last_registered_sprint"]


def test_uoc_003_project_state_tracks_open_and_closed_lifecycle() -> None:
    state = load(".devpilot/project_state.json")
    assert state["uoc_003_candidate_repo"] == "repo_DevPilot_Local_331_CANDIDATE_POST_H_EVAL_002_UOC_003.zip"
    assert state["uoc_003_source_write_enabled"] is False
    if state["uoc_003_closed"]:
        current_repo = str(state["current_repo"])
        assert current_repo.startswith("repo_DevPilot_Local_")
        assert int(current_repo.split("_", 4)[3]) >= 331
        assert state["uoc_003_status"] == "closed/PASS"
        assert state["uoc_003_authoritative_baseline"] == "repo_DevPilot_Local_331_POST_H_EVAL_002_UOC_003.zip"
        assert state["uoc_004_authorized"] is True
    else:
        assert state["current_repo"] == "repo_DevPilot_Local_330_POST_H_EVAL_002_UOC_002.zip"
        assert state["uoc_003_status"] == "implemented-initial/pending-windows-acceptance"
        assert state["uoc_004_authorized"] is False


def test_uoc_003_ui_version_is_synchronized() -> None:
    package = load("ui/web/package.json")
    lock = load("ui/web/package-lock.json")
    version = str(package["version"])
    current_sprint = str(package["devpilot"]["currentSprint"])
    assert lock["version"] == version
    assert lock["packages"][""]["version"] == version
    assert "-post-h-eval-002-uoc-" in version
    version_uoc = int(version.rsplit("-uoc-", 1)[1])
    historical_uoc = str(package["devpilot"]["postHEvolutionCurrent"])
    historical_uoc_number = int(historical_uoc.rsplit("UOC-", 1)[1])
    # The package version and UOC lineage remain frozen at the last UOC
    # operational-console release. Later DEVPL-GSDLC successors own
    # ``currentSprint`` and must not be forced back to a historical UOC label.
    assert version_uoc == historical_uoc_number
    assert current_sprint == "DEVPL-GSDLC-02-E"
    assert version_uoc >= 3
    assert package["devpilot"]["uoc003Status"] == "closed/PASS"
