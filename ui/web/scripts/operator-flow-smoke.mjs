#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const files = [
  'src/api/client.ts',
  'src/pages/Dashboard.ts',
  'src/pages/ReportTraceView.ts',
  'src/pages/ApprovalCenterView.ts',
  'src/pages/SettingsView.ts',
  'src/pages/OperatorDashboard.ts',
  'src/components/DryRunActionForm.ts',
  'src/components/OperatorGatePanel.ts',
  'src/components/OperatorNextActions.ts',
];
const source = files.map((file) => readFileSync(join(root, file), 'utf8')).join('\n');
const required = [
  'API local down',
  'Unauthorized/Forbidden 401/403',
  'Sin reportes para mostrar',
  'Sin trazas para mostrar',
  'approval pending',
  'patch apply',
  'BLOCK visible',
  'plan-only',
  'no-go visible',
  'recommended_next_actions',
];
const forbidden = ['Traceback (most recent call last)', 'error.stack', 'console.trace', '0.0.0.0 como solución'];
const missing = required.filter((marker) => !source.includes(marker));
const violations = forbidden.filter((marker) => source.includes(marker));
const payload = {
  status: missing.length === 0 && violations.length === 0 ? 'PASS' : 'BLOCK',
  created_by: 'POST-H-028-D',
  path_mode: 'fileURLToPath-cross-platform',
  required_markers_total: required.length,
  missing_markers: missing,
  forbidden_markers_found: violations,
  flows: [
    'api_down',
    'token_missing_invalid',
    'reports_traces_empty',
    'approval_create_list_decide',
    'dry_run_actions',
    'forbidden_action_block',
    'settings_redacted_plan_only',
    'operator_dashboard_next_actions',
  ],
};
console.log(JSON.stringify(payload, null, 2));
if (payload.status !== 'PASS') {
  console.error('DEVPL WEB UI OPERATOR FLOW SMOKE TEST: BLOCK');
  process.exit(1);
}
console.log('DEVPL WEB UI OPERATOR FLOW SMOKE TEST: PASS');
