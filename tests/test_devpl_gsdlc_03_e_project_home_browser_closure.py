from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def j(path:str)->dict:
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def text(path:str)->str:
    return (ROOT/path).read_text(encoding='utf-8')


def test_03_d_final_authority_is_bound_before_03_e() -> None:
    state=j('.devpilot/project_state.json')
    assert state['gsdlc_03_d_status']=='closed/PASS'
    assert state['gsdlc_03_d_final_commit']=='7eb5f6512da8644ff08651cec0bd464795cfda8e'
    assert state['gsdlc_03_d_successor_sha256']=='a660005465fa8ee566d0b9d1cdaa8bd978457cbbc59ca9ebb83891f8b1f53b4b'
    assert state['gsdlc_03_d_windows_evidence_sha256']=='94190f496f8a3e56fb9191577126e61ea9021bed1a4f20ece718395360e3cda7'
    assert state['gsdlc_03_e_authorized'] is True
    assert (ROOT/'DEVPL_GSDLC_03_D_FINAL_OWNER_ADJUDICATION_v1_0_0.md').is_file()


def test_03_d_contracts_are_frozen_without_rewriting_03_c_or_03_b() -> None:
    api=j('.devpilot/interfaces/api_route_contract_registry_gsdlc03d_at_close.json')
    rbac=j('.devpilot/identity/server_rbac_policy_catalog_gsdlc03d_at_close.json')
    ui=j('.devpilot/interfaces/ui_route_contract_registry_gsdlc03d_at_close.json')
    assert len(api['routes'])==104
    assert len(rbac['route_policies'])==104
    assert len(ui['routes'])==11
    assert len(j('.devpilot/interfaces/ui_route_contract_registry_gsdlc03c_at_close.json')['routes'])==11
    assert len(j('.devpilot/interfaces/ui_route_contract_registry_gsdlc03b_at_close.json')['routes'])==10
    assert len(j('.devpilot/interfaces/ui_route_contract_registry_uoc011_at_close.json')['routes'])==9


def test_project_home_is_primary_without_replacing_historical_dashboard_route() -> None:
    main=text('ui/web/src/main.ts')
    dashboard=text('ui/web/src/pages/Dashboard.ts')
    home=text('ui/web/src/components/ProjectHomeEntryPanel.ts')
    registry=j('.devpilot/interfaces/ui_route_contract_registry.json')
    routes={r['route_id']:r for r in registry['routes']}
    assert routes['ui.dashboard']['path']=='/'
    assert len(registry['routes'])==11
    assert 'ui/web/src/components/ProjectHomeEntryPanel.ts' in routes['ui.dashboard']['source_files']
    assert "renderDashboard(page, session," in main
    assert 'renderProjectHomeEntryPanel(session)' in dashboard
    assert all(label in home for label in ('Crear nuevo proyecto','Abrir proyecto existente','Importar repositorio Git'))
    assert all(mode in home for mode in ('CREATE_NEW','OPEN_EXISTING','IMPORT_GIT'))
    assert 'journey normal ocurre íntegramente en el navegador' in home


def test_project_entry_is_browser_complete_and_plan_state_is_invalidated_on_change() -> None:
    main=text('ui/web/src/main.ts')
    entry=text('ui/web/src/pages/ProjectEntryDryRunView.ts')
    assert 'readEntryMode' in main
    assert 'PROJECT_ID_PATTERN' in entry
    assert 'invalidatePlan' in entry
    assert 'parámetros cambiaron' in entry
    assert "roles.includes('owner')" in entry
    assert 'approvalId.input.readOnly=true' in entry
    assert 'Recovery / rollback evidence' in entry
    assert 'Continuar a Estado del proyecto' in entry
    assert "link.href='/project/status'" in entry


def test_acceptance_fault_injection_is_dev_and_server_gated() -> None:
    entry=text('ui/web/src/pages/ProjectEntryDryRunView.ts')
    service=text('src/devpilot_core/application/project_bootstrap_execution_service.py')
    assert 'import.meta.env.DEV' in entry
    assert 'VITE_GSDLC03E_BROWSER_ACCEPTANCE' in entry
    assert 'fault_stage' in entry
    assert 'DEVPILOT_GSDLC03D_FAULT_INJECTION' in service
    assert 'restricted to the explicit GSDLC-03-D evaluation harness' in service


