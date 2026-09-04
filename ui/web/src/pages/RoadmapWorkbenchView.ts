import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { AuthSessionContext, RoadmapProposalRequest, RoadmapWorkbenchProjection } from '../api/types';
import { renderStepActionAdvisor } from '../components/StepActionAdvisor';

const DEFAULT_ROADMAP = {
  roadmap_id: 'planning-roadmap-001', version: '1.0.0', milestones: [
    { id: 'mil-foundation', version: '1.0.0', title: 'Foundation', owner_role: 'product-owner', outcome: 'Validated planning foundation', exit_criteria: ['Required scope covered'], trace_links: [{ kind: 'requirement', target_id: 'REQ-001' }, { kind: 'risk', target_id: 'RISK-001' }] },
  ], dependencies: [],
};

export function renderRoadmapWorkbenchView(tokenProvider: () => string | null, session: AuthSessionContext): HTMLElement {
  const host=document.createElement('section'); host.className='roadmap-workbench'; host.dataset.gsdlc08b='roadmap-workbench'; host.setAttribute('aria-labelledby','roadmap-workbench-title');
  const intro=document.createElement('div'); intro.className='panel roadmap-workbench__intro';
  const h=document.createElement('h2'); h.id='roadmap-workbench-title'; h.textContent='Roadmap Workbench';
  const p=document.createElement('p'); p.textContent='Manual, import y propuesta de agente producen el mismo contrato DRAFT. Review, approval y freeze siguen siendo autoridad humana del servidor.';
  const safety=document.createElement('p'); safety.className='muted'; safety.textContent='Local-first · runtime planning only · sin escritura de source · sin API externa obligatoria · agent output nunca auto-aprueba.';
  intro.append(h,p,safety); host.append(intro);

  const status=document.createElement('div'); status.className='notice'; status.setAttribute('role','status'); status.setAttribute('aria-live','polite'); host.append(status);
  const content=document.createElement('div'); content.className='roadmap-workbench__content'; host.append(content);
  const client=()=>new DevPilotApiClient({ token: tokenProvider() });

  async function load(message=''):Promise<void>{
    status.className='notice notice--loading'; status.textContent=message||'Cargando roadmap gobernado…';
    try {
      const response=await client().roadmapStatus(); const wb=extract(response.data); draw(wb); status.className='notice notice--pass'; status.textContent=message||'Roadmap Workbench listo.';
    } catch (error) { content.replaceChildren(); status.className='notice notice--block'; status.textContent=errorText(error); }
  }

  function draw(wb:RoadmapWorkbenchProjection):void{
    content.replaceChildren();
    if(wb.advisor) content.append(renderStepActionAdvisor({ui_state:'READY',workspace_id:wb.workspace_id,current_step:'PLANNING_ROADMAP',advisor:wb.advisor,read_only:false,actor_neutral:false,server_authoritative:true,network_used:false,external_api_used:false,mutations_performed:false,source_mutations_performed:false}));
    content.append(editor(wb), summary(wb));
  }

  function editor(wb:RoadmapWorkbenchProjection):HTMLElement{
    const panel=document.createElement('section'); panel.className='panel roadmap-workbench__editor'; const title=document.createElement('h3'); title.textContent='Crear / revisar propuesta DRAFT'; panel.append(title);
    const mode=selectField('Ruta de autoría',[['MANUAL','Manual'],['IMPORT','Importar JSON local'],['AGENT','Propuesta estructurada de agente']],new URLSearchParams(globalThis.location.search).get('mode')||'MANUAL');
    const req=inputField('Requirements obligatorios (separados por coma)','REQ-001'); const risks=inputField('Risks conocidos (separados por coma)','RISK-001');
    const area=document.createElement('textarea'); area.rows=18; area.value=JSON.stringify(DEFAULT_ROADMAP,null,2); area.setAttribute('aria-label','Roadmap JSON estructurado'); area.spellcheck=false;
    const file=document.createElement('input'); file.type='file'; file.accept='.json,application/json'; file.setAttribute('aria-label','Archivo JSON local'); file.addEventListener('change',async()=>{const f=file.files?.[0];if(f){area.value=await f.text();mode.value='IMPORT';}});
    const controls=document.createElement('div'); controls.className='roadmap-workbench__actions';
    controls.append(button('Guardar DRAFT',async()=>{try{const roadmap=JSON.parse(area.value); await client().roadmapPropose({mode:mode.value as RoadmapProposalRequest['mode'],roadmap,required_requirement_ids:split(req.value),required_risk_ids:split(risks.value),source_label:mode.value==='IMPORT'?(file.files?.[0]?.name||'local-json'):mode.value==='AGENT'?'structured-agent-output':'manual'});await load('DRAFT guardado. Review obligatorio antes de approval.');}catch(e){setBlock(e);}}));
    controls.append(button('Validar / Review',async()=>{try{await client().roadmapReview();await load('Review ejecutado: coverage y findings actualizados.');}catch(e){setBlock(e);}}));
    const approve=button('Approve humano',async()=>{try{await client().roadmapApprove();await load('Approval server-side registrado.');}catch(e){setBlock(e);}}); approve.disabled=!canApprove(session); controls.append(approve);
    const freeze=button('Freeze revisionado',async()=>{try{await client().roadmapFreeze();await load('Roadmap FROZEN como revisión inmutable.');}catch(e){setBlock(e);}}); freeze.disabled=!canApprove(session); controls.append(freeze);
    const note=document.createElement('p'); note.className='muted'; note.textContent=canApprove(session)?'Tu rol puede aprobar/freeze. El servidor revalida RBAC en cada request.':'Approval/freeze deshabilitado visualmente para este rol; el servidor también deniega la operación.';
    panel.append(mode,req,risks,file,area,controls,note); return panel;
  }

  function summary(wb:RoadmapWorkbenchProjection):HTMLElement{
    const panel=document.createElement('section'); panel.className='panel roadmap-workbench__summary'; const h=document.createElement('h3'); h.textContent='Estado, coverage y provenance'; panel.append(h);
    const roadmap=asRecord(wb.roadmap); if(!roadmap){const empty=document.createElement('p');empty.textContent='Aún no existe DRAFT. Elige una ruta de autoría.';panel.append(empty);return panel;}
    const dl=document.createElement('dl'); dl.className='roadmap-workbench__facts'; add(dl,'Lifecycle',String(roadmap.lifecycle??'DRAFT')); add(dl,'Modo',String(roadmap.authoring_mode??'')); add(dl,'Requirements coverage',`${String(asRecord(roadmap.coverage)?.requirement_percent??0)}%`); add(dl,'Risk coverage',`${String(asRecord(roadmap.coverage)?.risk_percent??0)}%`); add(dl,'Provenance',String(asRecord(roadmap.provenance)?.mode??'')); panel.append(dl);
    const findings=Array.isArray(roadmap.findings)?roadmap.findings:[]; const list=document.createElement('ul'); list.className='roadmap-workbench__findings'; if(!findings.length){const li=document.createElement('li');li.textContent='Sin findings de coverage/contrato.';list.append(li);} for(const row of findings){const r=asRecord(row);const li=document.createElement('li');li.dataset.severity=String(r?.severity??'');li.textContent=`${String(r?.code??'finding')}: ${String(r?.message??'')}${r?.subject?` · ${String(r.subject)}`:''}`;list.append(li);} panel.append(list);
    if(wb.review){const pre=document.createElement('pre');pre.className='roadmap-workbench__review';pre.textContent=JSON.stringify(wb.review,null,2);panel.append(pre);} return panel;
  }

  function setBlock(error:unknown):void{status.className='notice notice--block';status.textContent=errorText(error);}
  void load(); return host;
}

