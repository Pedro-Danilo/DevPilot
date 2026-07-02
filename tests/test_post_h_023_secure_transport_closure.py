from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.remote import SecureTransportDesignQualityGate, SecureTransportDesignValidator


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def test_secure_transport_runbook_declares_design_only_closure() -> None:
    runbook = read_text("docs/05_operations/secure_transport_design_runbook.md")
    closure_report = read_text("docs/audits/post_h_023_e_secure_transport_closure_report.md")

    required_fragments = [
        'status: "approved"',
        'implementation_status: "implemented-initial"',
        "secure transport design != secure transport implemented",
        "validator PASS != autorización de red",
        "selected_for_now=local-only-no-transport",
        "transport_implemented=false",
        "secure_transport_implemented=false",
        "network_allowed=false",
        "network_used=false",
        "sockets_opened=false",
        "certificates_generated=false",
        "certificate_authority_created=false",
        "private_key_material_present=false",
        "raw_secret_storage_allowed=false",
        "secrets_required=false",
        "secrets_stored=false",
        "secrets_read=false",
        "remote_execution_enabled=false",
        "connector_write_enabled=false",
        "plugin_execution_enabled=false",
        "ADR futura",
        "POST-H-024",
    ]

    for text in (runbook, closure_report):
        for fragment in required_fragments:
            assert fragment in text

    forbidden_claims = [
        "transport production-ready",
        "remote-ready=true",
        "secure transport is implemented",
        "network is allowed",
        "remote execution is enabled",
    ]
    combined = (runbook + "\n" + closure_report).lower()
    for claim in forbidden_claims:
        assert claim.lower() not in combined


def test_post_h_023_backlog_and_implementation_are_closed_for_post_h_024() -> None:
    backlog = read_text("docs/backlogs/POST-H-023_secure_transport_design.md")
    implementation = read_text("docs/POST-H-023_secure_transport_design.md")
    state = read_json(".devpilot/project_state.json")

    for text in (backlog, implementation):
        assert 'implementation_status: "closed"' in text
        assert 'current_micro_sprint: "POST-H-023-E"' in text
        assert 'next_micro_sprint: "POST-H-024"' in text
        assert "implemented-initial / design-only" in text
        assert "POST-H-023-E — Runbook y cierre" in text
        assert "POST-H-024" in text

    assert state["last_completed_sprint"] == "POST-H-023"
    assert state["next_sprint"] == "POST-H-024"
    assert state["current_micro_sprint"] == "POST-H-024-B"
    assert state["next_micro_sprint"] == "POST-H-024-C"
    assert state["post_h_023_closed"] is True
    assert state["post_h_023_secure_transport_design_closed"] is True
    assert state["post_h_023_secure_transport_design_runbook_path"] == "docs/05_operations/secure_transport_design_runbook.md"
    assert state["post_h_023_secure_transport_closure_report_path"] == "docs/audits/post_h_023_e_secure_transport_closure_report.md"
    assert state["secure_transport_implemented"] is False
    assert state["network_allowed"] is False
    assert state["remote_execution_enabled"] is False


def test_post_h_023_e_manifest_source_registry_and_tcr_are_registered() -> None:
    manifest = read_json("docs/post_h_023_e_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    assert manifest["micro_sprint"] == "POST-H-023-E"
    assert manifest["status"] == "closed"
    assert manifest["closure"]["backlog_closed"] is True
    assert manifest["closure"]["next_sprint"] == "POST-H-024"
    assert manifest["transport_implemented"] is False
    assert manifest["secure_transport_implemented"] is False
    assert manifest["network_allowed"] is False
    assert manifest["remote_execution_enabled"] is False
    assert "docs/05_operations/secure_transport_design_runbook.md" in manifest["created_files"]
    assert "tests/test_post_h_023_secure_transport_closure.py" in manifest["created_files"]

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-023-SECURE-TRANSPORT-DESIGN-RUNBOOK" in doc_ids
    assert "POST-H-023-E-SECURE-TRANSPORT-CLOSURE-REPORT" in doc_ids
    assert "POST-H-023-E-MANIFEST" in doc_ids
    assert "POST-H-023-E-SECURE-TRANSPORT-CLOSURE-TEST" in doc_ids
    assert source_registry["project_state_snapshot"]["last_completed_sprint"] == "POST-H-023"
    assert source_registry["project_state_snapshot"]["next_sprint"] == "POST-H-024"

    contract_ids_v1 = {item["contract_id"] for item in tcr_v1["contracts"]}
    contract_ids_v2 = {item["contract_id"] for item in tcr_v2["contracts"]}
    assert "post-h-023-secure-transport-runbook-closure" in contract_ids_v1
    assert "post-h-023-secure-transport-runbook-closure" in contract_ids_v2

    closure_contract = next(
        item for item in tcr_v1["contracts"] if item["contract_id"] == "post-h-023-secure-transport-runbook-closure"
    )
    assert closure_contract["scope"] == "safety"
    assert closure_contract["critical"] is True
    assert closure_contract["mutable_global_state_allowed"] is False
    assert closure_contract["network_allowed"] is False
    assert closure_contract["external_api_allowed"] is False


def test_readme_runbook_changelog_and_validator_remain_design_only_after_closure() -> None:
    readme = read_text("README.md")
    operations_runbook = read_text("docs/05_operations/runbook.md")
    changelog = read_text("docs/release/CHANGELOG.md")

    for text in (readme, operations_runbook):
        assert "POST-H-023-E — Runbook y cierre" in text
        assert "Último hito cerrado: `POST-H-023`" in text
        assert "Siguiente hito: `POST-H-024" in text
        assert "transport_implemented=false" in text
        assert "network_used=false" in text
        assert "remote_execution_enabled=false" in text

    assert "post-h-023-e" in changelog
    assert "secure_transport_implemented=false" in changelog or "No active transport" in changelog

    validator_result = SecureTransportDesignValidator(ROOT).validate()
    assert validator_result.ok is True
    summary = validator_result.data["summary"]
    assert summary["decision_status"] == "design-only"
    assert summary["selected_for_now"] == "local-only-no-transport"
    assert summary["no_network_static_scan_passed"] is True
    assert summary["forbidden_network_primitives_total"] == 0
    assert summary["network_used"] is False
    assert summary["sockets_opened"] is False
    assert summary["certificates_generated"] is False
    assert summary["remote_execution_enabled"] is False

    gate_result = SecureTransportDesignQualityGate(ROOT).run()
    assert gate_result.ok is True
    assert gate_result.data["summary"]["quality_gate_subgate"] == "secure-transport-design-only"
    assert gate_result.data["summary"]["blocking_findings_total"] == 0
