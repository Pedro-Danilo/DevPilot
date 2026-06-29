from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import ExitCode
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_015_a_operator_dashboard_snapshot_schema_validates_fixture() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="OperatorDashboardSnapshot",
        instance="tests/fixtures/operator_dashboard_snapshot.valid.json",
    )

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["network_used"] is False
    assert result.data["summary"]["external_api_used"] is False


def test_post_h_015_a_operator_dashboard_snapshot_requires_source_refs() -> None:
    payload = _read_json("tests/fixtures/operator_dashboard_snapshot.valid.json")
    invalid_payload = copy.deepcopy(payload)
    invalid_payload["sections"]["quality_gates"].pop("source_refs")

    result = SchemaValidator(ROOT).validate_payload(
        schema="OperatorDashboardSnapshot",
        payload=invalid_payload,
        instance_label="synthetic-missing-source-refs",
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(
        finding.id == "SCHEMA_VALIDATION_ERROR" and "source_refs" in finding.message
        for finding in result.findings
    )


def test_post_h_015_a_dashboard_config_is_local_read_only_and_section_complete() -> None:
    config = _read_json(".devpilot/operator/dashboard_config.json")
    fixture = _read_json("tests/fixtures/operator_dashboard_snapshot.valid.json")

    assert config["created_by"] == "POST-H-015-A"
    assert config["status"] == "implemented-initial"
    assert config["snapshot_schema_id"] == "SCHEMA-DEVPL-OPERATOR-DASHBOARD-SNAPSHOT-V1"
    assert config["snapshot_output_path"] == "outputs/reports/operator_dashboard_snapshot.json"
    assert config["local_first"] is True
    assert config["read_only"] is True
    assert config["dry_run"] is True
    assert config["network_used"] is False
    assert config["external_api_used"] is False
    assert config["mutations_performed"] is False
    assert config["source_mutations_performed"] is False
    assert config["remote_execution_enabled"] is False
    assert config["connector_write_enabled"] is False
    assert config["plugin_execution_enabled"] is False
    assert set(config["required_sections"]) == set(fixture["sections"])
    assert set(config["section_order"]) == set(config["required_sections"])
    assert all(item["dry_run"] is True for item in config["recommended_next_actions"])
    assert all(item["required"] in {True, False} for item in config["required_source_refs"])


def test_post_h_015_a_schema_cli_and_docs_are_synchronized(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = main(
        [
            "schema",
            "validate",
            "--schema-id",
            "OperatorDashboardSnapshot",
            "--instance",
            "tests/fixtures/operator_dashboard_snapshot.valid.json",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["valid"] is True

    catalog = (ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-015_local_operator_dashboard.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/local_operator_dashboard_runbook.md").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    source_registry = (ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8")

    assert "SCHEMA-DEVPL-OPERATOR-DASHBOARD-SNAPSHOT-V1" in catalog
    assert 'status: "approved"' in backlog
    assert 'current_micro_sprint: "POST-H-015-A"' in backlog
    assert "POST-H-015-A — Dashboard snapshot schema y config" in runbook
    assert "post-h-015-operator-dashboard-schema-config" in tcr_v1
    assert "post-h-015-operator-dashboard-schema-config" in tcr_v2
    assert "POST-H-015-BACKLOG" in source_registry
