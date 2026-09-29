from __future__ import annotations

import re
from typing import Any, Protocol


class PlanningCandidateProvider(Protocol):
    """Provider contract for governed Planning candidates.

    Providers may build candidate payloads, but they never own review, approval,
    freeze, source-write or lifecycle transitions. Those remain in the existing
    RoadmapWorkbench, BacklogWorkbench and SprintPlanner.
    """

    provider_id: str
    strategy_id: str

    def generate_roadmap(self, authority: dict[str, Any]) -> dict[str, Any]: ...

    def derive_backlog(self, authority: dict[str, Any], frozen_roadmap: dict[str, Any]) -> dict[str, Any]: ...

    def derive_sprint(
        self,
        authority: dict[str, Any],
        frozen_backlog: dict[str, Any],
        *,
        capacity_limit: int,
    ) -> dict[str, Any]: ...

    def projection(self) -> dict[str, Any]: ...


def _slug(value: str, *, fallback: str = "project", limit: int = 40) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").casefold()).strip("-")
    text = text[:limit].strip("-")
    return text or fallback


def _provider_provenance(provider_id: str, strategy_id: str) -> dict[str, Any]:
    return {
        "provider_id": provider_id,
        "strategy_id": strategy_id,
        "model_id": None,
        "model_execution_used": False,
        "agent_execution_used": False,
        "rag_execution_used": False,
        "network_used": False,
        "external_api_used": False,
        "cost_usd": 0.0,
        "human_review_required": True,
        "approval_authority": "existing-planning-workbench-human-lifecycle",
    }


