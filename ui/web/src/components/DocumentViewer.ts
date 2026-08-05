// Contract route marker: ui.workspace-documents
import type { WorkspaceDocumentResource } from '../api/types';
import { renderUiStateNotice } from './ContractBadges';

export interface DocumentViewerOptions {
  document?: WorkspaceDocumentResource;
  loading?: boolean;
  error?: string;
}

export function renderDocumentViewer(options: DocumentViewerOptions): HTMLElement {
  const section = document.createElement('section');
  section.className = 'document-viewer';
  section.setAttribute('aria-label', 'Visor read-only de documento');

  if (options.loading) {
    section.append(renderUiStateNotice('loading', 'Leyendo el documento seleccionado mediante identificador opaco…'));
    return section;
  }
  if (options.error) {
    section.append(renderUiStateNotice('error', options.error));
    return section;
  }
  if (!options.document) {
    section.append(renderUiStateNotice('empty', 'Selecciona un documento permitido para inspeccionarlo.'));
    return section;
  }

  const resource = options.document;
  const header = document.createElement('header');
  header.className = 'document-viewer__header';
  const titleBlock = document.createElement('div');
  const title = document.createElement('h2');
  title.textContent = resource.name;
  const path = document.createElement('code');
  path.textContent = resource.relative_path;
  titleBlock.append(title, path);
  const badges = document.createElement('div');
  badges.className = 'context-badges';
  badges.append(
    badge('READ-ONLY', 'pass'),
    badge((resource.extension ?? 'text').toUpperCase(), 'pending'),
    badge(resource.category.toUpperCase(), 'pending'),
    badge(viewModeLabel(resource), 'pending'),
  );
  header.append(titleBlock, badges);
  section.append(header, renderBreadcrumbs(resource));

  const metadata = document.createElement('dl');
  metadata.className = 'document-viewer__metadata';
  metadata.append(
    meta('SHA-256', resource.sha256 ?? 'no calculado'),
    meta('Tamaño', `${resource.size_bytes ?? 0} bytes`),
    meta('Modificado', resource.modified_at ?? 'no informado'),
    meta('Encoding', resource.encoding ?? 'no informado'),
  );
  section.append(metadata);

  const content = document.createElement('article');
  content.className = 'document-viewer__content';
  if (resource.extension === '.md') renderSafeMarkdown(content, resource.content ?? '');
  else if (resource.extension === '.json' && resource.structured !== null && resource.structured !== undefined) {
    const pre = document.createElement('pre');
    pre.className = 'document-viewer__code';
    pre.textContent = JSON.stringify(resource.structured, null, 2);
    content.append(pre);
  } else {
    const pre = document.createElement('pre');
    pre.className = 'document-viewer__code';
    pre.textContent = resource.content ?? '';
    content.append(pre);
  }
  section.append(content);
  return section;
}

function renderBreadcrumbs(resource: WorkspaceDocumentResource): HTMLElement {
  const nav = document.createElement('nav');
  nav.className = 'document-breadcrumbs';
  nav.setAttribute('aria-label', 'Ruta relativa del documento');
  for (const [index, item] of (resource.breadcrumbs ?? []).entries()) {
    const crumb = document.createElement('span');
    crumb.textContent = item.label;
    nav.append(crumb);
    if (index < (resource.breadcrumbs ?? []).length - 1) {
      const separator = document.createElement('span');
      separator.className = 'document-breadcrumbs__separator';
      separator.textContent = '/';
      nav.append(separator);
    }
  }
  return nav;
}

function renderSafeMarkdown(target: HTMLElement, source: string): void {
  const parsed = splitFrontmatter(source);
  if (parsed.frontmatter.length) renderFrontmatter(target, parsed.frontmatter);
  source = parsed.body;
  let codeFence = false;
  let codeLines: string[] = [];
  let list: HTMLUListElement | null = null;
  const flushList = (): void => {
    if (list) target.append(list);
    list = null;
  };
  const flushCode = (): void => {
    const pre = document.createElement('pre');
    pre.className = 'document-viewer__code';
    const code = document.createElement('code');
    code.textContent = codeLines.join('\n');
    pre.append(code);
    target.append(pre);
    codeLines = [];
  };

  for (const rawLine of source.split(/\r?\n/)) {
    if (rawLine.trim().startsWith('```')) {
      flushList();
      if (codeFence) flushCode();
      codeFence = !codeFence;
      continue;
    }
    if (codeFence) {
      codeLines.push(rawLine);
      continue;
    }
    const heading = /^(#{1,6})\s+(.+)$/.exec(rawLine);
    if (heading) {
      flushList();
      const element = document.createElement(`h${heading[1].length}`);
      element.textContent = heading[2];
      target.append(element);
      continue;
    }
    const listItem = /^\s*[-*+]\s+(.+)$/.exec(rawLine);
    if (listItem) {
      if (!list) list = document.createElement('ul');
      const item = document.createElement('li');
      item.textContent = listItem[1];
      list.append(item);
      continue;
    }
    flushList();
    if (!rawLine.trim()) continue;
    const paragraph = document.createElement('p');
    paragraph.textContent = rawLine;
    target.append(paragraph);
  }
  flushList();
  if (codeFence || codeLines.length) flushCode();
}

function badge(text: string, state: string): HTMLElement {
  const item = document.createElement('span');
  item.className = `badge ${state}`;
  item.textContent = text;
  return item;
}

function meta(label: string, value: string): HTMLElement {
  const wrapper = document.createElement('div');
  const term = document.createElement('dt');
  term.textContent = label;
  const description = document.createElement('dd');
  description.textContent = value;
  wrapper.append(term, description);
  return wrapper;
}

function splitFrontmatter(source: string): { frontmatter: string[]; body: string } {
  const lines = source.split(/\r?\n/);
  if (lines[0]?.trim() !== '---') return { frontmatter: [], body: source };
  const closing = lines.slice(1).findIndex((line) => line.trim() === '---');
  if (closing < 0) return { frontmatter: [], body: source };
  const end = closing + 1;
  return { frontmatter: lines.slice(1, end), body: lines.slice(end + 1).join('\n') };
}

function renderFrontmatter(target: HTMLElement, lines: string[]): void {
  const details = document.createElement('details');
  details.className = 'document-frontmatter';
  const summary = document.createElement('summary');
  summary.textContent = 'Metadatos de frontmatter';
  const list = document.createElement('dl');
  for (const line of lines) {
    const match = /^([A-Za-z0-9_.-]+):\s*(.*)$/.exec(line);
    if (!match) continue;
    const wrapper = document.createElement('div');
    const term = document.createElement('dt');
    term.textContent = match[1];
    const value = document.createElement('dd');
    value.textContent = match[2] || '—';
    wrapper.append(term, value);
    list.append(wrapper);
  }
  details.append(summary, list);
  target.append(details);
}

function viewModeLabel(resource: WorkspaceDocumentResource): string {
  if (resource.extension === '.json' && resource.structured !== null && resource.structured !== undefined) return 'ESTRUCTURADO';
  if (resource.extension === '.md') return 'MARKDOWN SEGURO';
  return 'RAW SEGURO';
}
