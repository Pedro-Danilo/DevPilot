from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def test_key_lifecycle_schema_and_instance_are_design_only_no_material() -> None:
    schema = read_json("docs/schemas/secure_transport_key_lifecycle.schema.json")
    lifecycle = read_json(".devpilot/remote/secure_transport_key_lifecycle.json")
    catalog = read_json("docs/schemas/schema_catalog.json")

    assert schema["x-devpilot-schema-id"] == "SCHEMA-DEVPL-SECURE-TRANSPORT-KEY-LIFECYCLE-V1"
    assert schema["properties"]["created_by"]["const"] == "POST-H-023-C"
    assert schema["properties"]["lifecycle_status"]["const"] == "design-only-no-material"
    assert schema["properties"]["certificates_generated"]["const"] is False
    assert schema["properties"]["raw_secret_storage_allowed"]["const"] is False
    assert schema["properties"]["private_key_material_present"]["const"] is False
    assert schema["properties"]["network_allowed"]["const"] is False
    assert schema["properties"]["requires_future_enablement_adr"]["const"] is True

    assert lifecycle["schema_id"] == "SCHEMA-DEVPL-SECURE-TRANSPORT-KEY-LIFECYCLE-V1"
    assert lifecycle["created_by"] == "POST-H-023-C"
    assert lifecycle["decision_status"] == "design-only"
    assert lifecycle["lifecycle_status"] == "design-only-no-material"
    assert lifecycle["transport_implemented"] is False
    assert lifecycle["network_allowed"] is False
    assert lifecycle["certificates_generated"] is False
    assert lifecycle["raw_secret_storage_allowed"] is False
    assert lifecycle["private_key_material_present"] is False
    assert lifecycle["requires_future_enablement_adr"] is True

    no_go = lifecycle["no_go_gates"]
    for key in [
        "transport_implemented",
        "secure_transport_implemented",
        "network_allowed",
        "network_used",
        "sockets_opened",
        "certificates_generated",
        "certificate_authority_created",
        "private_key_material_present",
        "raw_secret_storage_allowed",
        "secrets_required",
        "secrets_stored",
        "secrets_read",
        "remote_execution_enabled",
    ]:
        assert no_go[key] is False

    assert any(
        entry["schema_id"] == "SCHEMA-DEVPL-SECURE-TRANSPORT-KEY-LIFECYCLE-V1"
        and entry["path"] == "docs/schemas/secure_transport_key_lifecycle.schema.json"
        for entry in catalog["schemas"]
    )


def test_key_lifecycle_covers_required_future_phases_and_credential_classes() -> None:
    lifecycle = read_json(".devpilot/remote/secure_transport_key_lifecycle.json")

    phases = {item["phase_id"]: item for item in lifecycle["lifecycle_phases"]}
    assert {
        "generation-design",
        "storage-design",
        "distribution-design",
        "rotation-design",
        "revocation-design",
    } <= set(phases)
    assert all(item["implementation_allowed_now"] is False for item in phases.values())
    assert all(item["material_generated_now"] is False for item in phases.values())

    classes = {item["class_id"]: item for item in lifecycle["credential_classes"]}
    assert {"transport-cert", "private-key", "ca-root", "token-binding-secret"} <= set(classes)
    assert all(item["allowed_now"] is False for item in classes.values())
    assert all(item["storage_allowed_now"] is False for item in classes.values())
    assert all(item["raw_value_allowed"] is False for item in classes.values())
    assert all(item["redaction_required"] is True for item in classes.values())

    assert lifecycle["storage_policy"]["raw_secret_storage_allowed"] is False
    assert lifecycle["storage_policy"]["repo_storage_allowed"] is False
    assert lifecycle["storage_policy"]["runtime_db_storage_allowed"] is False
    assert lifecycle["storage_policy"]["logs_raw_secret_allowed"] is False
    assert lifecycle["rotation_policy"]["implemented_now"] is False
    assert lifecycle["rotation_policy"]["requires_overlap_window"] is True
    assert lifecycle["rotation_policy"]["requires_revocation_test"] is True
    assert lifecycle["revocation_policy"]["implemented_now"] is False
    assert lifecycle["revocation_policy"]["fail_closed_required"] is True
    assert lifecycle["revocation_policy"]["requires_kill_switch"] is True


