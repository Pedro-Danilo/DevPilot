from __future__ import annotations
import copy
from pathlib import Path
import pytest
from devpilot_core.evals.candidate_harness import CandidateEvaluationHarness, CandidateEvalError

BASE="70b5eddce83708c01cfdd6557e82e8369990e878"
FIXTURE=Path(__file__).resolve().parents[1]/"evals/fixtures/candidate_eval_v1.json"

def test_offline_fixture_complete():
    result=CandidateEvaluationHarness.evaluate_file(FIXTURE,baseline_head=BASE)
    assert result["summary"]=={"total":6,"matched":6,"mismatched":0,"negative_cases":4,"mock_only":True,"network_calls":0,"external_api_calls":0,"real_model_evaluated":False,"costs_and_latency":"NOT_AVAILABLE"}
    assert len({r["candidate_id"] for r in result["cases"]})==6

def test_deterministic_report_including_hash():
    one=CandidateEvaluationHarness.evaluate_file(FIXTURE,baseline_head=BASE)
    two=CandidateEvaluationHarness.evaluate_file(FIXTURE,baseline_head=BASE)
    assert one == two and len(one["report_sha256"])==64
    assert all(r["measured_cost_usd"]=="NOT_AVAILABLE" for r in one["cases"])

def test_no_raw_secrets_and_provider_provenance():
    result=CandidateEvaluationHarness.evaluate_file(FIXTURE,baseline_head=BASE)
    assert all(r["provider_id"]=="mock" and r["evidence_level"]=="deterministic_mock_service" for r in result["cases"])
    assert "ignore previous instructions" not in str(result)

def test_quality_codes():
    rows={r["case_id"]:r for r in CandidateEvaluationHarness.evaluate_file(FIXTURE,baseline_head=BASE)["cases"]}
    assert "SCHEMA_MISSING_SUMMARY" in rows["missing-summary"]["finding_ids"]
    assert "UNGROUNDED_CLAIM" in rows["unsupported-claim"]["finding_ids"]
    assert "ADVERSARIAL_CONTENT" in rows["prompt-injection"]["finding_ids"]
    assert "SEMANTIC_MISSING_SUMMARY" in rows["semantic-fail"]["finding_ids"]

@pytest.mark.parametrize("bad",["", "x"*40, "deadbeef", "G"*40])
def test_invalid_head_blocked(bad):
    import json
    with pytest.raises(CandidateEvalError):CandidateEvaluationHarness.evaluate_fixture(json.loads(FIXTURE.read_text()),baseline_head=bad)

@pytest.mark.parametrize("mutant",["duplicate", "invalid-route", "empty", "expected", "missing-rules", "schema"])
def test_fixture_fail_closed(mutant):
    import json
    data=json.loads(FIXTURE.read_text())
    if mutant=="duplicate":data["cases"][1]["id"]=data["cases"][0]["id"]
    elif mutant=="invalid-route":data["cases"][1]["route"]="openai"
    elif mutant=="empty":data["cases"]=[]
    elif mutant=="expected":data["cases"][1].pop("expected_pass")
    elif mutant=="missing-rules":data["cases"][1].pop("rules")
    else:data["schema"]="wrong"
    with pytest.raises(CandidateEvalError):CandidateEvaluationHarness.evaluate_fixture(data,baseline_head=BASE)

def test_disallowed_claim_shape_blocks():
    import json
    data=json.loads(FIXTURE.read_text());data["cases"][0]["candidate_payload"]["claims"]="unstructured"
    row=CandidateEvaluationHarness.evaluate_fixture(data,baseline_head=BASE)["cases"][0]
    assert not row["actual_pass"] and "CLAIMS_NOT_LIST" in row["finding_ids"]

def test_report_mismatch_visible_when_bad_expected():
    import json
    data=json.loads(FIXTURE.read_text());data["cases"][1]["expected_pass"]=True
    result=CandidateEvaluationHarness.evaluate_fixture(data,baseline_head=BASE)
    assert result["summary"]["mismatched"]==1

def test_no_modification_of_dataset():
    import json
    data=json.loads(FIXTURE.read_text());snapshot=copy.deepcopy(data)
    CandidateEvaluationHarness.evaluate_fixture(data,baseline_head=BASE)
    assert data==snapshot
