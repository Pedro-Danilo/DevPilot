from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from .dependency_graph import PlanningDependencyGraphService
from .models import PlanningApproval, PlanningLifecycle, PlanningState, TraceKind, valid_id, valid_semver

APPROVER_ROLES = frozenset({"owner", "product-owner"})
REVIEW_ROLES = frozenset({"owner", "product-owner", "architect", "qa-reviewer"})
ENTITY_OWNER_ROLES = frozenset({"owner", "product-owner", "architect", "developer", "qa-reviewer"})


class PlanningPolicyError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class PlanningContractFinding:
    finding_id: str
    message: str
    subject: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"finding_id": self.finding_id, "message": self.message, "subject": self.subject}


@dataclass(frozen=True)
class PlanningContractReport:
    ok: bool
    findings: tuple[PlanningContractFinding, ...]
    metrics: dict[str, int | bool]

    def to_dict(self) -> dict:
        return {
            "schema_id": "DEVPL-GSDLC-08-A-PLANNING-CONTRACT-REPORT-V1",
            "status": "PASS" if self.ok else "BLOCK",
            "findings": [x.to_dict() for x in self.findings],
            "metrics": dict(self.metrics),
            "safety": {
                "source_mutations_performed": False,
                "network_used": False,
                "external_api_used": False,
                "agent_auto_approval_allowed": False,
            },
        }


