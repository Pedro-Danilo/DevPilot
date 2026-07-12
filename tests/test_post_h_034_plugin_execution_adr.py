from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.plugins import PluginPermissionModel, PluginRegistry
from devpilot_core.schemas import SchemaRegistry, SchemaValidator
from devpilot_core.sensitive_capabilities import PluginExecutionAdrValidator, SensitiveCapabilityAdrGate, SensitiveCapabilityOptions

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_034_b_schemas_are_registered_and_instances_validate() -> None:
    registry = SchemaRegistry(ROOT).list()
    assert registry.ok, registry.to_dict()
    schema_ids = {schema["schema_id"] for schema in registry.data["schemas"]}
    assert "SCHEMA-DEVPL-PLUGIN-EXECUTION-DECISION-V1" in schema_ids
    assert "SCHEMA-DEVPL-SENSITIVE-CAPABILITY-DECISION-MATRIX-V1" in schema_ids

    checklist = SchemaValidator(ROOT).validate(
        schema="PluginExecutionDecision",
        instance=".devpilot/sensitive_capabilities/plugin_execution_enablement_checklist.json",
    )
    matrix = SchemaValidator(ROOT).validate(
        schema="SensitiveCapabilityDecisionMatrix",
        instance=".devpilot/sensitive_capabilities/capability_decision_matrix.json",
    )
    manifest = SchemaValidator(ROOT).validate(
        schema="PluginExecutionDecision",
        instance="docs/post_h_034_b_manifest.json",
    )

    assert checklist.ok, checklist.to_dict()
    assert matrix.ok, matrix.to_dict()
    assert manifest.ok, manifest.to_dict()
    assert checklist.data["summary"]["valid"] is True
    assert matrix.data["summary"]["valid"] is True
    assert manifest.data["summary"]["valid"] is True


def test_post_h_034_b_adr_is_approved_and_does_not_enable_plugin_execution() -> None:
    adr = (ROOT / "docs/adr/ADR-POSTH-034-B-plugin-execution-enable-or-continue-blocked.md").read_text(encoding="utf-8")
    checklist = _read_json(".devpilot/sensitive_capabilities/plugin_execution_enablement_checklist.json")
    matrix = _read_json(".devpilot/sensitive_capabilities/capability_decision_matrix.json")

    assert 'status: "approved"' in adr
    assert 'decision_status: "continue-blocked"' in adr
    assert 'plugin_execution_enabled: false' in adr
    assert 'plugin_code_loading_enabled: false' in adr
    assert 'dynamic_import_allowed: false' in adr
    assert "enabled-now" not in adr.lower()
    assert checklist["decision_state"] == "continue-blocked"
    assert checklist["plugin_execution_enabled"] is False
    assert checklist["runtime_execution_enabled"] is False
    assert checklist["plugin_code_loading_enabled"] is False
    assert checklist["dynamic_import_allowed"] is False
    assert checklist["subprocess_allowed"] is False
    assert checklist["network_allowed"] is False
    assert checklist["external_api_allowed"] is False
    assert checklist["filesystem_write_allowed"] is False
    assert checklist["credentials_required"] is False
    assert checklist["requires_future_enablement_adr"] is True
    assert matrix["global_no_go_gates"]["plugin_execution_enabled"] is False
    plugin_capability = next(item for item in matrix["capabilities"] if item["capability_id"] == "plugin.execution")
    assert plugin_capability["decision_state"] == "continue-blocked"
    assert plugin_capability["runtime_enabled"] is False


def test_post_h_034_b_sensitive_capability_gate_passes_with_plugin_execution_blocked() -> None:
    result = SensitiveCapabilityAdrGate(ROOT).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["connector_write_gate_ok"] is True
    assert summary["plugin_execution_gate_ok"] is True
    assert summary["plugin_decision_state"] == "continue-blocked"
    assert summary["plugin_execution_enabled"] is False
    assert summary["runtime_execution_enabled"] is False
    assert summary["plugin_code_loading_enabled"] is False
    assert summary["project_state_plugin_execution_enabled"] is False
    assert summary["blocking_findings_total"] == 0
    assert any(finding.id == "PLUGIN_EXECUTION_ADR_GATE_PASS" for finding in result.findings)


def test_post_h_034_b_gate_blocks_bad_plugin_execution_enablement(tmp_path: Path) -> None:
    checklist = _read_json(".devpilot/sensitive_capabilities/plugin_execution_enablement_checklist.json")
    bad = copy.deepcopy(checklist)
    bad["plugin_execution_enabled"] = True
    bad["runtime_execution_enabled"] = True
    bad["decision_state"] = "approved-for-future-implementation"
    bad_path = tmp_path / "bad_plugin_execution_enablement_checklist.json"
    bad_path.write_text(json.dumps(bad, indent=2), encoding="utf-8")

    result = PluginExecutionAdrValidator(
        ROOT,
        options=SensitiveCapabilityOptions(plugin_execution_checklist_path=bad_path),
    ).validate()

    assert not result.ok
    finding_ids = {finding.id for finding in result.findings}
    assert "PLUGIN_EXECUTION_DECISION_FLAG_BLOCK" in finding_ids or "PLUGIN_EXECUTION_DECISION_SCHEMA_BLOCK" in finding_ids
    assert "PLUGIN_EXECUTION_DECISION_NOT_CONTINUE_BLOCKED" in finding_ids


