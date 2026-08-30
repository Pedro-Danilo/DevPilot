import fs from 'node:fs';
const files = {
  panel: 'src/components/ArtifactAIPanel.ts',
  view: 'src/pages/WorkspaceDocumentsView.ts',
  editor: 'src/components/ArtifactManualEditor.ts',
  client: 'src/api/client.ts',
  types: 'src/api/types.ts',
};
const text = Object.fromEntries(Object.entries(files).map(([k,p]) => [k, fs.readFileSync(new URL(`../${p}`, import.meta.url), 'utf8')]));
const checks = [
  ['panel mounted', text.view.includes('createArtifactAIPanel') && text.view.includes('manualEditor, editPlanner, aiPanel')],
  ['plan before run', text.panel.includes('1 · Preparar PLAN') && text.panel.includes('2 · RUN hermético')],
  ['untrusted/draft boundary', text.panel.includes('UNTRUSTED') && text.panel.includes('DRAFT ONLY') && text.panel.includes('APPROVED/FROZEN')],
  ['human decisions', ['ACCEPT','REJECT','MODIFY'].every(x => text.panel.includes(x))],
  ['diff review', text.panel.includes('artifact-ai-diff') && text.panel.includes('Revise el diff completo')],
  ['pre-run route/context/cost', ['Agent role','Model','Provider','Access route','Context','Estimate','Limits'].every(x => text.panel.includes(x))],
  ['api client typed operations', ['planArtifactAssist','runArtifactAssist','decideArtifactAssist','artifactAssistProposal'].every(x => text.client.includes(x))],
  ['history provenance', text.editor.includes('revision.agent_provenance') && text.types.includes('AgentProvenanceRecord')],
];
const failed = checks.filter(([,ok]) => !ok);
for (const [name,ok] of checks) console.log(`${ok ? 'PASS' : 'BLOCK'} — ${name}`);
if (failed.length) process.exit(2);
console.log(`PASS — GSDLC-07-C Artifact AI static UI: ${checks.length}/${checks.length}`);
