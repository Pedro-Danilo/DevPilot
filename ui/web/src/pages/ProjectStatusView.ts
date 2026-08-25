import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { GuidedSdlcNextAction, GuidedSdlcProjectStatus, GuidedSdlcProjectStatusResponseData, MiasiApplicabilityStatus } from '../api/types';
import { renderStepActionAdvisor, renderStepActionAdvisorError } from '../components/StepActionAdvisor';

const ROUTE_ID = 'ui.project-status';

export function renderProjectStatusView(tokenProvider: () => string): HTMLElement {
  const root = document.createElement('section');
  root.className = 'project-status-view';
  root.dataset.routeId = ROUTE_ID;
  root.dataset.uiState = 'loading';
  root.setAttribute('aria-live', 'polite');

  const intro = document.createElement('div');
  intro.className = 'project-status-hero';
  const eyebrow = document.createElement('p');
  eyebrow.className = 'project-status-eyebrow';
  eyebrow.textContent = 'Guided SDLC · estado persistente';
  const title = document.createElement('h2');
  title.textContent = 'Dónde estás y qué sigue';
  const description = document.createElement('p');
  description.textContent = 'Proyección read-only del estado de ingeniería. DevPilot no avanza el workflow desde esta vista.';
  intro.append(eyebrow, title, description);

  const content = document.createElement('div');
  content.className = 'project-status-content';
  content.append(renderLoading());
  root.append(intro, content);
  void loadProjectStatus(root, content, tokenProvider);
  return root;
}

async function loadProjectStatus(root: HTMLElement, content: HTMLElement, tokenProvider: () => string): Promise<void> {
  root.dataset.uiState = 'loading';
  try {
    const response = await new DevPilotApiClient({ token: tokenProvider() }).projectStatus();
    const data = response.data;
    const statePanel = renderState(data);
    const advisorMount = document.createElement('div');
    advisorMount.className = 'step-action-advisor-mount';
    advisorMount.setAttribute('aria-live', 'polite');
    const loading = document.createElement('section');
    loading.className = 'step-action-advisor panel';
    loading.textContent = 'Calculando opciones permitidas para el paso actual…';
    advisorMount.append(loading);
    content.replaceChildren(statePanel, advisorMount);
    root.dataset.uiState = normalizeUiState(data.ui_state);
    void loadStepActions(advisorMount, tokenProvider);
  } catch (error) {
    const state = classifyError(error);
    content.replaceChildren(renderRequestError(error, state));
    root.dataset.uiState = state;
  }
}

async function loadStepActions(mount: HTMLElement, tokenProvider: () => string): Promise<void> {
  try {
    const response = await new DevPilotApiClient({ token: tokenProvider() }).stepActions();
    mount.replaceChildren(renderStepActionAdvisor(response.data));
  } catch (error) {
    mount.replaceChildren(renderStepActionAdvisorError(error));
  }
}

function renderLoading(): HTMLElement {
  const panel = panelBase('Cargando estado del proyecto…', 'Consultando la proyección local y protegida.', 'loading');
  panel.setAttribute('aria-busy', 'true');
  return panel;
}

function renderState(data: GuidedSdlcProjectStatusResponseData): HTMLElement {
  const state = normalizeUiState(data.ui_state);
  const status = data.project_status ?? {};
  const next = data.next_action ?? {};
  if (state === 'empty') return renderEmpty(status, next);
  if (state === 'unknown') return renderUnknown(status, next);

  const wrapper = document.createElement('div');
  wrapper.className = 'project-status-grid';
  wrapper.append(renderOverview(status, state));
  wrapper.append(renderNextAction(next));
  wrapper.append(renderSignals(status));
  wrapper.append(renderMiasi(status.miasi ?? {}));
  wrapper.append(renderBlockers(status));
  return wrapper;
}

