import { DevPilotApiClient, DevPilotApiError } from '../api/client';
import type { ReleaseReadinessBlocker, ReleaseReadinessProjection } from '../api/types';
import { renderOperationalSurfaceSummary } from '../components/OperationalPatterns';

function text(value: unknown, fallback = 'No disponible'): string {
  return value === null || value === undefined || String(value).trim() === '' ? fallback : String(value);
}

function stateLabel(state: string): string {
  if (state === 'RELEASE_READY') return 'Lista para preparar release';
  if (state === 'BLOCKED') return 'Bloqueada';
  return 'Evidencia incompleta';
}

function renderBlocker(blocker: ReleaseReadinessBlocker): HTMLElement {
  const row = document.createElement('article');
  row.className = 'release-readiness-blocker';
  row.dataset.blockerId = blocker.blocker_id;
  row.dataset.severity = blocker.severity;
  const head = document.createElement('div'); head.className = 'release-readiness-blocker__head';
  const title = document.createElement('h4'); title.textContent = blocker.title;
  const severity = document.createElement('span'); severity.className = 'release-readiness-severity'; severity.textContent = blocker.severity;
  head.append(title, severity);
  const facts = document.createElement('dl'); facts.className = 'release-readiness-facts';
  for (const [label, value] of [['Responsable', blocker.owner], ['Política', blocker.policy_source], ['Evidencia', blocker.evidence_ref]]) {
    const dt=document.createElement('dt'); dt.textContent=label; const dd=document.createElement('dd'); dd.textContent=text(value); facts.append(dt,dd);
  }
  const action = document.createElement('p'); action.className='release-readiness-action'; action.textContent=`Siguiente acción: ${blocker.next_action}`;
  row.append(head, facts, action); return row;
}

function renderProjection(projection: ReleaseReadinessProjection): HTMLElement {
  const wrap = document.createElement('div'); wrap.className='release-readiness-layout'; wrap.dataset.releaseReadinessState=projection.state;

  const hero=document.createElement('article'); hero.className=`panel release-readiness-hero release-readiness-hero--${projection.state.toLowerCase()}`;
  const eyebrow=document.createElement('p'); eyebrow.className='release-readiness-eyebrow'; eyebrow.textContent='Release Readiness · GSDLC-11-A';
  const title=document.createElement('h2'); title.textContent=stateLabel(projection.state);
  const summary=document.createElement('p'); summary.textContent=projection.release_ready
    ? 'Todas las evidencias obligatorias current-active están completas. Esto habilita la preparación de artefactos de 11-B; no constituye aprobación de release.'
    : projection.state === 'UNKNOWN'
      ? 'DevPilot falla cerrado porque falta evidencia actual o no puede verificarse. Resuelve la primera acción indicada antes de continuar.'
      : 'Existen blockers explícitos. DevPilot no declara RELEASE_READY hasta resolverlos.';
  const badge=document.createElement('span'); badge.className='release-readiness-state'; badge.textContent=projection.state;
  hero.append(eyebrow,title,badge,summary);

  const next=document.createElement('article'); next.className='panel release-readiness-next';
  const nextTitle=document.createElement('h3'); nextTitle.textContent='Próxima acción determinística';
  const nextBody=document.createElement('p'); nextBody.textContent=text(projection.next_action?.title);
  const nextMeta=document.createElement('p'); nextMeta.className='release-readiness-muted'; nextMeta.textContent=`Responsable: ${text(projection.next_action?.owner)} · Evidencia: ${text(projection.next_action?.evidence_ref)}`;
  next.append(nextTitle,nextBody,nextMeta);

  const authority=document.createElement('article'); authority.className='panel release-readiness-authority';
  const aTitle=document.createElement('h3'); aTitle.textContent='Autoridad de release';
  const aBody=document.createElement('p'); aBody.textContent=projection.release_authority.allowed
    ? `La sesión incluye rol de release (${projection.release_authority.release_roles.join(', ')}), pero readiness NO equivale a aprobación.`
    : 'La sesión puede consultar readiness, pero no tiene rol release-manager/owner para una futura aprobación de release.';
  const boundary=document.createElement('p'); boundary.className='release-readiness-muted'; boundary.textContent='Modelos/agentes no pueden aprobar, ampliar waivers ni convertir READY en una autorización de release.';
  authority.append(aTitle,aBody,boundary);

  const claims=document.createElement('article'); claims.className='panel release-readiness-claims';
  const cTitle=document.createElement('h3'); cTitle.textContent='Alcance de los claims';
  const cBody=document.createElement('p'); cBody.textContent='Local-only. No se declara enterprise-ready, compliance-certified ni public-release.';
  claims.append(cTitle,cBody);

  const blockers=document.createElement('section'); blockers.className='release-readiness-blockers';
  const bTitle=document.createElement('h3'); bTitle.textContent=`Blockers y evidencia (${projection.blockers_total})`;
  blockers.append(bTitle);
  if (!projection.blockers.length) {
    const empty=document.createElement('p'); empty.className='panel release-readiness-empty'; empty.textContent='No hay blockers current-active. La preparación reproducible pertenece a GSDLC-11-B.'; blockers.append(empty);
  } else projection.blockers.forEach((item)=>blockers.append(renderBlocker(item)));

  wrap.append(hero,next,authority,claims,blockers); return wrap;
}

