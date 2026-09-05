import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..','..','..');
const read=(rel)=>fs.readFileSync(path.join(root,rel),'utf8');
const json=(rel)=>JSON.parse(read(rel));
const assert=(condition,message)=>{if(!condition)throw new Error(message);};
const main=read('ui/web/src/main.ts'); const view=read('ui/web/src/pages/RoadmapWorkbenchView.ts'); const client=read('ui/web/src/api/client.ts'); const css=read('ui/web/src/styles.css')+read('ui/web/src/planning.css');
const api=json('.devpilot/interfaces/api_route_contract_registry.json'); const ui=json('.devpilot/interfaces/ui_route_contract_registry.json'); const rbac=json('.devpilot/identity/server_rbac_policy_catalog.json'); const pkg=json('ui/web/package.json');
const apiIds=['api.planning-roadmap.status','api.planning-roadmap.propose','api.planning-roadmap.review','api.planning-roadmap.approve','api.planning-roadmap.freeze'];
assert(main.includes("'/planning/roadmap'")&&main.includes('renderRoadmapWorkbenchView'),'planning route must be wired');
for(const token of ['MANUAL','IMPORT','AGENT','Guardar DRAFT','Validar / Review','Approve humano','Freeze revisionado','coverage','Provenance'])assert(view.includes(token),`RoadmapWorkbenchView missing ${token}`);
assert(!view.includes('innerHTML'),'RoadmapWorkbenchView must use safe DOM APIs'); assert(!view.includes('fetch('),'RoadmapWorkbenchView must use DevPilotApiClient');
for(const path of ['/planning/roadmap','/planning/roadmap/proposals','/planning/roadmap/review','/planning/roadmap/approve','/planning/roadmap/freeze'])assert(client.includes(path),`client missing ${path}`);
const uiRoute=ui.routes.find(x=>x.route_id==='ui.planning-roadmap'); assert(uiRoute?.path==='/planning/roadmap','UI registry route missing'); for(const id of apiIds)assert(uiRoute.allowed_api_routes.includes(id),`UI route missing ${id}`);
for(const id of apiIds){const route=api.routes.find(x=>x.route_id===id); assert(route,'API registry missing '+id); assert(route.external_api_allowed===false&&route.source_mutation_allowed===false,'route must remain local/source-safe '+id); const pol=rbac.route_policies.find(x=>x.route_id===id);assert(pol?.human_session_required===true&&pol?.legacy_token_allowed===false,'RBAC human-session required '+id);}
assert(pkg.devpilot.gsdlc08bAgentAutoApproval===false,'agent auto approval must be false');assert(pkg.devpilot.gsdlc08bFullRegressionRuns===0,'B cannot consume full');assert(css.includes('.roadmap-workbench__content')&&css.includes('@media(max-width:900px)'),'responsive CSS required');
console.log(JSON.stringify({status:'PASS',check:'DEVPL-GSDLC-08-B Roadmap Workbench static browser smoke',api_routes:5,authoring_modes:3,full_regression_runs:0},null,2));
