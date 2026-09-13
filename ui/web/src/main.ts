import { clearProjectJourneyContext, clearProjectRecoveryIntent, DevPilotApiClient, DevPilotApiError, parseExplicitProjectRecoveryIntent, projectRecoveryTarget, readApprovalCenterArtifactReviewHandoff, readApprovalCenterEntryHandoff, readProjectJourneyContext, readProjectRecoveryIntent, readStoredToken, resolvePostLoginReturn, restoreProjectJourneyContextFromDurableRecovery, restoreProjectJourneyContextFromProjectStatusRecovery, restoreProjectJourneyContextFromRegisteredWorkspaceRecovery, restoreProjectJourneyContextFromServerRecovery, saveProjectRecoveryIntent } from './api/client';
import type { ProjectJourneyContext } from './api/client';
import type { AuthSessionContext } from './api/types';
import { renderDashboard } from './pages/Dashboard';
import { renderReportsView } from './pages/ReportsView';
import { renderTracesView } from './pages/TracesView';
import { renderJobsView } from './pages/JobsView';
import { renderQualityOperationsView } from './pages/QualityOperationsView';
import { renderReleaseReadinessView } from './pages/ReleaseReadinessView';
import { renderReleasePackageView } from './pages/ReleasePackageView';
import { renderReleaseLifecycleView } from './pages/ReleaseLifecycleView';
import { renderReleaseMetadataView } from './pages/ReleaseMetadataView';
import { renderReleaseClosureView } from './pages/ReleaseClosureView';
import { renderRecoveryView } from './pages/RecoveryView';
import { renderConflictResolutionView } from './pages/ConflictResolutionView';
import { renderAiOperationsView } from './pages/AiOperationsView';
import { renderApprovalCenterView } from './pages/ApprovalCenterView';
import { renderSettingsView } from './pages/SettingsView';
import { renderWorkspaceDocumentsView } from './pages/WorkspaceDocumentsView';
import { renderProjectStatusView } from './pages/ProjectStatusView';
import { renderPreCodeWizardView } from './pages/PreCodeWizardView';
import { renderRoadmapWorkbenchView } from './pages/RoadmapWorkbenchView';
import { renderStoryCodeWorkbenchView } from './pages/StoryCodeWorkbenchView';
import { renderProjectEntryDryRunView } from './pages/ProjectEntryDryRunView';
import { renderLoginView } from './pages/LoginView';
import { renderFirstRunOwnerView } from './pages/FirstRunOwnerView';
import { renderAccountRoleView } from './pages/AccountRoleView';
import { renderSessionBanner } from './components/SessionBanner';
import { renderExperienceModeControl } from './components/ExperienceModeControl';
import { renderHelpSystemView } from './pages/HelpSystemView';
import { initializeExperienceMode, readExperienceMode } from './ux/experienceMode';
import './styles.css';
import './planning.css';

const root = document.querySelector<HTMLElement>('#app');
if (!root) throw new Error('No se encontró el contenedor #app para DevPilot Web UI.');

