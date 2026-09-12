from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_11_d_restart_recovery_keeps_project_status_as_primary_and_registered_workspace_as_read_only_fallback() -> None:
    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    segment = main.split("async function recoverSessionBoundProjectRouteContext", 1)[1].split("function renderRouteHeader", 1)[0]
    assert "scopes.length !== 1" in segment
    assert "client.projectStatusSessionRecovery(expectedWorkspaceId)" in segment
    assert "restoreProjectJourneyContextFromProjectStatusRecovery(response, expectedWorkspaceId)" in segment
    assert "client.settingsWorkspace()" in segment
    assert "restoreProjectJourneyContextFromRegisteredWorkspaceRecovery(workspace, expectedWorkspaceId)" in segment
    assert segment.index("projectStatusSessionRecovery") < segment.index("settingsWorkspace")
    assert "projectEntryDryRun" not in segment
    assert "projectEntryExecute" not in segment


def test_11_d_registered_workspace_recovery_is_scope_bound_read_only_and_gsdlc03_shaped() -> None:
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    helper = client.split("export function restoreProjectJourneyContextFromRegisteredWorkspaceRecovery", 1)[1].split("export function beginProjectEntryJourney", 1)[0]
    for required in [
        "response.ok === true",
        "summary.scope === 'active-workspace'",
        "summary.exists === true",
        "summary.write_enabled === false",
        "summary.plan_only === true",
        "summary.secrets_redacted === true",
        "context.configured === true",
        "context.valid === true",
        "context.read_only === true",
        "context.network_used === false",
        "context.external_api_used === false",
        "context.mutations_performed === false",
        "workspaceId === expectedWorkspaceId",
        "projectId === workspaceId",
        "projectId.toLowerCase() !== 'unknown'",
        "String(workspace.project_type ?? '').trim() === 'agent-assisted-sdlc'",
        "workspace.miasi_required === true",
        "standards.includes('MIPSoftware')",
        "standards.includes('MIASI')",
        "phase: 'project'",
        "globalThis.sessionStorage?.setItem(PROJECT_JOURNEY_CONTEXT_KEY",
    ]:
        assert required in helper
    assert "projectEntry" not in helper


def test_11_d_recovery_does_not_relax_existing_project_status_authority_contract() -> None:
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    helper = client.split("export function restoreProjectJourneyContextFromProjectStatusRecovery", 1)[1].split("export function restoreProjectJourneyContextFromRegisteredWorkspaceRecovery", 1)[0]
    assert "projectId.toLowerCase() !== 'unknown'" in helper
    assert "!['EMPTY', 'UNKNOWN'].includes(uiState)" in helper
    assert "data?.read_only === true" in helper
    assert "data?.actor_neutral === true" in helper


def test_11_d_registered_workspace_fallback_backend_projection_matches_open_existing_shape(tmp_path: Path, monkeypatch) -> None:
    from devpilot_core.application.settings_service import SettingsApplicationService

    workspace = tmp_path / "devpilot-local"
    project_file = workspace / ".devpilot" / "project.yaml"
    project_file.parent.mkdir(parents=True)
    project_file.write_text(
        "schema_version: '1.0'\n"
        "project_id: devpilot-local\n"
        'project_name: "DevPilot Local — GSDLC 11-D browser acceptance"\n'
        "project_type: agent-assisted-sdlc\n"
        "miasi_required: true\n"
        "standards:\n"
        "  - MIPSoftware\n"
        "  - MIASI\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(workspace))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)

    result = SettingsApplicationService(ROOT).workspace()
    assert result.ok is True
    assert result.data["summary"]["scope"] == "active-workspace"
    assert result.data["summary"]["exists"] is True
    assert result.data["summary"]["write_enabled"] is False
    assert result.data["summary"]["plan_only"] is True
    assert result.data["summary"]["secrets_redacted"] is True
    assert result.data["workspace"]["project_id"] == "devpilot-local"
    assert result.data["workspace"]["project_type"] == "agent-assisted-sdlc"
    assert result.data["workspace"]["miasi_required"] is True
    assert result.data["workspace"]["standards"] == ["MIPSoftware", "MIASI"]
    context = result.data["workspace_context"]
    assert context["configured"] is True
    assert context["valid"] is True
    assert context["active_workspace_id"] == "devpilot-local"
    assert context["read_only"] is True
    assert context["network_used"] is False
    assert context["external_api_used"] is False
    assert context["mutations_performed"] is False
