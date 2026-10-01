from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devpilot_core.application import AuthApplicationService
from devpilot_core.application.story_activation_service import StoryActivationApplicationService
from devpilot_core.application.ui_workspace_context import UiWorkspaceContext
from devpilot_core.identity.auth_models import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.interfaces.api.security import resolve_route_policy
from devpilot_core.story_execution import StoryExecutionStatus, StoryExecutionStore

ROOT = Path(__file__).resolve().parents[1]


class StaticResolver:
    def __init__(self, context: UiWorkspaceContext) -> None:
        self.context = context

    def resolve(self) -> UiWorkspaceContext:
        return self.context


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture(tmp_path: Path):
    platform = tmp_path / "platform"
    workspace = tmp_path / "inventory-sales-local-greenfield"
    platform.mkdir(parents=True)
    workspace.mkdir(parents=True)
    workspace_id = "inventory-sales-local-greenfield"

    _write(
        workspace / ".devpilot/project.yaml",
        'schema_version: "1.0"\nproject:\n  id: "inventory-sales-local-greenfield"\n  name: "Inventory Sales"\n  type: "application"\n  owner: "owner"\n',
    )
    _write(
        workspace / "docs/01_requirements/requirements_specification.md",
        "# Requirements\n\n### RF-001\nCreate a product with a stable identifier.\n\n### RF-002\nList current products.\n",
    )
    _write(workspace / "docs/02_architecture/adrs/ADR-001.md", "# ADR-001\n\nKeep the first implementation local and deterministic.\n")
    _write(workspace / "docs/03_security/security_threat_model.md", "# Risks\n\n### SEC-001\nReject invalid product identity.\n")
    _write(workspace / "docs/04_quality/test_strategy.md", "# Test Strategy\n\n### TEST-001\nVerify create product.\n\n### TEST-002\nVerify list products.\n")

    story1 = {
        "id": "story-rf-001",
        "version": "1.0.0",
        "title": "Create product",
        "acceptance_criteria": ["A valid product can be created and observed by id."],
        "trace_links": [
            {"kind": "requirement", "target_id": "RF-001"},
            {"kind": "adr", "target_id": "ADR-001"},
            {"kind": "risk", "target_id": "SEC-001"},
            {"kind": "test-intent", "target_id": "TEST-001"},
        ],
    }
    story2 = {
        "id": "story-rf-002",
        "version": "1.0.0",
        "title": "List products",
        "acceptance_criteria": ["Current products can be listed deterministically."],
        "trace_links": [
            {"kind": "requirement", "target_id": "RF-002"},
            {"kind": "adr", "target_id": "ADR-001"},
            {"kind": "risk", "target_id": "SEC-001"},
            {"kind": "test-intent", "target_id": "TEST-002"},
        ],
    }
    sprint_record = {
        "schema_id": "DEVPL-GSDLC-08-D-SPRINT-PLANNER-V1",
        "lifecycle": "FROZEN",
        "backlog": {"stories": [story1, story2]},
        "sprint_plan": {
            "sprint_plan_id": "sprint-plan-pilot-a",
            "selected_stories": [
                {"story_id": story1["id"], "readiness": "READY", "blocking_reasons": [], "estimate": 1},
                {"story_id": story2["id"], "readiness": "READY", "blocking_reasons": [], "estimate": 1},
            ],
            "definition_of_ready": ["Requirement, ADR, risk and test intent are bound."],
            "definition_of_done": ["Targeted tests and governed Git evidence pass."],
            "test_intent_ids": ["TEST-001", "TEST-002"],
            "risk_focus_ids": ["SEC-001"],
            "completed_story_ids": [],
        },
    }
    sprint_path = workspace / "outputs/planning/gsdlc_08_d" / workspace_id / "sprint_planner.json"
    _write(sprint_path, json.dumps(sprint_record, indent=2))

    context = UiWorkspaceContext(
        platform_root=platform,
        mode="active-root",
        configured=True,
        valid=True,
        active_workspace_id=workspace_id,
        active_workspace_root=workspace,
        reports_root=workspace / "outputs/reports",
        traces_root=workspace / "outputs/traces",
        project_file=workspace / ".devpilot/project.yaml",
    )
    return platform, workspace, workspace_id, StaticResolver(context), story1, story2, sprint_path


