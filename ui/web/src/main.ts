import { DevPilotApiClient, DevPilotApiError, readStoredToken } from './api/client';
import type { AuthSessionContext } from './api/types';
import { renderDashboard } from './pages/Dashboard';
import { renderReportsView } from './pages/ReportsView';
import { renderTracesView } from './pages/TracesView';
import { renderJobsView } from './pages/JobsView';
import { renderQualityOperationsView } from './pages/QualityOperationsView';
import { renderAiOperationsView } from './pages/AiOperationsView';
import { renderApprovalCenterView } from './pages/ApprovalCenterView';
import { renderSettingsView } from './pages/SettingsView';
import { renderWorkspaceDocumentsView } from './pages/WorkspaceDocumentsView';
import { renderProjectStatusView } from './pages/ProjectStatusView';
import { renderProjectEntryDryRunView } from './pages/ProjectEntryDryRunView';
import { renderLoginView } from './pages/LoginView';
import { renderFirstRunOwnerView } from './pages/FirstRunOwnerView';
import { renderAccountRoleView } from './pages/AccountRoleView';
import { renderSessionBanner } from './components/SessionBanner';
import './styles.css';

const root = document.querySelector<HTMLElement>('#app');
if (!root) throw new Error('No se encontró el contenedor #app para DevPilot Web UI.');

interface UiRoute { path: string; routeId: string; title: string; }
const UI_ROUTES: UiRoute[] = [
  { path: '/', routeId: 'ui.dashboard', title: 'Dashboard' },
  { path: '/project/status', routeId: 'ui.project-status', title: 'Estado del proyecto' },
  { path: '/project/entry', routeId: 'ui.project-entry-dry-run', title: 'Crear / Abrir / Importar' },
  { path: '/workspace/documents', routeId: 'ui.workspace-documents', title: 'Documentos' },
  { path: '/reports', routeId: 'ui.reports', title: 'Reportes' },
  { path: '/traces', routeId: 'ui.traces', title: 'Trazas' },
  { path: '/jobs', routeId: 'ui.jobs', title: 'Jobs' },
  { path: '/quality', routeId: 'ui.quality', title: 'Calidad / Tests' },
  { path: '/ai', routeId: 'ui.ai', title: 'IA / RAG' },
  { path: '/approvals', routeId: 'ui.approvals', title: 'Approval Center' },
  { path: '/settings', routeId: 'ui.settings', title: 'Configuración' },
  { path: '/account', routeId: 'ui.account-role', title: 'Cuenta / Roles' },
];

void bootstrapAuthenticatedUi(root);

async function bootstrapAuthenticatedUi(target: HTMLElement): Promise<void> {
  const path=normalizePath(globalThis.location.pathname);
  const params=new URLSearchParams(globalThis.location.search);
  const client=new DevPilotApiClient();
  try {
    const bootstrap=await client.authBootstrapStatus();
    if (bootstrap.first_run_required) {
      if (path !== '/first-run') return redirect('/first-run');
      target.replaceChildren(renderFirstRunOwnerView(()=>redirect('/')));
      return;
    }
    const status=await client.authSessionStatus();
    if (!status.authenticated || status.state !== 'active') {
      const reason=status.state==='expired'?'expired':status.state==='revoked'?'revoked':status.state==='stale'?'stale':'required';
      if (path !== '/login') return redirect(`/login?reason=${encodeURIComponent(reason)}&return=${encodeURIComponent(path)}`);
      target.replaceChildren(renderLoginView(()=>redirect(safeReturn(params.get('return'))), params.get('reason') ?? reason));
      return;
    }
    const envelope=await client.authSession();
    if (path === '/login' || path === '/first-run') return redirect(safeReturn(params.get('return')));
    renderApplication(target,envelope.session);
  } catch (error) {
    if (path !== '/login' && path !== '/first-run') return redirect(`/login?reason=required&return=${encodeURIComponent(path)}`);
    const message=error instanceof DevPilotApiError && error.status===0 ? 'API local no disponible. Inicia la API en 127.0.0.1:8787.' : 'No fue posible validar el estado de autenticación local.';
    const section=document.createElement('section'); section.className='auth-page'; section.innerHTML=`<div class="auth-card"><h1>Autenticación no disponible</h1><p>${message}</p><p>DevPilot falla cerrado: el Project Shell no se abre sin sesión humana validada.</p></div>`; target.replaceChildren(section);
  }
}

