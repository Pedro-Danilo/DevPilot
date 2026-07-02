from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def test_secure_transport_design_schema_and_matrix_are_design_only() -> None:
    schema = read_json("docs/schemas/secure_transport_design.schema.json")
    matrix = read_json(".devpilot/remote/secure_transport_protocol_decision_matrix.json")
    catalog = read_json("docs/schemas/schema_catalog.json")

    assert schema["x-devpilot-schema-id"] == "SCHEMA-DEVPL-SECURE-TRANSPORT-DESIGN-V1"
    assert schema["properties"]["selected_for_now"]["const"] == "local-only-no-transport"
    assert schema["properties"]["transport_implemented"]["const"] is False
    assert schema["properties"]["network_allowed"]["const"] is False
    assert schema["properties"]["remote_execution_enabled"]["const"] is False
    assert schema["properties"]["requires_future_enablement_adr"]["const"] is True

    assert matrix["schema_id"] == "SCHEMA-DEVPL-SECURE-TRANSPORT-DESIGN-V1"
    assert matrix["created_by"] == "POST-H-023-B"
    assert matrix["decision_status"] == "design-only"
    assert matrix["selected_for_now"] == "local-only-no-transport"
    assert matrix["transport_implemented"] is False
    assert matrix["network_allowed"] is False
    assert matrix["remote_execution_enabled"] is False
    assert matrix["secrets_required"] is False
    assert matrix["requires_future_enablement_adr"] is True

    assert any(
        entry["schema_id"] == "SCHEMA-DEVPL-SECURE-TRANSPORT-DESIGN-V1"
        and entry["path"] == "docs/schemas/secure_transport_design.schema.json"
        for entry in catalog["schemas"]
    )


def test_protocol_decision_matrix_compares_required_alternatives_without_enabling_them() -> None:
    matrix = read_json(".devpilot/remote/secure_transport_protocol_decision_matrix.json")

    protocols = {item["protocol_id"]: item for item in matrix["decision_matrix"]}

    assert {
        "local-only-no-transport",
        "mtls-over-http2",
        "https-token-bound",
        "ssh-restricted",
    } <= set(protocols)

    assert protocols["local-only-no-transport"]["current_decision"] == "selected_current"
    assert protocols["mtls-over-http2"]["current_decision"] == "future_candidate_only"
    assert protocols["https-token-bound"]["current_decision"] == "future_candidate_only"
    assert protocols["ssh-restricted"]["current_decision"] == "rejected_now"

    assert all(item["implementation_allowed_now"] is False for item in protocols.values())
    assert protocols["local-only-no-transport"]["network_required_if_implemented"] is False
    assert protocols["mtls-over-http2"]["network_required_if_implemented"] is True
    assert protocols["https-token-bound"]["network_required_if_implemented"] is True
    assert protocols["ssh-restricted"]["network_required_if_implemented"] is True

    assert "mtls-over-http2" in matrix["rejected_alternatives"]
    assert "https-token-bound" in matrix["rejected_alternatives"]
    assert "ssh-restricted" in matrix["rejected_alternatives"]
    assert "future_enablement_adr" in matrix["required_controls_before_transport"]
    assert "key_certificate_lifecycle" in matrix["required_controls_before_transport"]
    assert "transport_quality_gate" in matrix["required_controls_before_transport"]


def test_adr_posth_005_preserves_design_only_no_go_gates() -> None:
    adr = read_text("docs/adr/ADR-POSTH-005-secure-transport-design-only.md").lower()
    report = read_text("docs/audits/post_h_023_b_protocol_decision_matrix_report.md").lower()
    implementation = read_text("docs/POST-H-023_secure_transport_design.md").lower()
    security_design = read_text("docs/03_security/secure_transport_design.md").lower()

    combined = "\n".join([adr, report, implementation, security_design])

    assert "decision_status: \"design-only\"" in adr
    assert "selected_for_now=local-only-no-transport" in combined
    assert "requires_future_enablement_adr=true" in combined
    assert "transport_implemented=false" in combined
    assert "secure_transport_implemented=false" in combined
    assert "network_allowed=false" in combined
    assert "network_used=false" in combined
    assert "sockets_opened=false" in combined
    assert "certificates_generated=false" in combined
    assert "secrets_required=false" in combined
    assert "secrets_stored=false" in combined
    assert "remote_execution_enabled=false" in combined

    forbidden_positive_claims = [
        "transport is now enabled",
        "network is now enabled",
        "sockets are now opened",
        "certificates are now generated",
        "secrets are now required",
        "remote execution is now enabled",
        "mtls is now implemented",
        "ssh is now implemented",
        "https transport is now implemented",
    ]
    for claim in forbidden_positive_claims:
        assert claim not in combined


def test_post_h_023_b_governance_artifacts_are_synchronized() -> None:
    state = read_json(".devpilot/project_state.json")
    manifest = read_json("docs/post_h_023_b_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")
    readme = read_text("README.md")
    runbook = read_text("docs/05_operations/runbook.md")
    changelog = read_text("docs/release/CHANGELOG.md")
    backlog = read_text("docs/backlogs/POST-H-023_secure_transport_design.md")

    assert state["post_h_023_current_micro_sprint"] == "POST-H-023-E"
    assert state["current_micro_sprint"] == "POST-H-024-A"
    assert state["post_h_023_next_micro_sprint"] == "POST-H-024"
    assert state["post_h_023_secure_transport_design_schema_registered"] is True
    assert state["post_h_023_selected_transport_for_now"] == "local-only-no-transport"
    assert state["post_h_023_requires_future_enablement_adr"] is True
    assert state["transport_implemented"] is False
    assert state["network_allowed"] is False
    assert state["remote_execution_enabled"] is False

    assert manifest["micro_sprint"] == "POST-H-023-B"
    assert manifest["next_micro_sprint"] == "POST-H-023-C"
    assert manifest["transport_implemented"] is False
    assert manifest["network_allowed"] is False
    assert "docs/schemas/secure_transport_design.schema.json" in manifest["created_files"]
    assert ".devpilot/remote/secure_transport_protocol_decision_matrix.json" in manifest["created_files"]
    assert "tests/test_schema_registry.py" in manifest["modified_files"]

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "ADR-POSTH-005" in doc_ids
    assert "SCHEMA-DEVPL-SECURE-TRANSPORT-DESIGN-V1" in doc_ids
    assert "POST-H-023-B-PROTOCOL-DECISION-MATRIX" in doc_ids
    assert "POST-H-023-B-MANIFEST" in doc_ids

    contract_ids_v1 = {item["contract_id"] for item in tcr_v1["contracts"]}
    contract_ids_v2 = {item["contract_id"] for item in tcr_v2["contracts"]}
    assert "post-h-023-secure-transport-protocol-decision" in contract_ids_v1
    assert "post-h-023-secure-transport-protocol-decision" in contract_ids_v2

    assert 'current_micro_sprint: "POST-H-023-E"' in backlog
    assert 'next_micro_sprint: "POST-H-024"' in backlog
    assert "POST-H-023-B — Protocol decision matrix y ADR" in readme
    assert "POST-H-023-B — Protocol decision matrix y ADR" in runbook
    assert "Siguiente micro-sprint: `POST-H-023-E — Runbook y cierre`" in readme
    assert "post-h-023-b" in changelog
