#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const webRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const repoRoot = resolve(webRoot, '../..');
const readWeb = (relative) => readFileSync(join(webRoot, relative), 'utf8');
const readRepoJson = (relative) => JSON.parse(readFileSync(join(repoRoot, relative), 'utf8'));

const main = readWeb('src/main.ts');
const client = readWeb('src/api/client.ts');
const packageJson = JSON.parse(readWeb('package.json'));
const registry = readRepoJson('.devpilot/interfaces/ui_route_contract_registry.json');

const expected = [
  ['ui.dashboard', '/', 'Dashboard'],
  ['ui.reports', '/reports', 'ReportsView'],
  ['ui.traces', '/traces', 'TracesView'],
  ['ui.approvals', '/approvals', 'ApprovalCenterView'],
  ['ui.settings', '/settings', 'SettingsView'],
];

const checks = [];
function add(id, pass, detail) {
  checks.push({ id, status: pass ? 'PASS' : 'BLOCK', detail });
}

for (const [routeId, path, component] of expected) {
  const contract = registry.routes.find((item) => item.route_id === routeId);
  add(`REGISTRY_${routeId}`, Boolean(contract && contract.path === path && contract.page_component === component), `${routeId} -> ${path} -> ${component}`);
  add(`RUNTIME_${routeId}`, main.includes(`path: '${path}'`) && main.includes(`routeId: '${routeId}'`), `${routeId} runtime dispatch`);
}

add('ROUTE_NAVIGATION_PRESENT', main.includes('renderPrimaryNavigation') && main.includes('aria-current'), 'route navigation and active state');
add('UNKNOWN_ROUTE_CONTROLLED', main.includes('renderNotFound') && main.includes('Ruta UI no registrada'), 'controlled 404 state');
add('REQUEST_TIMEOUT_BOUNDED', client.includes('AbortController') && client.includes('DEFAULT_REQUEST_TIMEOUT_MS = 8000') && client.includes("state: 'timeout'"), '8s default bounded timeout');
add('TOKEN_SESSION_ONLY', client.includes("sessionStorage") && !client.includes('localStorage'), 'token stored only in sessionStorage');
add('NO_TOKEN_IN_URL', !main.includes('?token=') && !client.includes('token='), 'no token query parameter');
add('PACKAGE_SCRIPT_REGISTERED', packageJson.scripts['test:acceptance-baseline'] === 'node scripts/acceptance-baseline.mjs', 'npm script registered');

const blocked = checks.filter((item) => item.status === 'BLOCK');
const payload = {
  schema_version: '1.0',
  micro_sprint: 'POST-H-EVAL-002-01-D',
  status: blocked.length === 0 ? 'PASS' : 'BLOCK',
  phase: 'acceptance-readiness/static',
  checks_total: checks.length,
  checks_passed: checks.length - blocked.length,
  blockers: blocked,
  checks,
  safety: {
    local_first: true,
    browser_acceptance_executed: false,
    workspace_created: false,
    network_used: false,
    external_api_used: false,
  },
};
console.log(JSON.stringify(payload, null, 2));
if (blocked.length) process.exit(1);
