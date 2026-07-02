from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def test_secure_transport_requirements_schema_and_instance_are_design_only() -> None:
    schema = read_json("docs/schemas/secure_transport_requirements.schema.json")
    requirements = read_json(".devpilot/remote/secure_transport_requirements.json")
    catalog = read_json("docs/schemas/schema_catalog.json")

    assert schema["x-devpilot-schema-id"] == "SCHEMA-DEVPL-SECURE-TRANSPORT-REQUIREMENTS-V1"
    assert schema["properties"]["transport_implemented"]["const"] is False
    assert schema["properties"]["network_allowed"]["const"] is False
    assert schema["properties"]["selected_for_now"]["const"] == "local-only-no-transport"
    assert schema["properties"]["no_go_gates"]["properties"]["sockets_opened"]["const"] is False
    assert schema["properties"]["no_go_gates"]["properties"]["certificates_generated"]["const"] is False
    assert schema["properties"]["no_go_gates"]["properties"]["secrets_required"]["const"] is False
    assert schema["properties"]["no_go_gates"]["properties"]["remote_execution_enabled"]["const"] is False

    assert requirements["schema_id"] == "SCHEMA-DEVPL-SECURE-TRANSPORT-REQUIREMENTS-V1"
    assert requirements["created_by"] == "POST-H-023-A"
    assert requirements["decision_status"] == "design-only"
    assert requirements["transport_implemented"] is False
    assert requirements["network_allowed"] is False
    assert requirements["selected_for_now"] == "local-only-no-transport"
    assert requirements["no_go_gates"]["sockets_opened"] is False
    assert requirements["no_go_gates"]["certificates_generated"] is False
    assert requirements["no_go_gates"]["secrets_required"] is False
    assert requirements["no_go_gates"]["remote_execution_enabled"] is False
    assert requirements["safety"]["network_used"] is False
    assert requirements["safety"]["external_api_used"] is False
    assert requirements["safety"]["remote_execution_used"] is False
    assert requirements["safety"]["secrets_read"] is False

    assert any(
        entry["schema_id"] == "SCHEMA-DEVPL-SECURE-TRANSPORT-REQUIREMENTS-V1"
        and entry["path"] == "docs/schemas/secure_transport_requirements.schema.json"
        for entry in catalog["schemas"]
    )


def test_secure_transport_threats_and_controls_cover_required_categories() -> None:
    requirements = read_json(".devpilot/remote/secure_transport_requirements.json")

    categories = {item["category"] for item in requirements["threats"]}
    severities = {item["severity"] for item in requirements["threats"]}
    control_ids = {item["control_id"] for item in requirements["controls_required"]}

    assert {
        "mitm",
        "replay",
        "spoofing",
        "token_theft",
        "downgrade",
        "impersonation",
    } <= categories
    assert {"critical", "high"} <= severities
    assert len(requirements["threats"]) >= 8
    assert len(control_ids) >= 8
    assert all(item["blocks_enablement"] is True for item in requirements["threats"])
    assert all(item["required_before_transport"] is True for item in requirements["controls_required"])
    assert all(item["implemented_now"] is False for item in requirements["controls_required"])
    assert "replay_protection" in requirements["required_controls_before_implementation"]
    assert "revocation_rotation" in requirements["required_controls_before_implementation"]
    assert "transport_quality_gate" in requirements["required_controls_before_implementation"]


def test_secure_transport_documents_do_not_claim_transport_enablement() -> None:
    design = read_text("docs/03_security/secure_transport_design.md").lower()
    implementation = read_text("docs/POST-H-023_secure_transport_design.md").lower()
    backlog = read_text("docs/backlogs/POST-H-023_secure_transport_design.md")

    for text in (design, implementation):
        assert "secure transport design != secure transport implemented" in text
        assert "transport_implemented=false" in text
        assert "network_allowed=false" in text
        assert "sockets_opened=false" in text
        assert "certificates_generated=false" in text
        assert "secrets_required=false" in text
        assert "remote_execution_enabled=false" in text
        assert "local-only-no-transport" in text

    combined = design + implementation + backlog.lower()
    positive_enablement_claims = [
        "secure transport is now implemented",
        "transport is now enabled",
        "network is now enabled",
        "sockets are now opened",
        "certificates are now generated",
        "secrets are now required",
        "remote execution is now enabled",
        "tls is now implemented",
        "mtls is now implemented",
        "ssh is now implemented",
        "grpc is now implemented",
        "websocket is now implemented",
    ]
    for claim in positive_enablement_claims:
        assert claim not in combined

    assert "transport_implemented=true" in combined
    assert "network_allowed=true" in combined
    assert "remote_execution_enabled=true" in combined
    assert "bloquea el avance" in combined or "block if" in combined

    assert 'status: "approved"' in backlog
    assert 'implementation_status: "closed"' in backlog
    assert 'current_micro_sprint: "POST-H-023-E"' in backlog
    assert 'next_micro_sprint: "POST-H-024"' in backlog


