// Contract route marker: ui.workspace-documents
import type { WorkspaceDocumentNode } from '../api/types';

export interface DocumentTreeOptions {
  nodes: WorkspaceDocumentNode[];
  selectedId?: string;
  onSelect: (documentId: string) => void;
}

export function renderDocumentTree(options: DocumentTreeOptions): HTMLElement {
  const section = document.createElement('section');
  section.className = 'document-tree';
  section.setAttribute('aria-label', 'Árbol de documentos del workspace');

  const heading = document.createElement('div');
  heading.className = 'document-tree__heading';
  const title = document.createElement('h2');
  title.textContent = 'Documentos';
  const count = document.createElement('span');
  count.className = 'muted';
  count.textContent = `${options.nodes.filter((node) => node.kind === 'document').length} documentos en esta página`;
  heading.append(title, count);
  section.append(heading);

  const list = document.createElement('ul');
  list.className = 'document-tree__list';
  list.setAttribute('role', 'tree');
  for (const node of options.nodes) {
    const item = document.createElement('li');
    item.setAttribute('role', 'treeitem');
    item.setAttribute('aria-level', String(Math.max(1, node.relative_path.split('/').length)));
    item.className = `document-tree__item document-tree__item--${node.kind}`;
    item.style.setProperty('--tree-depth', String(Math.max(0, node.relative_path.split('/').length - 1)));

    if (node.kind === 'folder') {
      const folder = document.createElement('span');
      folder.className = 'document-tree__folder';
      folder.textContent = `▸ ${node.name}`;
      const meta = document.createElement('small');
      meta.textContent = node.relative_path;
      item.append(folder, meta);
    } else {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'document-tree__document';
      button.dataset.documentId = node.document_id ?? node.node_id;
      if ((node.document_id ?? node.node_id) === options.selectedId) {
        button.classList.add('is-selected');
        button.setAttribute('aria-current', 'true');
      }
      button.disabled = !node.readable;
      button.addEventListener('click', () => options.onSelect(node.document_id ?? node.node_id));
      const label = document.createElement('span');
      label.textContent = node.name;
      const details = document.createElement('small');
      details.textContent = `${node.category} · ${formatBytes(node.size_bytes)}${node.readable ? '' : ' · BLOQUEADO POR TAMAÑO'}`;
      button.append(label, details);
      item.append(button);
    }
    list.append(item);
  }
  section.append(list);
  return section;
}

function formatBytes(value?: number | null): string {
  if (value === null || value === undefined) return 'tamaño desconocido';
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KiB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MiB`;
}
