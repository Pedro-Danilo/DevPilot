import { renderUoc011BrowserStateFixture } from '../testing/Uoc011BrowserStateFixture';
import { DevPilotApiClient } from '../api/client';
import type { DevPilotApplicationResponse, TraceSummaryItem } from '../api/types';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { renderWorkspaceContextPanel } from '../components/WorkspaceContextPanel';
import { runBounded } from '../utils/async';

interface TracesState {
  loading: boolean;
  traces?: DevPilotApplicationResponse;
  metrics?: DevPilotApplicationResponse;
  portfolio?: DevPilotApplicationResponse;
  traceDetail?: DevPilotApplicationResponse;
  errors: Record<string, string>;
  durations: Record<string, number>;
  scope: string;
  query: string;
  page: number;
  pageSize: number;
}

export function renderTracesView(tokenProvider: () => string): HTMLElement {
  const section = document.createElement('section');
  section.className = 'viewer-panel';
  section.dataset.devpilotUiContract = 'ui.traces';
  const uoc011Fixture = renderUoc011BrowserStateFixture('ui.traces');
  if (uoc011Fixture) return uoc011Fixture;
  const state: TracesState = { loading: false, errors: {}, durations: {}, scope: 'active', query: '', page: 0, pageSize: 20 };

  async function refresh(): Promise<void> {
    state.loading = true;
    state.errors = {};
    state.page = 0;
    draw();
    const client = new DevPilotApiClient({ token: tokenProvider() });
    await runBounded<DevPilotApplicationResponse>([
      { key: 'traces', run: () => client.listTraces(100, state.scope) },
      { key: 'metrics', run: () => client.metricsSummary(state.scope) },
      { key: 'portfolio', run: () => client.portfolioStatus() },
    ], 2, (result) => {
      state.durations[result.key] = result.durationMs;
      if (result.value) {
        if (result.key === 'traces') state.traces = result.value;
        if (result.key === 'metrics') state.metrics = result.value;
        if (result.key === 'portfolio') state.portfolio = result.value;
      }
      if (result.error) state.errors[result.key] = result.error;
      draw();
    });
    state.loading = false;
    draw();
  }

  async function inspect(traceId: string): Promise<void> {
    state.loading = true;
    draw();
    const started = performance.now();
    try {
      state.traceDetail = await new DevPilotApiClient({ token: tokenProvider() }).inspectTrace(traceId, 100, state.scope);
      delete state.errors.traceDetail;
    } catch (error) {
      state.errors.traceDetail = error instanceof Error ? error.message : String(error);
    } finally {
      state.durations.traceDetail = Math.round(performance.now() - started);
      state.loading = false;
      draw();
    }
  }

  function draw(): void {
    section.replaceChildren();
    const header = document.createElement('div');
    header.className = 'viewer-panel__header';
    const title = document.createElement('div');
    title.innerHTML = '<h2>Trazas</h2><p>Lista y detalle de trazas locales con contexto explícito de plataforma o workspace.</p>';
    title.append(renderContractBadges('ui.traces', { warning: 'Lectura local y redactada; no expone token ni prompts crudos.' }));
    const controls = document.createElement('div');
    controls.className = 'viewer-controls';
    const scope = document.createElement('select');
    for (const [value, text] of [['active', 'Contexto activo'], ['workspace', 'Workspace'], ['platform', 'Plataforma']]) {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = text;
      option.selected = state.scope === value;
      scope.append(option);
    }
    scope.addEventListener('change', () => { state.scope = scope.value; void refresh(); });
    const search = document.createElement('input');
    search.type = 'search';
    search.placeholder = 'Filtrar trace id o fecha';
    search.value = state.query;
    search.addEventListener('input', () => { state.query = search.value; state.page = 0; draw(); });
    const button = document.createElement('button');
    button.textContent = state.loading ? 'Consultando…' : state.errors.traces ? 'Reintentar trazas' : 'Actualizar trazas';
    button.disabled = state.loading;
    button.addEventListener('click', () => void refresh());
    controls.append(scope, search, button);
    header.append(title, controls);
    section.append(header);

    section.append(renderWorkspaceContextPanel(state.portfolio, state.errors.portfolio, state.durations.portfolio));
    if (state.loading) section.append(renderUiStateNotice('loading', 'Consultando trazas locales con concurrencia acotada.'));
    const allTraces = ((state.traces?.data as { traces?: TraceSummaryItem[] } | undefined)?.traces ?? []);
    const query = state.query.trim().toLowerCase();
    const filtered = query
      ? allTraces.filter((trace) => `${trace.trace_id} ${trace.started_at ?? ''} ${trace.ended_at ?? ''}`.toLowerCase().includes(query))
      : allTraces;
    const pages = Math.max(1, Math.ceil(filtered.length / state.pageSize));
    if (state.page >= pages) state.page = pages - 1;
    const traces = filtered.slice(state.page * state.pageSize, (state.page + 1) * state.pageSize);
    if (!state.loading && state.traces && !state.errors.traces && filtered.length === 0) {
      section.append(renderUiStateNotice('empty', 'No hay trazas disponibles para el contexto o filtro actual. Ejecute una operación instrumentada y vuelva a intentar.'));
    }
    for (const [key, message] of Object.entries(state.errors)) section.append(renderUiStateNotice('error', `${key}: ${message}`));

    const grid = document.createElement('div');
    grid.className = 'viewer-grid';
    const listCard = document.createElement('article');
    listCard.className = 'viewer-card';
    listCard.innerHTML = `<h3>Índice de trazas</h3><p>${filtered.length} resultado(s) · página ${state.page + 1}/${pages} · ${durationLabel(state.durations.traces)}</p>`;
    const list = document.createElement('div');
    list.className = 'viewer-list';
    for (const trace of traces) {
      const item = document.createElement('button');
      item.className = 'viewer-list__item';
      item.textContent = `${trace.trace_id} · ${trace.spans_total ?? 0} spans · ${trace.duration_ms_total ?? 0} ms · ${trace.started_at ?? 'sin fecha'}`;
      item.addEventListener('click', () => void inspect(trace.trace_id));
      list.append(item);
    }
    const pager = document.createElement('div');
    pager.className = 'viewer-controls';
    const previous = document.createElement('button');
    previous.className = 'button-secondary';
    previous.textContent = 'Anterior';
    previous.disabled = state.page === 0;
    previous.addEventListener('click', () => { state.page -= 1; draw(); });
    const next = document.createElement('button');
    next.className = 'button-secondary';
    next.textContent = 'Siguiente';
    next.disabled = state.page + 1 >= pages;
    next.addEventListener('click', () => { state.page += 1; draw(); });
    pager.append(previous, next);
    listCard.append(list, pager);

    const detailCard = document.createElement('article');
    detailCard.className = 'viewer-card';
    detailCard.innerHTML = `<h3>Detalle seleccionado</h3><p>${durationLabel(state.durations.traceDetail)}</p>`;
    const detail = document.createElement('pre');
    detail.className = 'viewer-pre';
    detail.textContent = state.traceDetail ? JSON.stringify(state.traceDetail.data, null, 2) : 'Seleccione una traza para inspeccionar spans, eventos y métricas.';
    detailCard.append(detail);
    grid.append(listCard, detailCard);
    section.append(grid);

    const metricsCard = document.createElement('article');
    metricsCard.className = 'viewer-card';
    metricsCard.innerHTML = `<h3>Métricas del contexto seleccionado</h3><p>${durationLabel(state.durations.metrics)}</p>`;
    const metrics = document.createElement('pre');
    metrics.className = 'viewer-pre';
    metrics.textContent = state.metrics ? JSON.stringify(state.metrics.data, null, 2) : 'Sin métricas consultadas.';
    metricsCard.append(metrics);
    section.append(metricsCard);
  }

  draw();
  void refresh();
  return section;
}

function durationLabel(value?: number): string {
  return value === undefined ? 'duración pendiente' : `última consulta: ${value} ms`;
}