def test_key_lifecycle_documents_do_not_claim_generation_or_storage_enablement() -> None:
    lifecycle_doc = read_text("docs/03_security/secure_transport_key_lifecycle.md").lower()
    report = read_text("docs/audits/post_h_023_c_key_lifecycle_report.md").lower()
    design = read_text("docs/03_security/secure_transport_design.md").lower()
    implementation = read_text("docs/POST-H-023_secure_transport_design.md").lower()
    backlog = read_text("docs/backlogs/POST-H-023_secure_transport_design.md")

    combined = "\n".join([lifecycle_doc, report, design, implementation, backlog.lower()])

    for required in [
        "key lifecycle design != key generation",
        "certificate lifecycle design != certificate creation",
        "secret handling design != secret storage",
        "lifecycle_status=design-only-no-material",
        "certificates_generated=false",
        "certificate_authority_created=false",
        "private_key_material_present=false",
        "raw_secret_storage_allowed=false",
        "secrets_stored=false",
        "secrets_read=false",
        "network_used=false",
        "remote_execution_enabled=false",
    ]:
        assert required in combined

    forbidden_positive_claims = [
        "certificates are now generated",
        "private keys are now generated",
        "certificate authority is now created",
        "raw secret storage is now enabled",
        "secret storage is now enabled",
        "network is now enabled",
        "remote execution is now enabled",
        "mtls is now implemented",
        "ssh is now implemented",
        "https transport is now implemented",
    ]
    for claim in forbidden_positive_claims:
        assert claim not in combined

    assert 'current_micro_sprint: "POST-H-023-D"' in backlog
    assert 'next_micro_sprint: "POST-H-023-E"' in backlog


def test_key_lifecycle_governance_artifacts_are_synchronized() -> None:
    state = read_json(".devpilot/project_state.json")
    manifest = read_json("docs/post_h_023_c_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")
    readme = read_text("README.md")
    runbook = read_text("docs/05_operations/runbook.md")
    changelog = read_text("docs/release/CHANGELOG.md")

    assert state["current_micro_sprint"] == "POST-H-023-D"
    assert state["next_micro_sprint"] == "POST-H-023-E"
    assert state["post_h_023_secure_transport_key_lifecycle_schema_registered"] is True
    assert state["post_h_023_certificates_generated"] is False
    assert state["post_h_023_private_key_material_present"] is False
    assert state["post_h_023_raw_secret_storage_allowed"] is False
    assert state["secrets_stored"] is False
    assert state["secrets_read"] is False
    assert state["network_allowed"] is False
    assert state["remote_execution_enabled"] is False

    assert manifest["micro_sprint"] == "POST-H-023-C"
    assert manifest["next_micro_sprint"] == "POST-H-023-D"
    assert manifest["lifecycle_status"] == "design-only-no-material"
    assert manifest["certificates_generated"] is False
    assert manifest["private_key_material_present"] is False
    assert manifest["raw_secret_storage_allowed"] is False
    assert "docs/schemas/secure_transport_key_lifecycle.schema.json" in manifest["created_files"]
    assert "tests/test_post_h_023_secure_transport_key_lifecycle.py" in manifest["created_files"]

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "SCHEMA-DEVPL-SECURE-TRANSPORT-KEY-LIFECYCLE-V1" in doc_ids
    assert "POST-H-023-C-KEY-LIFECYCLE" in doc_ids
    assert "POST-H-023-SECURE-TRANSPORT-KEY-LIFECYCLE" in doc_ids
    assert "POST-H-023-C-KEY-LIFECYCLE-REPORT" in doc_ids
    assert "POST-H-023-C-MANIFEST" in doc_ids
    assert "POST-H-023-C-KEY-LIFECYCLE-TEST" in doc_ids

    contract_ids_v1 = {item["contract_id"] for item in tcr_v1["contracts"]}
    contract_ids_v2 = {item["contract_id"] for item in tcr_v2["contracts"]}
    assert "post-h-023-secure-transport-key-lifecycle" in contract_ids_v1
    assert "post-h-023-secure-transport-key-lifecycle" in contract_ids_v2

    assert "POST-H-023-C — Key/certificate lifecycle design" in readme
    assert "POST-H-023-C — Key/certificate lifecycle design" in runbook
    assert "Siguiente micro-sprint: `POST-H-023-D — Validator de diseño y no-network invariant`" in readme
    assert "post-h-023-c" in changelog
