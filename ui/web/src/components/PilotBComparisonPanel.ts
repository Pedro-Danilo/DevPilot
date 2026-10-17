import { DevPilotApiClient, DevPilotApiError } from '../api/client';

// R02-06: context-bound review of D vs real local L. No artifact approval or FROZEN.
type Stage = 'vision'|'scope'|'requirements';
type Route = 'deterministic'|'local-model';
type Classification = 'EQUIVALENT'|'REDUCED'|'MODEL_REQUIRED';
interface CandidateRow { candidate?: {candidate_id?:string;content_sha256?:string;payload?: {title?:string;content?:string;evidence_refs?:string[]};origin?: {provider_id?:string;model_id?:string};provenance?: {latency_ms?:number}}; status?:string; observed?:Record<string,unknown>; }
interface ReviewState {selected_candidate_id?:string;classification?:Classification;reason?:string;}
interface ComparisonState {project_id?:string;stage?:Stage;input_sha256?:string;source_sha256?:string;candidates?:Partial<Record<Route,CandidateRow>>;review?:ReviewState|null;}

function el<K extends keyof HTMLElementTagNameMap>(tag:K,text?:string):HTMLElementTagNameMap[K]{
 const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;
}
function button(label:string, disabled=false):HTMLButtonElement{
 const node=el('button',label);node.type='button';node.disabled=disabled;return node;
}
function caption(parent:HTMLElement,name:string,value:string):void{
 const line=el('p');line.append(el('strong',name+': '),document.createTextNode(value));parent.append(line);
}

