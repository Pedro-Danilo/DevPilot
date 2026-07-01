from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_020_a_mapping_report_schema_is_registered() -> None:
    catalog = read_json("docs/schemas/schema_catalog.json")
    entries = {item["schema_id"]: item for item in catalog["schemas"]}

    assert "SCHEMA-DEVPL-COMPLIANCE-MAPPING-REPORT-V1" in entries
    entry = entries["SCHEMA-DEVPL-COMPLIANCE-MAPPING-REPORT-V1"]
    assert entry["path"] == "docs/schemas/compliance_mapping_report.schema.json"
    assert entry["contract"] == "ComplianceMappingReport"


def test_post_h_020_a_report_schema_blocks_certification_and_requires_disclaimer() -> None:
    valid_report = {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-COMPLIANCE-MAPPING-REPORT-V1",
        "created_by": "POST-H-020-A",
        "report_id": "synthetic-compliance-mapping-report",
        "generated_at_utc": "2026-07-01T00:00:00Z",
        "pack_id": "devpilot.local.governance.baseline",
        "ok": True,
        "certification_claimed": False,
        "legal_advice_claimed": False,
        "controls_total": 7,
        "controls_mapped": 7,
        "controls_with_evidence": 7,
        "controls_missing_evidence": 0,
        "blocking_findings_total": 0,
        "disclaimer_present": True,
        "domain_coverage": {"security": 2, "testing": 1},
        "findings": [],
        "safety": {
            "local_first": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
        },
    }
    result = SchemaValidator(ROOT).validate_payload(
        schema="ComplianceMappingReport",
        payload=valid_report,
        instance_label="in-memory:valid-report",
    )
    assert result.ok, result.to_dict()

    invalid = copy.deepcopy(valid_report)
    invalid["certification_claimed"] = True
    invalid["disclaimer_present"] = False
    result = SchemaValidator(ROOT).validate_payload(
        schema="ComplianceMappingReport",
        payload=invalid,
        instance_label="in-memory:invalid-certifying-report",
    )
    assert not result.ok
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)


def test_post_h_020_a_human_docs_keep_no_certification_language() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-020_compliance_mapping_packs.md").read_text(encoding="utf-8")
    implementation = (ROOT / "docs/POST-H-020_compliance_mapping_packs.md").read_text(encoding="utf-8")
    audit = (ROOT / "docs/audits/post_h_020_a_compliance_mapping_schema_registry_report.md").read_text(encoding="utf-8")

    for text in (backlog, implementation, audit):
        lowered = text.lower()
        assert "no certificación" in lowered or "not certification" in lowered
        assert "no asesoría legal" in lowered or "not legal advice" in lowered
        assert "certification_claimed=false" in lowered or '"certification_claimed": false' in lowered
