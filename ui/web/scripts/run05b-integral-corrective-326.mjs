#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(scriptDirectory, '..');
const read = (relative) => fs.readFileSync(path.join(webRoot, relative), 'utf8');
const checks = [];
const check = (id, pass, detail) => checks.push({ id, status: pass ? 'PASS' : 'BLOCK', detail });

const dashboard = read('src/pages/Dashboard.ts');
const approvals = read('src/pages/ApprovalCenterView.ts');
const settings = read('src/pages/SettingsView.ts');
const badges = read('src/components/ContractBadges.ts');
const packageJson = JSON.parse(read('package.json'));

const healthIndex = dashboard.indexOf('await client.health()');
const warmupIndex = dashboard.indexOf('await client.protectedWarmup()');
check('HEALTH_CONSUMED_BY_DASHBOARD', healthIndex >= 0, 'client.health() must have a real UI consumer');
check('HEALTH_PRECEDES_PROTECTED_FANOUT', healthIndex >= 0 && warmupIndex > healthIndex, 'health preflight must precede protected warm-up');
check('HEALTH_VISIBLE', dashboard.includes("panel.dataset.apiOperation = 'api.health'") && dashboard.includes('Preflight Health'), 'health status and duration are visible');
check('SIX_CONTRACTUAL_OPERATIONS_VISIBLE', dashboard.includes('Operaciones contractuales:') && dashboard.includes('state.total + 1'), 'health plus five protected data operations');
check('HEALTH_FAILURE_STOPS_FANOUT', dashboard.includes('El fan-out autenticado no se ejecutó'), 'failed health cannot produce a synthetic operational dashboard');

check('APPROVAL_BLOCK_CONDITIONAL', approvals.includes("if (state.actionOutcome.phase === 'block')") && !approvals.includes("section.append(renderUiStateNotice('block', 'POST-H-028-D ui.approvals block state: acciones críticas"), 'BLOCK notice depends on an actual blocked outcome');
check('APPROVAL_PENDING_CONDITIONAL', approvals.includes("approvalItems(state).some((approval) => approval.status === 'requested')"), 'pending notice depends on requested records');
check('APPROVAL_INITIAL_IS_NOT_EMPTY', approvals.includes('Consulta inicial pendiente. Este estado no acredita una lista vacía.'), 'unqueried state is pending');

check('SETTINGS_VISUAL_REDACTION', settings.includes('redactSecrets(') && settings.includes('JSON.stringify(redactSecrets('), 'secret-like fields are fully redacted before visual rendering');
check('STATE_NOTICES_ACCESSIBLE', badges.includes("setAttribute('role'") && badges.includes("setAttribute('aria-live'") && badges.includes("'pending'"), 'state notices have role, live region and pending semantics');

check('PACKAGE_VERSION', packageJson.version === '0.6.8-post-h-eval-002-01-d-run05b-integral-corrective', '326 web package version');
check('PACKAGE_RUN_ID', packageJson.devpilot.browserRetestRunId === 'PILOT-E2E-001-RUN-05B-RERUN-03', 'fresh authoritative rerun required');
check('PACKAGE_CONTRACT', packageJson.devpilot.run05bIntegralCorrective326 === true && packageJson.devpilot.dashboardContractualOperations === 6, 'integral corrective metadata');

const blockers = checks.filter((item) => item.status === 'BLOCK');
console.log(JSON.stringify({
  schema_version: '1.0',
  patch: '325-to-326-run05b-integral-corrective',
  decision: blockers.length ? 'BLOCK' : 'PASS',
  checks_total: checks.length,
  checks_passed: checks.length - blockers.length,
  blockers,
  checks,
  safety: {
    local_first: true,
    external_api_used: false,
    remote_execution_enabled: false,
    connector_write_enabled: false,
    plugin_execution_enabled: false,
    closure_allowed: false,
    required_retest: 'PILOT-E2E-001-RUN-05B-RERUN-03',
  },
}, null, 2));
if (blockers.length) process.exit(1);
