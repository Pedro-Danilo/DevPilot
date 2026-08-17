import { renderUoc011BrowserStateFixture } from '../testing/Uoc011BrowserStateFixture';
import { DevPilotApiClient } from '../api/client';
import type { ApprovalRecordItem, DevPilotApplicationResponse } from '../api/types';
import { idleOutcome, renderDryRunActionForm } from '../components/DryRunActionForm';
import type { DryRunUiOutcome } from '../components/DryRunActionForm';
import { renderFindingTable } from '../components/FindingTable';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { renderWorkspaceContextPanel } from '../components/WorkspaceContextPanel';

interface ApprovalState {
  approvals?: DevPilotApplicationResponse;
  portfolio?: DevPilotApplicationResponse;
  capabilities?: DevPilotApplicationResponse;
  selected?: DevPilotApplicationResponse;
  actionResult?: DevPilotApplicationResponse;
  requestResult?: DevPilotApplicationResponse;
  errors: Record<string, string>;
  statusFilter: string;
  pendingAction?: string;
  actionOutcome: DryRunUiOutcome;
  durations: Record<string, number>;
}

export function renderApprovalCenterView(tokenProvider: () => string): HTMLElement {
  const section = document.createElement('section');
  section.className = 'approval-panel';
  const uoc011Fixture = renderUoc011BrowserStateFixture('ui.approvals');
  if (uoc011Fixture) return uoc011Fixture;
  const state: ApprovalState = { errors: {}, statusFilter: '', actionOutcome: idleOutcome(), durations: {} };

  async function loadApprovals(): Promise<void> {
    const client = new DevPilotApiClient({ token: tokenProvider() });
    const started = performance.now();
    state.approvals = await client.listApprovals({ status: state.statusFilter || undefined, limit: 100 });
    state.durations.approvals = Math.round(performance.now() - started);
    delete state.errors.approvals;
  }

  async function loadPortfolio(): Promise<void> {
    const client = new DevPilotApiClient({ token: tokenProvider() });
    const started = performance.now();
    state.portfolio = await client.portfolioStatus();
    state.durations.portfolio = Math.round(performance.now() - started);
    delete state.errors.portfolio;
  }


  async function loadCapabilities(): Promise<void> {
    const client = new DevPilotApiClient({ token: tokenProvider() });
    try {
      state.capabilities = await client.authCapabilities('devpilot-local');
      delete state.errors.capabilities;
    } catch (error) {
      state.errors.capabilities = error instanceof Error ? error.message : String(error);
    }
  }

  async function runPending(action: string, work: () => Promise<void>, errorKey: string): Promise<void> {
    if (state.pendingAction) return;
    state.pendingAction = action;
    delete state.errors[errorKey];
    draw();
    try {
      await work();
    } catch (error) {
      state.errors[errorKey] = error instanceof Error ? error.message : String(error);
    } finally {
      state.pendingAction = undefined;
      draw();
    }
  }

  async function refresh(): Promise<void> {
    await runPending('refresh', async () => { await Promise.all([loadApprovals(), loadPortfolio(), loadCapabilities()]); }, 'approvals');
  }

  async function selectApproval(approvalId: string): Promise<void> {
    await runPending(`show:${approvalId}`, async () => {
      state.selected = await new DevPilotApiClient({ token: tokenProvider() }).showApproval(approvalId);
    }, 'selected');
  }

  async function decide(approvalId: string, decision: 'approve' | 'deny'): Promise<void> {
    await runPending(`${decision}:${approvalId}`, async () => {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      state.selected = await client.decideApproval(approvalId, decision, { reason: `${decision} from authenticated Approval Center` });
      await loadApprovals();
    }, 'selected');
  }

  async function requestApprovalFromForm(): Promise<void> {
    const value = (id: string): string => section.querySelector<HTMLInputElement>(`#${id}`)?.value.trim() ?? '';
    const payload = {
      tool_id: value('approval-tool-id') || 'docs.review',
      action: value('approval-action') || 'approve',
      subject: value('approval-subject'),
      reason: value('approval-reason'),
      scope: value('approval-scope') || undefined,
      ttl_minutes: Number(value('approval-ttl') || '120'),
    };
    if (!payload.subject || !payload.reason) {
      state.errors.requestResult = 'Subject y reason son obligatorios para crear un approval trazable.';
      draw();
      return;
    }
    await runPending('request', async () => {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      state.requestResult = await client.requestApproval(payload);
      const created = (state.requestResult.data as { approval?: ApprovalRecordItem }).approval;
      if (created?.approval_id) state.selected = await client.showApproval(created.approval_id);
      await loadApprovals();
    }, 'requestResult');
  }

  function draw(): void {
    section.replaceChildren();
    const header = document.createElement('div');
    header.className = 'viewer-panel__header';
    const titleBlock = document.createElement('div');
    const title = document.createElement('h2');
    title.textContent = 'Approval Center y Action Launcher';
    const subtitle = document.createElement('p');
    subtitle.textContent = 'Approvals locales ligados a sesión humana, roles efectivos, scope y separación de funciones.';
    titleBlock.append(title, subtitle, renderContractBadges('ui.approvals', { warning: 'Mutaciones limitadas al lifecycle local de approvals; ejecución destructiva bloqueada.' }));

    const controls = document.createElement('div');
    controls.className = 'viewer-controls';
    const filterLabel = document.createElement('label');
    filterLabel.textContent = 'Filtrar estado';
    const filter = document.createElement('select');
    filter.disabled = Boolean(state.pendingAction);
    for (const [value, label] of [['', 'Todos'], ['requested', 'Requested'], ['approved', 'Approved'], ['denied', 'Denied'], ['revoked', 'Revoked'], ['expired', 'Expired']]) {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = label;
      option.selected = state.statusFilter === value;
      filter.append(option);
    }
    filter.addEventListener('change', () => { state.statusFilter = filter.value; void refresh(); });
    filterLabel.append(filter);
    const refreshButton = actionButton('Actualizar approvals', state.pendingAction === 'refresh' ? 'Ejecutando…' : 'Actualizar approvals', state.pendingAction, () => void refresh());
    controls.append(filterLabel, refreshButton);
    header.append(titleBlock, controls);
    section.append(header);

    section.append(renderWorkspaceContextPanel(state.portfolio, state.errors.portfolio, state.durations.portfolio));
    section.append(renderApprovalAuthorityPanel(state.capabilities, state.errors.capabilities));
    section.append(renderApprovalRequestForm(state, requestApprovalFromForm));

    const actionStatus = document.createElement('p');
    actionStatus.className = 'action-status';
    actionStatus.setAttribute('role', 'status');
    actionStatus.setAttribute('aria-live', 'polite');
    actionStatus.textContent = state.pendingAction ? `Ejecutando acción local: ${state.pendingAction}` : 'Approval Center listo.';
    section.append(actionStatus);

    const grid = document.createElement('div');
    grid.className = 'viewer-grid';
    grid.append(renderApprovalsPanel(state, selectApproval, decide));
    grid.append(renderActionPanel(state, tokenProvider, draw));
    section.append(grid);
    if (state.pendingAction) section.append(renderUiStateNotice('loading', `Acción en curso ${state.pendingAction}. Los controles permanecen deshabilitados hasta finalizar.`));
    if (state.actionOutcome.phase === 'block') section.append(renderUiStateNotice('block', 'La última acción fue bloqueada y no se presenta como éxito.'));
    if (approvalItems(state).some((approval) => approval.status === 'requested')) section.append(renderUiStateNotice('pending', 'Existe al menos un approval requested con acciones Approve/Deny disponibles.'));
    if (state.errors.approvals || state.errors.selected || state.errors.requestResult || state.errors.actionResult || state.errors.portfolio || state.errors.capabilities) section.append(renderUiStateNotice('error', 'Approval Center mantiene BLOCK/ERROR visibles.'));
    section.append(renderApprovalDetailPanel(state.selected, state.errors.selected));
    section.append(renderDetailPanel('Última solicitud approval', state.requestResult, state.errors.requestResult));
  }

  draw();
  if (tokenProvider()) void refresh();
  return section;
}

