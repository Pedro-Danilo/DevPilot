import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { RecoveryStatusData } from '../api/types';
import { renderAccessibleError, renderContextualHelp } from '../components/ContextualHelp';
import { renderOperationalSurfaceSummary } from '../components/OperationalPatterns';

function panel(title:string):HTMLElement{const el=document.createElement('article');el.className='panel recovery-card';const h=document.createElement('h3');h.textContent=title;el.append(h);return el;}
function fact(label:string,value:unknown):HTMLElement{const row=document.createElement('div');row.className='recovery-fact';const k=document.createElement('strong');k.textContent=label;const v=document.createElement('span');v.textContent=String(value??'—');row.append(k,v);return row;}
function errorPanel(error:unknown):HTMLElement{
  const status=error instanceof DevPilotApiError?error.status:undefined;
  return renderAccessibleError({
    title:'Recovery bloqueado',
    plain:'DevPilot no completó la operación de recovery. El estado seguro se conserva y ninguna acción sensible se reanuda automáticamente.',
    status,
    nextAction:'Revise el estado de sesión/lock y vuelva a cargar Recovery. Si el bloqueo persiste, conserve la evidencia antes de cambiar contexto.',
    evidenceRef:'ui.recovery.error',
  });
}

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
  const expert=document.createElement('details');expert.className='expert-only expert-authority-trace';const expertSummary=document.createElement('summary');expertSummary.textContent='Authority trace';const expertBody=document.createElement('p');expertBody.textContent=`checkpoint=${String(data.recovery?.checkpoint?.sequence??'none')} · state=${String(data.recovery?.state??'UNKNOWN')} · browser-authority=${data.authority?.browser_storage_authority===false?'false':'unexpected'}`;expert.append(expertSummary,expertBody);recovery.append(expert);
  const work=panel('Pending safe work');
  const rows=Array.isArray(data.recovery?.pending_work)?data.recovery.pending_work:[];
  if(!rows.length){const p=document.createElement('p');p.textContent='No hay trabajo pendiente registrado en el checkpoint.';work.append(p);}else{const ul=document.createElement('ul');for(const row of rows){const li=document.createElement('li');li.textContent=`${String(row.work_id??'work')} · ${String(row.recovery_state??'UNKNOWN')} · ${String(row.reason_code??'')}`;ul.append(li);}work.append(ul);}
  const locks=panel('Workspace locks');const lockRows=Array.isArray(data.locks?.locks)?data.locks.locks:[];
  if(!lockRows.length){const p=document.createElement('p');p.textContent='No hay locks activos.';locks.append(p);}else{const ul=document.createElement('ul');for(const row of lockRows){const li=document.createElement('li');li.textContent=`${String(row.action_id??'action')} · ${row.stale===true?'STALE':'ACTIVE'} · owner=${String(row.actor??'unknown')} · current-session=${row.owned_by_current_session===true?'YES':'NO'}`;ul.append(li);}locks.append(ul);}
  const coherence=panel('Project Status coherence');coherence.dataset.lifecycleDisplay=String(data.project_status_coherence?.display_state??'UNKNOWN');coherence.append(fact('Lifecycle',data.project_status_coherence?.lifecycle_status),fact('Aggregate UI',data.project_status_coherence?.aggregate_ui_state),fact('Display state',data.project_status_coherence?.display_state),fact('Non-authoritative gaps',data.project_status_coherence?.non_authoritative_gap_count),fact('Authoritative blockers',data.project_status_coherence?.authoritative_blocker_count));
  wrap.append(recovery,work,locks,coherence);return wrap;
}

function labeledInput(labelText:string, input:HTMLInputElement):HTMLLabelElement{const label=document.createElement('label');const span=document.createElement('span');span.textContent=labelText;label.append(span,input);return label;}

