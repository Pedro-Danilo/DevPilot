from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devpilot_core.application.approval_service import ApprovalApplicationService
from devpilot_core.application.auth_service import AuthApplicationService
from devpilot_core.application.services import ApplicationService
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.interfaces.api.security import resolve_route_policy
from devpilot_core.identity.auth_models import utc_now_iso

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "TestOwnerPassword!2026"

STAGES = [
    ("product-vision", "docs/00_product/product_vision.md", ["Resumen ejecutivo", "Problema", "Visión", "MVP", "Indicadores"]),
    ("scope", "docs/00_product/mvp_scope.md", ["MVP", "MVP+", "Out of scope", "Criterios"]),
    ("requirements", "docs/01_requirements/requirements_specification.md", ["Propósito", "Alcance", "Requerimientos funcionales del MVP", "Requerimientos no funcionales", "Criterios de bloqueo"]),
    ("architecture", "docs/02_architecture/architecture_document.md", ["Propósito", "Alcance", "Drivers", "Componentes", "Riesgos"]),
    ("security", "docs/03_security/security_threat_model.md", ["Propósito", "Alcance", "Amenazas", "Controles", "Criterios de bloqueo"]),
    ("test-strategy", "docs/04_quality/test_strategy.md", ["Propósito", "Alcance", "Tipos de pruebas", "Quality gates", "Criterios"]),
    ("traceability", "docs/01_requirements/traceability_matrix.md", ["Propósito", "Matriz"]),
]


def _copy_platform(tmp_path: Path) -> Path:
    platform = tmp_path / "platform"
    shutil.copytree(ROOT / ".devpilot", platform / ".devpilot", ignore=shutil.ignore_patterns("*.db", "*.db-*", "outputs", "__pycache__"))
    for rel in ["docs/schemas", "docs/validation", "docs/06_miasi"]:
        shutil.copytree(ROOT / rel, platform / rel)
    return platform


def _content(stage_id: str, headings: list[str]) -> str:
    body = [
        "---",
        f'doc_id: "GSDLC-05-E-{stage_id.upper().replace("-", "_")}"',
        f'title: "GSDLC-05-E {stage_id}"',
        'status: "draft"',
        'version: "1.0.0"',
        'owner: "owner05e.local"',
        'updated: "2026-08-25"',
        'approval: "pending"',
        "---",
        f"# {stage_id}",
        "",
    ]
    for heading in headings:
        body.extend([f"## {heading}", "", f"Contenido determinístico para {heading}. Local-first, sin secretos ni red externa.", ""])
    return "\n".join(body)


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    platform = _copy_platform(tmp_path)
    workspace = tmp_path / "workspace"
    for rel in ["docs/00_product", "docs/01_requirements", "docs/02_architecture", "docs/03_security", "docs/04_quality", ".devpilot"]:
        (workspace / rel).mkdir(parents=True, exist_ok=True)
    (workspace / ".devpilot/project.yaml").write_text("project_id: gsdlc05e-fixture\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.name", "Fixture"], cwd=workspace, check=True)
    subprocess.run(["git", "add", "."], cwd=workspace, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=workspace, check=True)

    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(workspace))
    monkeypatch.setenv("DEVPILOT_UOC005_CONTROL_ROOT", str(tmp_path / "control"))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)

    miasi_dir = platform / "outputs/workspaces/workspace"
    miasi_dir.mkdir(parents=True, exist_ok=True)
    (miasi_dir / "miasi_applicability_context.json").write_text(json.dumps({
        "schema_id":"SCHEMA-DEVPL-MIASI-APPLICABILITY-CONTEXT-V1", "schema_version":"1.0", "workspace_id":"workspace",
        "project":{"declared_ai_usage":False,"capabilities":[],"risk_level":"low","evidence_refs":["fixture:explicit-non-ai"]},
        "features":[], "risk_review_status":"NOT_REQUIRED", "evidence_refs":["fixture:gsdlc-05-e"]
    }, indent=2), encoding="utf-8")

    auth = AuthApplicationService(platform)
    issue = auth.bootstrap_owner(username="owner05e.local", display_name="GSDLC 05-E Owner", password=PASSWORD)
    service = ApplicationService(platform, approval_auth_store=auth.store)
    return platform, workspace, auth, issue, service


