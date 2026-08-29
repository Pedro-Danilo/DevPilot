import { readFileSync } from 'node:fs';
const settings=readFileSync(new URL('../src/pages/SettingsView.ts', import.meta.url),'utf8');
const shell=readFileSync(new URL('../src/components/AIControlCenterView.ts', import.meta.url),'utf8');
const runtime=readFileSync(new URL('../src/components/AgentRuntimeView.ts', import.meta.url),'utf8');
const advisor=readFileSync(new URL('../src/components/StepActionAdvisor.ts', import.meta.url),'utf8');
const client=readFileSync(new URL('../src/api/client.ts', import.meta.url),'utf8');
const checks=[
 ['AgentRuntimeView present',runtime.includes('data-agent-runtime-view')&&runtime.includes('Roles contextuales y límites')],
 ['Eight-role descriptors rendered',runtime.includes('data-agent-role')&&runtime.includes('required_model_capabilities')],
 ['Limits visible',runtime.includes('max_steps')&&runtime.includes('wall_time_seconds')&&runtime.includes('max_cost_usd')],
 ['Authority separation visible',runtime.includes('ToolIntent')&&runtime.includes('PolicyEngine/RBAC/Approval')&&runtime.includes('Model route grants tool permission')],
 ['Settings endpoint used',client.includes("'/settings/agent-runtime'")&&settings.includes('settingsAgentRuntime')],
 ['AI Control Center composition',shell.includes('agentRuntimeHtml')&&settings.includes('renderAgentRuntimeView')],
 ['Advisor explains recommended agent',advisor.includes('Agente recomendado')&&advisor.includes('Por qué')&&advisor.includes('agent_descriptor')],
 ['No agent execution button added',!runtime.includes('Ejecutar agente')&&!runtime.includes('Run agent')],
];
let failed=0; for(const [n,ok] of checks){console.log(`${ok?'PASS':'FAIL'} ${n}`); if(!ok) failed++;} console.log(`${checks.length-failed}/${checks.length} GSDLC-07-A static UI checks passed`); if(failed)process.exit(1);
