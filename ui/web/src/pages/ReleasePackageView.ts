import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { ReleasePackagePlan, ReleasePackageResult } from '../api/types';
import { renderOperationalSurfaceSummary } from '../components/OperationalPatterns';

function short(value: string | undefined, n = 12): string { return value ? value.slice(0, n) : '—'; }
function bytes(value: number | undefined): string { if (!value && value !== 0) return '—'; return `${(value / 1024 / 1024).toFixed(2)} MiB`; }
function fact(label: string, value: string): HTMLElement { const row=document.createElement('div'); row.className='release-package-fact'; const dt=document.createElement('strong'); dt.textContent=label; const dd=document.createElement('span'); dd.textContent=value; row.append(dt,dd); return row; }

function renderPlan(plan: ReleasePackagePlan): HTMLElement {
  const card=document.createElement('article'); card.className='panel release-package-plan'; card.dataset.planId=plan.plan_id;
  const title=document.createElement('h3'); title.textContent='Plan reproducible listo para revisión';
  const note=document.createElement('p'); note.textContent='Dry-run únicamente. El plan está ligado al commit/tree exactos y todavía no crea el paquete.';
  const facts=document.createElement('div'); facts.className='release-package-facts';
  facts.append(
    fact('Commit', plan.source_authority.commit),
    fact('Tree', plan.source_authority.tree),
    fact('Versión', plan.release_version),
    fact('Destino local', plan.expected_package_path),
    fact('Plan hash', plan.plan_hash),
    fact('Red / API externa', `${plan.network_used ? 'SÍ' : 'NO'} / ${plan.external_api_used ? 'SÍ' : 'NO'}`),
  );
  card.append(title,note,facts); return card;
}

function renderResult(result: ReleasePackageResult): HTMLElement {
  const wrap=document.createElement('div'); wrap.className='release-package-result'; wrap.dataset.packageStatus=result.status;
  const hero=document.createElement('article'); hero.className='panel release-package-hero';
  const eyebrow=document.createElement('p'); eyebrow.className='release-package-eyebrow'; eyebrow.textContent='Release Package · GSDLC-11-B';
  const title=document.createElement('h2'); title.textContent=result.status==='PASS' ? 'Paquete reproducible verificado' : `Estado ${result.status}`;
  const body=document.createElement('p'); body.textContent='Artefacto local commit-bound. El browser muestra evidencia; no concede autoridad de publicación ni altera el commit.';
  hero.append(eyebrow,title,body);
  const integrity=document.createElement('article'); integrity.className='panel'; const it=document.createElement('h3'); it.textContent='Integridad y provenance'; const facts=document.createElement('div'); facts.className='release-package-facts'; facts.append(
    fact('Commit exacto', result.source_authority.commit),
    fact('Tree exacto', result.source_authority.tree),
    fact('Artifact', result.artifact.path),
    fact('SHA-256', result.artifact.sha256),
    fact('Tamaño', bytes(result.artifact.size_bytes)),
    fact('Archivos', String(result.artifact.file_count ?? result.included_files_total)),
    fact('Checksum sidecar', result.checksums.path),
    fact('SBOM', `${result.sbom.path} · ${result.sbom.format}`),
  ); integrity.append(it,facts);
  const repro=document.createElement('article'); repro.className='panel'; const rt=document.createElement('h3'); rt.textContent='Reproducibilidad'; const rb=document.createElement('p'); rb.textContent=`Package byte-reproducible: ${result.reproducibility.package_byte_reproducible ? 'PASS' : 'BLOCK'} · SBOM semantic: ${result.reproducibility.sbom_semantically_reproducible ? 'PASS' : 'BLOCK'}.`; const rn=document.createElement('p'); rn.className='release-package-muted'; rn.textContent='Timestamps permitidos se normalizan solo para comparación semántica; no se ignoran hashes del artefacto.'; repro.append(rt,rb,rn);
  const boundary=document.createElement('article'); boundary.className='panel'; const bt=document.createElement('h3'); bt.textContent='Límites de autoridad'; const bp=document.createElement('p'); bp.textContent='Local-only. No publish, upload, deploy, tag ni firma remota. El SBOM es inventario local baseline: no certifica vulnerabilidades, licencias ni compliance.'; boundary.append(bt,bp);
  wrap.append(hero,integrity,repro,boundary); return wrap;
}

