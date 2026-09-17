import fs from 'node:fs';
const read=(p)=>fs.readFileSync(new URL('../'+p,import.meta.url),'utf8');
const files={
  home:read('src/components/ProjectHomeEntryPanel.ts'),
  entry:read('src/pages/ProjectEntryDryRunView.ts'),
  status:read('src/pages/ProjectStatusView.ts'),
  pre:read('src/pages/PreCodeWizardView.ts'),
  docs:read('src/pages/WorkspaceDocumentsView.ts'),
  planning:read('src/pages/RoadmapWorkbenchView.ts'),
  guide:read('src/components/CriticalPathGuidance.ts'),
  css:read('src/styles.css'),
  main:read('src/main.ts'),
};
const failures=[]; const check=(name,ok)=>{if(!ok) failures.push(name);};
check('common-guidance-component',files.guide.includes('renderCriticalPathGuidance')&&files.guide.includes('critical-path-guidance__steps'));
check('home-primary-create',files.home.includes('project-home-card--primary')&&files.home.includes('Empezar proyecto'));
check('home-resume-server-active',files.home.includes('/project/status?recover_project_context=server-active'));
check('entry-governed-sequence',files.entry.includes("title:'Revisa primero; muta después'")&&files.entry.includes("label:'Dry-run'")&&files.entry.includes("label:'Approval'"));
check('entry-effect-copy',files.entry.includes('Qué puede cambiar esta operación'));
check('status-center-guidance',files.status.includes("eyebrow: 'Centro operacional'")&&files.status.includes('Tu recorrido hasta Planning'));
check('status-technical-disclosure',files.status.includes('Ver razón técnica'));
check('precode-guided-progress',files.pre.includes("eyebrow:'Pre-code · 7 etapas'")&&files.pre.includes('draft → validar/diff → approval → apply → freeze'));
check('documents-entry-guidance',files.docs.includes("eyebrow: 'Documentos del proyecto'")&&files.docs.includes('AI Assist nunca auto-aprueba'));
check('planning-hierarchy',files.planning.includes("eyebrow:'Planning'")&&files.planning.includes("label:'Roadmap'")&&files.planning.includes("label:'Backlog'")&&files.planning.includes("label:'Sprint'"));
check('planning-json-progressive-disclosure',files.planning.includes('planning-json-disclosure')&&files.planning.includes('Editar contenido técnico JSON'));
check('responsive-critical-path',files.css.includes('.critical-path-guidance__steps')&&files.css.includes('@media (max-width: 720px)'));
check('44px-target',files.css.includes('var(--dp-control-min-target)'));
check('route-contract-preserved',['/project/status','/pre-code','/planning/roadmap','/workspace/documents'].every((route)=>files.main.includes(route)));
check('no-framework-migration',!files.main.includes('react-router')&&!files.main.includes('vue-router'));
console.log(JSON.stringify({schema_id:'devpilot.ux_p0_c.critical_path_smoke.v1',status:failures.length?'BLOCK':'PASS',checks_total:15,failures},null,2));
process.exit(failures.length?2:0);
