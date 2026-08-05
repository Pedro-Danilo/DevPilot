import { DevPilotApiClient } from '../api/client';
import type { DevPilotApplicationResponse, WorkspaceDocumentNode, WorkspaceDocumentResource } from '../api/types';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { renderDocumentTree } from '../components/DocumentTree';
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
  query: string;
  extension: string;
  category: string;
  offset: number;
  limit: number;
  matchingTotal: number;
  nextOffset?: number | null;
}

export function renderWorkspaceDocumentsView(tokenProvider: () => string): HTMLElement {
  const root = document.createElement('div');
  root.className = 'workspace-documents-view';
  root.dataset.devpilotUiContract = 'ui.workspace-documents';
  const deepLinkedId = new URLSearchParams(globalThis.location.search).get('document') ?? undefined;
  const state: WorkspaceDocumentsState = {
    loading: false,
    detailLoading: false,
    nodes: [],
    selectedId: deepLinkedId,
    query: '',
    extension: '',
    category: '',
    offset: 0,
    limit: 100,
    matchingTotal: 0,
  };

  async function load(resetOffset = false): Promise<void> {
    if (state.loading) return;
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
      state.listResponse = response;
      const data = response.data as { nodes?: WorkspaceDocumentNode[]; summary?: Record<string, unknown> };
      state.nodes = Array.isArray(data.nodes) ? data.nodes : [];
      const summary = data.summary ?? {};
      state.matchingTotal = Number(summary.matching_total ?? state.nodes.length);
      state.nextOffset = summary.next_offset === null || summary.next_offset === undefined ? null : Number(summary.next_offset);
      if (state.selectedId && !state.selected) await loadDocument(state.selectedId, false);
    } catch (error) {
      state.nodes = [];
      state.listError = error instanceof Error ? error.message : String(error);
    } finally {
      state.loading = false;
      draw();
    }
  }

  async function loadDocument(documentId: string, updateUrl = true): Promise<void> {
    state.selectedId = documentId;
    state.detailLoading = true;
    state.detailError = undefined;
    state.selected = undefined;
    if (updateUrl) {
      const url = new URL(globalThis.location.href);
      url.searchParams.set('document', documentId);
      globalThis.history.replaceState({}, '', url);
    }
    draw();
    const client = new DevPilotApiClient({ token: tokenProvider() });
    try {
      const response = await client.readWorkspaceDocument(documentId);
      const data = response.data as { document?: WorkspaceDocumentResource };
      state.selected = data.document;
    } catch (error) {
      state.detailError = error instanceof Error ? error.message : String(error);
    } finally {
      state.detailLoading = false;
      draw();
    }
  }

  function draw(): void {
    root.replaceChildren();
    root.append(renderIntroduction(), renderFilters(state, () => void load(true)));
    const contextData = state.listResponse?.data as { ui_workspace_context?: Record<string, unknown> } | undefined;
    const contextResponse = state.listResponse && contextData?.ui_workspace_context
      ? ({ ...state.listResponse, data: { ui_workspace_context: contextData.ui_workspace_context, summary: { active_workspace_id: contextData.ui_workspace_context.active_workspace_id } } } as DevPilotApplicationResponse)
      : undefined;
    root.append(renderWorkspaceContextPanel(contextResponse, state.listError));

    if (state.loading && !state.nodes.length) root.append(renderUiStateNotice('loading', 'Construyendo índice bounded del workspace activo…'));
    else if (state.listError) root.append(renderUiStateNotice(state.listError.includes('403') ? 'block' : 'error', state.listError));
    else if (!state.nodes.length) root.append(renderUiStateNotice('empty', 'No hay documentos permitidos que coincidan con los filtros.'));

    const layout = document.createElement('div');
    layout.className = 'workspace-documents-layout';
    layout.append(
      renderDocumentTree({ nodes: state.nodes, selectedId: state.selectedId, onSelect: (id) => void loadDocument(id) }),
      renderDocumentViewer({ document: state.selected, loading: state.detailLoading, error: state.detailError }),
    );
    root.append(layout, renderPagination(state, () => void load(false)));
  }

  draw();
  if (tokenProvider()) void load();
  return root;
}

function renderIntroduction(): HTMLElement {
  const section = document.createElement('section');
  section.className = 'panel workspace-documents-intro';
  const title = document.createElement('h1');
  title.textContent = 'Workspace Documents';
  const description = document.createElement('p');
  description.textContent = 'Explorador read-only del workspace activo. El navegador usa identificadores opacos y nunca entrega rutas absolutas como autoridad.';
  section.append(title, description, renderContractBadges('ui.workspace-documents', { dryRunLabel: 'Read-only', warning: 'Primera versión UOC-001: consulta y búsqueda por nombre; Git y búsqueda full-text llegan en UOC-002.' }));
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
  status.textContent = `${state.offset + Math.min(1, state.matchingTotal)}–${Math.min(state.offset + state.nodes.length, state.matchingTotal)} de ${state.matchingTotal}`;
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
