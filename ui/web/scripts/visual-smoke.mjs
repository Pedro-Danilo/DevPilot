import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.cwd());
const repoRoot = path.resolve(root, '../..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');
const readRepo = (relative) => fs.readFileSync(path.join(repoRoot, relative), 'utf8');
const readJson = (relative) => JSON.parse(read(relative));
const readRepoJson = (relative) => JSON.parse(readRepo(relative));

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const packageJson = readJson('package.json');
const uiRegistry = readRepoJson('.devpilot/interfaces/ui_route_contract_registry.json');
const apiRegistry = readRepoJson('.devpilot/interfaces/api_route_contract_registry.json');
const apiRouteIds = new Set(apiRegistry.routes.map((route) => route.route_id));

const sourceFiles = [
  'src/main.ts',
  'src/api/client.ts',
  'src/pages/Dashboard.ts',
  'src/pages/ReportsView.ts',
  'src/pages/TracesView.ts',
  'src/pages/ApprovalCenterView.ts',
  'src/pages/SettingsView.ts',
  'src/pages/JobsView.ts',
  'src/pages/QualityOperationsView.ts',
  'src/pages/OperatorDashboard.ts',
  'src/components/StatusCard.ts',
  'src/components/ContractBadges.ts',
  'src/components/DryRunActionForm.ts',
  'src/components/ProviderSettings.ts',
  'src/components/OperatorGatePanel.ts',
  'src/components/OperatorNextActions.ts',
  'src/components/OperatorStatusCard.ts',
  'src/utils/sanitize.ts',
];
const sources = Object.fromEntries(sourceFiles.map((file) => [file, read(file)]));
const combined = Object.values(sources).join('\n');

assert(packageJson.devpilot.postH028C === true, 'package.json debe declarar postH028C=true');
assert(packageJson.devpilot.uiVisualSmoke === true, 'package.json debe declarar uiVisualSmoke=true');
assert(packageJson.scripts['test:visual'] === 'node scripts/visual-smoke.mjs', 'npm run test:visual debe ser dependency-light');

const expectedRoutes = ['ui.dashboard', 'ui.reports', 'ui.traces', 'ui.approvals', 'ui.settings', 'ui.workspace-documents', 'ui.jobs', 'ui.quality'];
for (const routeId of expectedRoutes) {
  assert(uiRegistry.routes.some((route) => route.route_id === routeId), `Falta contrato UI ${routeId}`);
}
for (const route of uiRegistry.routes) {
  assert(route.local_only === true, `${route.route_id} debe ser local-only`);
  assert(route.remote_execution_allowed === false, `${route.route_id} no debe permitir remote execution`);
  assert(route.connector_write_allowed === false, `${route.route_id} no debe permitir connector write`);
  assert(route.plugin_execution_allowed === false, `${route.route_id} no debe permitir plugin execution`);
  assert(route.external_api_allowed === false, `${route.route_id} no debe permitir external APIs`);
  assert(route.state_contract.loading && route.state_contract.empty && route.state_contract.error && route.state_contract.block_visible, `${route.route_id} debe declarar estados visuales`);
  for (const apiRoute of route.allowed_api_routes) {
    assert(apiRouteIds.has(apiRoute), `${route.route_id} referencia API desconocida ${apiRoute}`);
  }
}

const visualMarkers = [
  ['dashboard', 'src/pages/Dashboard.ts', ['DevPilot Local Dashboard', 'ui.dashboard', 'renderOperatorDashboard']],
  ['report viewer', 'src/pages/ReportsView.ts', ['Reportes', 'ui.reports', 'No hay reportes locales']],
  ['trace viewer', 'src/pages/TracesView.ts', ['Trazas', 'ui.traces', 'No hay trazas disponibles']],
  ['approval center', 'src/pages/ApprovalCenterView.ts', ['Approval Center', 'ui.approvals', 'Action Launcher', 'Sin approvals']],
  ['settings', 'src/pages/SettingsView.ts', ['Configuración', 'ui.settings', 'Editor de provider — plan-only', 'Postura de seguridad']],
  ['job console', 'src/pages/JobsView.ts', ['Job Console', 'ui.jobs', 'Heartbeat', 'Solicitar cancelación', 'Crear retry gobernado']],
  ['quality console', 'src/pages/QualityOperationsView.ts', ['Quality, tests y release', 'ui.quality', 'Planificar Test Impact', 'Full regression', 'Approval requerido']],
  ['operator dashboard', 'src/pages/OperatorDashboard.ts', ['Operator Dashboard', 'POST-H-015-D']],
];
for (const [view, file, markers] of visualMarkers) {
  for (const marker of markers) {
    assert(sources[file].includes(marker), `${view} no contiene marker visual: ${marker}`);
  }
}

for (const marker of ['loading state', 'empty state', 'error state', 'BLOCK', '401/403', 'API local down']) {
  assert(combined.includes(marker), `Falta estado visual requerido: ${marker}`);
}
for (const forbidden of ['devpilot_core', 'child_process', 'outputs/', '.devpilot/', '/patch/apply', '/rollback/execute', '/git/push']) {
  assert(!combined.includes(forbidden), `La UI no debe contener marcador prohibido: ${forbidden}`);
}

console.log(JSON.stringify({
  status: 'PASS',
  created_by: 'POST-H-028-C',
  critical_views_total: visualMarkers.length,
  critical_views_passed: visualMarkers.length,
  browser_tooling_status: 'optional-advisory',
  screenshots_output_path: 'outputs/ui-smoke/screenshots/',
}, null, 2));
console.log('DEVPL WEB UI VISUAL SMOKE TEST: PASS');
