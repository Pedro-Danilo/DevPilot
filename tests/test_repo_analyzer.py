from __future__ import annotations

import json
import subprocess
from pathlib import Path

from devpilot_core import cli
from devpilot_core.repo import RepoAnalyzer


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _init_git(repo: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, text=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "DevPilot Test"], cwd=repo, check=True, text=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "devpilot@example.test"], cwd=repo, check=True, text=True, capture_output=True)


def test_repo_analyzer_summarizes_src_tests_docs_and_dependencies(tmp_path: Path) -> None:
    root = tmp_path
    _init_git(root)
    _write(root / "src" / "pkg" / "__init__.py", "")
    _write(root / "src" / "pkg" / "service.py", "from pkg import model\n")
    _write(root / "src" / "pkg" / "model.py", "VALUE = 1\n")
    _write(root / "tests" / "test_service.py", "def test_service():\n    assert True\n")
    _write(root / "docs" / "README.md", "# Docs\n")

    result = RepoAnalyzer(root).analyze()

    assert result.ok
    assert result.data["summary"]["sections_summary"]["files_total"] >= 5
    assert result.data["sections"]["source"]["python_files"] == 3
    assert result.data["sections"]["tests"]["python_files"] == 1
    assert result.data["dependency_summary"]["nodes_total"] == 3
    assert result.data["summary"]["network_used"] is False
    assert result.data["summary"]["mutations_performed"] is False


def test_repo_analyzer_reports_secret_like_content_without_raw_secret(tmp_path: Path) -> None:
    root = tmp_path
    _write(root / "src" / "pkg" / "__init__.py", "")
    secret_value = "sk-test_12345678901234567890"
    _write(root / ".env", f"OPENAI_API_KEY={secret_value}\n")

    result = RepoAnalyzer(root).analyze()
    payload = json.dumps(result.to_dict())

    assert result.ok
    assert any(finding.id == "REPO_ANALYZER_SECRET_LIKE_CONTENT" for finding in result.findings)
    assert secret_value not in payload
    assert "[REDACTED]" not in payload  # analyzer emits only metadata, not redacted payloads


def test_repo_analyzer_without_git_returns_partial_controlled_result(tmp_path: Path) -> None:
    root = tmp_path
    _write(root / "src" / "pkg" / "__init__.py", "")
    _write(root / "tests" / "test_pkg.py", "def test_ok():\n    assert True\n")

    result = RepoAnalyzer(root).analyze()

    assert result.ok
    assert result.data["git_summary"]["is_git_repo"] is False
    assert any(finding.id == "REPO_ANALYZER_GIT_UNAVAILABLE" for finding in result.findings)


def test_repo_analyzer_blocks_target_outside_workspace(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    _write(outside / "x.py", "import os\n")

    result = RepoAnalyzer(root).analyze(target=outside)

    assert not result.ok
    assert result.exit_code == 2
    assert result.findings[0].id == "PATHGUARD_OUTSIDE_ROOT"


def test_repo_analyzer_cli_writes_report(capsys) -> None:
    exit_code = cli.main(["repo", "analyze", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "repo analyze"
    assert payload["data"]["summary"]["health_score"] >= 0
    assert payload["data"]["reports"]["json"].endswith("repo_analyze.json")
    assert payload["data"]["reports"]["markdown"].endswith("repo_analyze.md")
