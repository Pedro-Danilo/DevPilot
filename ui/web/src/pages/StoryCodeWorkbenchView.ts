import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { AuthSessionContext } from '../api/types';

type SourceRow = { source_id:string; relative_path:string; name:string; extension:string; size_bytes:number; language_hint:string };
type SourceData = { source_id:string; relative_path:string; content:string; sha256:string; language_hint:string };
type Draft = { draft_id:string; operation:'CREATE'|'EDIT'|'RENAME'; target_path:string; status:'DRAFT'|'CONFLICT'; revision_sha256:string; source?:{source_id?:string;relative_path?:string;sha256?:string}; safety?:Record<string,unknown> };

export function renderStoryCodeWorkbenchView(tokenProvider:()=>string|null, session:AuthSessionContext):HTMLElement {
  const host=document.createElement('section'); host.className='story-code-workbench'; host.dataset.routeId='ui.story-code-workbench'; host.dataset.gsdlc09b='code-workbench';
  const intro=panel('Story Code Workbench','Navega código allowlisted y prepara cambios manuales como SourceDraftBuffer. En 09-B el source real nunca se modifica.');
  const safety=document.createElement('div'); safety.className='code-safety-strip'; safety.dataset.sourceWrite='false'; safety.textContent='DRAFT ONLY · SOURCE UNCHANGED · APPLY NO DISPONIBLE HASTA 09-C · SIN TERMINAL'; intro.append(safety); host.append(intro);
  const state=document.createElement('div'); state.className='notice'; state.setAttribute('role','status'); state.setAttribute('aria-live','polite'); host.append(state);
  const layout=document.createElement('div'); layout.className='code-workbench-grid';
  const sourcePanel=panel('Source tree','Solo archivos de texto/código admitidos por la policy server-side.');
  const sourceList=document.createElement('div'); sourceList.className='code-source-list'; sourceList.dataset.sourceList='true'; sourcePanel.append(sourceList);
  const editorPanel=panel('Editor de draft','Editar aquí modifica exclusivamente estado runtime de draft; el navegador no conoce ni accede a su ruta física.');
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
  const client=()=>new DevPilotApiClient({token:tokenProvider()});
  let selected:SourceData|null=null; let draft:Draft|null=null;
  const canAuthor=session.principal.roles.some((x)=>['owner','developer'].includes(x));
  save.disabled=!canAuthor; if(!canAuthor){save.title='Solo owner/developer puede persistir SourceDraftBuffer. La lectura sigue disponible.';}
  recheck.disabled=true; discard.disabled=true;

  mode.addEventListener('change',()=>{const op=mode.value;if(op==='CREATE'){selected=null;target.value='src/new_file.py';editor.value='';sourceMeta.textContent='CREATE · archivo nuevo como draft runtime-only.';}else if(selected){target.value=selected.relative_path;editor.value=selected.content;} updateAuthoring();});
  save.addEventListener('click',()=>void saveDraft()); recheck.addEventListener('click',()=>void recheckDraft()); discard.addEventListener('click',()=>void discardDraft());
  void refresh();

  async function refresh():Promise<void>{
    setState('loading','Cargando story/context y source tree…');
    try{
      const [status,sources]=await Promise.all([client().storyCodeStatus(),client().storyCodeSources()]);
      const story=((status.data as any).story??{}); sourceMeta.textContent=`Story ${String(story.story_id??'sin story')} · ${String(story.status??'UNKNOWN')} · source write=false`;
      renderSources(((sources.data as any).sources??[]) as SourceRow[]); setState('pass',`PASS · ${((sources.data as any).summary?.sources_total??0)} fuentes allowlisted · source sin cambios.`);
    }catch(e){setState('block',errorText(e));}
  }
  function renderSources(rows:SourceRow[]):void{
    sourceList.replaceChildren(); if(!rows.length){const p=document.createElement('p');p.className='muted';p.textContent='No hay source allowlisted.';sourceList.append(p);return;}
    for(const row of rows){const b=button(`${row.relative_path} · ${row.language_hint}`);b.className='code-source-item';b.dataset.sourcePath=row.relative_path;b.addEventListener('click',()=>void openSource(row));sourceList.append(b);}
  }
  async function openSource(row:SourceRow):Promise<void>{
    setState('loading',`Leyendo ${row.relative_path}…`); try{const r=await client().storyCodeSource(row.source_id); selected=(r.data as any).source as SourceData; mode.value='EDIT'; target.value=selected.relative_path; editor.value=selected.content; sourceMeta.textContent=`${selected.relative_path} · ${selected.language_hint}`; sourceHash.textContent=`preimage ${selected.sha256}`; draft=null; draftInfo.textContent=''; recheck.disabled=true;discard.disabled=true;updateAuthoring();setState('pass','PASS · source leído por opaque id.');}catch(e){setState('block',errorText(e));}
  }
  async function saveDraft():Promise<void>{
    if(!canAuthor){setState('block','BLOCK · el rol actual es read-only para autoría de código.');return;}
    const operation=mode.value as 'CREATE'|'EDIT'|'RENAME';
    if(operation!=='CREATE'&&!selected){setState('block','BLOCK · selecciona source para EDIT/RENAME.');return;}
    setState('loading','Guardando SourceDraftBuffer runtime-only…');
    try{const r=await client().storyCodeDraftSave({operation,content:editor.value,target_path:target.value,source_id:selected?.source_id??null,expected_source_sha256:selected?.sha256??null,expected_revision_sha256:draft?.revision_sha256??null});draft=(r.data as any).draft as Draft;renderDraft();setState('pass','PASS · draft guardado; source real permanece sin cambios.');}catch(e){setState('block',errorText(e));}
  }
  async function recheckDraft():Promise<void>{if(!draft)return;setState('loading','Revalidando source preimage…');try{const r=await client().storyCodeDraftRecheck(draft.draft_id);draft=(r.data as any).draft as Draft;renderDraft();setState('pass','PASS · preimage vigente; source sigue sin cambios.');}catch(e){setState('block',errorText(e));draftInfo.textContent='CONFLICT · external edit/revalidation requerida';draftInfo.dataset.conflict='true';}}
  async function discardDraft():Promise<void>{if(!draft)return;try{await client().storyCodeDraftDiscard(draft.draft_id,draft.revision_sha256);draft=null;draftInfo.textContent='Draft descartado; source no fue modificado.';recheck.disabled=true;discard.disabled=true;setState('pass','PASS · runtime draft descartado.');}catch(e){setState('block',errorText(e));}}
  function renderDraft():void{if(!draft)return;draftInfo.dataset.conflict=draft.status==='CONFLICT'?'true':'false';draftInfo.textContent=`${draft.status} · ${draft.operation} → ${draft.target_path} · revision ${draft.revision_sha256.slice(0,12)} · source_mutations=false`;recheck.disabled=false;discard.disabled=false;}
  function updateAuthoring():void{save.disabled=!canAuthor;}
  function setState(kind:string,text:string):void{state.className=`notice notice--${kind}`;state.textContent=text;}
  return host;
}
function panel(title:string,description:string):HTMLElement{const p=document.createElement('section');p.className='panel';const h=document.createElement('h3');h.textContent=title;const d=document.createElement('p');d.textContent=description;p.append(h,d);return p;}
function button(label:string):HTMLButtonElement{const b=document.createElement('button');b.type='button';b.textContent=label;return b;}
function errorText(error:unknown):string{if(error instanceof DevPilotApiError){const payload=error.payload as any;const finding=payload?.findings?.[0]?.message;return `BLOCK · ${finding??error.message}`;}return error instanceof Error?`ERROR · ${error.message}`:'ERROR · fallo local no clasificado';}
