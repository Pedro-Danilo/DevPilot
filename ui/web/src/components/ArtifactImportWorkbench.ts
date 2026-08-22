// DevPilot UI contract: ui.workspace-documents — GSDLC-04-C governed PASTE/UPLOAD/IMPORT DRAFT creation.
import { DevPilotApiClient } from '../api/client';
import type { ArtifactImportPreview, ArtifactImportRecord, ArtifactImportSourceType } from '../api/types';
import { renderContractBadges, renderUiStateNotice } from './ContractBadges';

const MAX_IMPORT_BYTES = 1_048_576;
const ALLOWED = new Set(['.md', '.json']);

interface ArtifactImportWorkbenchOptions { tokenProvider: () => string; onDraftPersisted?: (record: ArtifactImportRecord) => void; }
interface ImportPayload {
  source_type: ArtifactImportSourceType;
  destination_path: string;
  source_label?: string | null;
  source_reference?: string | null;
  original_filename?: string | null;
  declared_mime?: string | null;
  text_content?: string | null;
  content_base64?: string | null;
}

type ViewState = 'idle' | 'loading' | 'preview' | 'saved' | 'block';

export function createArtifactImportWorkbench(options: ArtifactImportWorkbenchOptions): HTMLElement {
  const root = document.createElement('section');
  root.className = 'panel artifact-import-workbench';
  root.dataset.devpilotUiContract = 'ui.workspace-documents';
  root.dataset.gsdlc04c = 'artifact-import-workbench';

  let sourceType: ArtifactImportSourceType = 'PASTE';
  let destinationPath = 'docs/imported_artifact.md';
  let sourceLabel = '';
  let sourceReference = '';
  let pasteContent = '# Imported artifact\n\n';
  let originalFilename = '';
  let declaredMime = '';
  let contentBase64 = '';
  let preview: ArtifactImportPreview | undefined;
  let persisted: ArtifactImportRecord | undefined;
  let state: ViewState = 'idle';
  let message = 'Prepare una fuente externa y genere preview antes de crear el DRAFT.';
  let recent: Array<Record<string, unknown>> = [];

  const client = () => new DevPilotApiClient({ token: options.tokenProvider() });
  const invalidate = () => { preview = undefined; persisted = undefined; state = 'idle'; message = 'Entrada modificada: genere un preview nuevo antes de persistir.'; draw(); };

  function payload(): ImportPayload {
    return {
      source_type: sourceType,
      destination_path: destinationPath.trim(),
      source_label: sourceLabel.trim() || null,
      source_reference: sourceReference.trim() || null,
      original_filename: sourceType === 'PASTE' ? null : (originalFilename || null),
      declared_mime: sourceType === 'PASTE' ? null : (declaredMime || null),
      text_content: sourceType === 'PASTE' ? pasteContent : null,
      content_base64: sourceType === 'PASTE' ? null : (contentBase64 || null),
    };
  }

  async function previewImport(): Promise<void> {
    state = 'loading'; message = 'Validando path, encoding, hashes, provenance y diff…'; draw();
    try {
      const response = await client().previewArtifactImport(payload());
      const data = response.data as { preview?: ArtifactImportPreview };
      if (!data.preview) throw new Error('La API no devolvió un preview de importación.');
      preview = data.preview; persisted = undefined; state = 'preview';
      message = preview.secret_warning
        ? 'Preview listo con WARNING de secreto: el contenido está redactado y persistir DRAFT permanece bloqueado.'
        : 'Preview PASS · sin writes · sin network · revise hashes/diff antes de crear el DRAFT.';
    } catch (error) { state = 'block'; message = readable(error); preview = undefined; }
    draw();
  }

  async function persistImport(): Promise<void> {
    if (!preview) return;
    state = 'loading'; message = 'Persistiendo DRAFT runtime con provenance…'; draw();
    try {
      const response = await client().persistArtifactImport({ ...payload(), expected_preview_sha256: preview.preview_sha256 });
      const data = response.data as { import?: ArtifactImportRecord };
      if (!data.import) throw new Error('La API no devolvió el registro DRAFT persistido.');
      persisted = data.import; state = 'saved';
      message = 'PASS · importación persistida como DRAFT runtime; source/workspace sin writes.';
      options.onDraftPersisted?.(persisted);
      await loadRecent();
    } catch (error) { state = 'block'; message = readable(error); }
    draw();
  }

  async function loadRecent(): Promise<void> {
    try {
      const response = await client().recentArtifactImports(10);
      const data = response.data as { imports?: Array<Record<string, unknown>> };
      recent = Array.isArray(data.imports) ? data.imports : [];
    } catch { recent = []; }
  }

  async function onFile(file?: File): Promise<void> {
    preview = undefined; persisted = undefined;
    if (!file) { originalFilename = ''; declaredMime = ''; contentBase64 = ''; state = 'idle'; message = 'Seleccione un archivo .md o .json.'; draw(); return; }
    const ext = file.name.includes('.') ? `.${file.name.split('.').pop()?.toLowerCase()}` : '';
    if (!ALLOWED.has(ext)) { originalFilename = ''; declaredMime = ''; contentBase64 = ''; state = 'block'; message = 'BLOCK: solo se admiten archivos .md y .json.'; draw(); return; }
    if (file.size > MAX_IMPORT_BYTES) { originalFilename = ''; declaredMime = ''; contentBase64 = ''; state = 'block'; message = 'BLOCK: el archivo supera el límite client-side de 1 MiB; el servidor vuelve a verificar el límite.'; draw(); return; }
    const bytes = new Uint8Array(await file.arrayBuffer());
    originalFilename = file.name;
    declaredMime = file.type || '';
    contentBase64 = bytesToBase64(bytes);
    state = 'idle'; message = 'Archivo cargado solo en memoria del navegador. Genere preview; todavía no hay persistencia.'; draw();
  }

  function draw(): void {
    root.replaceChildren();
    const heading = document.createElement('div'); heading.className = 'artifact-editor-heading';
    const title = document.createElement('h2'); title.textContent = 'Artifact Workbench · importar fuente externa';
    heading.append(title, renderContractBadges('ui.workspace-documents', { dryRunLabel: 'PREVIEW → DRAFT', warning: 'URL/reference es metadata: GSDLC-04-C nunca hace fetch de red.' }));
    root.append(heading);
    const intro = document.createElement('p'); intro.textContent = 'Pegue texto o adjunte Markdown/JSON. DevPilot normaliza encoding/EOL, calcula hash original + normalizado, muestra preview/diff y solo después permite un DRAFT runtime con provenance.'; root.append(intro);

    const form = document.createElement('div'); form.className = 'artifact-import-form';
    const mode = selectField('Origen', [['PASTE','Pegar texto'],['UPLOAD','Upload local'],['IMPORT','Importar archivo externo']], sourceType, (value) => { sourceType = value as ArtifactImportSourceType; originalFilename=''; declaredMime=''; contentBase64=''; invalidate(); });
    const destination = inputField('Destino relativo (.md/.json)', destinationPath, (value) => { destinationPath=value; invalidate(); });
    const label = inputField('Source label (opcional)', sourceLabel, (value) => { sourceLabel=value; invalidate(); });
    const reference = inputField('URL / reference (metadata, no fetch)', sourceReference, (value) => { sourceReference=value; invalidate(); });
    form.append(mode, destination, label, reference);
    if (sourceType === 'PASTE') {
      const wrap = document.createElement('label'); wrap.className='artifact-import-field artifact-import-content'; const span=document.createElement('span'); span.textContent='Contenido pegado'; const area=document.createElement('textarea'); area.rows=10; area.value=pasteContent; area.addEventListener('input',()=>{pasteContent=area.value; preview=undefined; persisted=undefined; state='idle'; message='Texto modificado: genere preview nuevo.'; drawStatus();}); wrap.append(span,area); form.append(wrap);
    } else {
      const wrap=document.createElement('label'); wrap.className='artifact-import-field artifact-import-file'; const span=document.createElement('span'); span.textContent=sourceType==='UPLOAD'?'Archivo local':'Archivo de fuente externa'; const input=document.createElement('input'); input.type='file'; input.accept='.md,.json,text/markdown,application/json,text/plain'; input.addEventListener('change',()=>void onFile(input.files?.[0])); wrap.append(span,input); if(originalFilename){const note=document.createElement('small');note.textContent=`En memoria: ${originalFilename}`;wrap.append(note);} form.append(wrap);
    }
    root.append(form);

    const status=document.createElement('div'); status.className='artifact-import-status'; status.dataset.importStatus='true'; status.dataset.state=state; status.setAttribute('role',state==='block'?'alert':'status'); status.setAttribute('aria-live','polite'); status.textContent=message; root.append(status);
    const actions=document.createElement('div'); actions.className='artifact-editor-actions';
    actions.append(button('Generar preview',()=>void previewImport(),state==='loading'),button('Crear DRAFT',()=>void persistImport(),state==='loading'||!preview||Boolean(preview?.secret_warning),'button-secondary')); root.append(actions);

    if (preview) root.append(renderPreview(preview));
    if (persisted) root.append(renderProvenance(persisted));
    if (recent.length) root.append(renderRecent(recent));
    if (state==='block') root.append(renderUiStateNotice('block','Importación bloqueada de forma fail-closed. Corrija la entrada y genere un preview nuevo; no hubo write del source.'));
  }

  function drawStatus(): void { const status=root.querySelector<HTMLElement>('[data-import-status]'); if(status){status.textContent=message;status.dataset.state=state;} }
  draw(); void loadRecent().then(draw); return root;
}

