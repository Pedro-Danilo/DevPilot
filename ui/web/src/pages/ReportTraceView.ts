import { DevPilotApiClient } from '../api/client';
import type { DevPilotApplicationResponse, ReportIndexItem, TraceSummaryItem } from '../api/types';
import { renderFindingTable } from '../components/FindingTable';

interface ViewerState {
  loading: boolean;
  reports?: DevPilotApplicationResponse;
  traces?: DevPilotApplicationResponse;
  metrics?: DevPilotApplicationResponse;
  reportDetail?: DevPilotApplicationResponse;
  traceDetail?: DevPilotApplicationResponse;
  errors: Record<string, string>;
  severity: string;
}

export function renderReportTraceView(tokenProvider: () => string): HTMLElement {
  const section = document.createElement('section');
  section.className = 'viewer-panel';
  const state: ViewerState = { loading: false, errors: {}, severity: '' };

  async function refresh(): Promise<void> {
    state.loading = true;
    state.errors = {};
    draw();
    const client = new DevPilotApiClient({ token: tokenProvider() });
    const tasks: Array<[keyof ViewerState, () => Promise<DevPilotApplicationResponse>]> = [
      ['reports', () => client.listReports({ limit: 50, severity: state.severity })],
      ['traces', () => client.listTraces(20)],
      ['metrics', () => client.metricsSummary()],
    ];
    const entries = await Promise.all(tasks.map(async ([key, loader]) => {
      try { return [key, await loader(), undefined] as const; }
      catch (error) { return [key, undefined, error instanceof Error ? error.message : String(error)] as const; }
    }));
    for (const [key, response, error] of entries) {
      if (response) (state as unknown as Record<string, DevPilotApplicationResponse>)[key] = response;
      if (error) state.errors[String(key)] = error;
    }
    state.loading = false;
    draw();
  }

  async function loadReport(reportId: string): Promise<void> {
    state.loading = true;
    draw();
    try { state.reportDetail = await new DevPilotApiClient({ token: tokenProvider() }).readReport(reportId, 'json'); }
    catch (error) { state.errors.reportDetail = error instanceof Error ? error.message : String(error); }
    state.loading = false;
    draw();
  }

  async function loadTrace(traceId: string): Promise<void> {
    state.loading = true;
    draw();
    try { state.traceDetail = await new DevPilotApiClient({ token: tokenProvider() }).inspectTrace(traceId); }
    catch (error) { state.errors.traceDetail = error instanceof Error ? error.message : String(error); }
    state.loading = false;
    draw();
  }

  function draw(): void {
    section.replaceChildren();
    const header = document.createElement('div');
    header.className = 'viewer-panel__header';
    const title = document.createElement('div');
    title.innerHTML = '<h2>Report Viewer y Trace Viewer</h2><p>Sprint 70 MVP · API-only · reportes/trazas/métricas redacted y bounded.</p>';
    const controls = document.createElement('form');
    controls.className = 'viewer-controls';
    controls.innerHTML = '<label>Filtrar severity <select name="severity"><option value="">Todas</option><option value="info">info</option><option value="warning">warning</option><option value="block">block</option><option value="error">error</option></select></label><button type="submit">Actualizar viewers</button>';
    const select = controls.querySelector<HTMLSelectElement>('select[name="severity"]');
    if (select) select.value = state.severity;
    controls.addEventListener('submit', (event) => {
      event.preventDefault();
      state.severity = controls.querySelector<HTMLSelectElement>('select[name="severity"]')?.value ?? '';
      void refresh();
    });
    header.append(title, controls);
    section.append(header);

    const grid = document.createElement('div');
    grid.className = 'viewer-grid';
    grid.append(renderReportsPanel(state, loadReport));
    grid.append(renderTracesPanel(state, loadTrace));
    section.append(grid);
    section.append(renderDetailPanel('Reporte seleccionado', state.reportDetail, state.errors.reportDetail));
    section.append(renderDetailPanel('Traza seleccionada', state.traceDetail, state.errors.traceDetail));
    section.append(renderMetricsPanel(state.metrics, state.errors.metrics));
  }

  draw();
  if (tokenProvider()) void refresh();
  return section;
}

function renderReportsPanel(state: ViewerState, onSelect: (reportId: string) => Promise<void>): HTMLElement {
  const panel = panelShell('Report Viewer', state.errors.reports ?? state.reports?.message ?? 'Pendiente de consulta.');
  const reports = ((state.reports?.data as { reports?: ReportIndexItem[] } | undefined)?.reports ?? []);
  if (!reports.length) {
    panel.append(emptyPre('Sin reportes para mostrar.'));
    return panel;
  }
  const list = document.createElement('div');
  list.className = 'viewer-list';
  for (const report of reports.slice(0, 25)) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'viewer-list__item';
    button.textContent = `${report.status ?? 'UNKNOWN'} · ${report.report_id} · ${report.command ?? ''}`;
    button.addEventListener('click', () => { void onSelect(report.report_id); });
    list.append(button);
  }
  panel.append(list);
  const findings = state.reports?.findings ?? [];
  panel.append(renderFindingTable(findings));
  return panel;
}

function renderTracesPanel(state: ViewerState, onSelect: (traceId: string) => Promise<void>): HTMLElement {
  const panel = panelShell('Trace Viewer', state.errors.traces ?? state.traces?.message ?? 'Pendiente de consulta.');
  const traces = ((state.traces?.data as { traces?: TraceSummaryItem[] } | undefined)?.traces ?? []);
  if (!traces.length) {
    panel.append(emptyPre('Sin trazas para mostrar. El viewer maneja trazas vacías sin bloquear la UI.'));
    return panel;
  }
  const list = document.createElement('div');
  list.className = 'viewer-list';
  for (const trace of traces.slice(0, 25)) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'viewer-list__item';
    button.textContent = `${trace.trace_id} · spans=${trace.spans_total ?? 0} · events=${trace.events_total ?? 0}`;
    button.addEventListener('click', () => { void onSelect(trace.trace_id); });
    list.append(button);
  }
  panel.append(list);
  return panel;
}

function renderMetricsPanel(response?: DevPilotApplicationResponse, error?: string): HTMLElement {
  const panel = panelShell('Métricas AgentOps', error ?? response?.message ?? 'Pendiente de consulta.');
  panel.append(emptyPre(JSON.stringify(response?.data?.summary ?? { message: 'Sin métricas todavía.' }, null, 2)));
  return panel;
}

function renderDetailPanel(title: string, response?: DevPilotApplicationResponse, error?: string): HTMLElement {
  const panel = panelShell(title, error ?? response?.message ?? 'Selecciona un elemento para ver el detalle.');
  panel.append(emptyPre(JSON.stringify(response?.data ?? { detail: 'Sin detalle seleccionado.' }, null, 2)));
  if (response?.findings?.length) panel.append(renderFindingTable(response.findings));
  return panel;
}

function panelShell(titleText: string, messageText: string): HTMLElement {
  const panel = document.createElement('section');
  panel.className = 'viewer-card';
  const title = document.createElement('h3');
  title.textContent = titleText;
  const message = document.createElement('p');
  message.textContent = messageText;
  panel.append(title, message);
  return panel;
}

function emptyPre(text: string): HTMLElement {
  const pre = document.createElement('pre');
  pre.className = 'viewer-pre';
  pre.textContent = text;
  return pre;
}
