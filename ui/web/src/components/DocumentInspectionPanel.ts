// ui.workspace-documents — UOC-002 read-only inspection surface
import type {
  WorkspaceDocumentDiffData,
  WorkspaceDocumentHistoryData,
  WorkspaceDocumentInspectionMetadata,
  WorkspaceDocumentLinksData,
  WorkspaceDocumentSearchResult,
} from '../api/types';

export interface DocumentInspectionPanelOptions {
  metadata?: WorkspaceDocumentInspectionMetadata;
  history?: WorkspaceDocumentHistoryData;
  diff?: WorkspaceDocumentDiffData;
  links?: WorkspaceDocumentLinksData;
  loading?: boolean;
  error?: string;
  onSelectCommit?: (commit: string) => void;
  onOpenDocument?: (documentId: string) => void;
}

export function renderDocumentInspectionPanel(options: DocumentInspectionPanelOptions): HTMLElement {
  const section = document.createElement('section');
  section.className = 'panel document-inspection-panel';
  section.setAttribute('aria-label', 'Inspección técnica del documento');

  const heading = document.createElement('div');
  heading.className = 'document-inspection-heading';
  const title = document.createElement('h3');
  title.textContent = 'Inspección técnica';
  const badge = document.createElement('span');
  badge.className = 'contract-badge status-pass';
  badge.textContent = 'READ-ONLY · UOC-002';
  heading.append(title, badge);
  section.append(heading);

  if (options.loading) {
    section.append(notice('loading', 'Consultando metadatos, Git, diff y relaciones…'));
    return section;
  }
  if (options.error) {
    section.append(notice(options.error.includes('403') ? 'block' : 'error', options.error));
    return section;
  }
  if (!options.metadata) {
    section.append(notice('empty', 'Seleccione un documento para inspeccionar su metadata, historia y relaciones.'));
    return section;
  }

  const summary = document.createElement('div');
  summary.className = 'document-inspection-grid';
  summary.append(
    metric('SHA-256', options.metadata.sha256 || '—', true),
    metric('Tamaño', formatBytes(options.metadata.size_bytes), false),
    metric('Clasificación', String(options.metadata.classification?.level ?? 'optional').toUpperCase(), false),
    metric('Git', gitStateLabel(options.metadata.git?.status), false),
  );
  section.append(summary);

  const frontmatter = document.createElement('details');
  frontmatter.open = true;
  const fmSummary = document.createElement('summary');
  fmSummary.textContent = 'Frontmatter parseado';
  const fmGrid = document.createElement('dl');
  fmGrid.className = 'document-inspection-definition-list';
  const fields = options.metadata.frontmatter?.fields ?? {};
  if (!Object.keys(fields).length) {
    const empty = document.createElement('p');
    empty.textContent = options.metadata.frontmatter?.has_frontmatter ? 'Frontmatter sin campos visibles.' : 'Este documento no contiene frontmatter Markdown.';
    frontmatter.append(fmSummary, empty);
  } else {
    for (const [key, value] of Object.entries(fields)) {
      const row = document.createElement('div');
      const term = document.createElement('dt');
      term.textContent = key;
      const description = document.createElement('dd');
      description.textContent = typeof value === 'string' ? value : JSON.stringify(value);
      row.append(term, description);
      fmGrid.append(row);
    }
    frontmatter.append(fmSummary, fmGrid);
  }
  section.append(frontmatter);

  section.append(renderHistory(options.history, options.onSelectCommit), renderDiff(options.diff), renderLinks(options.links, options.onOpenDocument));
  return section;
}

export function renderFullTextSearchResults(
  results: WorkspaceDocumentSearchResult[],
  summary: Record<string, unknown> | undefined,
  loading: boolean,
  error: string | undefined,
  onOpen: (documentId: string) => void,
): HTMLElement {
  const section = document.createElement('section');
  section.className = 'panel document-search-results';
  const heading = document.createElement('div');
  heading.className = 'document-inspection-heading';
  const title = document.createElement('h3');
  title.textContent = 'Resultados full-text';
  const details = document.createElement('span');
  details.textContent = `${Number(summary?.matching_total ?? results.length)} coincidencias · ${Number(summary?.cache_reindexed ?? 0)} reindexados · ${Number(summary?.cache_reused ?? 0)} reutilizados`;
  heading.append(title, details);
  section.append(heading);
  if (loading) {
    section.append(notice('loading', 'Actualizando índice local incremental…'));
    return section;
  }
  if (error) {
    section.append(notice(error.includes('403') ? 'block' : 'error', error));
    return section;
  }
  if (!results.length) {
    section.append(notice('empty', 'No hay coincidencias full-text para la consulta actual.'));
    return section;
  }
  const list = document.createElement('ul');
  list.className = 'document-search-result-list';
  for (const result of results) {
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'document-search-result-button';
    button.addEventListener('click', () => onOpen(result.document_id));
    const name = document.createElement('strong');
    name.textContent = result.title;
    const path = document.createElement('span');
    path.textContent = result.relative_path;
    const meta = document.createElement('span');
    meta.textContent = `${result.classification.toUpperCase()} · ${result.match_count} coincidencias${result.line_number ? ` · línea ${result.line_number}` : ''}`;
    const snippet = document.createElement('p');
    snippet.textContent = result.snippet || 'Coincidencia en nombre o ruta.';
    button.append(name, path, meta, snippet);
    item.append(button);
    list.append(item);
  }
  section.append(list);
  return section;
}

