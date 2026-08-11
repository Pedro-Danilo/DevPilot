import { DevPilotApiClient, readStoredToken, storeToken } from './api/client';
import { renderDashboard } from './pages/Dashboard';
import { renderReportsView } from './pages/ReportsView';
import { renderTracesView } from './pages/TracesView';
import { renderJobsView } from './pages/JobsView';
import { renderQualityOperationsView } from './pages/QualityOperationsView';
import { renderApprovalCenterView } from './pages/ApprovalCenterView';
import { renderSettingsView } from './pages/SettingsView';
import { renderWorkspaceDocumentsView } from './pages/WorkspaceDocumentsView';
import './styles.css';

const root = document.querySelector<HTMLElement>('#app');
if (!root) throw new Error('No se encontró el contenedor #app para DevPilot Web UI.');

interface UiRoute { path: string; routeId: string; title: string; }
const UI_ROUTES: UiRoute[] = [
  { path: '/', routeId: 'ui.dashboard', title: 'Dashboard' },
  { path: '/workspace/documents', routeId: 'ui.workspace-documents', title: 'Documentos' },
  { path: '/reports', routeId: 'ui.reports', title: 'Reportes' },
  { path: '/traces', routeId: 'ui.traces', title: 'Trazas' },
  { path: '/jobs', routeId: 'ui.jobs', title: 'Jobs' },
  { path: '/quality', routeId: 'ui.quality', title: 'Calidad / Tests' },
  { path: '/approvals', routeId: 'ui.approvals', title: 'Approval Center' },
  { path: '/settings', routeId: 'ui.settings', title: 'Configuración' },
];

renderApplication(root);

function renderApplication(target: HTMLElement): void {
  const currentPath = normalizePath(globalThis.location.pathname);
  const jobsDetail = currentPath.match(/^\/jobs\/(job_[A-Za-z0-9_-]+)$/);
  const route = UI_ROUTES.find((item) => item.path === currentPath) ?? (jobsDetail ? UI_ROUTES.find((item) => item.path === '/jobs') : undefined);
  target.replaceChildren();
  const shell = document.createElement('div');
  shell.className = 'app-shell';
  shell.append(renderPrimaryNavigation(currentPath));
  const page = document.createElement('div');
  page.className = 'route-page';
  page.dataset.routePath = currentPath;
  if (!route) page.append(renderNotFound(currentPath));
  else if (route.path === '/') renderDashboard(page);
  else {
    page.append(renderRouteHeader(route));
    if (route.path === '/workspace/documents') page.append(renderWorkspaceDocumentsView(() => readStoredToken()));
    else if (route.path === '/reports') page.append(renderReportsView(() => readStoredToken()));
    else if (route.path === '/traces') page.append(renderTracesView(() => readStoredToken()));
    else if (route.path === '/jobs') page.append(renderJobsView(() => readStoredToken(), jobsDetail?.[1]));
    else if (route.path === '/quality') page.append(renderQualityOperationsView(() => readStoredToken()));
    else if (route.path === '/approvals') page.append(renderApprovalCenterView(() => readStoredToken()));
    else if (route.path === '/settings') page.append(renderSettingsView(new DevPilotApiClient({ token: readStoredToken() }), () => readStoredToken()));
  }
  shell.append(page);
  target.append(shell);
}

function renderPrimaryNavigation(currentPath: string): HTMLElement {
  const nav = document.createElement('nav');
  nav.className = 'primary-nav';
  nav.setAttribute('aria-label', 'Navegación principal DevPilot');
  const brand = document.createElement('a');
  brand.href = '/';
  brand.className = 'primary-nav__brand';
  brand.textContent = 'DevPilot Local';
  const links = document.createElement('div');
  links.className = 'primary-nav__links';
  for (const route of UI_ROUTES) {
    const link = document.createElement('a');
    link.href = route.path;
    link.textContent = route.title;
    link.dataset.routeId = route.routeId;
    if (route.path === currentPath || (route.path === '/jobs' && currentPath.startsWith('/jobs/'))) {
      link.classList.add('is-active');
      link.setAttribute('aria-current', 'page');
    }
    links.append(link);
  }
  nav.append(brand, links);
  return nav;
}

function renderRouteHeader(route: UiRoute): HTMLElement {
  const header = document.createElement('header');
  header.className = 'route-header';
  const heading = document.createElement('div');
  const title = document.createElement('h1');
  title.textContent = route.title;
  const meta = document.createElement('p');
  meta.textContent = `${route.routeId} · ${route.path} · local-first · no-remote · token en sessionStorage.`;
  heading.append(title, meta);
  const form = document.createElement('form');
  form.className = 'token-form route-token-form';
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const input = form.querySelector<HTMLInputElement>('input[name="token"]');
    storeToken(input?.value ?? '');
    renderApplication(root as HTMLElement);
  });
  const label = document.createElement('label');
  label.textContent = 'Token local';
  const input = document.createElement('input');
  input.name = 'token';
  input.type = 'password';
  input.placeholder = 'Pega DEVPILOT_API_TOKEN';
  input.value = readStoredToken();
  input.autocomplete = 'off';
  const apply = document.createElement('button');
  apply.type = 'submit';
  apply.textContent = 'Aplicar token';
  const clear = document.createElement('button');
  clear.type = 'button';
  clear.className = 'button-secondary';
  clear.textContent = 'Limpiar token';
  clear.addEventListener('click', () => { storeToken(''); renderApplication(root as HTMLElement); });
  label.append(input);
  form.append(label, apply, clear);
  header.append(heading, form);
  return header;
}

function renderNotFound(path: string): HTMLElement {
  const section = document.createElement('section');
  section.className = 'panel route-not-found';
  const title = document.createElement('h1');
  title.textContent = 'Ruta UI no registrada';
  const description = document.createElement('p');
  description.textContent = `La ruta ${path} no pertenece al contrato crítico local. Usa la navegación principal.`;
  section.append(title, description);
  return section;
}

function normalizePath(path: string): string {
  if (!path || path === '/') return '/';
  const normalized = path.replace(/\/+$/, '');
  return normalized || '/';
}
