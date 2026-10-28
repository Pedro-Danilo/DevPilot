import {renderArchitectureWorkbench} from '../src/components/ArchitectureWorkbench';
import {renderPreCodeWizardView} from '../src/pages/PreCodeWizardView';
import {DevPilotApiClient,DevPilotApiError} from '../src/api/client';

const outcomes:Array<{name:string;pass:boolean;error?:string}>=[];
const tick=()=>new Promise(r=>setTimeout(r,30));
const assert=(value:unknown,message='assertion failed')=>{if(!value)throw new Error(message);};
const focused=new URLSearchParams(location.search).get('focus')==='selectors';
const retained=new Set(['one container and exactly three accessible document tabs','three distinct complete documents and keyboard tab focus','FROZEN is full read-only and cannot offer direct editing','non-owner has identical documents but no mutation capability','reload pending receipt blocks generation without fake percentage or cancel','long inference gives immediate state and prevents duplicate request','dirty review prevents dependent mutation even if old button remains enabled']);
const checks=async(name:string,fn:()=>unknown)=>{if(focused&&!name.startsWith('[selectors]')&&!retained.has(name))return;try{await fn();outcomes.push({name,pass:true});}catch(e){outcomes.push({name,pass:false,error:String(e)});}};
let sequence=0;
const markdown='# Architecture\n\n**Completo** y `código`. [Fuente](https://example.invalid/docs)\n\n| RF | Componente |\n| --- | --- |\n| RF-001 | Registro |\n\n1. Validar\n2. Persistir\n\n> Cita de origen.\n\n```python\nassert stock >= 0\n```\n\nFinal íntegro de Architecture.';
function fixture(settings:{models?:string[];healthy?:boolean;probeError?:boolean;modes?:string[];mode?:string;status?:string}={}){
  const id=`ux01c-fixture-${++sequence}`;
  const quality={current:{quality_level:'REVIEW_REQUIRED',handoff_ready:false,professional_reviewed:false,sources:[{source_id:'requirements',sha256:'a'.repeat(64)}],findings:[{id:'gap',severity:'REVIEW_REQUIRED',section_id:'datos',why:'Pendiente de justificar',suggested_fix:'Describir transacción y rollback RF-001.'}]},before_owner:{quality_level:'REVIEW_REQUIRED'}};
  const docs:any={architecture:{content:markdown,status:'DRAFT',source:'runtime',sha256:'a'.repeat(64),can_edit:true,candidate_id:'arch-1',generation_epoch:'e1',quality},technology_options:{content:'# Opciones\n## Opción T1 — Python SQLite\nPrimera alternativa.\n## Opción T2 — Python PostgreSQL\nSegunda alternativa.\nFinal completo de Options.',status:'REVIEW_REQUIRED',source:'runtime',sha256:'b'.repeat(64),can_edit:true,candidate_id:'tech-1',generation_epoch:'e1',quality},adr:{content:'# ADR-001\n## Decisión\nOwner elige T1.\nFinal íntegro del ADR.',status:'REVIEW_REQUIRED',source:'runtime',sha256:'c'.repeat(64),can_edit:true,candidate_id:'adr-1',generation_epoch:'e1',quality}};
  const arch:any={stage_id:'architecture',order:4,label:'Architecture',relative_path:'docs/02_architecture/architecture_document.md',profile_id:'architecture-document',advisor_step:'technical-design',allowed_modes:settings.modes??['LOCAL_MODEL','MANUAL'],status:settings.status??'DRAFT',mode:settings.mode??'LOCAL_MODEL',content_sha256:docs.architecture.sha256,draft_content:markdown,derivation:{model:'installed:test',generation_epoch:'e1'}};
  const p:any={workspace_id:id,project_name:'Proyecto aislado simulado',status:'IN_PROGRESS',current_stage_id:'architecture',stages:[arch],readiness:{status:'BLOCK',mandatory_stages_frozen:3,mandatory_stages_total:7},miasi:{status:'UNKNOWN',gate_status:'BLOCK',risk_level:'unknown'},architecture_workbench_documents:docs,r03_04_authoring:{status:'ADR_DRAFT',selected_option_id:'T1',architecture_reconciled:false,technology:{...docs.technology_options,candidate_sha256:docs.technology_options.sha256},adr:{...docs.adr,candidate_sha256:docs.adr.sha256},activity:[]}};
  const session:any={authenticated:true,principal:{actor_id:'owner',roles:['owner'],workspace_scopes:[id]},created_at:'2026-10-27T00:00:00Z'};
  if(settings.status==='FROZEN'){p.current_stage_id='security';for(const d of Object.values(docs) as any[]){d.status='FROZEN';d.can_edit=false;}}
  const calls:any[]=[];let probes=0;let reject:number|null=null;let deferred:((v:any)=>void)|null=null;
  const client:any={probeLocalModelReadiness:async()=>{probes++;if(settings.probeError)throw new Error('PRIVATE_PROBE_ERROR');return {ok:true,data:{providers:[{provider_id:'ollama',healthy:settings.healthy??true,models:settings.models??['installed:test','alternate:local']}]}};},authSession:async()=>({authenticated:true}),preCodeTechnologyAction:async(payload:any)=>{calls.push(payload);if(reject!==null)throw new DevPilotApiError('PRIVATE_STACK_SECRET',reject,{});if(deferred===null)return {ok:true,message:'done',data:{handoff:{findings:quality.current.findings}}};return await new Promise(r=>{deferred=r;});},preCodeDraft:async(...payload:any[])=>{calls.push(payload);if(reject!==null)throw new DevPilotApiError('PRIVATE_STACK_SECRET',reject,{});return {ok:true,message:'saved'};},preCodeReview:async()=>({ok:true,message:'review'})};
  const mount=()=>{document.querySelectorAll('[data-mount]').forEach(e=>e.remove());const wrap=document.createElement('main');wrap.dataset.mount='true';const created=renderArchitectureWorkbench({projection:p,session,client:()=>client,refresh:async()=>{view=mount();}});wrap.append(created);document.body.append(wrap);return created;};
  let view=mount();
  const button=(text:string)=>{const b=Array.from(view.querySelectorAll<HTMLButtonElement>('button')).find(b=>b.textContent===text);assert(b,`button ${text}`);return b!;};
  const tab=(name:string)=>{button(name).click();};
  return {p,arch,docs,session,calls,client,probes:()=>probes,view:()=>view,button,tab,mount:()=>{view=mount();return view;},setError:(status:number)=>{reject=status;},defer:()=>{deferred=()=>{};},finish:()=>{deferred?.({ok:true,message:'complete'});deferred=null;}};
}
async function main(){
window.confirm=()=>true;
await checks('one container and exactly three accessible document tabs',()=>{const f=fixture();assert(f.view().querySelectorAll('[role=tab]').length===3);assert(document.querySelectorAll('[data-architecture-workbench]').length===1);assert(f.view().querySelector('[role=tabpanel]')?.getAttribute('aria-labelledby')==='ux01c-architecture-tab');});
await checks('full safe Markdown: headings tables lists quotes code links and tail',()=>{const f=fixture(),v=f.view();for(const selector of ['h1','table','th','ol','blockquote','pre code','a[href]','strong'])assert(v.querySelector(`[data-workbench-document] ${selector}`),selector);assert(v.textContent?.includes('Final íntegro de Architecture.'));});
await checks('three distinct complete documents and keyboard tab focus',()=>{const f=fixture();f.tab('Opciones tecnológicas');assert(f.view().textContent?.includes('Final completo de Options.'));f.tab('ADR');assert(f.view().textContent?.includes('Final íntegro del ADR.'));f.button('ADR').dispatchEvent(new KeyboardEvent('keydown',{key:'Home',bubbles:true}));assert(f.button('Arquitectura').getAttribute('aria-selected')==='true');});
await checks('single canonical editor and draft survives tab navigation',()=>{const f=fixture();f.button('Editar revisión Owner').click();assert(f.view().querySelectorAll('textarea').length===1);assert(!f.view().querySelector('[data-workbench-document]'));let e=f.view().querySelector('textarea')!;e.value='Owner conserva texto';e.dispatchEvent(new Event('input'));f.tab('ADR');f.tab('Arquitectura');f.button('Editar revisión Owner').click();assert(f.view().querySelector('textarea')?.value==='Owner conserva texto');});
await checks('preview and cancel preserve editorial draft without server authority',()=>{const f=fixture();f.button('Editar revisión Owner').click();const e=f.view().querySelector('textarea')!;e.value='# Revisión temporal';e.dispatchEvent(new Event('input'));f.button('Previsualizar revisión').click();assert(f.view().querySelector('article h1')?.textContent==='Revisión temporal');assert(f.view().querySelectorAll('textarea').length===0);f.button('Cancelar edición (conservar borrador)').click();assert(f.calls.length===0);assert(f.docs.architecture.content===markdown);});
await checks('T1 to T2 requires confirmation and successor binds SHA epoch',async()=>{const f=fixture();f.tab('Opciones tecnológicas');window.confirm=()=>false;f.button('Elegir T2 — Python PostgreSQL').click();await tick();assert(f.calls.length===0);window.confirm=()=>true;f.button('Elegir T2 — Python PostgreSQL').click();await tick();assert(f.calls[0].successor===true&&f.calls[0].option_id==='T2'&&f.calls[0].expected_sha256===f.docs.technology_options.sha256&&f.calls[0].generation_epoch==='e1');});
await checks('dirty review prevents dependent mutation even if old button remains enabled',async()=>{const f=fixture();await tick();f.button('Editar revisión Owner').click();const e=f.view().querySelector('textarea')!;e.value+=' unsaved';e.dispatchEvent(new Event('input'));f.button('Generar alternativa sucesora').click();await tick();assert(f.calls.length===0);});
await checks('long inference gives immediate state and prevents duplicate request',async()=>{const f=fixture();await tick();f.tab('Opciones tecnológicas');window.confirm=()=>true;f.defer();const b=f.button('Generar alternativa sucesora');b.click();assert(f.view().textContent?.includes('Generando Opciones tecnológicas con modelo local'));b.click();await tick();assert(f.calls.length===1);assert(f.button('Generar alternativa sucesora').disabled);f.finish();await tick();});
await checks('409 preserves Owner text and shows actionable plan renewal',async()=>{const f=fixture();f.button('Editar revisión Owner').click();let e=f.view().querySelector('textarea')!;e.value='Revisión conservada 409';e.dispatchEvent(new Event('input'));f.setError(409);f.button('Guardar revisión Owner').click();await tick();assert(f.view().textContent?.includes('renueva plan/diff'));f.mount();f.button('Editar revisión Owner').click();assert(f.view().querySelector('textarea')?.value==='Revisión conservada 409');});
await checks('500 is redacted and preserves text with uncertainty guard',async()=>{const f=fixture();f.button('Editar revisión Owner').click();let e=f.view().querySelector('textarea')!;e.value='Revisión protegida 500';e.dispatchEvent(new Event('input'));f.setError(500);f.button('Guardar revisión Owner').click();await tick();assert(f.view().textContent?.includes('Error del servidor (500)'));assert(!f.view().textContent?.includes('PRIVATE_STACK_SECRET'));assert(sessionStorage.getItem(`ux01C:${f.p.workspace_id}:draft:architecture`)?.includes('Revisión protegida 500'));assert(f.button('Generar alternativa sucesora').disabled);});
await checks('reload pending receipt blocks generation without fake percentage or cancel',()=>{const f=fixture();f.p.r03_04_authoring.activity=[{kind:'technology',status:'IN_PROGRESS',candidate_id:'running'}];f.mount();assert(f.button('Generar alternativa sucesora').disabled);assert(!f.view().textContent?.includes('90 %'));assert(!Array.from(f.view().querySelectorAll('button')).some(b=>b.textContent==='Cancelar inferencia'));});
await checks('terminal new receipt recovers after uncertain reload without automatic retry',()=>{const f=fixture();sessionStorage.setItem(`ux01C:${f.p.workspace_id}:pending`,JSON.stringify({kind:'technology',document:'technology_options',before:'old',beforeSha:'old',stageStatus:'DRAFT',selection:'T1'}));f.p.r03_04_authoring.activity=[{kind:'technology',status:'COMPLETE',candidate_id:'new'}];f.mount();assert(!sessionStorage.getItem(`ux01C:${f.p.workspace_id}:pending`));assert(f.calls.length===0);});
await checks('FROZEN is full read-only and cannot offer direct editing',()=>{const f=fixture();f.arch.status='FROZEN';f.p.current_stage_id='security';for(const d of Object.values(f.docs) as any[]){d.status='FROZEN';d.can_edit=false;}f.mount();assert(f.button('Editar revisión Owner').disabled);assert(f.view().textContent?.includes('Final íntegro de Architecture.'));f.tab('ADR');assert(f.button('Editar revisión Owner').disabled);});
await checks('non-owner has identical documents but no mutation capability',()=>{const f=fixture();f.session.principal.roles=['viewer'];f.mount();assert(f.button('Editar revisión Owner').disabled&&f.button('Generar alternativa sucesora').disabled);assert(f.view().textContent?.includes('Final íntegro de Architecture.'));});
await checks('empty versus blocked source is explicit, not a stale excerpt',()=>{const f=fixture();f.docs.adr.content='';f.docs.adr.status='SIN_GENERAR';f.tab('ADR');assert(f.view().textContent?.includes('SIN GENERAR'));f.docs.adr.status='BLOCK';f.docs.adr.error_code='HASH_DRIFT';f.mount();assert(f.view().textContent?.includes('HASH_DRIFT'));});
await checks('quality gaps and handoff preserve REVIEW_REQUIRED not professional approval',async()=>{const f=fixture();assert(f.view().textContent?.includes('Describir transacción y rollback RF-001'));f.button('Consultar handoff offline').click();await tick();assert(f.calls[0].action==='export_handoff');assert(f.view().textContent?.includes('no acreditado'));});
await checks('Guided and Expert retain same document authority',()=>{const f=fixture();document.body.className='guided';const before=f.view().querySelector('[data-workbench-document]')?.textContent;document.body.className='expert';assert(f.view().querySelector('[data-workbench-document]')?.textContent===before);assert(f.button('Editar revisión Owner').disabled===false);});
await checks('unsafe Markdown remains text and javascript links cannot execute',()=>{const f=fixture();f.docs.architecture.content='# Seguro\n<script>window.hacked=true</script>\n[ataque](javascript:alert)\n--- final';f.mount();assert(!f.view().querySelector('script'));assert(!f.view().querySelector('a[href^="javascript:"]'));assert(!(window as any).hacked);assert(f.view().textContent?.includes('<script>'));});
await checks('mobile overflow stays within table/code containers',()=>{const f=fixture();f.docs.architecture.content='# Ancho\n\n| A | B |\n| --- | --- |\n| '+('wide-data-'.repeat(100))+' | x |\n\n```\n'+('long-path/'.repeat(150))+'\n```';f.mount();assert(document.documentElement.scrollWidth<=innerWidth+2,`overflow ${document.documentElement.scrollWidth}/${innerWidth}`);assert(f.view().querySelector('.markdown-table-scroll'));});
await checks('actual Pre-code view mounts one workbench and removes old duplicate editor',async()=>{const f=fixture();const proto=DevPilotApiClient.prototype;const old=proto.preCodeStatus,oldProbe=proto.probeLocalModelReadiness;proto.probeLocalModelReadiness=f.client.probeLocalModelReadiness;proto.preCodeStatus=async()=>({ok:true,message:'fixture',data:{pre_code:f.p}} as any);document.querySelectorAll('[data-mount]').forEach(e=>e.remove());const wrap=document.createElement('div');wrap.dataset.mount='true';wrap.append(renderPreCodeWizardView(()=>null,f.session));document.body.append(wrap);await tick();assert(wrap.querySelectorAll('[data-architecture-workbench]').length===1);assert(wrap.querySelectorAll('[role=tab]').length===3);assert(!wrap.querySelector('[data-r0304-local-authoring]'));assert(!wrap.querySelector('[data-pre-code-authoring-content]'));proto.preCodeStatus=old;proto.probeLocalModelReadiness=oldProbe;});
await checks('client serializes epoch/hash and preserves the 450-second technology budget without retry',async()=>{
  const oldFetch=window.fetch,oldTimeout=window.setTimeout;const budgets:number[]=[];let count=0,body:any;
  window.setTimeout=((fn:any,ms?:number,...args:any[])=>{budgets.push(ms??0);return oldTimeout(fn,ms,...args);}) as any;
  window.fetch=async(_url:any,init:any)=>{count++;body=JSON.parse(init.body);return new Response(JSON.stringify({ok:true,message:'fixture',data:{}}),{status:200,headers:{'Content-Type':'application/json'}});};
  try{await new DevPilotApiClient({token:''}).preCodeTechnologyAction({action:'generate_adr',expected_sha256:'d'.repeat(64),generation_epoch:'e2',successor:true});assert(budgets.includes(450000),'technology budget clipped');assert(count===1&&body.generation_epoch==='e2'&&body.successor===true&&body.expected_sha256==='d'.repeat(64));}finally{window.fetch=oldFetch;window.setTimeout=oldTimeout;}
});
await checks('frontmatter keeps multiline metadata and preference reload keeps selected tab',()=>{const f=fixture();f.docs.adr.content='---\ndoc_id: ADR-X\nnotes: |\n  línea preservada\n---\n# Decisión\nContenido final.';f.tab('ADR');f.mount();assert(f.button('ADR').getAttribute('aria-selected')==='true');assert(f.view().querySelector('.document-frontmatter')?.textContent?.includes('línea preservada'));assert(f.view().textContent?.includes('Contenido final.'));});
await checks('elapsed inference timer starts at request gesture rather than page mount',async()=>{
 const f=fixture();await tick();f.tab('Opciones tecnológicas');f.defer();window.confirm=()=>true;
 const now=Date.now;const shifted=now()+600000;Date.now=()=>shifted;
 try{f.button('Generar alternativa sucesora').click();assert(f.view().querySelector('[data-workbench-feedback]')?.textContent?.includes('0 s.'),'timer includes page idle time');await tick();f.finish();await tick();}finally{Date.now=now;}
});
await checks('shared Markdown renderer preserves existing source-line navigation',()=>{
 const f=fixture();f.docs.architecture.content='# Cabecera\n\n- Primera\n- Segunda\n\nTexto final.';f.mount();
 assert(f.view().querySelector('li[data-source-line="4"]')?.textContent==='Segunda');
 assert(f.view().querySelector('p[data-source-line="6"]')?.textContent==='Texto final.');
});
await checks('[selectors] authoring modes follow the server allowlist and exclude unsupported values',async()=>{
 const f=fixture({modes:['LOCAL_MODEL','DEVPL_MOCK','MANUAL','IMPORT','UNSUPPORTED']});await tick();
 const mode=f.view().querySelector<HTMLSelectElement>('select[aria-label="Modo de autoría"]')!;
 assert(Array.from(mode.options).map(o=>o.value).join(',')==='LOCAL_MODEL,DEVPL_MOCK,MANUAL,IMPORT');
 assert(!f.view().querySelector('input[aria-label="Nombre exacto del modelo local instalado"]'));
});
await checks('[selectors] installed model selector uses only healthy discovered models and no mandatory model',async()=>{
 const f=fixture({models:['local-one:v1','local-two:v2','local-one:v1','remote://invalid']});await tick();
 const select=f.view().querySelector<HTMLSelectElement>('select[aria-label="Modelo Ollama instalado"]')!;
 assert(Array.from(select.options).map(o=>o.value).join(',')===',local-one:v1,local-two:v2');
 assert(select.value===''&&f.button('Generar alternativa sucesora').disabled);
 select.value='local-two:v2';select.dispatchEvent(new Event('change'));assert(!f.button('Generar alternativa sucesora').disabled);
 f.tab('Opciones tecnológicas');assert(f.view().querySelector<HTMLSelectElement>('select[aria-label="Modelo Ollama instalado"]')?.value==='local-two:v2');
});
for(const kind of ['architecture','technology_options','adr'])await checks('[selectors] selected installed model reaches '+kind+' generation',async()=>{
 const f=fixture({models:['other-local:v3','second-local:v2']});await tick();
 f.tab(kind==='architecture'?'Arquitectura':kind==='adr'?'ADR':'Opciones tecnológicas');
 const select=f.view().querySelector<HTMLSelectElement>('select[aria-label="Modelo Ollama instalado"]')!;select.value='other-local:v3';select.dispatchEvent(new Event('change'));
 f.button('Generar alternativa sucesora').click();await tick();
 const payload=kind==='architecture'?f.calls[0][1]:f.calls[0];assert(payload.model==='other-local:v3');
 assert(kind==='architecture'?payload.mode==='LOCAL_MODEL':payload.action===(kind==='adr'?'generate_adr':'generate_options'));
});
await checks('[selectors] absent models block inference only and preserve Owner editing review and choice',async()=>{
 const f=fixture({models:[]});await tick();assert(f.view().textContent?.includes('No hay modelos Ollama disponibles'));
 assert(f.button('Generar alternativa sucesora').disabled&&!f.button('Validar y preparar diff').disabled);
 f.tab('Opciones tecnológicas');assert(!f.button('Elegir T2 — Python PostgreSQL').disabled);assert(!f.button('Editar revisión Owner').disabled);
 f.tab('Arquitectura');f.button('Editar revisión Owner').click();const e=f.view().querySelector('textarea')!;e.value='Revisión sin inferencia';e.dispatchEvent(new Event('input'));
 f.button('Guardar revisión Owner').click();await tick();assert(f.calls[0][1].content==='Revisión sin inferencia');
});
await checks('[selectors] discovery failure is actionable and does not disclose private probe errors',async()=>{
 const f=fixture({probeError:true});await tick();assert(f.view().textContent?.includes('No se pudo consultar Ollama'));
 assert(!f.view().textContent?.includes('PRIVATE_PROBE_ERROR'));assert(!f.button('Editar revisión Owner').disabled);assert(f.button('Generar alternativa sucesora').disabled);
});
await checks('[selectors] MANUAL mode saves through the existing draft endpoint without a model',async()=>{
 const f=fixture({mode:'MANUAL'});assert(f.probes()===0);f.button('Escribir Architecture manual').click();
 const e=f.view().querySelector('textarea')!;e.value='# Architecture manual';e.dispatchEvent(new Event('input'));f.button('Guardar revisión Owner').click();await tick();
 assert(f.calls[0][0]==='architecture'&&f.calls[0][1].mode==='MANUAL'&&f.calls[0][1].content==='# Architecture manual'&&!f.calls[0][1].model);
});
await checks('[selectors] IMPORT keeps one editor and forwards the selected mode and complete file',async()=>{
 const f=fixture({mode:'IMPORT',modes:['LOCAL_MODEL','DEVPL_MOCK','MANUAL','IMPORT']});assert(f.probes()===0);
 const input=f.view().querySelector<HTMLInputElement>('input[type="file"]')!,files=new DataTransfer();files.items.add(new File(['# Importado\nTexto íntegro.'],'fixture.md',{type:'text/markdown'}));input.files=files.files;input.dispatchEvent(new Event('change'));await tick();
 assert(f.view().querySelectorAll('textarea').length===1&&f.view().querySelector('textarea')?.value==='# Importado\nTexto íntegro.');
 f.button('Guardar revisión Owner').click();await tick();assert(f.calls[0][1].mode==='IMPORT'&&f.calls[0][1].content==='# Importado\nTexto íntegro.');
});
await checks('[selectors] deterministic mode uses existing DEVPL_MOCK with no model discovery or inference',async()=>{
 const f=fixture({mode:'DEVPL_MOCK',modes:['LOCAL_MODEL','DEVPL_MOCK','MANUAL','IMPORT']});assert(f.probes()===0);
 f.button('Generar propuesta determinística').click();await tick();assert(f.calls[0][1].mode==='DEVPL_MOCK'&&f.calls[0][1].content===''&&!f.calls[0][1].model);
});
await checks('[selectors] FROZEN disables both selectors and performs no discovery or generation',async()=>{
 const f=fixture({status:'FROZEN',modes:['LOCAL_MODEL','DEVPL_MOCK','MANUAL','IMPORT']});await tick();
 assert(f.probes()===0&&f.calls.length===0);for(const select of f.view().querySelectorAll('select'))assert(select.disabled);
 assert(f.button('Editar revisión Owner').disabled&&f.button('Generar alternativa sucesora').disabled);
});
await checks('[selectors] model discovery is shared across tabs and refreshed only on explicit request',async()=>{
 const f=fixture();await tick();assert(f.probes()===1);f.tab('ADR');f.tab('Opciones tecnológicas');f.tab('Arquitectura');await tick();assert(f.probes()===1&&f.calls.length===0);
 f.button('Consultar modelos instalados').click();await tick();assert(f.probes()===2&&f.calls.length===0);
});
await checks('[selectors] changing authoring mode preserves the unsaved editorial text',async()=>{
 const f=fixture({modes:['LOCAL_MODEL','DEVPL_MOCK','MANUAL','IMPORT']});await tick();f.button('Editar revisión Owner').click();
 const e=f.view().querySelector('textarea')!;e.value='Borrador conservado al cambiar modo';e.dispatchEvent(new Event('input'));
 const select=f.view().querySelector<HTMLSelectElement>('select[aria-label="Modo de autoría"]')!;select.value='MANUAL';select.dispatchEvent(new Event('change'));
 assert(f.view().querySelector('textarea')?.value==='Borrador conservado al cambiar modo'&&f.calls.length===0);
});
await checks('[selectors] tabs are visually distinct while preserving ARIA keyboard and responsive behavior',()=>{
 const f=fixture(),selected=f.button('Arquitectura'),other=f.button('ADR');
 assert(getComputedStyle(selected).backgroundColor!==getComputedStyle(other).backgroundColor);
 assert(parseFloat(getComputedStyle(selected).borderTopLeftRadius)>0&&parseFloat(getComputedStyle(selected).borderTopWidth)>parseFloat(getComputedStyle(other).borderTopWidth));
 selected.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));assert(f.button('Opciones tecnológicas').getAttribute('aria-selected')==='true');
 assert(document.documentElement.scrollWidth<=innerWidth+2&&f.view().querySelectorAll('[role="tab"]').length===3);
});

const result=document.createElement('pre');result.id='ux01c-test-result';result.textContent=JSON.stringify({status:outcomes.every(x=>x.pass)?'PASS':'BLOCK',cases:outcomes.length,focus:focused?'selectors':'all',viewport:{width:innerWidth,height:innerHeight},results:outcomes});document.body.append(result);
document.body.dataset.focalResult=outcomes.every(x=>x.pass)?'PASS':'BLOCK';
}
void main().catch(e=>{const pre=document.createElement('pre');pre.id='ux01c-test-result';pre.textContent=JSON.stringify({status:'BLOCK',error:String(e),results:outcomes});document.body.append(pre);});
