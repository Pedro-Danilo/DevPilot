import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.cwd());
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

const packageJson = JSON.parse(read('package.json'));
const client = read('src/api/client.ts');
const dashboard = read('src/pages/Dashboard.ts');
const reportTraceView = read('src/pages/ReportTraceView.ts');
const approvalCenterView = read('src/pages/ApprovalCenterView.ts');
const dryRunActionForm = read('src/components/DryRunActionForm.ts');
const findingTable = read('src/components/FindingTable.ts');
const statusCard = read('src/components/StatusCard.ts');
const filesToScan = [client, dashboard, statusCard, reportTraceView, findingTable, approvalCenterView, dryRunActionForm, read('src/main.ts')];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

assert(packageJson.devpilot.sprint === 'FUNC-SPRINT-71', 'package.json debe declarar FUNC-SPRINT-71');
assert(packageJson.devpilot.apiOnly === true, 'La UI debe ser API-only');
assert(packageJson.devpilot.dryRunOnly === true, 'La UI debe declarar dry-run only');
assert(packageJson.scripts.test === 'node scripts/smoke-test.mjs', 'npm test debe ser local y reproducible');

for (const source of filesToScan) {
  assert(!source.includes('devpilot_core'), 'La UI no debe importar Python/core');
  assert(!source.includes('child_process'), 'La UI no debe ejecutar procesos locales');
  assert(!source.includes('outputs/'), 'La UI no debe leer outputs directamente');
}

for (const expectedPath of ['/workspace/status', '/validation/readiness', '/standards/status', '/miasi/status', '/reports', '/traces', '/metrics/summary', '/approvals', '/actions/dry-run']) {
  assert(client.includes(expectedPath), `El cliente API debe consumir ${expectedPath}`);
}

assert(client.includes('X-DevPilot-Token'), 'El cliente debe enviar token local por header');
assert(statusCard.includes('PASS') && statusCard.includes('WARN') && statusCard.includes('BLOCK'), 'La UI debe traducir estados PASS/WARN/BLOCK');
assert(reportTraceView.includes('Report Viewer') && reportTraceView.includes('Trace Viewer'), 'La UI debe incluir Report Viewer y Trace Viewer');
assert(reportTraceView.includes('Sin trazas para mostrar'), 'Trace Viewer debe manejar trazas vacías');
assert(approvalCenterView.includes('Approval Center') && approvalCenterView.includes('Action Launcher'), 'La UI debe incluir Approval Center y Action Launcher');
assert(dryRunActionForm.includes('Solo acciones read-only/dry-run'), 'El formulario debe declarar dry-run seguro');
assert(!client.includes('/patch/apply'), 'La UI no debe invocar acciones destructivas');
assert(!client.includes('/rollback/execute'), 'La UI no debe invocar rollback execute');
assert(!client.includes('/git/push'), 'La UI no debe invocar git push');

console.log('DEVPL WEB UI SMOKE TEST: PASS');
