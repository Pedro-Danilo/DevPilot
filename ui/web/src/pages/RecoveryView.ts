import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { RecoveryStatusData } from '../api/types';

function panel(title:string):HTMLElement{const el=document.createElement('article');el.className='panel recovery-card';const h=document.createElement('h3');h.textContent=title;el.append(h);return el;}
function fact(label:string,value:unknown):HTMLElement{const row=document.createElement('div');row.className='recovery-fact';const k=document.createElement('strong');k.textContent=label;const v=document.createElement('span');v.textContent=String(value??'—');row.append(k,v);return row;}
function errorPanel(error:unknown):HTMLElement{const el=panel('Operación bloqueada');const p=document.createElement('p');p.textContent=error instanceof DevPilotApiError?error.message:error instanceof Error?error.message:String(error);el.append(p);return el;}

function renderStatus(data:RecoveryStatusData):HTMLElement{
  const wrap=document.createElement('div');wrap.className='recovery-grid';
  const recovery=panel('Contexto recuperable');
  recovery.dataset.recoveryState=String(data.recovery?.state??'UNKNOWN');
  recovery.append(
    fact('Estado',data.recovery?.state),
    fact('Workspace',data.recovery?.workspace_id),
    fact('Current step',data.recovery?.current_step),
    fact('Checkpoint sequence',data.recovery?.checkpoint?.sequence),
    fact('Draft refs',Array.isArray(data.recovery?.checkpoint?.draft_refs)?data.recovery.checkpoint.draft_refs.join(', '):'—'),
    fact('Nueva sesión',data.recovery?.session_changed===true?'YES':'NO'),
    fact('Git coincide',data.recovery?.git_match===true?'PASS':data.recovery?.git_match===false?'REVALIDATION':'N/A'),
    fact('Browser storage authority',data.authority?.browser_storage_authority===false?'NO':'BLOCK'),
  );
  const next=document.createElement('p');next.className='recovery-next-action';next.textContent=String(data.recovery?.next_action??'Sin checkpoint durable todavía.');recovery.append(next);
  const work=panel('Pending safe work');
  const rows=Array.isArray(data.recovery?.pending_work)?data.recovery.pending_work:[];
  if(!rows.length){const p=document.createElement('p');p.textContent='No hay trabajo pendiente registrado en el checkpoint.';work.append(p);}else{const ul=document.createElement('ul');for(const row of rows){const li=document.createElement('li');li.textContent=`${String(row.work_id??'work')} · ${String(row.recovery_state??'UNKNOWN')} · ${String(row.reason_code??'')}`;ul.append(li);}work.append(ul);}
  const locks=panel('Workspace locks');const lockRows=Array.isArray(data.locks?.locks)?data.locks.locks:[];
  if(!lockRows.length){const p=document.createElement('p');p.textContent='No hay locks activos.';locks.append(p);}else{const ul=document.createElement('ul');for(const row of lockRows){const li=document.createElement('li');li.textContent=`${String(row.action_id??'action')} · ${row.stale===true?'STALE':'ACTIVE'} · owner=${String(row.actor??'unknown')} · current-session=${row.owned_by_current_session===true?'YES':'NO'}`;ul.append(li);}locks.append(ul);}
  const coherence=panel('Project Status coherence');coherence.dataset.lifecycleDisplay=String(data.project_status_coherence?.display_state??'UNKNOWN');coherence.append(fact('Lifecycle',data.project_status_coherence?.lifecycle_status),fact('Aggregate UI',data.project_status_coherence?.aggregate_ui_state),fact('Display state',data.project_status_coherence?.display_state),fact('Non-authoritative gaps',data.project_status_coherence?.non_authoritative_gap_count),fact('Authoritative blockers',data.project_status_coherence?.authoritative_blocker_count));
  wrap.append(recovery,work,locks,coherence);return wrap;
}

export function renderRecoveryView(tokenProvider:()=>string|null):HTMLElement{
  const section=document.createElement('section');section.className='recovery-view';section.dataset.uiRouteId='ui.recovery';
  const h=document.createElement('h2');h.textContent='Recovery / Resume';
  const p=document.createElement('p');p.textContent='Recupera contexto desde autoridad server-side. Los checkpoints guardan solo metadatos/referencias; una operación sensible nunca se reejecuta automáticamente después de restart.';
  const legend=document.createElement('p');legend.className='recovery-legend';legend.textContent='Estados de recovery: SAFE_TO_RESUME = metadato seguro; REVALIDATION_REQUIRED = debe confirmar/revalidar; ABORTED_REQUIRES_REPLAN = autoridad cambió; COMPLETED = ya terminado.';
  const controls=document.createElement('div');controls.className='recovery-controls';
  const draft=document.createElement('input');draft.placeholder='draft-ref (ej. draft:story-123)';draft.value='draft:browser-gsdlc12a';
  const action=document.createElement('input');action.placeholder='action id';action.value='workspace.sensitive.demo';
  const checkpoint=document.createElement('button');checkpoint.textContent='Guardar checkpoint seguro';
  const lock=document.createElement('button');lock.textContent='Adquirir lock sensible';
  const release=document.createElement('button');release.textContent='Liberar lock';
  const refresh=document.createElement('button');refresh.textContent='Actualizar recovery';
  controls.append(draft,action,checkpoint,lock,release,refresh);
  const note=document.createElement('p');note.className='recovery-note';note.textContent='Para la validación de restart: guarda checkpoint + lock, reinicia API/UI y vuelve a esta vista. La sesión recuperada o rotada debe conservar el contexto durable y exigir revalidación para el trabajo sensible.';
  const content=document.createElement('div');section.append(h,p,legend,controls,note,content);
  const api=()=>new DevPilotApiClient({token:tokenProvider()});
  const load=async()=>{try{const r=await api().recoveryStatus();content.replaceChildren(renderStatus(r.data));}catch(e){content.replaceChildren(errorPanel(e));}};
  checkpoint.onclick=()=>void(async()=>{try{const ref=draft.value.trim()||'draft:browser-gsdlc12a';const workId=action.value.trim()||'workspace.sensitive.demo';await api().recoveryCheckpoint({draft_refs:[ref],pending_work:[{work_id:'draft.metadata.resume',kind:'draft-ref',status:'PENDING',sensitive:false,safe_to_resume:true},{work_id:workId,kind:'sensitive-action',status:'PLANNED',sensitive:true,safe_to_resume:false}],evidence_refs:['browser:gsdlc12a'],recovery_reason:'browser-restart-acceptance'});await load();}catch(e){content.replaceChildren(errorPanel(e));}})();
  lock.onclick=()=>void(async()=>{try{await api().recoveryLockAcquire(action.value.trim()||'workspace.sensitive.demo',true,300);await load();}catch(e){content.replaceChildren(errorPanel(e));}})();
  release.onclick=()=>void(async()=>{try{await api().recoveryLockRelease(action.value.trim()||'workspace.sensitive.demo');await load();}catch(e){content.replaceChildren(errorPanel(e));}})();
  refresh.onclick=()=>void load();void load();return section;
}
