from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

ROLE_CATALOG_PATH = Path(".devpilot/agents/agent_role_binding_catalog.json")
STEP_BINDINGS_PATH = Path(".devpilot/agents/step_agent_bindings.json")
RUNTIME_BOUNDARY_PATH = Path(".devpilot/agents/agent_runtime_boundary.json")
MIASI_AGENT_REGISTRY_PATH = Path(".devpilot/miasi/agent_registry.json")
MIASI_TOOL_REGISTRY_PATH = Path(".devpilot/miasi/tool_registry.json")
MIP_WORKFLOW_REGISTRY_PATH = Path(".devpilot/gsdlc/mip_workflow_registry.json")
MODEL_CAPABILITY_CATALOG_PATH = Path(".devpilot/modeling/model_capability_catalog.json")
REQUIRED_ROLE_IDS = ("product", "requirements", "architecture", "security", "test", "planning", "coding", "review")


def _load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load governed agent binding authority {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"governed agent binding authority must be object: {path}")
    return payload


def _hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class AgentRoleDescriptor:
    role_id: str
    display_name: str
    runtime_agent_id: str
    enabled: bool
    required_model_capabilities: tuple[str, ...]
    fallback: Mapping[str, Any]
    tool_allowlist: tuple[str, ...]
    limits: Mapping[str, Any]
    policy_status: str
    can_approve: bool

    def to_payload(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "display_name": self.display_name,
            "runtime_agent_id": self.runtime_agent_id,
            "enabled": self.enabled,
            "required_model_capabilities": list(self.required_model_capabilities),
            "fallback": dict(self.fallback),
            "tool_allowlist": list(self.tool_allowlist),
            "limits": dict(self.limits),
            "policy_status": self.policy_status,
            "can_approve": self.can_approve,
        }


@dataclass(frozen=True)
class StepAgentBinding:
    step_id: str
    agent_role_id: str | None
    explicit_none: bool
    allowed_artifacts: tuple[str, ...]
    required_model_capabilities: tuple[str, ...]
    fallback: Mapping[str, Any]
    tool_allowlist: tuple[str, ...]
    rationale: str
    human_review_required: bool
    approval_authority: str
    policy_status: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "agent_role_id": self.agent_role_id,
            "explicit_none": self.explicit_none,
            "allowed_artifacts": list(self.allowed_artifacts),
            "required_model_capabilities": list(self.required_model_capabilities),
            "fallback": dict(self.fallback),
            "tool_allowlist": list(self.tool_allowlist),
            "rationale": self.rationale,
            "human_review_required": self.human_review_required,
            "approval_authority": self.approval_authority,
            "policy_status": self.policy_status,
        }