def test_normal_journey_metrics_and_exactly_once_full_policy_are_declared() -> None:
    state=j('.devpilot/project_state.json')
    current=j('docs/audits/DEVPL_GSDLC_03_E_CURRENT.json')
    op=j('docs/audits/DEVPL_GSDLC_03_E_OPERATION_DECLARATION.json')
    assert state['gsdlc_03_e_normal_user_powershell_required']==0
    assert state['gsdlc_03_e_external_operator_project_writes']==0
    assert current['full_regression_executed'] is True
    assert current['full_regression_runs_performed']==1
    assert current['full_regression_result']=='FAIL-ONCE-COMPOSITE-RECOVERY-REQUIRED'
    assert current['second_full_regression_allowed'] is False
    assert op['normal_user_powershell_required']==0
    assert op['external_operator_project_writes']==0
    assert op['full_regression']=='FAIL-ONCE/RECOVERED-BY-COMPOSITE-EVIDENCE'
    assert op['validation_mode']=='composite-full-regression-selective-retest'


def test_browser_closure_static_smoke_and_accessibility_contract() -> None:
    smoke=text('ui/web/scripts/gsdlc03e-project-home-browser-closure-smoke.mjs')
    home=text('ui/web/src/components/ProjectHomeEntryPanel.ts')
    entry=text('ui/web/src/pages/ProjectEntryDryRunView.ts')
    assert 'normal_user_powershell_required:0' in smoke
    assert "setAttribute('aria-labelledby'" in home
    assert "setAttribute('aria-label'" in home
    assert "setAttribute('aria-live','polite')" in entry
    assert 'button[data-busy="true"]' in text('ui/web/src/styles.css')


def test_03e_default_environment_discovery_timeout_is_windows_tolerant_but_bounded() -> None:
    from devpilot_core.workspace.environment_discovery import DEFAULT_TIMEOUT_SECONDS, EnvironmentDiscoveryService

    assert DEFAULT_TIMEOUT_SECONDS == 8.0
    service = EnvironmentDiscoveryService(ROOT)
    assert service.timeout_seconds == 8.0
    assert 0.1 <= service.timeout_seconds <= 15.0

