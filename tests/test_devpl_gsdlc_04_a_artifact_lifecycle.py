from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from devpilot_core.application import ArtifactLifecycleService, ArtifactSourceType, ArtifactState
from devpilot_core.schemas import SchemaValidator
from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "7f6c9ed8a49fd9300d8b10eb3255969256eb2865"
FROZEN_04A_PREDECESSOR_PATHS = {
    ".devpilot/interfaces/api_route_contract_registry.json",
    ".devpilot/interfaces/ui_route_contract_registry.json",
    ".devpilot/interfaces/ui_capability_registry.json",
    ".devpilot/approval/sensitive_action_catalog.json",
    ".devpilot/identity/server_rbac_policy_catalog.json",
    "src/devpilot_core/application/workspace_edit_plan_service.py",
    "src/devpilot_core/application/workspace_edit_execution_service.py",
}


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def fixture() -> dict:
    return load_json("evals/fixtures/gsdlc_04_a_artifact_lifecycle_cases.json")


def service() -> ArtifactLifecycleService:
    return ArtifactLifecycleService(ROOT)


def draft() -> dict:
    case = fixture()["valid"]
    result = service().create_draft(
        artifact_id=case["artifact_id"],
        relative_path=case["relative_path"],
        content=case["content"],
        source_type=case["source_type"],
        base_commit=BASE_COMMIT,
        actor=case["actor"],
        actor_role=case["actor_role"],
        session_principal=case["session_principal"],
        reviewer=case["reviewer"],
        reviewer_role=case["reviewer_role"],
        source_label="manual-test",
    )
    assert result.ok, result.to_dict()
    return result.data["artifact"]


def transition(record: dict, target: ArtifactState, *, actor="owner.local", role="owner", findings_present=None) -> dict:
    result = service().transition(record, target_state=target, actor=actor, actor_role=role, findings_present=findings_present)
    assert result.ok, result.to_dict()
    return result.data["artifact"]


def test_artifact_lifecycle_schemas_are_registered_and_validate_positive_negative() -> None:
    catalog = load_json("docs/schemas/schema_catalog.json")
    by_contract = {row.get("contract"): row for row in catalog["schemas"]}
    for contract in ("ArtifactState", "ArtifactProvenance", "ArtifactLifecycleRecord", "ArtifactLifecyclePolicy"):
        assert contract in by_contract
        assert (ROOT / by_contract[contract]["path"]).is_file()

    validator = SchemaValidator(ROOT)
    assert validator.validate_payload(schema="ArtifactState", payload={"state": "DRAFT"}, instance_label="positive").ok
    assert not validator.validate_payload(schema="ArtifactState", payload={"state": "UNKNOWN"}, instance_label="negative").ok
    assert validator.validate(schema="ArtifactLifecyclePolicy", instance=".devpilot/artifacts/artifact_lifecycle_policy.json").ok


def test_profile_policy_covers_data_driven_profiles_without_duplicating_selection_truth() -> None:
    registry = ArtifactProfileRegistry(ROOT)
    profiles, generic, fallback = registry.load_profiles(allow_fallback=False)
    assert fallback is False
    policy = service().policy()
    expected = {p.id for p in profiles} | {generic.id, "structured-json"}
    assert set(policy["profile_permissions"]) == expected
    assert "path_contains" not in json.dumps(policy["profile_permissions"])
    assert "filename" not in json.dumps(policy["profile_permissions"])
    assert policy["agent_assisted_execution_enabled"] is False
    assert policy["server_authoritative"] is True
    assert "AGENT_ASSISTED" not in policy["profile_permissions"]["miasi-human-approval-card"]["allowed_source_types"]


def test_draft_requires_complete_provenance_and_hashes_are_deterministic() -> None:
    record = draft()
    provenance = record["provenance"]
    assert record["state"] == "DRAFT"
    assert provenance["author_actor"] == "owner.local"
    assert provenance["reviewer"] == "qa.local"
    assert provenance["session_principal"] == "authenticated:owner.local"
    assert provenance["base_commit"] == BASE_COMMIT
    assert provenance["artifact_version"] == 1
    assert record["content_hash"] == provenance["normalized_sha256"]
    assert service().validate_record(record).ok

    assert ArtifactLifecycleService.hash_normalized("\ufeffa\r\nb\r\n") == ArtifactLifecycleService.hash_normalized("a\nb\n")
    assert ArtifactLifecycleService.hash_source("\ufeffa\r\nb\r\n") != ArtifactLifecycleService.hash_source("a\nb\n")


