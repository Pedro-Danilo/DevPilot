import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { AuthSessionContext, PreCodeWizardProjection, PreCodeWizardStage, ArchitectureDocumentKind } from '../api/types';
import { renderSafeMarkdown } from './DocumentViewer';

const labels: Record<ArchitectureDocumentKind, string> = {architecture:'Arquitectura', technology_options:'Opciones tecnológicas', adr:'ADR'};
const kinds = Object.keys(labels) as ArchitectureDocumentKind[];
const memory = new Map<string, {busy:boolean; uncertain:boolean; startedAt?:number}>();

export function renderArchitectureWorkbench(options: {
  projection: PreCodeWizardProjection; session: AuthSessionContext;
  client: () => DevPilotApiClient; refresh: (message?:string) => Promise<void>;
  lifecycle?: HTMLElement; companion?: HTMLElement;
}): HTMLElement {
  const p = options.projection;
  const arch = p.stages.find(s=>s.stage_id==='architecture')!;
  const owner = options.session.principal.roles.includes('owner') && options.session.principal.workspace_scopes.includes(p.workspace_id);
  const state = memory.get(p.workspace_id) ?? {busy:false, uncertain:false}; memory.set(p.workspace_id,state);
  const key = `ux01C:${p.workspace_id}`;
  const read = (suffix:string) => {try{return sessionStorage.getItem(`${key}:${suffix}`);}catch{return null;}};
  const store = (suffix:string,value:string|null) => {try{value===null?sessionStorage.removeItem(`${key}:${suffix}`):sessionStorage.setItem(`${key}:${suffix}`,value);}catch{/* preference/draft persistence is optional, never authority */}};
  let active = kinds.find(k=>k===read('tab')) ?? 'architecture';
  let editing = false, preview = false, feedback = '', blockedFeedback = false;
  const host=document.createElement('section'); host.className='panel architecture-workbench';host.dataset.architectureWorkbench='true';
  host.setAttribute('aria-label','Architecture Workbench');
  let elapsed:HTMLElement|null=null;
  const seconds=()=>Math.max(0,Math.floor((Date.now()-(state.startedAt??Date.now()))/1000));
  const pendingReceipt=(p.r03_04_authoring?.activity??[]).some(a=>a.status==='IN_PROGRESS');
  const pendingServer=p.architecture_inference_pending || pendingReceipt;
  if(read('pending')) state.uncertain=true;
  if(!state.busy && read('pending') && !pendingServer){
    let marker:any={};try{marker=JSON.parse(read('pending')!);}catch{/* unknown pending marker stays blocked */}
    const receipt=(p.r03_04_authoring?.activity??[]).find(a=>a.kind===marker.kind);
    const terminal=receipt && ['COMPLETE','BLOCK'].includes(receipt.status??'') && receipt.candidate_id!==marker.before;
    const changedDoc=p.architecture_workbench_documents?.[marker.document as ArchitectureDocumentKind]?.sha256;
    const changed=changedDoc && changedDoc!==marker.beforeSha;
    const transition=arch.status!==marker.stageStatus || p.r03_04_authoring?.selected_option_id!==marker.selection;
    if(terminal || changed || transition || (marker.kind==='architecture' && arch.content_sha256!==marker.before && arch.status!=='MISSING')){
      store('pending',null);state.uncertain=false;
    }
  }
  const serverDoc=(kind:ArchitectureDocumentKind) => p.architecture_workbench_documents?.[kind] ?? {
    content:kind==='architecture'?(arch.draft_content??''):(kind==='adr'?p.r03_04_authoring?.adr?.content:p.r03_04_authoring?.technology?.content)??'',
    status:kind==='architecture'?arch.status:'REVIEW_REQUIRED',can_edit:false,sha256:'',source:'DTO pendiente de actualizar',quality:null};
  const draft=(kind:ArchitectureDocumentKind) => {
    try{return JSON.parse(read(`draft:${kind}`)??'null') as {text:string;base:string}|null;}catch{return null;}
  };
  const dirty=() => kinds.some(k=>{const d=draft(k);return d && d.text!==serverDoc(k).content;});
  const busy=() => state.busy || Boolean(pendingServer) || state.uncertain;
  const mayMutate=() => owner && p.current_stage_id==='architecture' && !arch.approval_id && ['MISSING','DRAFT','FINDINGS','APPROVAL_REQUIRED'].includes(arch.status);
  type AuthoringMode=PreCodeWizardStage['allowed_modes'][number];
  const modeLabels:Record<AuthoringMode,string>={LOCAL_MODEL:'Modelo local · asistente de redacción',DEVPL_MOCK:'DevPilot · Diseño local + RAG / sin API',MANUAL:'Manual',IMPORT:'Importar archivo local'};
  const supportedModes=arch.allowed_modes.filter(value=>Object.hasOwn(modeLabels,value));
  let authoringMode=supportedModes.includes(arch.mode as AuthoringMode)?arch.mode as AuthoringMode:supportedModes.includes('LOCAL_MODEL')?'LOCAL_MODEL':supportedModes[0];
  const preferredModel=String(arch.derivation?.model??p.r03_04_authoring?.technology?.model??'');
  let model='',installedModels:string[]=[],modelState:'idle'|'loading'|'ready'|'empty'|'error'='idle';
  const requiresModel=()=>active!=='architecture'||authoringMode==='LOCAL_MODEL';
  const usableModel=()=>modelState==='ready'&&installedModels.includes(model);
  async function discoverModels():Promise<void>{
    if(modelState==='loading'||!mayMutate()||busy())return;
    modelState='loading';draw();
    try{
      const result=await options.client().probeLocalModelReadiness();
      if(!result.ok)throw new Error('Readiness not confirmed');
      const providers=(result.data as {providers?:Array<{provider_id?:string;healthy?:boolean;models?:string[]}>}).providers??[];
      const ollama=providers.find(row=>row.provider_id==='ollama');
      installedModels=ollama?.healthy===true?[...new Set((ollama.models??[]).filter(value=>typeof value==='string'&&/^[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,99}$/.test(value)&&!value.includes('://')))]:[];
      model=installedModels.includes(model)?model:installedModels.includes(preferredModel)?preferredModel:installedModels.length===1?installedModels[0]:'';
      modelState=installedModels.length?'ready':'empty';
    }catch{installedModels=[];model='';modelState='error';}
    draw();
  }

  const button=(text:string,action:()=>void,reason='') => {
    const b=document.createElement('button');b.type='button';b.textContent=text;b.disabled=Boolean(reason);b.title=reason;
    if(reason)b.setAttribute('aria-description',reason);
    b.addEventListener('click',action);return b;
  };
  async function action(name:string,operation:()=>Promise<{ok:boolean;message:string}>,inference=false,kind=active):Promise<void>{
    if(busy() || !mayMutate() || (dirty() && !name.startsWith('Guardar'))){feedback='Acción bloqueada por estado, sesión o trabajo pendiente.';blockedFeedback=true;draw();return;}
    state.busy=true;state.startedAt=Date.now();feedback=inference?`Generando ${labels[kind]} con modelo local…`:`${name}…`;blockedFeedback=false;
    const receiptKind=kind==='technology_options'?'technology':kind;
    store('pending',JSON.stringify({document:kind,beforeSha:serverDoc(kind).sha256,stageStatus:arch.status,selection:p.r03_04_authoring?.selected_option_id,kind:receiptKind,before:kind==='architecture'?arch.content_sha256:(kind==='adr'?p.r03_04_authoring?.adr?.candidate_id:p.r03_04_authoring?.technology?.candidate_id)}));
    draw();
    try{
      await options.client().authSession();
      const result=await operation();
      if(!result.ok)throw new Error(result.message);
      state.busy=false;state.uncertain=false;store('pending',null);
      await options.refresh(`${name}: operación conservada. Revisa el estado y el recibo.`);
    }catch(error){
      state.busy=false;blockedFeedback=true;
      const http=error instanceof DevPilotApiError?error.status:null;
      state.uncertain=http===0 || http===500 || http===null;
      if(!state.uncertain)store('pending',null);
      feedback=http===409?'Conflicto 409: conserva tu revisión. Si el plan venció, renueva plan/diff sobre los mismos bytes; no repitas approval ni inferencia.':http===500?'Error del servidor (500). Revisión conservada; consulta recibos antes de reintentar.':http===0?'Respuesta de red incierta. Revisión conservada; consulta el estado antes de otra solicitud.':http===401||http===403?'Sesión/permiso no válido; vuelve a autenticarte. Se conserva tu revisión.':inference?'No se confirmó la generación. Consulta el recibo y conserva el candidato; no hay reintento automático.':error instanceof Error?error.message:'Operación no confirmada; revisión conservada.';
      draw();
    }
  }
  const techAction=(name:string,extra:Record<string,unknown>={},inference=false,kind=active) => {
    const doc=serverDoc(kind);
    if(inference&&!usableModel()){feedback='Selecciona un modelo realmente disponible antes de generar.';blockedFeedback=true;draw();return;}
    void action(name,()=>options.client().preCodeTechnologyAction({action:name as 'generate_options', model,
      generation_epoch:inference?arch.derivation?.generation_epoch:(doc.generation_epoch??arch.derivation?.generation_epoch),
      ...(doc.sha256?{expected_sha256:doc.sha256}:{}),...extra}),inference,kind);
  };
  function draw():void{
    host.replaceChildren();
    const h=document.createElement('h3');h.textContent='Architecture Workbench';
    const common=document.createElement('p');common.className='architecture-workbench__facts';
    const doc=serverDoc(active), q=doc.quality?.current;
    common.textContent=`Proyecto ${p.project_name??p.workspace_id} · workspace ${p.workspace_id} · etapa ${arch.status} · ${labels[active]} ${doc.status} · candidato ${doc.candidate_id??doc.sha256??'SIN GENERAR'} · fuente ${doc.source} · opción Owner ${p.r03_04_authoring?.selected_option_id??'pendiente'} · calidad ${q?.quality_level??'sin evaluación'} · HANDOFF_READY ${q?.handoff_ready===true?'acreditado':'no acreditado'}`;
    const next=document.createElement('p');next.textContent=arch.status==='FROZEN'?'Documentos en lectura. Companion conserva su plan/approval exactos.':dirty()?'Siguiente acción: guarda o descarta la revisión antes de cambiar dependencias.':busy()?'Siguiente acción: esperar o consultar el estado; no duplicar inferencia.':'Siguiente acción: revisar documento → opciones → elección Owner → ADR → conciliación → diff/approval.';
    const status=document.createElement('p');status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.dataset.workbenchFeedback='true';
    status.className=blockedFeedback?'notice notice--block':'notice notice--info';status.textContent=feedback || (pendingServer?'Inferencia en curso o interrumpida según el recibo; consulta el estado.':state.uncertain?'Resultado incierto. Consulta el estado antes de reintentar.':'Estado obtenido del servidor; la estructura no acredita calidad profesional.');
    elapsed=document.createElement('span');if(state.busy)elapsed.textContent=` Tiempo transcurrido: ${seconds()} s.`;status.append(elapsed);
    host.append(h,common,next,status,button('Consultar estado y recibos',()=>{void options.refresh();},state.busy?'Espera a que termine la solicitud activa.':''));
    const nav=document.createElement('div');nav.setAttribute('role','tablist');nav.setAttribute('aria-label','Documentos Architecture');
    for(const kind of kinds){
      const b=button(labels[kind],()=>{active=kind;editing=false;preview=false;store('tab',kind);draw();});
      b.setAttribute('role','tab');b.id=`ux01c-${kind}-tab`;b.setAttribute('aria-selected',String(active===kind));b.setAttribute('aria-controls','ux01c-panel');b.tabIndex=active===kind?0:-1;
      b.addEventListener('keydown',(e)=>{let i=kinds.indexOf(kind);if(e.key==='ArrowRight')i=(i+1)%3;else if(e.key==='ArrowLeft')i=(i+2)%3;else if(e.key==='Home')i=0;else if(e.key==='End')i=2;else return;e.preventDefault();active=kinds[i];editing=false;store('tab',active);draw();host.querySelector<HTMLElement>(`#ux01c-${active}-tab`)?.focus();});
      nav.append(b);
    }
    host.append(nav);
    const panel=document.createElement('section');panel.id='ux01c-panel';panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby',`ux01c-${active}-tab`);
    const saved=draft(active), stale=saved && saved.base!==doc.sha256;
    const canEdit=owner && mayMutate() && doc.can_edit && !busy();
    if(saved && saved.text!==doc.content){const note=document.createElement('p');note.textContent=stale?'Hay una revisión local de otro candidato. Consérvala o descártala; no se guardará sobre la versión nueva.':'Revisión Owner sin guardar conservada localmente; no concede aprobación.';panel.append(note);}
    if(!editing || preview){
      const article=document.createElement('article');article.className='architecture-workbench__markdown';article.dataset.workbenchDocument=active;
      if(doc.status==='BLOCK')article.textContent=`BLOCK: no se puede acreditar el documento (${doc.error_code??'integridad'}).`;
      else if(!doc.content && !(preview&&saved))article.textContent='SIN GENERAR: no existe documento para esta pestaña.';
      else renderSafeMarkdown(article,preview&&saved?saved.text:doc.content);
      panel.append(article);
    }else{
      const editor=document.createElement('textarea');editor.value=saved?.text??doc.content;editor.rows=22;editor.readOnly=busy()||!canEdit;editor.setAttribute('aria-label',`Revisión Owner de ${labels[active]}`);editor.dataset.workbenchEditor=active;
      editor.addEventListener('input',()=>{store(`draft:${active}`,JSON.stringify({text:editor.value,base:saved?.base??doc.sha256}));});panel.append(editor);
    }
    panel.append(button(editing?'Vista Markdown':'Editar revisión Owner',()=>{editing=!editing;preview=false;draw();},!canEdit?'Lectura: requiere Owner, etapa vigente y ausencia de operación/approval activo.':''));
    if(editing){
      panel.append(button(preview?'Volver al editor':'Previsualizar revisión',()=>{preview=!preview;draw();}));
      panel.append(button('Cancelar edición (conservar borrador)',()=>{editing=false;preview=false;draw();}));
      panel.append(button('Descartar revisión local',()=>{if(window.confirm('¿Descartar solo la revisión local sin guardar?')){store(`draft:${active}`,null);draw();}}));
      panel.append(button('Guardar revisión Owner',()=>{
        const kind=active; const value=draft(kind);if(!value || stale)return;
        if(kind==='architecture'){
          if(!supportedModes.includes(authoringMode)){feedback='El servidor no ofrece un modo de autoría soportado.';draw();return;}
          if(arch.mode&&arch.mode!==authoringMode&&doc.content&&!window.confirm('Guardar con otro modo invalida el plan/diff dependiente. La fuente FROZEN no se modifica. ¿Continuar?'))return;
          const mode=authoringMode;
          void action('Guardar revisión',async()=>{const r=await options.client().preCodeDraft('architecture',{mode,content:value.text,...(mode==='LOCAL_MODEL'?{model}:{}),semantic_model:null});if(r.ok)store(`draft:${kind}`,null);return r;});
        }
        else{
          if(kind==='technology_options' && p.r03_04_authoring?.selected_option_id && !window.confirm('La revisión invalidará elección, ADR, conciliación y plan dependientes. ¿Continuar?'))return;
          void action('Guardar revisión',async()=>{const r=await options.client().preCodeTechnologyAction({action:kind==='adr'?'owner_revise_adr':'owner_revise_options',content:value.text,expected_sha256:doc.sha256,generation_epoch:doc.generation_epoch});if(r.ok)store(`draft:${kind}`,null);return r;});
        }
      },!canEdit||Boolean(stale)?'No se puede guardar una revisión obsoleta o sin permiso.':''));
    }
    const quality=document.createElement('details');const summary=document.createElement('summary');summary.textContent='Calidad, fuentes y tareas de reparación';quality.append(summary);
    for(const f of q?.findings??[]){const item=document.createElement('p');item.textContent=`${f.severity} · ${f.section_id}: ${f.why}. Reparación: ${f.suggested_fix}`;quality.append(item);}
    const facts=document.createElement('pre');facts.textContent=JSON.stringify({sources:q?.sources??[],before_owner:doc.quality?.before_owner?.quality_level,epoch:doc.generation_epoch,receipts:p.r03_04_authoring?.activity??[]},null,2);quality.append(facts);panel.append(quality);
    const actions=document.createElement('div');actions.className='architecture-workbench__actions';
    const reason=!mayMutate()?'Lectura: etapa/rol/approval no permite mutaciones.':busy()?'Trabajo en curso o resultado incierto; consulta recibos.':dirty()?'Guarda o descarta las revisiones antes de cambiar dependencias.':'';
    if(active==='architecture'){
      const label=document.createElement('label');label.textContent='Modo de autoría';
      const select=document.createElement('select');select.setAttribute('aria-label','Modo de autoría');
      for(const value of supportedModes){const item=document.createElement('option');item.value=value;item.textContent=modeLabels[value];select.append(item);}
      select.value=authoringMode??'';select.disabled=!mayMutate()||busy()||supportedModes.length===0;
      select.addEventListener('change',()=>{authoringMode=select.value as AuthoringMode;draw();if(requiresModel()&&modelState==='idle')void discoverModels();});
      label.append(select);actions.append(label);
    }
    const modelLabel=document.createElement('label');modelLabel.textContent='Modelo Ollama instalado';
    const modelSelect=document.createElement('select');modelSelect.setAttribute('aria-label','Modelo Ollama instalado');
    const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=modelState==='loading'?'Consultando modelos…':installedModels.length?'Selecciona un modelo instalado':'Sin modelos disponibles';modelSelect.append(placeholder);
    for(const value of installedModels){const item=document.createElement('option');item.value=value;item.textContent=value;modelSelect.append(item);}
    modelSelect.value=model;modelSelect.disabled=!mayMutate()||busy()||modelState!=='ready'||!requiresModel();
    modelSelect.addEventListener('change',()=>{model=installedModels.includes(modelSelect.value)?modelSelect.value:'';draw();});modelLabel.append(modelSelect);actions.append(modelLabel);
    actions.append(button('Consultar modelos instalados',()=>{void discoverModels();},!mayMutate()?'Consulta no disponible en lectura.':busy()?'Espera o consulta el recibo activo.':modelState==='loading'?'Consulta de modelos en curso.':''));
    const modelNote=document.createElement('p');modelNote.className='architecture-workbench__model-note';modelNote.setAttribute('role','status');
    modelNote.textContent=!mayMutate()?'Documento en lectura: generación y edición deshabilitadas.':!requiresModel()?'Este modo no requiere modelo Ollama. Conserva revisión, validación y approval gobernados.':modelState==='loading'?'Consultando el servicio local existente; no se ejecuta inferencia.':modelState==='ready'?`${installedModels.length} modelo(s) instalado(s) disponible(s); elige uno antes de generar.`:modelState==='error'?'No se pudo consultar Ollama. No se inició inferencia; solo queda bloqueada la generación con modelo.':modelState==='empty'?'No hay modelos Ollama disponibles. La generación local está bloqueada; puedes revisar, guardar o usar otro modo permitido sin instalar modelos.':'Consulta los modelos instalados antes de generar.';
    actions.append(modelNote);
    let importFile:HTMLInputElement|undefined;
    if(active==='architecture'&&authoringMode==='IMPORT'){
      const label=document.createElement('label');label.textContent='Archivo Markdown para importar';
      importFile=document.createElement('input');importFile.type='file';importFile.accept='.md,text/markdown,text/plain';importFile.setAttribute('aria-label','Archivo Markdown para importar');importFile.disabled=!mayMutate()||busy();
      importFile.addEventListener('change',()=>{const selected=importFile?.files?.[0];if(!selected)return;const base=serverDoc('architecture').sha256;void selected.text().then(text=>{store('draft:architecture',JSON.stringify({text,base}));active='architecture';editing=true;preview=false;draw();});});label.append(importFile);actions.append(label);
    }
    const generate=(kind:ArchitectureDocumentKind)=>{
      if(reason||dirty()){feedback=reason||'Guarda o descarta la revisión antes de generar.';draw();return;}
      if(kind==='architecture'&&(authoringMode==='MANUAL'||authoringMode==='IMPORT')){
        if(authoringMode==='IMPORT')importFile?.click();else{editing=true;preview=false;draw();}return;
      }
      const local=kind!=='architecture'||authoringMode==='LOCAL_MODEL';
      if(local&&!usableModel()){feedback='Selecciona un modelo realmente instalado; no se instala ninguno.';draw();return;}
      if(kind==='architecture'&&!supportedModes.includes(authoringMode)){feedback='Modo de autoría no soportado.';draw();return;}
      const exists=Boolean(serverDoc(kind).content);
      if(exists && !window.confirm('Se conserva el candidato anterior. La sucesión invalida elección/ADR/conciliación/plan dependientes. ¿Continuar?'))return;
      if(kind==='architecture'){const mode=authoringMode;void action(mode==='LOCAL_MODEL'?'Generar Architecture':'Generar propuesta determinística',()=>options.client().preCodeDraft('architecture',{mode,content:'',semantic_model:null,...(mode==='LOCAL_MODEL'?{model,regenerate:exists}:{})}),mode==='LOCAL_MODEL',kind);}
      else techAction(kind==='adr'?'generate_adr':'generate_options',{successor:exists,expected_sha256:undefined},true,kind);
    };
    const dependency=active!=='architecture' && (arch.mode!=='LOCAL_MODEL'||!arch.draft_content)?'Primero genera y revisa Architecture LOCAL_MODEL.':active==='adr'&&!p.r03_04_authoring?.selected_option_id?'Primero elige una opción real.':'';
    const generationLabel=active==='architecture'&&authoringMode==='MANUAL'?'Escribir Architecture manual':active==='architecture'&&authoringMode==='IMPORT'?'Importar Markdown':active==='architecture'&&authoringMode==='DEVPL_MOCK'?'Generar propuesta determinística':doc.content?'Generar alternativa sucesora':active==='architecture'?'Generar/continuar una unidad Architecture':'Generar documento con modelo local';
    const modelBlock=requiresModel()&&!usableModel()?'Selecciona un modelo instalado disponible; otros controles siguen habilitados.':'';
    actions.append(button(generationLabel,()=>generate(active),reason||dependency||modelBlock||(active==='architecture'&&!supportedModes.length?'No hay modos soportados.':'')));
    if(active==='technology_options'){
      const choices=Array.from(doc.content.matchAll(/^##\s+Opci[oó]n\s+(T[1-3])\s*[—–:-]\s*(.+)$/gim));
      for(const choice of choices){const id=choice[1].toUpperCase(),selected=p.r03_04_authoring?.selected_option_id;
        actions.append(button(selected===id?`Seleccionada: ${id}`:`Elegir ${id} — ${choice[2]}`,()=>{
          if(selected && selected!==id && !window.confirm('Cambiar la elección invalida ADR, conciliación y plan. ¿Crear una selección sucesora?'))return;
          techAction('select_option',{option_id:id,successor:Boolean(selected&&selected!==id)},false,'technology_options');
        },reason||(selected===id?'Opción ya registrada.':'')));
      }
    }
    if(active==='adr')actions.append(button('Conciliar elección y ADR con Architecture',()=>techAction('reconcile',{expected_sha256:arch.content_sha256},false,'architecture'),reason||(!p.r03_04_authoring?.adr?.content?'Primero genera y revisa el ADR.':'')));
    if(active==='architecture')actions.append(button('Validar y preparar diff',()=>{void action('Validar y preparar diff',()=>options.client().preCodeReview('architecture'));},reason||(!doc.content?'Falta Architecture.':'')));
    if(q)actions.append(button('Consultar handoff offline',()=>{void (async()=>{try{const r=await options.client().preCodeTechnologyAction({action:'export_handoff',artifact_kind:active,expected_sha256:doc.sha256,generation_epoch:doc.generation_epoch});if(!r.ok)throw new Error(r.message);const pre=document.createElement('pre');pre.textContent=JSON.stringify(r.data.handoff,null,2);panel.append(pre);}catch{feedback='No se pudo exportar: revisa fuentes, candidato y permisos.';blockedFeedback=true;draw();}})();},busy()?'Consulta recibos primero.':''));
    panel.append(actions);host.append(panel);
    if(options.lifecycle){
      const lifecycle=options.lifecycle;
      if(!lifecycle.dataset.workbenchGuard){
        lifecycle.dataset.workbenchGuard='true';
        lifecycle.addEventListener('click',event=>{if(busy()||dirty()||!owner){event.preventDefault();event.stopPropagation();feedback='Conserva tu revisión y consulta el estado antes de continuar.';blockedFeedback=true;draw();}},true);
      }
      for(const b of lifecycle.querySelectorAll<HTMLButtonElement>('button')){
        b.dataset.initialDisabled??=String(b.disabled);b.disabled=Boolean(reason)||b.dataset.initialDisabled==='true';if(reason)b.title=reason;
      }
      host.append(lifecycle);
    }
    if(options.companion){
      for(const b of options.companion.querySelectorAll<HTMLButtonElement>('button')){
        b.dataset.initialDisabled??=String(b.disabled);b.disabled=!owner||busy()||b.dataset.initialDisabled==='true';if(b.disabled)b.title='Requiere Owner y ausencia de operación incierta.';
      }
      host.append(options.companion);
    }
  }
  draw();
  if(mayMutate()&&!busy()&&requiresModel())void discoverModels();
  const timer=setInterval(()=>{if(!host.isConnected){clearInterval(timer);return;}if(elapsed&&state.busy)elapsed.textContent=` Tiempo transcurrido: ${seconds()} s.`;},1000);
  return host;
}