def _approve(platform: Path, auth: AuthApplicationService, issue, approval_id: str) -> None:
    result = ApprovalApplicationService(platform, auth_store=auth.store).decide_authenticated(
        approval_id=approval_id,
        decision="approved",
        principal=issue.context.principal,
        session=issue.context,
        caller_actor=None,
        reason="GSDLC-05-E browser-equivalent owner approval",
    )
    assert result.ok, result.to_dict()


def test_catalog_is_seven_stage_sequential_and_manual_import_only():
    payload = json.loads((ROOT / ".devpilot/gsdlc/pre_code_wizard_catalog.json").read_text(encoding="utf-8"))
    assert payload["schema_id"] == "devpilot.gsdlc05e.pre_code_wizard_catalog.v1"
    assert payload["profile_id"] == "guided-pre-code-manual-v1"
    assert [row["stage_id"] for row in payload["stages"]] == [x[0] for x in STAGES]
    assert [row["order"] for row in payload["stages"]] == list(range(1, 8))
    assert payload["stages"][0]["allowed_modes"] == ["MANUAL"]
    assert all(set(row["allowed_modes"]).issubset({"MANUAL", "IMPORT"}) for row in payload["stages"])


def test_skip_and_wrong_role_are_fail_closed_before_source_write(env):
    platform, workspace, auth, issue, service = env
    actor = issue.context.principal.actor_id
    before = subprocess.check_output(["git", "-C", str(workspace), "status", "--porcelain=v1", "-z"])
    skipped = service.guided_pre_code_save_draft(
        stage_id="requirements", content=_content("requirements", STAGES[2][2]), mode="MANUAL",
        actor=actor, actor_role="owner", session_principal=actor, effective_roles=["owner"], workspace_scopes=[],
    )
    assert not skipped.ok and any(f.id == "GSDLC05E_STAGE_SKIP_BLOCK" for f in skipped.findings)
    denied = service.guided_pre_code_save_draft(
        stage_id="product-vision", content=_content("product-vision", STAGES[0][2]), mode="MANUAL",
        actor=actor, actor_role="developer", session_principal=actor, effective_roles=["developer"], workspace_scopes=[],
    )
    assert not denied.ok and any(f.id == "GSDLC05E_AUTHOR_ROLE_BLOCK" for f in denied.findings)
    after = subprocess.check_output(["git", "-C", str(workspace), "status", "--porcelain=v1", "-z"])
    assert before == after == b""


