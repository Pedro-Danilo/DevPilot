from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.release_candidate import UiApiRcSmokeOptions, UiApiRcSmokeRunner
from devpilot_core.schemas.validator import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_ui_api_rc_smoke_passes_without_network_or_source_mutations() -> None:
    result = UiApiRcSmokeRunner(ROOT).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["api_localhost_only"] is True
    assert summary["api_token_required"] is True
    assert summary["cors_wildcard_enabled"] is False
    assert summary["no_go_action_blocked"] is True
    assert summary["browser_automation_used"] is False
    assert summary["network_used"] is False
    assert summary["external_apis_required"] is False
    assert summary["checks_failed_total"] == 0
    safety = result.data["report"]["safety"]
    assert safety["socket_opened"] is False
    assert safety["network_used"] is False
    assert safety["external_api_used"] is False
    assert safety["remote_execution_enabled"] is False
    assert safety["connector_write_enabled"] is False
    assert safety["plugin_execution_enabled"] is False
    assert safety["raw_token_persisted"] is False
    assert any(finding.id == "UI_API_RC_SMOKE_PASS" for finding in result.findings)


def test_ui_api_rc_smoke_blocks_non_local_base_url() -> None:
    result = UiApiRcSmokeRunner(ROOT, UiApiRcSmokeOptions(base_url="http://0.0.0.0:8787")).run()

    assert not result.ok
    assert result.exit_code == ExitCode.BLOCK
    finding_ids = {finding.id for finding in result.findings}
    assert "UI_API_RC_BASE_URL_NOT_LOCALHOST_BLOCK" in finding_ids


def test_ui_api_rc_smoke_write_report_validates_schema(tmp_path: Path) -> None:
    output_json = ROOT / "outputs/test_fixtures/post_h_026_c/ui_api_rc_smoke_report.json"
    output_markdown = ROOT / "outputs/test_fixtures/post_h_026_c/ui_api_rc_smoke_report.md"
    result = UiApiRcSmokeRunner(
        ROOT,
        UiApiRcSmokeOptions(
            output_json=str(output_json),
            output_markdown=str(output_markdown),
            write_report=True,
        ),
    ).run()

    assert result.ok, result.to_dict()
    assert output_json.exists()
    assert output_markdown.exists()
    report = json.loads(output_json.read_text(encoding="utf-8"))
    validation = SchemaValidator(ROOT).validate_payload(
        schema="UiApiRcSmokeReport",
        payload=report,
        instance_label="memory:ui-api-rc-smoke-report",
    )
    assert validation.ok, validation.to_dict()
    assert report["decision"] == "PASS"
    assert report["safety"]["reports_written"] is True


def test_ui_api_rc_smoke_cli_json(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["release-candidate", "ui-api-smoke", "--base-url", "http://127.0.0.1:8787", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "release-candidate ui-api-smoke"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == "PASS"
    assert payload["data"]["summary"]["network_used"] is False
