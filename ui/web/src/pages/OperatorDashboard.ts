// POST-H-015-D contract marker: ui.dashboard
import type { DevPilotApplicationResponse, OperatorDashboardResponseData } from '../api/types';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { renderOperatorGatePanel } from '../components/OperatorGatePanel';
import { renderOperatorNextActions } from '../components/OperatorNextActions';
import { renderOperatorStatusCard } from '../components/OperatorStatusCard';

export function renderOperatorDashboard(
  response?: DevPilotApplicationResponse<OperatorDashboardResponseData>,
  error?: string,
): HTMLElement {
  const section = document.createElement('section');
  section.className = 'operator-dashboard';
  section.dataset.uiRoute = 'ui.dashboard';
  section.dataset.postH = 'POST-H-015-D';

  const header = document.createElement('div');
  header.className = 'operator-dashboard__header';

  const titleBlock = document.createElement('div');
  const title = document.createElement('h2');
  title.textContent = 'Operator Dashboard';
  const subtitle = document.createElement('p');
  subtitle.textContent = 'POST-H-015-D · snapshot operacional local · source-linked · no-go visible · API-only.';
  titleBlock.append(title, subtitle, renderContractBadges('ui.dashboard', { warning: 'Operator UI read-only: no remote execution, no connector write, no plugin execution.' }));

  const status = document.createElement('div');
  status.className = `operator-dashboard__status operator-dashboard__status--${statusClass(response, error)}`;
  status.textContent = error ? 'ERROR' : response?.data?.snapshot?.status?.toUpperCase() ?? 'PENDING';

  header.append(titleBlock, status);
  section.append(header);

  if (error) {
    section.append(renderUiStateNotice('error', `POST-H-015-D ui.dashboard error state: ${error}`));
    section.append(renderOperatorGatePanel(undefined));
    return section;
  }

  if (!response) {
    section.append(renderUiStateNotice('empty', 'POST-H-015-D ui.dashboard empty state: actualiza con token local para consultar /operator/dashboard.'));
    section.append(renderOperatorGatePanel(undefined));
    return section;
  }

  const snapshot = response.data?.snapshot;
  if (!snapshot) {
    section.append(renderUiStateNotice('block', 'POST-H-015-D ui.dashboard block state: la respuesta no contiene snapshot operacional.'));
    section.append(renderOperatorGatePanel(undefined));
    return section;
  }

  const meta = document.createElement('div');
  meta.className = 'operator-dashboard__meta';
  meta.textContent = `Snapshot ${snapshot.snapshot_id} · workspace ${snapshot.workspace_id} · generado ${snapshot.generated_at_utc}`;
  section.append(meta);

  const grid = document.createElement('div');
  grid.className = 'operator-dashboard__grid';
  for (const [sectionId, item] of Object.entries(snapshot.sections ?? {})) {
    grid.append(renderOperatorStatusCard({ sectionId, section: item }));
  }

  const decisionGrid = document.createElement('div');
  decisionGrid.className = 'operator-dashboard__decision-grid';
  decisionGrid.append(renderOperatorGatePanel(snapshot), renderOperatorNextActions(snapshot.recommended_next_actions ?? []));

  section.append(grid, decisionGrid);
  return section;
}

function statusClass(response?: DevPilotApplicationResponse<OperatorDashboardResponseData>, error?: string): string {
  if (error) return 'error';
  const status = String(response?.data?.snapshot?.status ?? 'pending').toLowerCase();
  if (['pass', 'warn', 'block', 'error'].includes(status)) return status;
  return 'pending';
}
