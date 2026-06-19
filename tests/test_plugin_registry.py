from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.plugins import PluginDryRunOptions, PluginRegistry

ROOT = Path(__file__).resolve().parents[1]


def test_plugin_registry_validate_passes() -> None:
    result = PluginRegistry(ROOT).validate()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["plugins_total"] >= 2
    assert summary["schema_valid"] is True
    assert summary["connector_registry_valid"] is True
    assert summary["plugin_code_loaded"] is False
    assert summary["arbitrary_code_execution_performed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    plugin_ids = {plugin["plugin_id"] for plugin in result.data["plugins"]}
    assert "local.docs.plugin" in plugin_ids


def test_plugin_registry_list_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["plugin", "list", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "plugin list"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["plugins_total"] >= 2


def test_plugin_validate_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["plugin", "validate", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "plugin validate"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["blocked_findings_total"] == 0


def test_plugin_loader_dry_run_passes_and_emits_trace() -> None:
    result = PluginRegistry(ROOT).dry_run(PluginDryRunOptions(plugin="local.docs.plugin", operation="metadata", dry_run=True))

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["dry_run"] is True
    assert summary["plugin_code_loaded"] is False
    assert summary["arbitrary_code_execution_performed"] is False
    assert summary["trace_event_emitted"] is True
    assert summary["event_path"] == "outputs/traces/events.jsonl"


def test_plugin_loader_blocks_without_dry_run() -> None:
    result = PluginRegistry(ROOT).dry_run(PluginDryRunOptions(plugin="local.docs.plugin", operation="metadata", dry_run=False))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "PLUGIN_DRY_RUN_REQUIRED" for finding in result.findings)


def test_plugin_loader_blocks_unregistered_plugin() -> None:
    result = PluginRegistry(ROOT).dry_run(PluginDryRunOptions(plugin="unknown.plugin", operation="metadata", dry_run=True))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "PLUGIN_NOT_REGISTERED" for finding in result.findings)


def test_plugin_ecosystem_eval_suite_passes(capsys) -> None:
    exit_code = cli.main(["eval", "run", "--suite", "plugin-ecosystem", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["suite_id"] == "plugin-ecosystem"
    assert payload["data"]["summary"]["safety_score"] >= 90
