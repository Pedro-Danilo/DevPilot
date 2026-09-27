import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');
const view = read('ui/web/src/pages/PreCodeWizardView.ts');
const client = read('ui/web/src/api/client.ts');
const types = read('ui/web/src/api/types.ts');
const checks = [
  ['ADR gate UI', view.includes("data.architectureAdrGate") || view.includes("dataset.architectureAdrGate")],
  ['decision summary', view.includes('Decisiones incluidas en Architecture')],
  ['ContextPack label', view.includes('DevPilot local · grounding ContextPack')],
  ['prepare API', client.includes('/guided-sdlc/pre-code/architecture-adrs/prepare')],
  ['approval API', client.includes('/guided-sdlc/pre-code/architecture-adrs/approval-request')],
  ['apply API', client.includes('/guided-sdlc/pre-code/architecture-adrs/apply')],
  ['projection type', types.includes('ArchitectureAdrBundleProjection')],
];
const failed = checks.filter(([, ok]) => !ok);
if (failed.length) {
  console.error(JSON.stringify({status:'BLOCK', checks:Object.fromEntries(checks)}, null, 2));
  process.exit(2);
}
console.log(JSON.stringify({status:'PASS', checks:Object.fromEntries(checks)}, null, 2));
