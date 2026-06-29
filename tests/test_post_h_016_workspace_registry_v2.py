from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.workspace import MultiworkspaceRegistry, MultiworkspaceRegistryV2

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_016_a_v1_registry_remains_valid_and_compatible() -> None:
    result = MultiworkspaceRegistry(ROOT).validate()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["schema_valid"] is True
    assert result.data["summary"]["workspaces_total"] >= 1
    assert result.data["summary"]["mutations_performed"] is False


def test_post_h_016_a_v2_fixture_matches_schema_contract() -> None:
    fixture = json.loads((ROOT / "tests/fixtures/multiworkspace_registry_v2.valid.json").read_text(encoding="utf-8"))
    result = MultiworkspaceRegistryV2(ROOT).validate_payload(fixture)

    assert result.ok is True
    assert result.data["summary"]["v2_schema_valid"] is True
    assert result.data["summary"]["mutations_performed"] is False


def test_post_h_016_a_v2_migration_is_read_only_and_schema_valid() -> None:
    registry_path = ROOT / ".devpilot/workspaces/workspace_registry.json"
    before = registry_path.read_text(encoding="utf-8")

    result = MultiworkspaceRegistryV2(ROOT).validate()

    after = registry_path.read_text(encoding="utf-8")
    assert after == before
    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["v1_registry_valid"] is True
    assert summary["v2_schema_valid"] is True
    assert summary["migration_mode"] == "read-only"
    assert summary["mutations_performed"] is False
    payload = result.data["registry"]
    assert payload["schema_version"] == "2.0"
    assert payload["defaults"]["deny_unregistered_workspaces"] is True
    assert payload["defaults"]["cross_workspace_writes"] is False
    assert payload["defaults"]["secret_sharing_allowed"] is False
    assert payload["security"]["connector_write_used"] is False
    assert payload["security"]["plugin_execution_used"] is False
    assert payload["migration"]["compatible_with_v1"] is True
    assert payload["migration"]["source_registry_preserved"] is True
    assert payload["workspaces"][0]["root_path"] == "."
    assert payload["workspaces"][0]["project_file"] == ".devpilot/project.yaml"


def test_post_h_016_a_cli_registry_validate_v2_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["workspace", "registry-validate", "--registry-version", "v2", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "workspace registry validate v2"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["v2_schema_valid"] is True
    assert payload["data"]["summary"]["mutations_performed"] is False


def test_post_h_016_a_v2_blocks_unsafe_defaults() -> None:
    validator = MultiworkspaceRegistryV2(ROOT)
    base = validator.validate()
    assert base.ok is True
    payload = copy.deepcopy(base.data["registry"])
    payload["defaults"]["secret_sharing_allowed"] = True
    payload["defaults"]["cross_workspace_writes"] = True

    result = validator.validate_payload(payload)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    finding_ids = {finding.id for finding in result.findings}
    assert "WORKSPACE_REGISTRY_V2_SECRET_SHARING_ENABLED" in finding_ids
    assert "WORKSPACE_REGISTRY_V2_CROSS_WORKSPACE_WRITES_ENABLED" in finding_ids
