from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.rag import GroundednessOptions, RagGroundednessEvaluator
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = "evals/fixtures/rag_groundedness_post_h_cases.json"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_fixture(case: dict) -> dict:
    return {
        "suite_id": "synthetic-claims-suite",
        "cases": [case],
    }


def test_post_h_011_c_groundedness_claims_pass_against_fixture_sources() -> None:
    result = RagGroundednessEvaluator(ROOT).run()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-011-C"
    assert summary["suite_id"] == "rag-groundedness-post-h"
    assert summary["cases_total"] >= 10
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
    assert all(case["status"] == "pass" for case in result.data["case_results"])
    assert all(case["supported_claims_total"] == case["required_claims_total"] for case in result.data["case_results"])


def test_post_h_011_c_report_conforms_to_groundedness_report_schema() -> None:
    result = RagGroundednessEvaluator(ROOT).run()

    validation = SchemaValidator(ROOT).validate_payload(
        schema="RagGroundednessReport",
        payload=result.data["report"],
        instance_label="in-memory:post-h-011-c-groundedness-claims-report",
    )

    assert validation.ok, validation.to_dict()
    assert validation.data["summary"]["valid"] is True
    report = result.data["report"]
    assert report["created_by"] == "POST-H-011-C"
    assert report["summary"]["claim_support_avg"] >= 0.8
    assert report["summary"]["unsupported_claims_total"] == 0
    assert all("claim_evidence" in case for case in report["case_results"])


def test_post_h_011_c_blocks_unsupported_required_claims(tmp_path: Path) -> None:
    _write(tmp_path / "docs/source.md", "---\ndoc_id: TMP\nstatus: approved\n---\n# Source\n\nLocal alpha evidence only.\n")
    case = {
        "case_id": "rag-posth-unsupported-claim",
        "expected_sources": ["docs/source.md"],
        "required_claims": ["Local alpha evidence", "missing beta evidence"],
        "forbidden_claims": [],
        "minimum_source_coverage": 1.0,
        "minimum_claim_support": 1.0,
    }
    (tmp_path / "evals/fixtures").mkdir(parents=True)
    (tmp_path / FIXTURE_PATH).write_text(json.dumps(_minimal_fixture(case)), encoding="utf-8")

    result = RagGroundednessEvaluator(tmp_path).run()

    assert not result.ok
    assert int(result.exit_code) == 2
    claim_case = result.data["case_results"][0]
    assert claim_case["status"] == "block"
    assert claim_case["claim_support"] == 0.5
    assert claim_case["unsupported_claims"] == ["missing beta evidence"]
    finding_ids = {finding.id for finding in result.findings}
    assert "RAG_REQUIRED_CLAIM_UNSUPPORTED" in finding_ids
    assert "RAG_CLAIM_SUPPORT_BELOW_THRESHOLD" in finding_ids


def test_post_h_011_c_blocks_forbidden_claims_in_candidate_answer(tmp_path: Path) -> None:
    _write(tmp_path / "docs/source.md", "---\ndoc_id: TMP\nstatus: approved\n---\n# Source\n\nRemote execution remains blocked by deny-by-default policy.\n")
    case = {
        "case_id": "rag-posth-forbidden-answer",
        "expected_sources": ["docs/source.md"],
        "required_claims": ["remote execution", "deny-by-default"],
        "forbidden_claims": ["remote execution enabled"],
        "minimum_source_coverage": 1.0,
        "minimum_claim_support": 1.0,
    }
    (tmp_path / "evals/fixtures").mkdir(parents=True)
    (tmp_path / FIXTURE_PATH).write_text(json.dumps(_minimal_fixture(case)), encoding="utf-8")

    result = RagGroundednessEvaluator(
        tmp_path,
        options=GroundednessOptions(candidate_answers={"rag-posth-forbidden-answer": "Remote execution enabled for production use."}),
    ).run()

    assert not result.ok
    assert int(result.exit_code) == 2
    claim_case = result.data["case_results"][0]
    assert claim_case["status"] == "block"
    assert claim_case["claim_support"] == 1.0
    assert claim_case["forbidden_claims_detected"] == ["remote execution enabled"]
    assert claim_case["candidate_answer_evaluated"] is True
    assert any(finding.id == "RAG_FORBIDDEN_CLAIM_DETECTED" for finding in result.findings)


def test_post_h_011_c_non_strict_mode_warns_low_claim_support(tmp_path: Path) -> None:
    _write(tmp_path / "docs/source.md", "---\ndoc_id: TMP\nstatus: approved\n---\n# Source\n\nOnly alpha is supported.\n")
    case = {
        "case_id": "rag-posth-warning-claim-support",
        "expected_sources": ["docs/source.md"],
        "required_claims": ["alpha", "gamma"],
        "forbidden_claims": [],
        "minimum_source_coverage": 1.0,
        "minimum_claim_support": 1.0,
    }
    (tmp_path / "evals/fixtures").mkdir(parents=True)
    (tmp_path / FIXTURE_PATH).write_text(json.dumps(_minimal_fixture(case)), encoding="utf-8")

    result = RagGroundednessEvaluator(tmp_path, options=GroundednessOptions(strict=False)).run()

    assert result.ok
    claim_case = result.data["case_results"][0]
    assert claim_case["status"] == "warning"
    assert claim_case["claim_support"] == 0.5
    assert claim_case["unsupported_claims"] == ["gamma"]
    assert any(finding.severity.value == "warning" for finding in result.findings)
