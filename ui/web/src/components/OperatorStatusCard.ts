// POST-H-015-D contract marker: ui.dashboard
import type { OperatorDashboardSection } from '../api/types';

export interface OperatorStatusCardModel {
  sectionId: string;
  section: OperatorDashboardSection;
}

export function renderOperatorStatusCard(model: OperatorStatusCardModel): HTMLElement {
  const card = document.createElement('article');
  card.className = `operator-card operator-card--${statusClass(model.section.status)}`;
  card.dataset.operatorSection = model.sectionId;
  card.dataset.status = String(model.section.status ?? 'unknown').toUpperCase();

  const header = document.createElement('div');
  header.className = 'operator-card__header';

  const title = document.createElement('h3');
  title.textContent = model.section.title || titleFromId(model.sectionId);

  const badge = document.createElement('span');
  badge.className = 'operator-card__badge';
  badge.textContent = String(model.section.status ?? 'unknown').toUpperCase();

  header.append(title, badge);

  const summary = document.createElement('p');
  summary.className = 'operator-card__summary';
  summary.textContent = model.section.summary || 'Sin resumen operacional.';

  const metrics = document.createElement('dl');
  metrics.className = 'operator-card__metrics';
  for (const [key, value] of Object.entries(model.section.metrics ?? {})) {
    const term = document.createElement('dt');
    term.textContent = key;
    const description = document.createElement('dd');
    description.textContent = formatValue(value);
    metrics.append(term, description);
  }

  const sources = document.createElement('ul');
  sources.className = 'operator-card__sources';
  for (const ref of model.section.source_refs ?? []) {
    const item = document.createElement('li');
    item.dataset.required = String(Boolean(ref.required));
    item.dataset.available = String(Boolean(ref.available));
    item.textContent = `${ref.available ? 'available' : 'missing'} · ${ref.required ? 'required' : 'optional'} · ${ref.kind ?? 'source'} · ${ref.path}`;
    sources.append(item);
  }

  if (!sources.children.length) {
    const item = document.createElement('li');
    item.textContent = 'Sin source_refs declarados.';
    sources.append(item);
  }

  card.append(header, summary);
  if (metrics.children.length) card.append(metrics);
  card.append(sources);
  return card;
}

function statusClass(status: unknown): string {
  const normalized = String(status ?? 'unknown').toLowerCase();
  if (['pass', 'warn', 'block', 'error', 'unknown'].includes(normalized)) return normalized;
  return 'unknown';
}

function titleFromId(sectionId: string): string {
  return sectionId
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return 'n/a';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
  return JSON.stringify(value);
}