export function renderPilotBComparisonPanel(token:()=>string):HTMLElement {
 const root=el('section');root.className='panel';root.dataset.devpilotUiContract='ui.r02-06-pilot-b-comparison';
 const api=new DevPilotApiClient({token:token()});
 let stage:Stage='vision';let data:ComparisonState|null=null;let busy=false;let notice='Seleccione etapa y consulte el contexto activo.';
 let model='qwen2.5:3b-instruct';let selectedId='';let classification:Classification='REDUCED';let reason='';
 let authRequired=false;let localNotice='';let initialOwnerId='';
 const isAuthExpired=(error:unknown):boolean=>error instanceof DevPilotApiError && error.status===401;
 function authRecovery():void{
  authRequired=true;
  localNotice='BLOCK · La sesión humana ya no está activa. No se guardó ninguna decisión. El texto y la selección siguen aquí. Reautentícate como el mismo Owner y confirma después manualmente.';
 }
 function setReviewFeedback(message:string):void{localNotice=message;draw();}

 function draw():void{
  root.replaceChildren();root.append(el('h2','Pilot B · Comparar alternativas D / L'));
  root.append(el('p','R02-06 · Comparación experimental vinculada a Pilot B. No es el editor definitivo de Product Vision: D preserva la necesidad B0 y L es una propuesta no confiable que requiere evaluación humana. No hay aprobación ni publicación FROZEN.'));
  const label=el('label','Etapa documental: ');const select=el('select');select.setAttribute('aria-label','Etapa a comparar');
  ([['vision','Visión'],['scope','Alcance MVP'],['requirements','Requisitos']] as const).forEach(([id,name])=>{
   const opt=el('option',name);opt.value=id;opt.selected=id===stage;select.append(opt);
  });
  select.disabled=busy;select.addEventListener('change',()=>{stage=select.value as Stage;data=null;notice='Etapa cambiada; consultar recibos.';selectedId='';reason='';draw();});
  label.append(select);const refresh=button('Consultar recibos de Pilot B',busy);refresh.addEventListener('click',()=>void load());
  root.append(label,refresh);
  const status=el('p',notice);status.setAttribute('role','status');status.setAttribute('aria-live','polite');root.append(status);
  if(!data)return;
  caption(root,'Identidad activa (backend)',data.project_id||'NO_DISPONIBLE');
  caption(root,'SHA contexto',data.source_sha256||'NO_DISPONIBLE');
  caption(root,'SHA input canónico',data.input_sha256||'NO_DISPONIBLE');
  const actions=el('div');actions.className='model-lab-grid';
  const dPanel=el('div');dPanel.append(el('h3','Ruta D · reproducible / sin modelo'));
  dPanel.append(el('p','Proyección extractiva conservadora. No pretende generar RF profesionales ni establecer equivalencia semántica.'));
  const dRun=button('Generar referencia D (runtime-only)',busy||!!data.candidates?.deterministic||!!data.review);
  dRun.addEventListener('click',()=>void run('deterministic'));dPanel.append(dRun);actions.append(dPanel);
  const lPanel=el('div');lPanel.append(el('h3','Ruta L · Ollama REAL (solo localhost)'));
  lPanel.append(el('p','Una sola inferencia acotada; costo API $0, utiliza recursos locales. Sin fallback a D o API externa.'));
  const ml=el('label','Modelo Ollama instalado: ');const modelInput=el('input');modelInput.value=model;modelInput.maxLength=100;
  modelInput.setAttribute('aria-label','Identificador exacto del modelo Ollama');modelInput.addEventListener('input',()=>{model=modelInput.value.trim();});
  ml.append(modelInput);lPanel.append(ml);
  const lRun=button('Ejecutar inferencia L local (opt-in)',busy||!!data.candidates?.['local-model']||!!data.review);
  lRun.addEventListener('click',()=>void run('local-model'));lPanel.append(lRun);actions.append(lPanel);root.append(actions);
  const candidates=data.candidates||{};
  for(const route of ['deterministic','local-model'] as Route[]){
   const current=candidates[route];if(!current?.candidate)continue;
   const candidate=current.candidate;
   const section=el('section');section.className='panel';section.append(el('h3',route==='deterministic'?'D · candidato':'L · candidato'));
   caption(section,'Candidate ID',candidate.candidate_id||'');caption(section,'SHA contenido',candidate.content_sha256||'');
   caption(section,'Proveedor / modelo',`${candidate.origin?.provider_id||''} / ${candidate.origin?.model_id||''}`);
   caption(section,'Latencia',candidate.provenance?.latency_ms===undefined?'NO DISPONIBLE':`${candidate.provenance.latency_ms} ms`);
   const details=el('details');details.open=true;details.append(el('summary',candidate.payload?.title||'Ver propuesta completa'));
   const pre=el('pre',candidate.payload?.content||'Sin contenido');pre.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere;max-height:24rem;overflow:auto';details.append(pre);
   details.append(el('p',`Fuentes declaradas: ${(candidate.payload?.evidence_refs||[]).join(', ')}`));section.append(details);root.append(section);
  }
  if(data.review){
   root.append(el('h3','Revisión Owner registrada (inmutable)'));
   caption(root,'Selección',data.review.selected_candidate_id||'');caption(root,'Clasificación',data.review.classification||'');
   caption(root,'Justificación',data.review.reason||'');root.append(el('p','Esto NO aprueba documentación ni autoriza FROZEN.'));const done=el('p','PASS · Decisión consultada desde el servidor.');done.setAttribute('role','status');root.append(done);return;
  }
  if(!candidates.deterministic||!candidates['local-model']){
   root.append(el('p','La decisión se habilita solo con un candidato D y un candidato Ollama REAL vinculados al mismo contexto.'));
   return;
  }
  const review=el('section');review.className='panel';review.append(el('h3','Revisión humana y decisión'));
  review.append(el('p','Examine contenido, afirmaciones sin fuente, contradicciones, idioma, preguntas abiertas y verificabilidad. D no equivale a una Vision profesional; L podría omitir restricciones. Clasifique EQUIVALENT solo con respaldo explícito.'));
  const warning=el('p','Idioma requerido: español. La instrucción a Ollama lo solicita, pero no garantiza cumplimiento. Si L está en inglés, registre la desviación como un hallazgo; no regenere ni sobrescriba el candidato inmutable.');
  warning.style.cssText='border-left:3px solid #64748b;padding:.5rem .8rem;background:rgba(100,116,139,.07)';review.append(warning);

  const chooseLabel=el('label','Candidato a seleccionar: ');const choose=el('select');choose.setAttribute('aria-label','Candidato elegido');
  ([candidates.deterministic,candidates['local-model']] as CandidateRow[]).forEach((row,index)=>{
   const id=row.candidate?.candidate_id||'';const option=el('option',`${index===0?'D':'L'} — ${id}`);option.value=id;choose.append(option);
  });
  if(!selectedId)selectedId=choose.options[0].value;choose.value=selectedId;
  choose.addEventListener('change',()=>{selectedId=choose.value;});chooseLabel.append(choose);review.append(chooseLabel);
  const qualityLabel=el('label','Clasificación semántica: ');const qualitySelect=el('select');qualitySelect.setAttribute('aria-label','Evaluación comparativa');
  ([['EQUIVALENT','Equivalencia argumentada'],['REDUCED','Cobertura reducida'],['MODEL_REQUIRED','Requiere modelo para este objetivo']] as const).forEach(([value,title])=>{
   const option=el('option',title);option.value=value;qualitySelect.append(option);
  });qualitySelect.value=classification;qualitySelect.addEventListener('change',()=>{classification=qualitySelect.value as Classification;});
  qualityLabel.append(qualitySelect);review.append(qualityLabel);
  const reasonLabel=el('label','Motivo Owner, fuentes y diferencias observadas:');const textarea=el('textarea');textarea.value=reason;textarea.rows=5;textarea.maxLength=2000;
  textarea.setAttribute('aria-label','Justificación de la selección');textarea.addEventListener('input',()=>{reason=textarea.value;});reasonLabel.append(textarea);review.append(reasonLabel);review.append(el('p','Máximo 2000 caracteres. La decisión sólo se registra después de autenticar y confirmar; el texto sigue editable ante un BLOCK.'));
  const feedback=el('div');feedback.dataset.devpilotUiContract='ui.r02-06-local-feedback';feedback.style.cssText='margin:.7rem 0;padding:.8rem;border-left:4px solid #2563eb;background:rgba(37,99,235,.07);overflow-wrap:anywhere';
  feedback.setAttribute('role',localNotice.startsWith('BLOCK')?'alert':'status');feedback.setAttribute('aria-live','polite');feedback.textContent=localNotice||'PENDIENTE · Aún no se ha registrado esta revisión. Puede analizarla el tiempo que necesite.';review.append(feedback);
  if(authRequired){
   const auth=el('form');auth.className='auth-form';auth.setAttribute('aria-label','Reautenticación local para conservar revisión');
   const heading=el('h4','Reautenticar Owner sin perder el borrador');auth.append(heading);
   const userLabel=el('label','Usuario Owner');const username=el('input');username.required=true;username.autocomplete='username';userLabel.append(username);
   const passLabel=el('label','Contraseña');const password=el('input');password.type='password';password.required=true;password.autocomplete='current-password';passLabel.append(password);
   const reconnect=button('Reautenticar (sin registrar revisión)',busy);reconnect.type='submit';
   auth.append(userLabel,passLabel,reconnect);
   auth.addEventListener('submit',event=>{event.preventDefault();void reauthenticate(username.value,password.value);password.value='';});
   review.append(auth);
  }
  const submit=button('Confirmar selección Owner sin publicar',busy||authRequired);submit.dataset.devpilotUiContract='ui.r02-06-review-submit';submit.addEventListener('click',()=>void decide());review.append(submit);root.append(review);

 }
 async function load():Promise<void>{if(busy)return;busy=true;notice='Consultando solo Pilot B activo…';draw();
  try{const response=await api.pilotBComparisonStatus(stage);if(!response.ok)throw new Error(String((response.data as any)?.reason||response.message));
   data=response.data as ComparisonState;notice='PASS · Recibos server-authoritative consultados.';
   try{const s=await api.authSession();if(!initialOwnerId)initialOwnerId=s.session.principal.actor_id;}
   catch(err){if(isAuthExpired(err))authRecovery();}

  }catch(err){data=null;notice='BLOCK · '+(err instanceof Error?err.message:'No se recuperó el proyecto');}
  finally{busy=false;draw();}
 }
 async function run(route:Route):Promise<void>{if(busy)return;
  if(route==='local-model'&&!window.confirm(`¿Autoriza UNA inferencia REAL en Ollama local con el modelo ${model} para ${stage}? No usa API externa, no publica.`))return;
  busy=true;notice=`Ejecutando ruta ${route}…`;draw();
  try{const response=await api.pilotBComparisonCandidate({stage,route,model:route==='local-model'?model:'',execute:route==='local-model'});
   if(!response.ok)throw new Error(String((response.data as any)?.reason||response.message));notice=`PASS · Candidato ${route} persistido, sin aprobar.`;
   const status=await api.pilotBComparisonStatus(stage);if(!status.ok)throw new Error(String((status.data as any)?.reason||status.message));data=status.data as ComparisonState;
  }catch(err){notice='BLOCK · '+(err instanceof Error?err.message:'No se generó candidato');}
  finally{busy=false;draw();}
 }
 async function reauthenticate(username:string,password:string):Promise<void>{
  if(busy||!authRequired)return;busy=true;
  localNotice='Validando credenciales con autenticación local…';draw();
  try{
   // Uses the same HttpOnly cookie + CSRF login contract as LoginView; never stores credentials.
   const logged=await api.authLogin({username,password});
   if(!logged.ok||!logged.session?.principal?.roles?.includes('owner'))throw new Error('La nueva sesión no acredita rol Owner.');
   if(initialOwnerId&&logged.session.principal.actor_id!==initialOwnerId)throw new Error('La identidad Owner cambió: no se permite reasignar silenciosamente esta revisión.');
   authRequired=false;localNotice='PASS · Sesión Owner renovada. Justificación conservada; comprueba el texto y pulsa Confirmar cuando estés listo.';
  }catch(err){authRequired=true;localNotice='BLOCK · '+(isAuthExpired(err)?'Credenciales no aceptadas por la API local.':err instanceof Error?err.message:'No se pudo reautenticar');}
  finally{busy=false;draw();}
 }
 async function decide():Promise<void>{
  if(busy||authRequired||!data?.input_sha256||!selectedId)return;
  if(reason.trim().length<20||reason.length>2000){setReviewFeedback('BLOCK · Justificación requerida (entre 20 y 2000 caracteres). Nada se ha guardado.');return;}
  busy=true;localNotice='Comprobando sesión Owner antes de registrar…';draw();
  try{
   const sessionStatus=await api.authSessionStatus();
   if(!sessionStatus.authenticated||sessionStatus.state!=='active'){authRecovery();return;}
   const session=await api.authSession();
   if(!session.session.principal.roles.includes('owner'))throw new Error('Esta cuenta no tiene rol Owner.');
   if(initialOwnerId&&session.session.principal.actor_id!==initialOwnerId)throw new Error('Se detectó otro Owner. La revisión no se registró.');
   if(!window.confirm('¿Registrar esta selección humana INMUTABLE? El texto ya está revisado. No se publicará ningún documento.')){
    localNotice='PENDIENTE · Confirmación cancelada. El texto continúa intacto.';return;
   }
   localNotice='Guardando decisión Owner exacta…';draw();
   const response=await api.pilotBComparisonReview({stage,candidate_id:selectedId,classification,reason,expected_input_sha256:data.input_sha256});
   if(!response.ok)throw new Error(String((response.data as any)?.reason||response.message));
   const status=await api.pilotBComparisonStatus(stage);
   if(!status.ok)throw new Error(String((status.data as any)?.reason||status.message));
   data=status.data as ComparisonState;localNotice='PASS · Selección registrada en recibo inmutable.';notice='PASS · Revisión Owner persistida, sin FROZEN.';
  }catch(err){
   if(isAuthExpired(err))authRecovery();
   else localNotice='BLOCK · '+(err instanceof Error?err.message:'Revisión rechazada. Conservar el texto.');
  }finally{busy=false;draw();}
 }
 void load();return root;
}
