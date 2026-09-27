import fs from 'node:fs';

const view=fs.readFileSync(new URL('../src/pages/PreCodeWizardView.ts',import.meta.url),'utf8');
const types=fs.readFileSync(new URL('../src/api/types.ts',import.meta.url),'utf8');
const catalog=JSON.parse(fs.readFileSync(new URL('../../../.devpilot/gsdlc/pre_code_wizard_catalog.json',import.meta.url),'utf8'));
const advisor=fs.readFileSync(new URL('../../../src/devpilot_core/guided_sdlc/step_action_advisor.py',import.meta.url),'utf8');

const checks=[];
function check(name,condition){checks.push({name,pass:Boolean(condition)});if(!condition){console.error(`BLOCK ${name}`);process.exitCode=1;}else console.log(`PASS ${name}`);}
const rows=Object.fromEntries(catalog.stages.map(x=>[x.stage_id,x]));
for(const id of ['architecture','security','test-strategy','traceability']) check(`${id} DEVPL_MOCK`,rows[id]?.allowed_modes?.includes('DEVPL_MOCK'));
check('C02 label',view.includes('DevPilot · Diseño local + RAG / sin API'));
check('C02 route card',view.includes('DevPilot local + RAG'));
check('C02 RAG provenance',view.includes('RAG local ${rag?'));
check('No C01 regenerate leakage',view.includes('c01SemanticStage=stage.order<=3'));
check('Agent truth copy',view.includes('aún no son providers de primer DRAFT de Pre-code'));
check('Types RAG fields',types.includes('rag_context_pack_id?: string'));
check('Advisor no stale GSDLC06 copy',!advisor.includes('until GSDLC-06'));
check('Advisor no stale GSDLC07 copy',!advisor.includes('until GSDLC-07'));
if(process.exitCode) process.exit(process.exitCode);
console.log(`PASS — ${checks.length} C02 technical design UI contract checks.`);
