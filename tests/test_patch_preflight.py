from __future__ import annotations

import json
import subprocess
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.review import PatchPreflightEngine

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _git_fixture(root: Path) -> None:
    _run(["git", "init", "-q"], root)
    _run(["git", "config", "user.email", "devpilot@example.test"], root)
    _run(["git", "config", "user.name", "DevPilot Test"], root)
    _write(root / "hello.txt", "old\n")
    _run(["git", "add", "hello.txt"], root)
    _run(["git", "commit", "-q", "-m", "initial"], root)


def _safe_patch() -> str:
    return """diff --git a/hello.txt b/hello.txt
--- a/hello.txt
+++ b/hello.txt
@@ -1 +1 @@
-old
+new
"""


def _mismatch_patch() -> str:
    return """diff --git a/hello.txt b/hello.txt
--- a/hello.txt
+++ b/hello.txt
@@ -1 +1 @@
-missing
+new
"""


def test_patch_preflight_passes_applicable_patch_without_modifying_worktree(tmp_path: Path) -> None:
    _git_fixture(tmp_path)
    _write(tmp_path / "change.patch", _safe_patch())
    before = (tmp_path / "hello.txt").read_text(encoding="utf-8")
    status_before = subprocess.run(["git", "status", "--short"], cwd=tmp_path, check=True, capture_output=True, text=True).stdout

    result = PatchPreflightEngine(tmp_path).check(patch_file="change.patch")

    status_after = subprocess.run(["git", "status", "--short"], cwd=tmp_path, check=True, capture_output=True, text=True).stdout
    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["applies"] is True
    assert result.data["summary"]["apply_check_executed"] is True
    assert result.data["summary"]["working_tree_unchanged"] is True
    assert result.data["summary"]["patch_applied"] is False
    assert result.data["summary"]["mutations_performed"] is False
    assert (tmp_path / "hello.txt").read_text(encoding="utf-8") == before
    assert status_after == status_before


def test_patch_preflight_fails_non_applicable_patch_without_modifying_file(tmp_path: Path) -> None:
    _git_fixture(tmp_path)
    _write(tmp_path / "bad.patch", _mismatch_patch())
    before = (tmp_path / "hello.txt").read_text(encoding="utf-8")

    result = PatchPreflightEngine(tmp_path).check(patch_file="bad.patch")

    assert result.ok is False
    assert result.exit_code == ExitCode.FAIL
    assert result.data["summary"]["applicability_fail"] is True
    assert result.data["summary"]["applies"] is False
    assert any(finding.id == "PATCH_PREFLIGHT_APPLY_CHECK_FAILED" for finding in result.findings)
    assert (tmp_path / "hello.txt").read_text(encoding="utf-8") == before


def test_patch_preflight_blocks_secret_patch_without_raw_secret_or_apply_check(tmp_path: Path) -> None:
    _git_fixture(tmp_path)
    secret = "sk-proj-abcdefghijklmnop123456"
    _write(
        tmp_path / "secret.patch",
        f"""diff --git a/hello.txt b/hello.txt
--- a/hello.txt
+++ b/hello.txt
@@ -1 +1,2 @@
 old
+API_KEY = '{secret}'
""",
    )

    result = PatchPreflightEngine(tmp_path).check(patch_file="secret.patch")
    payload = json.dumps(result.to_dict(), ensure_ascii=False)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["security_block"] is True
    assert result.data["summary"]["apply_check_executed"] is False
    assert secret not in payload


def test_patch_preflight_blocks_patch_file_outside_workspace(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.patch"
    _write(outside, _safe_patch())

    result = PatchPreflightEngine(tmp_path).check(patch_file=str(outside))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id in {"PATHGUARD_OUTSIDE_ROOT", "PATCH_PREFLIGHT_PATH_OUTSIDE_ROOT"} for finding in result.findings)


def test_patch_check_cli_writes_report(monkeypatch, capsys, tmp_path: Path) -> None:
    _git_fixture(tmp_path)
    _write(tmp_path / "change.patch", _safe_patch())
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["patch", "check", "--patch-file", "change.patch", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "patch check"
    assert payload["data"]["summary"]["applies"] is True
    assert payload["data"]["summary"]["patch_applied"] is False
    assert payload["data"]["reports"] == {
        "json": "outputs/reports/patch_preflight.json",
        "markdown": "outputs/reports/patch_preflight.md",
    }
    assert (tmp_path / "outputs/reports/patch_preflight.json").exists()
    assert (tmp_path / "outputs/reports/patch_preflight.md").exists()
