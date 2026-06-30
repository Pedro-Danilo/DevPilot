from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.release import ReleaseEnvironmentSnapshotBuilder, ReleaseEnvironmentSnapshotOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_017_b_environment_snapshot_builder_is_redacted_and_diagnostic() -> None:
    result = ReleaseEnvironmentSnapshotBuilder(ROOT).build()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    snapshot = result.data["snapshot"]
    summary = result.data["summary"]
    assert snapshot["created_by"] == "POST-H-017-B"
    assert snapshot["redaction"]["env_files_read"] is False
    assert snapshot["redaction"]["secret_values_read"] is False
    assert snapshot["redaction"]["secret_values_included"] is False
    assert snapshot["safety"]["secrets_included"] is False
    assert snapshot["safety"]["network_used"] is False
    assert snapshot["safety"]["external_api_used"] is False
    assert snapshot["diagnostics"]["allows_local_diagnosis"] is True
    assert snapshot["diagnostics"]["env_file_contents_read"] is False
    assert snapshot["diagnostics"]["package_manager_processes_executed"] is False
    assert summary["created_by"] == "POST-H-017-B"
    assert summary["env_files_read"] is False
    assert summary["secret_values_read"] is False
    assert summary["secrets_included"] is False
    assert summary["dependencies_total"] >= 0


def test_post_h_017_b_environment_snapshot_cli_writes_schema_valid_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["release", "environment-snapshot", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "release environment-snapshot"
    assert payload["ok"] is True
    reports = payload["data"]["reports"]
    assert reports["json"] == "outputs/release/environment_snapshot.json"
    assert reports["markdown"] == "outputs/release/environment_snapshot.md"
    assert payload["data"]["summary"]["reports_written"] is True
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()

    schema_result = SchemaValidator(ROOT).validate(
        schema="ReleaseEnvironmentSnapshot",
        instance=reports["json"],
    )
    assert schema_result.ok, schema_result.to_dict()
    assert schema_result.data["summary"]["valid"] is True


def test_post_h_017_b_environment_snapshot_does_not_read_env_file_contents(tmp_path: Path) -> None:
    (tmp_path / ".devpilot" / "release").mkdir(parents=True)
    (tmp_path / ".devpilot" / "release" / "reproducibility_policy.json").write_text(
        (ROOT / ".devpilot" / "release" / "reproducibility_policy.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'tmp-devpilot'\nversion = '0.1.0'\ndependencies = ['click>=8']\n",
        encoding="utf-8",
    )
    secret_value = "sk-test-THIS-SHOULD-NOT-APPEAR-1234567890"
    (tmp_path / ".env").write_text(f"OPENAI_API_KEY={secret_value}\n", encoding="utf-8")

    result = ReleaseEnvironmentSnapshotBuilder(tmp_path).build()

    assert result.ok, result.to_dict()
    snapshot_text = json.dumps(result.data["snapshot"], ensure_ascii=False)
    assert secret_value not in snapshot_text
    assert f"OPENAI_API_KEY={secret_value}" not in snapshot_text
    assert result.data["snapshot"]["diagnostics"]["env_file_paths_detected"][0] == {
        "path": ".env",
        "exists": True,
        "contents_read": False,
    }
    assert result.data["snapshot"]["redaction"]["env_files_read"] is False
    assert result.data["snapshot"]["safety"]["secret_values_read"] is False


def test_post_h_017_b_docs_state_and_contracts_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-017_release_reproducibility_pack.md").read_text(encoding="utf-8")
    post_doc = (ROOT / "docs/POST-H-017_release_reproducibility_pack.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    source_registry = (ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8")

    assert 'status: "approved"' in backlog
    assert 'current_micro_sprint: "POST-H-017-E"' in backlog
    assert 'next_micro_sprint: "POST-H-018"' in backlog
    assert "POST-H-017-A — Release reproducibility schema y policy" in backlog
    assert "POST-H-017-B — Environment snapshot redactado" in backlog
    assert "POST-H-017-B — Environment snapshot redactado" in post_doc
    assert "release environment-snapshot --json --write-report" in readme
    assert "release environment-snapshot --json --write-report" in runbook
    assert "post-h-017-b" in changelog
    assert state["last_completed_sprint"] == "POST-H-017"
    assert state["next_sprint"] == "POST-H-018"
    assert state["current_micro_sprint"] == "POST-H-017-E"
    assert state["next_micro_sprint"] == "POST-H-018"
    assert "post-h-017-environment-snapshot-redacted" in tcr_v1
    assert "post-h-017-environment-snapshot-redacted" in tcr_v2
    assert "release_environment_module" in source_registry