function renderApprovalAuthorityPanel(response: DevPilotApplicationResponse | undefined, error: string | undefined): HTMLElement {
  const panel = document.createElement('section');
  panel.className = 'viewer-card approval-authority-panel';
  const title = document.createElement('h3');
  title.textContent = 'Autoridad autenticada';
  panel.append(title);
  if (error) {
    panel.append(renderUiStateNotice('block', 'Sesión humana/capability view no disponible. Crear o decidir approvals permanece bloqueado hasta autenticarse; Login UI llega en GSDLC-02-E.'));
    return panel;
  }
  const data = (response?.data ?? {}) as Record<string, unknown>;
  const identity = (data.identity ?? {}) as Record<string, unknown>;
  const roles = Array.isArray(data.effective_roles) ? data.effective_roles.map(String) : [];
  const p = document.createElement('p');
  p.textContent = response
    ? `Principal: ${String(identity.display_name ?? identity.actor_id ?? 'authenticated')} · Roles: ${roles.join(', ') || 'sin rol'} · El servidor es la autoridad.`
    : 'Se requiere sesión humana para solicitar o decidir approvals. El token local no es autoridad humana.';
  panel.append(p);
  return panel;
}

function renderApprovalRequestForm(state: ApprovalState, onRequest: () => Promise<void>): HTMLElement {
  const panel = document.createElement('section');
  panel.className = 'viewer-card approval-request-form';
  panel.innerHTML = `
    <h3>Solicitar approval gobernado</h3>
    <p>Registra una solicitud ligada al principal autenticado. El caller no elige actor; el servidor deriva identidad, roles y autoridad de la sesión.</p>
    <div class="grid two-cols">
      <label>Tool id<input id="approval-tool-id" value="docs.review" /></label>
      <label>Action<input id="approval-action" value="approve" /></label>
      <label>Subject<input id="approval-subject" placeholder="docs/00_product/product_vision.md" /></label>
      <label>Scope<input id="approval-scope" placeholder="workspace:inventory-sales-local" /></label>
      <label>TTL minutos<input id="approval-ttl" type="number" min="1" max="1440" value="120" /></label>
    </div>
    <label>Reason<input id="approval-reason" placeholder="Aprobar artefacto después de revisión humana y validaciones." /></label>
  `;
  const button = actionButton('Crear approval gobernado', state.pendingAction === 'request' ? 'Creando…' : 'Crear approval solicitado', state.pendingAction, () => void onRequest());
  panel.append(button);
  if (state.errors.requestResult) panel.append(renderUiStateNotice('error', state.errors.requestResult));
  return panel;
}

