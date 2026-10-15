"""R01-09: deterministic/offline evaluation for MP-v2 candidate envelopes.

This is a rule-based gate, *not* an LLM judge or real-model benchmark.
No network, provider invocation, filesystem mutation or implicit approval.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from devpilot_core.generation.contracts import (
    ArtifactCandidateEnvelope, CandidateOrigin, CandidateOriginKind,
    GenerationProvenance, GenerationRequest, ProviderClass,
    canonical_sha256, create_candidate,
)

SCHEMA = "devpilot.mp132.candidate-eval.v1"


class CandidateEvalError(ValueError):
    """An unsafe or inconsistent fixture cannot be executed."""


def _fail_codes(case: Mapping[str, Any], candidate: ArtifactCandidateEnvelope[Any], request: GenerationRequest) -> list[str]:
    rules = case["rules"]
    payload = candidate.payload
    failures: list[str] = []
    if not candidate.content_integrity_ok() or candidate.canonical_input_sha256 != request.canonical_input_sha256:
        failures.append("INTEGRITY_MISMATCH")
    if not isinstance(payload, dict):
        return failures + ["SCHEMA_PAYLOAD_NOT_OBJECT"]
    for field in rules.get("required_fields", []):
        if field not in payload or payload[field] is None or isinstance(payload[field], str) and not payload[field].strip():
            failures.append("SCHEMA_MISSING_" + field.upper())
    forbidden = rules.get("forbidden_phrases", [])
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False).casefold()
    if any(isinstance(phrase, str) and phrase.casefold() in text for phrase in forbidden):
        failures.append("ADVERSARIAL_CONTENT")
    for field, required_fragments in rules.get("semantic_contains", {}).items():
        value = payload.get(field)
        if not isinstance(value, str) or any(fragment.casefold() not in value.casefold() for fragment in required_fragments):
            failures.append("SEMANTIC_MISSING_" + field.upper())
    approved_refs = set(rules.get("approved_evidence_refs", []))
    claims = payload.get("claims", [])
    if not isinstance(claims, list):
        failures.append("CLAIMS_NOT_LIST")
    else:
        for claim in claims:
            if not isinstance(claim, dict) or not isinstance(claim.get("text"), str) or not claim["text"].strip():
                failures.append("INVALID_CLAIM")
            elif claim.get("evidence_ref") not in approved_refs:
                failures.append("UNGROUNDED_CLAIM")
    if candidate.unsupported_claims:
        failures.append("UNSUPPORTED_CLAIMS_DECLARED")
    return sorted(set(failures))


class CandidateEvaluationHarness:
    """Evaluate versioned fixture candidates with preapproved deterministic rules."""

    @staticmethod
    def evaluate_fixture(fixture: Mapping[str, Any], *, baseline_head: str) -> dict[str, Any]:
        if fixture.get("schema") != SCHEMA or fixture.get("version") != 1:
            raise CandidateEvalError("UNSUPPORTED_EVAL_FIXTURE_SCHEMA")
        if not isinstance(baseline_head, str) or len(baseline_head) != 40 or any(c not in "0123456789abcdef" for c in baseline_head):
            raise CandidateEvalError("INVALID_BASELINE_HEAD")
        cases = fixture.get("cases")
        if not isinstance(cases, list) or not cases:
            raise CandidateEvalError("EMPTY_EVAL_DATASET")
        ids = [case.get("id") for case in cases if isinstance(case, dict)]
        if len(ids) != len(cases) or any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids):
            raise CandidateEvalError("INVALID_CASE_IDS")
        rows = []
        for case in cases:
            if not isinstance(case.get("rules"), dict) or not isinstance(case.get("candidate_payload"), dict):
                raise CandidateEvalError("INVALID_CASE_CONTRACT")
            if case.get("route") != "mock-deterministic":
                raise CandidateEvalError("PROVIDER_ROUTE_NOT_AUTHORIZED")
            expected = case.get("expected_pass")
            if type(expected) is not bool:
                raise CandidateEvalError("MISSING_EXPECTED_RESULT")
            req = GenerationRequest(
                request_id="eval-" + case["id"], artifact_type="architecture",
                profile_version="architecture/v1", dependency_profile_version="architecture-deps/v1",
                upstream_hashes={"requirements": canonical_sha256(case.get("context", {}))},
                owner_inputs={"case_id": case["id"]}, preferred_route="deterministic",
                allowed_routes=("deterministic",), policy_snapshot={"external_api": False},
                budget_snapshot={"max_cost_usd": 0.0}, context_reference="fixture:" + str(fixture["dataset_id"]),
            )
            origin = CandidateOrigin(kind=CandidateOriginKind.PROVIDER, provider_class=ProviderClass.DETERMINISTIC,
                                     provider_id="mock", model_id="deterministic-fixture-v1")
            candidate = create_candidate(request=req, payload=case["candidate_payload"], origin=origin,
                                         provenance=GenerationProvenance(profile_ref=req.profile_version,
                                                                        context_ref=req.context_reference))
            failures = _fail_codes(case, candidate, req)
            actual_pass = not failures
            rows.append({
                "case_id": case["id"], "expected_pass": expected, "actual_pass": actual_pass,
                "matched": expected == actual_pass, "finding_ids": failures,
                "candidate_id": candidate.candidate_id, "candidate_version": candidate.version,
                "candidate_sha256": candidate.content_sha256, "input_sha256": req.canonical_input_sha256,
                "provider_id": "mock", "model_id": "deterministic-fixture-v1",
                "source_ref": req.context_reference,
                "measured_cost_usd": "NOT_AVAILABLE", "measured_latency_ms": "NOT_AVAILABLE",
                "evidence_level": "deterministic_mock_service",
            })
        results = {
            "schema": "devpilot.mp132.candidate-eval-report.v1",
            "dataset_id": fixture["dataset_id"], "dataset_version": fixture["version"],
            "dataset_sha256": canonical_sha256(fixture), "baseline_head": baseline_head,
            "cases": rows,
            "summary": {"total": len(rows), "matched": sum(r["matched"] for r in rows),
                        "mismatched": sum(not r["matched"] for r in rows),
                        "negative_cases": sum(not r["expected_pass"] for r in rows),
                        "mock_only": True, "network_calls": 0, "external_api_calls": 0,
                        "real_model_evaluated": False, "costs_and_latency": "NOT_AVAILABLE"},
        }
        results["report_sha256"] = canonical_sha256(results)
        return results

    @classmethod
    def evaluate_file(cls, fixture_path: Path, *, baseline_head: str) -> dict[str, Any]:
        return cls.evaluate_fixture(json.loads(Path(fixture_path).read_text(encoding="utf-8")),baseline_head=baseline_head)
