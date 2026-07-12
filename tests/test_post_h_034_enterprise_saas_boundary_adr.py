from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.schemas import SchemaRegistry, SchemaValidator
from devpilot_core.sensitive_capabilities import EnterpriseSaasBoundaryAdrValidator, SensitiveCapabilityAdrGate, SensitiveCapabilityOptions

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_034_e_schemas_are_registered_and_instances_validate() -> None:
    registry = SchemaRegistry(ROOT).list()
    assert registry.ok, registry.to_dict()
    schema_ids = {schema["schema_id"] for schema in registry.data["schemas"]}
    assert "SCHEMA-DEVPL-ENTERPRISE-SAAS-BOUNDARY-DECISION-V1" in schema_ids
    assert "SCHEMA-DEVPL-SENSITIVE-CAPABILITY-DECISION-MATRIX-V1" in schema_ids

    checklist = SchemaValidator(ROOT).validate(
        schema="EnterpriseSaasBoundaryDecision",
        instance=".devpilot/sensitive_capabilities/enterprise_saas_boundary_checklist.json",
    )
    manifest = SchemaValidator(ROOT).validate(
        schema="EnterpriseSaasBoundaryDecision",
        instance="docs/post_h_034_e_manifest.json",
    )
    matrix = SchemaValidator(ROOT).validate(
        schema="SensitiveCapabilityDecisionMatrix",
        instance=".devpilot/sensitive_capabilities/capability_decision_matrix.json",
    )

    assert checklist.ok, checklist.to_dict()
    assert manifest.ok, manifest.to_dict()
    assert matrix.ok, matrix.to_dict()
    assert checklist.data["summary"]["valid"] is True
    assert manifest.data["summary"]["valid"] is True
    assert matrix.data["summary"]["valid"] is True


def test_post_h_034_e_adr_is_approved_and_does_not_enable_enterprise_saas() -> None:
    adr = (ROOT / "docs/adr/ADR-POSTH-034-E-enterprise-saas-boundary.md").read_text(encoding="utf-8")
    checklist = _read_json(".devpilot/sensitive_capabilities/enterprise_saas_boundary_checklist.json")
    matrix = _read_json(".devpilot/sensitive_capabilities/capability_decision_matrix.json")

    assert 'status: "approved"' in adr
    assert 'decision_status: "continue-blocked"' in adr
    assert 'enterprise_ready_claimed: false' in adr
    assert 'saas_ready_claimed: false' in adr
    assert 'compliance_certification_claim: false' in adr
    assert 'control_plane_enabled: false' in adr
    assert 'tenancy_enabled: false' in adr
    assert 'public_api_enabled: false' in adr
    assert 'network_allowed: false' in adr
    assert "enterprise threat model exists != enterprise-ready" in adr.lower()
    assert "compliance mapping exists != compliance-certified" in adr.lower()
    assert "production-ready-local exists != saas-ready" in adr.lower()

    assert checklist["decision_state"] == "continue-blocked"
    assert checklist["enterprise_ready_claimed"] is False
    assert checklist["enterprise_ready_enabled"] is False
    assert checklist["saas_ready_claimed"] is False
    assert checklist["control_plane_enabled"] is False
    assert checklist["cloud_deployment_enabled"] is False
    assert checklist["tenancy_enabled"] is False
    assert checklist["public_api_enabled"] is False
    assert checklist["compliance_certification_claim"] is False
    assert checklist["external_audit_claimed"] is False
    assert checklist["network_allowed"] is False
    assert checklist["external_api_allowed"] is False
    assert checklist["credentials_required"] is False
    assert checklist["requires_future_enablement_adr"] is True

    capability = next(item for item in matrix["capabilities"] if item["capability_id"] == "enterprise.saas")
    assert capability["decision_state"] == "continue-blocked"
    assert capability["runtime_enabled"] is False
    assert matrix["global_no_go_gates"]["enterprise_ready"] is False
    assert matrix["global_no_go_gates"]["saas_ready"] is False
    assert matrix["global_no_go_gates"]["compliance_certified"] is False
    assert all(capability["runtime_enabled"] is False for capability in matrix["capabilities"])


def test_post_h_034_e_sensitive_capability_gate_passes_with_enterprise_saas_blocked() -> None:
    result = EnterpriseSaasBoundaryAdrValidator(ROOT).validate()
    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["enterprise_saas_decision_state"] == "continue-blocked"
    assert summary["enterprise_ready_claimed"] is False
    assert summary["saas_ready_claimed"] is False
    assert summary["compliance_certification_claim"] is False
    assert summary["control_plane_enabled"] is False
    assert summary["tenancy_enabled"] is False
    assert summary["network_allowed"] is False
    assert any(finding.id == "ENTERPRISE_SAAS_BOUNDARY_ADR_GATE_PASS" for finding in result.findings)

    gate = SensitiveCapabilityAdrGate(ROOT).run()
    assert gate.ok, gate.to_dict()
    assert gate.data["summary"]["subgates_total"] == 5
    assert gate.data["summary"]["subgates_passed"] == 5
    assert gate.data["summary"]["enterprise_saas_boundary_gate_ok"] is True


def test_post_h_034_e_gate_blocks_bad_enterprise_saas_enablement(tmp_path: Path) -> None:
    bad = copy.deepcopy(_read_json(".devpilot/sensitive_capabilities/enterprise_saas_boundary_checklist.json"))
    bad["enterprise_ready_claimed"] = True
    bad["saas_ready_claimed"] = True
    bad["compliance_certification_claim"] = True
    bad_path = tmp_path / "bad_enterprise_saas_boundary.json"
    bad_path.write_text(json.dumps(bad, indent=2), encoding="utf-8")

    options = SensitiveCapabilityOptions(enterprise_saas_boundary_checklist_path=bad_path)
    result = EnterpriseSaasBoundaryAdrValidator(ROOT, options=options).validate()
    assert not result.ok
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "ENTERPRISE_SAAS_DECISION_FLAG_BLOCK" for finding in result.findings)


