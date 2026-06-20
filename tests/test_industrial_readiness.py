from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.industrial import IndustrialReadinessGate
from devpilot_core.quality import QualityGate, QualityGateOptions

ROOT = Path(__file__).resolve().parents[1]


def test_industrial_readiness_gate_passes_without_overclaiming() -> None:
    result = IndustrialReadinessGate(ROOT).check()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["phase_h_closed"] is True
    assert summary["industrial_readiness_score"] >= 80.0
    assert summary["maturity_level"] == "industrial-baseline-ready"
    assert summary["production_ready_total"] < summary["capabilities_total"]
    assert summary["implemented_initial_total"] >= 1
    assert summary["experimental_total"] >= 1
    assert summary["policy_engine_used"] is True
    assert summary["policy_engine_replaced"] is False
    assert summary["remote_runner_enabled"] is False
    assert summary["remote_execution_used"] is False
    assert summary["cloud_control_plane_enabled"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations_performed"] is False
    assert result.data["gaps"]["blocking"] == []

    capability_ids = {item["id"] for item in result.data["capabilities"]}
    assert {
        "contract",
        "policy",
        "security",
        "evals",
        "observability",
        "release",
        "ui_api",
        "multiagent",
        "rag",
        "connectors",
        "enterprise",
    }.issubset(capability_ids)


def test_industrial_readiness_cli_json_and_report_are_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["industrial-readiness", "check", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "industrial-readiness check"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    reports = payload["data"]["reports"]
    assert reports["json"] == "outputs/reports/industrial_readiness.json"
    assert reports["markdown"] == "outputs/reports/industrial_readiness.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()


def test_industrial_readiness_schema_validates_written_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    cli.main(["industrial-readiness", "check", "--json", "--write-report"])
    capsys.readouterr()

    exit_code = cli.main([
        "schema",
        "validate",
        "--schema",
        "docs/schemas/industrial_readiness.schema.json",
        "--instance",
        "outputs/reports/industrial_readiness.json",
        "--json",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["valid"] is True


def test_quality_gate_industrial_profile_consumes_industrial_readiness() -> None:
    result = QualityGate(ROOT, options=QualityGateOptions(profile="industrial")).run()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["profile"] == "industrial"
    assert summary["subgates_failed"] == 0
    subgates = {item["id"]: item for item in result.data["subgates"]}
    assert "industrial-readiness" in subgates
    assert subgates["industrial-readiness"]["ok"] is True
    assert subgates["industrial-readiness"]["summary"]["industrial_readiness_score"] >= 80.0
