from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from .models import ApprovalRecord, ApprovalStatus, is_expired

POST_H_012_B_CREATED_BY = "POST-H-012-B"
APPROVAL_BINDING_COMMAND = "approval binding-validate"


@dataclass(frozen=True)
class ApprovalBindingRequest:
    """Exact-scope request validated against an approved local approval record.

    POST-H-012-B deliberately keeps this contract local and deterministic.  It
    does not execute the requested action, does not grant RBAC by itself and
    does not bypass PathGuard, SecretGuard, CostGuard or PolicyEngine.
    """

    approval_id: str
    actor_id: str
    tool_id: str
    action: str
    subject: str
    role_at_decision: str | None = None
    command_id: str | None = None
    tool_call_id: str | None = None
    subject_hash: str | None = None
    interface: str | None = None
    now: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ApprovalBindingOptions:
    catalog_path: Path = Path(".devpilot/approval/sensitive_action_catalog.json")


class StrongApprovalBindingValidator:
    """Validate that an approval can only authorize its exact bound scope.

    The validator checks a stored ApprovalRecord against the requested actor,
    role, tool, action, subject, optional subject hash, command_id and
    tool_call_id.  It is fail-closed for sensitive catalog actions and
    conservative for legacy approvals.
    """

    def __init__(self, root: Path, *, options: ApprovalBindingOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ApprovalBindingOptions()

    @property
    def catalog_path(self) -> Path:
        return self.root / self.options.catalog_path

    def evaluate(self, record: ApprovalRecord | None, request: ApprovalBindingRequest) -> CommandResult:
        findings: list[Finding] = []
        action_entry = self._resolve_sensitive_action(request.tool_id, request.action)
        sensitive = action_entry is not None
        requirements = _requirements(action_entry)

        summary: dict[str, Any] = {
            "created_by": POST_H_012_B_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "approval_id": request.approval_id,
            "actor_id": request.actor_id,
            "tool_id": request.tool_id,
            "action": request.action,
            "subject": request.subject,
            "role_at_decision": request.role_at_decision,
            "command_id": request.command_id,
            "tool_call_id": request.tool_call_id,
            "subject_hash": request.subject_hash or compute_subject_hash(request.subject),
            "sensitive_action_matched": sensitive,
            "sensitive_action_id": action_entry.get("action_id") if action_entry else None,
            "requires_approval": requirements["requires_approval"],
            "requires_rbac_role": requirements["requires_rbac_role"],
            "requires_command_binding": requirements["requires_command_binding"],
            "requires_tool_call_binding": requirements["requires_tool_call_binding"],
            "network_used": False,
            "external_api_used": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
        }

        if not request.approval_id.strip():
            findings.append(_block("APPROVAL_BINDING_ID_REQUIRED", "Approval binding requires approval_id."))
        if record is None:
            findings.append(_block("APPROVAL_BINDING_RECORD_MISSING", "Approval binding requires an existing approval record."))
            return self._result(False, findings, summary)

        summary.update(
            {
                "record_status": record.status,
                "record_actor": record.actor,
                "record_tool_id": record.tool_id,
                "record_action": record.action,
                "record_subject": record.subject,
                "record_expires_at": record.expires_at,
            }
        )

        if record.approval_id.strip() != request.approval_id.strip():
            findings.append(
                _block(
                    "APPROVAL_BINDING_APPROVAL_ID_MISMATCH",
                    "Approval record ID does not match requested approval_id.",
                    approval_id=request.approval_id,
                    record_approval_id=record.approval_id,
                )
            )
        if record.status == ApprovalStatus.REVOKED.value:
            findings.append(_block("APPROVAL_BINDING_REVOKED", "Revoked approval cannot authorize any action.", approval_id=record.approval_id))
        elif record.status == ApprovalStatus.EXPIRED.value or is_expired(record.expires_at, now=request.now):
            findings.append(_block("APPROVAL_BINDING_EXPIRED", "Expired approval cannot authorize any action.", approval_id=record.approval_id, expires_at=record.expires_at))
        elif record.status != ApprovalStatus.APPROVED.value:
            findings.append(_block("APPROVAL_BINDING_NOT_APPROVED", "Approval must be approved before it can authorize a bound action.", approval_id=record.approval_id, status=record.status))

        scope = _binding_scope(record)
        summary["approval_scope_keys"] = sorted(scope.keys())

        self._check_exact("actor_id", request.actor_id, _scope_value(scope, "actor_id", record.actor), findings)
        self._check_role(request, scope, requirements, findings)
        self._check_exact("tool_id", request.tool_id, _scope_value(scope, "tool_id", record.tool_id), findings)
        self._check_action(request, scope, record, action_entry, findings)
        self._check_exact("subject", request.subject, _scope_value(scope, "subject", record.subject), findings)
        self._check_subject_hash(request, scope, findings)
        self._check_command_binding(request, scope, requirements, findings)
        self._check_tool_call_binding(request, scope, requirements, findings)
        self._check_generic_scope(scope, requirements, findings)

        ok = not any(finding.severity in {Severity.BLOCK, Severity.ERROR} for finding in findings)
        if ok:
            findings.append(
                Finding(
                    id="APPROVAL_BINDING_VALID",
                    message="Approval is approved, unexpired and exactly bound to actor/role/tool/action/subject scope.",
                    severity=Severity.INFO,
                    metadata={"approval_id": request.approval_id, "sensitive_action_id": summary["sensitive_action_id"]},
                )
            )
        summary["binding_valid"] = ok
        summary["blocking_findings_total"] = sum(1 for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR})
        return self._result(ok, findings, summary)

    def _check_exact(self, field_name: str, requested: str | None, recorded: Any, findings: list[Finding]) -> None:
        requested_norm = _norm(requested)
        recorded_norm = _norm(recorded)
        if not requested_norm:
            findings.append(_block(f"APPROVAL_BINDING_{field_name.upper()}_REQUIRED", f"Approval binding requires {field_name}.", field=field_name))
            return
        if _is_wildcard(recorded_norm):
            findings.append(_block("APPROVAL_BINDING_GENERIC_SCOPE_BLOCKED", "Generic or wildcard approval scope cannot authorize sensitive operations.", field=field_name, recorded=recorded_norm))
            return
        if recorded_norm != requested_norm:
            findings.append(_block(f"APPROVAL_BINDING_{field_name.upper()}_MISMATCH", f"Approval {field_name} does not match requested {field_name}.", field=field_name, requested=requested_norm, recorded=recorded_norm))

    def _check_role(self, request: ApprovalBindingRequest, scope: dict[str, Any], requirements: dict[str, Any], findings: list[Finding]) -> None:
        required_role = _norm(requirements.get("requires_rbac_role"))
        recorded_role = _norm(_scope_value(scope, "role_at_decision", None))
        requested_role = _norm(request.role_at_decision)
        if required_role and not recorded_role:
            findings.append(_block("APPROVAL_BINDING_ROLE_REQUIRED", "Sensitive approval binding requires role_at_decision in approval scope or metadata.", required_role=required_role))
            return
        if recorded_role and not requested_role:
            findings.append(_block("APPROVAL_BINDING_ROLE_AT_DECISION_REQUIRED", "Approval binding request requires role_at_decision when the record is role-bound.", recorded_role=recorded_role))
            return
        if required_role and recorded_role != required_role:
            findings.append(_block("APPROVAL_BINDING_REQUIRED_ROLE_MISMATCH", "Approval role_at_decision does not satisfy the sensitive action required role.", required_role=required_role, recorded_role=recorded_role))
        if recorded_role and requested_role and recorded_role != requested_role:
            findings.append(_block("APPROVAL_BINDING_ROLE_MISMATCH", "Approval role_at_decision does not match requested role_at_decision.", requested_role=requested_role, recorded_role=recorded_role))

    def _check_action(self, request: ApprovalBindingRequest, scope: dict[str, Any], record: ApprovalRecord, action_entry: dict[str, Any] | None, findings: list[Finding]) -> None:
        requested = _norm(request.action)
        candidates = {_norm(record.action), _norm(scope.get("action")), _norm(scope.get("action_id"))}
        if action_entry:
            action_id = _norm(action_entry.get("action_id"))
            domain_action = action_id.split(".")[-1]
            candidates.update({action_id, domain_action})
        candidates.discard("")
        if not requested:
            findings.append(_block("APPROVAL_BINDING_ACTION_REQUIRED", "Approval binding requires action."))
            return
        if any(_is_wildcard(candidate) for candidate in candidates):
            findings.append(_block("APPROVAL_BINDING_GENERIC_SCOPE_BLOCKED", "Generic or wildcard action scope cannot authorize sensitive operations.", field="action"))
            return
        if requested not in candidates:
            findings.append(_block("APPROVAL_BINDING_ACTION_MISMATCH", "Approval action does not match requested action.", requested=requested, recorded=sorted(candidates)))

    def _check_subject_hash(self, request: ApprovalBindingRequest, scope: dict[str, Any], findings: list[Finding]) -> None:
        recorded_hash = _norm(scope.get("subject_hash"))
        requested_hash = _norm(request.subject_hash or compute_subject_hash(request.subject))
        if recorded_hash and recorded_hash != requested_hash:
            findings.append(_block("APPROVAL_BINDING_SUBJECT_HASH_MISMATCH", "Approval subject_hash does not match requested subject hash.", requested_hash=requested_hash, recorded_hash=recorded_hash))

    def _check_command_binding(self, request: ApprovalBindingRequest, scope: dict[str, Any], requirements: dict[str, Any], findings: list[Finding]) -> None:
        recorded = _norm(scope.get("command_id"))
        requested = _norm(request.command_id)
        if requirements["requires_command_binding"]:
            if not recorded or not requested:
                findings.append(_block("APPROVAL_BINDING_COMMAND_ID_REQUIRED", "Sensitive approval binding requires matching command_id on record and request.", recorded=recorded, requested=requested))
                return
        if recorded and requested and recorded != requested:
            findings.append(_block("APPROVAL_BINDING_COMMAND_ID_MISMATCH", "Approval command_id does not match requested command_id.", requested=requested, recorded=recorded))

    def _check_tool_call_binding(self, request: ApprovalBindingRequest, scope: dict[str, Any], requirements: dict[str, Any], findings: list[Finding]) -> None:
        recorded = _norm(scope.get("tool_call_id"))
        requested = _norm(request.tool_call_id)
        if requirements["requires_tool_call_binding"]:
            if not recorded or not requested:
                findings.append(_block("APPROVAL_BINDING_TOOL_CALL_ID_REQUIRED", "Sensitive approval binding requires matching tool_call_id on record and request.", recorded=recorded, requested=requested))
                return
        if recorded and requested and recorded != requested:
            findings.append(_block("APPROVAL_BINDING_TOOL_CALL_ID_MISMATCH", "Approval tool_call_id does not match requested tool_call_id.", requested=requested, recorded=recorded))

    def _check_generic_scope(self, scope: dict[str, Any], requirements: dict[str, Any], findings: list[Finding]) -> None:
        if not any(requirements.values()):
            return
        for field_name in ("actor_id", "tool_id", "action", "subject"):
            value = _norm(scope.get(field_name))
            if _is_wildcard(value):
                findings.append(_block("APPROVAL_BINDING_GENERIC_SCOPE_BLOCKED", "Generic or wildcard approval scope cannot authorize sensitive operations.", field=field_name, recorded=value))

    def _resolve_sensitive_action(self, tool_id: str, action: str) -> dict[str, Any] | None:
        catalog = _load_json(self.catalog_path)
        requested_action = _norm(action)
        requested_tool = _norm(tool_id)
        for entry in catalog.get("actions", []):
            if not isinstance(entry, dict):
                continue
            action_id = _norm(entry.get("action_id"))
            action_tail = action_id.split(".")[-1]
            tool_ids = {_norm(item) for item in entry.get("tool_ids", [])}
            if requested_action == action_id:
                return entry
            if requested_tool and requested_tool in tool_ids and requested_action in {action_id, action_tail}:
                return entry
        return None

    def _result(self, ok: bool, findings: list[Finding], summary: dict[str, Any]) -> CommandResult:
        return CommandResult(
            command=APPROVAL_BINDING_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Approval binding validation passed." if ok else "Approval binding validation blocked the request.",
            data={"summary": summary},
            findings=findings,
        )


