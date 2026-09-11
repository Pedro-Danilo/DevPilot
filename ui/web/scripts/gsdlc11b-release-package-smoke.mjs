import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..');
const read=(rel)=>fs.readFileSync(path.join(root,rel),'utf8');
const main=read('src/main.ts'); const client=read('src/api/client.ts'); const page=read('src/pages/ReleasePackageView.ts'); const types=read('src/api/types.ts');
const checks=[
 [main.includes("path: '/release/package'") && main.includes("routeId: 'ui.release-package'") && main.includes("scope: 'project'"),'project-scoped route'],
 [main.includes('renderReleasePackageView'),'view wired'],
 [client.includes('releasePackagePlan') && client.includes('releasePackageExecute'),'typed API client'],
 [types.includes('ReleasePackagePlan') && types.includes('ReleasePackageResult'),'typed package contracts'],
 [page.includes('Preparar plan') && page.includes('Ejecutar paquete local'),'plan-before-execute UX'],
 [page.includes('SBOM') && page.includes('Local-only'),'SBOM/local-only disclosure'],
 [!page.includes('sessionStorage') && !page.includes('localStorage'),'browser storage not authority'],
 [page.includes('No publish') && page.toLowerCase().includes('nunca publica'),'no implicit publish UX'],
];
for(const [ok,label] of checks) console.log(`${ok?'PASS':'BLOCK'} - ${label}`);
if(checks.some(([ok])=>!ok)) process.exit(1);
console.log(`PASS - GSDLC-11-B Release Package UI smoke ${checks.length}/${checks.length}`);
