from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def test_enterprise_threat_model_schema_and_instance_are_design_only() -> None:
    schema = read_json("docs/schemas/enterprise_threat_model.schema.json")
    model = read_json(".devpilot/enterprise/enterprise_threat_model.json")
    catalog = read_json("docs/schemas/schema_catalog.json")

    assert schema["x-devpilot-schema-id"] == "SCHEMA-DEVPL-ENTERPRISE-THREAT-MODEL-V1"
    assert schema["properties"]["enterprise_deployment_enabled"]["const"] is False
    assert schema["properties"]["production_multiuser_enabled"]["const"] is False
    assert schema["properties"]["control_plane_enabled"]["const"] is False
    assert schema["properties"]["remote_execution_enabled"]["const"] is False
    assert schema["properties"]["secure_transport_implemented"]["const"] is False
    assert schema["properties"]["compliance_certification_claim"]["const"] is False

    assert model["schema_id"] == "SCHEMA-DEVPL-ENTERPRISE-THREAT-MODEL-V1"
    assert model["created_by"] == "POST-H-022-A"
    assert model["decision_status"] == "design-only"
    assert model["enterprise_deployment_enabled"] is False
    assert model["production_multiuser_enabled"] is False
    assert model["control_plane_enabled"] is False
    assert model["remote_execution_enabled"] is False
    assert model["secure_transport_implemented"] is False
    assert model["compliance_certification_claim"] is False
    assert model["safety"]["network_used"] is False
    assert model["safety"]["external_api_used"] is False
    assert model["safety"]["secrets_read"] is False

    assert any(
        entry["schema_id"] == "SCHEMA-DEVPL-ENTERPRISE-THREAT-MODEL-V1"
        and entry["path"] == "docs/schemas/enterprise_threat_model.schema.json"
        for entry in catalog["schemas"]
    )


def test_enterprise_assets_actors_boundaries_cover_required_backlog_items() -> None:
    model = read_json(".devpilot/enterprise/enterprise_threat_model.json")

    asset_ids = {item["asset_id"] for item in model["assets"]}
    actor_ids = {item["actor_id"] for item in model["actors"]}
    boundary_ids = {item["boundary_id"] for item in model["trust_boundaries"]}
    flow_ids = {item["flow_id"] for item in model["data_flows"]}

    assert len(asset_ids) >= 8
    assert len(actor_ids) >= 6
    assert len(boundary_ids) >= 4
    assert len(flow_ids) >= 3

    assert {
        "workspace",
        "source_code",
        "local_store",
        "reports",
        "traces",
        "approvals",
        "secrets",
    }.issubset(asset_ids)
    assert {
        "owner",
        "local_operator",
        "developer",
        "auditor",
        "malicious_local_user",
        "future_remote_worker",
    }.issubset(actor_ids)
    assert {
        "local_machine",
        "workspace_root",
        "api_localhost",
        "future_network_boundary",
    }.issubset(boundary_ids)

    assert all(flow["network_used"] is False for flow in model["data_flows"])
    assert any(item["no_go_gate"] is True for item in model["trust_boundaries"])
    assert all(value is False for value in model["no_go_gates"].values())


