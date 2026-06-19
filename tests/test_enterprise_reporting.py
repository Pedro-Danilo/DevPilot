from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.enterprise import EnterpriseReportBuilder
from devpilot_core.evals import EvalRunner
from devpilot_core.remote import RemoteRunnerStub

ROOT = Path(__file__).resolve().parents[1]


def test_remote_runner_status_is_disabled_and_experimental() -> None:
    result = RemoteRunnerStub(ROOT).status()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["remote_runner_enabled"] is False
    assert summary["execution_allowed"] is False
    assert summary["remote_execution_used"] is False
    assert summary["cloud_control_plane_enabled"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["policy_engine_used"] is True
    assert summary["policy_engine_replaced"] is False


def test_remote_runner_execute_is_always_blocked() -> None:
    result = RemoteRunnerStub(ROOT).execute(runner_id="experimental-disabled", command="pytest -q")

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["remote_runner_enabled"] is False
    assert result.data["summary"]["execution_allowed"] is False
    assert any(finding.id == "REMOTE_RUNNER_EXECUTION_BLOCKED" for finding in result.findings)


def test_remote_runner_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["remote", "runner", "status", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "remote runner status"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["remote_runner_enabled"] is False
    assert payload["data"]["summary"]["execution_allowed"] is False


def test_enterprise_report_is_local_read_only_and_aggregates_governance() -> None:
    result = EnterpriseReportBuilder(ROOT).build()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["enterprise_report_read_only"] is True
    assert summary["local_first"] is True
    assert summary["policy_engine_used"] is True
    assert summary["policy_engine_replaced"] is False
    assert summary["remote_runner_enabled"] is False
    assert summary["remote_execution_used"] is False
    assert summary["cloud_control_plane_enabled"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["gaps_total"] == 0
    assert result.data["controls"]["remote_runner_disabled"] is True
    assert result.data["controls"]["identity_rbac_available"] is True
    assert result.data["controls"]["compliance_packs_available"] is True


def test_enterprise_report_cli_json_and_report_are_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["enterprise", "report", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "enterprise report"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["gaps_total"] == 0
    reports = payload["data"].get("reports")
    assert reports["json"] == "outputs/reports/enterprise_report.json"
    assert reports["markdown"] == "outputs/reports/enterprise_report.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()


def test_remote_enterprise_eval_suite_passes() -> None:
    result = EvalRunner(ROOT).run(suite="remote-enterprise")

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["suite_id"] == "remote-enterprise"
    assert result.data["summary"]["cases_total"] == 4
    assert result.data["summary"]["cases_failed"] == 0
    assert result.data["summary"]["safety_score"] >= 90.0
    assert result.data["summary"]["false_negatives"] == 0
    assert result.data["summary"]["network_used"] is False
    assert result.data["summary"]["external_api_used"] is False
