#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const webRoot = path.resolve(process.cwd());
const repoRoot = path.resolve(webRoot, '../..');
const read = (relative) => fs.readFileSync(path.join(webRoot, relative), 'utf8');
const readJson = (relative) => JSON.parse(read(relative));
const readRepoJson = (relative) => JSON.parse(fs.readFileSync(path.join(repoRoot, relative), 'utf8'));
const checks = [];
const check = (id, condition, detail) => checks.push({ id, status: condition ? 'PASS' : 'BLOCK', detail });

const main = read('src/main.ts');
const dashboard = read('src/pages/Dashboard.ts');
const reports = read('src/pages/ReportsView.ts');
const traces = read('src/pages/TracesView.ts');
const settings = read('src/pages/SettingsView.ts');
const gates = read('src/components/OperatorGatePanel.ts');
const client = read('src/api/client.ts');
const asyncUtils = read('src/utils/async.ts');
const approvals = read('src/pages/ApprovalCenterView.ts');
const dryRun = read('src/components/DryRunActionForm.ts');
const packageJson = readJson('package.json');
const registry = readRepoJson('.devpilot/interfaces/ui_route_contract_registry.json');

check('DASHBOARD_NO_EMBEDDED_DETAIL_VIEWS', !dashboard.includes('renderReportTraceView') && !dashboard.includes('renderApprovalCenterView') && !dashboard.includes('renderSettingsView'), 'Dashboard only renders summaries and route links');
check('DASHBOARD_BOUNDED_CONCURRENCY', dashboard.includes('runBounded') && dashboard.includes('tasks.map') && dashboard.includes('      2,'), 'Dashboard limits protected request fan-out to 2');
check('DASHBOARD_PROGRESSIVE_RESULTS', dashboard.includes('onResult') || dashboard.includes('(result) =>'), 'Dashboard redraws per completed task');
check('REPORTS_ROUTE_SPECIFIC', main.includes("renderReportsView") && reports.includes('ui.reports') && !reports.includes('listTraces'), 'Reports route does not fetch trace list');
check('TRACES_ROUTE_SPECIFIC', main.includes("renderTracesView") && traces.includes('ui.traces') && !traces.includes('listReports'), 'Traces route does not fetch report list');
check('SETTINGS_EXCLUSIVE_PHASE', settings.includes("type SettingsPhase = 'idle' | 'loading' | 'ready' | 'empty' | 'error'") && settings.includes('renderPhaseNotice'), 'Settings uses one explicit phase');
check('SETTINGS_BOUNDED_CONCURRENCY', settings.includes('runBounded') && settings.includes('], 2,'), 'Settings limits request fan-out to 2');
check('GATE_UNKNOWN_NOT_BLOCK', gates.includes("'UNKNOWN'") && gates.includes('este estado no equivale a BLOCK'), 'Missing snapshot is UNKNOWN');
check('SENSITIVE_CAPABILITY_DISABLED', gates.includes("'DISABLED BY POLICY'"), 'Disabled sensitive capability is not rendered as failure');
check('TIMEOUT_ENDPOINT_CONTEXT', client.includes('endpoint: path') && client.includes('action: \'retry\''), 'Timeout includes endpoint and retry guidance');
check('TIMEOUT_REMAINS_BOUNDED', client.includes('DEFAULT_REQUEST_TIMEOUT_MS = 8000') && client.includes('AbortController'), 'Default/NEG-08 timeout stays at 8 seconds');
check('EXPENSIVE_TIMEOUT_BOUNDED', client.includes('READINESS_REQUEST_TIMEOUT_MS = 30000') && client.includes('ACTION_DRY_RUN_TIMEOUT_MS = 60000') && client.includes('PROVIDER_PLAN_TIMEOUT_MS = 60000') && client.includes('PROTECTED_WARMUP_TIMEOUT_MS = 15000'), 'Expensive operations and warm-up use explicit bounded timeouts');
check('TRANSIENT_RETRY_BOUNDED', client.includes('TRANSIENT_NETWORK_RETRY_DELAYS_MS = [500, 1000]') && client.includes('isTransientNetworkError'), 'Only transient status 0 receives bounded retry');
check('DASHBOARD_PROTECTED_WARMUP', dashboard.includes('protectedWarmup') && dashboard.includes('Warm-up protegido') && dashboard.includes('state.snapshot = {}'), 'Dashboard warms protected API and clears stale state before fan-out');
check('ACTION_PENDING_FEEDBACK', settings.includes("providerPlanPhase = 'loading'") && approvals.includes('runPending') && dryRun.includes('Ejecutando…') && [settings, approvals, dryRun].every((source) => source.includes('aria-busy')), 'Provider/approval/dry-run actions expose pending feedback');
check('GENERIC_BOUNDED_RUNNER', asyncUtils.includes('runBounded') && asyncUtils.includes('concurrency = 2'), 'Generic dependency-free bounded runner exists');
check('ROUTE_REGISTRY_SEPARATED', registry.routes.find((r) => r.route_id === 'ui.reports')?.page_component === 'ReportsView' && registry.routes.find((r) => r.route_id === 'ui.traces')?.page_component === 'TracesView', 'Route registry uses distinct components');
check('PACKAGE_SCRIPT', packageJson.scripts['test:acceptance-corrective'] === 'node scripts/acceptance-corrective.mjs', 'Corrective npm script registered');
check('NO_SENSITIVE_ENABLEMENT', ![dashboard, reports, traces, settings, main].join('\n').includes('/patch/apply'), 'No destructive API route enabled');

const blockers = checks.filter((item) => item.status !== 'PASS');
console.log(JSON.stringify({
  schema_version: '1.0',
  micro_sprint: 'POST-H-EVAL-002-01-D',
  phase: 'ui-corrective/static',
  status: blockers.length ? 'BLOCK' : 'PASS',
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
    workspace_created: false,
    browser_retest_required: true,
  },
}, null, 2));
if (blockers.length) process.exit(1);
console.log('POST-H-EVAL-002-01-D UI CORRECTIVE BASELINE: PASS');