export function renderRecoveryView(tokenProvider:()=>string|null):HTMLElement{
  const section=document.createElement('section');section.className='recovery-view';section.dataset.uiRouteId='ui.recovery';
  const h=document.createElement('h2');h.textContent='Recovery / Resume';
  const p=document.createElement('p');p.textContent='Recupera contexto desde autoridad server-side. Los checkpoints guardan solo metadatos/referencias; una operación sensible nunca se reejecuta automáticamente después de restart.';
  const legend=document.createElement('p');legend.className='recovery-legend';legend.textContent='Estados de recovery: SAFE_TO_RESUME = metadato seguro; REVALIDATION_REQUIRED = debe confirmar/revalidar; ABORTED_REQUIRES_REPLAN = autoridad cambió; COMPLETED = ya terminado.';
  const help=renderContextualHelp({
    title:'Ayuda para Recovery',
    plain:'Use esta vista para entender qué contexto sobrevivió a un restart y qué trabajo exige revalidación.',
    technical:'La autoridad proviene del servicio server-side de recovery y locks. Guided/Expert solo cambian cuánto detalle se muestra; no cambian policy ni permisos.',
    nextAction:'Si ve REVALIDATION_REQUIRED, revise el contexto y no reutilice approvals o acciones sensibles sin validarlas otra vez.',
    evidenceRef:'ui.recovery',
  });
  const controls=document.createElement('div');controls.className='recovery-controls';controls.setAttribute('aria-label','Controles de recovery');
  const draft=document.createElement('input');draft.id='recovery-draft-ref';draft.placeholder='draft-ref (ej. draft:story-123)';draft.value='draft:browser-gsdlc12a';draft.autocomplete='off';
  const action=document.createElement('input');action.id='recovery-action-id';action.placeholder='action id';action.value='workspace.sensitive.demo';action.autocomplete='off';
  const checkpoint=document.createElement('button');checkpoint.type='button';checkpoint.textContent='Guardar checkpoint seguro';
  const lock=document.createElement('button');lock.type='button';lock.textContent='Adquirir lock sensible';
  const release=document.createElement('button');release.type='button';release.textContent='Liberar lock';
  const refresh=document.createElement('button');refresh.type='button';refresh.textContent='Actualizar recovery';
  controls.append(labeledInput('Referencia de draft',draft),labeledInput('Action ID',action),checkpoint,lock,release,refresh);
  const note=document.createElement('p');note.className='recovery-note';note.textContent='Para la validación de restart: guarda checkpoint + lock, reinicia API/UI y vuelve a esta vista. La sesión recuperada o rotada debe conservar el contexto durable y exigir revalidación para el trabajo sensible.';
  const content=document.createElement('div');content.className='recovery-content';content.setAttribute('role','status');content.setAttribute('aria-live','polite');content.setAttribute('aria-atomic','false');
  section.append(h,p,legend,help,renderOperationalSurfaceSummary({eyebrow:'Operación · Recovery',title:'Retomar solo contexto seguro',state:'recovery',stateDetail:'Checkpoints guardan metadatos/referencias; acciones sensibles exigen revalidación.',primaryAction:{label:'Actualizar recovery',hierarchy:'primary',detail:'Comprueba server-side state antes de continuar.'},gate:{label:'Resume safety',state:'PENDING',detail:'SAFE_TO_RESUME no equivale a permiso para reejecutar mutaciones.'},recovery:'REVALIDATION_REQUIRED y ABORTED_REQUIRES_REPLAN se muestran como estados distintos, nunca como PASS.',evidenceSummary:'Recovery diagnostics',evidenceBody:'checkpoint sequence · draft refs · pending safe work · locks · Git coherence · authority trace.'}),controls,note,content);
  const api=()=>new DevPilotApiClient({token:tokenProvider()});
  const load=async()=>{content.setAttribute('aria-busy','true');try{const r=await api().recoveryStatus();content.replaceChildren(renderStatus(r.data));}catch(e){content.replaceChildren(errorPanel(e));}finally{content.setAttribute('aria-busy','false');}};
  checkpoint.onclick=()=>void(async()=>{try{const ref=draft.value.trim()||'draft:browser-gsdlc12a';const workId=action.value.trim()||'workspace.sensitive.demo';await api().recoveryCheckpoint({draft_refs:[ref],pending_work:[{work_id:'draft.metadata.resume',kind:'draft-ref',status:'PENDING',sensitive:false,safe_to_resume:true},{work_id:workId,kind:'sensitive-action',status:'PLANNED',sensitive:true,safe_to_resume:false}],evidence_refs:['browser:gsdlc12a'],recovery_reason:'browser-restart-acceptance'});await load();}catch(e){content.replaceChildren(errorPanel(e));}})();
  lock.onclick=()=>void(async()=>{try{await api().recoveryLockAcquire(action.value.trim()||'workspace.sensitive.demo',true,300);await load();}catch(e){content.replaceChildren(errorPanel(e));}})();
  release.onclick=()=>void(async()=>{try{await api().recoveryLockRelease(action.value.trim()||'workspace.sensitive.demo');await load();}catch(e){content.replaceChildren(errorPanel(e));}})();
  refresh.onclick=()=>void load();void load();return section;
}