class AgentRoleBindingCatalog:
    """GSDLC-07-A contextual-role authority.

    It maps Guided-SDLC steps to least-privilege role descriptors. It never
    executes agents or tools and never converts a ModelRouteDecision into tool
    authority. Tool execution remains downstream of deterministic
    PolicyEngine/RBAC/Approval.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.roles_payload = _load(self.root / ROLE_CATALOG_PATH)
        self.bindings_payload = _load(self.root / STEP_BINDINGS_PATH)
        self.boundary_payload = _load(self.root / RUNTIME_BOUNDARY_PATH)
        self.miasi_agents = _load(self.root / MIASI_AGENT_REGISTRY_PATH)
        self.miasi_tools = _load(self.root / MIASI_TOOL_REGISTRY_PATH)
        self.mip = _load(self.root / MIP_WORKFLOW_REGISTRY_PATH)
        self.model_capabilities = _load(self.root / MODEL_CAPABILITY_CATALOG_PATH)
        self._roles = {str(row.get("role_id")): row for row in self.roles_payload.get("roles", [])}
        self._bindings = {str(row.get("step_id")): row for row in self.bindings_payload.get("bindings", [])}
        self._miasi_agents = {str(row.get("agent_id")): row for row in self.miasi_agents.get("agents", [])}
        self._tool_ids = {str(row.get("tool_id")) for row in self.miasi_tools.get("tools", [])}
        self._capability_vocabulary = set(self.model_capabilities.get("capability_vocabulary", []))

    def validate(self) -> dict[str, Any]:
        issues: list[dict[str, str]] = []
        role_ids = tuple(sorted(self._roles))
        if set(role_ids) != set(REQUIRED_ROLE_IDS):
            issues.append({"code": "AGENT_ROLE_SET_MISMATCH", "message": ",".join(role_ids)})
        for role_id, role in self._roles.items():
            runtime_agent_id = str(role.get("runtime_agent_id") or "")
            miasi = self._miasi_agents.get(runtime_agent_id)
            if miasi is None:
                issues.append({"code": "RUNTIME_AGENT_MISSING", "message": f"{role_id}:{runtime_agent_id}"})
                continue
            allowlist = {str(x) for x in role.get("tool_allowlist", [])}
            unknown = sorted(allowlist - self._tool_ids)
            outside_runtime = sorted(allowlist - {str(x) for x in miasi.get("allowed_tools", [])})
            if unknown:
                issues.append({"code": "ROLE_TOOL_UNKNOWN", "message": f"{role_id}:{','.join(unknown)}"})
            if outside_runtime:
                issues.append({"code": "ROLE_TOOL_OUTSIDE_RUNTIME_AGENT_SCOPE", "message": f"{role_id}:{','.join(outside_runtime)}"})
            if any("approval" in tool.lower() for tool in allowlist):
                issues.append({"code": "ROLE_APPROVAL_TOOL_FORBIDDEN", "message": role_id})
            if bool(role.get("human_approval_role")) or bool(role.get("can_approve")):
                issues.append({"code": "ROLE_HUMAN_APPROVAL_AUTHORITY_FORBIDDEN", "message": role_id})
            required_caps = {str(x) for x in role.get("required_model_capabilities", [])}
            if not required_caps.issubset(self._capability_vocabulary):
                issues.append({"code": "ROLE_MODEL_CAPABILITY_UNKNOWN", "message": f"{role_id}:{','.join(sorted(required_caps-self._capability_vocabulary))}"})
        mip_steps = [str(row.get("current_step")) for row in self.mip.get("phases", [])]
        missing = sorted(set(mip_steps)-set(self._bindings))
        extra = sorted(set(self._bindings)-set(mip_steps))
        if missing:
            issues.append({"code": "STEP_AGENT_BINDING_MISSING", "message": ",".join(missing)})
        if extra:
            issues.append({"code": "STEP_AGENT_BINDING_EXTRA", "message": ",".join(extra)})
        for step_id, binding in self._bindings.items():
            role_id = binding.get("agent_role_id")
            explicit_none = bool(binding.get("explicit_none"))
            if (role_id is None) == (not explicit_none):
                issues.append({"code": "STEP_BINDING_EXPLICITNESS_INVALID", "message": step_id})
            if role_id is not None and str(role_id) not in self._roles:
                issues.append({"code": "STEP_BINDING_ROLE_UNKNOWN", "message": f"{step_id}:{role_id}"})
            if binding.get("approval_authority") != "human-only" or not bool(binding.get("human_review_required")):
                issues.append({"code": "STEP_BINDING_HUMAN_REVIEW_REQUIRED", "message": step_id})
            if role_id is not None:
                role_tools = {str(x) for x in self._roles[str(role_id)].get("tool_allowlist", [])}
                binding_tools = {str(x) for x in binding.get("tool_allowlist", [])}
                if not binding_tools.issubset(role_tools):
                    issues.append({"code": "STEP_BINDING_TOOL_SCOPE_ESCALATION", "message": step_id})
        tool_authority = self.boundary_payload.get("tool_authority", {})
        safety = self.boundary_payload.get("safety", {})
        if bool(tool_authority.get("model_route_can_grant_tool_permission")):
            issues.append({"code": "MODEL_ROUTE_TOOL_AUTHORITY_FORBIDDEN", "message": "model route cannot grant tool permission"})
        if bool(tool_authority.get("agent_role_can_approve")) or bool(safety.get("self_approval")):
            issues.append({"code": "AGENT_SELF_APPROVAL_FORBIDDEN", "message": "human approval remains separate"})
        adopted = [str(row.get("framework_id")) for row in self.boundary_payload.get("framework_candidates", []) if bool(row.get("dependency_adopted")) and str(row.get("framework_id")) != "devpilot-governed-runtime"]
        if adopted:
            issues.append({"code": "EXTERNAL_FRAMEWORK_ADOPTED_WITHOUT_EXPERIMENT", "message": ",".join(adopted)})
        return {
            "status": "PASS" if not issues else "BLOCK",
            "roles_total": len(self._roles),
            "steps_total": len(self._bindings),
            "mip_steps_total": len(mip_steps),
            "generic_all_tools_agent": False,
            "model_route_grants_tool_permission": False,
            "agent_role_can_approve": False,
            "external_framework_dependency_adopted": bool(adopted),
            "issues": issues,
            "catalog_sha256": hashlib.sha256((self.root / ROLE_CATALOG_PATH).read_bytes()).hexdigest(),
            "bindings_sha256": hashlib.sha256((self.root / STEP_BINDINGS_PATH).read_bytes()).hexdigest(),
            "boundary_sha256": hashlib.sha256((self.root / RUNTIME_BOUNDARY_PATH).read_bytes()).hexdigest(),
        }

    def role(self, role_id: str) -> AgentRoleDescriptor | None:
        row = self._roles.get(str(role_id).strip())
        if row is None:
            return None
        return AgentRoleDescriptor(
            role_id=str(row["role_id"]), display_name=str(row["display_name"]), runtime_agent_id=str(row["runtime_agent_id"]),
            enabled=bool(row.get("enabled")), required_model_capabilities=tuple(str(x) for x in row.get("required_model_capabilities", [])),
            fallback=dict(row.get("fallback") or {}), tool_allowlist=tuple(str(x) for x in row.get("tool_allowlist", [])),
            limits=dict(row.get("limits") or {}), policy_status=str(row.get("policy_status") or "UNKNOWN"), can_approve=bool(row.get("can_approve")),
        )

    def binding(self, step_id: str) -> StepAgentBinding | None:
        row = self._bindings.get(str(step_id).strip())
        if row is None:
            return None
        return StepAgentBinding(
            step_id=str(row["step_id"]), agent_role_id=None if row.get("agent_role_id") is None else str(row.get("agent_role_id")), explicit_none=bool(row.get("explicit_none")),
            allowed_artifacts=tuple(str(x) for x in row.get("allowed_artifacts", [])), required_model_capabilities=tuple(str(x) for x in row.get("required_model_capabilities", [])),
            fallback=dict(row.get("fallback") or {}), tool_allowlist=tuple(str(x) for x in row.get("tool_allowlist", [])), rationale=str(row.get("rationale") or ""),
            human_review_required=bool(row.get("human_review_required")), approval_authority=str(row.get("approval_authority") or ""), policy_status=str(row.get("policy_status") or "UNKNOWN"),
        )

    def descriptor_for_step(self, step_id: str, *, available_model_capabilities: set[str] | None = None) -> dict[str, Any] | None:
        binding = self.binding(step_id)
        if binding is None:
            return None
        if binding.explicit_none or binding.agent_role_id is None:
            return {"step_id": binding.step_id, "agent_role_id": None, "explicit_none": True, "reason": binding.rationale, "human_review_required": True, "tool_execution_authority": False}
        role = self.role(binding.agent_role_id)
        if role is None:
            return None
        available = set(available_model_capabilities or ())
        missing = sorted(set(binding.required_model_capabilities)-available) if available_model_capabilities is not None else []
        return {
            "step_id": binding.step_id,
            "agent_role_id": role.role_id,
            "display_name": role.display_name,
            "runtime_agent_id": role.runtime_agent_id,
            "enabled": role.enabled,
            "reason": binding.rationale,
            "allowed_artifacts": list(binding.allowed_artifacts),
            "required_model_capabilities": list(binding.required_model_capabilities),
            "missing_model_capabilities": missing,
            "fallback": dict(binding.fallback),
            "tool_allowlist": list(binding.tool_allowlist),
            "limits": dict(role.limits),
            "policy_status": binding.policy_status,
            "human_review_required": True,
            "approval_authority": "human-only",
            "model_route_grants_tool_permission": False,
            "tool_execution_authority": False,
            "execution_enabled_in_07_a": False,
        }

    def snapshot(self) -> CommandResult:
        validation = self.validate()
        ok = validation["status"] == "PASS"
        rows = []
        for step_id in [str(row.get("current_step")) for row in self.mip.get("phases", [])]:
            descriptor = self.descriptor_for_step(step_id)
            if descriptor is not None:
                rows.append(descriptor)
        data = {
            "summary": {
                "roles_total": len(self._roles), "bindings_total": len(rows), "validation_status": validation["status"],
                "execution_enabled_in_07_a": False, "network_used": False, "external_api_used": False,
                "model_route_grants_tool_permission": False, "agent_role_can_approve": False,
            },
            "roles": [self.role(role_id).to_payload() for role_id in REQUIRED_ROLE_IDS if self.role(role_id) is not None],
            "bindings": rows,
            "runtime_boundary": self.boundary_payload,
            "validation": validation,
        }
        return CommandResult(command="settings agent-runtime", ok=ok, exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Agent runtime role bindings loaded safely." if ok else "Agent runtime role bindings are blocked by deterministic validation.",
            data=data, findings=[Finding("GSDLC_07_A_AGENT_BINDINGS_PASS" if ok else "GSDLC_07_A_AGENT_BINDINGS_BLOCK", "Agent role/step/runtime boundary validation completed.", Severity.INFO if ok else Severity.BLOCK)])
