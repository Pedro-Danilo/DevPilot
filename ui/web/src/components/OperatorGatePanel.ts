// POST-H-015-D contract marker: ui.dashboard
import type { OperatorDashboardSnapshot } from '../api/types';

type GateState = 'PASS' | 'BLOCK' | 'UNKNOWN' | 'DISABLED BY POLICY';

interface GateDefinition {
  label: string;
  evaluate: (snapshot: OperatorDashboardSnapshot) => GateState;
}

const GATES: GateDefinition[] = [
  { label: 'local_first', evaluate: (value) => value.local_first ? 'PASS' : 'BLOCK' },
  { label: 'read_only', evaluate: (value) => value.read_only ? 'PASS' : 'BLOCK' },
  { label: 'dry_run', evaluate: (value) => value.dry_run ? 'PASS' : 'BLOCK' },
  { label: 'network', evaluate: (value) => value.network_used ? 'BLOCK' : 'PASS' },
  { label: 'external APIs', evaluate: (value) => value.external_api_used ? 'BLOCK' : 'DISABLED BY POLICY' },
  { label: 'source mutations', evaluate: (value) => value.mutations_performed ? 'BLOCK' : 'PASS' },
  { label: 'remote execution', evaluate: (value) => value.remote_execution_enabled ? 'BLOCK' : 'DISABLED BY POLICY' },
  { label: 'connector write', evaluate: (value) => value.connector_write_enabled ? 'BLOCK' : 'DISABLED BY POLICY' },
  { label: 'plugin execution', evaluate: (value) => value.plugin_execution_enabled ? 'BLOCK' : 'DISABLED BY POLICY' },
];

export function renderOperatorGatePanel(snapshot?: OperatorDashboardSnapshot): HTMLElement {
  const panel = document.createElement('section');
  panel.className = 'operator-gate-panel';
  panel.dataset.uiState = snapshot ? 'ready' : 'unknown';
  const title = document.createElement('h3');
  title.textContent = 'No-go gates';
  const description = document.createElement('p');
  description.textContent = snapshot
    ? 'PASS indica una condición segura verificada. DISABLED BY POLICY indica una capacidad sensible deshabilitada intencionalmente.'
    : 'UNKNOWN: todavía no existe un snapshot operacional; este estado no equivale a BLOCK.';
  const list = document.createElement('ul');
  list.className = 'operator-gate-list';
  for (const gate of GATES) {
    const state: GateState = snapshot ? gate.evaluate(snapshot) : 'UNKNOWN';
    const item = document.createElement('li');
    item.className = `operator-gate-list__item operator-gate-list__item--${stateClass(state)}`;
    item.textContent = `${state} · ${gate.label}`;
    list.append(item);
  }
  panel.append(title, description, list);
  return panel;
}

function stateClass(state: GateState): string {
  if (state === 'PASS') return 'pass';
  if (state === 'BLOCK') return 'block';
  if (state === 'DISABLED BY POLICY') return 'disabled';
  return 'unknown';
}
