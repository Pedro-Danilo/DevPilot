// UI contract: ui.workspace-documents — UOC-004 plan-only child surface.
import { DevPilotApiClient } from '../api/client';
import type { DevPilotApplicationResponse, WorkspaceDocumentResource, WorkspaceEditPlan, WorkspaceEditPlanResponseData } from '../api/types';
import { renderUiStateNotice } from './ContractBadges';

const EDITABLE_EXTENSIONS = new Set(['.md', '.json', '.yaml', '.yml']);
const MAX_DRAFT_BYTES = 262144;

interface Options {
  tokenProvider: () => string;
  document?: WorkspaceDocumentResource;
}

export function createDocumentEditPlanner(options: Options): HTMLElement {
  const root = document.createElement('section');
  root.className = 'panel document-edit-planner';
  root.dataset.uoc004EditPlanner = 'true';
  let currentDocument: WorkspaceDocumentResource | undefined = options.document;
  let draft = '';
  let status = '';
  let error = '';
  let plan: WorkspaceEditPlan | undefined;
  let busy = false;
  let exportFeedback = '';

  function storageKey(document: WorkspaceDocumentResource): string {
    return `devpilot:uoc004:draft:${document.document_id ?? document.node_id}:${document.sha256 ?? 'unknown'}`;
  }

  function secretLike(text: string): boolean {
    return /(-----BEGIN [A-Z ]+PRIVATE KEY-----|\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*[^\s]{8,}|\bsk-[A-Za-z0-9_-]{16,})/i.test(text);
  }

  function loadStored(document: WorkspaceDocumentResource): string | null {
    try { return globalThis.sessionStorage.getItem(storageKey(document)); } catch { return null; }
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
    draft = String(currentDocument.content ?? ''); plan = undefined;
    status = 'Draft descartado; se restauró el contenido leído del documento.'; error = ''; draw();
  }

  async function generatePlan(): Promise<void> {
    if (!currentDocument?.document_id || !currentDocument.sha256) return;
    busy = true; error = ''; status = 'Generando plan inmutable…'; plan = undefined; exportFeedback=''; delete root.dataset.patchExportState; draw();
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
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = exportPlan.patch_evidence.filename;
      anchor.style.display = 'none';
      document.body.append(anchor);
      anchor.click();
      anchor.remove();
      globalThis.setTimeout(() => URL.revokeObjectURL(url), 1000);
    };

    if (typeof globalThis.requestAnimationFrame === 'function') {
      globalThis.requestAnimationFrame(() => globalThis.requestAnimationFrame(startDownload));
    } else {
      globalThis.setTimeout(startDownload, 0);
    }
  }

  function previewElement(resource: WorkspaceDocumentResource, content: string): HTMLElement {
    const pre = document.createElement('pre');
    pre.className = 'uoc004-preview';
    if (resource.extension === '.json') {
      try { pre.textContent = JSON.stringify(JSON.parse(content), null, 2); } catch { pre.textContent = content; }
    } else { pre.textContent = content; }
    return pre;
  }

  function draw(): void {
    root.replaceChildren();
    const heading = document.createElement('div'); heading.className = 'uoc004-heading';
    const title = document.createElement('h2'); title.textContent = 'Plan de edición gobernado';
    const badges = document.createElement('div'); badges.className = 'uoc004-badges'; badges.innerHTML = '<span>UOC-004</span><span>PLAN-ONLY</span><span>NO-WRITE</span><span>LOCAL-FIRST</span>';
    heading.append(title, badges); root.append(heading);
    const intro = document.createElement('p'); intro.textContent = 'Proponga cambios sobre Markdown/JSON/YAML, valide sintaxis/frontmatter, genere un plan inmutable y revise el diff completo. UOC-004 nunca aplica ni guarda el documento fuente.'; root.append(intro);
    if (!currentDocument) { root.append(renderUiStateNotice('empty', 'Seleccione un documento para evaluar si es editable en UOC-004.')); return; }
    const extension = String(currentDocument.extension ?? '').toLowerCase();
    if (!EDITABLE_EXTENSIONS.has(extension)) { root.append(renderUiStateNotice('block', `${extension || 'Este tipo'} permanece read-only. UOC-004 solo admite Markdown, JSON y YAML.`)); return; }
    const identity = document.createElement('div'); identity.className = 'uoc004-identity';
    identity.innerHTML = `<strong>${escapeHtml(currentDocument.relative_path)}</strong><code>${escapeHtml(String(currentDocument.sha256 ?? 'sha unavailable'))}</code>`; root.append(identity);
    const textarea = document.createElement('textarea'); textarea.className = 'uoc004-editor'; textarea.value = draft; textarea.rows = 18; textarea.spellcheck = false; textarea.setAttribute('aria-label','Propuesta de edición');
    textarea.addEventListener('input',()=>{ draft=textarea.value; plan=undefined; exportFeedback=''; delete root.dataset.patchExportState; status='Draft modificado en memoria; no se ha guardado ni planificado.'; }); root.append(textarea);
    const actions=document.createElement('div'); actions.className='uoc004-actions';
    const save=button('Guardar draft de sesión', saveDraft); const discard=button('Descartar draft', discardDraft,'button-secondary'); const generate=button(busy?'Procesando…':'Generar plan inmutable',()=>void generatePlan()); generate.disabled=busy; actions.append(save,discard,generate); root.append(actions);
    const note=document.createElement('p'); note.className='uoc004-storage-note'; note.textContent='Draft: sessionStorage manual únicamente. Sin auto-save, localStorage, filesystem, Git stage ni apply.'; root.append(note);
    if (status) root.append(renderUiStateNotice('success',status)); if(error) root.append(renderUiStateNotice(error.includes('BLOCK')?'block':'error',error));
    if (!plan) return;
    const summary=document.createElement('section'); summary.className='uoc004-plan-summary'; summary.innerHTML=`<h3>Plan inmutable</h3><dl><dt>Plan ID</dt><dd><code>${escapeHtml(plan.plan_id)}</code></dd><dt>Plan hash</dt><dd><code>${escapeHtml(plan.plan_hash)}</code></dd><dt>Base SHA</dt><dd><code>${escapeHtml(plan.document.document_sha_before)}</code></dd><dt>Risk</dt><dd>${escapeHtml(plan.risk.level)} (${plan.risk.score})</dd><dt>Expira</dt><dd>${escapeHtml(plan.expires_at)}</dd><dt>Apply</dt><dd>NO DISPONIBLE — UOC-005</dd></dl>`; root.append(summary);
    const recheckButton=button('Revalidar hash base',()=>void recheck()); recheckButton.disabled=busy; root.append(recheckButton);
    const diff=document.createElement('section'); diff.className='uoc004-diff'; const dh=document.createElement('h3'); dh.textContent=`Diff completo · +${plan.diff.additions} / -${plan.diff.deletions}`; const pre=document.createElement('pre'); pre.textContent=plan.diff.content; diff.append(dh,pre); root.append(diff);
    const preview=document.createElement('section'); preview.className='uoc004-preview-panel'; const ph=document.createElement('h3'); ph.textContent='Preview seguro'; preview.append(ph,previewElement(currentDocument!,plan.proposed_content)); root.append(preview);
    const exportButton=button('Exportar .patch (no ejecutado)',exportPatch,'button-secondary'); root.append(exportButton);
    if (exportFeedback) {
      const exportNotice=document.createElement('div');
      exportNotice.className='uoc004-export-feedback';
      exportNotice.dataset.uoc004ExportFeedback='true';
      exportNotice.setAttribute('role','status');
      exportNotice.setAttribute('aria-live','polite');
      exportNotice.tabIndex=-1;
      exportNotice.textContent=exportFeedback;
      root.append(exportNotice);
    }
    const noGo=document.createElement('div'); noGo.className='uoc004-no-go'; noGo.textContent='NO-GO UOC-004: no Save-to-file · no Apply · no Stage · no Commit · no shell · no secretos.'; root.append(noGo);
  }

  function setDocument(documentValue?: WorkspaceDocumentResource): void {
    const changed=(currentDocument?.document_id ?? '') !== (documentValue?.document_id ?? '') || (currentDocument?.sha256 ?? '') !== (documentValue?.sha256 ?? '');
    currentDocument=documentValue;
    if (changed) {
      plan=undefined; error=''; status=''; exportFeedback=''; delete root.dataset.patchExportState;
      if(documentValue){ const stored=loadStored(documentValue); draft=stored ?? String(documentValue.content ?? ''); }
      else draft='';
    }
    draw();
  }

  (root as HTMLElement & { setDocument?: (document?: WorkspaceDocumentResource) => void }).setDocument=setDocument;
  setDocument(currentDocument);
  return root;
}

function button(label:string, handler:()=>void, className=''): HTMLButtonElement { const b=document.createElement('button'); b.type='button'; b.textContent=label; if(className)b.className=className; b.addEventListener('click',handler); return b; }
function escapeHtml(value:string):string { return value.replace(/[&<>'"]/g,(char)=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char] ?? char)); }
