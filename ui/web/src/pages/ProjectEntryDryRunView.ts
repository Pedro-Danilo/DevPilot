import { DevPilotApiClient, DevPilotApiError } from '../api/client';

type EntryMode='CREATE_NEW'|'OPEN_EXISTING'|'IMPORT_GIT';

export function renderProjectEntryDryRunView(): HTMLElement {
  const root=document.createElement('section'); root.className='project-entry-workbench'; root.dataset.gsdlc03c='dry-run-workbench'; root.dataset.gsdlc03d='approval-bound-bootstrap';
  const intro=document.createElement('div'); intro.className='project-entry-hero';
  const eyebrow=document.createElement('p'); eyebrow.className='project-entry-eyebrow'; eyebrow.textContent='GSDLC-03-D · approval-bound execution';
  const h=document.createElement('h2'); h.textContent='Revisar, aprobar y materializar Create / Open / Import';
  const p=document.createElement('p'); p.textContent='Primero genera y revalida un plan exacto. La ejecución solo se habilita con una aprobación humana vinculada al mismo plan, preimage, actor y workspace.';
  intro.append(eyebrow,h,p);

  const form=document.createElement('form'); form.className='project-entry-form'; form.noValidate=true;
  const mode=selectField('Modo de entrada','entry-mode',[['CREATE_NEW','Crear nuevo'],['OPEN_EXISTING','Abrir existente'],['IMPORT_GIT','Importar Git']]);
  const projectId=inputField('Project ID','project-id','gsdlc03d-demo'); const projectName=inputField('Nombre','project-name','GSDLC 03-D demo'); const target=inputField('Ruta destino / workspace *','target-root','');
  const sourceKind=selectField('Tipo de origen Git','git-source-kind',[['local-path','Repositorio local'],['remote-url','URL remota · ejecución deshabilitada']]);
  const source=inputField('Ruta / URL de origen Git','git-source-location','');
  const grid=document.createElement('div'); grid.className='project-entry-form-grid'; grid.append(mode.wrapper,projectId.wrapper,projectName.wrapper,target.wrapper,sourceKind.wrapper,source.wrapper);
  const hint=document.createElement('p'); hint.className='project-entry-hint'; hint.textContent='IMPORT_GIT usa el origen Git. Remote Git sigue disabled-by-default. Dependencias que requieren red quedan diferidas salvo una autoridad de cache/network explícita futura.';
  const buttons=document.createElement('div'); buttons.className='project-entry-actions';
  const dry=document.createElement('button'); dry.type='submit'; dry.textContent='Generar dry-run';
  const revalidate=document.createElement('button'); revalidate.type='button'; revalidate.textContent='Revalidar preimage'; revalidate.disabled=true;
  buttons.append(dry,revalidate); form.append(grid,hint,buttons);

  const status=document.createElement('div'); status.className='project-entry-status'; status.setAttribute('role','status'); status.setAttribute('aria-live','polite');
  const result=document.createElement('div'); result.className='project-entry-result'; result.dataset.state='empty';

  const execution=document.createElement('section'); execution.className='project-entry-execution-panel'; execution.dataset.state='locked';
  const execHeading=document.createElement('div'); execHeading.className='project-entry-execution-heading';
  const execTitle=document.createElement('h3'); execTitle.textContent='Ejecución gobernada';
  const execBadge=document.createElement('span'); execBadge.className='project-entry-execution-badge'; execBadge.textContent='LOCKED · requiere revalidación + approval';
  execHeading.append(execTitle,execBadge);
  const execHelp=document.createElement('p'); execHelp.textContent='El approval debe decidirse desde una sesión humana con rol owner. Para aceptación 03-D, abre Approval Center en otra pestaña, aprueba el ID exacto y vuelve aquí.';
  const approvalId=inputField('Approval ID','bootstrap-approval-id',''); approvalId.input.readOnly=false; approvalId.input.placeholder='Se completa al solicitar approval';
  const approvalReason=inputField('Motivo de aprobación','bootstrap-approval-reason','Materializar el plan GSDLC-03-D revisado');
  const execActions=document.createElement('div'); execActions.className='project-entry-actions';
  const requestApproval=document.createElement('button'); requestApproval.type='button'; requestApproval.textContent='Solicitar approval'; requestApproval.disabled=true;
  const verifyApproval=document.createElement('button'); verifyApproval.type='button'; verifyApproval.textContent='Verificar approval'; verifyApproval.disabled=true; verifyApproval.className='button-secondary';
  const executePlan=document.createElement('button'); executePlan.type='button'; executePlan.textContent='Ejecutar plan aprobado'; executePlan.disabled=true;
  const approvalLink=document.createElement('a'); approvalLink.href='/approvals'; approvalLink.target='_blank'; approvalLink.rel='noopener'; approvalLink.textContent='Abrir Approval Center ↗';
  execActions.append(requestApproval,verifyApproval,executePlan,approvalLink);
  const execStatus=document.createElement('div'); execStatus.className='project-entry-status'; execStatus.setAttribute('role','status'); execStatus.setAttribute('aria-live','polite');
  const execResult=document.createElement('div'); execResult.className='project-entry-result'; execResult.dataset.state='empty';
  execution.append(execHeading,execHelp,approvalReason.wrapper,approvalId.wrapper,execActions,execStatus,execResult);

  let lastIntake:Record<string,unknown>|null=null, lastPlan='', lastPreimage='', revalidated=false;
  const client=new DevPilotApiClient();

  const lockExecution=(message='LOCKED · requiere revalidación + approval')=>{revalidated=false;requestApproval.disabled=true;verifyApproval.disabled=true;executePlan.disabled=true;approvalId.input.value='';execBadge.textContent=message;execution.dataset.state='locked';execStatus.textContent='';execResult.replaceChildren();execResult.dataset.state='empty';};
  const sync=()=>{const isImport=mode.select.value==='IMPORT_GIT';sourceKind.select.disabled=!isImport;source.input.disabled=!isImport;lockExecution();};
  mode.select.addEventListener('change',sync); sync();

  form.addEventListener('submit',async(ev)=>{
    ev.preventDefault();
    const projectIdValue=projectId.input.value.trim(), projectNameValue=projectName.input.value.trim(), targetValue=target.input.value.trim(), sourceValue=source.input.value.trim();
    if(!projectIdValue){status.textContent='BLOCK: Project ID es obligatorio.';result.replaceChildren();result.dataset.state='error';projectId.input.focus();return;}
    if(!projectNameValue){status.textContent='BLOCK: Nombre es obligatorio.';result.replaceChildren();result.dataset.state='error';projectName.input.focus();return;}
    if(!targetValue){status.textContent='BLOCK: la Ruta destino / workspace es obligatoria y debe permanecer dentro de una raíz de workspace autorizada.';result.replaceChildren();result.dataset.state='error';target.input.focus();return;}
    if(mode.select.value==='IMPORT_GIT'&&!sourceValue){status.textContent='BLOCK: IMPORT_GIT requiere una Ruta / URL de origen Git.';result.replaceChildren();result.dataset.state='error';source.input.focus();return;}
    status.textContent='Generando dry-run read-only…';result.replaceChildren();result.dataset.state='loading';dry.disabled=true;revalidate.disabled=true;lockExecution();
    try{
      const intake=buildIntake(mode.select.value as EntryMode,projectIdValue,projectNameValue,targetValue,sourceKind.select.value,sourceValue);lastIntake=intake;
      const response=await client.projectEntryDryRun({intake});const data=response.data as Record<string,unknown>;const preview=(data.dry_run??{}) as Record<string,unknown>;lastPlan=String(preview.plan_hash??'');lastPreimage=String(preview.preimage_hash??'');
      renderPreview(result,preview,(data.bootstrap_plan??{}) as Record<string,unknown>);result.dataset.state='ready';status.textContent='PASS: dry-run generado sin writes ni network.';revalidate.disabled=!(lastPlan&&lastPreimage);
    }catch(error){lastIntake=null;lastPlan='';lastPreimage='';result.dataset.state='error';status.textContent=`BLOCK: ${error instanceof Error?error.message:'No fue posible generar el dry-run.'}`;}finally{dry.disabled=false;}
  });

  revalidate.addEventListener('click',async()=>{
    if(!lastIntake||!lastPlan||!lastPreimage)return;
    status.textContent='Revalidando preimage…';revalidate.disabled=true;lockExecution();
    try{
      const response=await client.projectEntryRevalidate({intake:lastIntake,expected_plan_hash:lastPlan,expected_preimage_hash:lastPreimage});
      if(response.ok===true){revalidated=true;status.textContent='PASS: plan y preimage permanecen inmutables.';requestApproval.disabled=false;execBadge.textContent='READY · puede solicitar approval';execution.dataset.state='ready';}
      else status.textContent='BLOCK: el preimage cambió; genera un nuevo dry-run.';
    }catch(error){status.textContent=`BLOCK: ${error instanceof Error?error.message:'Revalidación falló.'}`;}finally{revalidate.disabled=false;}
  });

  requestApproval.addEventListener('click',async()=>{
    if(!revalidated||!lastIntake||!lastPlan||!lastPreimage)return;
    requestApproval.disabled=true;executePlan.disabled=true;execStatus.textContent='Solicitando approval exacto…';
    try{
      const response=await client.projectEntryRequestExecutionApproval({intake:lastIntake,expected_plan_hash:lastPlan,expected_preimage_hash:lastPreimage,reason:approvalReason.input.value.trim(),ttl_minutes:30});
      const data=response.data as Record<string,unknown>;const approval=(data.approval??{}) as Record<string,unknown>;const id=String(approval.approval_id??'');
      if(!id)throw new Error('La API no devolvió approval_id.');
      approvalId.input.value=id;execStatus.textContent=`PENDING: approval ${id} creado. Apruébalo en Approval Center y luego usa Verificar approval.`;execBadge.textContent='PENDING APPROVAL';execution.dataset.state='pending';verifyApproval.disabled=false;executePlan.disabled=true;
    }catch(error){execStatus.textContent=`BLOCK: ${error instanceof Error?error.message:'No fue posible solicitar approval.'}`;requestApproval.disabled=false;}
  });

  verifyApproval.addEventListener('click',async()=>{
    const id=approvalId.input.value.trim();if(!id){execStatus.textContent='BLOCK: Approval ID es obligatorio.';approvalId.input.focus();return;}
    verifyApproval.disabled=true;executePlan.disabled=true;execStatus.textContent='Verificando estado del approval…';
    try{
      const response=await client.showApproval(id);const data=response.data as Record<string,unknown>;const approval=(data.approval??data) as Record<string,unknown>;const approvalStatus=String(approval.status??'').toLowerCase();
      if(approvalStatus==='approved'){execStatus.textContent='PASS: approval vigente y aprobado. Execute permanece sujeto a revalidación server-side de scope/policy.';execBadge.textContent='APPROVED · listo para execute';execution.dataset.state='approved';executePlan.disabled=false;}
      else{execStatus.textContent=`PENDING/BLOCK: approval ${id} está en estado ${approvalStatus||'desconocido'}.`;execBadge.textContent='PENDING APPROVAL';execution.dataset.state='pending';verifyApproval.disabled=false;}
    }catch(error){execStatus.textContent=`BLOCK: ${error instanceof Error?error.message:'No fue posible verificar approval.'}`;verifyApproval.disabled=false;}
  });

  executePlan.addEventListener('click',async()=>{
    if(!revalidated||!lastIntake||!lastPlan||!lastPreimage)return;
    const id=approvalId.input.value.trim();if(!id){execStatus.textContent='BLOCK: Approval ID es obligatorio.';approvalId.input.focus();return;}
    executePlan.disabled=true;requestApproval.disabled=true;execStatus.textContent='Ejecutando stages tipados dentro del workspace autorizado…';execResult.replaceChildren();execResult.dataset.state='loading';
    try{
      const response=await client.projectEntryExecute({intake:lastIntake,expected_plan_hash:lastPlan,expected_preimage_hash:lastPreimage,approval_id:id,dependency_mode:'defer-network'});
      const data=response.data as Record<string,unknown>;const executionPayload=(data.execution??{}) as Record<string,unknown>;
      renderExecution(execResult,executionPayload);execResult.dataset.state='ready';execStatus.textContent='PASS: bootstrap approval-bound completado y verificado.';execBadge.textContent='PASS · workspace materializado';execution.dataset.state='pass';
    }catch(error){
      execResult.dataset.state='error';
      if(error instanceof DevPilotApiError&&error.status===408){execStatus.textContent=`UNKNOWN: ${error.message}`;execBadge.textContent='UNKNOWN · reconciliar antes de reintentar';execution.dataset.state='unknown';verifyApproval.disabled=true;executePlan.disabled=true;requestApproval.disabled=true;}
      else{execStatus.textContent=`BLOCK: ${error instanceof Error?error.message:'La ejecución fue bloqueada o revertida.'}`;execBadge.textContent='BLOCKED · requiere nuevo dry-run/revalidación';execution.dataset.state='error';verifyApproval.disabled=false;executePlan.disabled=true;requestApproval.disabled=true;}
    }
  });

  const noExecute=document.createElement('div');noExecute.className='project-entry-no-execute';noExecute.textContent='Ejecución deshabilitada sin approval. GSDLC-03-D solo permite execute tras revalidación exacta, human-session/RBAC, approval y policy PASS.';
  root.append(intro,form,status,noExecute,result,execution);return root;
}

