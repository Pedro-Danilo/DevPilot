import fs from 'node:fs';

const read = (rel) => fs.readFileSync(new URL(`../${rel}`, import.meta.url), 'utf8');
const view = read('src/components/AgentEvalTraceView.ts');
const center = read('src/components/AIControlCenterView.ts');
const settings = read('src/pages/SettingsView.ts');
const client = read('src/api/client.ts');

const checks = [
  ['AgentEvalTraceView component exists', /AgentEvalTraceView|renderAgentEvalTraceView/.test(view)],
  ['agent/runtime/model route visible', /agent|runtime/i.test(view) && /provider|model/i.test(view) && /access-route|access route/i.test(view)],
  ['sources, tokens and cost visible', /sources|citations/i.test(view) && /tokens/i.test(view) && /cost/i.test(view)],
  ['ToolIntent separated from deterministic authority', /ToolIntent/.test(view) && /PolicyEngine|Policy/.test(view) && /ToolExecutionDecision/.test(view)],
  ['AI Control Center renders eval sub-view', /agentEvalHtml/.test(center) && /ToolExecutionDecision/.test(center)],
  ['Settings fetches and renders agent evals', /settingsAgentEvals/.test(settings) && /renderAgentEvalTraceView/.test(settings)],
  ['API client uses governed agent-evals route', /settingsAgentEvals/.test(client) && /\/settings\/agent-evals/.test(client)],
];

let failed = false;
for (const [label, ok] of checks) {
  if (!ok) {
    console.error(`BLOCK — ${label}`);
    failed = true;
  } else {
    console.log(`PASS — ${label}`);
  }
}
if (failed) process.exit(2);
console.log(`PASS — GSDLC-07-E AgentEvalTraceView static smoke ${checks.length}/${checks.length}.`);
