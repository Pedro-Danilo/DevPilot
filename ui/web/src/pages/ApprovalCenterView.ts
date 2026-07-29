import { DevPilotApiClient } from '../api/client';
import type { ApprovalRecordItem, DevPilotApplicationResponse } from '../api/types';
import { idleOutcome, renderDryRunActionForm } from '../components/DryRunActionForm';
import type { DryRunUiOutcome } from '../components/DryRunActionForm';
import { renderFindingTable } from '../components/FindingTable';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';

interface ApprovalState {
  approvals?: DevPilotApplicationResponse;
  selected?: DevPilotApplicationResponse;
  actionResult?: DevPilotApplicationResponse;
  requestResult?: DevPilotApplicationResponse;
  errors: Record<string, string>;
  statusFilter: string;
  pendingAction?: string;
  actionOutcome: DryRunUiOutcome;
}

export function renderApprovalCenterView(tokenProvider: () => string): HTMLElement {
  const section = document.createElement('section');
  section.className = 'approval-panel';
  const state: ApprovalState = { errors: {}, statusFilter: '', actionOutcome: idleOutcome() };

  async function loadApprovals(): Promise<void> {
    const client = new DevPilotApiClient({ token: tokenProvider() });
    state.approvals = await client.listApprovals({ status: state.statusFilter || undefined, limit: 100 });
    delete state.errors.approvals;
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
    await runPending('refresh', loadApprovals, 'approvals');
  }

  async function selectApproval(approvalId: string): Promise<void> {
    await runPending(`show:${approvalId}`, async () => {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      state.selected = await client.showApproval(approvalId);
    }, 'selected');
  }

  async function decide(approvalId: string, decision: 'approve' | 'deny'): Promise<void> {
    await runPending(`${decision}:${approvalId}`, async () => {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      state.selected = await client.decideApproval(approvalId, decision, { actor: 'local-owner', reason: `${decision} from Approval Center` });
      await loadApprovals();
    }, 'selected');
  }

  async function requestSampleApproval(): Promise<void> {
    await runPending('request', async () => {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      state.requestResult = await client.requestApproval({
        tool_id: 'tests.run',
        action: 'execute',
        subject: 'pytest',
        actor: 'local-owner',
        reason: 'Sample approval request generated from POST-H-028-D Approval Center operator flow.',
        ttl_minutes: 60,
      });
      const created = (state.requestResult.data as { approval?: ApprovalRecordItem }).approval;
      if (created?.approval_id) {
        state.selected = await client.showApproval(created.approval_id);
      }
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
    subtitle.textContent = 'POST-H-028-D · ui.approvals · approvals locales · action launcher dry-run · no-remote · approval pending/approved/denied · BLOCK/ERROR visibles.';
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
    const requestButton = actionButton('Crear approval demo', state.pendingAction === 'request' ? 'Ejecutando…' : 'Crear approval demo', state.pendingAction, () => void requestSampleApproval());
    controls.append(filterLabel, refreshButton, requestButton);
    header.append(titleBlock, controls);
    section.append(header);

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
    if (state.pendingAction) section.append(renderUiStateNotice('loading', `POST-H-028-D ui.approvals loading state: acción en curso ${state.pendingAction}. Los controles permanecen deshabilitados hasta finalizar.`));
    if (state.actionOutcome.phase === 'block') section.append(renderUiStateNotice('block', 'POST-H-028-D ui.approvals block state: la última acción fue bloqueada y no se presenta como éxito.'));
    if (approvalItems(state).some((approval) => approval.status === 'requested')) section.append(renderUiStateNotice('pending', 'POST-H-028-D ui.approvals pending state: existe al menos un approval requested con acciones Approve/Deny disponibles.'));
    if (state.errors.approvals || state.errors.selected || state.errors.requestResult || state.errors.actionResult) section.append(renderUiStateNotice('error', 'POST-H-014-C ui.approvals error state: BLOCK/ERROR se mantiene visible.'));
    section.append(renderApprovalDetailPanel(state.selected, state.errors.selected));
    section.append(renderDetailPanel('Última solicitud approval', state.requestResult, state.errors.requestResult));
  }

  draw();
  if (tokenProvider()) void refresh();
  return section;
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
    panel.append(renderUiStateNotice('empty', 'POST-H-014-C ui.approvals empty state: Sin approvals para mostrar.'));
    panel.append(emptyPre('Sin approvals para mostrar. Puedes crear un approval demo.'));
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
  const panel = panelShell('Action Launcher dry-run — POST-H-014-C ui.approvals', state.errors.actionResult ?? state.actionResult?.message ?? 'Solo acciones read-only/dry-run.');
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
    ['approval_id', approval.approval_id],
    ['status', approval.status],
    ['tool_id', approval.tool_id],
    ['action', approval.action],
    ['subject', approval.subject],
    ['actor', approval.actor ?? ''],
    ['created_at', approval.created_at ?? ''],
    ['expires_at', approval.expires_at ?? ''],
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
  const panel = panelShell(title, error ?? response?.message ?? 'Selecciona un approval para ver el detalle.');
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
