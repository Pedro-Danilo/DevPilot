from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.connectors import (
    ConnectorPolicyBindingOptions,
    ConnectorPolicyBindingRequest,
    ConnectorPolicyBindingValidator,
    ConnectorSandboxRequest,
    ConnectorSandboxRunner,
)
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_018_d_connector_policy_exposure_schema_is_registered() -> None:
    result = SchemaRegistry(ROOT).list()

    assert result.ok, result.to_dict()
    schema_ids = {schema["schema_id"] for schema in result.data["schemas"]}
    assert "SCHEMA-DEVPL-CONNECTOR-POLICY-EXPOSURE-REPORT-V1" in schema_ids


def test_post_h_018_d_exposure_report_lists_connectors_by_risk_and_blocks_future_write(tmp_path: Path) -> None:
    output_json = tmp_path / "connector_policy_exposure_report.json"
    output_markdown = tmp_path / "connector_policy_exposure_report.md"
    result = ConnectorPolicyBindingValidator(
        ROOT,
        options=ConnectorPolicyBindingOptions(write_report=True, output_json=output_json, output_markdown=output_markdown),
    ).exposure_report()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-018-D"
    assert summary["connectors_total"] == 4
    assert summary["connectors_by_risk"] == {"medium": 1, "medium_high": 1, "high": 1, "critical": 1}
    assert summary["write_future_blocked_total"] == 4
    assert summary["policy_coverage_complete"] is True
    assert summary["all_high_risk_rbac_evaluated"] is True
    assert summary["all_side_effecting_future_write_blocked"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["connector_write_used"] is False
    assert output_json.exists()
    assert output_markdown.exists()

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    validation = SchemaValidator(ROOT).validate_payload(
        schema="ConnectorPolicyExposureReport",
        payload=payload,
        instance_label="memory:connector-policy-exposure-report",
    )
    assert validation.ok, validation.to_dict()
    assert all(connector["write_future_blocked"] is True for connector in payload["connectors"])
    assert all(
        connector["rbac_evaluated"] is True
        for connector in payload["connectors"]
        if connector["risk_level"] in {"high", "critical"}
    )


def test_post_h_018_d_binding_allows_read_only_replay_but_records_write_future_block() -> None:
    result = ConnectorPolicyBindingValidator(ROOT).evaluate_request(
        ConnectorPolicyBindingRequest(connector_id="local.docs", operation="list_sources", mode="replay")
    )

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-018-D"
    assert summary["policy_coverage"] is True
    assert summary["approval_policy_checked"] is True
    assert summary["approval_required"] is False
    assert summary["write_future_blocked"] is True
    assert summary["rbac_evaluated"] is False
    assert summary["network_used"] is False
    assert summary["mutations_performed"] is False


def test_post_h_018_d_side_effecting_connector_blocks_without_approval_and_unknown_rbac() -> None:
    result = ConnectorPolicyBindingValidator(ROOT).evaluate_request(
        ConnectorPolicyBindingRequest(
            connector_id="mcp.local.prototype",
            operation="discover_tools",
            mode="validate",
            actor_id="unknown-actor",
        )
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    summary = result.data["summary"]
    assert summary["approval_policy_checked"] is True
    assert summary["approval_required"] is True
    assert summary["approval_missing_blocks"] is True
    assert summary["rbac_evaluated"] is True
    assert summary["rbac_allowed"] is False
    assert summary["write_future_blocked"] is True
    assert any(finding.id == "CONNECTOR_BINDING_APPROVAL_REQUIRED" for finding in result.findings)
    assert any(finding.id == "CONNECTOR_BINDING_RBAC_DENIED" for finding in result.findings)


def test_post_h_018_d_sandbox_runner_embeds_binding_before_replay() -> None:
    result = ConnectorSandboxRunner(ROOT).run(
        ConnectorSandboxRequest(connector_id="local.docs", operation="list_sources", mode="replay")
    )

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-018-D"
    assert summary["connector_binding_checked"] is True
    assert summary["connector_binding_passed"] is True
    assert summary["write_future_blocked"] is True
    assert summary["fixtures_total"] == 1
    assert summary["redaction_passed"] is True
    assert "binding" in result.data


def test_post_h_018_d_sandbox_blocks_side_effecting_connector_without_approval() -> None:
    result = ConnectorSandboxRunner(ROOT).run(
        ConnectorSandboxRequest(connector_id="mcp.local.prototype", operation="discover_tools", mode="validate")
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-018-D"
    assert summary["connector_binding_checked"] is True
    assert summary["approval_missing_blocks"] is True
    assert any(finding.id == "BINDING_CONNECTOR_BINDING_APPROVAL_REQUIRED" for finding in result.findings)


def test_post_h_018_d_cli_exposes_connector_policy_exposure_report(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    output_json = tmp_path / "exposure.json"
    output_markdown = tmp_path / "exposure.md"

    exit_code = cli.main([
        "connector",
        "sandbox",
        "exposure",
        "--json",
        "--write-report",
        "--output-json",
        str(output_json),
        "--output-markdown",
        str(output_markdown),
    ])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "connector sandbox exposure"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["created_by"] == "POST-H-018-D"
    assert payload["data"]["summary"]["write_future_blocked_total"] == 4
    assert output_json.exists()
    assert output_markdown.exists()
