// DevPilot UI route contract: ui.workspace-documents
import { DevPilotApiClient } from '../api/client';
import type {
  ApprovalRecordItem,
  WorkspaceDocumentResource,
  WorkspaceGitBranchPlan,
  WorkspaceGitCommitExecution,
  WorkspaceGitCommitPlan,
  WorkspaceGitStageExecution,
} from '../api/types';
import { escapeHtml } from '../utils/sanitize';
import { renderUiStateNotice } from './ContractBadges';

const ACTOR = 'owner';

export interface WorkspaceGitOperationsPanelOptions {
  tokenProvider: () => string;
  onCommitComplete?: () => Promise<void> | void;
}

interface ApprovalState extends ApprovalRecordItem {
  expires_at?: string;
}

export function createWorkspaceGitOperationsPanel(options: WorkspaceGitOperationsPanelOptions): HTMLElement {
  const root = document.createElement('section');
  root.className = 'panel uoc006-git-panel';
  root.dataset.uoc006GitOperations = 'true';
  let currentDocument: WorkspaceDocumentResource | undefined;
  let busy = false;
  let error = '';
  let status = '';
  let gitStatus: Record<string, unknown> | undefined;
  let gitHistory: Record<string, unknown> | undefined;
  let gitCompare: Record<string, unknown> | undefined;
  let plan: WorkspaceGitCommitPlan | undefined;
  let stageApproval: ApprovalState | undefined;
  let stageExecution: WorkspaceGitStageExecution | undefined;
  let commitApproval: ApprovalState | undefined;
  let commitExecution: WorkspaceGitCommitExecution | undefined;
  let branchPlan: WorkspaceGitBranchPlan | undefined;
  let branchApproval: ApprovalState | undefined;
  let branchResult: Record<string, unknown> | undefined;
  let commitMessage = 'docs: commit reviewed document change';
  let authorName = 'DevPilot Owner';
  let authorEmail = 'devpilot-owner@local.invalid';
  let branchName = 'feat/uoc006-review';

  const client = (): DevPilotApiClient => new DevPilotApiClient({ token: options.tokenProvider() });

  function setDocument(document?: WorkspaceDocumentResource): void {
    const transientCommitReload = Boolean(!document && currentDocument && commitExecution);
    if (transientCommitReload) {
      status = 'COMMIT PASS · estado preservado mientras se recarga el documento después del commit.';
      draw();
      return;
    }
    const before = currentDocument?.document_id;
    currentDocument = document;
    if (before && document && before !== document.document_id) resetMutationState();
    draw();
  }

  function resetMutationState(): void {
    plan = undefined;
    stageApproval = undefined;
    stageExecution = undefined;
    commitApproval = undefined;
    commitExecution = undefined;
    status = '';
    error = '';
  }

  async function refreshStatus(): Promise<void> {
    busy = true; error = ''; status = 'Actualizando status, history y compare gobernados…'; draw();
    try {
      const compareBase = commitExecution?.parent ?? 'HEAD';
      const compareHead = commitExecution?.commit ?? 'HEAD';
      const [statusResponse, historyResponse, compareResponse] = await Promise.all([
        client().workspaceGitStatus(),
        client().workspaceGitHistory(10),
        client().workspaceGitCompare(compareBase, compareHead),
      ]);
      if (!statusResponse.ok) throw new Error(statusResponse.message || 'Git status blocked.');
      if (!historyResponse.ok) throw new Error(historyResponse.message || 'Git history blocked.');
      if (!compareResponse.ok) throw new Error(compareResponse.message || 'Git compare blocked.');
      gitStatus = statusResponse.data as Record<string, unknown>;
      gitHistory = historyResponse.data as Record<string, unknown>;
      gitCompare = compareResponse.data as Record<string, unknown>;
      status = 'GIT READ PASS · status/history/compare tipados; no se ejecutó ninguna mutación.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function createPlan(): Promise<void> {
    if (!currentDocument) return;
    busy = true; error = ''; status = 'Generando plan Git inmutable…'; draw();
    try {
      const response = await client().planWorkspaceGitCommit({
        document_ids: [currentDocument.document_id],
        commit_message: commitMessage,
        author_name: authorName,
        author_email: authorEmail,
      });
      const next = (response.data as { plan?: WorkspaceGitCommitPlan }).plan;
      if (!response.ok || !next) throw new Error(response.message || 'Git plan blocked.');
      plan = next; stageApproval = undefined; stageExecution = undefined; commitApproval = undefined; commitExecution = undefined;
      status = 'PLAN PASS · índice e historial siguen sin mutación.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function requestStageApproval(): Promise<void> {
    if (!plan) return;
    busy = true; error = ''; status = 'Solicitando aprobación exacta para staging…'; draw();
    try {
      const response = await client().requestWorkspaceGitStageApproval(plan.plan_id, { plan_hash: plan.plan_hash, actor: ACTOR, reason: 'Stage exact reviewed UOC-006 plan', ttl_minutes: 15 });
      const approval = (response.data as { approval?: ApprovalState }).approval;
      if (!response.ok || !approval) throw new Error(response.message || 'Stage approval request blocked.');
      stageApproval = approval; status = 'STAGE APPROVAL REQUESTED · todavía no se modificó el índice Git.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function decide(approval: ApprovalState, decision: 'approve' | 'deny', target: 'stage' | 'commit' | 'branch'): Promise<void> {
    busy = true; error = ''; status = `${decision === 'approve' ? 'Aprobando' : 'Denegando'} ${target}…`; draw();
    try {
      const response = await client().decideApproval(approval.approval_id, decision, { actor: ACTOR, reason: `${decision === 'approve' ? 'Approved' : 'Denied'} UOC-006 ${target}` });
      const next = (response.data as { approval?: ApprovalState }).approval;
      if (!response.ok || !next) throw new Error(response.message || 'Approval decision blocked.');
      if (target === 'stage') stageApproval = next;
      if (target === 'commit') commitApproval = next;
      if (target === 'branch') branchApproval = next;
      status = `${target.toUpperCase()} APPROVAL ${String(next.status).toUpperCase()}`;
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function stageExact(): Promise<void> {
    if (!plan || !stageApproval || stageApproval.status !== 'approved') return;
    busy = true; error = ''; status = 'Revalidando HEAD, hashes, aprobación y secretos antes de staging…'; draw();
    try {
      const response = await client().stageWorkspaceGitPlan(plan.plan_id, { plan_hash: plan.plan_hash, approval_id: stageApproval.approval_id, actor: ACTOR });
      const next = (response.data as { stage_execution?: WorkspaceGitStageExecution }).stage_execution;
      if (!response.ok || !next) throw new Error(response.message || 'Stage blocked.');
      stageExecution = next; status = 'STAGE PASS · índice exacto verificado; historial aún sin commit.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function requestCommitApproval(): Promise<void> {
    if (!stageExecution) return;
    busy = true; error = ''; status = 'Solicitando segunda aprobación para commit…'; draw();
    try {
      const response = await client().requestWorkspaceGitCommitApproval(stageExecution.stage_execution_id, { actor: ACTOR, reason: 'Commit exact staged UOC-006 index', ttl_minutes: 15 });
      const approval = (response.data as { approval?: ApprovalState }).approval;
      if (!response.ok || !approval) throw new Error(response.message || 'Commit approval request blocked.');
      commitApproval = approval; status = 'COMMIT APPROVAL REQUESTED · todavía no existe nuevo commit.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function commitExact(): Promise<void> {
    if (!stageExecution || !commitApproval || commitApproval.status !== 'approved') return;
    busy = true; error = ''; status = 'Verificando fingerprint del índice y creando commit local…'; draw();
    try {
      const response = await client().commitWorkspaceGitExecution(stageExecution.stage_execution_id, { approval_id: commitApproval.approval_id, actor: ACTOR });
      const next = (response.data as { execution?: WorkspaceGitCommitExecution }).execution;
      if (!response.ok || !next) throw new Error(response.message || 'Commit blocked.');
      commitExecution = next; status = 'COMMIT PASS · parent, paths e índice post-commit verificados; push NO ejecutado.';
      await options.onCommitComplete?.();
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function createBranchPlan(): Promise<void> {
    busy = true; error = ''; status = 'Generando plan local de branch ref…'; draw();
    try {
      const response = await client().planWorkspaceGitBranch(branchName);
      const next = (response.data as { plan?: WorkspaceGitBranchPlan }).plan;
      if (!response.ok || !next) throw new Error(response.message || 'Branch plan blocked.');
      branchPlan = next; branchApproval = undefined; branchResult = undefined; status = 'BRANCH PLAN PASS · no checkout y ninguna ref creada todavía.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function requestBranchApproval(): Promise<void> {
    if (!branchPlan) return;
    busy = true; error = ''; status = 'Solicitando aprobación de branch local…'; draw();
    try {
      const response = await client().requestWorkspaceGitBranchApproval(branchPlan.plan_id, { plan_hash: branchPlan.plan_hash, actor: ACTOR, reason: 'Create controlled local UOC-006 branch ref', ttl_minutes: 15 });
      const approval = (response.data as { approval?: ApprovalState }).approval;
      if (!response.ok || !approval) throw new Error(response.message || 'Branch approval request blocked.');
      branchApproval = approval; status = 'BRANCH APPROVAL REQUESTED';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function createBranch(): Promise<void> {
    if (!branchPlan || !branchApproval || branchApproval.status !== 'approved') return;
    busy = true; error = ''; status = 'Creando únicamente la ref local aprobada…'; draw();
    try {
      const response = await client().createWorkspaceGitBranch(branchPlan.plan_id, { plan_hash: branchPlan.plan_hash, approval_id: branchApproval.approval_id, actor: ACTOR });
      if (!response.ok) throw new Error(response.message || 'Branch creation blocked.');
      branchResult = response.data as Record<string, unknown>; status = 'BRANCH CREATE PASS · ref local creada; checkout/push/delete no ejecutados.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  function input(labelText: string, value: string, onInput: (value: string) => void, type = 'text'): HTMLElement {
    const label = document.createElement('label'); label.className = 'uoc006-field';
    const span = document.createElement('span'); span.textContent = labelText;
    const field = document.createElement('input'); field.type = type; field.value = value; field.disabled = busy || Boolean(stageExecution); field.addEventListener('input', () => onInput(field.value));
    label.append(span, field); return label;
  }

  function button(label: string, fn: () => void, secondary = false): HTMLButtonElement {
    const b = document.createElement('button'); b.type = 'button'; b.className = secondary ? 'button-secondary' : 'validation-action-button'; b.textContent = label; b.addEventListener('click', fn); return b;
  }

  function approvalCard(title: string, approval: ApprovalState, target: 'stage' | 'commit' | 'branch'): HTMLElement {
    const card = document.createElement('section'); card.className = 'uoc006-approval-card';
    card.innerHTML = `<h4>${escapeHtml(title)}</h4><dl><dt>ID</dt><dd><code>${escapeHtml(approval.approval_id)}</code></dd><dt>Estado</dt><dd><strong>${escapeHtml(approval.status)}</strong></dd><dt>Expira</dt><dd>${escapeHtml(approval.expires_at ?? '')}</dd></dl>`;
    if (approval.status === 'requested') {
      const actions = document.createElement('div'); actions.className = 'uoc006-actions';
      const approve = button('Aprobar', () => void decide(approval, 'approve', target));
      const deny = button('Denegar', () => void decide(approval, 'deny', target), true);
      approve.disabled = busy; deny.disabled = busy; actions.append(approve, deny); card.append(actions);
    }
    return card;
  }

  function draw(): void {
    root.replaceChildren();
    const head = document.createElement('div'); head.className = 'uoc006-heading';
    head.innerHTML = '<div><h2>Operaciones Git gobernadas</h2><p>UOC-006 · versión inicial local-first: plan → aprobación de stage → stage exacto → aprobación de commit → commit verificado.</p></div><div class="uoc006-badges"><span>IMPLEMENTED-INITIAL</span><span>NO SHELL</span><span>NO PUSH</span><span>NO FORCE</span><span>APPROVAL ×2</span></div>';
    root.append(head);
    const noGo = document.createElement('div'); noGo.className = 'uoc006-no-go'; noGo.textContent = 'NO-GO: reset --hard, rebase interactivo, force push, branch delete, checkout/switch libre, hooks, tags y argumentos Git libres permanecen bloqueados.'; root.append(noGo);
    const refresh = button(busy ? 'Actualizando…' : 'Actualizar status, history y compare', () => void refreshStatus(), true); refresh.disabled = busy; root.append(refresh);
    if (gitStatus || gitHistory || gitCompare) {
      const readCard = document.createElement('section'); readCard.className = 'uoc006-read-card';
      readCard.innerHTML = '<h3>Lecturas Git tipadas</h3><p>Status, history y compare están limitados por el adapter; no aceptan argumentos Git libres.</p>';
      if (gitStatus) { const pre = document.createElement('pre'); pre.className = 'uoc006-status-json'; pre.textContent = `STATUS\n${JSON.stringify((gitStatus as { summary?: unknown }).summary ?? gitStatus, null, 2)}`; readCard.append(pre); }
      if (gitHistory) { const pre = document.createElement('pre'); pre.className = 'uoc006-history-json'; pre.textContent = `HISTORY\n${JSON.stringify(gitHistory, null, 2)}`; readCard.append(pre); }
      if (gitCompare) { const pre = document.createElement('pre'); pre.className = 'uoc006-compare-json'; pre.textContent = `COMPARE\n${JSON.stringify(gitCompare, null, 2)}`; readCard.append(pre); }
      root.append(readCard);
    }
    if (status) root.append(renderUiStateNotice('success', status));
    if (error) root.append(renderUiStateNotice(error.includes('BLOCK') ? 'block' : 'error', error));
    if (!currentDocument) { root.append(renderUiStateNotice('empty', 'Seleccione un documento cambiado para preparar un commit gobernado.')); return; }

    const selected = document.createElement('div'); selected.className = 'uoc006-selected'; selected.innerHTML = `<strong>Documento seleccionado</strong><code>${escapeHtml(currentDocument.relative_path)}</code><code>${escapeHtml(String(currentDocument.sha256 ?? ''))}</code>`; root.append(selected);
    const fields = document.createElement('div'); fields.className = 'uoc006-form-grid';
    fields.append(
      input('Mensaje de commit', commitMessage, value => { commitMessage = value; plan = undefined; }),
      input('Autor', authorName, value => { authorName = value; plan = undefined; }),
      input('Email', authorEmail, value => { authorEmail = value; plan = undefined; }, 'email'),
    ); root.append(fields);
    const planButton = button('Planificar staging y commit', () => void createPlan()); planButton.disabled = busy || Boolean(stageExecution); root.append(planButton);
    if (plan) {
      const planCard = document.createElement('section'); planCard.className = 'uoc006-plan-card';
      planCard.innerHTML = `<h3>Plan Git inmutable</h3><dl><dt>Plan ID</dt><dd><code>${escapeHtml(plan.plan_id)}</code></dd><dt>Plan hash</dt><dd><code>${escapeHtml(plan.plan_hash)}</code></dd><dt>HEAD</dt><dd><code>${escapeHtml(plan.head_before)}</code></dd><dt>Branch</dt><dd>${escapeHtml(plan.branch)}</dd><dt>Documento</dt><dd>${escapeHtml(plan.files[0]?.relative_path ?? '')}</dd><dt>Diff SHA</dt><dd><code>${escapeHtml(plan.combined_diff_sha256)}</code></dd></dl>`;
      const diff = document.createElement('pre'); diff.textContent = plan.combined_diff; planCard.append(diff); root.append(planCard);
      if (!stageApproval) { const b = button('Solicitar aprobación de staging', () => void requestStageApproval()); b.disabled = busy; root.append(b); }
    }
    if (stageApproval) root.append(approvalCard('Aprobación de staging', stageApproval, 'stage'));
    if (plan && stageApproval?.status === 'approved' && !stageExecution) { const b = button('Aplicar staging aprobado', () => void stageExact()); b.disabled = busy; root.append(b); }
    if (stageExecution) {
      const card = document.createElement('section'); card.className = 'uoc006-execution-card'; card.innerHTML = `<h3>STAGE PASS</h3><dl><dt>Execution ID</dt><dd><code>${escapeHtml(stageExecution.stage_execution_id)}</code></dd><dt>Index fingerprint</dt><dd><code>${escapeHtml(stageExecution.index_fingerprint)}</code></dd><dt>Commit intent hash</dt><dd><code>${escapeHtml(stageExecution.commit_intent_hash)}</code></dd><dt>Push</dt><dd>${String(stageExecution.push_performed)}</dd></dl>`; root.append(card);
      if (!commitApproval && !commitExecution) { const b = button('Solicitar aprobación de commit', () => void requestCommitApproval()); b.disabled = busy; root.append(b); }
    }
    if (commitApproval) root.append(approvalCard('Aprobación de commit', commitApproval, 'commit'));
    if (stageExecution && commitApproval?.status === 'approved' && !commitExecution) { const b = button('Crear commit aprobado', () => void commitExact()); b.disabled = busy; root.append(b); }
    if (commitExecution) {
      const card = document.createElement('section'); card.className = 'uoc006-execution-card uoc006-commit-pass'; card.innerHTML = `<h3>COMMIT PASS</h3><dl><dt>Commit</dt><dd><code>${escapeHtml(commitExecution.commit)}</code></dd><dt>Parent</dt><dd><code>${escapeHtml(commitExecution.parent)}</code></dd><dt>Paths</dt><dd>${commitExecution.committed_paths.map(escapeHtml).join(', ')}</dd><dt>Hooks ejecutados</dt><dd>${String(commitExecution.hooks_executed)}</dd><dt>Push ejecutado</dt><dd>${String(commitExecution.push_performed)}</dd></dl>`; root.append(card);
    }

    const branch = document.createElement('section'); branch.className = 'uoc006-branch-panel'; const title = document.createElement('h3'); title.textContent = 'Branch local controlado'; branch.append(title);
    const branchField = input('Nombre permitido', branchName, value => { branchName = value; branchPlan = undefined; branchApproval = undefined; branchResult = undefined; }); branch.append(branchField);
    const bp = button('Planificar branch local', () => void createBranchPlan(), true); bp.disabled = busy; branch.append(bp);
    if (branchPlan) { const p = document.createElement('p'); p.innerHTML = `Plan <code>${escapeHtml(branchPlan.plan_id)}</code> · HEAD <code>${escapeHtml(branchPlan.head_before)}</code> · no checkout.`; branch.append(p); if (!branchApproval) branch.append(button('Solicitar aprobación de branch', () => void requestBranchApproval())); }
    if (branchApproval) branch.append(approvalCard('Aprobación de branch', branchApproval, 'branch'));
    if (branchPlan && branchApproval?.status === 'approved' && !branchResult) branch.append(button('Crear branch local aprobado', () => void createBranch()));
    if (branchResult) branch.append(renderUiStateNotice('success', 'BRANCH CREATE PASS · ref local creada sin checkout/push/delete.'));
    root.append(branch);
  }

  draw();
  (root as HTMLElement & { setDocument?: (document?: WorkspaceDocumentResource) => void }).setDocument = setDocument;
  return root;
}
