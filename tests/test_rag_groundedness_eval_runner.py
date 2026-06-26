from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.application import ApplicationService
from devpilot_core.rag import RagGroundednessEvalRunOptions, RagGroundednessEvalRunner
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = "evals/fixtures/rag_groundedness_post_h_cases.json"


def _remove_eval_outputs() -> None:
    for relative in ["outputs/evals/rag_groundedness_report.json", "outputs/evals/rag_groundedness_report.md"]:
        path = ROOT / relative
        if path.exists():
            path.unlink()


def test_post_h_011_d_eval_runner_integrates_rag_query_and_groundedness() -> None:
    result = RagGroundednessEvalRunner(ROOT).run()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-011-D"
    assert summary["suite_id"] == "rag-groundedness-post-h"
    assert summary["cases_total"] >= 10
    assert summary["rag_query_used"] is True
    assert summary["queries_total"] == summary["cases_total"]
    assert summary["queries_with_sources_total"] == summary["cases_total"]
    assert summary["query_failures_total"] == 0
    assert summary["source_coverage_avg"] >= 0.8
    assert summary["claim_support_avg"] >= 0.8
    assert summary["unsupported_claims_total"] == 0
    assert summary["forbidden_claims_detected_total"] == 0
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["web_search_used"] is False
    assert summary["llm_judge_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert all(case["query_executed"] is True for case in result.data["case_results"])
    assert all(case["query_grounded"] is True for case in result.data["case_results"])
    assert all(case["query_sources_total"] > 0 for case in result.data["case_results"])


def test_post_h_011_d_eval_runner_supports_single_case_and_schema_report() -> None:
    result = RagGroundednessEvalRunner(
        ROOT,
        options=RagGroundednessEvalRunOptions(case_id="rag-posth-roadmap-prioritized-hitos"),
    ).run()

    assert result.ok, result.to_dict()
    assert result.data["summary"]["cases_total"] == 1
    assert result.data["summary"]["case_id"] == "rag-posth-roadmap-prioritized-hitos"
    report = result.data["report"]
    validation = SchemaValidator(ROOT).validate_payload(
        schema="RagGroundednessReport",
        payload=report,
        instance_label="in-memory:post-h-011-d-rag-groundedness-eval-runner-report",
    )
    assert validation.ok, validation.to_dict()
    assert report["created_by"] == "POST-H-011-D"
    assert report["summary"]["rag_query_used"] is True
    assert report["case_results"][0]["query_grounded"] is True


def test_post_h_011_d_eval_runner_writes_outputs_evals_reports() -> None:
    _remove_eval_outputs()

    result = RagGroundednessEvalRunner(
        ROOT,
        options=RagGroundednessEvalRunOptions(case_id="rag-posth-roadmap-prioritized-hitos"),
    ).run(write_report=True)

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["reports_written"] is True
    assert result.data["reports"] == {
        "json": "outputs/evals/rag_groundedness_report.json",
        "markdown": "outputs/evals/rag_groundedness_report.md",
    }
    json_report = ROOT / "outputs/evals/rag_groundedness_report.json"
    md_report = ROOT / "outputs/evals/rag_groundedness_report.md"
    assert json_report.exists()
    assert md_report.exists()
    payload = json.loads(json_report.read_text(encoding="utf-8"))
    assert payload["created_by"] == "POST-H-011-D"
    assert payload["summary"]["reports_written"] is True
    assert "RAG Groundedness Eval Report" in md_report.read_text(encoding="utf-8")


def test_post_h_011_d_cli_rag_groundedness_eval_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "rag",
            "groundedness-eval",
            "--suite",
            FIXTURE,
            "--case-id",
            "rag-posth-roadmap-prioritized-hitos",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={"PYTHONPATH": "src"},
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "rag groundedness-eval"
    assert payload["data"]["summary"]["created_by"] == "POST-H-011-D"
    assert payload["data"]["summary"]["cases_total"] == 1
    assert payload["data"]["summary"]["network_used"] is False
    assert payload["data"]["summary"]["external_api_used"] is False


def test_post_h_011_d_eval_run_suite_bridge_json() -> None:
    result = ApplicationService(ROOT).eval_run(suite="rag-groundedness", case_id="rag-posth-roadmap-prioritized-hitos")

    assert result.ok, result.to_dict()
    assert result.command == "rag groundedness-eval"
    assert result.data["summary"]["created_by"] == "POST-H-011-D"
    assert result.data["summary"]["cases_total"] == 1
    assert result.data["summary"]["queries_with_sources_total"] == 1
