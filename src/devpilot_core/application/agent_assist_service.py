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

from devpilot_core.agents.role_bindings import AgentRoleBindingCatalog
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.budget import estimate_text_tokens
from devpilot_core.policy import SecretGuard
from devpilot_core.rag.context_pack_v2 import ContextPackV2Builder, ContextPackV2Options
from devpilot_core.schemas.validator import SchemaValidator

from .artifact_draft_service import ArtifactDraftApplicationService
from .artifact_import_service import ArtifactImportApplicationService
from .model_gateway_settings_service import ModelGatewaySettingsService
from .workspace_documents_service import WorkspaceDocumentsApplicationService

DEFAULT_ASSIST_ROOT = Path("outputs/agent_assist/gsdlc_07_c")
ALLOWED_OPERATIONS = {"generate_draft", "rewrite_selection", "critique", "improve", "transform_imported_source"}
ALLOWED_MODES = {"mock", "fake-local"}
MAX_INSTRUCTION_CHARS = 4000
MAX_CONTENT_CHARS = 1_048_576
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class AgentAssistApplicationService:
    """GSDLC-07-C governed artifact assistance boundary.

    The service separates planning from execution so model/provider/context/cost
    are visible before any model-like transformation.  Execution is hermetic in
    07-C (mock/fake-local only), returns an untrusted proposal, and never writes
    workspace source.  Only an authenticated human ACCEPT/MODIFY decision may
    persist the proposal as a runtime DRAFT revision through the existing
    ArtifactDraftApplicationService optimistic-concurrency boundary.
    """

    def __init__(
        self,
        root: Path,
        *,
        documents: WorkspaceDocumentsApplicationService,
        drafts: ArtifactDraftApplicationService,
        imports: ArtifactImportApplicationService,
        assist_root: Path = DEFAULT_ASSIST_ROOT,
    ) -> None:
        self.root = Path(root).resolve()
        self.documents = documents
        self.drafts = drafts
        self.imports = imports
        self.assist_root = self.root / assist_root
        self.secret_guard = SecretGuard(self.root)
        self.schemas = SchemaValidator(self.root)
        self.gateway = ModelGatewaySettingsService(self.root)
        self.roles = AgentRoleBindingCatalog(self.root)
        self._lock = threading.RLock()

    def plan(
        self,
        *,
        document_id: str,
        operation: str,
        mode: str,
        instruction: str,
        current_content: str,
        expected_source_sha256: str,
        expected_revision_sha256: str | None,
        actor: str,
        actor_role: str,
        session_principal: str,
        selection_start: int | None = None,
        selection_end: int | None = None,
        import_id: str | None = None,
        step_id: str | None = None,
    ) -> CommandResult:
        command = "workspace artifact assist plan"
        op = str(operation or "").strip().lower()
        mode = str(mode or "mock").strip().lower()
        if op not in ALLOWED_OPERATIONS:
            return self._block(command, "GSDLC07C_OPERATION_BLOCK", "Agent-assist operation is not allowlisted.")
        if mode not in ALLOWED_MODES:
            return self._block(command, "GSDLC07C_MODE_BLOCK", "07-C only permits hermetic mock or fake-local modes.")
        if not actor.strip() or not actor_role.strip() or not session_principal.strip():
            return self._block(command, "GSDLC07C_HUMAN_SESSION_REQUIRED_BLOCK", "Authenticated human actor/role/session are required.")
        if len(str(instruction or "")) > MAX_INSTRUCTION_CHARS or len(str(current_content or "")) > MAX_CONTENT_CHARS:
            return self._block(command, "GSDLC07C_INPUT_BUDGET_BLOCK", "Agent-assist input exceeds the bounded request size.")
        if not _SHA256.fullmatch(str(expected_source_sha256 or "")):
            return self._block(command, "GSDLC07C_SOURCE_PREIMAGE_REQUIRED_BLOCK", "Exact source SHA-256 preimage is required.")

        doc_result = self.documents.read_document(document_id)
        if not doc_result.ok:
            return CommandResult(command, False, doc_result.exit_code, "Agent assist requires a readable project-scoped document.", data=doc_result.data, findings=doc_result.findings)
        document = (doc_result.data or {}).get("document") or {}
        if str(document.get("sha256") or "") != expected_source_sha256:
            return self._block(command, "GSDLC07C_SOURCE_PREIMAGE_CONFLICT_BLOCK", "Approved source changed before agent-assist planning.")
        extension = str(document.get("extension") or "").lower()
        if extension not in {".md", ".json"}:
            return self._block(command, "GSDLC07C_DOCUMENT_TYPE_BLOCK", "Agent assist is bounded to Markdown/JSON Artifact Workbench documents.")
        secret = self.secret_guard.scan_text(current_content, subject=str(document.get("relative_path") or document_id))
        if secret.effect.value == "block":
            return self._block(command, "GSDLC07C_INPUT_SECRET_BLOCK", "Secret-like content cannot be sent to the agent-assist boundary.")

        base_content = current_content
        source_kind = "DOCUMENT"
        imported: dict[str, Any] | None = None
        if op == "transform_imported_source":
            if not str(import_id or "").strip():
                return self._block(command, "GSDLC07C_IMPORT_REQUIRED_BLOCK", "transform_imported_source requires an import_id.")
            imported_result = self.imports.get(import_id=str(import_id))
            if not imported_result.ok:
                return CommandResult(command, False, imported_result.exit_code, "Imported DRAFT could not be loaded.", data=imported_result.data, findings=imported_result.findings)
            imported = (imported_result.data or {}).get("import") or {}
            base_content = str(imported.get("normalized_content") or "")
            source_kind = "IMPORT"
        if op == "rewrite_selection":
            if selection_start is None or selection_end is None or selection_start < 0 or selection_end <= selection_start or selection_end > len(base_content):
                return self._block(command, "GSDLC07C_SELECTION_BLOCK", "rewrite_selection requires a valid non-empty selection range.")
            if extension == ".json":
                return self._block(command, "GSDLC07C_JSON_SELECTION_BLOCK", "rewrite_selection is not enabled for JSON because partial replacement could invalidate structure.")

        resolved_step = str(step_id or _infer_step(str(document.get("relative_path") or ""))).strip().lower()
        descriptor = self.roles.descriptor_for_step(resolved_step)
        if not isinstance(descriptor, dict):
            return self._block(command, "GSDLC07C_AGENT_BINDING_BLOCK", f"No explicit agent binding exists for step {resolved_step}.")
        context_query = " ".join(x for x in [op.replace("_", " "), str(instruction or "").strip(), str(document.get("relative_path") or "")] if x).strip()
        context_result = ContextPackV2Builder(
            self.root,
            ContextPackV2Options(step_id=resolved_step, query=context_query, changed_paths=(str(document.get("relative_path") or ""),)),
        ).build()
        if not context_result.ok:
            return CommandResult(command, False, context_result.exit_code, "ContextPack v2 could not be built for agent assist.", data=context_result.data, findings=context_result.findings)
        context_pack = (context_result.data or {}).get("context_pack") or {}
        input_tokens = estimate_text_tokens(base_content) + int(((context_pack.get("budget") or {}).get("selected_tokens") or 0)) + estimate_text_tokens(instruction)
        output_tokens = max(128, min(1200, max(256, input_tokens // 3)))
        required_caps = tuple(str(x) for x in (descriptor.get("required_model_capabilities") or ["text_generation"]))
        route_result = self.gateway.controlled_evaluation(
            mode=mode,
            workload_id=f"gsdlc-07-c-{op}",
            required_capabilities=required_caps or ("text_generation",),
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            max_cost_usd=float((descriptor.get("limits") or {}).get("max_cost_usd", 0.5)),
        )
        capability_fallback_used = False
        fallback_caps = tuple(str(x) for x in ((descriptor.get("fallback") or {}).get("required_capabilities") or []))
        if not route_result.ok and fallback_caps and fallback_caps != required_caps:
            route_result = self.gateway.controlled_evaluation(
                mode=mode,
                workload_id=f"gsdlc-07-c-{op}-fallback",
                required_capabilities=fallback_caps,
                estimated_input_tokens=input_tokens,
                estimated_output_tokens=output_tokens,
                max_cost_usd=float((descriptor.get("limits") or {}).get("max_cost_usd", 0.5)),
            )
            capability_fallback_used = route_result.ok
        if not route_result.ok:
            return CommandResult(command, False, route_result.exit_code, "Model Gateway could not select a bounded route for agent assist.", data=route_result.data, findings=route_result.findings)
        route = deepcopy((route_result.data or {}).get("decision") or {})
        summary = deepcopy((route_result.data or {}).get("summary") or {})
        if summary.get("network_used") or summary.get("external_api_used") or summary.get("tool_authority_granted"):
            return self._block(command, "GSDLC07C_ROUTE_BOUNDARY_BLOCK", "07-C route must be hermetic and cannot grant tool authority.")

        plan = {
            "schema_id": "devpilot.gsdlc07c.agent_assist_plan.v1",
            "plan_id": f"aip_{uuid.uuid4().hex}",
            "plan_sha256": "0" * 64,
            "operation": op,
            "mode": mode,
            "document": {
                "document_id": document_id,
                "relative_path": document.get("relative_path"),
                "extension": extension,
                "source_preimage_sha256": expected_source_sha256,
                "expected_revision_sha256": expected_revision_sha256,
                "source_kind": source_kind,
                "import_id": import_id,
                "base_content_sha256": _sha(base_content),
            },
            "instruction": str(instruction or "").strip(),
            "selection": {"start": selection_start, "end": selection_end},
            "agent": {
                "role_id": descriptor.get("agent_role_id"),
                "runtime_agent_id": descriptor.get("runtime_agent_id"),
                "runtime_binding": descriptor.get("runtime_binding"),
                "required_model_capabilities": list(required_caps),
                "routed_model_capabilities": list(fallback_caps if capability_fallback_used else required_caps),
                "capability_fallback_used": capability_fallback_used,
                "fallback": deepcopy(descriptor.get("fallback") or {}),
                "can_approve": False,
            },
            "runtime": {"implementation": "DevPilot governed runtime", "mode": mode, "bounded": True, "tool_execution_enabled": False, "human_review_required": True},
            "model_route": {
                "provider_id": route.get("provider_id"),
                "model_id": route.get("model_id"),
                "access_route_id": route.get("access_route_id"),
                "gateway_adapter_id": route.get("gateway_adapter_id"),
                "estimate": route.get("estimate") or {},
                "network_used": False,
                "external_api_used": False,
                "tool_authority_granted": False,
            },
            "context": {
                "pack_id": context_pack.get("pack_id"),
                "pack_sha256": ((context_pack.get("provenance") or {}).get("pack_sha256")),
                "status": context_pack.get("status"),
                "sources": [{k: s.get(k) for k in ("source_id", "path", "citation_ref", "content_sha256", "trust_tag", "freshness", "selection_reason", "estimated_tokens")} for s in (context_pack.get("sources") or [])],
                "citations": context_pack.get("citations") or [],
                "selected_tokens": ((context_pack.get("budget") or {}).get("selected_tokens")),
            },
            "limits": deepcopy(descriptor.get("limits") or {}),
            "cost": deepcopy(route.get("estimate") or {}),
            "actor": {"actor": actor, "actor_role": actor_role, "session_principal": session_principal},
            "created_at": _now(),
            "network_used": False,
            "external_api_used": False,
            "source_mutations_performed": False,
            "approval_state": "not-requested",
        }
        plan["plan_sha256"] = _canonical_hash({**plan, "plan_sha256": "0" * 64})
        validation = self.schemas.validate_payload(schema="SCHEMA-DEVPL-GSDLC-07-C-AGENT-ASSIST-PLAN-V1", payload=plan, instance_label=plan["plan_id"])
        if not validation.ok:
            return self._block(command, "GSDLC07C_PLAN_SCHEMA_BLOCK", "Generated agent-assist plan failed its registered schema.")
        self._write("plans", plan["plan_id"], plan)
        return CommandResult(command, True, ExitCode.PASS, "Agent-assist plan prepared; human can inspect route/context/cost before run.", data={"plan": plan, "summary": {"pre_run_visible": True, "human_review_required": True, "source_mutations_performed": False, "network_used": False, "external_api_used": False}}, findings=[Finding("GSDLC07C_ASSIST_PLAN_PASS", "Plan exposes agent/model/context/cost before hermetic execution.", Severity.INFO)])

    def run(self, *, plan_id: str, plan_sha256: str, simulate_invalid_output: bool = False) -> CommandResult:
        command = "workspace artifact assist run"
        plan = self._load("plans", plan_id)
        if plan is None:
            return self._block(command, "GSDLC07C_PLAN_NOT_FOUND_BLOCK", "Agent-assist plan does not exist.")
        if plan.get("plan_sha256") != plan_sha256 or _canonical_hash({**plan, "plan_sha256": "0" * 64}) != plan_sha256:
            return self._block(command, "GSDLC07C_PLAN_HASH_BLOCK", "Agent-assist plan hash mismatch; rerun planning.")
        document_id = str((plan.get("document") or {}).get("document_id") or "")
        source_sha = str((plan.get("document") or {}).get("source_preimage_sha256") or "")
        doc_result = self.documents.read_document(document_id)
        if not doc_result.ok or str(((doc_result.data or {}).get("document") or {}).get("sha256") or "") != source_sha:
            return self._block(command, "GSDLC07C_RUN_SOURCE_CONFLICT_BLOCK", "Approved source changed after agent-assist planning.")
        if str((plan.get("context") or {}).get("status") or "") != "grounded":
            return self._block(command, "GSDLC07C_INSUFFICIENT_EVIDENCE_BLOCK", "Agent assist refuses to generate an authoritative proposal with insufficient evidence.")

        base_content = self._base_content(plan)
        if isinstance(base_content, CommandResult):
            return base_content
        structured = self._deterministic_output(plan, base_content)
        if simulate_invalid_output:
            structured.pop("proposed_content", None)
        proposal_id = f"aiprop_{uuid.uuid4().hex}"
        validation_payload = {
            "schema_id": "devpilot.gsdlc07c.agent_assist_structured_output.v1",
            "operation": plan["operation"],
            "proposal_text": structured.get("proposal_text"),
            "proposed_content": structured.get("proposed_content"),
            "critique": structured.get("critique"),
            "untrusted_output": True,
        }
        validation = self.schemas.validate_payload(schema="SCHEMA-DEVPL-GSDLC-07-C-AGENT-ASSIST-STRUCTURED-OUTPUT-V1", payload=validation_payload, instance_label=proposal_id)
        if not validation.ok:
            return self._block(command, "GSDLC07C_STRUCTURED_OUTPUT_BLOCK", "Model/agent output failed the registered structured-output contract.")
        proposed = str(validation_payload["proposed_content"])
        secret = self.secret_guard.scan_text(proposed, subject=proposal_id)
        if secret.effect.value == "block":
            return self._block(command, "GSDLC07C_OUTPUT_SECRET_BLOCK", "Untrusted model output contains secret-like material and was blocked before persistence.")
        diff = "".join(difflib.unified_diff(base_content.splitlines(keepends=True), proposed.splitlines(keepends=True), fromfile="current-draft", tofile="agent-proposal", n=3))
        provenance = self._provenance(plan=plan, proposal_id=proposal_id, proposed_content=proposed, decision="PENDING")
        proposal = {
            "schema_id": "devpilot.gsdlc07c.agent_assist_proposal.v1",
            "proposal_id": proposal_id,
            "proposal_sha256": "0" * 64,
            "plan_id": plan_id,
            "plan_sha256": plan_sha256,
            "operation": plan["operation"],
            "status": "PROPOSED",
            "base_content_sha256": _sha(base_content),
            "proposed_content_sha256": _sha(proposed),
            "proposed_content": proposed,
            "proposal_text": validation_payload["proposal_text"],
            "critique": validation_payload.get("critique") or [],
            "diff": diff,
            "provenance": provenance,
            "decision": None,
            "created_at": _now(),
            "updated_at": _now(),
            "source_mutations_performed": False,
            "workspace_writes_performed": False,
            "network_used": False,
            "external_api_used": False,
            "untrusted_output": True,
            "human_review_required": True,
        }
        proposal["proposal_sha256"] = _canonical_hash({**proposal, "proposal_sha256": "0" * 64})
        pv = self.schemas.validate_payload(schema="SCHEMA-DEVPL-GSDLC-07-C-AGENT-ASSIST-PROPOSAL-V1", payload=proposal, instance_label=proposal_id)
        if not pv.ok:
            return self._block(command, "GSDLC07C_PROPOSAL_SCHEMA_BLOCK", "Generated proposal failed its registered schema.")
        self._write("proposals", proposal_id, proposal)
        return CommandResult(command, True, ExitCode.PASS, "Untrusted agent-assisted proposal generated; no DRAFT/source mutation occurred.", data={"proposal": proposal, "summary": {"diff_required_before_decision": True, "human_review_required": True, "source_mutations_performed": False, "workspace_writes_performed": False, "network_used": False, "external_api_used": False}}, findings=[Finding("GSDLC07C_ASSIST_RUN_PASS", "Proposal is review-only until an authenticated human decision.", Severity.INFO)])

    def decide(
        self,
        *,
        proposal_id: str,
        proposal_sha256: str,
        decision: str,
        actor: str,
        actor_role: str,
        session_principal: str,
        modified_content: str | None = None,
    ) -> CommandResult:
        command = "workspace artifact assist decide"
        proposal = self._load("proposals", proposal_id)
        if proposal is None:
            return self._block(command, "GSDLC07C_PROPOSAL_NOT_FOUND_BLOCK", "Agent-assist proposal does not exist.")
        if proposal.get("proposal_sha256") != proposal_sha256 or _canonical_hash({**proposal, "proposal_sha256": "0" * 64}) != proposal_sha256:
            return self._block(command, "GSDLC07C_PROPOSAL_HASH_BLOCK", "Proposal hash mismatch; review the current proposal again.")
        normalized = str(decision or "").strip().upper()
        if normalized not in {"ACCEPT", "REJECT", "MODIFY"}:
            return self._block(command, "GSDLC07C_DECISION_BLOCK", "Human decision must be ACCEPT, REJECT or MODIFY.")
        existing = proposal.get("decision")
        if isinstance(existing, dict):
            if existing.get("decision") == normalized and existing.get("actor") == actor:
                return CommandResult(command, True, ExitCode.PASS, "Human decision already recorded idempotently.", data={"proposal": proposal, "decision": existing}, findings=[Finding("GSDLC07C_DECISION_IDEMPOTENT_PASS", "Repeated identical decision did not create another draft revision.", Severity.INFO)])
            return self._block(command, "GSDLC07C_DECISION_ALREADY_RECORDED_BLOCK", "Proposal already has a human decision.")
        plan = self._load("plans", str(proposal.get("plan_id") or ""))
        if plan is None:
            return self._block(command, "GSDLC07C_PLAN_NOT_FOUND_BLOCK", "Proposal plan is missing; decision fails closed.")
        if not actor.strip() or not actor_role.strip() or not session_principal.strip():
            return self._block(command, "GSDLC07C_HUMAN_SESSION_REQUIRED_BLOCK", "Authenticated human actor/role/session are required for proposal decisions.")

        chosen_content = str(proposal.get("proposed_content") or "")
        if normalized == "MODIFY":
            if modified_content is None or not str(modified_content).strip():
                return self._block(command, "GSDLC07C_MODIFIED_CONTENT_REQUIRED_BLOCK", "MODIFY requires explicit human-edited content.")
            chosen_content = str(modified_content)
        if normalized != "REJECT":
            secret = self.secret_guard.scan_text(chosen_content, subject=proposal_id)
            if secret.effect.value == "block":
                return self._block(command, "GSDLC07C_DECISION_SECRET_BLOCK", "Human-selected proposal content contains secret-like material.")

        decision_record = {
            "decision": normalized,
            "actor": actor,
            "actor_role": actor_role,
            "session_principal": session_principal,
            "decided_at": _now(),
            "human_reviewed": True,
            "approved_state_granted": False,
            "frozen_state_granted": False,
            "source_mutations_performed": False,
        }
        draft_result: CommandResult | None = None
        if normalized != "REJECT" and str(proposal.get("operation")) != "critique":
            provenance = self._provenance(plan=plan, proposal_id=proposal_id, proposed_content=chosen_content, decision=normalized)
            draft_result = self.drafts.save(
                document_id=str((plan.get("document") or {}).get("document_id") or ""),
                content=chosen_content,
                expected_source_sha256=str((plan.get("document") or {}).get("source_preimage_sha256") or ""),
                expected_revision_sha256=(plan.get("document") or {}).get("expected_revision_sha256"),
                actor=actor,
                actor_role=actor_role,
                session_principal=session_principal,
                event="SAVE",
                agent_provenance=provenance,
            )
            if not draft_result.ok:
                return CommandResult(command, False, draft_result.exit_code, "Human decision could not be persisted as a DRAFT revision.", data=draft_result.data, findings=draft_result.findings)
        proposal["status"] = "DECIDED"
        proposal["decision"] = decision_record
        proposal["updated_at"] = _now()
        proposal["provenance"] = self._provenance(plan=plan, proposal_id=proposal_id, proposed_content=chosen_content, decision=normalized)
        proposal["proposal_sha256"] = "0" * 64
        proposal["proposal_sha256"] = _canonical_hash(proposal)
        self._write("proposals", proposal_id, proposal)
        return CommandResult(command, True, ExitCode.PASS, f"Human {normalized} decision recorded; approved workspace source remains unchanged.", data={"proposal": proposal, "decision": decision_record, "draft": None if draft_result is None else (draft_result.data or {}).get("draft"), "summary": {"human_reviewed": True, "draft_revision_persisted": draft_result is not None, "approved_transition": False, "frozen_transition": False, "source_mutations_performed": False, "network_used": False, "external_api_used": False}}, findings=[Finding("GSDLC07C_HUMAN_DECISION_PASS", "Agent-assisted output remains DRAFT/proposal only; APPROVED/FROZEN transitions were not granted.", Severity.INFO)])

    def get(self, *, proposal_id: str) -> CommandResult:
        proposal = self._load("proposals", proposal_id)
        if proposal is None:
            return self._block("workspace artifact assist get", "GSDLC07C_PROPOSAL_NOT_FOUND_BLOCK", "Agent-assist proposal does not exist.")
        return CommandResult("workspace artifact assist get", True, ExitCode.PASS, "Agent-assist proposal loaded from runtime state.", data={"proposal": proposal}, findings=[])

    def _base_content(self, plan: dict[str, Any]) -> str | CommandResult:
        document = plan.get("document") or {}
        if document.get("source_kind") == "IMPORT":
            result = self.imports.get(import_id=str(document.get("import_id") or ""))
            if not result.ok:
                return CommandResult("workspace artifact assist run", False, result.exit_code, "Imported DRAFT disappeared after planning.", data=result.data, findings=result.findings)
            content = str(((result.data or {}).get("import") or {}).get("normalized_content") or "")
        else:
            result = self.drafts.get(document_id=str(document.get("document_id") or ""))
            if result.ok and isinstance((result.data or {}).get("draft"), dict) and (result.data or {})["draft"].get("active"):
                store = (result.data or {})["draft"]
                current = store.get("current_revision_sha256")
                rev = next((x for x in store.get("revisions", []) if x.get("revision_sha256") == current), None)
                content = str((rev or {}).get("content") or "")
            else:
                doc = self.documents.read_document(str(document.get("document_id") or ""))
                if not doc.ok:
                    return CommandResult("workspace artifact assist run", False, doc.exit_code, "Document disappeared after planning.", data=doc.data, findings=doc.findings)
                content = str(((doc.data or {}).get("document") or {}).get("content") or "")
        if _sha(content) != str(document.get("base_content_sha256") or ""):
            return self._block("workspace artifact assist run", "GSDLC07C_DRAFT_PREIMAGE_CONFLICT_BLOCK", "Draft/import content changed after agent-assist planning; generate a new plan.")
        return content

    def _deterministic_output(self, plan: dict[str, Any], base_content: str) -> dict[str, Any]:
        op = str(plan["operation"])
        instruction = str(plan.get("instruction") or "").strip() or "Improve clarity while preserving governed intent."
        mode = str(plan.get("mode") or "mock")
        extension = str((plan.get("document") or {}).get("extension") or ".md")
        marker = "fake-local" if mode == "fake-local" else "mock"
        critique: list[str] = []
        if op == "generate_draft":
            if extension == ".json":
                proposed = _json_transform(base_content, {"agent_assist": {"mode": marker, "operation": op, "instruction": instruction}})
            else:
                proposed = f"# Agent-assisted draft\n\n{instruction}\n\n## Grounded proposal\n\n{_first_context_note(plan)}\n"
        elif op == "rewrite_selection":
            start = int((plan.get("selection") or {}).get("start") or 0); end = int((plan.get("selection") or {}).get("end") or 0)
            selected = base_content[start:end]
            rewritten = f"{selected.strip()}\n\n> Rewritten ({marker}): {instruction}".strip()
            proposed = base_content[:start] + rewritten + base_content[end:]
        elif op == "critique":
            proposed = base_content
            critique = ["Preserve explicit lifecycle/state language.", f"Review against grounded context: {_first_context_note(plan)}", f"Human instruction: {instruction}"]
        elif op == "improve":
            if extension == ".json": proposed = _json_transform(base_content, {"agent_assist_improvement": instruction})
            else: proposed = base_content.rstrip() + f"\n\n## Improvement proposal ({marker})\n\n{instruction}\n"
        else:
            if extension == ".json": proposed = _json_transform(base_content, {"agent_assist_transform": instruction})
            else: proposed = base_content.rstrip() + f"\n\n<!-- transformed-import proposal ({marker}): {instruction} -->\n"
        return {"proposal_text": f"{op} proposal produced by hermetic {marker} route.", "proposed_content": proposed, "critique": critique}

    def _provenance(self, *, plan: dict[str, Any], proposal_id: str, proposed_content: str, decision: str) -> dict[str, Any]:
        route = plan.get("model_route") or {}; context = plan.get("context") or {}
        return {
            "schema_id": "devpilot.gsdlc07c.agent_provenance.v1",
            "proposal_id": proposal_id,
            "plan_id": plan.get("plan_id"),
            "operation": plan.get("operation"),
            "agent_role_id": (plan.get("agent") or {}).get("role_id"),
            "runtime_agent_id": (plan.get("agent") or {}).get("runtime_agent_id"),
            "runtime_mode": (plan.get("runtime") or {}).get("mode"),
            "provider_id": route.get("provider_id"),
            "model_id": route.get("model_id"),
            "access_route_id": route.get("access_route_id"),
            "context_pack_id": context.get("pack_id"),
            "context_pack_sha256": context.get("pack_sha256"),
            "citations": deepcopy(context.get("citations") or []),
            "estimated_tokens": (route.get("estimate") or {}).get("total_tokens"),
            "estimated_cost_usd": (route.get("estimate") or {}).get("cost_usd"),
            "cost_state": (route.get("estimate") or {}).get("cost_state"),
            "output_sha256": _sha(proposed_content),
            "decision": decision,
            "human_review_required": True,
            "model_output_untrusted": True,
            "approval_state": "not-requested",
            "approved_transition": False,
            "frozen_transition": False,
            "network_used": False,
            "external_api_used": False,
            "source_mutations_performed": False,
        }

    def _path(self, kind: str, identifier: str) -> Path:
        token = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(identifier))[:120]
        return self.assist_root / kind / f"{token}.json"

    def _write(self, kind: str, identifier: str, payload: dict[str, Any]) -> None:
        path = self._path(kind, identifier)
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        with self._lock:
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(raw, encoding="utf-8", newline="\n")
            tmp.replace(path)

    def _load(self, kind: str, identifier: str) -> dict[str, Any] | None:
        path = self._path(kind, identifier)
        if not path.is_file(): return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None

    @staticmethod
    def _block(command: str, finding_id: str, message: str) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"summary": {"source_mutations_performed": False, "network_used": False, "external_api_used": False}}, findings=[Finding(finding_id, message, Severity.BLOCK)])


def _infer_step(path: str) -> str:
    p = path.lower()
    for token, step in (("product", "product-vision"), ("requirement", "requirements"), ("architecture", "architecture"), ("security", "security-plan"), ("test", "test-plan"), ("implementation", "implementation-plan"), ("coding", "coding"), ("review", "review")):
        if token in p: return step
    return "requirements"


def _first_context_note(plan: dict[str, Any]) -> str:
    sources = (plan.get("context") or {}).get("sources") or []
    if not sources: return "No grounded source was available."
    first = sources[0]
    return f"Grounded in {first.get('citation_ref')} ({str(first.get('content_sha256') or '')[:12]}…)."


def _json_transform(content: str, addition: dict[str, Any]) -> str:
    try: value = json.loads(content or "{}")
    except Exception: value = {}
    if not isinstance(value, dict): value = {"value": value}
    value = deepcopy(value); value.update(addition)
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _canonical_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
