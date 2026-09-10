// DevPilot UI route contract: ui.workspace-documents
import { DevPilotApiClient } from '../api/client';
import type {
  ApprovalRecordItem,
  WorkspaceDocumentResource,
  WorkspaceGitBranchPlan,
  WorkspaceGitCommitExecution,
  WorkspaceGitCommitPlan,
  WorkspaceGitStageExecution,
  StoryGitCommitReadyContext,
  StoryGitCommitPlan,
  StoryGitStageExecution,
  StoryGitCommitRecord,
} from '../api/types';
import { escapeHtml } from '../utils/sanitize';
import { renderUiStateNotice } from './ContractBadges';

const ACTOR = 'owner';

export interface WorkspaceGitOperationsPanelOptions {
  tokenProvider: () => string;
  onCommitComplete?: () => Promise<void> | void;
  storyMode?: boolean;
}

interface ApprovalState extends ApprovalRecordItem {
  expires_at?: string;
}

export function createWorkspaceGitOperationsPanel(options: WorkspaceGitOperationsPanelOptions): HTMLElement {
  if (options.storyMode) return createStoryGitOperationsPanel(options);
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


function createStoryGitOperationsPanel(options: WorkspaceGitOperationsPanelOptions): HTMLElement {
  const root = document.createElement('section');
  root.className = 'panel uoc006-git-panel story-git-governed-panel';
  root.dataset.gsdlc10d = 'story-git-governed';
  root.dataset.fullRegression = '0';
  let busy = false;
  let notice = 'Recupera el contexto COMMIT_READY validado por el servidor para comenzar.';
  let error = '';
  let context: StoryGitCommitReadyContext | undefined;
  let plan: StoryGitCommitPlan | undefined;
  let stageApproval: ApprovalState | undefined;
  let stageExecution: StoryGitStageExecution | undefined;
  let commitApproval: ApprovalState | undefined;
  let commitRecord: StoryGitCommitRecord | undefined;
  let commitMessage = 'feat: close governed story';
  let authorName = 'DevPilot Owner';
  let authorEmail = 'devpilot-owner@local.invalid';

  const client = (): DevPilotApiClient => new DevPilotApiClient({ token: options.tokenProvider() });
  const approvalFrom = (response: Record<string, unknown>): ApprovalState | undefined => {
    const direct = response.approval as ApprovalState | undefined;
    if (direct?.approval_id) return direct;
    const data = response as { approval_id?: string; status?: string; expires_at?: string };
    return data.approval_id ? data as ApprovalState : undefined;
  };

  async function recover(): Promise<void> {
    busy = true; error = ''; notice = 'Recuperando Quality PASS + COMMIT_READY server-side…'; draw();
    try {
      const response = await client().storyGitContextRecover();
      if (!response.ok) throw new Error(response.message || 'COMMIT_READY context blocked.');
      context = response.data as unknown as StoryGitCommitReadyContext;
      plan = undefined; stageApproval = undefined; stageExecution = undefined; commitApproval = undefined; commitRecord = undefined;
      notice = 'CONTEXT PASS · Quality/TestPlan/SourcePlan recuperados read-only; Git authority=false.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function createPlan(): Promise<void> {
    if (!context) return;
    busy = true; error = ''; notice = 'Construyendo CommitPlan immutable/hash-bound sin mutar Git…'; draw();
    try {
      const response = await client().storyGitCommitPlanCreate({ quality_report_id: context.quality_report_id, quality_report_hash: context.quality_report_hash, commit_message: commitMessage, author_name: authorName, author_email: authorEmail });
      const next = (response.data as { commit_plan?: StoryGitCommitPlan }).commit_plan;
      if (!response.ok || !next) throw new Error(response.message || 'CommitPlan blocked.');
      plan = next; stageApproval = undefined; stageExecution = undefined; commitApproval = undefined; commitRecord = undefined;
      notice = 'PLAN PASS · exact path set bound to story/change-plan/tests/quality; index unchanged.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function requestStageApproval(): Promise<void> {
    if (!plan) return;
    busy = true; error = ''; notice = 'Solicitando approval owner para stage exacto…'; draw();
    try {
      const response = await client().storyGitStageApprovalRequest(plan.commit_plan_id, plan.commit_plan_hash);
      const next = approvalFrom(response.data as Record<string, unknown>);
      if (!response.ok || !next) throw new Error(response.message || 'Stage approval blocked.');
      stageApproval = next; notice = 'STAGE APPROVAL REQUESTED · aún no se modificó el índice.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function decide(approval: ApprovalState, decision: 'approve' | 'deny', kind: 'stage' | 'commit'): Promise<void> {
    busy = true; error = ''; notice = `${decision === 'approve' ? 'Aprobando' : 'Denegando'} ${kind} con sesión humana…`; draw();
    try {
      const response = await client().decideApproval(approval.approval_id, decision, { actor: ACTOR, reason: `${decision === 'approve' ? 'Approved' : 'Denied'} GSDLC-10-D ${kind}` });
      const next = approvalFrom(response.data as Record<string, unknown>);
      if (!response.ok || !next) throw new Error(response.message || 'Approval decision blocked.');
      if (kind === 'stage') stageApproval = next; else commitApproval = next;
      notice = `${kind.toUpperCase()} APPROVAL ${String(next.status).toUpperCase()} · authority=human-session.`;
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function stage(): Promise<void> {
    if (!plan || stageApproval?.status !== 'approved') return;
    busy = true; error = ''; notice = 'Revalidando Quality, dirty set y hashes antes del stage exacto…'; draw();
    try {
      const response = await client().storyGitStage(plan.commit_plan_id, plan.commit_plan_hash, stageApproval.approval_id);
      const next = (response.data as { stage_execution?: StoryGitStageExecution }).stage_execution;
      if (!response.ok || !next) throw new Error(response.message || 'Story stage blocked.');
      stageExecution = next; notice = 'STAGE PASS · índice contiene únicamente el delta aprobado; git add .=false.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function requestCommitApproval(): Promise<void> {
    if (!stageExecution) return;
    busy = true; error = ''; notice = 'Solicitando segundo approval owner para commit…'; draw();
    try {
      const response = await client().storyGitCommitApprovalRequest(stageExecution.stage_execution_id);
      const next = approvalFrom(response.data as Record<string, unknown>);
      if (!response.ok || !next) throw new Error(response.message || 'Commit approval blocked.');
      commitApproval = next; notice = 'COMMIT APPROVAL REQUESTED · sigue sin existir un nuevo commit.';
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  async function commit(): Promise<void> {
    if (!stageExecution || commitApproval?.status !== 'approved') return;
    busy = true; error = ''; notice = 'Revalidando Quality + index fingerprint y ejecutando commit tipado…'; draw();
    try {
      const response = await client().storyGitCommit(stageExecution.stage_execution_id, commitApproval.approval_id);
      const next = (response.data as { git_commit_record?: StoryGitCommitRecord }).git_commit_record;
      if (!response.ok || !next) throw new Error(response.message || 'Story commit blocked.');
      commitRecord = next; notice = 'COMMIT PASS · exact delta + traceability + clean worktree; push=false; Full=0.';
      await options.onCommitComplete?.();
    } catch (cause) { error = cause instanceof Error ? cause.message : String(cause); }
    finally { busy = false; draw(); }
  }

  function btn(label: string, fn: () => void, secondary = false): HTMLButtonElement {
    const b = document.createElement('button'); b.type = 'button'; b.className = secondary ? 'button-secondary' : 'validation-action-button'; b.textContent = label; b.disabled = busy; b.addEventListener('click', fn); return b;
  }
  function field(labelText: string, value: string, setter: (v: string) => void, type = 'text'): HTMLElement {
    const label = document.createElement('label'); label.className = 'uoc006-field'; const span = document.createElement('span'); span.textContent = labelText;
    const input = document.createElement('input'); input.type = type; input.value = value; input.disabled = busy || Boolean(stageExecution); input.addEventListener('input', () => { setter(input.value); plan = undefined; draw(); });
    label.append(span, input); return label;
  }
  function approvalCard(title: string, approval: ApprovalState, kind: 'stage' | 'commit'): HTMLElement {
    const card = document.createElement('section'); card.className = 'uoc006-approval-card'; card.dataset.approvalKind = kind;
    card.innerHTML = `<h4>${escapeHtml(title)}</h4><dl><dt>ID</dt><dd><code>${escapeHtml(approval.approval_id)}</code></dd><dt>Estado</dt><dd><strong>${escapeHtml(approval.status)}</strong></dd><dt>Rol</dt><dd>owner · human-session</dd></dl>`;
    if (approval.status === 'requested') { const actions = document.createElement('div'); actions.className = 'uoc006-actions'; actions.append(btn('Aprobar', () => void decide(approval, 'approve', kind)), btn('Denegar', () => void decide(approval, 'deny', kind), true)); card.append(actions); }
    return card;
  }

  function draw(): void {
    root.replaceChildren();
    const heading = document.createElement('div'); heading.className = 'uoc006-heading'; heading.innerHTML = '<div><h2>Cierre Git gobernado de la story</h2><p>GSDLC-10-D · Quality PASS + COMMIT_READY → plan exacto → RBAC/approval → stage exacto → segundo approval → commit y trazabilidad.</p></div><div class="uoc006-badges"><span>EXACT PATHS</span><span>RBAC ×2</span><span>NO PUSH</span><span>NO FORCE</span><span>NO REBASE</span><span>FULL=0</span></div>';
    root.append(heading);
    const boundary = document.createElement('div'); boundary.className = 'uoc006-no-go'; boundary.dataset.authorityBoundary = 'server-side'; boundary.textContent = 'AUTORIDAD: Quality/COMMIT_READY son precondición; solo policy + RBAC + approval human-session autorizan stage/commit. Agente/modelo puede proponer, nunca conceder permiso Git.'; root.append(boundary);
    if (notice) root.append(renderUiStateNotice(notice.includes('PASS') ? 'success' : 'loading', notice));
    if (error) root.append(renderUiStateNotice(error.includes('BLOCK') ? 'block' : 'error', error));
    const recoverButton = btn('Recuperar contexto COMMIT_READY', () => void recover(), true); root.append(recoverButton);
    if (!context) return;
    const contextCard = document.createElement('section'); contextCard.className = 'uoc006-read-card'; contextCard.dataset.commitReadyContext = 'true';
    contextCard.innerHTML = `<h3>Precondición server-side</h3><dl><dt>Story</dt><dd><code>${escapeHtml(context.story_id)}</code></dd><dt>Quality</dt><dd><code>${escapeHtml(context.quality_report_id)}</code> · PASS</dd><dt>TestPlan</dt><dd><code>${escapeHtml(context.story_test_plan_id)}</code></dd><dt>ChangePlan</dt><dd><code>${escapeHtml(context.source_change_plan_id)}</code></dd><dt>Paths</dt><dd>${context.exact_paths.map(escapeHtml).join(', ')}</dd></dl>`; root.append(contextCard);
    const fields = document.createElement('div'); fields.className = 'uoc006-form-grid'; fields.append(field('Mensaje de commit', commitMessage, v => commitMessage = v), field('Autor', authorName, v => authorName = v), field('Email', authorEmail, v => authorEmail = v, 'email')); root.append(fields);
    const planButton = btn('Construir CommitPlan exacto', () => void createPlan()); planButton.disabled = busy || Boolean(stageExecution); root.append(planButton);
    if (plan) {
      const card = document.createElement('section'); card.className = 'uoc006-plan-card'; card.dataset.storyCommitPlan = 'true';
      card.innerHTML = `<h3>CommitPlan PASS</h3><dl><dt>ID</dt><dd><code>${escapeHtml(plan.commit_plan_id)}</code></dd><dt>Hash</dt><dd><code>${escapeHtml(plan.commit_plan_hash)}</code></dd><dt>HEAD</dt><dd><code>${escapeHtml(plan.head_before)}</code></dd><dt>Exact paths</dt><dd>${plan.exact_paths.map(escapeHtml).join(', ')}</dd><dt>Quality hash</dt><dd><code>${escapeHtml(plan.story_quality_report_hash)}</code></dd><dt>Approval</dt><dd>owner · stage_and_commit_separate=${String(plan.approval.stage_and_commit_separate)}</dd></dl>`; root.append(card);
      if (!stageApproval) root.append(btn('Solicitar approval de stage', () => void requestStageApproval()));
    }
    if (stageApproval) root.append(approvalCard('Approval 1 · stage exacto', stageApproval, 'stage'));
    if (plan && stageApproval?.status === 'approved' && !stageExecution) root.append(btn('Ejecutar stage exacto', () => void stage()));
    if (stageExecution) {
      const card = document.createElement('section'); card.className = 'uoc006-execution-card'; card.dataset.storyStagePass = 'true'; card.innerHTML = `<h3>STAGE PASS</h3><dl><dt>Execution</dt><dd><code>${escapeHtml(stageExecution.stage_execution_id)}</code></dd><dt>Paths</dt><dd>${stageExecution.staging_manifest.exact_paths.map(escapeHtml).join(', ')}</dd><dt>Index fingerprint</dt><dd><code>${escapeHtml(stageExecution.index_fingerprint)}</code></dd><dt>git add .</dt><dd>false</dd><dt>shell</dt><dd>false</dd></dl>`; root.append(card);
      if (!commitApproval && !commitRecord) root.append(btn('Solicitar approval de commit', () => void requestCommitApproval()));
    }
    if (commitApproval) root.append(approvalCard('Approval 2 · commit', commitApproval, 'commit'));
    if (stageExecution && commitApproval?.status === 'approved' && !commitRecord) root.append(btn('Crear commit gobernado', () => void commit()));
    if (commitRecord) {
      const card = document.createElement('section'); card.className = 'uoc006-execution-card uoc006-commit-pass'; card.dataset.storyCommitPass = 'true';
      card.innerHTML = `<h3>COMMIT PASS · TRACEABILITY COMPLETE</h3><dl><dt>Commit</dt><dd><code>${escapeHtml(commitRecord.commit_hash)}</code></dd><dt>Parent</dt><dd><code>${escapeHtml(commitRecord.parent_hash)}</code></dd><dt>Paths</dt><dd>${commitRecord.committed_paths.map(escapeHtml).join(', ')}</dd><dt>Requirements</dt><dd>${commitRecord.requirement_ids.map(escapeHtml).join(', ')}</dd><dt>Tests/evidence</dt><dd>${commitRecord.test_evidence_ids.map(escapeHtml).join(', ')}</dd><dt>Worktree clean</dt><dd>${String(commitRecord.worktree_clean)}</dd><dt>Push / force / rebase / reset-hard</dt><dd>false / false / false / false</dd><dt>Full Regression</dt><dd>0</dd></dl>`; root.append(card);
    }
  }

  draw();
  return root;
}
