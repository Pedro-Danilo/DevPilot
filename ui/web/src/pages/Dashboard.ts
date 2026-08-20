import { renderUoc011BrowserStateFixture } from '../testing/Uoc011BrowserStateFixture';
import { DevPilotApiClient, DevPilotApiError, readProjectJourneyContext, readStoredToken, storeToken } from '../api/client';
import type { AuthSessionContext, DashboardSnapshot, DevPilotApplicationResponse } from '../api/types';
import { renderFindingList } from '../components/FindingList';
import { renderStatusCard } from '../components/StatusCard';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { renderOperatorDashboard } from './OperatorDashboard';
import { runBounded } from '../utils/async';
import { renderWorkspaceContextPanel } from '../components/WorkspaceContextPanel';
import { renderProjectHomeEntryPanel } from '../components/ProjectHomeEntryPanel';

interface DashboardState {
  loading: boolean;
  warming: boolean;
  token: string;
  health?: DevPilotApplicationResponse;
  healthError?: string;
  healthDuration?: number;
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
const DASHBOARD_TOTAL = DASHBOARD_KEYS.length + 1;

export function renderDashboard(root: HTMLElement, session: AuthSessionContext, guardReason: string | null = null): void {
  const uoc011Fixture = renderUoc011BrowserStateFixture('ui.dashboard');
  if (uoc011Fixture) { root.append(uoc011Fixture); return; }
  let advancedOpen = false;
  const state: DashboardState = {
    loading: false,
    warming: false,
    token: readStoredToken(),
    snapshot: {},
    errors: {},
    durations: {},
    completed: 0,
    total: DASHBOARD_TOTAL,
  };

  async function refresh(): Promise<void> {
    if (state.loading) return;
    state.loading = true;
    state.warming = true;
    state.health = undefined;
    state.healthError = undefined;
    state.healthDuration = undefined;
    state.snapshot = {};
    state.errors = {};
    state.durations = {};
    state.completed = 0;
    state.refreshedAt = undefined;
    draw();

    const client = new DevPilotApiClient({ token: state.token });
    const healthStarted = performance.now();
    try {
      state.health = await client.health();
      state.healthDuration = Math.round(performance.now() - healthStarted);
      draw();
    } catch (error) {
      state.healthDuration = Math.round(performance.now() - healthStarted);
      state.healthError = error instanceof Error ? error.message : String(error);
      state.warming = false;
      state.loading = false;
      state.refreshedAt = new Date().toISOString();
      draw();
      return;
    }

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
      { key: 'portfolio', run: () => client.portfolioStatus() },
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
    if (guardReason) root.append(renderJourneyGuardNotice(guardReason));
    root.append(renderProjectHomeEntryPanel(session));

    const advanced = document.createElement('details');
    advanced.className = 'dashboard-advanced';
    advanced.open = advancedOpen;
    advanced.addEventListener('toggle', () => { advancedOpen = advanced.open; });
    const advancedSummary = document.createElement('summary');
    advancedSummary.textContent = 'Dashboard operacional avanzado · no requerido para Crear / Abrir / Importar';
    const advancedBody = document.createElement('div');
    advancedBody.className = 'dashboard-advanced__body';
    advancedBody.append(renderHeader(state, refresh));
    advancedBody.append(renderConnectionSummary(state));
    advancedBody.append(renderHealthPreflight(state));
    advancedBody.append(renderWorkspaceContextPanel(state.snapshot.portfolio, state.errors.portfolio, state.durations.portfolio));
    advancedBody.append(renderOperatorDashboard(state.snapshot.operator, state.errors.operator));

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
    advancedBody.append(grid);

    if (state.warming) advancedBody.append(renderUiStateNotice('loading', 'Warm-up protegido: esperando que la superficie autenticada de la API local esté lista antes de lanzar el resumen.'));
    else if (state.loading) advancedBody.append(renderUiStateNotice('loading', `Consultando API local de forma progresiva (${state.completed}/${state.total}); máximo 2 solicitudes simultáneas.`));
    if (!state.loading && !Object.keys(state.snapshot).length && !Object.keys(state.errors).length) advancedBody.append(renderUiStateNotice('empty', 'El Dashboard avanzado requiere token local de compatibilidad. Crear / Abrir / Importar no lo requiere.'));
    if (state.healthError) advancedBody.append(renderUiStateNotice('error', 'El preflight Health falló. El Project Home sigue disponible; el resumen operacional avanzado permanece fail-closed.'));
    else if (Object.keys(state.errors).length) advancedBody.append(renderUiStateNotice('error', 'Una o más tarjetas no pudieron actualizarse. Los resultados exitosos permanecen visibles; use Reintentar para la consulta afectada.'));

    const allFindings = Object.values(state.snapshot)
      .flatMap((response) => response?.findings ?? [])
      .filter((finding) => ['warning', 'block', 'error'].includes(String(finding.severity).toLowerCase()));
    advancedBody.append(renderFindingList(allFindings));
    advancedBody.append(renderRouteSummaries());
    advanced.append(advancedSummary, advancedBody);
    if (readProjectJourneyContext()?.phase === 'project') root.append(advanced);
  }

  draw();
  if (state.token) void refresh();
}

function renderJourneyGuardNotice(routeTitle: string): HTMLElement {
  const notice = document.createElement('div');
  notice.className = 'project-journey-guard';
  notice.setAttribute('role', 'status');
  const strong = document.createElement('strong');
  strong.textContent = 'Superficie todavía no habilitada. ';
  const detail = document.createElement('span');
  detail.textContent = routeTitle === 'Approval Center'
    ? 'Approval Center se habilita durante un journey Crear/Abrir/Importar cuando existe una solicitud de approval, o después de activar un proyecto.'
    : `${routeTitle} requiere completar primero Crear, Abrir o Importar. DevPilot te devuelve a Project Home para mantener el journey guiado.`;
  notice.append(strong, detail);
  return notice;
}

function renderHeader(state: DashboardState, refresh: () => Promise<void>): HTMLElement {
  const header = document.createElement('header');
  header.className = 'app-header';
  const titleBlock = document.createElement('div');
  const title = document.createElement('h1');
  title.textContent = 'Dashboard operacional avanzado';
  const subtitle = document.createElement('p');
  subtitle.textContent = 'Superficie avanzada/compatibilidad. El Project Home y el journey Crear/Abrir/Importar usan human-session y no requieren pegar un token local.';
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
  label.textContent = 'Token local de compatibilidad (opcional para este dashboard)';
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
  panel.setAttribute('role', 'status');
  panel.setAttribute('aria-live', 'polite');
  const status = state.loading
    ? 'ACTUALIZANDO'
    : state.healthError
      ? 'NO DISPONIBLE'
      : Object.keys(state.errors).length
        ? 'DEGRADADO'
        : Object.keys(state.snapshot).length
          ? 'OPERATIVO'
          : 'NO CONSULTADO';
  const healthCompleted = state.health ? 1 : 0;
  const items = [
    ['strong', `API local: ${status}`],
    ['span', 'http://127.0.0.1:8787'],
    ['span', `Datos: ${state.completed}/${state.total}`],
    ['span', `Operaciones contractuales: ${healthCompleted + state.completed}/${state.total + 1}`],
    ['span', `Última actualización: ${state.refreshedAt ?? 'pendiente'}`],
  ] as const;
  for (const [tag, text] of items) {
    const item = document.createElement(tag);
    item.textContent = text;
    panel.append(item);
  }
  return panel;
}

function renderHealthPreflight(state: DashboardState): HTMLElement {
  const panel = document.createElement('section');
  panel.className = 'health-preflight';
  panel.dataset.apiOperation = 'api.health';
  const title = document.createElement('strong');
  title.textContent = 'Preflight Health';
  const status = document.createElement('span');
  status.className = `badge ${state.healthError ? 'error' : state.health ? 'pass' : 'pending'}`;
  status.textContent = state.healthError ? 'ERROR' : state.health ? 'PASS' : 'PENDING';
  const detail = document.createElement('span');
  const duration = state.healthDuration === undefined ? 'duración pendiente' : `${state.healthDuration} ms`;
  detail.textContent = state.healthError
    ? `GET /api/v1/health · ${duration} · ${state.healthError}`
    : `GET /api/v1/health · ${duration} · preflight previo al warm-up autenticado`;
  panel.append(title, status, detail);
  return panel;
}

function renderRouteSummaries(): HTMLElement {
  const section = document.createElement('section');
  section.className = 'route-summary-grid';
  const routes = [
    ['/workspace/documents', 'Documentos', 'Explorador read-only del workspace activo.'],
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