function extract(data:unknown):RoadmapWorkbenchProjection{const root=asRecord(data);return (asRecord(root?.roadmap_workbench)??{}) as RoadmapWorkbenchProjection;}
function asRecord(value:unknown):Record<string,any>|null{return value&&typeof value==='object'&&!Array.isArray(value)?value as Record<string,any>:null;}
function inputField(label:string,value:string):HTMLInputElement{const input=document.createElement('input');input.type='text';input.value=value;input.setAttribute('aria-label',label);input.placeholder=label;return input;}
function selectField(label:string,options:Array<[string,string]>,value:string):HTMLSelectElement{const select=document.createElement('select');select.setAttribute('aria-label',label);for(const [v,t] of options){const o=document.createElement('option');o.value=v;o.textContent=t;o.selected=v===value;select.append(o);}return select;}
function button(label:string,fn:()=>Promise<void>):HTMLButtonElement{const b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',()=>void fn());return b;}
function split(value:string):string[]{return value.split(',').map(x=>x.trim()).filter(Boolean);}
function add(dl:HTMLDListElement,k:string,v:string):void{const dt=document.createElement('dt');dt.textContent=k;const dd=document.createElement('dd');dd.textContent=v;dl.append(dt,dd);}
function canApprove(session:AuthSessionContext):boolean{return session.principal.roles.some(x=>['owner','product-owner'].includes(x));}
function errorText(error:unknown):string{return error instanceof DevPilotApiError?`${error.message}`:error instanceof Error?error.message:'Error local no clasificado.';}
