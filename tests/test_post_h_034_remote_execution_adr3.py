from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.remote import RemoteReadinessQualityGate, RemoteRunnerRegistry, RemoteRunnerStub
from devpilot_core.schemas import SchemaRegistry, SchemaValidator
from devpilot_core.sensitive_capabilities import RemoteExecutionAdr3Validator, SensitiveCapabilityAdrGate, SensitiveCapabilityOptions

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_034_c_schemas_are_registered_and_instances_validate() -> None:
    registry = SchemaRegistry(ROOT).list()
    assert registry.ok, registry.to_dict()
    schema_ids = {schema["schema_id"] for schema in registry.data["schemas"]}
    assert "SCHEMA-DEVPL-REMOTE-EXECUTION-ADR3-DECISION-V1" in schema_ids
    assert "SCHEMA-DEVPL-SENSITIVE-CAPABILITY-DECISION-MATRIX-V1" in schema_ids

    checklist = SchemaValidator(ROOT).validate(
        schema="RemoteExecutionAdr3Decision",
        instance=".devpilot/sensitive_capabilities/remote_execution_adr3_checklist.json",
    )
    matrix = SchemaValidator(ROOT).validate(
        schema="SensitiveCapabilityDecisionMatrix",
        instance=".devpilot/sensitive_capabilities/capability_decision_matrix.json",
    )
    manifest = SchemaValidator(ROOT).validate(
        schema="RemoteExecutionAdr3Decision",
        instance="docs/post_h_034_c_manifest.json",
    )

    assert checklist.ok, checklist.to_dict()
    assert matrix.ok, matrix.to_dict()
    assert manifest.ok, manifest.to_dict()
    assert checklist.data["summary"]["valid"] is True
    assert matrix.data["summary"]["valid"] is True
    assert manifest.data["summary"]["valid"] is True


def test_post_h_034_c_adr_is_approved_and_does_not_enable_remote_execution() -> None:
    adr = (ROOT / "docs/adr/ADR-POSTH-034-C-remote-execution-adr3.md").read_text(encoding="utf-8")
    checklist = _read_json(".devpilot/sensitive_capabilities/remote_execution_adr3_checklist.json")
    matrix = _read_json(".devpilot/sensitive_capabilities/capability_decision_matrix.json")

    assert 'status: "approved"' in adr
    assert 'decision_status: "continue-blocked"' in adr
    assert 'remote_execution_enabled: false' in adr
    assert 'remote_runner_enabled: false' in adr
    assert 'network_allowed: false' in adr
    assert 'shell_allowed: false' in adr
    assert "enable-now" in adr.lower()
    assert checklist["decision_state"] == "continue-blocked"
    assert checklist["remote_execution_enabled"] is False
    assert checklist["remote_runner_enabled"] is False
    assert checklist["runtime_execution_enabled"] is False
    assert checklist["remote_transport_enabled"] is False
    assert checklist["secure_transport_implemented"] is False
    assert checklist["transport_implemented"] is False
    assert checklist["shell_allowed"] is False
    assert checklist["arbitrary_command_execution_allowed"] is False
    assert checklist["network_allowed"] is False
    assert checklist["external_api_allowed"] is False
    assert checklist["credentials_required"] is False
    assert checklist["requires_future_enablement_adr"] is True
    assert matrix["global_no_go_gates"]["remote_execution_enabled"] is False
    remote_capability = next(item for item in matrix["capabilities"] if item["capability_id"] == "remote.execution")
    assert remote_capability["decision_state"] == "continue-blocked"
    assert remote_capability["runtime_enabled"] is False


def test_post_h_034_c_sensitive_capability_gate_passes_with_remote_execution_blocked() -> None:
    result = SensitiveCapabilityAdrGate(ROOT).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["connector_write_gate_ok"] is True
    assert summary["plugin_execution_gate_ok"] is True
    assert summary["remote_execution_adr3_gate_ok"] is True
    assert summary["remote_decision_state"] == "continue-blocked"
    assert summary["remote_execution_enabled"] is False
    assert summary["remote_runner_enabled"] is False
    assert summary["remote_transport_enabled"] is False
    assert summary["secure_transport_implemented"] is False
    assert summary["project_state_remote_execution_enabled"] is False
    assert summary["blocking_findings_total"] == 0
    assert any(finding.id == "REMOTE_EXECUTION_ADR3_GATE_PASS" for finding in result.findings)


def test_post_h_034_c_gate_blocks_bad_remote_execution_enablement(tmp_path: Path) -> None:
    checklist = _read_json(".devpilot/sensitive_capabilities/remote_execution_adr3_checklist.json")
    bad = copy.deepcopy(checklist)
    bad["remote_execution_enabled"] = True
    bad["remote_runner_enabled"] = True
    bad["decision_state"] = "approved-for-future-implementation"
    bad_path = tmp_path / "bad_remote_execution_adr3_checklist.json"
    bad_path.write_text(json.dumps(bad, indent=2), encoding="utf-8")

    result = RemoteExecutionAdr3Validator(
        ROOT,
        options=SensitiveCapabilityOptions(remote_execution_adr3_checklist_path=bad_path),
    ).validate()

    assert not result.ok
    finding_ids = {finding.id for finding in result.findings}
    assert "REMOTE_EXECUTION_ADR3_DECISION_FLAG_BLOCK" in finding_ids or "REMOTE_EXECUTION_ADR3_DECISION_SCHEMA_BLOCK" in finding_ids
    assert "REMOTE_EXECUTION_ADR3_NOT_CONTINUE_BLOCKED" in finding_ids


