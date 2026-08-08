import { DevPilotApiClient } from '../api/client';
import type {
  DevPilotApplicationResponse,
  WorkspaceDocumentDiffData,
  WorkspaceDocumentHistoryData,
  WorkspaceDocumentInspectionMetadata,
  WorkspaceDocumentLinksData,
  WorkspaceDocumentNode,
  WorkspaceDocumentResource,
  WorkspaceDocumentSearchResult,
} from '../api/types';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { renderDocumentInspectionPanel, renderFullTextSearchResults } from '../components/DocumentInspectionPanel';
import { renderDocumentTree } from '../components/DocumentTree';
import { createDocumentValidationPanel } from '../components/DocumentValidationPanel';
import { renderDocumentViewer } from '../components/DocumentViewer';
import { renderWorkspaceContextPanel } from '../components/WorkspaceContextPanel';

interface WorkspaceDocumentsState {
  loading: boolean;
  detailLoading: boolean;
  nodes: WorkspaceDocumentNode[];
  selectedId?: string;
  selected?: WorkspaceDocumentResource;
  listResponse?: DevPilotApplicationResponse;
  listError?: string;
  detailError?: string;
  inspectionLoading: boolean;
  inspectionError?: string;
  inspectionMetadata?: WorkspaceDocumentInspectionMetadata;
  inspectionHistory?: WorkspaceDocumentHistoryData;
  inspectionDiff?: WorkspaceDocumentDiffData;
  inspectionLinks?: WorkspaceDocumentLinksData;
  selectedDiffRef: string;
  fullTextQuery: string;
  searchLoading: boolean;
  searchError?: string;
  searchResults: WorkspaceDocumentSearchResult[];
  searchSummary?: Record<string, unknown>;
  query: string;
  extension: string;
  category: string;
  offset: number;
  limit: number;
  matchingTotal: number;
  documentsTotal: number;
  foldersTotal: number;
  returnedDocuments: number;
  returnedFolders: number;
  elapsedMs?: number;
  nextOffset?: number | null;
  focusLine?: number | null;
  focusSection?: string | null;
  renderError?: string;
  navigationOrigin?: 'finding' | 'traceability';
  navigationLabel?: string;
}

