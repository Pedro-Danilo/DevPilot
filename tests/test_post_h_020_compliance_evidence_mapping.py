from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_020_a_evidence_mapping_schema_is_registered_and_validates_registry() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="ComplianceEvidenceMapping",
        instance=".devpilot/compliance/evidence_mappings.json",
    )

    assert result.ok, result.to_dict()

    catalog = read_json("docs/schemas/schema_catalog.json")
    entries = {item["schema_id"]: item for item in catalog["schemas"]}
    assert "SCHEMA-DEVPL-COMPLIANCE-EVIDENCE-MAPPING-V1" in entries
    assert entries["SCHEMA-DEVPL-COMPLIANCE-EVIDENCE-MAPPING-V1"]["path"] == "docs/schemas/compliance_evidence_mapping.schema.json"


def test_post_h_020_a_evidence_mappings_link_to_known_controls() -> None:
    controls_payload = read_json(".devpilot/compliance/control_mappings.json")
    evidence_payload = read_json(".devpilot/compliance/evidence_mappings.json")
    known_controls = {control["control_id"] for control in controls_payload["controls"]}

    assert evidence_payload["certification_claimed"] is False
    assert evidence_payload["legal_advice_claimed"] is False
    assert "not certification" in evidence_payload["disclaimer"].lower()
    assert len(evidence_payload["evidence"]) >= len(known_controls)

    linked_controls = {
        control_id
        for evidence in evidence_payload["evidence"]
        for control_id in evidence["control_ids"]
    }
    assert known_controls <= linked_controls
    assert all(
        evidence.get("source_command") or evidence.get("source_paths") or evidence.get("justification")
        for evidence in evidence_payload["evidence"]
    )


def test_post_h_020_a_evidence_mapping_schema_blocks_missing_source_or_justification() -> None:
    payload = read_json(".devpilot/compliance/evidence_mappings.json")
    invalid = copy.deepcopy(payload)
    invalid["evidence"][0].pop("source_command", None)
    invalid["evidence"][0].pop("source_paths", None)
    invalid["evidence"][0].pop("justification", None)

    result = SchemaValidator(ROOT).validate_payload(
        schema="ComplianceEvidenceMapping",
        payload=invalid,
        instance_label="in-memory:missing-source",
    )

    assert not result.ok
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)