def test_full_seven_stage_service_flow_reaches_pre_code_ready_with_exact_hashes(env):
    platform, workspace, auth, issue, service = env
    actor = issue.context.principal.actor_id
    trace_events = []
    for index, (stage_id, rel, headings) in enumerate(STAGES):
        status = service.guided_pre_code_status(effective_roles=["owner"], workspace_scopes=[])
        assert status.ok, status.to_dict()
        assert status.data["pre_code"]["current_stage_id"] == stage_id
        advisor = status.data["pre_code"]["advisor"]
        assert status.data["pre_code"]["miasi"]["status"] == "NOT_APPLICABLE"
        assert status.data["pre_code"]["miasi"]["gate_status"] == "PASS"
        assert advisor["status"] == "PASS"
        assert any(card["kind"] == "AGENT" and card["availability"] == "UNAVAILABLE" for card in advisor["actions"])
        assert any(card["kind"] == "RAG" and card["availability"] == "UNAVAILABLE" for card in advisor["actions"])

        mode = "MANUAL" if index == 0 or index % 2 == 0 else "IMPORT"
        content = _content(stage_id, headings)
        draft = service.guided_pre_code_save_draft(
            stage_id=stage_id, content=content, mode=mode, actor=actor, actor_role="owner", session_principal=actor,
            effective_roles=["owner"], workspace_scopes=[],
        )
        assert draft.ok, draft.to_dict()
        assert not (workspace / rel).exists(), "DRAFT must not preinject managed source"

        review = service.guided_pre_code_review(stage_id=stage_id, actor=actor, actor_role="owner", session_principal=actor, effective_roles=["owner"])
        assert review.ok, review.to_dict()
        record = review.data["review"]
        assert record["status"] == "APPROVAL_REQUIRED"
        assert record["plan"]["document"]["operation"] == "create"

        req = service.guided_pre_code_request_approval(
            stage_id=stage_id, actor=actor, actor_role="owner", session_principal=actor, effective_roles=["owner"],
            reason=f"Approve {stage_id} for 05-E fixture",
        )
        assert req.ok, req.to_dict()
        approval_id = req.data["pre_code"]["approval_id"]
        _approve(platform, auth, issue, approval_id)

        applied = service.guided_pre_code_apply(stage_id=stage_id, actor=actor, actor_role="owner", session_principal=actor, effective_roles=["owner"])
        assert applied.ok, applied.to_dict()
        execution_id = applied.data["pre_code"]["execution_id"]
        assert (workspace / rel).read_text(encoding="utf-8") == content

        frozen = service.guided_pre_code_freeze(
            stage_id=stage_id, review_id=record["review_id"], execution_id=execution_id,
            actor=actor, actor_role="owner", session_principal=actor, effective_roles=["owner"], workspace_scopes=[],
        )
        assert frozen.ok, frozen.to_dict()
        stage = next(row for row in frozen.data["pre_code"]["stages"] if row["stage_id"] == stage_id)
        assert stage["status"] == "FROZEN"
        assert stage["approved_sha256"] == hashlib.sha256((workspace / rel).read_bytes()).hexdigest()

    final = service.guided_pre_code_status(effective_roles=["owner"], workspace_scopes=[])
    assert final.ok, final.to_dict()
    projection = final.data["pre_code"]
    assert projection["status"] == "PRE_CODE_READY"
    assert projection["current_stage_id"] is None
    assert projection["readiness"]["status"] == "PASS"
    assert projection["readiness"]["pre_code_ready"] is True
    assert projection["readiness"]["mandatory_stages_frozen"] == 7
    assert projection["readiness"]["historical_global_readiness_replaced"] is False
    readiness = service.guided_pre_code_readiness(effective_roles=["owner"], workspace_scopes=[])
    assert readiness.ok, readiness.to_dict()

    trace_path = platform / "outputs/pre_code_wizard/gsdlc_05_e/workspace/transition_trace.jsonl"
    assert trace_path.is_file()
    trace_events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [row["stage_id"] for row in trace_events] == [x[0] for x in STAGES]
    assert all(row["event"] == "STAGE_FROZEN" for row in trace_events)



def test_missing_miasi_context_fails_readiness_closed(env):
    platform, workspace, auth, issue, service = env
    (platform / "outputs/workspaces/workspace/miasi_applicability_context.json").unlink()
    status = service.guided_pre_code_status(effective_roles=["owner"], workspace_scopes=[])
    assert status.ok, status.to_dict()
    projection = status.data["pre_code"]
    assert projection["miasi"]["gate_status"] == "BLOCK"
    assert projection["readiness"]["status"] == "BLOCK"
    assert any(row.get("stage_id") == "miasi-applicability" for row in projection["readiness"]["blockers"])


