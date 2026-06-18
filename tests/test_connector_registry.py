from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.connectors import ConnectorRegistry


def test_connector_registry_validate_passes_on_default_registry() -> None:
    result = ConnectorRegistry(Path.cwd()).validate()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["connectors_total"] >= 4
    assert summary["policy_rules_missing_total"] == 0
    assert summary["enabled_by_default_total"] == 0
    assert summary["execution_enabled_total"] == 0
    assert summary["mcp_enabled_by_default"] is False
    assert summary["mcp_client_implemented"] is False
    assert summary["mcp_server_implemented"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False


def test_connector_registry_schema_validates_registry() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "schema",
            "validate",
            "--schema",
            "docs/schemas/connector_registry.schema.json",
            "--instance",
            ".devpilot/connectors/connector_registry.json",
            "--json",
        ],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
        env={"PYTHONPATH": "src"},
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True


def test_connector_validate_cli_json_and_write_report() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "connector", "validate", "--json", "--write-report"],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
        env={"PYTHONPATH": "src"},
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["command"] == "connector validate"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/connector_validate.json"


def test_connector_registry_blocks_missing_policy(tmp_path: Path) -> None:
    root = tmp_path
    (root / "docs/schemas").mkdir(parents=True)
    (root / ".devpilot/connectors").mkdir(parents=True)
    schema = json.loads(Path("docs/schemas/connector_registry.schema.json").read_text(encoding="utf-8"))
    registry = json.loads(Path(".devpilot/connectors/connector_registry.json").read_text(encoding="utf-8"))
    registry["connectors"][0]["policy_rule_ids"] = []
    (root / "docs/schemas/connector_registry.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    (root / ".devpilot/connectors/connector_registry.json").write_text(json.dumps(registry), encoding="utf-8")

    result = ConnectorRegistry(root).validate()

    assert result.ok is False
    assert any(f.id in {"CONNECTOR_POLICY_MISSING", "SCHEMA_VALIDATION_FAIL"} for f in result.findings)


def test_connector_registry_blocks_premature_mcp_runtime(tmp_path: Path) -> None:
    root = tmp_path
    (root / "docs/schemas").mkdir(parents=True)
    (root / ".devpilot/connectors").mkdir(parents=True)
    schema = json.loads(Path("docs/schemas/connector_registry.schema.json").read_text(encoding="utf-8"))
    registry = json.loads(Path(".devpilot/connectors/connector_registry.json").read_text(encoding="utf-8"))
    registry["mcp"]["client_implemented"] = True
    (root / "docs/schemas/connector_registry.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    (root / ".devpilot/connectors/connector_registry.json").write_text(json.dumps(registry), encoding="utf-8")

    result = ConnectorRegistry(root).validate()

    assert result.ok is False
    assert any(f.id == "MCP_RUNTIME_PREMATURE_BLOCKED" for f in result.findings)