function renderPreview(value: ArtifactImportPreview): HTMLElement {
  const section=document.createElement('section'); section.className='artifact-import-preview'; const h=document.createElement('h3');h.textContent='Preview / diff antes de persistir';section.append(h);
  const dl=document.createElement('dl');dl.className='artifact-editor-identity';
  for(const [k,v] of [['Origen',value.source_type],['Destino',value.relative_path],['MIME declarado',value.declared_mime??'—'],['Encoding',value.encoding],['SHA original',value.original_sha256],['SHA normalizado',value.normalized_sha256],['Preview SHA',value.preview_sha256],['Destino existente',String(value.destination_exists)],['Secret warning',String(value.secret_warning)]]) appendDefinition(dl,k,String(v)); section.append(dl);
  const preview=document.createElement('pre');preview.className='artifact-import-content-preview';preview.textContent=value.normalized_content;section.append(preview);
  const diff=document.createElement('pre');diff.className='artifact-import-diff';diff.textContent=value.diff||'(sin diferencias textuales frente al destino actual)';section.append(diff);
  return section;
}

function renderProvenance(value: ArtifactImportRecord): HTMLElement {
  const section=document.createElement('section');section.className='artifact-provenance-panel';const h=document.createElement('h3');h.textContent='Artifact provenance · DRAFT';section.append(h);
  const dl=document.createElement('dl');dl.className='artifact-editor-identity';
  for(const [k,v] of [['Import ID',value.import_id],['Estado',value.lifecycle_state],['Origen',value.source_type],['MIME declarado',value.declared_mime??'—'],['Source label',value.source_label??'—'],['Source reference',value.source_reference??'—'],['SHA original',value.original_sha256],['SHA normalizado',value.normalized_sha256],['Workspace writes','false'],['Network','false']]) appendDefinition(dl,k,String(v));section.append(dl);
  const note=document.createElement('p');note.textContent='Este DRAFT runtime no es APPROVED/FROZEN ni evidence y no creó/modificó el archivo destino. La promoción gobernada corresponde a GSDLC-04-D.';section.append(note);return section;
}

