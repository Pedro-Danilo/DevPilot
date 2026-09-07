from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import canonical_sha256

_REQUIRED_TRACE_KINDS = ("requirement", "adr", "risk", "test-intent")


@dataclass(frozen=True)
class StoryDoREvaluator:
    policy_version: str = "DEVPL-GSDLC-09-A-DOR-V1"

    def evaluate(
        self,
        *,
        story: dict[str, Any],
        frozen_sprint_record: dict[str, Any],
        source_fragments: dict[str, dict[str, Any]],
        project_context: dict[str, Any],
        evaluated_at_utc: str,
    ) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []

        def check(code: str, passed: bool, message: str, *, subject: str | None = None) -> None:
            checks.append({"code": code, "status": "PASS" if passed else "BLOCK", "message": message, "subject": subject})

        configured = bool(project_context.get("configured"))
        valid = bool(project_context.get("valid"))
        workspace_id = str(project_context.get("active_workspace_id") or "").strip()
        check("DOR_PROJECT_CONTEXT_SERVER_VALID", configured and valid and bool(workspace_id), "A server-validated active project context is required.")

        check("DOR_SPRINT_FROZEN", str(frozen_sprint_record.get("lifecycle") or "") == "FROZEN", "Story execution requires a FROZEN sprint authority.")
        sprint_plan = dict(frozen_sprint_record.get("sprint_plan") or {})
        selected = [x for x in sprint_plan.get("selected_stories") or [] if str(x.get("story_id") or "") == str(story.get("id") or "")]
        row = selected[0] if len(selected) == 1 else {}
        check("DOR_STORY_SELECTED", len(selected) == 1, "Story must be selected exactly once in the frozen sprint.", subject=str(story.get("id") or ""))
        ready = str(row.get("readiness") or "") == "READY" and not list(row.get("blocking_reasons") or [])
        check("DOR_STORY_READY", ready, "Selected story must be READY with zero blocking reasons.", subject=str(story.get("id") or ""))

        acceptance = [str(x).strip() for x in story.get("acceptance_criteria") or [] if str(x).strip()]
        check("DOR_ACCEPTANCE_CRITERIA", bool(acceptance), "At least one acceptance criterion is required.")
        check("DOR_DEFINITION_OF_READY", bool([x for x in sprint_plan.get("definition_of_ready") or [] if str(x).strip()]), "Sprint Definition of Ready is required.")

        trace_links = [x for x in story.get("trace_links") or [] if isinstance(x, dict)]
        by_kind: dict[str, list[str]] = {}
        for link in trace_links:
            by_kind.setdefault(str(link.get("kind") or ""), []).append(str(link.get("target_id") or ""))
        for kind in _REQUIRED_TRACE_KINDS:
            targets = [x for x in by_kind.get(kind, []) if x]
            check(f"DOR_TRACE_{kind.upper().replace('-', '_')}", bool(targets), f"Story requires at least one {kind} trace binding.")
            for target in targets:
                check("DOR_TRACE_SOURCE_RESOLVED", target in source_fragments, "Every trace target must resolve to an authoritative source fragment.", subject=target)

        risk_ids = {str(x) for x in sprint_plan.get("risk_focus_ids") or []}
        test_ids = {str(x) for x in sprint_plan.get("test_intent_ids") or []}
        story_risks = {x for x in by_kind.get("risk", []) if x}
        story_tests = {x for x in by_kind.get("test-intent", []) if x}
        check("DOR_RISK_FOCUS_BOUND", bool(story_risks) and story_risks.issubset(risk_ids), "Story risk bindings must be present in sprint risk focus.")
        check("DOR_TEST_INTENT_BOUND", bool(story_tests) and story_tests.issubset(test_ids), "Story test-intent bindings must be present in sprint test intent.")

        blockers = [x for x in checks if x["status"] == "BLOCK"]
        stable = {
            "policy_version": self.policy_version,
            "story_id": str(story.get("id") or ""),
            "story_version": str(story.get("version") or ""),
            "workspace_id": workspace_id,
            "checks": checks,
        }
        report_sha = canonical_sha256(stable)
        return {
            "schema_id": "SCHEMA-DEVPL-STORY-DOR-REPORT-V1",
            "schema_version": "1.0.0",
            "status": "PASS" if not blockers else "BLOCK",
            "policy_version": self.policy_version,
            "story_id": stable["story_id"],
            "story_version": stable["story_version"],
            "workspace_id": workspace_id,
            "evaluated_at_utc": str(evaluated_at_utc),
            "checks": checks,
            "blockers_total": len(blockers),
            "dor_report_sha256": report_sha,
            "source_mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
        }
