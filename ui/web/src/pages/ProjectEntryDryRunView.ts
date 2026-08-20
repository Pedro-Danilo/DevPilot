import { activateProjectJourney, armApprovalCenterEntryHandoff, clearApprovalCenterEntryHandoff, clearProjectEntryResumeState, DevPilotApiClient, DevPilotApiError, readProjectEntryResumeState, saveProjectEntryResumeState } from '../api/client';
import type { AuthSessionContext } from '../api/types';

const PROJECT_ENTRY_ROUTE_ID='ui.project-entry-dry-run';

type EntryMode = 'CREATE_NEW' | 'OPEN_EXISTING' | 'IMPORT_GIT';

interface ProjectEntryViewOptions {
  session: AuthSessionContext;
  initialMode?: EntryMode;
}

const PROJECT_ID_PATTERN = /^[a-z0-9][a-z0-9_-]{2,63}$/;
const MODE_GUIDANCE: Record<EntryMode, string> = {
  CREATE_NEW: 'Crea un workspace nuevo dentro de una raíz autorizada. El target debe estar libre antes de execute.',
  OPEN_EXISTING: 'Abre un Git worktree existente. DevPilot conserva el source y registra metadata de forma gobernada.',
  IMPORT_GIT: 'Importa un repositorio Git local hacia un target nuevo. Remote Git permanece disabled-by-default.',
};

