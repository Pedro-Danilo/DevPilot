from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable


def _canonical_sha(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _yaml(value: Any) -> str:
    return json.dumps(str(value if value is not None else ""), ensure_ascii=False)


def _updated(record: dict[str, Any]) -> str:
    candidates = (
        (record.get("freeze") or {}).get("frozen_at"),
        (record.get("approval") or {}).get("approved_at"),
        (record.get("review") or {}).get("reviewed_at"),
        (record.get("provenance") or {}).get("created_at"),
    )
    for value in candidates:
        text = str(value or "").strip()
        if text:
            return text[:10]
    return "unknown"


def _approval(record: dict[str, Any]) -> str:
    approval = record.get("approval") if isinstance(record.get("approval"), dict) else {}
    actor = str(approval.get("actor_id") or "").strip()
    role = str(approval.get("actor_role") or "").strip()
    return f"human:{actor}:{role}" if actor else "pending"


def _frontmatter(*, doc_id: str, title: str, record: dict[str, Any], source_json: str) -> str:
    status = str(record.get("lifecycle") or "DRAFT")
    version = str(record.get("version") or "1.0.0")
    return "\n".join(
        [
            "---",
            f"doc_id: {_yaml(doc_id)}",
            f"title: {_yaml(title)}",
            f"status: {_yaml(status)}",
            f"version: {_yaml(version)}",
            'owner: "product-owner"',
            f"updated: {_yaml(_updated(record))}",
            f"approval: {_yaml(_approval(record))}",
            'doc_type: "planning-human-projection"',
            'canonical_authority: "json"',
            f"source_json: {_yaml(source_json)}",
            f"source_record_sha256: {_yaml(_canonical_sha(record))}",
            f"candidate_content_sha256: {_yaml(record.get('content_sha256') or '')}",
            'edit_policy: "Edit in DevPilot Planning Workbench; do not edit this derived projection directly."',
            "---",
            "",
        ]
    )


def _bullets(values: Iterable[Any]) -> list[str]:
    rows = [str(x).strip() for x in values if str(x).strip()]
    return [f"- {x}" for x in rows] if rows else ["- N/A"]


def _trace(values: Any) -> str:
    links = values if isinstance(values, list) else []
    parts = [
        f"{str(x.get('kind') or 'trace')}:{str(x.get('target_id') or '')}"
        for x in links
        if isinstance(x, dict)
    ]
    return ", ".join(parts) or "N/A"


def render_roadmap(record: dict[str, Any], *, source_json: str = "roadmap_workbench.json") -> str:
    wid = str(record.get("workspace_id") or "project")
    state = record.get("planning_state") if isinstance(record.get("planning_state"), dict) else {}
    coverage = record.get("coverage") if isinstance(record.get("coverage"), dict) else {}
    title = f"Roadmap — {wid}"
    out = [
        _frontmatter(doc_id=f"PLANNING-ROADMAP-{wid}", title=title, record=record, source_json=source_json),
        f"# {title}",
        "",
        "> Human-readable projection generated from canonical Planning JSON. Edit through DevPilot Planning Workbench, not this file.",
        "",
        "## Governance",
        "",
        f"- Lifecycle: **{record.get('lifecycle', 'DRAFT')}**",
        f"- Authoring mode: `{record.get('authoring_mode', 'N/A')}`",
        f"- Version: `{record.get('version', '1.0.0')}`",
        f"- Requirement coverage: **{coverage.get('requirement_percent', 'N/A')}%**",
        f"- Risk coverage: **{coverage.get('risk_percent', 'N/A')}%**",
        f"- Candidate SHA-256: `{record.get('content_sha256', '')}`",
        "",
        "## Milestones",
        "",
    ]
    for row in state.get("milestones") or []:
        if not isinstance(row, dict):
            continue
        out += [
            f"### {row.get('id', 'milestone')} — {row.get('title', '')}",
            "",
            f"**Outcome.** {row.get('outcome', 'N/A')}",
            "",
            "**Exit criteria**",
            *_bullets(row.get("exit_criteria") or []),
            "",
            f"**Traceability.** {_trace(row.get('trace_links'))}",
            "",
        ]
    out += ["## Dependencies", ""]
    deps = state.get("dependencies") or []
    if deps:
        for dep in deps:
            if isinstance(dep, dict):
                out.append(
                    f"- `{dep.get('predecessor_id', '')}` → `{dep.get('successor_id', '')}` "
                    f"({dep.get('kind', 'requires')}): {dep.get('rationale', '')}"
                )
    else:
        out.append("- None declared.")
    out.append("")
    return "\n".join(out) + "\n"


def render_backlog(record: dict[str, Any], *, source_json: str = "backlog_workbench.json") -> str:
    wid = str(record.get("workspace_id") or "project")
    backlog = record.get("backlog") if isinstance(record.get("backlog"), dict) else {}
    coverage = record.get("coverage") if isinstance(record.get("coverage"), dict) else {}
    title = f"Backlog — {wid}"
    out = [
        _frontmatter(doc_id=f"PLANNING-BACKLOG-{wid}", title=title, record=record, source_json=source_json),
        f"# {title}",
        "",
        "> Human-readable projection generated from canonical Planning JSON. Edit through DevPilot Planning Workbench, not this file.",
        "",
        "## Governance",
        "",
        f"- Lifecycle: **{record.get('lifecycle', 'DRAFT')}**",
        f"- Authoring mode: `{record.get('authoring_mode', 'N/A')}`",
        f"- Version: `{record.get('version', '1.0.0')}`",
        f"- Requirement coverage: **{coverage.get('requirement_coverage_percent', 'N/A')}%**",
        f"- Blockers: **{coverage.get('blockers_total', 'N/A')}**",
        f"- Candidate SHA-256: `{record.get('content_sha256', '')}`",
        "",
        "## Epics",
        "",
    ]
    for epic in backlog.get("epics") or []:
        if not isinstance(epic, dict):
            continue
        priority = epic.get("priority") if isinstance(epic.get("priority"), dict) else {}
        out += [
            f"### {epic.get('id', 'epic')} — {epic.get('title', '')}",
            "",
            f"- Milestone: `{epic.get('milestone_id', 'N/A')}`",
            f"- Priority: `{priority.get('level', 'N/A')}` · value {priority.get('value_score', 'N/A')} · risk {priority.get('risk_score', 'N/A')}",
            f"- Rationale: {priority.get('rationale', 'N/A')}",
            f"- Traceability: {_trace(epic.get('trace_links'))}",
            "",
        ]
    out += ["## Stories", ""]
    for story in backlog.get("stories") or []:
        if not isinstance(story, dict):
            continue
        priority = story.get("priority") if isinstance(story.get("priority"), dict) else {}
        out += [
            f"### {story.get('id', 'story')} — {story.get('title', '')}",
            "",
            f"- Epic: `{story.get('epic_id', 'N/A')}`",
            f"- Priority: `{priority.get('level', 'N/A')}` · value {priority.get('value_score', 'N/A')} · risk {priority.get('risk_score', 'N/A')}",
            f"- Rationale: {priority.get('rationale', 'N/A')}",
            f"- Traceability: {_trace(story.get('trace_links'))}",
            "",
            "**Acceptance criteria**",
            *_bullets(story.get("acceptance_criteria") or []),
            "",
        ]
    out += ["## Dependencies", ""]
    deps = backlog.get("dependencies") or []
    if deps:
        for dep in deps:
            if isinstance(dep, dict):
                out.append(
                    f"- `{dep.get('predecessor_id', '')}` → `{dep.get('successor_id', '')}` "
                    f"({dep.get('kind', 'requires')}): {dep.get('rationale', '')}"
                )
    else:
        out.append("- None declared.")
    out.append("")
    return "\n".join(out) + "\n"


def render_sprint(record: dict[str, Any], *, source_json: str = "sprint_planner.json") -> str:
    wid = str(record.get("workspace_id") or "project")
    plan = record.get("sprint_plan") if isinstance(record.get("sprint_plan"), dict) else {}
    validation = record.get("validation") if isinstance(record.get("validation"), dict) else {}
    backlog = record.get("backlog") if isinstance(record.get("backlog"), dict) else {}
    title = str(plan.get("title") or f"Sprint plan — {wid}")
    stories_by_id = {
        str(x.get("id") or ""): x
        for x in backlog.get("stories") or []
        if isinstance(x, dict) and str(x.get("id") or "")
    }
    selected = [x for x in plan.get("selected_stories") or [] if isinstance(x, dict)]
    selected_ids = {str(x.get("story_id") or "") for x in selected}
    unscheduled = [x for sid, x in stories_by_id.items() if sid not in selected_ids]
    capacity = plan.get("capacity") if isinstance(plan.get("capacity"), dict) else {}
    out = [
        _frontmatter(doc_id=f"PLANNING-SPRINT-{wid}", title=title, record=record, source_json=source_json),
        f"# {title}",
        "",
        "> Human-readable projection generated from canonical Planning JSON. Edit through DevPilot Planning Workbench, not this file.",
        "",
        "## Governance and readiness",
        "",
        f"- Lifecycle: **{record.get('lifecycle', 'DRAFT')}**",
        f"- Version: `{record.get('version', '1.0.0')}`",
        f"- Validation: **{validation.get('status', 'N/A')}**",
        f"- Executable: **{validation.get('executable', False)}**",
        f"- Blockers: **{validation.get('blockers_total', 'N/A')}**",
        f"- Capacity: **{capacity.get('limit', 'N/A')} {capacity.get('unit', '')}**",
        f"- Planned load: **{validation.get('planned_load', 'N/A')}**",
        f"- Utilization: **{validation.get('capacity_utilization_percent', 'N/A')}%**",
        f"- Overcommitted: **{validation.get('overcommitted', False)}**",
        f"- Candidate SHA-256: `{record.get('content_sha256', '')}`",
        "",
        "## Selected stories",
        "",
    ]
    for row in selected:
        sid = str(row.get("story_id") or "")
        story = stories_by_id.get(sid) or {}
        label = str(story.get("title") or "").strip()
        title_suffix = f" — {label}" if label else ""
        out.append(
            f"- `{sid}`{title_suffix} · readiness **{row.get('readiness', 'N/A')}** · estimate **{row.get('estimate', 'N/A')}**"
        )
    if not selected:
        out.append("- None selected.")
    out += ["", "## Unscheduled backlog stories", ""]
    if unscheduled:
        for story in unscheduled:
            out.append(f"- `{story.get('id', '')}` — {story.get('title', '')}")
    else:
        out.append("- None.")
    out += [
        "",
        "## Definition of Ready",
        *_bullets(plan.get("definition_of_ready") or []),
        "",
        "## Definition of Done",
        *_bullets(plan.get("definition_of_done") or []),
        "",
        "## Test intents",
        *_bullets(plan.get("test_intent_ids") or []),
        "",
        "## Risk focus",
        *_bullets(plan.get("risk_focus_ids") or []),
        "",
    ]
    provenance = plan.get("generation_provenance") if isinstance(plan.get("generation_provenance"), dict) else {}
    out += [
        "## Provenance",
        "",
        f"- Provider: `{provenance.get('provider_id', 'N/A')}`",
        f"- Strategy: `{provenance.get('strategy_id', 'N/A')}`",
        f"- Model execution used: `{provenance.get('model_execution_used', False)}`",
        f"- Agent execution used: `{provenance.get('agent_execution_used', False)}`",
        f"- Network used: `{provenance.get('network_used', False)}`",
        "",
    ]
    return "\n".join(out) + "\n"


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def write_roadmap_projection(runtime_root: Path, record: dict[str, Any], *, revision_number: int | None = None) -> list[Path]:
    targets: list[tuple[Path, str]] = [(Path(runtime_root) / "roadmap.md", "roadmap_workbench.json")]
    if revision_number is not None:
        name = f"roadmap-revision-{revision_number:04d}.json"
        targets.append((Path(runtime_root) / "revisions" / f"roadmap-revision-{revision_number:04d}.md", name))
    paths: list[Path] = []
    for path, source_json in targets:
        _atomic_text(path, render_roadmap(record, source_json=source_json))
        paths.append(path)
    return paths


def write_backlog_projection(runtime_root: Path, record: dict[str, Any], *, revision_number: int | None = None) -> list[Path]:
    targets: list[tuple[Path, str]] = [(Path(runtime_root) / "backlog.md", "backlog_workbench.json")]
    if revision_number is not None:
        name = f"backlog-revision-{revision_number:04d}.json"
        targets.append((Path(runtime_root) / "revisions" / f"backlog-revision-{revision_number:04d}.md", name))
    paths: list[Path] = []
    for path, source_json in targets:
        _atomic_text(path, render_backlog(record, source_json=source_json))
        paths.append(path)
    return paths


def write_sprint_projection(runtime_root: Path, record: dict[str, Any], *, revision_number: int | None = None) -> list[Path]:
    targets: list[tuple[Path, str]] = [(Path(runtime_root) / "sprint_plan.md", "sprint_planner.json")]
    if revision_number is not None:
        name = f"sprint-plan-revision-{revision_number:04d}.json"
        targets.append((Path(runtime_root) / "revisions" / f"sprint-plan-revision-{revision_number:04d}.md", name))
    paths: list[Path] = []
    for path, source_json in targets:
        _atomic_text(path, render_sprint(record, source_json=source_json))
        paths.append(path)
    return paths


def reconcile_existing_planning_projections(workspace_root: Path, *, workspace_id: str) -> dict[str, list[str]]:
    workspace_root = Path(workspace_root).resolve()
    specs = (
        ("roadmap", workspace_root / "outputs" / "planning" / "gsdlc_08_b" / workspace_id, "roadmap_workbench.json", write_roadmap_projection),
        ("backlog", workspace_root / "outputs" / "planning" / "gsdlc_08_c" / workspace_id, "backlog_workbench.json", write_backlog_projection),
        ("sprint", workspace_root / "outputs" / "planning" / "gsdlc_08_d" / workspace_id, "sprint_planner.json", write_sprint_projection),
    )
    result: dict[str, list[str]] = {}
    for name, runtime_root, filename, writer in specs:
        source = runtime_root / filename
        if not source.is_file():
            result[name] = []
            continue
        record = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError(f"Planning record must be an object: {source}")
        revision = None
        freeze = record.get("freeze") if isinstance(record.get("freeze"), dict) else {}
        if str(record.get("lifecycle") or "") == "FROZEN" and freeze.get("revision") is not None:
            revision = int(freeze["revision"])
        paths = writer(runtime_root, record, revision_number=revision)
        result[name] = [str(path.relative_to(workspace_root)).replace("\\", "/") for path in paths]
    return result
