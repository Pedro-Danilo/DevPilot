import { DevPilotApiClient } from '../api/client';
import type { ApprovalRecordItem, DevPilotApplicationResponse } from '../api/types';
import { renderDryRunActionForm } from '../components/DryRunActionForm';
import { renderFindingTable } from '../components/FindingTable';

interface ApprovalState {
  approvals?: DevPilotApplicationResponse;
  selected?: DevPilotApplicationResponse;
  actionResult?: DevPilotApplicationResponse;
  requestResult?: DevPilotApplicationResponse;
  errors: Record<string, string>;
  statusFilter: string;
}

export function renderApprovalCenterView(tokenProvider: () => string): HTMLElement {
  const section = document.createElement('section');
  section.className = 'approval-panel';
  const state: ApprovalState = { errors: {}, statusFilter: '' };

  async function refresh(): Promise<void> {
    state.errors = {};
    try {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      state.approvals = await client.listApprovals({ status: state.statusFilter || undefined, limit: 100 });
    } catch (error) {
      state.errors.approvals = error instanceof Error ? error.message : String(error);
    }
    draw();
  }

  async function selectApproval(approvalId: string): Promise<void> {
    try {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      state.selected = await client.showApproval(approvalId);
      delete state.errors.selected;
    } catch (error) {
      state.errors.selected = error instanceof Error ? error.message : String(error);
    }
    draw();
  }

  async function decide(approvalId: string, decision: 'approve' | 'deny'): Promise<void> {
    try {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      state.selected = await client.decideApproval(approvalId, decision, { actor: 'ui-local', reason: `${decision} from Approval Center` });
      await refresh();
    } catch (error) {
      state.errors.selected = error instanceof Error ? error.message : String(error);
      draw();
    }
  }

  async function requestSampleApproval(): Promise<void> {
    try {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      state.requestResult = await client.requestApproval({
        tool_id: 'tests.run',
        action: 'execute',
        subject: 'pytest',
        actor: 'ui-local',
        reason: 'Sample approval request generated from Sprint 71 Approval Center.',
        ttl_minutes: 60,
      });
      await refresh();
    } catch (error) {
      state.errors.requestResult = error instanceof Error ? error.message : String(error);
      draw();
    }
  }

  function draw(): void {
    section.replaceChildren();
    const header = document.createElement('div');
    header.className = 'viewer-panel__header';
    const titleBlock = document.createElement('div');
    const title = document.createElement('h2');
    title.textContent = 'Approval Center y Action Launcher';
    const subtitle = document.createElement('p');
    subtitle.textContent = 'Sprint 71 MVP · approvals locales · acciones dry-run seguras · ejecución crítica bloqueada.';
    titleBlock.append(title, subtitle);

    const controls = document.createElement('div');
    controls.className = 'viewer-controls';
    const filterLabel = document.createElement('label');
    filterLabel.textContent = 'Filtrar estado';
    const filter = document.createElement('select');
    for (const [value, label] of [['', 'Todos'], ['requested', 'Requested'], ['approved', 'Approved'], ['denied', 'Denied'], ['revoked', 'Revoked'], ['expired', 'Expired']]) {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = label;
      option.selected = state.statusFilter === value;
      filter.append(option);
    }
    filter.addEventListener('change', () => { state.statusFilter = filter.value; void refresh(); });
    filterLabel.append(filter);
    const refreshButton = document.createElement('button');
    refreshButton.type = 'button';
    refreshButton.textContent = 'Actualizar approvals';
    refreshButton.addEventListener('click', () => { void refresh(); });
    const requestButton = document.createElement('button');
    requestButton.type = 'button';
    requestButton.textContent = 'Crear approval demo';
    requestButton.addEventListener('click', () => { void requestSampleApproval(); });
    controls.append(filterLabel, refreshButton, requestButton);
    header.append(titleBlock, controls);
    section.append(header);

    const grid = document.createElement('div');
    grid.className = 'viewer-grid';
    grid.append(renderApprovalsPanel(state, selectApproval, decide));
    grid.append(renderActionPanel(state, tokenProvider));
    section.append(grid);
    section.append(renderDetailPanel('Approval seleccionado', state.selected, state.errors.selected));
    section.append(renderDetailPanel('Última solicitud approval', state.requestResult, state.errors.requestResult));
  }

  draw();
  if (tokenProvider()) void refresh();
  return section;
}

function renderApprovalsPanel(state: ApprovalState, onSelect: (approvalId: string) => Promise<void>, onDecide: (approvalId: string, decision: 'approve' | 'deny') => Promise<void>): HTMLElement {
  const panel = panelShell('Approval Center', state.errors.approvals ?? state.approvals?.message ?? 'Pendiente de consulta.');
  const approvals = ((state.approvals?.data as { approvals?: ApprovalRecordItem[] } | undefined)?.approvals ?? []);
  if (!approvals.length) {
    panel.append(emptyPre('Sin approvals para mostrar. Puedes crear un approval demo.'));
    return panel;
  }
  const list = document.createElement('div');
  list.className = 'viewer-list';
  for (const approval of approvals.slice(0, 50)) {
    const row = document.createElement('div');
    row.className = 'approval-row';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'viewer-list__item';
    button.textContent = `${approval.status.toUpperCase()} · ${approval.tool_id}/${approval.action} · ${approval.subject}`;
    button.addEventListener('click', () => { void onSelect(approval.approval_id); });
    row.append(button);
    if (approval.status === 'requested') {
      const approve = document.createElement('button');
      approve.type = 'button';
      approve.textContent = 'Approve';
      approve.addEventListener('click', () => { void onDecide(approval.approval_id, 'approve'); });
      const deny = document.createElement('button');
      deny.type = 'button';
      deny.className = 'button-secondary';
      deny.textContent = 'Deny';
      deny.addEventListener('click', () => { void onDecide(approval.approval_id, 'deny'); });
      row.append(approve, deny);
    }
    list.append(row);
  }
  panel.append(list);
  return panel;
}

function renderActionPanel(state: ApprovalState, tokenProvider: () => string): HTMLElement {
  const panel = panelShell('Action Launcher dry-run', state.errors.actionResult ?? state.actionResult?.message ?? 'Solo acciones read-only/dry-run.');
  panel.append(renderDryRunActionForm(tokenProvider, (response, error) => {
    state.actionResult = response;
    if (error) state.errors.actionResult = error;
    else delete state.errors.actionResult;
    const current = panel.parentElement?.parentElement;
    if (current) current.dispatchEvent(new Event('devpilot-redraw'));
  }));
  panel.append(emptyPre(JSON.stringify(state.actionResult?.data?.action_launcher ?? { dry_run: true, critical_actions_blocked: true }, null, 2)));
  if (state.actionResult?.findings?.length) panel.append(renderFindingTable(state.actionResult.findings));
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
