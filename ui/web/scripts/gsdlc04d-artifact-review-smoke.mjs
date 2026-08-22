import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=(rel)=>fs.readFileSync(path.join(root,rel),'utf8');
const review=read('src/components/ArtifactReviewFlow.ts'); const editor=read('src/components/ArtifactManualEditor.ts'); const view=read('src/pages/WorkspaceDocumentsView.ts'); const client=read('src/api/client.ts'); const main=read('src/main.ts');
const checks=[
 ['review flow',review.includes('Artifact Review · validate, approve, apply & freeze')],
 ['import + manual',review.includes('startArtifactImportReview')&&review.includes('startArtifactDocumentReview')],
 ['findings navigation',review.includes('Ir al hallazgo')&&editor.includes('devpilot:artifact-finding-navigate')],
 ['immutable plan diff',review.includes('Plan hash')&&review.includes('artifact-review-diff')],
 ['targeted approval',review.includes('handoff=artifact-review')&&main.includes('artifact-review')],
 ['cross-tab approval handoff',review.includes('armApprovalCenterArtifactReviewHandoff')&&client.includes('APPROVAL_CENTER_ARTIFACT_REVIEW_HANDOFF_KEY')&&client.includes("handoff_kind: 'artifact-review'")&&main.includes('readApprovalCenterArtifactReviewHandoff')&&view.includes('session: AuthSessionContext')],
 ['no direct approval authority',!review.includes('decideApproval')&&!review.includes('approveApproval')],
 ['atomic apply via existing client',review.includes('applyWorkspaceEdit')],
 ['server-authoritative actor transport',!review.includes("actor:''")&&client.includes('serverAuthoritativePayload')&&client.includes('actor?: string')],
 ['freeze',review.includes('freezeArtifactReview')],
 ['safe DOM',!review.includes('.innerHTML')&&review.includes('.textContent')],
 ['API client review routes',client.includes('startArtifactImportReview')&&client.includes('freezeArtifactReview')&&client.includes('reconcileArtifactReview')],
 ['workspace integration',view.includes('ArtifactReviewFlow')&&view.includes('setDocument')&&view.includes('setImport')],
];
let pass=0;for(const [name,ok] of checks){console.log(`${ok?'PASS':'BLOCK'} ${name}`);if(ok)pass++;}
console.log(`DEVPL UI SUMMARY: ${pass}/${checks.length} PASS`);if(pass!==checks.length)process.exit(1);
