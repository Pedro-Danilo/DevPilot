from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "12334ffa5ea181f7d72fd66e55fb383baed2195f"


def j(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def t(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_uoc005_manifest_lifecycle_and_uoc006_gate_are_consistent() -> None:
    manifest = j("docs/post_h_eval_002_uoc_005_manifest.json")
    state = j(".devpilot/project_state.json")
    assert manifest["base_commit"] == BASE
    assert manifest["scope"]["approval_bound"] is True
    assert manifest["scope"]["atomic_apply"] is True
    assert manifest["scope"]["manual_rollback_requires_separate_approval"] is True
    assert manifest["scope"]["generic_patch_apply_enabled"] is False
    if manifest["closed"]:
        assert manifest["status"] == "closed/PASS"
        assert manifest["decision"] == "PASS"
        assert manifest["next"]["uoc_006_authorized"] is True
        assert state["uoc_005_closed"] is True
        assert state["uoc_006_authorized"] is True
        assert state["current_repo"] == "repo_DevPilot_Local_333_POST_H_EVAL_002_UOC_005.zip"
    else:
        assert manifest["status"] == "implemented-initial/pending-windows-browser-closure"
        assert manifest["decision"] in {"PENDING", "PENDING-WINDOWS-BROWSER-CLOSURE"}
        assert manifest["next"]["uoc_006_authorized"] is False
        assert state["uoc_005_closed"] is False
        assert state["uoc_006_authorized"] is False
        assert state["current_repo"] == "repo_DevPilot_Local_332_POST_H_EVAL_002_UOC_004.zip"


def test_uoc005_sensitive_actions_are_narrow_and_generic_no_go_remains() -> None:
    catalog = j(".devpilot/approval/sensitive_action_catalog.json")
    actions = {item["action_id"]: item for item in catalog["actions"]}
    apply = actions["filesystem.workspace_document_apply"]
    rollback = actions["filesystem.workspace_document_rollback"]
    assert apply["requires_approval"] and rollback["requires_approval"]
    assert apply["requires_tool_call_binding"] is False and rollback["requires_tool_call_binding"] is False
    assert apply["source_mutation_allowed"] and rollback["source_mutation_allowed"]
    assert apply["allowed_interfaces"] == ["api", "ui"]
    assert rollback["allowed_interfaces"] == ["api", "ui"]
    for action_id in ["patch.apply", "refactor.execute", "release.publish_deploy_tag", "connector.write_execute", "plugin.execute_code", "remote.execute"]:
        assert actions[action_id]["executable"] is False
        assert actions[action_id]["source_mutation_allowed"] is False


def test_uoc005_api_ui_and_flags_are_synchronized() -> None:
    api = j(".devpilot/interfaces/api_route_contract_registry.json")
    ui = j(".devpilot/interfaces/ui_route_contract_registry.json")
    flags = j(".devpilot/interfaces/ui_operational_console_flags.json")
    expected = {
        "api.workspace.edit-plans.approval-request",
        "api.workspace.edit-plans.apply",
        "api.workspace.edit-executions.status",
        "api.workspace.edit-executions.rollback-approval-request",
        "api.workspace.edit-executions.rollback",
    }
    api_routes = {item["route_id"]: item for item in api["routes"]}
    assert expected <= api_routes.keys()
    assert api_routes["api.workspace.edit-plans.apply"]["source_mutation_allowed"] is True
    assert api_routes["api.workspace.edit-executions.rollback"]["source_mutation_allowed"] is True
    route = next(item for item in ui["routes"] if item["route_id"] == "ui.workspace-documents")
    assert expected <= set(route["allowed_api_routes"])
    assert {"api.approvals.approve", "api.approvals.deny"} <= set(route["allowed_api_routes"])
    assert route["shows_mutation_controls"] is True
    flag = next(item for item in flags["feature_flags"] if item["flag_id"] == "uoc.documents.apply_rollback")
    assert flag["enabled"] is True and flag["enabled_by"] == "UOC-005"
    assert flags["safety"]["document_write_mode"] == "approval-gated-atomic-uoc005"
    assert flags["safety"]["generic_patch_apply_enabled"] is False


def test_uoc005_policy_matrix_and_test_contracts_are_registered() -> None:
    policy = j(".devpilot/miasi/policy_matrix.json")
    rule_ids = {item["rule_id"] for item in policy["rules"]}
    assert "WORKSPACE_DOCUMENT_APPLY_APPROVAL_GATED" in rule_ids
    assert "WORKSPACE_DOCUMENT_ROLLBACK_APPROVAL_GATED" in rule_ids
    for rel in [".devpilot/testing/test_contract_registry.json", ".devpilot/testing/test_contract_registry_v2.json"]:
        contracts = j(rel)["contracts"]
        assert any(item["contract_id"] == "post-h-eval-002-uoc-005-approval-apply-rollback" for item in contracts)


def test_uoc005_schema_and_docs_are_registered() -> None:
    catalog = j("docs/schemas/schema_catalog.json")
    assert any(item["schema_id"] == "SCHEMA-DEVPL-WORKSPACE-EDIT-EXECUTION-V1" for item in catalog["schemas"])
    docs = {item["doc_id"] for item in j(".devpilot/docs_governance/source_registry.json")["documents"]}
    assert {
        "DEVPL-UOC-005-APPROVAL-APPLY-ROLLBACK-REPORT",
        "DEVPL-UOC-005-CLOSURE-REPORT",
        "UOC-005-MANIFEST",
        "UOC-005-WORKSPACE-EDIT-EXECUTION-V1",
    } <= docs


def test_uoc005_openapi_contains_typed_mutation_routes() -> None:
    paths = j("docs/07_interfaces/openapi_v1.json")["paths"]
    assert "post" in paths["/api/v1/workspace/edit-plans/{plan_id}/approval-request"]
    assert "post" in paths["/api/v1/workspace/edit-plans/{plan_id}/apply"]
    assert "get" in paths["/api/v1/workspace/edit-executions/{execution_id}"]
    assert "post" in paths["/api/v1/workspace/edit-executions/{execution_id}/rollback-approval-request"]
    assert "post" in paths["/api/v1/workspace/edit-executions/{execution_id}/rollback"]


def test_uoc005_ui_exposes_human_approval_and_shared_traceability_styling() -> None:
    ui = t("ui/web/src/components/DocumentEditPlanner.ts")
    panel = t("ui/web/src/components/DocumentValidationPanel.ts")
    styles = t("ui/web/src/styles.css")
    assert "Solicitar aprobación de apply" in ui
    assert "Aplicar cambio aprobado" in ui
    assert "Solicitar aprobación de rollback" in ui
    assert "Revertir cambio aprobado" in ui
    assert "Aprobar" in ui and "Denegar" in ui
    assert "refreshButton.className = 'validation-action-button traceability-refresh-button'" in panel
    assert ".validation-action-button" in styles
    assert ".traceability-refresh-button:not(:disabled)" not in styles


def test_uoc004_closure_residual_status_is_reconciled() -> None:
    uoc4 = j("docs/post_h_eval_002_uoc_004_manifest.json")
    assert uoc4["status"] == "closed/PASS"
    assert uoc4["browser_export_feedback_corrective"]["status"] == "closed/PASS"
    assert 'updated: "2026-08-09"' in t("docs/audits/uoc_004_closure_report.md")

def test_uoc005_sensitive_catalog_remains_post_h_012_schema_compatible() -> None:
    from devpilot_core.approval import ApprovalRbacHardeningGate
    from devpilot_core.policy.sensitive_actions import SensitiveActionCatalogValidator

    catalog = j(".devpilot/approval/sensitive_action_catalog.json")
    assert catalog["created_by"] == "POST-H-012-A"
    assert "updated" not in catalog
    assert SensitiveActionCatalogValidator(ROOT).run().ok is True
    assert ApprovalRbacHardeningGate(ROOT).run().ok is True


def test_uoc005_miasi_approval_gates_are_concrete_and_semantically_valid() -> None:
    from devpilot_core.miasi import MiasiSemanticValidator

    rules = {item["rule_id"]: item for item in j(".devpilot/miasi/policy_matrix.json")["rules"]}
    for rule_id in ["WORKSPACE_DOCUMENT_APPLY_APPROVAL_GATED", "WORKSPACE_DOCUMENT_ROLLBACK_APPROVAL_GATED"]:
        gate = rules[rule_id]["gate"]
        assert "ApprovalPolicyChecker" in gate
        assert "StrongApprovalBindingValidator" in gate
        assert "RBAC(owner)" in gate
    result = MiasiSemanticValidator(ROOT).validate()
    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["blocking_findings_total"] == 0



def test_uoc005_inherited_docs_governance_reconciliation_is_explicit() -> None:
    from devpilot_core.docs_governance.drift import _roadmap_sync_passed

    checks = [
        {"rule": "version_match", "source_path": ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json", "counterpart_path": "docs/backlogs/post_h_prioritized_roadmap.md", "ok": True},
        {"rule": "milestones_match", "source_path": ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json", "counterpart_path": "docs/backlogs/post_h_prioritized_roadmap.md", "ok": True},
        {"rule": "decisions_match", "source_path": ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json", "counterpart_path": "docs/backlogs/post_h_prioritized_roadmap.md", "ok": True},
    ]
    assert _roadmap_sync_passed(checks) is True
    assert 'approval: "approved_by_owner"' in t("docs/audits/uoc_004_closure_report.md")


def test_uoc005_local_release_candidate_freshness_tracks_uoc004_authoritative_repo() -> None:
    criteria = j(".devpilot/release/local_release_candidate_criteria.json")
    state = j(".devpilot/project_state.json")
    evidence = next(item for item in criteria["evidence"] if item["evidence_id"] == "project-state-current-repo")
    expected = "repo_DevPilot_Local_332_POST_H_EVAL_002_UOC_004.zip"
    assert criteria["expected_current_repo"] == expected
    assert evidence["expected_fields"]["current_repo"] == expected
    assert state["current_repo"] == expected


def test_uoc005_historical_contract_reconciliation_keeps_evolving_registries_schema_valid():
    from jsonschema import Draft202012Validator

    pairs = [
        ("docs/schemas/ui_capability_registry.schema.json", ".devpilot/interfaces/ui_capability_registry.json"),
        ("docs/schemas/ui_operational_console_flags.schema.json", ".devpilot/interfaces/ui_operational_console_flags.json"),
    ]
    for schema_path, instance_path in pairs:
        schema = j(schema_path)
        instance = j(instance_path)
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(instance))
        assert errors == [], [error.message for error in errors]

    state = j(".devpilot/project_state.json")
    flags = j(".devpilot/interfaces/ui_operational_console_flags.json")
    assert state["uoc_006_authorized"] is False
    assert next(item for item in flags["feature_flags"] if item["flag_id"] == "uoc.git.governed_operations")["enabled"] is False


def test_uoc005_historical_route_contract_allows_only_narrow_source_mutations():
    routes = {item["route_id"]: item for item in j(".devpilot/interfaces/api_route_contract_registry.json")["routes"]}
    source_mutating = {route_id for route_id, route in routes.items() if route.get("source_mutation_allowed") is True}
    assert source_mutating == {"api.workspace.edit-plans.apply", "api.workspace.edit-executions.rollback"}
    for route_id in source_mutating:
        route = routes[route_id]
        assert route["local_only"] is True
        assert route["auth_required"] is True
        assert route["policy_check_required"] is True
        assert route["destructive_action_allowed"] is False
        assert str(route["policy_sensitivity"]).startswith("approval-bound-")
