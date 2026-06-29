import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.cwd());
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

const packageJson = JSON.parse(read('package.json'));
const client = read('src/api/client.ts');
const dashboard = read('src/pages/Dashboard.ts');
const reportTraceView = read('src/pages/ReportTraceView.ts');
const approvalCenterView = read('src/pages/ApprovalCenterView.ts');
const settingsView = read('src/pages/SettingsView.ts');
const providerSettings = read('src/components/ProviderSettings.ts');
const dryRunActionForm = read('src/components/DryRunActionForm.ts');
const findingTable = read('src/components/FindingTable.ts');
const statusCard = read('src/components/StatusCard.ts');
const contractBadges = read('src/components/ContractBadges.ts');
const uiContractRegistry = JSON.parse(read('../../.devpilot/interfaces/ui_route_contract_registry.json'));
const apiContractRegistry = JSON.parse(read('../../.devpilot/interfaces/api_route_contract_registry.json'));
const sanitizeUtils = read('src/utils/sanitize.ts');
const filesToScan = [client, dashboard, statusCard, reportTraceView, findingTable, approvalCenterView, dryRunActionForm, settingsView, providerSettings, contractBadges, sanitizeUtils, read('src/main.ts')];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

assert(packageJson.devpilot.sprint === 'FUNC-SPRINT-73', 'package.json debe declarar FUNC-SPRINT-73');
assert(packageJson.devpilot.apiOnly === true, 'La UI debe ser API-only');
assert(packageJson.devpilot.dryRunOnly === true, 'La UI debe declarar dry-run only');
assert(packageJson.devpilot.phaseFClosed === true, 'La UI debe declarar cierre Fase F');
assert(packageJson.devpilot.desktopDeferred === true, 'La UI debe declarar Desktop diferido');
assert(packageJson.devpilot.webRealEvolutionPlanned === true, 'La UI debe declarar evolución Web real');
assert(packageJson.devpilot.postH014C === true, 'La UI debe declarar POST-H-014-C activo');
assert(packageJson.devpilot.postH014D === true, 'La UI debe declarar POST-H-014-D activo');
assert(packageJson.devpilot.postH014E === true, 'La UI debe declarar POST-H-014-E activo');
assert(packageJson.devpilot.uiApiShellQualityGate === true, 'La UI debe declarar quality gate UI/API shell');
assert(packageJson.devpilot.securityPosture === true, 'La UI debe declarar security posture local');
assert(packageJson.devpilot.uiRouteContractRegistry === true, 'La UI debe declarar UI Route Contract Registry');
assert(packageJson.devpilot.localFirstBadges === true, 'La UI debe declarar badges local-first');
assert(packageJson.devpilot.noRemoteBadges === true, 'La UI debe declarar badges no-remote');
assert(packageJson.scripts.test === 'node scripts/smoke-test.mjs', 'npm test debe ser local y reproducible');

assert(uiContractRegistry.schema_id === 'SCHEMA-DEVPL-UI-ROUTE-CONTRACT-REGISTRY-V1', 'UI registry schema_id inválido');
assert(uiContractRegistry.created_by === 'POST-H-014-C', 'UI registry debe declarar POST-H-014-C');
const expectedUiRoutes = ['ui.dashboard', 'ui.reports', 'ui.traces', 'ui.approvals', 'ui.settings'];
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

for (const expectedPath of ['/workspace/status', '/validation/readiness', '/standards/status', '/miasi/status', '/reports', '/traces', '/metrics/summary', '/approvals', '/actions/dry-run', '/settings/workspace', '/settings/providers', '/settings/policy', '/security/posture', '/settings/providers/plan']) {
  assert(client.includes(expectedPath), `El cliente API debe consumir ${expectedPath}`);
}

assert(client.includes('X-DevPilot-Token'), 'El cliente debe enviar token local por header');
assert(statusCard.includes('PASS') && statusCard.includes('WARN') && statusCard.includes('BLOCK'), 'La UI debe traducir estados PASS/WARN/BLOCK');
assert(reportTraceView.includes('Report Viewer') && reportTraceView.includes('Trace Viewer'), 'La UI debe incluir Report Viewer y Trace Viewer');
assert(contractBadges.includes('renderContractBadges'), 'La UI debe tener componente ContractBadges');
assert(dashboard.includes('ui.dashboard'), 'Dashboard debe declarar marker ui.dashboard');
assert(reportTraceView.includes('ui.reports') && reportTraceView.includes('ui.traces'), 'ReportTraceView debe declarar markers ui.reports/ui.traces');
assert(approvalCenterView.includes('ui.approvals'), 'ApprovalCenterView debe declarar marker ui.approvals');
assert(settingsView.includes('ui.settings'), 'SettingsView debe declarar marker ui.settings');
assert(reportTraceView.includes('Sin trazas para mostrar'), 'Trace Viewer debe manejar trazas vacías');
assert(approvalCenterView.includes('Approval Center') && approvalCenterView.includes('Action Launcher'), 'La UI debe incluir Approval Center y Action Launcher');
assert(settingsView.includes('Settings UI') && settingsView.includes('Provider editor plan-only'), 'La UI debe incluir Settings UI y editor plan-only');
assert(settingsView.includes('Security posture') && settingsView.includes('POST-H-014-D'), 'Settings UI debe mostrar Security posture POST-H-014-D');
assert(settingsView.includes('data-ui-state=\"loading\"') && settingsView.includes('data-ui-state=\"empty\"') && settingsView.includes('data-ui-state=\"error\"'), 'Settings UI debe declarar loading/empty/error states');
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