function renderApplication(target: HTMLElement, session: AuthSessionContext): void {
  const currentPath = normalizePath(globalThis.location.pathname);
  const jobsDetail = currentPath.match(/^\/jobs\/(job_[A-Za-z0-9_-]+)$/);
  const route = UI_ROUTES.find((item) => item.path === currentPath) ?? (jobsDetail ? UI_ROUTES.find((item) => item.path === '/jobs') : undefined);
  target.replaceChildren();
  const shell = document.createElement('div'); shell.className = 'app-shell';
  const skipLink = document.createElement('a'); skipLink.className = 'skip-link'; skipLink.href = '#route-main'; skipLink.textContent = 'Saltar al contenido principal';
  shell.append(skipLink, renderSessionBanner(session,()=>redirect('/login?reason=logout')), renderPrimaryNavigation(currentPath));
  const page = document.createElement('div'); page.className = 'route-page'; page.id = 'route-main'; page.setAttribute('role', 'main'); page.setAttribute('tabindex', '-1'); page.dataset.routePath = currentPath;
  if (!route) page.append(renderNotFound(currentPath));
  else if (route.path === '/') renderDashboard(page);
  else {
    page.append(renderRouteHeader(route,session));
    if (route.path === '/project/status') page.append(renderProjectStatusView(() => readStoredToken()));
    else if (route.path === '/project/entry') page.append(renderProjectEntryDryRunView());
    else if (route.path === '/workspace/documents') page.append(renderWorkspaceDocumentsView(() => readStoredToken()));
    else if (route.path === '/reports') page.append(renderReportsView(() => readStoredToken()));
    else if (route.path === '/traces') page.append(renderTracesView(() => readStoredToken()));
    else if (route.path === '/jobs') page.append(renderJobsView(() => readStoredToken(), jobsDetail?.[1]));
    else if (route.path === '/quality') page.append(renderQualityOperationsView(() => readStoredToken()));
    else if (route.path === '/ai') page.append(renderAiOperationsView(() => readStoredToken()));
    else if (route.path === '/approvals') page.append(renderApprovalCenterView(() => readStoredToken()));
    else if (route.path === '/settings') page.append(renderSettingsView(new DevPilotApiClient({ token: readStoredToken() }), () => readStoredToken()));
    else if (route.path === '/account') page.append(renderAccountRoleView(session));
  }
  shell.append(page); target.append(shell);
}

function renderPrimaryNavigation(currentPath: string): HTMLElement {
  const nav = document.createElement('nav'); nav.className = 'primary-nav'; nav.setAttribute('aria-label', 'Navegación principal DevPilot');
  const brand = document.createElement('a'); brand.href = '/'; brand.className = 'primary-nav__brand'; brand.textContent = 'DevPilot Local';
  const links = document.createElement('div'); links.className = 'primary-nav__links';
  for (const route of UI_ROUTES) { const link=document.createElement('a'); link.href=route.path; link.textContent=route.title; link.dataset.routeId=route.routeId; if(route.path===currentPath||(route.path==='/jobs'&&currentPath.startsWith('/jobs/'))){link.classList.add('is-active');link.setAttribute('aria-current','page');} links.append(link); }
  nav.append(brand, links); return nav;
}

function renderRouteHeader(route: UiRoute, session: AuthSessionContext): HTMLElement {
  const header=document.createElement('header'); header.className='route-header'; const heading=document.createElement('div'); const title=document.createElement('h1'); title.textContent=route.title; const meta=document.createElement('p'); meta.textContent=`${route.routeId} · ${route.path} · human-session · ${session.principal.roles.join(', ')} · local-first · no-remote · TTL máximo de 8h`; heading.append(title,meta); header.append(heading); return header;
}
function renderNotFound(path:string):HTMLElement{const section=document.createElement('section');section.className='panel route-not-found';const title=document.createElement('h1');title.textContent='Ruta UI no registrada';const description=document.createElement('p');description.textContent=`La ruta ${path} no pertenece al contrato local. Usa la navegación principal.`;section.append(title,description);return section;}
function normalizePath(path:string):string{if(!path||path==='/')return '/';const normalized=path.replace(/\/+$/,'');return normalized||'/';}
function safeReturn(value:string|null):string{if(!value||!value.startsWith('/')||value.startsWith('//')||value==='/login'||value==='/first-run')return '/';return value;}
function redirect(path:string):void{globalThis.location.replace(path);}
