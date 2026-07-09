#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const webRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const repoRoot = resolve(webRoot, '../..');
const readWeb = (relative) => readFileSync(join(webRoot, relative), 'utf8');
const readRepoJson = (relative) => JSON.parse(readFileSync(join(repoRoot, relative), 'utf8'));

const uiRegistry = readRepoJson('.devpilot/interfaces/ui_route_contract_registry.json');
const apiRegistry = readRepoJson('.devpilot/interfaces/api_route_contract_registry.json');
const apiRouteIds = new Set(apiRegistry.routes.map((route) => route.route_id));
const requiredRoutes = ['ui.dashboard', 'ui.reports', 'ui.traces', 'ui.approvals', 'ui.settings'];
const forbidden = ['/patch/apply', 'patch-apply</option>', '/rollback/execute', '/refactor/execute', '/tests/run', '/git/push', '/deploy', 'child_process', 'devpilot_core', '.devpilot/', 'outputs/'];
const sources = [
  'src/main.ts',
  'src/api/client.ts',
  'src/pages/Dashboard.ts',
  'src/pages/ReportTraceView.ts',
  'src/pages/ApprovalCenterView.ts',
  'src/pages/SettingsView.ts',
  'src/pages/OperatorDashboard.ts',
  'src/components/DryRunActionForm.ts',
  'src/components/ProviderSettings.ts',
  'src/components/OperatorGatePanel.ts',
  'src/components/OperatorNextActions.ts',
].map((file) => readWeb(file)).join('\n');

const missingRoutes = requiredRoutes.filter((routeId) => !uiRegistry.routes.some((route) => route.route_id === routeId));
const unknownApiRefs = [];
const missingState = [];
const noGoViolations = [];
for (const route of uiRegistry.routes) {
  for (const apiRoute of route.allowed_api_routes ?? []) {
    if (!apiRouteIds.has(apiRoute)) unknownApiRefs.push({ route_id: route.route_id, api_route: apiRoute });
  }
  const state = route.state_contract ?? {};
  if (!(state.loading && state.empty && state.error && state.block_visible)) missingState.push(route.route_id);
  for (const flag of ['remote_execution_allowed', 'connector_write_allowed', 'plugin_execution_allowed', 'external_api_allowed']) {
    if (route[flag] !== false) noGoViolations.push({ route_id: route.route_id, flag });
  }
}
const forbiddenFound = forbidden.filter((marker) => sources.includes(marker));
const status = missingRoutes.length === 0 && unknownApiRefs.length === 0 && missingState.length === 0 && noGoViolations.length === 0 && forbiddenFound.length === 0 ? 'PASS' : 'BLOCK';
console.log(JSON.stringify({
  status,
  created_by: 'POST-H-028-E',
  required_routes_total: requiredRoutes.length,
  missing_routes: missingRoutes,
  unknown_api_refs: unknownApiRefs,
  missing_state_contracts: missingState,
  no_go_violations: noGoViolations,
  forbidden_markers_found: forbiddenFound,
}, null, 2));
if (status !== 'PASS') {
  console.error('DEVPL WEB UI ROUTE ENFORCEMENT SMOKE TEST: BLOCK');
  process.exit(1);
}
console.log('DEVPL WEB UI ROUTE ENFORCEMENT SMOKE TEST: PASS');
