from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.catalog import ModelCapabilityCatalog
from devpilot_core.modeling.provider_credentials import (
    CredentialResolutionError,
    ProviderCredentialReference,
    CredentialReferenceType,
    auth_adapter_for,
)
from devpilot_core.modeling.providers import ProviderRegistry
from devpilot_core.policy.secrets import redact_sensitive_data


DEFAULT_POLICY_PATH = Path(".devpilot/modeling/external_provider_enablement_policy.json")
DEFAULT_STATE_PATH = Path(".devpilot/runtime/provider_enablement/state.json")
DEFAULT_AUDIT_PATH = Path(".devpilot/runtime/provider_enablement/audit.jsonl")

REQUIRED_GATE_IDS = (
    "provider_model_route",
    "region",
    "auth",
    "terms_billing_privacy",
    "data_classes",
    "budget",
    "health_fallback",
    "logging_redaction",
    "kill_switch_rollback",
    "eval_threshold",
    "rbac",
    "freshness_ttl",
)
REQUIRED_NOTICE_IDS = ("privacy", "terms", "cost", "data_class")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class EnablementGateReport:
    provider_id: str
    access_route_id: str
    evidence_observed_at: str
    evidence_expires_at: str
    gates: dict[str, bool]
    evidence_refs: tuple[str, ...] = ()

    @property
    def missing_gates(self) -> tuple[str, ...]:
        return tuple(gate for gate in REQUIRED_GATE_IDS if self.gates.get(gate) is not True)

    def freshness_valid(self, *, now: datetime | None = None) -> bool:
        reference = now or _utc_now()
        try:
            return _parse_iso(self.evidence_observed_at) <= reference < _parse_iso(self.evidence_expires_at)
        except (TypeError, ValueError):
            return False

    def to_dict(self, *, now: datetime | None = None) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "access_route_id": self.access_route_id,
            "required_gates": list(REQUIRED_GATE_IDS),
            "gates": {gate: bool(self.gates.get(gate)) for gate in REQUIRED_GATE_IDS},
            "missing_gates": list(self.missing_gates),
            "evidence_observed_at": self.evidence_observed_at,
            "evidence_expires_at": self.evidence_expires_at,
            "freshness_valid": self.freshness_valid(now=now),
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class ProviderEnablementRequest:
    provider_id: str
    access_route_id: str
    workspace_id: str
    credential_reference: ProviderCredentialReference
    gate_report: EnablementGateReport
    notices_acknowledged: tuple[str, ...]
    budget_limit_usd: float
    approval_id: str | None = None
    requested_mode: str = "fake"
    reason: str = "External provider enablement request"

    def safe_dict(self, *, now: datetime | None = None) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "access_route_id": self.access_route_id,
            "workspace_id": self.workspace_id,
            "credential_reference": self.credential_reference.to_dict(),
            "gate_report": self.gate_report.to_dict(now=now),
            "notices_acknowledged": list(self.notices_acknowledged),
            "budget_limit_usd": self.budget_limit_usd,
            "approval_id": self.approval_id,
            "requested_mode": self.requested_mode,
            "reason": self.reason,
            "raw_secret_present": False,
        }


@dataclass(frozen=True)
class FakeConnectivityResponse:
    ok: bool
    status_code: int
    provider_message: str = "ok"
    models_seen: int = 1


