from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def j(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def t(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_uoc006_manifest_state_backlog_and_next_gate_are_synchronized() -> None:
    manifest = j("docs/post_h_eval_002_uoc_006_manifest.json")
    state = j(".devpilot/project_state.json")
    backlog = t("docs/backlogs/POST-H-EVAL-002_ui_operational_console_evolution.md")
    assert manifest["base_commit"] == "9dfb0f380c3a7dea11321a5b75d2923cd7529a68"
    assert manifest["authoritative_input_repo"] == "repo_DevPilot_Local_333_POST_H_EVAL_002_UOC_005.zip"
    if manifest["closed"]:
        assert manifest["status"] == "closed/PASS"
        assert manifest["decision"] == "PASS"
        assert manifest["preliminary"] is False
        assert manifest["authoritative_output_repo"] == "repo_DevPilot_Local_334_POST_H_EVAL_002_UOC_006.zip"
        assert manifest["next"]["uoc_007_authorized"] is True
        current_repo = str(state["current_repo"])
        assert current_repo.startswith("repo_DevPilot_Local_")
        assert int(current_repo.split("_", 4)[3]) >= 334
        assert state["uoc_006_closed"] is True
        assert state["uoc_007_authorized"] is True
    else:
        assert manifest["status"] == "implemented-initial/pending-windows-browser-closure"
        assert manifest["preliminary"] is True
        assert manifest["next"]["uoc_007_authorized"] is False
        assert state["current_repo"] == "repo_DevPilot_Local_333_POST_H_EVAL_002_UOC_005.zip"
        assert state["uoc_006_closed"] is False
        assert state["uoc_007_authorized"] is False
    assert state["uoc_006_status"] == manifest["status"]
    if manifest["closed"]:
        # UOC-006 owns immutable closure facts, not the mutable global
        # last_registered_sprint/current_sprint pointer. Later UOC closures and
        # successor programs may legitimately replace that global pointer.
        assert state["uoc_006_status"] == "closed/PASS"
        assert state["uoc_007_authorized"] is True
        assert 'uoc_007_authorized: true' in backlog
    else:
        assert state["last_registered_sprint"] == "UOC-006"
        assert 'current_sprint: "UOC-006"' in backlog
        assert 'uoc_007_authorized: false' in backlog
    if manifest['closed']:
        completed_line = next(line for line in backlog.splitlines() if line.startswith("completed_sprints:"))
        completed = completed_line.split(":", 1)[1].strip().strip('"').split(",")
        assert completed[:7] == ["UOC-000", "UOC-001", "UOC-002", "UOC-003", "UOC-004", "UOC-005", "UOC-006"]
    else:
        assert 'UOC-005-closed/PASS' in backlog


def test_uoc005_final_closure_metadata_is_reconciled_before_uoc006() -> None:
    prior = j("docs/post_h_eval_002_uoc_005_manifest.json")
    assert prior["status"] == "closed/PASS"
    assert prior["closed"] is True
    assert prior["preliminary"] is False
    assert prior["authoritative_output_repo"] == "repo_DevPilot_Local_333_POST_H_EVAL_002_UOC_005.zip"


def test_uoc006_sensitive_action_catalog_and_miasi_are_schema_valid_and_concrete() -> None:
    from devpilot_core.miasi import MiasiSemanticValidator
    from devpilot_core.policy.sensitive_actions import SensitiveActionCatalogValidator

    assert SensitiveActionCatalogValidator(ROOT).run().ok is True
    semantic = MiasiSemanticValidator(ROOT).validate()
    assert semantic.ok is True, semantic.to_dict()
    policy = {x["rule_id"]: x for x in j(".devpilot/miasi/policy_matrix.json")["rules"]}
    tools = {x["tool_id"]: x for x in j(".devpilot/miasi/tool_registry.json")["tools"]}
    for rule_id in [
        "WORKSPACE_GIT_STAGE_APPROVAL_GATED",
        "WORKSPACE_GIT_COMMIT_APPROVAL_GATED",
        "WORKSPACE_GIT_BRANCH_CREATE_APPROVAL_GATED",
    ]:
        gate = policy[rule_id]["gate"]
        assert policy[rule_id]["approval_required"] is True
        assert "ApprovalPolicyChecker" in gate
        assert "StrongApprovalBindingValidator" in gate
        assert "RBAC(owner)" in gate
    for tool_id in ["git.workspace.stage", "git.workspace.commit", "git.workspace.branch_create"]:
        assert tools[tool_id]["requires_approval"] is True
        assert "GIT_WRITE_DENY" not in tools[tool_id]["policy_rule_ids"]


def test_uoc006_api_routes_are_exact_typed_local_and_no_go_stays_blocked() -> None:
    registry = j(".devpilot/interfaces/api_route_contract_registry.json")
    routes = {x["route_id"]: x for x in registry["routes"]}
    expected = {
        "api.workspace.git.status", "api.workspace.git.history", "api.workspace.git.compare",
        "api.workspace.git.plans.create", "api.workspace.git.plans.read",
        "api.workspace.git.stage-approval", "api.workspace.git.stage",
        "api.workspace.git.executions.read", "api.workspace.git.commit-approval",
        "api.workspace.git.commit", "api.workspace.git.branch-plan",
        "api.workspace.git.branch-approval", "api.workspace.git.branch-create",
    }
    assert expected <= routes.keys()
    source_mutations = {rid for rid, route in routes.items() if route.get("source_mutation_allowed") is True}
    assert {
        "api.workspace.edit-plans.apply", "api.workspace.edit-executions.rollback",
        "api.workspace.git.stage", "api.workspace.git.commit", "api.workspace.git.branch-create",
    } == source_mutations
    for rid in expected:
        route = routes[rid]
        assert route["local_only"] is True
        assert route["auth_required"] is True
        assert route["policy_check_required"] is True
        assert route["remote_execution_allowed"] is False
        assert route["connector_write_allowed"] is False
        assert route["plugin_execution_allowed"] is False
        assert route["external_api_allowed"] is False
    for rid in ["api.workspace.git.stage", "api.workspace.git.commit", "api.workspace.git.branch-create"]:
        assert routes[rid]["destructive_action_allowed"] is False
        assert routes[rid]["risk_level"] == "high"
        assert str(routes[rid]["policy_sensitivity"]).startswith("approval-bound-")


def test_uoc006_flags_and_capability_registry_declare_only_narrow_git_write() -> None:
    flags = j(".devpilot/interfaces/ui_operational_console_flags.json")
    capabilities = j(".devpilot/interfaces/ui_capability_registry.json")
    git_flag = next(x for x in flags["feature_flags"] if x["flag_id"] == "uoc.git.governed_operations")
    assert git_flag["enabled"] is True and git_flag["enabled_by"] == "UOC-006"
    safety = flags["safety"]
    assert safety["governed_git_write_enabled"] is True
    for key in ["generic_git_write_enabled", "git_push_enabled", "git_force_push_enabled", "git_reset_hard_enabled", "git_rebase_enabled", "git_branch_delete_enabled"]:
        assert safety[key] is False
    assert capabilities["summary"]["api_routes_total"] >= 71
    assert capabilities["safety"]["remote_execution_enabled"] is False
    assert capabilities["safety"]["connector_write_enabled"] is False
    assert capabilities["safety"]["plugin_execution_enabled"] is False


def test_uoc006_schemas_docs_and_test_contract_are_registered() -> None:
    catalog = j("docs/schemas/schema_catalog.json")
    ids = {x["schema_id"] for x in catalog["schemas"]}
    assert {"SCHEMA-DEVPL-WORKSPACE-GIT-PLAN-V1", "SCHEMA-DEVPL-WORKSPACE-GIT-EXECUTION-V1"} <= ids
    docs = {x["doc_id"] for x in j(".devpilot/docs_governance/source_registry.json")["documents"]}
    assert {"DEVPL-UOC-006-GOVERNED-GIT-OPERATIONS-REPORT", "DEVPL-UOC-006-CLOSURE-REPORT", "UOC-006-MANIFEST", "UOC-006-WORKSPACE-GIT-PLAN-V1", "UOC-006-WORKSPACE-GIT-EXECUTION-V1"} <= docs
    for rel in [".devpilot/testing/test_contract_registry.json", ".devpilot/testing/test_contract_registry_v2.json"]:
        assert any(x["contract_id"] == "post-h-eval-002-uoc-006-governed-git-operations" for x in j(rel)["contracts"])


def test_uoc006_adapter_does_not_expose_arbitrary_or_dangerous_git_surface() -> None:
    from devpilot_core.repo.governed_git_mutation import GovernedGitMutationAdapter

    public = {name for name in dir(GovernedGitMutationAdapter) if not name.startswith("_")}
    for forbidden in ["run", "push", "force_push", "reset", "reset_hard", "rebase", "delete_branch", "checkout", "switch", "tag"]:
        assert forbidden not in public
    assert {"stage_paths", "unstage_paths", "commit", "create_branch", "compare"} <= public


def test_uoc006_openapi_and_ui_route_registry_are_synchronized() -> None:
    paths = j("docs/07_interfaces/openapi_v1.json")["paths"]
    for path in [
        "/api/v1/workspace/git/status",
        "/api/v1/workspace/git/history",
        "/api/v1/workspace/git/compare",
        "/api/v1/workspace/git/plans",
        "/api/v1/workspace/git/plans/{plan_id}/stage",
        "/api/v1/workspace/git/stage-executions/{execution_id}/commit",
        "/api/v1/workspace/git/branches/{plan_id}/create",
    ]:
        assert path in paths
    ui = next(x for x in j(".devpilot/interfaces/ui_route_contract_registry.json")["routes"] if x["route_id"] == "ui.workspace-documents")
    assert "api.workspace.git.status" in ui["allowed_api_routes"]
    assert "api.workspace.git.commit" in ui["allowed_api_routes"]
    assert "api.workspace.git.branch-create" in ui["allowed_api_routes"]
