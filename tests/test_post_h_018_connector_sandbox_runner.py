from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.connectors import ConnectorSandboxOptions, ConnectorSandboxRequest, ConnectorSandboxRunner
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_018_b_runner_accepts_replay_without_network_or_mutation() -> None:
    result = ConnectorSandboxRunner(ROOT).run(
        ConnectorSandboxRequest(connector_id="local.docs", operation="list_sources", mode="replay")
    )

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    report = result.data["report"]
    assert summary["created_by"] == "POST-H-018-B"
    assert summary["mode"] == "replay"
    assert summary["policy_valid"] is True
    assert summary["policy_engine_invoked"] is True
    assert summary["policy_passed"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["connector_write_used"] is False
    assert report["schema_id"] == "SCHEMA-DEVPL-CONNECTOR-SANDBOX-REPORT-V1"
    assert report["created_by"] == "POST-H-018-B"
    assert report["status"] == "passed"
    assert report["summary"]["fixtures_total"] == 0


def test_post_h_018_b_runner_blocks_write_like_modes() -> None:
    result = ConnectorSandboxRunner(ROOT).run(
        ConnectorSandboxRequest(connector_id="local.docs", operation="list_sources", mode="write")
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["requested_mode"] == "write"
    assert result.data["summary"]["connector_write_used"] is False
    assert any(finding.id == "CONNECTOR_SANDBOX_WRITE_MODE_BLOCKED" for finding in result.findings)


def test_post_h_018_b_runner_blocks_disallowed_connector_mode() -> None:
    result = ConnectorSandboxRunner(ROOT).run(
        ConnectorSandboxRequest(connector_id="mcp.local.prototype", operation="tool_call", mode="replay")
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    summary = result.data["summary"]
    assert summary["connector_id"] == "mcp.local.prototype"
    assert summary["mode"] == "replay"
    assert summary["allowed_modes"] == ["validate"]
    assert any(finding.id == "CONNECTOR_SANDBOX_CONNECTOR_MODE_NOT_ALLOWED" for finding in result.findings)


def test_post_h_018_b_runner_writes_schema_valid_report(tmp_path: Path) -> None:
    output_json = tmp_path / "connector_sandbox_report.json"
    output_markdown = tmp_path / "connector_sandbox_report.md"
    result = ConnectorSandboxRunner(
        ROOT,
        options=ConnectorSandboxOptions(write_report=True, output_json=output_json, output_markdown=output_markdown),
    ).run(ConnectorSandboxRequest(connector_id="local.docs", operation="list_sources", mode="dry-run"))

    assert result.ok is True, result.to_dict()
    assert output_json.exists()
    assert output_markdown.exists()
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["created_by"] == "POST-H-018-B"
    assert payload["summary"]["reports_written"] is True
    validation = SchemaValidator(ROOT).validate_payload(
        schema="ConnectorSandboxReport",
        payload=payload,
        instance_label="memory:connector-sandbox-report",
    )
    assert validation.ok, validation.to_dict()


def test_post_h_018_b_cli_exposes_connector_sandbox_run() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "connector",
            "sandbox",
            "run",
            "--mode",
            "validate",
            "--json",
        ],
        cwd=ROOT,
        env={"PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["command"] == "connector sandbox run"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["created_by"] == "POST-H-018-B"
    assert payload["data"]["summary"]["network_used"] is False
    assert payload["data"]["summary"]["mutations_performed"] is False
