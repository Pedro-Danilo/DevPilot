from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = "evals/fixtures/rag_groundedness_post_h_cases.json"


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_rag_groundedness_schemas_are_registered() -> None:
    catalog = read_json("docs/schemas/schema_catalog.json")
    entries = {item["schema_id"]: item for item in catalog["schemas"]}

    eval_entry = entries["SCHEMA-DEVPL-RAG-GROUNDEDNESS-EVAL-V1"]
    assert eval_entry["path"] == "docs/schemas/rag_groundedness_eval.schema.json"
    assert eval_entry["contract"] == "RagGroundednessEval"
    assert eval_entry["sprint"] == "POST-H-011-A"
    assert eval_entry["validates_instances"] is True

    report_entry = entries["SCHEMA-DEVPL-RAG-GROUNDEDNESS-REPORT-V1"]
    assert report_entry["path"] == "docs/schemas/rag_groundedness_report.schema.json"
    assert report_entry["contract"] == "RagGroundednessReport"
    assert report_entry["sprint"] == "POST-H-011-A"
    assert report_entry["validates_instances"] is True

    registry_result = SchemaRegistry(ROOT).list()
    assert registry_result.ok, registry_result.to_dict()
    registered = {item["schema_id"] for item in registry_result.data["schemas"]}
    assert "SCHEMA-DEVPL-RAG-GROUNDEDNESS-EVAL-V1" in registered
    assert "SCHEMA-DEVPL-RAG-GROUNDEDNESS-REPORT-V1" in registered


def test_rag_groundedness_fixture_validates_against_schema() -> None:
    result = SchemaValidator(ROOT).validate(schema="RagGroundednessEval", instance=FIXTURE_PATH)

    assert result.ok, result.to_dict()
    assert result.data["summary"]["valid"] is True


def test_rag_groundedness_report_schema_accepts_minimal_future_report() -> None:
    payload = {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-RAG-GROUNDEDNESS-REPORT-V1",
        "report_id": "synthetic-post-h-011-a-report-contract-check",
        "suite_id": "rag-groundedness-post-h",
        "created_by": "POST-H-011-A",
        "status": "implemented-initial",
        "generated_at_utc": "2026-06-26T22:00:00Z",
        "summary": {
            "cases_total": 0,
            "cases_passed": 0,
            "cases_warned": 0,
            "cases_blocked": 0,
            "source_coverage_avg": 0,
            "claim_support_avg": 0,
            "unsupported_claims_total": 0,
            "missing_sources_total": 0,
            "stale_sources_total": 0,
            "forbidden_claims_detected_total": 0,
            "network_used": False,
            "external_api_used": False,
            "web_search_used": False,
            "llm_judge_used": False,
        },
        "case_results": [],
        "findings": [],
        "safety": {
            "local_first": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "web_search_used": False,
            "llm_judge_used": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
        },
        "notes": ["Contract-only synthetic payload for POST-H-011-A."],
    }

    result = SchemaValidator(ROOT).validate_payload(
        schema="RagGroundednessReport",
        payload=payload,
        instance_label="in-memory:rag-groundedness-report-minimal",
    )

    assert result.ok, result.to_dict()
    assert result.data["summary"]["valid"] is True


def test_rag_groundedness_fixture_cases_cover_required_domains_and_no_go_gates() -> None:
    fixture = read_json(FIXTURE_PATH)
    cases = fixture["cases"]

    assert fixture["created_by"] == "POST-H-011-A"
    assert fixture["local_first"] is True
    assert fixture["dry_run"] is True
    assert fixture["network_used"] is False
    assert fixture["external_api_used"] is False
    assert fixture["web_search_used"] is False
    assert fixture["llm_judge_required"] is False
    assert fixture["remote_execution_enabled"] is False
    assert fixture["connector_write_enabled"] is False
    assert fixture["plugin_execution_enabled"] is False
    assert len(cases) >= fixture["minimum_cases_required"] >= 10

    domains = {case["domain"] for case in cases}
    assert {"roadmap", "security", "testing", "architecture", "onboarding", "operations", "rag"}.issubset(domains)

    negative_cases = [case for case in cases if case["case_type"] in {"negative", "mixed"}]
    assert len(negative_cases) >= 3
    assert any("remote execution enabled" in case["forbidden_claims"] for case in negative_cases)
    assert any("plugin execution enabled" in case["forbidden_claims"] for case in negative_cases)
    assert any(case["expected_behavior"] == "block_forbidden_claim" for case in negative_cases)

    for case in cases:
        assert case["expected_sources"], case["case_id"]
        assert case["required_claims"], case["case_id"]
        assert case["minimum_source_coverage"] >= 0.6
        assert case["minimum_claim_support"] >= 0.7


def test_rag_groundedness_expected_sources_are_local_existing_non_runtime_paths() -> None:
    fixture = read_json(FIXTURE_PATH)

    for case in fixture["cases"]:
        for source in case["expected_sources"]:
            assert not source.startswith("outputs/"), (case["case_id"], source)
            assert "://" not in source, (case["case_id"], source)
            assert (ROOT / source).exists(), (case["case_id"], source)
