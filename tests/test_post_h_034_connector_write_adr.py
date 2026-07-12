from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.connectors import ConnectorSandboxPolicyValidator
from devpilot_core.schemas import SchemaRegistry, SchemaValidator
from devpilot_core.sensitive_capabilities import ConnectorWriteAdrValidator, SensitiveCapabilityAdrGate, SensitiveCapabilityOptions

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_034_a_schemas_are_registered_and_instances_validate() -> None:
    registry = SchemaRegistry(ROOT).list()
    assert registry.ok, registry.to_dict()
    schema_ids = {schema["schema_id"] for schema in registry.data["schemas"]}
    assert "SCHEMA-DEVPL-CONNECTOR-WRITE-DECISION-V1" in schema_ids
    assert "SCHEMA-DEVPL-SENSITIVE-CAPABILITY-DECISION-MATRIX-V1" in schema_ids

    checklist = SchemaValidator(ROOT).validate(
        schema="ConnectorWriteDecision",
        instance=".devpilot/sensitive_capabilities/connector_write_enablement_checklist.json",
    )
    matrix = SchemaValidator(ROOT).validate(
        schema="SensitiveCapabilityDecisionMatrix",
        instance=".devpilot/sensitive_capabilities/capability_decision_matrix.json",
    )
    manifest = SchemaValidator(ROOT).validate(
        schema="ConnectorWriteDecision",
        instance="docs/post_h_034_a_manifest.json",
    )

    assert checklist.ok, checklist.to_dict()
    assert matrix.ok, matrix.to_dict()
    assert manifest.ok, manifest.to_dict()
    assert checklist.data["summary"]["valid"] is True
    assert matrix.data["summary"]["valid"] is True
    assert manifest.data["summary"]["valid"] is True


def test_post_h_034_a_adr_is_approved_and_does_not_enable_connector_write() -> None:
    adr = (ROOT / "docs/adr/ADR-POSTH-034-A-connector-write-enable-or-continue-blocked.md").read_text(encoding="utf-8")
    checklist = _read_json(".devpilot/sensitive_capabilities/connector_write_enablement_checklist.json")
    matrix = _read_json(".devpilot/sensitive_capabilities/capability_decision_matrix.json")

    assert 'status: "approved"' in adr
    assert 'decision_status: "continue-blocked"' in adr
    assert 'connector_write_enabled: false' in adr
    assert 'runtime_write_enabled: false' in adr
    assert "enabled-now" not in adr.lower()
    assert checklist["decision_state"] == "continue-blocked"
    assert checklist["connector_write_enabled"] is False
    assert checklist["runtime_write_enabled"] is False
    assert checklist["network_allowed"] is False
    assert checklist["external_api_allowed"] is False
    assert checklist["credentials_required"] is False
    assert checklist["requires_future_enablement_adr"] is True
    assert matrix["global_no_go_gates"]["connector_write_enabled"] is False
    assert all(capability["runtime_enabled"] is False for capability in matrix["capabilities"])


def test_post_h_034_a_sensitive_capability_gate_passes_with_connector_write_blocked() -> None:
    result = SensitiveCapabilityAdrGate(ROOT).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["decision_state"] == "continue-blocked"
    assert summary["connector_write_enabled"] is False
    assert summary["runtime_write_enabled"] is False
    assert summary["sandbox_policy_connector_write_enabled"] is False
    assert summary["project_state_connector_write_enabled"] is False
    assert summary["blocking_findings_total"] == 0
    assert any(finding.id == "CONNECTOR_WRITE_ADR_GATE_PASS" for finding in result.findings)


