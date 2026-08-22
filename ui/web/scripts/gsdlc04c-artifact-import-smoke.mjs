import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (rel) => fs.readFileSync(path.join(root, rel), 'utf8');
const component = read('src/components/ArtifactImportWorkbench.ts');
const view = read('src/pages/WorkspaceDocumentsView.ts');
const client = read('src/api/client.ts');
const css = read('src/styles.css');
const checks = [
  ['PASTE mode', component.includes("['PASTE','Pegar texto']")],
  ['UPLOAD mode', component.includes("['UPLOAD','Upload local']")],
  ['IMPORT mode', component.includes("['IMPORT','Importar archivo externo']")],
  ['preview first', component.includes('Generar preview') && component.includes('Crear DRAFT')],
  ['original hash visible', component.includes('SHA original')],
  ['normalized hash visible', component.includes('SHA normalizado')],
  ['provenance visible', component.includes('Artifact provenance · DRAFT')],
  ['metadata no fetch copy', component.includes('URL/reference es metadata') && component.includes('nunca hace fetch')],
  ['client size bound', component.includes('MAX_IMPORT_BYTES = 1_048_576')],
  ['allowlisted file types', component.includes("input.accept='.md,.json")],
  ['safe DOM rendering', !component.includes('.innerHTML =') && !component.includes('.innerHTML=') && component.includes('textContent')],
  ['API client routes', client.includes('/workspace/artifact-imports/preview') && client.includes('/workspace/artifact-imports/persist') && client.includes('/workspace/artifact-imports/recent')],
  ['integrated in workspace view', view.includes('createArtifactImportWorkbench')],
  ['responsive styles', css.includes('.artifact-import-workbench') && css.includes('@media(max-width:720px)')],
  ['no direct fetch in component', !component.includes('fetch(')],
];
for (const [name, ok] of checks) console.log(`${ok ? 'PASS' : 'BLOCK'} ${name}`);
if (checks.some(([, ok]) => !ok)) process.exit(2);
console.log(`DEVPL UI SUMMARY: ${checks.length}/${checks.length} PASS`);
