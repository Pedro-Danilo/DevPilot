from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from devpilot_core.agents.role_bindings import AgentRoleBindingCatalog


CATALOG_PATH = Path(".devpilot/gsdlc/step_action_catalog.json")
MIP_REGISTRY_PATH = Path(".devpilot/gsdlc/mip_workflow_registry.json")
RBAC_CATALOG_PATH = Path(".devpilot/identity/server_rbac_policy_catalog.json")
API_ROUTE_REGISTRY_PATH = Path(".devpilot/interfaces/api_route_contract_registry.json")
UI_ROUTE_REGISTRY_PATH = Path(".devpilot/interfaces/ui_route_contract_registry.json")
ACTION_KINDS = (
    "MANUAL",
    "PASTE",
    "UPLOAD_IMPORT",
    "EXTERNAL_EDITOR",
    "AGENT",
    "RAG",
    "TYPED_OPERATION",
)


class StepActionAdvisorError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StepActionAdvisorError(f"cannot load step action authority {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise StepActionAdvisorError(f"step action authority must be a JSON object: {path}")
    return raw


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _normalized(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


@dataclass(frozen=True)
class AdvisorContext:
    workspace_id: str
    current_step: str
    effective_roles: tuple[str, ...]
    workspace_scopes: tuple[str, ...]
    artifact_readiness: str = "UNKNOWN"
    miasi_gate_status: str = "UNKNOWN"
    provider_status: str = "NOT_AVAILABLE"
    budget_status: str = "NOT_APPLICABLE"
    active_project_context: bool = True

    @classmethod
    def from_payload(
        cls,
        *,
        workspace_id: str,
        current_step: str,
        effective_roles: Sequence[str],
        workspace_scopes: Sequence[str],
        project_status: Mapping[str, Any] | None = None,
    ) -> "AdvisorContext":
        status = dict(project_status or {})
        artifact = status.get("artifact_readiness") if isinstance(status.get("artifact_readiness"), Mapping) else {}
        miasi = status.get("miasi") if isinstance(status.get("miasi"), Mapping) else {}
        model_budget = status.get("model_budget") if isinstance(status.get("model_budget"), Mapping) else {}
        provider = status.get("provider") if isinstance(status.get("provider"), Mapping) else {}
        return cls(
            workspace_id=str(workspace_id).strip(),
            current_step=str(current_step).strip(),
            effective_roles=_normalized(effective_roles),
            workspace_scopes=_normalized(workspace_scopes),
            artifact_readiness=str(artifact.get("status") or "UNKNOWN").upper(),
            miasi_gate_status=str(miasi.get("gate_status") or "UNKNOWN").upper(),
            provider_status=str(provider.get("status") or model_budget.get("provider_status") or "NOT_AVAILABLE").upper(),
            budget_status=str(model_budget.get("status") or "NOT_APPLICABLE").upper(),
            active_project_context=bool(workspace_id and str(workspace_id).lower() != "unknown"),
        )


@dataclass(frozen=True)
class DisabledReason:
    code: str
    message: str
    authority: str

    def to_payload(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "authority": self.authority}


@dataclass(frozen=True)
class PrerequisiteStatus:
    prerequisite_id: str
    satisfied: bool
    reason: str

    def to_payload(self) -> dict[str, Any]:
        return {"prerequisite_id": self.prerequisite_id, "satisfied": self.satisfied, "reason": self.reason}


@dataclass(frozen=True)
class StepActionCard:
    action_id: str
    kind: str
    label: str
    purpose: str
    availability: str
    executable: bool
    disabled_reasons: tuple[DisabledReason, ...]
    prerequisites: tuple[PrerequisiteStatus, ...]
    required_roles: tuple[str, ...]
    effective_roles: tuple[str, ...]
    risk: Mapping[str, Any]
    side_effects: tuple[str, ...]
    approval_required: bool
    network_required: bool
    external_api_required: bool
    cost: Mapping[str, Any]
    tokens: Mapping[str, Any]
    rank: int
    recommended: bool
    navigation_target: str | None
    configuration_target: str | None
    typed_operation_id: str | None
    api_route_id: str | None
    source_refs: tuple[str, ...]
    agent_descriptor: Mapping[str, Any] | None

    def to_payload(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "kind": self.kind,
            "label": self.label,
            "purpose": self.purpose,
            "availability": self.availability,
            "executable": self.executable,
            "disabled_reasons": [row.to_payload() for row in self.disabled_reasons],
            "prerequisites": [row.to_payload() for row in self.prerequisites],
            "required_roles": list(self.required_roles),
            "effective_roles": list(self.effective_roles),
            "risk": dict(self.risk),
            "side_effects": list(self.side_effects),
            "approval_required": self.approval_required,
            "network_required": self.network_required,
            "external_api_required": self.external_api_required,
            "cost": dict(self.cost),
            "tokens": dict(self.tokens),
            "rank": self.rank,
            "recommended": self.recommended,
            "navigation_target": self.navigation_target,
            "configuration_target": self.configuration_target,
            "typed_operation_id": self.typed_operation_id,
            "api_route_id": self.api_route_id,
            "source_refs": list(self.source_refs),
            "agent_descriptor": None if self.agent_descriptor is None else dict(self.agent_descriptor),
        }


@dataclass(frozen=True)
class AdvisorDecision:
    workspace_id: str
    current_step: str
    status: str
    recommended_action_id: str | None
    actions: tuple[StepActionCard, ...]
    decision_fingerprint: str
    authority: Mapping[str, Any]
    safety: Mapping[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "current_step": self.current_step,
            "status": self.status,
            "recommended_action_id": self.recommended_action_id,
            "actions": [row.to_payload() for row in self.actions],
            "decision_fingerprint": self.decision_fingerprint,
            "authority": dict(self.authority),
            "safety": dict(self.safety),
        }


class StepActionCatalog:
    """Machine-readable catalog plus deterministic authority cross-checks.

    The catalog describes candidates. It never grants capability. A candidate
    becomes executable only when the current server RBAC/API route contracts and
    GSDLC policy all permit it for the supplied authenticated context.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.path = self.root / CATALOG_PATH
        self.payload = _load_json(self.path)
        self.mip = _load_json(self.root / MIP_REGISTRY_PATH)
        self.rbac = _load_json(self.root / RBAC_CATALOG_PATH)
        self.api_routes = _load_json(self.root / API_ROUTE_REGISTRY_PATH)
        self.ui_routes = _load_json(self.root / UI_ROUTE_REGISTRY_PATH)
        self._step_map = {str(row.get("current_step")): row for row in self.payload.get("steps", [])}
        self._rbac_routes = {str(row.get("route_id")): row for row in self.rbac.get("route_policies", [])}
        self._api_route_map = {str(row.get("route_id")): row for row in self.api_routes.get("routes", [])}

    def validate(self) -> dict[str, Any]:
        issues: list[dict[str, str]] = []
        kinds = tuple(self.payload.get("action_kinds", []))
        if set(kinds) != set(ACTION_KINDS):
            issues.append({"code": "ACTION_KIND_SET_MISMATCH", "message": "Catalog action kinds do not match the GSDLC-05-D contract."})
        mip_steps = [str(row.get("current_step")) for row in self.mip.get("phases", [])]
        catalog_steps = list(self._step_map)
        missing = sorted(set(mip_steps) - set(catalog_steps))
        extra = sorted(set(catalog_steps) - set(mip_steps))
        if missing:
            issues.append({"code": "STEP_COVERAGE_MISSING", "message": ",".join(missing)})
        if extra:
            issues.append({"code": "STEP_COVERAGE_EXTRA", "message": ",".join(extra)})
        seen: set[str] = set()
        route_refs: set[str] = set()
        for step, row in self._step_map.items():
            action_kinds = {str(action.get("kind")) for action in row.get("actions", [])}
            if not set(ACTION_KINDS).issubset(action_kinds):
                issues.append({"code": "STEP_ACTION_KIND_COVERAGE", "message": step})
            for action in row.get("actions", []):
                action_id = str(action.get("action_id") or "")
                if not action_id or action_id in seen:
                    issues.append({"code": "ACTION_ID_DUPLICATE_OR_EMPTY", "message": action_id or step})
                seen.add(action_id)
                route_id = str(action.get("api_route_id") or "")
                if route_id:
                    route_refs.add(route_id)
                    if route_id not in self._rbac_routes:
                        issues.append({"code": "RBAC_ROUTE_MISSING", "message": route_id})
                    if route_id not in self._api_route_map:
                        issues.append({"code": "API_ROUTE_MISSING", "message": route_id})
        return {
            "status": "PASS" if not issues else "BLOCK",
            "mip_steps_total": len(mip_steps),
            "catalog_steps_total": len(catalog_steps),
            "actions_total": len(seen),
            "referenced_api_routes_total": len(route_refs),
            "missing_steps": missing,
            "extra_steps": extra,
            "issues": issues,
            "catalog_sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(),
            "advisor_grants_capability": False,
            "server_policy_authoritative": True,
        }

    def step(self, current_step: str) -> Mapping[str, Any] | None:
        return self._step_map.get(str(current_step).strip())

    def route_authority(self, route_id: str | None) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None]:
        if not route_id:
            return None, None
        return self._rbac_routes.get(route_id), self._api_route_map.get(route_id)


class ExecutionModeAdvisor:
    """Deterministically rank valid routes for one current Guided SDLC step."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.catalog = StepActionCatalog(self.root)
        self.agent_bindings = AgentRoleBindingCatalog(self.root)

    def advise(self, context: AdvisorContext) -> AdvisorDecision:
        step = self.catalog.step(context.current_step)
        authority = self.catalog.validate()
        if authority["status"] != "PASS" or step is None:
            payload = {
                "workspace_id": context.workspace_id,
                "current_step": context.current_step,
                "status": "BLOCK",
                "recommended_action_id": None,
                "actions": [],
                "authority": authority,
                "safety": self._safety(),
            }
            return AdvisorDecision(
                workspace_id=context.workspace_id,
                current_step=context.current_step,
                status="BLOCK",
                recommended_action_id=None,
                actions=(),
                decision_fingerprint=_canonical_hash(payload),
                authority=authority,
                safety=self._safety(),
            )

        cards = [self._card(step, action, context) for action in step.get("actions", [])]
        cards.sort(key=lambda row: (row.rank, row.action_id))
        recommended_id = next((row.action_id for row in cards if row.availability == "AVAILABLE"), None)
        normalized_cards = tuple(
            StepActionCard(**{**row.__dict__, "recommended": row.action_id == recommended_id}) for row in cards
        )
        status = "PASS" if recommended_id else "BLOCK"
        payload = {
            "workspace_id": context.workspace_id,
            "current_step": context.current_step,
            "status": status,
            "recommended_action_id": recommended_id,
            "actions": [row.to_payload() for row in normalized_cards],
            "authority": authority,
            "safety": self._safety(),
        }
        return AdvisorDecision(
            workspace_id=context.workspace_id,
            current_step=context.current_step,
            status=status,
            recommended_action_id=recommended_id,
            actions=normalized_cards,
            decision_fingerprint=_canonical_hash(payload),
            authority=authority,
            safety=self._safety(),
        )

    def _card(self, step: Mapping[str, Any], action: Mapping[str, Any], context: AdvisorContext) -> StepActionCard:
        reasons: list[DisabledReason] = []
        prerequisites = [self._prerequisite(item, context) for item in action.get("prerequisites", [])]
        reasons.extend(
            DisabledReason("PREREQUISITE_NOT_SATISFIED", row.reason, row.prerequisite_id)
            for row in prerequisites
            if not row.satisfied
        )
        route_id = str(action.get("api_route_id") or "") or None
        rbac_policy, api_contract = self.catalog.route_authority(route_id)
        required_roles: tuple[str, ...] = ()
        if route_id:
            if rbac_policy is None or api_contract is None:
                reasons.append(DisabledReason("SERVER_ROUTE_AUTHORITY_MISSING", f"{route_id} is not present in both API and RBAC registries.", route_id))
            else:
                required_roles = _normalized(rbac_policy.get("allowed_roles", []))
                if required_roles and not set(context.effective_roles).intersection(required_roles):
                    reasons.append(DisabledReason("RBAC_ROLE_DENY", "Authenticated role is not allowed by the target server route policy.", route_id))
                if bool(rbac_policy.get("workspace_scope_required")) and context.workspace_id not in set(context.workspace_scopes):
                    reasons.append(DisabledReason("RBAC_WORKSPACE_SCOPE_DENY", "Authenticated principal does not hold the target workspace scope.", route_id))
                if bool(api_contract.get("external_api_allowed")):
                    reasons.append(DisabledReason("EXTERNAL_API_ROUTE_FORBIDDEN", "GSDLC-05-D never recommends an external-API action as executable.", route_id))
                if bool(api_contract.get("remote_execution_allowed")):
                    reasons.append(DisabledReason("REMOTE_ROUTE_FORBIDDEN", "GSDLC-05-D never recommends remote execution.", route_id))

        forced = str((action.get("policy") or {}).get("forced_unavailable_reason") or "")
        if forced:
            reasons.append(DisabledReason(forced, self._forced_message(forced), str((action.get("policy") or {}).get("server_authority") or "GSDLC-05")))
        if bool(action.get("provider_required")) and context.provider_status not in {"AVAILABLE", "READY", "PASS"}:
            reasons.append(DisabledReason("PROVIDER_UNAVAILABLE", f"Provider/model route status is {context.provider_status}; advisor does not synthesize provider availability.", "ProjectStatus.model_budget/provider"))
        if bool(action.get("budget_required")) and context.budget_status in {"EXHAUSTED", "BLOCK", "BLOCKED", "DENIED"}:
            reasons.append(DisabledReason("BUDGET_EXHAUSTED", f"Model budget status is {context.budget_status}.", "ProjectStatus.model_budget"))
        if action.get("kind") in {"AGENT", "RAG"} and context.miasi_gate_status == "BLOCK":
            reasons.append(DisabledReason("MIASI_GATE_BLOCK", "MIASI gate is BLOCK; agentic routes cannot be executable.", "MIASIApplicabilityEvaluator"))
        # Artifact readiness is an input to availability, not a UI-derived hint.
        # Authoring/import modes remain available to remediate missing artifacts,
        # while validation/execute typed operations fail closed until some artifact
        # state is materialized by the server projection.
        if action.get("kind") == "TYPED_OPERATION" and context.artifact_readiness == "UNKNOWN":
            reasons.append(DisabledReason("ARTIFACT_STATE_UNKNOWN", "Typed operations require a materialized artifact-readiness state; author/import actions remain available for remediation.", "ProjectStatus.artifact_readiness"))

        deduped: list[DisabledReason] = []
        seen: set[tuple[str, str]] = set()
        for reason in reasons:
            key = (reason.code, reason.authority)
            if key not in seen:
                seen.add(key)
                deduped.append(reason)
        availability = "AVAILABLE" if not deduped else "UNAVAILABLE"
        # No unavailable card exposes an executable navigation target. A separate
        # configuration target may be shown to explain how to satisfy a future prerequisite.
        navigation_target = (str(action.get("ui_target") or "") or None) if availability == "AVAILABLE" else None
        return StepActionCard(
            action_id=str(action["action_id"]),
            kind=str(action["kind"]),
            label=str(action["label"]),
            purpose=str(action["purpose"]),
            availability=availability,
            executable=availability == "AVAILABLE",
            disabled_reasons=tuple(deduped),
            prerequisites=tuple(prerequisites),
            required_roles=required_roles,
            effective_roles=context.effective_roles,
            risk=dict(action.get("risk") or {}),
            side_effects=tuple(str(value) for value in action.get("side_effects", [])),
            approval_required=bool(action.get("approval_required")),
            network_required=bool(action.get("network_required")),
            external_api_required=bool(action.get("external_api_required")),
            cost=dict(action.get("cost") or {}),
            tokens=dict(action.get("tokens") or {}),
            rank=int(action.get("base_rank", 999)),
            recommended=False,
            navigation_target=navigation_target,
            configuration_target=str(action.get("configuration_target") or "") or None,
            typed_operation_id=str(action.get("typed_operation_id") or "") or None,
            api_route_id=route_id,
            source_refs=_normalized(step.get("source_refs", [])),
            agent_descriptor=self.agent_bindings.descriptor_for_step(context.current_step) if str(action.get("kind")) == "AGENT" else None,
        )

    @staticmethod
    def _prerequisite(prerequisite_id: str, context: AdvisorContext) -> PrerequisiteStatus:
        item = str(prerequisite_id)
        if item == "active-project-context":
            ok = context.active_project_context
            return PrerequisiteStatus(item, ok, "active project context is available" if ok else "active project context is missing")
        if item.startswith("current-step:"):
            expected = item.split(":", 1)[1]
            ok = expected == context.current_step
            return PrerequisiteStatus(item, ok, "current step matches catalog binding" if ok else f"current step is {context.current_step}")
        if item == "miasi-gate-pass":
            ok = context.miasi_gate_status == "PASS"
            return PrerequisiteStatus(item, ok, f"MIASI gate is {context.miasi_gate_status}")
        if item == "provider-route-authorized":
            ok = context.provider_status in {"AVAILABLE", "READY", "PASS"}
            return PrerequisiteStatus(item, ok, f"provider status is {context.provider_status}")
        if item == "budget-available":
            ok = context.budget_status not in {"EXHAUSTED", "BLOCK", "BLOCKED", "DENIED"}
            return PrerequisiteStatus(item, ok, f"budget status is {context.budget_status}")
        if item == "registered-quality-job":
            # Advisor cannot assert a concrete job id from Project Status. The card
            # remains descriptive unless the target route is later supplied a job.
            return PrerequisiteStatus(item, True, "quality job selection is deferred to the governed /quality surface")
        if item in {"artifact-profile-supports-manual", "artifact-profile-supports-import", "external-edit-reconciliation-required", "rag-card-ready"}:
            if item == "rag-card-ready":
                ok = context.miasi_gate_status == "PASS"
                return PrerequisiteStatus(item, ok, "RAG readiness is represented by the MIASI gate in GSDLC-05-D")
            return PrerequisiteStatus(item, True, "bound by the current step artifact profile/workbench contract")
        return PrerequisiteStatus(item, False, "unknown prerequisite fails closed")

    @staticmethod
    def _forced_message(code: str) -> str:
        if code == "GSDLC_05_AGENT_EXECUTION_OUT_OF_SCOPE":
            return "AGENT remains visible but unavailable until GSDLC-06 authorizes a real governed route."
        if code == "GSDLC_05_RAG_EXECUTION_OUT_OF_SCOPE":
            return "RAG remains visible but unavailable until GSDLC-07 authorizes a real governed route."
        return "Action is disabled by the current GSDLC policy."

    @staticmethod
    def _safety() -> dict[str, Any]:
        return {
            "advisor_grants_capability": False,
            "server_policy_authoritative": True,
            "agent_execution_enabled": False,
            "rag_execution_enabled": False,
            "network_used": False,
            "external_api_used": False,
            "model_execution_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
        }
