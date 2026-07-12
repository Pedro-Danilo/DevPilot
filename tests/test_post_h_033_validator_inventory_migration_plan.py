from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.schemas import SchemaValidator
from devpilot_core.validation import ValidatorInventoryManager, ValidatorInventoryOptions

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_VALIDATORS = {
    "validators.artifact_profiles",
    "validators.frontmatter",
    "validators.readiness",
    "miasi.registry",
    "miasi.semantic",
    "miasi.semantic_rules",
    "docs_governance.validator",
    "docs_governance.backlogs",
    "docs_governance.drift",
    "policy.prompt_guard",
    "policy.tool_injection_guard",
    "policy.secrets",
    "validation.artifact_profile_registry",
    "schemas.validator",
}


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_033_a_inventory_schema_and_minimum_validators() -> None:
    inventory = load_json(".devpilot/validation/validator_inventory.json")

    assert inventory["created_by"] == "POST-H-033-A"
    assert inventory["status"] == "implemented-initial"
    assert inventory["summary"]["runtime_behavior_changed"] is False
    assert inventory["summary"]["llm_judge_required"] is False
    assert inventory["summary"]["critical_defenses_disable_allowed"] is False
    assert {item["validator_id"] for item in inventory["validators"]} >= REQUIRED_VALIDATORS

    for item in inventory["validators"]:
        assert item["owner"]
        assert item["module_path"]
        assert (ROOT / item["module_path"]).exists()
        assert item["criticality"] in {"P0", "P1", "P2", "P3"}
        assert item["inputs"]
        assert item["outputs"]
        assert item["tests"]
        assert item["migration_micro_sprint"]
        assert item["compatibility_strategy"]
        assert item["hardcoded_elements"]
        for element in item["hardcoded_elements"]:
            assert element["decision"] in {"migrate", "keep", "fallback", "parser", "security-core"}
            assert element["rationale"]

    result = SchemaValidator(ROOT).validate(schema="ValidatorInventory", instance=".devpilot/validation/validator_inventory.json")
    assert result.ok is True


def test_post_h_033_a_migration_plan_preserves_runtime_invariants() -> None:
    plan = load_json(".devpilot/validation/validator_migration_plan.json")

    assert plan["created_by"] == "POST-H-033-A"
    assert plan["summary"]["decision"] == "PASS"
    assert plan["summary"]["runtime_behavior_changed"] is False
    assert plan["summary"]["llm_judge_required"] is False
    assert plan["summary"]["external_dependencies_added"] is False
    assert plan["summary"]["critical_defenses_disable_allowed"] is False
    assert plan["summary"]["no_go_gates_preserved"] is True
    assert {wave["micro_sprint"] for wave in plan["migration_waves"]} == {
        "POST-H-033-B",
        "POST-H-033-C",
        "POST-H-033-D",
        "POST-H-033-E",
        "POST-H-033-F",
    }
    assert all(decision["hardcoded_decisions"] for decision in plan["validator_decisions"])

    result = SchemaValidator(ROOT).validate(schema="ValidatorMigrationReport", instance=".devpilot/validation/validator_migration_plan.json")
    assert result.ok is True


def test_post_h_033_a_manager_evaluates_inventory_and_plan_without_runtime_mutation(tmp_path: Path) -> None:
    result = ValidatorInventoryManager(ROOT, ValidatorInventoryOptions()).evaluate()

    assert result.ok is True
    assert result.exit_code == 0
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["validators_total"] >= 14
    assert summary["runtime_behavior_changed"] is False
    assert summary["llm_judge_required"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations_performed"] is False


def test_post_h_033_a_manifest_validates_as_migration_report() -> None:
    result = SchemaValidator(ROOT).validate(schema="ValidatorMigrationReport", instance="docs/post_h_033_a_manifest.json")
    manifest = load_json("docs/post_h_033_a_manifest.json")

    assert result.ok is True
    assert manifest["manifest_id"] == "post-h-033-a-validator-inventory-migration-plan"
    assert manifest["next_micro_sprint"] == "POST-H-033-B — Frontmatter schema-backed validator"


def test_post_h_033_a_governance_artifacts_registered_and_docs_synced() -> None:
    source_registry = load_json(".devpilot/docs_governance/source_registry.json")
    schema_catalog = load_json("docs/schemas/schema_catalog.json")
    tcr_v1 = load_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = load_json(".devpilot/testing/test_contract_registry_v2.json")
    state = load_json(".devpilot/project_state.json")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-033_schema_backed_validators_declarative_semantics.md").read_text(encoding="utf-8")
    top_level = (ROOT / "docs/POST-H-033_schema_backed_validators_declarative_semantics.md").read_text(encoding="utf-8")

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-033-A-VALIDATOR-INVENTORY" in doc_ids
    assert "POST-H-033-A-VALIDATOR-MIGRATION-PLAN" in doc_ids
    assert "POST-H-033-A-VALIDATOR-INVENTORY-MODULE" in doc_ids
    assert "POST-H-033-A-VALIDATOR-INVENTORY-TEST" in doc_ids

    schema_ids = {item["schema_id"] for item in schema_catalog["schemas"]}
    assert "SCHEMA-DEVPL-VALIDATOR-INVENTORY-V1" in schema_ids
    assert "SCHEMA-DEVPL-VALIDATOR-MIGRATION-REPORT-V1" in schema_ids

    assert any(contract["contract_id"] == "post-h-033-validator-inventory-migration-plan" for contract in tcr_v1["contracts"])
    contract_v2 = next(contract for contract in tcr_v2["contracts"] if contract["contract_id"] == "post-h-033-validator-inventory-migration-plan")
    assert contract_v2["subgate_id"] == "schema-backed-validator-governance"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False

    assert state["current_micro_sprint"] in {"POST-H-033-C", "POST-H-033-D"}
    assert state["next_micro_sprint"] in {"POST-H-033-D", "POST-H-033-E"}
    assert state["post_h_033_a_closed"] is True
    assert state["current_repo"] in {"repo_DevPilot_Local_304_POST_H_033_C.zip", "repo_DevPilot_Local_305_POST_H_033_D.zip"}
    assert state["post_h_032_status"] == "closed/advanced-ai-agents-governed"
    assert state["post_h_033_status"] in {"active/readiness-requirements-registry-implemented-initial", "active/miasi-semantic-rules-registry-implemented-initial"}
    assert state["post_h_033_a_runtime_behavior_changed"] is False
    assert state["post_h_033_a_llm_judge_required"] is False
    assert state["post_h_033_a_critical_defenses_disable_allowed"] is False

    assert "POST-H-033-A — Validator inventory and migration plan" in readme
    assert "POST-H-033-A — Validator inventory and migration plan" in runbook
    assert 'status: approved' in backlog
    assert any(marker in backlog for marker in ['implementation_status: "active/post-h-033-c-implemented-initial"', 'implementation_status: "active/post-h-033-d-implemented-initial"'])
    assert 'status: approved' in top_level
