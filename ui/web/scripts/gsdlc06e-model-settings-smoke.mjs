import { readFileSync } from 'node:fs';

const settings = readFileSync(new URL('../src/pages/SettingsView.ts', import.meta.url), 'utf8');
const shell = readFileSync(new URL('../src/components/AIControlCenterView.ts', import.meta.url), 'utf8');
const model = readFileSync(new URL('../src/components/ModelSettingsView.ts', import.meta.url), 'utf8');
const client = readFileSync(new URL('../src/api/client.ts', import.meta.url), 'utf8');

const checks = [
  ['AIControlCenterView shell', shell.includes('AI CONTROL CENTER') && shell.includes('Model Gateway')],
  ['Authority separation', shell.includes('Agent Runtime') && shell.includes('Skills / Tools') && shell.includes('ModelRouteDecision no concede ToolExecutionDecision')],
  ['Blocked and unknown visible', model.includes("normalized === 'blocked' || normalized === 'unknown'") && model.includes('Blocked/unknown nunca se ocultan')],
  ['Credential is masked/reference-only', model.includes('masked_display') && !model.includes('credential_reference?.raw_secret')],
  ['Controlled Model Gateway client', client.includes("'/settings/model-gateway/evaluate'") && settings.includes('evaluateModelGateway')],
  ['Settings composition', settings.includes('renderAIControlCenterShell') && settings.includes('renderModelSettingsView')],
  ['Disable/Revoke browser controls', model.includes('data-provider-disable') && model.includes('data-provider-revoke')],
  ['Kill-switch client methods', client.includes('disableExternalProvider') && client.includes('revokeExternalProvider')],
  ['Evaluation form state persists after redraw', settings.includes('modelEvalMode') && model.includes('evaluationMode') && model.includes('evaluationHardStop')],
  ['Expected hard-stop BLOCK rendered as successful guard', settings.includes('hard-stop demostrado') && model.includes('BLOCK esperado')],
  ['Provider action feedback is inline', model.includes('provider-action-feedback') && settings.includes('providerAction')],
  ['Runtime provider state is visible', model.includes('Runtime credential state') && model.includes('Last runtime action')],
  ['Hermetic evaluation semantics are explained', model.includes('Simulación hermética de routing') && model.includes('No genera contenido LLM')],
  ['MP-0E foundation provenance vertical', model.includes('data-multiprovider-foundation') && model.includes('Provider, candidate y provenance') && model.includes('SIN INFERENCIA')],
  ['MP-0E disabled routes have no execution CTA', model.includes('Una ruta disabled no ofrece CTA de ejecución') && model.includes('execution_enabled')],
  ['MP-0E ContextPack is distinct from Agentic RAG', model.includes('Grounding ≠ Agentic RAG') && model.includes('Agentic RAG')],
  ['MP-0E expert provenance details', model.includes('Expert details · hashes, provenance y receipt') && model.includes('receipt_sha256')],
];

let failed = 0;
for (const [name, ok] of checks) {
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}`);
  if (!ok) failed += 1;
}
console.log(`${checks.length - failed}/${checks.length} GSDLC-06-E model-settings static checks passed`);
if (failed) process.exit(1);
