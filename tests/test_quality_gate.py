from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.quality import QualityGate, QualityGateOptions

ROOT = Path(__file__).resolve().parents[1]


def test_quality_gate_fast_profile_passes_and_reports_subgates() -> None:
    result = QualityGate(ROOT, options=QualityGateOptions(profile="fast")).run()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["profile"] == "fast"
    assert summary["subgates_total"] == 5
    assert summary["subgates_failed"] == 0
    assert summary["include_pytest"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations_performed"] is False
    subgates = {item["id"]: item for item in result.data["subgates"]}
    for expected in ["readiness-strict", "standards-status", "miasi-validate", "eval-harness-ready", "app-contract"]:
        assert expected in subgates
        assert subgates[expected]["ok"] is True
        assert isinstance(subgates[expected]["duration_ms"], int)


def test_quality_gate_full_profile_adds_extended_local_subgates() -> None:
    result = QualityGate(ROOT, options=QualityGateOptions(profile="full")).run()

    assert result.ok is True
    subgate_ids = {item["id"] for item in result.data["subgates"]}
    assert "validation-gateway-all" in subgate_ids
    assert "visual-product-smoke" in subgate_ids
    assert "pytest" not in subgate_ids


def test_quality_gate_cli_json_and_report_output_are_parseable() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "quality-gate", "run", "--json", "--write-report"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["command"] == "quality-gate run"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["subgates_failed"] == 0
    reports = payload["data"].get("reports")
    assert reports["json"] == "outputs/reports/quality_gate.json"
    assert reports["markdown"] == "outputs/reports/quality_gate.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()


def test_quality_gate_rejects_unknown_profile() -> None:
    result = QualityGate(ROOT, options=QualityGateOptions(profile="unsafe")).run()

    assert result.ok is False
    assert result.exit_code == ExitCode.ERROR
    assert result.findings[0].id == "QUALITY_GATE_PROFILE_UNSUPPORTED"
