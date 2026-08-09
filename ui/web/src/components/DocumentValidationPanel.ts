// ui.workspace-documents — UOC-003 validation and traceability surface
import { DevPilotApiClient } from '../api/client';
import type {
  DevPilotApplicationResponse,
  DevPilotFinding,
  WorkspaceTraceabilityData,
  WorkspaceTraceabilityRecord,
  WorkspaceValidationJobData,
  WorkspaceValidationNavigation,
  WorkspaceValidationPlan,
} from '../api/types';
import { renderContractBadges, renderUiStateNotice } from './ContractBadges';

const DEFAULT_SCOPES = [
  'frontmatter',
  'artifact_profile',
  'links',
  'miasi',
  'readiness_strict',
  'checklist_pre_code',
  'traceability',
] as const;

const RESIDUAL_CLI_BRIDGES = [
  { capabilityId: 'cli.docs-governance.validate', targetSprint: 'UOC-007', reason: 'El perfil global completo conserva opciones avanzadas y exportes que todavía no tienen contrato UI tipado.' },
  { capabilityId: 'cli.industrial-readiness.check', targetSprint: 'UOC-007', reason: 'La evaluación industrial transversal permanece registrada como bridge hasta el framework común de jobs.' },
  { capabilityId: 'cli.workspace.readiness-preview', targetSprint: 'UOC-007', reason: 'La vista UOC-003 muestra readiness strict pre-code; el preview operacional completo conserva bridge gobernado.' },
] as const;

export interface DocumentValidationPanelOptions {
  tokenProvider: () => string;
  onNavigate: (navigation: WorkspaceValidationNavigation, origin: 'finding' | 'traceability') => Promise<void> | void;
}

interface ValidationPanelState {
  planning: boolean;
  executing: boolean;
  loadingTraceability: boolean;
  error?: string;
  planResponse?: DevPilotApplicationResponse;
  plan?: WorkspaceValidationPlan;
  execution?: DevPilotApplicationResponse<WorkspaceValidationJobData>;
  traceability?: DevPilotApplicationResponse<WorkspaceTraceabilityData>;
  findingSeverityFilter: string;
  findingPage: number;
  navigationPending: boolean;
  navigationStatus?: string;
  navigationError?: string;
  navigationContext?: 'finding' | 'traceability';
}