function buildIntake(mode:EntryMode,id:string,name:string,target:string,sourceKind:string,source:string):Record<string,unknown>{const intake:Record<string,unknown>={schema_id:'SCHEMA-DEVPL-GSDLC-03-A-PROJECT-INTAKE-V1',schema_version:'1.0',project_id:id.trim(),project_name:name.trim(),project_type:'agent-assisted-sdlc',entry_mode:mode,target_root:target.trim(),stack:{frontend:'react-typescript',backend:'fastapi-python',database:'sqlite'},standards:['MIPSoftware','MIASI'],provider:{mode:'none',provider_id:null},restrictions:{arbitrary_shell_allowed:false,silent_network_allowed:false,remote_git_execute_allowed:false}};if(mode==='IMPORT_GIT')intake.git_source={kind:sourceKind,location:source.trim()};return intake;}
function inputField(label:string,id:string,value:string){const wrapper=document.createElement('label');wrapper.className='project-entry-field';wrapper.htmlFor=id;const span=document.createElement('span');span.textContent=label;const input=document.createElement('input');input.id=id;input.value=value;input.autocomplete='off';input.required=true;wrapper.append(span,input);return{wrapper,input};}
function selectField(label:string,id:string,items:[string,string][]){const wrapper=document.createElement('label');wrapper.className='project-entry-field';wrapper.htmlFor=id;const span=document.createElement('span');span.textContent=label;const select=document.createElement('select');select.id=id;for(const[v,t]of items){const o=document.createElement('option');o.value=v;o.textContent=t;select.append(o);}wrapper.append(span,select);return{wrapper,select};}
function renderPreview(target:HTMLElement,dry:Record<string,unknown>,plan:Record<string,unknown>){const review=(dry.review??{}) as Record<string,unknown>;const approval=(dry.approval_preview??{}) as Record<string,unknown>;const safety=(dry.safety??{}) as Record<string,unknown>;const top=document.createElement('div');top.className='project-entry-summary-grid';for(const[label,value]of [['Modo',review.entry_mode],['Plan hash',dry.plan_hash],['Preimage hash',dry.preimage_hash],['Writes ejecutados',safety.writes_performed],['Network usada',safety.network_used],['Approval solicitado',safety.approval_requested]]){const c=document.createElement('div');c.className='project-entry-summary-card';const k=document.createElement('span');k.textContent=String(label);const v=document.createElement('strong');v.textContent=String(value??'—');c.append(k,v);top.append(c);}const details=document.createElement('div');details.className='project-entry-review-grid';details.append(jsonCard('Preview de aprobación',approval),jsonCard('Efectos declarados',{directories:plan.directories,files:plan.files,git_operations:plan.git_operations,venv:plan.venv,dependency_jobs:plan.dependency_jobs,workspace_registration:plan.workspace_registration,network:plan.network}),jsonCard('Preimage',dry.preimage));target.append(top,details);}
function renderExecution(target:HTMLElement,execution:Record<string,unknown>){const top=document.createElement('div');top.className='project-entry-summary-grid';const verification=(execution.verification??{}) as Record<string,unknown>;for(const[label,value]of [['Estado',execution.status],['Execution hash',execution.execution_hash],['Git clean',verification.git_clean],['Venv OK',verification.venv_ok],['Network usada',execution.network_used],['Writes fuera workspace',execution.writes_outside_workspace]]){const c=document.createElement('div');c.className='project-entry-summary-card';const k=document.createElement('span');k.textContent=String(label);const v=document.createElement('strong');v.textContent=String(value??'—');c.append(k,v);top.append(c);}target.append(top,jsonCard('Stages y rollback contract',{stages:execution.stages,verification:execution.verification,dependency_mode:execution.dependency_mode}));}
function jsonCard(title:string,payload:unknown){const card=document.createElement('article');card.className='project-entry-review-card';const h=document.createElement('h3');h.textContent=title;const pre=document.createElement('pre');pre.textContent=JSON.stringify(payload,null,2);card.append(h,pre);return card;}
