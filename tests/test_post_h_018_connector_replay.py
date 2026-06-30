from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.connectors import (
    ConnectorReplayOptions,
    ConnectorReplayRequest,
    ConnectorReplayRunner,
    ConnectorSandboxOptions,
    ConnectorSandboxRequest,
    ConnectorSandboxRunner,
)
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SET = ROOT / "evals/fixtures/connector_replay_cases.json"


def _fixture_set() -> dict:
    return json.loads(FIXTURE_SET.read_text(encoding="utf-8"))


def test_post_h_018_c_fixture_set_exists_and_each_fixture_schema_validates() -> None:
    payload = _fixture_set()

    assert payload["created_by"] == "POST-H-018-C"
    assert payload["redaction_required"] is True
    assert payload["safety"]["network_used"] is False
    assert payload["safety"]["external_api_used"] is False
    assert payload["safety"]["mutations_performed"] is False
    assert payload["safety"]["secrets_included"] is False
    assert len(payload["fixtures"]) >= 2

    validator = SchemaValidator(ROOT)
    for fixture in payload["fixtures"]:
        validation = validator.validate_payload(
            schema="ConnectorReplayFixture",
            payload=fixture,
            instance_label=f"memory:{fixture['fixture_id']}",
        )
        assert validation.ok, validation.to_dict()
        assert fixture["redaction_required"] is True
        assert fixture["expected"]["network_used"] is False
        assert fixture["expected"]["external_api_used"] is False
        assert fixture["expected"]["mutations_performed"] is False


def test_post_h_018_c_replay_runner_is_deterministic_and_secret_free() -> None:
    runner = ConnectorReplayRunner(ROOT)
    first = runner.run(ConnectorReplayRequest(connector_id="local.docs", operation="list_sources"))
    second = runner.run(ConnectorReplayRequest(connector_id="local.docs", operation="list_sources"))

    assert first.ok is True, first.to_dict()
    assert second.ok is True, second.to_dict()
    assert first.exit_code == ExitCode.PASS
    assert first.data["summary"]["created_by"] == "POST-H-018-C"
    assert first.data["summary"]["fixtures_total"] == 1
    assert first.data["summary"]["fixtures_passed"] == 1
    assert first.data["summary"]["deterministic_replay"] is True
    assert first.data["summary"]["redaction_passed"] is True
    assert first.data["summary"]["redaction_findings_total"] == 0
    assert first.data["summary"]["network_used"] is False
    assert first.data["summary"]["external_api_used"] is False
    assert first.data["summary"]["mutations_performed"] is False
    assert first.data["summary"]["secrets_included"] is False
    assert first.data["fixtures"][0]["deterministic_fingerprint"] == second.data["fixtures"][0]["deterministic_fingerprint"]


def test_post_h_018_c_replay_runner_blocks_secret_like_fixture(tmp_path: Path) -> None:
    fixture_set = _fixture_set()
    bad = copy.deepcopy(fixture_set)
    bad["fixtures"][0]["input"]["token"] = "not-a-real-token-but-forbidden-field-name"
    bad_path = tmp_path / "connector_replay_cases.bad.json"
    bad_path.write_text(json.dumps(bad, indent=2), encoding="utf-8")

    result = ConnectorReplayRunner(ROOT, options=ConnectorReplayOptions(fixtures_path=bad_path)).run(
        ConnectorReplayRequest(connector_id="local.docs", operation="list_sources")
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["fixtures_total"] == 1
    assert result.data["summary"]["fixtures_passed"] == 0
    assert result.data["summary"]["redaction_passed"] is False
    assert any(finding.id == "CONNECTOR_REPLAY_SECRET_KEY_BLOCKED" for finding in result.findings)


def test_post_h_018_c_sandbox_replay_integrates_fixture_summary_and_reports(tmp_path: Path) -> None:
    sandbox_json = tmp_path / "connector_sandbox_report.json"
    sandbox_md = tmp_path / "connector_sandbox_report.md"
    redaction_json = tmp_path / "connector_replay_redaction_report.json"
    redaction_md = tmp_path / "connector_replay_redaction_report.md"
    result = ConnectorSandboxRunner(
        ROOT,
        options=ConnectorSandboxOptions(
            write_report=True,
            output_json=sandbox_json,
            output_markdown=sandbox_md,
            redaction_output_json=redaction_json,
            redaction_output_markdown=redaction_md,
        ),
    ).run(ConnectorSandboxRequest(connector_id="local.docs", operation="list_sources", mode="replay"))

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-018-C"
    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    assert summary["redaction_passed"] is True
    assert summary["deterministic_replay"] is True
    expected_redaction_json = str(redaction_json.relative_to(ROOT)) if redaction_json.is_relative_to(ROOT) else redaction_json.as_posix()
    assert summary["redaction_report_json"] == expected_redaction_json
    assert sandbox_json.exists()
    assert sandbox_md.exists()
    assert redaction_json.exists()
    assert redaction_md.exists()
    sandbox_payload = json.loads(sandbox_json.read_text(encoding="utf-8"))
    redaction_payload = json.loads(redaction_json.read_text(encoding="utf-8"))
    assert sandbox_payload["created_by"] == "POST-H-018-C"
    assert redaction_payload["created_by"] == "POST-H-018-C"
    validation = SchemaValidator(ROOT).validate_payload(
        schema="ConnectorSandboxReport",
        payload=sandbox_payload,
        instance_label="memory:connector-sandbox-report-post-h-018-c",
    )
    assert validation.ok, validation.to_dict()


def test_post_h_018_c_cli_replay_uses_fixtures_and_writes_redaction_report(tmp_path: Path) -> None:
    sandbox_json = tmp_path / "sandbox.json"
    sandbox_md = tmp_path / "sandbox.md"
    redaction_json = tmp_path / "redaction.json"
    redaction_md = tmp_path / "redaction.md"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "connector",
            "sandbox",
            "run",
            "--mode",
            "replay",
            "--json",
            "--write-report",
            "--output-json",
            str(sandbox_json),
            "--output-markdown",
            str(sandbox_md),
            "--redaction-output-json",
            str(redaction_json),
            "--redaction-output-markdown",
            str(redaction_md),
        ],
        cwd=ROOT,
        env={"PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["command"] == "connector sandbox run"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["created_by"] == "POST-H-018-C"
    assert payload["data"]["summary"]["fixtures_total"] == 1
    assert payload["data"]["summary"]["redaction_passed"] is True
    assert sandbox_json.exists()
    assert redaction_json.exists()
