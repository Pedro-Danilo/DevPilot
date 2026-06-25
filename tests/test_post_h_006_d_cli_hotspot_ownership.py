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
def _registry_result():
    from devpilot_core.cli_registry.report import CliCommandRegistryReportBuilder

    return CliCommandRegistryReportBuilder(ROOT).build()


def test_post_h_006_d_report_differentiates_migrated_registered_and_legacy_commands() -> None:
    result = _registry_result()

    assert result.ok is True, result.to_dict()
    registry = result.data["registry"]
    hotspot_report = result.data["hotspot_report"]
    summary = result.data["summary"]

    assert registry["created_by"] == "POST-H-006-D"
    assert registry["metadata"]["hotspot_ownership_report_enabled"] is True
    assert hotspot_report["created_by"] == "POST-H-006-D"
    assert hotspot_report["report_id"] == "devpilot-cli-command-hotspot-ownership-report"
    assert summary["hotspot_report_created_by"] == "POST-H-006-D"
    assert summary["migrated_commands_total"] == 3
    assert summary["registered_only_commands_total"] >= 18
    assert summary["legacy_commands_total"] > 100
    assert summary["migrated_commands_total"] + summary["registered_only_commands_total"] + summary["legacy_commands_total"] == summary["commands_total"]
    assert hotspot_report["summary"]["ownership_status_counts"]["migrated"] == 3
    assert hotspot_report["summary"]["ownership_status_counts"]["registered_only"] >= 18
    assert hotspot_report["summary"]["ownership_status_counts"]["legacy"] > 100


def test_post_h_006_d_report_identifies_risk_side_effects_boundaries_and_contract_gaps() -> None:
    report = _registry_result().data["hotspot_report"]
    summary = report["summary"]

    assert summary["commands_with_side_effects_total"] > 0
    assert summary["high_or_critical_risk_commands_total"] > 0
    assert summary["commands_without_application_service_boundary_total"] > 0
    assert summary["commands_without_test_contract_total"] >= 0
    assert report["risk"]["high_or_critical_commands"]
    assert report["ownership"]["application_service_boundary"]["missing_commands"]
    assert any(item["side_effect"] == "write-report" for item in report["risk"]["side_effects"])
    assert {link["id"] for link in report["roadmap_links"]} >= {"POST-H-003", "POST-H-007", "POST-H-006-E"}


def test_post_h_006_d_top_hotspots_are_actionable_and_safe() -> None:
    report = _registry_result().data["hotspot_report"]
    hotspots = report["hotspots"]

    assert 1 <= len(hotspots) <= 20
    assert hotspots == sorted(hotspots, key=lambda item: (-item["hotspot_score"], item["command_id"]))
    top = hotspots[0]
    assert top["risk_level"] in {"high", "critical"}
    assert top["ownership_status"] in {"legacy", "registered_only", "migrated"}
    assert top["hotspot_score"] >= 50
    assert top["hotspot_reasons"]
    assert top["recommendations"]
    assert report["safety"]["read_only"] is True
    assert report["safety"]["remote_execution_enabled"] is False
    assert report["safety"]["connector_write_enabled"] is False
    assert report["safety"]["plugin_execution_enabled"] is False
    assert report["safety"]["dynamic_handler_loading_enabled"] is False


def test_post_h_006_d_writes_registry_and_hotspot_reports() -> None:
    from devpilot_core.cli_registry.report import CliCommandRegistryReportBuilder, CliCommandRegistryReportOptions

    outputs = ROOT / "outputs" / "reports"
    for name in [
        "cli_command_registry.json",
        "cli_command_registry.md",
        "cli_command_registry_report.json",
        "cli_command_registry_report.md",
    ]:
        path = outputs / name
        if path.exists():
            path.unlink()

    result = CliCommandRegistryReportBuilder(ROOT, CliCommandRegistryReportOptions(write_report=True)).build()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    assert summary["reports_written"] is True
    assert summary["hotspot_report_written"] is True
    assert summary["output_hotspot_json"] == "outputs/reports/cli_command_registry_report.json"
    assert summary["output_hotspot_markdown"] == "outputs/reports/cli_command_registry_report.md"

    registry_payload = _read_json("outputs/reports/cli_command_registry.json")
    hotspot_payload = _read_json("outputs/reports/cli_command_registry_report.json")
    hotspot_md = _read("outputs/reports/cli_command_registry_report.md")

    assert registry_payload["created_by"] == "POST-H-006-D"
    assert hotspot_payload["created_by"] == "POST-H-006-D"
    assert hotspot_payload["summary"]["migrated_commands_total"] == 3
    assert "CLI hotspots and command ownership report" in hotspot_md


def test_post_h_006_d_docs_manifest_and_contracts_are_synchronized() -> None:
    backlog = _read("docs/backlogs/POST-H-006_cli_command_registry.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    architecture_doc = _read("docs/02_architecture/cli_command_registry_map.md")
    audit = _read("docs/audits/post_h_006_d_hotspot_ownership_report.md")
    manifest = _read_json("docs/post_h_006_d_manifest.json")
    changelog = _read("docs/release/CHANGELOG.md")
    v1 = _read_json(".devpilot/testing/test_contract_registry.json")
    v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    v1_contracts = {item["contract_id"]: item for item in v1["contracts"]}
    v2_contracts = {item["contract_id"]: item for item in v2["contracts"]}

    assert "POST-H-006-D — Reporte de hotspots CLI y ownership por comando" in backlog
    assert "Último micro-sprint implementado: `POST-H-006-D" in readme
    assert "Siguiente micro-sprint: `POST-H-006-E" in readme
    assert "POST-H-006-D — Operación del reporte de hotspots CLI y ownership" in runbook
    assert "CliHotspotOwnershipReportBuilder" in architecture_doc
    assert "cli_command_registry_report.json" in audit
    assert "post-h-006-d" in changelog
    assert manifest["id"] == "POST-H-006-D"
    assert manifest["read_only"] is True
    assert manifest["runtime_router_enabled"] is False
    assert manifest["dynamic_handler_loading_enabled"] is False
    assert "post-h-006-cli-hotspot-ownership" in v1_contracts
    assert "post-h-006-cli-hotspot-ownership" in v2_contracts
    assert v1_contracts["post-h-006-cli-hotspot-ownership"]["owner"] == "POST-H-006-D"
    assert v2_contracts["post-h-006-cli-hotspot-ownership"]["domain"] == "interface.cli"
    assert v2_contracts["post-h-006-cli-hotspot-ownership"]["owner"] == "POST-H-006-D"