interface UiRoute { path: string; routeId: string; title: string; scope: 'home' | 'global' | 'entry' | 'entry-or-project' | 'project'; }
const UI_ROUTES: UiRoute[] = [
  { path: '/', routeId: 'ui.dashboard', title: 'Project Home', scope: 'home' },
  { path: '/project/status', routeId: 'ui.project-status', title: 'Estado del proyecto', scope: 'project' },
  { path: '/pre-code', routeId: 'ui.pre-code-wizard', title: 'Pre-code guiado', scope: 'project' },
  { path: '/planning/roadmap', routeId: 'ui.planning-roadmap', title: 'Planning · Roadmap', scope: 'project' },
  { path: '/project/entry', routeId: 'ui.project-entry-dry-run', title: 'Crear / Abrir / Importar', scope: 'entry' },
  { path: '/workspace/documents', routeId: 'ui.workspace-documents', title: 'Documentos', scope: 'project' },
  { path: '/story/code', routeId: 'ui.story-code-workbench', title: 'Story Code Workbench', scope: 'project' },
  { path: '/reports', routeId: 'ui.reports', title: 'Reportes', scope: 'project' },
  { path: '/traces', routeId: 'ui.traces', title: 'Trazas', scope: 'project' },
  { path: '/jobs', routeId: 'ui.jobs', title: 'Jobs', scope: 'project' },
  { path: '/quality', routeId: 'ui.quality', title: 'Calidad / Tests', scope: 'project' },
  { path: '/release/readiness', routeId: 'ui.release-readiness', title: 'Release readiness', scope: 'project' },
  { path: '/release/package', routeId: 'ui.release-package', title: 'Release package', scope: 'project' },
  { path: '/release/lifecycle', routeId: 'ui.release-lifecycle', title: 'Install / rollback', scope: 'project' },
  { path: '/release/metadata', routeId: 'ui.release-metadata', title: 'Version / tag', scope: 'project' },
  { path: '/release/closure', routeId: 'ui.release-closure', title: 'Release closure', scope: 'project' },
  { path: '/recovery', routeId: 'ui.recovery', title: 'Recovery / Resume', scope: 'project' },
  { path: '/reconciliation', routeId: 'ui.reconciliation', title: 'Conflict Resolution', scope: 'project' },
  { path: '/ai', routeId: 'ui.ai', title: 'IA / RAG', scope: 'project' },
  { path: '/approvals', routeId: 'ui.approvals', title: 'Approval Center', scope: 'entry-or-project' },
  { path: '/settings', routeId: 'ui.settings', title: 'Configuración', scope: 'global' },
  { path: '/account', routeId: 'ui.account-role', title: 'Cuenta / Roles', scope: 'global' },
  { path: '/help', routeId: 'ui.help', title: 'Ayuda', scope: 'global' },
];

initializeExperienceMode();
void bootstrapAuthenticatedUi(root);

async function bootstrapAuthenticatedUi(target: HTMLElement): Promise<void> {
  const path=normalizePath(globalThis.location.pathname);
  const params=new URLSearchParams(globalThis.location.search);
  const explicitRecoveryIntent=parseExplicitProjectRecoveryIntent(path, params);
  const client=new DevPilotApiClient();
  try {
    const bootstrap=await client.authBootstrapStatus();
    if (bootstrap.first_run_required) {
      clearProjectJourneyContext();
      clearProjectRecoveryIntent();
      if (path !== '/first-run') return redirect('/first-run');
      target.replaceChildren(renderFirstRunOwnerView(()=>redirect('/')));
      return;
    }
    const status=await client.authSessionStatus();
    if (!status.authenticated || status.state !== 'active') {
      clearProjectJourneyContext();
      if (explicitRecoveryIntent) saveProjectRecoveryIntent(explicitRecoveryIntent);
      const reason=status.state==='expired'?'expired':status.state==='revoked'?'revoked':status.state==='stale'?'stale':'required';
      if (path !== '/login') {
        const returnTarget=explicitRecoveryIntent ? projectRecoveryTarget(explicitRecoveryIntent) : currentLocationTarget(path);
        return redirect(`/login?reason=${encodeURIComponent(reason)}&return=${encodeURIComponent(returnTarget)}`);
      }
      target.replaceChildren(renderLoginView(()=>redirect(resolvePostLoginReturn(params.get('return'))), params.get('reason') ?? reason));
      return;
    }
    const envelope=await client.authSession();
    if (path === '/login' || path === '/first-run') return redirect(resolvePostLoginReturn(params.get('return')));
    const projectStatusRecoveryOutcome=await recoverExplicitProjectStatusContext(client, envelope.session, path, params);
    if (projectStatusRecoveryOutcome === 'failed') {
      return redirect('/?guard=Estado%20del%20proyecto&attempted=%2Fproject%2Fstatus&recovery=server-context-failed');
    }
    const recoveryOutcome=await recoverExplicitServerProjectContext(client, path, params);
    if (recoveryOutcome === 'failed') {
      clearProjectRecoveryIntent();
      return redirect('/?guard=Documentos&attempted=%2Fworkspace%2Fdocuments&recovery=server-context-failed');
    }
    const routeRecoveryOutcome=await recoverSessionBoundProjectRouteContext(client, envelope.session, path);
    if (routeRecoveryOutcome === 'failed') {
      const route=resolveUiRoute(path);
      const guard=encodeURIComponent(route?.title ?? 'Proyecto');
      const attempted=encodeURIComponent(path);
      return redirect(`/?guard=${guard}&attempted=${attempted}&recovery=session-bound-project-failed`);
    }
    renderApplication(target,envelope.session);
  } catch (error) {
    if (path !== '/login' && path !== '/first-run') {
      if (explicitRecoveryIntent) saveProjectRecoveryIntent(explicitRecoveryIntent);
      const returnTarget=explicitRecoveryIntent ? projectRecoveryTarget(explicitRecoveryIntent) : currentLocationTarget(path);
      return redirect(`/login?reason=required&return=${encodeURIComponent(returnTarget)}`);
    }
    const message=error instanceof DevPilotApiError && error.status===0 ? 'API local no disponible. Inicia la API en 127.0.0.1:8787.' : 'No fue posible validar el estado de autenticación local.';
    const section=document.createElement('section'); section.className='auth-page'; section.innerHTML=`<div class="auth-card"><h1>Autenticación no disponible</h1><p>${message}</p><p>DevPilot falla cerrado: el Project Shell no se abre sin sesión humana validada.</p></div>`; target.replaceChildren(section);
  }
}

