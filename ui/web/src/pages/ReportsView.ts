import { DevPilotApiClient } from '../api/client';
import type { DevPilotApplicationResponse, ReportIndexItem } from '../api/types';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { renderFindingTable } from '../components/FindingTable';
import { runBounded } from '../utils/async';

interface ReportsState {
  loading: boolean;
  reports?: DevPilotApplicationResponse;
  metrics?: DevPilotApplicationResponse;
  reportDetail?: DevPilotApplicationResponse;
  errors: Record<string, string>;
  durations: Record<string, number>;
  severity: string;
}

export function renderReportsView(tokenProvider: () => string): HTMLElement {
  const section = document.createElement('section');
  section.className = 'viewer-panel';
  section.dataset.devpilotUiContract = 'ui.reports';
  const state: ReportsState = {
    loading: false,
    errors: {},
    durations: {},
    severity: '',
  };

  async function refresh(): Promise<void> {
    state.loading = true;
    state.errors = {};
    draw();
    const client = new DevPilotApiClient({ token: tokenProvider() });
    await runBounded<DevPilotApplicationResponse>([
      { key: 'reports', run: () => client.listReports({ limit: 50, severity: state.severity }) },
      { key: 'metrics', run: () => client.metricsSummary() },
    ], 2, (result) => {
      state.durations[result.key] = result.durationMs;
      if (result.value) {
        if (result.key === 'reports') state.reports = result.value;
        if (result.key === 'metrics') state.metrics = result.value;
      }
      if (result.error) state.errors[result.key] = result.error;
      draw();
    });
    state.loading = false;
    draw();
  }

  async function loadReport(reportId: string): Promise<void> {
    state.loading = true;
    draw();
    const started = performance.now();
    try {
      state.reportDetail = await new DevPilotApiClient({ token: tokenProvider() }).readReport(reportId, 'json');
      delete state.errors.reportDetail;
    } catch (error) {
      state.errors.reportDetail = error instanceof Error ? error.message : String(error);
    } finally {
      state.durations.reportDetail = Math.round(performance.now() - started);
      state.loading = false;
      draw();
    }
  }

  function draw(): void {
    section.replaceChildren();
    const header = document.createElement('div');
    header.className = 'viewer-panel__header';
    const title = document.createElement('div');
    title.innerHTML = '<h2>Reportes</h2><p>Índice y detalle de reportes locales. Esta ruta no consulta trazas automáticamente.</p>';
    title.append(renderContractBadges('ui.reports', { warning: 'Lectura local; sin acceso directo a outputs desde el navegador.' }));
    const controls = document.createElement('div');
    controls.className = 'viewer-controls';
    const severity = document.createElement('select');
    for (const value of ['', 'warning', 'block', 'error']) {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = value || 'Todas las severidades';
      option.selected = state.severity === value;
      severity.append(option);
    }
    severity.addEventListener('change', () => { state.severity = severity.value; });
    const button = document.createElement('button');
    button.textContent = state.loading ? 'Consultando…' : 'Actualizar reportes';
    button.disabled = state.loading;
    button.addEventListener('click', () => void refresh());
    controls.append(severity, button);
    header.append(title, controls);
    section.append(header);

    if (state.loading) section.append(renderUiStateNotice('loading', 'Consultando reportes locales con concurrencia acotada.'));
    const reports = ((state.reports?.data as { reports?: ReportIndexItem[] } | undefined)?.reports ?? []);
    if (!state.loading && state.reports && reports.length === 0) {
      section.append(renderUiStateNotice('empty', 'No hay reportes locales. Genere una operación con write-report o ejecute el comando indicado por el runbook.'));
    }
    for (const [key, message] of Object.entries(state.errors)) {
      section.append(renderUiStateNotice('error', `${key}: ${message}`));
    }

    const grid = document.createElement('div');
    grid.className = 'viewer-grid';
    const listCard = document.createElement('article');
    listCard.className = 'viewer-card';
    listCard.innerHTML = `<h3>Índice de reportes</h3><p>${reports.length} reporte(s) · ${durationLabel(state.durations.reports)}</p>`;
    const list = document.createElement('div');
    list.className = 'viewer-list';
    for (const report of reports) {
      const item = document.createElement('button');
      item.className = 'viewer-list__item';
      item.textContent = `${report.report_id} · ${report.status ?? 'sin estado'} · ${report.modified_at ?? report.generated_at ?? 'sin fecha'}`;
      item.addEventListener('click', () => void loadReport(report.report_id));
      list.append(item);
    }
    listCard.append(list);

    const detailCard = document.createElement('article');
    detailCard.className = 'viewer-card';
    detailCard.innerHTML = `<h3>Detalle seleccionado</h3><p>${durationLabel(state.durations.reportDetail)}</p>`;
    const detail = document.createElement('pre');
    detail.className = 'viewer-pre';
    detail.textContent = state.reportDetail
      ? JSON.stringify(state.reportDetail.data, null, 2)
      : 'Seleccione un reporte para inspeccionarlo.';
    detailCard.append(detail);
    grid.append(listCard, detailCard);
    section.append(grid);
    section.append(renderFindingTable(state.reports?.findings ?? []));

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
