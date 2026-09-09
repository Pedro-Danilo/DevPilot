import fs from 'node:fs';
const view=fs.readFileSync(new URL('../src/pages/StoryCodeWorkbenchView.ts',import.meta.url),'utf8');
const client=fs.readFileSync(new URL('../src/api/client.ts',import.meta.url),'utf8');
const required=['Validar story','StoryTestPlan','Required tests','Recommended tests','unknown impact','SENSITIVE','informative only','execution_authorized'];
const api=['storyTestPlanCreate','storyTestPlanDecision','/test-plan','/test-plans/'];
const missing=[...required.filter(x=>!view.includes(x)),...api.filter(x=>!client.includes(x))];
if(missing.length){console.error('BLOCK - GSDLC-10-A UI contract missing:',missing.join(', '));process.exit(2);}
if(view.toLowerCase().includes('free-form test command')){console.error('BLOCK - free-form test command surface detected');process.exit(2);}
console.log('PASS - GSDLC-10-A StoryTestPlan UI contract: Validate/TestImpact/review visible; no free-form test execution.');