function renderApplication(target: HTMLElement, session: AuthSessionContext): void {
  const currentPath = normalizePath(globalThis.location.pathname);
  const jobsDetail = currentPath.match(/^\/jobs\/(job_[A-Za-z0-9_-]+)$/);
  const route = resolveUiRoute(currentPath);
  const params = new URLSearchParams(globalThis.location?.search ?? '');
  const handoffKind = currentPath === '/approvals' ? (params.get('handoff') ?? '').trim() : '';
  const handoffApprovalId = currentPath === '/approvals' && ['project-entry','artifact-review'].includes(handoffKind) ? (params.get('approval_id') ?? '').trim() : '';
  const approvalHandoffJourney = currentPath === '/approvals' && handoffApprovalId
    ? handoffKind === 'project-entry'
      ? readApprovalCenterEntryHandoff(session, handoffApprovalId)
      : handoffKind === 'artifact-review'
        ? readApprovalCenterArtifactReviewHandoff(session, handoffApprovalId)
        : null
    : null;
  const journey = readProjectJourneyContext() ?? approvalHandoffJourney;
  if (route && !routeAllowed(route, journey)) {
    const guard = encodeURIComponent(route.title);
    const attempted = encodeURIComponent(currentPath);
    return redirect(`/?guard=${guard}&attempted=${attempted}`);
  }
  target.replaceChildren();
  const shell = document.createElement('div'); shell.className = 'app-shell'; shell.dataset.experienceMode = readExperienceMode();
  const skipLink = document.createElement('a'); skipLink.className = 'skip-link'; skipLink.href = '#route-main'; skipLink.textContent = 'Saltar al contenido principal';
  shell.append(skipLink, renderSessionBanner(session,()=>{ clearProjectJourneyContext(); clearProjectRecoveryIntent(); redirect('/login?reason=logout'); }), renderExperienceModeControl(), renderPrimaryNavigation(currentPath, journey, Boolean(handoffApprovalId)));
  const page = document.createElement('div'); page.className = 'route-page'; page.id = 'route-main'; page.setAttribute('role', 'main'); page.setAttribute('tabindex', '-1'); page.dataset.routePath = currentPath;
  if (!route) page.append(renderNotFound(currentPath));
  else if (route.path === '/') renderDashboard(page, session, new URLSearchParams(globalThis.location.search).get('guard'));
  else {
    page.append(renderRouteHeader(route,session), renderExperienceModeContext(route, session));
    if (route.path === '/project/status') page.append(renderProjectStatusView(() => readStoredToken()));
    else if (route.path === '/pre-code') page.append(renderPreCodeWizardView(() => readStoredToken(), session));
    else if (route.path === '/planning/roadmap') page.append(renderRoadmapWorkbenchView(() => readStoredToken(), session));
    else if (route.path === '/project/entry') page.append(renderProjectEntryDryRunView({ session, initialMode: readEntryMode(new URLSearchParams(globalThis.location.search).get('mode')) }));
    else if (route.path === '/workspace/documents') page.append(renderWorkspaceDocumentsView(() => readStoredToken(), session));
    else if (route.path === '/story/code') page.append(renderStoryCodeWorkbenchView(() => readStoredToken(), session));
    else if (route.path === '/reports') page.append(renderReportsView(() => readStoredToken()));
    else if (route.path === '/traces') page.append(renderTracesView(() => readStoredToken()));
    else if (route.path === '/jobs') page.append(renderJobsView(() => readStoredToken(), jobsDetail?.[1]));
    else if (route.path === '/quality') page.append(renderQualityOperationsView(() => readStoredToken()));
    else if (route.path === '/release/readiness') page.append(renderReleaseReadinessView(() => readStoredToken()));
    else if (route.path === '/release/package') page.append(renderReleasePackageView(() => readStoredToken()));
    else if (route.path === '/release/lifecycle') page.append(renderReleaseLifecycleView(() => readStoredToken()));
    else if (route.path === '/release/metadata') page.append(renderReleaseMetadataView(() => readStoredToken()));
    else if (route.path === '/release/closure') page.append(renderReleaseClosureView(() => readStoredToken()));
    else if (route.path === '/recovery') page.append(renderRecoveryView(() => readStoredToken()));
    else if (route.path === '/reconciliation') page.append(renderConflictResolutionView(() => readStoredToken()));
    else if (route.path === '/ai') page.append(renderAiOperationsView(() => readStoredToken()));
    else if (route.path === '/approvals') page.append(renderApprovalCenterView({ tokenProvider: () => readStoredToken(), session, handoffApprovalId: handoffApprovalId || undefined }));
    else if (route.path === '/settings') page.append(renderSettingsView(new DevPilotApiClient({ token: readStoredToken() }), () => readStoredToken()));
    else if (route.path === '/account') page.append(renderAccountRoleView(session));
    else if (route.path === '/help') page.append(renderHelpSystemView());
  }
  shell.append(page); target.append(shell); queueMicrotask(() => page.focus());
}


