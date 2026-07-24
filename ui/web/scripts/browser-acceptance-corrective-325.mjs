#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const webRoot = path.resolve(process.cwd());
const repoRoot = path.resolve(webRoot, '../..');
const read = (relative) => fs.readFileSync(path.join(webRoot, relative), 'utf8');
const readRepo = (relative) => fs.readFileSync(path.join(repoRoot, relative), 'utf8');
const checks = [];
const check = (id, pass, detail) => checks.push({ id, status: pass ? 'PASS' : 'BLOCK', detail });

const client = read('src/api/client.ts');
const dryRun = read('src/components/DryRunActionForm.ts');
const approvals = read('src/pages/ApprovalCenterView.ts');
const settings = read('src/pages/SettingsView.ts');
const service = readRepo('src/devpilot_core/application/settings_service.py');
const providers = readRepo('src/devpilot_core/modeling/providers.py');
const packageJson = JSON.parse(read('package.json'));

check('DEFAULT_TIMEOUT_PRESERVED', client.includes('DEFAULT_REQUEST_TIMEOUT_MS = 8000'), 'ordinary requests remain bounded to 8000 ms');
check('OPERATION_TIMEOUTS_EXPLICIT', ['READINESS_REQUEST_TIMEOUT_MS = 30000', 'PROVIDER_SETTINGS_READ_TIMEOUT_MS = 45000', 'ACTION_DRY_RUN_TIMEOUT_MS = 60000', 'PROVIDER_PLAN_TIMEOUT_MS = 60000'].every((marker) => client.includes(marker)), 'operation-specific budgets');
check('DRY_RUN_USES_SPECIFIC_BUDGET', client.includes("return this.post('/actions/dry-run', payload, {") && client.includes('timeoutMs: ACTION_DRY_RUN_TIMEOUT_MS'), 'dry-run budget');
check('PROVIDER_PLAN_USES_SPECIFIC_BUDGET', client.includes("return this.post('/settings/providers/plan', payload, {") && client.includes('timeoutMs: PROVIDER_PLAN_TIMEOUT_MS'), 'provider plan budget');
check('CLIENT_METADATA_VISIBLE', client.includes('client_request:') && client.includes('timeout_budget_ms') && client.includes('duration_ms'), 'client duration/budget metadata');
check('DRY_RUN_STATE_MACHINE', dryRun.includes("'idle' | 'loading' | 'pass' | 'block' | 'timeout' | 'error'") && dryRun.includes('No existe resultado PASS'), 'exclusive dry-run state');
check('DRY_RUN_NO_SYNTHETIC_PASS', !approvals.includes("{ dry_run: true, critical_actions_blocked: true }"), 'no synthetic dry-run response');
check('PROVIDER_PLAN_STATE_MACHINE', settings.includes("'idle' | 'loading' | 'pass' | 'block' | 'timeout' | 'error'") && settings.includes('No existe un plan válido'), 'exclusive provider plan state');
check('PROVIDER_PLAN_CLEARS_STALE_RESULT', settings.includes('state.providerPlan = undefined') && settings.includes("state.providerPlanPhase = 'loading'"), 'stale result cleared before retry');
check('APPROVAL_SHOW_EVIDENCE', approvals.includes('state.selected = await client.showApproval(created.approval_id)') && approvals.includes('DETAIL LOADED'), 'approval detail loaded explicitly');
check('SYNTHETIC_PROPOSAL_VALIDATED', service.includes('synthetic_payload') && service.includes('parse_provider_config_payload') && service.includes('validate_provider_configs(synthetic_configs'), 'backend validates proposed config');
check('NO_PROVIDER_WRITE', !service.includes('write_text(') && !service.includes('write_bytes('), 'provider plan remains plan-only');
check('PAYLOAD_PARSER_PRESENT', providers.includes('def parse_provider_config_payload'), 'in-memory parser');
check('PACKAGE_CONTRACT', packageJson.devpilot.browserAcceptanceCorrective325 === true && packageJson.devpilot.browserRetestRunId === 'PILOT-E2E-001-RUN-04', 'package metadata');

const blockers = checks.filter((item) => item.status === 'BLOCK');
console.log(JSON.stringify({
  schema_version: '1.0',
  patch: '324-to-325-browser-acceptance-corrective',
  decision: blockers.length ? 'BLOCK' : 'PASS',
  checks_total: checks.length,
  checks_passed: checks.length - blockers.length,
  blockers,
  checks,
  safety: {
    local_first: true,
    external_api_used: false,
    write_performed: false,
    closure_allowed: false,
    required_retest: 'PILOT-E2E-001-RUN-04',
  },
}, null, 2));
if (blockers.length) process.exit(1);
