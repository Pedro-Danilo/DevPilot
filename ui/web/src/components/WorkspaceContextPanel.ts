import type { DevPilotApplicationResponse } from '../api/types';
import { renderUiStateNotice } from './ContractBadges';

interface PortfolioWorkspace {
  workspace_id?: string;
  project_id?: string;
  name?: string;
  status?: string;
  active?: boolean;
  ready?: boolean;
  root_path?: string;
  readiness?: Record<string, unknown>;
  isolation?: Record<string, unknown>;
  risks?: Record<string, unknown>;
}

interface PortfolioData {
  summary?: Record<string, unknown>;
  workspaces?: PortfolioWorkspace[];
  ui_workspace_context?: Record<string, unknown>;
}

export function renderWorkspaceContextPanel(
  response?: DevPilotApplicationResponse,
  error?: string,
  durationMs?: number,
): HTMLElement {
  const panel = document.createElement('section');
  panel.className = 'workspace-context-panel';
  panel.dataset.devpilotUiContext = 'workspace';

  const heading = document.createElement('div');
  heading.className = 'workspace-context-panel__heading';
  const title = document.createElement('h3');
  title.textContent = 'Contexto operativo';
  const telemetry = document.createElement('span');
  telemetry.className = 'muted';
  telemetry.textContent = durationMs === undefined ? 'consulta pendiente' : `${durationMs} ms`;
  heading.append(title, telemetry);
  panel.append(heading);

  if (error) {
    panel.append(renderUiStateNotice('error', `No fue posible resolver el contexto de workspace: ${error}`));
    return panel;
  }
  if (!response) {
    panel.append(renderUiStateNotice('pending', 'Contexto de workspace pendiente de consulta.'));
    return panel;
  }

  const data = (response.data ?? {}) as PortfolioData;
  const summary = data.summary ?? {};
  const context = (data.ui_workspace_context ?? {}) as Record<string, unknown>;
  const workspaces = Array.isArray(data.workspaces) ? data.workspaces : [];
  const activeId = String(summary.active_workspace_id ?? context.active_workspace_id ?? '');
  const active = workspaces.find((item) => item.active || item.workspace_id === activeId)
    ?? (activeId ? {
      workspace_id: activeId,
      active: true,
      root_path: String(context.active_workspace_root ?? context.effective_workspace_root ?? ''),
      status: context.valid === false ? 'blocked' : 'configured',
    } : undefined);
  const mode = String(context.mode ?? 'platform');
  const configured = context.configured === true;
  const valid = context.valid !== false;

  const badges = document.createElement('div');
  badges.className = 'context-badges';
  badges.append(
    badge(configured && valid ? 'WORKSPACE CONFIGURADO' : 'PLATAFORMA', configured && valid ? 'pass' : 'pending'),
    badge('READ-ONLY', 'pass'),
    badge('LOCAL-FIRST', 'pass'),
    badge('NO-REMOTE', 'pass'),
  );
  panel.append(badges);

  const grid = document.createElement('div');
  grid.className = 'workspace-context-grid';
  grid.append(
    contextItem('Modo API/UI', mode),
    contextItem('Plataforma', compactPath(String(context.platform_root ?? 'no informado'))),
    contextItem('Workspace activo', active?.workspace_id ?? (activeId || 'no configurado')),
    contextItem('Root activo', compactPath(active?.root_path ?? String(context.active_workspace_root ?? context.effective_workspace_root ?? 'no informado'))),
    contextItem('Estado', active?.status ?? (configured ? 'desconocido' : 'platform-only')),
    contextItem('Readiness portfolio', active?.ready === true ? 'ready' : active?.ready === false ? 'not-ready' : 'no evaluado'),
  );
  panel.append(grid);

  if (configured && !valid) {
    panel.append(renderUiStateNotice('block', 'La configuración externa existe pero no pasó los controles de registry/PathGuard. La UI no debe asumir un workspace activo.'));
  } else if (!configured) {
    panel.append(renderUiStateNotice('pending', 'La API está operando en contexto de plataforma. Configure explícitamente el registry local para inspeccionar el proyecto piloto desde la UI.'));
  } else if (!activeId) {
    panel.append(renderUiStateNotice('pending', 'El registry configurado no expuso un workspace activo.'));
  }
  return panel;
}

function contextItem(label: string, value: string): HTMLElement {
  const item = document.createElement('div');
  item.className = 'workspace-context-item';
  const key = document.createElement('span');
  key.className = 'workspace-context-item__label';
  key.textContent = label;
  const rendered = document.createElement('code');
  rendered.textContent = value;
  item.append(key, rendered);
  return item;
}

function badge(text: string, state: string): HTMLElement {
  const item = document.createElement('span');
  item.className = `badge ${state}`;
  item.textContent = text;
  return item;
}

function compactPath(value: string): string {
  if (!value || value === 'no informado') return value || 'no informado';
  const normalized = value.replace(/\\/g, '/');
  const parts = normalized.split('/').filter(Boolean);
  if (parts.length <= 3) return value;
  return `…/${parts.slice(-3).join('/')}`;
}
