import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const read = (path) => readFileSync(resolve(root, path), 'utf8');
const editor = read('src/components/ArtifactManualEditor.ts');
const planner = read('src/components/DocumentEditPlanner.ts');
const view = read('src/pages/WorkspaceDocumentsView.ts');
const client = read('src/api/client.ts');
const styles = read('src/styles.css');

const checks = [
  ['manual editor marker', editor.includes("dataset.gsdlc04b = 'artifact-manual-editor'")],
  ['1100ms bounded autosave', editor.includes('AUTOSAVE_DELAY_MS = 1100')],
  ['runtime draft save', editor.includes('saveArtifactDraft')],
  ['history recovery', editor.includes('recoverArtifactDraft') && editor.includes('Version history')],
  ['discard', editor.includes('discardArtifactDraft')],
  ['conflict state', editor.includes("'conflict'") && editor.includes('Lost update bloqueado')],
  ['safe preview no assignment', !/\.innerHTML\s*=/.test(editor) && editor.includes('textContent')],
  ['json hints', editor.includes('JSON inválido') && editor.includes('JSON válido')],
  ['planner governed handoff', planner.includes('setDraftContent') && planner.includes('sessionStorage no es autoridad para Markdown/JSON')],
  ['planner still UOC-005 apply', planner.includes('Aplicar cambio aprobado')],
  ['view integrates editor before planner', view.includes('createArtifactManualEditor') && view.includes('manualEditor, editPlanner')],
  ['client has five operations', ['artifactDraft(', 'artifactDraftHistory(', 'saveArtifactDraft(', 'discardArtifactDraft(', 'recoverArtifactDraft('].every((x) => client.includes(x))],
  ['source authority warning visible', editor.includes('source aprobado') && editor.includes('DRAFT no es evidence')],
  ['responsive styles present', styles.includes('.artifact-manual-editor-input') && styles.includes('.artifact-version-history')],
  ['no external networking added', !editor.includes('fetch(') && !editor.includes('WebSocket')],
];

const failed = checks.filter(([, ok]) => !ok);
for (const [name, ok] of checks) console.log(`${ok ? 'PASS' : 'BLOCK'}  ${name}`);
if (failed.length) {
  console.error(`GSDLC-04-B static browser smoke BLOCK: ${failed.length}/${checks.length} checks failed.`);
  process.exit(2);
}
console.log(`GSDLC-04-B static browser smoke PASS: ${checks.length}/${checks.length}.`);
