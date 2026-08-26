import fs from 'node:fs';
const read=(p)=>fs.readFileSync(new URL(`../${p}`,import.meta.url),'utf8');
const view=read('src/pages/PreCodeWizardView.ts');
const main=read('src/main.ts');
const client=read('src/api/client.ts');
const types=read('src/api/types.ts');
const status=read('src/pages/ProjectStatusView.ts');
const advisor=read('src/components/StepActionAdvisor.ts');
const approvals=read('src/pages/ApprovalCenterView.ts');
const required=[
  ['route',main.includes("path: '/pre-code'")&&main.includes("ui.pre-code-wizard")],
  ['wizard-render',main.includes('renderPreCodeWizardView')],
  ['seven-stage-copy',view.includes('Product Vision → Scope → Requirements → Architecture → Security → Test Strategy → Traceability')],
  ['advisor',view.includes('renderStepActionAdvisor')],
  ['manual-import',view.includes('Modo de autoría')&&view.includes('Importar archivo local')],
  ['contextual-upload-import',view.includes("action.kind==='UPLOAD_IMPORT'")&&view.includes('file.click()')&&view.includes('La selección permanece dentro del wizard')&&advisor.includes('options.onAction?.(action) === true')],
  ['approval-rbac-403-copy',approvals.includes('DENY/BLOCK server-side confirmado (HTTP 403)')],
  ['plan-hash-diff',view.includes('Plan hash')&&view.includes('Diff SHA-256')&&view.includes('pre-code-plan__diff')],
  ['targeted-approval',view.includes('armApprovalCenterArtifactReviewHandoff')&&view.includes('handoff=artifact-review&approval_id=')],
  ['fail-closed',view.includes('El wizard falla cerrado')],
  ['session-preflight',view.includes('ensureLiveHumanSession')&&view.includes('client().authSession()')&&((view.match(/if\(!await ensureLiveHumanSession\(feedback\)\) return/g)||[]).length>=5)],
  ['session-vs-api-down',view.includes('la sesión humana local ya no es válida')&&view.includes('la API local responde, pero la sesión humana')&&view.includes('no repitas DRAFT, approval ni apply ya completados')],
  ['pre-code-ready',view.includes('PRE_CODE_READY')],
  ['api-client',client.includes('preCodeStatus')&&client.includes('preCodeDraft')&&client.includes('preCodeFreeze')],
  ['typed-contract',types.includes('interface PreCodeWizardStage')&&types.includes("format: 'unified'" )],
  ['project-status-cta',status.includes("wizardLink.href = '/pre-code'")],
  ['no-inner-html',!view.includes('.innerHTML')],
  ['no-inline-approval-decision',!view.includes('decideApproval')],
];
const failed=required.filter(([,ok])=>!ok).map(([id])=>id);
if(failed.length){console.error(JSON.stringify({status:'BLOCK',failed},null,2));process.exit(2);}
console.log(JSON.stringify({status:'PASS',checks:required.length,route:'/pre-code',authority:'server-side',full_regression_runs:0},null,2));
