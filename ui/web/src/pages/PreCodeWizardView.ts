import { armApprovalCenterArtifactReviewHandoff, DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { AuthSessionContext, DevPilotApplicationResponse, PreCodeSemanticModel, PreCodeSemanticItem, PreCodeWizardProjection, PreCodeWizardStage } from '../api/types';
import { renderCriticalPathGuidance, renderTechnicalDisclosure } from '../components/CriticalPathGuidance';

const ROUTE_CONTRACT_ID = 'ui.pre-code-wizard';

export function renderPreCodeWizardView(tokenProvider: () => string | null, session: AuthSessionContext): HTMLElement {
  const host=document.createElement('section'); host.className='pre-code-wizard'; host.dataset.routeContractId=ROUTE_CONTRACT_ID;
  const title=document.createElement('div'); title.className='panel pre-code-wizard__intro';
  const h=document.createElement('h2'); h.textContent='Pre-code guiado';
  const p=document.createElement('p'); p.textContent='Completa Product Vision → Scope → Requirements → Architecture → Security → Test Strategy → Traceability. DevPilot conserva orden, validación, approval, apply y freeze server-side.';
  title.append(h,p); host.append(title);
  const body=document.createElement('div'); body.className='pre-code-wizard__body'; host.append(body);
  const client=()=>new DevPilotApiClient({token:tokenProvider()});
  void load();

  async function ensureLiveHumanSession(feedback: HTMLElement): Promise<boolean> {
    try {
      await client().authSession();
      return true;
    } catch (error) {
      await renderGovernedError(feedback,error);
      return false;
    }
  }

  async function renderGovernedError(feedback: HTMLElement, error: unknown): Promise<void> {
    if(error instanceof DevPilotApiError && error.status===401){
      setFeedback(feedback,'block','BLOCK: la sesión humana local ya no es válida. El estado server-side se conserva. Vuelve a iniciar sesión como Owner, recupera el contexto del proyecto y reanuda esta misma etapa; no repitas DRAFT, approval ni apply ya completados.');
      return;
    }
    if(error instanceof DevPilotApiError && error.status===0){
      try {
        const health=await client().health();
        const auth=await client().authSessionStatus();
        if(health.ok && !auth.authenticated){
          setFeedback(feedback,'block',`BLOCK: la API local responde, pero la sesión humana está ${auth.state}. Vuelve a iniciar sesión como Owner y reanuda la etapa actual; no repitas operaciones ya completadas.`);
          return;
        }
        if(health.ok){
          setFeedback(feedback,'block','BLOCK: la API local responde, pero la operación no pudo confirmar la sesión/transporte. Recarga una sola vez; si persiste, conserva el estado y reporta la evidencia.');
          return;
        }
      } catch {
        // Fall through to the bounded API-down message below.
      }
    }
    setFeedback(feedback,'block',errorText(error));
  }

  async function load(message?: string): Promise<void> {
    body.replaceChildren(statusBox('loading','Cargando estado server-authoritative…'));
    try {
      const response=await client().preCodeStatus();
      if(!response.ok) throw new Error(response.message);
      render(response.data.pre_code,message);
    } catch(error) {
      if(error instanceof DevPilotApiError && error.status===403){
        body.replaceChildren(statusBox('block','BLOCK: la API local está disponible, pero RBAC/policy denegó el acceso a Pre-code (HTTP 403). DevPilot no mutó el proyecto. Conserve esta evidencia; no reingrese contenido por fuera del producto.'));
        return;
      }
      const text=error instanceof DevPilotApiError && error.status===0 ? 'API/transporte local no disponible. El wizard falla cerrado: ninguna acción mutante queda habilitada.' : error instanceof Error ? error.message : 'No fue posible cargar el wizard.';
      body.replaceChildren(statusBox('block',text));
    }
  }

  function render(preCode: PreCodeWizardProjection, message?: string): void {
    body.replaceChildren();
    const partial=(preCode as PreCodeWizardProjection & {segmented_progress?:{completed:number;total:number;model:string;status:string}}).segmented_progress;
    const summary=document.createElement('section'); summary.className='panel pre-code-wizard__summary'; summary.dataset.status=preCode.status;
    const currentStage=preCode.stages.find((row)=>row.stage_id===preCode.current_stage_id);
    const sh=document.createElement('h3'); sh.textContent='Preparación antes de programar';
    const sp=document.createElement('p'); sp.textContent=`${preCode.readiness.mandatory_stages_frozen}/${preCode.readiness.mandatory_stages_total} etapas listas. ${currentStage ? `Ahora: ${currentStage.label}.` : preCode.status==='PRE_CODE_READY' ? 'Baseline Pre-code completo; Planning es el siguiente checkpoint.' : 'Baseline documental completo; falta resolver MIASI/readiness.'}`;
    const technical=renderTechnicalDisclosure('Ver readiness y controles técnicos',`Estado: ${preCode.status} · Readiness estricta: ${preCode.readiness.status} · MIASI: ${preCode.miasi.status} · gate ${preCode.miasi.gate_status} · riesgo ${preCode.miasi.risk_level}.`);
    technical.classList.add('pre-code-wizard__technical');
    summary.append(sh,sp,technical);
    if(partial && partial.status==='IN_PROGRESS'){
      const progress=document.createElement('p');progress.className='notice notice--info';progress.dataset.preCodeSegmentProgress='true';
      progress.textContent=`Requirements: ${partial.completed}/${partial.total} unidades guardadas con ${partial.model}. Selecciona el mismo modelo y pulsa una vez «Crear alternativa mejorada» para reanudar la secuencia automática; no existe DRAFT nuevo hasta completar el ensamblado.`;
      summary.append(progress);
    }
    if(message){ const m=document.createElement('p'); m.className='notice notice--pass'; m.textContent=message; summary.append(m); }
    const currentStatus=currentStage?.status ?? 'UNKNOWN';
    const sevenFrozen=preCode.readiness.mandatory_stages_frozen===preCode.readiness.mandatory_stages_total;
    const atC03Boundary=!currentStage && sevenFrozen && preCode.status!=='PRE_CODE_READY';
    const nextAction=preCode.status==='PRE_CODE_READY'
      ? 'Pre-code está READY. La siguiente frontera gobernada es Planning/Roadmap.'
      : atC03Boundary
        ? 'Confirma la aplicabilidad MIASI del producto y deja que DevPilot recalcule readiness estricta.'
        : currentStatus==='APPROVAL_REQUIRED'
          ? 'Revisa el diff y solicita/verifica el approval antes de aplicar.'
          : currentStatus==='APPLIED'
            ? 'Congela la etapa aplicada para habilitar la siguiente.'
            : currentStatus==='FROZEN'
              ? 'Continúa con la siguiente etapa disponible.'
              : 'Completa el contenido de la etapa actual y valida antes de pedir approval.';
    const guide=renderCriticalPathGuidance({
      eyebrow:'Pre-code · 7 etapas',
      title:currentStage ? `Etapa ${currentStage.order}: ${currentStage.label}` : preCode.status==='PRE_CODE_READY' ? 'Pre-code listo' : 'Boundary C-03 · MIASI/readiness',
      summary:atC03Boundary ? 'Los siete documentos ya están FROZEN. MIPSoftware sigue siendo el estándar transversal; este perfil Pre-code acredita su slice gobernado y MIASI/readiness decide si puede avanzar a Planning, sin afirmar que todas las fases del registry MIPSoftware global hayan sido ejecutadas.' : 'Cada etapa conserva la misma secuencia gobernada: draft → validar/diff → approval → apply → freeze.',
      steps:preCode.stages.map((row)=>({label:row.label,state:row.status==='FROZEN'?'done':row.stage_id===preCode.current_stage_id?'current':'upcoming'})),
      nextAction,
      blocker:preCode.readiness.status==='PASS' ? 'Sin blocker de readiness para este milestone.' : atC03Boundary ? 'MIASI debe quedar evaluado y el gate debe PASS antes de declarar PRE_CODE_READY.' : 'La etapa actual debe completar sus gates antes de avanzar.',
      approvalEffect:'El approval autoriza únicamente el plan/diff actual; no salta validación ni freeze.',
      recoveryHref:'/recovery',
    });
    const skipFeedback=document.createElement('div'); skipFeedback.className='pre-code-stepper__feedback'; skipFeedback.setAttribute('aria-live','assertive');
    body.append(summary,guide,stageStepper(preCode.stages,preCode.current_stage_id,(attempted)=>{
      skipFeedback.replaceChildren(statusBox('block',`BLOCK: ${attempted.label} todavía no está habilitada. Completa y congela la etapa actual antes de avanzar; no se ejecutó ninguna mutación.`));
      skipFeedback.tabIndex=-1; skipFeedback.focus();
    }),skipFeedback);
    if(!currentStage && preCode.readiness.mandatory_stages_frozen===preCode.readiness.mandatory_stages_total && preCode.status!=='PRE_CODE_READY') {
      body.append(renderC03ReadinessGate(preCode));
      return;
    }
    if(preCode.status==='PRE_CODE_READY'){
      const done=document.createElement('section'); done.className='panel pre-code-wizard__done'; done.dataset.preCodeReady='true';
      const dh=document.createElement('h3'); dh.textContent='PRE_CODE_READY';
      const dp=document.createElement('p'); dp.textContent='Las siete etapas obligatorias están FROZEN, sus hashes coinciden y los perfiles documentales están válidos.';
      done.append(dh,dp); body.append(done); return;
    }
    const stage=preCode.stages.find((row)=>row.stage_id===preCode.current_stage_id);
    if(!stage){ body.append(statusBox('block','BLOCK: no existe current stage determinístico.')); return; }
    const adrGate=preCode.architecture_adr_bundle;
    if(adrGate?.required && !adrGate.ready){
      body.append(renderArchitectureAdrGate(adrGate));
      if(stage.order>4) return;
    }
    const editor=stageEditor(stage,preCode);
    if(preCode.advisor){
      body.append(renderPreCodeActionGuide(stage,preCode,editor));
    }
    body.append(editor);
  }

  function renderC03ReadinessGate(preCode: PreCodeWizardProjection): HTMLElement {
    const section=document.createElement('section'); section.className='panel pre-code-c03-readiness'; section.dataset.c03Readiness='true';
    const h=document.createElement('h3'); h.textContent='Paso 13 · MIASI/MIPSoftware + Pre-code readiness';
    const p=document.createElement('p'); p.textContent='Las siete etapas documentales están FROZEN y fueron ejecutadas bajo el perfil Pre-code gobernado por MIPSoftware. El estado formal del registry MIPSoftware global es una proyección distinta y todavía no está mapeado fase por fase; para cerrar este perfil falta clasificar explícitamente si el producto incorpora capacidades AI/agentic.';
    const state=document.createElement('p'); state.className='notice notice--info'; state.textContent=`MIASI ${preCode.miasi.status} · gate ${preCode.miasi.gate_status} · strict readiness ${preCode.readiness.status}. Esta decisión escribe solo runtime de DevPilot; no modifica documentos del proyecto.`;
    const feedback=document.createElement('div'); feedback.setAttribute('role','status'); feedback.setAttribute('aria-live','polite');
    const form=document.createElement('div'); form.className='pre-code-c03-readiness__form';
    const label=document.createElement('label'); label.textContent='¿El producto inventory-sales-local-greenfield usa capacidades AI/agentic?';
    const select=document.createElement('select'); select.setAttribute('aria-label','Aplicabilidad MIASI del producto');
    const no=document.createElement('option'); no.value='no'; no.textContent='No · producto sin AI/agents/RAG';
    const yes=document.createElement('option'); yes.value='yes'; yes.textContent='Sí · el producto incorpora AI/agentic'; select.append(no,yes);
    const riskLabel=document.createElement('label'); riskLabel.textContent='Riesgo declarado';
    const risk=document.createElement('select'); risk.setAttribute('aria-label','Riesgo MIASI');
    for(const value of ['low','medium','medium_high','high','critical']){const o=document.createElement('option');o.value=value;o.textContent=value;risk.append(o);}
    const capabilities=document.createElement('input'); capabilities.type='text'; capabilities.placeholder='Capacidades AI separadas por coma (solo si aplica)'; capabilities.setAttribute('aria-label','Capacidades MIASI');
    capabilities.disabled=true; risk.disabled=true;
    select.addEventListener('change',()=>{const ai=select.value==='yes';capabilities.disabled=!ai;risk.disabled=!ai;if(!ai){capabilities.value='';risk.value='low';}});
    const submit=button('Evaluar MIASI y recalcular readiness',async()=>{
      if(!await ensureLiveHumanSession(feedback))return;
      const declared=select.value==='yes';
      const caps=declared?capabilities.value.split(',').map(x=>x.trim()).filter(Boolean):[];
      try{const r=await client().preCodeMiasiApplicability({declared_ai_usage:declared,capabilities:caps,risk_level:(declared?risk.value:'low') as 'low'|'medium'|'medium_high'|'high'|'critical',evidence_refs:['owner-confirmed:13-C-03']});if(!r.ok)throw new Error(formatFindings(r));await load(declared?'MIASI evaluada. Revisa controles faltantes antes de avanzar.':'MIASI NOT_APPLICABLE confirmada por el Owner; readiness estricta fue reevaluada.');}catch(e){await renderGovernedError(feedback,e);}
    });
    const disclosure=renderTechnicalDisclosure('Qué cambia y qué no cambia','La decisión se guarda como evidencia runtime local del workspace a través de la API gobernada. No edita estándares, no ejecuta modelos/agentes/RAG ni usa red externa; el registry MIPSoftware conserva autoridad separada.');
    form.append(label,select,riskLabel,risk,capabilities,submit); section.append(h,p,state,form,feedback,disclosure); return section;
  }

  function renderArchitectureAdrGate(gate: NonNullable<PreCodeWizardProjection['architecture_adr_bundle']>): HTMLElement {
    const section=document.createElement('section'); section.className='panel pre-code-adr-gate'; section.dataset.architectureAdrGate='true'; section.dataset.status=gate.status;
    const h=document.createElement('h3'); h.textContent='ADRs de Architecture · materialización gobernada';
    const p=document.createElement('p'); p.textContent='Architecture ya está FROZEN. Sus decisiones ADR deben materializarse como documentos standalone antes de comenzar Security. Este paso no reinterpreta ni cambia las decisiones aprobadas.';
    const list=document.createElement('ul');
    for(const adr of gate.adrs??[]){const li=document.createElement('li');li.textContent=`${adr.adr_id} · ${adr.title} → ${adr.relative_path} · ${adr.source_state??'PENDIENTE'}`;list.append(li);}
    const feedback=document.createElement('div'); feedback.setAttribute('role','status'); feedback.setAttribute('aria-live','polite');
    section.append(h,p,list,feedback);
    if(gate.status==='REQUIRED' || gate.status==='BLOCK'){
      section.append(button('Preparar plan/diff de ADRs',async()=>{if(!await ensureLiveHumanSession(feedback))return;try{const r=await client().preCodeArchitectureAdrsPrepare();if(!r.ok)throw new Error(formatFindings(r));await load('Plan ADR multiarchivo preparado sin escribir source. Revisa paths/hashes y solicita approval.');}catch(e){await renderGovernedError(feedback,e);}}));
    } else if(gate.status==='PLANNED'){
      const meta=document.createElement('p'); meta.textContent=`Plan ${gate.plan_id??'n/a'} · hash ${gate.plan_hash??'n/a'}. Paths exactos: ${(gate.exact_paths??[]).join(', ')}`; section.append(meta);
      section.append(button('Solicitar approval para materializar ADRs',async()=>{if(!await ensureLiveHumanSession(feedback))return;try{const r=await client().preCodeArchitectureAdrsApprovalRequest();if(!r.ok)throw new Error(formatFindings(r));await load('Approval ADR solicitado. Abre Approval Center dirigido, decide y vuelve a verificar/aplicar.');}catch(e){await renderGovernedError(feedback,e);}}));
    } else if(gate.status==='APPROVAL_PENDING' && gate.approval_id){
      const approvalId=String(gate.approval_id); armApprovalCenterArtifactReviewHandoff(session,approvalId);
      const a=document.createElement('p'); a.textContent=`Approval ADR: ${approvalId}`; section.append(a);
      const open=document.createElement('button'); open.type='button'; open.className='button-link'; open.textContent='Abrir Approval Center dirigido ↗'; open.addEventListener('click',()=>{armApprovalCenterArtifactReviewHandoff(session,approvalId);globalThis.open(`/approvals?handoff=artifact-review&approval_id=${encodeURIComponent(approvalId)}`,'_blank','noopener,noreferrer');}); section.append(open);
      section.append(button('Verificar approval y materializar ADRs',async()=>{if(!await ensureLiveHumanSession(feedback))return;try{const shown=await client().showApproval(approvalId);const status=String((shown.data as Record<string,unknown>)?.['approval']&&((shown.data as Record<string,unknown>)['approval'] as Record<string,unknown>)['status']||'');if(status!=='approved'){setFeedback(feedback,'block',`Approval todavía está ${status||'pending'}. No se escriben ADRs.`);return;}const r=await client().preCodeArchitectureAdrsApply();if(!r.ok)throw new Error(formatFindings(r));await load('ADRs standalone materializados con approval exacto. Security queda habilitada.');}catch(e){await renderGovernedError(feedback,e);}}));
    }
    return section;
  }

  function renderPreCodeActionGuide(stage: PreCodeWizardStage, preCode: PreCodeWizardProjection, editor: HTMLElement): HTMLElement {
    const section=document.createElement('section'); section.className='panel pre-code-action-guide'; section.dataset.preCodeActionGuide='true';
    const title=document.createElement('h3'); title.textContent='Rutas para esta etapa';
    const copy=document.createElement('p'); copy.textContent='Las tarjetas muestran rutas y acciones disponibles; el selector Modo de autoría controla cómo se produce el DRAFT de esta etapa.';
    section.append(title,copy);
    const actions=preCode.advisor?.actions ?? [];

    const authoring=actionGroup('Cómo crear el DRAFT');
    if((stage.allowed_modes as string[]).includes('LOCAL_MODEL')) authoring.append(simpleActionCard('Generar propuesta con IA local','Un candidato Markdown trazable, sin publicar ni aprobar automáticamente.','RECOMENDADO',true,()=>selectAuthoringMode(editor,'LOCAL_MODEL')));
    if(stage.allowed_modes.includes('DEVPL_MOCK')){
      const c02=['architecture','security','test-strategy','traceability'].includes(stage.stage_id);
      authoring.append(simpleActionCard(c02?'DevPilot local · grounding ContextPack':'Referencia determinística (diagnóstico)',c02?'Genera un baseline técnico trazable desde artefactos FROZEN y ContextPack v2 local como grounding suplementario. No ejecuta LLM ni API externa; el Owner revisa/edita y aprueba.':'Genera una propuesta determinística desde Project Context y artefactos FROZEN, sin red ni API externa.','DIAGNÓSTICO',true,()=>selectAuthoringMode(editor,'DEVPL_MOCK')));
    }
    const manual=actions.find((row)=>row.kind==='MANUAL');
    if(stage.allowed_modes.includes('MANUAL')) authoring.append(simpleActionCard('Manual / Paste','Escribe o pega el contenido dentro del editor gobernado de esta etapa.',manual?.availability ?? 'AVAILABLE',manual?.executable ?? true,()=>selectAuthoringMode(editor,'MANUAL')));
    const imported=actions.find((row)=>row.kind==='UPLOAD_IMPORT');
    if(stage.allowed_modes.includes('IMPORT')) authoring.append(simpleActionCard('Importar archivo local','Carga Markdown local dentro del mismo wizard; no escribe source hasta approval/apply.',imported?.availability ?? 'AVAILABLE',imported?.executable ?? true,()=>selectAuthoringMode(editor,'IMPORT')));

    const auxiliary=actionGroup('Herramientas auxiliares');
    const external=actions.find((row)=>row.kind==='EXTERNAL_EDITOR');
    auxiliary.append(simpleActionCard('Abrir Documentos / preparar edición externa','DevPilot abre el workbench documental; no lanza ni controla un editor externo. Al regresar, la reconciliación sigue siendo obligatoria.',external?.availability ?? 'UNAVAILABLE',Boolean(external?.executable && external?.navigation_target),()=>{if(external?.navigation_target)globalThis.location.assign(external.navigation_target);}));
    const validation=actions.find((row)=>row.kind==='TYPED_OPERATION');
    auxiliary.append(simpleActionCard('Validar artefacto actual','El gate canónico es “Validar y preparar diff” dentro del editor. Se habilita después de materializar un DRAFT.',stage.status==='MISSING'?'DISPONIBLE DESPUÉS DE DRAFT':(validation?.availability ?? 'AVAILABLE'),false));

    const advanced=actionGroup('IA avanzada');
    for(const kind of ['AGENT','RAG'] as const){
      const action=actions.find((row)=>row.kind===kind);
      const label=kind==='AGENT'?'Agent':'RAG';
      const reasons=action?.disabled_reasons?.map((row)=>row.message).join(' · ') || 'Esta ruta avanzada no es necesaria para el baseline determinístico.';
      const c02Note=stage.order>=4?(kind==='AGENT'?'Los agentes especializados existentes son capacidades gobernadas de análisis/review; aún no son providers de primer DRAFT de Pre-code.':'El DRAFT local de C-02 usa ContextPack v2 internamente; esta tarjeta representa una ruta RAG/agentic independiente todavía no integrada.'):'';
      advanced.append(simpleActionCard(label,action?.availability==='AVAILABLE'?(action.purpose || 'Ruta agentic gobernada.'):`${c02Note} ${reasons}`.trim(),action?.availability ?? 'UNAVAILABLE',false));
    }
    section.append(authoring,auxiliary,advanced);
    return section;
  }

  function actionGroup(label:string):HTMLElement{
    const group=document.createElement('section'); group.className='pre-code-action-guide__group';
    const h=document.createElement('h4'); h.textContent=label; group.append(h); return group;
  }

  function simpleActionCard(label:string,purpose:string,status:string,enabled:boolean,onClick?:()=>void):HTMLElement{
    const card=document.createElement('article'); card.className='pre-code-action-guide__card'; card.dataset.status=status;
    const h=document.createElement('h5'); h.textContent=label; const badge=document.createElement('span'); badge.className='step-action-card__badge'; badge.textContent=status;
    const p=document.createElement('p'); p.textContent=purpose; card.append(h,badge,p);
    if(onClick){const b=document.createElement('button'); b.type='button'; b.textContent=label.startsWith('Abrir Documentos')?'Abrir Documentos / preparar edición externa':'Usar esta ruta'; b.disabled=!enabled; b.addEventListener('click',()=>onClick()); card.append(b);}
    return card;
  }

  function selectAuthoringMode(editor:HTMLElement,value:'DEVPL_MOCK'|'MANUAL'|'IMPORT'|'LOCAL_MODEL'):void{
    const mode=editor.querySelector<HTMLSelectElement>('[data-pre-code-authoring-mode]');
    if(!mode || !Array.from(mode.options).some((row)=>row.value===value))return;
    mode.value=value; mode.dispatchEvent(new Event('change'));
    if(value==='IMPORT') editor.querySelector<HTMLInputElement>('[data-pre-code-authoring-file]')?.click();
    else editor.querySelector<HTMLTextAreaElement>('[data-pre-code-authoring-content]')?.focus();
  }

  function semanticAdvancedDetails(model: PreCodeSemanticModel): HTMLElement {
    const details=document.createElement('details'); details.className='pre-code-semantic-details'; details.dataset.preCodeSemanticAdvanced='true';
    const summary=document.createElement('summary'); summary.textContent='Ver análisis de DevPilot';
    const intro=document.createElement('p'); intro.className='muted'; intro.textContent='Detalle avanzado para auditoría. No necesitas revisar esta estructura para completar el flujo normal.';
    const pre=document.createElement('pre'); pre.textContent=JSON.stringify(model,null,2);
    details.append(summary,intro,pre); return details;
  }

  function decisionQuestions(model: PreCodeSemanticModel, stageId: string): PreCodeSemanticItem[] {
    const order:Record<string,number>={'product-vision':1,'scope':2,'requirements':3};
    const current=order[stageId]??3;
    return (model.open_questions??[]).filter((item)=>{
      if(item.status==='REJECTED' || !item.critical)return false;
      const required=order[item.required_stage??'requirements']??3;
      if(required>current)return false;
      return !(item.status==='CONFIRMED' && Boolean((item.decision??'').trim()));
    });
  }

  function semanticDecisionInbox(model: PreCodeSemanticModel, stageId: string): { element: HTMLElement; read: () => PreCodeSemanticModel } | null {
    const draft=JSON.parse(JSON.stringify(model)) as PreCodeSemanticModel;
    const questions=decisionQuestions(draft,stageId);
    if(!questions.length)return null;
    const host=document.createElement('section'); host.className='pre-code-decision-inbox'; host.dataset.preCodeDecisionInbox='true';
    const h=document.createElement('h4'); h.textContent=`Decisiones pendientes (${questions.length})`;
    const p=document.createElement('p'); p.textContent='DevPilot ya preparó el documento. Responde solo estas decisiones porque son necesarias para que la etapa actual pueda quedar verificable; no necesitas revisar el modelo interno.';
    host.append(h,p);
    for(const item of questions){
      const row=document.createElement('div'); row.className='pre-code-decision-inbox__item'; row.dataset.semanticItemId=item.id;
      const label=document.createElement('label'); label.textContent=item.statement; label.htmlFor=`decision-${stageId}-${item.id}`;
      const impact=document.createElement('p'); impact.className='muted'; impact.textContent=`Afecta ${item.required_stage??stageId}. Fuente: ${item.source_excerpt??'Project Context'}.`;
      const input=document.createElement('input'); input.type='text'; input.id=`decision-${stageId}-${item.id}`; input.value=item.decision??''; input.placeholder='Escribe la decisión del Owner';
      input.addEventListener('input',()=>{item.decision=input.value;if(input.value.trim()){item.status='CONFIRMED';item.owner_confirmed=true;}else{item.status='OPEN';item.owner_confirmed=false;}});
      row.append(label,impact,input); host.append(row);
    }
    return {element:host,read:()=>draft};
  }

  function stageEditor(stage: PreCodeWizardStage, preCode: PreCodeWizardProjection): HTMLElement {
    const section=document.createElement('section'); section.className='panel pre-code-stage'; section.dataset.stageId=stage.stage_id; section.dataset.stageStatus=stage.status;
    const heading=document.createElement('h3'); heading.textContent=`${stage.order}. ${stage.label}`;
    const path=document.createElement('p'); path.className='muted'; path.textContent=`Destino gobernado: ${stage.relative_path} · Estado ${stage.status}`;
    section.append(heading,path);
    const feedback=document.createElement('div'); feedback.dataset.preCodeStageFeedback='true'; feedback.setAttribute('role','status'); feedback.setAttribute('aria-live','polite'); section.append(feedback);
    const inbox=preCode.semantic_model && stage.status!=='MISSING' ? semanticDecisionInbox(preCode.semantic_model,stage.stage_id) : null;

    if(['MISSING','DRAFT','FINDINGS'].includes(stage.status)){
      const form=document.createElement('div'); form.className='pre-code-stage__editor';
      const modeLabel=document.createElement('label'); modeLabel.textContent='Modo de autoría';
      const mode=document.createElement('select'); mode.dataset.preCodeAuthoringMode='true'; mode.setAttribute('aria-label','Modo de autoría');
      for(const value of stage.allowed_modes as string[]){ const option=document.createElement('option'); option.value=value; option.textContent=value==='DEVPL_MOCK'?(stage.order>=4?'DevPilot · Diseño local + RAG / sin API':'DevPilot · Mock local / sin API'):value==='MANUAL'?'Manual':value==='LOCAL_MODEL'?'Modelo local · asistente de redacción':'Importar archivo local'; mode.append(option); }
      if(stage.mode && stage.allowed_modes.includes(stage.mode)) mode.value=stage.mode;
      // R02-07/COR192: the dropdown is populated through existing Owner-gated
      // local readiness. Never accept an arbitrary model name or remote endpoint.
      const modelLabel=document.createElement('label'); modelLabel.textContent='Modelo Ollama instalado';modelLabel.htmlFor=`pre-code-model-${stage.stage_id}`;
      const modelInput=document.createElement('select'); modelInput.setAttribute('aria-label','Modelo local instalado');modelInput.id=`pre-code-model-${stage.stage_id}`; modelInput.dataset.r0207Model='true';
      const modelNotice=document.createElement('p'); modelNotice.setAttribute('role','status'); modelNotice.setAttribute('aria-live','polite');
      const reloadModels=button('Consultar modelos instalados',async()=>{await loadInstalledModels();}); reloadModels.type='button';
      const modelControls=document.createElement('div');modelControls.className='pre-code-model-controls';modelControls.style.display='flex';modelControls.style.flexWrap='wrap';modelControls.style.gap='0.75rem';modelControls.style.alignItems='center';
      modelInput.style.minWidth='min(100%, 19rem)';modelInput.style.flex='1 1 19rem';reloadModels.className='button-link';
      modelControls.append(modelInput,reloadModels);
      const modelPanel=document.createElement('div');modelPanel.append(modelLabel,modelControls,modelNotice);modelPanel.hidden=mode.value!=='LOCAL_MODEL';
      let modelProbeBusy=false;
      const setModelOptions=(models:string[], selected?:string)=>{
        modelInput.replaceChildren();const choice=document.createElement('option');choice.value='';choice.textContent='Selecciona un modelo instalado';modelInput.append(choice);
        for(const name of models){const option=document.createElement('option');option.value=name;option.textContent=name;modelInput.append(option);}
        modelInput.value=(selected&&models.includes(selected))?selected:(models.length===1?models[0]:'');
        save.disabled=!correlationOK || draftBusy || (mode.value==='LOCAL_MODEL' && stage.status==='MISSING' && !modelInput.value);
      };
      async function loadInstalledModels():Promise<void>{
        if(modelProbeBusy)return;modelProbeBusy=true;reloadModels.disabled=true;modelInput.disabled=true;
        modelNotice.textContent='Consultando Ollama local, sin inferencia ni API externa…';
        const previous=modelInput.value;
        try{
          const reply=await client().probeLocalModelReadiness();
          if(!reply.ok)throw new Error(formatFindings(reply));
          const providers=(reply.data as {providers?:Array<{provider_id?:string;healthy?:boolean;models?:string[]}>}).providers??[];
          const ollama=providers.find((item)=>item.provider_id==='ollama');
          const names=ollama?.healthy===true?(ollama.models??[]).filter((s)=>/^[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,99}$/.test(s)).slice(0,32):[];
          setModelOptions([...new Set(names)],previous||String((stage.derivation as {model?:string}|null)?.model??''));
          modelNotice.textContent=names.length?`PASS: ${names.length} modelo(s) disponible(s) en Ollama. Selecciona uno antes de generar.`:'BLOCK: Ollama no responde o no se encontraron modelos instalados. No se ejecutó inferencia.';
          reloadModels.hidden=names.length>0;
        }catch(error){setModelOptions([]);reloadModels.hidden=false;modelNotice.textContent='BLOCK: '+(error instanceof Error?error.message:'No fue posible consultar Ollama.');}
        finally{modelProbeBusy=false;reloadModels.disabled=false;modelInput.disabled=false;}
      }
      modelInput.addEventListener('change',()=>{save.disabled=!correlationOK || draftBusy || (mode.value==='LOCAL_MODEL' && stage.status==='MISSING' && !modelInput.value);});

      const textLabel=document.createElement('label'); textLabel.htmlFor=`pre-code-${stage.stage_id}`; textLabel.textContent='Propuesta del artefacto';
      const textarea=document.createElement('textarea'); textarea.dataset.preCodeAuthoringContent='true'; textarea.id=`pre-code-${stage.stage_id}`; textarea.rows=20; textarea.spellcheck=false; textarea.value=stage.draft_content??'';
      // Correlate the editor with the server-authoritative candidate receipt.
      // Never call a near-identical generation a successful semantic refinement.
      const binding=(stage as PreCodeWizardStage & {candidate_content_binding?: {
        status?:string;reason?:string;visible_sha256?:string;candidate_sha256?:string;
        candidate_path?:string;owner_edited?:boolean;model?:string
      }}).candidate_content_binding;
      const active=document.createElement('div'); active.dataset.preCodeActiveCandidate='true';
      active.setAttribute('role','status'); active.setAttribute('aria-live','polite');
      const localDraft=String(stage.mode)==='LOCAL_MODEL'&&stage.status!=='MISSING';
      const correlationOK=!localDraft || binding?.status==='PASS';
      const short=(v?:string)=>v?`${v.slice(0,12)}…`: 'no disponible';
      active.className=correlationOK?'notice notice--info':'notice notice--block';
      if(localDraft){
        active.textContent=correlationOK
          ? `Candidato activo verificado · ${binding?.candidate_path??'sin ruta'} · modelo ${binding?.model??'desconocido'} · SHA Markdown ${short(binding?.visible_sha256)} · origen ${short(binding?.candidate_sha256)}${binding?.owner_edited?' · edición Owner':''}`
          : `BLOCK: Markdown/editor y procedencia no concuerdan (${binding?.reason??'sin recibo'}). No validar, aprobar ni generar otra alternativa hasta reconciliar el estado.`;
        form.append(active);
      }
      const nearDuplicate=Boolean((stage.derivation as {near_duplicate_predecessor?:boolean}|null)?.near_duplicate_predecessor);
      if(nearDuplicate){
        const warning=document.createElement('p');warning.className='notice notice--warning';
        warning.dataset.preCodeNearDuplicate='true';
        warning.textContent='La nueva alternativa es casi idéntica a la anterior: se conservó su trazabilidad, pero no demuestra una mejora semántica. Considera revisar/editar el Markdown en lugar de repetir la inferencia.';
        form.append(warning);
      }
      textarea.placeholder=mode.value==='DEVPL_MOCK'?(stage.status==='MISSING'?'Pulsa “Generar propuesta con DevPilot”. DevPilot mostrará primero el DRAFT completo.':'Revisa y edita directamente la propuesta completa si lo necesitas.'):'Escribe o pega aquí el contenido del artefacto. No incluyas secretos.';
      const fileLabel=document.createElement('label'); fileLabel.textContent='Archivo local para IMPORT';
      const file=document.createElement('input'); file.dataset.preCodeAuthoringFile='true'; file.type='file'; file.accept='.md,text/markdown,text/plain'; file.hidden=mode.value!=='IMPORT'; fileLabel.hidden=file.hidden;
      let draftBusy=false;
      const nearButtonStatus=document.createElement('span'); nearButtonStatus.dataset.preCodeDraftProgress='true';
      nearButtonStatus.setAttribute('role','status'); nearButtonStatus.setAttribute('aria-live','polite');
      nearButtonStatus.style.marginLeft='0.75rem'; nearButtonStatus.style.fontWeight='600';
      const segmentProgress=(preCode as PreCodeWizardProjection & {segmented_progress?:{
        completed:number;total:number;model:string;status:string
      }}).segmented_progress;
      // COR208: Each HTTP request is one bounded inference on the server, but a
      // single Owner gesture drives the sequence. Persisted checkpoints stay
      // authoritative and survive reload; never maintain hidden local receipts.
      const segmentMeter=document.createElement('progress');
      segmentMeter.dataset.preCodeSegmentMeter='true';
      segmentMeter.max=segmentProgress?.total || 1;
      segmentMeter.value=segmentProgress?.completed || 0;
      segmentMeter.style.width='min(100%, 19rem)';
      segmentMeter.style.verticalAlign='middle';
      const segmentMeterBox=document.createElement('div');
      segmentMeterBox.dataset.preCodeSegmentMeterBox='true';
      segmentMeterBox.style.margin='0.65rem 0';
      segmentMeterBox.hidden=stage.stage_id!=='requirements'||!segmentProgress;
      segmentMeterBox.append(segmentMeter);
      if(stage.stage_id==='requirements' && segmentProgress?.status==='IN_PROGRESS'){
        nearButtonStatus.textContent=`Requirements: ${segmentProgress.completed}/${segmentProgress.total} unidades conservadas. Una acción continúa la secuencia.`;
      }else if(stage.stage_id==='requirements' && segmentProgress?.status==='COMPLETE'){
        nearButtonStatus.textContent=`Requirements: ${segmentProgress.completed}/${segmentProgress.total} unidades completas; revisar DRAFT ensamblado.`;
      }
      const setSegmentMeter=(completed:number,total:number):void=>{
        segmentMeterBox.hidden=false;segmentMeter.max=total;segmentMeter.value=completed;
        nearButtonStatus.textContent=`Requirements: ${completed}/${total} unidades validadas. Continuando automáticamente…`;
      };
      async function runRequirementsSequence(model:string):Promise<void>{
        // No autonomous retries; at most 12 Scope capabilities and one global
        // unit. A failed or uncertain response stops immediately, preserving
        // server-side checkpoints. On refresh, the Owner explicitly resumes.
        const limit=13;
        let previous=segmentProgress?.status==='IN_PROGRESS'?segmentProgress.completed:0;
        // A completed old 6-unit profile is not the active COR209 plan.
        // Do not announce an old denominator while a new profile is loading.
        let activeTotal=segmentProgress?.status==='IN_PROGRESS'?segmentProgress.total:undefined;
        if(segmentProgress?.status==='IN_PROGRESS' && segmentProgress.model!==model){
          throw new Error(`BLOCK: existe una secuencia parcial con ${segmentProgress.model}. Selecciona ese modelo antes de reanudar; no crees otro plan accidental.`);
        }
        for(let i=0;i<limit;i++){
          nearButtonStatus.textContent=`⏳ Generando Requirements: unidad ${previous+1} de ${activeTotal ?? 'total por confirmar'}…`;
          const result=await client().preCodeDraft(stage.stage_id,{mode:'LOCAL_MODEL',content:'',semantic_model:null,model});
          if(!result.ok)throw new Error(formatFindings(result));
          const seg=(result.data as {segmented_progress?:{
            completed:number;total:number;model?:string;status?:string
          }}|undefined)?.segmented_progress;
          if(!seg){
            await load('Requirements ensamblado como un único DRAFT Markdown; revisa íntegramente el contenido antes de validar.');
            return;
          }
          if(!Number.isInteger(seg.completed)||!Number.isInteger(seg.total)||seg.total<1||seg.total>limit||
              seg.completed<=previous||seg.completed>=seg.total||seg.model!==model||seg.status!=='IN_PROGRESS'){
            throw new Error('BLOCK: progreso segmentado inconsistente. Verifica el estado persistido antes de reanudar.');
          }
          previous=seg.completed;
          activeTotal=seg.total;
          setSegmentMeter(seg.completed,seg.total);
        }
        throw new Error('BLOCK: se alcanzó el límite finito de unidades; conserva checkpoints y revisa el plan.');
      }
      function setDraftBusy(value:boolean,inference=false):void{
        draftBusy=value; save.disabled=!correlationOK || value || Boolean(inbox) || (mode.value==='LOCAL_MODEL'&&stage.status==='MISSING'&&!modelInput.value);
        alternative.disabled=value || !modelInput.value;
        mode.disabled=value; modelInput.disabled=value; textarea.readOnly=value;
        save.setAttribute('aria-busy',String(value)); alternative.setAttribute('aria-busy',String(value));
        nearButtonStatus.textContent=value?(inference?'⏳ Generando documento con el modelo local. No vuelvas a pulsar; puede tardar varios minutos.':'⏳ Guardando revisión del DRAFT…'):'';
        if(value){save.textContent=inference?'Generando…':'Guardando…';alternative.textContent='Generando…';}
        else{updateSaveLabel();alternative.textContent='Crear alternativa mejorada con modelo local';}
      }
      const save=button(mode.value==='DEVPL_MOCK'?(stage.status==='MISSING'?'Generar propuesta con DevPilot':'Guardar revisión del Owner'):mode.value==='LOCAL_MODEL'&&stage.status==='MISSING'?'Generar DRAFT con modelo local':'Guardar DRAFT',async()=>{
        if(draftBusy)return;
        setDraftBusy(true,mode.value==='LOCAL_MODEL'&&stage.status==='MISSING');
        setFeedback(feedback,'loading',mode.value==='DEVPL_MOCK'?(stage.status==='MISSING'?'Generando propuesta completa desde el contexto gobernado; sin red ni API externa…':'Guardando revisión del Owner sin escribir source…'):'Guardando DRAFT sin escribir source…');
        if(!await ensureLiveHumanSession(feedback)){setDraftBusy(false);return;}
        try{
          const devpilot=mode.value==='DEVPL_MOCK';
          if(mode.value==='LOCAL_MODEL'&&stage.status==='MISSING'&&!modelInput.value){setFeedback(feedback,'block','Selecciona un modelo Ollama instalado antes de generar.');return;}
          const r=await client().preCodeDraft(stage.stage_id,{mode:mode.value as 'MANUAL'|'IMPORT'|'DEVPL_MOCK'|'LOCAL_MODEL',content:devpilot?(stage.status==='MISSING'?'':textarea.value):mode.value==='LOCAL_MODEL'&&stage.status==='MISSING'?'':textarea.value,semantic_model:null,model:mode.value==='LOCAL_MODEL'?modelInput.value.trim():''});
          if(!r.ok) throw new Error(formatFindings(r));
          const seg=(r.data as {segmented_progress?:{completed:number;total:number}}|undefined)?.segmented_progress;
          if(seg){await load(`PASS: Requirements ${seg.completed}/${seg.total} unidades validadas. No se ha publicado DRAFT ni escrito source. Pulsa una vez para continuar.`);return;}
          await load(mode.value==='LOCAL_MODEL'?(stage.status==='MISSING'?'Propuesta Ollama registrada como DRAFT. Revisa contenido, calidad y procedencia antes del diff.':'Revisión humana de propuesta local guardada; plan previo invalidado.') : devpilot?(stage.status==='MISSING'?'Propuesta completa generada como DRAFT. Revísala; source todavía no fue mutado.':'Revisión del Owner guardada como DRAFT gobernado. Cualquier plan anterior quedó invalidado.'):'DRAFT persistido server-side; source todavía no fue mutado.');
        }catch(e){await renderGovernedError(feedback,e);}
        finally{setDraftBusy(false);}
      });
      const alternative=button('Crear alternativa mejorada con modelo local',async()=>{
        if(draftBusy)return;
        if(!modelInput.value){setFeedback(feedback,'block','Selecciona un modelo instalado.');return;}
        if(textarea.value!==String(stage.draft_content??'')){
          setFeedback(feedback,'block','Hay cambios sin guardar en el Markdown. Guarda la revisión humana antes de generar una alternativa.');return;
        }
        if(!window.confirm(stage.stage_id==='requirements'?'Se conservará el DRAFT anterior. DevPilot generará automáticamente las unidades pendientes, con un máximo finito de 13 solicitudes y sin reintentos ante BLOCK. Mantén abierta esta pestaña. ¿Iniciar o reanudar?':'Se conservará el candidato Markdown original. Se solicitará una alternativa con el modelo seleccionado, sin aprobar ni escribir el documento FROZEN. ¿Continuar?'))return;
        setDraftBusy(true,true);
        setFeedback(feedback,'loading',stage.stage_id==='requirements'?'Generación segmentada automática en curso. Checkpoints persistentes; no cerrar ni recargar la página.':'Ollama genera una alternativa Markdown. La versión anterior permanece inmutable…');
        try{
          if(!await ensureLiveHumanSession(feedback))return;
          if(stage.stage_id==='requirements'){
            await runRequirementsSequence(modelInput.value.trim());
          }else{
            const result=await client().preCodeDraft(stage.stage_id,{mode:'LOCAL_MODEL',content:'',semantic_model:null,model:modelInput.value.trim()});
            if(!result.ok)throw new Error(formatFindings(result));
            await load('Alternativa nueva conservada como DRAFT Markdown. Revisa las diferencias antes de aprobar; el original sigue inmutable.');
          }
        }catch(error){
          nearButtonStatus.textContent='BLOCK: secuencia detenida. Checkpoints anteriores conservados; no se hicieron reintentos.';
          await renderGovernedError(feedback,error);
        }
        finally{setDraftBusy(false);}
      });
      alternative.hidden=!(mode.value==='LOCAL_MODEL'&&stage.status==='DRAFT'&&['product-vision','scope','requirements'].includes(stage.stage_id));
      if(!correlationOK){alternative.disabled=true;save.disabled=true;}
      setModelOptions([]);
      const updateSaveLabel=()=>{alternative.hidden=!(mode.value==='LOCAL_MODEL'&&stage.status==='DRAFT'&&['product-vision','scope','requirements'].includes(stage.stage_id));modelPanel.hidden=mode.value!=='LOCAL_MODEL';file.hidden=mode.value!=='IMPORT';fileLabel.hidden=file.hidden;textarea.placeholder=mode.value==='DEVPL_MOCK'?(stage.status==='MISSING'?'Pulsa “Generar propuesta con DevPilot”. DevPilot mostrará primero el DRAFT completo.':'Revisa y edita directamente la propuesta completa si lo necesitas.'):'Escribe o pega aquí el contenido del artefacto. No incluyas secretos.';save.textContent=mode.value==='DEVPL_MOCK'?(stage.status==='MISSING'?'Generar propuesta con DevPilot':'Guardar revisión del Owner'):mode.value==='LOCAL_MODEL'&&stage.status==='MISSING'?'Generar DRAFT con modelo local':'Guardar DRAFT';save.disabled=!correlationOK || (mode.value==='LOCAL_MODEL'&&stage.status==='MISSING'&&!modelInput.value);if(!correlationOK)alternative.disabled=true;};
      mode.addEventListener('change',()=>{updateSaveLabel();if(mode.value==='LOCAL_MODEL')void loadInstalledModels();});
      if(mode.value==='LOCAL_MODEL')void loadInstalledModels();
      file.addEventListener('change',async()=>{ const selected=file.files?.[0]; if(selected) textarea.value=await selected.text(); });
      const review=button('Validar y preparar diff',async()=>{
        if(!correlationOK){setFeedback(feedback,'block','El editor no coincide con el recibo de candidato. No se solicitó revisión.');return;}
        setFeedback(feedback,'loading','Ejecutando validadores y plan inmutable…');
        if(!await ensureLiveHumanSession(feedback)) return; try{ const r=await client().preCodeReview(stage.stage_id); if(!r.ok){ setFeedback(feedback,'block',formatFindings(r)); return; } await load('Validación PASS; plan/diff inmutable listo para approval.'); }catch(e){await renderGovernedError(feedback,e);}
      });
      review.disabled=!correlationOK || stage.status==='MISSING' || Boolean(inbox);
      if(inbox) review.title='Resuelve y guarda las decisiones pendientes antes de validar el DRAFT.';
      form.append(modeLabel,mode,modelPanel,fileLabel,file,textLabel,textarea);
      if(inbox){
        form.append(inbox.element);
        form.append(button('Guardar decisiones y regenerar propuesta',async()=>{
          setFeedback(feedback,'loading','Guardando únicamente las decisiones pendientes y regenerando la propuesta afectada…');
          if(!await ensureLiveHumanSession(feedback)) return;
          try{const r=await client().preCodeDraft(stage.stage_id,{mode:'DEVPL_MOCK',content:'',semantic_model:inbox.read()});if(!r.ok) throw new Error(formatFindings(r));await load('Decisiones guardadas. DevPilot regeneró el DRAFT; revisa el documento completo antes de validar.');}catch(e){await renderGovernedError(feedback,e);}
        }));
      }
      if(inbox){ save.disabled=true; save.title='Primero guarda las decisiones pendientes y revisa el DRAFT regenerado.'; }
      const regenerate=button('Regenerar propuesta desde decisiones guardadas',async()=>{
        if(!await ensureLiveHumanSession(feedback))return;
        const accepted=window.confirm('DevPilot reemplazará el DRAFT actual por una nueva propuesta determinística usando las decisiones semánticas ya guardadas. El source del proyecto no cambia hasta approval/apply. ¿Continuar?');
        if(!accepted){setFeedback(feedback,'info','Regeneración cancelada; el DRAFT actual se conserva.');return;}
        setFeedback(feedback,'loading','Regenerando DRAFT desde el Semantic Model y decisiones gobernadas…');
        try{const r=await client().preCodeDraft(stage.stage_id,{mode:'DEVPL_MOCK',content:'',semantic_model:null});if(!r.ok)throw new Error(formatFindings(r));await load('DRAFT regenerado desde las decisiones guardadas. Revísalo antes de validar.');}catch(e){await renderGovernedError(feedback,e);}
      });
      const c01SemanticStage=stage.order<=3;
      regenerate.hidden=!(c01SemanticStage && stage.status==='DRAFT' && mode.value==='DEVPL_MOCK' && !inbox);
      mode.addEventListener('change',()=>{regenerate.hidden=!(c01SemanticStage && stage.status==='DRAFT' && mode.value==='DEVPL_MOCK' && !inbox);});
      form.append(save,alternative,nearButtonStatus,segmentMeterBox,regenerate,review); section.append(form);
      if(preCode.semantic_model)section.append(semanticAdvancedDetails(preCode.semantic_model));
      if(stage.derivation){
        const d=stage.derivation as typeof stage.derivation & {owner_revision?: {candidate_path?:string};candidate_path?:string}; const provenance=document.createElement('div'); provenance.className='notice notice--info'; provenance.dataset.preCodeDerivation='true';
        const rag=Boolean(d.rag_execution_used);
        provenance.textContent=`Candidato Markdown · archivo ${d.owner_revision?.candidate_path??d.candidate_path??"DRAFT"} · provider ${d.provider??'devpilot-local'} · modelo ${d.model??'deterministic-semantic-model-template-v3'} · RAG local ${rag?'sí':'no'}${d.rag_grounding_status?` (${d.rag_grounding_status})`:''} · LLM ejecutado ${d.model_execution_used?'sí':'no'} · agente ejecutado ${d.agent_execution_used?'sí':'no'} · red ${d.network_used?'sí':'no'} · API externa ${d.external_api_used?'sí':'no'} · costo USD ${String(d.cost_usd??0)} · edición Owner ${d.owner_edited?'sí':'no'} · revisión humana obligatoria.`;
        section.append(provenance);
        if(stage.stage_id==='architecture' && Array.isArray(d.decision_summary) && d.decision_summary.length){
          const decisions=document.createElement('section'); decisions.className='pre-code-architecture-decisions'; decisions.dataset.architectureDecisionSummary='true';
          const dh=document.createElement('h4'); dh.textContent='Decisiones incluidas en Architecture';
          const dc=document.createElement('p'); dc.textContent='Estas decisiones forman parte del DRAFT. Aprobar el plan/diff de Architecture aprueba también estas decisiones; puedes editar o rechazar el DRAFT antes del approval.';
          const ul=document.createElement('ul');
          for(const item of d.decision_summary){const li=document.createElement('li');li.textContent=`${item.adr_id} · ${item.title}: ${item.decision}${item.selection_basis?` · base ${item.selection_basis}`:''}`;ul.append(li);}
          decisions.append(dh,dc,ul); section.append(decisions);
        }
      }
      if(stage.findings?.length){ const findings=document.createElement('ul'); findings.className='pre-code-findings'; for(const row of stage.findings){const li=document.createElement('li'); li.textContent=`${String(row['id']??'finding')}: ${String(row['message']??'')}`; findings.append(li);} section.append(findings); }
    }

    if(stage.status==='APPROVAL_REQUIRED'){
      const plan=document.createElement('div'); plan.className='pre-code-plan'; plan.dataset.planId=stage.plan_id??''; plan.dataset.planHash=stage.plan_hash??'';
      const text=document.createElement('p'); text.textContent=`Plan ${stage.plan_id ?? 'n/a'} listo. Approval requerido antes de apply.`; plan.append(text);
      const comparison=document.createElement('p'); comparison.className='notice notice--info'; const isNew=!stage.base_sha256 || /^0{64}$/.test(stage.base_sha256); comparison.textContent=isNew?'Comparando: baseline vacío → DRAFT propuesto. Archivo nuevo; todo el diff representa contenido a crear.':'Comparando: source actual → DRAFT propuesto. El approval autoriza exactamente este preimage y esta propuesta.'; plan.append(comparison);
      const meta=document.createElement('dl'); meta.className='pre-code-plan__meta';
      for(const [label,value] of [['Plan hash',stage.plan_hash??'n/a'],['Base SHA-256',stage.base_sha256??'n/a'],['Proposed SHA-256',stage.content_sha256??'n/a'],['Diff SHA-256',stage.diff?.sha256??'n/a'],['Cambio',`${stage.diff?.additions??0} adiciones · ${stage.diff?.deletions??0} eliminaciones · ${stage.diff?.hunks??0} hunks`]]){
        const dt=document.createElement('dt'); dt.textContent=label; const dd=document.createElement('dd'); dd.textContent=String(value); meta.append(dt,dd);
      }
      plan.append(meta);
      if(stage.diff?.content){ const diff=document.createElement('pre'); diff.className='pre-code-plan__diff'; diff.dataset.diffSha256=stage.diff.sha256; diff.textContent=stage.diff.content; plan.append(diff); const warning=document.createElement('p'); warning.className='muted'; warning.textContent='Si cambia el DRAFT o una decisión semántica, este plan/diff deja de representar el cambio aprobado y debe generarse de nuevo.'; plan.append(warning); }
      if((stage.mode==='DEVPL_MOCK'||(stage.mode as string)==='LOCAL_MODEL') && stage.draft_content){
        const edit=document.createElement('details'); edit.className='pre-code-plan-edit';
        const es=document.createElement('summary'); es.textContent='Editar propuesta antes de aprobar';
        const ep=document.createElement('p'); ep.className='muted'; ep.textContent='Guardar una edición invalida este plan/diff y obliga a validar de nuevo.';
        const et=document.createElement('textarea'); et.rows=18; et.value=stage.draft_content; et.setAttribute('aria-label','Editar DRAFT antes de approval');
        edit.append(es,ep,et,button('Guardar edición e invalidar plan',async()=>{if(!await ensureLiveHumanSession(feedback))return;try{const r=await client().preCodeDraft(stage.stage_id,{mode:stage.mode as 'DEVPL_MOCK'|'LOCAL_MODEL',content:et.value,semantic_model:null});if(!r.ok)throw new Error(formatFindings(r));await load('Edición guardada. El plan anterior fue invalidado; vuelve a validar y revisar el nuevo diff.');}catch(e){await renderGovernedError(feedback,e);}}));
        plan.append(edit);
      }
      if(!stage.approval_id){
        plan.append(button('Solicitar approval',async()=>{ if(!await ensureLiveHumanSession(feedback)) return; try{const r=await client().preCodeApprovalRequest(stage.stage_id); if(!r.ok) throw new Error(formatFindings(r)); const approvalId=String(((r.data as Record<string,unknown>)?.['pre_code'] as Record<string,unknown>|undefined)?.['approval_id']??''); if(!approvalId) throw new Error('La API no devolvió Approval ID.'); armApprovalCenterArtifactReviewHandoff(session,approvalId); await load(`Approval solicitado: ${approvalId}. Abre Approval Center dirigido y decide con un rol autorizado.`);}catch(e){await renderGovernedError(feedback,e);} }));
      } else {
        const approvalId=String(stage.approval_id); armApprovalCenterArtifactReviewHandoff(session,approvalId);
        const a=document.createElement('p'); a.textContent=`Approval: ${approvalId}`; plan.append(a);
        const open=document.createElement('button'); open.type='button'; open.className='button-link'; open.textContent='Abrir Approval Center dirigido ↗'; open.addEventListener('click',()=>{armApprovalCenterArtifactReviewHandoff(session,approvalId); globalThis.open(`/approvals?handoff=artifact-review&approval_id=${encodeURIComponent(approvalId)}`,'_blank','noopener,noreferrer');}); plan.append(open);
        plan.append(button('Verificar approval y aplicar',async()=>{ if(!await ensureLiveHumanSession(feedback)) return; try{const shown=await client().showApproval(approvalId); const status=String((shown.data as Record<string,unknown>)?.['approval'] && ((shown.data as Record<string,unknown>)['approval'] as Record<string,unknown>)['status'] || ''); if(status!=='approved'){setFeedback(feedback,'block',`Approval todavía está ${status||'pending'}. No se aplica source.`);return;} const r=await client().preCodeApply(stage.stage_id); if(!r.ok) throw new Error(formatFindings(r)); await load('Apply aprobado completado. Freeze es el siguiente gate.');}catch(e){await renderGovernedError(feedback,e);} }));
      }
      section.append(plan);
      if(preCode.semantic_model)section.append(semanticAdvancedDetails(preCode.semantic_model));
    }
    if(stage.status==='APPLIED'){
      const reviewId=String(stage.review_id??''), executionId=String(stage.execution_id??'');
      const freeze=button('Freeze y avanzar',async()=>{ if(!await ensureLiveHumanSession(feedback)) return; try{const r=await client().preCodeFreeze(stage.stage_id,{review_id:reviewId,execution_id:executionId}); if(!r.ok) throw new Error(formatFindings(r)); await load(`${stage.label} FROZEN; siguiente etapa habilitada.`);}catch(e){await renderGovernedError(feedback,e);} });
      freeze.disabled=!reviewId||!executionId; section.append(freeze);
    }
    return section;
  }

  return host;
}
function stageStepper(stages: PreCodeWizardStage[], currentId: string|null|undefined, onBlockedAttempt: (stage: PreCodeWizardStage)=>void): HTMLElement {
  const nav=document.createElement('ol'); nav.className='pre-code-stepper'; nav.setAttribute('aria-label','Etapas obligatorias de pre-code');
  const current=stages.find((row)=>row.stage_id===currentId);
  for(const stage of stages){
    const li=document.createElement('li'); li.dataset.status=stage.status; li.dataset.current=stage.stage_id===currentId?'true':'false';
    const label=document.createElement('span'); label.textContent=`${stage.order}. ${stage.label} · ${stage.status}`; li.append(label);
    if(current && stage.order>current.order && stage.status!=='FROZEN'){
      const probe=document.createElement('button'); probe.type='button'; probe.className='button-link pre-code-stepper__skip-probe'; probe.textContent='Intentar abrir'; probe.setAttribute('aria-label',`Intentar abrir ${stage.label} antes de completar la etapa actual`); probe.addEventListener('click',()=>onBlockedAttempt(stage)); li.append(probe);
    }
    nav.append(li);
  }
  return nav;
}
function button(label:string,handler:()=>Promise<void>):HTMLButtonElement{const b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',()=>void handler());return b;}
function statusBox(kind:string,text:string):HTMLElement{const div=document.createElement('div');div.className=`notice notice--${kind}`;div.dataset.status=kind.toUpperCase();div.textContent=text;return div;}
function setFeedback(host:HTMLElement,kind:string,text:string):void{host.replaceChildren(statusBox(kind,text));}
function errorText(error:unknown):string{return error instanceof Error?error.message:'Error local no clasificado.';}
function formatFindings(response:DevPilotApplicationResponse<unknown>):string{const rows=(response.findings??[]).map((x)=>`${x.id}: ${x.message}`);return rows.length?rows.join(' · '):response.message;}