def test_full_legal_transition_matrix_and_findings_remediation() -> None:
    record = draft()
    record = transition(record, ArtifactState.VALIDATING)

    findings = service().transition(
        record,
        target_state=ArtifactState.FINDINGS,
        actor="qa.local",
        actor_role="qa-reviewer",
        findings_present=True,
    )
    assert findings.ok
    record = findings.data["artifact"]
    record = transition(record, ArtifactState.DRAFT, actor="owner.local", role="owner")
    record = transition(record, ArtifactState.VALIDATING)
    record = transition(record, ArtifactState.READY_FOR_REVIEW, actor="qa.local", role="qa-reviewer", findings_present=False)
    record = transition(record, ArtifactState.APPROVAL_REQUIRED, actor="qa.local", role="qa-reviewer")
    record = transition(record, ArtifactState.APPROVED, actor="qa.local", role="qa-reviewer")
    record = transition(record, ArtifactState.FROZEN, actor="qa.local", role="qa-reviewer")
    assert record["state"] == "FROZEN"
    assert service().validate_record(record).ok


def test_illegal_transition_and_wrong_role_fail_closed() -> None:
    record = draft()
    illegal = service().transition(record, target_state=ArtifactState.APPROVED, actor="owner.local", actor_role="owner")
    assert not illegal.ok
    assert any(f.id == "GSDLC04A_ILLEGAL_TRANSITION_BLOCK" for f in illegal.findings)

    validating = transition(record, ArtifactState.VALIDATING)
    wrong_role = service().transition(
        validating,
        target_state=ArtifactState.READY_FOR_REVIEW,
        actor="agent.local",
        actor_role="agent-supervisor",
        findings_present=False,
    )
    assert not wrong_role.ok
    assert any(f.id == "GSDLC04A_TRANSITION_ROLE_BLOCK" for f in wrong_role.findings)


def test_assigned_reviewer_is_bound_to_approval_and_freeze() -> None:
    record = draft()
    record = transition(record, ArtifactState.VALIDATING)
    record = transition(record, ArtifactState.READY_FOR_REVIEW, actor="qa.local", role="qa-reviewer", findings_present=False)
    record = transition(record, ArtifactState.APPROVAL_REQUIRED, actor="qa.local", role="qa-reviewer")

    wrong = service().transition(record, target_state=ArtifactState.APPROVED, actor="other.qa", actor_role="qa-reviewer")
    assert not wrong.ok
    assert any(f.id == "GSDLC04A_REVIEWER_BINDING_BLOCK" for f in wrong.findings)

    approved = transition(record, ArtifactState.APPROVED, actor="qa.local", role="qa-reviewer")
    frozen = transition(approved, ArtifactState.FROZEN, actor="qa.local", role="qa-reviewer")
    direct_edit = service().transition(frozen, target_state=ArtifactState.DRAFT, actor="owner.local", actor_role="owner")
    assert not direct_edit.ok


def test_external_hash_drift_invalidates_approved_and_frozen_without_writing_source() -> None:
    record = draft()
    record = transition(record, ArtifactState.VALIDATING)
    record = transition(record, ArtifactState.READY_FOR_REVIEW, actor="qa.local", role="qa-reviewer", findings_present=False)
    record = transition(record, ArtifactState.APPROVAL_REQUIRED, actor="qa.local", role="qa-reviewer")
    record = transition(record, ArtifactState.APPROVED, actor="qa.local", role="qa-reviewer")
    record = transition(record, ArtifactState.FROZEN, actor="qa.local", role="qa-reviewer")
    version = record["provenance"]["artifact_version"]

    result = service().reconcile_external_content(
        record,
        current_content="# externally changed\n",
        actor="owner.local",
        actor_role="owner",
        session_principal="authenticated:owner.local",
    )
    assert result.ok, result.to_dict()
    updated = result.data["artifact"]
    assert updated["state"] == "REVALIDATION_REQUIRED"
    assert updated["provenance"]["source_type"] == "EXTERNAL_EDITOR"
    assert updated["provenance"]["artifact_version"] == version + 1
    assert result.data["summary"]["source_mutations_performed"] is False