export function createDocumentValidationPanel(options: DocumentValidationPanelOptions): HTMLElement {
  const root = document.createElement('section');
  root.className = 'panel document-validation-panel';
  root.dataset.devpilotUiContract = 'ui.workspace-document-validation';
  root.setAttribute('aria-label', 'Validación y trazabilidad documental');
  const state: ValidationPanelState = { planning: false, executing: false, loadingTraceability: false, findingSeverityFilter: 'all', findingPage: 0, navigationPending: false };

  async function plan(): Promise<void> {
    if (state.planning || state.executing) return;
    state.planning = true;
    state.error = undefined;
    state.execution = undefined;
    draw();
    try {
      const response = await new DevPilotApiClient({ token: options.tokenProvider() }).planWorkspaceValidations({
        scopes: [...DEFAULT_SCOPES],
        strict: true,
        timeout_seconds: 90,
      });
      state.planResponse = response;
      state.plan = (response.data as { plan?: WorkspaceValidationPlan }).plan;
      if (!response.ok || !state.plan) throw new Error(response.message || 'No se pudo crear el plan de validación.');
    } catch (error) {
      state.error = error instanceof Error ? error.message : String(error);
      state.plan = undefined;
    } finally {
      state.planning = false;
      draw();
    }
  }

  async function execute(): Promise<void> {
    if (state.executing || !state.plan) return;
    state.executing = true;
    state.error = undefined;
    draw();
    try {
      const response = await new DevPilotApiClient({ token: options.tokenProvider() }).executeWorkspaceValidations({
        plan_id: state.plan.plan_id,
        plan_hash: state.plan.plan_hash,
        plan: state.plan as unknown as Record<string, unknown>,
      }) as DevPilotApplicationResponse<WorkspaceValidationJobData>;
      state.execution = response;
      state.findingPage = 0;
      state.findingSeverityFilter = 'all';
      state.navigationStatus = undefined;
      state.navigationError = undefined;
      state.navigationContext = undefined;
      await loadTraceability();
    } catch (error) {
      state.error = error instanceof Error ? error.message : String(error);
    } finally {
      state.executing = false;
      draw();
    }
  }

  async function loadTraceability(): Promise<void> {
    if (state.loadingTraceability) return;
    state.loadingTraceability = true;
    try {
      state.traceability = await new DevPilotApiClient({ token: options.tokenProvider() }).workspaceTraceability() as DevPilotApplicationResponse<WorkspaceTraceabilityData>;
    } catch (error) {
      state.error = error instanceof Error ? error.message : String(error);
    } finally {
      state.loadingTraceability = false;
    }
  }

  function draw(): void {
    root.replaceChildren();
    const header = document.createElement('header');
    header.className = 'document-validation-panel__header';
    const heading = document.createElement('div');
    const title = document.createElement('h2');
    title.textContent = 'Validación y trazabilidad pre-code';
    const description = document.createElement('p');
    description.textContent = 'Plan inmutable → ejecución determinística → findings navegables → trace/report local. No modifica documentos fuente.';
    heading.append(title, description);
    header.append(heading, renderContractBadges('ui.workspace-document-validation', {
      dryRunLabel: 'Source read-only',
      warning: 'UOC-003 v1 preliminar: el job es síncrono; cancelación, heartbeat y cola gobernada llegan en UOC-007/UOC-008.',
    }));
    root.append(header);

    const controls = document.createElement('div');
    controls.className = 'document-validation-panel__controls';
    const planButton = document.createElement('button');
    planButton.type = 'button';
    planButton.textContent = state.planning ? 'Preparando plan…' : '1. Preparar validación estricta';
    planButton.disabled = state.planning || state.executing;
    planButton.addEventListener('click', () => void plan());
    const executeButton = document.createElement('button');
    executeButton.type = 'button';
    executeButton.textContent = state.executing ? 'Ejecutando validadores…' : '2. Ejecutar plan';
    executeButton.disabled = state.executing || state.planning || !state.plan;
    executeButton.addEventListener('click', () => void execute());
    const refreshButton = document.createElement('button');
    refreshButton.type = 'button';
    refreshButton.className = 'traceability-refresh-button';
    refreshButton.textContent = state.loadingTraceability ? 'Actualizando trazabilidad…' : state.traceability ? 'Recargar trazabilidad' : 'Actualizar trazabilidad';
    refreshButton.disabled = state.loadingTraceability || state.executing;
    refreshButton.addEventListener('click', async () => { await loadTraceability(); draw(); });
    controls.append(planButton, executeButton, refreshButton);
    root.append(controls);
    if (state.traceability && !state.executing) {
      const traceHint = document.createElement('p');
      traceHint.className = 'traceability-refresh-hint';
      traceHint.textContent = 'La matriz se cargó automáticamente al ejecutar el plan. Use “Recargar trazabilidad” solo para solicitar una lectura nueva.';
      root.append(traceHint);
    }
    root.append(renderResidualCliBridges());

    if (state.planning || state.executing) root.append(renderUiStateNotice('loading', state.planning ? 'Calculando hashes y presupuesto sin escribir evidencia…' : 'Ejecutando validadores tipados y escribiendo únicamente report/trace runtime…'));
    if (state.error) root.append(renderUiStateNotice(state.error.includes('403') ? 'block' : 'error', state.error));
    if (!state.plan && !state.planning && !state.error) root.append(renderUiStateNotice('empty', 'Primero crea el plan. La ejecución queda vinculada a sus hashes y al workspace activo.'));
    if (state.plan) root.append(renderPlan(state.plan));
    if (state.execution) root.append(renderExecution(state.execution, options.onNavigate, state, draw));
    if (state.traceability) root.append(renderTraceability(state.traceability, options.onNavigate, state, draw));
  }

  draw();
  return root;
}


function renderResidualCliBridges(): HTMLElement {
  const details = document.createElement('details');
  details.className = 'document-validation-bridges';
  const summary = document.createElement('summary');
  summary.textContent = `Bridges CLI residuales registrados (${RESIDUAL_CLI_BRIDGES.length})`;
  const intro = document.createElement('p');
  intro.textContent = 'No se ejecutan desde el navegador. Permanecen declarados, gobernados y diferidos hasta disponer de Application Service, policy, job y evidencia equivalentes.';
  const list = document.createElement('ul');
  for (const bridge of RESIDUAL_CLI_BRIDGES) {
    const item = document.createElement('li');
    const id = document.createElement('code');
    id.textContent = bridge.capabilityId;
    const text = document.createElement('span');
    text.textContent = ` · ${bridge.targetSprint} · ${bridge.reason}`;
    item.append(id, text);
    list.append(item);
  }
  details.append(summary, intro, list);
  return details;
}

