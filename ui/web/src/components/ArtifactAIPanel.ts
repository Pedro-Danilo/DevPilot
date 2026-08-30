// DEVPL-GSDLC-07-C — governed Artifact Workbench AI assistance panel.
import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { AgentAssistDecision, AgentAssistMode, AgentAssistOperation, AgentAssistPlan, AgentAssistProposal, WorkspaceDocumentResource } from '../api/types';
import { renderContractBadges, renderUiStateNotice } from './ContractBadges';

interface ArtifactAIPanelOptions {
  tokenProvider: () => string;
  onDraftDecision?: () => void | Promise<void>;
}

type PanelState = 'idle' | 'loading' | 'planned' | 'proposed' | 'decided' | 'block';
const OPERATIONS: AgentAssistOperation[] = ['generate_draft', 'rewrite_selection', 'critique', 'improve', 'transform_imported_source'];

export function createArtifactAIPanel(options: ArtifactAIPanelOptions): HTMLElement {
  const root = document.createElement('section');
  root.className = 'panel artifact-ai-panel';
  root.dataset.devpilotUiContract = 'ui.workspace-documents';
  root.dataset.gsdlc07c = 'artifact-ai-panel';

  let documentValue: WorkspaceDocumentResource | undefined;
  let currentContent = '';
  let revisionSha256: string | null = null;
  let operation: AgentAssistOperation = 'improve';
  let mode: AgentAssistMode = 'mock';
  let instruction = 'Improve clarity while preserving governed intent.';
  let selectionStart: number | null = null;
  let selectionEnd: number | null = null;
  let importId = '';
  let plan: AgentAssistPlan | undefined;
  let proposal: AgentAssistProposal | undefined;
  let modifiedContent = '';
  let state: PanelState = 'idle';
  let message = 'Planifique primero. DevPilot mostrará agente, modelo, fuentes, costo y límites antes del run.';

  function client(): DevPilotApiClient { return new DevPilotApiClient({ token: options.tokenProvider() }); }
  function documentId(): string { return String(documentValue?.document_id ?? documentValue?.node_id ?? ''); }
  function sourceSha(): string { return String(documentValue?.sha256 ?? ''); }
  function supported(): boolean { return ['.md', '.json'].includes(String(documentValue?.extension ?? '').toLowerCase()); }

  async function preparePlan(): Promise<void> {
    if (!documentValue || !supported()) return;
    state = 'loading'; message = 'Preparando plan gobernado…'; draw();
    try {
      const response = await client().planArtifactAssist(documentId(), {
        operation, mode, instruction, current_content: currentContent, expected_source_sha256: sourceSha(),
        expected_revision_sha256: revisionSha256,
        selection_start: operation === 'rewrite_selection' ? selectionStart : null,
        selection_end: operation === 'rewrite_selection' ? selectionEnd : null,
        import_id: operation === 'transform_imported_source' ? importId.trim() || null : null,
      });
      plan = ((response.data ?? {}) as { plan?: AgentAssistPlan }).plan;
      proposal = undefined; modifiedContent = '';
      if (!plan) throw new Error('La API no devolvió un AgentAssistPlan verificable.');
      state = 'planned';
      message = 'PLAN PASS · revise ruta, contexto, costo y límites. RUN aún no escribe DRAFT ni source.';
    } catch (error) { state = 'block'; message = readableError(error); }
    draw();
  }

  async function runPlan(): Promise<void> {
    if (!plan) return;
    state = 'loading'; message = 'Ejecutando ruta hermética…'; draw();
    try {
      const response = await client().runArtifactAssist(plan.plan_id, plan.plan_sha256);
      proposal = ((response.data ?? {}) as { proposal?: AgentAssistProposal }).proposal;
      if (!proposal) throw new Error('La API no devolvió una propuesta estructurada.');
      modifiedContent = proposal.proposed_content;
      state = 'proposed';
      message = 'PROPOSAL PASS · salida UNTRUSTED. Revise diff antes de ACCEPT / REJECT / MODIFY.';
    } catch (error) { state = 'block'; message = readableError(error); }
    draw();
  }

  async function decide(decision: AgentAssistDecision): Promise<void> {
    if (!proposal) return;
    state = 'loading'; message = `Registrando decisión humana ${decision}…`; draw();
    try {
      const response = await client().decideArtifactAssist(proposal.proposal_id, {
        proposal_sha256: proposal.proposal_sha256,
        decision,
        modified_content: decision === 'MODIFY' ? modifiedContent : null,
      });
      proposal = ((response.data ?? {}) as { proposal?: AgentAssistProposal }).proposal ?? proposal;
      state = 'decided';
      message = `${decision} PASS · decisión humana registrada. APPROVED/FROZEN siguen en NO; source aprobado intacto.`;
      if (decision !== 'REJECT' && operation !== 'critique') await options.onDraftDecision?.();
    } catch (error) { state = 'block'; message = readableError(error); }
    draw();
  }

  function resetPlan(): void { plan = undefined; proposal = undefined; modifiedContent = ''; state = 'idle'; message = 'Parámetros cambiados. Genere un nuevo PLAN antes del run.'; draw(); }

  function draw(): void {
    root.replaceChildren();
    const heading = document.createElement('div'); heading.className = 'artifact-ai-heading';
    const title = document.createElement('h2'); title.textContent = 'Artifact Workbench · AI Assist';
    heading.append(title, renderContractBadges('ui.workspace-documents', { dryRunLabel: 'PLAN → PROPOSAL → HUMAN DECISION', warning: 'UNTRUSTED · DRAFT ONLY · ningún agente puede aprobar o congelar source.' }));
    root.append(heading);
    if (!documentValue) { root.append(renderUiStateNotice('empty', 'Seleccione un documento Markdown o JSON para habilitar asistencia contextual.')); return; }
    if (!supported()) { root.append(renderUiStateNotice('block', '07-C limita Agent Assist a Markdown/JSON. Esta superficie permanece read-only.')); return; }

    const boundary = document.createElement('p'); boundary.className = 'artifact-ai-boundary';
    boundary.textContent = 'Frontera 07-C: salida de modelo = UNTRUSTED. PLAN no ejecuta. RUN solo genera proposal. ACCEPT/MODIFY persisten una revisión runtime DRAFT; REJECT no escribe. APPROVED/FROZEN requieren el flujo humano gobernado existente.';
    root.append(boundary);

    const form = document.createElement('div'); form.className = 'artifact-ai-controls';
    const opLabel = labeledSelect('Operación', OPERATIONS, operation, (v) => { operation = v as AgentAssistOperation; resetPlan(); });
    const modeLabel = labeledSelect('Ruta', ['mock', 'fake-local'], mode, (v) => { mode = v as AgentAssistMode; resetPlan(); });
    const instructionLabel = document.createElement('label'); instructionLabel.textContent = 'Instrucción humana';
    const instructionArea = document.createElement('textarea'); instructionArea.rows = 3; instructionArea.maxLength = 4000; instructionArea.value = instruction;
    instructionArea.addEventListener('input', () => { instruction = instructionArea.value; plan = undefined; proposal = undefined; state = 'idle'; }); instructionLabel.append(instructionArea);
    form.append(opLabel, modeLabel, instructionLabel);

    if (operation === 'rewrite_selection') {
      const range = document.createElement('div'); range.className = 'artifact-ai-range';
      range.append(numberInput('Inicio selección', selectionStart, (v) => { selectionStart = v; resetPlan(); }), numberInput('Fin selección', selectionEnd, (v) => { selectionEnd = v; resetPlan(); }));
      const hint = document.createElement('small'); hint.textContent = `Contenido actual: ${currentContent.length} caracteres. Use índices de selección válidos; JSON parcial está bloqueado.`;
      range.append(hint); form.append(range);
    }
    if (operation === 'transform_imported_source') {
      const label = document.createElement('label'); label.textContent = 'Import ID existente';
      const input = document.createElement('input'); input.value = importId; input.placeholder = 'ai_… / import id'; input.maxLength = 128;
      input.addEventListener('input', () => { importId = input.value; plan = undefined; proposal = undefined; }); label.append(input); form.append(label);
    }
    const planButton = document.createElement('button'); planButton.type = 'button'; planButton.textContent = state === 'loading' ? 'Procesando…' : '1 · Preparar PLAN'; planButton.disabled = state === 'loading'; planButton.addEventListener('click', () => void preparePlan());
    form.append(planButton); root.append(form);

    if (plan) root.append(renderPlan(plan, () => void runPlan(), state === 'loading' || Boolean(proposal)));
    if (proposal) root.append(renderProposal(proposal, modifiedContent, (v) => { modifiedContent = v; }, (d) => void decide(d), state === 'loading' || state === 'decided'));
    const status = document.createElement('p'); status.dataset.agentAssistStatus = state; status.setAttribute('aria-live', 'polite'); status.textContent = message; root.append(status);
  }

  Object.assign(root, {
    setDocument(value?: WorkspaceDocumentResource) {
      documentValue = value; currentContent = String(value?.content ?? ''); revisionSha256 = null; plan = undefined; proposal = undefined; modifiedContent = ''; state = 'idle';
      message = 'Planifique primero. DevPilot mostrará agente, modelo, fuentes, costo y límites antes del run.'; draw();
    },
    setDraftContent(value: string, revision?: string | null) {
      currentContent = value; revisionSha256 = revision ?? null; if (plan || proposal) { plan = undefined; proposal = undefined; modifiedContent = ''; state = 'idle'; message = 'El DRAFT cambió; el plan anterior quedó invalidado. Prepare un nuevo PLAN.'; } draw();
    },
  });
  draw();
  return root;
}

