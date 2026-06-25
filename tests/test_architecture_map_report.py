from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _map_result():
    from devpilot_core.architecture.report import ArchitectureMapReportBuilder

    return ArchitectureMapReportBuilder(ROOT).build()


def test_architecture_map_report_builder_validates_ownership_and_contract() -> None:
    from devpilot_core.cli_models import ExitCode

    result = _map_result()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["packages_total"] >= 40
    assert summary["modules_total"] >= 200
    assert summary["dependencies_total"] >= 200
    assert summary["hotspots_total"] == 20
    assert summary["ownership_entries_total"] >= 12
    assert summary["ownership_gaps_total"] >= 1
    assert summary["critical_packages_missing_test_contracts_total"] == 0
    assert summary["schema_validation_ok"] is True
    assert summary["blocking_findings_total"] == 0
    assert summary["dry_run"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["remote_execution_enabled"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["plugin_execution_enabled"] is False


def test_architecture_map_report_payload_is_schema_valid_and_actionable() -> None:
    from devpilot_core.schemas import SchemaValidator

    result = _map_result()
    architecture_map = result.data["architecture_map"]

    assert architecture_map["created_by"] == "POST-H-005-E"
    assert architecture_map["map_id"] == "devpilot-post-h-005-executable-architecture-map"
    assert architecture_map["summary"]["hotspots_total"] == 20
    assert architecture_map["summary"]["ownership_gaps_total"] >= 1
    assert architecture_map["recommendations"]
    assert any("POST-H-006" in recommendation for recommendation in architecture_map["recommendations"])
    assert any(gap["gap_type"] == "missing-owner" for gap in architecture_map["ownership_gaps"])
    assert any(edge["policy"] == "forbidden" for edge in architecture_map["dependencies"])
    assert any(edge["policy"] == "restricted" for edge in architecture_map["dependencies"])
    assert any(hotspot["subject_id"] == "devpilot_core.cli" for hotspot in architecture_map["hotspots"])

    validation = SchemaValidator(ROOT).validate_payload(
        schema="ArchitectureMap",
        payload=architecture_map,
        instance_label="unit-test:architecture-map-final",
    )
    assert validation.ok is True, validation.to_dict()


def test_architecture_map_builder_writes_raw_schema_valid_reports() -> None:
    from devpilot_core.architecture.report import ArchitectureMapReportBuilder, ArchitectureMapReportOptions

    outputs = ROOT / "outputs" / "reports"
    for name in ["architecture_map.json", "architecture_map.md"]:
        path = outputs / name
        if path.exists():
            path.unlink()

    result = ArchitectureMapReportBuilder(ROOT, ArchitectureMapReportOptions(write_report=True)).build()

    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["reports_written"] is True
    assert result.data["summary"]["output_json"] == "outputs/reports/architecture_map.json"
    assert result.data["summary"]["output_markdown"] == "outputs/reports/architecture_map.md"
    raw_json = ROOT / "outputs/reports/architecture_map.json"
    raw_md = ROOT / "outputs/reports/architecture_map.md"
    assert raw_json.exists()
    assert raw_md.exists()
    raw_payload = json.loads(raw_json.read_text(encoding="utf-8"))
    assert raw_payload["schema_id"] == "SCHEMA-DEVPL-ARCHITECTURE-MAP-V1"
    assert raw_payload["summary"]["hotspots_total"] == 20
    assert "POST-H-005 — Executable architecture map report" in raw_md.read_text(encoding="utf-8")


def test_architecture_map_cli_contract_is_registered() -> None:
    cli = _read("src/devpilot_core/cli.py")

    assert 'architecture_sub.add_parser("map"' in cli
    assert "ArchitectureMapReportBuilder" in cli
    assert "ArchitectureMapReportOptions" in cli
    assert "architecture_map_command" in cli


def test_architecture_map_quality_gate_subgate_is_registered() -> None:
    quality_gate = _read("src/devpilot_core/quality/gate.py")

    assert '"architecture-map"' in quality_gate
    assert "ArchitectureMapReportBuilder" in quality_gate
    assert "ArchitectureMapReportOptions" in quality_gate
    assert "POST-H-005 executable architecture map" in quality_gate
    assert "def _architecture_map" in quality_gate


def test_post_h_005_e_docs_manifest_and_contracts_are_synchronized() -> None:
    backlog = _read("docs/backlogs/POST-H-005_architecture_map_executable.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    changelog = _read("docs/release/CHANGELOG.md")
    audit = _read("docs/audits/post_h_005_e_architecture_map_report.md")
    closure = _read("docs/audits/post_h_005_closure_report.md")
    manifest = _read_json("docs/post_h_005_e_manifest.json")
    v1 = _read_json(".devpilot/testing/test_contract_registry.json")
    v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    v1_contracts = {item["contract_id"]: item for item in v1["contracts"]}
    v2_contracts = {item["contract_id"]: item for item in v2["contracts"]}

    assert 'implementation_status: "closed"' in backlog
    assert "POST-H-005-E — Ownership validation y reporte" in backlog
    assert "POST-H-005" in readme
    assert "POST-H-006" in readme
    assert "POST-H-005-E — Operación del reporte final ArchitectureMap" in runbook
    assert "post-h-005-e" in changelog
    assert "architecture map --write-report --json" in audit
    assert "POST-H-006 — CLI command registry" in closure
    assert manifest["id"] == "POST-H-005-E"
    assert manifest["parent_hito_status"] == "closed"
    assert manifest["next_hito"] == "POST-H-006"
    assert manifest["final_architecture_map_report_implemented"] is True
    assert manifest["quality_gate_subgate_added"] == "architecture-map"
    assert manifest["network_used"] is False
    assert manifest["external_api_used"] is False
    assert manifest["source_mutations_performed"] is False
    assert "post-h-005-architecture-map" in v1_contracts
    assert "post-h-005-architecture-map" in v2_contracts
    assert v1_contracts["post-h-005-architecture-map"]["owner"] == "POST-H-005-E"
    assert v2_contracts["post-h-005-architecture-map"]["domain"] == "governance.schemas"
    assert v2_contracts["post-h-005-architecture-map"]["criticality"] == "P0"
    assert v2_contracts["post-h-005-architecture-map"]["classification_status"] == "explicit"