export function renderWorkspaceDocumentsView(tokenProvider: () => string): HTMLElement {
  const root = document.createElement('div');
  root.className = 'workspace-documents-view';
  root.dataset.devpilotUiContract = 'ui.workspace-documents';
  const deepLinkedId = new URLSearchParams(globalThis.location.search).get('document') ?? undefined;
  const state: WorkspaceDocumentsState = {
    loading: false,
    detailLoading: false,
    inspectionLoading: false,
    selectedDiffRef: 'HEAD',
    fullTextQuery: '',
    searchLoading: false,
    searchResults: [],
    nodes: [],
    selectedId: deepLinkedId,
    query: '',
    extension: '',
    category: '',
    offset: 0,
    limit: 100,
    matchingTotal: 0,
    documentsTotal: 0,
    foldersTotal: 0,
    returnedDocuments: 0,
    returnedFolders: 0,
  };
  let listRequestSequence = 0;
  let documentRequestSequence = 0;
  const validationPanel = createDocumentValidationPanel({
    tokenProvider,
    onNavigate: async (navigation, origin) => {
      if (!navigation.document_id) return;
      state.focusLine = navigation.line;
      state.focusSection = navigation.section;
      await loadDocument(navigation.document_id, true, { origin, label: navigation.relative_path });
      if (state.detailError) throw new Error(state.detailError);
    },
  });

  async function load(resetOffset = false): Promise<void> {
    if (state.loading) return;
    const requestSequence = ++listRequestSequence;
    if (resetOffset) state.offset = 0;
    state.loading = true;
    state.listError = undefined;
    draw();
    const client = new DevPilotApiClient({ token: tokenProvider() });
    try {
      const response = await client.listWorkspaceDocuments({
        limit: state.limit,
        offset: state.offset,
        query: state.query,
        extension: state.extension,
        category: state.category,
      });
      if (requestSequence !== listRequestSequence) return;
      state.listResponse = response;
      const data = response.data as { nodes?: WorkspaceDocumentNode[]; summary?: Record<string, unknown> };
      state.nodes = Array.isArray(data.nodes) ? data.nodes : [];
      const summary = data.summary ?? {};
      state.matchingTotal = Number(summary.matching_total ?? state.nodes.length);
      state.documentsTotal = Number(summary.documents_total ?? state.nodes.filter((node) => node.kind === 'document').length);
      state.foldersTotal = Number(summary.folders_total ?? state.nodes.filter((node) => node.kind === 'folder').length);
      state.returnedDocuments = state.nodes.filter((node) => node.kind === 'document').length;
      state.returnedFolders = state.nodes.filter((node) => node.kind === 'folder').length;
      state.elapsedMs = summary.elapsed_ms === undefined ? undefined : Number(summary.elapsed_ms);
      state.nextOffset = summary.next_offset === null || summary.next_offset === undefined ? null : Number(summary.next_offset);
      if (state.selectedId && !state.selected) await loadDocument(state.selectedId, false);
    } catch (error) {
      if (requestSequence !== listRequestSequence) return;
      state.nodes = [];
      state.listError = error instanceof Error ? error.message : String(error);
    } finally {
      if (requestSequence === listRequestSequence) {
        state.loading = false;
        draw();
      }
    }
  }

  async function loadDocument(
    documentId: string,
    updateUrl = true,
    navigationContext?: { origin: 'finding' | 'traceability'; label?: string },
  ): Promise<void> {
    const requestSequence = ++documentRequestSequence;
    state.selectedId = documentId;
    state.navigationOrigin = navigationContext?.origin;
    state.navigationLabel = navigationContext?.label;
    state.focusLine = navigationContext ? state.focusLine : undefined;
    state.focusSection = navigationContext ? state.focusSection : undefined;
    state.detailLoading = true;
    state.detailError = undefined;
    state.selected = undefined;
    state.inspectionLoading = true;
    state.inspectionError = undefined;
    state.inspectionMetadata = undefined;
    state.inspectionHistory = undefined;
    state.inspectionDiff = undefined;
    state.inspectionLinks = undefined;
    state.selectedDiffRef = 'HEAD';
    if (updateUrl) {
      const url = new URL(globalThis.location.href);
      url.searchParams.set('document', documentId);
      globalThis.history.replaceState({}, '', url);
    }
    draw();
    const client = new DevPilotApiClient({ token: tokenProvider() });
    try {
      const [resource, metadata, history, diff, links] = await Promise.allSettled([
        client.readWorkspaceDocument(documentId),
        client.workspaceDocumentMetadata(documentId),
        client.workspaceDocumentHistory(documentId, 20, 0),
        client.workspaceDocumentDiff(documentId, state.selectedDiffRef),
        client.workspaceDocumentLinks(documentId),
      ]);
      if (requestSequence !== documentRequestSequence) return;
      if (resource.status === 'rejected') throw resource.reason;
      const data = resource.value.data as { document?: WorkspaceDocumentResource };
      state.selected = data.document;
      if (!state.selected) throw new Error(`La API no devolvió un documento utilizable para ${documentId}.`);
      if (metadata.status === 'fulfilled') state.inspectionMetadata = (metadata.value.data as { document?: WorkspaceDocumentInspectionMetadata }).document;
      if (history.status === 'fulfilled') state.inspectionHistory = history.value.data as WorkspaceDocumentHistoryData;
      if (diff.status === 'fulfilled') state.inspectionDiff = diff.value.data as WorkspaceDocumentDiffData;
      if (links.status === 'fulfilled') state.inspectionLinks = links.value.data as WorkspaceDocumentLinksData;
      const rejected = [metadata, history, diff, links].find((item) => item.status === 'rejected');
      if (rejected?.status === 'rejected') state.inspectionError = rejected.reason instanceof Error ? rejected.reason.message : String(rejected.reason);
    } catch (error) {
      if (requestSequence !== documentRequestSequence) return;
      state.detailError = error instanceof Error ? error.message : String(error);
    } finally {
      if (requestSequence === documentRequestSequence) {
        state.detailLoading = false;
        state.inspectionLoading = false;
        draw();
      }
    }
  }

  async function reloadDiff(baseRef: string): Promise<void> {
    if (!state.selectedId) return;
    state.selectedDiffRef = baseRef;
    state.inspectionLoading = true;
    state.inspectionError = undefined;
    draw();
    try {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      const response = await client.workspaceDocumentDiff(state.selectedId, baseRef);
      state.inspectionDiff = response.data as WorkspaceDocumentDiffData;
    } catch (error) {
      state.inspectionError = error instanceof Error ? error.message : String(error);
    } finally {
      state.inspectionLoading = false;
      draw();
    }
  }

  async function searchFullText(): Promise<void> {
    const query = state.fullTextQuery.trim();
    state.searchError = undefined;
    state.searchResults = [];
    state.searchSummary = undefined;
    if (query.length < 2) {
      state.searchError = 'La búsqueda full-text requiere al menos 2 caracteres.';
      draw();
      return;
    }
    state.searchLoading = true;
    draw();
    try {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      const response = await client.searchWorkspaceDocuments(query, 50, 0);
      const data = response.data as { results?: WorkspaceDocumentSearchResult[]; summary?: Record<string, unknown> };
      state.searchResults = Array.isArray(data.results) ? data.results : [];
      state.searchSummary = data.summary;
    } catch (error) {
      state.searchError = error instanceof Error ? error.message : String(error);
    } finally {
      state.searchLoading = false;
      draw();
    }
  }

  function draw(): void {
    try {
      const next = document.createDocumentFragment();
      next.append(renderIntroduction(), renderFilters(state, () => void load(true)), renderFullTextSearchForm(state, () => void searchFullText()));
      if (state.searchLoading || state.searchError || state.searchSummary) {
        next.append(renderFullTextSearchResults(state.searchResults, state.searchSummary, state.searchLoading, state.searchError, (id) => void loadDocument(id)));
      }
      const contextData = state.listResponse?.data as { ui_workspace_context?: Record<string, unknown> } | undefined;
      const context = contextData?.ui_workspace_context;
      const activeWorkspaceId = String(context?.active_workspace_id ?? '');
      const activeWorkspaceRoot = String(context?.active_workspace_root ?? context?.effective_workspace_root ?? '');
      const contextResponse = state.listResponse && context
        ? ({
          ...state.listResponse,
          data: {
            ui_workspace_context: context,
            summary: { active_workspace_id: activeWorkspaceId },
            workspaces: activeWorkspaceId ? [{
              workspace_id: activeWorkspaceId,
              active: true,
              root_path: activeWorkspaceRoot,
              status: context.valid === false ? 'blocked' : 'configured',
            }] : [],
          },
        } as DevPilotApplicationResponse)
        : undefined;
      next.append(renderGuarded(() => renderWorkspaceContextPanel(contextResponse, state.listError, state.elapsedMs), 'Contexto operativo'));

      if (state.loading && !state.nodes.length) next.append(renderUiStateNotice('loading', 'Construyendo índice bounded del workspace activo…'));
      else if (state.listError) next.append(renderUiStateNotice(state.listError.includes('403') ? 'block' : 'error', state.listError));
      else if (!state.nodes.length) next.append(renderUiStateNotice('empty', 'No hay documentos permitidos que coincidan con los filtros.'));

      const layout = document.createElement('div');
      layout.className = 'workspace-documents-layout';
      layout.append(
        renderGuarded(() => renderDocumentTree({
          nodes: state.nodes,
          selectedId: state.selectedId,
          returnedDocuments: state.returnedDocuments,
          returnedFolders: state.returnedFolders,
          onSelect: (id) => void loadDocument(id),
        }), 'Árbol de documentos'),
        renderGuarded(() => renderDocumentViewer({
          document: state.selected,
          loading: state.detailLoading,
          error: state.detailError,
          focusLine: state.focusLine,
          focusSection: state.focusSection,
          navigationOrigin: state.navigationOrigin,
          navigationLabel: state.navigationLabel,
          onReturnToValidation: () => {
            const selector = state.navigationOrigin === 'traceability' ? '.document-traceability' : '.validation-findings';
            const target = validationPanel.querySelector<HTMLElement>(selector) ?? validationPanel;
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            target.tabIndex = -1;
            target.focus({ preventScroll: true });
          },
        }), 'Visor de documento'),
      );
      next.append(layout, renderPagination(state, () => void load(false)));
      next.append(renderGuarded(() => renderDocumentInspectionPanel({
        metadata: state.inspectionMetadata,
        history: state.inspectionHistory,
        diff: state.inspectionDiff,
        links: state.inspectionLinks,
        loading: state.inspectionLoading,
        error: state.inspectionError,
        onSelectCommit: (commit) => void reloadDiff(commit),
        onOpenDocument: (id) => void loadDocument(id),
      }), 'Inspección técnica'));
      if (state.renderError) next.append(renderUiStateNotice('error', state.renderError));
      next.append(validationPanel);
      root.replaceChildren(next);
      state.renderError = undefined;
    } catch (error) {
      state.renderError = `La UI aisló un error de render sin perder el estado operativo: ${error instanceof Error ? error.message : String(error)}`;
      const fallback = document.createDocumentFragment();
      fallback.append(renderIntroduction(), renderUiStateNotice('error', state.renderError), validationPanel);
      root.replaceChildren(fallback);
    }
  }

  draw();
  if (tokenProvider()) void load();
  return root;
}