def test_pre_code_api_route_and_registry_contracts_are_explicit():
    expected = {
        ("GET", "/api/v1/guided-sdlc/pre-code"): "guided_sdlc.pre_code.status",
        ("POST", "/api/v1/guided-sdlc/pre-code/stages/product-vision/draft"): "guided_sdlc.pre_code.draft",
        ("POST", "/api/v1/guided-sdlc/pre-code/stages/product-vision/review"): "guided_sdlc.pre_code.review",
        ("POST", "/api/v1/guided-sdlc/pre-code/stages/product-vision/approval-request"): "guided_sdlc.pre_code.approval_request",
        ("POST", "/api/v1/guided-sdlc/pre-code/stages/product-vision/apply"): "guided_sdlc.pre_code.apply",
        ("POST", "/api/v1/guided-sdlc/pre-code/stages/product-vision/freeze"): "guided_sdlc.pre_code.freeze",
        ("GET", "/api/v1/guided-sdlc/pre-code/readiness"): "guided_sdlc.pre_code.readiness",
    }
    for (method, path), operation in expected.items():
        policy = resolve_route_policy(method, path)
        assert policy is not None and policy.operation == operation

    registry = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    rows = [x for x in registry["routes"] if "gsdlc-05-e" in x.get("tags", [])]
    assert len(rows) == 7
    assert all(x["auth_required"] and x["application_service_required"] and x["local_only"] for x in rows)
    assert all(not x["external_api_allowed"] and not x["remote_execution_allowed"] for x in rows)


def test_ui_pre_code_contract_is_project_scoped_and_has_no_authority_fallback():
    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    view = (ROOT / "ui/web/src/pages/PreCodeWizardView.ts").read_text(encoding="utf-8")
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    assert "{ path: '/pre-code', routeId: 'ui.pre-code-wizard'" in main
    assert "scope: 'project'" in main
    assert "renderPreCodeWizardView(() => readStoredToken(), session)" in main
    assert "API local no disponible. El wizard falla cerrado" in view
    assert "StepActionAdvisor" in view and "AGENT" not in view  # cards come from server projection, not UI recomputation
    assert "preCodeDraft" in client and "preCodeReview" in client and "preCodeFreeze" in client
    assert "armApprovalCenterArtifactReviewHandoff" in view
    assert "handoff=artifact-review&approval_id=" in view
    assert "Plan hash" in view and "Diff SHA-256" in view and "pre-code-plan__diff" in view
    assert "Intentar abrir" in view and "no se ejecutó ninguna mutación" in view
    assert "MIASI:" in view and "miasi_gate" not in view
    assert "ensureLiveHumanSession" in view and "client().authSession()" in view
    assert view.count("if(!await ensureLiveHumanSession(feedback)) return") >= 5
    assert "la sesión humana local ya no es válida" in view
    assert "la API local responde, pero la sesión humana" in view
    assert "no repitas DRAFT, approval ni apply ya completados" in view
    assert "decideApproval" not in view
    assert ".innerHTML" not in view


def test_05_d_owner_adjudication_and_05_e_rebound_are_materialized():
    decision = (ROOT / "DEVPL_GSDLC_05_D_FINAL_OWNER_ADJUDICATION_v1_0_0.md").read_text(encoding="utf-8")
    rebound = (ROOT / "05_PROMPT_DEVPL_GSDLC_05_E_v1_0_1_REBOUND.md").read_text(encoding="utf-8")
    assert "CLOSED/PASS" in decision
    assert "repo_DevPilot_Local_373_DEVPL_GSDLC_05_D_STEP_ACTION_ADVISOR_WINDOWS_VALIDATED_CANDIDATE.zip" in rebound
    assert "a5b01a6ffb7f7808ccbaae54847bf2117b95b9f8" in rebound
    assert "56166db2626faf505fe4ebc93a9119abcffd6fbc0d21f5a5be364472d14c60c7" in rebound

def test_pre_code_http_rbac_uses_server_active_workspace_context(env):
    platform, workspace, auth, _, _ = env
    active_workspace_id = workspace.name
    auth.store.update_identity_authority(
        "local-owner",
        roles=("owner",),
        workspace_scopes=(active_workspace_id,),
        changed_at=utc_now_iso(),
    )
    client = TestClient(create_app(platform, api_token="gsdlc05e-local-token", auth_service=auth))
    login = client.post(
        "/api/v1/auth/login",
        json={"username":"owner05e.local","password":PASSWORD},
        headers={"origin":"http://127.0.0.1:5173"},
    )
    assert login.status_code == 200, login.text
    projected = client.get("/api/v1/guided-sdlc/pre-code")
    # The synthetic platform fixture intentionally omits unrelated API-policy files;
    # the regression target is that RBAC resolves the active server workspace rather
    # than the historical default workspace. A downstream 5xx from omitted fixture
    # material is acceptable here, but a workspace-scope 403 is not.
    assert projected.status_code != 403, projected.text
    assert "RBAC_WORKSPACE_SCOPE_DENY" not in projected.text
    mismatch = client.get("/api/v1/guided-sdlc/pre-code?workspace_id=other-workspace")
    assert mismatch.status_code == 403, mismatch.text
    assert "RBAC_WORKSPACE_SCOPE_DENY" in mismatch.text


