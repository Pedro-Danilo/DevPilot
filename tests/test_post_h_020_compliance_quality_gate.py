from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.auditpack import AuditPackV2BuildOptions, AuditPackV2Builder
from devpilot_core.compliance import ComplianceMappingQualityGate, ComplianceMappingQualityGateOptions
from devpilot_core.quality import QualityGate, QualityGateOptions

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_post_h_020_d_compliance_mapping_quality_gate_passes() -> None:
    result = ComplianceMappingQualityGate(ROOT).run()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["quality_gate_subgate"] == "compliance-mapping-pack"
    assert summary["validator_ok"] is True
    assert summary["collector_ok"] is True
    assert summary["reporter_ok"] is True
    assert summary["audit_pack_dry_run_ok"] is True
    assert summary["audit_pack_manifest_has_compliance_mapping"] is True
    assert summary["eval_signal_present"] is True
    assert summary["eval_suite_id"] == "compliance-pack-integrity"
    assert summary["controls_total"] >= 8
    assert summary["controls_missing_evidence"] == 0
    assert summary["critical_controls_missing_evidence"] == 0
    assert summary["certification_claimed"] is False
    assert summary["legal_advice_claimed"] is False
    assert summary["disclaimer_present"] is True
    assert summary["source_command_values_executed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["blocking_findings_total"] == 0


def test_post_h_020_d_quality_gate_blocks_certification_claims(tmp_path: Path) -> None:
    controls = copy.deepcopy(_read_json(".devpilot/compliance/control_mappings.json"))
    evidence = _read_json(".devpilot/compliance/evidence_mappings.json")
    controls["certification_claimed"] = True
    controls_path = tmp_path / "control_mappings.json"
    evidence_path = tmp_path / "evidence_mappings.json"
    _write_json(controls_path, controls)
    _write_json(evidence_path, evidence)

    result = ComplianceMappingQualityGate(
        ROOT,
        options=ComplianceMappingQualityGateOptions(
            control_mappings_path=str(controls_path),
            evidence_mappings_path=str(evidence_path),
        ),
    ).run()

    assert result.ok is False
    assert result.data["summary"]["certification_claimed"] is True
    assert any(finding.id.endswith("COMPLIANCE_CERTIFICATION_CLAIM_BLOCKED") for finding in result.findings)


def test_post_h_020_d_audit_pack_manifest_includes_compliance_mapping_summary() -> None:
    result = AuditPackV2Builder(ROOT).build(AuditPackV2BuildOptions(dry_run=True, execute=False))

    assert result.ok, result.to_dict()
    manifest = result.data["manifest"]
    summary = manifest["compliance_mapping"]
    assert summary["created_by"] == "POST-H-020-D"
    assert summary["available"] is True
    assert summary["controls_total"] >= 8
    assert summary["controls_missing_evidence"] == 0
    assert summary["certification_claimed"] is False
    assert summary["legal_advice_claimed"] is False
    assert summary["source_command_values_executed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False


def test_post_h_020_d_quality_gate_hardening_profile_includes_subgate() -> None:
    gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    subgate_ids = [subgate.id for subgate in gate._subgates()]

    assert "compliance-mapping-pack" in subgate_ids
    assert subgate_ids.index("plugin-sandbox-design") < subgate_ids.index("compliance-mapping-pack")
