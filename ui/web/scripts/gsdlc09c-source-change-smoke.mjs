import fs from 'node:fs';
const view=fs.readFileSync(new URL('../src/pages/StoryCodeWorkbenchView.ts',import.meta.url),'utf8');
const client=fs.readFileSync(new URL('../src/api/client.ts',import.meta.url),'utf8');
const checks=[
 ['approval-gated badge',view.includes('SOURCE WRITE · APPROVAL-GATED')],
 ['full diff',view.includes('data.fullDiff')||view.includes('dataset.fullDiff')],
 ['test impact',view.includes('dataset.testImpact')],
 ['immutable plan',view.includes('Crear SourceChangePlan')],
 ['dry-run',view.includes('Dry-run')],
 ['apply approval',view.includes('Solicitar approval owner')],
 ['separate rollback approval',view.includes('Solicitar approval de rollback')],
 ['no terminal',view.includes('SIN TERMINAL')],
 ['11 client routes',[
  '/story/code/change-plans', '/recheck', '/dry-run', '/approval-request', '/apply',
  '/story/code/change-executions/', '/rollback-approval-request', '/rollback', '/apply-manifest', '/rollback-evidence'
 ].every(x=>client.includes(x))],
];
const failed=checks.filter(([,ok])=>!ok);for(const [name,ok] of checks)console.log(`${ok?'PASS':'BLOCK'} ${name}`);if(failed.length)process.exit(2);console.log('PASS GSDLC-09-C UI static contract');
