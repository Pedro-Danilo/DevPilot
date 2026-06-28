// POST-H-014-C contract markers: ui.reports ui.traces
import type { DevPilotFinding } from '../api/types';

export function renderFindingTable(findings: DevPilotFinding[]): HTMLElement {
  const container = document.createElement('div');
  container.className = 'finding-table';

  if (!findings.length) {
    const empty = document.createElement('p');
    empty.textContent = 'No hay findings para los filtros actuales.';
    container.append(empty);
    return container;
  }

  const table = document.createElement('table');
  table.innerHTML = '<thead><tr><th>Severidad</th><th>ID</th><th>Mensaje</th><th>Ruta</th></tr></thead>';
  const body = document.createElement('tbody');
  for (const finding of findings.slice(0, 50)) {
    const row = document.createElement('tr');
    row.className = `finding-row finding-row--${String(finding.severity).toLowerCase()}`;
    for (const value of [finding.severity, finding.id, finding.message, finding.path ?? '']) {
      const cell = document.createElement('td');
      cell.textContent = String(value ?? '');
      row.append(cell);
    }
    body.append(row);
  }
  table.append(body);
  container.append(table);
  return container;
}