function renderPlan(plan: WorkspaceValidationPlan): HTMLElement {
  const section = document.createElement('section');
  section.className = 'document-validation-plan';
  const title = document.createElement('h3');
  title.textContent = 'Plan listo';
  const summary = document.createElement('div');
  summary.className = 'validation-summary-grid';
  summary.append(
    metric('Artefactos pre-code', String(plan.artifacts.length), plan.artifacts.length === 8 ? 'pass' : 'warn'),
    metric('Validaciones', String(plan.scopes.length), plan.scopes.length === DEFAULT_SCOPES.length ? 'pass' : 'warn'),
    metric('Strict', plan.strict ? 'Sí' : 'No', plan.strict ? 'pass' : 'warn'),
    metric('Fuente', 'Read-only', 'pass'),
  );
  const details = document.createElement('details');
  const detailTitle = document.createElement('summary');
  detailTitle.textContent = 'Ver identidad y artefactos del plan';
  const id = document.createElement('code');
  id.textContent = `${plan.plan_id} · ${plan.plan_hash}`;
  const list = document.createElement('ul');
  for (const artifact of plan.artifacts) {
    const item = document.createElement('li');
    item.textContent = `${artifact.role}: ${artifact.relative_path} · ${artifact.sha256.slice(0, 12)}…`;
    list.append(item);
  }
  details.append(detailTitle, id, list);
  section.append(title, summary, details);
  return section;
}

function renderExecution(response: DevPilotApplicationResponse<WorkspaceValidationJobData>, onNavigate: (navigation: WorkspaceValidationNavigation, origin: 'finding' | 'traceability') => Promise<void> | void, state: ValidationPanelState, redraw: () => void): HTMLElement {
  const section = document.createElement('section');
  section.className = 'document-validation-results';
  const data = response.data ?? {};
  const summary = data.summary ?? {};
  const status = String(summary.status ?? (response.ok ? 'pass' : 'block')).toUpperCase();
  const heading = document.createElement('div');
  heading.className = 'document-validation-results__heading';
  const title = document.createElement('h3');
  title.textContent = 'Resultado de validación';
  const badge = document.createElement('span');
  badge.className = `badge ${response.ok ? 'pass' : 'block'}`;
  badge.textContent = status;
  heading.append(title, badge);
  section.append(heading);

  const counts = summary.findings_by_severity as Record<string, unknown> | undefined;
  const metrics = document.createElement('div');
  metrics.className = 'validation-summary-grid';
  metrics.append(
    metric('Pasos', `${summary.steps_passed ?? 0}/${summary.steps_total ?? 0}`, response.ok ? 'pass' : 'warn'),
    metric('Findings', String(summary.findings_total ?? response.findings.length), response.ok ? 'pass' : 'warn'),
    metric('BLOCK', String(counts?.block ?? 0), Number(counts?.block ?? 0) === 0 ? 'pass' : 'block'),
    metric('ERROR', String(counts?.error ?? 0), Number(counts?.error ?? 0) === 0 ? 'pass' : 'block'),
  );
  section.append(metrics);

  const steps = document.createElement('div');
  steps.className = 'validation-steps';
  for (const step of data.steps ?? []) {
    const row = document.createElement('article');
    row.className = `validation-step validation-step--${step.status.toLowerCase()}`;
    const name = document.createElement('strong');
    name.textContent = humanScope(step.scope);
    const value = document.createElement('span');
    value.textContent = `${step.status} · ${step.duration_ms ?? 0} ms`;
    const message = document.createElement('p');
    message.textContent = step.message;
    row.append(name, value, message);
    steps.append(row);
  }
  section.append(steps, renderFindings(response.findings, onNavigate, state, redraw));

  const job = data.job;
  if (job) {
    const evidence = document.createElement('details');
    const summaryNode = document.createElement('summary');
    summaryNode.textContent = 'Evidencia runtime local';
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify({ job_id: job.job_id, trace_path: job.trace_path, report_paths: job.report_paths, event_ref: job.event_ref }, null, 2);
    evidence.append(summaryNode, pre);
    section.append(evidence);
  }
  return section;
}

