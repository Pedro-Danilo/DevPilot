from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil

from devpilot_core import cli  # noqa: F401 - initializes policy package before direct approval.policy import
from devpilot_core.approval import ApprovalRequest, ApprovalStatus
from devpilot_core.approval.binding import (
    ApprovalBindingRequest,
    StrongApprovalBindingValidator,
    compute_subject_hash,
)
from devpilot_core.approval.policy import ApprovalPolicyChecker, ApprovalPolicyInput
from devpilot_core.store import LocalStore


def _future(minutes: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _past(minutes: int = 30) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _record(
    *,
    approval_id: str = "APPROVAL-BINDING-VALID",
    status: str = ApprovalStatus.APPROVED.value,
    subject: str = "changes.patch",
    tool_id: str = "patch.sandbox",
    action: str = "apply",
    actor: str = "local-owner",
    role_at_decision: str = "maintainer",
    command_id: str | None = "cmd-012-b",
    tool_call_id: str | None = "tool-call-012-b",
    subject_hash: str | None = None,
    expires_at: str | None = None,
):
    scope = {
        "actor_id": actor,
        "role_at_decision": role_at_decision,
        "tool_id": tool_id,
        "action": action,
        "subject": subject,
        "subject_hash": subject_hash or compute_subject_hash(subject),
    }
    if command_id is not None:
        scope["command_id"] = command_id
    if tool_call_id is not None:
        scope["tool_call_id"] = tool_call_id
    record = ApprovalRequest(
        approval_id=approval_id,
        subject=subject,
        tool_id=tool_id,
        action=action,
        actor=actor,
        reason="Approve one exact local patch operation.",
        scope=scope,
        expires_at=expires_at or _future(),
        metadata={"source": "POST-H-012-B-test"},
    ).to_record(approval_id=approval_id)
    payload = record.to_dict()
    payload.pop("expired", None)
    payload.update({"status": status, "decision_at": _future(1), "decided_by": actor})
    return type(record)(**payload)


def _binding_request(**overrides: object) -> ApprovalBindingRequest:
    data = {
        "approval_id": "APPROVAL-BINDING-VALID",
        "actor_id": "local-owner",
        "role_at_decision": "maintainer",
        "tool_id": "patch.sandbox",
        "action": "apply",
        "subject": "changes.patch",
        "subject_hash": compute_subject_hash("changes.patch"),
        "command_id": "cmd-012-b",
        "tool_call_id": "tool-call-012-b",
        "interface": "cli",
    }
    data.update(overrides)
    return ApprovalBindingRequest(**data)  # type: ignore[arg-type]


def _finding_ids(result) -> set[str]:
    return {finding.id for finding in result.findings}


def test_strong_approval_binding_accepts_exact_scope() -> None:
    result = StrongApprovalBindingValidator(Path.cwd()).evaluate(_record(), _binding_request())

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    assert summary["binding_valid"] is True
    assert summary["sensitive_action_id"] == "patch.apply"
    assert summary["requires_command_binding"] is True
    assert summary["requires_tool_call_binding"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert "APPROVAL_BINDING_VALID" in _finding_ids(result)


def test_strong_approval_binding_blocks_wrong_actor_tool_action_subject() -> None:
    validator = StrongApprovalBindingValidator(Path.cwd())

    assert "APPROVAL_BINDING_ACTOR_ID_MISMATCH" in _finding_ids(validator.evaluate(_record(), _binding_request(actor_id="spoofed-actor")))
    assert "APPROVAL_BINDING_TOOL_ID_MISMATCH" in _finding_ids(validator.evaluate(_record(), _binding_request(tool_id="rollback.plan")))
    assert "APPROVAL_BINDING_ACTION_MISMATCH" in _finding_ids(validator.evaluate(_record(), _binding_request(action="delete")))
    assert "APPROVAL_BINDING_SUBJECT_MISMATCH" in _finding_ids(validator.evaluate(_record(), _binding_request(subject="other.patch")))


def test_strong_approval_binding_blocks_expired_and_revoked_approvals() -> None:
    validator = StrongApprovalBindingValidator(Path.cwd())

    expired = validator.evaluate(_record(expires_at=_past()), _binding_request())
    revoked = validator.evaluate(_record(status=ApprovalStatus.REVOKED.value), _binding_request())

    assert expired.ok is False
    assert "APPROVAL_BINDING_EXPIRED" in _finding_ids(expired)
    assert revoked.ok is False
    assert "APPROVAL_BINDING_REVOKED" in _finding_ids(revoked)


def test_strong_approval_binding_blocks_subject_hash_and_tool_call_mismatch() -> None:
    validator = StrongApprovalBindingValidator(Path.cwd())

    hash_mismatch = validator.evaluate(_record(), _binding_request(subject_hash=compute_subject_hash("other.patch")))
    tool_call_mismatch = validator.evaluate(_record(), _binding_request(tool_call_id="tool-call-other"))
    command_mismatch = validator.evaluate(_record(), _binding_request(command_id="cmd-other"))

    assert "APPROVAL_BINDING_SUBJECT_HASH_MISMATCH" in _finding_ids(hash_mismatch)
    assert "APPROVAL_BINDING_TOOL_CALL_ID_MISMATCH" in _finding_ids(tool_call_mismatch)
    assert "APPROVAL_BINDING_COMMAND_ID_MISMATCH" in _finding_ids(command_mismatch)


def test_strong_approval_binding_blocks_missing_required_command_or_tool_call() -> None:
    validator = StrongApprovalBindingValidator(Path.cwd())

    missing_command = validator.evaluate(_record(command_id=None), _binding_request(command_id=None))
    missing_tool_call = validator.evaluate(_record(tool_call_id=None), _binding_request(tool_call_id=None))

    assert missing_command.ok is False
    assert "APPROVAL_BINDING_COMMAND_ID_REQUIRED" in _finding_ids(missing_command)
    assert missing_tool_call.ok is False
    assert "APPROVAL_BINDING_TOOL_CALL_ID_REQUIRED" in _finding_ids(missing_tool_call)


def test_strong_approval_binding_blocks_generic_approval_scope() -> None:
    validator = StrongApprovalBindingValidator(Path.cwd())
    generic = _record(subject="*", subject_hash=compute_subject_hash("*"))

    result = validator.evaluate(generic, _binding_request(subject="changes.patch"))

    assert result.ok is False
    assert "APPROVAL_BINDING_GENERIC_SCOPE_BLOCKED" in _finding_ids(result) or "APPROVAL_BINDING_SUBJECT_MISMATCH" in _finding_ids(result)


def test_approval_policy_checker_uses_strong_binding_for_sensitive_catalog_actions(tmp_path: Path) -> None:
    catalog_target = tmp_path / ".devpilot" / "approval"
    catalog_target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path.cwd() / ".devpilot" / "approval" / "sensitive_action_catalog.json", catalog_target / "sensitive_action_catalog.json")
    record = _record()
    created, _ = LocalStore(tmp_path).create_approval(record.to_dict())
    assert created is True
    checker = ApprovalPolicyChecker(tmp_path)

    blocked = checker.evaluate(
        ApprovalPolicyInput(
            action="apply",
            approval_id=record.approval_id,
            tool_id="patch.sandbox",
            subject="changes.patch",
            metadata={"actor_id": "local-owner", "role_at_decision": "maintainer", "command_id": "cmd-012-b"},
        )
    )
    allowed = checker.evaluate(
        ApprovalPolicyInput(
            action="apply",
            approval_id=record.approval_id,
            tool_id="patch.sandbox",
            subject="changes.patch",
            actor_id="local-owner",
            role_at_decision="maintainer",
            command_id="cmd-012-b",
            tool_call_id="tool-call-012-b",
        )
    )

    assert blocked.effect.value == "block"
    assert blocked.rule_id == "APPROVAL_BINDING_MISMATCH"
    assert "APPROVAL_BINDING_TOOL_CALL_ID_REQUIRED" in blocked.metadata["binding_findings"]
    assert allowed.effect.value == "allow"
    assert allowed.rule_id == "APPROVAL_VALID"
    assert allowed.metadata["strong_binding_required"] is True
