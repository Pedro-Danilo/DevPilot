from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.enterprise import (
    EnterpriseThreatModelQualityGate,
    EnterpriseThreatModelReporter,
    EnterpriseThreatModelValidator,
)


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def test_post_h_022_backlog_and_project_state_are_closed_for_post_h_023() -> None:
    backlog = read_text("docs/backlogs/POST-H-022_enterprise_deployment_threat_model.md")
    implementation = read_text("docs/POST-H-022_enterprise_deployment_threat_model.md")
    state = read_json(".devpilot/project_state.json")

    for text in (backlog, implementation):
        assert 'implementation_status: "closed"' in text
        assert 'current_micro_sprint: "POST-H-022-E"' in text
        assert 'next_micro_sprint: "POST-H-023"' in text
        assert "implemented-initial / design-only" in text

    assert state["last_completed_sprint"] == "POST-H-022"
    assert state["next_sprint"] == "POST-H-023"
    assert state["current_micro_sprint"] == "POST-H-022-E"
    assert state["next_micro_sprint"] == "POST-H-023"
    assert state["post_h_022_closed"] is True
    assert state["post_h_022_enterprise_deployment_threat_model_closed"] is True
    assert state["post_h_022_enterprise_design_runbook_path"] == "docs/05_operations/enterprise_design_runbook.md"
    assert state["post_h_022_enterprise_closure_report_path"] == "docs/audits/post_h_022_e_enterprise_closure_report.md"


def test_enterprise_design_runbook_declares_go_no_go_and_no_readiness_claims() -> None:
    runbook = read_text("docs/05_operations/enterprise_design_runbook.md").lower()
    closure_report = read_text("docs/audits/post_h_022_e_enterprise_closure_report.md").lower()
    readme = read_text("README.md")
    operations = read_text("docs/05_operations/runbook.md")

    for text in (runbook, closure_report):
        assert "enterprise report != enterprise readiness" in text
        assert "enterprise_deployment_enabled=false" in text
        assert "remote_execution_enabled=false" in text
        assert "secure_transport_implemented=false" in text
        assert "compliance_certification_claim=false" in text
        assert "enterprise_ready_claimed=false" in text
        assert "required-not-implemented" in text or "required_not_implemented_total>0" in text
        assert "post-h-023" in text

    assert "GO para diseño" in read_text("docs/05_operations/enterprise_design_runbook.md")
    assert "NO-GO para ejecución enterprise" in read_text("docs/05_operations/enterprise_design_runbook.md")
    assert "Último hito: `POST-H-022`" in readme
    assert "Siguiente hito: `POST-H-023`" in readme
    assert "Último hito: `POST-H-022`" in operations
    assert "Siguiente hito: `POST-H-023`" in operations

    forbidden_claims = [
        "enterprise-ready=true",
        "production enterprise enabled",
        "certified compliant",
        "compliance-certified",
        "remote execution enabled",
        "control plane enabled",
    ]
    combined = runbook + closure_report
    for claim in forbidden_claims:
        assert claim not in combined


def test_post_h_022_e_manifest_source_registry_and_tcr_are_registered() -> None:
    manifest = read_json("docs/post_h_022_e_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    assert manifest["micro_sprint"] == "POST-H-022-E"
    assert manifest["next_sprint"] == "POST-H-023"
    assert manifest["enterprise_deployment_enabled"] is False
    assert manifest["remote_execution_enabled"] is False
    assert manifest["secure_transport_implemented"] is False
    assert manifest["compliance_certification_claim"] is False
    assert manifest["enterprise_ready_claimed"] is False
    assert "docs/05_operations/enterprise_design_runbook.md" in manifest["created_files"]
    assert "tests/test_post_h_022_enterprise_closure.py" in manifest["created_files"]

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-022-ENTERPRISE-DESIGN-RUNBOOK" in doc_ids
    assert "POST-H-022-E-ENTERPRISE-CLOSURE-REPORT" in doc_ids
    assert "POST-H-022-E-MANIFEST" in doc_ids
    assert "POST-H-022-E-ENTERPRISE-CLOSURE-TEST" in doc_ids
    assert source_registry["project_state_snapshot"]["last_completed_sprint"] == "POST-H-022"
    assert source_registry["project_state_snapshot"]["next_sprint"] == "POST-H-023"

    contract_ids_v1 = {item["contract_id"] for item in tcr_v1["contracts"]}
    contract_ids_v2 = {item["contract_id"] for item in tcr_v2["contracts"]}
    assert "post-h-022-enterprise-runbook-closure" in contract_ids_v1
    assert "post-h-022-enterprise-runbook-closure" in contract_ids_v2

    closure_contract = next(
        item for item in tcr_v1["contracts"] if item["contract_id"] == "post-h-022-enterprise-runbook-closure"
    )
    assert closure_contract["scope"] == "safety"
    assert closure_contract["critical"] is True
    assert closure_contract["mutable_global_state_allowed"] is False


def test_enterprise_validator_reporter_and_gate_remain_design_only_after_closure() -> None:
    validator_result = EnterpriseThreatModelValidator(ROOT).validate()
    assert validator_result.ok is True
    summary = validator_result.data["summary"]
    assert summary["decision_status"] == "design-only"
    assert summary["enterprise_deployment_enabled"] is False
    assert summary["remote_execution_enabled"] is False
    assert summary["secure_transport_implemented"] is False
    assert summary["compliance_certification_claim"] is False
    assert summary["enterprise_ready_claimed"] is False
    assert summary["required_not_implemented_total"] > 0
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["secrets_read"] is False

    report_result = EnterpriseThreatModelReporter(ROOT).build(write_report=False)
    assert report_result.ok is True
    assert report_result.data["summary"]["reports_written"] is False
    assert report_result.data["report"]["decision_status"] == "design-only"
    assert report_result.data["report"]["enterprise_deployment_enabled"] is False
    assert report_result.data["report"]["enterprise_ready_claimed"] is False

    gate_result = EnterpriseThreatModelQualityGate(ROOT).run()
    assert gate_result.ok is True
    gate_summary = gate_result.data["summary"]
    assert gate_summary["quality_gate_subgate"] == "enterprise-threat-model-design-only"
    assert gate_summary["reports_written"] is False
    assert gate_summary["blocking_findings_total"] == 0
