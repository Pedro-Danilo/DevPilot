from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.schemas import SchemaRegistry, SchemaValidator
from devpilot_core.sensitive_capabilities import MultiuserAuthAdrValidator, SensitiveCapabilityAdrGate, SensitiveCapabilityOptions

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_034_d_schemas_are_registered_and_instances_validate() -> None:
    registry = SchemaRegistry(ROOT).list()
    assert registry.ok, registry.to_dict()
    schema_ids = {schema["schema_id"] for schema in registry.data["schemas"]}
    assert "SCHEMA-DEVPL-MULTIUSER-AUTH-DECISION-V1" in schema_ids
    assert "SCHEMA-DEVPL-SENSITIVE-CAPABILITY-DECISION-MATRIX-V1" in schema_ids

    checklist = SchemaValidator(ROOT).validate(
        schema="MultiuserAuthDecision",
        instance=".devpilot/sensitive_capabilities/multiuser_auth_checklist.json",
    )
    manifest = SchemaValidator(ROOT).validate(
        schema="MultiuserAuthDecision",
        instance="docs/post_h_034_d_manifest.json",
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


def test_post_h_034_d_adr_is_approved_and_does_not_enable_multiuser_auth() -> None:
    adr = (ROOT / "docs/adr/ADR-POSTH-034-D-multiuser-auth-boundary.md").read_text(encoding="utf-8")
    checklist = _read_json(".devpilot/sensitive_capabilities/multiuser_auth_checklist.json")
    matrix = _read_json(".devpilot/sensitive_capabilities/capability_decision_matrix.json")

    assert 'status: "approved"' in adr
    assert 'decision_status: "continue-blocked"' in adr
    assert 'multiuser_auth_enabled: false' in adr
    assert 'production_multiuser_enabled: false' in adr
    assert 'iam_enterprise_enabled: false' in adr
    assert 'session_management_enabled: false' in adr
    assert 'tenancy_enabled: false' in adr
    assert 'public_api_enabled: false' in adr
    assert 'network_allowed: false' in adr
    assert "local api token exists != production multiuser enabled" in adr.lower()
    assert checklist["decision_state"] == "continue-blocked"
    assert checklist["local_api_token_control"] is True
    assert checklist["local_rbac_initial"] is True
    assert checklist["local_approval_binding_initial"] is True
    assert checklist["multiuser_auth_enabled"] is False
    assert checklist["production_multiuser_enabled"] is False
    assert checklist["multiuser_runtime_enabled"] is False
    assert checklist["iam_enterprise_enabled"] is False
    assert checklist["session_management_enabled"] is False
    assert checklist["tenancy_enabled"] is False
    assert checklist["public_api_enabled"] is False
    assert checklist["network_allowed"] is False
    assert checklist["external_api_allowed"] is False
    assert checklist["credentials_required"] is False
    assert checklist["requires_future_enablement_adr"] is True
    assert matrix["global_no_go_gates"]["production_multiuser"] is False
    multiuser = next(item for item in matrix["capabilities"] if item["capability_id"] == "multiuser.auth")
    assert multiuser["decision_state"] == "continue-blocked"
    assert multiuser["runtime_enabled"] is False


def test_post_h_034_d_sensitive_capability_gate_passes_with_multiuser_blocked() -> None:
    result = SensitiveCapabilityAdrGate(ROOT).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["connector_write_gate_ok"] is True
    assert summary["plugin_execution_gate_ok"] is True
    assert summary["remote_execution_adr3_gate_ok"] is True
    assert summary["multiuser_auth_gate_ok"] is True
    assert summary["multiuser_decision_state"] == "continue-blocked"
    assert summary["multiuser_auth_enabled"] is False
    assert summary["production_multiuser_enabled"] is False
    assert summary["iam_enterprise_enabled"] is False
    assert summary["session_management_enabled"] is False
    assert summary["tenancy_enabled"] is False
    assert summary["public_api_enabled"] is False
    assert summary["blocking_findings_total"] == 0
    assert any(finding.id == "MULTIUSER_AUTH_ADR_GATE_PASS" for finding in result.findings)


def test_post_h_034_d_gate_blocks_bad_multiuser_enablement(tmp_path: Path) -> None:
    checklist = _read_json(".devpilot/sensitive_capabilities/multiuser_auth_checklist.json")
    bad = copy.deepcopy(checklist)
    bad["multiuser_auth_enabled"] = True
    bad["production_multiuser_enabled"] = True
    bad["decision_state"] = "approved-for-future-implementation"
    bad_path = tmp_path / "bad_multiuser_auth_checklist.json"
    bad_path.write_text(json.dumps(bad, indent=2), encoding="utf-8")

    result = MultiuserAuthAdrValidator(
        ROOT,
        options=SensitiveCapabilityOptions(multiuser_auth_checklist_path=bad_path),
    ).validate()

    assert not result.ok
    finding_ids = {finding.id for finding in result.findings}
    assert "MULTIUSER_AUTH_DECISION_FLAG_BLOCK" in finding_ids or "MULTIUSER_AUTH_DECISION_SCHEMA_BLOCK" in finding_ids
    assert "MULTIUSER_AUTH_NOT_CONTINUE_BLOCKED" in finding_ids


def test_post_h_034_d_local_identity_rbac_and_api_security_remain_local_only() -> None:
    identity = _read_json(".devpilot/identity/identity_registry.json")
    api_report = (ROOT / "docs/audits/post_h_028_b_local_auth_cors_hardening_report.md").read_text(encoding="utf-8").lower()

    assert identity["defaults"]["auth_remote_enabled"] is False
    assert identity["defaults"]["credentials_stored"] is False
    assert identity["defaults"]["deny_unknown_actor"] is True
    assert identity["defaults"]["rbac_enforced_for_sensitive_actions"] is True
    assert identity["security"]["network_used"] is False
    assert identity["security"]["external_api_used"] is False
    assert identity["security"]["remote_auth_used"] is False
    assert identity["security"]["credentials_stored"] is False
    assert all(actor["credentials_stored"] is False for actor in identity["actors"])
    assert all(actor["remote_auth_enabled"] is False for actor in identity["actors"])
    assert "no es iam enterprise" in api_report or "no es iam" in api_report
    assert "login multiusuario" in api_report


def test_post_h_034_d_project_state_and_claims_remain_blocked() -> None:
    state = _read_json(".devpilot/project_state.json")

    assert state["post_h_034_current_micro_sprint"] == "POST-H-034-D"
    assert state["post_h_034_next_micro_sprint"] == "POST-H-034-E"
    assert state["post_h_034_c_closed"] is True
    assert state["post_h_034_d_decision_state"] == "continue-blocked"
    assert state["post_h_034_d_multiuser_auth_enabled"] is False
    assert state["post_h_034_d_production_multiuser_enabled"] is False
    assert state["post_h_034_d_multiuser_runtime_enabled"] is False
    assert state["post_h_034_d_iam_enterprise_enabled"] is False
    assert state["post_h_034_d_session_management_enabled"] is False
    assert state["post_h_034_d_tenancy_enabled"] is False
    assert state["post_h_034_d_public_api_enabled"] is False
    assert state["post_h_034_d_network_allowed"] is False
    assert state["post_h_034_d_credentials_required"] is False
    assert state["production_multiuser"] is False
    assert state["multiuser_auth_enabled"] is False
    assert state["public_api_enabled"] is False
    assert state["network_allowed"] is False
    assert state["connector_write_enabled"] is False
    assert state["plugin_execution_enabled"] is False
    assert state["remote_execution_enabled"] is False
    assert state["enterprise_ready_claimed"] is False
    assert state["compliance_certification_claim"] is False
    assert state["post_h_034_d_claims_changed"] is False


def test_post_h_034_d_governance_artifacts_are_synchronized() -> None:
    source_registry = (ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-034_sensitive_capabilities_adrs.md").read_text(encoding="utf-8")

    assert "ADR-POSTH-034-D" in source_registry
    assert "POST-H-034-D-MULTIUSER-AUTH-CHECKLIST" in source_registry
    assert "POST-H-034-D-MULTIUSER-AUTH-SCHEMA" in source_registry
    assert "post-h-034-multiuser-auth-adr" in tcr_v1
    assert "post-h-034-multiuser-auth-adr" in tcr_v2
    assert "POST-H-034-D — Multiuser/auth ADR" in readme
    assert "POST-H-034-D — Operación de ADR multiuser/auth" in runbook
    assert "post-h-034-d" in changelog
    assert 'current_micro_sprint: "POST-H-034-D"' in backlog
    assert 'next_micro_sprint: "POST-H-034-E"' in backlog


def test_post_h_034_d_no_real_credentials_network_or_enablement_terms_are_versioned() -> None:
    watched_paths = [
        "docs/adr/ADR-POSTH-034-D-multiuser-auth-boundary.md",
        ".devpilot/sensitive_capabilities/multiuser_auth_checklist.json",
        ".devpilot/sensitive_capabilities/capability_decision_matrix.json",
        "docs/audits/post_h_034_d_multiuser_auth_adr_report.md",
        "docs/post_h_034_d_manifest.json",
    ]
    combined = "\n".join((ROOT / path).read_text(encoding="utf-8").lower() for path in watched_paths)

    forbidden = [
        "api_key=",
        "authorization: bearer",
        "private_key",
        "production-enabled",
        "multiuser-ready=true",
        "enterprise-auth-ready=true",
    ]
    assert all(term not in combined for term in forbidden)
