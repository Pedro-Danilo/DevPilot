import { renderUiStateNotice } from '../components/ContractBadges';

export const UOC011_BROWSER_RUNTIME_STATES = [
  'loading', 'empty', 'ready', 'warn', 'block', 'error', 'api_down', 'unauthorized',
  'forbidden', 'timeout', 'cancelled', 'stale_data',
] as const;
export type Uoc011BrowserRuntimeState = typeof UOC011_BROWSER_RUNTIME_STATES[number];

const KINDS: Record<Uoc011BrowserRuntimeState, 'loading' | 'pending' | 'empty' | 'error' | 'block' | 'success'> = {
  loading: 'loading', empty: 'empty', ready: 'success', warn: 'pending', block: 'block', error: 'error',
  api_down: 'error', unauthorized: 'block', forbidden: 'block', timeout: 'error', cancelled: 'pending', stale_data: 'block',
};
const LABELS: Record<Uoc011BrowserRuntimeState, string> = {
  loading: 'loading state', empty: 'empty state', ready: 'ready state', warn: 'warn state', block: 'BLOCK state',
  error: 'error state', api_down: 'API local down state', unauthorized: '401 unauthorized state',
  forbidden: '403 forbidden state', timeout: 'timeout state', cancelled: 'cancelled state', stale_data: 'stale data state',
};

/**
 * Presentation-only local browser fixture. It never calls the API or mutates source/runtime state.
 * It is unavailable in production builds and opt-in even in Vite dev mode. The final-closure
 * operator is the only supported caller and sets VITE_UOC011_BROWSER_MATRIX=1 for its own
 * localhost Vite process. Query parameters alone can never activate the fixture.
 */
export function renderUoc011BrowserStateFixture(routeId: string): HTMLElement | undefined {
  if (!import.meta.env.DEV || import.meta.env.VITE_UOC011_BROWSER_MATRIX !== '1') return undefined;
  const params = new URLSearchParams(globalThis.location.search);
  if (params.get('__uoc011_matrix') !== '1' || params.get('__uoc011_route') !== routeId) return undefined;
  const rawState = params.get('__uoc011_state');
  if (!rawState || !(UOC011_BROWSER_RUNTIME_STATES as readonly string[]).includes(rawState)) return undefined;
  const state = rawState as Uoc011BrowserRuntimeState;
  const section = document.createElement('section'); section.className = 'panel uoc011-browser-runtime-fixture';
  section.dataset.uoc011RuntimeRoute = routeId; section.dataset.uoc011RuntimeState = state; section.dataset.uoc011RuntimeEvidence = 'browser-runtime-controlled-fixture';
  section.setAttribute('aria-label', `UOC-011 runtime fixture ${routeId} ${state}`);
  const title = document.createElement('h2'); title.textContent = `UOC-011 browser runtime · ${routeId}`;
  const explanation = document.createElement('p'); explanation.textContent = 'Controlled presentation-only fixture. No API call, source mutation, remote execution or external provider is used.';
  const notice = renderUiStateNotice(KINDS[state], `${routeId} · ${LABELS[state]} · controlled browser runtime fixture.`); notice.dataset.uoc011ExpectedState = state;
  section.append(title, explanation, notice); return section;
}
