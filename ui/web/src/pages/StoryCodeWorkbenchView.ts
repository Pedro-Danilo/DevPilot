import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { AuthSessionContext } from '../api/types';

type SourceRow = { source_id:string; relative_path:string; name:string; extension:string; size_bytes:number; language_hint:string };
type SourceData = { source_id:string; relative_path:string; content:string; sha256:string; language_hint:string };
type Draft = { draft_id:string; operation:'CREATE'|'EDIT'|'RENAME'; target_path:string; status:'DRAFT'|'CONFLICT'; revision_sha256:string; source?:{source_id?:string;relative_path?:string;sha256?:string}; safety?:Record<string,unknown> };
type ChangePlan = { plan_id:string; plan_hash:string; full_diff:string; exact_path_allowlist:string[]; required_approval_role:string; risk:{level:string;reasons:string[]}; test_impact_preview:Record<string,unknown>; changes:Array<Record<string,unknown>> };
type Execution = { execution_id:string; status:string; plan_id:string; plan_hash:string; approval_id:string; changes:Array<Record<string,unknown>> };

export function renderStoryCodeWorkbenchView(tokenProvider:()=>string|null, session:AuthSessionContext):HTMLElement {
  const host=document.createElement('section'); host.className='story-code-workbench'; host.dataset.routeId='ui.story-code-workbench'; host.dataset.gsdlc09c='governed-source-change';
  const intro=panel('Story Code Workbench','Autoría manual bounded + SourceChangePlan inmutable. 09-C habilita apply/rollback únicamente mediante plan, dry-run, RBAC, approval owner y revalidación de preimage.');
  const safety=document.createElement('div'); safety.className='code-safety-strip'; safety.dataset.sourceWrite='approval-gated'; safety.textContent='SOURCE WRITE · APPROVAL-GATED · EXACT PATH ALLOWLIST · ATOMIC APPLY/ROLLBACK · SIN TERMINAL'; intro.append(safety); host.append(intro);
  const state=document.createElement('div'); state.className='notice'; state.setAttribute('role','status'); state.setAttribute('aria-live','polite'); host.append(state);
  const layout=document.createElement('div'); layout.className='code-workbench-grid';
  const sourcePanel=panel('Source tree','Solo archivos de texto/código admitidos por la policy server-side.');
  const sourceList=document.createElement('div'); sourceList.className='code-source-list'; sourceList.dataset.sourceList='true'; sourcePanel.append(sourceList);
  const editorPanel=panel('Editor de draft','El editor persiste SourceDraftBuffer runtime-only. Source no cambia hasta apply aprobado.');
  const sourceMeta=document.createElement('p'); sourceMeta.className='muted'; sourceMeta.dataset.sourceMeta='true'; sourceMeta.textContent='Selecciona un archivo o usa CREATE.';
  const mode=document.createElement('select'); mode.setAttribute('aria-label','Operación de draft'); for(const value of ['EDIT','CREATE','RENAME']){const o=document.createElement('option');o.value=value;o.textContent=value;mode.append(o);}
  const target=document.createElement('input'); target.type='text'; target.placeholder='src/module.py'; target.setAttribute('aria-label','Ruta destino'); target.dataset.targetPath='true';
  const editor=document.createElement('textarea'); editor.rows=22; editor.spellcheck=false; editor.setAttribute('aria-label','Contenido del draft'); editor.dataset.draftEditor='true';
  const actions=document.createElement('div'); actions.className='code-workbench-actions';
  const save=button('Guardar draft'); save.dataset.saveDraft='true';
  const recheck=button('Revalidar preimage'); recheck.dataset.recheckDraft='true';
  const discard=button('Descartar draft'); discard.dataset.discardDraft='true';
  const sourceHash=document.createElement('code'); sourceHash.dataset.sourceHash='true';
  const draftInfo=document.createElement('div'); draftInfo.className='code-draft-status'; draftInfo.dataset.draftStatus='true';
  actions.append(save,recheck,discard); editorPanel.append(sourceMeta,mode,target,editor,actions,sourceHash,draftInfo);
  layout.append(sourcePanel,editorPanel); host.append(layout);

  const changePanel=panel('Governed source change','Secuencia obligatoria: immutable plan → diff/Test Impact → recheck/dry-run → owner approval → atomic apply → separate rollback approval.'); changePanel.dataset.changePlanPanel='true';
  const planActions=document.createElement('div'); planActions.className='code-workbench-actions';
  const createPlan=button('Crear SourceChangePlan'); createPlan.dataset.createChangePlan='true';
  const planRecheck=button('Revalidar plan'); planRecheck.dataset.recheckChangePlan='true';
  const dryRun=button('Dry-run'); dryRun.dataset.dryRunChangePlan='true';
  const requestApproval=button('Solicitar approval owner'); requestApproval.dataset.requestApplyApproval='true';
  const approvalLink=document.createElement('a'); approvalLink.href='/approvals'; approvalLink.target='_blank'; approvalLink.rel='noopener'; approvalLink.textContent='Abrir Approval Center ↗'; approvalLink.hidden=true;
  const approvalInput=document.createElement('input'); approvalInput.type='text'; approvalInput.placeholder='Approval ID aprobado'; approvalInput.setAttribute('aria-label','Approval ID de apply'); approvalInput.dataset.applyApprovalId='true';
  const apply=button('Aplicar plan aprobado'); apply.dataset.applyChangePlan='true';
  planActions.append(createPlan,planRecheck,dryRun,requestApproval,approvalLink,approvalInput,apply);
  const planMeta=document.createElement('div'); planMeta.className='code-draft-status'; planMeta.dataset.changePlanMeta='true';
  const diff=document.createElement('pre'); diff.className='code-full-diff'; diff.dataset.fullDiff='true'; diff.textContent='Crea un draft y luego el SourceChangePlan para ver el diff completo.';
  const impact=document.createElement('pre'); impact.className='code-test-impact'; impact.dataset.testImpact='true';
  changePanel.append(planActions,planMeta,diff,impact); host.append(changePanel);

  const rollbackPanel=panel('Apply manifest y rollback','Rollback es una operación gobernada separada; nunca reutiliza el approval de apply.'); rollbackPanel.dataset.rollbackPanel='true';
  const rollbackActions=document.createElement('div'); rollbackActions.className='code-workbench-actions';
  const requestRollback=button('Solicitar approval de rollback'); requestRollback.dataset.requestRollbackApproval='true';
  const rollbackLink=document.createElement('a'); rollbackLink.href='/approvals'; rollbackLink.target='_blank'; rollbackLink.rel='noopener'; rollbackLink.textContent='Abrir Approval Center ↗'; rollbackLink.hidden=true;
  const rollbackInput=document.createElement('input'); rollbackInput.type='text'; rollbackInput.placeholder='Approval ID de rollback aprobado'; rollbackInput.setAttribute('aria-label','Approval ID de rollback'); rollbackInput.dataset.rollbackApprovalId='true';
  const rollback=button('Ejecutar rollback aprobado'); rollback.dataset.executeRollback='true';
  const evidence=document.createElement('pre'); evidence.className='code-change-evidence'; evidence.dataset.changeEvidence='true';
  rollbackActions.append(requestRollback,rollbackLink,rollbackInput,rollback); rollbackPanel.append(rollbackActions,evidence); host.append(rollbackPanel);

  const client=()=>new DevPilotApiClient({token:tokenProvider()});
  let selected:SourceData|null=null; let draft:Draft|null=null; let plan:ChangePlan|null=null; let execution:Execution|null=null;
  const canAuthor=session.principal.roles.some((x)=>['owner','developer'].includes(x)); const isOwner=session.principal.roles.includes('owner');
  save.disabled=!canAuthor; createPlan.disabled=true; planRecheck.disabled=true; dryRun.disabled=true; requestApproval.disabled=true; apply.disabled=true; requestRollback.disabled=true; rollback.disabled=true;
  if(!canAuthor)save.title='Solo owner/developer puede persistir SourceDraftBuffer.'; if(!isOwner){requestApproval.title='Solo owner puede solicitar/aplicar.';apply.title=requestApproval.title;requestRollback.title=requestApproval.title;rollback.title=requestApproval.title;}

  mode.addEventListener('change',()=>{const op=mode.value;if(op==='CREATE'){selected=null;target.value='src/new_file.py';editor.value='';sourceMeta.textContent='CREATE · archivo nuevo como draft runtime-only.';}else if(selected){target.value=selected.relative_path;editor.value=selected.content;} updateButtons();});
  save.addEventListener('click',()=>void saveDraft()); recheck.addEventListener('click',()=>void recheckDraft()); discard.addEventListener('click',()=>void discardDraft());
  createPlan.addEventListener('click',()=>void createChangePlan()); planRecheck.addEventListener('click',()=>void recheckPlan()); dryRun.addEventListener('click',()=>void runDryRun()); requestApproval.addEventListener('click',()=>void requestApplyApproval()); apply.addEventListener('click',()=>void executeApply()); requestRollback.addEventListener('click',()=>void requestRollbackApproval()); rollback.addEventListener('click',()=>void executeRollback());
  void refresh();

  async function refresh():Promise<void>{
    setState('loading','Cargando story/context y source tree…');
    try{const [status,sources]=await Promise.all([client().storyCodeStatus(),client().storyCodeSources()]);const story=((status.data as any).story??{});sourceMeta.textContent=`Story ${String(story.story_id??'sin story')} · ${String(story.status??'UNKNOWN')} · source write=approval-gated`;renderSources(((sources.data as any).sources??[]) as SourceRow[]);setState('pass',`PASS · ${((sources.data as any).summary?.sources_total??0)} fuentes allowlisted.`);}catch(e){setState('block',errorText(e));}
  }
  function renderSources(rows:SourceRow[]):void{sourceList.replaceChildren();if(!rows.length){const p=document.createElement('p');p.className='muted';p.textContent='No hay source allowlisted.';sourceList.append(p);return;}for(const row of rows){const b=button(`${row.relative_path} · ${row.language_hint}`);b.className='code-source-item';b.dataset.sourcePath=row.relative_path;b.addEventListener('click',()=>void openSource(row));sourceList.append(b);}}
  async function openSource(row:SourceRow):Promise<void>{setState('loading',`Leyendo ${row.relative_path}…`);try{const r=await client().storyCodeSource(row.source_id);selected=(r.data as any).source as SourceData;mode.value='EDIT';target.value=selected.relative_path;editor.value=selected.content;sourceMeta.textContent=`${selected.relative_path} · ${selected.language_hint}`;sourceHash.textContent=`preimage ${selected.sha256}`;draft=null;clearPlan();draftInfo.textContent='';recheck.disabled=true;discard.disabled=true;updateButtons();setState('pass','PASS · source leído por opaque id.');}catch(e){setState('block',errorText(e));}}
  async function saveDraft():Promise<void>{if(!canAuthor){setState('block','BLOCK · rol read-only.');return;}const operation=mode.value as 'CREATE'|'EDIT'|'RENAME';if(operation!=='CREATE'&&!selected){setState('block','BLOCK · selecciona source para EDIT/RENAME.');return;}setState('loading','Guardando SourceDraftBuffer runtime-only…');try{const r=await client().storyCodeDraftSave({operation,content:editor.value,target_path:target.value,source_id:selected?.source_id??null,expected_source_sha256:selected?.sha256??null,expected_revision_sha256:draft?.revision_sha256??null});draft=(r.data as any).draft as Draft;clearPlan();renderDraft();setState('pass','PASS · draft guardado; source real permanece sin cambios.');}catch(e){setState('block',errorText(e));}}
  async function recheckDraft():Promise<void>{if(!draft)return;setState('loading','Revalidando source preimage…');try{const r=await client().storyCodeDraftRecheck(draft.draft_id);draft=(r.data as any).draft as Draft;renderDraft();setState('pass','PASS · preimage vigente.');}catch(e){setState('block',errorText(e));draftInfo.textContent='CONFLICT · external edit/revalidation requerida';draftInfo.dataset.conflict='true';clearPlan();}}
  async function discardDraft():Promise<void>{if(!draft)return;try{await client().storyCodeDraftDiscard(draft.draft_id,draft.revision_sha256);draft=null;clearPlan();draftInfo.textContent='Draft descartado; source no fue modificado.';recheck.disabled=true;discard.disabled=true;updateButtons();setState('pass','PASS · runtime draft descartado.');}catch(e){setState('block',errorText(e));}}
  async function createChangePlan():Promise<void>{if(!draft)return;setState('loading','Construyendo plan inmutable y Test Impact preview…');try{const r=await client().storySourceChangePlanCreate([draft.draft_id]);plan=(r.data as any).plan as ChangePlan;renderPlan();setState('pass','PASS · SourceChangePlan inmutable creado; no hubo source write.');}catch(e){setState('block',errorText(e));}}
  async function recheckPlan():Promise<void>{if(!plan)return;setState('loading','Revalidando preimages exactos…');try{await client().storySourceChangePlanRecheck(plan.plan_id,plan.plan_hash);setState('pass','PASS · plan/preimages vigentes.');}catch(e){setState('block',errorText(e));}}
  async function runDryRun():Promise<void>{if(!plan)return;setState('loading','Ejecutando dry-run gobernado…');try{const r=await client().storySourceChangeDryRun(plan.plan_id,plan.plan_hash);evidence.textContent=JSON.stringify(r.data,null,2);setState('pass','PASS · dry-run sin mutación de source.');}catch(e){setState('block',errorText(e));}}
  async function requestApplyApproval():Promise<void>{if(!plan||!isOwner)return;setState('loading','Solicitando approval owner exacto…');try{const r=await client().storySourceChangeApplyApprovalRequest(plan.plan_id,plan.plan_hash);const id=String((r.data as any)?.approval?.approval_id??(r.data as any)?.approval_id??'');if(!id)throw new Error('La API no devolvió Approval ID.');approvalInput.value=id;approvalLink.href=`/approvals?approval_id=${encodeURIComponent(id)}`;approvalLink.hidden=false;apply.disabled=false;setState('pass',`PENDING · approval ${id} creado; debe decidirse por sesión humana owner.`);}catch(e){setState('block',errorText(e));}}
  async function executeApply():Promise<void>{if(!plan||!isOwner)return;const id=approvalInput.value.trim();if(!id){setState('block','BLOCK · ingresa el Approval ID aprobado.');return;}setState('loading','Revalidando preimage y ejecutando apply all-or-nothing…');try{const r=await client().storySourceChangeApply(plan.plan_id,plan.plan_hash,id);execution=(r.data as any).execution as Execution;evidence.textContent=JSON.stringify((r.data as any).apply_manifest??r.data,null,2);requestRollback.disabled=false;setState('pass','PASS · apply exacto verificado; manifest disponible.');await refresh();}catch(e){setState('block',errorText(e));}}
  async function requestRollbackApproval():Promise<void>{if(!execution||!isOwner)return;setState('loading','Solicitando approval separado de rollback…');try{const r=await client().storySourceChangeRollbackApprovalRequest(execution.execution_id);const id=String((r.data as any)?.approval?.approval_id??(r.data as any)?.approval_id??'');if(!id)throw new Error('La API no devolvió Approval ID de rollback.');rollbackInput.value=id;rollbackLink.href=`/approvals?approval_id=${encodeURIComponent(id)}`;rollbackLink.hidden=false;rollback.disabled=false;setState('pass',`PENDING · rollback approval ${id} creado.`);}catch(e){setState('block',errorText(e));}}
  async function executeRollback():Promise<void>{if(!execution||!isOwner)return;const id=rollbackInput.value.trim();if(!id){setState('block','BLOCK · ingresa Approval ID de rollback.');return;}setState('loading','Restaurando preimages exactos…');try{const r=await client().storySourceChangeRollback(execution.execution_id,id);evidence.textContent=JSON.stringify((r.data as any).rollback_evidence??r.data,null,2);setState('pass','PASS · rollback limpio; source_hash_parity=true.');await refresh();}catch(e){setState('block',errorText(e));}}
  function clearPlan():void{plan=null;execution=null;planMeta.textContent='';diff.textContent='Crea un SourceChangePlan para ver el diff completo.';impact.textContent='';approvalInput.value='';rollbackInput.value='';approvalLink.hidden=true;rollbackLink.hidden=true;updateButtons();}
  function renderPlan():void{if(!plan)return;planMeta.textContent=`${plan.plan_id} · hash ${plan.plan_hash.slice(0,16)} · risk=${plan.risk.level} · required=${plan.required_approval_role} · allowlist=${plan.exact_path_allowlist.join(', ')}`;diff.textContent=plan.full_diff||'(diff vacío)';impact.textContent=JSON.stringify(plan.test_impact_preview,null,2);updateButtons();}
  function renderDraft():void{if(!draft)return;draftInfo.dataset.conflict=draft.status==='CONFLICT'?'true':'false';draftInfo.textContent=`${draft.status} · ${draft.operation} → ${draft.target_path} · revision ${draft.revision_sha256.slice(0,12)} · source_mutations=false`;recheck.disabled=false;discard.disabled=false;updateButtons();}
  function updateButtons():void{save.disabled=!canAuthor;createPlan.disabled=!canAuthor||!draft||draft.status==='CONFLICT';planRecheck.disabled=!canAuthor||!plan;dryRun.disabled=!canAuthor||!plan;requestApproval.disabled=!isOwner||!plan;apply.disabled=!isOwner||!plan||!approvalInput.value.trim();requestRollback.disabled=!isOwner||!execution;rollback.disabled=!isOwner||!execution||!rollbackInput.value.trim();}
  approvalInput.addEventListener('input',updateButtons); rollbackInput.addEventListener('input',updateButtons);
  function setState(kind:string,text:string):void{state.className=`notice notice--${kind}`;state.textContent=text;}
  return host;
}
function panel(title:string,description:string):HTMLElement{const p=document.createElement('section');p.className='panel';const h=document.createElement('h3');h.textContent=title;const d=document.createElement('p');d.textContent=description;p.append(h,d);return p;}
function button(label:string):HTMLButtonElement{const b=document.createElement('button');b.type='button';b.textContent=label;return b;}
function errorText(error:unknown):string{if(error instanceof DevPilotApiError){const payload=error.payload as any;const finding=payload?.findings?.[0]?.message;return `BLOCK · ${finding??error.message}`;}return error instanceof Error?`ERROR · ${error.message}`:'ERROR · fallo local no clasificado';}
