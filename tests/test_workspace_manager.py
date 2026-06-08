from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import ExitCode
from devpilot_core.workspace import WorkspaceManager, parse_project_yaml_metadata


def _create_minimal_docs(root: Path) -> None:
    (root / "docs" / "standards").mkdir(parents=True)
    (root / "docs" / "checklists").mkdir(parents=True)
    (root / "docs" / "checklists" / "checklist_pre_code.md").write_text("# Checklist\n", encoding="utf-8")


def test_workspace_init_dry_run_does_not_write(tmp_path):
    manager = WorkspaceManager(tmp_path)

    result = manager.init_workspace(execute=False)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["dry_run"] is True
    assert result.data["plan"]["would_create_project_file"] is True
    assert not (tmp_path / ".devpilot" / "project.yaml").exists()


def test_workspace_init_execute_writes_project_yaml(tmp_path):
    manager = WorkspaceManager(tmp_path)

    result = manager.init_workspace(execute=True, project_id="demo", project_name="Demo")
    project_file = tmp_path / ".devpilot" / "project.yaml"

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert project_file.exists()
    metadata = parse_project_yaml_metadata(project_file)
    assert metadata["project_id"] == "demo"
    assert metadata["project_name"] == "Demo"
    assert metadata["miasi_required"] is True
    assert metadata["standards"] == ["MIPSoftware", "MIASI"]



def test_workspace_init_dry_run_reports_existing_workspace_without_overwrite(tmp_path):
    manager = WorkspaceManager(tmp_path)
    manager.init_workspace(execute=True)

    result = manager.init_workspace(execute=False)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["dry_run"] is True
    assert result.data["plan"]["already_initialized"] is True
    assert result.findings[0].severity.value == "info"

def test_workspace_init_blocks_existing_project_yaml(tmp_path):
    manager = WorkspaceManager(tmp_path)
    first = manager.init_workspace(execute=True)
    second = manager.init_workspace(execute=True)

    assert first.ok is True
    assert second.ok is False
    assert second.exit_code == ExitCode.BLOCK
    assert second.findings[0].id == "WORKSPACE_ALREADY_INITIALIZED"


def test_workspace_status_ready_when_initialized(tmp_path):
    _create_minimal_docs(tmp_path)
    manager = WorkspaceManager(tmp_path)
    manager.init_workspace(execute=True)

    result = manager.status()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["ready"] is True
    assert result.data["summary"]["outputs_present"] is False


def test_workspace_status_fails_when_not_initialized_but_docs_exist(tmp_path):
    _create_minimal_docs(tmp_path)
    manager = WorkspaceManager(tmp_path)

    result = manager.status()

    assert result.ok is False
    assert result.exit_code == ExitCode.FAIL
    assert any(finding.id == "WORKSPACE_NOT_INITIALIZED" for finding in result.findings)


def test_workspace_discovery_from_nested_directory(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    nested = tmp_path / "src" / "pkg"
    nested.mkdir(parents=True)

    manager = WorkspaceManager.discover(nested)

    assert manager.root == tmp_path.resolve()


def test_workspace_cli_init_and_status_json_are_parseable(tmp_path, monkeypatch, capsys):
    _create_minimal_docs(tmp_path)
    monkeypatch.chdir(tmp_path)

    init_exit = main(["workspace", "init", "--execute", "--json"])
    init_payload = json.loads(capsys.readouterr().out)
    status_exit = main(["workspace", "status", "--json"])
    status_payload = json.loads(capsys.readouterr().out)

    assert init_exit == 0
    assert init_payload["command"] == "workspace init"
    assert init_payload["data"]["created"]["project_file"] == ".devpilot/project.yaml"
    assert status_exit == 0
    assert status_payload["command"] == "workspace status"
    assert status_payload["data"]["summary"]["ready"] is True


def test_workspace_cli_dry_run_write_report(tmp_path, monkeypatch, capsys):
    _create_minimal_docs(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["workspace", "init", "--dry-run", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["data"]["dry_run"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/workspace_init.json"
    assert (tmp_path / "outputs" / "reports" / "workspace_init.json").exists()
    assert not (tmp_path / ".devpilot" / "project.yaml").exists()
