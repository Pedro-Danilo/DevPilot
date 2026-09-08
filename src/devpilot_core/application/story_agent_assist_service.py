from __future__ import annotations

import difflib
import hashlib
import json
import re
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.agents.execution_policy import ToolIntent
from devpilot_core.agents.role_bindings import AgentRoleBindingCatalog
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.budget import estimate_text_tokens
from devpilot_core.policy import PolicyEffect, SecretGuard
from devpilot_core.rag.retriever import LocalRagRetriever, RagQueryOptions
from devpilot_core.story_execution.store import StoryExecutionStore

from .agent_execution_service import AgentExecutionApplicationService
from .model_gateway_settings_service import ModelGatewaySettingsService

MAX_INSTRUCTION_CHARS = 2000
_ALLOWED_AGENT_TYPES = {"coding", "test"}
_ALLOWED_MODES = {"mock", "fake-local"}
_UNSAFE = re.compile(r"(?i)(filesystem\.delete|rm\s+-rf|os\.remove|shutil\.rmtree|subprocess\.|git\s+push|self[-_ ]?approve|force\s+push|connector\.write|remote\.runner\.execute)")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class StoryAgentAssistApplicationService:
    """GSDLC-09-D proposal-only CodingAgent/TestAgent boundary.

    The service consumes the server-authoritative StoryContextPack, bounded local
    RAG and Model Gateway routing.  It may create runtime proposal records only.
    It never creates a SourceDraftBuffer, never applies source, never approves,
    never commits and never derives tool authority from ModelRouteDecision.
    """

    def __init__(self, root: Path, *, context_resolver, code_workbench) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver
        self.code_workbench = code_workbench
        self.gateway = ModelGatewaySettingsService(self.root)
        self.roles = AgentRoleBindingCatalog(self.root)
        self.execution = AgentExecutionApplicationService(self.root)
        self.secret_guard = SecretGuard(self.root)
        self._lock = threading.RLock()

    def propose(self, *, agent_type: str, mode: str, instruction: str, source_id: str | None, actor: str, actor_role: str) -> CommandResult:
        command = "story agent proposal create"
        agent_type = str(agent_type or "").strip().lower()
        mode = str(mode or "mock").strip().lower()
        instruction = str(instruction or "").strip()
        if agent_type not in _ALLOWED_AGENT_TYPES:
            return self._block(command, "GSDLC09D_AGENT_TYPE_BLOCK", "Only CodingAgent or TestAgent proposal modes are allowed.")
        if mode not in _ALLOWED_MODES:
            return self._block(command, "GSDLC09D_ROUTE_MODE_BLOCK", "09-D PASS requires mock/fake-local routing; external API is not required.")
        if actor_role not in {"owner", "developer"} or not actor.strip():
            return self._block(command, "GSDLC09D_HUMAN_ROLE_BLOCK", "Authenticated owner/developer is required to request agent proposals.")
        if not instruction or len(instruction) > MAX_INSTRUCTION_CHARS:
            return self._block(command, "GSDLC09D_INSTRUCTION_BUDGET_BLOCK", "Instruction must be non-empty and within the 09-D bounded size.")
        if _UNSAFE.search(instruction):
            return self._block(command, "GSDLC09D_UNSAFE_PROPOSAL_BLOCK", "Unsafe proposal instruction requested forbidden execution/mutation semantics.")
        if self.secret_guard.scan_text(instruction, subject="story-agent-instruction").effect is PolicyEffect.BLOCK:
            return self._block(command, "GSDLC09D_SECRET_INPUT_BLOCK", "Secret-like content cannot enter the agent proposal boundary.")

        context = self.context_resolver.resolve()
        workspace_id = str(context.active_workspace_id or "").strip()
        if not context.configured or not context.valid or not workspace_id:
            return self._block(command, "GSDLC09D_WORKSPACE_CONTEXT_BLOCK", "Active server-valid project context is required.")
        workspace_root = context.effective_workspace_root
        story_store = StoryExecutionStore(workspace_root, workspace_id=workspace_id)
        state = story_store.load_state()
        story_context = story_store.load_context()
        if state is None or not isinstance(story_context, dict):
            return self._block(command, "GSDLC09D_STORY_CONTEXT_BLOCK", "StoryExecutionState and StoryContextPack are required before agent assistance.")
        if str(state.status.value) not in {"IN_PROGRESS", "CHANGES_READY", "VALIDATING"}:
            return self._block(command, "GSDLC09D_STORY_STATE_BLOCK", "Agent proposals require an active story execution state.")

        selected_source: dict[str, Any] | None = None
        if source_id:
            source_result = self.code_workbench.read_source(source_id)
            if not source_result.ok:
                return source_result
            selected_source = dict((source_result.data or {}).get("source") or {})
        if agent_type == "coding" and selected_source is None:
            return self._block(command, "GSDLC09D_CODING_SOURCE_REQUIRED", "CodingAgent requires one selected bounded source file.")
        source_text = str((selected_source or {}).get("content") or "")
        if source_text and self.secret_guard.scan_text(source_text, subject=str((selected_source or {}).get("relative_path") or "source")).effect is PolicyEffect.BLOCK:
            return self._block(command, "GSDLC09D_SOURCE_SECRET_BLOCK", "Selected source contains secret-like material and cannot enter the proposal context.")

        step_id = "implementation" if agent_type == "coding" else "test-plan"
        role_id = "coding" if agent_type == "coding" else "test"
        descriptor = self.roles.descriptor_for_step(step_id)
        if not descriptor or descriptor.get("agent_role_id") != role_id:
            return self._block(command, "GSDLC09D_AGENT_BINDING_BLOCK", "Governed role/step binding is missing or inconsistent.")

        rag_query = " ".join([
            "story coding testing source change approval proposal-only",
            str((story_context.get("story") or {}).get("title") or ""),
            instruction,
        ])
        rag_result = LocalRagRetriever(self.root, options=RagQueryOptions(query=rag_query, top_k=3)).query()
        rag_sources = list((rag_result.data or {}).get("sources") or []) if rag_result.ok else []
        input_tokens = estimate_text_tokens(json.dumps(story_context, ensure_ascii=False)) + estimate_text_tokens(source_text) + estimate_text_tokens(instruction)
        output_tokens = 1000 if agent_type == "coding" else 800
        required_caps = tuple(str(x) for x in descriptor.get("required_model_capabilities") or ["text_generation"])
        route_result = self.gateway.controlled_evaluation(mode=mode, workload_id=f"gsdlc-09-d-{agent_type}", required_capabilities=required_caps, estimated_input_tokens=input_tokens, estimated_output_tokens=output_tokens, max_cost_usd=0.0)
        capability_fallback_used = False
        if not route_result.ok:
            fallback_caps = tuple(str(x) for x in ((descriptor.get("fallback") or {}).get("required_capabilities") or ["text_generation"]))
            route_result = self.gateway.controlled_evaluation(mode=mode, workload_id=f"gsdlc-09-d-{agent_type}-fallback", required_capabilities=fallback_caps, estimated_input_tokens=input_tokens, estimated_output_tokens=output_tokens, max_cost_usd=0.0)
            capability_fallback_used = route_result.ok
        if not route_result.ok:
            return CommandResult(command, False, route_result.exit_code, "Model Gateway could not select a bounded proposal route.", data=route_result.data, findings=route_result.findings)
        route = deepcopy((route_result.data or {}).get("decision") or {})
        route_summary = deepcopy((route_result.data or {}).get("summary") or {})
        if route_summary.get("network_used") or route_summary.get("external_api_used") or route_summary.get("tool_authority_granted"):
            return self._block(command, "GSDLC09D_MODEL_AUTHORITY_BLOCK", "Model route violated the no-network/no-tool-authority invariant.")

        session_result = self.execution.create_session(role_id=role_id, step_id=step_id, actor_id=actor, mode=mode)
        if not session_result.ok:
            return session_result
        session_id = str((session_result.data or {}).get("summary", {}).get("session_id") or "")
        route_ref = str(route.get("decision_id") or route.get("access_route_id") or "model-route")
        probe_tool = "story.source-change.apply" if agent_type == "coding" else "tests.run"
        probe = self.execution.tool_intent(
            session_id=session_id,
            actor_id=actor,
            role_at_decision=actor_role,
            payload={
                "agent_role_id": role_id,
                "step_id": step_id,
                "tool_id": probe_tool,
                "action": "propose-only",
                "subject": str((selected_source or {}).get("relative_path") or state.story_id),
                "arguments": {"proposal_only": True, "real_execution_requested": False},
                "dry_run": True,
                "model_route_decision_ref": route_ref,
                "estimated_input_tokens": input_tokens,
                "estimated_output_tokens": output_tokens,
                "estimated_cost_usd": 0.0,
            },
        )
        probe_decision = deepcopy((probe.data or {}).get("tool_execution_decision") or {})
        if probe_decision.get("model_route_granted_permission") is not False or probe_decision.get("tool_executed") is True:
            return self._block(command, "GSDLC09D_TOOL_AUTHORITY_ESCALATION_BLOCK", "Model route or agent intent unexpectedly obtained execution authority.")

        delete_probe = self.execution.tool_intent(
            session_id=session_id,
            actor_id=actor,
            role_at_decision=actor_role,
            payload={
                "agent_role_id": role_id,
                "step_id": step_id,
                "tool_id": "filesystem.delete",
                "action": "delete",
                "subject": "forbidden-fixture",
                "arguments": {"proposal_only": True},
                "dry_run": True,
                "model_route_decision_ref": route_ref,
            },
        )
        delete_decision = deepcopy((delete_probe.data or {}).get("tool_execution_decision") or {})
        if delete_decision.get("effect") != "BLOCK" or delete_decision.get("tool_executed") is True:
            return self._block(command, "GSDLC09D_DELETE_GUARD_BLOCK", "filesystem.delete did not remain blocked.")

        proposed_content, target_path, operation = self._proposal_content(agent_type, instruction, selected_source, state.story_id, story_context)
        full_diff = self._diff(selected_source, proposed_content, target_path)
        stable = {
            "schema_id": "DEVPL-GSDLC-09-D-AGENT-PROPOSAL-V1",
            "agent_type": agent_type,
            "agent_role_id": role_id,
            "step_id": step_id,
            "story_id": state.story_id,
            "story_execution_id": state.execution_id,
            "story_context_pack_id": story_context.get("context_pack_id"),
            "story_context_sha256": story_context.get("context_sha256"),
            "source_id": None if selected_source is None else selected_source.get("source_id"),
            "source_preimage_sha256": None if selected_source is None else selected_source.get("sha256"),
            "target_path": target_path,
            "operation": operation,
            "instruction": instruction,
            "proposed_content": proposed_content,
            "full_diff": full_diff,
            "rag_source_refs": [str(x.get("ref") or "") for x in rag_sources],
            "model_id": route.get("model_id"),
            "provider_id": route.get("provider_id"),
            "access_route_id": route.get("access_route_id"),
            "agent_session": session_id,
            "tool_intent": deepcopy((probe.data or {}).get("tool_intent") or {}),
            "tool_execution_decision": probe_decision,
            "forbidden_delete_decision": delete_decision,
        }
        proposal_hash = _hash(stable)
        proposal_id = "agent-proposal-" + proposal_hash[:24]
        trace_id = "trace_" + uuid.uuid4().hex
        proposal = {
            **stable,
            "proposal_id": proposal_id,
            "proposal_sha256": proposal_hash,
            "status": "PROPOSED",
            "created_at_utc": _now(),
            "trace_id": trace_id,
            "mode": mode,
            "capability_fallback_used": capability_fallback_used,
            "rag_grounded": bool(rag_sources),
            "rag_sources": rag_sources,
            "cost": {"estimated_input_tokens": input_tokens, "estimated_output_tokens": output_tokens, "estimated_cost_usd": 0.0},
            "provenance": {
                "model_id": route.get("model_id"), "provider_id": route.get("provider_id"), "access_route_id": route.get("access_route_id"),
                "agent_session": session_id, "trace_id": trace_id, "story_context_pack_id": story_context.get("context_pack_id"),
                "story_context_sha256": story_context.get("context_sha256"), "rag_source_refs": [str(x.get("ref") or "") for x in rag_sources],
            },
            "safety": {
                "proposal_only": True, "human_decision_required": True, "source_mutations_performed": False,
                "draft_mutations_performed": False, "agent_self_apply": False, "agent_self_approve": False,
                "agent_self_commit": False, "generic_shell": False, "filesystem_delete_blocked": True,
                "model_route_grants_tool_permission": False, "network_used": False, "external_api_used": False,
            },
        }
        self._save_proposal(workspace_root, workspace_id, proposal)
        return CommandResult(command, True, ExitCode.PASS, f"{agent_type.title()}Agent proposal created without source/draft mutation.", data={"proposal": proposal, "summary": {"proposal_only": True, "human_decision_required": True, "model_route_grants_tool_permission": False, "source_mutations_performed": False}}, findings=[])

    def get(self, *, proposal_id: str) -> CommandResult:
        context = self.context_resolver.resolve(); workspace_id = str(context.active_workspace_id or "").strip()
        proposal = self._load_proposal(context.effective_workspace_root, workspace_id, proposal_id) if context.configured and context.valid and workspace_id else None
        if not proposal:
            return self._block("story agent proposal get", "GSDLC09D_PROPOSAL_NOT_FOUND", "Agent proposal was not found in active workspace runtime state.")
        return CommandResult("story agent proposal get", True, ExitCode.PASS, "Agent proposal loaded.", data={"proposal": proposal}, findings=[])

    def decide(self, *, proposal_id: str, proposal_sha256: str, decision: str, actor: str, actor_role: str) -> CommandResult:
        command = "story agent proposal decision"
        decision = str(decision or "").strip().upper()
        if actor_role not in {"owner", "developer"} or not actor.strip():
            return self._block(command, "GSDLC09D_HUMAN_DECISION_ROLE_BLOCK", "Authenticated owner/developer is required for proposal decision.")
        if decision not in {"ACCEPT", "REJECT"}:
            return self._block(command, "GSDLC09D_DECISION_BLOCK", "Proposal decision must be ACCEPT or REJECT.")
        context = self.context_resolver.resolve(); workspace_id = str(context.active_workspace_id or "").strip()
        if not context.configured or not context.valid or not workspace_id:
            return self._block(command, "GSDLC09D_WORKSPACE_CONTEXT_BLOCK", "Active server-valid project context is required.")
        proposal = self._load_proposal(context.effective_workspace_root, workspace_id, proposal_id)
        if not proposal:
            return self._block(command, "GSDLC09D_PROPOSAL_NOT_FOUND", "Agent proposal was not found.")
        if str(proposal.get("proposal_sha256") or "") != str(proposal_sha256 or ""):
            return self._block(command, "GSDLC09D_PROPOSAL_TAMPER_BLOCK", "Proposal SHA-256 preimage changed; refresh before decision.")
        if proposal.get("status") != "PROPOSED":
            return self._block(command, "GSDLC09D_PROPOSAL_ALREADY_DECIDED_BLOCK", "Proposal already has a terminal human decision.")
        if decision == "ACCEPT" and proposal.get("source_id"):
            current = self.code_workbench.read_source(str(proposal["source_id"]))
            if not current.ok or str((current.data or {}).get("source", {}).get("sha256") or "") != str(proposal.get("source_preimage_sha256") or ""):
                return self._block(command, "GSDLC09D_PROPOSAL_STALE_SOURCE_BLOCK", "Selected source changed after proposal generation; regenerate proposal.")
        proposal["status"] = "ACCEPTED" if decision == "ACCEPT" else "REJECTED"
        proposal["human_decision"] = {"decision": decision, "actor": actor, "actor_role": actor_role, "decided_at_utc": _now(), "insert_into_editor_authorized": decision == "ACCEPT", "source_write_authorized": False, "draft_write_performed": False}
        self._save_proposal(context.effective_workspace_root, workspace_id, proposal)
        return CommandResult(command, True, ExitCode.PASS, f"Human {decision} recorded; source remains unchanged.", data={"proposal": proposal, "insert_into_editor_authorized": decision == "ACCEPT", "source_mutations_performed": False, "draft_mutations_performed": False}, findings=[])

    def _proposal_content(self, agent_type: str, instruction: str, source: dict[str, Any] | None, story_id: str, story_context: dict[str, Any]) -> tuple[str, str, str]:
        safe_instruction = re.sub(r"\s+", " ", instruction).strip()[:240]
        if agent_type == "coding":
            assert source is not None
            text = str(source.get("content") or "")
            suffix = "\n" if text and not text.endswith("\n") else ""
            ext = Path(str(source.get("relative_path") or "")).suffix.lower()
            marker = f"# Agent-assisted proposal for {story_id}: {safe_instruction}" if ext in {".py", ".pyi"} else f"// Agent-assisted proposal for {story_id}: {safe_instruction}"
            return text + suffix + marker + "\n", str(source.get("relative_path") or ""), "EDIT"
        acceptance = [str(x) for x in story_context.get("fragments", []) if isinstance(x, dict) and x.get("kind") == "acceptance"]
        target = f"tests/test_agent_proposal_{re.sub(r'[^a-zA-Z0-9_]+','_',story_id).strip('_').lower() or 'story'}.py"
        body = (
            f'"""Human-review-required TestAgent proposal for {story_id}."""\n\n'
            f"def test_{re.sub(r'[^a-zA-Z0-9_]+','_',story_id).strip('_').lower() or 'story'}_acceptance_contract():\n"
            f"    # Proposed intent: {safe_instruction}\n"
            f"    # Generated from StoryContextPack; replace with executable assertions after human review.\n"
            f"    assert True\n"
        )
        return body, target, "CREATE"

    @staticmethod
    def _diff(source: dict[str, Any] | None, proposed: str, target: str) -> str:
        before = str((source or {}).get("content") or "").splitlines(keepends=True)
        after = proposed.splitlines(keepends=True)
        fromfile = str((source or {}).get("relative_path") or "/dev/null")
        return "".join(difflib.unified_diff(before, after, fromfile=fromfile, tofile=target))

    def _store_path(self, workspace_root: Path, workspace_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in workspace_id).strip("-") or "workspace"
        return Path(workspace_root) / "outputs" / "story_agent_assist" / "gsdlc_09_d" / safe / "proposals.json"

    def _save_proposal(self, workspace_root: Path, workspace_id: str, proposal: dict[str, Any]) -> None:
        path = self._store_path(workspace_root, workspace_id)
        with self._lock:
            payload = {"schema_version": "1.0.0", "proposals": {}}
            if path.is_file():
                try: payload = json.loads(path.read_text(encoding="utf-8"))
                except Exception: payload = {"schema_version": "1.0.0", "proposals": {}}
            payload.setdefault("proposals", {})[str(proposal["proposal_id"])] = proposal
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
            tmp.replace(path)

    def _load_proposal(self, workspace_root: Path, workspace_id: str, proposal_id: str) -> dict[str, Any] | None:
        path = self._store_path(workspace_root, workspace_id)
        if not path.is_file(): return None
        try: payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception: return None
        row = (payload.get("proposals") or {}).get(str(proposal_id))
        return deepcopy(row) if isinstance(row, dict) else None

    @staticmethod
    def _block(command: str, finding_id: str, message: str) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"summary": {"proposal_only": True, "source_mutations_performed": False, "network_used": False, "external_api_used": False}}, findings=[Finding(finding_id, message, Severity.BLOCK)])