function renderExperienceModeContext(route: UiRoute, session: AuthSessionContext): HTMLElement {
  const wrap = document.createElement('section');
  wrap.className = 'experience-mode-context';
  wrap.setAttribute('aria-label', 'Contexto del modo de experiencia');
  const guided = document.createElement('div');
  guided.className = 'guided-only guided-focus';
  const guidedTitle = document.createElement('strong');
  guidedTitle.textContent = 'Guided · Qué hacer ahora';
  const guidedCopy = document.createElement('span');
  guidedCopy.textContent = guidedNextAction(route.path);
  const guidedSafety = document.createElement('span');
  guidedSafety.className = 'guided-focus__safety';
  guidedSafety.textContent = 'Los blockers críticos siempre permanecen visibles.';
  guided.append(guidedTitle, guidedCopy, guidedSafety);

  const expert = document.createElement('details');
  expert.className = 'expert-only expert-diagnostics';
  expert.open = true;
  const summary = document.createElement('summary');
  summary.textContent = 'Expert diagnostics · autoridad sin cambios';
  const dl = document.createElement('dl');
  for (const [label, value] of [
    ['Route ID', route.routeId],
    ['Scope', route.scope],
    ['Roles', session.principal.roles.join(', ') || 'none'],
    ['Authority', 'server-side'],
    ['RBAC / approvals / tools / models', 'identical-to-guided'],
    ['Mode storage', 'browser UX preference only'],
  ]) {
    const row = document.createElement('div'); const dt = document.createElement('dt'); const dd = document.createElement('dd'); dt.textContent = label; dd.textContent = value; row.append(dt, dd); dl.append(row);
  }
  expert.append(summary, dl);
  wrap.append(guided, expert);
  return wrap;
}

function guidedNextAction(path: string): string {
  const actions: Record<string, string> = {
    '/': 'Elige Crear, Abrir o Importar y revisa el plan antes de ejecutar.',
    '/project/status': 'Lee el estado actual y usa la siguiente acción determinística; resuelve cualquier blocker antes de avanzar.',
    '/pre-code': 'Completa la etapa de ingeniería mostrada y conserva approvals/preimages vigentes.',
    '/planning/roadmap': 'Revisa roadmap, backlog y sprint activo antes de pasar a implementación.',
    '/story/code': 'Trabaja una historia por vez: plan, dry-run, approval cuando aplique, tests y evidencia.',
    '/quality': 'Revisa resultados y blockers; no fuerces un gate fallido.',
    '/release/readiness': 'Comprueba readiness antes de empaquetar o cambiar lifecycle.',
    '/recovery': 'Revisa el contexto recuperable y revalida cualquier trabajo sensible antes de continuar.',
    '/reconciliation': 'Revisa branch, HEAD y cambios externos; adopta autoridad solo después de review explícita.',
    '/approvals': 'Aprueba únicamente operaciones cuyo actor, preimage y evidencia sigan vigentes.',
    '/help': 'Consulta el glosario y las instrucciones de recovery sin cambiar autoridad.',
  };
  return actions[path] ?? 'Completa esta superficie y revisa su resultado antes de continuar. Los detalles avanzados están disponibles en Expert.';
}

