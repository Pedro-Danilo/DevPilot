export type NavigationGroupId = 'start' | 'understand-plan' | 'build-validate' | 'release' | 'recover' | 'ai' | 'diagnostics' | 'global';

export interface NavigationGroupDefinition {
  id: NavigationGroupId;
  label: string;
  guidedLabel: string;
  description: string;
  paths: readonly string[];
}

export interface NavigationRouteLike {
  path: string;
  routeId: string;
  title: string;
  scope: string;
}

export const NAVIGATION_GROUPS: readonly NavigationGroupDefinition[] = Object.freeze([
  { id: 'start', label: 'Start', guidedLabel: 'Inicio', description: 'Entrar, crear, abrir o retomar un proyecto.', paths: ['/', '/project/entry'] },
  { id: 'understand-plan', label: 'Understand & Plan', guidedLabel: 'Entender y planificar', description: 'Estado, ingeniería previa, documentos y planificación.', paths: ['/project/status', '/pre-code', '/workspace/documents', '/planning/roadmap'] },
  { id: 'build-validate', label: 'Build & Validate', guidedLabel: 'Construir y validar', description: 'Historias, aprobaciones, jobs y calidad.', paths: ['/story/code', '/approvals', '/jobs', '/quality'] },
  { id: 'release', label: 'Release', guidedLabel: 'Release', description: 'Readiness, package, lifecycle, metadata y cierre.', paths: ['/release/readiness', '/release/package', '/release/lifecycle', '/release/metadata', '/release/closure'] },
  { id: 'recover', label: 'Recover', guidedLabel: 'Recuperar', description: 'Reanudar trabajo y reconciliar cambios externos.', paths: ['/recovery', '/reconciliation'] },
  { id: 'ai', label: 'AI', guidedLabel: 'IA', description: 'Operaciones IA/RAG gobernadas.', paths: ['/ai'] },
  { id: 'diagnostics', label: 'Diagnostics', guidedLabel: 'Diagnóstico', description: 'Reportes y trazas disponibles bajo progressive disclosure.', paths: ['/reports', '/traces'] },
  { id: 'global', label: 'Global', guidedLabel: 'Global', description: 'Configuración, cuenta y ayuda.', paths: ['/settings', '/account', '/help'] },
]);

export function navigationGroupForPath(path: string): NavigationGroupDefinition | undefined {
  const normalized = path.startsWith('/jobs/') ? '/jobs' : path;
  return NAVIGATION_GROUPS.find((group) => group.paths.includes(normalized));
}

export function groupVisibleRoutes<T extends NavigationRouteLike>(routes: readonly T[], currentPath: string): Array<{ group: NavigationGroupDefinition; routes: T[]; active: boolean }> {
  return NAVIGATION_GROUPS.map((group) => {
    const grouped = routes.filter((route) => group.paths.includes(route.path));
    const activePath = currentPath.startsWith('/jobs/') ? '/jobs' : currentPath;
    return { group, routes: grouped, active: group.paths.includes(activePath) };
  }).filter((entry) => entry.routes.length > 0);
}

export interface BreadcrumbItem { label: string; href?: string; current?: boolean; }

export function breadcrumbItems(route: NavigationRouteLike, auxiliaryApprovalHandoff = false): BreadcrumbItem[] {
  if (auxiliaryApprovalHandoff) return [{ label: 'Decisión', current: false }, { label: route.title, current: true }];
  if (route.path === '/') return [{ label: 'Project Home', current: true }];
  const group = navigationGroupForPath(route.path);
  const items: BreadcrumbItem[] = [{ label: 'Project Home', href: '/' }];
  if (group && group.id !== 'start') items.push({ label: group.guidedLabel });
  items.push({ label: route.title, current: true });
  return items;
}

export function navigationPathFromServerTarget(target: string | null | undefined): string | null {
  const value = String(target ?? '').trim();
  const direct: Record<string, string> = {
    'project-status': '/project/status',
    'ui.dashboard': '/',
    'ui.project-status': '/project/status',
    'ui.pre-code-wizard': '/pre-code',
    'ui.planning-roadmap': '/planning/roadmap',
    'ui.workspace-documents': '/workspace/documents',
    'ui.story-code-workbench': '/story/code',
    'ui.approvals': '/approvals',
    'ui.jobs': '/jobs',
    'ui.quality': '/quality',
    'ui.release-readiness': '/release/readiness',
    'ui.release-package': '/release/package',
    'ui.release-lifecycle': '/release/lifecycle',
    'ui.release-metadata': '/release/metadata',
    'ui.release-closure': '/release/closure',
    'ui.recovery': '/recovery',
    'ui.reconciliation': '/reconciliation',
    'ui.ai': '/ai',
    'ui.reports': '/reports',
    'ui.traces': '/traces',
    'ui.settings': '/settings',
    'ui.account-role': '/account',
    'ui.help': '/help',
  };
  if (direct[value]) return direct[value];
  if (value.startsWith('/') && NAVIGATION_GROUPS.some((group) => group.paths.includes(value))) return value;
  return null;
}