def test_same_normalized_hash_preserves_frozen_state() -> None:
    case = fixture()["valid"]
    result = service().create_draft(
        artifact_id=case["artifact_id"],
        relative_path=case["relative_path"],
        content="a\r\nb\r\n",
        source_type="MANUAL",
        base_commit=BASE_COMMIT,
        actor="owner.local",
        actor_role="owner",
        session_principal="authenticated:owner.local",
        reviewer="qa.local",
        reviewer_role="qa-reviewer",
    )
    assert result.ok
    record=result.data["artifact"]
    record = transition(record, ArtifactState.VALIDATING)
    record = transition(record, ArtifactState.READY_FOR_REVIEW, actor="qa.local", role="qa-reviewer", findings_present=False)
    record = transition(record, ArtifactState.APPROVAL_REQUIRED, actor="qa.local", role="qa-reviewer")
    record = transition(record, ArtifactState.APPROVED, actor="qa.local", role="qa-reviewer")
    record = transition(record, ArtifactState.FROZEN, actor="qa.local", role="qa-reviewer")

    stable=service().reconcile_external_content(
        record,
        current_content="a\nb\n",
        actor="owner.local",
        actor_role="owner",
        session_principal="authenticated:owner.local",
    )
    assert stable.ok
    assert stable.data["summary"]["drift_detected"] is False
    assert stable.data["artifact"]["state"] == "FROZEN"


@pytest.mark.parametrize("bad_path", fixture()["negative_paths"])
def test_path_policy_blocks_traversal_absolute_and_unsupported_types(bad_path: str) -> None:
    case=fixture()["valid"]
    result=service().create_draft(
        artifact_id="negative-path",
        relative_path=bad_path,
        content="# safe\n",
        source_type="MANUAL",
        base_commit=BASE_COMMIT,
        actor=case["actor"],
        actor_role=case["actor_role"],
        session_principal=case["session_principal"],
        reviewer=case["reviewer"],
        reviewer_role=case["reviewer_role"],
    )
    assert not result.ok


def test_unknown_source_actor_reviewer_and_secret_content_fail_closed() -> None:
    case=fixture()["valid"]
    unknown=service().create_draft(
        artifact_id="unknown-source",
        relative_path=case["relative_path"],
        content="# safe\n",
        source_type=fixture()["unknown_source"],
        base_commit=BASE_COMMIT,
        actor=case["actor"], actor_role=case["actor_role"],
        session_principal=case["session_principal"],
        reviewer=case["reviewer"], reviewer_role=case["reviewer_role"],
    )
    assert not unknown.ok
    assert any(f.id=="GSDLC04A_UNKNOWN_SOURCE_BLOCK" for f in unknown.findings)

    missing=service().create_draft(
        artifact_id="missing-identity",
        relative_path=case["relative_path"],
        content="# safe\n", source_type="MANUAL", base_commit=BASE_COMMIT,
        actor="", actor_role="owner", session_principal="", reviewer="", reviewer_role="qa-reviewer",
    )
    assert not missing.ok
    ids={f.id for f in missing.findings}
    assert {"GSDLC04A_ACTOR_REQUIRED_BLOCK","GSDLC04A_SESSION_PRINCIPAL_REQUIRED_BLOCK","GSDLC04A_REVIEWER_REQUIRED_BLOCK"} <= ids

    secret=service().create_draft(
        artifact_id="secret-source",
        relative_path=case["relative_path"],
        content=fixture()["secret_content"],
        source_type="MANUAL", base_commit=BASE_COMMIT,
        actor=case["actor"], actor_role=case["actor_role"],
        session_principal=case["session_principal"],
        reviewer=case["reviewer"], reviewer_role=case["reviewer_role"],
    )
    assert not secret.ok
    assert any(f.id=="GSDLC04A_SECRET_AUTO_VERSION_BLOCK" for f in secret.findings)


