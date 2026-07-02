from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core.quality.gate import QualityGate, QualityGateOptions
from devpilot_core.remote import SecureTransportDesignQualityGate, SecureTransportDesignValidationOptions, SecureTransportDesignValidator


ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_secure_transport_validator_passes_design_only_no_network_contract() -> None:
    result = SecureTransportDesignValidator(ROOT).validate()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["validator_status"] == "design-only-validator"
    assert summary["decision_status"] == "design-only"
    assert summary["selected_for_now"] == "local-only-no-transport"
    assert summary["lifecycle_status"] == "design-only-no-material"
    assert summary["schema_validations_total"] == 3
    assert summary["schema_validations_passed"] == 3
    assert summary["report_schema_valid"] is True
    assert summary["no_network_static_scan_passed"] is True
    assert summary["forbidden_network_primitives_total"] == 0
    assert summary["read_only"] is True
    assert summary["dry_run"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["sockets_opened"] is False
    assert summary["transport_implemented"] is False
    assert summary["secure_transport_implemented"] is False
    assert summary["certificates_generated"] is False
    assert summary["raw_secret_storage_allowed"] is False
    assert summary["secrets_required"] is False
    assert summary["secrets_stored"] is False
    assert summary["secrets_read"] is False
    assert summary["remote_execution_enabled"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["plugin_execution_enabled"] is False

    report = result.data["report"]
    assert report["schema_id"] == "SCHEMA-DEVPL-SECURE-TRANSPORT-VALIDATION-REPORT-V1"
    assert report["ok"] is True
    assert report["no_network_static_scan"]["ok"] is True
    assert "src/devpilot_core/remote/transport_design.py" in report["no_network_static_scan"]["scanned_files"]


def test_secure_transport_quality_gate_is_registered_in_hardening_profiles() -> None:
    result = SecureTransportDesignQualityGate(ROOT).run()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["quality_gate_subgate"] == "secure-transport-design-only"
    assert summary["validator_ok"] is True
    assert summary["report_schema_valid"] is True
    assert summary["no_network_static_scan_passed"] is True
    assert summary["network_used"] is False
    assert summary["sockets_opened"] is False

    hardening_subgates = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))._subgates()
    subgate_ids = [subgate.id for subgate in hardening_subgates]
    assert "secure-transport-design-only" in subgate_ids
    assert subgate_ids.index("enterprise-threat-model-design-only") < subgate_ids.index("secure-transport-design-only")


def test_secure_transport_validation_report_schema_is_registered_and_exports_are_available() -> None:
    catalog = read_json("docs/schemas/schema_catalog.json")
    state = read_json(".devpilot/project_state.json")
    manifest = read_json("docs/post_h_023_d_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    assert any(
        item["schema_id"] == "SCHEMA-DEVPL-SECURE-TRANSPORT-VALIDATION-REPORT-V1"
        and item["path"] == "docs/schemas/secure_transport_validation_report.schema.json"
        for item in catalog["schemas"]
    )

    assert state["post_h_023_current_micro_sprint"] == "POST-H-023-E"
    assert state["current_micro_sprint"] == "POST-H-024-B"
    assert state["post_h_023_next_micro_sprint"] == "POST-H-024"
    assert state["post_h_023_secure_transport_validation_report_schema_registered"] is True
    assert state["post_h_023_secure_transport_validator_available"] is True
    assert state["post_h_023_secure_transport_quality_gate_subgate"] == "secure-transport-design-only"
    assert state["post_h_023_no_network_invariant_available"] is True

    assert manifest["micro_sprint"] == "POST-H-023-D"
    assert manifest["validator_status"] == "design-only-validator"
    assert manifest["quality_gate_subgate"] == "secure-transport-design-only"
    assert manifest["network_used"] is False
    assert "src/devpilot_core/remote/transport_design.py" in manifest["created_files"]

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "SCHEMA-DEVPL-SECURE-TRANSPORT-VALIDATION-REPORT-V1" in doc_ids
    assert "POST-H-023-D-TRANSPORT-DESIGN-VALIDATOR-MODULE" in doc_ids
    assert "POST-H-023-D-TRANSPORT-DESIGN-VALIDATOR-REPORT" in doc_ids
    assert "POST-H-023-D-MANIFEST" in doc_ids
    assert "POST-H-023-D-TRANSPORT-DESIGN-VALIDATOR-TEST" in doc_ids
    assert "POST-H-023-D-NO-NETWORK-INVARIANT-TEST" in doc_ids

    assert "post-h-023-secure-transport-design-validator" in {item["contract_id"] for item in tcr_v1["contracts"]}
    assert "post-h-023-secure-transport-design-validator" in {item["contract_id"] for item in tcr_v2["contracts"]}


def test_secure_transport_validator_blocks_unsafe_artifact_flag(tmp_path: Path) -> None:
    unsafe_lifecycle = tmp_path / "secure_transport_key_lifecycle.json"
    shutil.copyfile(ROOT / ".devpilot/remote/secure_transport_key_lifecycle.json", unsafe_lifecycle)
    payload = json.loads(unsafe_lifecycle.read_text(encoding="utf-8"))
    payload["network_allowed"] = True
    payload["no_go_gates"]["network_allowed"] = True
    unsafe_lifecycle.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    options = SecureTransportDesignValidationOptions(
        requirements_path=str(ROOT / ".devpilot/remote/secure_transport_requirements.json"),
        requirements_schema_path=str(ROOT / "docs/schemas/secure_transport_requirements.schema.json"),
        protocol_matrix_path=str(ROOT / ".devpilot/remote/secure_transport_protocol_decision_matrix.json"),
        protocol_matrix_schema_path=str(ROOT / "docs/schemas/secure_transport_design.schema.json"),
        key_lifecycle_path=str(unsafe_lifecycle),
        key_lifecycle_schema_path=str(ROOT / "docs/schemas/secure_transport_key_lifecycle.schema.json"),
        validation_report_schema_path=str(ROOT / "docs/schemas/secure_transport_validation_report.schema.json"),
        static_scan_roots=(str(ROOT / "src/devpilot_core/remote"),),
    )

    result = SecureTransportDesignValidator(ROOT, options=options).validate()

    assert result.ok is False
    finding_ids = {finding.id for finding in result.findings}
    assert "SECURE_TRANSPORT_UNSAFE_FLAG_BLOCKED" in finding_ids or "SCHEMA_VALIDATION_FAILED" in finding_ids
