from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import jsonschema
import pytest

from devpilot_core.application.guided_sdlc_service import GuidedSDLCApplicationService
from devpilot_core.application.ui_workspace_context import UiWorkspaceContext
from devpilot_core.guided_sdlc import ProjectProgressEngine
from devpilot_core.story_execution import (
    StoryContextPackBuilder,
    StoryContextPackError,
    StoryDoREvaluator,
    StoryExecutionApplicationService,
    StoryExecutionState,
    StoryExecutionStatus,
    StoryExecutionStore,
    StoryExecutionTransitionError,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/fixtures/gsdlc09a/story_context_fixture.json").read_text(encoding="utf-8"))


class StaticResolver:
    def __init__(self, context: UiWorkspaceContext) -> None:
        self.context = context

    def resolve(self) -> UiWorkspaceContext:
        return self.context


def _workspace(tmp_path: Path) -> tuple[Path, StaticResolver]:
    root = tmp_path / "workspace"
    (root / ".devpilot").mkdir(parents=True)
    (root / "src").mkdir()
    (root / ".devpilot/project.yaml").write_text('schema_version: "1.0"\nproject:\n  id: "pilot-local"\n  name: "Pilot"\n  type: "agent-assisted-sdlc"\n  owner: "owner"\n', encoding="utf-8")
    (root / "src/example.py").write_text("def create_item(item_id: str) -> str:\n    return item_id\n", encoding="utf-8")
    context = UiWorkspaceContext(
        platform_root=root,
        mode="active-root",
        configured=True,
        valid=True,
        active_workspace_id="pilot-workspace",
        active_workspace_root=root,
        reports_root=root / "outputs/reports",
        traces_root=root / "outputs/traces",
        project_file=root / ".devpilot/project.yaml",
    )
    return root, StaticResolver(context)


def _schema(name: str) -> dict:
    return json.loads((ROOT / "docs/schemas" / name).read_text(encoding="utf-8"))


def _prepared(tmp_path: Path):
    root, resolver = _workspace(tmp_path)
    service = StoryExecutionApplicationService(root, context_resolver=resolver)
    result = service.prepare(
        story=FIXTURE["story"],
        frozen_sprint_record=FIXTURE["frozen_sprint_record"],
        source_fragments=FIXTURE["source_fragments"],
        relevant_files=["src/example.py"],
        observed_at_utc="2026-09-06T15:00:00Z",
    )
    return root, resolver, service, result


def test_state_transition_matrix_is_strict_and_linear() -> None:
    state = StoryExecutionState(
        execution_id="story-exec-test",
        workspace_id="ws",
        project_id="project",
        story_id="story-inv-001",
        story_version="1.0.0",
        status=StoryExecutionStatus.PLANNED,
        sequence=0,
        dor_report_sha256="a" * 64,
        context_pack_id="context-1",
        context_pack_sha256="b" * 64,
        created_at_utc="2026-09-06T15:00:00Z",
        updated_at_utc="2026-09-06T15:00:00Z",
    )
    for target in (StoryExecutionStatus.IN_PROGRESS, StoryExecutionStatus.CHANGES_READY, StoryExecutionStatus.VALIDATING, StoryExecutionStatus.COMMIT_READY, StoryExecutionStatus.DONE):
        state = state.transition(target, actor_id="owner", observed_at_utc=f"2026-09-06T15:0{state.sequence + 1}:00Z")
    assert state.status is StoryExecutionStatus.DONE
    assert state.sequence == 5
    assert len(state.history) == 5


def test_invalid_state_transition_is_blocked() -> None:
    state = StoryExecutionState("e", "ws", "p", "s", "1.0.0", StoryExecutionStatus.PLANNED, 0, "a"*64, "c", "b"*64, "t", "t")
    with pytest.raises(StoryExecutionTransitionError, match="INVALID_TRANSITION"):
        state.transition(StoryExecutionStatus.CHANGES_READY, actor_id="owner", observed_at_utc="t2")


def test_dor_blocks_missing_required_trace_and_server_project_context() -> None:
    story = dict(FIXTURE["story"])
    story["trace_links"] = [x for x in story["trace_links"] if x["kind"] != "requirement"]
    report = StoryDoREvaluator().evaluate(
        story=story,
        frozen_sprint_record=FIXTURE["frozen_sprint_record"],
        source_fragments=FIXTURE["source_fragments"],
        project_context={"configured": False, "valid": True, "active_workspace_id": None},
        evaluated_at_utc="2026-09-06T15:00:00Z",
    )
    assert report["status"] == "BLOCK"
    assert report["blockers_total"] >= 2
    assert {x["code"] for x in report["checks"] if x["status"] == "BLOCK"} >= {"DOR_PROJECT_CONTEXT_SERVER_VALID", "DOR_TRACE_REQUIREMENT"}


def test_prepare_builds_deterministic_minimized_traceable_context_and_schemas(tmp_path: Path) -> None:
    root, resolver, service, result = _prepared(tmp_path)
    assert result.status == "PASS"
    dor = result.data["dor_report"]
    pack = result.data["context_pack"]
    state = result.data["story_execution_state"]
    assert dor["status"] == "PASS" and dor["blockers_total"] == 0
    kinds = {x["kind"] for x in pack["fragments"]}
    assert kinds == {"requirement", "adr", "risk", "test-intent", "acceptance"}
    assert all(x["write_authority"] is False for x in pack["fragments"])
    assert all(x["write_authority"] is False for x in pack["relevant_files"])
    assert pack["safety"]["context_minimized"] is True
    assert pack["safety"]["runtime_stores_excluded"] is True
    assert state["status"] == "PLANNED"
    jsonschema.Draft202012Validator(_schema("story_dor_report.schema.json")).validate(dor)
    jsonschema.Draft202012Validator(_schema("story_context_pack.schema.json")).validate(pack)
    jsonschema.Draft202012Validator(_schema("story_execution_state.schema.json")).validate(state)

    again = StoryContextPackBuilder(root).build(
        workspace_id="pilot-workspace", project_id="pilot-local", story=FIXTURE["story"], source_fragments=FIXTURE["source_fragments"], relevant_files=["src/example.py"], created_at_utc="2099-01-01T00:00:00Z"
    )
    assert again["context_sha256"] == pack["context_sha256"]


def test_context_pack_blocks_secret_runtime_store_and_path_escape(tmp_path: Path) -> None:
    root, _ = _workspace(tmp_path)
    builder = StoryContextPackBuilder(root)
    bad_fragments = json.loads(json.dumps(FIXTURE["source_fragments"]))
    bad_fragments["FR-INV-001"]["content"] = "api_key=sk-proj-abcdefghijklmnop"
    with pytest.raises(StoryContextPackError, match="SECRET_BLOCKED"):
        builder.build(workspace_id="ws", project_id="p", story=FIXTURE["story"], source_fragments=bad_fragments, relevant_files=["src/example.py"], created_at_utc="t")
    with pytest.raises(StoryContextPackError, match="RUNTIME_OR_SECRET_PATH"):
        builder.build(workspace_id="ws", project_id="p", story=FIXTURE["story"], source_fragments=FIXTURE["source_fragments"], relevant_files=["outputs/devpilot.db"], created_at_utc="t")
    with pytest.raises(StoryContextPackError, match="PATH_ESCAPE"):
        builder.build(workspace_id="ws", project_id="p", story=FIXTURE["story"], source_fragments=FIXTURE["source_fragments"], relevant_files=["../secret.txt"], created_at_utc="t")


def test_prepare_blocks_before_state_when_dor_is_missing(tmp_path: Path) -> None:
    root, resolver = _workspace(tmp_path)
    story = dict(FIXTURE["story"])
    story["acceptance_criteria"] = []
    service = StoryExecutionApplicationService(root, context_resolver=resolver)
    result = service.prepare(story=story, frozen_sprint_record=FIXTURE["frozen_sprint_record"], source_fragments=FIXTURE["source_fragments"], relevant_files=["src/example.py"], observed_at_utc="t")
    assert result.status == "BLOCK"
    store = StoryExecutionStore(root, workspace_id="pilot-workspace")
    assert store.load_state() is None
    assert store.load_context() is None
    assert store.load_dor()["status"] == "BLOCK"


def test_start_requires_preimage_and_durable_dor_context_match(tmp_path: Path) -> None:
    root, resolver, service, prepared = _prepared(tmp_path)
    state = prepared.data["story_execution_state"]
    blocked = service.start(expected_state_sha256="0" * 64, actor_id="owner", observed_at_utc="2026-09-06T15:01:00Z")
    assert blocked.status == "BLOCK"
    started = service.start(expected_state_sha256=state["state_sha256"], actor_id="owner", observed_at_utc="2026-09-06T15:01:00Z")
    assert started.status == "PASS"
    assert started.data["story_execution_state"]["status"] == "IN_PROGRESS"
    assert started.data["story_execution_state"]["sequence"] == 1


def test_project_status_projects_current_story_without_browser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, resolver, service, prepared = _prepared(tmp_path)
    state = prepared.data["story_execution_state"]
    service.start(expected_state_sha256=state["state_sha256"], actor_id="owner", observed_at_utc="2026-09-06T15:01:00Z")
    app = GuidedSDLCApplicationService(root, context_resolver=resolver)
    projection = ProjectProgressEngine.unknown(workspace_id="pilot-workspace", observed_at_utc="2026-09-06T15:02:00Z")
    fake = SimpleNamespace(project_status=lambda **_: projection, next_action=lambda **_: projection)
    monkeypatch.setattr(app, "_service", lambda: fake)
    result = app.project_status_primary(workspace_id="pilot-workspace", observed_at_utc="2026-09-06T15:02:00Z")
    current = result.data["project_status"]["planning"]["current_story"]
    assert current["story_id"] == "story-inv-001"
    assert current["status"] == "IN_PROGRESS"
    assert current["read_only"] is True
    jsonschema.Draft202012Validator(_schema("guided_sdlc_project_status.schema.json")).validate(result.data["project_status"])


def test_context_pack_is_runtime_only_and_source_tree_unchanged(tmp_path: Path) -> None:
    root, _, _, result = _prepared(tmp_path)
    assert result.status == "PASS"
    assert (root / "src/example.py").read_text(encoding="utf-8").startswith("def create_item")
    assert (root / "outputs/story_execution/gsdlc_09_a/pilot-workspace/current_state.json").is_file()
    assert not any(p.name.startswith(("auth.db", "devpilot.db")) for p in (root / "outputs").rglob("*"))


def test_story_execution_package_imports_standalone_without_application_import_order_dependency() -> None:
    import subprocess
    import sys

    completed = subprocess.run(
        [sys.executable, "-c", "import devpilot_core.story_execution as s; assert s.StoryDoREvaluator is not None"],
        cwd=ROOT,
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout
