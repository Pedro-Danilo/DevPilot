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
def _dependencies_result():
    from devpilot_core.architecture.dependencies import ArchitectureDependenciesBuilder

    return ArchitectureDependenciesBuilder(ROOT).build()


def test_architecture_dependencies_builder_materializes_edges_and_fan_metrics() -> None:
    from devpilot_core.cli_models import ExitCode

    result = _dependencies_result()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["modules_total"] >= 150
    assert summary["packages_total"] >= 20
    assert summary["module_edges_total"] > 0
    assert summary["package_edges_total"] > 0
    assert summary["dependencies_total"] == summary["package_edges_total"]
    assert summary["fan_in_total"] > 0
    assert summary["fan_out_total"] > 0
    assert summary["parse_errors_total"] == 0
    assert summary["dry_run"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False


def test_architecture_dependencies_payload_validates_and_contains_governed_edges() -> None:
    from devpilot_core.schemas import SchemaValidator

    result = _dependencies_result()
    architecture_map = result.data["architecture_map"]
    edges = {(edge["source"], edge["target"]): edge for edge in architecture_map["dependencies"]}
    packages = {package["package"]: package for package in architecture_map["packages"]}

    assert architecture_map["created_by"] == "POST-H-005-C"
    assert architecture_map["summary"]["dependencies_total"] > 0
    assert edges
    assert any(edge["kind"] == "internal-import" for edge in architecture_map["dependencies"])
    assert any(edge["sensitive"] is True for edge in architecture_map["dependencies"])
    assert any(edge["policy"] in {"restricted", "forbidden"} for edge in architecture_map["dependencies"])
    assert packages["devpilot_core.cli"]["fan_out"] > 0
    assert packages["devpilot_core.cli"]["direct_dependencies"]
    assert packages["devpilot_core.cli"]["metadata"]["dependency_edges_materialized"] is True
    assert architecture_map["hotspots"] == []
    assert architecture_map["safety"]["dry_run"] is True
    assert architecture_map["safety"]["network_used"] is False

    validation = SchemaValidator(ROOT).validate_payload(
        schema="ArchitectureMap",
        payload=architecture_map,
        instance_label="unit-test:architecture-dependencies",
    )
    assert validation.ok is True, validation.to_dict()


def test_architecture_dependencies_detects_core_to_interfaces_and_sensitive_boundaries() -> None:
    result = _dependencies_result()
    findings = [finding.to_dict() for finding in result.findings]

    assert result.data["summary"]["forbidden_dependency_findings_total"] >= 1
    assert result.data["summary"]["restricted_dependency_findings_total"] >= 1
    assert result.data["summary"]["sensitive_dependencies_total"] >= 1
    assert any(finding["id"] == "ARCHITECTURE_DEPENDENCY_FORBIDDEN" for finding in findings)
    assert any(finding["id"] == "ARCHITECTURE_DEPENDENCY_SENSITIVE" for finding in findings)
    assert result.data["summary"]["blocking_findings_total"] == 0


def test_architecture_dependencies_cli_parser_is_registered_in_cli_source() -> None:
    cli_source = _read("src/devpilot_core/cli.py")

    assert 'architecture_sub.add_parser("dependencies"' in cli_source
    assert "architecture_dependencies_command" in cli_source
    assert "ArchitectureDependenciesBuilder" in cli_source


def test_post_h_005_c_docs_and_manifest_are_synchronized() -> None:
    backlog = _read("docs/backlogs/POST-H-005_architecture_map_executable.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    changelog = _read("docs/release/CHANGELOG.md")
    audit = _read("docs/audits/post_h_005_c_architecture_dependencies_report.md")
    manifest = _read_json("docs/post_h_005_c_manifest.json")

    assert "POST-H-005-C — Grafo de dependencias y boundaries" in backlog
    assert "Estado: `implemented-initial`" in backlog
    assert "POST-H-005-C — Grafo de dependencias y boundaries" in readme
    assert "POST-H-005-E — Ownership validation y reporte" in readme
    assert "POST-H-005-C — Operación del grafo de dependencias ArchitectureMap" in runbook
    assert "post-h-005-c" in changelog
    assert "architecture dependencies --json" in audit
    assert manifest["id"] == "POST-H-005-C"
    assert manifest["status"] == "implemented-initial"
    assert manifest["dependency_graph_implemented"] is True
    assert manifest["fan_in_fan_out_implemented"] is True
    assert manifest["sensitive_dependency_marking_implemented"] is True
    assert manifest["hotspot_analyzer_implemented"] is False
    assert manifest["quality_gate_subgate_added"] is False
    assert manifest["network_used"] is False
    assert manifest["external_api_used"] is False
    assert manifest["source_mutations_performed"] is False
