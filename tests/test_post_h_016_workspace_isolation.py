from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.workspace import MultiworkspaceRegistryV2, WorkspaceIsolationOptions, WorkspaceIsolationValidator

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_016_b_workspace_isolation_passes_without_source_mutations() -> None:
    registry_path = ROOT / ".devpilot/workspaces/workspace_registry.json"
    before = registry_path.read_text(encoding="utf-8")

    result = WorkspaceIsolationValidator(ROOT).run()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert registry_path.read_text(encoding="utf-8") == before
    summary = result.data["summary"]
    assert summary["registered_workspaces_only"] is True
    assert summary["path_guard_aligned"] is True
    assert summary["state_paths_inside_workspace"] is True
    assert summary["outputs_inside_workspace"] is True
    assert summary["traces_inside_workspace"] is True
    assert summary["secrets_read"] is False
    assert summary["state_files_read"] is False
    assert summary["mutations_performed"] is False
    assert result.data["report"]["schema_id"] == "SCHEMA-DEVPL-WORKSPACE-ISOLATION-REPORT-V1"


def test_post_h_016_b_cli_writes_report_only_when_requested(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    output_json = tmp_path / "workspace_isolation_report.json"
    output_md = tmp_path / "workspace_isolation_report.md"

    exit_code = cli.main([
        "workspace",
        "isolation-check",
        "--json",
        "--write-report",
        "--output-json",
        str(output_json),
        "--output-markdown",
        str(output_md),
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "workspace isolation-check"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    assert output_json.is_file()
    assert output_md.is_file()
    report = json.loads(output_json.read_text(encoding="utf-8"))
    assert report["summary"]["secrets_read"] is False
    assert report["summary"]["state_files_read"] is False


def test_post_h_016_b_blocks_state_path_outside_workspace() -> None:
    base = MultiworkspaceRegistryV2(ROOT).validate()
    assert base.ok is True
    payload = copy.deepcopy(base.data["registry"])
    payload["workspaces"][0]["state_path"] = "../outside/devpilot.db"

    result = WorkspaceIsolationValidator(ROOT).validate_registry_payload(payload)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    finding_ids = {finding.id for finding in result.findings}
    assert "WORKSPACE_ISOLATION_STATE_PATH_OUTSIDE_ROOT" in finding_ids
    assert result.data["summary"]["state_paths_inside_workspace"] is False
    assert result.data["summary"]["secrets_read"] is False
    assert result.data["summary"]["state_files_read"] is False


def test_post_h_016_b_detects_cross_workspace_reference() -> None:
    base = MultiworkspaceRegistryV2(ROOT).validate()
    assert base.ok is True
    payload = copy.deepcopy(base.data["registry"])
    first = copy.deepcopy(payload["workspaces"][0])
    first["workspace_id"] = "secondary-local"
    first["root_path"] = "docs"
    first["status"] = "registered"
    payload["workspaces"].append(first)
    payload["workspaces"][0]["reports_path"] = "docs/outputs/reports"

    result = WorkspaceIsolationValidator(ROOT).validate_registry_payload(payload)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["cross_workspace_refs_detected"] is True
    assert any(finding.id == "WORKSPACE_ISOLATION_CROSS_WORKSPACE_REFERENCE" for finding in result.findings)