def test_workspace_document_routes_use_single_authenticated_workspace_scope(env):
    platform, workspace, auth, _, _ = env
    auth.store.update_identity_authority(
        "local-owner",
        roles=("owner",),
        workspace_scopes=(workspace.name,),
        changed_at=utc_now_iso(),
    )
    client = TestClient(create_app(platform, api_token="gsdlc05e-local-token", auth_service=auth))
    login = client.post(
        "/api/v1/auth/login",
        json={"username":"owner05e.local","password":PASSWORD},
        headers={"origin":"http://127.0.0.1:5173"},
    )
    assert login.status_code == 200, login.text

    # Workspace routes that predate explicit active-server-context metadata must not
    # silently fall back to historical devpilot-local when the authenticated actor
    # has one unambiguous server-authoritative workspace scope.
    for path in (
        "/api/v1/workspace/documents?limit=100&offset=0",
        "/api/v1/workspace/artifact-imports/recent?limit=10",
    ):
        response = client.get(path)
        assert response.status_code != 403, response.text
        assert "RBAC_WORKSPACE_SCOPE_DENY" not in response.text

    explicit_mismatch = client.get(
        "/api/v1/workspace/documents?limit=100&offset=0&workspace_id=other-workspace"
    )
    assert explicit_mismatch.status_code == 403, explicit_mismatch.text
    assert "RBAC_WORKSPACE_SCOPE_DENY" in explicit_mismatch.text


def test_pre_code_import_action_stays_in_wizard_and_approval_403_is_explicit():
    view = (ROOT / "ui/web/src/pages/PreCodeWizardView.ts").read_text(encoding="utf-8")
    advisor = (ROOT / "ui/web/src/components/StepActionAdvisor.ts").read_text(encoding="utf-8")
    approvals = (ROOT / "ui/web/src/pages/ApprovalCenterView.ts").read_text(encoding="utf-8")
    assert "activateWizardAction" in view
    assert "action.kind==='UPLOAD_IMPORT'" in view
    assert "file.click()" in view
    assert "La selección permanece dentro del wizard" in view
    assert "options.onAction?.(action) === true" in advisor
    assert "DENY/BLOCK server-side confirmado (HTTP 403)" in approvals