export function renderReleasePackageView(tokenProvider: () => string | null): HTMLElement {
  const section=document.createElement('section'); section.className='release-package-view'; section.dataset.uiRouteId='ui.release-package';
  const toolbar=document.createElement('div'); toolbar.className='release-package-toolbar';
  const intro=document.createElement('div'); const h=document.createElement('h2'); h.textContent='Reproducibility, source package, checksum and SBOM'; const p=document.createElement('p'); p.textContent='Planifica primero; ejecuta después de revisar commit/tree. DevPilot reutiliza la maquinaria local existente y nunca publica desde esta vista.'; intro.append(h,p);
  const actions=document.createElement('div'); actions.className='release-package-actions';
  const refresh=document.createElement('button'); refresh.type='button'; refresh.textContent='Actualizar estado';
  const planButton=document.createElement('button'); planButton.type='button'; planButton.textContent='1. Preparar plan (dry-run)';
  const executeButton=document.createElement('button'); executeButton.type='button'; executeButton.textContent='2. Ejecutar paquete local'; executeButton.disabled=true;
  actions.append(refresh,planButton,executeButton); toolbar.append(intro,actions);
  const content=document.createElement('div'); content.className='release-package-content'; section.append(toolbar,renderOperationalSurfaceSummary({eyebrow:'Operación · Release package',title:'Paquete reproducible y verificable',state:'ready',stateDetail:'Plan dry-run ligado a commit/tree exactos antes de materializar artefactos.',primaryAction:{label:'Preparar plan reproducible',hierarchy:'primary',detail:'Package execute solo desde un plan vigente.'},gate:{label:'Package integrity',state:'PENDING',detail:'Checksum/SBOM/source package deben concordar.'},diff:{risk:'bounded',detail:'La autoridad es el source commit/tree exactos, no el working tree accidental.'},evidenceSummary:'Checksum / SBOM / provenance',evidenceBody:'plan hash · source commit/tree · package SHA-256 · SBOM · network/external API flags.'}),content);
  let currentPlan: ReleasePackagePlan | null=null;
  const client=()=>new DevPilotApiClient({token:tokenProvider()});
  const showError=(error:unknown)=>{const card=document.createElement('article'); card.className='panel release-package-error'; const t=document.createElement('h3');t.textContent='Operación bloqueada'; const m=document.createElement('p');m.textContent=error instanceof DevPilotApiError?error.message:error instanceof Error?error.message:String(error); const hint=document.createElement('p');hint.className='release-package-muted';hint.textContent='DevPilot falla cerrado: revisa el finding y no intentes publicar o modificar artefactos manualmente.';card.append(t,m,hint);content.replaceChildren(card);};
  const load=async()=>{refresh.disabled=true;try{const response=await client().releasePackageStatus();const data=response.data?.release_package;if(data&&'artifact' in data){content.replaceChildren(renderResult(data as ReleasePackageResult));}else{const empty=document.createElement('article');empty.className='panel';empty.innerHTML='<h3>Sin paquete ejecutado</h3><p>Comienza con el plan dry-run. Ningún artefacto de release se ha publicado.</p>';content.replaceChildren(empty);}}catch(error){showError(error);}finally{refresh.disabled=false;}};
  planButton.addEventListener('click',()=>void(async()=>{planButton.disabled=true;executeButton.disabled=true;try{const response=await client().releasePackagePlan();currentPlan=response.data?.plan??null;if(!currentPlan)throw new Error('La API no devolvió el plan commit-bound.');content.replaceChildren(renderPlan(currentPlan));executeButton.disabled=false;}catch(error){showError(error);}finally{planButton.disabled=false;}})());
  executeButton.addEventListener('click',()=>void(async()=>{if(!currentPlan)return;executeButton.disabled=true;planButton.disabled=true;try{const response=await client().releasePackageExecute(currentPlan.plan_id,currentPlan.plan_hash);const result=response.data?.release_package;if(!result)throw new Error('La API no devolvió release_artifact_manifest.');content.replaceChildren(renderResult(result));}catch(error){showError(error);executeButton.disabled=false;}finally{planButton.disabled=false;}})());
  refresh.addEventListener('click',()=>void load()); void load(); return section;
}
