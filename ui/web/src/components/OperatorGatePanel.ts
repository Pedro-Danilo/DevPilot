// POST-H-015-D contract marker: ui.dashboard
import type { OperatorDashboardSnapshot } from '../api/types';

export function renderOperatorGatePanel(snapshot?: OperatorDashboardSnapshot): HTMLElement {
  const panel = document.createElement('section');
  panel.className = 'operator-gate-panel';
  panel.dataset.uiState = snapshot ? 'ready' : 'empty';

  const title = document.createElement('h3');
  title.textContent = 'No-go gates';

  const description = document.createElement('p');
  description.textContent = 'POST-H-015-D muestra explícitamente las banderas local-first/no-remote/no connector write/no plugin execution.';

  const flags = [
    ['local_first', snapshot?.local_first === true],
    ['read_only', snapshot?.read_only === true],
    ['dry_run', snapshot?.dry_run === true],
    ['network_used=false', snapshot?.network_used === false],
    ['external_api_used=false', snapshot?.external_api_used === false],
    ['mutations_performed=false', snapshot?.mutations_performed === false],
    ['remote_execution_enabled=false', snapshot?.remote_execution_enabled === false],
    ['connector_write_enabled=false', snapshot?.connector_write_enabled === false],
    ['plugin_execution_enabled=false', snapshot?.plugin_execution_enabled === false],
  ] as const;

  const list = document.createElement('ul');
  list.className = 'operator-gate-list';
  for (const [label, ok] of flags) {
    const item = document.createElement('li');
    item.className = ok ? 'operator-gate-list__item operator-gate-list__item--pass' : 'operator-gate-list__item operator-gate-list__item--block';
    item.textContent = `${ok ? 'PASS' : 'BLOCK'} · ${label}`;
    list.append(item);
  }

  panel.append(title, description, list);
  return panel;
}
