from __future__ import annotations

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from devpilot_core.approval import ApprovalRequest, ApprovalStatus
from devpilot_core.approval.binding import compute_subject_hash
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.store import LocalStore

ROOT = Path(__file__).resolve().parents[1]


def _future(minutes: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _workspace(tmp_path: Path) -> Path:
    (tmp_path / ".devpilot" / "approval").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".devpilot" / "identity").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / ".devpilot" / "approval" / "sensitive_action_catalog.json", tmp_path / ".devpilot" / "approval" / "sensitive_action_catalog.json")
    shutil.copyfile(ROOT / ".devpilot" / "identity" / "identity_registry.json", tmp_path / ".devpilot" / "identity" / "identity_registry.json")
    return tmp_path


def _approved_record(
    root: Path,
    *,
    approval_id: str = "APPROVAL-012D-VALID",
    actor: str = "local-owner",
    role_at_decision: str = "owner",
    tool_id: str = "release.manager",
    action: str = "release.publish_deploy_tag",
    subject: str = "v1.2.3",
    command_id: str = "cmd-012-d",
    tool_call_id: str = "tool-call-012-d",
) -> str:
    scope = {
        "actor_id": actor,
        "role_at_decision": role_at_decision,
        "tool_id": tool_id,
        "action": action,
        "subject": subject,
        "subject_hash": compute_subject_hash(subject),
        "command_id": command_id,
        "tool_call_id": tool_call_id,
    }
    record = ApprovalRequest(
        approval_id=approval_id,
        subject=subject,
        tool_id=tool_id,
        action=action,
        actor=actor,
        reason="POST-H-012-D scoped approval fixture.",
        scope=scope,
        expires_at=_future(),
        metadata={"source": "POST-H-012-D-test"},
    ).to_record(approval_id=approval_id)
    payload = record.to_dict()
    payload.pop("expired", None)
    payload.update({"status": ApprovalStatus.APPROVED.value, "decision_at": _future(1), "decided_by": actor})
    created, _ = LocalStore(root).create_approval(payload)
    assert created is True
    return approval_id


def _finding_ids(result) -> set[str]:
    return {finding.id for finding in result.findings}


def test_policy_engine_blocks_sensitive_catalog_action_without_approval(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    result = PolicyEngine(root, observability_enabled=False).evaluate(
        PolicyRequest(
            action="release.publish_deploy_tag",
            tool_id="release.manager",
            subject="v1.2.3",
            actor="local-owner",
            role_at_decision="owner",
            command_id="cmd-012-d",
            tool_call_id="tool-call-012-d",
            interface="cli",
        )
    )

    ids = _finding_ids(result)
    assert result.ok is False
    assert "APPROVAL_REQUIRED" in ids
    assert "APPROVAL_REQUIRED_MISSING" in ids
    assert "SENSITIVE_ACTION_INTERFACE_BLOCKED" in ids
    assert "SENSITIVE_ACTION_NON_EXECUTABLE_BLOCKED" in ids
    assert result.data["summary"]["post_h_012_d_enforced"] is True
    assert result.data["summary"]["sensitive_action_id"] == "release.publish_deploy_tag"
    assert result.data["summary"]["remote_execution_enabled"] is False
    assert result.data["summary"]["connector_write_enabled"] is False
    assert result.data["summary"]["plugin_execution_enabled"] is False


def test_policy_engine_blocks_sensitive_action_with_insufficient_required_role(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    approval_id = _approved_record(
        root,
        approval_id="APPROVAL-012D-PATCH",
        role_at_decision="maintainer",
        tool_id="patch.sandbox",
        action="apply",
        subject="changes.patch",
    )

    result = PolicyEngine(root, observability_enabled=False).evaluate(
        PolicyRequest(
            action="apply",
            tool_id="patch.sandbox",
            subject="changes.patch",
            approval_id=approval_id,
            actor="local-owner",
            role_at_decision="maintainer",
            command_id="cmd-012-d",
            tool_call_id="tool-call-012-d",
            interface="cli",
        )
    )

    ids = _finding_ids(result)
    assert result.ok is False
    assert result.data["summary"]["approval_valid"] is True
    assert "RBAC_DENIED" in ids
    rbac_findings = [finding for finding in result.findings if finding.id == "RBAC_DENIED"]
    assert any(finding.metadata.get("requires_rbac_role") == "maintainer" for finding in rbac_findings)
    assert any(finding.metadata.get("required_role_declared") is False for finding in rbac_findings)
    assert "SENSITIVE_ACTION_NON_EXECUTABLE_BLOCKED" in ids


def test_policy_engine_reports_normalized_approval_scope_mismatch(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    approval_id = _approved_record(root)

    result = PolicyEngine(root, observability_enabled=False).evaluate(
        PolicyRequest(
            action="release.publish_deploy_tag",
            tool_id="release.manager",
            subject="v1.2.3",
            approval_id=approval_id,
            actor="local-owner",
            role_at_decision="owner",
            command_id="cmd-012-d",
            tool_call_id="wrong-tool-call",
            interface="cli",
        )
    )

    ids = _finding_ids(result)
    assert result.ok is False
    assert result.data["summary"]["approval_valid"] is False
    assert "APPROVAL_BINDING_MISMATCH" in ids
    assert "APPROVAL_SCOPE_MISMATCH" in ids
    assert any(
        finding.id == "APPROVAL_SCOPE_MISMATCH" and "APPROVAL_BINDING_TOOL_CALL_ID_MISMATCH" in finding.metadata.get("binding_findings", [])
        for finding in result.findings
    )


def test_policy_engine_keeps_read_only_requests_unchanged(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "readme.md").write_text("# Safe\n", encoding="utf-8")

    result = PolicyEngine(root, observability_enabled=False).evaluate(
        PolicyRequest(action="read", path="docs/readme.md", actor="local-owner", interface="cli")
    )

    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["sensitive_action_matched"] is False
    assert result.data["summary"]["post_h_012_d_enforced"] is True
    assert "POLICY_PASS" in _finding_ids(result)