function renderFindings(
  findings: DevPilotFinding[],
  onNavigate: (navigation: WorkspaceValidationNavigation, origin: 'finding' | 'traceability') => Promise<void> | void,
  state: ValidationPanelState,
  redraw: () => void,
): HTMLElement {
  const section = document.createElement('section');
  section.className = 'validation-findings';
  const title = document.createElement('h4');
  title.textContent = `Findings por severidad (${findings.length})`;
  section.append(title);
  if (!findings.length) {
    section.append(renderUiStateNotice('empty', 'No se registraron findings.'));
    return section;
  }

  const ordered = [...findings].sort((a, b) => severityRank(b.severity) - severityRank(a.severity));
  const severityCounts = new Map<string, number>();
  for (const finding of ordered) {
    const severity = String(finding.severity).toLowerCase();
    severityCounts.set(severity, (severityCounts.get(severity) ?? 0) + 1);
  }
  const availableSeverities = [...severityCounts.keys()].sort((a, b) => severityRank(b) - severityRank(a) || a.localeCompare(b));
  if (state.findingSeverityFilter !== 'all' && !severityCounts.has(state.findingSeverityFilter)) {
    state.findingSeverityFilter = 'all';
    state.findingPage = 0;
  }

  const toolbar = document.createElement('div');
  toolbar.className = 'validation-findings-toolbar';
  const filterLabel = document.createElement('label');
  filterLabel.textContent = 'Filtrar severidad';
  const filter = document.createElement('select');
  const allOption = document.createElement('option');
  allOption.value = 'all';
  allOption.textContent = `Todas (${ordered.length})`;
  filter.append(allOption);
  for (const severity of availableSeverities) {
    const option = document.createElement('option');
    option.value = severity;
    option.textContent = `${severity.toUpperCase()} (${severityCounts.get(severity) ?? 0})`;
    filter.append(option);
  }
  filter.value = state.findingSeverityFilter;
  filter.addEventListener('change', () => {
    state.findingSeverityFilter = filter.value;
    state.findingPage = 0;
    redraw();
  });
  filterLabel.append(filter);
  const pagingHint = document.createElement('p');
  pagingHint.className = 'muted';
  pagingHint.textContent = 'Se muestran 25 findings por página para evitar scroll masivo y mantener la navegación estable.';
  toolbar.append(filterLabel, pagingHint);
  section.append(toolbar);

  if (state.navigationContext === 'finding') {
    if (state.navigationPending) section.append(renderUiStateNotice('loading', state.navigationStatus ?? 'Abriendo documento del finding…'));
    else if (state.navigationError) section.append(renderUiStateNotice('error', state.navigationError));
    else if (state.navigationStatus) section.append(renderUiStateNotice('success', state.navigationStatus));
  }

  const filtered = state.findingSeverityFilter === 'all'
    ? ordered
    : ordered.filter((finding) => String(finding.severity).toLowerCase() === state.findingSeverityFilter);
  const pageSize = 25;
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  state.findingPage = Math.min(Math.max(0, state.findingPage), pageCount - 1);
  const startIndex = state.findingPage * pageSize;
  const pageItems = filtered.slice(startIndex, startIndex + pageSize);

  const list = document.createElement('div');
  list.className = 'validation-findings-list';
  for (const finding of pageItems) {
    const item = document.createElement('article');
    item.className = `validation-finding validation-finding--${String(finding.severity).toLowerCase()}`;
    const header = document.createElement('div');
    const id = document.createElement('code');
    id.textContent = finding.id;
    const severity = document.createElement('span');
    severity.className = `badge ${finding.severity === 'info' ? 'pass' : finding.severity === 'warning' ? 'warn' : 'block'}`;
    severity.textContent = String(finding.severity).toUpperCase();
    header.append(id, severity);
    const message = document.createElement('p');
    message.textContent = finding.message;
    item.append(header, message);
    const navigation = extractNavigation(finding);
    if (navigation.document_id) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'button-link';
      button.disabled = state.navigationPending;
      button.textContent = `Abrir ${navigation.relative_path ?? 'documento'}${navigation.section ? ` · ${navigation.section}` : ''}${navigation.line ? ` · línea ${navigation.line}` : ''}`;
      button.addEventListener('click', async () => {
        state.navigationPending = true;
        state.navigationContext = 'finding';
        state.navigationError = undefined;
        state.navigationStatus = `Abriendo ${navigation.relative_path ?? 'documento'}…`;
        redraw();
        try {
          await onNavigate(navigation, 'finding');
          state.navigationStatus = `Documento abierto: ${navigation.relative_path ?? 'documento'}${navigation.section ? ` · ${navigation.section}` : ''}${navigation.line ? ` · línea ${navigation.line}` : ''}.`;
        } catch (error) {
          state.navigationError = `No se pudo abrir el destino del finding: ${error instanceof Error ? error.message : String(error)}`;
          state.navigationStatus = undefined;
        } finally {
          state.navigationPending = false;
          redraw();
        }
      });
      item.append(button);
    } else if (finding.path) {
      const path = document.createElement('code');
      path.textContent = finding.path;
      item.append(path);
    }
    list.append(item);
  }
  section.append(list);

  const pagination = document.createElement('nav');
  pagination.className = 'validation-findings-pagination';
  pagination.setAttribute('aria-label', 'Paginación de findings');
  const previous = document.createElement('button');
  previous.type = 'button';
  previous.className = 'button-secondary';
  previous.textContent = '← Findings anteriores';
  previous.disabled = state.findingPage === 0 || state.navigationPending;
  previous.addEventListener('click', () => { state.findingPage = Math.max(0, state.findingPage - 1); redraw(); });
  const status = document.createElement('span');
  const first = filtered.length ? startIndex + 1 : 0;
  const last = Math.min(startIndex + pageItems.length, filtered.length);
  status.textContent = `${first}–${last} de ${filtered.length} · página ${state.findingPage + 1}/${pageCount}`;
  status.setAttribute('aria-live', 'polite');
  const next = document.createElement('button');
  next.type = 'button';
  next.className = 'button-secondary';
  next.textContent = 'Findings siguientes →';
  next.disabled = state.findingPage >= pageCount - 1 || state.navigationPending;
  next.addEventListener('click', () => { state.findingPage = Math.min(pageCount - 1, state.findingPage + 1); redraw(); });
  pagination.append(previous, status, next);
  section.append(pagination);
  return section;
}

