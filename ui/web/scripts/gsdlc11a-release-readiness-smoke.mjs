import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const read = (rel) => fs.readFileSync(path.join(root, rel), 'utf8');
const main = read('src/main.ts');
const client = read('src/api/client.ts');
const page = read('src/pages/ReleaseReadinessView.ts');
const types = read('src/api/types.ts');
const checks = [
  [main.includes("path: '/release/readiness'") && main.includes("routeId: 'ui.release-readiness'") && main.includes("scope: 'project'"), 'project-scoped route'],
  [main.includes('renderReleaseReadinessView'), 'view wired'],
  [client.includes('async releaseReadiness()') && client.includes("'/release/readiness'"), 'typed API client'],
  [types.includes("'RELEASE_READY' | 'BLOCKED' | 'UNKNOWN'"), 'typed states'],
  [page.includes('readiness NO equivale a aprobación') && page.toLowerCase().includes('modelos/agentes'), 'approval separation'],
  [page.includes('DevPilot falla cerrado'), 'fail-closed UI'],
  [!page.includes('sessionStorage') && !page.includes('localStorage'), 'browser storage not authority'],
];
const failed = checks.filter(([ok]) => !ok);
for (const [ok, label] of checks) console.log(`${ok ? 'PASS' : 'BLOCK'} - ${label}`);
if (failed.length) process.exit(1);
console.log(`PASS - GSDLC-11-A Release Readiness UI smoke ${checks.length}/${checks.length}`);
