from __future__ import annotations

import json
from pathlib import Path

import pytest

from devpilot_core.cli import main
from devpilot_core.quality import QualityGate, QualityGateOptions
from devpilot_core.rag import RagGroundednessReadyGate, RagGroundednessReadyGateOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_rag_groundedness_ready_gate_passes_offline_without_writing_outputs() -> None:
    result = RagGroundednessReadyGate(ROOT, options=RagGroundednessReadyGateOptions()).run()

    assert result.ok, result.to_dict()
    assert result.command == "quality rag-groundedness-ready"
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-011-E"
    assert summary["quality_gate_ready"] is True
    assert summary["cases_total"] >= 10
    assert summary["source_coverage_avg"] == pytest.approx(1.0)
    assert summary["claim_support_avg"] >= 0.8
    assert summary["negative_case_block_checked"] is True
    assert summary["negative_case_blocked"] is True
    assert summary["reports_written"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["web_search_used"] is False
    assert summary["llm_judge_used"] is False
    assert summary["outputs_as_sources_allowed"] is False


def test_rag_groundedness_ready_gate_blocks_missing_fixture(tmp_path: Path) -> None:
    result = RagGroundednessReadyGate(
        ROOT,
        options=RagGroundednessReadyGateOptions(suite_path=str(tmp_path / "missing.json")),
    ).run()

    assert result.ok is False
    assert result.exit_code.value in {2, 3, 4}
    assert any(finding.id in {"RAG_GROUNDEDNESS_SUITE_NOT_FOUND", "RAG_GROUNDEDNESS_READY_NEGATIVE_LOAD_ERROR"} for finding in result.findings)


def test_quality_gate_hardening_includes_rag_groundedness_ready_subgate() -> None:
    result = QualityGate(ROOT, options=QualityGateOptions(profile="hardening", include_pytest=False)).run()

    assert result.ok, result.to_dict()
    subgates = {item["id"]: item for item in result.data["subgates"]}
    assert "rag-groundedness-ready" in subgates
    subgate = subgates["rag-groundedness-ready"]
    assert subgate["ok"] is True
    assert subgate["command"] == "quality rag-groundedness-ready"
    assert subgate["summary"]["quality_gate_ready"] is True
    assert subgate["summary"]["negative_case_blocked"] is True
    assert subgate["summary"]["network_used"] is False
    assert subgate["summary"]["external_api_used"] is False


def test_post_h_011_e_cli_report_still_validates_when_written(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([
        "rag",
        "groundedness-eval",
        "--suite",
        "evals/fixtures/rag_groundedness_post_h_cases.json",
        "--write-report",
        "--json",
    ])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True

    report_path = ROOT / "outputs/evals/rag_groundedness_report.json"
    assert report_path.exists()
    validation = SchemaValidator(ROOT).validate(schema="RagGroundednessReport", instance=report_path)
    assert validation.ok, validation.to_dict()