def test_d01_frozen_planning_projects_ready_story_and_prepares_context(tmp_path: Path) -> None:
    platform, workspace, wid, resolver, story1, story2, sprint_path = _fixture(tmp_path)
    before_sprint = sprint_path.read_bytes()
    service = StoryActivationApplicationService(platform, context_resolver=resolver)

    status = service.status().to_dict()
    assert status["ok"] is True
    activation = status["data"]["story_activation"]
    assert activation["status"] == "READY_TO_PREPARE"
    assert [x["story_id"] for x in activation["ready_candidates"]] == [story1["id"], story2["id"]]
    assert activation["recommended_story_id"] == story1["id"]

    prepared = service.prepare(
        story_id=story1["id"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-09-30T21:30:00Z"
    ).to_dict()
    assert prepared["ok"] is True
    data = prepared["data"]
    assert data["dor_report"]["status"] == "PASS"
    assert data["story_execution_state"]["status"] == "PLANNED"
    assert data["story_execution_state"]["story_id"] == story1["id"]
    assert data["context_pack"]["story"]["id"] == story1["id"]
    assert {x["kind"] for x in data["context_pack"]["fragments"]} == {"requirement", "adr", "risk", "test-intent", "acceptance"}
    assert data["implementation_route"]["manual"]["first_class"] is True
    assert data["implementation_route"]["external_api_required"] is False
    assert data["safety"]["planning_artifacts_mutated"] is False
    assert data["safety"]["source_mutations_performed"] is False
    assert sprint_path.read_bytes() == before_sprint
    assert not (workspace / "src").exists()


def test_d01_start_is_hash_bound_and_blocks_second_story_while_active(tmp_path: Path) -> None:
    platform, workspace, wid, resolver, story1, story2, _ = _fixture(tmp_path)
    service = StoryActivationApplicationService(platform, context_resolver=resolver)
    prepared = service.prepare(story_id=story1["id"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-09-30T21:30:00Z").to_dict()["data"]

    bad = service.start(expected_state_sha256="0" * 64, actor_id="owner-1", actor_role="owner", observed_at_utc="2026-09-30T21:31:00Z").to_dict()
    assert bad["ok"] is False

    started = service.start(expected_state_sha256=prepared["story_execution_state"]["state_sha256"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-09-30T21:31:00Z").to_dict()
    assert started["ok"] is True
    assert started["data"]["story_execution_state"]["status"] == "IN_PROGRESS"

    blocked = service.prepare(story_id=story2["id"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-09-30T21:32:00Z").to_dict()
    assert blocked["ok"] is False
    assert blocked["findings"][0]["id"] == "GSDLC13D01_ACTIVE_STORY_BLOCK"


def test_d05_done_story_is_archived_and_not_reselected(tmp_path: Path) -> None:
    platform, workspace, wid, resolver, story1, story2, _ = _fixture(tmp_path)
    service = StoryActivationApplicationService(platform, context_resolver=resolver)
    prepared = service.prepare(story_id=story1["id"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-09-30T21:30:00Z").to_dict()["data"]
    service.start(expected_state_sha256=prepared["story_execution_state"]["state_sha256"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-09-30T21:31:00Z")

    store = StoryExecutionStore(workspace, workspace_id=wid)
    state = store.load_state()
    assert state is not None
    for target in (StoryExecutionStatus.CHANGES_READY, StoryExecutionStatus.VALIDATING, StoryExecutionStatus.COMMIT_READY, StoryExecutionStatus.DONE):
        state = state.transition(target, actor_id="owner-1", observed_at_utc="2026-09-30T21:40:00Z")
        store.save_state(state)

    status = service.status().to_dict()["data"]["story_activation"]
    assert story1["id"] in status["completed_story_ids"]
    assert [x["story_id"] for x in status["ready_candidates"]] == [story2["id"]]

    second = service.prepare(story_id=story2["id"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-09-30T21:50:00Z").to_dict()
    assert second["ok"] is True
    assert second["data"]["story_execution_state"]["story_id"] == story2["id"]
    assert (store.history_root / state.execution_id / "story_execution_state.json").is_file()
    assert story1["id"] in store.completed_story_ids()


def test_d01_transport_policy_and_ui_contract_are_registered() -> None:
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    ui = json.loads((ROOT / ".devpilot/interfaces/ui_route_contract_registry.json").read_text(encoding="utf-8"))
    route_ids = {r["route_id"] for r in api["routes"]}
    policy_ids = {r["route_id"] for r in rbac["route_policies"]}
    expected = {
        "api.story-code.activation.status",
        "api.story-code.activation.prepare",
        "api.story-code.activation.start",
    }
    assert expected <= route_ids
    assert expected <= policy_ids
    assert len(api["routes"]) == len(rbac["route_policies"]) == 243
    assert api["summary"]["gsdlc_13_d_01_story_activation_routes_total"] == 3
    assert rbac["summary"]["gsdlc_13_d_01_story_activation_policies_total"] == 3
    story_ui = next(x for x in ui["routes"] if x["route_id"] == "ui.story-code-workbench")
    assert expected <= set(story_ui["allowed_api_routes"])

    assert resolve_route_policy("GET", "/api/v1/story/code/activation") is not None
    assert resolve_route_policy("POST", "/api/v1/story/code/activation/prepare") is not None
    assert resolve_route_policy("POST", "/api/v1/story/code/activation/start") is not None

    router_text = (ROOT / "src/devpilot_core/interfaces/api/routers/story_code.py").read_text(encoding="utf-8")
    assert '@router.get("/api/v1/story/code/activation")' in router_text
    assert '@router.post("/api/v1/story/code/activation/prepare")' in router_text
    assert '@router.post("/api/v1/story/code/activation/start")' in router_text

    view = (ROOT / "ui/web/src/pages/StoryCodeWorkbenchView.ts").read_text(encoding="utf-8")
    for marker in (
        "storyActivationPanel",
        "storyReadyCandidates",
        "Preparar contexto",
        "storyDorReport",
        "storyContextPack",
        "implementationRoute",
        "Iniciar story preparada",
    ):
        assert marker in view



def test_d01_v103_run_card_and_story_code_operational_contract() -> None:
    run_card = (ROOT / "docs/validation/RUN_CARD_13_D_01_v1_0_3_APPROVED.md").read_text(encoding="utf-8")
    for marker in (
        'version: "1.0.3"',
        "RUN_02",
        "Story activation & context",
        "04_ready_story_before_prepare.png",
        "05_dor_context_pack_planned.png",
        "06_story_execution_in_progress.png",
        "07_context_reviewability.png",
        "08_implementation_route_provenance.png",
        "09_stop_before_d02.png",
        "99_block_state.png",
        "no source mutation antes de D02",
    ):
        assert marker in run_card

    contract = (ROOT / "docs/05_operations/DEVPL_GSDLC_13_D_STORY_CODE_WORKBENCH_OPERATIONAL_CONTRACT_v1_0_0.md").read_text(encoding="utf-8")
    for product in (
        "StoryDoRReport",
        "StoryContextPack",
        "StoryExecutionState(PLANNED)",
        "SourceDraftBuffer",
        "SourceChangePlan",
        "TestImpactReport",
        "StoryTestPlan",
        "QualityReport",
        "CommitPlan",
        "GitCommitRecord",
    ):
        assert product in contract

    adjudication = (ROOT / "docs/audits/DEVPL_GSDLC_13_D_01_FIRST_ATTEMPT_ADJUDICATION_v1_0_0.md").read_text(encoding="utf-8")
    assert "CAP-13D01-STORY-ACTIVATION-002" in adjudication
    assert "BLOCK / FUNCTIONAL / ACTIVE-CORRECTIVE-REQUIRED" in adjudication

def test_d01_activation_api_transport_is_human_session_and_hash_bound(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, workspace, _, _, story1, _, _ = _fixture(tmp_path)
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(workspace))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)

    auth_root = tmp_path / "auth-d01"
    auth = AuthApplicationService(auth_root, store=LocalAuthStore(auth_root))
    client = TestClient(create_app(ROOT, api_token="legacy-d01", auth_service=auth))
    origin = {"Origin": "http://127.0.0.1:5173"}
    boot = client.post(
        "/api/v1/auth/bootstrap/owner",
        json={
            "username": "owner.d01",
            "display_name": "Owner D01",
            "password": "correct horse battery staple",
        },
        headers=origin,
    )
    assert boot.status_code == 201, boot.text
    csrf = {
        **origin,
        CSRF_HEADER_NAME: str(client.cookies.get(CSRF_COOKIE_NAME) or ""),
    }

    projected = client.get("/api/v1/story/code/activation", headers=origin)
    assert projected.status_code == 200, projected.text
    activation = projected.json()["data"]["story_activation"]
    assert activation["recommended_story_id"] == story1["id"]
    assert activation["status"] == "READY_TO_PREPARE"

    prepared = client.post(
        "/api/v1/story/code/activation/prepare",
        json={"story_id": story1["id"]},
        headers=csrf,
    )
    assert prepared.status_code == 200, prepared.text
    prepared_data = prepared.json()["data"]
    assert prepared_data["dor_report"]["status"] == "PASS"
    assert prepared_data["story_execution_state"]["status"] == "PLANNED"
    assert prepared_data["safety"]["source_mutations_performed"] is False

    planned_hash = prepared_data["story_execution_state"]["state_sha256"]
    stale = client.post(
        "/api/v1/story/code/activation/start",
        json={"expected_state_sha256": "0" * 64},
        headers=csrf,
    )
    assert stale.status_code == 403, stale.text
    assert stale.json()["ok"] is False

    started = client.post(
        "/api/v1/story/code/activation/start",
        json={"expected_state_sha256": planned_hash},
        headers=csrf,
    )
    assert started.status_code == 200, started.text
    assert started.json()["data"]["story_execution_state"]["status"] == "IN_PROGRESS"


def test_d01_v103_run_card_has_no_control_characters() -> None:
    payload = (ROOT / "docs/validation/RUN_CARD_13_D_01_v1_0_3_APPROVED.md").read_bytes()
    bad = sorted({value for value in payload if value < 32 and value not in {9, 10, 13}})
    assert bad == []
