from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import re
from .registry import MiasiRegistryValidator

POLICY_PATH = Path(".devpilot/miasi/applicability_policy.json")
CONTEXT_FILENAME = "miasi_applicability_context.json"


_SECRET_KEY_RE = re.compile(r"(?:password|passwd|secret|token|api[_-]?key|private[_-]?key|authorization|cookie)", re.I)
_SECRET_VALUE_RE = re.compile(r"(?:\bBearer\s+[A-Za-z0-9._~+/=-]{8,}|\bsk-[A-Za-z0-9_-]{12,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)", re.I)

def _secret_paths(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}"
            if _SECRET_KEY_RE.search(str(key)):
                findings.append(child)
            findings.extend(_secret_paths(item, child))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            findings.extend(_secret_paths(item, f"{path}[{index}]"))
    elif isinstance(value, str) and _SECRET_VALUE_RE.search(value):
        findings.append(path)
    return findings


class MIASIApplicabilityError(RuntimeError):
    pass


@dataclass(frozen=True)
class MIASIApplicabilityResult:
    status: str
    gate_status: str
    reason_codes: tuple[str, ...]
    risk_level: str
    project_decision: dict[str, Any]
    feature_decisions: tuple[dict[str, Any], ...]
    required_controls: tuple[dict[str, Any], ...]
    missing_controls: tuple[str, ...]
    policy_binding: dict[str, Any]
    blockers: tuple[dict[str, Any], ...]
    evidence_refs: tuple[str, ...]
    context_source: str
    reevaluation_required: bool
    agent_execution_allowed: bool = False
    rag_execution_allowed: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "gate_status": self.gate_status,
            "reason_codes": list(self.reason_codes),
            "risk_level": self.risk_level,
            "project_decision": dict(self.project_decision),
            "feature_decisions": [dict(row) for row in self.feature_decisions],
            "required_controls": [dict(row) for row in self.required_controls],
            "missing_controls": list(self.missing_controls),
            "policy_binding": dict(self.policy_binding),
            "blockers": [dict(row) for row in self.blockers],
            "evidence_refs": list(self.evidence_refs),
            "context_source": self.context_source,
            "reevaluation_required": self.reevaluation_required,
            "agent_execution_allowed": self.agent_execution_allowed,
            "rag_execution_allowed": self.rag_execution_allowed,
            "execution_reason_code": "GSDLC_06_07_NOT_IMPLEMENTED" if self.gate_status == "PASS" else "MIASI_GATE_INCOMPLETE",
            "network_used": False,
            "external_api_used": False,
            "model_execution_used": False,
            "agents_executed": False,
            "rag_executed": False,
            "source_mutations_performed": False,
        }

    def project_status_blockers(self) -> tuple[dict[str, Any], ...]:
        return tuple({"code": row["code"], "message": row["message"], "source": "MIASI"} for row in self.blockers)