function renderOverview(status: GuidedSdlcProjectStatus, state: string): HTMLElement {
  const panel = document.createElement('article');
  panel.className = 'panel project-status-card project-status-card--overview';
  const heading = document.createElement('div');
  heading.className = 'project-status-card__heading';
  const title = document.createElement('h3');
  title.textContent = 'Estado de ingeniería';
  const badge = document.createElement('span');
  badge.className = `project-status-state project-status-state--${state}`;
  badge.textContent = humanState(state);
  heading.append(title, badge);

  const progress = asNumber(status.progress?.percent);
  const progressWrap = document.createElement('div');
  progressWrap.className = 'project-status-progress';
  const progressLabel = document.createElement('div');
  progressLabel.className = 'project-status-progress__label';
  progressLabel.append(textPair('Progreso', progress === null ? 'No disponible' : `${progress}%`));
  const bar = document.createElement('progress');
  bar.max = 100;
  bar.value = progress ?? 0;
  bar.setAttribute('aria-label', 'Progreso Guided SDLC');
  progressWrap.append(progressLabel, bar);

  const facts = document.createElement('dl');
  facts.className = 'project-status-facts';
  addFact(facts, 'Workspace', safe(status.workspace_id));
  addFact(facts, 'Proyecto', safe(status.project_id));
  addFact(facts, 'Fase', safe(status.phase));
  addFact(facts, 'Paso actual', safe(status.current_step));
  addFact(facts, 'Lifecycle', safe(status.lifecycle_status));
  addFact(facts, 'MIPSoftware', safe(status.mipsoftware?.status));
  addFact(facts, 'MIASI', safe(status.miasi?.status));
  panel.append(heading, progressWrap, facts);
  return panel;
}

function renderNextAction(action: GuidedSdlcNextAction): HTMLElement {
  const panel = document.createElement('article');
  panel.className = 'panel project-status-card project-status-card--next';
  const title = document.createElement('h3');
  title.textContent = 'Próxima acción';
  const kind = document.createElement('p');
  kind.className = 'project-status-next-kind';
  kind.textContent = safe(action.kind, 'INSPECT_STATE');
  const explanation = document.createElement('p');
  explanation.textContent = safe(action.explanation, 'No existe una acción determinística disponible todavía.');
  const reason = document.createElement('p');
  reason.className = 'project-status-muted';
  reason.textContent = `Razón: ${safe(action.reason_code)}`;

  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'project-status-continue';
  button.textContent = 'Continuar';
  const target = safe(action.navigation_target, 'project-status');
  const destination = navigationPath(target);
  const canNavigate = action.available === true && action.mutating !== true && destination !== null;
  if (!canNavigate) {
    button.disabled = true;
    button.setAttribute('aria-disabled', 'true');
    const disabled = safe(action.disabled_reason, action.mutating ? 'La acción requiere una ola futura o aprobación.' : 'Destino todavía no disponible en la UI.');
    button.title = disabled;
    const note = document.createElement('p');
    note.className = 'project-status-disabled-reason';
    note.textContent = `Continuar deshabilitado: ${disabled}`;
    panel.append(title, kind, explanation, reason, button, note);
    return panel;
  }
  button.addEventListener('click', () => {
    globalThis.location.assign(destination);
  });
  panel.append(title, kind, explanation, reason, button);
  return panel;
}

function renderSignals(status: GuidedSdlcProjectStatus): HTMLElement {
  const panel = document.createElement('article');
  panel.className = 'panel project-status-card';
  const title = document.createElement('h3');
  title.textContent = 'Señales de control';
  const facts = document.createElement('dl');
  facts.className = 'project-status-facts';
  addFact(facts, 'Artifacts', safe(status.artifact_readiness?.status));
  addFact(facts, 'Approvals pendientes', String(Array.isArray(status.pending_approvals) ? status.pending_approvals.length : 0));
  addFact(facts, 'Quality', safe(status.quality?.status));
  addFact(facts, 'Git', safe(status.git?.status));
  addFact(facts, 'Revalidación', safe(status.revalidation?.status));
  addFact(facts, 'Freshness', safe(status.freshness?.status));
  addFact(facts, 'Model/token budget', safe(status.model_budget?.status, 'NOT_AVAILABLE'));
  panel.append(title, facts);
  return panel;
}


