from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.traceability import ArchitectureDriftDetector, TraceabilityEngine

ROOT = Path(__file__).resolve().parents[1]


def test_architecture_drift_detector_reports_non_destructive_findings() -> None:
    result = ArchitectureDriftDetector(ROOT).detect()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["modules_total"] >= 10
    assert summary["architecture_docs_existing"] == 3
    assert summary["blocking_findings_total"] == 0
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert any(finding.id == "ARCHITECTURE_DRIFT_CHECK_COMPLETED" for finding in result.findings)


def test_traceability_engine_exposes_architecture_drift() -> None:
    result = TraceabilityEngine(ROOT).architecture_drift()

    assert result.command == "traceability architecture-drift"
    assert result.ok is True
    assert "modules" in result.data
    assert any(item["module_name"] == "traceability" for item in result.data["modules"])


def test_architecture_drift_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["traceability", "architecture-drift", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "traceability architecture-drift"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["modules_total"] >= 10
    assert payload["data"]["summary"]["blocking_findings_total"] == 0


def test_architecture_drift_cli_write_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    report_json = ROOT / "outputs/reports/traceability_architecture_drift.json"
    report_md = ROOT / "outputs/reports/traceability_architecture_drift.md"
    if report_json.exists():
        report_json.unlink()
    if report_md.exists():
        report_md.unlink()

    exit_code = cli.main(["traceability", "architecture-drift", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["data"]["reports"] == {
        "json": "outputs/reports/traceability_architecture_drift.json",
        "markdown": "outputs/reports/traceability_architecture_drift.md",
    }
    assert report_json.exists()
    assert report_md.exists()


def test_architecture_drift_missing_architecture_doc_is_warning(tmp_path: Path) -> None:
    root = tmp_path
    src = root / "src/devpilot_core/example"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("", encoding="utf-8")

    result = ArchitectureDriftDetector(root, architecture_docs=["docs/missing.md"]).detect()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    finding_ids = {finding.id for finding in result.findings}
    assert "ARCHITECTURE_DRIFT_ARCH_DOC_MISSING" in finding_ids
    assert "ARCHITECTURE_DRIFT_CODE_MODULE_UNDOCUMENTED" in finding_ids