function renderPrimaryNavigation(currentPath: string, journey: ProjectJourneyContext | null, auxiliaryApprovalHandoff = false): HTMLElement {
  const nav = document.createElement('nav'); nav.className = 'primary-nav'; nav.setAttribute('aria-label', 'Navegación principal DevPilot');
  nav.dataset.journeyPhase = journey?.phase ?? 'home';
  const brand = document.createElement(auxiliaryApprovalHandoff ? 'span' : 'a'); if(!auxiliaryApprovalHandoff)(brand as HTMLAnchorElement).href='/'; brand.className = 'primary-nav__brand'; brand.textContent = 'DevPilot Local';
  const links = document.createElement('div'); links.className = 'primary-nav__links';
  const advanced = document.createElement('details'); advanced.className = 'primary-nav__advanced'; advanced.open = readExperienceMode() === 'expert';
  const advancedSummary = document.createElement('summary'); advancedSummary.textContent = 'Más herramientas';
  const advancedLinks = document.createElement('div'); advancedLinks.className = 'primary-nav__advanced-links';
  advanced.append(advancedSummary, advancedLinks);
  const guidedCorePaths = new Set(['/', '/project/status', '/pre-code', '/planning/roadmap', '/story/code', '/quality', '/release/readiness', '/recovery', '/reconciliation', '/approvals', '/help', '/account']);
  const visibleRoutes = UI_ROUTES.filter((item) => routeVisible(item, journey) && (!auxiliaryApprovalHandoff || item.path === '/approvals' || item.path === '/account'));
  for (const route of visibleRoutes) {
    const link=document.createElement('a'); link.href=route.path; link.textContent=route.title; link.dataset.routeId=route.routeId;
    if(route.path===currentPath||(route.path==='/jobs'&&currentPath.startsWith('/jobs/'))){link.classList.add('is-active');link.setAttribute('aria-current','page');}
    (guidedCorePaths.has(route.path) ? links : advancedLinks).append(link);
  }
  nav.append(brand, links); if (advancedLinks.childElementCount > 0 && !auxiliaryApprovalHandoff) nav.append(advanced); return nav;
}

function routeAllowed(route: UiRoute, journey: ProjectJourneyContext | null): boolean {
  if (route.scope === 'home' || route.scope === 'global') return true;
  if (route.scope === 'entry') return journey?.phase === 'entry';
  if (route.scope === 'entry-or-project') return journey?.phase === 'entry' || journey?.phase === 'project';
  return journey?.phase === 'project';
}

function routeVisible(route: UiRoute, journey: ProjectJourneyContext | null): boolean {
  if (route.scope === 'entry') return false;
  return routeAllowed(route, journey);
}

function resolveUiRoute(path: string): UiRoute | undefined {
  const jobsDetail = path.match(/^\/jobs\/(job_[A-Za-z0-9_-]+)$/);
  return UI_ROUTES.find((item) => item.path === path) ?? (jobsDetail ? UI_ROUTES.find((item) => item.path === '/jobs') : undefined);
}

async function recoverSessionBoundProjectRouteContext(
  client: DevPilotApiClient,
  session: AuthSessionContext,
  path: string,
): Promise<ProjectRecoveryOutcome> {
  if (readProjectJourneyContext()?.phase === 'project') return 'already-project';
  const route=resolveUiRoute(path);
  if (!route || route.scope !== 'project') return 'not-requested';
  const scopes=[...new Set((session.principal.workspace_scopes ?? []).map((value) => String(value).trim()).filter(Boolean))];
  if (scopes.length !== 1) return 'failed';
  const expectedWorkspaceId=scopes[0];
  try {
    const response=await client.projectStatusSessionRecovery(expectedWorkspaceId);
    const restored=restoreProjectJourneyContextFromProjectStatusRecovery(response, expectedWorkspaceId);
    if (restored) return 'restored';
  } catch { /* A registered project may legitimately have no WorkspaceEngineeringState yet. */ }
  try {
    const workspace=await client.settingsWorkspace();
    const restored=restoreProjectJourneyContextFromRegisteredWorkspaceRecovery(workspace, expectedWorkspaceId);
    if (restored) return 'restored';
  } catch { /* A minimal OPEN_EXISTING fixture may not satisfy the richer settings projection contract. */ }
  try {
    const recovery=await client.recoveryStatus();
    const restored=restoreProjectJourneyContextFromDurableRecovery(recovery, expectedWorkspaceId);
    return restored ? 'restored' : 'failed';
  } catch {
    return 'failed';
  }
}

