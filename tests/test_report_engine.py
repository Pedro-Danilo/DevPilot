from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.reports import ReportEngine, ReportStatus, build_report_id, render_markdown_report
from devpilot_core.reports.models import EvidenceReport


def test_report_id_is_filesystem_safe_and_stable():
    report_id = build_report_id("validate-artifact", subject="docs/01_requirements/requirements_specification.md")

    assert report_id == "validate-artifact-docs-01_requirements-requirements_specification.md"


def test_evidence_report_from_command_result_uses_contract():
    result = CommandResult(
        command="demo-gate",
        ok=True,
        exit_code=ExitCode.PASS,
        message="Demo gate passed.",
        data={"summary": {"checked": 1}},
        findings=[Finding(id="DEMO_INFO", message="Synthetic info finding.", severity=Severity.INFO)],
    )

    report = EvidenceReport.from_command_result(
        result,
        report_id="demo_gate",
        generated_at=datetime(2026, 6, 7, 12, 0, 0, tzinfo=timezone.utc),
        subject="docs/demo.md",
        project_root=".",
    )

    payload = report.to_dict()
    assert payload["report_id"] == "demo_gate"
    assert payload["status"] == ReportStatus.PASS.value
    assert payload["generated_at"] == "2026-06-07T12:00:00Z"
    assert payload["summary"] == {"checked": 1}
    assert payload["findings"][0]["id"] == "DEMO_INFO"


def test_report_engine_writes_json_and_markdown(tmp_path):
    result = CommandResult(
        command="demo-gate",
        ok=False,
        exit_code=ExitCode.BLOCK,
        message="Demo gate blocked.",
        data={"summary": {"blocked": 1}},
        findings=[Finding(id="DEMO_BLOCK", message="Synthetic block.", severity=Severity.BLOCK, path="docs/demo.md")],
    )
    engine = ReportEngine(tmp_path)

    paths = engine.write_command_report(
        result,
        report_id="demo_gate",
        generated_at=datetime(2026, 6, 7, 12, 0, 0, tzinfo=timezone.utc),
        subject="docs/demo.md",
    )

    json_path = tmp_path / paths.json
    markdown_path = tmp_path / paths.markdown
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")

    assert paths.json == "outputs/reports/demo_gate.json"
    assert paths.markdown == "outputs/reports/demo_gate.md"
    assert payload["status"] == "BLOCK"
    assert payload["subject"] == "docs/demo.md"
    assert "# DevPilot Evidence Report — demo_gate" in markdown
    assert "**BLOCK** `DEMO_BLOCK`" in markdown


def test_markdown_report_snapshot_core_fields():
    result = CommandResult(
        command="snapshot-gate",
        ok=True,
        exit_code=ExitCode.PASS,
        message="Snapshot gate passed.",
        data={"summary": {"checked": 2, "warnings": 0}},
        findings=[],
    )
    report = EvidenceReport.from_command_result(
        result,
        report_id="snapshot_gate",
        generated_at=datetime(2026, 6, 7, 12, 0, 0, tzinfo=timezone.utc),
    )

    markdown = render_markdown_report(report)

    expected = """# DevPilot Evidence Report — snapshot_gate

## Metadata

- Report ID: `snapshot_gate`
- Command: `snapshot-gate`
- Status: `PASS`
- OK: `true`
- Exit code: `0`
- Generated at: `2026-06-07T12:00:00Z`

## Message

Snapshot gate passed.

## Summary

- `checked`: 2
- `warnings`: 0

## Findings

No findings.
"""
    assert markdown == expected


def test_validate_frontmatter_cli_can_write_evidence_report(capsys):
    root = Path(__file__).resolve().parents[1]
    json_report = root / "outputs" / "reports" / "validate-frontmatter-docs-00_product-product_vision.md.json"
    markdown_report = root / "outputs" / "reports" / "validate-frontmatter-docs-00_product-product_vision.md.md"
    json_report.unlink(missing_ok=True)
    markdown_report.unlink(missing_ok=True)

    exit_code = main([
        "validate-frontmatter",
        "docs/00_product/product_vision.md",
        "--json",
        "--write-report",
    ])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["data"]["reports"]["json"] == "outputs/reports/validate-frontmatter-docs-00_product-product_vision.md.json"
    assert json_report.exists()
    assert markdown_report.exists()


def test_checklist_cli_can_write_evidence_report(capsys):
    root = Path(__file__).resolve().parents[1]
    json_report = root / "outputs" / "reports" / "checklist_pre_code.json"
    markdown_report = root / "outputs" / "reports" / "checklist_pre_code.md"
    json_report.unlink(missing_ok=True)
    markdown_report.unlink(missing_ok=True)

    exit_code = main(["checklist-pre-code", "--json", "--write-report"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["data"]["reports"]["json"] == "outputs/reports/checklist_pre_code.json"
    assert json_report.exists()
    assert markdown_report.exists()
