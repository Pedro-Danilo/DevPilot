/** R01-11. Accessible governed settings surface; no runtime permission effects. */
import { DevPilotApiClient } from '../api/client';

export function renderPersistentSettingsHome(clientFactory: () => DevPilotApiClient): HTMLElement {
  const card = document.createElement('section');
  card.className = 'card persistent-settings-home';
  card.dataset.settingsHome = 'R01-11';
  card.setAttribute('aria-label', 'Preferencias persistentes');
  const title = document.createElement('h3'); title.textContent = 'Preferencias persistentes';
  const guidance = document.createElement('p');
  guidance.textContent = 'Las preferencias guardadas no activan proveedores, red ni herramientas. Revocar un proveedor es una acción runtime separada.';
  const status = document.createElement('p'); status.id = 'persistent-settings-status';
  status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  const form = document.createElement('div'); form.className = 'settings-persist-form';
  const label = (name: string, control: HTMLElement) => { const node = document.createElement('label'); node.textContent = name; node.append(control); form.append(node); return node; };
  const scope = document.createElement('select'); scope.id = 'settings-scope';
  for (const value of ['platform','workspace','project']) { const option = document.createElement('option'); option.value=value; option.textContent=value; scope.append(option); }
  label('Ámbito', scope);
  const scopeId = document.createElement('input'); scopeId.id='settings-scope-id';scopeId.value='platform';label('Identificador del ámbito',scopeId);
  const workspace = document.createElement('input'); workspace.id='settings-workspace-id';workspace.placeholder='Workspace autorizado (solo proyecto)';label('Workspace del proyecto, cuando aplique',workspace);
  const key = document.createElement('select'); key.id='settings-key';
  for (const [value,name] of [['ui.detail_level','Detalle de interfaz'], ['generation.default_route','Ruta de generación (preferencia)'], ['generation.max_output_tokens','Límite sugerido de tokens']]) { const option=document.createElement('option'); option.value=value; option.textContent=name; key.append(option); }
  label('Preferencia',key);
  const value = document.createElement('select'); value.id='settings-value'; label('Valor propuesto',value);
  const origin=document.createElement('p');origin.id='settings-effective';origin.textContent='Valor efectivo pendiente.';
  const plan=document.createElement('pre');plan.id='settings-plan-preview';plan.textContent='No hay plan aprobado.';
  const load=document.createElement('button');load.type='button';load.id='settings-load';load.textContent='Consultar valor efectivo';
  const preview=document.createElement('button');preview.type='button';preview.id='settings-preview';preview.textContent='Vista previa sin escribir';
  const approve=document.createElement('input');approve.type='checkbox';approve.id='settings-write-confirm';
  const confirmLabel=document.createElement('label');confirmLabel.textContent='Confirmo guardar esta preferencia';confirmLabel.append(approve);
  const save=document.createElement('button');save.type='button';save.id='settings-save';save.textContent='Guardar con permiso Owner';save.disabled=true;
  const buttons=document.createElement('div');buttons.className='settings-action-row';buttons.append(load,preview,confirmLabel,save);
  card.append(title,guidance,form,origin,plan,buttons,status);
  let revision=0;let currentPlan: null | { scope: string; scope_id: string; key: string; value: string | number; expected_revision: number; workspace_id?: string }=null;
  let busy=false;
  function setStatus(message:string,kind:'pass'|'block'|'loading'='pass') {status.textContent=message;status.dataset.status=kind;}
  function invalidate(){currentPlan=null;approve.checked=false;save.disabled=true;plan.textContent='La propuesta cambió. Solicita una nueva vista previa.';}
  function choices(){value.replaceChildren();const options=key.value==='ui.detail_level'?['guided','expert']:key.value==='generation.default_route'?['deterministic','local']:['256','512','1024','2048'];for(const v of options){const option=document.createElement('option');option.value=v;option.textContent=v;value.append(option);}invalidate();}
  function ids(){return {scope:scope.value,scope_id:scope.value==='platform'?'platform':scopeId.value.trim(),workspace_id:scope.value==='project'?workspace.value.trim():undefined};}
  function proposed(){const idsValue=ids();return {...idsValue,key:key.value,value:key.value==='generation.max_output_tokens'?Number(value.value):value.value,expected_revision:revision};}
  function setBusy(active:boolean){busy=active;[scope,scopeId,workspace,key,value,load,preview,approve].forEach(x=>{x.disabled=active;});save.disabled=active||!currentPlan||!approve.checked;}
  async function effective(){invalidate();setBusy(true);setStatus('Consultando servidor…','loading');try{const result=await clientFactory().persistentSettingsEffective(key.value,scope.value,ids().scope_id,scope.value==='platform'?undefined:scope.value==='workspace'?scopeId.value.trim():workspace.value.trim(),scope.value==='project'?scopeId.value.trim():undefined);if(!result.ok)throw Error(result.message);const data=result.data as Record<string,unknown>;revision=Number(data.target_revision ?? 0);origin.textContent=`Valor: ${String(data.effective_value)} · Origen: ${String(data.origin)} · Rev: ${revision} · Plan-only`;
    const currentValue=String(data.effective_value);if(Array.from(value.options).some(option=>option.value===currentValue))value.value=currentValue;setStatus('PASS: dato leído del backend.');}catch(err){revision=0;origin.textContent='Valor efectivo no disponible';setStatus(`BLOCK: ${err instanceof Error?err.message:String(err)}`,'block');}finally{setBusy(false);}}
  scope.addEventListener('change',()=>{scopeId.value=scope.value==='platform'?'platform':'';invalidate();origin.textContent='Consultar tras cambiar ámbito.';});
  for(const control of [scopeId,workspace,value]) control.addEventListener('input',invalidate);
  key.addEventListener('change',()=>{choices();origin.textContent='Consultar tras cambiar preferencia.';});
  load.addEventListener('click',()=>void effective());
  preview.addEventListener('click',async()=>{setBusy(true);setStatus('Validando vista previa…','loading');try{const candidate=proposed();const result=await clientFactory().persistentSettingsPlan(candidate);if(!result.ok)throw Error(result.message);const data=result.data as Record<string,unknown>;if(data.permitted!==true)throw Error('REVISION_CONFLICT');currentPlan=candidate;approve.checked=false;plan.textContent=`Ámbito: ${candidate.scope}:${candidate.scope_id} · ${candidate.key} = ${candidate.value} · revisión esperada: ${candidate.expected_revision}. Escritura: NO · Efecto runtime: NO`;setStatus('PASS: plan válido. Confirma únicamente si deseas guardar.');}catch(err){invalidate();setStatus(`BLOCK: ${err instanceof Error?err.message:String(err)}`,'block');}finally{setBusy(false);}});
  approve.addEventListener('change',()=>{save.disabled=busy||!currentPlan||!approve.checked;});
  save.addEventListener('click',async()=>{if(!currentPlan||!approve.checked||busy)return;const candidate=currentPlan;setBusy(true);setStatus('Guardando bajo permisos Owner…','loading');try{const result=await clientFactory().persistentSettingsApply({...candidate,approve_write:true});if(!result.ok)throw Error(result.message);currentPlan=null;approve.checked=false;plan.textContent='Guardado. Reconsulta el valor efectivo.';setStatus('PASS: persistido; runtime no modificado.');}catch(err){currentPlan=null;approve.checked=false;setStatus(`BLOCK: ${err instanceof Error?err.message:String(err)}. Reconsulta antes de reintentar.`,'block');}finally{setBusy(false);if(status.dataset.status!=='block')await effective();}});
  choices();setStatus('Consulta una preferencia para iniciar.');
  return card;
}