def test_project_state_manifest_source_registry_and_tcr_are_synchronized_for_post_h_023_requirements() -> None:
    state = read_json(".devpilot/project_state.json")
    manifest = read_json("docs/post_h_023_a_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")
    readme = read_text("README.md")
    runbook = read_text("docs/05_operations/runbook.md")
    changelog = read_text("docs/release/CHANGELOG.md")

    assert state["last_completed_sprint"] == "POST-H-023"
    assert state["next_sprint"] == "POST-H-024"
    assert state["current_micro_sprint"] == "POST-H-023-E"
    assert state["next_micro_sprint"] == "POST-H-024"
    assert state["post_h_023_backlog_approved"] is True
    assert state["post_h_023_secure_transport_requirements_schema_registered"] is True
    assert state["post_h_023_secure_transport_design_schema_registered"] is True
    assert state["post_h_023_secure_transport_key_lifecycle_schema_registered"] is True
    assert state["transport_implemented"] is False
    assert state["network_allowed"] is False
    assert state["sockets_opened"] is False
    assert state["certificates_generated"] is False
    assert state["secrets_required"] is False
    assert state["remote_execution_enabled"] is False

    assert manifest["micro_sprint"] == "POST-H-023-A"
    assert manifest["next_sprint"] == "POST-H-023"
    assert manifest["transport_implemented"] is False
    assert manifest["network_allowed"] is False
    assert "docs/schemas/secure_transport_requirements.schema.json" in manifest["created_files"]
    assert ".devpilot/remote/secure_transport_requirements.json" in manifest["created_files"]

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-023-BACKLOG" in doc_ids
    assert "POST-H-023-IMPLEMENTATION-DOC" in doc_ids
    assert "POST-H-023-SECURE-TRANSPORT-DESIGN" in doc_ids
    assert "SCHEMA-DEVPL-SECURE-TRANSPORT-REQUIREMENTS-V1" in doc_ids
    assert "POST-H-023-A-SECURE-TRANSPORT-REQUIREMENTS" in doc_ids
    assert "POST-H-023-A-MANIFEST" in doc_ids
    assert "ADR-POSTH-005" in doc_ids
    assert "SCHEMA-DEVPL-SECURE-TRANSPORT-DESIGN-V1" in doc_ids
    assert "POST-H-023-B-PROTOCOL-DECISION-MATRIX" in doc_ids
    assert "POST-H-023-B-MANIFEST" in doc_ids
    assert "SCHEMA-DEVPL-SECURE-TRANSPORT-KEY-LIFECYCLE-V1" in doc_ids
    assert "POST-H-023-C-KEY-LIFECYCLE" in doc_ids
    assert "POST-H-023-C-MANIFEST" in doc_ids

    contract_ids_v1 = {item["contract_id"] for item in tcr_v1["contracts"]}
    contract_ids_v2 = {item["contract_id"] for item in tcr_v2["contracts"]}
    assert "post-h-023-secure-transport-requirements" in contract_ids_v1
    assert "post-h-023-secure-transport-requirements" in contract_ids_v2
    assert "post-h-023-secure-transport-key-lifecycle" in contract_ids_v1
    assert "post-h-023-secure-transport-key-lifecycle" in contract_ids_v2

    assert "POST-H-023-A — Requisitos y amenazas de transporte" in readme
    assert "POST-H-023-A — Requisitos y amenazas de transporte" in runbook
    assert "POST-H-023-C — Key/certificate lifecycle design" in readme
    assert "POST-H-023-C — Key/certificate lifecycle design" in runbook
    assert "Siguiente micro-sprint: `POST-H-023-E — Runbook y cierre`" in readme
    assert "post-h-023-a" in changelog
    assert "post-h-023-b" in changelog
    assert "post-h-023-c" in changelog