class PlanningStateService:
    """Pure domain lifecycle/contract service; it never writes files or executes tools."""

    _transitions = {
        PlanningLifecycle.DRAFT: frozenset({PlanningLifecycle.REVIEW}),
        PlanningLifecycle.REVIEW: frozenset({PlanningLifecycle.DRAFT, PlanningLifecycle.APPROVED}),
        PlanningLifecycle.APPROVED: frozenset({PlanningLifecycle.FROZEN}),
        PlanningLifecycle.FROZEN: frozenset(),
    }

    def __init__(self) -> None:
        self.graph = PlanningDependencyGraphService()

    def transition(
        self,
        state: PlanningState,
        target: PlanningLifecycle,
        *,
        actor_id: str,
        actor_role: str,
        actor_kind: str = "human",
    ) -> PlanningState:
        current = PlanningLifecycle(state.lifecycle)
        target = PlanningLifecycle(target)
        if target not in self._transitions[current]:
            raise PlanningPolicyError("PLANNING_ILLEGAL_TRANSITION", f"Illegal planning transition {current.value}->{target.value}.")
        if not actor_id.strip():
            raise PlanningPolicyError("PLANNING_ACTOR_REQUIRED", "Planning lifecycle transition requires an actor.")
        role = actor_role.strip().lower()
        if target in {PlanningLifecycle.APPROVED, PlanningLifecycle.FROZEN}:
            if actor_kind != "human":
                raise PlanningPolicyError("PLANNING_AGENT_APPROVAL_BLOCK", "Agent-originated decisions cannot approve or freeze planning.")
            if role not in APPROVER_ROLES:
                raise PlanningPolicyError("PLANNING_APPROVAL_ROLE_BLOCK", "Only owner/product-owner may approve or freeze planning.")
        elif role not in REVIEW_ROLES:
            raise PlanningPolicyError("PLANNING_REVIEW_ROLE_BLOCK", "Role is not authorized for planning review lifecycle transitions.")

        approval = state.approval
        frozen_by = state.frozen_by
        if target is PlanningLifecycle.APPROVED:
            approval = PlanningApproval(actor_id=actor_id, actor_role=role, source_kind="human")
        if target is PlanningLifecycle.FROZEN:
            if approval is None:
                raise PlanningPolicyError("PLANNING_APPROVAL_REQUIRED", "Planning must be approved before freeze.")
            frozen_by = PlanningApproval(actor_id=actor_id, actor_role=role, source_kind="human")
        if target is PlanningLifecycle.DRAFT:
            approval = None
            frozen_by = None
        return replace(state, lifecycle=target, approval=approval, frozen_by=frozen_by)

    def validate(self, state: PlanningState, *, known_trace_refs: Iterable[tuple[str, str]]) -> PlanningContractReport:
        known = {(str(kind), str(target)) for kind, target in known_trace_refs}
        findings: list[PlanningContractFinding] = []
        graph = self.graph.validate(state)
        for item in graph.duplicate_ids:
            findings.append(PlanningContractFinding("PLANNING_ID_COLLISION", "Planning entity id must be globally unique.", item))
        for dep in graph.orphan_dependency_ids:
            findings.append(PlanningContractFinding("PLANNING_DEPENDENCY_ORPHAN", "Dependency endpoint does not exist.", dep))
        for dep in graph.self_dependency_ids:
            findings.append(PlanningContractFinding("PLANNING_DEPENDENCY_SELF", "Self dependency is forbidden.", dep))
        for node in graph.cycle_nodes:
            findings.append(PlanningContractFinding("PLANNING_DEPENDENCY_CYCLE", "Dependency graph contains a cycle.", node))

        milestones = {x.id for x in state.milestones}
        epics = {x.id for x in state.epics}
        stories = {x.id for x in state.stories}
        all_entities = [*state.milestones, *state.epics, *state.stories, *state.sprints]
        prefixes = {"mil": state.milestones, "epic": state.epics, "story": state.stories, "sprint": state.sprints}
        for prefix, rows in prefixes.items():
            for row in rows:
                if not valid_id(row.id, prefix):
                    findings.append(PlanningContractFinding("PLANNING_STABLE_ID_INVALID", f"{prefix} id does not match stable-id contract.", row.id))
                if not valid_semver(row.version):
                    findings.append(PlanningContractFinding("PLANNING_VERSION_INVALID", "Planning entity version must be semantic x.y.z.", row.id))
                if row.owner_role not in ENTITY_OWNER_ROLES:
                    findings.append(PlanningContractFinding("PLANNING_OWNER_ROLE_INVALID", "Planning entity owner_role is not a canonical planning role.", row.id))
        if not valid_id(state.planning_id, "planning") or not valid_semver(state.version):
            findings.append(PlanningContractFinding("PLANNING_STATE_ID_VERSION_INVALID", "PlanningState id/version contract is invalid.", state.planning_id))

        for epic in state.epics:
            if epic.milestone_id not in milestones:
                findings.append(PlanningContractFinding("PLANNING_EPIC_ORPHAN", "Epic milestone parent is missing.", epic.id))
        for story in state.stories:
            if story.epic_id not in epics:
                findings.append(PlanningContractFinding("PLANNING_STORY_ORPHAN", "Story epic parent is missing.", story.id))
            if not story.acceptance_criteria:
                findings.append(PlanningContractFinding("PLANNING_STORY_ACCEPTANCE_REQUIRED", "Story requires acceptance criteria.", story.id))
            if not any(str(link.kind.value if hasattr(link.kind, 'value') else link.kind) == TraceKind.REQUIREMENT.value for link in story.trace_links):
                findings.append(PlanningContractFinding("PLANNING_STORY_REQUIREMENT_TRACE_REQUIRED", "Story requires at least one requirement trace.", story.id))
        for sprint in state.sprints:
            for story_id in sprint.story_ids:
                if story_id not in stories:
                    findings.append(PlanningContractFinding("PLANNING_SPRINT_STORY_ORPHAN", "Sprint references an unknown story.", sprint.id))

        for entity in all_entities:
            for link in entity.trace_links:
                key = (str(link.kind.value if hasattr(link.kind, 'value') else link.kind), link.target_id)
                if key not in known:
                    findings.append(PlanningContractFinding("PLANNING_TRACE_ORPHAN", "Trace target is not present in the supplied authoritative trace set.", f"{entity.id}:{key[0]}:{key[1]}"))

        lifecycle = PlanningLifecycle(state.lifecycle)
        if lifecycle in {PlanningLifecycle.APPROVED, PlanningLifecycle.FROZEN} and state.approval is None:
            findings.append(PlanningContractFinding("PLANNING_APPROVAL_REQUIRED", "Approved/frozen planning requires a human approval record.", state.planning_id))
        if state.approval and (state.approval.source_kind != "human" or state.approval.actor_role not in APPROVER_ROLES):
            findings.append(PlanningContractFinding("PLANNING_APPROVAL_AUTHORITY_INVALID", "Approval must be human and owner/product-owner bound.", state.planning_id))
        if lifecycle is PlanningLifecycle.FROZEN and state.frozen_by is None:
            findings.append(PlanningContractFinding("PLANNING_FREEZE_RECORD_REQUIRED", "Frozen planning requires a role-bound freeze record.", state.planning_id))
        if state.frozen_by and (state.frozen_by.source_kind != "human" or state.frozen_by.actor_role not in APPROVER_ROLES):
            findings.append(PlanningContractFinding("PLANNING_FREEZE_AUTHORITY_INVALID", "Freeze must be human and owner/product-owner bound.", state.planning_id))

        metrics = {
            "entities_total": len(all_entities),
            "milestones_total": len(state.milestones),
            "epics_total": len(state.epics),
            "stories_total": len(state.stories),
            "sprints_total": len(state.sprints),
            "dependencies_total": len(state.dependencies),
            "duplicate_ids_total": len(graph.duplicate_ids),
            "cycle_nodes_total": len(graph.cycle_nodes),
            "orphan_dependencies_total": len(graph.orphan_dependency_ids),
            "findings_total": len(findings),
            "source_mutations_performed": False,
        }
        return PlanningContractReport(ok=not findings, findings=tuple(findings), metrics=metrics)
