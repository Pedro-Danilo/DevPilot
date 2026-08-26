import type { GuidedSdlcStepActionsResponseData, StepActionCard } from '../api/types';

export interface StepActionAdvisorRenderOptions {
  onAction?: (action: StepActionCard) => boolean;
}

// Registered as part of the existing Project Status successor surface.
const ROUTE_CONTRACT_ID = 'ui.project-status';

export function renderStepActionAdvisor(data: GuidedSdlcStepActionsResponseData, options: StepActionAdvisorRenderOptions = {}): HTMLElement {
  const section = document.createElement('section');
  section.className = 'step-action-advisor panel';
  section.dataset.routeContractId = ROUTE_CONTRACT_ID;
  section.dataset.status = String(data.advisor?.status ?? 'BLOCK');
  section.dataset.serverAuthoritative = data.server_authoritative === true ? 'true' : 'false';
  section.setAttribute('aria-labelledby', 'step-action-advisor-title');

  const header = document.createElement('div');
  header.className = 'step-action-advisor__header';
  const title = document.createElement('h3');
  title.id = 'step-action-advisor-title';
  title.textContent = 'Qué puedes hacer ahora';
  const subtitle = document.createElement('p');
  subtitle.textContent = `Paso actual: ${safe(data.current_step, 'no disponible')} · disponibilidad calculada por RBAC/policy del servidor.`;
  header.append(title, subtitle);

  const safety = document.createElement('p');
  safety.className = 'step-action-advisor__safety';
  safety.textContent = 'El Advisor no concede permisos. Una tarjeta solo describe una ruta; la API objetivo vuelve a aplicar autenticación, RBAC, policy y approval.';

  const list = document.createElement('div');
  list.className = 'step-action-advisor__list';
  list.setAttribute('role', 'list');
  const actions = Array.isArray(data.advisor?.actions) ? data.advisor?.actions ?? [] : [];
  for (const action of actions) list.append(renderStepActionCard(action, options));

  if (!actions.length) {
    const empty = document.createElement('div');
    empty.className = 'step-action-card step-action-card--unavailable';
    empty.textContent = 'BLOCK explícito: no existe una acción catalogada para el paso actual.';
    list.append(empty);
  }

  section.append(header, safety, list);
  return section;
}

export function renderStepActionAdvisorError(error: unknown): HTMLElement {
  const section = document.createElement('section');
  section.className = 'step-action-advisor panel step-action-advisor--error';
  section.dataset.status = 'ERROR';
  const title = document.createElement('h3');
  title.textContent = 'Qué puedes hacer ahora';
  const message = document.createElement('p');
  message.textContent = `Advisor no disponible: ${error instanceof Error ? error.message : 'error local no clasificado'}`;
  const note = document.createElement('p');
  note.textContent = 'Project Status sigue siendo read-only. No se habilita ninguna acción por fallback de UI.';
  section.append(title, message, note);
  return section;
}

function renderStepActionCard(action: StepActionCard, options: StepActionAdvisorRenderOptions): HTMLElement {
  const card = document.createElement('article');
  const available = action.availability === 'AVAILABLE' && action.executable === true;
  card.className = `step-action-card step-action-card--${available ? 'available' : 'unavailable'}`;
  card.dataset.actionId = action.action_id;
  card.dataset.actionKind = action.kind;
  card.dataset.availability = action.availability;
  card.dataset.recommended = action.recommended === true ? 'true' : 'false';
  card.setAttribute('role', 'listitem');

  const heading = document.createElement('div');
  heading.className = 'step-action-card__heading';
  const title = document.createElement('h4');
  title.textContent = action.label;
  const badges = document.createElement('div');
  badges.className = 'step-action-card__badges';
  badges.append(badge(action.kind));
  badges.append(badge(action.availability));
  if (action.recommended) badges.append(badge('RECOMENDADO'));
  heading.append(title, badges);

  const purpose = document.createElement('p');
  purpose.className = 'step-action-card__purpose';
  purpose.textContent = action.purpose;

  const facts = document.createElement('dl');
  facts.className = 'step-action-card__facts';
  addFact(facts, 'Riesgo', safe(action.risk?.level));
  addFact(facts, 'Approval', action.approval_required ? 'requerido' : 'no requerido en esta ruta');
  addFact(facts, 'Side effects', action.side_effects?.join(' · ') || 'none');
  addFact(facts, 'Costo', estimate(action.cost));
  addFact(facts, 'Tokens', estimate(action.tokens));
  addFact(facts, 'Rol(es)', action.required_roles?.length ? action.required_roles.join(', ') : 'no aplica');
  addFact(facts, 'Red / API externa', `${action.network_required ? 'red' : 'sin red'} / ${action.external_api_required ? 'API externa' : 'sin API externa'}`);

  const reasons = document.createElement('ul');
  reasons.className = 'step-action-card__reasons';
  if (!available) {
    for (const row of action.disabled_reasons ?? []) {
      const item = document.createElement('li');
      item.textContent = `${row.code}: ${row.message}`;
      reasons.append(item);
    }
    if (!reasons.childElementCount) {
      const item = document.createElement('li');
      item.textContent = 'UNAVAILABLE: la ruta no fue autorizada por el Advisor server-side.';
      reasons.append(item);
    }
  }

  const controls = document.createElement('div');
  controls.className = 'step-action-card__controls';
  const primary = document.createElement('button');
  primary.type = 'button';
  primary.textContent = action.recommended ? 'Usar opción recomendada' : 'Abrir opción';
  const target = typeof action.navigation_target === 'string' ? action.navigation_target : '';
  if (!available || (!target && !options.onAction)) {
    primary.disabled = true;
    primary.setAttribute('aria-disabled', 'true');
    primary.title = action.disabled_reasons?.map((row) => row.code).join(', ') || 'Ruta no ejecutable';
  } else {
    primary.addEventListener('click', () => {
      if (options.onAction?.(action) === true) return;
      if (target) globalThis.location.assign(target);
    });
  }
  controls.append(primary);

  if (!available && action.configuration_target) {
    const config = document.createElement('button');
    config.type = 'button';
    config.className = 'step-action-card__secondary';
    config.textContent = 'Ver configuración';
    config.addEventListener('click', () => globalThis.location.assign(String(action.configuration_target)));
    controls.append(config);
  }

  card.append(heading, purpose, facts);
  if (!available) card.append(reasons);
  card.append(controls);
  return card;
}

function badge(text: string): HTMLElement {
  const value = document.createElement('span');
  value.className = 'step-action-card__badge';
  value.textContent = text;
  return value;
}

function estimate(value: { applicable?: boolean; value?: number | null; unit?: string; reason?: string } | undefined): string {
  if (!value || value.applicable !== true) return `not applicable · ${safe(value?.reason)}`;
  return `${String(value.value ?? '?')} ${safe(value.unit)}`;
}

function addFact(list: HTMLDListElement, key: string, value: string): void {
  const dt = document.createElement('dt');
  dt.textContent = key;
  const dd = document.createElement('dd');
  dd.textContent = value;
  list.append(dt, dd);
}

function safe(value: unknown, fallback = 'not applicable'): string {
  const text = String(value ?? '').trim();
  return text || fallback;
}