export function renderProjectEntryDryRunView(options: ProjectEntryViewOptions): HTMLElement {
  const { session } = options;
  const canExecute = session.principal.roles.includes('owner');
  const acceptanceEnabled = Boolean(import.meta.env.DEV) && String(import.meta.env.VITE_GSDLC03E_BROWSER_ACCEPTANCE ?? '') === '1';

  const root=document.createElement('section');root.dataset.routeId=PROJECT_ENTRY_ROUTE_ID; root.className='project-entry-workbench'; root.dataset.gsdlc03c='dry-run-workbench'; root.dataset.gsdlc03d='approval-bound-bootstrap'; root.dataset.gsdlc03e='guided-browser-journey';
  const intro=document.createElement('div'); intro.className='project-entry-hero';
  const eyebrow=document.createElement('p'); eyebrow.className='project-entry-eyebrow'; eyebrow.textContent='GSDLC-03-E · browser-complete project entry';
  const h=document.createElement('h2'); h.textContent='Crear / Abrir / Importar con plan, approval y recuperación';
  const p=document.createElement('p'); p.textContent='El navegador guía el journey completo: parámetros → dry-run → preimage → approval → execute → verificación → Estado del proyecto. PowerShell no forma parte del flujo normal del usuario.';
  intro.append(eyebrow,h,p);

  const form=document.createElement('form'); form.className='project-entry-form'; form.noValidate=true;
  const mode=selectField('Modo de entrada','entry-mode',[['CREATE_NEW','Crear nuevo'],['OPEN_EXISTING','Abrir existente'],['IMPORT_GIT','Importar Git']]);
  mode.select.value=options.initialMode ?? 'CREATE_NEW';
  const projectId=inputField('Project ID','project-id','gsdlc03e-demo'); const projectName=inputField('Nombre','project-name','GSDLC 03-E demo'); const target=inputField('Ruta destino / workspace *','target-root','');
  const sourceKind=selectField('Tipo de origen Git','git-source-kind',[['local-path','Repositorio local'],['remote-url','URL remota · ejecución deshabilitada']]);
  const source=inputField('Ruta / URL de origen Git','git-source-location','');
  sourceKind.wrapper.classList.add('project-entry-import-only'); source.wrapper.classList.add('project-entry-import-only');
  const grid=document.createElement('div'); grid.className='project-entry-form-grid'; grid.append(mode.wrapper,projectId.wrapper,projectName.wrapper,target.wrapper,sourceKind.wrapper,source.wrapper);
  const modeHint=document.createElement('p'); modeHint.className='project-entry-mode-hint'; modeHint.setAttribute('role','note');
  const hint=document.createElement('p'); hint.className='project-entry-hint'; hint.textContent='Remote Git y dependency network permanecen disabled-by-default. El backend revalida PathGuard, RBAC, approval, plan y preimage inmediatamente antes de escribir.';
  const buttons=document.createElement('div'); buttons.className='project-entry-actions';
  const dry=document.createElement('button'); dry.type='submit'; dry.textContent='Generar dry-run';
  const revalidate=document.createElement('button'); revalidate.type='button'; revalidate.textContent='Revalidar preimage'; revalidate.disabled=true;
  buttons.append(dry,revalidate); form.append(grid,modeHint,hint,buttons);

  const status=document.createElement('div'); status.className='project-entry-status'; status.setAttribute('role','status'); status.setAttribute('aria-live','polite');
  const result=document.createElement('div'); result.className='project-entry-result'; result.dataset.state='empty';

  const execution=document.createElement('section'); execution.className='project-entry-execution-panel'; execution.dataset.state='locked';
  const execHeading=document.createElement('div'); execHeading.className='project-entry-execution-heading';
  const execTitle=document.createElement('h3'); execTitle.textContent='Ejecución gobernada';
  const execBadge=document.createElement('span'); execBadge.className='project-entry-execution-badge'; execBadge.textContent='LOCKED · requiere revalidación + approval';
  execHeading.append(execTitle,execBadge);
  const execHelp=document.createElement('p'); execHelp.textContent='La mutación requiere sesión humana owner y una aprobación vinculada al mismo plan/preimage. Cualquier cambio de parámetros invalida el estado previo.';
  const roleNotice=document.createElement('p'); roleNotice.className='project-entry-role-notice'; roleNotice.setAttribute('role','note'); roleNotice.textContent=canExecute?'Rol owner efectivo: approval/execute puede habilitarse después de revalidación.':`Rol efectivo: ${session.principal.roles.join(', ')||'sin rol'}. Dry-run/revisión puede estar disponible, pero approval/execute bootstrap requiere owner.`;
  const approvalId=inputField('Approval ID','bootstrap-approval-id',''); approvalId.input.readOnly=true; approvalId.input.placeholder='Se completa al solicitar approval';
  const approvalReason=inputField('Motivo de aprobación','bootstrap-approval-reason','Materializar el plan GSDLC-03-E revisado');
  const execActions=document.createElement('div'); execActions.className='project-entry-actions';
  const requestApproval=document.createElement('button'); requestApproval.type='button'; requestApproval.textContent='Solicitar approval'; requestApproval.disabled=true;
  const verifyApproval=document.createElement('button'); verifyApproval.type='button'; verifyApproval.textContent='Verificar approval'; verifyApproval.disabled=true; verifyApproval.className='button-secondary';
  const executePlan=document.createElement('button'); executePlan.type='button'; executePlan.textContent='Ejecutar plan aprobado'; executePlan.disabled=true;
  const approvalLink=document.createElement('a'); approvalLink.href='/approvals'; approvalLink.target='_blank'; approvalLink.rel='noopener'; approvalLink.textContent='Abrir Approval Center ↗'; approvalLink.hidden=true;
  execActions.append(requestApproval,verifyApproval,executePlan,approvalLink);
  const execStatus=document.createElement('div'); execStatus.className='project-entry-status'; execStatus.setAttribute('role','status'); execStatus.setAttribute('aria-live','polite');
  const execResult=document.createElement('div'); execResult.className='project-entry-result'; execResult.dataset.state='empty';

  let faultStage: HTMLSelectElement | null = null;
  if(acceptanceEnabled){
    const acceptance=document.createElement('details'); acceptance.className='project-entry-acceptance-controls';
    const summary=document.createElement('summary'); summary.textContent='Acceptance harness · rollback controlado';
    const note=document.createElement('p'); note.textContent='Solo visible en Vite DEV con VITE_GSDLC03E_BROWSER_ACCEPTANCE=1. El API además exige DEVPILOT_GSDLC03D_FAULT_INJECTION=1.';
    const field=selectField('Fault stage de aceptación','acceptance-fault-stage',[['','Sin fault injection'],['git','Git · verificar rollback'],['venv','Venv · verificar rollback']]);
    faultStage=field.select; acceptance.append(summary,note,field.wrapper); execution.append(acceptance);
  }
  execution.prepend(execHeading,execHelp,roleNotice,approvalReason.wrapper,approvalId.wrapper,execActions,execStatus,execResult);

  let lastIntake:Record<string,unknown>|null=null, lastDryRun:Record<string,unknown>|null=null, lastBootstrapPlan:Record<string,unknown>|null=null, lastPlan='', lastPreimage='', revalidated=false, approvalVerified=false, dirtySincePlan=false;
  const client=new DevPilotApiClient();

  const lockExecution=(message='LOCKED · requiere revalidación + approval', preserveApproval=false)=>{revalidated=false;approvalVerified=false;requestApproval.disabled=true;verifyApproval.disabled=true;executePlan.disabled=true;if(!preserveApproval){approvalId.input.value='';approvalLink.hidden=true;approvalLink.href='/approvals';}else if(approvalId.input.value.trim()){approvalLink.hidden=false;}execBadge.textContent=message;execution.dataset.state='locked';execStatus.textContent='';execResult.replaceChildren();execResult.dataset.state='empty';};
  const clearPersistedEntry=()=>{clearProjectEntryResumeState();clearApprovalCenterEntryHandoff();};
  const persistEntry=(approvalOverride?:string)=>{if(!lastIntake||!lastDryRun||!lastBootstrapPlan||!lastPlan||!lastPreimage)return;saveProjectEntryResumeState(session,{entry_mode:mode.select.value as EntryMode,intake:lastIntake,dry_run:lastDryRun,bootstrap_plan:lastBootstrapPlan,plan_hash:lastPlan,preimage_hash:lastPreimage,approval_id:(approvalOverride ?? approvalId.input.value.trim()) || undefined});};
  const invalidatePlan=()=>{if(lastPlan||lastPreimage||revalidated||approvalId.input.value){dirtySincePlan=true;lastIntake=null;lastDryRun=null;lastBootstrapPlan=null;lastPlan='';lastPreimage='';revalidate.disabled=true;clearPersistedEntry();lockExecution('STALE · parámetros cambiaron; genera nuevo dry-run');status.textContent='STALE: los parámetros cambiaron. El plan/approval anterior quedó invalidado; genera un nuevo dry-run.';result.replaceChildren();result.dataset.state='empty';}};
  const syncMode=()=>{const isImport=mode.select.value==='IMPORT_GIT';sourceKind.wrapper.hidden=!isImport;source.wrapper.hidden=!isImport;sourceKind.select.disabled=!isImport;source.input.disabled=!isImport;modeHint.textContent=MODE_GUIDANCE[mode.select.value as EntryMode];invalidatePlan();};
  mode.select.addEventListener('change',syncMode);
  for(const input of [projectId.input,projectName.input,target.input,source.input]) input.addEventListener('input',invalidatePlan);
  sourceKind.select.addEventListener('change',invalidatePlan);
  syncMode();

  form.addEventListener('submit',async(ev)=>{
    ev.preventDefault();
    const projectIdValue=projectId.input.value.trim(), projectNameValue=projectName.input.value.trim(), targetValue=target.input.value.trim(), sourceValue=source.input.value.trim();
    if(!PROJECT_ID_PATTERN.test(projectIdValue)){status.textContent='BLOCK: Project ID debe usar 3-64 caracteres lowercase [a-z0-9_-] y comenzar por letra o número.';result.replaceChildren();result.dataset.state='error';projectId.input.focus();return;}
    if(!projectNameValue){status.textContent='BLOCK: Nombre es obligatorio.';result.replaceChildren();result.dataset.state='error';projectName.input.focus();return;}
    if(!targetValue){status.textContent='BLOCK: la Ruta destino / workspace es obligatoria y debe permanecer dentro de una raíz de workspace autorizada.';result.replaceChildren();result.dataset.state='error';target.input.focus();return;}
    if(mode.select.value==='IMPORT_GIT'&&!sourceValue){status.textContent='BLOCK: IMPORT_GIT requiere una Ruta / URL de origen Git.';result.replaceChildren();result.dataset.state='error';source.input.focus();return;}
    dirtySincePlan=false;status.textContent='Generando dry-run read-only…';result.replaceChildren();result.dataset.state='loading';dry.disabled=true;revalidate.disabled=true;lockExecution();
    try{
      const intake=buildIntake(mode.select.value as EntryMode,projectIdValue,projectNameValue,targetValue,sourceKind.select.value,sourceValue);lastIntake=intake;
      const response=await client.projectEntryDryRun({intake});const data=response.data as Record<string,unknown>;const preview=(data.dry_run??{}) as Record<string,unknown>;const bootstrapPlan=(data.bootstrap_plan??{}) as Record<string,unknown>;lastDryRun=preview;lastBootstrapPlan=bootstrapPlan;lastPlan=String(preview.plan_hash??'');lastPreimage=String(preview.preimage_hash??'');
      renderPreview(result,preview,bootstrapPlan);result.dataset.state='ready';status.textContent='PASS: dry-run generado sin writes ni network.';revalidate.disabled=!(lastPlan&&lastPreimage);persistEntry();
    }catch(error){lastIntake=null;lastDryRun=null;lastBootstrapPlan=null;lastPlan='';lastPreimage='';clearPersistedEntry();result.dataset.state='error';status.textContent=`BLOCK: ${error instanceof Error?error.message:'No fue posible generar el dry-run.'}`;}finally{dry.disabled=false;}
  });

  revalidate.addEventListener('click',async()=>{
    if(!lastIntake||!lastPlan||!lastPreimage)return;
    const preservedApproval=approvalId.input.value.trim();status.textContent='Revalidando preimage…';revalidate.disabled=true;lockExecution('LOCKED · revalidación server-side en curso',Boolean(preservedApproval));
    try{
      const response=await client.projectEntryRevalidate({intake:lastIntake,expected_plan_hash:lastPlan,expected_preimage_hash:lastPreimage});
      if(response.ok===true){revalidated=true;status.textContent=preservedApproval?'PASS: plan/preimage revalidados después de retomar el journey. Verifica ahora el approval en servidor.':'PASS: plan y preimage permanecen inmutables.';requestApproval.disabled=!canExecute||Boolean(preservedApproval);verifyApproval.disabled=!canExecute||!Boolean(preservedApproval);if(preservedApproval){approvalId.input.value=preservedApproval;approvalLink.href=`/approvals?handoff=project-entry&approval_id=${encodeURIComponent(preservedApproval)}`;approvalLink.hidden=false;execBadge.textContent='APPROVAL REGISTRADO · verificar servidor';execution.dataset.state='pending';persistEntry(preservedApproval);}else{execBadge.textContent=canExecute?'READY · puede solicitar approval':'PLAN READY · ejecución requiere owner';execution.dataset.state=canExecute?'ready':'role-blocked';persistEntry();}if(!canExecute)execStatus.textContent='BLOCK de rol visible: esta sesión no puede solicitar approval/execute bootstrap.';}
      else{clearPersistedEntry();status.textContent='BLOCK: el preimage cambió; genera un nuevo dry-run.';}
    }catch(error){status.textContent=`BLOCK: ${error instanceof Error?error.message:'Revalidación falló.'}`;}finally{revalidate.disabled=false;}
  });

  requestApproval.addEventListener('click',async()=>{
    if(!canExecute){execStatus.textContent='BLOCK: solo owner puede solicitar approval de bootstrap.';return;}
    if(!revalidated||!lastIntake||!lastPlan||!lastPreimage||dirtySincePlan)return;
    requestApproval.disabled=true;executePlan.disabled=true;execStatus.textContent='Solicitando approval exacto…';
    try{
      const response=await client.projectEntryRequestExecutionApproval({intake:lastIntake,expected_plan_hash:lastPlan,expected_preimage_hash:lastPreimage,reason:approvalReason.input.value.trim(),ttl_minutes:30});
      const data=response.data as Record<string,unknown>;const approval=(data.approval??{}) as Record<string,unknown>;const id=String(approval.approval_id??'');
      if(!id)throw new Error('La API no devolvió approval_id.');
      approvalId.input.value=id;
      armApprovalCenterEntryHandoff(session, mode.select.value as EntryMode, id);
      approvalLink.href=`/approvals?handoff=project-entry&approval_id=${encodeURIComponent(id)}`;
      approvalLink.hidden=false;persistEntry(id);
      execStatus.textContent=`PENDING: approval ${id} creado. Usa Abrir Approval Center, apruébalo y vuelve a esta pestaña para Verificar approval.`;execBadge.textContent='PENDING APPROVAL';execution.dataset.state='pending';verifyApproval.disabled=false;executePlan.disabled=true;
    }catch(error){execStatus.textContent=`BLOCK: ${error instanceof Error?error.message:'No fue posible solicitar approval.'}`;requestApproval.disabled=!canExecute;}
  });

  verifyApproval.addEventListener('click',async()=>{
    const id=approvalId.input.value.trim();if(!id){execStatus.textContent='BLOCK: Approval ID es obligatorio.';approvalId.input.focus();return;}
    verifyApproval.disabled=true;executePlan.disabled=true;execStatus.textContent='Verificando estado del approval…';
    try{
      const response=await client.showApproval(id);const data=response.data as Record<string,unknown>;const approval=(data.approval??data) as Record<string,unknown>;const approvalStatus=String(approval.status??'').toLowerCase();
      if(approvalStatus==='approved'){approvalVerified=true;execStatus.textContent='PASS: approval vigente y aprobado. Execute permanece sujeto a revalidación server-side de scope/policy.';execBadge.textContent='APPROVED · listo para execute';execution.dataset.state='approved';executePlan.disabled=!canExecute;}
      else{approvalVerified=false;execStatus.textContent=`PENDING/BLOCK: approval ${id} está en estado ${approvalStatus||'desconocido'}.`;execBadge.textContent='PENDING APPROVAL';execution.dataset.state='pending';verifyApproval.disabled=false;}
    }catch(error){approvalVerified=false;execStatus.textContent=`BLOCK: ${error instanceof Error?error.message:'No fue posible verificar approval.'}`;verifyApproval.disabled=false;}
  });

  executePlan.addEventListener('click',async()=>{
    if(!canExecute||!approvalVerified||dirtySincePlan||!revalidated||!lastIntake||!lastPlan||!lastPreimage)return;
    const id=approvalId.input.value.trim();if(!id){execStatus.textContent='BLOCK: Approval ID es obligatorio.';approvalId.input.focus();return;}
    executePlan.disabled=true;requestApproval.disabled=true;verifyApproval.disabled=true;execStatus.textContent='Ejecutando stages tipados dentro del workspace autorizado…';execResult.replaceChildren();execResult.dataset.state='loading';executePlan.dataset.busy='true';
    try{
      const response=await client.projectEntryExecute({intake:lastIntake,expected_plan_hash:lastPlan,expected_preimage_hash:lastPreimage,approval_id:id,dependency_mode:'defer-network',fault_stage:faultStage?.value||undefined});
      const data=response.data as Record<string,unknown>;const executionPayload=(data.execution??{}) as Record<string,unknown>;
      if(String(executionPayload.status??'').toUpperCase()!=='PASS')throw new Error('La API no confirmó execution.status=PASS; el contexto de proyecto permanece bloqueado.');
      const intakeContext=lastIntake as Record<string,unknown>;
      activateProjectJourney({ entry_mode:String(intakeContext.entry_mode) as EntryMode, project_id:String(intakeContext.project_id??''), target_root:String(intakeContext.target_root??'') });
      renderExecution(execResult,executionPayload);appendProjectStatusCta(execResult);execResult.dataset.state='ready';execStatus.textContent='PASS: bootstrap approval-bound completado y verificado. Contexto de proyecto habilitado; continúa al Estado del proyecto.';execBadge.textContent='PASS · workspace materializado';execution.dataset.state='pass';
    }catch(error){
      execResult.dataset.state='error';
      if(error instanceof DevPilotApiError&&error.status===408){execStatus.textContent=`UNKNOWN: ${error.message}`;execBadge.textContent='UNKNOWN · reconciliar antes de reintentar';execution.dataset.state='unknown';verifyApproval.disabled=true;executePlan.disabled=true;requestApproval.disabled=true;renderRecoveryError(execResult,error);}
      else{execStatus.textContent=`BLOCK: ${error instanceof Error?error.message:'La ejecución fue bloqueada o revertida.'}`;execBadge.textContent='BLOCKED · requiere nuevo dry-run/revalidación';execution.dataset.state='error';verifyApproval.disabled=false;executePlan.disabled=true;requestApproval.disabled=true;if(error instanceof DevPilotApiError)renderRecoveryError(execResult,error);}
    }finally{delete executePlan.dataset.busy;}
  });

  const resumeState=readProjectEntryResumeState(session, mode.select.value as EntryMode);
  if(resumeState){
    mode.select.value=resumeState.entry_mode;syncMode();
    const intake=resumeState.intake as Record<string,unknown>;
    projectId.input.value=String(intake.project_id??'');projectName.input.value=String(intake.project_name??'');target.input.value=String(intake.target_root??'');
    const git=(intake.git_source??{}) as Record<string,unknown>;sourceKind.select.value=String(git.kind??'local-path');source.input.value=String(git.location??'');
    sourceKind.wrapper.hidden=resumeState.entry_mode!=='IMPORT_GIT';source.wrapper.hidden=resumeState.entry_mode!=='IMPORT_GIT';sourceKind.select.disabled=resumeState.entry_mode!=='IMPORT_GIT';source.input.disabled=resumeState.entry_mode!=='IMPORT_GIT';modeHint.textContent=MODE_GUIDANCE[resumeState.entry_mode];
    lastIntake=resumeState.intake;lastDryRun=resumeState.dry_run;lastBootstrapPlan=resumeState.bootstrap_plan;lastPlan=resumeState.plan_hash;lastPreimage=resumeState.preimage_hash;dirtySincePlan=false;revalidated=false;approvalVerified=false;
    renderPreview(result,resumeState.dry_run,resumeState.bootstrap_plan);result.dataset.state='ready';revalidate.disabled=false;requestApproval.disabled=true;verifyApproval.disabled=true;executePlan.disabled=true;
    if(resumeState.approval_id){approvalId.input.value=resumeState.approval_id;approvalLink.href=`/approvals?handoff=project-entry&approval_id=${encodeURIComponent(resumeState.approval_id)}`;approvalLink.hidden=false;execBadge.textContent='RESUMED APPROVAL · revalidación requerida';execution.dataset.state='pending';}
    else{execBadge.textContent='RESUMED PLAN · revalidación requerida';execution.dataset.state='locked';}
    status.textContent='RESUMED: plan/preimage restaurados desde sessionStorage de esta pestaña. Por seguridad, pulse Revalidar preimage antes de verificar approval o ejecutar.';
  }

  const noExecute=document.createElement('div');noExecute.className='project-entry-no-execute';noExecute.textContent='Fail-closed: execute requiere plan vigente, revalidación exacta, human-session/RBAC owner, approval y policy PASS. Cambiar cualquier parámetro invalida el plan/approval.';
  root.append(intro,form,status,noExecute,result,execution);return root;
}