def test_block03_project_status_recovers_external_server_context_via_runtime_guided_registry(tmp_path, monkeypatch: pytest.MonkeyPatch):
    import os
    from devpilot_core.application.guided_sdlc_service import GuidedSDLCApplicationService
    from devpilot_core.guided_sdlc.models import WorkspaceEngineeringState, EngineeringLifecycleStatus, MIPSoftwarePhase

    platform = tmp_path / "platform-full"
    shutil.copytree(
        ROOT,
        platform,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "node_modules", "outputs", ".pytest_cache", "__pycache__", "*.pyc", "auth.db*", "devpilot.db*"
        ),
    )
    workspace = tmp_path / "gsdlc05e-browser-project"
    workspace.mkdir(parents=True)
    assert not (workspace / ".devpilot/project.yaml").exists(), "BLOCK-03 fixture must not inject project metadata"

    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(workspace))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)

    runtime_registry = platform / "outputs/runtime/gsdlc05e_guided_sdlc_workspace_registry.json"
    runtime_registry.parent.mkdir(parents=True, exist_ok=True)
    runtime_registry.write_text(json.dumps({
        "schema_version": "1.0",
        "created_by": "DEVPL-GSDLC-05-E-BLOCK-03-TEST",
        "active_workspace_id": workspace.name,
        "defaults": {"deny_unregistered_workspaces": True},
        "workspaces": [{
            "workspace_id": workspace.name,
            "project_id": workspace.name,
            "path": str(workspace.resolve()),
            "path_mode": "absolute-local",
            "status": "active",
        }],
    }, indent=2), encoding="utf-8")
    monkeypatch.setenv("DEVPILOT_GUIDED_SDLC_WORKSPACE_REGISTRY_PATH", str(runtime_registry))

    fingerprint = hashlib.sha256(os.path.normcase(str(workspace.resolve())).encode("utf-8")).hexdigest()
    state = WorkspaceEngineeringState(
        workspace_id=workspace.name,
        project_id=workspace.name,
        workspace_root_fingerprint=fingerprint,
        lifecycle_status=EngineeringLifecycleStatus.IN_PROGRESS,
        phase=MIPSoftwarePhase.REQUIREMENTS,
        current_step="requirements",
        sequence=0,
        created_at_utc="2026-08-25T00:00:00Z",
        updated_at_utc="2026-08-25T00:00:00Z",
        git={"head":None,"branch":None,"dirty":None,"fingerprint":None},
        artifacts=(), planning=(), quality=(), gates=(), blockers=(),
        revalidation={"status":"NOT_REQUIRED","reason_codes":[]},
        source_fingerprints=(), next_action_ref=None,
    )
    state_dir = platform / "outputs/workspaces" / workspace.name
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "engineering_state.json").write_text(json.dumps(state.to_payload(), indent=2), encoding="utf-8")
    (state_dir / "miasi_applicability_context.json").write_text(json.dumps({
        "schema_id":"SCHEMA-DEVPL-MIASI-APPLICABILITY-CONTEXT-V1",
        "schema_version":"1.0",
        "workspace_id":workspace.name,
        "project":{"declared_ai_usage":False,"capabilities":[],"risk_level":"low","evidence_refs":["block03:explicit-non-ai"]},
        "features":[],
        "risk_review_status":"NOT_REQUIRED",
        "evidence_refs":["block03:project-status-recovery"],
    }, indent=2), encoding="utf-8")

    direct = GuidedSDLCApplicationService(platform).project_status_primary(
        workspace_id=None,
        observed_at_utc="2026-08-25T00:00:01Z",
    )
    assert direct.ok is True, direct.to_dict()
    assert direct.data["workspace_id"] == workspace.name
    assert direct.data["project_status"]["workspace_id"] == workspace.name
    assert direct.data["project_status"]["project_id"] == workspace.name
    assert direct.data["ui_state"] not in {"EMPTY", "UNKNOWN"}
    assert direct.data["read_only"] is True and direct.data["actor_neutral"] is True
    assert direct.data["network_used"] is False and direct.data["external_api_used"] is False
    assert direct.data["mutations_performed"] is False and direct.data["source_mutations_performed"] is False

    auth = AuthApplicationService(platform)
    issue = auth.bootstrap_owner(username="owner05e.local", display_name="GSDLC 05-E Owner", password=PASSWORD)
    auth.store.update_identity_authority(
        issue.context.principal.actor_id,
        roles=("owner",),
        workspace_scopes=(workspace.name,),
        changed_at=utc_now_iso(),
    )
    client = TestClient(create_app(platform, api_token="gsdlc05e-local-token", auth_service=auth))
    common = {"X-DevPilot-Token":"gsdlc05e-local-token", "origin":"http://127.0.0.1:5173"}
    login = client.post("/api/v1/auth/login", json={"username":"owner05e.local","password":PASSWORD}, headers=common)
    assert login.status_code == 200, login.text
    response = client.get("/api/v1/guided-sdlc/status", headers=common)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True
    data = body["data"]
    assert data["workspace_id"] == workspace.name
    assert data["project_status"]["workspace_id"] == workspace.name
    assert data["project_status"]["project_id"] == workspace.name
    assert data["ui_state"] not in {"EMPTY", "UNKNOWN"}

