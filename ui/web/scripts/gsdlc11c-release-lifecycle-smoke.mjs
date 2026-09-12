import fs from 'node:fs'; import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..'); const read=(r)=>fs.readFileSync(path.join(root,r),'utf8');
const main=read('src/main.ts'), client=read('src/api/client.ts'), page=read('src/pages/ReleaseLifecycleView.ts'), types=read('src/api/types.ts');
const checks=[
 [main.includes("path: '/release/lifecycle'")&&main.includes("routeId: 'ui.release-lifecycle'")&&main.includes("scope: 'project'"),'project-scoped lifecycle route'],
 [main.includes('renderReleaseLifecycleView'),'view wired'],
 [client.includes('releaseLifecycleInstallPlan')&&client.includes('releaseLifecycleRollbackExecute'),'typed lifecycle client'],
 [types.includes('ReleaseLifecyclePlan')&&types.includes('ReleaseLifecycleStatus'),'typed lifecycle contracts'],
 [page.includes('Plan clean install')&&page.includes('Plan upgrade + backup')&&page.includes('Plan rollback'),'plan-before-execute UX'],
 [page.includes('backup-before-upgrade')&&page.includes('rollback verificado'),'backup/rollback disclosure'],
 [page.includes('Local-only')&&page.includes('sandbox-only'),'local sandbox authority'],
 [!page.includes('sessionStorage')&&!page.includes('localStorage'),'browser storage not authority'],
];
for(const [ok,label] of checks) console.log(`${ok?'PASS':'BLOCK'} - ${label}`); if(checks.some(([ok])=>!ok)) process.exit(1); console.log(`PASS - GSDLC-11-C Release Lifecycle UI smoke ${checks.length}/${checks.length}`);
