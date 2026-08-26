import { armApprovalCenterArtifactReviewHandoff, DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { AuthSessionContext, DevPilotApplicationResponse, PreCodeWizardProjection, PreCodeWizardStage, StepActionCard } from '../api/types';
import { renderStepActionAdvisor } from '../components/StepActionAdvisor';

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
      const text=error instanceof DevPilotApiError && error.status===0 ? 'API local no disponible. El wizard falla cerrado: ninguna acción mutante queda habilitada.' : error instanceof Error ? error.message : 'No fue posible cargar el wizard.';
      body.replaceChildren(statusBox('block',text));
    }
  }

  function render(preCode: PreCodeWizardProjection, message?: string): void {
    body.replaceChildren();
    const summary=document.createElement('section'); summary.className='panel pre-code-wizard__summary'; summary.dataset.status=preCode.status;
    const sh=document.createElement('h3'); sh.textContent=`Estado: ${preCode.status}`;
    const sp=document.createElement('p'); sp.textContent=`Readiness estricta del vertical slice: ${preCode.readiness.status} · ${preCode.readiness.mandatory_stages_frozen}/${preCode.readiness.mandatory_stages_total} etapas FROZEN.`;
    const note=document.createElement('p'); note.className='muted'; note.textContent='Este perfil strict corresponde al milestone guiado de 7 etapas y no reescribe el readiness histórico global.';
    const miasi=document.createElement('p'); miasi.className='muted'; miasi.dataset.miasiGate=preCode.miasi.gate_status; miasi.textContent=`MIASI: ${preCode.miasi.status} · gate ${preCode.miasi.gate_status} · riesgo ${preCode.miasi.risk_level}.`;
    summary.append(sh,sp,note,miasi);
    if(message){ const m=document.createElement('p'); m.className='notice notice--pass'; m.textContent=message; summary.append(m); }
    const skipFeedback=document.createElement('div'); skipFeedback.className='pre-code-stepper__feedback'; skipFeedback.setAttribute('aria-live','assertive');
    body.append(summary,stageStepper(preCode.stages,preCode.current_stage_id,(attempted)=>{
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
      body.append(renderStepActionAdvisor(
        {ui_state:preCode.advisor.status==='PASS'?'READY':'BLOCKED',workspace_id:preCode.workspace_id,current_step:stage.advisor_step,advisor:preCode.advisor,read_only:true,actor_neutral:false,server_authoritative:true,network_used:false,external_api_used:false,mutations_performed:false,source_mutations_performed:false},
        {onAction:(action)=>activateWizardAction(editor,stage,action)},
      ));
    }
    body.append(editor);
  }

  function activateWizardAction(editor: HTMLElement, stage: PreCodeWizardStage, action: StepActionCard): boolean {
    const feedback=editor.querySelector<HTMLElement>('[data-pre-code-stage-feedback]');
    const mode=editor.querySelector<HTMLSelectElement>('[data-pre-code-authoring-mode]');
    const textarea=editor.querySelector<HTMLTextAreaElement>('[data-pre-code-authoring-content]');
    const file=editor.querySelector<HTMLInputElement>('[data-pre-code-authoring-file]');
    const allowed=new Set(stage.allowed_modes ?? []);
    if(action.kind==='MANUAL' || action.kind==='PASTE'){
      if(!allowed.has('MANUAL') || !mode || !textarea){
        if(feedback) setFeedback(feedback,'block','BLOCK: la etapa actual no permite autoría MANUAL/PASTE en este vertical slice.');
        return true;
      }
      mode.value='MANUAL'; mode.dispatchEvent(new Event('change')); textarea.focus();
      if(feedback) setFeedback(feedback,'pass',action.kind==='PASTE'?'PASTE listo: pegue el contenido en el editor MANUAL gobernado y después guarde DRAFT.':'MANUAL listo: escriba o pegue contenido en el editor gobernado y después guarde DRAFT.');
      return true;
    }
    if(action.kind==='UPLOAD_IMPORT'){
      if(!allowed.has('IMPORT') || !mode || !file){
        return false;
      }
      mode.value='IMPORT'; mode.dispatchEvent(new Event('change')); file.disabled=false; file.focus();
      if(feedback) setFeedback(feedback,'pass','IMPORT listo: seleccione el archivo local permitido. La selección permanece dentro del wizard y no navega al Artifact Workbench general.');
      file.click();
      return true;
    }
    return false;
  }

  function stageEditor(stage: PreCodeWizardStage, preCode: PreCodeWizardProjection): HTMLElement {
    const section=document.createElement('section'); section.className='panel pre-code-stage'; section.dataset.stageId=stage.stage_id; section.dataset.stageStatus=stage.status;
    const heading=document.createElement('h3'); heading.textContent=`${stage.order}. ${stage.label}`;
    const path=document.createElement('p'); path.className='muted'; path.textContent=`Destino gobernado: ${stage.relative_path} · Estado ${stage.status}`;
    section.append(heading,path);
    const feedback=document.createElement('div'); feedback.dataset.preCodeStageFeedback='true'; feedback.setAttribute('role','status'); feedback.setAttribute('aria-live','polite'); section.append(feedback);

    if(['MISSING','DRAFT','FINDINGS'].includes(stage.status)){
      const form=document.createElement('div'); form.className='pre-code-stage__editor';
      const modeLabel=document.createElement('label'); modeLabel.textContent='Modo de autoría';
      const mode=document.createElement('select'); mode.dataset.preCodeAuthoringMode='true'; mode.setAttribute('aria-label','Modo de autoría');
      for(const value of stage.allowed_modes){ const option=document.createElement('option'); option.value=value; option.textContent=value==='MANUAL'?'Manual':'Importar archivo local'; mode.append(option); }
      const textLabel=document.createElement('label'); textLabel.htmlFor=`pre-code-${stage.stage_id}`; textLabel.textContent='Contenido Markdown';
      const textarea=document.createElement('textarea'); textarea.dataset.preCodeAuthoringContent='true'; textarea.id=`pre-code-${stage.stage_id}`; textarea.rows=18; textarea.spellcheck=false; textarea.placeholder='Escribe o pega aquí el contenido del artefacto. No incluyas secretos.';
      const fileLabel=document.createElement('label'); fileLabel.textContent='Archivo local para IMPORT';
      const file=document.createElement('input'); file.dataset.preCodeAuthoringFile='true'; file.type='file'; file.accept='.md,text/markdown,text/plain'; file.disabled=mode.value!=='IMPORT';
      mode.addEventListener('change',()=>{file.disabled=mode.value!=='IMPORT';});
      file.addEventListener('change',async()=>{ const selected=file.files?.[0]; if(selected) textarea.value=await selected.text(); });
      const save=button('Guardar DRAFT',async()=>{
        setFeedback(feedback,'loading','Guardando DRAFT sin escribir source…');
        if(!await ensureLiveHumanSession(feedback)) return; try{ const r=await client().preCodeDraft(stage.stage_id,{mode:mode.value as 'MANUAL'|'IMPORT',content:textarea.value}); if(!r.ok) throw new Error(formatFindings(r)); await load('DRAFT persistido server-side; source todavía no fue mutado.'); }catch(e){await renderGovernedError(feedback,e);}
      });
      const review=button('Validar y preparar diff',async()=>{
        setFeedback(feedback,'loading','Ejecutando validadores y plan inmutable…');
        if(!await ensureLiveHumanSession(feedback)) return; try{ const r=await client().preCodeReview(stage.stage_id); if(!r.ok){ setFeedback(feedback,'block',formatFindings(r)); await load(); return; } await load('Validación PASS; plan/diff inmutable listo para approval.'); }catch(e){await renderGovernedError(feedback,e);}
      });
      review.disabled=stage.status==='MISSING';
      form.append(modeLabel,mode,fileLabel,file,textLabel,textarea,save,review); section.append(form);
      if(stage.findings?.length){ const findings=document.createElement('ul'); findings.className='pre-code-findings'; for(const row of stage.findings){const li=document.createElement('li'); li.textContent=`${String(row['id']??'finding')}: ${String(row['message']??'')}`; findings.append(li);} section.append(findings); }
    }

    if(stage.status==='APPROVAL_REQUIRED'){
      const plan=document.createElement('div'); plan.className='pre-code-plan'; plan.dataset.planId=stage.plan_id??''; plan.dataset.planHash=stage.plan_hash??'';
      const text=document.createElement('p'); text.textContent=`Plan ${stage.plan_id ?? 'n/a'} listo. Approval requerido antes de apply.`; plan.append(text);
      const meta=document.createElement('dl'); meta.className='pre-code-plan__meta';
      for(const [label,value] of [['Plan hash',stage.plan_hash??'n/a'],['Diff SHA-256',stage.diff?.sha256??'n/a'],['Cambio',`${stage.diff?.additions??0} adiciones · ${stage.diff?.deletions??0} eliminaciones · ${stage.diff?.hunks??0} hunks`]]){
        const dt=document.createElement('dt'); dt.textContent=label; const dd=document.createElement('dd'); dd.textContent=String(value); meta.append(dt,dd);
      }
      plan.append(meta);
      if(stage.diff?.content){ const diff=document.createElement('pre'); diff.className='pre-code-plan__diff'; diff.dataset.diffSha256=stage.diff.sha256; diff.textContent=stage.diff.content; plan.append(diff); }
      if(!stage.approval_id){
        plan.append(button('Solicitar approval',async()=>{ if(!await ensureLiveHumanSession(feedback)) return; try{const r=await client().preCodeApprovalRequest(stage.stage_id); if(!r.ok) throw new Error(formatFindings(r)); const approvalId=String(((r.data as Record<string,unknown>)?.['pre_code'] as Record<string,unknown>|undefined)?.['approval_id']??''); if(!approvalId) throw new Error('La API no devolvió Approval ID.'); armApprovalCenterArtifactReviewHandoff(session,approvalId); await load(`Approval solicitado: ${approvalId}. Abre Approval Center dirigido y decide con un rol autorizado.`);}catch(e){await renderGovernedError(feedback,e);} }));
      } else {
        const approvalId=String(stage.approval_id); armApprovalCenterArtifactReviewHandoff(session,approvalId);
        const a=document.createElement('p'); a.textContent=`Approval: ${approvalId}`; plan.append(a);
        const open=document.createElement('button'); open.type='button'; open.className='button-link'; open.textContent='Abrir Approval Center dirigido ↗'; open.addEventListener('click',()=>{armApprovalCenterArtifactReviewHandoff(session,approvalId); globalThis.open(`/approvals?handoff=artifact-review&approval_id=${encodeURIComponent(approvalId)}`,'_blank','noopener,noreferrer');}); plan.append(open);
        plan.append(button('Verificar approval y aplicar',async()=>{ if(!await ensureLiveHumanSession(feedback)) return; try{const shown=await client().showApproval(approvalId); const status=String((shown.data as Record<string,unknown>)?.['approval'] && ((shown.data as Record<string,unknown>)['approval'] as Record<string,unknown>)['status'] || ''); if(status!=='approved'){setFeedback(feedback,'block',`Approval todavía está ${status||'pending'}. No se aplica source.`);return;} const r=await client().preCodeApply(stage.stage_id); if(!r.ok) throw new Error(formatFindings(r)); await load('Apply aprobado completado. Freeze es el siguiente gate.');}catch(e){await renderGovernedError(feedback,e);} }));
      }
      section.append(plan);
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
