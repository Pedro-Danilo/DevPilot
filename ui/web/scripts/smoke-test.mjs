import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.cwd());
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

const packageJson = JSON.parse(read('package.json'));
const client = read('src/api/client.ts');
const dashboard = read('src/pages/Dashboard.ts');
const reportsView = read('src/pages/ReportsView.ts');
const tracesView = read('src/pages/TracesView.ts');
const approvalCenterView = read('src/pages/ApprovalCenterView.ts');
const settingsView = read('src/pages/SettingsView.ts');
const jobsView = read('src/pages/JobsView.ts');
const workspaceDocumentsView = read('src/pages/WorkspaceDocumentsView.ts');
const documentTree = read('src/components/DocumentTree.ts');
const documentViewer = read('src/components/DocumentViewer.ts');
const documentValidationPanel = read('src/components/DocumentValidationPanel.ts');
const providerSettings = read('src/components/ProviderSettings.ts');
const dryRunActionForm = read('src/components/DryRunActionForm.ts');
const findingTable = read('src/components/FindingTable.ts');
const statusCard = read('src/components/StatusCard.ts');
const contractBadges = read('src/components/ContractBadges.ts');
const operatorDashboard = read('src/pages/OperatorDashboard.ts');
const operatorStatusCard = read('src/components/OperatorStatusCard.ts');
const operatorGatePanel = read('src/components/OperatorGatePanel.ts');
const operatorNextActions = read('src/components/OperatorNextActions.ts');
const uiContractRegistry = JSON.parse(read('../../.devpilot/interfaces/ui_route_contract_registry.json'));
const apiContractRegistry = JSON.parse(read('../../.devpilot/interfaces/api_route_contract_registry.json'));
const sanitizeUtils = read('src/utils/sanitize.ts');
const filesToScan = [client, dashboard, statusCard, reportsView, tracesView, findingTable, approvalCenterView, dryRunActionForm, settingsView, providerSettings, contractBadges, sanitizeUtils, operatorDashboard, operatorStatusCard, operatorGatePanel, operatorNextActions, workspaceDocumentsView, documentTree, documentViewer, documentValidationPanel, read('src/main.ts')];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

assert(packageJson.devpilot.sprint === 'FUNC-SPRINT-73', 'package.json debe declarar FUNC-SPRINT-73');
assert(packageJson.devpilot.apiOnly === true, 'La UI debe ser API-only');
const uoc005Active = packageJson.devpilot.uoc005ApprovalBinding === true;
assert(packageJson.devpilot.dryRunOnly === (uoc005Active ? false : true), 'dryRunOnly debe reflejar la frontera UOC-005');
if (uoc005Active) {
  assert(packageJson.devpilot.documentWriteMode === 'approval-gated-atomic-uoc005', 'UOC-005 debe declarar documentWriteMode gobernado');
  assert(packageJson.devpilot.genericPatchApplyEnabled === false, 'patch.apply genérico debe permanecer bloqueado');
  assert(packageJson.devpilot.genericRollbackEnabled === false, 'rollback genérico debe permanecer bloqueado');
  assert(packageJson.devpilot.uoc005AtomicDocumentApply === true && packageJson.devpilot.uoc005BoundedDocumentRollback === true, 'UOC-005 debe declarar apply/rollback acotados');
}
assert(packageJson.devpilot.phaseFClosed === true, 'La UI debe declarar cierre Fase F');
assert(packageJson.devpilot.desktopDeferred === true, 'La UI debe declarar Desktop diferido');
assert(packageJson.devpilot.webRealEvolutionPlanned === true, 'La UI debe declarar evolución Web real');
assert(packageJson.devpilot.postH014C === true, 'La UI debe declarar POST-H-014-C activo');
assert(packageJson.devpilot.postH014D === true, 'La UI debe declarar POST-H-014-D activo');
assert(packageJson.devpilot.postH014E === true, 'La UI debe declarar POST-H-014-E activo');
assert(packageJson.devpilot.postH015D === true, 'La UI debe declarar POST-H-015-D activo');
assert(packageJson.devpilot.operatorDashboardUi === true, 'La UI debe declarar Operator Dashboard activo');
assert(packageJson.devpilot.uiApiShellQualityGate === true, 'La UI debe declarar quality gate UI/API shell');
assert(packageJson.devpilot.securityPosture === true, 'La UI debe declarar security posture local');
assert(packageJson.devpilot.uiRouteContractRegistry === true, 'La UI debe declarar UI Route Contract Registry');
assert(packageJson.devpilot.localFirstBadges === true, 'La UI debe declarar badges local-first');
assert(packageJson.devpilot.noRemoteBadges === true, 'La UI debe declarar badges no-remote');
assert(packageJson.devpilot.uoc003ValidationTraceability === true, 'La UI debe declarar UOC-003 validation/traceability');
assert(packageJson.devpilot.uoc003SourceReadOnly === true, 'UOC-003 debe preservar source read-only');
assert(packageJson.scripts.test === 'node scripts/smoke-test.mjs', 'npm test debe ser local y reproducible');

