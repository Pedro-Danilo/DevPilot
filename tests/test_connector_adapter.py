from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.connectors import ConnectorAdapter, ConnectorCallOptions


def test_connector_adapter_list_sources_dry_run_passes() -> None:
    result = ConnectorAdapter(Path.cwd()).call(ConnectorCallOptions(connector="local-docs", operation="list", dry_run=True, limit=5))

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["connector_id"] == "local.docs"
    assert summary["operation_id"] == "list_sources"
    assert summary["dry_run"] is True
    assert summary["policy_checked"] is True
    assert summary["policy_allowed"] is True
    assert summary["read_only"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["shell_used"] is False
    assert summary["remote_execution_used"] is False
    assert summary["mcp_client_used"] is False
    assert summary["mcp_server_used"] is False
    assert summary["connector_execution_performed"] is False
    assert summary["trace_event_emitted"] is True
    assert result.data["result"]["sources_total"] > 0


def test_connector_adapter_query_sources_is_read_only_and_grounded() -> None:
    result = ConnectorAdapter(Path.cwd()).call(ConnectorCallOptions(connector="local.docs", operation="query_sources", dry_run=True, query="readiness strict", limit=5))

    assert result.ok is True
    assert result.data["summary"]["operation_id"] == "query_sources"
    assert result.data["result"]["sources_total"] > 0
    assert all("ref" in item for item in result.data["result"]["items"])


def test_connector_adapter_blocks_without_dry_run() -> None:
    result = ConnectorAdapter(Path.cwd()).call(ConnectorCallOptions(connector="local-docs", operation="list", dry_run=False))

    assert result.ok is False
    assert any(f.id == "CONNECTOR_CALL_REQUIRES_DRY_RUN" for f in result.findings)


def test_connector_adapter_blocks_disabled_mcp_connector() -> None:
    result = ConnectorAdapter(Path.cwd()).call(ConnectorCallOptions(connector="mcp.local.prototype", operation="discover_tools", dry_run=True))

    assert result.ok is False
    ids = {f.id for f in result.findings}
    assert "CONNECTOR_NOT_READ_ONLY_MVP" in ids
    assert "CONNECTOR_NOT_IMPLEMENTED" in ids


def test_connector_adapter_blocks_unknown_connector() -> None:
    result = ConnectorAdapter(Path.cwd()).call(ConnectorCallOptions(connector="unknown.connector", operation="list", dry_run=True))

    assert result.ok is False
    assert any(f.id == "CONNECTOR_NOT_REGISTERED" for f in result.findings)


def test_connector_call_cli_json_and_write_report() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "connector",
            "call",
            "--connector",
            "local-docs",
            "--operation",
            "list",
            "--dry-run",
            "--json",
            "--write-report",
        ],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
        env={"PYTHONPATH": "src"},
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["command"] == "connector call"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    assert payload["data"]["summary"]["trace_event_emitted"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/connector_call_local_docs_list.json"
