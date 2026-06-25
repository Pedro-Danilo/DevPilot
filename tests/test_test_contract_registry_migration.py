from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.schemas import SchemaValidator
from devpilot_core.testing import TestContractRegistry, TestContractRegistryV2MigrationOptions, TestContractRegistryV2Migrator

ROOT = Path(__file__).resolve().parents[1]


def _current_v1_contracts_total() -> int:
    return len(read_json(".devpilot/testing/test_contract_registry.json").get("contracts", []))


def read_json(path: str | Path) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8") if isinstance(path, str) else path.read_text(encoding="utf-8"))


def test_test_contract_registry_v2_migration_dry_run_preserves_v1_and_validates_schema(tmp_path: Path) -> None:
    output = tmp_path / "test_contract_registry_v2.json"
    result = TestContractRegistryV2Migrator(ROOT).migrate()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    expected_total = _current_v1_contracts_total()
    assert summary["contracts_v1_total"] == expected_total
    assert summary["contracts_v2_total"] == expected_total
    assert summary["classification_gaps_total"] == expected_total
    assert summary["needs_review_total"] >= 1
    assert summary["v1_registry_preserved"] is True
    assert summary["dry_run"] is True
    assert summary["reports_written"] is False
    assert summary["mutations_performed"] is False
    assert not output.exists()

    registry = result.data["registry"]
    assert registry["schema_version"] == "2.0"
    assert registry["created_by"] == "POST-H-003-B"
    assert registry["generated_from"] == ".devpilot/testing/test_contract_registry.json"
    assert registry["compatibility"]["compatibility_mode"] == "migration-dry-run"
    assert len(registry["contracts"]) == expected_total

    schema_result = SchemaValidator(ROOT).validate_payload(
        schema="TestContractRegistryV2",
        payload=registry,
        instance_label="in-memory:test-contract-registry-v2-dry-run-test",
    )
    assert schema_result.ok, schema_result.to_dict()


def test_test_contract_registry_v2_migration_write_output_is_explicit_and_valid() -> None:
    output = ROOT / ".devpilot" / "testing" / "test_contract_registry_v2_test_output.json"
    try:
        result = TestContractRegistryV2Migrator(
            ROOT,
            TestContractRegistryV2MigrationOptions(write_output=output),
        ).migrate()

        assert result.ok, result.to_dict()
        assert result.data["summary"]["reports_written"] is True
        assert result.data["summary"]["dry_run"] is False
        assert result.data["summary"]["mutations_performed"] is True
        assert output.exists()

        persisted = json.loads(output.read_text(encoding="utf-8"))
        assert len(persisted["contracts"]) == _current_v1_contracts_total()
        assert persisted["contracts"][0]["schema_version"] == "2.0"

        schema_result = SchemaValidator(ROOT).validate(schema="TestContractRegistryV2", instance=output)
        assert schema_result.ok, schema_result.to_dict()
    finally:
        output.unlink(missing_ok=True)


def test_test_contract_registry_v2_migration_refuses_to_overwrite_v1() -> None:
    result = TestContractRegistryV2Migrator(
        ROOT,
        TestContractRegistryV2MigrationOptions(write_output=".devpilot/testing/test_contract_registry.json"),
    ).migrate()

    assert not result.ok
    assert any(finding.id == "TEST_CONTRACT_V2_REFUSES_V1_OVERWRITE" for finding in result.findings)
    assert TestContractRegistry(ROOT).validate().ok


def test_migrated_registry_v2_file_is_present_and_schema_valid_after_post_h_003_b() -> None:
    path = ROOT / ".devpilot" / "testing" / "test_contract_registry_v2.json"

    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["created_by"] == "POST-H-003-B"
    assert payload["status"] == "implemented-initial"
    assert len(payload["contracts"]) == _current_v1_contracts_total()
    assert {item["source_contract_id"] for item in payload["contracts"] if item.get("source_contract_id")}

    result = SchemaValidator(ROOT).validate(schema="TestContractRegistryV2", instance=path)
    assert result.ok, result.to_dict()


def test_migrated_registry_v2_classifies_core_contracts_without_collapsing_risk_and_criticality() -> None:
    payload = read_json(".devpilot/testing/test_contract_registry_v2.json")
    contracts = {item["contract_id"]: item for item in payload["contracts"]}

    assert contracts["project-global-state"]["criticality"] == "P0"
    assert contracts["project-global-state"]["risk_level"] == "high"
    assert contracts["project-global-state"]["criticality"] != contracts["project-global-state"]["risk_level"]
    assert contracts["project-global-state"]["source_mutations_allowed"] is True
    assert contracts["project-global-state"]["requires_human_approval"] is True
    assert "safety_exception" in contracts["project-global-state"]

    assert contracts["schema-registry"]["domain"] == "governance.schemas"
    assert contracts["schema-registry"]["test_type"] == "schema"
    assert contracts["schema-registry"]["required_for_release"] is True

    assert contracts["post-h-003-test-contract-registry-2"]["domain"] == "governance.testing"
    assert contracts["post-h-003-test-contract-registry-2"]["capability"] == "TestContractRegistryV2"
    assert contracts["post-h-003-test-contract-registry-2"]["criticality"] == "P0"
    assert contracts["post-h-003-test-contract-registry-2"]["classification_status"] == "explicit"

    historical = [item for item in payload["contracts"] if item["domain"] == "documentation.historical"]
    assert len(historical) == 78
    assert all(item["test_type"] == "documentation" for item in historical)
    assert all(item["risk_level"] in {"medium", "low"} for item in historical)


def test_post_h_003_b_documentation_is_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-003_test_contract_registry_2.md").read_text(encoding="utf-8")
    design = (ROOT / "docs/04_quality/test_contract_registry_2_design.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    assert "POST-H-003-B" in backlog
    assert "Migrador v1 → v2 dry-run" in backlog
    assert 'version: "1.0.0"' in backlog
    assert "POST-H-003-B" in design
    assert "test-contracts migrate-v2" in runbook
    assert "POST-H-003-B" in readme
    assert "post-h-003-b" in changelog