class DeterministicPlanningCandidateProvider:
    """E0 local deterministic Planning provider.

    The provider consumes only the already-resolved PlanningAuthoritySnapshot.
    It performs no file I/O, no model/agent execution and no lifecycle write.
    """

    provider_id = "devpilot-local"
    strategy_id = "deterministic-planning-template-v1"

    def projection(self) -> dict[str, Any]:
        return {
            **_provider_provenance(self.provider_id, self.strategy_id),
            "status": "AVAILABLE",
            "provider_family": "PlanningCandidateProvider",
            "future_provider_slots": ["LocalModelPlanningCandidateProvider", "ExternalModelPlanningCandidateProvider"],
        }

    def generate_roadmap(self, authority: dict[str, Any]) -> dict[str, Any]:
        workspace_slug = _slug(authority.get("workspace_id") or "project", limit=32)
        grouped: dict[str, list[dict[str, Any]]] = {}
        for requirement in authority["requirements"]:
            source = str(requirement.get("source") or "UNMAPPED")
            grouped.setdefault(source, []).append(requirement)

        milestones: list[dict[str, Any]] = []
        for source_id in sorted(grouped):
            requirements = grouped[source_id]
            source_slug = _slug(source_id, fallback="unmapped", limit=48)
            trace_links: list[dict[str, str]] = []
            seen: set[tuple[str, str]] = set()
            for requirement in requirements:
                trace = authority["traceability"].get(requirement["id"], {}) or {}
                for kind, ids in (
                    ("requirement", [requirement["id"]]),
                    ("risk", trace.get("risks", [])),
                ):
                    for target in ids:
                        key = (kind, str(target))
                        if key in seen:
                            continue
                        seen.add(key)
                        trace_links.append({"kind": kind, "target_id": str(target)})
            capability = authority["capabilities"].get(source_id) or "; ".join(
                str(x.get("statement") or x["id"]) for x in requirements
            )
            milestones.append(
                {
                    "id": f"mil-{source_slug}",
                    "version": "1.0.0",
                    "title": f"{source_id} · {capability}",
                    "owner_role": "product-owner",
                    "outcome": f"Capability/source {source_id} implementable and acceptance-ready: {capability}",
                    "exit_criteria": [
                        f"{x['id']}: {x.get('acceptance_criterion') or 'acceptance criterion must be demonstrated'}"
                        for x in requirements
                    ],
                    "trace_links": trace_links,
                }
            )
        return {
            "roadmap_id": f"planning-{workspace_slug}-roadmap",
            "version": "1.0.0",
            "milestones": milestones,
            "dependencies": [],
            "generation_provenance": _provider_provenance(self.provider_id, self.strategy_id),
        }

    def derive_backlog(self, authority: dict[str, Any], frozen_roadmap: dict[str, Any]) -> dict[str, Any]:
        workspace_slug = _slug(authority.get("workspace_id") or "project", limit=32)
        planning_state = frozen_roadmap.get("planning_state") if isinstance(frozen_roadmap.get("planning_state"), dict) else {}
        milestones = planning_state.get("milestones") if isinstance(planning_state.get("milestones"), list) else []
        milestone_by_source: dict[str, str] = {}
        for row in milestones:
            if not isinstance(row, dict):
                continue
            requirement_links = {
                str(x.get("target_id"))
                for x in row.get("trace_links") or []
                if isinstance(x, dict) and x.get("kind") == "requirement" and x.get("target_id")
            }
            for requirement in authority["requirements"]:
                if requirement["id"] in requirement_links:
                    milestone_by_source.setdefault(str(requirement.get("source") or "UNMAPPED"), str(row.get("id") or ""))

        sources = sorted({str(x.get("source") or "UNMAPPED") for x in authority["requirements"]})
        epics: list[dict[str, Any]] = []
        for source_id in sources:
            milestone_id = milestone_by_source.get(source_id)
            if not milestone_id:
                continue
            source_slug = _slug(source_id, fallback="unmapped", limit=48)
            requirements = [x for x in authority["requirements"] if str(x.get("source") or "UNMAPPED") == source_id]
            epics.append(
                {
                    "id": f"epic-{source_slug}",
                    "version": "1.0.0",
                    "title": authority["capabilities"].get(source_id) or source_id,
                    "owner_role": "product-owner",
                    "milestone_id": milestone_id,
                    "trace_links": [{"kind": "requirement", "target_id": x["id"]} for x in requirements],
                    "priority": {
                        "level": "P0",
                        "value_score": 5,
                        "risk_score": 4,
                        "rationale": f"Required source/capability {source_id} in the FROZEN Requirements baseline.",
                        "source": "DERIVED",
                    },
                }
            )

        stories: list[dict[str, Any]] = []
        for requirement in authority["requirements"]:
            trace = authority["traceability"].get(requirement["id"], {}) or {}
            source_id = str(requirement.get("source") or "UNMAPPED")
            source_slug = _slug(source_id, fallback="unmapped", limit=48)
            requirement_slug = _slug(requirement["id"], fallback="requirement", limit=48)
            links = [{"kind": "requirement", "target_id": requirement["id"]}]
            links += [{"kind": "adr", "target_id": x} for x in trace.get("adrs", [])]
            links += [{"kind": "risk", "target_id": x} for x in trace.get("risks", [])]
            links += [{"kind": "test-intent", "target_id": x} for x in trace.get("test_intents", [])]
            stories.append(
                {
                    "id": f"story-{requirement_slug}",
                    "version": "1.0.0",
                    "title": requirement.get("statement") or requirement["id"],
                    "owner_role": "developer",
                    "epic_id": f"epic-{source_slug}",
                    "acceptance_criteria": [
                        requirement.get("acceptance_criterion")
                        or f"{requirement['id']} acceptance criterion must be demonstrated."
                    ],
                    "trace_links": links,
                    "priority": {
                        "level": "P0" if str(requirement.get("priority") or "MUST").upper() == "MUST" else "P1",
                        "value_score": 5,
                        "risk_score": 4 if trace.get("risks") else 3,
                        "rationale": f"{requirement['id']} is governed by the FROZEN Requirements baseline.",
                        "source": "DERIVED",
                    },
                }
            )
        return {
            "backlog_id": f"planning-backlog-{workspace_slug}",
            "version": "1.0.0",
            "epics": epics,
            "stories": stories,
            "dependencies": [],
            "generation_provenance": _provider_provenance(self.provider_id, self.strategy_id),
        }

    def derive_sprint(
        self,
        authority: dict[str, Any],
        frozen_backlog: dict[str, Any],
        *,
        capacity_limit: int,
    ) -> dict[str, Any]:
        workspace_slug = _slug(authority.get("workspace_id") or "project", limit=32)
        backlog = frozen_backlog.get("backlog") if isinstance(frozen_backlog.get("backlog"), dict) else {}
        stories = [x for x in backlog.get("stories") or [] if isinstance(x, dict)]
        limit = max(1, min(int(capacity_limit), 20))
        selected = [
            {"story_id": str(story.get("id") or ""), "estimate": 1, "readiness": "READY", "blocking_reasons": []}
            for story in stories[:limit]
        ]
        test_ids = sorted(
            {
                x.get("target_id")
                for story in stories[:limit]
                for x in story.get("trace_links") or []
                if isinstance(x, dict) and x.get("kind") == "test-intent" and x.get("target_id")
            }
        )
        risk_ids = sorted(
            {
                x.get("target_id")
                for story in stories[:limit]
                for x in story.get("trace_links") or []
                if isinstance(x, dict) and x.get("kind") == "risk" and x.get("target_id")
            }
        )
        return {
            "schema_id": "SCHEMA-DEVPL-PLANNING-SPRINT-PLAN-V1",
            "schema_version": "1.0.0",
            "sprint_plan_id": f"sprint-plan-{workspace_slug}-001",
            "version": "1.0.0",
            "title": "Sprint 1 · First executable planning slice",
            "owner_role": "product-owner",
            "lifecycle": "DRAFT",
            "backlog_reference": {
                "backlog_id": str(backlog.get("backlog_id") or ""),
                "version": str(backlog.get("version") or ""),
                "lifecycle": "FROZEN",
                "content_sha256": str(frozen_backlog.get("content_sha256") or ""),
            },
            "capacity": {"unit": "points", "limit": limit},
            "selected_stories": selected,
            "completed_story_ids": [],
            "definition_of_ready": ["acceptance criteria present", "Requirement trace present", "dependencies known"],
            "definition_of_done": ["acceptance criteria PASS", "required tests PASS", "evidence stored"],
            "test_intent_ids": test_ids,
            "risk_focus_ids": risk_ids,
            "generation_provenance": _provider_provenance(self.provider_id, self.strategy_id),
        }