def test_enterprise_threat_catalog_covers_boundaries_controls_and_residual_risks() -> None:
    model = read_json(".devpilot/enterprise/enterprise_threat_model.json")

    boundary_ids = {item["boundary_id"] for item in model["trust_boundaries"]}
    threats = model["threat_catalog"]
    controls = {item["control_id"]: item for item in model["required_controls"]}
    residual_risks = {item["risk_id"]: item for item in model["residual_risks"]}
    summary = model["threat_catalog_summary"]

    assert summary["created_by"] == "POST-H-022-B"
    assert set(summary["methodologies"]) == {"STRIDE", "LINDDUN"}
    assert summary["all_boundaries_have_threats"] is True
    assert summary["critical_threats_have_controls"] is True
    assert summary["enterprise_deployment_enabled"] is False
    assert summary["remote_execution_enabled"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False

    threat_boundary_ids = {item["boundary_id"] for item in threats}
    assert boundary_ids <= threat_boundary_ids
    assert len(threats) >= len(boundary_ids)
    assert len(controls) >= 8
    assert len(residual_risks) >= 6

    stride_categories = {category for threat in threats for category in threat["stride_categories"]}
    linddun_categories = {category for threat in threats for category in threat["linddun_categories"]}
    assert {
        "spoofing",
        "tampering",
        "repudiation",
        "information_disclosure",
        "denial_of_service",
        "elevation_of_privilege",
    } <= stride_categories
    assert {"disclosure_of_information", "non_compliance", "unawareness"} <= linddun_categories

    critical_threats = [item for item in threats if item["severity"] == "critical"]
    assert critical_threats
    for threat in critical_threats:
        assert threat["required_control_ids"]
        assert all(control_id in controls for control_id in threat["required_control_ids"])
        assert all(risk_id in residual_risks for risk_id in threat["residual_risk_ids"])

    assert any(threat["boundary_id"] == "secrets_boundary" and threat["severity"] == "critical" for threat in threats)
    assert any("remote_runner" in risk["no_go_until"] for risk in residual_risks.values())


def test_enterprise_threat_model_documents_do_not_overclaim_enterprise_readiness() -> None:
    threat_model = read_text("docs/03_security/enterprise_deployment_threat_model.md").lower()
    implementation = read_text("docs/POST-H-022_enterprise_deployment_threat_model.md").lower()
    backlog = read_text("docs/backlogs/POST-H-022_enterprise_deployment_threat_model.md")

    for text in (threat_model, implementation):
        assert "enterprise_deployment_enabled=false" in text
        assert "remote_execution_enabled=false" in text
        assert "compliance_certification_claim=false" in text
        assert "enterprise report != enterprise readiness" in text
        assert "control plane" in text
        assert "secretos" in text or "secrets" in text
        assert "trazas" in text or "traces" in text
        assert "approvals" in text or "aprobaciones" in text

    forbidden_claims = [
        "enterprise-ready=true",
        "production enterprise enabled",
        "certified compliant",
        "compliance-certified",
        "sso enabled",
        "remote execution enabled",
        "control plane enabled",
    ]
    combined = threat_model + implementation
    for claim in forbidden_claims:
        assert claim not in combined

    assert 'status: "approved"' in backlog
    assert 'implementation_status: "active"' in backlog
    assert 'current_micro_sprint: "POST-H-022-B"' in backlog
    assert 'next_micro_sprint: "POST-H-022-C"' in backlog
    assert "stride/linddun" in threat_model
    assert "critical_threats_have_controls=true" in threat_model


def test_project_state_and_historical_remote_closure_are_synchronized_for_post_h_022_a() -> None:
    state = read_json(".devpilot/project_state.json")
    readme = read_text("README.md")
    runbook = read_text("docs/05_operations/runbook.md")
    changelog = read_text("docs/release/CHANGELOG.md")

    assert state["last_completed_sprint"] == "POST-H-021"
    assert state["next_sprint"] == "POST-H-022"
    assert state["current_micro_sprint"] == "POST-H-022-B"
    assert state["next_micro_sprint"] == "POST-H-022-C"
    assert state["post_h_021_closed"] is True
    assert state["post_h_022_current_micro_sprint"] == "POST-H-022-B"
    assert state["post_h_022_next_micro_sprint"] == "POST-H-022-C"
    assert state["post_h_022_enterprise_threat_catalog_registered"] is True
    assert state["post_h_022_enterprise_critical_threats_have_controls"] is True
    assert state["post_h_022_enterprise_all_boundaries_have_threats"] is True
    assert state["enterprise_deployment_enabled"] is False
    assert state["remote_execution_enabled"] is False
    assert any("POST-H-022-A approves Enterprise deployment threat model" in note for note in state["notes"])
    assert any("POST-H-022-B adds STRIDE/LINDDUN threat catalog" in note for note in state["notes"])

    for text in (readme, runbook):
        assert "POST-H-022-A — Asset inventory y trust boundaries" in text
        assert "POST-H-022-B — Threat catalog STRIDE/LINDDUN adaptado" in text
        assert "Último hito cerrado: `POST-H-021`" in text
        assert "Siguiente hito: `POST-H-022`" in text

    assert "post-h-022-a" in changelog
    assert "post-h-022-b" in changelog
    assert "EnterpriseThreatModel" in changelog


def test_post_h_022_a_manifest_source_registry_and_tcr_are_registered() -> None:
    manifest = read_json("docs/post_h_022_a_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    assert manifest["micro_sprint"] == "POST-H-022-A"
    assert manifest["enterprise_deployment_enabled"] is False
    assert "docs/schemas/enterprise_threat_model.schema.json" in manifest["created_files"]
    assert ".devpilot/enterprise/enterprise_threat_model.json" in manifest["created_files"]
    assert "tests/test_post_h_022_enterprise_threat_model.py" in manifest["created_files"]

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-022-BACKLOG" in doc_ids
    assert "SCHEMA-DEVPL-ENTERPRISE-THREAT-MODEL-V1" in doc_ids
    assert "POST-H-022-ENTERPRISE-THREAT-MODEL" in doc_ids
    assert "POST-H-022-A-ENTERPRISE-THREAT-MODEL-INSTANCE" in doc_ids
    assert "POST-H-022-A-MANIFEST" in doc_ids

    contract_ids_v1 = {item["contract_id"] for item in tcr_v1["contracts"]}
    contract_ids_v2 = {item["contract_id"] for item in tcr_v2["contracts"]}
    assert "post-h-022-enterprise-threat-model" in contract_ids_v1
    assert "post-h-022-enterprise-threat-model" in contract_ids_v2

    manifest_b = read_json("docs/post_h_022_b_manifest.json")
    assert manifest_b["micro_sprint"] == "POST-H-022-B"
    assert manifest_b["enterprise_deployment_enabled"] is False
    assert "docs/audits/post_h_022_b_enterprise_threat_catalog_report.md" in manifest_b["created_files"]
    assert "POST-H-022-B-ENTERPRISE-THREAT-CATALOG-REPORT" in doc_ids
    assert "POST-H-022-B-MANIFEST" in doc_ids
    assert "post-h-022-enterprise-threat-catalog" in contract_ids_v1
    assert "post-h-022-enterprise-threat-catalog" in contract_ids_v2