function renderRecent(values:Array<Record<string,unknown>>):HTMLElement{const section=document.createElement('section');section.className='artifact-import-recent';const h=document.createElement('h3');h.textContent='Imports DRAFT recientes';const list=document.createElement('ul');for(const item of values){const li=document.createElement('li');li.textContent=`${String(item.source_type??'')} · ${String(item.relative_path??'')} · ${String(item.normalized_sha256??'').slice(0,12)}`;list.append(li);}section.append(h,list);return section;}
function button(label:string,action:()=>void,disabled=false,className=''):HTMLButtonElement{const b=document.createElement('button');b.type='button';b.textContent=label;b.disabled=disabled;if(className)b.className=className;b.addEventListener('click',action);return b;}
function inputField(label:string,value:string,onChange:(value:string)=>void):HTMLElement{const wrap=document.createElement('label');wrap.className='artifact-import-field';const span=document.createElement('span');span.textContent=label;const input=document.createElement('input');input.type='text';input.value=value;input.addEventListener('input',()=>onChange(input.value));wrap.append(span,input);return wrap;}
function selectField(label:string,options:Array<[string,string]>,value:string,onChange:(value:string)=>void):HTMLElement{const wrap=document.createElement('label');wrap.className='artifact-import-field';const span=document.createElement('span');span.textContent=label;const select=document.createElement('select');for(const [v,t] of options){const option=document.createElement('option');option.value=v;option.textContent=t;option.selected=v===value;select.append(option);}select.addEventListener('change',()=>onChange(select.value));wrap.append(span,select);return wrap;}
function appendDefinition(list:HTMLDListElement,term:string,value:string):void{const dt=document.createElement('dt');dt.textContent=term;const dd=document.createElement('dd');const code=document.createElement('code');code.textContent=value;dd.append(code);list.append(dt,dd);}
function bytesToBase64(bytes:Uint8Array):string{let binary='';const chunk=0x8000;for(let i=0;i<bytes.length;i+=chunk)binary+=String.fromCharCode(...bytes.subarray(i,Math.min(i+chunk,bytes.length)));return btoa(binary);}
function readable(error:unknown):string{return error instanceof Error?error.message:String(error);}