function buildIntake(mode:EntryMode,id:string,name:string,target:string,sourceKind:string,source:string):Record<string,unknown>{const intake:Record<string,unknown>={schema_id:'SCHEMA-DEVPL-GSDLC-03-A-PROJECT-INTAKE-V1',schema_version:'1.0',project_id:id.trim(),project_name:name.trim(),project_type:'agent-assisted-sdlc',entry_mode:mode,target_root:target.trim(),stack:{frontend:'react-typescript',backend:'fastapi-python',database:'sqlite'},standards:['MIPSoftware','MIASI'],provider:{mode:'none',provider_id:null},restrictions:{arbitrary_shell_allowed:false,silent_network_allowed:false,remote_git_execute_allowed:false}};if(mode==='IMPORT_GIT')intake.git_source={kind:sourceKind,location:source.trim()};return intake;}
function inputField(label:string,id:string,value:string){const wrapper=document.createElement('label');wrapper.className='project-entry-field';wrapper.htmlFor=id;const span=document.createElement('span');span.textContent=label;const input=document.createElement('input');input.id=id;input.value=value;input.autocomplete='off';input.required=true;wrapper.append(span,input);return{wrapper,input};}
function selectField(label:string,id:string,items:[string,string][]){const wrapper=document.createElement('label');wrapper.className='project-entry-field';wrapper.htmlFor=id;const span=document.createElement('span');span.textContent=label;const select=document.createElement('select');select.id=id;for(const[v,t]of items){const o=document.createElement('option');o.value=v;o.textContent=t;select.append(o);}wrapper.append(span,select);return{wrapper,select};}
function renderPreview(target:HTMLElement,dry:Record<string,unknown>,plan:Record<string,unknown>){const review=(dry.review??{}) as Record<string,unknown>;const approval=(dry.approval_preview??{}) as Record<string,unknown>;const safety=(dry.safety??{}) as Record<string,unknown>;const top=document.createElement('div');top.className='project-entry-summary-grid';for(const[label,value]of [['Modo',review.entry_mode],['Plan hash',dry.plan_hash],['Preimage hash',dry.preimage_hash],['Writes ejecutados',safety.writes_performed],['Network usada',safety.network_used],['Approval solicitado',safety.approval_requested]]){const c=document.createElement('div');c.className='project-entry-summary-card';const k=document.createElement('span');k.textContent=String(label);const v=document.createElement('strong');v.textContent=String(value??'—');c.append(k,v);top.append(c);}const details=document.createElement('div');details.className='project-entry-review-grid';details.append(jsonCard('Preview de aprobación',approval),jsonCard('Efectos declarados',{directories:plan.directories,files:plan.files,git_operations:plan.git_operations,venv:plan.venv,dependency_jobs:plan.dependency_jobs,workspace_registration:plan.workspace_registration,network:plan.network}),jsonCard('Preimage',dry.preimage));target.append(top,details);}
function renderExecution(target:HTMLElement,execution:Record<string,unknown>){const top=document.createElement('div');top.className='project-entry-summary-grid';const verification=(execution.verification??{}) as Record<string,unknown>;for(const[label,value]of [['Estado',execution.status],['Execution hash',execution.execution_hash],['Git clean',verification.git_clean],['Venv OK',verification.venv_ok],['Network usada',execution.network_used],['Writes fuera workspace',execution.writes_outside_workspace]]){const c=document.createElement('div');c.className='project-entry-summary-card';const k=document.createElement('span');k.textContent=String(label);const v=document.createElement('strong');v.textContent=String(value??'—');c.append(k,v);top.append(c);}target.append(top,jsonCard('Stages y rollback contract',{stages:execution.stages,rollback:execution.rollback,verification:execution.verification,dependency_mode:execution.dependency_mode}));}
function renderRecoveryError(target:HTMLElement,error:DevPilotApiError){const payload=(error.payload??{}) as Record<string,unknown>;const data=(payload.data??{}) as Record<string,unknown>;const execution=(data.execution??{}) as Record<string,unknown>;if(Object.keys(execution).length)target.append(jsonCard('Recovery / rollback evidence',execution));else target.append(jsonCard('Estado de recuperación',{state:error.status===408?'UNKNOWN':'BLOCK',action:error.status===408?'reconcile-before-retry':'nuevo dry-run/revalidación',finding:(payload.findings as unknown)??null}));}
function appendProjectStatusCta(target:HTMLElement){const card=document.createElement('article');card.className='project-entry-success-next';const title=document.createElement('h3');title.textContent='Workspace listo';const text=document.createElement('p');text.textContent='La transacción terminó PASS. Continúa al Estado del proyecto para revisar readiness y siguientes pasos.';const link=document.createElement('a');link.href='/project/status';link.className='button-link';link.textContent='Continuar a Estado del proyecto →';card.append(title,text,link);target.append(card);}
function jsonCard(title:string,payload:unknown){const card=document.createElement('article');card.className='project-entry-review-card';const h=document.createElement('h3');h.textContent=title;const pre=document.createElement('pre');pre.textContent=JSON.stringify(payload,null,2);card.append(h,pre);return card;}
