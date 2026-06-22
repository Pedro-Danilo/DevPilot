from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / ".devpilot/evals/post_h_eval_001_decision_matrix.json"
ASSESSMENT_PATH = ROOT / "docs/audits/post_h_eval_001_baseline_assessment.md"

REQUIRED_DOMAINS = {
    "core_cli",
    "application_services",
    "schemas_contracts",
    "project_state",
    "quality_gates",
    "testing_contracts",
    "policy_engine",
    "miasi",
    "approval",
    "rbac_identity",
    "security_guards",
    "agent_runtime",
    "sdlc_agents",
    "multiagent_coordinator",
    "multiagent_workflows",
    "rag_local",
    "connectors_mcp",
    "plugin_registry",
    "multiworkspace",
    "observability_agentops",
    "audit_packs",
    "compliance_packs",
    "release_dry_run",
    "remote_runner_stub",
    "enterprise_reports",
    "web_ui",
    "api_local",
    "documentation_governance",
}
ALLOWED_MATURITY = {
    "production-ready-local",
    "implemented",
    "implemented-initial",
    "experimental",
    "planned",
    "deprecated",
}


def load_matrix() -> dict:
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def test_post_h_eval_001_b_decision_matrix_exists_and_has_contract() -> None:
    matrix = load_matrix()

    assert matrix["id"] == "POST-H-EVAL-001-B"
    assert matrix["status"] == "implemented"
    assert matrix["policy"]["no_runtime_features_added"] is True
    assert matrix["policy"]["no_remote_execution_enabled"] is True
    assert matrix["quality_signals"]["project_state_ok"] is True
    assert matrix["quality_signals"]["hardening_quality_gate_ok"] is True
    assert matrix["domains_total"] == len(matrix["domains"])


def test_post_h_eval_001_b_all_required_domains_are_evaluated() -> None:
    matrix = load_matrix()
    observed = {domain["domain_id"] for domain in matrix["domains"]}

    assert REQUIRED_DOMAINS <= observed
    assert matrix["required_domains_total"] == len(REQUIRED_DOMAINS)


def test_post_h_eval_001_b_domains_have_evidence_maturity_risk_and_action() -> None:
    matrix = load_matrix()

    for domain in matrix["domains"]:
        assert domain["maturity"] in ALLOWED_MATURITY
        assert domain["risk_level"]
        assert domain["priority"] in {"P0", "P1", "P2", "P3"}
        assert domain["recommended_action"]
        assert domain["rationale"]
        assert domain["evidence"]
        assert any(item["exists"] for item in domain["evidence"]), domain["domain_id"]


def test_post_h_eval_001_b_remote_and_enterprise_remain_experimental() -> None:
    matrix = load_matrix()
    by_id = {domain["domain_id"]: domain for domain in matrix["domains"]}

    assert by_id["remote_runner_stub"]["maturity"] == "experimental"
    assert by_id["remote_runner_stub"]["risk_level"] == "critical"
    assert by_id["enterprise_reports"]["maturity"] == "experimental"
    assert matrix["quality_signals"]["remote_runner_enabled"] is False
    assert matrix["quality_signals"]["remote_execution_used"] is False


def test_post_h_eval_001_b_assessment_document_contains_matrix_and_decisions() -> None:
    content = ASSESSMENT_PATH.read_text(encoding="utf-8")

    assert "POST-H-EVAL-001-B — Assessment integral de capacidades y madurez" in content
    assert "Matriz integral de capacidades" in content
    assert "DEC-B-001" in content
    assert "Remote runner stub" in content
    assert "production-ready-local" in content