assert(uiContractRegistry.schema_id === 'SCHEMA-DEVPL-UI-ROUTE-CONTRACT-REGISTRY-V1', 'UI registry schema_id inválido');
assert(uiContractRegistry.created_by === 'POST-H-014-C', 'UI registry debe declarar POST-H-014-C');
const expectedUiRoutes = ['ui.dashboard', 'ui.reports', 'ui.traces', 'ui.approvals', 'ui.settings', 'ui.workspace-documents', 'ui.jobs'];
const apiRouteIds = new Set(apiContractRegistry.routes.map((route) => route.route_id));
for (const routeId of expectedUiRoutes) {
  assert(uiContractRegistry.routes.some((route) => route.route_id === routeId), `Falta contrato UI ${routeId}`);
}
for (const route of uiContractRegistry.routes) {
  assert(route.local_only === true, `${route.route_id} debe ser local_only`);
  assert(route.remote_execution_allowed === false, `${route.route_id} no debe permitir remote execution`);
  assert(route.connector_write_allowed === false, `${route.route_id} no debe permitir connector write`);
  assert(route.plugin_execution_allowed === false, `${route.route_id} no debe permitir plugin execution`);
  assert(route.external_api_allowed === false, `${route.route_id} no debe permitir external APIs`);
  assert(route.state_contract.loading && route.state_contract.empty && route.state_contract.error && route.state_contract.block_visible, `${route.route_id} debe declarar loading/empty/error/block states`);
  for (const apiRoute of route.allowed_api_routes) {
    assert(apiRouteIds.has(apiRoute), `${route.route_id} referencia API desconocida ${apiRoute}`);
  }
}


for (const source of filesToScan) {
  assert(!source.includes('devpilot_core'), 'La UI no debe importar Python/core');
  assert(!source.includes('child_process'), 'La UI no debe ejecutar procesos locales');
  assert(!source.includes('outputs/'), 'La UI no debe leer outputs directamente');
}

for (const expectedPath of ['/operator/dashboard', '/workspace/status', '/validation/readiness', '/standards/status', '/miasi/status', '/reports', '/traces', '/metrics/summary', '/approvals', '/actions/dry-run', '/settings/workspace', '/settings/providers', '/settings/policy', '/security/posture', '/settings/providers/plan', '/workspace/documents', '/workspace/validations/plan', '/workspace/validations/execute', '/workspace/traceability', '/jobs', '/logs', '/cancel', '/retry']) {
  assert(client.includes(expectedPath), `El cliente API debe consumir ${expectedPath}`);
}
if (uoc005Active) {
  for (const marker of ['/approval-request', '/apply', '/workspace/edit-executions/', '/rollback-approval-request', '/rollback']) {
    assert(client.includes(marker), `UOC-005 debe exponer cliente tipado ${marker}`);
  }
  const workspaceRoute = uiContractRegistry.routes.find((route) => route.route_id === 'ui.workspace-documents');
  assert(workspaceRoute?.shows_mutation_controls === true, 'UOC-005 debe registrar mutation controls en Workspace Documents');
  assert(workspaceRoute?.mutation_controls?.approval_required === true, 'UOC-005 debe exigir approval en UI route contract');
  assert(workspaceRoute?.mutation_controls?.destructive_action_allowed === false, 'UOC-005 no debe habilitar acción destructiva libre');
}

