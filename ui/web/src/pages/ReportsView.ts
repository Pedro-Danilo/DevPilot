import { renderUoc011BrowserStateFixture } from '../testing/Uoc011BrowserStateFixture';
import { DevPilotApiClient } from '../api/client';
import type { DevPilotApplicationResponse, ReportIndexItem } from '../api/types';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { renderFindingTable } from '../components/FindingTable';
import { renderWorkspaceContextPanel } from '../components/WorkspaceContextPanel';
import { runBounded } from '../utils/async';

interface ReportsState {
  loading: boolean;
  reports?: DevPilotApplicationResponse;
  metrics?: DevPilotApplicationResponse;
  portfolio?: DevPilotApplicationResponse;
  reportDetail?: DevPilotApplicationResponse;
  selectedReport?: ReportIndexItem;
  errors: Record<string, string>;
  durations: Record<string, number>;
  severity: string;
  status: string;
  query: string;
  scope: string;
  detailFormat: 'json' | 'markdown';
}

export function renderReportsView(tokenProvider: () => string): HTMLElement {
  const section = document.createElement('section');
  section.className = 'viewer-panel';
  section.dataset.devpilotUiContract = 'ui.reports';
  const uoc011Fixture = renderUoc011BrowserStateFixture('ui.reports');
  if (uoc011Fixture) return uoc011Fixture;
  const state: ReportsState = {
    loading: false,
    errors: {},
    durations: {},
    severity: '',
    status: '',
    query: '',
    scope: 'all',
    detailFormat: 'json',
  };

  async function refresh(): Promise<void> {
    state.loading = true;
    state.errors = {};
    draw();
    const client = new DevPilotApiClient({ token: tokenProvider() });
    await runBounded<DevPilotApplicationResponse>([
      {
        key: 'reports',
        run: () => client.listReports({
          limit: 50,
          severity: state.severity,
          status: state.status,
          query: state.query,
          scope: state.scope,
        }),
      },
      { key: 'metrics', run: () => client.metricsSummary('active') },
      { key: 'portfolio', run: () => client.portfolioStatus() },
    ], 2, (result) => {
      state.durations[result.key] = result.durationMs;
      if (result.value) {
        if (result.key === 'reports') state.reports = result.value;
        if (result.key === 'metrics') state.metrics = result.value;
        if (result.key === 'portfolio') state.portfolio = result.value;
      }
      if (result.error) state.errors[result.key] = result.error;
      draw();
    });
    state.loading = false;
    draw();
  }

  async function loadReport(report: ReportIndexItem, requestedFormat?: 'json' | 'markdown'): Promise<void> {
    state.loading = true;
    state.selectedReport = report;
    const available = report.formats ?? [];
    const preferred = requestedFormat ?? (available.includes('json') ? 'json' : 'markdown');
    state.detailFormat = preferred;
    draw();
    const started = performance.now();
    try {
      state.reportDetail = await new DevPilotApiClient({ token: tokenProvider() }).readReport(report.report_id, preferred);
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
    title.innerHTML = '<h2>Reportes</h2><p>Índice recursivo y detalle de reportes locales gobernados. La UI no accede directamente al filesystem.</p>';
    title.append(renderContractBadges('ui.reports', { warning: 'Lectura local; roots de plataforma/workspace explícitos; no remote.' }));
    const controls = renderControls(state, () => void refresh(), draw);
    header.append(title, controls);
    section.append(header);

    section.append(renderWorkspaceContextPanel(state.portfolio, state.errors.portfolio, state.durations.portfolio));

    if (state.loading) section.append(renderUiStateNotice('loading', 'Consultando reportes locales con concurrencia acotada y discovery bounded.'));
    const reports = ((state.reports?.data as { reports?: ReportIndexItem[] } | undefined)?.reports ?? []);
    const summary = ((state.reports?.data as { summary?: Record<string, unknown> } | undefined)?.summary ?? {});
    if (!state.loading && state.reports && !state.errors.reports && reports.length === 0) {
      section.append(renderUiStateNotice('empty', 'No hay reportes locales para el scope y filtros seleccionados. Genere una operación con write-report o revise el contexto activo.'));
    }
    for (const [key, message] of Object.entries(state.errors)) {
      section.append(renderUiStateNotice('error', `${key}: ${message}`));
    }
    if (summary.discovery_truncated === true || summary.summary_parse_budget_exhausted === true) {
      section.append(renderUiStateNotice('pending', 'El índice aplicó límites de discovery/summary. Refine scope o búsqueda antes de interpretar la lista como exhaustiva.'));
    }

    const grid = document.createElement('div');
    grid.className = 'viewer-grid';
    const listCard = document.createElement('article');
    listCard.className = 'viewer-card';
    listCard.innerHTML = `<h3>Índice de reportes</h3><p>${indexTelemetry(reports.length, summary, state.durations.reports)}</p>`;
    const list = document.createElement('div');
    list.className = 'viewer-list';
    for (const report of reports) {
      const item = document.createElement('button');
      item.className = 'viewer-list__item report-index-item';
      const scope = report.scope ?? 'platform';
      const path = report.relative_path ?? report.report_id;
      const status = report.status || (report.summary_loaded === false ? 'summary diferido' : 'sin estado');
      const formats = (report.formats ?? []).join('+') || 'sin formato';
      item.textContent = `[${scope}] ${path} · ${status} · ${formats} · ${report.modified_at ?? report.generated_at ?? 'sin fecha'}`;
      item.title = `Report id: ${report.report_id}`;
      item.addEventListener('click', () => void loadReport(report));
      list.append(item);
    }
    listCard.append(list);

    const detailCard = document.createElement('article');
    detailCard.className = 'viewer-card';
    const detailHeading = document.createElement('div');
    detailHeading.className = 'report-detail-heading';
    const detailTitle = document.createElement('div');
    detailTitle.innerHTML = `<h3>Detalle seleccionado</h3><p>${state.selectedReport ? `${state.selectedReport.relative_path ?? state.selectedReport.report_id} · ${durationLabel(state.durations.reportDetail)}` : durationLabel(state.durations.reportDetail)}</p>`;
    const formatControls = document.createElement('div');
    formatControls.className = 'viewer-controls';
    if (state.selectedReport) {
      for (const format of ['json', 'markdown'] as const) {
        if (!(state.selectedReport.formats ?? []).includes(format)) continue;
        const button = document.createElement('button');
        button.className = state.detailFormat === format ? '' : 'button-secondary';
        button.textContent = format.toUpperCase();
        button.disabled = state.loading;
        button.addEventListener('click', () => void loadReport(state.selectedReport as ReportIndexItem, format));
        formatControls.append(button);
      }
    }
    detailHeading.append(detailTitle, formatControls);
    const detail = document.createElement('pre');
    detail.className = 'viewer-pre';
    detail.textContent = state.reportDetail
      ? JSON.stringify(state.reportDetail.data, null, 2)
      : 'Seleccione un reporte para inspeccionarlo.';
    detailCard.append(detailHeading, detail);
    grid.append(listCard, detailCard);
    section.append(grid);
    section.append(renderFindingTable(state.reports?.findings ?? []));

    const metricsCard = document.createElement('article');
    metricsCard.className = 'viewer-card';
    metricsCard.innerHTML = `<h3>Métricas relacionadas del contexto activo</h3><p>${durationLabel(state.durations.metrics)}</p>`;
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

function renderControls(state: ReportsState, refresh: () => void, draw: () => void): HTMLElement {
  const controls = document.createElement('div');
  controls.className = 'viewer-controls report-controls';

  const scope = selectControl('Scope', [
    ['all', 'Plataforma + workspace'],
    ['workspace', 'Workspace activo'],
    ['platform', 'Plataforma DevPilot'],
  ], state.scope, (value) => { state.scope = value; });
  const severity = selectControl('Severidad', [
    ['', 'Todas las severidades'],
    ['warning', 'Warning'],
    ['block', 'Block'],
    ['error', 'Error'],
  ], state.severity, (value) => { state.severity = value; });
  const status = selectControl('Estado', [
    ['', 'Todos los estados'],
    ['pass', 'PASS'],
    ['warning', 'WARNING'],
    ['block', 'BLOCK'],
    ['fail', 'FAIL'],
    ['error', 'ERROR'],
  ], state.status, (value) => { state.status = value; });

  const searchLabel = document.createElement('label');
  searchLabel.textContent = 'Buscar path/id';
  const search = document.createElement('input');
  search.type = 'search';
  search.value = state.query;
  search.placeholder = 'bootstrap, readiness, release…';
  search.addEventListener('input', () => { state.query = search.value; });
  search.addEventListener('keydown', (event) => { if (event.key === 'Enter') { event.preventDefault(); refresh(); } });
  searchLabel.append(search);

  const button = document.createElement('button');
  button.textContent = state.loading ? 'Consultando…' : state.errors.reports ? 'Reintentar reportes' : 'Actualizar reportes';
  button.disabled = state.loading;
  button.addEventListener('click', refresh);

  const clear = document.createElement('button');
  clear.className = 'button-secondary';
  clear.textContent = 'Limpiar filtros';
  clear.disabled = state.loading;
  clear.addEventListener('click', () => {
    state.scope = 'all';
    state.severity = '';
    state.status = '';
    state.query = '';
    draw();
  });

  controls.append(scope, severity, status, searchLabel, button, clear);
  return controls;
}

function selectControl(labelText: string, values: Array<[string, string]>, selected: string, onChange: (value: string) => void): HTMLElement {
  const label = document.createElement('label');
  label.textContent = labelText;
  const select = document.createElement('select');
  for (const [value, text] of values) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = text;
    option.selected = selected === value;
    select.append(option);
  }
  select.addEventListener('change', () => onChange(select.value));
  label.append(select);
  return label;
}

function indexTelemetry(returned: number, summary: Record<string, unknown>, duration?: number): string {
  const total = Number(summary.reports_total ?? returned);
  const files = Number(summary.files_discovered_total ?? 0);
  const recursive = summary.recursive_discovery === true ? 'recursivo' : 'nivel raíz';
  return `${returned} mostrado(s) de ${total} · ${files} archivo(s) · ${recursive} · ${durationLabel(duration)}`;
}

function durationLabel(value?: number): string {
  return value === undefined ? 'duración pendiente' : `última consulta: ${value} ms`;
}
