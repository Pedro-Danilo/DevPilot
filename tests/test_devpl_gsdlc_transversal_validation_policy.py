from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / ".devpilot/gsdlc/transversal_validation_policy.json"
DECISION = ROOT / "docs/audits/DEVPL_GSDLC_01_A_FULL_REGRESSION_DECISION.json"

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def test_transversal_validation_policy_is_approved_and_active():
    p = load(POLICY)
    assert p["status"] == "APPROVED/ACTIVE"
    assert p["version"] == "1.0.0"
    assert p["effective_from"] == "DEVPL-GSDLC-01-A"

def test_intermediate_micro_sprints_do_not_auto_enforce_full_regression():
    p = load(POLICY)
    assert p["default"]["intermediate_validation_mode"] == "cumulative-selective"
    assert p["default"]["intermediate_full_regression_enforced"] is False
    assert p["test_impact"]["intermediate_auto_enforce"] is False

def test_backlog_closing_micro_sprint_runs_full_regression_exactly_once():
    p = load(POLICY)
    assert p["default"]["closing_full_regression_runs"] == 1
    assert p["default"]["full_regression_rerun_after_failure"] is False
    assert p["closing_failure_policy"]["validation_mode"] == "composite-full-regression-selective-retest"

def test_intermediate_exception_requires_hard_trigger_decision():
    p = load(POLICY)
    assert len(p["hard_triggers"]) >= 9
    assert p["exception_decision_required"]["required"] is True
    assert p["exception_decision_required"]["run_exactly_once_must_be"] is True

def test_gsdlc_01_a_full_regression_is_deferred_even_when_test_impact_recommends_it():
    p = load(POLICY)
    d = load(DECISION)
    assert p["gsdlc_01"]["A"]["deferred_to"] == "DEVPL-GSDLC-01-E"
    assert d["decision"] == "DEFERRED-TO-BACKLOG-CLOSURE"
    assert d["test_impact"]["full_regression_recommended"] is True
    assert d["execution_policy"]["full_regression_enforced"] is False
    assert d["execution_policy"]["hard_trigger_present"] is False
    assert d["execution_policy"]["deferred_to"] == "DEVPL-GSDLC-01-E"

def test_no_full_regression_rerun_after_closure_failure():
    p = load(POLICY)
    assert p["closing_failure_policy"]["rerun_full"] is False
    assert p["closing_failure_policy"]["selective_retest"] is True
    assert p["closing_failure_policy"]["full_pytest_repeated"] is False


def test_legacy_regression_guard_is_bridged_by_bounded_waiver_not_bypassed():
    p = load(POLICY)
    bridge = p["legacy_guard_bridge"]
    assert bridge["intermediate_compatibility_decision"] == "waiver"
    assert bridge["waiver_expiry_days"] == 7
    assert bridge["must_attach_test_evidence"] is True
    assert bridge["core_guard_bypass_allowed"] is False
