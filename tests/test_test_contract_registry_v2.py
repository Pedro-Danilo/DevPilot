from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.schemas import SchemaValidator
from devpilot_core.testing import (
    TestContractCriticality as ContractCriticality,
    TestContractRegistry,
    TestContractRegistryV2Design as RegistryV2Design,
    TestContractRiskLevel as ContractRiskLevel,
    load_registry_v2_fixture,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "test_contract_registry_v2"


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_test_contract_registry_v2_schema_is_registered() -> None:
    catalog = read_json("docs/schemas/schema_catalog.json")
    entries = {item["schema_id"]: item for item in catalog["schemas"]}

    assert "SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V2" in entries
    entry = entries["SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V2"]
    assert entry["path"] == "docs/schemas/test_contract_registry_v2.schema.json"
    assert entry["contract"] == "TestContractRegistryV2"
    assert (ROOT / entry["path"]).exists()


def test_test_contract_registry_v2_valid_fixture_passes_schema() -> None:
    result = RegistryV2Design(ROOT).validate_file(FIXTURES / "valid_minimal_registry.json")

    assert result.ok, result.to_dict()
    assert result.data["post_h_003_a"]["schema_version"] == "2.0"
    assert result.data["post_h_003_a"]["migrates_v1"] is False
    assert any(finding.id == "TEST_CONTRACT_REGISTRY_V2_SCHEMA_PASS" for finding in result.findings)


def test_test_contract_registry_v2_rejects_missing_safety_flags() -> None:
    result = RegistryV2Design(ROOT).validate_file(FIXTURES / "invalid_missing_safety_flags.json")

    assert not result.ok
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)
    assert any("network_allowed" in finding.message or "required" in finding.message for finding in result.findings)


def test_test_contract_registry_v2_rejects_network_without_exception() -> None:
    result = RegistryV2Design(ROOT).validate_file(FIXTURES / "invalid_network_without_exception.json")

    assert not result.ok
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)
    messages = "\n".join(finding.message for finding in result.findings)
    assert "safety_exception" in messages or "manual" in messages or "release" in messages


def test_test_contract_registry_v1_still_validates_during_v2_design() -> None:
    result = TestContractRegistry(ROOT).validate()

    assert result.ok, result.to_dict()
    assert result.data["summary"]["contracts_total"] == 89
    assert result.data["summary"]["historical_contracts_total"] == 78
    assert result.data["summary"]["global_state_contracts_total"] == 1


def test_test_contract_registry_v2_keeps_criticality_and_risk_separate() -> None:
    payload = load_registry_v2_fixture(FIXTURES / "valid_minimal_registry.json")
    contract = payload["contracts"][0]

    assert contract["criticality"] == ContractCriticality.P0.value
    assert contract["risk_level"] == ContractRiskLevel.HIGH.value
    assert contract["criticality"] != contract["risk_level"]
    assert "criticality" in contract
    assert "risk_level" in contract


def test_test_contract_registry_v2_schema_rejects_invalid_enum_values() -> None:
    payload = load_registry_v2_fixture(FIXTURES / "valid_minimal_registry.json")
    payload["contracts"][0]["criticality"] = "high"
    payload["contracts"][0]["risk_level"] = "P0"

    result = SchemaValidator(ROOT).validate_payload(
        schema="TestContractRegistryV2",
        payload=payload,
        instance_label="in-memory:invalid-enums",
    )

    assert not result.ok
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)


def test_post_h_003_backlog_approved_and_documents_schema_design() -> None:
    text = (ROOT / "docs" / "backlogs" / "POST-H-003_test_contract_registry_2.md").read_text(encoding="utf-8")

    assert 'status: "approved"' in text
    assert 'version: "1.0.0"' in text
    assert "POST-H-003-A" in text
    assert "SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V2" in text
    assert "POST-H-003-B" in text
    assert "POST-H-003-E" in text
    assert 'implementation_status: "closed"' in text