def test_post_h_034_e_enterprise_and_compliance_artifacts_remain_design_only_or_non_certifying() -> None:
    threat_model = _read_json(".devpilot/enterprise/enterprise_threat_model.json")
    control_matrix = _read_json(".devpilot/enterprise/enterprise_control_matrix.json")
    compliance_controls = _read_json(".devpilot/compliance/control_mappings.json")
    compliance_evidence = _read_json(".devpilot/compliance/evidence_mappings.json")

    assert threat_model["decision_status"] == "design-only"
    assert threat_model["enterprise_deployment_enabled"] is False
    assert threat_model["control_plane_enabled"] is False
    assert threat_model["compliance_certification_claim"] is False
    assert control_matrix["decision_status"] == "design-only"
    assert control_matrix["enterprise_ready_claimed"] is False
    assert control_matrix["enterprise_deployment_enabled"] is False
    assert control_matrix["summary"]["required_not_implemented_total"] > 0
    assert compliance_controls["certification_claimed"] is False
    assert compliance_controls["legal_advice_claimed"] is False
    assert compliance_evidence["certification_claimed"] is False
    assert compliance_evidence["legal_advice_claimed"] is False
    assert "not a certification" in compliance_controls["disclaimer"].lower()


def test_post_h_034_e_project_state_and_claims_remain_blocked() -> None:
    state = _read_json(".devpilot/project_state.json")
    assert state["post_h_034_current_micro_sprint"] == "POST-H-034-E"
    assert state["post_h_034_next_micro_sprint"] == "POST-H-034-CLOSURE"
    assert state["post_h_034_d_closed"] is True
    assert state["post_h_034_e_decision_state"] == "continue-blocked"
    assert state["post_h_034_e_enterprise_ready_claimed"] is False
    assert state["post_h_034_e_enterprise_ready_enabled"] is False
    assert state["post_h_034_e_saas_ready_claimed"] is False
    assert state["post_h_034_e_control_plane_enabled"] is False
    assert state["post_h_034_e_cloud_deployment_enabled"] is False
    assert state["post_h_034_e_tenancy_enabled"] is False
    assert state["post_h_034_e_public_api_enabled"] is False
    assert state["post_h_034_e_compliance_certification_claim"] is False
    assert state["post_h_034_e_network_allowed"] is False
    assert state["post_h_034_e_credentials_required"] is False
    assert state["post_h_034_e_no_go_gates_preserved"] is True
    assert state["post_h_034_e_requires_future_enablement_adr"] is True
    assert state["enterprise_ready_claimed"] is False
    assert state["saas_ready_claimed"] is False
    assert state["compliance_certification_claim"] is False
    assert state["control_plane_enabled"] is False
    assert state["network_allowed"] is False


def test_post_h_034_e_governance_artifacts_are_synchronized() -> None:
    source_registry = {item["doc_id"] for item in _read_json(".devpilot/docs_governance/source_registry.json")["documents"]}
    schema_catalog = {item["schema_id"] for item in _read_json("docs/schemas/schema_catalog.json")["schemas"]}
    tcr_v1 = {item["contract_id"] for item in _read_json(".devpilot/testing/test_contract_registry.json")["contracts"]}
    tcr_v2 = {item["contract_id"] for item in _read_json(".devpilot/testing/test_contract_registry_v2.json")["contracts"]}
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-034_sensitive_capabilities_adrs.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    assert "ADR-POSTH-034-E" in source_registry
    assert "POST-H-034-E-ENTERPRISE-SAAS-BOUNDARY-CHECKLIST" in source_registry
    assert "POST-H-034-E-ENTERPRISE-SAAS-BOUNDARY-SCHEMA" in source_registry
    assert "SCHEMA-DEVPL-ENTERPRISE-SAAS-BOUNDARY-DECISION-V1" in schema_catalog
    assert "post-h-034-enterprise-saas-boundary-adr" in tcr_v1
    assert "post-h-034-enterprise-saas-boundary-adr" in tcr_v2
    assert "POST-H-034-E — Enterprise/SaaS boundary ADR" in readme
    assert "POST-H-034-E — Operación de ADR Enterprise/SaaS boundary" in runbook
    assert 'current_micro_sprint: "POST-H-034-E"' in backlog
    assert 'next_micro_sprint: "POST-H-034-CLOSURE"' in backlog
    assert "post-h-034-e" in changelog


def test_post_h_034_e_no_real_credentials_network_or_claim_terms_are_versioned() -> None:
    sensitive_files = [
        "docs/adr/ADR-POSTH-034-E-enterprise-saas-boundary.md",
        ".devpilot/sensitive_capabilities/enterprise_saas_boundary_checklist.json",
        "docs/audits/post_h_034_e_enterprise_saas_boundary_adr_report.md",
        "docs/post_h_034_e_manifest.json",
    ]
    forbidden = [
        "enterprise_ready_claimed: true",
        '"enterprise_ready_claimed": true',
        "saas_ready_claimed: true",
        '"saas_ready_claimed": true',
        "compliance_certification_claim: true",
        '"compliance_certification_claim": true',
        "control_plane_enabled: true",
        '"control_plane_enabled": true',
        "network_allowed: true",
        '"network_allowed": true',
        "external_api_allowed: true",
        '"external_api_allowed": true',
        "credentials_required: true",
        '"credentials_required": true',
        "api_key",
        "client_secret",
        "private_key",
        "BEGIN PRIVATE KEY",
    ]
    for file_name in sensitive_files:
        content = (ROOT / file_name).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in content, (file_name, token)