class ProviderEnablementStore:
    def __init__(self, root: Path, *, state_path: Path = DEFAULT_STATE_PATH, audit_path: Path = DEFAULT_AUDIT_PATH) -> None:
        self.root = root.resolve()
        self.state_path = self.root / state_path
        self.audit_path = self.root / audit_path

    def load(self) -> dict[str, Any]:
        if not self.state_path.is_file():
            return {"schema_id": "devpilot.external-provider-enablement-state.v1", "providers": {}, "runtime_ephemeral": True}
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return {"schema_id": "devpilot.external-provider-enablement-state.v1", "providers": {}, "runtime_ephemeral": True, "state_corrupt": True}
        if not isinstance(payload, dict) or not isinstance(payload.get("providers"), dict):
            return {"schema_id": "devpilot.external-provider-enablement-state.v1", "providers": {}, "runtime_ephemeral": True, "state_corrupt": True}
        return payload

    def write_provider(self, provider_id: str, state: dict[str, Any], *, event: str) -> dict[str, Any]:
        payload = self.load()
        safe_state = redact_sensitive_data(dict(state))
        # Preserve machine-readable safety booleans after structural redaction.
        # Secret values are never admitted to ``state``; credential references contain
        # names only.  The generic redactor intentionally treats keys containing
        # ``secret`` as sensitive, so reassert the explicit no-secret invariant.
        if isinstance(safe_state, dict):
            safe_state["raw_secret_present"] = False
            credential_reference = safe_state.get("credential_reference")
            if isinstance(credential_reference, dict):
                credential_reference["raw_secret_present"] = False
        payload.setdefault("providers", {})[provider_id] = safe_state
        payload["runtime_ephemeral"] = True
        payload["updated_at"] = _iso(_utc_now())
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=self.state_path.parent, delete=False) as tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
            temp_name = tmp.name
        os.replace(temp_name, self.state_path)
        self._append_audit({"event": event, "provider_id": provider_id, "state": state, "at": payload["updated_at"]})
        return payload["providers"][provider_id]

    def _append_audit(self, event: dict[str, Any]) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        safe = redact_sensitive_data(event)
        with self.audit_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(safe, sort_keys=True, ensure_ascii=True) + "\n")


