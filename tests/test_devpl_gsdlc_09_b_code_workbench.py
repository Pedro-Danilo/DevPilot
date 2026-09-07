from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devpilot_core.application import ApplicationService, AuthApplicationService
from devpilot_core.code_workbench import CodeWorkbenchApplicationService
from devpilot_core.identity.auth_models import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.story_execution import StoryExecutionState, StoryExecutionStatus, StoryExecutionStore

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = {"Origin": "http://127.0.0.1:5173"}
PASSWORD = "correct horse battery staple"


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "code-workspace"
    (root / ".devpilot").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "assets").mkdir()
    (root / ".devpilot/project.yaml").write_text("project_id: code-fixture\nproject_name: Code Fixture\nproject_type: software\n", encoding="utf-8")
    (root / "src/app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    (root / "src/view.ts").write_text("export const view = 'safe';\n", encoding="utf-8")
    (root / ".env").write_text("SECRET=never-index\n", encoding="utf-8")
    (root / "assets/blob.bin").write_bytes(b"\x00\x01binary")
    outside = tmp_path / "outside.py"; outside.write_text("outside = True\n", encoding="utf-8")
    try:
        (root / "src/outside-link.py").symlink_to(outside)
    except OSError:
        pass
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(root))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(root))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)
    state = StoryExecutionState(
        execution_id="story-exec-1234567890abcdef12345678", workspace_id=root.name, project_id="code-fixture",
        story_id="story-first", story_version="1.0.0", status=StoryExecutionStatus.IN_PROGRESS, sequence=1,
        dor_report_sha256="a"*64, context_pack_id="story-context-1234567890abcdef12345678", context_pack_sha256="b"*64,
        created_at_utc="2026-09-07T10:00:00+00:00", updated_at_utc="2026-09-07T10:01:00+00:00",
    )
    StoryExecutionStore(root, workspace_id=root.name).save_state(state)
    return root


def _service() -> CodeWorkbenchApplicationService:
    app = ApplicationService(ROOT)
    return app.code_workbench


def _source(service: CodeWorkbenchApplicationService, rel: str) -> dict:
    listed = service.list_sources(); assert listed.ok, listed.to_dict()
    return next(x for x in listed.data["sources"] if x["relative_path"] == rel)


def test_source_tree_is_bounded_and_current_story_is_visible(workspace: Path) -> None:
    service = _service(); status = service.status(); listed = service.list_sources()
    assert status.ok and status.data["story"]["story_id"] == "story-first"
    paths = {x["relative_path"] for x in listed.data["sources"]}
    assert "src/app.py" in paths and "src/view.ts" in paths
    assert ".env" not in paths and "assets/blob.bin" not in paths and "src/outside-link.py" not in paths
    assert listed.data["summary"]["source_mutations_performed"] is False
    assert listed.data["source_policy"]["apply_enabled"] is False


def test_edit_draft_never_mutates_source_and_recheck_passes(workspace: Path) -> None:
    service = _service(); row = _source(service, "src/app.py"); read = service.read_source(row["source_id"])
    before = (workspace / "src/app.py").read_bytes(); source = read.data["source"]
    saved = service.save_draft(operation="EDIT", content="def answer():\n    return 43\n", target_path="src/app.py", source_id=row["source_id"], expected_source_sha256=source["sha256"], expected_revision_sha256=None, actor="owner.local", actor_role="owner")
    assert saved.ok, saved.to_dict(); assert (workspace / "src/app.py").read_bytes() == before
    draft = saved.data["draft"]
    assert draft["safety"]["source_mutations_performed"] is False and draft["safety"]["apply_enabled"] is False
    recheck = service.recheck_draft(draft["draft_id"]); assert recheck.ok, recheck.to_dict()


def test_external_edit_invalidates_edit_draft(workspace: Path) -> None:
    service = _service(); row = _source(service, "src/app.py"); source = service.read_source(row["source_id"]).data["source"]
    saved = service.save_draft(operation="EDIT", content="changed in draft\n", target_path="src/app.py", source_id=row["source_id"], expected_source_sha256=source["sha256"], expected_revision_sha256=None, actor="owner.local", actor_role="owner")
    assert saved.ok
    (workspace / "src/app.py").write_text("# external edit\n", encoding="utf-8")
    conflict = service.recheck_draft(saved.data["draft"]["draft_id"])
    assert not conflict.ok and any(f.id == "GSDLC09B_EXTERNAL_EDIT_CONFLICT" for f in conflict.findings)
    assert "external edit" in (workspace / "src/app.py").read_text(encoding="utf-8")


def test_create_and_rename_are_drafts_only(workspace: Path) -> None:
    service = _service()
    created = service.save_draft(operation="CREATE", content="value = 1\n", target_path="src/new_file.py", source_id=None, expected_source_sha256=None, expected_revision_sha256=None, actor="owner.local", actor_role="developer")
    assert created.ok and not (workspace / "src/new_file.py").exists()
    row = _source(service, "src/view.ts"); source = service.read_source(row["source_id"]).data["source"]
    renamed = service.save_draft(operation="RENAME", content=source["content"], target_path="src/view-renamed.ts", source_id=row["source_id"], expected_source_sha256=source["sha256"], expected_revision_sha256=None, actor="owner.local", actor_role="owner")
    assert renamed.ok and (workspace / "src/view.ts").is_file() and not (workspace / "src/view-renamed.ts").exists()


