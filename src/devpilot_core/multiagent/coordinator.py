from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.agents import AgentRuntime
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.miasi import AgentSpec, MiasiRegistryValidator, PolicyRule
from devpilot_core.multiagent.handoff import HandoffRecord
from devpilot_core.observability import EventLogger, EventRecord
from devpilot_core.policy import PolicyEngine, PolicyRequest

_IMPLEMENTED_AGENT_STATUSES = {"implemented", "implemented-initial"}
_COORDINATOR_AGENT_ID = "multiagent.coordinator"
_DEFAULT_TARGET = "src/devpilot_core/connectors"

_WORKFLOWS: dict[str, list[dict[str, str]]] = {
    "repo-review": [
        {
            "step_id": "repo-analysis",
            "agent_id": "repo.analysis",
            "reason": "Inventory and repository health signals provide the first review context.",
        },
        {
            "step_id": "code-review",
            "agent_id": "code.review",
            "reason": "CodeReviewAgent receives the repository analysis context through an explicit governed handoff.",
        },
        {
            "step_id": "security-review",
            "agent_id": "security.agent",
            "reason": "SecurityAgent receives prior review context to check local safety boundaries without mutation.",
        },
    ]
}


@dataclass(frozen=True)
class MultiAgentRunOptions:
    """Options for the FUNC-SPRINT-90 coordinator MVP."""

    workflow: str
    target: str = _DEFAULT_TARGET
    dry_run: bool = True
    max_steps: int = 10


class MultiAgentCoordinator:
    """Sequential dry-run coordinator with explicit handoffs.

    This MVP does not implement graph planning, autonomous routing, shared
    semantic memory or destructive actions. It executes one allowlisted workflow
    over already implemented local agents, validates MIASI status before every
    step, checks PolicyEngine for the handoff/read boundary and emits a trace
    event for each handoff.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.policy = PolicyEngine(self.root)
        self.events = EventLogger(self.root)

    def run(self, options: MultiAgentRunOptions) -> CommandResult:
        workflow_id = _canonical_workflow(options.workflow)
        target = options.target or _DEFAULT_TARGET
        max_steps = max(1, min(int(options.max_steps), 25))

        if not options.dry_run:
            return self._blocked(
                workflow_id,
                target,
                [
                    Finding(
                        "MULTIAGENT_REQUIRES_DRY_RUN",
                        "MultiAgentCoordinator MVP only runs in dry-run/report-only mode.",
                        Severity.BLOCK,
                        metadata={"workflow": workflow_id},
                    )
                ],
                message="MultiAgentCoordinator blocked: --dry-run is required.",
            )

        workflow = _WORKFLOWS.get(workflow_id)
        if workflow is None:
            return self._blocked(
                workflow_id,
                target,
                [
                    Finding(
                        "MULTIAGENT_WORKFLOW_UNKNOWN",
                        "Requested multiagent workflow is not registered in the local allowlist.",
                        Severity.BLOCK,
                        metadata={"workflow": workflow_id, "available_workflows": sorted(_WORKFLOWS)},
                    )
                ],
                message="MultiAgentCoordinator blocked: workflow is unknown.",
            )

        workflow = workflow[:max_steps]
        bundle, load_findings = MiasiRegistryValidator(self.root).load_bundle()
        if load_findings or bundle is None:
            return self._blocked(workflow_id, target, load_findings, message="MultiAgentCoordinator blocked: MIASI registries could not be loaded.")

        agents = {agent.agent_id: agent for agent in bundle.agents}
        rules = {rule.rule_id: rule for rule in bundle.rules}
        coordinator = agents.get(_COORDINATOR_AGENT_ID)
        governance_findings = self._validate_coordinator_contract(coordinator, rules)
        governance_findings.extend(self._validate_workflow_agents(workflow, agents))
        if governance_findings:
            return self._blocked(workflow_id, target, governance_findings, message="MultiAgentCoordinator blocked by MIASI governance.")

        steps: list[dict[str, Any]] = []
        handoffs: list[HandoffRecord] = []
        findings: list[Finding] = []
        previous_agent: str | None = None
        policy_checks_total = 0
        trace_events_total = 0
        child_blocking_total = 0
        child_failing_total = 0
        child_non_ok_total = 0

        runtime = AgentRuntime(self.root)
        for index, step in enumerate(workflow, start=1):
            agent_id = step["agent_id"]
            agent_spec = agents[agent_id]
            handoff = HandoffRecord(
                workflow_id=workflow_id,
                sequence=index,
                from_agent=previous_agent,
                to_agent=agent_id,
                reason=step["reason"],
                target=target,
                dry_run=True,
                metadata={"step_id": step["step_id"], "coordinator_agent_id": _COORDINATOR_AGENT_ID},
            )
            policy_result = self._evaluate_handoff_policy(handoff)
            policy_checks_total += 1
            handoff.policy_checked = True
            handoff.policy_allowed = policy_result.ok
            if not policy_result.ok:
                findings.extend(policy_result.findings)
                event = self._emit_handoff_event(handoff, ok=False, exit_code=policy_result.exit_code, message="Handoff blocked by PolicyEngine.")
                handoff.trace_event_emitted = True
                handoff.event_id = event.get("event_id")
                handoff.event_path = event.get("path")
                trace_events_total += 1
                handoffs.append(handoff)
                return self._blocked(
                    workflow_id,
                    target,
                    findings,
                    message="MultiAgentCoordinator blocked by handoff policy.",
                    partial_steps=steps,
                    partial_handoffs=handoffs,
                )

            event = self._emit_handoff_event(handoff, ok=True, exit_code=ExitCode.PASS, message="Explicit handoff traced before agent run.")
            handoff.trace_event_emitted = True
            handoff.event_id = event.get("event_id")
            handoff.event_path = event.get("path")
            trace_events_total += 1
            handoffs.append(handoff)

            agent_result = runtime.run(agent_id, target=target, dry_run=True)
            child_summary = (agent_result.data or {}).get("summary", {})
            child_agent = (agent_result.data or {}).get("agent", {})
            child_blocking = int(child_summary.get("blocking_findings", 0) or 0)
            child_failing = int(child_summary.get("failing_findings", 0) or 0)
            child_blocking_total += child_blocking
            child_failing_total += child_failing
            if not agent_result.ok:
                child_non_ok_total += 1
                findings.append(
                    Finding(
                        "MULTIAGENT_CHILD_AGENT_COMPLETED_WITH_FINDINGS",
                        "A child agent completed and reported fail/block findings; coordinator remains report-only but surfaces the issue.",
                        Severity.WARNING,
                        metadata={
                            "agent_id": agent_id,
                            "agent_exit_code": int(agent_result.exit_code),
                            "blocking_findings": child_blocking,
                            "failing_findings": child_failing,
                        },
                    )
                )

            steps.append(
                {
                    "step_id": step["step_id"],
                    "sequence": index,
                    "agent_id": agent_id,
                    "agent_name": child_agent.get("agent_name") or agent_spec.name,
                    "miasi_status": agent_spec.status,
                    "max_autonomy": agent_spec.max_autonomy,
                    "allowed_runtime_status": agent_spec.status in _IMPLEMENTED_AGENT_STATUSES,
                    "dry_run": True,
                    "handoff_id": handoff.handoff_id,
                    "handoff_trace_event_emitted": handoff.trace_event_emitted,
                    "agent_result_ok": agent_result.ok,
                    "agent_exit_code": int(agent_result.exit_code),
                    "agent_message": agent_result.message,
                    "agent_session_id": child_summary.get("agent_session_id"),
                    "summary": child_summary,
                }
            )
            previous_agent = agent_id

        findings.append(
            Finding(
                "MULTIAGENT_WORKFLOW_DRY_RUN_COMPLETED",
                "MultiAgentCoordinator completed the governed sequential workflow in dry-run/report-only mode.",
                Severity.INFO,
                metadata={"workflow": workflow_id, "steps_total": len(steps), "handoffs_total": len(handoffs)},
            )
        )
        result = CommandResult(
            command="multiagent run",
            ok=True,
            exit_code=ExitCode.PASS,
            message="MultiAgentCoordinator completed governed dry-run workflow.",
            data={
                "summary": {
                    "schema_version": "1.0.0",
                    "workflow_id": workflow_id,
                    "target": target,
                    "dry_run": True,
                    "coordinator_agent_id": _COORDINATOR_AGENT_ID,
                    "coordinator_status": coordinator.status if coordinator else None,
                    "runtime_allowed_statuses": sorted(_IMPLEMENTED_AGENT_STATUSES),
                    "steps_total": len(steps),
                    "steps_completed": len(steps),
                    "child_agent_runs_total": len(steps),
                    "child_non_ok_total": child_non_ok_total,
                    "child_blocking_findings_total": child_blocking_total,
                    "child_failing_findings_total": child_failing_total,
                    "handoffs_total": len(handoffs),
                    "handoffs_explicit_total": sum(1 for item in handoffs if item.explicit),
                    "handoffs_traced_total": sum(1 for item in handoffs if item.trace_event_emitted),
                    "policy_checks_total": policy_checks_total,
                    "policy_allowed": True,
                    "trace_events_total": trace_events_total,
                    "mutations_performed": False,
                    "destructive_actions_executed": False,
                    "network_used": False,
                    "external_api_used": False,
                    "shell_used": False,
                    "remote_execution_used": False,
                    "preliminary": True,
                },
                "workflow": {"workflow_id": workflow_id, "mode": "sequential-governed", "autonomy_open": False},
                "steps": steps,
                "handoffs": [handoff.to_dict() for handoff in handoffs],
                "notes": [
                    "FUNC-SPRINT-90 is an implemented-initial coordinator MVP, not an autonomous planner.",
                    "Child agent findings are surfaced as report evidence; this command is not a quality gate.",
                    "Only agents with implemented or implemented-initial MIASI status are eligible.",
                ],
            },
            findings=findings,
        )
        self.events.emit_result(result, event_type="multiagent.workflow.evaluated", subject=workflow_id)
        return result

    def _validate_coordinator_contract(self, coordinator: AgentSpec | None, rules: dict[str, PolicyRule]) -> list[Finding]:
        findings: list[Finding] = []
        if coordinator is None:
            findings.append(Finding("MULTIAGENT_COORDINATOR_NOT_REGISTERED", "multiagent.coordinator must exist in MIASI Agent Registry.", Severity.BLOCK))
            return findings
        if coordinator.status not in _IMPLEMENTED_AGENT_STATUSES:
            findings.append(
                Finding(
                    "MULTIAGENT_COORDINATOR_STATUS_BLOCKED",
                    "multiagent.coordinator must be implemented or implemented-initial before runtime use.",
                    Severity.BLOCK,
                    metadata=coordinator.to_dict(),
                )
            )
        for rule_id in coordinator.policy_rule_ids:
            if rule_id not in rules:
                findings.append(Finding("MULTIAGENT_COORDINATOR_POLICY_UNKNOWN", "Coordinator references an unknown policy rule.", Severity.BLOCK, metadata={"rule_id": rule_id}))
        if not coordinator.observability_required:
            findings.append(Finding("MULTIAGENT_COORDINATOR_OBSERVABILITY_REQUIRED", "Coordinator must require observability.", Severity.BLOCK))
        if not coordinator.eval_required:
            findings.append(Finding("MULTIAGENT_COORDINATOR_EVAL_REQUIRED", "Coordinator must require eval coverage.", Severity.BLOCK))
        return findings

    def _validate_workflow_agents(self, workflow: list[dict[str, str]], agents: dict[str, AgentSpec]) -> list[Finding]:
        findings: list[Finding] = []
        for step in workflow:
            agent_id = step["agent_id"]
            agent = agents.get(agent_id)
            if agent is None:
                findings.append(Finding("MULTIAGENT_WORKFLOW_AGENT_UNKNOWN", "Workflow references an agent absent from MIASI registry.", Severity.BLOCK, metadata={"agent_id": agent_id}))
                continue
            if agent.status not in _IMPLEMENTED_AGENT_STATUSES:
                findings.append(
                    Finding(
                        "MULTIAGENT_WORKFLOW_AGENT_STATUS_BLOCKED",
                        "MultiAgentCoordinator MVP cannot use planned/future/disabled agents.",
                        Severity.BLOCK,
                        metadata={"agent_id": agent_id, "status": agent.status, "allowed_statuses": sorted(_IMPLEMENTED_AGENT_STATUSES)},
                    )
                )
            if agent.max_autonomy not in {"A2", "A3"}:
                findings.append(
                    Finding(
                        "MULTIAGENT_WORKFLOW_AGENT_AUTONOMY_BLOCKED",
                        "Sprint 90 workflow agents must remain at bounded A2/A3 autonomy.",
                        Severity.BLOCK,
                        metadata={"agent_id": agent_id, "max_autonomy": agent.max_autonomy},
                    )
                )
        return findings

    def _evaluate_handoff_policy(self, handoff: HandoffRecord) -> CommandResult:
        return self.policy.evaluate(
            PolicyRequest(
                action="read",
                path=handoff.target,
                text=handoff.reason,
                dry_run=True,
                tool_id="multiagent.handoff",
                subject=f"{handoff.from_agent or 'user'}->{handoff.to_agent}",
                metadata={
                    "component": "MultiAgentCoordinator",
                    "sprint": "FUNC-SPRINT-90",
                    "workflow_id": handoff.workflow_id,
                    "handoff_id": handoff.handoff_id,
                    "explicit_handoff": True,
                    "mutations_performed": False,
                    "network_used": False,
                    "external_api_used": False,
                },
            )
        )

    def _emit_handoff_event(self, handoff: HandoffRecord, *, ok: bool, exit_code: ExitCode, message: str) -> dict[str, str]:
        event = self.events.emit(
            EventRecord(
                event_type="multiagent.handoff.evaluated",
                command="multiagent run",
                subject=f"{handoff.workflow_id}:{handoff.from_agent or 'user'}->{handoff.to_agent}",
                ok=ok,
                status="PASS" if ok else "BLOCK",
                exit_code=int(exit_code),
                message=message,
                summary=handoff.to_dict(),
                metadata={
                    "workflow_id": handoff.workflow_id,
                    "handoff_id": handoff.handoff_id,
                    "explicit": True,
                    "dry_run": True,
                    "sprint": "FUNC-SPRINT-90",
                },
            )
        )
        return event.to_dict()

    def _blocked(
        self,
        workflow_id: str,
        target: str,
        findings: list[Finding],
        *,
        message: str,
        partial_steps: list[dict[str, Any]] | None = None,
        partial_handoffs: list[HandoffRecord] | None = None,
    ) -> CommandResult:
        result = CommandResult(
            command="multiagent run",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message=message,
            data={
                "summary": {
                    "schema_version": "1.0.0",
                    "workflow_id": workflow_id,
                    "target": target,
                    "dry_run": True,
                    "coordinator_agent_id": _COORDINATOR_AGENT_ID,
                    "steps_completed": len(partial_steps or []),
                    "handoffs_total": len(partial_handoffs or []),
                    "handoffs_traced_total": sum(1 for item in (partial_handoffs or []) if item.trace_event_emitted),
                    "mutations_performed": False,
                    "destructive_actions_executed": False,
                    "network_used": False,
                    "external_api_used": False,
                    "shell_used": False,
                    "remote_execution_used": False,
                    "preliminary": True,
                },
                "steps": partial_steps or [],
                "handoffs": [handoff.to_dict() for handoff in (partial_handoffs or [])],
            },
            findings=findings,
        )
        self.events.emit_result(result, event_type="multiagent.workflow.evaluated", subject=workflow_id)
        return result


def _canonical_workflow(value: str) -> str:
    normalized = (value or "").strip().lower().replace("_", "-")
    aliases = {"repo": "repo-review", "repository-review": "repo-review", "repo-review": "repo-review"}
    return aliases.get(normalized, normalized)