function renderMiasi(miasi: MiasiApplicabilityStatus): HTMLElement {
  const panel = document.createElement('article');
  panel.className = 'panel project-status-card project-status-card--miasi';
  panel.dataset.miasiStatus = safe(miasi.status, 'REVIEW_REQUIRED');
  panel.dataset.miasiGate = safe(miasi.gate_status, 'BLOCK');
  const heading = document.createElement('div');
  heading.className = 'project-status-card__heading';
  const title = document.createElement('h3');
  title.textContent = 'MIASI · Aplicabilidad y controles';
  const badge = document.createElement('span');
  const gate = safe(miasi.gate_status, 'BLOCK').toLowerCase();
  badge.className = `project-status-state project-status-state--${gate === 'pass' ? 'ready' : 'blocked'}`;
  badge.textContent = `${safe(miasi.status, 'REVIEW_REQUIRED')} · ${safe(miasi.gate_status, 'BLOCK')}`;
  heading.append(title, badge);

  const rationale = document.createElement('p');
  rationale.className = 'project-status-miasi-rationale';
  const reasons = Array.isArray(miasi.reason_codes) ? miasi.reason_codes : [];
  rationale.textContent = reasons.length ? `Razón: ${reasons.join(' · ')}` : 'Razón: clasificación MIASI no disponible.';

  const facts = document.createElement('dl');
  facts.className = 'project-status-facts';
  addFact(facts, 'Riesgo', safe(miasi.risk_level, 'unknown'));
  addFact(facts, 'Agent execution', miasi.agent_execution_allowed === true ? 'AVAILABLE' : 'UNAVAILABLE');
  addFact(facts, 'RAG execution', miasi.rag_execution_allowed === true ? 'AVAILABLE' : 'UNAVAILABLE');
  addFact(facts, 'Reevaluación', miasi.reevaluation_required === true ? 'REQUIRED' : 'NOT_REQUIRED');

  const controlsTitle = document.createElement('h4');
  controlsTitle.textContent = 'Controles requeridos';
  const controls = document.createElement('ul');
  controls.className = 'project-status-miasi-controls';
  const rows = Array.isArray(miasi.required_controls) ? miasi.required_controls : [];
  if (!rows.length) {
    const row = document.createElement('li');
    row.textContent = safe(miasi.status) === 'NOT_APPLICABLE' ? 'No aplican controles MIASI para la declaración actual.' : 'No hay controles materializados todavía.';
    controls.append(row);
  } else {
    for (const control of rows) {
      const row = document.createElement('li');
      row.dataset.ready = control.ready === true ? 'true' : 'false';
      const name = document.createElement('strong');
      name.textContent = safe(control.kind, 'Control');
      const detail = document.createElement('span');
      detail.textContent = ` — ${safe(control.lifecycle, 'MISSING')} · ${safe(control.artifact_id)}`;
      row.append(name, detail);
      controls.append(row);
    }
  }

  const missing = Array.isArray(miasi.missing_controls) ? miasi.missing_controls : [];
  const warning = document.createElement('p');
  warning.className = 'project-status-disabled-reason';
  warning.hidden = missing.length === 0;
  warning.textContent = missing.length ? `Faltan controles: ${missing.join(', ')}. El avance permanece bloqueado.` : '';

  const execution = document.createElement('p');
  execution.className = 'project-status-muted';
  execution.textContent = `AGENT/RAG permanecen no ejecutables en GSDLC-05: ${safe(miasi.execution_reason_code, 'GSDLC_06_07_NOT_IMPLEMENTED')}.`;
  panel.append(heading, rationale, facts, controlsTitle, controls, warning, execution);
  return panel;
}

function renderBlockers(status: GuidedSdlcProjectStatus): HTMLElement {
  const panel = document.createElement('article');
  panel.className = 'panel project-status-card';
  const title = document.createElement('h3');
  title.textContent = 'Blockers';
  const rows = Array.isArray(status.blockers) ? status.blockers : [];
  if (!rows.length) {
    const empty = document.createElement('p');
    empty.textContent = 'No hay blockers materializados en el estado actual.';
    panel.append(title, empty);
    return panel;
  }
  const list = document.createElement('ul');
  list.className = 'project-status-blockers';
  for (const row of rows) {
    const item = document.createElement('li');
    const code = document.createElement('strong');
    code.textContent = safe(row.code, 'BLOCKER');
    const message = document.createElement('span');
    message.textContent = ` — ${safe(row.message, 'Bloqueo sin descripción')}`;
    item.append(code, message);
    list.append(item);
  }
  panel.append(title, list);
  return panel;
}