function renderPlan(plan: AgentAssistPlan, run: () => void, disabled: boolean): HTMLElement {
  const box = document.createElement('section'); box.className = 'artifact-ai-plan'; box.dataset.agentAssistPlan = plan.plan_id;
  const h = document.createElement('h3'); h.textContent = 'Pre-run · plan sellado'; box.append(h);
  const dl = document.createElement('dl');
  const route = plan.model_route ?? {}; const agent = plan.agent ?? {}; const runtime = plan.runtime ?? {}; const cost = plan.cost ?? {}; const limits = plan.limits ?? {};
  add(dl, 'Agent role', agent.role_id); add(dl, 'Runtime', `${runtime.implementation ?? ''} · ${runtime.mode ?? ''}`); add(dl, 'Model', route.model_id); add(dl, 'Provider', route.provider_id); add(dl, 'Access route', route.access_route_id);
  add(dl, 'Context', `${plan.context?.status ?? 'unknown'} · ${(plan.context?.sources ?? []).length} sources · ${plan.context?.selected_tokens ?? 0} tokens`);
  add(dl, 'Estimate', `${cost.total_tokens ?? 'n/a'} tokens · $${cost.cost_usd ?? 0} · ${cost.cost_state ?? 'unknown'}`);
  add(dl, 'Limits', `${limits.max_steps ?? '?'} steps · ${limits.max_wall_time_seconds ?? '?'}s · max cost $${limits.max_cost_usd ?? '?'}`);
  add(dl, 'Authority', 'tool execution NO · human review YES · approval not-requested'); box.append(dl);
  const sources = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = `Fuentes grounded (${(plan.context?.sources ?? []).length})`; sources.append(summary);
  const ul = document.createElement('ul'); for (const source of plan.context?.sources ?? []) { const li=document.createElement('li'); li.textContent=`${source.citation_ref ?? 'citation'} · ${source.path ?? ''} · ${String(source.content_sha256 ?? '').slice(0,12)}…`; ul.append(li); } sources.append(ul); box.append(sources);
  const button = document.createElement('button'); button.type='button'; button.textContent='2 · RUN hermético'; button.disabled=disabled; button.addEventListener('click', run); box.append(button); return box;
}