def test_post_h_034_c_remote_runner_and_secure_transport_still_design_only() -> None:
    runner_registry = _read_json(".devpilot/remote/runner_registry.json")
    readiness = _read_json(".devpilot/remote/remote_readiness_criteria.json")
    transport = _read_json(".devpilot/remote/secure_transport_protocol_decision_matrix.json")

    registry_result = RemoteRunnerRegistry(ROOT).validate()
    quality_result = RemoteReadinessQualityGate(ROOT).run()
    stub_result = RemoteRunnerStub(ROOT).execute(runner_id="experimental-disabled", command="status")

    assert registry_result.ok, registry_result.to_dict()
    assert quality_result.ok, quality_result.to_dict()
    assert not stub_result.ok
    assert stub_result.exit_code == ExitCode.BLOCK
    assert runner_registry["security"]["remote_runner_enabled"] is False
    assert runner_registry["security"]["execution_allowed"] is False
    assert runner_registry["security"]["network_used"] is False
    assert runner_registry["security"]["shell_allowed"] is False
    assert readiness["decision_status"] == "design-only"
    assert readiness["remote_execution_allowed"] is False
    assert readiness["remote_runner_enabled"] is False
    assert transport["decision_status"] == "design-only"
    assert transport["selected_for_now"] == "local-only-no-transport"
    assert transport["transport_implemented"] is False
    assert transport["network_allowed"] is False
    assert transport["remote_execution_enabled"] is False


def test_post_h_034_c_project_state_and_claims_remain_blocked() -> None:
    state = _read_json(".devpilot/project_state.json")

    assert state["post_h_034_current_micro_sprint"] in {"POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE"}
    assert state["post_h_034_next_micro_sprint"] in {"POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE"}
    assert state["post_h_034_b_closed"] is True
    assert state["post_h_034_c_decision_state"] == "continue-blocked"
    assert state["post_h_034_c_remote_execution_enabled"] is False
    assert state["post_h_034_c_remote_runner_enabled"] is False
    assert state["post_h_034_c_remote_transport_enabled"] is False
    assert state["post_h_034_c_secure_transport_implemented"] is False
    assert state["post_h_034_c_shell_allowed"] is False
    assert state["post_h_034_c_network_allowed"] is False
    assert state["post_h_034_c_credentials_required"] is False
    assert state["remote_execution_enabled"] is False
    assert state["remote_runner_enabled"] is False
    assert state["network_allowed"] is False
    assert state["plugin_execution_enabled"] is False
    assert state["connector_write_enabled"] is False
    assert state["enterprise_ready_claimed"] is False
    assert state["compliance_certification_claim"] is False
    assert state["post_h_034_c_claims_changed"] is False


def test_post_h_034_c_governance_artifacts_are_synchronized() -> None:
    source_registry = (ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    remote_runbook = (ROOT / "docs/05_operations/remote_runner_design_runbook.md").read_text(encoding="utf-8")
    transport_runbook = (ROOT / "docs/05_operations/secure_transport_design_runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-034_sensitive_capabilities_adrs.md").read_text(encoding="utf-8")

    assert "ADR-POSTH-034-C" in source_registry
    assert "POST-H-034-C-REMOTE-EXECUTION-ADR3-CHECKLIST" in source_registry
    assert "POST-H-034-C-REMOTE-EXECUTION-ADR3-SCHEMA" in source_registry
    assert "post-h-034-remote-execution-adr3" in tcr_v1
    assert "post-h-034-remote-execution-adr3" in tcr_v2
    assert "POST-H-034-C — Remote execution ADR-3" in readme
    assert "POST-H-034-C — Operación de ADR remote execution" in runbook
    assert "POST-H-034-C — Remote execution sigue bloqueado" in remote_runbook
    assert "POST-H-034-C — Secure transport no habilita remote execution" in transport_runbook
    assert "post-h-034-c" in changelog
    assert any(marker in backlog for marker in [
        'current_micro_sprint: "POST-H-034-D"',
        'current_micro_sprint: "POST-H-034-E"',
        'current_micro_sprint: "POST-H-034-CLOSURE"',
    ])
    assert 'next_micro_sprint: "POST-H-034-E"' in backlog or 'next_micro_sprint: "POST-H-034-CLOSURE"' in backlog


def test_post_h_034_c_no_real_credentials_network_or_enablement_terms_are_versioned() -> None:
    watched_paths = [
        "docs/adr/ADR-POSTH-034-C-remote-execution-adr3.md",
        ".devpilot/sensitive_capabilities/remote_execution_adr3_checklist.json",
        ".devpilot/sensitive_capabilities/capability_decision_matrix.json",
        "docs/audits/post_h_034_c_remote_execution_adr3_report.md",
        "docs/post_h_034_c_manifest.json",
    ]
    combined = "\n".join((ROOT / path).read_text(encoding="utf-8").lower() for path in watched_paths)

    forbidden = [
        "api_key=",
        "authorization: bearer",
        "private_key",
        "production-enabled",
        "remote-ready=true",
    ]
    assert all(term not in combined for term in forbidden)