export function renderReleaseReadinessView(tokenProvider: () => string | null): HTMLElement {
  const section=document.createElement('section'); section.className='release-readiness-view'; section.dataset.uiRouteId='ui.release-readiness';
  const toolbar=document.createElement('div'); toolbar.className='release-readiness-toolbar';
  const intro=document.createElement('p'); intro.textContent='Proyección read-only y project-scoped. DevPilot explica blockers, evidencia y siguiente acción sin conceder autoridad de release.';
  const refresh=document.createElement('button'); refresh.type='button'; refresh.textContent='Actualizar readiness';
  toolbar.append(intro,refresh);
  const content=document.createElement('div'); content.className='release-readiness-content';
  section.append(toolbar,renderOperationalSurfaceSummary({eyebrow:'Operación · Release',title:'Readiness antes de preparar release',state:'ready',stateDetail:'Read-only projection: blockers y evidencia determinan RELEASE_READY.',primaryAction:{label:'Actualizar readiness',hierarchy:'primary',detail:'Actualizar no aprueba ni publica una release.'},gate:{label:'Release readiness',state:'PENDING',detail:'READY/BLOCKED/UNKNOWN provienen del backend.'},approval:{required:false,status:'readiness != approval',effect:'La aprobación de release permanece separada.'},evidenceSummary:'Evidencia de readiness',evidenceBody:'Blockers · owners · policy source · evidence refs · release authority. Guided muestra decisión; Expert conserva detalles.'}),content);

  const load=async()=>{
    refresh.disabled=true; content.replaceChildren();
    const loading=document.createElement('p'); loading.className='panel release-readiness-loading'; loading.textContent='Calculando release readiness desde autoridad server-side…'; content.append(loading);
    try {
      const client=new DevPilotApiClient({ token: tokenProvider() });
      const response=await client.releaseReadiness();
      const projection=response.data?.release_readiness;
      if (!projection) throw new Error('La API no devolvió ReleaseReadinessProjection.');
      content.replaceChildren(renderProjection(projection));
    } catch(error) {
      const card=document.createElement('article'); card.className='panel release-readiness-error';
      const title=document.createElement('h3'); title.textContent='Readiness no disponible';
      const message=document.createElement('p'); message.textContent=error instanceof DevPilotApiError ? error.message : error instanceof Error ? error.message : String(error);
      const hint=document.createElement('p'); hint.className='release-readiness-muted'; hint.textContent='DevPilot falla cerrado. Verifica sesión, proyecto activo y API local; no interpretes este estado como READY.';
      card.append(title,message,hint); content.replaceChildren(card);
    } finally { refresh.disabled=false; }
  };
  refresh.addEventListener('click',()=>void load()); void load(); return section;
}
