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
def _hotspots_result():
    from devpilot_core.architecture.hotspots import ArchitectureHotspotsBuilder

    return ArchitectureHotspotsBuilder(ROOT).build()


def test_architecture_hotspots_builder_ranks_top20_without_execution() -> None:
    from devpilot_core.cli_models import ExitCode

    result = _hotspots_result()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["hotspots_total"] == 20
    assert summary["top_hotspots_limit"] == 20
    assert summary["technical_hotspots_total"] >= 1
    assert summary["core_domain_hotspots_total"] >= 1
    assert summary["module_hotspots_total"] >= 1
    assert summary["package_hotspots_total"] >= 1
    assert summary["blocking_findings_total"] == 0
    assert summary["dry_run"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False


def test_architecture_hotspots_payload_validates_and_flags_cli() -> None:
    from devpilot_core.schemas import SchemaValidator

    result = _hotspots_result()
    architecture_map = result.data["architecture_map"]
    hotspots = architecture_map["hotspots"]
    packages = {package["package"]: package for package in architecture_map["packages"]}

    assert architecture_map["created_by"] == "POST-H-005-D"
    assert architecture_map["summary"]["hotspots_total"] == 20
    assert hotspots
    assert hotspots[0]["subject_id"] in {"devpilot_core.cli", "devpilot_core.cli.py"} or "cli" in hotspots[0]["subject_id"]
    assert any(hotspot["subject_id"] == "devpilot_core.cli" for hotspot in hotspots)
    assert any(hotspot["metadata"]["technical_hotspot"] is True for hotspot in hotspots)
    assert any(hotspot["metadata"]["core_domain_hotspot"] is True for hotspot in hotspots)
    assert all(hotspot["reasons"] for hotspot in hotspots)
    assert all(hotspot["recommendations"] for hotspot in hotspots)
    assert all("raw_metrics" in hotspot["metadata"] for hotspot in hotspots)
    assert packages["devpilot_core.cli"]["metadata"]["hotspot_score_materialized"] is True
    assert packages["devpilot_core.cli"]["metadata"]["top_hotspot_score"] > 0
    assert architecture_map["safety"]["dry_run"] is True
    assert architecture_map["safety"]["network_used"] is False

    validation = SchemaValidator(ROOT).validate_payload(
        schema="ArchitectureMap",
        payload=architecture_map,
        instance_label="unit-test:architecture-hotspots",
    )
    assert validation.ok is True, validation.to_dict()


def test_architecture_hotspots_exposes_advisory_findings_and_formula() -> None:
    result = _hotspots_result()
    findings = [finding.to_dict() for finding in result.findings]

    assert result.data["summary"]["score_formula"].startswith("LOC + fan-in + fan-out")
    assert result.data["score_formula"]["loc_weight"] == 35
    assert result.data["score_formula"]["criticality_weight"] == 10
    assert any(finding["id"] == "ARCHITECTURE_HOTSPOT_TOP5" for finding in findings)
    assert any(finding["id"] == "ARCHITECTURE_HOTSPOTS_PASS" for finding in findings)
    assert all(finding.get("metadata", {}).get("enforcement") != "blocking" for finding in findings)


def test_architecture_hotspots_cli_parser_is_registered_in_cli_source() -> None:
    cli_source = _read("src/devpilot_core/cli.py")

    assert 'architecture_sub.add_parser("hotspots"' in cli_source
    assert "architecture_hotspots_command" in cli_source
    assert "ArchitectureHotspotsBuilder" in cli_source


def test_post_h_005_d_docs_and_manifest_are_synchronized() -> None:
    backlog = _read("docs/backlogs/POST-H-005_architecture_map_executable.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    changelog = _read("docs/release/CHANGELOG.md")
    audit = _read("docs/audits/post_h_005_d_hotspot_analyzer_report.md")
    manifest = _read_json("docs/post_h_005_d_manifest.json")

    assert "POST-H-005-D — Hotspot analyzer" in backlog
    assert "Estado: `implemented-initial`" in backlog
    assert "Último micro-sprint implementado: `POST-H-005-D" in readme
    assert "Siguiente micro-sprint: `POST-H-005-E" in readme
    assert "POST-H-005-D — Operación del hotspot analyzer ArchitectureMap" in runbook
    assert "post-h-005-d" in changelog
    assert "architecture hotspots --json" in audit
    assert manifest["id"] == "POST-H-005-D"
    assert manifest["status"] == "implemented-initial"
    assert manifest["inventory_ast_implemented"] is True
    assert manifest["dependency_graph_implemented"] is True
    assert manifest["hotspot_analyzer_implemented"] is True
    assert manifest["top_hotspots_implemented"] is True
    assert manifest["technical_vs_core_domain_classification_implemented"] is True
    assert manifest["quality_gate_subgate_added"] is False
    assert manifest["network_used"] is False
    assert manifest["external_api_used"] is False
    assert manifest["source_mutations_performed"] is False