assert(client.includes('X-DevPilot-Token'), 'El cliente debe enviar token local por header');
assert(statusCard.includes('PASS') && statusCard.includes('WARN') && statusCard.includes('BLOCK'), 'La UI debe traducir estados PASS/WARN/BLOCK');
assert(reportsView.includes('Reportes') && tracesView.includes('Trazas'), 'La UI debe incluir vistas específicas de Reportes y Trazas');
assert(contractBadges.includes('renderContractBadges'), 'La UI debe tener componente ContractBadges');
assert(dashboard.includes('ui.dashboard'), 'Dashboard debe declarar marker ui.dashboard');
assert(reportsView.includes('ui.reports') && tracesView.includes('ui.traces'), 'ReportsView/TracesView deben declarar contratos específicos');
assert(!reportsView.includes('listTraces') && !tracesView.includes('listReports'), 'Reports y Traces no deben realizar consultas cruzadas automáticas');
assert(approvalCenterView.includes('ui.approvals'), 'ApprovalCenterView debe declarar marker ui.approvals');
assert(settingsView.includes('ui.settings'), 'SettingsView debe declarar marker ui.settings');
assert(reportsView.includes('No hay reportes locales') && tracesView.includes('No hay trazas disponibles'), 'Reportes/Trazas deben manejar estados vacíos');
assert(approvalCenterView.includes('Approval Center') && approvalCenterView.includes('Action Launcher'), 'La UI debe incluir Approval Center y Action Launcher');
assert(workspaceDocumentsView.includes('ui.workspace-documents') && workspaceDocumentsView.includes('identificadores opacos'), 'Workspace Documents debe declarar contrato read-only y opaque ids');
assert(documentTree.includes("role', 'treeitem'"), 'DocumentTree debe declarar semántica treeitem');
assert(documentValidationPanel.includes('ui.workspace-documents') && documentValidationPanel.includes('planWorkspaceValidations') && documentValidationPanel.includes('executeWorkspaceValidations'), 'UOC-003 debe exponer plan/execute tipado');
assert(documentValidationPanel.includes('workspaceTraceability') && documentValidationPanel.includes('Findings') && documentValidationPanel.includes('Trazabilidad'), 'UOC-003 debe exponer findings y trazabilidad');
assert(documentViewer.includes('textContent') && !documentViewer.includes('innerHTML'), 'DocumentViewer debe renderizar contenido sin innerHTML');
assert(settingsView.includes('Configuración') && settingsView.includes('Editor de provider — plan-only'), 'La UI debe incluir Configuración y editor plan-only');
assert(settingsView.includes('Postura de seguridad') && settingsView.includes('securityPosture'), 'Configuración debe mostrar postura de seguridad');
assert(jobsView.includes('Job Console') && jobsView.includes('ui.jobs') && jobsView.includes('Heartbeat') && jobsView.includes('Logs sanitizados'), 'UOC-008 debe exponer Job Console observable');
assert(jobsView.includes('cancelJob') && jobsView.includes('retryJob') && !jobsView.includes('child_process'), 'Job Console debe usar cliente tipado sin shell');
assert(dashboard.includes('renderOperatorDashboard'), 'Dashboard debe integrar OperatorDashboard POST-H-015-D');
assert(operatorDashboard.includes('Operator Dashboard') && operatorDashboard.includes('POST-H-015-D'), 'OperatorDashboard debe declarar POST-H-015-D');
assert(operatorStatusCard.includes('source_refs'), 'OperatorStatusCard debe mostrar fuentes del snapshot');
assert(operatorGatePanel.includes('No-go gates') && operatorGatePanel.includes('remote_execution_enabled') && operatorGatePanel.includes('DISABLED BY POLICY'), 'OperatorGatePanel debe mostrar no-go gates con semántica segura');
assert(operatorNextActions.includes('Next actions') && operatorNextActions.includes('dry-run'), 'OperatorNextActions debe mostrar acciones locales/dry-run');
assert(contractBadges.includes('data-ui-state=\"loading\"') && contractBadges.includes('data-ui-state=\"empty\"') && contractBadges.includes('data-ui-state=\"error\"'), 'El contrato UI debe declarar loading/empty/error sin renderizarlos simultáneamente');
assert(providerSettings.includes('api_key_env'), 'Providers settings puede mostrar nombres de env var, no secretos crudos');
assert(providerSettings.includes('escapeHtml') && settingsView.includes('safeJsonForHtml'), 'Settings UI debe escapar HTML y redactar secretos antes de renderizar');
assert(sanitizeUtils.includes('redactSecrets') && sanitizeUtils.includes('escapeHtml'), 'La UI debe incluir utilidades locales de redacción/escape');
assert(dryRunActionForm.includes('Solo acciones read-only/dry-run'), 'El formulario debe declarar dry-run seguro');
assert(!client.includes('/patch/apply'), 'La UI no debe invocar acciones destructivas');
assert(!client.includes('/rollback/execute'), 'La UI no debe invocar rollback execute');
assert(!client.includes('/git/push'), 'La UI no debe invocar git push');
assert(!settingsView.includes('fs.readFile'), 'Settings UI no debe leer archivos locales');
assert(!settingsView.includes('writeFile'), 'Settings UI no debe escribir archivos locales');

console.log('DEVPL WEB UI SMOKE TEST: PASS');
