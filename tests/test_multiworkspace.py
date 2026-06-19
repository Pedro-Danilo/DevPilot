from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.portfolio import PortfolioStatusBuilder
from devpilot_core.workspace import MultiworkspaceRegistry, WorkspaceRegisterOptions, WorkspaceSelectOptions

ROOT = Path(__file__).resolve().parents[1]


def test_multiworkspace_registry_validate_passes() -> None:
    result = MultiworkspaceRegistry(ROOT).validate()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["workspaces_total"] >= 1
    assert summary["schema_valid"] is True
    assert summary["path_isolation_passed"] is True
    assert summary["state_isolation_passed"] is True
    assert summary["secrets_read"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False


def test_workspace_list_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["workspace", "list", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "workspace list"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["workspaces_total"] >= 1


def test_workspace_registry_validate_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["workspace", "registry-validate", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "workspace registry validate"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["blocked_findings_total"] == 0


def test_workspace_register_is_idempotent_and_isolated(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["workspace", "register", "--path", ".", "--registry-path", "outputs/test_runtime/workspace_registry_test.json", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "workspace register"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["registered"] is True
    assert payload["data"]["summary"]["path_isolation_passed"] is True
    assert payload["data"]["summary"]["state_isolation_passed"] is True


def test_workspace_select_blocks_unregistered_workspace() -> None:
    result = MultiworkspaceRegistry(ROOT).select(WorkspaceSelectOptions(workspace_id="not-registered"))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "MULTIWORKSPACE_NOT_REGISTERED" for finding in result.findings)


def test_workspace_register_blocks_path_escape(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    result = MultiworkspaceRegistry(ROOT).register(WorkspaceRegisterOptions(path=str(outside)))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "MULTIWORKSPACE_PATH_BLOCKED" for finding in result.findings)


def test_portfolio_status_read_only_cli_json(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["portfolio", "status", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "portfolio status"
    assert payload["ok"] is True
    summary = payload["data"]["summary"]
    assert summary["portfolio_status_read_only"] is True
    assert summary["mutations_performed"] is False
    assert summary["state_files_read"] is False
    assert summary["secrets_read"] is False


def test_portfolio_status_builder_does_not_read_state_or_secrets() -> None:
    result = PortfolioStatusBuilder(ROOT).build()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["state_files_read"] is False
    assert summary["secrets_read"] is False
    assert summary["state_isolation_passed"] is True


def test_multiworkspace_eval_suite_passes(capsys) -> None:
    exit_code = cli.main(["eval", "run", "--suite", "multiworkspace-isolation", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["suite_id"] == "multiworkspace-isolation"
    assert payload["data"]["summary"]["safety_score"] >= 90
