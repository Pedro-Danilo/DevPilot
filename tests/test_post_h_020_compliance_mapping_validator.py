from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.compliance import ComplianceMappingValidator, ComplianceMappingValidatorOptions

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_mapping_pair(tmp_path: Path, controls: dict, evidence: dict) -> ComplianceMappingValidatorOptions:
    control_path = tmp_path / "control_mappings.json"
    evidence_path = tmp_path / "evidence_mappings.json"
    _write_json(control_path, controls)
    _write_json(evidence_path, evidence)
    return ComplianceMappingValidatorOptions(
        control_mappings_path=str(control_path),
        evidence_mappings_path=str(evidence_path),
    )


def test_post_h_020_b_mapping_validator_passes_baseline() -> None:
    result = ComplianceMappingValidator(ROOT).validate()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["controls_total"] >= 8
    assert summary["evidence_total"] >= 12
    assert summary["controls_missing_evidence"] == 0
    assert summary["critical_controls_missing_evidence"] == 0
    assert summary["blocking_findings_total"] == 0
    assert summary["certification_claimed"] is False
    assert summary["legal_advice_claimed"] is False
    assert summary["commands_executed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert {"security", "testing", "policy", "release", "observability", "agentic"} <= set(summary["domain_coverage"])


def test_post_h_020_b_mapping_validator_blocks_unmapped_required_evidence(tmp_path: Path) -> None:
    controls = _read_json(".devpilot/compliance/control_mappings.json")
    evidence = _read_json(".devpilot/compliance/evidence_mappings.json")
    invalid = copy.deepcopy(controls)
    invalid["controls"][0]["required_evidence"].append("missing-critical-evidence")

    result = ComplianceMappingValidator(
        ROOT,
        _write_mapping_pair(tmp_path, invalid, evidence),
    ).validate()

    assert result.ok is False
    assert int(result.exit_code) == 2
    assert any(finding.id == "COMPLIANCE_CONTROL_REQUIRED_EVIDENCE_UNMAPPED" for finding in result.findings)
    assert result.data["summary"]["critical_controls_missing_evidence"] == 1


def test_post_h_020_b_mapping_validator_blocks_certification_and_legal_claims(tmp_path: Path) -> None:
    controls = _read_json(".devpilot/compliance/control_mappings.json")
    evidence = _read_json(".devpilot/compliance/evidence_mappings.json")
    invalid_controls = copy.deepcopy(controls)
    invalid_evidence = copy.deepcopy(evidence)
    invalid_controls["certification_claimed"] = True
    invalid_evidence["legal_advice_claimed"] = True

    result = ComplianceMappingValidator(
        ROOT,
        _write_mapping_pair(tmp_path, invalid_controls, invalid_evidence),
    ).validate()

    assert result.ok is False
    assert any(finding.id == "COMPLIANCE_CERTIFICATION_CLAIM_BLOCKED" for finding in result.findings)
    assert any(finding.id == "COMPLIANCE_LEGAL_ADVICE_CLAIM_BLOCKED" for finding in result.findings)
    assert result.data["summary"]["certification_claimed"] is True
    assert result.data["summary"]["legal_advice_claimed"] is True


def test_post_h_020_b_mapping_validator_reports_missing_domain_coverage(tmp_path: Path) -> None:
    controls = _read_json(".devpilot/compliance/control_mappings.json")
    evidence = _read_json(".devpilot/compliance/evidence_mappings.json")
    invalid = copy.deepcopy(controls)
    invalid["controls"] = [control for control in invalid["controls"] if control["domain"] != "agentic"]

    result = ComplianceMappingValidator(
        ROOT,
        _write_mapping_pair(tmp_path, invalid, evidence),
    ).validate()

    assert result.ok is False
    assert any(
        finding.id == "COMPLIANCE_DOMAIN_COVERAGE_MISSING"
        and finding.metadata.get("domain") == "agentic"
        for finding in result.findings
    )
    assert "agentic" in result.data["summary"]["missing_required_domains"]


def test_post_h_020_b_mapping_validator_blocks_duplicate_ids_and_forbidden_source(tmp_path: Path) -> None:
    controls = _read_json(".devpilot/compliance/control_mappings.json")
    evidence = _read_json(".devpilot/compliance/evidence_mappings.json")
    invalid_controls = copy.deepcopy(controls)
    invalid_evidence = copy.deepcopy(evidence)
    invalid_controls["controls"].append(copy.deepcopy(invalid_controls["controls"][0]))
    invalid_evidence["evidence"][0]["source_command"] = "curl https://example.invalid/evidence"

    result = ComplianceMappingValidator(
        ROOT,
        _write_mapping_pair(tmp_path, invalid_controls, invalid_evidence),
    ).validate()

    assert result.ok is False
    assert any(finding.id == "COMPLIANCE_CONTROL_ID_DUPLICATE" for finding in result.findings)
    assert any(finding.id == "COMPLIANCE_EVIDENCE_FORBIDDEN_SOURCE_COMMAND" for finding in result.findings)
