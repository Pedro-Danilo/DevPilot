import { DevPilotApiClient } from '../api/client';
import type { GuidedSdlcNextAction, GuidedSdlcProjectStatusResponseData, RecoveryStatusData } from '../api/types';
import { navigationPathFromServerTarget } from '../ux/navigationPresentation';

function text(value: unknown, fallback = 'No disponible'): string {
  if (value === null || value === undefined || value === '') return fallback;
  return String(value).slice(0, 256);
}

function addFact(host: HTMLElement, label: string, value: string, className = ''): void {
  const item = document.createElement('div'); item.className = `shell-project-context__fact ${className}`.trim();
  const dt = document.createElement('span'); dt.className = 'shell-project-context__label'; dt.textContent = label;
  const dd = document.createElement('strong'); dd.textContent = value;
  item.append(dt, dd); host.append(item);
}

function safeProjectStatus(data: GuidedSdlcProjectStatusResponseData | undefined): boolean {
  return Boolean(data
    && data.read_only === true
    && data.actor_neutral === true
    && data.network_used === false
    && data.external_api_used === false
    && data.mutations_performed === false
    && data.project_status);
}

function renderUnavailable(host: HTMLElement, reason: string): void {
  host.replaceChildren();
  host.dataset.authorityState = 'unavailable-fail-closed';
  const title = document.createElement('strong'); title.textContent = 'Contexto del proyecto no disponible';
  const copy = document.createElement('span'); copy.textContent = reason;
  const link = document.createElement('a'); link.href = '/project/status'; link.textContent = 'Abrir Estado del proyecto';
  host.append(title, copy, link);
}

function appendNextAction(host: HTMLElement, action: GuidedSdlcNextAction): void {
  const wrap = document.createElement('div'); wrap.className = 'shell-next-action'; wrap.dataset.serverAuthority = 'true';
  const eyebrow = document.createElement('span'); eyebrow.className = 'shell-next-action__label'; eyebrow.textContent = 'Siguiente acción';
  const copy = document.createElement('span'); copy.className = 'shell-next-action__copy'; copy.textContent = text(action.explanation, text(action.kind, 'Inspeccionar estado actual'));
  wrap.append(eyebrow, copy);
  const destination = navigationPathFromServerTarget(action.navigation_target);
  if (action.available === true && action.mutating !== true && destination) {
    const link = document.createElement('a'); link.className = 'shell-next-action__link'; link.href = destination; link.textContent = 'Ir';
    wrap.append(link);
  } else {
    const note = document.createElement('span'); note.className = 'shell-next-action__reason'; note.textContent = text(action.disabled_reason, text(action.reason_code, 'Revisa el estado antes de continuar.'));
    wrap.append(note);
  }
  host.append(wrap);
}

export function renderShellProjectContext(tokenProvider: () => string): HTMLElement {
  const section = document.createElement('section');
  section.className = 'shell-project-context';
  section.setAttribute('aria-label', 'Contexto persistente del proyecto');
  section.setAttribute('aria-live', 'polite');
  section.dataset.authority = 'server-side-guided-sdlc-status';
  section.dataset.browserStorageAuthority = 'false';
  const loading = document.createElement('span'); loading.textContent = 'Cargando contexto autoritativo del proyecto…';
  section.append(loading);

  void (async () => {
    const api = new DevPilotApiClient({ token: tokenProvider() });
    const [statusResult, recoveryResult] = await Promise.allSettled([api.projectStatus(), api.recoveryStatus()]);
    if (statusResult.status !== 'fulfilled' || statusResult.value.ok !== true || !safeProjectStatus(statusResult.value.data)) {
      renderUnavailable(section, 'DevPilot no inventa estado desde el navegador. Revisa Project Status o recovery.');
      return;
    }
    const data = statusResult.value.data!;
    const status = data.project_status ?? {};
    const recoveryData = recoveryResult.status === 'fulfilled' && recoveryResult.value.ok === true
      ? (recoveryResult.value.data as RecoveryStatusData | undefined)
      : undefined;
    const recovery = recoveryData?.recovery;
    const facts = document.createElement('div'); facts.className = 'shell-project-context__facts';
    addFact(facts, 'Proyecto', text(status.project_id));
    addFact(facts, 'Workspace', text(data.workspace_id ?? status.workspace_id));
    addFact(facts, 'Etapa', text(status.current_step ?? status.phase));
    addFact(facts, 'Estado', text(data.ui_state ?? status.lifecycle_status), `shell-project-context__state shell-project-context__state--${String(data.ui_state ?? 'unknown').toLowerCase()}`);
    const blockers = Array.isArray(status.blockers) ? status.blockers.length : 0;
    addFact(facts, 'Blockers', String(blockers), blockers ? 'shell-project-context__blockers' : '');
    addFact(facts, 'Revalidación', text(status.revalidation?.status, 'No requerida'));
    addFact(facts, 'Recovery', text(recovery?.state, 'Sin señal pendiente'));
    section.replaceChildren(facts);
    section.dataset.authorityState = 'server-validated';
    section.dataset.blockersTotal = String(blockers);
    appendNextAction(section, data.next_action ?? {});
    const expert = document.createElement('details'); expert.className = 'expert-only shell-project-context__diagnostics';
    const summary = document.createElement('summary'); summary.textContent = 'Authority diagnostics';
    const p = document.createElement('p'); p.textContent = `source=guided-sdlc/status · read_only=${String(data.read_only)} · actor_neutral=${String(data.actor_neutral)} · network_used=${String(data.network_used)} · external_api_used=${String(data.external_api_used)}`;
    expert.append(summary, p); section.append(expert);
  })();
  return section;
}