def test_path_binary_oversize_secret_and_role_negatives_fail_closed(workspace: Path) -> None:
    service = _service()
    for bad in ["../escape.py", ".hidden.py", "outputs/escape.py", "src/tool.exe"]:
        result = service.save_draft(operation="CREATE", content="safe\n", target_path=bad, source_id=None, expected_source_sha256=None, expected_revision_sha256=None, actor="owner.local", actor_role="owner")
        assert not result.ok, bad
    secret = service.save_draft(operation="CREATE", content="api_key=sk-proj-abcdefghijklmnop\n", target_path="src/secret.py", source_id=None, expected_source_sha256=None, expected_revision_sha256=None, actor="owner.local", actor_role="owner")
    assert not secret.ok and any(f.id == "GSDLC09B_SECRET_DRAFT_BLOCK" for f in secret.findings)
    denied = service.save_draft(operation="CREATE", content="safe\n", target_path="src/architect.py", source_id=None, expected_source_sha256=None, expected_revision_sha256=None, actor="arch.local", actor_role="architect")
    assert not denied.ok and any(f.id == "GSDLC09B_ROLE_BLOCK" for f in denied.findings)


def test_optimistic_draft_revision_blocks_stale_update(workspace: Path) -> None:
    service=_service(); row=_source(service,"src/app.py"); src=service.read_source(row["source_id"]).data["source"]
    first=service.save_draft(operation="EDIT",content="one\n",target_path="src/app.py",source_id=row["source_id"],expected_source_sha256=src["sha256"],expected_revision_sha256=None,actor="owner.local",actor_role="owner")
    rev=first.data["draft"]["revision_sha256"]
    second=service.save_draft(operation="EDIT",content="two\n",target_path="src/app.py",source_id=row["source_id"],expected_source_sha256=src["sha256"],expected_revision_sha256=rev,actor="owner.local",actor_role="owner")
    assert second.ok
    stale=service.save_draft(operation="EDIT",content="stale\n",target_path="src/app.py",source_id=row["source_id"],expected_source_sha256=src["sha256"],expected_revision_sha256=rev,actor="owner.local",actor_role="owner")
    assert not stale.ok and any(f.id=="GSDLC09B_DRAFT_REVISION_CONFLICT" for f in stale.findings)


def _human_client(tmp_path: Path) -> TestClient:
    store=LocalAuthStore(tmp_path/"auth")
    auth=AuthApplicationService(tmp_path/"auth",store=store)
    client=TestClient(create_app(ROOT,api_token="legacy-09b",auth_service=auth))
    r=client.post("/api/v1/auth/bootstrap/owner",json={"username":"owner.local","display_name":"Local Owner","password":PASSWORD},headers=ORIGIN)
    assert r.status_code==201,r.text
    return client


def _csrf(client: TestClient) -> dict[str,str]:
    return {"Origin":ORIGIN["Origin"],CSRF_HEADER_NAME:str(client.cookies.get(CSRF_COOKIE_NAME))}


def test_api_requires_human_session_and_exposes_no_apply_route(workspace: Path, tmp_path: Path) -> None:
    unauth=TestClient(create_app(ROOT,api_token="legacy-09b"))
    r=unauth.get("/api/v1/story/code/sources",headers={"X-DevPilot-Token":"legacy-09b"})
    assert r.status_code in {401,403}
    client=_human_client(tmp_path)
    sources=client.get("/api/v1/story/code/sources",headers=ORIGIN); assert sources.status_code==200,sources.text
    row=next(x for x in sources.json()["data"]["sources"] if x["relative_path"]=="src/app.py")
    read=client.get(f"/api/v1/story/code/sources/{row['source_id']}",headers=ORIGIN); assert read.status_code==200
    source=read.json()["data"]["source"]
    body={"operation":"EDIT","content":"def answer():\n    return 99\n","target_path":"src/app.py","source_id":row["source_id"],"expected_source_sha256":source["sha256"],"expected_revision_sha256":None}
    saved=client.post("/api/v1/story/code/drafts",json=body,headers=_csrf(client)); assert saved.status_code==200,saved.text
    assert (workspace/"src/app.py").read_text(encoding="utf-8").endswith("return 42\n")
    blocked=client.post("/api/v1/story/code/apply",json={},headers=_csrf(client)); assert blocked.status_code==403 and any(f.get("id")=="API_POLICY_BINDING_MISSING_BLOCK" for f in blocked.json().get("findings",[]))


def test_schemas_validate_policy_and_draft(workspace: Path) -> None:
    from jsonschema import Draft202012Validator
    policy=json.loads((ROOT/".devpilot/code_workbench/source_policy.json").read_text())
    schema=json.loads((ROOT/"docs/schemas/gsdlc_09_b_source_policy.schema.json").read_text())
    Draft202012Validator(schema).validate(policy)
    service=_service(); created=service.save_draft(operation="CREATE",content="x=1\n",target_path="src/schema.py",source_id=None,expected_source_sha256=None,expected_revision_sha256=None,actor="owner.local",actor_role="owner")
    draft_schema=json.loads((ROOT/"docs/schemas/gsdlc_09_b_source_draft_buffer.schema.json").read_text())
    Draft202012Validator(draft_schema).validate(created.data["draft"])
