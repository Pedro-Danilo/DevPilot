import fs from 'node:fs';
const files = {
  view: 'src/components/SkillToolPolicyView.ts', settings: 'src/pages/SettingsView.ts', client: 'src/api/client.ts', types: 'src/api/types.ts', shell: 'src/components/AIControlCenterView.ts'
};
const text = Object.fromEntries(Object.entries(files).map(([k,p]) => [k, fs.readFileSync(new URL(`../${p}`, import.meta.url), 'utf8')]));
const checks = [
  ['SkillToolPolicyView exists', text.view.includes('data-skill-tool-policy-view')],
  ['ToolIntent/ToolExecutionDecision visible', text.view.includes('ToolIntent') && text.view.includes('ToolExecutionDecision')],
  ['filesystem.delete BLOCK visible', text.view.includes('filesystem.delete') && text.view.includes('tool_executed=false')],
  ['kill/cancel controls visible', text.view.includes('agent-exec-kill') && text.view.includes('agent-exec-cancel')],
  ['handoff checkpoint visible', text.view.includes('human checkpoint') && text.view.includes('scope inheritance')],
  ['Settings loads agent execution', text.settings.includes('settingsAgentExecution') && text.settings.includes('renderSkillToolPolicyView')],
  ['API client bounded controls', text.client.includes('submitAgentToolIntent') && text.client.includes('controlAgentExecution')],
  ['AI Control Center includes skills view', text.shell.includes('skillsToolsHtml')],
];
let fail=0; for (const [name,ok] of checks) { console.log(`${ok?'PASS':'BLOCK'} — ${name}`); if(!ok) fail++; }
if(fail) process.exit(2); console.log(`PASS — GSDLC-07-D SkillToolPolicyView static smoke ${checks.length}/${checks.length}`);