def test_post_h_034_a_gate_blocks_bad_connector_write_enablement(tmp_path: Path) -> None:
    checklist = _read_json(".devpilot/sensitive_capabilities/connector_write_enablement_checklist.json")
    bad = copy.deepcopy(checklist)
    bad["connector_write_enabled"] = True
    bad["runtime_write_enabled"] = True
    bad["decision_state"] = "approved-for-future-implementation"
    bad_path = tmp_path / "bad_connector_write_enablement_checklist.json"
    bad_path.write_text(json.dumps(bad, indent=2), encoding="utf-8")

    result = ConnectorWriteAdrValidator(
        ROOT,
        options=SensitiveCapabilityOptions(connector_write_checklist_path=bad_path),
    ).validate()

    assert not result.ok
    finding_ids = {finding.id for finding in result.findings}
    assert "CONNECTOR_WRITE_DECISION_FLAG_BLOCK" in finding_ids or "CONNECTOR_WRITE_DECISION_SCHEMA_BLOCK" in finding_ids
    assert "CONNECTOR_WRITE_DECISION_NOT_CONTINUE_BLOCKED" in finding_ids


def test_post_h_034_a_connector_sandbox_policy_still_denies_write() -> None:
    result = ConnectorSandboxPolicyValidator(ROOT).validate()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["default_mode"] == "deny-write"
    assert summary["connector_write_enabled"] is False
    assert summary["connector_write_used"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert all(connector["write_allowed"] is False for connector in result.data["policy"]["connectors"])


def test_post_h_034_a_project_state_and_claims_remain_blocked() -> None:
    state = _read_json(".devpilot/project_state.json")

    assert state["post_h_034_backlog_approved"] is True
    assert state["post_h_034_current_micro_sprint"] == "POST-H-034-A"
    assert state["post_h_034_next_micro_sprint"] == "POST-H-034-B"
    assert state["post_h_034_a_decision_state"] == "continue-blocked"
    assert state["post_h_034_a_connector_write_enabled"] is False
    assert state["post_h_034_a_runtime_write_enabled"] is False
    assert state["connector_write_enabled"] is False
    assert state["plugin_execution_enabled"] is False
    assert state["remote_execution_enabled"] is False
    assert state["enterprise_ready_claimed"] is False
    assert state["compliance_certification_claim"] is False
    assert state["post_h_034_a_claims_changed"] is False


def test_post_h_034_a_governance_artifacts_are_synchronized() -> None:
    source_registry = (ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-034_sensitive_capabilities_adrs.md").read_text(encoding="utf-8")
    top_level = (ROOT / "docs/POST-H-034_sensitive_capabilities_adrs.md").read_text(encoding="utf-8")

    assert "ADR-POSTH-034-A" in source_registry
    assert "POST-H-034-A-CONNECTOR-WRITE-CHECKLIST" in source_registry
    assert "POST-H-034-A-SENSITIVE-CAPABILITY-MATRIX" in source_registry
    assert "post-h-034-connector-write-adr" in tcr_v1
    assert "post-h-034-connector-write-adr" in tcr_v2
    assert "POST-H-034-A — Connector write ADR" in readme
    assert "POST-H-034-A — Operación de ADR connector write" in runbook
    assert "post-h-034-a" in changelog
    assert 'status: "approved"' in backlog
    assert 'current_micro_sprint: "POST-H-034-A"' in backlog
    assert 'status: "approved"' in top_level


def test_post_h_034_a_no_real_credentials_or_enablement_terms_are_versioned() -> None:
    watched_paths = [
        "docs/adr/ADR-POSTH-034-A-connector-write-enable-or-continue-blocked.md",
        ".devpilot/sensitive_capabilities/connector_write_enablement_checklist.json",
        ".devpilot/sensitive_capabilities/capability_decision_matrix.json",
        "docs/audits/post_h_034_a_connector_write_adr_report.md",
        "docs/post_h_034_a_manifest.json",
    ]
    combined = "\n".join((ROOT / path).read_text(encoding="utf-8").lower() for path in watched_paths)

    forbidden = [
        "api_key=",
        "authorization: bearer",
        "private_key",
        "connector_write_enabled=true",
        "runtime_write_enabled=true",
        "production-enabled",
        "enabled-now",
    ]
    assert all(term not in combined for term in forbidden)