function renderTraceability(
  response: DevPilotApplicationResponse<WorkspaceTraceabilityData>,
  onNavigate: (navigation: WorkspaceValidationNavigation, origin: 'finding' | 'traceability') => Promise<void> | void,
  state: ValidationPanelState,
  redraw: () => void,
): HTMLElement {
  const section = document.createElement('section');
  section.className = 'document-traceability';
  const title = document.createElement('h3');
  title.textContent = 'Matriz requisito → historia → riesgo/control → prueba';
  section.append(title);
  const traceability = response.data?.traceability;
  const matrix = traceability?.matrix ?? [];
  const summary = traceability?.summary ?? {};
  const metrics = document.createElement('div');
  metrics.className = 'validation-summary-grid';
  metrics.append(
    metric('Requisitos', String(summary.requirements_total ?? matrix.length), matrix.length ? 'pass' : 'warn'),
    metric('Completos', String(summary.complete_requirements_total ?? 0), Number(summary.complete_requirements_total ?? 0) === matrix.length && matrix.length > 0 ? 'pass' : 'warn'),
    metric('Cobertura', `${summary.coverage_percent ?? 0}%`, Number(summary.coverage_percent ?? 0) === 100 ? 'pass' : 'warn'),
    metric('Inferencia', 'No', 'pass'),
  );
  section.append(metrics);
  if (state.navigationContext === 'traceability') {
    if (state.navigationPending) section.append(renderUiStateNotice('loading', state.navigationStatus ?? 'Abriendo fuente de trazabilidad…'));
    else if (state.navigationError) section.append(renderUiStateNotice('error', state.navigationError));
    else if (state.navigationStatus) section.append(renderUiStateNotice('success', state.navigationStatus));
  }
  if (!matrix.length) {
    section.append(renderUiStateNotice('empty', 'No se encontraron identificadores de requisito explícitos en los artefactos pre-code.'));
    return section;
  }
  const wrapper = document.createElement('div');
  wrapper.className = 'traceability-table-wrapper';
  const table = document.createElement('table');
  table.className = 'traceability-table';
  const head = document.createElement('thead');
  const row = document.createElement('tr');
  for (const label of ['Requisito', 'Historia', 'Riesgo', 'Control', 'Prueba', 'Cobertura', 'Fuente']) {
    const cell = document.createElement('th');
    cell.scope = 'col';
    cell.textContent = label;
    row.append(cell);
  }
  head.append(row);
  const body = document.createElement('tbody');
  for (const record of matrix) body.append(traceabilityRow(record, onNavigate, state, redraw));
  table.append(head, body);
  wrapper.append(table);
  section.append(wrapper);
  return section;
}