def compute_subject_hash(subject: str) -> str:
    normalized = str(subject or "").replace("\\", "/").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _binding_scope(record: ApprovalRecord) -> dict[str, Any]:
    scope = dict(record.scope or {})
    metadata = dict(record.metadata or {})
    scope.setdefault("approval_id", record.approval_id)
    scope.setdefault("actor_id", metadata.get("actor_id") or record.actor)
    scope.setdefault("tool_id", metadata.get("tool_id") or record.tool_id)
    scope.setdefault("action", metadata.get("action") or record.action)
    scope.setdefault("subject", metadata.get("subject") or record.subject)
    for key in ("role_at_decision", "command_id", "tool_call_id", "subject_hash", "interface"):
        if key not in scope and key in metadata:
            scope[key] = metadata[key]
    return scope


def _requirements(entry: dict[str, Any] | None) -> dict[str, Any]:
    if not entry:
        return {
            "requires_approval": False,
            "requires_rbac_role": "",
            "requires_command_binding": False,
            "requires_tool_call_binding": False,
        }
    return {
        "requires_approval": bool(entry.get("requires_approval")),
        "requires_rbac_role": str(entry.get("requires_rbac_role", "")).strip(),
        "requires_command_binding": bool(entry.get("requires_command_binding")),
        "requires_tool_call_binding": bool(entry.get("requires_tool_call_binding")),
    }


def _scope_value(scope: dict[str, Any], key: str, fallback: Any) -> Any:
    value = scope.get(key)
    return fallback if value in {None, ""} else value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _norm(value: Any) -> str:
    return str(value or "").strip()


def _is_wildcard(value: str) -> bool:
    return value in {"*", "all", "global", "any"}


def _block(finding_id: str, message: str, **metadata: Any) -> Finding:
    return Finding(id=finding_id, message=message, severity=Severity.BLOCK, metadata=metadata)
