import { DevPilotApiClient } from '../api/client';
import type { DevPilotApplicationResponse, GovernedJobSnapshot, JobLogEntry } from '../api/types';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';

interface JobsState {
  loading: boolean;
  jobs?: DevPilotApplicationResponse;
  detail?: DevPilotApplicationResponse;
  logs?: DevPilotApplicationResponse;
  selected?: GovernedJobSnapshot;
  errors: Record<string, string>;
  workspace: string;
  capability: string;
  status: string;
  polling: boolean;
  logCursor: number;
}

const ACTIVE = new Set(['queued', 'running', 'cancel-requested', 'rollback-running']);
const RETRYABLE = new Set(['pass', 'pass-with-gaps', 'block', 'error', 'cancelled', 'rolled-back', 'expired']);

export function renderJobsView(tokenProvider: () => string, initialJobId?: string): HTMLElement {
  const section = document.createElement('section');
  section.className = 'viewer-panel jobs-console';
  section.dataset.devpilotUiContract = 'ui.jobs';
  const state: JobsState = { loading: false, errors: {}, workspace: '', capability: '', status: '', polling: false, logCursor: 0 };
  let pollHandle: number | undefined;

  async function refresh(): Promise<void> {
    state.loading = true; draw();
    try {
      state.jobs = await new DevPilotApiClient({ token: tokenProvider() }).listJobs({ workspace_id: state.workspace || undefined, capability_id: state.capability || undefined, status: state.status || undefined, limit: 100 });
      delete state.errors.jobs;
    } catch (error) { state.errors.jobs = message(error); }
    state.loading = false; draw();
  }

  async function inspect(job: GovernedJobSnapshot): Promise<void> {
    state.selected = job; await inspectId(job.job_id);
  }

  async function inspectId(jobId: string): Promise<void> {
    state.logCursor = 0; state.loading = true; draw();
    const client = new DevPilotApiClient({ token: tokenProvider() });
    try {
      state.detail = await client.inspectJob(jobId);
      state.logs = await client.jobLogs(jobId, 0, 200);
      const detailJob = (state.detail?.data as { job?: GovernedJobSnapshot } | undefined)?.job;
      if (detailJob) state.selected = detailJob;
      delete state.errors.detail; delete state.errors.logs;
    } catch (error) { state.errors.detail = message(error); }
    state.loading = false; draw();
  }

  async function cancel(): Promise<void> {
    if (!state.selected) return;
    state.loading = true; draw();
    try {
      state.detail = await new DevPilotApiClient({ token: tokenProvider() }).cancelJob(state.selected.job_id, { actor: 'local-owner', reason: 'Cancelación gobernada desde Job Console' });
      delete state.errors.action; await refresh();
    } catch (error) { state.errors.action = message(error); state.loading = false; draw(); }
  }

  async function retry(): Promise<void> {
    if (!state.selected) return;
    state.loading = true; draw();
    try {
      state.detail = await new DevPilotApiClient({ token: tokenProvider() }).retryJob(state.selected.job_id, { actor: 'local-owner', reason: 'Retry gobernado desde Job Console' });
      delete state.errors.action; await refresh();
    } catch (error) { state.errors.action = message(error); state.loading = false; draw(); }
  }

  function togglePolling(): void {
    state.polling = !state.polling;
    if (pollHandle !== undefined) { globalThis.clearInterval(pollHandle); pollHandle = undefined; }
    if (state.polling) pollHandle = globalThis.setInterval(() => { if (!state.loading) void refresh(); }, 3000);
    draw();
  }

  function draw(): void {
    section.replaceChildren();
    const header = document.createElement('div'); header.className = 'viewer-panel__header';
    const title = document.createElement('div');
    title.innerHTML = '<h2>Job Console</h2><p>Jobs activos e históricos, heartbeat, progreso, logs sanitizados, cancelación y retry gobernado.</p>';
    title.append(renderContractBadges('ui.jobs', { warning: 'Local-only · no shell arbitrario · cancel/retry sujetos a policy y budgets.' }));
    const controls = document.createElement('div'); controls.className = 'viewer-controls jobs-filters';
    controls.append(input('Workspace', state.workspace, (v) => state.workspace = v), input('Capability', state.capability, (v) => state.capability = v), statusSelect());
    const refreshButton = document.createElement('button'); refreshButton.textContent = state.loading ? 'Consultando…' : 'Actualizar'; refreshButton.disabled = state.loading; refreshButton.addEventListener('click', () => void refresh());
    const polling = document.createElement('button'); polling.className = state.polling ? '' : 'button-secondary'; polling.textContent = state.polling ? 'Polling activo 3s' : 'Activar polling'; polling.addEventListener('click', togglePolling);
    controls.append(refreshButton, polling); header.append(title, controls); section.append(header);

    if (state.loading) section.append(renderUiStateNotice('loading', 'Consultando jobs locales y estado de heartbeat.'));
    for (const [key, value] of Object.entries(state.errors)) section.append(renderUiStateNotice('error', `${key}: ${value}`));
    const jobs = ((state.jobs?.data as { jobs?: GovernedJobSnapshot[] } | undefined)?.jobs ?? []);
    if (!state.loading && state.jobs && jobs.length === 0) section.append(renderUiStateNotice('empty', 'No hay jobs para los filtros actuales. Esta consola no crea shell jobs; los producen capacidades registradas.'));

    const grid = document.createElement('div'); grid.className = 'jobs-grid';
    const index = document.createElement('article'); index.className = 'viewer-card jobs-index'; index.innerHTML = `<h3>Jobs</h3><p>${jobs.length} registro(s). Los jobs en stale/error requieren revisión, no reanudación automática.</p>`;
    const list = document.createElement('div'); list.className = 'viewer-list';
    for (const job of jobs) {
      const button = document.createElement('button'); button.className = 'viewer-list__item job-row';
      const stale = job.operational?.stale ? ' · STALE' : '';
      button.textContent = `${job.status.toUpperCase()}${stale} · ${job.capability_id} · ${job.workspace_id} · ${job.updated_at}`;
      button.addEventListener('click', () => { globalThis.history.replaceState({}, '', `/jobs/${job.job_id}`); void inspect(job); }); list.append(button);
    }
    index.append(list);

    const detail = document.createElement('article'); detail.className = 'viewer-card job-detail'; detail.innerHTML = '<h3>Detalle operacional</h3>';
    const snapshot = currentSnapshot();
    if (!snapshot) {
      const p = document.createElement('p'); p.textContent = 'Seleccione un job para ver lifecycle, heartbeat, artefactos, evidencias y acciones disponibles.'; detail.append(p);
    } else {
      const metrics = document.createElement('div'); metrics.className = 'job-metrics';
      for (const [label, value] of [['Estado', snapshot.status], ['Fase', snapshot.operational?.phase ?? snapshot.status], ['Progreso', `${snapshot.operational?.progress_percent ?? 0}%`], ['Heartbeat', heartbeatLabel(snapshot)], ['Duración', `${snapshot.operational?.duration_seconds ?? 0}s`], ['Correlación', snapshot.correlation_id]]) metrics.append(metric(label, value));
      detail.append(metrics);
      if (snapshot.operational?.stale) detail.append(renderUiStateNotice('block', 'Heartbeat vencido: el job se considera stale y debe reconciliarse; no se asume PASS.'));
      const actions = document.createElement('div'); actions.className = 'viewer-controls job-actions';
      const cancelButton = document.createElement('button'); cancelButton.textContent = 'Solicitar cancelación'; cancelButton.disabled = state.loading || !snapshot.supports_cancel || !['queued', 'running'].includes(snapshot.status); cancelButton.addEventListener('click', () => void cancel());
      const retryButton = document.createElement('button'); retryButton.className = 'button-secondary'; retryButton.textContent = 'Crear retry gobernado'; retryButton.disabled = state.loading || !RETRYABLE.has(snapshot.status) || snapshot.retry_count >= snapshot.retry_limit; retryButton.addEventListener('click', () => void retry());
      actions.append(cancelButton, retryButton); detail.append(actions);
      const refs = document.createElement('pre'); refs.className = 'viewer-pre'; refs.textContent = JSON.stringify({ artifact_refs: snapshot.artifact_refs, evidence_refs: snapshot.evidence_refs, errors: snapshot.errors, result_summary: snapshot.result_summary, operational: snapshot.operational }, null, 2); detail.append(refs);
    }
    grid.append(index, detail); section.append(grid);

    const logsCard = document.createElement('article'); logsCard.className = 'viewer-card'; logsCard.innerHTML = '<h3>Logs sanitizados</h3><p>Polling local bounded. Tokens, secretos y credenciales son redactados en el backend.</p>';
    const pre = document.createElement('pre'); pre.className = 'viewer-pre job-log-stream';
    const entries = ((state.logs?.data as { entries?: JobLogEntry[] } | undefined)?.entries ?? []);
    pre.textContent = entries.length ? entries.map((entry) => `${entry.timestamp} ${entry.level} [${entry.phase}] ${entry.message}`).join('\n') : 'Sin logs para el job seleccionado.';
    logsCard.append(pre); section.append(logsCard);
  }

  function currentSnapshot(): GovernedJobSnapshot | undefined {
    return ((state.detail?.data as { job?: GovernedJobSnapshot } | undefined)?.job) ?? state.selected;
  }

  function input(labelText: string, value: string, setter: (value: string) => void): HTMLElement {
    const label = document.createElement('label'); label.textContent = labelText; const field = document.createElement('input'); field.type = 'search'; field.value = value; field.placeholder = `Filtrar ${labelText.toLowerCase()}`; field.addEventListener('input', () => setter(field.value)); label.append(field); return label;
  }

  function statusSelect(): HTMLElement {
    const label = document.createElement('label'); label.textContent = 'Estado'; const select = document.createElement('select');
    for (const value of ['', 'planned', 'pending-approval', 'approved', 'queued', 'running', 'pass', 'pass-with-gaps', 'block', 'error', 'cancel-requested', 'cancelled', 'rollback-running', 'rolled-back', 'expired']) { const option = document.createElement('option'); option.value = value; option.textContent = value || 'Todos'; option.selected = value === state.status; select.append(option); }
    select.addEventListener('change', () => { state.status = select.value; }); label.append(select); return label;
  }

  draw(); if (tokenProvider()) { if (initialJobId) void inspectId(initialJobId); else void refresh(); } return section;
}

function metric(label: string, value: string | number): HTMLElement { const div = document.createElement('div'); div.className = 'job-metric'; const strong = document.createElement('strong'); strong.textContent = String(value); const span = document.createElement('span'); span.textContent = label; div.append(strong, span); return div; }
function heartbeatLabel(job: GovernedJobSnapshot): string { const age = job.operational?.heartbeat_age_seconds; return age === null || age === undefined ? 'sin heartbeat' : `${age}s${job.operational?.stale ? ' · STALE' : ''}`; }
function message(error: unknown): string { return error instanceof Error ? error.message : String(error); }