def test_03e_project_entry_timeout_default_is_single_sourced_across_layers() -> None:
    import inspect

    from devpilot_core.application.project_bootstrap_execution_service import ProjectBootstrapExecutionApplicationService
    from devpilot_core.application.project_entry_dry_run_service import ProjectEntryDryRunApplicationService
    from devpilot_core.application.project_entry_planning_service import ProjectEntryPlanningApplicationService
    from devpilot_core.application.services import ApplicationService
    from devpilot_core.interfaces.api.routers.project_entry import ProjectEntryPlanningBody
    from devpilot_core.workspace.environment_discovery import DEFAULT_TIMEOUT_SECONDS
    from devpilot_core.workspace.project_entry_dry_run import ProjectEntryDryRunService

    assert DEFAULT_TIMEOUT_SECONDS == 8.0
    assert ProjectEntryPlanningBody.model_fields["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ProjectEntryPlanningApplicationService.environment_discovery).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ProjectEntryPlanningApplicationService.bootstrap_plan).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ProjectEntryDryRunApplicationService.dry_run).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ProjectEntryDryRunApplicationService.revalidate).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ProjectEntryDryRunService.__init__).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ProjectBootstrapExecutionApplicationService.request_approval_authenticated).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ProjectBootstrapExecutionApplicationService.execute_authenticated).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ApplicationService.project_entry_environment_discovery).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ApplicationService.project_entry_bootstrap_plan).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ApplicationService.project_entry_dry_run).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ApplicationService.project_entry_revalidate).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ApplicationService.project_entry_request_execution_approval_authenticated).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS
    assert inspect.signature(ApplicationService.project_entry_execute_authenticated).parameters["timeout_seconds"].default == DEFAULT_TIMEOUT_SECONDS

def test_03e_project_home_navigation_is_progressively_disclosed_and_context_guarded() -> None:
    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    home = (ROOT / "ui/web/src/components/ProjectHomeEntryPanel.ts").read_text(encoding="utf-8")
    entry = (ROOT / "ui/web/src/pages/ProjectEntryDryRunView.ts").read_text(encoding="utf-8")
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")

    assert "path: '/', routeId: 'ui.dashboard', title: 'Project Home', scope: 'home'" in main
    assert "scope: 'project'" in main
    assert "scope: 'entry-or-project'" in main
    assert "function routeAllowed" in main
    assert "function routeVisible" in main
    assert "beginProjectEntryJourney" in home
    assert "activateProjectJourney" in entry
    assert "PROJECT_JOURNEY_CONTEXT_KEY" in client
    assert "clearProjectJourneyContext" in main
    assert "readProjectJourneyContext()?.phase === 'project'" in (ROOT / "ui/web/src/pages/Dashboard.ts").read_text(encoding="utf-8")
    assert "executionPayload.status" in entry and "contexto de proyecto permanece bloqueado" in entry
    assert "Estado del proyecto, Documentos, Reportes, Trazas, Jobs, Calidad/Tests e IA/RAG" in home
    assert "APPROVAL_CENTER_ENTRY_HANDOFF_KEY" in client
    assert "APPROVAL_CENTER_ENTRY_HANDOFF_TTL_MS = 30 * 60 * 1000" in client
    assert "session_created_at" in client and "actor_id" in client
    assert "readApprovalCenterEntryHandoff(session, handoffApprovalId)" in main
    assert "currentPath === '/approvals'" in main
    assert "armApprovalCenterEntryHandoff" in entry
    assert "approvalLink.hidden=true" in entry
    assert "handoff=project-entry&approval_id=" in entry
    assert "clearApprovalCenterEntryHandoff" in client


def test_03e_current_route_registry_preserves_history_but_exposes_product_home() -> None:
    current = json.loads((ROOT / ".devpilot/interfaces/ui_route_contract_registry.json").read_text(encoding="utf-8"))
    frozen = json.loads((ROOT / ".devpilot/interfaces/ui_route_contract_registry_gsdlc03d_at_close.json").read_text(encoding="utf-8"))
    current_dashboard = next(row for row in current["routes"] if row["route_id"] == "ui.dashboard")
    frozen_dashboard = next(row for row in frozen["routes"] if row["route_id"] == "ui.dashboard")
    assert current_dashboard["path"] == "/"
    assert current_dashboard["title"] == "Project Home"
    assert frozen_dashboard["path"] == "/"
    assert frozen_dashboard["title"] != "Project Home"



def test_03e_approval_center_cross_tab_handoff_is_session_bound_ttl_bounded_and_not_authority() -> None:
    main = text('ui/web/src/main.ts')
    client = text('ui/web/src/api/client.ts')
    entry = text('ui/web/src/pages/ProjectEntryDryRunView.ts')
    dashboard = text('ui/web/src/pages/Dashboard.ts')
    assert "APPROVAL_CENTER_ENTRY_HANDOFF_KEY" in client
    assert "APPROVAL_CENTER_ENTRY_HANDOFF_TTL_MS = 30 * 60 * 1000" in client
    assert "value.actor_id === session.principal.actor_id" in client
    assert "value.session_created_at === session.created_at" in client
    assert "value.approval_id === expected" in client
    assert "Date.now() <= value.expires_at_ms" in client
    assert "currentPath === '/approvals' && handoffApprovalId ? readApprovalCenterEntryHandoff(session, handoffApprovalId) : null" in main
    assert "approvalLink.hidden=true" in entry
    assert "armApprovalCenterEntryHandoff(session, mode.select.value as EntryMode, id)" in entry
    assert "approval_id=${encodeURIComponent(id)}" in entry
    assert "Approval Center se habilita durante un journey" in dashboard
    # Cross-tab handoff is navigation UX only; mutation authority remains server-side human session/RBAC.
    assert "localStorage" in client
    assert "activateProjectJourney" in client and "clearApprovalCenterEntryHandoff();" in client


def test_03e_project_entry_uses_operation_specific_browser_budget_without_relaxing_global_timeout() -> None:
    client = text('ui/web/src/api/client.ts')
    package = j('ui/web/package.json')['devpilot']
    assert 'DEFAULT_REQUEST_TIMEOUT_MS = 8000' in client
    assert 'PROJECT_ENTRY_PROBE_TIMEOUT_SECONDS = 8.0' in client
    assert 'PROJECT_ENTRY_PLANNING_TIMEOUT_MS = 90000' in client
    assert 'PROJECT_ENTRY_EXECUTION_TIMEOUT_MS = 240000' in client
    assert 'MAX_REQUEST_TIMEOUT_MS = PROJECT_ENTRY_EXECUTION_TIMEOUT_MS' in client
    assert 'APPROVAL_CENTER_READ_TIMEOUT_MS = 30000' in client
    assert 'APPROVAL_CENTER_DECISION_TIMEOUT_MS = 30000' in client
    assert 'Math.min(Number(value), MAX_REQUEST_TIMEOUT_MS)' in client
    assert client.count('timeoutMs: PROJECT_ENTRY_PLANNING_TIMEOUT_MS') >= 3
    assert client.count('timeout_seconds: payload.timeout_seconds ?? PROJECT_ENTRY_PROBE_TIMEOUT_SECONDS') >= 4
    assert package['gsdlc03eProjectEntryProbeTimeoutSeconds'] == 8
    assert package['gsdlc03eProjectEntryPlanningTimeoutMs'] == 90000
    assert package['gsdlc03eOrdinaryRequestTimeoutPreservedMs'] == 8000
    assert package['gsdlc03eProjectEntryTimeoutCorrective'] == 'GSDLC-03-E-RUNTIME-002'


def test_03e_targeted_approval_handoff_does_not_depend_on_global_list_or_portfolio() -> None:
    main = text('ui/web/src/main.ts')
    center = text('ui/web/src/pages/ApprovalCenterView.ts')
    client = text('ui/web/src/api/client.ts')
    assert "handoffApprovalId" in main
    assert "renderApprovalCenterView({ tokenProvider: () => readStoredToken(), session, handoffApprovalId" in main
    assert "Approval Center · Project Entry" in center
    assert "No es necesario filtrar ni cargar la lista global" in center
    assert "if (state.handoffApprovalId) void loadHandoffApproval();" in center
    assert "state.selected = await new DevPilotApiClient({ token: tokenProvider() }).showApproval(state.handoffApprovalId!)" in center
    assert "Approval Center general — no requerido para este handoff" in center
    assert "renderApprovalAuthorityPanel(session)" in center
    assert "session.principal.roles" in center
    assert "capability_view" in center
    assert "if (state.handoffApprovalId) void loadHandoffApproval();" in center
    assert "APPROVAL_CENTER_READ_TIMEOUT_MS" in client


def test_03e_handoff_is_bound_to_exact_approval_id_and_not_only_session() -> None:
    client = text('ui/web/src/api/client.ts')
    entry = text('ui/web/src/pages/ProjectEntryDryRunView.ts')
    assert "approval_id: string" in client
    assert "approval_id: approvalId.trim()" in client
    assert "readApprovalCenterEntryHandoff(session: AuthSessionContext, expectedApprovalId: string)" in client
    assert "value.approval_id === expected" in client
    assert "armApprovalCenterEntryHandoff(session, mode.select.value as EntryMode, id)" in entry


def test_03e_browser_timeout_normalization_preserves_declared_planning_and_execute_budgets() -> None:
    client = text('ui/web/src/api/client.ts')
    assert "DEFAULT_REQUEST_TIMEOUT_MS = 8000" in client
    assert "PROJECT_ENTRY_PLANNING_TIMEOUT_MS = 90000" in client
    assert "PROJECT_ENTRY_EXECUTION_TIMEOUT_MS = 240000" in client
    assert "MAX_REQUEST_TIMEOUT_MS = PROJECT_ENTRY_EXECUTION_TIMEOUT_MS" in client
    assert "Math.min(Number(value), MAX_REQUEST_TIMEOUT_MS)" in client
    assert "Math.min(Number(value), 60000)" not in client


def test_03e_project_entry_state_is_resumable_but_never_authoritative() -> None:
    client = text('ui/web/src/api/client.ts')
    entry = text('ui/web/src/pages/ProjectEntryDryRunView.ts')
    home = text('ui/web/src/components/ProjectHomeEntryPanel.ts')
    main = text('ui/web/src/main.ts')
    center = text('ui/web/src/pages/ApprovalCenterView.ts')

    assert "PROJECT_ENTRY_RESUME_STATE_KEY = 'devpilot.gsdlc03e.projectEntryResumeState.v1'" in client
    assert 'PROJECT_ENTRY_RESUME_TTL_MS = 30 * 60 * 1000' in client
    assert 'value.actor_id === session.principal.actor_id' in client
    assert 'value.session_created_at === session.created_at' in client
    assert 'Date.now() <= value.expires_at_ms' in client
    assert 'globalThis.sessionStorage?.setItem(PROJECT_ENTRY_RESUME_STATE_KEY' in client
    assert 'localStorage?.setItem(PROJECT_ENTRY_RESUME_STATE_KEY' not in client
    assert 'saveProjectEntryResumeState' in entry
    assert 'readProjectEntryResumeState(session' in entry
    assert 'RESUMED: plan/preimage restaurados desde sessionStorage' in entry
    assert 'Revalidar preimage antes de verificar approval o ejecutar' in entry
    assert 'clearProjectEntryResumeState' in entry
    assert 'clearApprovalCenterEntryHandoff' in entry
    assert 'Retomar ${resumeState.entry_mode}' in home
    assert 'data-resume-project-entry' not in home  # property is assigned via dataset, not unsafe HTML.
    assert "link.dataset.resumeProjectEntry = 'true'" in home
    assert 'auxiliaryApprovalHandoff' in main
    assert "item.path === '/approvals' || item.path === '/account'" in main
    assert 'Cerrar esta pestaña y volver a CREATE' in center
    assert 'No navegue a Project Home desde aquí' in center


def test_03e_documented_source_count_and_windows_timeout_status_are_reconciled() -> None:
    state = j('.devpilot/project_state.json')
    current = j('docs/audits/DEVPL_GSDLC_03_E_CURRENT.json')
    assert state['gsdlc_03_e_source_delta_paths_total'] == 64
    assert current['source_delta_paths_total'] == 64
    assert state['gsdlc_03_e_timeout_default_propagation_status'] == 'PASS/windows-validated'
    assert current['timeout_default_propagation_status'] == 'PASS/windows-validated'
    assert state['gsdlc_03_e_current_corrective'] == 'GSDLC-03-E-UX-004/HARNESS-008'
    assert current['entry_resume']['finding_id'] == 'GSDLC-03-E-UX-004'

def test_03e_windows_composite_closure_candidate_is_reconciled() -> None:
    state = j('.devpilot/project_state.json')
    current = j('docs/audits/DEVPL_GSDLC_03_E_CURRENT.json')
    op = j('docs/audits/DEVPL_GSDLC_03_E_OPERATION_DECLARATION.json')
    registry = j('.devpilot/docs_governance/source_registry.json')
    closure = text('docs/audits/DEVPL_GSDLC_03_E_CLOSURE_REPORT.md')
    roadmap = text('docs/00_product/DEVPL_GSDLC_product_evolution_roadmap.md')
    readme = text('README.md')

    expected = 'closed/PASS'
    evidence_sha = 'a0a418d9cad544d3c10cac40e257d41baf01f9cb4df9c12d67005d1a7a6ece33'
    source_fingerprint = '8c698d63a75938267b6f9b8028b1cfbec9a54be9e2375da15d3b509f6822772a'

    assert state['gsdlc_03_e_status'] == expected
    assert state['gsdlc_03_status'] == 'closed/PASS'
    assert state['gsdlc_03_e_composite_regression_recovery_result'] == 'PASS'
    assert state['gsdlc_03_e_reg002_exact_11_passed'] == 11
    assert state['gsdlc_03_e_reg002_bounded_impact_passed'] == 13
    assert state['gsdlc_03_e_second_full_regression_executed'] is False
    assert state['gsdlc_03_e_exact_67_rerun_executed'] is False
    assert state['gsdlc_04_authorized'] is True
    assert state['gsdlc_03_e_windows_composite_evidence_sha256'] == evidence_sha
    assert state['gsdlc_03_e_windows_composite_source_fingerprint'] == source_fingerprint

    assert current['status'] == expected
    assert current['version'] == '1.0.16'
    assert current['composite_recovery'] == 'PASS/REG-002/exact-11-11-of-11'
    assert current['reg002_exact_11_residual_retest']['passed'] == 11
    assert current['reg002_bounded_impact_guard']['passed'] == 13
    assert current['historical_regression_guard'] == 'PASS'
    assert current['second_full_regression_executed'] is False
    assert current['owner_adjudication_pending'] is False

    assert op['status'] == expected
    assert op['full_regression'] == 'FAIL-ONCE/RECOVERED-BY-COMPOSITE-EVIDENCE'
    assert op['composite_recovery'] == 'PASS/REG-002'
    assert op['second_full_regression_executed'] is False
    assert op['owner_adjudication_pending'] is False

    registered = {row['path']: row for row in registry['documents']}
    for path in (
        'docs/audits/DEVPL_GSDLC_03_E_CURRENT.json',
        'docs/audits/DEVPL_GSDLC_03_E_OPERATION_DECLARATION.json',
        'docs/audits/DEVPL_GSDLC_03_E_CLOSURE_REPORT.md',
    ):
        assert registered[path]['status_required'] == expected

    assert 'CLOSED/PASS' in closure
    assert 'REG-002 `11/11 PASS`' in roadmap
    assert 'GSDLC-04-A' in readme

