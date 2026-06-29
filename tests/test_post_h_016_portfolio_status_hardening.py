from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.portfolio import PortfolioStatusBuilder
from devpilot_core.workspace import MultiworkspaceRegistryV2

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_016_c_portfolio_status_uses_registered_workspaces_only() -> None:
    result = PortfolioStatusBuilder(ROOT).build()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["portfolio_status_read_only"] is True
    assert summary["registered_workspaces_only"] is True
    assert summary["unregistered_workspace_policy"] == "denied"
    assert summary["unregistered_workspaces_denied_total"] == 0
    assert summary["state_files_read"] is False
    assert summary["secrets_read"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["cross_workspace_writes"] is False
    assert all(workspace["is_registered"] is True for workspace in result.data["workspaces"])


def test_post_h_016_c_portfolio_status_reports_unknown_operational_sources() -> None:
    base = MultiworkspaceRegistryV2(ROOT).validate()
    assert base.ok is True
    payload = copy.deepcopy(base.data["registry"])
    payload["workspaces"][0]["reports_path"] = "outputs/missing-post-h-016-c-reports"
    payload["workspaces"][0]["traces_path"] = "outputs/missing-post-h-016-c-traces"

    result = PortfolioStatusBuilder(ROOT).build_from_registry_payload(payload)

    assert result.ok is True
    workspace = result.data["workspaces"][0]
    assert workspace["reports"]["status"] == "unknown"
    assert workspace["traces"]["status"] == "unknown"
    assert "unknown_operational_sources" in workspace["risks"]["flags"]
    assert result.data["summary"]["unknown_sources_total"] >= 2
    assert result.data["summary"]["state_files_read"] is False
    assert result.data["summary"]["secrets_read"] is False


def test_post_h_016_c_portfolio_status_blocks_cross_workspace_reference() -> None:
    base = MultiworkspaceRegistryV2(ROOT).validate()
    assert base.ok is True
    payload = copy.deepcopy(base.data["registry"])
    second = copy.deepcopy(payload["workspaces"][0])
    second["workspace_id"] = "secondary-local"
    second["root_path"] = "docs"
    payload["workspaces"].append(second)
    payload["workspaces"][0]["reports_path"] = "docs/outputs/reports"

    result = PortfolioStatusBuilder(ROOT).build_from_registry_payload(payload)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["registered_workspaces_only"] is True
    assert result.data["summary"]["cross_workspace_refs_detected"] is True
    assert any(finding.id == "WORKSPACE_ISOLATION_CROSS_WORKSPACE_REFERENCE" for finding in result.findings)


def test_post_h_016_c_portfolio_status_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["portfolio", "status", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "portfolio status"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["registered_workspaces_only"] is True
    assert payload["data"]["summary"]["unregistered_workspace_policy"] == "denied"
    assert payload["data"]["summary"]["state_files_read"] is False
    assert payload["data"]["summary"]["secrets_read"] is False
