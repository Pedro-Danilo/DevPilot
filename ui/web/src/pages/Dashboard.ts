import { DevPilotApiClient, DevPilotApiError, readStoredToken, storeToken } from '../api/client';
import type { DashboardSnapshot, DevPilotApplicationResponse } from '../api/types';
import { renderFindingList } from '../components/FindingList';
import { renderStatusCard } from '../components/StatusCard';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { renderOperatorDashboard } from './OperatorDashboard';
import { runBounded } from '../utils/async';

interface DashboardState {
  loading: boolean;
  warming: boolean;
  token: string;
  snapshot: DashboardSnapshot;
  errors: Record<string, string>;
  durations: Record<string, number>;
  completed: number;
  total: number;
  refreshedAt?: string;
}

const CARD_META = {
  workspace: ['Workspace', 'Estado del proyecto local y readiness base.'],
  readiness: ['Readiness', 'Gate estricto de artefactos MIPSoftware/MIASI.'],
  standards: ['Standards', 'Estado de estándares locales y perfiles de validación.'],
  miasi: ['MIASI', 'Estado de registries agent/tool/policy.'],
} as const;

const DASHBOARD_KEYS: Array<keyof DashboardSnapshot> = ['operator', 'workspace', 'readiness', 'standards', 'miasi'];

export function renderDashboard(root: HTMLElement): void {
  const state: DashboardState = {
    loading: false,
    warming: false,
    token: readStoredToken(),
    snapshot: {},
    errors: {},
    durations: {},
    completed: 0,
    total: DASHBOARD_KEYS.length,
  };

  async function refresh(): Promise<void> {
    if (state.loading) return;
    state.loading = true;
    state.warming = true;
    state.snapshot = {};
    state.errors = {};
    state.durations = {};
    state.completed = 0;
    state.refreshedAt = undefined;
    draw();

    const client = new DevPilotApiClient({ token: state.token });
    const warmupStarted = performance.now();
    try {
      state.snapshot.workspace = await client.protectedWarmup();
      state.durations.workspace = Math.round(performance.now() - warmupStarted);
      state.completed = 1;
      state.warming = false;
      draw();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      for (const key of DASHBOARD_KEYS) state.errors[String(key)] = message;
      state.completed = state.total;
      state.warming = false;
      state.loading = false;
      state.refreshedAt = new Date().toISOString();
      draw();
      return;
    }

    const tasks: Array<{ key: keyof DashboardSnapshot; run: () => Promise<DevPilotApplicationResponse<any>> }> = [
      { key: 'operator', run: () => client.operatorDashboard(false) },
      { key: 'readiness', run: () => client.readiness(true) },
      { key: 'standards', run: () => client.standardsStatus() },
      { key: 'miasi', run: () => client.miasiStatus() },
    ];

    await runBounded<DevPilotApplicationResponse<any>>(
      tasks.map((task) => ({ key: String(task.key), run: task.run })),
      2,
      (result) => {
        const key = result.key as keyof DashboardSnapshot;
        state.durations[result.key] = result.durationMs;
        if (result.value) state.snapshot[key] = result.value;
        if (result.error) state.errors[result.key] = result.error;
        state.completed += 1;
        draw();
      }
    );
    state.loading = false;
    state.refreshedAt = new Date().toISOString();
    draw();
  }

  function draw(): void {
    root.replaceChildren();
    root.append(renderHeader(state, refresh));
    root.append(renderConnectionSummary(state));
    root.append(renderOperatorDashboard(state.snapshot.operator, state.errors.operator));

    const grid = document.createElement('main');
    grid.className = 'dashboard-grid';
    for (const key of Object.keys(CARD_META) as Array<keyof typeof CARD_META>) {
      const [title, description] = CARD_META[key];
      const wrapper = document.createElement('div');
      wrapper.className = 'status-card-wrapper';
      wrapper.append(renderStatusCard({ title, description, response: state.snapshot[key], error: state.errors[key] }));
      const timing = document.createElement('p');
      timing.className = 'request-timing';
      timing.textContent = state.durations[key] === undefined ? 'Consulta pendiente.' : `Última consulta: ${state.durations[key]} ms.`;
      wrapper.append(timing);
      grid.append(wrapper);
    }
    root.append(grid);

    if (state.warming) root.append(renderUiStateNotice('loading', 'Warm-up protegido: esperando que la superficie autenticada de la API local esté lista antes de lanzar el resumen.'));
    else if (state.loading) root.append(renderUiStateNotice('loading', `Consultando API local de forma progresiva (${state.completed}/${state.total}); máximo 2 solicitudes simultáneas.`));
    if (!state.loading && !Object.keys(state.snapshot).length && !Object.keys(state.errors).length) root.append(renderUiStateNotice('empty', 'Agrega el token local y actualiza para consultar el estado real del sistema.'));
    if (Object.keys(state.errors).length) root.append(renderUiStateNotice('error', 'Una o más tarjetas no pudieron actualizarse. Los resultados exitosos permanecen visibles; use Reintentar para la consulta afectada.'));

    const allFindings = Object.values(state.snapshot)
      .flatMap((response) => response?.findings ?? [])
      .filter((finding) => ['warning', 'block', 'error'].includes(String(finding.severity).toLowerCase()));
    root.append(renderFindingList(allFindings));
    root.append(renderRouteSummaries());
  }

  draw();
  if (state.token) void refresh();
}

