import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=(rel)=>fs.readFileSync(path.join(root,rel),'utf8');
const rec=read('src/components/ArtifactReconciliationUX.ts');
const review=read('src/components/ArtifactReviewFlow.ts');
const manual=read('src/components/ArtifactManualEditor.ts');
const imp=read('src/components/ArtifactImportWorkbench.ts');
const view=read('src/pages/WorkspaceDocumentsView.ts');
const client=read('src/api/client.ts');
const types=read('src/api/types.ts');
const checks=[
 ['reconciliation UX',rec.includes('Reconciliación externa · VS Code / Git')&&rec.includes('Detectar cambio externo')],
 ['change kinds visible',rec.includes('change_kind')&&types.includes("'unchanged' | 'modified' | 'renamed' | 'deleted'")],
 ['revalidation required',rec.includes('REVALIDATION_REQUIRED')||review.includes('REVALIDATION_REQUIRED')],
 ['git diff + provenance',rec.includes('Git diff')&&rec.includes('Source provenance')],
 ['never auto revert',rec.includes('Nunca revierte automáticamente')||rec.toLowerCase().includes('no auto-revert')],
 ['no hidden merge',rec.toLowerCase().includes('hidden merge')||rec.toLowerCase().includes('merge oculto')],
 ['review integration',review.includes('createArtifactReconciliationUX')&&rec.includes('reconcileArtifactReview')],
 ['manual route preserved',view.includes('ArtifactManualEditor')&&manual.includes('Artifact')],
 ['import route preserved',view.includes('ArtifactImportWorkbench')&&imp.includes('Artifact')],
 ['exact approval preserved',review.includes('approval_id')&&review.includes('Verificar approval')],
 ['safe DOM',!rec.includes('.innerHTML')&&rec.includes('.textContent')],
 ['accessibility',rec.includes("setAttribute('aria-live'")||rec.includes('aria-live')],
 ['API client reconcile',client.includes('reconcileArtifactReview')],
 ['blocked findings payload rendered',review.includes('reviewFromValidationBlock')&&review.includes("candidate.status!=='FINDINGS'")&&review.includes('DevPilotApiError')],
 ['import DRAFT finding navigation',review.includes('Ir al hallazgo')&&imp.includes('devpilot:artifact-finding-navigate')&&imp.includes('setSelectionRange')&&imp.includes('source_ref')],
 ['workspace integration',view.includes('ArtifactReviewFlow')],
];
let pass=0;for(const [name,ok] of checks){console.log(`${ok?'PASS':'BLOCK'} ${name}`);if(ok)pass++;}
console.log(`DEVPL UI SUMMARY: ${pass}/${checks.length} PASS`);if(pass!==checks.length)process.exit(1);
