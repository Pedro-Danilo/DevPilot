// DevPilot UI route contract: ui.workspace-documents — GSDLC-04-B governed MANUAL draft authoring.
import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { ArtifactDraftRecord, ArtifactDraftRevision, ArtifactDraftRevisionSummary, DevPilotApplicationResponse, WorkspaceDocumentResource } from '../api/types';
import { renderContractBadges, renderUiStateNotice } from './ContractBadges';

const EDITABLE = new Set(['.md', '.json']);
const AUTOSAVE_DELAY_MS = 1100;

interface ArtifactManualEditorOptions {
  tokenProvider: () => string;
  onDraftChange?: (content: string, revisionSha256?: string | null) => void;
}

type SaveState = 'idle' | 'loading' | 'saved' | 'conflict' | 'error';

export function createArtifactManualEditor(options: ArtifactManualEditorOptions): HTMLElement {
  const root = document.createElement('section');
  root.className = 'panel artifact-manual-editor';
  root.dataset.devpilotUiContract = 'ui.workspace-documents';
  root.dataset.gsdlc04b = 'artifact-manual-editor';

  let currentDocument: WorkspaceDocumentResource | undefined;
  let draft: ArtifactDraftRecord | undefined;
  let revisions: ArtifactDraftRevisionSummary[] = [];
  let content = '';
  let saveState: SaveState = 'idle';
  let message = '';
  let loadSequence = 0;
  let autosaveTimer: number | undefined;
  let editor: HTMLTextAreaElement | undefined;

  function client(): DevPilotApiClient { return new DevPilotApiClient({ token: options.tokenProvider() }); }
  function currentRevision(): ArtifactDraftRevision | undefined {
    if (!draft?.current_revision_sha256) return undefined;
    return draft.revisions.find((item) => item.revision_sha256 === draft?.current_revision_sha256);
  }
  function currentRevisionSha(): string | null { return draft?.current_revision_sha256 ?? null; }
  function sourceSha(): string { return String(currentDocument?.sha256 ?? ''); }

  async function loadDraft(documentValue: WorkspaceDocumentResource, sequence: number): Promise<void> {
    saveState = 'loading'; message = 'Recuperando draft runtime e historial…'; draw();
    try {
      const [draftResponse, historyResponse] = await Promise.all([
        client().artifactDraft(documentValue.document_id ?? documentValue.node_id),
        client().artifactDraftHistory(documentValue.document_id ?? documentValue.node_id),
      ]);
      if (sequence !== loadSequence || currentDocument?.document_id !== documentValue.document_id) return;
      const draftData = draftResponse.data as { draft?: ArtifactDraftRecord | null };
      const historyData = historyResponse.data as { revisions?: ArtifactDraftRevisionSummary[] };
      draft = draftData.draft ?? undefined;
      revisions = Array.isArray(historyData.revisions) ? historyData.revisions : [];
      if (draft?.active) content = currentRevision()?.content ?? String(documentValue.content ?? '');
      else content = String(documentValue.content ?? '');
      saveState = draft?.source_conflict ? 'conflict' : 'idle';
      message = draft?.source_conflict
        ? 'CONFLICT: el source aprobado cambió desde el preimage del draft. Revisa antes de continuar.'
        : draft?.active
          ? 'Draft runtime recuperado. Guardar no sobrescribe el source aprobado.'
          : 'Sin draft activo: el editor parte del source aprobado en modo DRAFT.';
      options.onDraftChange?.(content, currentRevisionSha());
    } catch (error) {
      saveState = error instanceof DevPilotApiError && error.status === 409 ? 'conflict' : 'error';
      message = readableError(error);
    }
    draw();
  }

  async function persist(event: 'SAVE' | 'AUTOSAVE'): Promise<void> {
    if (!currentDocument || !EDITABLE.has(String(currentDocument.extension ?? '').toLowerCase())) return;
    const text = editor?.value ?? content;
    saveState = 'loading'; message = event === 'AUTOSAVE' ? 'Autosave…' : 'Guardando draft…'; drawStatusOnly();
    try {
      const response = await client().saveArtifactDraft(currentDocument.document_id ?? currentDocument.node_id, {
        content: text,
        expected_source_sha256: sourceSha(),
        expected_revision_sha256: currentRevisionSha(),
        event,
      });
      const data = response.data as { draft?: ArtifactDraftRecord };
      if (data.draft) draft = data.draft;
      content = text;
      saveState = 'saved';
      message = event === 'AUTOSAVE' ? 'Autosave PASS · runtime DRAFT · source aprobado intacto.' : 'SAVE PASS · runtime DRAFT · source aprobado intacto.';
      options.onDraftChange?.(content, currentRevisionSha());
      await refreshHistory();
    } catch (error) {
      saveState = isConflict(error) ? 'conflict' : 'error';
      message = readableError(error);
    }
    draw();
  }

  async function refreshHistory(): Promise<void> {
    if (!currentDocument) return;
    try {
      const response = await client().artifactDraftHistory(currentDocument.document_id ?? currentDocument.node_id);
      const data = response.data as { revisions?: ArtifactDraftRevisionSummary[] };
      revisions = Array.isArray(data.revisions) ? data.revisions : [];
    } catch { /* history failure must not erase a successfully persisted draft */ }
  }

  async function discard(): Promise<void> {
    if (!currentDocument) return;
    if (autosaveTimer) globalThis.clearTimeout(autosaveTimer);
    saveState = 'loading'; message = 'Descartando draft activo…'; drawStatusOnly();
    try {
      const response = await client().discardArtifactDraft(currentDocument.document_id ?? currentDocument.node_id, {
        expected_source_sha256: sourceSha(), expected_revision_sha256: currentRevisionSha(),
      });
      const data = response.data as { draft?: ArtifactDraftRecord | null };
      draft = data.draft ?? undefined;
      content = String(currentDocument.content ?? '');
      saveState = 'idle'; message = 'Draft descartado; historial conservado y source aprobado intacto.';
      options.onDraftChange?.(content, null);
      await refreshHistory();
    } catch (error) { saveState = isConflict(error) ? 'conflict' : 'error'; message = readableError(error); }
    draw();
  }

  async function recover(revisionSha256: string): Promise<void> {
    if (!currentDocument) return;
    saveState = 'loading'; message = 'Recuperando revisión como nuevo DRAFT…'; drawStatusOnly();
    try {
      const response = await client().recoverArtifactDraft(currentDocument.document_id ?? currentDocument.node_id, {
        revision_sha256: revisionSha256,
        expected_source_sha256: sourceSha(),
        expected_revision_sha256: currentRevisionSha(),
      });
      const data = response.data as { draft?: ArtifactDraftRecord };
      if (data.draft) draft = data.draft;
      content = currentRevision()?.content ?? content;
      saveState = 'saved'; message = 'RECOVER PASS: la revisión histórica se materializó como nueva revisión runtime.';
      options.onDraftChange?.(content, currentRevisionSha());
      await refreshHistory();
    } catch (error) { saveState = isConflict(error) ? 'conflict' : 'error'; message = readableError(error); }
    draw();
  }

  function scheduleAutosave(): void {
    if (autosaveTimer) globalThis.clearTimeout(autosaveTimer);
    autosaveTimer = globalThis.setTimeout(() => { void persist('AUTOSAVE'); }, AUTOSAVE_DELAY_MS);
  }

  function drawStatusOnly(): void {
    const status = root.querySelector<HTMLElement>('[data-draft-status]');
    if (!status) return;
    status.textContent = message;
    status.dataset.state = saveState;
  }

  function draw(): void {
    root.replaceChildren();
    const heading = document.createElement('div'); heading.className = 'artifact-editor-heading';
    const title = document.createElement('h2'); title.textContent = 'Artifact Workbench · autoría manual';
    heading.append(title, renderContractBadges('ui.workspace-documents', { dryRunLabel: 'DRAFT runtime', warning: 'Guardar/autosave nunca equivale a APPROVED, FROZEN ni evidence.' }));
    root.append(heading);

    if (!currentDocument) { root.append(renderUiStateNotice('empty', 'Seleccione un documento Markdown o JSON para abrir el editor gobernado.')); return; }
    const extension = String(currentDocument.extension ?? '').toLowerCase();
    if (!EDITABLE.has(extension)) { root.append(renderUiStateNotice('block', 'GSDLC-04-B limita autoría manual a Markdown y JSON. Otros formatos permanecen read-only.')); return; }

    const identity = document.createElement('dl'); identity.className = 'artifact-editor-identity';
    appendDefinition(identity, 'Documento', currentDocument.relative_path);
    appendDefinition(identity, 'Source SHA', sourceSha());
    appendDefinition(identity, 'Estado', 'DRAFT'); appendDefinition(identity, 'Origen', 'MANUAL');
    appendDefinition(identity, 'Persistencia', 'runtime server-side · store efímero no versionado');
    root.append(identity);

    const status = document.createElement('div'); status.dataset.draftStatus = 'true'; status.dataset.state = saveState; status.className = 'artifact-draft-status'; status.setAttribute('role', saveState === 'conflict' || saveState === 'error' ? 'alert' : 'status'); status.setAttribute('aria-live', 'polite'); status.textContent = message; root.append(status);
    if (saveState === 'conflict') root.append(renderUiStateNotice('block', 'Lost update bloqueado: recargue el documento y revise el cambio externo antes de seguir.'));

    editor = document.createElement('textarea'); editor.className = 'artifact-manual-editor-input'; editor.rows = 22; editor.spellcheck = extension === '.md'; editor.value = content; editor.setAttribute('aria-label', `Editor manual ${extension === '.json' ? 'JSON' : 'Markdown'}`); editor.disabled = saveState === 'conflict';
    editor.addEventListener('input', () => { content = editor?.value ?? content; saveState = 'idle'; message = 'Cambios locales pendientes de autosave…'; options.onDraftChange?.(content, currentRevisionSha()); drawStatusOnly(); scheduleAutosave(); renderPreviewInto(preview, content, extension); renderHintsInto(hints, content, extension); });
    root.append(editor);

    const actions = document.createElement('div'); actions.className = 'artifact-editor-actions';
    actions.append(actionButton('Guardar draft', () => void persist('SAVE'), saveState === 'loading' || saveState === 'conflict'), actionButton('Descartar draft', () => void discard(), saveState === 'loading' || saveState === 'conflict', 'button-secondary'));
    root.append(actions);

    const hints = document.createElement('section'); hints.className = 'artifact-schema-hints'; const hintsTitle = document.createElement('h3'); hintsTitle.textContent = 'Hints'; hints.append(hintsTitle); renderHintsInto(hints, content, extension); root.append(hints);
    const preview = document.createElement('section'); preview.className = 'artifact-safe-preview'; const previewTitle = document.createElement('h3'); previewTitle.textContent = 'Preview seguro'; preview.append(previewTitle); renderPreviewInto(preview, content, extension); root.append(preview);
    root.append(renderHistory(revisions, (sha) => void recover(sha), saveState === 'loading' || saveState === 'conflict'));

    const warning = document.createElement('p'); warning.className = 'artifact-editor-warning'; warning.textContent = 'Seguridad: preview sin innerHTML de contenido no confiable; DRAFT no es evidence, no satisface approval y no escribe el source aprobado.'; root.append(warning);
  }

  function setDocument(documentValue?: WorkspaceDocumentResource): void {
    if (autosaveTimer) globalThis.clearTimeout(autosaveTimer);
    loadSequence += 1;
    currentDocument = documentValue;
    draft = undefined; revisions = []; content = String(documentValue?.content ?? ''); saveState = 'idle'; message = documentValue ? 'Preparando editor…' : '';
    options.onDraftChange?.(content, null);
    draw();
    if (documentValue && EDITABLE.has(String(documentValue.extension ?? '').toLowerCase())) void loadDraft(documentValue, loadSequence);
  }

  const findingNavigation = (event: Event): void => {
    const detail = (event as CustomEvent<{ relative_path?: string; line?: number | null; section?: string | null }>).detail;
    if (!detail || !currentDocument || !editor) return;
    if (detail.relative_path && detail.relative_path !== currentDocument.relative_path) return;
    const text = editor.value.replace(/\r\n?/g, '\n');
    const lines = text.split('\n');
    let offset = 0;
    if (detail.line && detail.line > 0) offset = lines.slice(0, Math.max(0, detail.line - 1)).reduce((n, line) => n + line.length + 1, 0);
    else if (detail.section) {
      const wanted = detail.section.trim().toLowerCase();
      const index = lines.findIndex((line) => line.replace(/^#{1,6}\s+/, '').trim().toLowerCase().includes(wanted));
      if (index >= 0) offset = lines.slice(0, index).reduce((n, line) => n + line.length + 1, 0);
    }
    editor.focus(); editor.setSelectionRange(offset, offset); editor.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };
  globalThis.addEventListener('devpilot:artifact-finding-navigate', findingNavigation as EventListener);
  (root as HTMLElement & { setDocument?: (document?: WorkspaceDocumentResource) => void }).setDocument = setDocument;
  draw();
  return root;
}

function actionButton(label: string, action: () => void, disabled = false, className = ''): HTMLButtonElement { const button = document.createElement('button'); button.type = 'button'; button.textContent = label; button.disabled = disabled; if (className) button.className = className; button.addEventListener('click', action); return button; }
function appendDefinition(list: HTMLDListElement, term: string, value: string): void { const dt = document.createElement('dt'); dt.textContent = term; const dd = document.createElement('dd'); const code = document.createElement('code'); code.textContent = value; dd.append(code); list.append(dt, dd); }
function isConflict(error: unknown): boolean { if (!(error instanceof DevPilotApiError)) return false; const text = `${error.message} ${JSON.stringify(error.payload)}`; return /CONFLICT|STALE|PREIMAGE|OPTIMISTIC/i.test(text); }
function readableError(error: unknown): string { return error instanceof Error ? error.message : String(error); }

function renderHistory(revisions: ArtifactDraftRevisionSummary[], recover: (sha: string) => void, disabled: boolean): HTMLElement {
  const section = document.createElement('section'); section.className = 'artifact-version-history'; const h = document.createElement('h3'); h.textContent = 'Version history'; section.append(h);
  if (!revisions.length) { const p = document.createElement('p'); p.textContent = 'Aún no existen revisiones runtime.'; section.append(p); return section; }
  const list = document.createElement('ol');
  for (const revision of revisions) { const item = document.createElement('li'); const label = document.createElement('span'); label.textContent = `r${revision.revision} · ${revision.event} · ${revision.created_at} · ${revision.revision_sha256.slice(0, 12)}`; const button = actionButton('Recuperar', () => recover(revision.revision_sha256), disabled, 'button-secondary'); item.append(label, button); list.append(item); }
  section.append(list); return section;
}

function renderHintsInto(section: HTMLElement, content: string, extension: string): void {
  for (const node of Array.from(section.querySelectorAll('[data-generated-hint]'))) node.remove();
  const p = document.createElement('p'); p.dataset.generatedHint = 'true';
  if (extension !== '.json') p.textContent = 'Markdown: preview textual seguro; la validación estructural completa se ejecuta en el flujo Validate de GSDLC-04-D.';
  else {
    try { const parsed = JSON.parse(content); p.textContent = parsed && typeof parsed === 'object' ? 'JSON válido · estructura parseable. Schema específico se resolverá por Artifact Profile/validator.' : 'JSON válido, pero el valor raíz no es un objeto/array.'; }
    catch (error) { const details = error instanceof Error ? error.message : String(error); p.textContent = `JSON inválido: ${details}`; p.dataset.hintSeverity = 'block'; }
  }
  section.append(p);
}

function renderPreviewInto(section: HTMLElement, content: string, extension: string): void {
  for (const node of Array.from(section.querySelectorAll('[data-generated-preview]'))) node.remove();
  const container = document.createElement('div'); container.dataset.generatedPreview = 'true';
  if (extension === '.json') { const pre = document.createElement('pre'); try { pre.textContent = JSON.stringify(JSON.parse(content), null, 2); } catch { pre.textContent = content; } container.append(pre); }
  else renderMarkdownText(container, content);
  section.append(container);
}

function renderMarkdownText(container: HTMLElement, content: string): void {
  const lines = content.replace(/\r\n?/g, '\n').split('\n'); let code: HTMLPreElement | undefined;
  for (const line of lines) {
    if (line.trim().startsWith('```')) { if (code) { container.append(code); code = undefined; } else code = document.createElement('pre'); continue; }
    if (code) { code.textContent += `${line}\n`; continue; }
    const match = /^(#{1,6})\s+(.*)$/.exec(line); if (match) { const heading = document.createElement(`h${match[1].length}`); heading.textContent = match[2]; container.append(heading); continue; }
    const paragraph = document.createElement('p'); paragraph.textContent = line || ' '; container.append(paragraph);
  }
  if (code) container.append(code);
}
