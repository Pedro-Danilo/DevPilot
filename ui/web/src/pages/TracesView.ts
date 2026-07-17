import { DevPilotApiClient } from '../api/client';
import type { DevPilotApplicationResponse, TraceSummaryItem } from '../api/types';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { runBounded } from '../utils/async';

interface TracesState {
  loading: boolean;
  traces?: DevPilotApplicationResponse;
  metrics?: DevPilotApplicationResponse;
  traceDetail?: DevPilotApplicationResponse;
  errors: Record<string, string>;
  durations: Record<string, number>;
}

export function renderTracesView(tokenProvider: () => string): HTMLElement {
  const section = document.createElement('section');
  section.className = 'viewer-panel';
  section.dataset.devpilotUiContract = 'ui.traces';
  const state: TracesState = { loading: false, errors: {}, durations: {} };

  async function refresh(): Promise<void> {
    state.loading = true;
    state.errors = {};
    draw();
    const client = new DevPilotApiClient({ token: tokenProvider() });
    await runBounded<DevPilotApplicationResponse>([
      { key: 'traces', run: () => client.listTraces(50) },
      { key: 'metrics', run: () => client.metricsSummary() },
    ], 2, (result) => {
      state.durations[result.key] = result.durationMs;
      if (result.value) {
        if (result.key === 'traces') state.traces = result.value;
        if (result.key === 'metrics') state.metrics = result.value;
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
      state.traceDetail = await new DevPilotApiClient({ token: tokenProvider() }).inspectTrace(traceId);
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
    title.innerHTML = '<h2>Trazas</h2><p>Lista y detalle de trazas locales. Esta ruta no consulta reportes automáticamente.</p>';
    title.append(renderContractBadges('ui.traces', { warning: 'Lectura local y redactada; no expone token ni prompts crudos.' }));
    const button = document.createElement('button');
    button.textContent = state.loading ? 'Consultando…' : 'Actualizar trazas';
    button.disabled = state.loading;
    button.addEventListener('click', () => void refresh());
    header.append(title, button);
    section.append(header);

    if (state.loading) section.append(renderUiStateNotice('loading', 'Consultando trazas locales con concurrencia acotada.'));
    const traces = ((state.traces?.data as { traces?: TraceSummaryItem[] } | undefined)?.traces ?? []);
    if (!state.loading && state.traces && traces.length === 0) {
      section.append(renderUiStateNotice('empty', 'No hay trazas disponibles. Ejecute una operación instrumentada y vuelva a intentar.'));
    }
    for (const [key, message] of Object.entries(state.errors)) {
      section.append(renderUiStateNotice('error', `${key}: ${message}`));
    }

    const grid = document.createElement('div');
    grid.className = 'viewer-grid';
    const listCard = document.createElement('article');
    listCard.className = 'viewer-card';
    listCard.innerHTML = `<h3>Índice de trazas</h3><p>${traces.length} traza(s) · ${durationLabel(state.durations.traces)}</p>`;
    const list = document.createElement('div');
    list.className = 'viewer-list';
    for (const trace of traces) {
      const item = document.createElement('button');
      item.className = 'viewer-list__item';
      item.textContent = `${trace.trace_id} · ${trace.spans_total ?? 0} spans · ${trace.duration_ms_total ?? 0} ms · ${trace.started_at ?? 'sin fecha'}`;
      item.addEventListener('click', () => void inspect(trace.trace_id));
      list.append(item);
    }
    listCard.append(list);

    const detailCard = document.createElement('article');
    detailCard.className = 'viewer-card';
    detailCard.innerHTML = `<h3>Detalle seleccionado</h3><p>${durationLabel(state.durations.traceDetail)}</p>`;
    const detail = document.createElement('pre');
    detail.className = 'viewer-pre';
    detail.textContent = state.traceDetail
      ? JSON.stringify(state.traceDetail.data, null, 2)
      : 'Seleccione una traza para inspeccionar spans, eventos y métricas.';
    detailCard.append(detail);
    grid.append(listCard, detailCard);
    section.append(grid);

    const metricsCard = document.createElement('article');
    metricsCard.className = 'viewer-card';
    metricsCard.innerHTML = `<h3>Métricas relacionadas</h3><p>${durationLabel(state.durations.metrics)}</p>`;
    const metrics = document.createElement('pre');
    metrics.className = 'viewer-pre';
    metrics.textContent = state.metrics ? JSON.stringify(state.metrics.data, null, 2) : 'Sin métricas consultadas.';
    metricsCard.append(metrics);
    section.append(metricsCard);
  }

  draw();
  if (tokenProvider()) void refresh();
  return section;
}

function durationLabel(value?: number): string {
  return value === undefined ? 'duración pendiente' : `última consulta: ${value} ms`;
}
