import { readFileSync } from 'node:fs';
const settings=readFileSync(new URL('../src/pages/SettingsView.ts', import.meta.url),'utf8');
const shell=readFileSync(new URL('../src/components/AIControlCenterView.ts', import.meta.url),'utf8');
const view=readFileSync(new URL('../src/components/RagProvenanceView.ts', import.meta.url),'utf8');
const client=readFileSync(new URL('../src/api/client.ts', import.meta.url),'utf8');
const checks=[
 ['Provenance panel present',view.includes('data-rag-provenance-view')&&view.includes('ContextPack v2')],
 ['Before/after selection visible',view.includes('Antes del presupuesto')&&view.includes('Pack sellado')],
 ['Source provenance visible',view.includes('content_sha256')&&view.includes('citation_ref')&&view.includes('trust_tag')],
 ['Freshness and budget visible',view.includes('freshness')&&view.includes('selected_tokens')&&view.includes('max_input_tokens')],
 ['No execution claim',view.includes('no ejecuta agentes ni APIs externas')],
 ['RAG settings endpoint used',client.includes('/settings/rag-context')&&settings.includes('settingsRagContext')],
 ['AI Control Center composition',shell.includes('ragProvenanceHtml')&&settings.includes('renderRagProvenanceView')],
 ['No external API/embedding control added',!view.includes('Enable external API')&&!view.includes('Enable embeddings')],
];
let failed=0; for(const [n,ok] of checks){console.log(`${ok?'PASS':'FAIL'} ${n}`); if(!ok) failed++;} console.log(`${checks.length-failed}/${checks.length} GSDLC-07-B static UI checks passed`); if(failed)process.exit(1);
