from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.release import SourceArchiveManifestBuilder, SourceArchiveManifestOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_017_c_source_archive_manifest_builder_generates_clean_manifest() -> None:
    result = SourceArchiveManifestBuilder(ROOT).build()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    manifest = result.data["manifest"]
    summary = result.data["summary"]
    assert manifest["created_by"] == "POST-H-017-C"
    assert manifest["status"] == "implemented-initial"
    assert manifest["exclusions"]["forbidden_entries_total"] == 0
    assert "outputs/" in manifest["exclusions"]["critical_exclusions"]
    assert ".devpilot/devpilot.db" in manifest["exclusions"]["forbidden_archive_entries"]
    assert manifest["critical_artifacts"]["present_total"] > 0
    assert manifest["critical_artifacts"]["checksums_sha256"]
    assert manifest["safety"]["network_used"] is False
    assert manifest["safety"]["external_api_used"] is False
    assert manifest["safety"]["secrets_included"] is False
    assert summary["included_files_total"] > 0
    assert summary["checksums_generated"] is True


def test_post_h_017_c_source_archive_manifest_cli_writes_schema_valid_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["release", "source-archive-manifest", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "release source-archive-manifest"
    assert payload["ok"] is True
    reports = payload["data"]["reports"]
    assert reports["json"] == "outputs/release/source_archive_manifest.json"
    assert reports["markdown"] == "outputs/release/source_archive_manifest.md"
    assert reports["checksums"] == "outputs/release/source_archive_checksums.sha256"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()
    assert (ROOT / reports["checksums"]).exists()

    schema_result = SchemaValidator(ROOT).validate(
        schema="ReleaseSourceArchiveManifest",
        instance=reports["json"],
    )
    assert schema_result.ok, schema_result.to_dict()
    assert schema_result.data["summary"]["valid"] is True


def test_post_h_017_c_source_archive_manifest_blocks_forbidden_archive_entries() -> None:
    result = SourceArchiveManifestBuilder(
        ROOT,
        options=SourceArchiveManifestOptions(
            archive_entries_override=(
                "README.md",
                "src/devpilot_core/__init__.py",
                "outputs/release/leaked.json",
                ".devpilot/devpilot.db",
            )
        ),
    ).build()

    assert not result.ok
    assert result.exit_code == ExitCode.BLOCK
    summary = result.data["summary"]
    manifest = result.data["manifest"]
    assert summary["forbidden_entries_total"] == 2
    assert {item["path"] for item in manifest["exclusions"]["forbidden_entries_detected"]} == {
        "outputs/release/leaked.json",
        ".devpilot/devpilot.db",
    }


def test_post_h_017_c_source_archive_manifest_filters_git_archive_runtime_entries(monkeypatch) -> None:
    def fake_git_archive_entries(self):
        return {
            "method": "git-archive-head-in-memory",
            "git_metadata_available": True,
            "git_archive_checked": True,
            "fallback_used": False,
            "entries": [
                "README.md",
                ".devpilot/project_state.json",
                ".devpilot/devpilot.db",
                ".devpilot/backups/backup.zip",
                ".devpilot/agent_sessions/session.json",
                "outputs/release/source_archive_manifest.json",
                "src/devpilot_core/__init__.py",
                "tests/__pycache__/test.cpython-312.pyc",
            ],
        }

    monkeypatch.setattr(SourceArchiveManifestBuilder, "_git_archive_head_entries", fake_git_archive_entries)

    result = SourceArchiveManifestBuilder(ROOT).build()

    assert result.ok, result.to_dict()
    manifest = result.data["manifest"]
    entries = set(manifest["archive"]["entries"])
    assert manifest["archive"]["method"] == "git-archive-head-in-memory"
    assert manifest["archive"]["git_archive_checked"] is True
    assert manifest["exclusions"]["forbidden_entries_total"] == 0
    assert "README.md" in entries
    assert ".devpilot/project_state.json" in entries
    assert "src/devpilot_core/__init__.py" in entries
    assert ".devpilot/devpilot.db" not in entries
    assert ".devpilot/backups/backup.zip" not in entries
    assert ".devpilot/agent_sessions/session.json" not in entries
    assert "outputs/release/source_archive_manifest.json" not in entries


def test_post_h_017_c_docs_state_and_contracts_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-017_release_reproducibility_pack.md").read_text(encoding="utf-8")
    post_doc = (ROOT / "docs/POST-H-017_release_reproducibility_pack.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    release_runbook = (ROOT / "docs/05_operations/release_reproducibility_runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    source_registry = (ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8")

    assert 'current_micro_sprint: "POST-H-017-E"' in backlog
    assert 'next_micro_sprint: "POST-H-018"' in backlog
    assert "POST-H-017-C — Source archive manifest y checksums" in backlog
    assert "POST-H-017-C — Source archive manifest y checksums" in post_doc
    assert "release source-archive-manifest --json --write-report" in readme
    assert "release source-archive-manifest --json --write-report" in runbook
    assert "ReleaseSourceArchiveManifest" in release_runbook
    assert "post-h-017-c" in changelog
    assert state["last_completed_sprint"] == "POST-H-017"
    assert state["next_sprint"] == "POST-H-018"
    assert state["current_micro_sprint"] == "POST-H-018-A"
    assert state["next_micro_sprint"] == "POST-H-018-B"
    assert "post-h-017-source-archive-manifest-checksums" in tcr_v1
    assert "post-h-017-source-archive-manifest-checksums" in tcr_v2
    assert "release_source_archive_manifest_schema" in source_registry
    assert "release_archive_manifest_module" in source_registry