function renderProposal(proposal: AgentAssistProposal, modified: string, update: (v: string) => void, decide: (d: AgentAssistDecision) => void, disabled: boolean): HTMLElement {
  const box=document.createElement('section'); box.className='artifact-ai-proposal'; box.dataset.agentAssistProposal=proposal.proposal_id;
  const h=document.createElement('h3'); h.textContent='Review · propuesta UNTRUSTED'; box.append(h);
  const warning=document.createElement('p'); warning.textContent='Revise el diff completo. Ningún botón de esta sección produce APPROVED/FROZEN ni escribe source aprobado.'; box.append(warning);
  if (proposal.critique?.length) { const ul=document.createElement('ul'); for (const item of proposal.critique) { const li=document.createElement('li'); li.textContent=item; ul.append(li); } box.append(ul); }
  const pre=document.createElement('pre'); pre.className='artifact-ai-diff'; pre.dataset.agentAssistDiff='true'; pre.textContent=proposal.diff || '(sin diferencias de contenido; critique es review-only)'; box.append(pre);
  const label=document.createElement('label'); label.textContent='Contenido propuesto / editable para MODIFY'; const area=document.createElement('textarea'); area.rows=12; area.value=modified; area.addEventListener('input',()=>update(area.value)); label.append(area); box.append(label);
  const provenance=document.createElement('p'); provenance.textContent=`Provenance: ${proposal.provenance.agent_role_id ?? ''} · ${proposal.provenance.provider_id ?? ''}/${proposal.provenance.model_id ?? ''} · ${proposal.provenance.estimated_tokens ?? 'n/a'} tokens · $${proposal.provenance.estimated_cost_usd ?? 0} · citations ${(proposal.provenance.citations ?? []).length}`; box.append(provenance);
  const actions=document.createElement('div'); actions.className='artifact-ai-decisions'; for (const d of ['ACCEPT','REJECT','MODIFY'] as AgentAssistDecision[]) { const b=document.createElement('button'); b.type='button'; b.textContent=d; b.disabled=disabled; b.dataset.agentAssistDecision=d; b.addEventListener('click',()=>decide(d)); actions.append(b); } box.append(actions); return box;
}

function labeledSelect(labelText: string, values: readonly string[], current: string, onChange: (v: string) => void): HTMLLabelElement { const label=document.createElement('label'); label.textContent=labelText; const select=document.createElement('select'); for(const value of values){const option=document.createElement('option');option.value=value;option.textContent=value;option.selected=value===current;select.append(option);} select.addEventListener('change',()=>onChange(select.value)); label.append(select); return label; }
function numberInput(labelText: string, value: number|null, onChange:(v:number|null)=>void): HTMLLabelElement { const label=document.createElement('label');label.textContent=labelText;const input=document.createElement('input');input.type='number';input.min='0';input.value=value===null?'':String(value);input.addEventListener('input',()=>onChange(input.value===''?null:Number(input.value)));label.append(input);return label; }
function add(dl: HTMLDListElement, term: string, value: unknown): void { const dt=document.createElement('dt');dt.textContent=term;const dd=document.createElement('dd');dd.textContent=String(value ?? 'n/a');dl.append(dt,dd); }
function readableError(error: unknown): string { if (error instanceof DevPilotApiError) return `${error.message}${error.findings?.length ? ` · ${error.findings.map((f)=>f.id).join(', ')}` : ''}`; return error instanceof Error ? error.message : String(error); }
