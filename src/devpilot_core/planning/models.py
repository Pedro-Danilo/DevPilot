from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")


class PlanningLifecycle(str, Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    FROZEN = "FROZEN"


class TraceKind(str, Enum):
    REQUIREMENT = "requirement"
    RISK = "risk"
    ADR = "adr"
    TEST_INTENT = "test-intent"


class DependencyKind(str, Enum):
    REQUIRES = "requires"
    BLOCKS = "blocks"
    SEQUENCES = "sequences"


@dataclass(frozen=True)
class TraceLink:
    kind: TraceKind | str
    target_id: str

    def to_dict(self) -> dict[str, str]:
        return {"kind": _value(self.kind), "target_id": self.target_id}


@dataclass(frozen=True)
class Milestone:
    id: str
    version: str
    title: str
    owner_role: str
    outcome: str
    exit_criteria: tuple[str, ...]
    lifecycle: PlanningLifecycle = PlanningLifecycle.DRAFT
    trace_links: tuple[TraceLink, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _entity_dict("SCHEMA-DEVPL-PLANNING-MILESTONE-V1", self, {"outcome": self.outcome, "exit_criteria": list(self.exit_criteria)})


@dataclass(frozen=True)
class Epic:
    id: str
    version: str
    title: str
    owner_role: str
    milestone_id: str
    lifecycle: PlanningLifecycle = PlanningLifecycle.DRAFT
    trace_links: tuple[TraceLink, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _entity_dict("SCHEMA-DEVPL-PLANNING-EPIC-V1", self, {"milestone_id": self.milestone_id})


@dataclass(frozen=True)
class Story:
    id: str
    version: str
    title: str
    owner_role: str
    epic_id: str
    acceptance_criteria: tuple[str, ...]
    lifecycle: PlanningLifecycle = PlanningLifecycle.DRAFT
    trace_links: tuple[TraceLink, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _entity_dict("SCHEMA-DEVPL-PLANNING-STORY-V1", self, {"epic_id": self.epic_id, "acceptance_criteria": list(self.acceptance_criteria)})


@dataclass(frozen=True)
class Sprint:
    id: str
    version: str
    title: str
    owner_role: str
    story_ids: tuple[str, ...]
    capacity: int
    lifecycle: PlanningLifecycle = PlanningLifecycle.DRAFT
    trace_links: tuple[TraceLink, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _entity_dict("SCHEMA-DEVPL-PLANNING-SPRINT-V1", self, {"story_ids": list(self.story_ids), "capacity": self.capacity})


@dataclass(frozen=True)
class Dependency:
    id: str
    predecessor_id: str
    successor_id: str
    kind: DependencyKind = DependencyKind.REQUIRES
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": "SCHEMA-DEVPL-PLANNING-DEPENDENCY-V1",
            "schema_version": "1.0.0",
            "id": self.id,
            "predecessor_id": self.predecessor_id,
            "successor_id": self.successor_id,
            "kind": _value(self.kind),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class PlanningApproval:
    actor_id: str
    actor_role: str
    source_kind: str = "human"

    def to_dict(self) -> dict[str, str]:
        return {"actor_id": self.actor_id, "actor_role": self.actor_role, "source_kind": self.source_kind}


@dataclass(frozen=True)
class PlanningState:
    planning_id: str
    version: str
    lifecycle: PlanningLifecycle = PlanningLifecycle.DRAFT
    milestones: tuple[Milestone, ...] = ()
    epics: tuple[Epic, ...] = ()
    stories: tuple[Story, ...] = ()
    sprints: tuple[Sprint, ...] = ()
    dependencies: tuple[Dependency, ...] = ()
    approval: PlanningApproval | None = None
    frozen_by: PlanningApproval | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": "SCHEMA-DEVPL-PLANNING-STATE-V1",
            "schema_version": "1.0.0",
            "planning_id": self.planning_id,
            "version": self.version,
            "lifecycle": _value(self.lifecycle),
            "milestones": [x.to_dict() for x in self.milestones],
            "epics": [x.to_dict() for x in self.epics],
            "stories": [x.to_dict() for x in self.stories],
            "sprints": [x.to_dict() for x in self.sprints],
            "dependencies": [x.to_dict() for x in self.dependencies],
            "approval": self.approval.to_dict() if self.approval else None,
            "frozen_by": self.frozen_by.to_dict() if self.frozen_by else None,
        }

    @property
    def entity_ids(self) -> tuple[str, ...]:
        return tuple(x.id for x in (*self.milestones, *self.epics, *self.stories, *self.sprints))


def valid_id(value: str, prefix: str) -> bool:
    return bool(ID_RE.fullmatch(value)) and value.startswith(prefix + "-")


def valid_semver(value: str) -> bool:
    return bool(SEMVER_RE.fullmatch(value))


def _value(value: Enum | str) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def _entity_dict(schema_id: str, entity: Any, extra: dict[str, Any]) -> dict[str, Any]:
    result = {
        "schema_id": schema_id,
        "schema_version": "1.0.0",
        "id": entity.id,
        "version": entity.version,
        "title": entity.title,
        "owner_role": entity.owner_role,
        "lifecycle": _value(entity.lifecycle),
        "trace_links": [x.to_dict() for x in entity.trace_links],
    }
    result.update(extra)
    return result
