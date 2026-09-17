from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_ux_p0_c_rebound_authority_and_full_policy():
    sprint = read("SPRINT_DEVPL_UX_P0_C_v1_0_0_APPROVED_REBOUND_REPO433.md")
    prompt = read("03_PROMPT_DEVPL_UX_P0_C_v1_0_1_APPROVED_REBOUND_REPO433.md")
    backlog = read("DEVPL_UX_P0_PRE_PILOT_PRODUCTIZATION_BACKLOG_v1_0_1_APPROVED_REBOUND_REPO433.md")
    assert 'status: "approved"' in sprint
    assert 'approval: "approved_by_owner"' in sprint
    assert 'repo_DevPilot_Local_433_DEVPL_UX_P0_B_PROJECT_CONTEXT_AUTH_SCOPE_CORRECTIVE_WINDOWS_VALIDATED_CANDIDATE.zip' in sprint
    assert 'dc63672f2d617968998f3c68374a03581b348578' in sprint
    assert 'successor_expected: "repo434"' in sprint
    assert 'full_regression: "PROHIBITED"' in sprint
    assert 'repo_DevPilot_Local_433_DEVPL_UX_P0_B_PROJECT_CONTEXT_AUTH_SCOPE_CORRECTIVE_WINDOWS_VALIDATED_CANDIDATE.zip' in prompt
    assert 'repo_DevPilot_Local_434_DEVPL_UX_P0_C_GREENFIELD_CRITICAL_PATH_WINDOWS_VALIDATED_CANDIDATE.zip' in prompt
    assert 'A-D selective/TestImpact only' in backlog


def test_ux_p0_b_final_closure_is_preserved():
    adjudication = read("docs/audits/DEVPL_UX_P0_B_FINAL_CLOSURE_ADJUDICATION_v1_0_0.md")
    assert 'CLOSED/PASS/WINDOWS-VALIDATED' in adjudication
    assert 'f4415775bd3bf5a01b6368197d0754374de93b659fa5f6bbff8b7a2b8ead4246' in adjudication
    assert 'Full Regression ejecutada en B: `0`' in adjudication


def test_critical_path_surfaces_are_productized_without_route_or_authority_shortcuts():
    main = read("ui/web/src/main.ts")
    home = read("ui/web/src/components/ProjectHomeEntryPanel.ts")
    entry = read("ui/web/src/pages/ProjectEntryDryRunView.ts")
    status = read("ui/web/src/pages/ProjectStatusView.ts")
    pre = read("ui/web/src/pages/PreCodeWizardView.ts")
    docs = read("ui/web/src/pages/WorkspaceDocumentsView.ts")
    planning = read("ui/web/src/pages/RoadmapWorkbenchView.ts")
    guide = read("ui/web/src/components/CriticalPathGuidance.ts")
    for route in ["/project/status", "/pre-code", "/planning/roadmap", "/project/entry", "/workspace/documents"]:
        assert route in main
    assert "Retomar proyecto activo" in home
    assert "recover_project_context=server-active" in home
    assert "Revisa primero; muta después" in entry
    assert "Tu recorrido hasta Planning" in status
    assert "draft → validar/diff → approval → apply → freeze" in pre
    assert "Documentos del proyecto" in docs
    assert "Roadmap" in planning and "Backlog" in planning and "Sprint" in planning
    assert "renderCriticalPathGuidance" in guide
    assert "reset --hard" not in guide
    assert "git clean" not in guide


def test_guided_copy_keeps_technical_detail_available_progressively():
    status = read("ui/web/src/pages/ProjectStatusView.ts")
    docs = read("ui/web/src/pages/WorkspaceDocumentsView.ts")
    planning = read("ui/web/src/pages/RoadmapWorkbenchView.ts")
    assert "Ver razón técnica" in status
    assert "Ver contrato técnico del Artifact Workbench" in docs
    assert "Editar contenido técnico JSON" in planning


def test_current_project_state_points_to_ux_p0_c_successor():
    state = json.loads(read(".devpilot/project_state.json"))
    assert state["ux_p0_b_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
    assert state["ux_p0_current_micro_sprint"] in {"DEVPL-UX-P0-C", "DEVPL-UX-P0-D", "DEVPL-UX-P0-E"}
    if state["ux_p0_current_micro_sprint"] == "DEVPL-UX-P0-E":
        assert state["ux_p0_c_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
        assert state["ux_p0_d_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
        assert state["ux_p0_next_micro_sprint"] == "DEVPL-GSDLC-13"
        assert state["ux_p0_source_repo"].startswith("repo_DevPilot_Local_435_")
        assert state["ux_p0_source_commit"] == "f1e4c5b8dc1882f7dc724ba87755cdd894f274c8"
    elif state["ux_p0_current_micro_sprint"] == "DEVPL-UX-P0-D":
        assert state["ux_p0_c_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
        assert state["ux_p0_next_micro_sprint"] == "DEVPL-UX-P0-E"
        assert state["ux_p0_source_repo"] == "repo_DevPilot_Local_434_DEVPL_UX_P0_C_GREENFIELD_CRITICAL_PATH_WINDOWS_VALIDATED_CANDIDATE.zip"
        assert state["ux_p0_source_commit"] == "75dbead73c6c6aaf1f792e02f3659ee2b6c0b927"
        assert state["ux_p0_source_sha256"] == "e1117ba5e9c3bace2de482940d6b447b0150acb2e26ba1647f9677939f5faf39"
        assert state["ux_p0_successor_repo"] == "repo_DevPilot_Local_435_DEVPL_UX_P0_D_CROSS_SURFACE_OPERATIONAL_PATTERNS_WINDOWS_VALIDATED_CANDIDATE.zip"
    else:
        assert state["ux_p0_next_micro_sprint"] == "DEVPL-UX-P0-D"
        assert state["ux_p0_source_repo"] == "repo_DevPilot_Local_433_DEVPL_UX_P0_B_PROJECT_CONTEXT_AUTH_SCOPE_CORRECTIVE_WINDOWS_VALIDATED_CANDIDATE.zip"
        assert state["ux_p0_source_commit"] == "dc63672f2d617968998f3c68374a03581b348578"
        assert state["ux_p0_source_sha256"] == "f4415775bd3bf5a01b6368197d0754374de93b659fa5f6bbff8b7a2b8ead4246"
        assert state["ux_p0_successor_repo"] == "repo_DevPilot_Local_434_DEVPL_UX_P0_C_GREENFIELD_CRITICAL_PATH_WINDOWS_VALIDATED_CANDIDATE.zip"
    assert state["ux_p0_c_full_regression_runs"] == 0
