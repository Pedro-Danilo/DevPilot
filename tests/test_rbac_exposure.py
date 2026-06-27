from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.identity.exposure import RbacExposureReporter

ROOT = Path(__file__).resolve().parents[1]


def _finding_ids(result) -> set[str]:
    return {finding.id for finding in result.findings}


def test_rbac_exposure_reporter_builds_read_only_matrix_without_outputs() -> None:
    result = RbacExposureReporter(ROOT).run()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    report = result.data["report"]
    assert summary["actions_total"] >= 11
    assert summary["actors_total"] >= 1
    assert summary["roles_total"] >= 6
    assert summary["matrix_entries_total"] >= summary["actions_total"] * summary["actors_total"]
    assert summary["critical_actions_without_required_role_total"] == 0
    assert summary["critical_exposed_without_role_total"] == 0
    assert summary["api_ui_exposed_critical_total"] == 0
    assert summary["dangerous_capability_exposed_total"] == 0
    assert summary["remote_plugin_connector_write_blocked_total"] > 0
    assert summary["identity_registry_read"] is True
    assert summary["sensitive_action_catalog_read"] is True
    assert summary["policy_matrix_read"] is True
    assert summary["reports_written"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["remote_execution_enabled"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["plugin_execution_enabled"] is False
    assert report["schema_id"] == "SCHEMA-DEVPL-RBAC-EXPOSURE-REPORT-V1"
    assert report["created_by"] == "POST-H-012-C"
    assert report["matrix"]
    assert "RBAC_EXPOSURE_DANGEROUS_SURFACES_BLOCKED" in _finding_ids(result)


def test_rbac_exposure_cli_writes_schema_valid_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    json_path = ROOT / "outputs/reports/approval_rbac_exposure.json"
    md_path = ROOT / "outputs/reports/approval_rbac_exposure.md"
    if json_path.exists():
        json_path.unlink()
    if md_path.exists():
        md_path.unlink()

    exit_code = cli.main(["identity", "exposure", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/approval_rbac_exposure.json"
    assert payload["data"]["reports"]["markdown"] == "outputs/reports/approval_rbac_exposure.md"
    assert json_path.exists()
    assert md_path.exists()

    validation_exit = cli.main([
        "schema",
        "validate",
        "--schema-id",
        "RbacExposureReport",
        "--instance",
        "outputs/reports/approval_rbac_exposure.json",
        "--json",
    ])
    validation = json.loads(capsys.readouterr().out)
    assert validation_exit == 0
    assert validation["ok"] is True
    assert validation["data"]["summary"]["valid"] is True


def test_rbac_exposure_matrix_blocks_api_ui_remote_plugin_connector_write() -> None:
    result = RbacExposureReporter(ROOT).run()
    matrix = result.data["report"]["matrix"]

    for entry in matrix:
        if entry["risk_level"] == "critical" and entry["interface"] in {"api", "ui"}:
            assert entry["effect"] in {"block", "deny"}
        if entry["domain"] in {"remote", "plugin", "connector"}:
            assert entry["effect"] in {"block", "deny"}
        if entry["source_mutation_allowed"] is False and entry["status"] == "blocked":
            assert entry["effect"] in {"block", "deny"}


def test_rbac_exposure_detects_role_binding_gaps_without_exposing_actions() -> None:
    result = RbacExposureReporter(ROOT).run()
    summary = result.data["summary"]

    assert summary["missing_required_role_refs_total"] >= 0
    assert summary["critical_exposed_without_role_total"] == 0
    assert summary["api_ui_exposed_critical_total"] == 0
    assert summary["dangerous_capability_exposed_total"] == 0
    assert summary["blocking_findings_total"] == 0
