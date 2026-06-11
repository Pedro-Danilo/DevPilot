from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.repo import GitAdapter


def _run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, text=True, capture_output=True)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init")
    _run_git(repo, "config", "user.name", "DevPilot Test")
    _run_git(repo, "config", "user.email", "devpilot@example.test")
    (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")
    _run_git(repo, "add", "app.py")
    _run_git(repo, "commit", "-m", "initial commit")
    _run_git(repo, "branch", "feature/read-only")
    _run_git(repo, "tag", "v0.1.0")
    return repo


def test_git_adapter_v2_branches_tags_and_log_are_read_only(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    adapter = GitAdapter(repo)

    branches = adapter.branches()
    tags = adapter.tags()
    log = adapter.log(limit=5)

    assert branches.ok
    assert tags.ok
    assert log.ok
    assert any(branch["name"] in {"master", "main"} for branch in branches.data["branches"])
    assert any(branch["name"] == "feature/read-only" for branch in branches.data["branches"])
    assert tags.data["tags"][0]["name"] == "v0.1.0"
    assert log.data["summary"]["commits_total"] >= 1
    assert log.data["commits"][0]["subject"] == "initial commit"

    status_after = subprocess.run(["git", "status", "--short"], cwd=repo, check=True, text=True, capture_output=True).stdout
    assert status_after == ""


def test_git_diff_report_includes_modified_added_deleted_and_untracked(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "deleted.py").write_text("obsolete = True\n", encoding="utf-8")
    _run_git(repo, "add", "deleted.py")
    _run_git(repo, "commit", "-m", "add deleted fixture")
    (repo / "app.py").write_text("print('hello')\nprint('changed')\n", encoding="utf-8")
    (repo / "new_module.py").write_text("VALUE = 1\n", encoding="utf-8")
    _run_git(repo, "add", "new_module.py")
    (repo / "deleted.py").unlink()
    _run_git(repo, "add", "deleted.py")
    (repo / "notes.txt").write_text("untracked\n", encoding="utf-8")

    result = GitAdapter(repo).diff_report()

    assert result.ok
    files = result.data["files"]
    by_path = {(item["scope"], item["path"]): item for item in files}
    assert by_path[("unstaged", "app.py")]["change_type"] == "modified"
    assert by_path[("staged", "deleted.py")]["change_type"] == "deleted"
    assert by_path[("staged", "new_module.py")]["change_type"] == "added"
    assert by_path[("untracked", "notes.txt")]["change_type"] == "untracked"
    assert result.data["summary"]["modified_files"] >= 1
    assert result.data["summary"]["added_files"] >= 1
    assert result.data["summary"]["deleted_files"] >= 1
    assert result.data["summary"]["untracked_files"] >= 1


def test_git_adapter_v2_blocks_write_commands(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    adapter = GitAdapter(repo)

    with pytest.raises(ValueError):
        adapter._run_allowed(("commit", "-m", "blocked"))
    with pytest.raises(ValueError):
        adapter._run_allowed(("checkout", "-b", "blocked"))
    with pytest.raises(ValueError):
        adapter._run_allowed(("push",))


def test_git_adapter_v2_non_git_repo_returns_controlled_result(tmp_path: Path) -> None:
    result = GitAdapter(tmp_path).branches()

    assert result.ok
    assert result.exit_code == 0
    assert result.data["summary"]["is_git_repo"] is False
    assert result.findings[0].id == "GIT_REPOSITORY_NOT_FOUND"


def test_git_v2_cli_diff_report_writes_report(capsys) -> None:
    exit_code = cli.main(["git", "diff-report", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "git diff-report"
    assert payload["data"]["reports"]["json"].endswith("git_diff_report.json")
    assert payload["data"]["reports"]["markdown"].endswith("git_diff_report.md")
