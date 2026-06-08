from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.repo import GitAdapter, RepoInventory


def _minimal_workspace(root: Path) -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='tmp-devpilot'\n", encoding="utf-8")


def _run_git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)


@pytest.mark.skipif(shutil.which("git") is None, reason="git executable not available")
def test_git_adapter_status_is_read_only_and_reports_changes(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    _run_git(tmp_path, "init")
    (tmp_path / "tracked.txt").write_text("v1\n", encoding="utf-8")
    _run_git(tmp_path, "add", "tracked.txt")
    _run_git(tmp_path, "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-m", "initial")
    (tmp_path / "tracked.txt").write_text("v2\n", encoding="utf-8")
    (tmp_path / "untracked.txt").write_text("new\n", encoding="utf-8")

    before = subprocess.run(["git", "status", "--short"], cwd=tmp_path, text=True, capture_output=True, check=True).stdout
    result = GitAdapter(tmp_path).status()
    after = subprocess.run(["git", "status", "--short"], cwd=tmp_path, text=True, capture_output=True, check=True).stdout

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["is_git_repo"] is True
    assert result.data["summary"]["counts"]["modified"] >= 1
    assert result.data["summary"]["counts"]["untracked"] >= 1
    assert before == after
    executed = {tuple(item["args"]) for item in result.data["commands_executed"]}
    assert ("status", "--short") in executed
    assert all(args[0] in {"rev-parse", "branch", "status", "diff"} for args in executed)


def test_git_adapter_handles_non_git_workspace_without_error(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)

    result = GitAdapter(tmp_path).status()

    if result.data["summary"].get("git_available") is False:
        assert result.exit_code == ExitCode.FAIL
    else:
        assert result.ok is True
        assert result.data["summary"]["is_git_repo"] is False
        assert any(finding.id == "GIT_REPOSITORY_NOT_FOUND" for finding in result.findings)


def test_repo_inventory_flags_secret_like_content_without_emitting_raw_secret(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "docs" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    (tmp_path / "config.txt").write_text("api_key=sk-1234567890abcdef\n", encoding="utf-8")

    result = RepoInventory(tmp_path).build()
    payload = json.dumps(result.to_dict(), ensure_ascii=False)

    assert result.ok is True
    assert result.data["summary"]["files_total"] >= 3
    assert result.data["summary"]["secret_like_files"] == 1
    assert "sk-1234567890abcdef" not in payload
    assert any(finding.id == "REPO_INVENTORY_SECRET_LIKE_CONTENT" for finding in result.findings)


def test_repo_inventory_cli_json_and_report_are_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    _minimal_workspace(tmp_path)
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["repo-inventory", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "repo-inventory"
    assert payload["ok"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/repo_inventory.json"
    assert (tmp_path / "outputs" / "reports" / "repo_inventory.json").is_file()


@pytest.mark.skipif(shutil.which("git") is None, reason="git executable not available")
def test_git_status_cli_json_and_report_are_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    _minimal_workspace(tmp_path)
    _run_git(tmp_path, "init")
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["git-status", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "git-status"
    assert payload["data"]["summary"]["is_git_repo"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/git_status.json"
    assert (tmp_path / "outputs" / "reports" / "git_status.json").is_file()