class MIASIApplicabilityEvaluator:
    """Deterministic MIASI project/feature applicability evaluator.

    Inputs are explicit local metadata. The evaluator never invokes an LLM,
    agent, tool, RAG pipeline, network service or managed-project source write.
    Missing/ambiguous high-risk evidence fails closed.
    """

    def __init__(self, root: Path, *, policy_path: Path | str = POLICY_PATH) -> None:
        self.root = Path(root).resolve()
        raw = Path(policy_path)
        self.policy_path = raw if raw.is_absolute() else self.root / raw
        self.policy = self._read_object(self.policy_path, "MIASI applicability policy")
        self._validate_policy_shape()

    def context_path(self, workspace_id: str) -> Path:
        return self.root / "outputs" / "workspaces" / workspace_id / CONTEXT_FILENAME

    def evaluate_workspace(self, workspace_id: str, state_payload: Mapping[str, Any]) -> MIASIApplicabilityResult:
        path = self.context_path(workspace_id)
        if not path.is_file():
            return self._review_required(
                workspace_id=workspace_id,
                reason="MIASI_APPLICABILITY_CONTEXT_MISSING",
                context_source=path.relative_to(self.root).as_posix(),
            )
        try:
            context = self._read_object(path, "MIASI applicability context")
        except MIASIApplicabilityError:
            return self._review_required(
                workspace_id=workspace_id,
                reason="MIASI_APPLICABILITY_CONTEXT_INVALID",
                context_source=path.relative_to(self.root).as_posix(),
            )
        return self.evaluate(context, state_payload=state_payload, context_source=path.relative_to(self.root).as_posix())

    def evaluate(self, context: Mapping[str, Any], *, state_payload: Mapping[str, Any], context_source: str = "in-memory") -> MIASIApplicabilityResult:
        self._validate_context(context)
        reasons: list[str] = []
        blockers: list[dict[str, Any]] = []
        project = self._scope_decision(context.get("project") or {}, scope_id="project")
        features = tuple(
            self._scope_decision(item, scope_id=str(item.get("feature_id") or "feature"))
            for item in context.get("features", [])
            if isinstance(item, Mapping)
        )
        scopes = (project,) + features
        any_ai = any(row["applicable_signal"] for row in scopes)
        all_explicit_non_ai = bool(scopes) and all(row["explicit_non_ai"] for row in scopes)
        if any_ai:
            status = "APPLICABLE"
            reasons.append("MIASI_AI_AGENTIC_SIGNAL_PRESENT")
            if project["explicit_non_ai"] and any(row["applicable_signal"] for row in features):
                reasons.append("MIASI_FEATURE_EVOLUTION_NON_AI_TO_AI")
        elif all_explicit_non_ai:
            status = "NOT_APPLICABLE"
            reasons.append("MIASI_EXPLICIT_NON_AI_DECLARATION")
        else:
            status = "REVIEW_REQUIRED"
            reasons.append("MIASI_APPLICABILITY_AMBIGUOUS")
            blockers.append(self._blocker("MIASI_APPLICABILITY_REVIEW_REQUIRED", "MIASI applicability is ambiguous; explicit project/feature classification is required."))

        risk = self._max_risk(scopes)
        capabilities = {cap for row in scopes for cap in row["capabilities"]}
        required = [] if status == "NOT_APPLICABLE" else list(self.policy["base_required_controls"])
        if "rag" in capabilities:
            required += self.policy["conditional_controls"].get("rag", [])
        if "memory" in capabilities:
            required += self.policy["conditional_controls"].get("memory", [])
        if risk in {"high", "critical"}:
            required += self.policy["conditional_controls"].get("high_risk", [])
        required = list(dict.fromkeys(required))

        artifact_rows = [row for row in state_payload.get("artifacts", []) if isinstance(row, Mapping)]
        artifacts = {str(row.get("artifact_id")): str(row.get("lifecycle")) for row in artifact_rows}
        ready_states = set(self.policy["ready_artifact_lifecycles"])
        controls: list[dict[str, Any]] = []
        missing: list[str] = []
        for kind in required:
            artifact_id = str(self.policy["control_artifact_ids"].get(kind) or "")
            lifecycle = artifacts.get(artifact_id, "MISSING")
            ready = lifecycle in ready_states
            controls.append({"kind": kind, "artifact_id": artifact_id, "lifecycle": lifecycle, "ready": ready})
            if not ready:
                missing.append(kind)
        if status == "APPLICABLE" and missing:
            blockers.append(self._blocker("MIASI_REQUIRED_CONTROL_MISSING", "Required MIASI control artifacts are missing or not approved/frozen: " + ", ".join(missing)))

        policy_binding = self._policy_binding()
        if status == "APPLICABLE" and not policy_binding["ready"]:
            blockers.append(self._blocker("MIASI_POLICY_BINDING_INCOMPLETE", "Required MIASI policy/RBAC/approval semantic bindings are incomplete."))

        review = str(context.get("risk_review_status") or "NOT_REQUIRED")
        if risk == "critical" and self.policy.get("critical_risk_review_required") is True and review != "APPROVED":
            blockers.append(self._blocker("MIASI_CRITICAL_RISK_REVIEW_REQUIRED", "Critical AI/agentic risk requires explicit governed human risk review before advance."))
            reasons.append("MIASI_RISK_ESCALATED_CRITICAL")
        elif risk == "high":
            reasons.append("MIASI_RISK_ESCALATED_HIGH")

        gate_status = "BLOCK" if blockers else "PASS"
        evidence = list(context.get("evidence_refs") or [])
        for row in scopes:
            evidence.extend(row["evidence_refs"])
        evidence.extend(ref["path"] for ref in self.policy.get("source_refs", []))
        return MIASIApplicabilityResult(
            status=status,
            gate_status=gate_status,
            reason_codes=tuple(dict.fromkeys(reasons)),
            risk_level=risk,
            project_decision=project,
            feature_decisions=features,
            required_controls=tuple(controls),
            missing_controls=tuple(missing),
            policy_binding=policy_binding,
            blockers=tuple(blockers),
            evidence_refs=tuple(dict.fromkeys(str(x) for x in evidence if str(x))),
            context_source=context_source,
            reevaluation_required=(status == "REVIEW_REQUIRED" or bool(blockers)),
        )

    def _scope_decision(self, scope: Mapping[str, Any], *, scope_id: str) -> dict[str, Any]:
        declared = scope.get("declared_ai_usage")
        capabilities = tuple(str(x) for x in scope.get("capabilities", []) if str(x))
        applicable_signal = declared is True or bool(capabilities)
        return {
            "scope_id": scope_id,
            "declared_ai_usage": declared,
            "capabilities": list(capabilities),
            "risk_level": str(scope.get("risk_level") or "low"),
            "applicable_signal": applicable_signal,
            "explicit_non_ai": declared is False and not capabilities,
            "evidence_refs": [str(x) for x in scope.get("evidence_refs", []) if str(x)],
        }

    def _max_risk(self, scopes: tuple[dict[str, Any], ...]) -> str:
        order = list(self.policy["risk_order"])
        values = [str(row.get("risk_level") or "low") for row in scopes]
        return max(values or ["low"], key=lambda value: order.index(value) if value in order else len(order))

    def _policy_binding(self) -> dict[str, Any]:
        registry = MiasiRegistryValidator(self.root).validate_all()
        matrix = self._read_object(self.root / ".devpilot/miasi/policy_matrix.json", "MIASI policy matrix")
        rules = {str(row.get("rule_id")) for row in matrix.get("rules", []) if isinstance(row, Mapping)}
        sem = self._read_object(self.root / ".devpilot/miasi/semantic_rules.json", "MIASI semantic rules")
        semantic = {str(row.get("rule_id")): row for row in sem.get("semantic_rules", []) if isinstance(row, Mapping)}
        missing_policy = sorted(set(self.policy["required_policy_rule_ids"]) - rules)
        missing_semantic = sorted(
            rule_id for rule_id in self.policy["required_semantic_rule_ids"]
            if rule_id not in semantic or semantic[rule_id].get("critical") is not True
        )
        return {
            "ready": bool(registry.ok) and not missing_policy and not missing_semantic,
            "registry_validation_ok": bool(registry.ok),
            "missing_policy_rule_ids": missing_policy,
            "missing_semantic_rule_ids": missing_semantic,
            "rbac_server_authority": True,
            "approval_server_authority": True,
        }

    def _review_required(self, *, workspace_id: str, reason: str, context_source: str) -> MIASIApplicabilityResult:
        return MIASIApplicabilityResult(
            status="REVIEW_REQUIRED", gate_status="BLOCK", reason_codes=(reason,), risk_level="medium_high",
            project_decision={"scope_id":"project","declared_ai_usage":None,"capabilities":[],"risk_level":"medium_high","applicable_signal":False,"explicit_non_ai":False,"evidence_refs":[]},
            feature_decisions=(), required_controls=(), missing_controls=(),
            policy_binding={"ready":False,"registry_validation_ok":False,"missing_policy_rule_ids":[],"missing_semantic_rule_ids":[],"rbac_server_authority":True,"approval_server_authority":True},
            blockers=(self._blocker("MIASI_APPLICABILITY_REVIEW_REQUIRED", "MIASI applicability context is unavailable or invalid; fail-closed review is required."),),
            evidence_refs=(), context_source=context_source, reevaluation_required=True,
        )

    def _validate_policy_shape(self) -> None:
        if self.policy.get("schema_id") != "SCHEMA-DEVPL-MIASI-APPLICABILITY-POLICY-V1":
            raise MIASIApplicabilityError("unsupported applicability policy schema")
        if self.policy.get("agent_execution_enabled") is not False or self.policy.get("rag_execution_enabled") is not False:
            raise MIASIApplicabilityError("GSDLC-05 policy cannot enable agent/RAG execution")

    def _validate_context(self, context: Mapping[str, Any]) -> None:
        if context.get("schema_id") != "SCHEMA-DEVPL-MIASI-APPLICABILITY-CONTEXT-V1" or context.get("schema_version") != "1.0":
            raise MIASIApplicabilityError("unsupported MIASI applicability context")
        findings = _secret_paths(context)
        if findings:
            raise MIASIApplicabilityError(f"secret-like material forbidden in applicability context: {findings[:5]}")
        allowed = set(self.policy["capability_catalog"])
        scopes = [context.get("project") or {}] + list(context.get("features") or [])
        for scope in scopes:
            if not isinstance(scope, Mapping):
                raise MIASIApplicabilityError("applicability scopes must be objects")
            unknown = set(str(x) for x in scope.get("capabilities", [])) - allowed
            if unknown:
                raise MIASIApplicabilityError(f"unknown AI capabilities: {sorted(unknown)}")
            if str(scope.get("risk_level") or "") not in self.policy["risk_order"]:
                raise MIASIApplicabilityError("invalid risk_level")

    @staticmethod
    def _read_object(path: Path, label: str) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MIASIApplicabilityError(f"{label} is unreadable: {exc}") from exc
        if not isinstance(value, dict):
            raise MIASIApplicabilityError(f"{label} must be a JSON object")
        return value

    @staticmethod
    def _blocker(code: str, message: str) -> dict[str, Any]:
        return {"code": code, "message": message, "severity": "S1"}
