from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.review import CodeReviewEngine, PatchReviewEngine


def _minimal_workspace(root: Path) -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='tmp-devpilot'\n", encoding="utf-8")


def _safe_patch() -> str:
    return """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,3 @@
 print('hello')
+print('safe')
"""


def test_patch_review_safe_patch_passes_without_applying(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    (tmp_path / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    before = (tmp_path / "src" / "app.py").read_text(encoding="utf-8")

    result = PatchReviewEngine(tmp_path).review(patch_text=_safe_patch())

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["files_changed"] == 1
    assert result.data["summary"]["patch_applied"] is False
    assert (tmp_path / "src" / "app.py").read_text(encoding="utf-8") == before


def test_patch_review_blocks_secret_like_addition_without_emitting_secret(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    patch = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1 +1,2 @@
 print('hello')
+api_key='sk-1234567890abcdef'
"""

    result = PatchReviewEngine(tmp_path).review(patch_text=patch)
    payload = json.dumps(result.to_dict(), ensure_ascii=False)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "PATCH_SECRET_LIKE_CONTENT" for finding in result.findings)
    assert "sk-1234567890abcdef" not in payload


def test_patch_review_blocks_denied_target_path(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    patch = """diff --git a/.env b/.env
--- a/.env
+++ b/.env
@@ -0,0 +1 @@
+DEBUG=true
"""

    result = PatchReviewEngine(tmp_path).review(patch_text=patch)

    assert result.ok is False
    assert any(finding.id == "PATCH_TARGET_POLICY_BLOCK" for finding in result.findings)


def test_patch_review_cli_json_and_report_are_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    _minimal_workspace(tmp_path)
    patch_path = tmp_path / "safe.patch"
    patch_path.write_text(_safe_patch(), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["patch-review", "--patch-file", "safe.patch", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "patch-review"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["patch_applied"] is False
    assert payload["data"]["reports"]["json"] == "outputs/reports/patch_review.json"
    assert (tmp_path / "outputs" / "reports" / "patch_review.json").is_file()


def test_code_review_clean_file_passes(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    (tmp_path / "src" / "app.py").write_text("def main():\n    return 42\n", encoding="utf-8")

    result = CodeReviewEngine(tmp_path).review("src")

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["files_reviewed"] == 1
    assert result.data["summary"]["files_modified"] == 0


def test_code_review_detects_risky_code_and_secret_without_emitting_secret(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    (tmp_path / "src" / "bad.py").write_text("import subprocess\nsubprocess.run('x', shell=True)\napi_key='sk-1234567890abcdef'\n", encoding="utf-8")

    result = CodeReviewEngine(tmp_path).review("src")
    payload = json.dumps(result.to_dict(), ensure_ascii=False)

    assert result.ok is False
    assert any(finding.id == "CODE_REVIEW_SHELL_TRUE" for finding in result.findings)
    assert any(finding.id == "CODE_REVIEW_SECRET_LIKE_CONTENT" for finding in result.findings)
    assert "sk-1234567890abcdef" not in payload


def test_code_review_cli_json_and_report_are_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    _minimal_workspace(tmp_path)
    (tmp_path / "src" / "app.py").write_text("def main():\n    return 42\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["code-review", "--target", "src", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "code-review"
    assert payload["ok"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/code_review.json"
    assert (tmp_path / "outputs" / "reports" / "code_review.json").is_file()
