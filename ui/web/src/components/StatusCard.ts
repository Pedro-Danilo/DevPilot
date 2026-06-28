// POST-H-014-C contract marker: ui.dashboard
import type { DashboardStatus, DevPilotApplicationResponse } from '../api/types';

export interface StatusCardModel {
  title: string;
  description: string;
  response?: DevPilotApplicationResponse;
  error?: string;
}

export function deriveStatus(response?: DevPilotApplicationResponse, error?: string): DashboardStatus {
  if (error) return 'ERROR';
  if (!response) return 'PENDING';
  if (!response.ok && response.exit_code === 1) return 'FAIL';
  if (!response.ok && response.exit_code === 3) return 'ERROR';
  if (!response.ok) return 'BLOCK';
  const severities = response.findings?.map((finding) => String(finding.severity).toLowerCase()) ?? [];
  if (severities.some((severity) => severity === 'block' || severity === 'error')) return 'BLOCK';
  if (severities.some((severity) => severity === 'warning')) return 'WARN';
  return 'PASS';
}

function statusLabel(status: DashboardStatus): string {
  switch (status) {
    case 'PASS':
      return 'PASS';
    case 'WARN':
      return 'WARN';
    case 'FAIL':
      return 'FAIL';
    case 'BLOCK':
      return 'BLOCK';
    case 'ERROR':
      return 'ERROR';
    default:
      return 'PENDING';
  }
}

export function renderStatusCard(model: StatusCardModel): HTMLElement {
  const status = deriveStatus(model.response, model.error);
  const card = document.createElement('section');
  card.className = `status-card status-card--${status.toLowerCase()}`;
  card.dataset.status = status;

  const header = document.createElement('div');
  header.className = 'status-card__header';

  const title = document.createElement('h2');
  title.textContent = model.title;

  const badge = document.createElement('span');
  badge.className = 'status-card__badge';
  badge.textContent = statusLabel(status);

  header.append(title, badge);

  const description = document.createElement('p');
  description.textContent = model.description;

  const message = document.createElement('p');
  message.className = 'status-card__message';
  message.textContent = model.error ?? model.response?.message ?? 'Pendiente de consulta.';

  const details = document.createElement('pre');
  details.className = 'status-card__details';
  details.textContent = summarizeResponse(model.response);

  card.append(header, description, message, details);
  return card;
}

function summarizeResponse(response?: DevPilotApplicationResponse): string {
  if (!response) return 'Sin datos todavía.';
  const summary = response.data?.summary ?? {};
  const findings = response.findings ?? [];
  return JSON.stringify({ operation: response.operation, ok: response.ok, summary, findings_total: findings.length }, null, 2);
}
