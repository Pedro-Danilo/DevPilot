from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.guided_sdlc import AdvisorContext, ExecutionModeAdvisor, GuidedSDLCService, ProjectProgressEngine, ReconciliationError, WorkflowEngineError
from devpilot_core.guided_sdlc.repository import WorkspaceEngineeringStateStoreError
from devpilot_core.story_execution import StoryExecutionStore

from .portfolio_service import PortfolioApplicationService
from .planning_closure_service import PlanningClosureApplicationService
from .pre_code_boundary import load_pre_code_boundary
from .ui_workspace_context import UiWorkspaceContextResolver


class GuidedSDLCApplicationService:
    """Application boundary for Guided SDLC deterministic services.

    B/C operations are read-only. GSDLC-01-D adds bounded reconciliation:
    preview remains source/state read-only; execute may persist only the local
    WorkspaceEngineeringState through its atomic repository. No HTTP route is
    exposed before GSDLC-01-E and managed workspace source/Git stay read-only.
    """

    def __init__(self, root: Path, *, context_resolver: UiWorkspaceContextResolver | None = None) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver or UiWorkspaceContextResolver(self.root)

    def _service(self) -> GuidedSDLCService:
        # Lazy construction preserves ApplicationService compatibility for
        # tests/tools that instantiate a facade over a minimal temporary root.
        return GuidedSDLCService.from_platform_root(self.root)

    @staticmethod
    def _guided_next_from_planning_closure(closure: dict[str, Any]) -> dict[str, Any]:
        journey_state = str(closure.get("journey_state") or "UNKNOWN").upper()
        closure_next = closure.get("next_action") if isinstance(closure.get("next_action"), dict) else {}
        if journey_state == "IMPLEMENTING_READY":
            return {
                "schema_id": "SCHEMA-DEVPL-GUIDED-SDLC-NEXT-ACTION-V1",
                "schema_version": "1.0",
                "action_id": "next.implementing-ready-story-context",
                "kind": "ADVANCE_TRANSITION",
                "priority": 60,
                "reason_code": "IMPLEMENTING_READY_STORY_CONTEXT_NEXT",
                "explanation": "Planning is complete and FROZEN. Continue to Story Code Workbench for the first READY story context and implementation route.",
                "target_phase": None,
                "target_step": "story-code-workbench",
                "transition_id": None,
                "navigation_target": "ui.story-code-workbench",
                "required_prerequisites": ["planning:IMPLEMENTING_READY"],
                "approval_needed": False,
                "mutating": False,
                "dry_run_required": False,
                "available": True,
                "disabled_reason": None,
                "expected_evidence": ["roadmap:FROZEN", "backlog:FROZEN", "sprint:FROZEN", "sprint:executable"],
                "source_state_fingerprint": None,
                "executes_action": False,
                "network_used": False,
                "external_api_used": False,
                "source_mutations_performed": False,
            }
        label = str(closure_next.get("label") or "Continue Planning").strip()
        reason = str(closure_next.get("reason_code") or "PLANNING_IN_PROGRESS").strip()
        return {
            "schema_id": "SCHEMA-DEVPL-GUIDED-SDLC-NEXT-ACTION-V1",
            "schema_version": "1.0",
            "action_id": f"next.planning.{reason.lower().replace('_', '-')}",
            "kind": "CONTINUE_STEP",
            "priority": 60,
            "reason_code": reason,
            "explanation": f"Planning is in progress. {label}.",
            "target_phase": None,
            "target_step": "planning-roadmap",
            "transition_id": None,
            "navigation_target": str(closure_next.get("navigation_target") or "planning-roadmap"),
            "required_prerequisites": ["pre-code-readiness:PASS"],
            "approval_needed": False,
            "mutating": False,
            "dry_run_required": False,
            "available": bool(closure_next.get("available", True)),
            "disabled_reason": None,
            "expected_evidence": [f"planning:{journey_state}"],
            "source_state_fingerprint": None,
            "executes_action": False,
            "network_used": False,
            "external_api_used": False,
            "source_mutations_performed": False,
        }

    def _apply_planning_journey_overlay(self, *, status_payload: dict[str, Any], next_payload: dict[str, Any], pre_code: dict[str, Any]) -> dict[str, Any]:
        if not pre_code.get("pre_code_ready"):
            return next_payload
        result = PlanningClosureApplicationService(self.root, context_resolver=self.context_resolver).status(effective_roles=[])
        if not result.ok or not isinstance(result.data, dict):
            return next_payload
        closure = (result.data.get("planning_closure") or {}) if isinstance(result.data.get("planning_closure"), dict) else {}
        if not closure:
            return next_payload
        journey_state = str(closure.get("journey_state") or "UNKNOWN").upper()
        # Keep Guided ProjectStatus within its existing governed schema: Planning
        # closure is an internal authority used to reconcile the current step and
        # next action, not a new ad-hoc ProjectStatus field. The global MIPSoftware
        # phase/lifecycle projection remains untouched.
        if journey_state == "IMPLEMENTING_READY":
            status_payload["current_step"] = "story-context-readiness"
            return self._guided_next_from_planning_closure(closure)
        if journey_state == "PLANNING":
            status_payload["current_step"] = "planning"
            return self._guided_next_from_planning_closure(closure)
        return next_payload

    def evaluate_transition(
        self,
        *,
        workspace_id: str,
        transition_id: str,
        evidence: dict[str, Any] | None = None,
    ) -> CommandResult:
        try:
            result = self._service().evaluate_transition(
                workspace_id=workspace_id,
                transition_id=transition_id,
                evidence=evidence,
            )
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, ReconciliationError, KeyError) as exc:
            return self._error("guided_sdlc.transition.evaluate", exc)
        return self._result("guided_sdlc.transition.evaluate", result.to_payload())

    def preview_transition(
        self,
        *,
        workspace_id: str,
        transition_id: str,
        evidence: dict[str, Any] | None = None,
        updated_at_utc: str,
    ) -> CommandResult:
        try:
            preview = self._service().preview_transition(
                workspace_id=workspace_id,
                transition_id=transition_id,
                evidence=evidence,
                updated_at_utc=updated_at_utc,
            )
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, ReconciliationError, KeyError) as exc:
            return self._error("guided_sdlc.transition.preview", exc)
        return self._result("guided_sdlc.transition.preview", preview.to_payload())

    def project_status(
        self,
        *,
        workspace_id: str,
        observed_at_utc: str,
        expected_state_fingerprint: str | None = None,
    ) -> CommandResult:
        try:
            projection = self._service().project_status(
                workspace_id=workspace_id,
                observed_at_utc=observed_at_utc,
                expected_state_fingerprint=expected_state_fingerprint,
            )
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, KeyError, ValueError):
            projection = ProjectProgressEngine.unknown(
                workspace_id=workspace_id,
                observed_at_utc=observed_at_utc,
            )
        return self._projection_result("guided_sdlc.project.status", projection.status.to_payload())

    def next_action(
        self,
        *,
        workspace_id: str,
        observed_at_utc: str,
        expected_state_fingerprint: str | None = None,
    ) -> CommandResult:
        try:
            projection = self._service().next_action(
                workspace_id=workspace_id,
                observed_at_utc=observed_at_utc,
                expected_state_fingerprint=expected_state_fingerprint,
            )
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, KeyError, ValueError):
            projection = ProjectProgressEngine.unknown(
                workspace_id=workspace_id,
                observed_at_utc=observed_at_utc,
            )
        return self._projection_result("guided_sdlc.next_action", projection.next_action.to_payload())

    def project_status_primary(
        self,
        *,
        workspace_id: str | None,
        observed_at_utc: str,
        expected_state_fingerprint: str | None = None,
    ) -> CommandResult:
        """Return the actor-neutral Project Status payload for API/UI consumption.

        GSDLC-01-E keeps this operation read-only. If workspace_id is omitted,
        the active registered workspace is resolved through the existing
        PortfolioApplicationService. Missing engineering state is represented
        honestly as EMPTY/UNKNOWN instead of being synthesized as PASS.
        """

        explicit = str(workspace_id or "").strip()
        context = self.context_resolver.resolve()
        server_active = ""
        if context.configured and context.valid:
            server_active = str(context.active_workspace_id or "").strip()
        portfolio = PortfolioApplicationService(self.root, context_resolver=self.context_resolver).status()
        portfolio_active = ""
        if isinstance(portfolio.data, dict):
            portfolio_active = str((portfolio.data.get("summary") or {}).get("active_workspace_id") or "").strip()
        resolved = explicit or server_active or portfolio_active
        if not resolved:
            unknown = ProjectProgressEngine.unknown(workspace_id="unknown", observed_at_utc=observed_at_utc)
            return CommandResult(
                command="guided_sdlc.project_status",
                ok=True,
                exit_code=ExitCode.PASS,
                message="No active registered workspace is available for Project Status.",
                data={
                    "ui_state": "EMPTY",
                    "workspace_id": None,
                    "project_status": unknown.status.to_payload(),
                    "next_action": unknown.next_action.to_payload(),
                    "read_only": True,
                    "actor_neutral": True,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                },
                findings=[],
            )

        try:
            projection = self._service().project_status(
                workspace_id=resolved,
                observed_at_utc=observed_at_utc,
                expected_state_fingerprint=expected_state_fingerprint,
            )
            next_projection = self._service().next_action(
                workspace_id=resolved,
                observed_at_utc=observed_at_utc,
                expected_state_fingerprint=expected_state_fingerprint,
            )
            status_payload = projection.status.to_payload()
            next_payload = next_projection.next_action.to_payload()
            pre_code = load_pre_code_boundary(self.root, resolved)
            if pre_code.get("available"):
                status_payload["pre_code_profile"] = pre_code
                progress = dict(status_payload.get("progress") or {})
                progress["mipsoftware_percent"] = progress.get("percent")
                progress["active_profile"] = "PRE_CODE"
                progress["active_profile_percent"] = pre_code.get("percent")
                progress["pre_code_stages_frozen"] = pre_code.get("mandatory_stages_frozen")
                progress["pre_code_stages_total"] = pre_code.get("mandatory_stages_total")
                status_payload["progress"] = progress
                status_payload["artifact_readiness"] = {
                    "status": "READY" if pre_code.get("all_stages_frozen") else "IN_PROGRESS",
                    "total": pre_code.get("mandatory_stages_total", 7),
                    "ready": pre_code.get("mandatory_stages_frozen", 0),
                    "attention": max(0, int(pre_code.get("mandatory_stages_total", 7)) - int(pre_code.get("mandatory_stages_frozen", 0))),
                    "counts": {"FROZEN": pre_code.get("mandatory_stages_frozen", 0)},
                    "authority": "guided-pre-code-runtime",
                }
                status_payload["miasi"] = dict(pre_code.get("miasi") or status_payload.get("miasi") or {})
                mip = dict(status_payload.get("mipsoftware") or {})
                # MIPSoftware remains the cross-lifecycle normative standard. The
                # Greenfield Pre-code wizard is a bounded execution/conformance
                # profile mapped to selected MIP steps; it does not prove that the
                # formal global MIP registry has advanced through every mandatory
                # phase. Keep both facts explicit instead of labelling the standard
                # itself as NOT_STARTED.
                mip["authority_scope"] = "global-lifecycle"
                mip["standard_applies"] = True
                mip["standard_scope"] = "cross-lifecycle"
                mip["pre_code_profile_status"] = "COMPLETE" if pre_code.get("all_stages_frozen") else "IN_PROGRESS"
                mip["pre_code_profile_conformance"] = "APPLIED" if pre_code.get("all_stages_frozen") else "IN_PROGRESS"
                mip["pre_code_profile_is_separate_authority"] = False
                mip["pre_code_profile_is_separate_execution_profile"] = True
                mip["formal_registry_phase"] = status_payload.get("phase")
                mip["formal_registry_lifecycle_status"] = status_payload.get("lifecycle_status")
                mip["formal_registry_synchronized"] = False
                mip["formal_registry_reason_code"] = "BOUNDED_PRE_CODE_PROFILE_NOT_MAPPED_TO_GLOBAL_MIP_PHASE"
                status_payload["mipsoftware"] = mip
                if pre_code.get("all_stages_frozen"):
                    status_payload["current_step_global_mipsoftware"] = status_payload.get("current_step")
                    status_payload["current_step"] = "planning-readiness" if pre_code.get("pre_code_ready") else "pre-code-readiness"
                    if pre_code.get("pre_code_ready"):
                        next_payload = {
                            "schema_id": "SCHEMA-DEVPL-GUIDED-SDLC-NEXT-ACTION-V1", "schema_version": "1.0",
                            "action_id": "next.pre-code-ready-planning", "kind": "ADVANCE_TRANSITION", "priority": 60,
                            "reason_code": "PRE_CODE_READY_PLANNING_NEXT",
                            "explanation": "Pre-code readiness is PASS. Continue to Roadmap/Planning without mutating the global MIPSoftware lifecycle projection.",
                            "target_phase": None, "target_step": "planning-roadmap", "transition_id": None,
                            "navigation_target": "planning-roadmap", "required_prerequisites": [], "approval_needed": False,
                            "mutating": False, "dry_run_required": False, "available": True, "disabled_reason": None,
                            "expected_evidence": ["pre-code-readiness:PASS"], "source_state_fingerprint": None,
                            "executes_action": False, "network_used": False, "external_api_used": False, "source_mutations_performed": False,
                        }
                    else:
                        next_payload = {
                            "schema_id": "SCHEMA-DEVPL-GUIDED-SDLC-NEXT-ACTION-V1", "schema_version": "1.0",
                            "action_id": "next.pre-code-miasi-applicability", "kind": "RESOLVE_BLOCKER", "priority": 30,
                            "reason_code": "MIASI_APPLICABILITY_REQUIRED",
                            "explanation": "The seven Pre-code artifacts are FROZEN. Complete the explicit MIASI applicability decision to evaluate strict Pre-code readiness.",
                            "target_phase": None, "target_step": "pre-code-readiness", "transition_id": None,
                            "navigation_target": "pre-code", "required_prerequisites": ["seven-pre-code-stages-frozen"], "approval_needed": False,
                            "mutating": False, "dry_run_required": False, "available": True, "disabled_reason": None,
                            "expected_evidence": ["miasi-applicability-decision"], "source_state_fingerprint": None,
                            "executes_action": False, "network_used": False, "external_api_used": False, "source_mutations_performed": False,
                        }
            next_payload = self._apply_planning_journey_overlay(status_payload=status_payload, next_payload=next_payload, pre_code=pre_code)
            freshness = str((status_payload.get("freshness") or {}).get("status") or "UNKNOWN").upper()
            revalidation = str((status_payload.get("revalidation") or {}).get("status") or "UNKNOWN").upper()
            lifecycle = str(status_payload.get("lifecycle_status") or "UNKNOWN").upper()
            current_step = str(status_payload.get("current_step") or "").strip()
            miasi_gate = str((status_payload.get("miasi") or {}).get("gate_status") or "UNKNOWN").upper()
            blocker_rows = [dict(row) for row in (status_payload.get("blockers") or []) if isinstance(row, dict)]
            lifecycle_reconciliation: dict[str, Any] = {}
            if revalidation in {"REQUIRED", "IN_PROGRESS"} or lifecycle == "REVALIDATION_REQUIRED":
                ui_state = "REVALIDATION_REQUIRED"
            elif lifecycle == "RELEASED" and current_step == "local-release-closed" and freshness != "STALE":
                authoritative_categories = {"release", "git", "security", "revalidation", "source", "source-integrity", "runtime"}
                authoritative_blockers = [row for row in blocker_rows if str(row.get("category") or "").lower() in authoritative_categories]
                non_authoritative_gaps = [row for row in blocker_rows if row not in authoritative_blockers]
                if miasi_gate == "BLOCK":
                    non_authoritative_gaps.append({"category":"miasi","code":"POST_RELEASE_MIASI_DOMAIN_GAP"})
                if str((status_payload.get("artifact_readiness") or {}).get("status") or "").upper() in {"UNKNOWN", "ATTENTION_REQUIRED"}:
                    non_authoritative_gaps.append({"category":"artifact","code":"POST_RELEASE_ARTIFACT_DOMAIN_GAP"})
                if str((status_payload.get("planning") or {}).get("status") or "").upper() == "UNKNOWN":
                    non_authoritative_gaps.append({"category":"planning","code":"POST_RELEASE_PLANNING_DOMAIN_GAP"})
                ui_state = "BLOCKED" if authoritative_blockers else "READY"
                lifecycle_reconciliation = {
                    "status": "BLOCKED_BY_AUTHORITATIVE_DOMAIN" if authoritative_blockers else "RELEASED_WITH_NON_AUTHORITATIVE_GAPS",
                    "display_state": "BLOCKED" if authoritative_blockers else "RELEASED",
                    "authoritative_lifecycle": "RELEASED",
                    "authoritative_blocker_count": len(authoritative_blockers),
                    "non_authoritative_gap_count": len(non_authoritative_gaps),
                    "non_authoritative_gap_codes": sorted({str(row.get("code") or row.get("category") or "gap") for row in non_authoritative_gaps}),
                    "blockers_preserved": True,
                    "hidden_blockers": False,
                }
            elif lifecycle == "BLOCKED" or miasi_gate == "BLOCK" or blocker_rows:
                ui_state = "BLOCKED"
            elif freshness == "STALE":
                ui_state = "STALE"
            elif status_payload.get("reason") == "unknown":
                ui_state = "UNKNOWN"
            else:
                ui_state = "READY"
            pre_code = status_payload.get("pre_code_profile") if isinstance(status_payload.get("pre_code_profile"), dict) else {}
            if pre_code.get("all_stages_frozen") and not pre_code.get("pre_code_ready"):
                ui_state = "BLOCKED"
            elif pre_code.get("pre_code_ready"):
                ui_state = "READY"
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, ReconciliationError, KeyError, ValueError):
            unknown = ProjectProgressEngine.unknown(workspace_id=resolved, observed_at_utc=observed_at_utc)
            status_payload = unknown.status.to_payload()
            next_payload = unknown.next_action.to_payload()
            ui_state = "EMPTY"
            lifecycle_reconciliation = {}

        # StoryExecution is an independent runtime authority. Project Status must
        # expose the current story even when WorkspaceEngineeringState is not yet
        # materialized and the engineering projection legitimately falls back to
        # UNKNOWN/EMPTY. This keeps the read-only status surface truthful without
        # synthesizing an engineering-state PASS.
        planning_payload = status_payload.get("planning")
        if isinstance(planning_payload, dict):
            story_root = context.effective_workspace_root if context.configured and context.valid else self.root
            story_workspace_id = server_active or resolved
            current_story = StoryExecutionStore(
                story_root, workspace_id=story_workspace_id
            ).current_story_projection()
            planning_payload["current_story"] = current_story
            if isinstance(current_story, dict) and str(current_story.get("status") or "").upper() == "DONE":
                planning_payload["story_cycle"] = {
                    "status": "STORY_COMPLETE",
                    "next_selection_ready": True,
                    "next_kind": "NEXT_STORY_OR_SPRINT",
                    "navigation_target": "ui.story-code-workbench",
                    "reason_code": "CURRENT_STORY_DONE",
                    "read_only": True,
                    "server_authoritative": True,
                    "source_mutations_performed": False,
                }
            else:
                planning_payload["story_cycle"] = {
                    "status": "STORY_ACTIVE" if isinstance(current_story, dict) else "NO_ACTIVE_STORY",
                    "next_selection_ready": False,
                    "next_kind": None,
                    "navigation_target": None,
                    "reason_code": "CURRENT_STORY_NOT_DONE" if isinstance(current_story, dict) else "NO_ACTIVE_STORY",
                    "read_only": True,
                    "server_authoritative": True,
                    "source_mutations_performed": False,
                }

        return CommandResult(
            command="guided_sdlc.project_status",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Project Status projected through the Guided SDLC application boundary.",
            data={
                "ui_state": ui_state,
                "workspace_id": resolved,
                "project_status": status_payload,
                "next_action": next_payload,
                "lifecycle_reconciliation": lifecycle_reconciliation,
                "read_only": True,
                "actor_neutral": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
            },
            findings=[],
        )

    def step_actions_primary(
        self,
        *,
        workspace_id: str | None,
        observed_at_utc: str,
        effective_roles: list[str] | tuple[str, ...],
        workspace_scopes: list[str] | tuple[str, ...],
        expected_state_fingerprint: str | None = None,
    ) -> CommandResult:
        """Return the actor-aware, server-policy-bound Step Action Advisor projection.

        The authenticated principal is resolved by the API security/RBAC layer;
        this method receives only sanitized canonical roles/scopes. The advisor
        is read-only and never grants target-route capability.
        """

        status_result = self.project_status_primary(
            workspace_id=workspace_id,
            observed_at_utc=observed_at_utc,
            expected_state_fingerprint=expected_state_fingerprint,
        )
        resolved = str((status_result.data or {}).get("workspace_id") or "").strip()
        project_status = (status_result.data or {}).get("project_status")
        if not resolved or not isinstance(project_status, dict):
            return CommandResult(
                command="guided_sdlc.step_actions",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Step Action Advisor requires an active server-valid project context.",
                data={
                    "ui_state": "BLOCKED",
                    "workspace_id": None,
                    "current_step": None,
                    "advisor": None,
                    "read_only": True,
                    "actor_neutral": False,
                    "server_authoritative": True,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "source_mutations_performed": False,
                },
                findings=[Finding(id="STEP_ACTION_ACTIVE_PROJECT_REQUIRED", message="An active registered workspace/project is required.", severity=Severity.BLOCK)],
            )

        current_step = str(project_status.get("current_step") or "").strip()
        pre_code = project_status.get("pre_code_profile") if isinstance(project_status.get("pre_code_profile"), dict) else {}
        if current_step == "story-context-readiness":
            action_id = "typed.implementing-ready-story-context"
            card = {
                "action_id": action_id, "kind": "TYPED_OPERATION",
                "label": "Abrir Story Code Workbench",
                "purpose": "Planning está completo y FROZEN; continúa al primer contexto de historia READY y su ruta de implementación.",
                "availability": "AVAILABLE", "executable": True, "disabled_reasons": [],
                "prerequisites": [{"prerequisite_id": "planning-implementing-ready", "satisfied": True, "reason": "Roadmap/Backlog/Sprint FROZEN; Planning IMPLEMENTING_READY"}],
                "required_roles": ["owner"], "effective_roles": sorted({str(x) for x in effective_roles}),
                "risk": {"level": "low", "policy_refs": ["PlanningClosureApplicationService"]},
                "side_effects": ["none"], "approval_required": False,
                "network_required": False, "external_api_required": False,
                "cost": {"applicable": False, "value": None, "unit": "USD", "reason": "local deterministic route"},
                "tokens": {"applicable": False, "value": None, "unit": "tokens", "reason": "no model execution"},
                "rank": 1, "recommended": True,
                "navigation_target": "ui.story-code-workbench",
                "configuration_target": None, "typed_operation_id": action_id,
                "api_route_id": None,
                "source_refs": ["guided-project-status", "PlanningClosureApplicationService"], "agent_descriptor": None,
            }
            import hashlib, json
            advisor = {
                "workspace_id": resolved, "current_step": current_step, "status": "PASS",
                "recommended_action_id": action_id, "actions": [card],
                "decision_fingerprint": hashlib.sha256(json.dumps(card, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
                "authority": {"server_rbac": True, "policy": True, "planning_closure": True},
                "safety": {"advisor_grants_capability": False, "network_used": False, "external_api_used": False, "source_mutations_performed": False},
            }
            return CommandResult(
                command="guided_sdlc.step_actions", ok=True, exit_code=ExitCode.PASS,
                message="Step Action Advisor projected the post-Planning Story Code boundary from authoritative Guided/Planning state.",
                data={"ui_state":"READY","workspace_id":resolved,"current_step":current_step,"advisor":advisor,"read_only":True,"actor_neutral":False,"server_authoritative":True,"network_used":False,"external_api_used":False,"model_execution_used":False,"mutations_performed":False,"source_mutations_performed":False},
                findings=[],
            )
        if pre_code.get("all_stages_frozen"):
            ready = bool(pre_code.get("pre_code_ready"))
            action_id = "typed.pre-code-ready-planning" if ready else "typed.miasi-applicability"
            card = {
                "action_id": action_id, "kind": "TYPED_OPERATION",
                "label": "Continuar a Roadmap" if ready else "Resolver aplicabilidad MIASI",
                "purpose": "Pre-code está READY; la siguiente frontera es Planning." if ready else "Clasificar explícitamente si el producto usa capacidades AI/agentic y reevaluar readiness estricta.",
                "availability": "AVAILABLE", "executable": True, "disabled_reasons": [],
                "prerequisites": [{"prerequisite_id": "seven-pre-code-stages-frozen", "satisfied": True, "reason": "7/7 stages FROZEN"}],
                "required_roles": ["owner"], "effective_roles": sorted({str(x) for x in effective_roles}),
                "risk": {"level": "low" if ready else "medium", "policy_refs": ["MIASIApplicabilityEvaluator"]},
                "side_effects": ["none"] if ready else ["platform-runtime-only"], "approval_required": False,
                "network_required": False, "external_api_required": False,
                "cost": {"applicable": False, "value": None, "unit": "USD", "reason": "local deterministic route"},
                "tokens": {"applicable": False, "value": None, "unit": "tokens", "reason": "no model execution"},
                "rank": 1, "recommended": True,
                "navigation_target": "/planning/roadmap" if ready else "/pre-code",
                "configuration_target": None, "typed_operation_id": action_id,
                "api_route_id": None if ready else "api.guided-sdlc.pre-code.miasi-applicability",
                "source_refs": ["guided-pre-code-runtime", "MIASIApplicabilityEvaluator"], "agent_descriptor": None,
            }
            import hashlib, json
            advisor = {
                "workspace_id": resolved, "current_step": current_step, "status": "PASS",
                "recommended_action_id": action_id, "actions": [card],
                "decision_fingerprint": hashlib.sha256(json.dumps(card, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
                "authority": {"server_rbac": True, "policy": True, "pre_code_runtime": True},
                "safety": {"advisor_grants_capability": False, "network_used": False, "external_api_used": False, "source_mutations_performed": False},
            }
            return CommandResult(
                command="guided_sdlc.step_actions", ok=True, exit_code=ExitCode.PASS,
                message="Step Action Advisor projected the C-03 boundary action from authoritative Pre-code runtime state.",
                data={"ui_state":"READY","workspace_id":resolved,"current_step":current_step,"advisor":advisor,"read_only":True,"actor_neutral":False,"server_authoritative":True,"network_used":False,"external_api_used":False,"model_execution_used":False,"mutations_performed":False,"source_mutations_performed":False},
                findings=[],
            )
        context = AdvisorContext.from_payload(
            workspace_id=resolved,
            current_step=current_step,
            effective_roles=effective_roles,
            workspace_scopes=workspace_scopes,
            project_status=project_status,
        )
        decision = ExecutionModeAdvisor(self.root).advise(context)
        payload = decision.to_payload()
        allowed = decision.status == "PASS" and bool(decision.recommended_action_id)
        findings = [] if allowed else [
            Finding(
                id="STEP_ACTION_NO_EXECUTABLE_ROUTE",
                message="No current-step action is executable under the authoritative prerequisites/RBAC/policy.",
                severity=Severity.BLOCK,
                metadata={"current_step": current_step},
            )
        ]
        return CommandResult(
            command="guided_sdlc.step_actions",
            ok=allowed,
            exit_code=ExitCode.PASS if allowed else ExitCode.BLOCK,
            message="Step Action Advisor derived deterministic server-policy-bound options." if allowed else "Step Action Advisor is explicitly blocked.",
            data={
                "ui_state": "READY" if allowed else "BLOCKED",
                "workspace_id": resolved,
                "current_step": current_step,
                "advisor": payload,
                "read_only": True,
                "actor_neutral": False,
                "server_authoritative": True,
                "network_used": False,
                "external_api_used": False,
                "model_execution_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
            },
            findings=findings,
        )

    def reconcile_preview(
        self,
        *,
        workspace_id: str,
        updated_at_utc: str,
        observed_at_utc: str,
    ) -> CommandResult:
        try:
            reconciliation, projection = self._service().reconcile_project_status(
                workspace_id=workspace_id,
                updated_at_utc=updated_at_utc,
                observed_at_utc=observed_at_utc,
                execute=False,
            )
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, ReconciliationError, KeyError, ValueError) as exc:
            return self._error("guided_sdlc.reconcile.preview", exc)
        return CommandResult(
            command="guided_sdlc.reconcile.preview",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Guided SDLC reconciliation preview completed deterministically.",
            data={
                "reconciliation": reconciliation.to_payload(),
                "project_status": projection.status.to_payload(),
                "next_action": projection.next_action.to_payload(),
                "execute": False,
            },
            findings=[],
        )

    def reconcile_execute(
        self,
        *,
        workspace_id: str,
        updated_at_utc: str,
        observed_at_utc: str,
    ) -> CommandResult:
        try:
            reconciliation, projection = self._service().reconcile_project_status(
                workspace_id=workspace_id,
                updated_at_utc=updated_at_utc,
                observed_at_utc=observed_at_utc,
                execute=True,
            )
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, ReconciliationError, KeyError, ValueError) as exc:
            return self._error("guided_sdlc.reconcile.execute", exc)
        return CommandResult(
            command="guided_sdlc.reconcile.execute",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Guided SDLC reconciliation persisted engineering-state only.",
            data={
                "reconciliation": reconciliation.to_payload(),
                "project_status": projection.status.to_payload(),
                "next_action": projection.next_action.to_payload(),
                "execute": True,
                "managed_workspace_source_mutated": False,
            },
            findings=[],
        )

    def _projection_result(self, command: str, payload: dict[str, Any]) -> CommandResult:
        unknown = payload.get("reason") == "unknown" or payload.get("reason_code") in {
            "WORKSPACE_ENGINEERING_STATE_UNKNOWN",
            "NEXT_ACTION_UNKNOWN",
        }
        return CommandResult(
            command=command,
            ok=not unknown,
            exit_code=ExitCode.PASS if not unknown else ExitCode.BLOCK,
            message="Guided SDLC projection derived deterministically." if not unknown else "Guided SDLC projection is unknown.",
            data=payload,
            findings=[] if not unknown else [
                Finding(
                    id=str(payload.get("reason_code") or "WORKSPACE_ENGINEERING_STATE_UNKNOWN"),
                    message="Project status/next action could not be derived from authoritative state.",
                    severity=Severity.BLOCK,
                )
            ],
        )

    def _result(self, command: str, payload: dict[str, Any]) -> CommandResult:
        evaluation = payload.get("evaluation", payload)
        allowed = evaluation.get("decision") == "PASS"
        findings = [
            Finding(
                id=str(item.get("code", "GUIDED_SDLC_BLOCKER")),
                message=str(item.get("message", "Transition is blocked.")),
                severity=Severity.BLOCK,
                metadata={
                    "category": item.get("category"),
                    "subject": item.get("subject"),
                },
            )
            for item in evaluation.get("blockers", [])
        ]
        return CommandResult(
            command=command,
            ok=allowed,
            exit_code=ExitCode.PASS if allowed else ExitCode.BLOCK,
            message="Guided SDLC transition is allowed." if allowed else "Guided SDLC transition is blocked.",
            data=payload,
            findings=findings,
        )

    def _error(self, command: str, exc: Exception) -> CommandResult:
        return CommandResult(
            command=command,
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Guided SDLC request could not be evaluated.",
            data={"network_used": False, "external_api_used": False},
            findings=[
                Finding(
                    id="GUIDED_SDLC_TRANSITION_INPUT_BLOCKED",
                    message=str(exc),
                    severity=Severity.BLOCK,
                )
            ],
        )
