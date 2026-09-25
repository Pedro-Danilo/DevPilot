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
    const summary=document.createElement('section'); summary.className='panel pre-code-wizard__summary'; summary.dataset.status=preCode.status;
    const currentStage=preCode.stages.find((row)=>row.stage_id===preCode.current_stage_id);
    const sh=document.createElement('h3'); sh.textContent='Preparación antes de programar';
    const sp=document.createElement('p'); sp.textContent=`${preCode.readiness.mandatory_stages_frozen}/${preCode.readiness.mandatory_stages_total} etapas listas. ${currentStage ? `Ahora: ${currentStage.label}.` : 'Revisa el estado antes de continuar.'}`;
    const technical=renderTechnicalDisclosure('Ver readiness y controles técnicos',`Estado: ${preCode.status} · Readiness estricta: ${preCode.readiness.status} · MIASI: ${preCode.miasi.status} · gate ${preCode.miasi.gate_status} · riesgo ${preCode.miasi.risk_level}.`);
    technical.classList.add('pre-code-wizard__technical');
    summary.append(sh,sp,technical);
    if(message){ const m=document.createElement('p'); m.className='notice notice--pass'; m.textContent=message; summary.append(m); }
    const currentStatus=currentStage?.status ?? 'UNKNOWN';
    const nextAction=currentStatus==='APPROVAL_REQUIRED'
      ? 'Revisa el diff y solicita/verifica el approval antes de aplicar.'
      : currentStatus==='APPLIED'
        ? 'Congela la etapa aplicada para habilitar la siguiente.'
        : currentStatus==='FROZEN'
          ? 'Continúa con la siguiente etapa disponible.'
          : 'Completa el contenido de la etapa actual y valida antes de pedir approval.';
    const guide=renderCriticalPathGuidance({
      eyebrow:'Pre-code · 7 etapas',
      title:currentStage ? `Etapa ${currentStage.order}: ${currentStage.label}` : 'Pre-code listo',
      summary:'Cada etapa conserva la misma secuencia gobernada: draft → validar/diff → approval → apply → freeze.',
      steps:preCode.stages.map((row)=>({label:row.label,state:row.status==='FROZEN'?'done':row.stage_id===preCode.current_stage_id?'current':'upcoming'})),
      nextAction,
      blocker:preCode.readiness.status==='PASS' ? 'Sin blocker de readiness para este milestone.' : 'La etapa actual debe completar sus gates antes de avanzar.',
      approvalEffect:'El approval autoriza únicamente el plan/diff actual; no salta validación ni freeze.',
      recoveryHref:'/recovery',
    });
    const skipFeedback=document.createElement('div'); skipFeedback.className='pre-code-stepper__feedback'; skipFeedback.setAttribute('aria-live','assertive');
    body.append(summary,guide,stageStepper(preCode.stages,preCode.current_stage_id,(attempted)=>{
      skipFeedback.replaceChildren(statusBox('block',`BLOCK: ${attempted.label} todavía no está habilitada. Completa y congela la etapa actual antes de avanzar; no se ejecutó ninguna mutación.`));
      skipFeedback.tabIndex=-1; skipFeedback.focus();
    }),skipFeedback);
    if(preCode.status==='PRE_CODE_READY'){
      const done=document.createElement('section'); done.className='panel pre-code-wizard__done'; done.dataset.preCodeReady='true';
      const dh=document.createElement('h3'); dh.textContent='PRE_CODE_READY';
      const dp=document.createElement('p'); dp.textContent='Las siete etapas obligatorias están FROZEN, sus hashes coinciden y los perfiles documentales están válidos.';
      done.append(dh,dp); body.append(done); return;
    }
    const stage=preCode.stages.find((row)=>row.stage_id===preCode.current_stage_id);
    if(!stage){ body.append(statusBox('block','BLOCK: no existe current stage determinístico.')); return; }
    const editor=stageEditor(stage,preCode);
    if(preCode.advisor){
      body.append(renderPreCodeActionGuide(stage,preCode,editor));
    }
    body.append(editor);
  }

  function renderPreCodeActionGuide(stage: PreCodeWizardStage, preCode: PreCodeWizardProjection, editor: HTMLElement): HTMLElement {
    const section=document.createElement('section'); section.className='panel pre-code-action-guide'; section.dataset.preCodeActionGuide='true';
    const title=document.createElement('h3'); title.textContent='Rutas para esta etapa';
    const copy=document.createElement('p'); copy.textContent='Las tarjetas muestran rutas y acciones disponibles; el selector Modo de autoría controla cómo se produce el DRAFT de esta etapa.';
    section.append(title,copy);
    const actions=preCode.advisor?.actions ?? [];

    const authoring=actionGroup('Cómo crear el DRAFT');
    if(stage.allowed_modes.includes('DEVPL_MOCK')){
      authoring.append(simpleActionCard('DevPilot local','Genera una propuesta determinística desde Project Context y artefactos FROZEN, sin red ni API externa.','RECOMENDADO',true,()=>selectAuthoringMode(editor,'DEVPL_MOCK')));
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
      const reasons=action?.disabled_reasons?.map((row)=>row.message).join(' · ') || 'No requerido para el baseline C-01.';
      advanced.append(simpleActionCard(label,action?.availability==='AVAILABLE'?(action.purpose || 'Ruta agentic gobernada.'):`${action?.purpose || 'Ruta agentic gobernada.'} ${reasons}`,action?.availability ?? 'UNAVAILABLE',false));
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

  function selectAuthoringMode(editor:HTMLElement,value:'DEVPL_MOCK'|'MANUAL'|'IMPORT'):void{
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
    const inbox=preCode.semantic_model ? semanticDecisionInbox(preCode.semantic_model,stage.stage_id) : null;

    if(['MISSING','DRAFT','FINDINGS'].includes(stage.status)){
      const form=document.createElement('div'); form.className='pre-code-stage__editor';
      const modeLabel=document.createElement('label'); modeLabel.textContent='Modo de autoría';
      const mode=document.createElement('select'); mode.dataset.preCodeAuthoringMode='true'; mode.setAttribute('aria-label','Modo de autoría');
      for(const value of stage.allowed_modes){ const option=document.createElement('option'); option.value=value; option.textContent=value==='DEVPL_MOCK'?'DevPilot · Mock local / sin API':value==='MANUAL'?'Manual':'Importar archivo local'; mode.append(option); }
      if(stage.mode && stage.allowed_modes.includes(stage.mode)) mode.value=stage.mode;
      const textLabel=document.createElement('label'); textLabel.htmlFor=`pre-code-${stage.stage_id}`; textLabel.textContent='Propuesta del artefacto';
      const textarea=document.createElement('textarea'); textarea.dataset.preCodeAuthoringContent='true'; textarea.id=`pre-code-${stage.stage_id}`; textarea.rows=20; textarea.spellcheck=false; textarea.value=stage.draft_content??'';
      textarea.placeholder=mode.value==='DEVPL_MOCK'?(stage.status==='MISSING'?'Pulsa “Generar propuesta con DevPilot”. DevPilot mostrará primero el DRAFT completo.':'Revisa y edita directamente la propuesta completa si lo necesitas.'):'Escribe o pega aquí el contenido del artefacto. No incluyas secretos.';
      const fileLabel=document.createElement('label'); fileLabel.textContent='Archivo local para IMPORT';
      const file=document.createElement('input'); file.dataset.preCodeAuthoringFile='true'; file.type='file'; file.accept='.md,text/markdown,text/plain'; file.hidden=mode.value!=='IMPORT'; fileLabel.hidden=file.hidden;
      const save=button(mode.value==='DEVPL_MOCK'?(stage.status==='MISSING'?'Generar propuesta con DevPilot':'Guardar revisión del Owner'):'Guardar DRAFT',async()=>{
        setFeedback(feedback,'loading',mode.value==='DEVPL_MOCK'?(stage.status==='MISSING'?'Generando propuesta completa desde el contexto gobernado; sin red ni API externa…':'Guardando revisión del Owner sin escribir source…'):'Guardando DRAFT sin escribir source…');
        if(!await ensureLiveHumanSession(feedback)) return;
        try{
          const devpilot=mode.value==='DEVPL_MOCK';
          const r=await client().preCodeDraft(stage.stage_id,{mode:mode.value as 'MANUAL'|'IMPORT'|'DEVPL_MOCK',content:devpilot?(stage.status==='MISSING'?'':textarea.value):textarea.value,semantic_model:null});
          if(!r.ok) throw new Error(formatFindings(r));
          await load(devpilot?(stage.status==='MISSING'?'Propuesta completa generada como DRAFT. Revísala; source todavía no fue mutado.':'Revisión del Owner guardada como DRAFT gobernado. Cualquier plan anterior quedó invalidado.'):'DRAFT persistido server-side; source todavía no fue mutado.');
        }catch(e){await renderGovernedError(feedback,e);}
      });
      const updateSaveLabel=()=>{file.hidden=mode.value!=='IMPORT';fileLabel.hidden=file.hidden;textarea.placeholder=mode.value==='DEVPL_MOCK'?(stage.status==='MISSING'?'Pulsa “Generar propuesta con DevPilot”. DevPilot mostrará primero el DRAFT completo.':'Revisa y edita directamente la propuesta completa si lo necesitas.'):'Escribe o pega aquí el contenido del artefacto. No incluyas secretos.';save.textContent=mode.value==='DEVPL_MOCK'?(stage.status==='MISSING'?'Generar propuesta con DevPilot':'Guardar revisión del Owner'):'Guardar DRAFT';};
      mode.addEventListener('change',updateSaveLabel);
      file.addEventListener('change',async()=>{ const selected=file.files?.[0]; if(selected) textarea.value=await selected.text(); });
      const review=button('Validar y preparar diff',async()=>{
        setFeedback(feedback,'loading','Ejecutando validadores y plan inmutable…');
        if(!await ensureLiveHumanSession(feedback)) return; try{ const r=await client().preCodeReview(stage.stage_id); if(!r.ok){ setFeedback(feedback,'block',formatFindings(r)); await load(); return; } await load('Validación PASS; plan/diff inmutable listo para approval.'); }catch(e){await renderGovernedError(feedback,e);}
      });
      review.disabled=stage.status==='MISSING';
      form.append(modeLabel,mode,fileLabel,file,textLabel,textarea);
      if(inbox){
        form.append(inbox.element);
        form.append(button('Guardar decisiones y regenerar propuesta',async()=>{
          setFeedback(feedback,'loading','Guardando únicamente las decisiones pendientes y regenerando la propuesta afectada…');
          if(!await ensureLiveHumanSession(feedback)) return;
          try{const r=await client().preCodeDraft(stage.stage_id,{mode:'DEVPL_MOCK',content:'',semantic_model:inbox.read()});if(!r.ok) throw new Error(formatFindings(r));await load('Decisiones guardadas. DevPilot regeneró el DRAFT; revisa el documento completo antes de validar.');}catch(e){await renderGovernedError(feedback,e);}
        }));
      }
      form.append(save,review); section.append(form);
      if(preCode.semantic_model)section.append(semanticAdvancedDetails(preCode.semantic_model));
      if(stage.derivation){
        const d=stage.derivation; const provenance=document.createElement('div'); provenance.className='notice notice--info'; provenance.dataset.preCodeDerivation='true';
        provenance.textContent=`Propuesta DevPilot local · provider ${d.provider??'devpilot-local'} · modelo ${d.model??'deterministic-semantic-model-template-v3'} · red ${d.network_used?'sí':'no'} · API externa ${d.external_api_used?'sí':'no'} · costo USD ${String(d.cost_usd??0)} · edición Owner ${d.owner_edited?'sí':'no'} · revisión humana obligatoria.`;
        section.append(provenance);
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
      if(stage.mode==='DEVPL_MOCK' && stage.draft_content){
        const edit=document.createElement('details'); edit.className='pre-code-plan-edit';
        const es=document.createElement('summary'); es.textContent='Editar propuesta antes de aprobar';
        const ep=document.createElement('p'); ep.className='muted'; ep.textContent='Guardar una edición invalida este plan/diff y obliga a validar de nuevo.';
        const et=document.createElement('textarea'); et.rows=18; et.value=stage.draft_content; et.setAttribute('aria-label','Editar DRAFT antes de approval');
        edit.append(es,ep,et,button('Guardar edición e invalidar plan',async()=>{if(!await ensureLiveHumanSession(feedback))return;try{const r=await client().preCodeDraft(stage.stage_id,{mode:'DEVPL_MOCK',content:et.value,semantic_model:null});if(!r.ok)throw new Error(formatFindings(r));await load('Edición guardada. El plan anterior fue invalidado; vuelve a validar y revisar el nuevo diff.');}catch(e){await renderGovernedError(feedback,e);}}));
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