function traceabilityRow(
  record: WorkspaceTraceabilityRecord,
  onNavigate: (navigation: WorkspaceValidationNavigation, origin: 'finding' | 'traceability') => Promise<void> | void,
  state: ValidationPanelState,
  redraw: () => void,
): HTMLTableRowElement {
  const row = document.createElement('tr');
  row.append(textCell(record.requirement_id), textCell(record.story_ids.join(', ') || '—'), textCell(record.risk_ids.join(', ') || '—'), textCell(record.control_ids.join(', ') || '—'), textCell(record.test_ids.join(', ') || '—'));
  const coverage = document.createElement('td');
  const complete = Boolean(record.coverage?.complete);
  const badge = document.createElement('span');
  badge.className = `badge ${complete ? 'pass' : 'warn'}`;
  badge.textContent = complete ? 'COMPLETA' : 'GAPS';
  coverage.append(badge);
  row.append(coverage);
  const source = document.createElement('td');
  if (record.navigation?.document_id) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'button-link';
    button.textContent = `${record.navigation.relative_path ?? 'documento'}:${record.navigation.line ?? '—'}`;
    button.disabled = state.navigationPending;
    button.addEventListener('click', async () => {
      const navigation = record.navigation ?? {};
      state.navigationPending = true;
      state.navigationContext = 'traceability';
      state.navigationError = undefined;
      state.navigationStatus = `Abriendo fuente ${navigation.relative_path ?? 'documento'}…`;
      redraw();
      try {
        await onNavigate(navigation, 'traceability');
        state.navigationStatus = `Fuente de trazabilidad abierta: ${navigation.relative_path ?? 'documento'}${navigation.line ? ` · línea ${navigation.line}` : ''}.`;
      } catch (error) {
        state.navigationError = `No se pudo abrir la fuente de trazabilidad: ${error instanceof Error ? error.message : String(error)}`;
        state.navigationStatus = undefined;
      } finally {
        state.navigationPending = false;
        redraw();
      }
    });
    source.append(button);
  } else source.textContent = record.navigation?.relative_path ?? '—';
  row.append(source);
  return row;
}

function metric(label: string, value: string, state: 'pass' | 'warn' | 'block'): HTMLElement {
  const item = document.createElement('div');
  item.className = `validation-metric validation-metric--${state}`;
  const term = document.createElement('span');
  term.textContent = label;
  const amount = document.createElement('strong');
  amount.textContent = value;
  item.append(term, amount);
  return item;
}

function textCell(value: string): HTMLTableCellElement {
  const cell = document.createElement('td');
  cell.textContent = value;
  return cell;
}

function extractNavigation(finding: DevPilotFinding): WorkspaceValidationNavigation {
  const metadata = finding.metadata ?? {};
  const candidate = metadata.navigation;
  if (candidate && typeof candidate === 'object') return candidate as WorkspaceValidationNavigation;
  return {
    relative_path: finding.path,
    document_id: typeof metadata.document_id === 'string' ? metadata.document_id : undefined,
    line: typeof metadata.line === 'number' ? metadata.line : undefined,
    section: typeof metadata.section === 'string' ? metadata.section : undefined,
  };
}

function severityRank(severity: string): number {
  return ({ error: 4, block: 3, warning: 2, info: 1 } as Record<string, number>)[String(severity).toLowerCase()] ?? 0;
}

function humanScope(scope: string): string {
  return ({
    frontmatter: 'Frontmatter',
    artifact_profile: 'Artifact profile',
    links: 'Enlaces',
    miasi: 'MIASI',
    readiness_strict: 'Readiness strict',
    checklist_pre_code: 'Checklist pre-code',
    traceability: 'Trazabilidad',
  } as Record<string, string>)[scope] ?? scope;
}
