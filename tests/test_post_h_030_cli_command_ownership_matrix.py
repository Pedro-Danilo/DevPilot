from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.cli_registry.ownership import CliCommandOwnershipMatrixBuilder
from devpilot_core.cli_registry.registry import DeclarativeCliRegistryBuilder

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _flatten_registry_commands() -> list[dict]:
    registry = DeclarativeCliRegistryBuilder(ROOT).build_registry().to_dict()
    return [command for group in registry["groups"] for command in group["commands"]]


def test_post_h_030_a_ownership_matrix_covers_public_cli_surface() -> None:
    matrix = _load(".devpilot/cli_registry/command_ownership_matrix.json")
    registry_commands = _flatten_registry_commands()
    matrix_commands = matrix["commands"]

    assert matrix["created_by"] == "POST-H-030-A"
    assert matrix["status"] == "implemented-initial"
    assert matrix["summary"]["commands_total"] == len(registry_commands)
    assert matrix["summary"]["commands_covered_total"] == len(registry_commands)
    assert matrix["summary"]["coverage_complete"] is True
    assert {item["command_id"] for item in matrix_commands} == {item["command_id"] for item in registry_commands}
    assert matrix["summary"]["missing_owner_total"] == 0
    assert matrix["summary"]["missing_compatibility_contract_total"] == 0
    assert matrix["safety"]["dynamic_handler_loading_enabled"] is False
    assert matrix["safety"]["runtime_router_enabled"] is False
    assert matrix["safety"]["commands_executed"] is False


def test_post_h_030_a_high_critical_commands_have_owner_and_contract() -> None:
    matrix = _load(".devpilot/cli_registry/command_ownership_matrix.json")
    high = [item for item in matrix["commands"] if item["risk_level"] in {"high", "critical"}]

    assert high
    assert all(item["domain_owner"] for item in high)
    assert all(item["compatibility_contract_id"].startswith("cli-compat:") for item in high)
    assert all(item["json_output_contract"] for item in high)
    assert all(item["exit_code_contract"] for item in high)
    assert all(item["human_output_contract"] for item in high)


def test_post_h_030_a_planned_targets_are_existing_or_in_extraction_plan() -> None:
    matrix = _load(".devpilot/cli_registry/command_ownership_matrix.json")
    plan = _load(".devpilot/cli_registry/cli_extraction_plan.json")
    target_modules = {item["module_path"]: item for item in plan["target_modules"]}

    assert plan["created_by"] == "POST-H-030-A"
    assert plan["status"] == "implemented-initial"
    assert plan["summary"]["public_behavior_changes_allowed"] is False
    assert plan["summary"]["dynamic_handler_loading_enabled"] is False
    assert plan["summary"]["commands_referenced_total"] > 0

    for command in matrix["commands"]:
        if command["migration_state"] == "planned":
            assert command["target_module"] in target_modules
        if command["migration_state"] == "deferred-cli-only":
            assert command["cli_only_reason"]

    assert "src/devpilot_core/cli_commands/industrial_readiness.py" in target_modules
    assert "src/devpilot_core/cli_commands/release.py" in target_modules
    assert "src/devpilot_core/cli_commands/workspace.py" in target_modules


def test_post_h_030_a_schema_validation_and_builder_pass() -> None:
    builder = CliCommandOwnershipMatrixBuilder(ROOT)
    matrix, plan = builder.build()
    result = builder.validate(matrix, plan)

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["commands_total"] == _load(".devpilot/cli_registry/command_ownership_matrix.json")["summary"]["commands_total"]
    assert result.data["summary"]["blocking_findings_total"] == 0

    ownership_schema = cli.main([
        "schema", "validate", "--schema-id", "CliCommandOwnershipMatrix", "--instance", ".devpilot/cli_registry/command_ownership_matrix.json", "--json"
    ])
    extraction_schema = cli.main([
        "schema", "validate", "--schema-id", "CliExtractionPlan", "--instance", ".devpilot/cli_registry/cli_extraction_plan.json", "--json"
    ])

    assert ownership_schema == 0
    assert extraction_schema == 0


def test_post_h_030_a_governance_artifacts_are_synchronized() -> None:
    state = _load(".devpilot/project_state.json")
    source_registry = _load(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = _load(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _load(".devpilot/testing/test_contract_registry_v2.json")
    catalog = _load("docs/schemas/schema_catalog.json")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-030_cli_hotspot_reduction_application_boundaries.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    assert state["current_micro_sprint"] == "POST-H-030-A"
    assert state["next_micro_sprint"] == "POST-H-030-B"
    assert state["current_repo"] == "repo_DevPilot_Local_284_POST_H_030_A.zip"
    assert state["post_h_030_status"] == "active/implemented-initial-post-h-030-a"
    assert state["post_h_030_cli_ownership_coverage_complete"] is True
    assert state["post_h_030_cli_dynamic_handler_loading_enabled"] is False

    assert 'status: approved' in backlog
    assert 'implementation_status: "active/implemented-initial-post-h-030-a"' in backlog
    assert "POST-H-030-A — CLI command ownership matrix" in readme
    assert "POST-H-030-A — CLI command ownership matrix" in runbook
    assert "post-h-030-a" in changelog.lower()

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-030-A-CLI-COMMAND-OWNERSHIP-MATRIX" in doc_ids
    assert "POST-H-030-A-CLI-EXTRACTION-PLAN" in doc_ids
    assert "POST-H-030-A-CLI-OWNERSHIP-TEST" in doc_ids

    schema_ids = {item["schema_id"] for item in catalog["schemas"]}
    assert "SCHEMA-DEVPL-CLI-COMMAND-OWNERSHIP-MATRIX-V1" in schema_ids
    assert "SCHEMA-DEVPL-CLI-EXTRACTION-PLAN-V1" in schema_ids

    assert any(c["contract_id"] == "post-h-030-cli-command-ownership-matrix" for c in tcr_v1["contracts"])
    assert any(c["contract_id"] == "post-h-030-cli-command-ownership-matrix" for c in tcr_v2["contracts"])


def test_post_h_030_a_cli_no_growth_gate_still_passes() -> None:
    exit_code = cli.main(["cli-registry", "guard", "--json"])

    assert exit_code == 0
