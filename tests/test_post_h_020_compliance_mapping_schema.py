from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_020_a_control_mapping_schema_is_registered_and_validates_registry() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="ComplianceControlMapping",
        instance=".devpilot/compliance/control_mappings.json",
    )

    assert result.ok, result.to_dict()

    catalog = read_json("docs/schemas/schema_catalog.json")
    entries = {item["schema_id"]: item for item in catalog["schemas"]}
    assert "SCHEMA-DEVPL-COMPLIANCE-CONTROL-MAPPING-V1" in entries
    assert entries["SCHEMA-DEVPL-COMPLIANCE-CONTROL-MAPPING-V1"]["path"] == "docs/schemas/compliance_control_mapping.schema.json"


def test_post_h_020_a_control_mappings_require_non_certifying_claims_and_evidence() -> None:
    payload = read_json(".devpilot/compliance/control_mappings.json")

    assert payload["created_by"] == "POST-H-020-A"
    assert payload["status"] == "implemented-initial"
    assert payload["certification_claimed"] is False
    assert payload["legal_advice_claimed"] is False
    assert "not a certification" in payload["disclaimer"].lower()
    assert payload["safety"]["local_first"] is True
    assert payload["safety"]["network_used"] is False
    assert payload["safety"]["external_api_used"] is False

    controls = payload["controls"]
    assert len(controls) >= 6
    required_domains = {"security", "testing", "policy", "release", "observability", "documentation"}
    assert required_domains <= {control["domain"] for control in controls}
    assert all(control["control_id"] for control in controls)
    assert all(control["risk_level"] for control in controls)
    assert all(control["required_evidence"] for control in controls)


def test_post_h_020_a_control_mapping_schema_blocks_certification_claim() -> None:
    payload = read_json(".devpilot/compliance/control_mappings.json")
    invalid = copy.deepcopy(payload)
    invalid["certification_claimed"] = True

    result = SchemaValidator(ROOT).validate_payload(
        schema="ComplianceControlMapping",
        payload=invalid,
        instance_label="in-memory:certification-claim",
    )

    assert not result.ok
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)