function renderGuarded(factory: () => HTMLElement, surface: string): HTMLElement {
  try {
    return factory();
  } catch (error) {
    const section = document.createElement('section');
    section.className = 'panel workspace-documents-render-boundary';
    section.dataset.renderBoundary = surface;
    section.append(renderUiStateNotice('error', `${surface}: la vista aisló un error de render y preservó el resto de la consola. ${error instanceof Error ? error.message : String(error)}`));
    return section;
  }
}

function renderIntroduction(): HTMLElement {
  const section = document.createElement('section');
  section.className = 'panel workspace-documents-intro';
  const title = document.createElement('h2');
  title.textContent = 'Explorador de documentos';
  const description = document.createElement('p');
  description.textContent = 'Explorador read-only del workspace activo. El navegador usa identificadores opacos y nunca entrega rutas absolutas como autoridad.';
  section.append(title, description, renderContractBadges('ui.workspace-documents', { dryRunLabel: 'Read-only', warning: 'UOC-003 preliminar: validación determinística y trazabilidad read-only; jobs asíncronos, cancelación y heartbeat llegan en UOC-007/UOC-008.' }));
  return section;
}

function renderFilters(state: WorkspaceDocumentsState, submit: () => void): HTMLElement {
  const form = document.createElement('form');
  form.className = 'document-filters panel';
  form.setAttribute('aria-label', 'Filtros de documentos');
  form.addEventListener('submit', (event) => { event.preventDefault(); submit(); });
  const query = input('Buscar por nombre o ruta relativa', 'search', state.query);
  query.input.addEventListener('input', () => { state.query = query.input.value; });
  const extension = select('Extensión', ['', '.md', '.json', '.yaml', '.yml', '.txt'], state.extension);
  extension.select.addEventListener('change', () => { state.extension = extension.select.value; });
  const category = select('Categoría', ['', 'product', 'requirements', 'architecture', 'security', 'quality', 'adr', 'documentation'], state.category);
  category.select.addEventListener('change', () => { state.category = category.select.value; });
  const button = document.createElement('button');
  button.type = 'submit';
  button.textContent = state.loading ? 'Consultando…' : 'Aplicar filtros';
  button.disabled = state.loading;
  form.append(query.label, extension.label, category.label, button);
  return form;
}

