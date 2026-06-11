from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.repo import RepoQualityGate, RepoQualityGateConfig
from devpilot_core.review.rule_packs import default_review_rule_packs, serialize_rule_packs

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_repo(root: Path) -> None:
    _write(root / "src/devpilot_core/repo/__init__.py", "VALUE = 1\n")
    _write(root / "src/devpilot_core/repo/safe.py", "def ok():\n    return 1\n")
    _write(root / "tests/test_safe.py", "def test_ok():\n    assert True\n")
    _write(root / "README.md", "# Fixture\n")


def test_review_rule_packs_are_serializable_and_versioned() -> None:
    packs = default_review_rule_packs()
    payload = serialize_rule_packs(packs)

    assert payload
    assert {pack["pack_id"] for pack in payload} >= {"repo-health-core", "code-review-safety", "patch-review-safety", "policy-safety"}
    assert all(pack["version"] for pack in payload)
    assert any(rule["default_effect"] == "block" for pack in payload for rule in pack["rules"])


def test_repo_quality_gate_passes_with_warning_only_fixture(tmp_path: Path) -> None:
    _minimal_repo(tmp_path)
    _write(tmp_path / "src/devpilot_core/repo/warning_only.py", "# TODO: improve later\ndef ok():\n    return 1\n")

    result = RepoQualityGate(tmp_path, config=RepoQualityGateConfig(target=".", code_target="src/devpilot_core/repo")).run()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["status"] == "PASS"
    assert result.data["summary"]["warnings_total"] >= 1
    assert result.data["summary"]["mutations_performed"] is False
    assert result.data["summary"]["external_api_used"] is False
    assert result.data["summary"]["network_used"] is False


def test_repo_quality_gate_blocks_secret_like_code_without_raw_secret(tmp_path: Path) -> None:
    _minimal_repo(tmp_path)
    secret = "sk-proj-abcdefghijklmnop123456"
    _write(tmp_path / "src/devpilot_core/repo/unsafe.py", f"API_KEY = '{secret}'\n")

    result = RepoQualityGate(tmp_path, config=RepoQualityGateConfig(target=".", code_target="src/devpilot_core/repo")).run()
    payload = json.dumps(result.to_dict(), ensure_ascii=False)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["status"] == "BLOCK"
    assert any(finding.severity.value == "block" for finding in result.findings)
    assert secret not in payload


def test_repo_quality_gate_reviews_patch_when_supplied(tmp_path: Path) -> None:
    _minimal_repo(tmp_path)
    patch = tmp_path / "change.diff"
    _write(
        patch,
        """diff --git a/src/devpilot_core/repo/new.py b/src/devpilot_core/repo/new.py
new file mode 100644
--- /dev/null
+++ b/src/devpilot_core/repo/new.py
@@ -0,0 +1,2 @@
+def ok():
+    return 1
""",
    )

    result = RepoQualityGate(tmp_path, config=RepoQualityGateConfig(target=".", code_target="src/devpilot_core/repo", patch_file="change.diff")).run()

    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["patch_reviewed"] is True
    patch_component = next(component for component in result.data["components"] if component["source"] == "patch_review")
    assert patch_component["findings_total"] >= 1


def test_repo_quality_gate_cli_writes_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    report_json = ROOT / "outputs/reports/repo_quality_gate.json"
    report_md = ROOT / "outputs/reports/repo_quality_gate.md"
    if report_json.exists():
        report_json.unlink()
    if report_md.exists():
        report_md.unlink()

    exit_code = cli.main(["repo", "quality-gate", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "repo quality-gate"
    assert payload["data"]["summary"]["status"] == "PASS"
    assert payload["data"]["summary"]["mutations_performed"] is False
    assert payload["data"]["reports"] == {
        "json": "outputs/reports/repo_quality_gate.json",
        "markdown": "outputs/reports/repo_quality_gate.md",
    }
    assert report_json.exists()
    assert report_md.exists()