class ExternalProviderEnablementService:
    """GSDLC-06-C external provider credential/enablement authority.

    Versioned provider config stays disabled-by-default.  Runtime enablement is
    stored separately, never includes raw credential values, and remains unable
    to use real external network unless a later provider-specific policy opts in.
    """

    def __init__(self, root: Path, *, policy_path: Path = DEFAULT_POLICY_PATH, store: ProviderEnablementStore | None = None) -> None:
        self.root = root.resolve()
        self.policy_path = self.root / policy_path
        self.policy = self._load_policy()
        self.store = store or ProviderEnablementStore(self.root)

    def _load_policy(self) -> dict[str, Any]:
        if not self.policy_path.is_file():
            return {"schema_id": "devpilot.external-provider-enablement-policy.v1", "defaults": {"external_api_disabled_by_default": True, "network_disabled_by_default": True, "real_network_supported": False}, "providers": []}
        payload = json.loads(self.policy_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("external provider enablement policy must be an object")
        return payload

    def status(self) -> CommandResult:
        registry = ProviderRegistry.load(self.root, prefer_example=True)
        runtime = self.store.load()
        rows: list[dict[str, Any]] = []
        for provider in registry.providers.values():
            if not provider.external_api:
                continue
            state = dict(runtime.get("providers", {}).get(provider.provider_id, {}))
            rows.append({
                "provider_id": provider.provider_id,
                "versioned_enabled": provider.enabled,
                "configured_enabled": bool(state.get("configured_enabled", False)),
                "runtime_network_enabled": bool(state.get("runtime_network_enabled", False)),
                "revoked": bool(state.get("revoked", False)),
                "credential_reference": state.get("credential_reference"),
                "approval_id": state.get("approval_id"),
                "last_action": state.get("last_action"),
                "raw_secret_present": False,
            })
        return CommandResult(
            command="settings providers enablement status",
            ok=True,
            exit_code=ExitCode.PASS,
            message="External provider enablement state projected without secrets.",
            data={"summary": {"external_providers_total": len(rows), "runtime_network_enabled_total": sum(1 for row in rows if row["runtime_network_enabled"]), "secrets_redacted": True, "runtime_ephemeral": True}, "providers": rows},
            findings=[Finding("PROVIDER_ENABLEMENT_STATUS_PASS", "External provider enablement state is redacted and runtime-only.", Severity.INFO)],
        )

    def plan(self, request: ProviderEnablementRequest, *, now: datetime | None = None) -> CommandResult:
        reference_time = now or _utc_now()
        findings: list[Finding] = []
        provider = ProviderRegistry.load(self.root, prefer_example=True).get(request.provider_id)
        route = ModelCapabilityCatalog(self.root).access_route(request.access_route_id)
        supported = self._provider_policy(request.provider_id)
        if provider is None or not provider.external_api:
            findings.append(Finding("PROVIDER_ENABLEMENT_EXTERNAL_PROVIDER_REQUIRED", "Enablement target must be a registered external API provider.", Severity.BLOCK))
        if provider is not None and provider.enabled:
            findings.append(Finding("PROVIDER_ENABLEMENT_VERSIONED_CONFIG_MUST_STAY_DISABLED", "Versioned provider configuration must remain disabled; runtime enablement is separate.", Severity.BLOCK))
        catalog_provider_id = str((supported or {}).get("catalog_provider_id") or request.provider_id)
        if route is None or not route.external_api or route.provider_id != catalog_provider_id:
            findings.append(Finding("PROVIDER_ENABLEMENT_ROUTE_MISMATCH", "Provider/access-route binding is invalid or non-external.", Severity.BLOCK, metadata={"expected_catalog_provider_id": catalog_provider_id}))
        if route is not None and route.locality.value == "consumer-session":
            findings.append(Finding("PROVIDER_ENABLEMENT_CONSUMER_SESSION_BLOCK", "Consumer browser/session routes are unsupported.", Severity.BLOCK))
        if supported is None:
            findings.append(Finding("PROVIDER_ENABLEMENT_PROVIDER_POLICY_MISSING", "Provider-specific enablement policy entry is missing.", Severity.BLOCK))
        elif request.access_route_id not in set(supported.get("allowed_access_routes", [])):
            findings.append(Finding("PROVIDER_ENABLEMENT_ROUTE_NOT_ALLOWLISTED", "Access route is not allowlisted for this provider policy.", Severity.BLOCK))
        credential_errors = request.credential_reference.validate()
        if credential_errors:
            findings.append(Finding("PROVIDER_CREDENTIAL_REFERENCE_INVALID", "Credential reference failed structural validation.", Severity.BLOCK, metadata={"errors": list(credential_errors)}))
        if provider is not None and request.credential_reference.provider_id != provider.provider_id:
            findings.append(Finding("PROVIDER_CREDENTIAL_PROVIDER_MISMATCH", "Credential reference provider does not match enablement target.", Severity.BLOCK))
        if route is not None and request.credential_reference.auth_adapter_id != route.auth_adapter_id:
            findings.append(Finding("PROVIDER_CREDENTIAL_AUTH_ADAPTER_MISMATCH", "Credential auth adapter does not match route contract.", Severity.BLOCK))
        if request.gate_report.provider_id != request.provider_id or request.gate_report.access_route_id != request.access_route_id:
            findings.append(Finding("PROVIDER_ENABLEMENT_GATE_SCOPE_MISMATCH", "ADR gate report does not bind the requested provider/route.", Severity.BLOCK))
        if request.gate_report.missing_gates:
            findings.append(Finding("PROVIDER_ENABLEMENT_ADR_GATES_INCOMPLETE", "Provider-specific ADR has unresolved required gates.", Severity.BLOCK, metadata={"missing_gates": list(request.gate_report.missing_gates)}))
        if not request.gate_report.freshness_valid(now=reference_time):
            findings.append(Finding("PROVIDER_ENABLEMENT_FRESHNESS_EXPIRED", "Provider evidence freshness TTL is missing or expired.", Severity.BLOCK))
        missing_notices = sorted(set(REQUIRED_NOTICE_IDS) - set(request.notices_acknowledged))
        if missing_notices:
            findings.append(Finding("PROVIDER_ENABLEMENT_NOTICE_ACK_REQUIRED", "Privacy/terms/cost/data-class notices must be acknowledged before enablement.", Severity.BLOCK, metadata={"missing_notices": missing_notices}))
        if request.budget_limit_usd <= 0:
            findings.append(Finding("PROVIDER_ENABLEMENT_BUDGET_REQUIRED", "A positive bounded budget is required before external provider enablement.", Severity.BLOCK))
        if request.requested_mode not in {"fake", "real"}:
            findings.append(Finding("PROVIDER_ENABLEMENT_MODE_INVALID", "Enablement mode must be fake or real.", Severity.BLOCK))
        defaults = dict(self.policy.get("defaults") or {})
        if request.requested_mode == "real" and not bool(defaults.get("real_network_supported", False)):
            findings.append(Finding("PROVIDER_ENABLEMENT_REAL_NETWORK_NOT_SUPPORTED", "Real external network is not supported by this 06-C policy baseline.", Severity.BLOCK))
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        safe = request.safe_dict(now=reference_time)
        safe["plan_id"] = "ENABLEMENT-PLAN-" + _stable_hash(safe)[:16].upper()
        safe["approval_required"] = True
        safe["write_performed"] = False
        safe["network_used"] = False
        safe["external_api_used"] = False
        safe["real_runtime_enablement_possible"] = bool(defaults.get("real_network_supported", False)) and request.requested_mode == "real"
        return CommandResult(
            command="settings providers enablement plan",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="External provider enablement plan passed all pre-execution gates." if not blocking else "External provider enablement plan blocked by fail-closed gates.",
            data={"summary": {"provider_id": request.provider_id, "plan_only": True, "write_performed": False, "approval_required": True, "blocking_findings_total": len(blocking), "secrets_redacted": True}, "plan": redact_sensitive_data(safe)},
            findings=findings or [Finding("PROVIDER_ENABLEMENT_PLAN_PASS", "External provider enablement plan passed all 06-C gates.", Severity.INFO)],
        )

    def apply_enable(
        self,
        request: ProviderEnablementRequest,
        *,
        approval: Mapping[str, Any] | None,
        actor_id: str,
        role_at_execution: str,
        now: datetime | None = None,
    ) -> CommandResult:
        plan = self.plan(request, now=now)
        findings = list(plan.findings)
        approval_ok, approval_reason = self._approval_matches(request, approval)
        if not approval_ok:
            findings.append(Finding("PROVIDER_ENABLEMENT_APPROVAL_REQUIRED", "Approved, unexpired, scope-matched approval is required.", Severity.BLOCK, metadata={"reason": approval_reason}))
        if role_at_execution != "owner":
            findings.append(Finding("PROVIDER_ENABLEMENT_RBAC_ROLE_DENY", "Only owner role may apply external provider enablement in 06-C.", Severity.BLOCK, metadata={"role": role_at_execution}))
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        if blocking:
            return CommandResult(
                command="settings providers enablement apply",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="External provider enablement apply was blocked.",
                data={"summary": {"updated": False, "provider_id": request.provider_id, "secrets_redacted": True, "network_used": False, "external_api_used": False}},
                findings=findings,
            )
        defaults = dict(self.policy.get("defaults") or {})
        runtime_network_enabled = request.requested_mode == "real" and bool(defaults.get("real_network_supported", False))
        state = {
            "provider_id": request.provider_id,
            "access_route_id": request.access_route_id,
            "workspace_id": request.workspace_id,
            "configured_enabled": True,
            "runtime_network_enabled": runtime_network_enabled,
            "evaluation_mode": request.requested_mode,
            "credential_reference": request.credential_reference.to_dict(),
            "approval_id": request.approval_id,
            "actor_id": actor_id,
            "role_at_execution": role_at_execution,
            "gate_report_sha256": _stable_hash(request.gate_report.to_dict(now=now)),
            "last_action": "enable",
            "revoked": False,
            "raw_secret_present": False,
        }
        stored = self.store.write_provider(request.provider_id, state, event="provider.enablement.enabled")
        return CommandResult(
            command="settings providers enablement apply",
            ok=True,
            exit_code=ExitCode.PASS,
            message="External provider enablement state persisted without credential value.",
            data={"summary": {"updated": True, "provider_id": request.provider_id, "configured_enabled": True, "runtime_network_enabled": runtime_network_enabled, "secrets_redacted": True, "network_used": False, "external_api_used": False}, "state": stored},
            findings=[Finding("PROVIDER_ENABLEMENT_APPLY_PASS", "Provider enablement was audited and persisted as runtime-only state.", Severity.INFO)],
        )

    def disable(self, *, provider_id: str, actor_id: str, role_at_execution: str, reason: str, revoke: bool = False) -> CommandResult:
        if role_at_execution != "owner":
            return CommandResult(
                command="settings providers enablement revoke" if revoke else "settings providers enablement disable",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Provider disable/revoke blocked by RBAC.",
                data={"summary": {"updated": False, "provider_id": provider_id, "secrets_redacted": True}},
                findings=[Finding("PROVIDER_ENABLEMENT_RBAC_ROLE_DENY", "Only owner role may disable/revoke external provider enablement in 06-C.", Severity.BLOCK)],
            )
        previous = dict(self.store.load().get("providers", {}).get(provider_id, {}))
        if not previous:
            previous = {"provider_id": provider_id}
        state = {
            **previous,
            "configured_enabled": False,
            "runtime_network_enabled": False,
            "credential_reference": None if revoke else previous.get("credential_reference"),
            "approval_id": None if revoke else previous.get("approval_id"),
            "actor_id": actor_id,
            "role_at_execution": role_at_execution,
            "last_action": "revoke" if revoke else "disable",
            "reason": reason,
            "revoked": bool(revoke),
            "raw_secret_present": False,
        }
        stored = self.store.write_provider(provider_id, state, event="provider.enablement.revoked" if revoke else "provider.enablement.disabled")
        return CommandResult(
            command="settings providers enablement revoke" if revoke else "settings providers enablement disable",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Provider credential reference revoked." if revoke else "Provider enablement disabled.",
            data={"summary": {"updated": True, "provider_id": provider_id, "configured_enabled": False, "runtime_network_enabled": False, "revoked": revoke, "secrets_redacted": True}, "state": stored},
            findings=[Finding("PROVIDER_ENABLEMENT_REVOKE_PASS" if revoke else "PROVIDER_ENABLEMENT_DISABLE_PASS", "Provider disable/revoke transition was audited.", Severity.INFO)],
        )

    def connectivity_test(
        self,
        request: ProviderEnablementRequest,
        *,
        transport: Callable[..., FakeConnectivityResponse] | None = None,
        environ: Mapping[str, str] | None = None,
        timeout_seconds: float = 2.0,
        now: datetime | None = None,
    ) -> CommandResult:
        plan = self.plan(request, now=now)
        if not plan.ok:
            return CommandResult(
                command="settings providers connectivity-test",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Connectivity test blocked because enablement gates are incomplete.",
                data={"summary": {"provider_id": request.provider_id, "network_used": False, "external_api_used": False, "secrets_redacted": True}},
                findings=list(plan.findings),
            )
        if transport is None:
            return CommandResult(
                command="settings providers connectivity-test",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Real external connectivity is disabled; no transport was invoked.",
                data={"summary": {"provider_id": request.provider_id, "network_used": False, "external_api_used": False, "secrets_redacted": True}},
                findings=[Finding("PROVIDER_CONNECTIVITY_NETWORK_DISABLED", "06-C PASS does not permit real external network connectivity.", Severity.BLOCK)],
            )
        try:
            adapter = auth_adapter_for(request.credential_reference)
            material = adapter.resolve(request.credential_reference, environ=environ)
            response = transport(
                provider_id=request.provider_id,
                access_route_id=request.access_route_id,
                credential=material,
                timeout_seconds=max(0.05, min(float(timeout_seconds), 5.0)),
            )
        except CredentialResolutionError as exc:
            return CommandResult(
                command="settings providers connectivity-test",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Connectivity test blocked by credential resolution.",
                data={"summary": {"provider_id": request.provider_id, "network_used": False, "external_api_used": False, "secrets_redacted": True, "credential_reference": request.credential_reference.to_dict()}},
                findings=[Finding("PROVIDER_CONNECTIVITY_CREDENTIAL_BLOCK", "Provider credential was missing/invalid without exposing its value.", Severity.BLOCK, metadata={"reason": exc.code})],
            )
        safe_response = {
            "ok": bool(response.ok),
            "status_code": int(response.status_code),
            "models_seen": max(0, min(int(response.models_seen), 100)),
            "provider_message": str(response.provider_message)[:160],
            "credential": material.safe_dict(),
            "transport": "fake-in-process",
            "network_used": False,
            "external_api_used": False,
            "payload_redacted": True,
        }
        ok = response.ok and 200 <= int(response.status_code) < 300
        return CommandResult(
            command="settings providers connectivity-test",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Fake provider connectivity test passed without external network." if ok else "Fake provider connectivity test failed closed.",
            data={"summary": {"provider_id": request.provider_id, "ok": ok, "network_used": False, "external_api_used": False, "secrets_redacted": True}, "result": redact_sensitive_data(safe_response)},
            findings=[Finding("PROVIDER_CONNECTIVITY_FAKE_PASS" if ok else "PROVIDER_CONNECTIVITY_FAKE_BLOCK", "Fake provider connectivity remained bounded and redacted.", Severity.INFO if ok else Severity.BLOCK)],
        )

    def _provider_policy(self, provider_id: str) -> dict[str, Any] | None:
        for item in self.policy.get("providers", []):
            if isinstance(item, dict) and str(item.get("provider_id", "")).strip().lower() == provider_id.strip().lower():
                return item
        return None

    @staticmethod
    def _approval_matches(request: ProviderEnablementRequest, approval: Mapping[str, Any] | None) -> tuple[bool, str]:
        if not approval:
            return False, "approval-missing"
        if approval.get("approval_id") != request.approval_id:
            return False, "approval-id-mismatch"
        if approval.get("status") != "approved":
            return False, "approval-not-approved"
        if approval.get("expired") is True:
            return False, "approval-expired"
        if approval.get("tool_id") != "model.external_provider.enable" or approval.get("action") != "provider.enablement.external":
            return False, "approval-tool-action-mismatch"
        scope = approval.get("scope") or {}
        if scope.get("provider_id") != request.provider_id or scope.get("access_route_id") != request.access_route_id or scope.get("workspace_id") != request.workspace_id:
            return False, "approval-scope-mismatch"
        return True, "approval-valid"


def credential_reference_from_dict(payload: Mapping[str, Any]) -> ProviderCredentialReference:
    ref_type = CredentialReferenceType(str(payload.get("reference_type") or "env"))
    return ProviderCredentialReference(
        provider_id=str(payload.get("provider_id") or ""),
        auth_adapter_id=str(payload.get("auth_adapter_id") or ""),
        reference_type=ref_type,
        reference_name=str(payload.get("reference_name")) if payload.get("reference_name") is not None else None,
        required=bool(payload.get("required", True)),
        source=str(payload.get("source") or "explicit-config"),
    )


def gate_report_from_dict(payload: Mapping[str, Any]) -> EnablementGateReport:
    return EnablementGateReport(
        provider_id=str(payload.get("provider_id") or ""),
        access_route_id=str(payload.get("access_route_id") or ""),
        evidence_observed_at=str(payload.get("evidence_observed_at") or ""),
        evidence_expires_at=str(payload.get("evidence_expires_at") or ""),
        gates={str(key): bool(value) for key, value in dict(payload.get("gates") or {}).items()},
        evidence_refs=tuple(str(value) for value in payload.get("evidence_refs", []) if str(value)),
    )


def enablement_request_from_dict(payload: Mapping[str, Any]) -> ProviderEnablementRequest:
    return ProviderEnablementRequest(
        provider_id=str(payload.get("provider_id") or ""),
        access_route_id=str(payload.get("access_route_id") or ""),
        workspace_id=str(payload.get("workspace_id") or "devpilot-local"),
        credential_reference=credential_reference_from_dict(dict(payload.get("credential_reference") or {})),
        gate_report=gate_report_from_dict(dict(payload.get("gate_report") or {})),
        notices_acknowledged=tuple(str(value) for value in payload.get("notices_acknowledged", []) if str(value)),
        budget_limit_usd=float(payload.get("budget_limit_usd") or 0.0),
        approval_id=str(payload.get("approval_id")) if payload.get("approval_id") else None,
        requested_mode=str(payload.get("requested_mode") or "fake"),
        reason=str(payload.get("reason") or "External provider enablement request"),
    )