function actionButton(label: string, text: string, pendingAction: string | undefined, onClick: () => void): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.setAttribute('aria-label', label);
  button.setAttribute('aria-busy', String(Boolean(pendingAction)));
  button.disabled = Boolean(pendingAction);
  button.textContent = text;
  button.addEventListener('click', onClick);
  return button;
}

function renderApprovalsPanel(state: ApprovalState, onSelect: (approvalId: string) => Promise<void>, onDecide: (approvalId: string, decision: 'approve' | 'deny') => Promise<void>): HTMLElement {
  const panel = panelShell('Approval Center', state.errors.approvals ?? state.approvals?.message ?? 'Pendiente de consulta.');
  if (!state.approvals && !state.errors.approvals) {
    panel.append(renderUiStateNotice('pending', 'Consulta inicial pendiente. Este estado no acredita una lista vacía.'));
    panel.append(emptyPre('Pendiente de consultar approvals.'));
    return panel;
  }
  const approvals = approvalItems(state);
  if (!approvals.length) {
    panel.append(renderUiStateNotice('empty', 'Sin approvals para mostrar. Usa el formulario gobernado para registrar una solicitud real.'));
    return panel;
  }
  const list = document.createElement('div');
  list.className = 'viewer-list';
  for (const approval of approvals.slice(0, 50)) {
    const row = document.createElement('div');
    row.className = 'approval-row';
    const showKey = `show:${approval.approval_id}`;
    const button = actionButton('Mostrar approval', state.pendingAction === showKey ? 'Ejecutando…' : `${approval.status.toUpperCase()} · ${approval.tool_id}/${approval.action} · ${approval.subject}`, state.pendingAction, () => void onSelect(approval.approval_id));
    button.className = 'viewer-list__item';
    row.append(button);
    if (approval.status === 'requested') {
      const approveKey = `approve:${approval.approval_id}`;
      const approve = actionButton('Approve', state.pendingAction === approveKey ? 'Ejecutando…' : 'Approve', state.pendingAction, () => void onDecide(approval.approval_id, 'approve'));
      const denyKey = `deny:${approval.approval_id}`;
      const deny = actionButton('Deny', state.pendingAction === denyKey ? 'Ejecutando…' : 'Deny', state.pendingAction, () => void onDecide(approval.approval_id, 'deny'));
      deny.className = 'button-secondary';
      row.append(approve, deny);
    }
    list.append(row);
  }
  panel.append(list);
  return panel;
}

