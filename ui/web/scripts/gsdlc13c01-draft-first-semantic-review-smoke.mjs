import fs from 'node:fs';
const read=(p)=>fs.readFileSync(new URL(`../${p}`,import.meta.url),'utf8');
const view=read('src/pages/PreCodeWizardView.ts');
const types=read('src/api/types.ts');
const client=read('src/api/client.ts');
const styles=read('src/styles.css');
const required=[
  ['draft-first',view.includes('Generar propuesta con DevPilot')&&view.includes('Propuesta completa generada como DRAFT')],
  ['owner-edit',view.includes('Guardar revisión del Owner')&&view.includes('Editar propuesta antes de aprobar')],
  ['decision-inbox',view.includes('Decisiones pendientes')&&view.includes('Guardar decisiones y regenerar propuesta')&&view.includes('pre-code-decision-inbox')],
  ['semantic-detail-advanced',view.includes('Ver análisis de DevPilot')&&view.includes('No necesitas revisar esta estructura para completar el flujo normal.')],
  ['no-microconfirmation-gate',!view.includes('Confirmar base semántica y generar DRAFT')&&!view.includes('Añadir actor')&&!view.includes('Añadir capacidad')],
  ['diff-explainability',view.includes('source actual → DRAFT propuesto')&&view.includes('baseline vacío → DRAFT propuesto')],
  ['plan-invalidation-copy',view.includes('invalida este plan/diff')&&view.includes('plan anterior fue invalidado')],
  ['typed-required-stage',types.includes("required_stage?: 'product-vision' | 'scope' | 'requirements'")],
  ['typed-owner-edit-provenance',types.includes('owner_edited?: boolean')&&types.includes('owner_edited_content_sha256?: string')],
  ['semantic-payload',client.includes('semantic_model?: import(\'./types\').PreCodeSemanticModel | null')],
  ['no-inner-html',!view.includes('.innerHTML')],
  ['diff-viewport-bounded',styles.includes('.pre-code-plan__diff')&&styles.includes('white-space:pre-wrap')&&styles.includes('overflow-wrap:anywhere')&&styles.includes('.pre-code-stage, .pre-code-plan')],
];
const failed=required.filter(([,ok])=>!ok).map(([id])=>id);
if(failed.length){console.error(JSON.stringify({status:'BLOCK',failed},null,2));process.exit(2);}
console.log(JSON.stringify({status:'PASS',checks:required.length,contract:'draft-first + Decision Inbox',full_regression_runs:0},null,2));
