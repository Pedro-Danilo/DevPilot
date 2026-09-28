from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from devpilot_core.application.guided_sdlc_service import GuidedSDLCApplicationService
from devpilot_core.application.planning_closure_service import PlanningClosureApplicationService
from devpilot_core.application.services import ApplicationService
from devpilot_core.guided_sdlc.models import EngineeringLifecycleStatus, MIPSoftwarePhase, WorkspaceEngineeringState
from devpilot_core.reconciliation.service import AdvancedWorkspaceReconciliationService
from devpilot_core.workspace.runtime_project_context import activate_project_runtime_context, bind_persisted_project_runtime

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ID = "inventory-sales-local-greenfield"
STAGES = ("product-vision", "scope", "requirements", "architecture", "security", "test-strategy", "traceability")


def _platform(tmp_path: Path) -> Path:
    platform = tmp_path / "platform"
    shutil.copytree(
        ROOT,
        platform,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "node_modules", "outputs", ".pytest_cache", "__pycache__", "*.pyc", "*.db", "*.db-*", "dist"
        ),
    )
    return platform


def _workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "workspaces" / WORKSPACE_ID
    (ws / ".devpilot").mkdir(parents=True)
    (ws / "docs/standards").mkdir(parents=True)
    (ws / ".devpilot/project.yaml").write_text(
        "project_id: inventory-sales-local-greenfield\n"
        "project_name: Inventory Sales Local Greenfield\n"
        "technology_decision_status: deferred-to-architecture\n",
        encoding="utf-8",
    )
    (ws / ".devpilot/workspace-registration.json").write_text(
        json.dumps({"workspace_id": WORKSPACE_ID, "project_id": WORKSPACE_ID, "root_path": str(ws.resolve())}, indent=2) + "\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=ws, check=True)
    subprocess.run(["git", "config", "user.name", "Fixture"], cwd=ws, check=True)
    subprocess.run(["git", "add", "."], cwd=ws, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=ws, check=True)
    return ws


def _activate(platform: Path, ws: Path, monkeypatch) -> None:
    activate_project_runtime_context(platform, ws, allowed_roots=(ws,))
    for name in [
        "DEVPILOT_ALLOWED_WORKSPACE_ROOTS",
        "DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT",
        "DEVPILOT_UI_WORKSPACE_REGISTRY_PATH",
        "DEVPILOT_GUIDED_SDLC_WORKSPACE_REGISTRY_PATH",
    ]:
        monkeypatch.delenv(name, raising=False)
    binding = bind_persisted_project_runtime(platform)
    assert binding.applied


def _write_seven_frozen_state(platform: Path, *, status: str = "BLOCKED") -> Path:
    path = platform / "outputs/pre_code_wizard/gsdlc_05_e" / WORKSPACE_ID / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    stages = {
        stage: {"stage_id": stage, "status": "FROZEN", "approved_sha256": hashlib.sha256(stage.encode()).hexdigest()}
        for stage in STAGES
    }
    path.write_text(
        json.dumps({"schema_id": "devpilot.gsdlc05e.pre_code_state.v1", "schema_version": "1.0", "workspace_id": WORKSPACE_ID, "profile_id": "guided-pre-code-manual-v1", "status": status, "stages": stages}, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def test_c03_project_status_composes_pre_code_without_advancing_global_mipsoftware(tmp_path: Path, monkeypatch) -> None:
    platform = _platform(tmp_path)
    ws = _workspace(tmp_path)
    _activate(platform, ws, monkeypatch)
    _write_seven_frozen_state(platform)

    result = GuidedSDLCApplicationService(platform).project_status_primary(workspace_id=None, observed_at_utc="2026-09-28T11:00:00Z")
    assert result.ok is True, result.to_dict()
    status = result.data["project_status"]
    pre = status["pre_code_profile"]

    assert pre["mandatory_stages_frozen"] == 7 and pre["percent"] == 100.0
    assert pre["all_stages_frozen"] is True and pre["pre_code_ready"] is False
    assert pre["miasi"]["status"] == "NOT_EVALUATED" and pre["miasi"]["gate_status"] == "DEFERRED"
    assert status["progress"]["active_profile"] == "PRE_CODE"
    assert status["progress"]["active_profile_percent"] == 100.0
    assert status["current_step"] == "pre-code-readiness"
    assert status["current_step_global_mipsoftware"] == "idea-intake"
    assert status["mipsoftware"]["status"] == "NOT_STARTED"
    assert status["mipsoftware"]["authority_scope"] == "global-lifecycle"
    assert status["mipsoftware"]["standard_applies"] is True
    assert status["mipsoftware"]["standard_scope"] == "cross-lifecycle"
    assert status["mipsoftware"]["pre_code_profile_conformance"] == "APPLIED"
    assert status["mipsoftware"]["pre_code_profile_is_separate_authority"] is False
    assert status["mipsoftware"]["pre_code_profile_is_separate_execution_profile"] is True
    assert status["mipsoftware"]["formal_registry_phase"] == "NOT_STARTED"
    assert status["mipsoftware"]["formal_registry_synchronized"] is False
    assert status["mipsoftware"]["formal_registry_reason_code"] == "BOUNDED_PRE_CODE_PROFILE_NOT_MAPPED_TO_GLOBAL_MIP_PHASE"
    assert result.data["next_action"]["reason_code"] == "MIASI_APPLICABILITY_REQUIRED"

    actions = GuidedSDLCApplicationService(platform).step_actions_primary(workspace_id=None, observed_at_utc="2026-09-28T11:00:01Z", effective_roles=["owner"], workspace_scopes=[WORKSPACE_ID])
    assert actions.ok is True, actions.to_dict()
    advisor = actions.data["advisor"]
    assert advisor["status"] == "PASS"
    assert advisor["recommended_action_id"] == "typed.miasi-applicability"
    assert advisor["actions"][0]["label"] == "Resolver aplicabilidad MIASI"


def test_c03_owner_non_ai_decision_is_runtime_only_and_can_mark_pre_code_ready(tmp_path: Path, monkeypatch) -> None:
    platform = _platform(tmp_path)
    ws = _workspace(tmp_path)
    _activate(platform, ws, monkeypatch)
    state_path = _write_seven_frozen_state(platform)
    before_source = subprocess.check_output(["git", "-C", str(ws), "status", "--porcelain=v1", "-z"])

    app = ApplicationService(platform)
    app.pre_code_wizard._readiness_payload = lambda state, workspace_id, workspace_root, miasi=None: {
        "schema_id": "test.readiness",
        "status": "PASS" if str((miasi or {}).get("gate_status")) == "PASS" else "BLOCK",
        "pre_code_ready": str((miasi or {}).get("gate_status")) == "PASS",
        "blockers": [],
        "miasi": miasi or {},
    }
    result = app.guided_pre_code_miasi_applicability(
        actor="local-owner",
        actor_role="owner",
        session_principal="local-owner",
        effective_roles=["owner"],
        workspace_scopes=[WORKSPACE_ID],
        declared_ai_usage=False,
        capabilities=[],
        risk_level="low",
        evidence_refs=["owner-confirmed-non-ai"],
    )
    assert result.ok is True, result.to_dict()
    assert result.data["pre_code"]["miasi"]["status"] == "NOT_APPLICABLE"
    assert result.data["pre_code"]["miasi"]["gate_status"] == "PASS"
    assert result.data["pre_code"]["status"] == "PRE_CODE_READY"
    assert result.data["miasi_decision"]["runtime_only"] is True
    assert result.data["miasi_decision"]["workspace_source_writes"] == 0

    context = platform / "outputs/workspaces" / WORKSPACE_ID / "miasi_applicability_context.json"
    assert context.is_file()
    payload = json.loads(context.read_text(encoding="utf-8"))
    assert payload["project"]["declared_ai_usage"] is False and payload["project"]["capabilities"] == []
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["status"] == "PRE_CODE_READY"
    assert subprocess.check_output(["git", "-C", str(ws), "status", "--porcelain=v1", "-z"]) == before_source == b""


def test_c03_planning_closure_reads_platform_pre_code_runtime(tmp_path: Path) -> None:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspace"
    platform.mkdir(); workspace.mkdir()
    path = platform / "outputs/pre_code_wizard/gsdlc_05_e" / WORKSPACE_ID / "state.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"status": "PRE_CODE_READY"}) + "\n", encoding="utf-8")
    assert PlanningClosureApplicationService._pre_code_ready(platform, workspace, WORKSPACE_ID) is True


def test_c03_route_is_registered_consistently_and_ui_count_matches_registry() -> None:
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    ui = json.loads((ROOT / ".devpilot/interfaces/ui_capability_registry.json").read_text(encoding="utf-8"))
    route_id = "api.guided-sdlc.pre-code.miasi-applicability"
    api_rows = {row["route_id"]: row for row in api["routes"]}
    rbac_rows = {row["route_id"]: row for row in rbac["route_policies"]}
    assert route_id in api_rows and route_id in rbac_rows
    assert api_rows[route_id]["source_mutation_allowed"] is False
    assert rbac_rows[route_id]["allowed_roles"] == ["owner"]
    assert rbac_rows[route_id]["human_session_required"] is True
    assert rbac_rows[route_id]["workspace_scope_required"] is True
    assert int(ui["summary"]["api_routes_total"]) == len(api["routes"]) == len(rbac["route_policies"])
    assert int(api["summary"]["routes_total"]) == len(api["routes"])
    assert int(rbac["summary"]["route_policies_total"]) == len(rbac["route_policies"])



def test_c03_planning_closure_blocks_roadmap_until_pre_code_ready(tmp_path: Path) -> None:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspace"
    platform.mkdir(); workspace.mkdir()
    projected = PlanningClosureApplicationService._project
    # Call the pure projection method through a minimal uninitialized instance;
    # no context resolver or source mutation is involved.
    service = object.__new__(PlanningClosureApplicationService)
    service.root = platform
    payload = service._project(workspace, WORKSPACE_ID, None, None, None, ["owner"])
    assert payload["pre_code_ready"] is False
    assert payload["journey_state"] == "PRE_CODE_BLOCKED"
    assert payload["next_action"]["navigation_target"] == "pre-code"
    assert payload["next_action"]["reason_code"] == "PRE_CODE_READY_REQUIRED"
    assert payload["next_action"]["label"] == "Completar Pre-code readiness"

def test_c03_ui_exposes_boundary_decision_without_false_current_stage_error() -> None:
    pre = (ROOT / "ui/web/src/pages/PreCodeWizardView.ts").read_text(encoding="utf-8")
    status = (ROOT / "ui/web/src/pages/ProjectStatusView.ts").read_text(encoding="utf-8")
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    for token in [
        "Paso 13 · MIASI/MIPSoftware + Pre-code readiness",
        "Evaluar MIASI y recalcular readiness",
        "Boundary C-03 · MIASI/readiness",
        "MIASI debe quedar evaluado",
        "runtime de DevPilot",
    ]:
        assert token in pre
    assert "preCodeMiasiApplicability" in client
    assert "Pre-code" in status
    assert "MIPSoftware · estándar" in status
    assert "Registry MIPSoftware formal" in status
    assert "APLICA · estándar transversal del ciclo" in status


def test_c03_ui_exposes_owner_miasi_gate_and_distinguishes_governed_pre_code_source() -> None:
    pre_code = (ROOT / "ui/web/src/pages/PreCodeWizardView.ts").read_text(encoding="utf-8")
    project_status = (ROOT / "ui/web/src/pages/ProjectStatusView.ts").read_text(encoding="utf-8")
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    assert "Paso 13 · MIASI/MIPSoftware + Pre-code readiness" in pre_code
    assert "Evaluar MIASI y recalcular readiness" in pre_code
    assert "preCodeMiasiApplicability" in pre_code and "preCodeMiasiApplicability" in client
    assert "/guided-sdlc/pre-code/miasi/applicability" in client
    assert "Cambios Pre-code gobernados" in project_status
    assert "governed-pre-code-source" in project_status
    assert "MIPSoftware · estándar" in project_status
    assert "perfil bounded aún no mapeado al phase-state global" in project_status


def test_c03_reconciliation_links_frozen_pre_code_and_adr_paths_without_hiding_baseline_gap(tmp_path: Path, monkeypatch) -> None:
    platform = _platform(tmp_path)
    ws = _workspace(tmp_path)
    _activate(platform, ws, monkeypatch)

    product = ws / "docs/00_product/product_vision.md"
    adr = ws / "docs/02_architecture/adrs/ADR-001-test.md"
    product.parent.mkdir(parents=True, exist_ok=True)
    adr.parent.mkdir(parents=True, exist_ok=True)
    product.write_text("# Product Vision\n\nGoverned change.\n", encoding="utf-8")
    adr.write_text("# ADR-001\n\nGoverned companion.\n", encoding="utf-8")

    path = platform / "outputs/pre_code_wizard/gsdlc_05_e" / WORKSPACE_ID / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    stages = {stage: {"stage_id": stage, "status": "MISSING"} for stage in STAGES}
    stages["product-vision"] = {
        "stage_id": "product-vision",
        "status": "FROZEN",
        "artifact": {"relative_path": "docs/00_product/product_vision.md"},
    }
    state = {
        "schema_id": "devpilot.gsdlc05e.pre_code_state.v1",
        "workspace_id": WORKSPACE_ID,
        "status": "IN_PROGRESS",
        "stages": stages,
        "architecture_adr_bundle": {
            "status": "APPLIED",
            "adrs": [{"relative_path": "docs/02_architecture/adrs/ADR-001-test.md"}],
        },
    }
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    report = AdvancedWorkspaceReconciliationService(platform).inspect(
        actor="local-owner",
        session_created_at="2026-09-28T11:30:00Z",
        rotation_counter=0,
    )
    assert report["classification"] == "READ_ONLY_BLOCK"
    assert report["reason_codes"] == ["RECONCILIATION_BASELINE_MISSING"]
    snapshot = report["snapshot"]
    assert snapshot["baseline_present"] is False
    assert snapshot["change_counts"]["MODIFY"] + snapshot["change_counts"]["UNTRACKED"] == 2
    assert snapshot["authority_linked_change_count"] == 2
    assert all(row["linked_to_engineering_authority"] is True for row in snapshot["changes"])


def test_c03_mipsoftware_copy_distinguishes_standard_from_formal_registry_state() -> None:
    pre = (ROOT / "ui/web/src/pages/PreCodeWizardView.ts").read_text(encoding="utf-8")
    status = (ROOT / "ui/web/src/pages/ProjectStatusView.ts").read_text(encoding="utf-8")
    assert "MIPSoftware sigue siendo el estándar transversal" in pre
    assert "MIPSoftware · estándar" in status
    assert "Registry MIPSoftware formal" in status
    assert "perfil bounded aún no mapeado al phase-state global" in status
    assert "autoridad separada del perfil Pre-code" not in status
