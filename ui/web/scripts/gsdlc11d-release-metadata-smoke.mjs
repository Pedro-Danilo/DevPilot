import fs from 'node:fs';
import path from 'node:path';
const root=process.cwd();
const checks=[];
function check(name,file,needles){const text=fs.readFileSync(path.join(root,file),'utf8');const ok=needles.every(n=>text.includes(n));checks.push({name,ok,file});if(!ok){console.error(`BLOCK ${name} ${file}`);process.exitCode=1}else console.log(`PASS ${name}`)}
check('route-registration','src/main.ts',["'/release/metadata'",'renderReleaseMetadataView']);
check('page-authority','src/pages/ReleaseMetadataView.ts',['proposal-only','owner/release-manager','annotated tag local']);
check('client-contract','src/api/client.ts',['releaseMetadataPrepare','releaseMetadataApprove','releaseMetadataTagExecute']);
check('types','src/api/types.ts',['ReleaseVersionDecision','ReleaseTagPlan','ReleaseApproval']);
check('no-publish-ui','src/pages/ReleaseMetadataView.ts',['push, publish and deploy remain disabled']);
check('exact-plan-ui','src/pages/ReleaseMetadataView.ts',['Crear TagPlan dry-run','Aprobar release']);
console.log(`${checks.filter(x=>x.ok).length}/${checks.length} PASS`);
