// UI contract: ui.workspace-documents — UOC-004 planning + UOC-005 governed apply/rollback.
import { DevPilotApiClient } from '../api/client';
import type { WorkspaceDocumentResource, WorkspaceEditApprovalRecord, WorkspaceEditExecutionRecord, WorkspaceEditPlan, WorkspaceEditPlanResponseData } from '../api/types';
import { renderUiStateNotice } from './ContractBadges';

const EDITABLE_EXTENSIONS = new Set(['.md', '.json', '.yaml', '.yml']);
const MAX_DRAFT_BYTES = 262144;
const ACTOR = 'local-owner';
const EXECUTION_QUERY_PARAM = 'execution';
const EXECUTION_STORAGE_PREFIX = 'devpilot:uoc005:execution:';

interface Options {
  tokenProvider: () => string;
  document?: WorkspaceDocumentResource;
  onMutationComplete?: () => Promise<void> | void;
}

export function createDocumentEditPlanner(options: Options): HTMLElement {
  const root = document.createElement('section');
  root.className = 'panel document-edit-planner';
  root.dataset.uoc004EditPlanner = 'true';
  root.dataset.uoc005EditExecution = 'true';
  let currentDocument: WorkspaceDocumentResource | undefined = options.document;
  let draft = '';
  let status = '';
  let error = '';
  let plan: WorkspaceEditPlan | undefined;
  let applyApproval: WorkspaceEditApprovalRecord | undefined;
  let rollbackApproval: WorkspaceEditApprovalRecord | undefined;
  let execution: WorkspaceEditExecutionRecord | undefined;
  let approvalReason = 'Aplicar el plan revisado y validado desde Workspace Documents.';
  let rollbackReason = 'Restaurar el documento al hash pre-apply antes de Git stage/commit.';
  let busy = false;
  let exportFeedback = '';
  let recoveryInFlight = false;
  let lastRecoveryAttempt = '';
  const deepLinkedExecutionId = new URLSearchParams(globalThis.location.search).get(EXECUTION_QUERY_PARAM) ?? '';

  function storageKey(document: WorkspaceDocumentResource): string {
    return `devpilot:uoc004:draft:${document.document_id ?? document.node_id}:${document.sha256 ?? 'unknown'}`;
  }

  function executionStorageKey(documentId: string): string {
    return `${EXECUTION_STORAGE_PREFIX}${documentId}`;
  }

  function rememberExecution(value: WorkspaceEditExecutionRecord): void {
    try { globalThis.sessionStorage.setItem(executionStorageKey(value.document_id), value.execution_id); } catch { /* recovery hint is best-effort only */ }
    try {
      const url = new URL(globalThis.location.href);
      url.searchParams.set(EXECUTION_QUERY_PARAM, value.execution_id);
      globalThis.history.replaceState({}, '', url);
    } catch { /* URL recovery hint is best-effort only */ }
  }

  function storedExecutionId(documentId: string): string {
    try { return globalThis.sessionStorage.getItem(executionStorageKey(documentId)) ?? ''; } catch { return ''; }
  }

  async function recoverExecutionForDocument(documentValue: WorkspaceDocumentResource): Promise<void> {
    const documentId = String(documentValue.document_id ?? '');
    if (!documentId || execution || recoveryInFlight) return;
    const candidates = [deepLinkedExecutionId, storedExecutionId(documentId)].filter((value, index, all) => Boolean(value) && all.indexOf(value) === index);
    for (const executionId of candidates) {
      const attemptKey = `${documentId}:${executionId}`;
      if (attemptKey === lastRecoveryAttempt) continue;
      recoveryInFlight = true;
      try {
        const response = await new DevPilotApiClient({ token: options.tokenProvider() }).workspaceEditExecutionStatus(executionId);
        const recovered = (response.data as { execution?: WorkspaceEditExecutionRecord }).execution;
        if (!response.ok || !recovered) throw new Error(response.message || 'Execution recovery blocked.');
        const currentSha = String(documentValue.sha256 ?? '');
        const validHash = [recovered.pre_sha256, recovered.post_sha256].includes(currentSha);
        if (recovered.document_id !== documentId || recovered.relative_path !== documentValue.relative_path || !validHash) {
          throw new Error('Execution recovery BLOCK: persisted execution does not match the selected document/hash.');
        }
        execution = recovered;
        lastRecoveryAttempt = attemptKey;
        applyApproval = recovered.approval;
        currentDocument = documentValue;
        draft = String(documentValue.content ?? draft);
        rememberExecution(recovered);
        if (recovered.status === 'applied') {
          status = 'APPLY PASS (recuperado): ejecución persistente cargada desde control-root; rollback pre-commit sigue disponible.';
        } else if (recovered.status === 'rolled-back-manual') {
          status = 'ROLLBACK PASS (recuperado): el registro persistente confirma restauración manual approval-bound.';
        } else {
          status = `Ejecución UOC-005 recuperada: ${recovered.status}.`;
        }
        error = '';
      } catch (cause) {
        error = cause instanceof Error ? cause.message : String(cause);
      } finally {
        recoveryInFlight = false;
        draw();
      }
      if (execution) return;
    }
  }

  function secretLike(text: string): boolean {
    return /(-----BEGIN [A-Z ]+PRIVATE KEY-----|\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*[^\s]{8,}|\bsk-[A-Za-z0-9_-]{16,})/i.test(text);
  }

  function loadStored(document: WorkspaceDocumentResource): string | null {
    try { return globalThis.sessionStorage.getItem(storageKey(document)); } catch { return null; }
  }

  function resetExecutionState(): void {
    applyApproval = undefined;
    rollbackApproval = undefined;
    execution = undefined;
  }

  function saveDraft(): void {
    if (!currentDocument) return;
    error = '';
    const bytes = new TextEncoder().encode(draft).byteLength;
    if (bytes > MAX_DRAFT_BYTES) { error = `Draft exceeds ${MAX_DRAFT_BYTES} bytes.`; draw(); return; }
    if (secretLike(draft)) { error = 'Draft session storage BLOCK: secret-like material detected. Nothing was persisted.'; draw(); return; }
    try {
      globalThis.sessionStorage.setItem(storageKey(currentDocument), draft);
      status = 'Draft guardado manualmente en sessionStorage para esta sesión. No se escribió al filesystem.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    draw();
  }

  function discardDraft(): void {
    if (!currentDocument) return;
    try { globalThis.sessionStorage.removeItem(storageKey(currentDocument)); } catch { /* fail closed in UI state */ }
    draft = String(currentDocument.content ?? ''); plan = undefined; resetExecutionState();
    status = 'Draft descartado; se restauró el contenido leído del documento.'; error = ''; draw();
  }

  async function generatePlan(): Promise<void> {
    if (!currentDocument?.document_id || !currentDocument.sha256) return;
    busy = true; error = ''; status = 'Generando plan inmutable…'; plan = undefined; resetExecutionState(); exportFeedback=''; delete root.dataset.patchExportState; draw();
    try {
      const client = new DevPilotApiClient({ token: options.tokenProvider() });
      const response = await client.planWorkspaceEdit({ document_id: currentDocument.document_id, document_sha_before: currentDocument.sha256, proposed_content: draft });
      const data = response.data as WorkspaceEditPlanResponseData;
      if (!response.ok || !data.plan) throw new Error(response.message || 'Edit plan blocked.');
      plan = data.plan; status = 'Plan inmutable listo. No se modificó el documento fuente.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function recheck(): Promise<void> {
    if (!plan) return;
    busy = true; error = ''; status = 'Revalidando hash base…'; draw();
    try {
      const response = await new DevPilotApiClient({ token: options.tokenProvider() }).recheckWorkspaceEditPlan(plan.plan_id, plan.plan_hash);
      if (!response.ok) throw new Error(response.message || 'Stale plan blocked.');
      status = 'Optimistic concurrency PASS: el blob fuente sigue coincidiendo con document_sha_before.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function requestApplyApproval(): Promise<void> {
    if (!plan) return;
    busy = true; error = ''; status = 'Creando solicitud de aprobación vinculada al plan…'; draw();
    try {
      const response = await new DevPilotApiClient({ token: options.tokenProvider() }).requestWorkspaceEditApplyApproval(plan.plan_id, { plan_hash: plan.plan_hash, actor: ACTOR, reason: approvalReason, ttl_minutes: 15 });
      const approval = (response.data as { approval?: WorkspaceEditApprovalRecord }).approval;
      if (!response.ok || !approval) throw new Error(response.message || 'Approval request blocked.');
      applyApproval = approval;
      status = `Solicitud ${approval.approval_id} creada. Requiere decisión humana explícita antes de apply.`;
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function decideApply(decision: 'approve' | 'deny'): Promise<void> {
    if (!applyApproval) return;
    busy = true; error = ''; status = decision === 'approve' ? 'Registrando aprobación humana…' : 'Registrando denegación humana…'; draw();
    try {
      const response = await new DevPilotApiClient({ token: options.tokenProvider() }).decideApproval(applyApproval.approval_id, decision, { actor: ACTOR, reason: decision === 'approve' ? 'Plan UOC-005 revisado en UI y aprobado por owner.' : 'Plan UOC-005 denegado por owner.' });
      const approval = (response.data as { approval?: WorkspaceEditApprovalRecord }).approval;
      if (!response.ok || !approval) throw new Error(response.message || 'Approval decision blocked.');
      applyApproval = approval;
      status = decision === 'approve' ? 'Aprobación exacta registrada. Apply permanece sujeto a recheck de hash/policy.' : 'Solicitud denegada. Apply permanece bloqueado.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function applyApproved(): Promise<void> {
    if (!plan || !applyApproval || applyApproval.status !== 'approved') return;
    busy = true; error = ''; status = 'Revalidando approval/hash/policy, creando backup y aplicando de forma atómica…'; draw();
    try {
      const response = await new DevPilotApiClient({ token: options.tokenProvider() }).applyWorkspaceEdit(plan.plan_id, { plan_hash: plan.plan_hash, approval_id: applyApproval.approval_id, actor: ACTOR });
      const nextExecution = (response.data as { execution?: WorkspaceEditExecutionRecord }).execution;
      if (!response.ok || !nextExecution) throw new Error(response.message || 'Approved apply blocked.');
      execution = nextExecution;
      rememberExecution(nextExecution);
      if (currentDocument) currentDocument = { ...currentDocument, content: plan.proposed_content, sha256: nextExecution.post_sha256 };
      draft = plan.proposed_content;
      status = 'APPLY PASS: escritura atómica validada. Git stage/commit siguen fuera de UOC-005; rollback pre-commit está disponible.';
      await options.onMutationComplete?.();
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function requestRollbackApproval(): Promise<void> {
    if (!execution || execution.status !== 'applied') return;
    busy = true; error = ''; status = 'Verificando elegibilidad pre-commit y creando aprobación de rollback…'; draw();
    try {
      const response = await new DevPilotApiClient({ token: options.tokenProvider() }).requestWorkspaceEditRollbackApproval(execution.execution_id, { actor: ACTOR, reason: rollbackReason, ttl_minutes: 15 });
      const approval = (response.data as { approval?: WorkspaceEditApprovalRecord }).approval;
      if (!response.ok || !approval) throw new Error(response.message || 'Rollback approval request blocked.');
      rollbackApproval = approval;
      status = `Solicitud de rollback ${approval.approval_id} creada. Requiere nueva decisión humana.`;
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function decideRollback(decision: 'approve' | 'deny'): Promise<void> {
    if (!rollbackApproval) return;
    busy = true; error = ''; status = decision === 'approve' ? 'Registrando aprobación de rollback…' : 'Registrando denegación de rollback…'; draw();
    try {
      const response = await new DevPilotApiClient({ token: options.tokenProvider() }).decideApproval(rollbackApproval.approval_id, decision, { actor: ACTOR, reason: decision === 'approve' ? 'Rollback pre-commit revisado y aprobado por owner.' : 'Rollback denegado por owner.' });
      const approval = (response.data as { approval?: WorkspaceEditApprovalRecord }).approval;
      if (!response.ok || !approval) throw new Error(response.message || 'Rollback decision blocked.');
      rollbackApproval = approval;
      status = decision === 'approve' ? 'Rollback aprobado. La restauración exacta sigue sujeta a hash/policy.' : 'Rollback denegado; no se modificó el documento.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function rollbackApproved(): Promise<void> {
    if (!execution || !rollbackApproval || rollbackApproval.status !== 'approved') return;
    busy = true; error = ''; status = 'Validando binding, estado Git y backup antes de rollback…'; draw();
    try {
      const response = await new DevPilotApiClient({ token: options.tokenProvider() }).rollbackWorkspaceEdit(execution.execution_id, { approval_id: rollbackApproval.approval_id, actor: ACTOR });
      const nextExecution = (response.data as { execution?: WorkspaceEditExecutionRecord }).execution;
      if (!response.ok || !nextExecution) throw new Error(response.message || 'Rollback blocked.');
      execution = nextExecution;
      rememberExecution(nextExecution);
      if (currentDocument) currentDocument = { ...currentDocument, sha256: nextExecution.pre_sha256 };
      status = 'ROLLBACK PASS: el hash pre-apply fue restaurado. UOC-005 no ejecutó Git stage/commit.';
      await options.onMutationComplete?.();
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  function exportPatch(): void {
    if (!plan) return;
    const exportPlan = plan;
    error = '';
    exportFeedback = 'Descarga solicitada · evidencia NO EJECUTADA. DevPilot no aplicó, no guardó, no stageó y no escribió el patch en el workspace.';
    root.dataset.patchExportState = 'requested-not-executed';
    draw();
    const feedback = root.querySelector<HTMLElement>('[data-uoc004-export-feedback="true"]');
    feedback?.focus({ preventScroll: true });
    feedback?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    const startDownload = (): void => {
      const blob = new Blob([exportPlan.diff.content], { type: 'text/x-diff;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = exportPlan.patch_evidence.filename; anchor.style.display = 'none'; document.body.append(anchor); anchor.click(); anchor.remove();
      globalThis.setTimeout(() => URL.revokeObjectURL(url), 1000);
    };
    if (typeof globalThis.requestAnimationFrame === 'function') globalThis.requestAnimationFrame(() => globalThis.requestAnimationFrame(startDownload)); else globalThis.setTimeout(startDownload, 0);
  }

  function previewElement(resource: WorkspaceDocumentResource, content: string): HTMLElement {
    const pre = document.createElement('pre'); pre.className = 'uoc004-preview';
    if (resource.extension === '.json') { try { pre.textContent = JSON.stringify(JSON.parse(content), null, 2); } catch { pre.textContent = content; } } else pre.textContent = content;
    return pre;
  }

  function approvalCard(label: string, approval: WorkspaceEditApprovalRecord, decision: (value: 'approve' | 'deny') => void): HTMLElement {
    const card = document.createElement('section'); card.className = 'uoc005-approval-card';
    const h = document.createElement('h4'); h.textContent = label;
    const details = document.createElement('dl');
    details.innerHTML = `<dt>ID</dt><dd><code>${escapeHtml(approval.approval_id)}</code></dd><dt>Estado</dt><dd><strong>${escapeHtml(approval.status)}</strong></dd><dt>Actor solicitante</dt><dd>${escapeHtml(approval.actor)}</dd><dt>Expira</dt><dd>${escapeHtml(approval.expires_at)}</dd>`;
    card.append(h, details);
    if (approval.status === 'requested') {
      const controls = document.createElement('div'); controls.className = 'uoc005-actions';
      const approve = button('Aprobar', () => decision('approve'));
      const deny = button('Denegar', () => decision('deny'), 'button-secondary');
      approve.disabled = busy; deny.disabled = busy; controls.append(approve, deny); card.append(controls);
    }
    return card;
  }

  function executionCard(value: WorkspaceEditExecutionRecord): HTMLElement {
    const card = document.createElement('section'); card.className = 'uoc005-execution-card';
    const rollback = value.rollback ?? {};
    const restoredSha = String(rollback.restored_sha256 ?? '');
    card.innerHTML = `<h4>Ejecución gobernada</h4><dl><dt>Execution ID</dt><dd><code>${escapeHtml(value.execution_id)}</code></dd><dt>Estado</dt><dd><strong>${escapeHtml(value.status)}</strong></dd><dt>Approval ID</dt><dd><code>${escapeHtml(value.approval_id)}</code></dd><dt>Pre SHA</dt><dd><code>${escapeHtml(value.pre_sha256)}</code></dd><dt>Post SHA</dt><dd><code>${escapeHtml(value.post_sha256)}</code></dd>${restoredSha ? `<dt>Restored SHA</dt><dd><code>${escapeHtml(restoredSha)}</code></dd>` : ''}<dt>Backup</dt><dd><code>${escapeHtml(value.backup_ref ?? 'control-root evidence')}</code></dd><dt>Evidence</dt><dd><code>${escapeHtml(value.evidence_ref ?? 'control-root evidence')}</code></dd><dt>Report</dt><dd><code>${escapeHtml(value.report_ref ?? 'control-root report')}</code></dd><dt>Git stage</dt><dd>${String(value.git_stage)}</dd><dt>Git commit</dt><dd>${String(value.git_commit)}</dd></dl>`;
    return card;
  }

  function draw(): void {
    root.replaceChildren();
    const heading = document.createElement('div'); heading.className = 'uoc004-heading';
    const title = document.createElement('h2'); title.textContent = 'Edición documental gobernada';
    const badges = document.createElement('div'); badges.className = 'uoc004-badges'; badges.innerHTML = '<span>UOC-004 PLAN</span><span>UOC-005 APPROVAL</span><span>ATOMIC APPLY</span><span>ROLLBACK</span><span>LOCAL-FIRST</span>';
    heading.append(title, badges); root.append(heading);
    const intro = document.createElement('p'); intro.textContent = 'Planifique sin escribir; después solicite aprobación humana exacta. UOC-005 solo aplica el plan inmutable aprobado, crea backup externo de control, valida postcondiciones y permite rollback acotado antes de Git stage/commit.'; root.append(intro);
    if (!currentDocument) { root.append(renderUiStateNotice('empty', 'Seleccione un documento para iniciar una edición gobernada.')); return; }
    const extension = String(currentDocument.extension ?? '').toLowerCase();
    if (!EDITABLE_EXTENSIONS.has(extension)) { root.append(renderUiStateNotice('block', `${extension || 'Este tipo'} permanece read-only. Solo se admiten Markdown, JSON y YAML.`)); return; }
    const identity = document.createElement('div'); identity.className = 'uoc004-identity'; identity.innerHTML = `<strong>${escapeHtml(currentDocument.relative_path)}</strong><code>${escapeHtml(String(currentDocument.sha256 ?? 'sha unavailable'))}</code>`; root.append(identity);
    const textarea = document.createElement('textarea'); textarea.className = 'uoc004-editor'; textarea.value = draft; textarea.rows = 18; textarea.spellcheck = false; textarea.setAttribute('aria-label','Propuesta de edición');
    textarea.disabled = execution?.status === 'applied';
    textarea.addEventListener('input',()=>{ draft=textarea.value; plan=undefined; resetExecutionState(); exportFeedback=''; delete root.dataset.patchExportState; status='Draft modificado en memoria; cualquier aprobación previa quedó invalidada por diseño.'; }); root.append(textarea);
    const actions=document.createElement('div'); actions.className='uoc004-actions';
    const save=button('Guardar draft de sesión', saveDraft); const discard=button('Descartar draft', discardDraft,'button-secondary'); const generate=button(busy?'Procesando…':'Generar plan inmutable',()=>void generatePlan()); generate.disabled=busy || execution?.status === 'applied'; actions.append(save,discard,generate); root.append(actions);
    const note=document.createElement('p'); note.className='uoc004-storage-note'; note.textContent='Draft: sessionStorage manual. Apply nunca usa texto libre: usa exactamente proposed_content del plan hash-bound. Git stage/commit pertenecen a UOC-006.'; root.append(note);
    if (status) root.append(renderUiStateNotice('success',status)); if(error) root.append(renderUiStateNotice(error.includes('BLOCK')?'block':'error',error));
    if (!plan && !execution) return;
    if (plan) {
      const summary=document.createElement('section'); summary.className='uoc004-plan-summary'; summary.innerHTML=`<h3>Plan inmutable</h3><dl><dt>Plan ID</dt><dd><code>${escapeHtml(plan.plan_id)}</code></dd><dt>Plan hash</dt><dd><code>${escapeHtml(plan.plan_hash)}</code></dd><dt>Base SHA</dt><dd><code>${escapeHtml(plan.document.document_sha_before)}</code></dd><dt>Risk</dt><dd>${escapeHtml(plan.risk.level)} (${plan.risk.score})</dd><dt>Expira</dt><dd>${escapeHtml(plan.expires_at)}</dd><dt>Apply</dt><dd>Approval-bound · UOC-005</dd></dl>`; root.append(summary);
      const recheckButton=button('Revalidar hash base',()=>void recheck()); recheckButton.disabled=busy || execution?.status === 'applied'; root.append(recheckButton);
      const diff=document.createElement('section'); diff.className='uoc004-diff'; const dh=document.createElement('h3'); dh.textContent=`Diff completo · +${plan.diff.additions} / -${plan.diff.deletions}`; const pre=document.createElement('pre'); pre.textContent=plan.diff.content; diff.append(dh,pre); root.append(diff);
      const preview=document.createElement('section'); preview.className='uoc004-preview-panel'; const ph=document.createElement('h3'); ph.textContent='Preview seguro'; preview.append(ph,previewElement(currentDocument,plan.proposed_content)); root.append(preview);
      const exportButton=button('Exportar .patch (no ejecutado)',exportPatch,'button-secondary'); root.append(exportButton);
      if (exportFeedback) { const exportNotice=document.createElement('div'); exportNotice.className='uoc004-export-feedback'; exportNotice.dataset.uoc004ExportFeedback='true'; exportNotice.setAttribute('role','status'); exportNotice.setAttribute('aria-live','polite'); exportNotice.tabIndex=-1; exportNotice.textContent=exportFeedback; root.append(exportNotice); }
    }

    const governance = document.createElement('section'); governance.className = 'uoc005-governance';
    const gh = document.createElement('h3'); gh.textContent = 'Approval binding, apply y rollback'; governance.append(gh);
    if (!execution && plan) {
      const label = document.createElement('label'); label.textContent = 'Justificación para apply'; const input = document.createElement('textarea'); input.value = approvalReason; input.maxLength = 1000; input.rows = 3; input.addEventListener('input', () => { approvalReason = input.value; }); label.append(input); governance.append(label);
      const request = button(applyApproval ? 'Aprobación solicitada' : 'Solicitar aprobación de apply', () => void requestApplyApproval()); request.disabled = busy || Boolean(applyApproval); governance.append(request);
      if (applyApproval) governance.append(approvalCard('Aprobación de apply', applyApproval, (decision) => void decideApply(decision)));
      const applyButton = button('Aplicar cambio aprobado', () => void applyApproved()); applyButton.disabled = busy || applyApproval?.status !== 'approved'; governance.append(applyButton);
    } else if (execution) {
      governance.append(executionCard(execution));
      if (execution.status === 'applied') {
        const label = document.createElement('label'); label.textContent = 'Justificación para rollback'; const input = document.createElement('textarea'); input.value = rollbackReason; input.maxLength = 1000; input.rows = 3; input.addEventListener('input', () => { rollbackReason = input.value; }); label.append(input); governance.append(label);
        const request = button(rollbackApproval ? 'Aprobación de rollback solicitada' : 'Solicitar aprobación de rollback', () => void requestRollbackApproval()); request.disabled = busy || Boolean(rollbackApproval); governance.append(request);
        if (rollbackApproval) governance.append(approvalCard('Aprobación de rollback', rollbackApproval, (decision) => void decideRollback(decision)));
        const rollback = button('Revertir cambio aprobado', () => void rollbackApproved(), 'button-secondary'); rollback.disabled = busy || rollbackApproval?.status !== 'approved'; governance.append(rollback);
      }
    }
    root.append(governance);
    const noGo=document.createElement('div'); noGo.className='uoc004-no-go'; noGo.textContent='NO-GO vigente: no auto-save · no shell · no patch.apply genérico · no Git stage/commit/push · no remote · no connector write · no plugin execution.'; root.append(noGo);
  }

  function setDocument(documentValue?: WorkspaceDocumentResource): void {
    const transientMutationReload = Boolean(!documentValue && currentDocument && execution && execution.document_id === currentDocument.document_id);
    if (transientMutationReload) {
      status = execution?.status === 'applied'
        ? 'APPLY PASS: ejecución preservada mientras se recarga el documento aplicado.'
        : status;
      draw();
      return;
    }
    const changed=(currentDocument?.document_id ?? '') !== (documentValue?.document_id ?? '') || (currentDocument?.sha256 ?? '') !== (documentValue?.sha256 ?? '');
    const sameExecutionTransition = Boolean(execution && documentValue && currentDocument?.document_id === documentValue.document_id && [execution.pre_sha256, execution.post_sha256].includes(String(documentValue.sha256 ?? '')));
    currentDocument=documentValue;
    if (changed && !sameExecutionTransition) {
      plan=undefined; resetExecutionState(); error=''; status=''; exportFeedback=''; delete root.dataset.patchExportState;
      if(documentValue){ const stored=loadStored(documentValue); draft=stored ?? String(documentValue.content ?? ''); } else draft='';
    } else if (changed && documentValue) {
      draft = String(documentValue.content ?? draft);
    }
    draw();
    if (documentValue) void recoverExecutionForDocument(documentValue);
  }

  (root as HTMLElement & { setDocument?: (document?: WorkspaceDocumentResource) => void }).setDocument=setDocument;
  setDocument(currentDocument);
  return root;
}

function button(label:string, handler:()=>void, className=''): HTMLButtonElement { const b=document.createElement('button'); b.type='button'; b.textContent=label; if(className)b.className=className; b.addEventListener('click',handler); return b; }
function escapeHtml(value:string):string { return value.replace(/[&<>'"]/g,(char)=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char] ?? char)); }
