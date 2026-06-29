import { DevPilotApiClient, readStoredToken, storeToken } from '../api/client';
import type { DashboardSnapshot, DevPilotApplicationResponse } from '../api/types';
import { renderFindingList } from '../components/FindingList';
import { renderStatusCard } from '../components/StatusCard';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { renderReportTraceView } from './ReportTraceView';
import { renderApprovalCenterView } from './ApprovalCenterView';
import { renderSettingsView } from './SettingsView';
import { renderOperatorDashboard } from './OperatorDashboard';

interface DashboardState {
  loading: boolean;
  token: string;
  snapshot: DashboardSnapshot;
  errors: Record<string, string>;
}

const CARD_META = {
  workspace: ['Workspace', 'Estado del proyecto local y readiness base.'],
  readiness: ['Readiness', 'Gate estricto de artefactos MIPSoftware/MIASI.'],
  standards: ['Standards', 'Estado de estándares locales y perfiles de validación.'],
  miasi: ['MIASI', 'Estado de registries agent/tool/policy.'],
} as const;

export function renderDashboard(root: HTMLElement): void {
  const state: DashboardState = {
    loading: false,
    token: readStoredToken(),
    snapshot: {},
    errors: {},
  };

  async function refresh(): Promise<void> {
    state.loading = true;
    state.errors = {};
    draw();
    const client = new DevPilotApiClient({ token: state.token });
    const tasks: Array<[keyof DashboardSnapshot, () => Promise<DevPilotApplicationResponse<any>>]> = [
      ['operator', () => client.operatorDashboard(false)],
      ['workspace', () => client.workspaceStatus()],
      ['readiness', () => client.readiness(true)],
      ['standards', () => client.standardsStatus()],
      ['miasi', () => client.miasiStatus()],
    ];

    const entries = await Promise.all(
      tasks.map(async ([key, loader]) => {
        try {
          return [key, await loader(), undefined] as const;
        } catch (error) {
          return [key, undefined, error instanceof Error ? error.message : String(error)] as const;
        }
      })
    );

    for (const [key, response, error] of entries) {
      if (response) state.snapshot[key] = response;
      if (error) state.errors[key] = error;
    }
    state.loading = false;
    draw();
  }

  function draw(): void {
    root.replaceChildren();
    root.append(renderHeader(state, refresh));
    root.append(renderOperatorDashboard(state.snapshot.operator, state.errors.operator));

    const grid = document.createElement('main');
    grid.className = 'dashboard-grid';
    for (const key of Object.keys(CARD_META) as Array<keyof typeof CARD_META>) {
      const [title, description] = CARD_META[key];
      grid.append(renderStatusCard({ title, description, response: state.snapshot[key], error: state.errors[key] }));
    }
    root.append(grid);
    if (state.loading) {
      root.append(renderUiStateNotice('loading', 'POST-H-015-D ui.dashboard loading state: consultando API local con token del operador.'));
    }
    if (!state.loading && !Object.keys(state.snapshot).length) {
      root.append(renderUiStateNotice('empty', 'POST-H-015-D ui.dashboard empty state: agrega token local y actualiza para consultar el API.'));
    }
    if (Object.keys(state.errors).length) {
      root.append(renderUiStateNotice('error', 'POST-H-015-D ui.dashboard error state: BLOCK/ERROR se muestra y no se oculta detrás de estado exitoso.'));
    }

    const allFindings = Object.values(state.snapshot)
      .flatMap((response) => response?.findings ?? [])
      .filter((finding) => ['warning', 'block', 'error'].includes(String(finding.severity).toLowerCase()));
    root.append(renderFindingList(allFindings));
    root.append(renderReportTraceView(() => state.token));
    root.append(renderApprovalCenterView(() => state.token));
    const settingsWrapper = document.createElement('div');
    settingsWrapper.innerHTML = renderSettingsView(new DevPilotApiClient({ token: state.token }), () => state.token);
    root.append(settingsWrapper);
  }

  draw();
  if (state.token) {
    void refresh();
  }
}

function renderHeader(state: DashboardState, refresh: () => Promise<void>): HTMLElement {
  const header = document.createElement('header');
  header.className = 'app-header';

  const titleBlock = document.createElement('div');
  const title = document.createElement('h1');
  title.textContent = 'DevPilot Local Dashboard';
  const subtitle = document.createElement('p');
  subtitle.textContent = 'POST-H-015-D · ui.dashboard · operator snapshot · local-first · dry-run visible · PASS/FAIL/BLOCK/ERROR explícitos.';
  titleBlock.append(title, subtitle, renderContractBadges('ui.dashboard', { warning: 'Shell local: no SaaS, no connector write, no plugin execution.' }));

  const form = document.createElement('form');
  form.className = 'token-form';
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const tokenInput = form.querySelector<HTMLInputElement>('input[name="token"]');
    state.token = tokenInput?.value ?? '';
    storeToken(state.token);
    void refresh();
  });

  const label = document.createElement('label');
  label.textContent = 'Token local';

  const input = document.createElement('input');
  input.name = 'token';
  input.type = 'password';
  input.placeholder = 'Pega DEVPILOT_API_TOKEN';
  input.value = state.token;
  input.autocomplete = 'off';

  const button = document.createElement('button');
  button.type = 'submit';
  button.textContent = state.loading ? 'Consultando…' : 'Actualizar dashboard';
  button.disabled = state.loading;

  label.append(input);
  form.append(label, button);
  header.append(titleBlock, form);
  return header;
}