def test_upload_policy_is_contractual_but_04a_does_not_execute_upload_or_workspace_writes() -> None:
    policy=service().policy()
    assert policy["path_policy"]["max_source_bytes"] == 1048576
    assert policy["path_policy"]["allowed_extensions"] == [".md", ".json"]
    assert policy["path_policy"]["secret_bearing_auto_version"] is False
    source=(ROOT/"src/devpilot_core/application/artifact_lifecycle_service.py").read_text(encoding="utf-8")
    assert "WorkspaceEditExecutionApplicationService(" not in source
    assert "WorkspaceEditPlanApplicationService(" not in source
    assert "os.replace(" not in source
    assert "subprocess" not in source


def test_04a_does_not_change_api_ui_rbac_sensitive_actions_or_uoc_write_engine() -> None:
    changed_paths = {
        line.strip().replace("\\", "/")
        for line in (ROOT / "docs/audits/DEVPL_GSDLC_04_A_CHANGED_PATHS.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    assert FROZEN_04A_PREDECESSOR_PATHS.isdisjoint(changed_paths)
    for relative in FROZEN_04A_PREDECESSOR_PATHS:
        assert (ROOT / relative).is_file(), relative


def test_activation_rebind_historical_pre_windows_snapshot_is_preserved() -> None:
    state=load_json(".devpilot/project_state.json")
    current=load_json("DEVPL_GSDLC_03_FINAL_OWNER_CLOSURE_CURRENT.json")
    registry=load_json(".devpilot/docs_governance/source_registry.json")
    assert current["status"]=="CLOSED/PASS"
    assert current["owner_adjudication_pending"] is False
    assert current["owner_adjudication_completed"] is True
    assert state["gsdlc_03_status"]=="closed/PASS"
    assert state["gsdlc_03_e_status"]=="closed/PASS"
    assert state["gsdlc_04_authorized"] is True
    assert state["gsdlc_04_a_status_at_pre_windows_close"]=="pass-candidate/pre-windows"
    assert state["gsdlc_04_a_full_regression_executed"] is False
    assert state["gsdlc_04_b_authorized_at_04_a_pre_windows_close"] is False
    historical_micro_sprint=state["gsdlc_current_micro_sprint_at_04_a_pre_windows_close"]
    assert historical_micro_sprint=="DEVPL-GSDLC-04-A"
    assert historical_micro_sprint.startswith("DEVPL-GSDLC-04-")
    assert state["gsdlc_execution_source_repo_at_04_a_pre_windows_close"]=="repo_DevPilot_Local_364_DEVPL_GSDLC_03_E_PROJECT_ENTRY_BROWSER_COMPOSITE_WINDOWS_VALIDATED_CANDIDATE.zip"
    assert state["gsdlc_execution_source_commit_at_04_a_pre_windows_close"]==BASE_COMMIT
    # Mutable execution-source pointers are allowed to advance with later
    # backlogs; the historical 04-A snapshot above is the frozen contract.
    assert state["gsdlc_execution_source_repo"] != state["gsdlc_execution_source_repo_at_04_a_pre_windows_close"]
    assert registry["gsdlc_last_registered_micro_sprint_at_04_a_pre_windows_close"]=="DEVPL-GSDLC-04-A"
    assert registry["gsdlc_04_a_status_at_pre_windows_close"]=="pass-candidate/pre-windows"


def test_runtime_ephemeral_and_validation_policy_remain_enforced() -> None:
    policy=load_json(".devpilot/gsdlc/transversal_validation_policy.json")
    docs=(ROOT/"docs/02_architecture/governance/DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED.md").read_text(encoding="utf-8")
    assert "auth.db*" in docs
    assert "devpilot.db*" in docs
    assert policy["default"]["full_regression_rerun_after_failure"] is False
    assert load_json("docs/audits/DEVPL_GSDLC_04_A_OPERATION_DECLARATION.json")["full_regression_executed"] is False
