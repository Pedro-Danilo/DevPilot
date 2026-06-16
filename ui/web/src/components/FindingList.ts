import type { DevPilotFinding } from '../api/types';

export function renderFindingList(findings: DevPilotFinding[]): HTMLElement {
  const section = document.createElement('section');
  section.className = 'finding-list';

  const title = document.createElement('h2');
  title.textContent = 'Findings relevantes';
  section.append(title);

  if (!findings.length) {
    const empty = document.createElement('p');
    empty.textContent = 'No hay findings críticos en la vista actual.';
    section.append(empty);
    return section;
  }

  const list = document.createElement('ul');
  for (const finding of findings.slice(0, 8)) {
    const item = document.createElement('li');
    item.className = `finding finding--${String(finding.severity).toLowerCase()}`;
    item.textContent = `${finding.severity.toUpperCase()} · ${finding.id} · ${finding.message}`;
    list.append(item);
  }
  section.append(list);
  return section;
}