def test_post_h_034_b_plugin_registry_and_permission_model_still_deny_execution() -> None:
    registry_result = PluginRegistry(ROOT).validate()
    permission_result = PluginPermissionModel(ROOT).validate()
    registry = _read_json(".devpilot/plugins/plugin_registry.json")
    permission_model = _read_json(".devpilot/plugins/plugin_permission_model.json")

    assert registry_result.ok, registry_result.to_dict()
    assert permission_result.ok, permission_result.to_dict()
    assert registry["defaults"]["executable_loading_default"] is False
    assert registry["security"]["plugin_code_loaded"] is False
    assert registry["security"]["arbitrary_code_execution_performed"] is False
    assert registry["security"]["dynamic_import_allowed"] is False
    assert registry["security"]["subprocess_allowed"] is False
    assert all(plugin["loading_mode"] == "metadata-only" for plugin in registry["plugins"])
    assert all(plugin["execution_enabled"] is False for plugin in registry["plugins"])
    assert permission_model["default_effect"] == "deny"
    assert permission_model["plugin_execution_allowed"] is False
    assert permission_model["dynamic_import_allowed"] is False
    assert permission_model["subprocess_allowed"] is False
    denied = {p["permission_id"]: p for p in permission_model["permissions"] if p.get("effect") == "deny"}
    assert "plugin.code.execute" in denied
    assert "plugin.dynamic_import" in denied
    assert "plugin.subprocess.run" in denied


def test_post_h_034_b_project_state_and_claims_remain_blocked() -> None:
    state = _read_json(".devpilot/project_state.json")

    assert state["post_h_034_backlog_approved"] is True
    assert state["post_h_034_current_micro_sprint"] == "POST-H-034-B"
    assert state["post_h_034_next_micro_sprint"] == "POST-H-034-C"
    assert state["post_h_034_a_closed"] is True
    assert state["post_h_034_b_decision_state"] == "continue-blocked"
    assert state["post_h_034_b_plugin_execution_enabled"] is False
    assert state["post_h_034_b_runtime_execution_enabled"] is False
    assert state["post_h_034_b_dynamic_import_allowed"] is False
    assert state["post_h_034_b_subprocess_allowed"] is False
    assert state["plugin_execution_enabled"] is False
    assert state["connector_write_enabled"] is False
    assert state["remote_execution_enabled"] is False
    assert state["enterprise_ready_claimed"] is False
    assert state["compliance_certification_claim"] is False
    assert state["post_h_034_b_claims_changed"] is False


def test_post_h_034_b_governance_artifacts_are_synchronized() -> None:
    source_registry = (ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    plugin_runbook = (ROOT / "docs/05_operations/plugin_metadata_runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-034_sensitive_capabilities_adrs.md").read_text(encoding="utf-8")

    assert "ADR-POSTH-034-B" in source_registry
    assert "POST-H-034-B-PLUGIN-EXECUTION-CHECKLIST" in source_registry
    assert "POST-H-034-B-PLUGIN-EXECUTION-DECISION-SCHEMA" in source_registry
    assert "post-h-034-plugin-execution-adr" in tcr_v1
    assert "post-h-034-plugin-execution-adr" in tcr_v2
    assert "POST-H-034-B — Plugin execution ADR" in readme
    assert "POST-H-034-B — Operación de ADR plugin execution" in runbook
    assert "POST-H-034-B — Plugin execution sigue bloqueado" in plugin_runbook
    assert "post-h-034-b" in changelog
    assert 'current_micro_sprint: "POST-H-034-B"' in backlog
    assert 'next_micro_sprint: "POST-H-034-C"' in backlog


def test_post_h_034_b_no_real_credentials_or_enablement_terms_are_versioned() -> None:
    watched_paths = [
        "docs/adr/ADR-POSTH-034-B-plugin-execution-enable-or-continue-blocked.md",
        ".devpilot/sensitive_capabilities/plugin_execution_enablement_checklist.json",
        ".devpilot/sensitive_capabilities/capability_decision_matrix.json",
        "docs/audits/post_h_034_b_plugin_execution_adr_report.md",
        "docs/post_h_034_b_manifest.json",
    ]
    combined = "\n".join((ROOT / path).read_text(encoding="utf-8").lower() for path in watched_paths)

    forbidden = [
        "api_key=",
        "authorization: bearer",
        "private_key",
        "plugin_execution_enabled=true",
        "runtime_execution_enabled=true",
        "dynamic_import_allowed=true",
        "subprocess_allowed=true",
        "production-enabled",
        "enabled-now",
    ]
    assert all(term not in combined for term in forbidden)