function renderEmpty(status: GuidedSdlcProjectStatus, action: GuidedSdlcNextAction): HTMLElement {
  const panel = panelBase('No hay estado de ingeniería disponible', 'El workspace está registrado, pero todavía no existe un WorkspaceEngineeringState proyectable.', 'empty');
  const detail = document.createElement('p');
  detail.className = 'project-status-muted';
  detail.textContent = `NextAction: ${safe(action.reason_code, 'STATE_AUTHORITY_UNAVAILABLE')} · ${safe(status.reason, 'unknown')}`;
  panel.append(detail);
  return panel;
}

function renderUnknown(status: GuidedSdlcProjectStatus, action: GuidedSdlcNextAction): HTMLElement {
  const panel = panelBase('Estado incompleto o desconocido', 'DevPilot no fabricará un PASS cuando la autoridad de estado no sea suficiente.', 'unknown');
  const detail = document.createElement('p');
  detail.textContent = `Razón: ${safe(action.reason_code, safe(status.reason, 'unknown'))}`;
  panel.append(detail);
  return panel;
}

function renderRequestError(error: unknown, state: string): HTMLElement {
  let title = 'No se pudo cargar Project Status';
  let description = 'La API local devolvió un error. Verifica la sesión local y reintenta.';
  if (state === 'timeout') { title = 'La API tardó demasiado'; description = 'El request alcanzó su timeout local; no se cambió ningún estado.'; }
  if (state === 'unauthorized' || state === 'forbidden') { title = 'Acceso local no autorizado'; description = 'Configura un token local válido. No se habilita auth productiva en GSDLC-01.'; }
  if (state === 'api_down') { title = 'API local no disponible'; description = 'Project Status necesita la API local. No existe lectura directa de filesystem/Git desde el navegador.'; }
  const panel = panelBase(title, description, state);
  const technical = document.createElement('p');
  technical.className = 'project-status-muted';
  technical.textContent = error instanceof DevPilotApiError ? `HTTP/local status: ${error.status}` : 'Error local sanitizado.';
  panel.append(technical);
  return panel;
}

function panelBase(titleText: string, descriptionText: string, state: string): HTMLElement {
  const panel = document.createElement('article');
  panel.className = `panel project-status-card project-status-card--message project-status-card--${state}`;
  const title = document.createElement('h3');
  title.textContent = titleText;
  const description = document.createElement('p');
  description.textContent = descriptionText;
  panel.append(title, description);
  return panel;
}

function classifyError(error: unknown): string {
  if (!(error instanceof DevPilotApiError)) return 'error';
  if (error.status === 408) return 'timeout';
  if (error.status === 401) return 'unauthorized';
  if (error.status === 403) return 'forbidden';
  if (error.status === 0) return 'api_down';
  return 'error';
}

function normalizeUiState(value: string): string {
  const normalized = String(value || 'UNKNOWN').toLowerCase();
  if (normalized === 'revalidation_required') return 'revalidation';
  return normalized;
}

function humanState(state: string): string {
  const labels: Record<string, string> = {
    ready: 'READY', blocked: 'BLOCKED', revalidation: 'REVALIDATION REQUIRED', stale: 'STALE', unknown: 'UNKNOWN', empty: 'EMPTY',
  };
  return labels[state] ?? state.toUpperCase();
}

function navigationPath(target: string): string | null {
  const mapping: Record<string, string> = {
    'ui.approvals': '/approvals',
    'project-status': '/project/status',
  };
  return mapping[target] ?? null;
}

function safe(value: unknown, fallback = 'unknown'): string {
  if (value === null || value === undefined || value === '') return fallback;
  return String(value).slice(0, 512);
}

function asNumber(value: unknown): number | null {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.min(number, 100)) : null;
}

function addFact(list: HTMLDListElement, label: string, value: string): void {
  const dt = document.createElement('dt');
  dt.textContent = label;
  const dd = document.createElement('dd');
  dd.textContent = value;
  list.append(dt, dd);
}

function textPair(label: string, value: string): DocumentFragment {
  const fragment = document.createDocumentFragment();
  const strong = document.createElement('strong');
  strong.textContent = label;
  const span = document.createElement('span');
  span.textContent = value;
  fragment.append(strong, span);
  return fragment;
}
