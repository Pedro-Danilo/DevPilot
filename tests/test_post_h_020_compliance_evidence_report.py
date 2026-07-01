from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.compliance import (
    ComplianceEvidenceCollector,
    ComplianceMappingReporter,
    ComplianceMappingReportOptions,
)
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_post_h_020_c_evidence_collector_is_local_and_does_not_execute_commands() -> None:
    result = ComplianceEvidenceCollector(ROOT).collect()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["controls_total"] >= 8
    assert summary["evidence_total"] >= 12
    assert summary["evidence_available_total"] == summary["evidence_total"]
    assert summary["missing_source_paths_total"] == 0
    assert summary["commands_executed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["certification_claimed"] is False
    assert summary["legal_advice_claimed"] is False
    assert all(item["source_command_executed"] is False for item in result.data["evidence"])


def test_post_h_020_c_report_is_schema_valid_and_non_certifying(tmp_path: Path) -> None:
    result = ComplianceMappingReporter(
        ROOT,
        ComplianceMappingReportOptions(
            output_json=str(tmp_path / "compliance_mapping_report.json"),
            output_markdown=str(tmp_path / "compliance_mapping_report.md"),
        ),
    ).build(write_report=True)

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    report = result.data["report"]
    assert summary["reports_written"] is True
    assert report["schema_id"] == "SCHEMA-DEVPL-COMPLIANCE-MAPPING-REPORT-V1"
    assert report["ok"] is True
    assert report["certification_claimed"] is False
    assert report["legal_advice_claimed"] is False
    assert report["disclaimer_present"] is True
    assert report["safety"]["network_used"] is False
    assert report["safety"]["external_api_used"] is False
    assert report["safety"]["mutations_performed"] is False
    assert SchemaValidator(ROOT).validate_payload(
        schema="ComplianceMappingReport",
        payload=report,
        instance_label="memory:compliance_mapping_report",
    ).ok
    assert (tmp_path / "compliance_mapping_report.json").is_file()
    assert "no certificación" in (tmp_path / "compliance_mapping_report.md").read_text(encoding="utf-8").lower()


def test_post_h_020_c_report_surfaces_missing_evidence(tmp_path: Path) -> None:
    controls = _read_json(".devpilot/compliance/control_mappings.json")
    evidence = copy.deepcopy(_read_json(".devpilot/compliance/evidence_mappings.json"))
    evidence["evidence"][0]["source_paths"] = ["missing/post_h_020_c_evidence.json"]
    controls_path = tmp_path / "control_mappings.json"
    evidence_path = tmp_path / "evidence_mappings.json"
    _write_json(controls_path, controls)
    _write_json(evidence_path, evidence)

    result = ComplianceMappingReporter(
        ROOT,
        ComplianceMappingReportOptions(
            control_mappings_path=str(controls_path),
            evidence_mappings_path=str(evidence_path),
        ),
    ).build()

    assert result.ok is False
    assert result.data["summary"]["missing_source_paths_total"] >= 1
    assert result.data["report"]["ok"] is False
    assert result.data["report"]["controls_missing_evidence"] == 0
    assert any(finding.id == "COMPLIANCE_EVIDENCE_SOURCE_PATH_MISSING" for finding in result.findings)
    assert any(finding.id == "COMPLIANCE_EVIDENCE_NOT_AVAILABLE" for finding in result.findings)


def test_post_h_020_c_cli_mapping_report_generates_outputs() -> None:
    for relative in ["outputs/reports/compliance_mapping_report.json", "outputs/reports/compliance_mapping_report.md"]:
        path = ROOT / relative
        if path.exists():
            path.unlink()

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "compliance",
            "mapping",
            "report",
            "--json",
            "--write-report",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "compliance mapping report"
    assert payload["data"]["summary"]["reports_written"] is True
    assert payload["data"]["summary"]["commands_executed"] is False
    report = _read_json("outputs/reports/compliance_mapping_report.json")
    assert report["ok"] is True
    assert report["certification_claimed"] is False
    assert report["legal_advice_claimed"] is False