function approvalItems(state: ApprovalState): ApprovalRecordItem[] {
  return ((state.approvals?.data as { approvals?: ApprovalRecordItem[] } | undefined)?.approvals ?? []);
}

function renderActionPanel(state: ApprovalState, tokenProvider: () => string, redraw: () => void): HTMLElement {
  const panel = panelShell('Action Launcher dry-run', state.errors.actionResult ?? state.actionResult?.message ?? 'Solo acciones read-only/dry-run.');
  panel.dataset.phase = state.actionOutcome.phase;
  panel.append(renderDryRunActionForm(tokenProvider, (outcome) => {
    state.actionOutcome = outcome;
    state.actionResult = outcome.response;
    if (outcome.error) state.errors.actionResult = outcome.error;
    else delete state.errors.actionResult;
    redraw();
  }, state.actionOutcome));
  const detail = state.actionResult?.data?.action_launcher;
  panel.append(emptyPre(JSON.stringify(detail ?? { detail: 'No existe respuesta de dry-run para esta sesión.' }, null, 2)));
  if (state.actionResult?.findings?.length) panel.append(renderFindingTable(state.actionResult.findings));
  return panel;
}

function renderApprovalDetailPanel(response?: DevPilotApplicationResponse, error?: string): HTMLElement {
  const panel = panelShell('Approval seleccionado', error ?? response?.message ?? 'Selecciona un approval para ver el detalle.');
  const approval = (response?.data as { approval?: ApprovalRecordItem } | undefined)?.approval;
  if (!approval) {
    panel.append(emptyPre(JSON.stringify({ detail: 'Sin detalle seleccionado.' }, null, 2)));
    return panel;
  }
  const badge = document.createElement('span');
  badge.className = 'badge pass';
  badge.textContent = 'DETAIL LOADED';
  badge.dataset.approvalId = approval.approval_id;
  const list = document.createElement('dl');
  list.className = 'approval-detail';
  for (const [label, value] of [
    ['approval_id', approval.approval_id], ['status', approval.status], ['tool_id', approval.tool_id], ['action', approval.action],
    ['subject', approval.subject], ['actor', approval.actor ?? ''], ['created_at', approval.created_at ?? ''], ['expires_at', approval.expires_at ?? ''],
  ]) {
    const term = document.createElement('dt');
    term.textContent = label;
    const description = document.createElement('dd');
    description.textContent = value;
    list.append(term, description);
  }
  panel.append(badge, list, emptyPre(JSON.stringify(response?.data ?? {}, null, 2)));
  if (response?.findings?.length) panel.append(renderFindingTable(response.findings));
  return panel;
}

function renderDetailPanel(title: string, response?: DevPilotApplicationResponse, error?: string): HTMLElement {
  const panel = panelShell(title, error ?? response?.message ?? 'Sin solicitud en esta sesión.');
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

// Operator-flow compatibility marker: approval pending remains visible until an explicit approve/deny decision.