function renderHistory(history: WorkspaceDocumentHistoryData | undefined, onSelectCommit?: (commit: string) => void): HTMLElement {
  const details = document.createElement('details');
  details.open = true;
  const summary = document.createElement('summary');
  summary.textContent = 'Historial Git del documento';
  details.append(summary);
  const commits = history?.commits ?? [];
  if (!commits.length) {
    const empty = document.createElement('p');
    empty.textContent = 'Sin commits asociados al documento o workspace sin historial Git.';
    details.append(empty);
    return details;
  }
  const list = document.createElement('ol');
  list.className = 'document-history-list';
  for (const commit of commits) {
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'document-history-commit';
    button.addEventListener('click', () => onSelectCommit?.(commit.commit));
    const subject = document.createElement('strong');
    subject.textContent = commit.subject || commit.short_commit;
    const meta = document.createElement('span');
    meta.textContent = `${commit.short_commit} · ${commit.author_name ?? 'autor desconocido'} · ${commit.authored_at ?? 'fecha desconocida'}`;
    button.append(subject, meta);
    item.append(button);
    list.append(item);
  }
  details.append(list);
  return details;
}

function renderDiff(diff: WorkspaceDocumentDiffData | undefined): HTMLElement {
  const details = document.createElement('details');
  const summary = document.createElement('summary');
  const base = String(diff?.summary?.base_ref ?? 'HEAD');
  summary.textContent = `Diff read-only contra ${base}`;
  details.append(summary);
  const status = document.createElement('p');
  status.textContent = `Estado: ${gitStateLabel(diff?.git_status)}${diff?.summary?.truncated ? ' · TRUNCADO POR BUDGET' : ''}`;
  const pre = document.createElement('pre');
  pre.className = 'document-diff-viewer';
  pre.textContent = diff?.diff || 'Sin cambios visibles contra la referencia seleccionada.';
  details.append(status, pre);
  return details;
}

function renderLinks(links: WorkspaceDocumentLinksData | undefined, onOpenDocument?: (documentId: string) => void): HTMLElement {
  const details = document.createElement('details');
  const summary = document.createElement('summary');
  summary.textContent = `Relaciones documentales · ${links?.outgoing?.length ?? 0} salientes · ${links?.incoming?.length ?? 0} entrantes`;
  details.append(summary);
  const wrapper = document.createElement('div');
  wrapper.className = 'document-link-columns';
  wrapper.append(linkList('Enlaces salientes', links?.outgoing ?? [], onOpenDocument), linkList('Enlaces entrantes', links?.incoming ?? [], onOpenDocument));
  details.append(wrapper);
  return details;
}

function linkList(titleText: string, links: WorkspaceDocumentLinksData['outgoing'], onOpenDocument?: (documentId: string) => void): HTMLElement {
  const section = document.createElement('section');
  const title = document.createElement('h4');
  title.textContent = titleText;
  section.append(title);
  if (!links?.length) {
    const empty = document.createElement('p');
    empty.textContent = 'Sin relaciones registradas.';
    section.append(empty);
    return section;
  }
  const list = document.createElement('ul');
  for (const link of links) {
    const item = document.createElement('li');
    const documentId = link.document_id ?? link.source_document_id;
    if (documentId && onOpenDocument) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'text-link-button';
      button.textContent = `${link.label ?? link.source_relative_path ?? link.target ?? 'documento'} · ${link.kind ?? 'document'}`;
      button.addEventListener('click', () => onOpenDocument(documentId));
      item.append(button);
    } else {
      item.textContent = `${link.label ?? link.source_relative_path ?? link.target ?? 'relación'} · ${link.kind ?? (link.resolved ? 'document' : 'missing')}`;
    }
    list.append(item);
  }
  section.append(list);
  return section;
}

function metric(labelText: string, valueText: string, mono: boolean): HTMLElement {
  const wrapper = document.createElement('div');
  const label = document.createElement('span');
  label.textContent = labelText;
  const value = document.createElement('strong');
  value.textContent = valueText;
  if (mono) value.className = 'mono-wrap';
  wrapper.append(label, value);
  return wrapper;
}

function gitStateLabel(status: Record<string, unknown> | undefined): string {
  if (!status || !Object.keys(status).length) return 'no disponible';
  if (status.untracked) return 'untracked';
  if (status.renamed) return 'renamed';
  if (status.deleted) return 'deleted';
  if (status.staged && status.unstaged) return 'staged + unstaged';
  if (status.staged) return 'staged';
  if (status.unstaged) return 'unstaged';
  if (status.clean) return 'clean';
  return String(status.porcelain ?? 'desconocido');
}

function formatBytes(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  if (value < 1024) return `${value} B`;
  return `${(value / 1024).toFixed(1)} KiB`;
}

function notice(kind: string, message: string): HTMLElement {
  const element = document.createElement('div');
  element.className = `ui-state-notice ui-state-${kind}`;
  element.setAttribute('role', kind === 'error' || kind === 'block' ? 'alert' : 'status');
  element.textContent = message;
  return element;
}
