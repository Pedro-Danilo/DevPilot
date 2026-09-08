from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devpilot_core.application import ApplicationService, AuthApplicationService
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.story_execution import StoryExecutionState, StoryExecutionStatus, StoryExecutionStore

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = {"Origin": "http://127.0.0.1:5173"}
PASSWORD = "A-very-long-local-password-09d"


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "agent-story-workspace"
    (root / ".devpilot").mkdir(parents=True)
    (root / "src").mkdir()
    (root / ".devpilot/project.yaml").write_text(
        "project_id: agent-story-fixture\nproject_name: Agent Story Fixture\nproject_type: software\n",
        encoding="utf-8",
    )
    (root / "src/app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(root))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(root))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)
    store = StoryExecutionStore(root, workspace_id=root.name)
    store.save_state(
        StoryExecutionState(
            execution_id="story-exec-09d1234567890abcdef1234",
            workspace_id=root.name,
            project_id="agent-story-fixture",
            story_id="story-09d",
            story_version="1.0.0",
            status=StoryExecutionStatus.IN_PROGRESS,
            sequence=1,
            dor_report_sha256="a" * 64,
            context_pack_id="story-context-09d1234567890abcdef12",
            context_pack_sha256="b" * 64,
            created_at_utc="2026-09-08T12:00:00Z",
            updated_at_utc="2026-09-08T12:01:00Z",
        )
    )
    store.save_context(
        {
            "schema_id": "SCHEMA-DEVPL-STORY-CONTEXT-PACK-V1",
            "context_pack_id": "story-context-09d1234567890abcdef12",
            "context_sha256": "b" * 64,
            "story": {"story_id": "story-09d", "title": "Proposal only agent story"},
            "fragments": [
                {"kind": "requirement", "text": "Keep source changes human governed."},
                {"kind": "acceptance", "text": "Agent proposals must never write source directly."},
            ],
            "safety": {"secrets_included": False, "runtime_stores_included": False},
        }
    )
    return root


def _app() -> ApplicationService:
    return ApplicationService(ROOT)


def _source(app: ApplicationService) -> dict:
    listed = app.story_code_sources(); assert listed.ok, listed.to_dict()
    row = next(x for x in listed.data["sources"] if x["relative_path"] == "src/app.py")
    read = app.story_code_source_read(source_id=row["source_id"]); assert read.ok, read.to_dict()
    return read.data["source"]


def test_coding_agent_proposal_is_mock_local_traceable_and_zero_mutation(workspace: Path) -> None:
    app = _app(); src = _source(app); before = (workspace / "src/app.py").read_bytes()
    result = app.story_agent_proposal_create(
        agent_type="coding", mode="mock", instruction="Add a human-review marker for this story.",
        source_id=src["source_id"], actor="local-owner", actor_role="owner",
    )
    assert result.ok, result.to_dict(); proposal = result.data["proposal"]
    assert proposal["status"] == "PROPOSED" and proposal["agent_type"] == "coding"
    for key in ("model_id", "provider_id", "access_route_id", "agent_session", "trace_id", "tool_intent", "tool_execution_decision", "provenance"):
        assert proposal.get(key), key
    assert proposal["cost"]["estimated_cost_usd"] == 0.0
    assert proposal["safety"]["proposal_only"] is True
    assert proposal["safety"]["source_mutations_performed"] is False
    assert proposal["safety"]["draft_mutations_performed"] is False
    assert proposal["tool_execution_decision"]["model_route_granted_permission"] is False
    assert proposal["tool_execution_decision"]["tool_executed"] is False
    assert proposal["forbidden_delete_decision"]["effect"] == "BLOCK"
    assert (workspace / "src/app.py").read_bytes() == before
    assert not (workspace / "outputs" / "code_workbench").exists()


def test_human_accept_only_authorizes_editor_insertion(workspace: Path) -> None:
    app = _app(); src = _source(app); before = (workspace / "src/app.py").read_bytes()
    created = app.story_agent_proposal_create(agent_type="coding", mode="mock", instruction="Prepare a bounded code proposal.", source_id=src["source_id"], actor="human-dev", actor_role="developer")
    assert created.ok, created.to_dict(); p = created.data["proposal"]
    decision = app.story_agent_proposal_decide(proposal_id=p["proposal_id"], proposal_sha256=p["proposal_sha256"], decision="ACCEPT", actor="human-dev", actor_role="developer")
    assert decision.ok, decision.to_dict()
    assert decision.data["insert_into_editor_authorized"] is True
    assert decision.data["source_mutations_performed"] is False
    assert decision.data["draft_mutations_performed"] is False
    assert (workspace / "src/app.py").read_bytes() == before


def test_test_agent_proposal_is_create_only_and_reject_is_zero_mutation(workspace: Path) -> None:
    app = _app(); before = sorted(p.relative_to(workspace).as_posix() for p in workspace.rglob("*.py"))
    created = app.story_agent_proposal_create(agent_type="test", mode="mock", instruction="Propose a test for the acceptance contract.", source_id=None, actor="local-owner", actor_role="owner")
    assert created.ok, created.to_dict(); p = created.data["proposal"]
    assert p["operation"] == "CREATE" and p["target_path"].startswith("tests/")
    assert p["agent_type"] == "test" and p["safety"]["proposal_only"] is True
    decision = app.story_agent_proposal_decide(proposal_id=p["proposal_id"], proposal_sha256=p["proposal_sha256"], decision="REJECT", actor="local-owner", actor_role="owner")
    assert decision.ok and decision.data["proposal"]["status"] == "REJECTED"
    after = sorted(p.relative_to(workspace).as_posix() for p in workspace.rglob("*.py"))
    assert after == before


def test_unsafe_delete_and_over_budget_instruction_fail_closed(workspace: Path) -> None:
    app = _app(); src = _source(app)
    unsafe = app.story_agent_proposal_create(agent_type="coding", mode="mock", instruction="Use filesystem.delete before editing.", source_id=src["source_id"], actor="local-owner", actor_role="owner")
    assert not unsafe.ok and any(f.id == "GSDLC09D_UNSAFE_PROPOSAL_BLOCK" for f in unsafe.findings)
    over = app.story_agent_proposal_create(agent_type="coding", mode="mock", instruction="x" * 2001, source_id=src["source_id"], actor="local-owner", actor_role="owner")
    assert not over.ok and any(f.id == "GSDLC09D_INSTRUCTION_BUDGET_BLOCK" for f in over.findings)


def test_stale_source_blocks_human_accept(workspace: Path) -> None:
    app = _app(); src = _source(app)
    created = app.story_agent_proposal_create(agent_type="coding", mode="mock", instruction="Propose a safe marker.", source_id=src["source_id"], actor="local-owner", actor_role="owner")
    assert created.ok; p = created.data["proposal"]
    (workspace / "src/app.py").write_text("# external edit\n", encoding="utf-8")
    result = app.story_agent_proposal_decide(proposal_id=p["proposal_id"], proposal_sha256=p["proposal_sha256"], decision="ACCEPT", actor="local-owner", actor_role="owner")
    assert not result.ok and any(f.id == "GSDLC09D_PROPOSAL_STALE_SOURCE_BLOCK" for f in result.findings)


def test_fake_local_route_remains_zero_cost_and_no_tool_authority(workspace: Path) -> None:
    app = _app(); src = _source(app)
    result = app.story_agent_proposal_create(agent_type="coding", mode="fake-local", instruction="Propose a local-only code marker.", source_id=src["source_id"], actor="local-owner", actor_role="owner")
    assert result.ok, result.to_dict(); p = result.data["proposal"]
    assert p["mode"] == "fake-local" and p["cost"]["estimated_cost_usd"] == 0.0
    assert p["safety"]["network_used"] is False and p["safety"]["external_api_used"] is False
    assert p["safety"]["model_route_grants_tool_permission"] is False


def test_api_human_session_and_accept_reject_contract(workspace: Path, tmp_path: Path) -> None:
    auth_store = LocalAuthStore(tmp_path / "auth09d")
    auth = AuthApplicationService(tmp_path / "auth09d", store=auth_store)
    client = TestClient(create_app(ROOT, api_token="legacy-09d", auth_service=auth))
    boot = client.post("/api/v1/auth/bootstrap/owner", json={"username":"owner09d","display_name":"Owner 09D","password":PASSWORD}, headers=ORIGIN)
    assert boot.status_code == 201, boot.text
    csrf = {"Origin": ORIGIN["Origin"], "X-DevPilot-CSRF": str(client.cookies.get("devpilot_csrf") or "")}
    sources = client.get("/api/v1/story/code/sources", headers=ORIGIN); assert sources.status_code == 200, sources.text
    source_id = next(x["source_id"] for x in sources.json()["data"]["sources"] if x["relative_path"] == "src/app.py")
    created = client.post("/api/v1/story/code/agent-assist/proposals", json={"agent_type":"coding","mode":"mock","instruction":"Prepare human-review code proposal.","source_id":source_id}, headers=csrf)
    assert created.status_code == 200, created.text
    p = created.json()["data"]["proposal"]
    got = client.get(f"/api/v1/story/code/agent-assist/proposals/{p['proposal_id']}", headers=ORIGIN)
    assert got.status_code == 200 and got.json()["data"]["proposal"]["proposal_id"] == p["proposal_id"]
    decided = client.post(f"/api/v1/story/code/agent-assist/proposals/{p['proposal_id']}/decision", json={"proposal_sha256":p["proposal_sha256"],"decision":"ACCEPT"}, headers=csrf)
    assert decided.status_code == 200, decided.text
    assert decided.json()["data"]["source_mutations_performed"] is False


def test_ui_static_contract_exposes_proposal_only_controls() -> None:
    text = (ROOT / "ui/web/src/pages/StoryCodeWorkbenchView.ts").read_text(encoding="utf-8")
    for marker in ["proposal-only", "CodingAgent", "TestAgent", "agentProposalDiff", "agentProvenance", "agentToolDecision", "Aceptar en editor", "Rechazar propuesta", "source/draft write=false"]:
        assert marker in text
    assert "storyAgentProposalCreate" in (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