function renderFullTextSearchForm(state: WorkspaceDocumentsState, submit: () => void): HTMLElement {
  const form = document.createElement('form');
  form.className = 'document-fulltext-search panel';
  form.setAttribute('aria-label', 'Búsqueda full-text de documentos');
  form.addEventListener('submit', (event) => { event.preventDefault(); submit(); });
  const query = input('Buscar dentro de los documentos', 'search', state.fullTextQuery);
  query.input.placeholder = 'Ejemplo: SQLite, amenaza, criterio de aceptación';
  query.input.minLength = 2;
  query.input.maxLength = 200;
  query.input.addEventListener('input', () => { state.fullTextQuery = query.input.value; });
  const button = document.createElement('button');
  button.type = 'submit';
  button.textContent = state.searchLoading ? 'Indexando…' : 'Buscar contenido';
  button.disabled = state.searchLoading;
  const note = document.createElement('p');
  note.textContent = 'Índice incremental en memoria, aislado por workspace y sin persistencia externa de contenido.';
  form.append(query.label, button, note);
  return form;
}

function renderPagination(state: WorkspaceDocumentsState, load: () => void): HTMLElement {
  const nav = document.createElement('nav');
  nav.className = 'document-pagination';
  nav.setAttribute('aria-label', 'Paginación de documentos');
  const previous = document.createElement('button');
  previous.type = 'button';
  previous.textContent = '← Anterior';
  previous.disabled = state.loading || state.offset === 0;
  previous.addEventListener('click', () => { state.offset = Math.max(0, state.offset - state.limit); load(); });
  const status = document.createElement('span');
  const first = state.matchingTotal === 0 ? 0 : state.offset + 1;
  const last = Math.min(state.offset + state.nodes.length, state.matchingTotal);
  status.textContent = `${first}–${last} de ${state.matchingTotal} elementos · ${state.returnedDocuments} documentos · ${state.returnedFolders} carpetas`;
  status.setAttribute('aria-live', 'polite');
  const next = document.createElement('button');
  next.type = 'button';
  next.textContent = 'Siguiente →';
  next.disabled = state.loading || state.nextOffset === null || state.nextOffset === undefined;
  next.addEventListener('click', () => { state.offset = state.nextOffset ?? state.offset; load(); });
  nav.append(previous, status, next);
  return nav;
}

function input(labelText: string, type: string, value: string): { label: HTMLLabelElement; input: HTMLInputElement } {
  const label = document.createElement('label');
  label.textContent = labelText;
  const input = document.createElement('input');
  input.type = type;
  input.value = value;
  input.maxLength = 200;
  label.append(input);
  return { label, input };
}

function select(labelText: string, values: string[], current: string): { label: HTMLLabelElement; select: HTMLSelectElement } {
  const label = document.createElement('label');
  label.textContent = labelText;
  const select = document.createElement('select');
  for (const value of values) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value || 'Todos';
    option.selected = value === current;
    select.append(option);
  }
  label.append(select);
  return { label, select };
}
