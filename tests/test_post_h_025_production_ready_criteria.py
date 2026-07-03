from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
CRITERIA_PATH = ROOT / ".devpilot" / "production" / "production_ready_local_criteria.json"

REQUIRED_HITOS = {
    "POST-H-002",
    "POST-H-003",
    "POST-H-004",
    "POST-H-005",
    "POST-H-006",
    "POST-H-007",
    "POST-H-008",
    "POST-H-009",
    "POST-H-010",
    "POST-H-011",
    "POST-H-012",
    "POST-H-013",
    "POST-H-014",
    "POST-H-015",
    "POST-H-016",
    "POST-H-017",
    "POST-H-024",
}
OPTIONAL_DESIGN_HITOS = {
    "POST-H-018",
    "POST-H-019",
    "POST-H-020",
    "POST-H-021",
    "POST-H-022",
    "POST-H-023",
}
NO_GO_KEYS = {
    "remote_execution_enabled",
    "connector_write_enabled",
    "plugin_execution_enabled",
    "external_apis_required",
    "compliance_certification_claim",
    "enterprise_ready_claim",
    "remote_ready_claim",
    "saas_ready_claim",
}


def _criteria() -> dict:
    return json.loads(CRITERIA_PATH.read_text(encoding="utf-8"))


def test_production_ready_local_criteria_validates_against_schema() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="ProductionReadyLocalCriteria",
        instance=".devpilot/production/production_ready_local_criteria.json",
    )

    assert result.ok, result.to_dict()
    assert result.data["summary"]["valid"] is True


def test_production_ready_local_report_schema_allows_block_but_blocks_overclaims() -> None:
    validator = SchemaValidator(ROOT)
    block_payload = {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-PRODUCTION-READY-LOCAL-REPORT-V1",
        "report_id": "production-ready-local-report-test-block",
        "created_by": "POST-H-025-B",
        "created_at": "2026-07-03T00:00:00Z",
        "scope": "production-ready-local",
        "decision": "BLOCK",
        "score": 87.5,
        "minimum_score": 90,
        "blocking_gaps_total": 2,
        "passed_hitos_total": 15,
        "required_hitos_total": 17,
        "no_go_gates_passed": True,
        "claims": {
            "production_ready_local": False,
            "enterprise_ready": False,
            "remote_ready": False,
            "compliance_certified": False,
            "saas_ready": False,
        },
        "no_go_gates": {key: False for key in NO_GO_KEYS},
        "evidence_results": [
            {"hito_id": "POST-H-024", "status": "pass", "required_for_pass": True, "findings_total": 0}
        ],
        "gaps": [
            {"gap_id": "missing-evidence", "severity": "block", "message": "Synthetic missing evidence."}
        ],
        "safety": {
            "local_first": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
        },
        "summary": {"preliminary": True},
        "limitations": ["Synthetic test payload."],
    }

    ok = validator.validate_payload(
        schema="ProductionReadyLocalReport",
        payload=block_payload,
        instance_label="synthetic-production-ready-local-block-report",
    )
    assert ok.ok, ok.to_dict()

    overclaim = dict(block_payload)
    overclaim["claims"] = dict(block_payload["claims"])
    overclaim["claims"]["enterprise_ready"] = True
    blocked = validator.validate_payload(
        schema="ProductionReadyLocalReport",
        payload=overclaim,
        instance_label="synthetic-production-ready-local-overclaim-report",
    )
    assert not blocked.ok
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in blocked.findings)


def test_criteria_maps_all_required_hitos_with_blocking_evidence() -> None:
    criteria = _criteria()

    assert set(criteria["required_hitos"]) == REQUIRED_HITOS
    assert set(criteria["optional_design_hitos"]) == OPTIONAL_DESIGN_HITOS
    evidence_map = {item["hito_id"]: item for item in criteria["evidence_map"]}
    assert REQUIRED_HITOS.issubset(evidence_map)

    for hito in REQUIRED_HITOS:
        item = evidence_map[hito]
        assert item["classification"] == "required"
        assert item["required_for_pass"] is True
        assert item["evidence"], hito
        assert any(evidence["blocker_on_missing"] for evidence in item["evidence"]), hito
        assert all(evidence["requirement_level"] in {"required", "blocker"} for evidence in item["evidence"])


def test_no_go_gates_and_claim_limits_are_explicit() -> None:
    criteria = _criteria()

    assert set(criteria["no_go_gates"]) == NO_GO_KEYS
    assert all(value is False for value in criteria["no_go_gates"].values())
    assert criteria["claims_allowed"] == {
        "production_ready_local": True,
        "enterprise_ready": False,
        "remote_ready": False,
        "compliance_certified": False,
        "saas_ready": False,
    }
    assert criteria["declaration_policy"]["block_by_default"] is True
    assert criteria["declaration_policy"]["pass_requires_zero_blocking_gaps"] is True
    assert criteria["blocking_gaps_allowed"] == 0
    assert criteria["minimum_score"] == 90


def test_versioned_artifacts_and_documentation_are_synchronized() -> None:
    criteria = _criteria()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-025_production_ready_declaration_gate.md").read_text(encoding="utf-8")

    assert (ROOT / "docs/schemas/production_ready_local_criteria.schema.json").exists()
    assert (ROOT / "docs/schemas/production_ready_local_report.schema.json").exists()
    assert (ROOT / "docs/audits/post_h_025_a_criteria_evidence_map_report.md").exists()
    assert (ROOT / "docs/post_h_025_a_manifest.json").exists()
    assert criteria["next_micro_sprint"] == "POST-H-025-B"
    assert 'status: "approved"' in backlog
    assert "POST-H-025-A — Criteria schema y evidence map" in readme
    assert "POST-H-025-A — Criteria schema y evidence map" in runbook
    assert "post-h-025-a" in changelog
    assert "POST-H-025-B — Evidence aggregator read-only" in readme
    assert "POST-H-025-B — Evidence aggregator read-only" in runbook