function renderRouteHeader(route: UiRoute, session: AuthSessionContext): HTMLElement {
  const header=document.createElement('header'); header.className='route-header'; const heading=document.createElement('div'); const title=document.createElement('h1'); title.textContent=route.title; const meta=document.createElement('p'); meta.textContent=`${route.routeId} · ${route.path} · human-session · ${session.principal.roles.join(', ')} · local-first · no-remote · TTL máximo de 8h`; heading.append(title,meta); header.append(heading); return header;
}
function renderNotFound(path:string):HTMLElement{const section=document.createElement('section');section.className='panel route-not-found';const title=document.createElement('h1');title.textContent='Ruta UI no registrada';const description=document.createElement('p');description.textContent=`La ruta ${path} no pertenece al contrato local. Usa la navegación principal.`;section.append(title,description);return section;}

function readEntryMode(value:string|null):'CREATE_NEW'|'OPEN_EXISTING'|'IMPORT_GIT'|undefined{if(value==='CREATE_NEW'||value==='OPEN_EXISTING'||value==='IMPORT_GIT')return value;return undefined;}
function normalizePath(path:string):string{if(!path||path==='/')return '/';const normalized=path.replace(/\/+$/,'');return normalized||'/';}
type ProjectRecoveryOutcome = 'not-requested' | 'already-project' | 'restored' | 'failed';
async function recoverExplicitProjectStatusContext(client: DevPilotApiClient, session: AuthSessionContext, path: string, params: URLSearchParams): Promise<ProjectRecoveryOutcome> {
  if (readProjectJourneyContext()?.phase === 'project') return 'already-project';
  if (path !== '/project/status' || params.get('recover_project_context') !== 'server-active') return 'not-requested';
  const scopes=[...new Set((session.principal.workspace_scopes ?? []).map((value) => String(value).trim()).filter(Boolean))];
  const expectedWorkspaceId=scopes.length===1 ? scopes[0] : undefined;
  try {
    const response=await client.projectStatus();
    const restored=restoreProjectJourneyContextFromProjectStatusRecovery(response);
    if (restored) {
      try { globalThis.history?.replaceState(null, '', '/project/status'); } catch { /* cosmetic only; route authority is already server-validated. */ }
      return 'restored';
    }
  } catch { /* session-bound fallback below keeps recovery read-only and fail-closed. */ }
  if (!expectedWorkspaceId) return 'failed';
  try {
    const response=await client.projectStatusSessionRecovery(expectedWorkspaceId);
    const restored=restoreProjectJourneyContextFromProjectStatusRecovery(response, expectedWorkspaceId);
    if (!restored) return 'failed';
    try { globalThis.history?.replaceState(null, '', '/project/status'); } catch { /* cosmetic only; route authority is already server-validated. */ }
    return 'restored';
  } catch {
    return 'failed';
  }
}
async function recoverExplicitServerProjectContext(client: DevPilotApiClient, path: string, params: URLSearchParams): Promise<ProjectRecoveryOutcome> {
  if (readProjectJourneyContext()?.phase === 'project') {
    clearProjectRecoveryIntent();
    return 'already-project';
  }
  const explicit=parseExplicitProjectRecoveryIntent(path, params);
  if (explicit) saveProjectRecoveryIntent(explicit);
  const intent=explicit ?? readProjectRecoveryIntent();
  if (path !== '/workspace/documents' || !intent) return 'not-requested';
  try {
    const [workspace, execution]=await Promise.all([client.settingsWorkspace(), client.workspaceEditExecutionStatus(intent.execution_id)]);
    const restored=restoreProjectJourneyContextFromServerRecovery(workspace, execution, { executionId:intent.execution_id, documentId:intent.document_id });
    return restored ? 'restored' : 'failed';
  } catch {
    // Recovery is UX-only and fail-closed. A failed explicit recovery is surfaced by bootstrapAuthenticatedUi.
    return 'failed';
  }
}
function currentLocationTarget(path:string):string{return `${path}${globalThis.location.search ?? ''}`;}
function redirect(path:string):void{globalThis.location.replace(path);}
