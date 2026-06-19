from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_changelog_builder_generates_keep_a_changelog_sections() -> None:
    from devpilot_core.cli_models import ExitCode
    from devpilot_core.release import ReleaseChangelogBuilder, ReleaseChangelogOptions

    result = ReleaseChangelogBuilder(ROOT, options=ReleaseChangelogOptions(version="0.1.0")).build()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    changelog = result.data["changelog"]
    markdown = result.data["changelog_markdown"]

    assert summary["version"] == "0.1.0"
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations_performed"] is False
    assert changelog["format"] == "keep-a-changelog-compatible"
    assert changelog["from_sprint"] == "FUNC-SPRINT-74"
    assert changelog["to_sprint"] == "FUNC-SPRINT-93"
    for category in ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]:
        assert category in changelog["sections"]
        assert f"### {category}" in markdown
    assert any(item["sprint"] == "FUNC-SPRINT-78" for item in changelog["source_manifests"])
    assert "docs/functional_sprint_78_manifest.json" in markdown
    assert "docs/functional_sprint_81_manifest.json" in markdown
    assert "docs/functional_sprint_84_manifest.json" in markdown
    assert "docs/functional_sprint_85_manifest.json" in markdown
    assert "docs/functional_sprint_86_manifest.json" in markdown
    assert "docs/functional_sprint_87_manifest.json" in markdown
    assert "docs/functional_sprint_88_manifest.json" in markdown
    assert "docs/functional_sprint_89_manifest.json" in markdown
    assert "docs/functional_sprint_91_manifest.json" in markdown
    assert "docs/functional_sprint_92_manifest.json" in markdown


def test_release_changelog_rejects_invalid_semver() -> None:
    from devpilot_core.cli_models import ExitCode
    from devpilot_core.release import ReleaseChangelogBuilder, ReleaseChangelogOptions

    result = ReleaseChangelogBuilder(ROOT, options=ReleaseChangelogOptions(version="bad-version")).build()

    assert result.ok is False
    assert result.exit_code == ExitCode.ERROR
    assert result.findings[0].id == "CHANGELOG_VERSION_INVALID"


def test_release_changelog_rejects_invalid_sprint_range() -> None:
    from devpilot_core.cli_models import ExitCode
    from devpilot_core.release import ReleaseChangelogBuilder, ReleaseChangelogOptions

    result = ReleaseChangelogBuilder(
        ROOT,
        options=ReleaseChangelogOptions(version="0.1.0", from_sprint="not-a-sprint"),
    ).build()

    assert result.ok is False
    assert result.exit_code == ExitCode.ERROR
    assert result.findings[0].id == "CHANGELOG_SPRINT_RANGE_INVALID"


def test_release_changelog_cli_json_and_report_are_parseable() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "release", "changelog", "--version", "0.1.0", "--json", "--write-report"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["command"] == "release changelog"
    assert payload["ok"] is True
    assert payload["data"]["changelog"]["release_version"] == "0.1.0"
    assert payload["data"]["summary"]["reports_written"] is True
    reports = payload["data"].get("reports")
    assert reports["json"] == "outputs/reports/release_changelog.json"
    assert reports["markdown"] == "outputs/reports/release_changelog.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()


def test_release_changelog_does_not_overwrite_canonical_changelog() -> None:
    before = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "release", "changelog", "--version", "0.1.0", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    after = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    assert before == after
