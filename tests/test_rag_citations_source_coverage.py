from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.rag import RagCitationExtractor, RagSourceCoverageEvaluator, SourceCoverageOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = "evals/fixtures/rag_groundedness_post_h_cases.json"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_post_h_011_b_source_coverage_passes_against_fixture_and_index() -> None:
    result = RagSourceCoverageEvaluator(ROOT).run()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-011-B"
    assert summary["suite_id"] == "rag-groundedness-post-h"
    assert summary["cases_total"] >= 10
    assert summary["source_coverage_avg"] >= 0.8
    assert summary["missing_sources_total"] == 0
    assert summary["stale_sources_total"] == 0
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["web_search_used"] is False
    assert summary["llm_judge_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["index_loaded"] is True
    assert summary["indexed_sources_total"] > 0
    assert any(case["citation_refs"] for case in result.data["case_results"])


def test_post_h_011_b_report_conforms_to_groundedness_report_schema() -> None:
    result = RagSourceCoverageEvaluator(ROOT).run()

    validation = SchemaValidator(ROOT).validate_payload(
        schema="RagGroundednessReport",
        payload=result.data["report"],
        instance_label="in-memory:post-h-011-b-source-coverage-report",
    )

    assert validation.ok, validation.to_dict()
    assert validation.data["summary"]["valid"] is True
    assert result.data["report"]["created_by"] == "POST-H-011-B"
    assert result.data["report"]["summary"]["missing_sources_total"] == 0


def test_post_h_011_b_extracts_normalized_metadata_headings_and_snippets() -> None:
    extractor = RagCitationExtractor(ROOT)
    entry, findings = extractor.source_catalog_entry("docs/backlogs/POST-H-011_rag_groundedness_evals.md")

    assert not [finding.to_dict() for finding in findings if finding.severity.value == "block"]
    assert entry["path"] == "docs/backlogs/POST-H-011_rag_groundedness_evals.md"
    assert entry["exists"] is True
    assert entry["allowed"] is True
    assert entry["doc_id"] == "POST-H-011-BACKLOG"
    assert entry["status"] == "approved"
    assert entry["stale"] is False
    assert entry["headings"]
    assert entry["snippets"]
    assert all(snippet["ref"].startswith(entry["path"] + "#L") for snippet in entry["snippets"])


def test_post_h_011_b_falls_back_to_direct_docs_when_index_is_absent(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/source.md",
        "---\ndoc_id: TMP-DOC\nstatus: approved\nupdated: 2026-06-26\n---\n# Source\n\nLocal source evidence.\n",
    )
    fixture = {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-RAG-GROUNDEDNESS-EVAL-V1",
        "suite_id": "tmp-suite",
        "created_by": "POST-H-011-A",
        "status": "implemented-initial",
        "version": "1.0.0",
        "owner": "tests",
        "generated_at_utc": "2026-06-26T22:00:00Z",
        "description": "tmp",
        "local_first": True,
        "dry_run": True,
        "network_used": False,
        "external_api_used": False,
        "web_search_used": False,
        "llm_judge_required": False,
        "remote_execution_enabled": False,
        "connector_write_enabled": False,
        "plugin_execution_enabled": False,
        "minimum_cases_required": 10,
        "suite_defaults": {
            "minimum_source_coverage": 0.8,
            "minimum_claim_support": 0.8,
            "forbidden_claims_block": True,
            "expected_sources_required": True,
            "canonical_sources_only": True,
            "outputs_as_sources_allowed": False,
        },
        "cases": [
            {
                "case_id": "rag-posth-tmp-direct-docs",
                "question": "Pregunta temporal con fuente local suficiente",
                "case_type": "positive",
                "domain": "rag",
                "expected_sources": ["docs/source.md"],
                "required_claims": ["Local source evidence"],
                "forbidden_claims": [],
                "minimum_source_coverage": 1.0,
                "minimum_claim_support": 0.8,
                "risk_level": "high",
                "expected_behavior": "pass_with_sources",
                "tags": ["tmp"],
            }
        ] * 10,
        "notes": ["synthetic"],
    }
    (tmp_path / "evals/fixtures").mkdir(parents=True)
    (tmp_path / FIXTURE_PATH).write_text(json.dumps(fixture), encoding="utf-8")

    result = RagSourceCoverageEvaluator(tmp_path).run()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["index_loaded"] is False
    assert summary["source_coverage_avg"] == 1.0
    assert summary["direct_sources_total"] == 10
    assert any(finding.id == "RAG_INDEX_NOT_FOUND_FOR_COVERAGE" for finding in result.findings)


def test_post_h_011_b_blocks_missing_runtime_remote_and_stale_sources(tmp_path: Path) -> None:
    _write(tmp_path / "docs/deprecated.md", "---\ndoc_id: OLD\nstatus: deprecated\n---\n# Deprecated\n")
    fixture = {
        "suite_id": "synthetic-blocking-suite",
        "cases": [
            {
                "case_id": "rag-posth-blocking-sources",
                "expected_sources": [
                    "docs/missing.md",
                    "outputs/evals/generated.json",
                    "https://example.invalid/source.md",
                    "docs/deprecated.md",
                ],
                "minimum_source_coverage": 1.0,
            }
        ],
    }
    (tmp_path / "evals/fixtures").mkdir(parents=True)
    (tmp_path / FIXTURE_PATH).write_text(json.dumps(fixture), encoding="utf-8")

    result = RagSourceCoverageEvaluator(tmp_path).run()

    assert not result.ok
    assert int(result.exit_code) == 2
    finding_ids = {finding.id for finding in result.findings}
    assert "RAG_SOURCE_MISSING" in finding_ids
    assert "RAG_SOURCE_RUNTIME_PATH_NOT_CANONICAL" in finding_ids
    assert "RAG_SOURCE_REMOTE_NOT_ALLOWED" in finding_ids
    assert "RAG_SOURCE_STALE" in finding_ids
    assert "RAG_SOURCE_LOW_COVERAGE" in finding_ids
    case = result.data["case_results"][0]
    assert case["status"] == "block"
    assert case["source_coverage"] == 0.0
    assert case["stale_sources"] == ["docs/deprecated.md"]