function renderHeader(state: DashboardState, refresh: () => Promise<void>): HTMLElement {
  const header = document.createElement('header');
  header.className = 'app-header';
  const titleBlock = document.createElement('div');
  const title = document.createElement('h1');
  title.textContent = 'DevPilot Local Dashboard';
  const subtitle = document.createElement('p');
  subtitle.textContent = 'Resumen operacional local. Las vistas detalladas se consultan solo al abrir su ruta para evitar fan-out duplicado.';
  titleBlock.append(title, subtitle, renderContractBadges('ui.dashboard', { warning: 'Local-first; no SaaS, connector write, plugin execution ni remote execution.' }));

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
  button.textContent = state.warming ? 'Preparando API…' : state.loading ? 'Consultando…' : 'Actualizar resumen';
  button.disabled = state.loading;
  button.setAttribute('aria-busy', String(state.loading));
  label.append(input);
  form.append(label, button);
  header.append(titleBlock, form);
  return header;
}

function renderConnectionSummary(state: DashboardState): HTMLElement {
  const panel = document.createElement('section');
  panel.className = 'connection-summary';
  const status = state.loading ? 'ACTUALIZANDO' : Object.keys(state.errors).length ? 'DEGRADADO' : Object.keys(state.snapshot).length ? 'OPERATIVO' : 'NO CONSULTADO';
  panel.innerHTML = `<strong>API local: ${status}</strong><span>http://127.0.0.1:8787</span><span>Progreso: ${state.completed}/${state.total}</span><span>Última actualización: ${state.refreshedAt ?? 'pendiente'}</span>`;
  return panel;
}

function renderRouteSummaries(): HTMLElement {
  const section = document.createElement('section');
  section.className = 'route-summary-grid';
  const routes = [
    ['/reports', 'Reportes', 'Índice y detalle de reportes locales.'],
    ['/traces', 'Trazas', 'Spans, eventos y métricas por traza.'],
    ['/approvals', 'Approval Center', 'Aprobaciones y acciones estrictamente dry-run.'],
    ['/settings', 'Configuración', 'Providers, política y postura de seguridad.'],
  ];
  for (const [href, title, description] of routes) {
    const link = document.createElement('a');
    link.href = href;
    link.className = 'route-summary-card';
    link.innerHTML = `<strong>${title}</strong><span>${description}</span><em>Abrir vista →</em>`;
    section.append(link);
  }
  return section;
}
