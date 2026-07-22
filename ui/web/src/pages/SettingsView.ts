import { DevPilotApiClient } from '../api/client';
import type { DevPilotApplicationResponse, SettingsSnapshot } from '../api/types';
import { renderProviderSettings } from '../components/ProviderSettings';
import { escapeHtml, safeJsonForHtml } from '../utils/sanitize';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { runBounded } from '../utils/async';

// Provider editor plan-only contract marker retained for compatibility.
type SettingsPhase = 'idle' | 'loading' | 'ready' | 'empty' | 'error';

interface SettingsState extends SettingsSnapshot {
  phase: SettingsPhase;
  errors: Record<string, string>;
  durations: Record<string, number>;
  pendingAction?: 'providerPlan';
}

function status(response?: DevPilotApplicationResponse, error?: string): string {
  if (error) return 'ERROR';
  if (!response) return 'PENDING';
  return response.ok ? 'PASS' : 'BLOCK';
}

export function renderSettingsView(client: DevPilotApiClient, token: () => string): HTMLElement {
  const root = document.createElement('section');
  root.className = 'panel settings-panel';
  root.dataset.devpilotUiContract = 'ui.settings';
  const state: SettingsState = { phase: 'idle', errors: {}, durations: {} };

  async function refresh(): Promise<void> {
    state.phase = 'loading';
    state.errors = {};
    draw();
    const fresh = new DevPilotApiClient({ token: token() });
    await runBounded<DevPilotApplicationResponse>([
      { key: 'workspace', run: () => fresh.settingsWorkspace() },
      { key: 'providers', run: () => fresh.settingsProviders() },
      { key: 'policy', run: () => fresh.settingsPolicy() },
      { key: 'securityPosture', run: () => fresh.securityPosture() },
    ], 2, (result) => {
      state.durations[result.key] = result.durationMs;
      if (result.value) {
        if (result.key === 'workspace') state.workspace = result.value;
        if (result.key === 'providers') state.providers = result.value;
        if (result.key === 'policy') state.policy = result.value;
        if (result.key === 'securityPosture') state.securityPosture = result.value;
      }
      if (result.error) state.errors[result.key] = result.error;
      draw();
    });
    const responses = [state.workspace, state.providers, state.policy, state.securityPosture].filter(Boolean);
    if (Object.keys(state.errors).length) state.phase = 'error';
    else if (!responses.length) state.phase = 'empty';
    else state.phase = 'ready';
    draw();
  }

  async function planProvider(): Promise<void> {
    if (state.pendingAction) return;
    state.pendingAction = 'providerPlan';
    delete state.errors.providerPlan;
    draw();
    const providerId = (root.querySelector<HTMLInputElement>('#settings-provider-id')?.value || 'ollama').trim();
    const enabled = root.querySelector<HTMLInputElement>('#settings-provider-enabled')?.checked ?? false;
    const model = root.querySelector<HTMLInputElement>('#settings-provider-model')?.value || '';
    const endpoint = root.querySelector<HTMLInputElement>('#settings-provider-endpoint')?.value || '';
    const changes: Record<string, unknown> = { enabled };
    if (model.trim()) changes.default_model = model.trim();
    if (endpoint.trim()) changes.endpoint = endpoint.trim();
    try {
      state.providerPlan = await new DevPilotApiClient({ token: token() }).planProviderChange({
        provider_id: providerId,
        changes,
        actor: 'ui-local',
        reason: 'Plan-only provider settings change from Settings UI.',
      });
      delete state.errors.providerPlan;
    } catch (error) {
      state.errors.providerPlan = error instanceof Error ? error.message : String(error);
      state.phase = 'error';
    } finally {
      state.pendingAction = undefined;
    }
    draw();
  }

  function draw(): void {
    root.replaceChildren();
    const heading = document.createElement('div');
    heading.className = 'section-heading-row';
    const intro = document.createElement('div');
    const title = document.createElement('h2');
    title.textContent = 'Configuración';
    const description = document.createElement('p');
    description.textContent = 'Configuración local en modo lectura y planificación. Los estados loading, empty, error y ready son mutuamente excluyentes.';
    intro.append(title, description, renderContractBadges('ui.settings', { warning: 'Plan-only; secretos redactados; no remote.' }));
    const refreshButton = document.createElement('button');
    refreshButton.textContent = state.phase === 'loading' ? 'Consultando…' : 'Actualizar configuración';
    refreshButton.disabled = state.phase === 'loading';
    refreshButton.addEventListener('click', () => void refresh());
    heading.append(intro, refreshButton);
    root.append(heading);
    root.append(renderPhaseNotice(state));

    const grid = document.createElement('div');
    grid.className = 'grid two-cols';
    grid.append(
      renderDataCard('Workspace', 'Project.yaml y rutas locales.', state.workspace, state.errors.workspace, state.durations.workspace),
      renderDataCard('Política', 'PolicyEngine, CostGuard y MIASI policy matrix.', state.policy, state.errors.policy, state.durations.policy),
      renderDataCard('Postura de seguridad', 'Token requerido, CORS local restrictivo y capacidades sensibles deshabilitadas.', state.securityPosture, state.errors.securityPosture, state.durations.securityPosture, true)
    );
    root.append(grid);

    const providerGrid = document.createElement('div');
    providerGrid.className = 'grid two-cols';
    const providers = document.createElement('article');
    providers.className = 'card';
    providers.innerHTML = `<span class="badge ${status(state.providers, state.errors.providers).toLowerCase()}">${status(state.providers, state.errors.providers)}</span><h3>Providers</h3><p>Listado seguro sin secretos ni activación externa accidental. ${durationLabel(state.durations.providers)}</p>${renderProviderSettings(state.providers)}<pre>${safeJsonForHtml(state.providers?.data?.summary ?? { detail: 'Sin providers cargados.' })}</pre>`;
    const editor = document.createElement('article');
    editor.className = 'card';
    editor.innerHTML = `
      <h3>Editor de provider — plan-only</h3>
      <p>Genera un plan. No escribe el archivo local de providers ni activa APIs externas.</p>
      <label>Provider id<input id="settings-provider-id" value="ollama" /></label>
      <label>Enabled plan<input id="settings-provider-enabled" type="checkbox" /></label>
      <label>Default model<input id="settings-provider-model" value="qwen2.5:3b-instruct" /></label>
      <label>Endpoint<input id="settings-provider-endpoint" value="http://localhost:11434" /></label>
      <button id="settings-plan-provider" aria-busy="${state.pendingAction === 'providerPlan'}" ${state.pendingAction ? 'disabled' : ''}>${state.pendingAction === 'providerPlan' ? 'Ejecutando…' : 'Generar plan sin escribir'}</button>
      <p class="action-status" role="status" aria-live="polite">${state.pendingAction === 'providerPlan' ? 'Generando plan local sin escribir configuración…' : 'Plan-only listo.'}</p>
      <pre>${safeJsonForHtml(state.providerPlan?.data ?? { detail: 'No se ha generado un plan.' })}</pre>
    `;
    editor.querySelector('#settings-plan-provider')?.addEventListener('click', () => void planProvider());
    providerGrid.append(providers, editor);
    root.append(providerGrid);
  }

  draw();
  if (client.token) void refresh();
  return root;
}

function renderPhaseNotice(state: SettingsState): HTMLElement {
  if (state.phase === 'loading') return renderUiStateNotice('loading', 'Consultando configuración local con máximo dos solicitudes simultáneas.');
  if (state.phase === 'empty') return renderUiStateNotice('empty', 'No se recibió configuración. Verifique el workspace activo y vuelva a intentar.');
  if (state.phase === 'error') {
    return renderUiStateNotice('error', `Configuración degradada: ${Object.entries(state.errors).map(([key, value]) => `${key}: ${value}`).join(' | ')}`);
  }
  if (state.phase === 'ready') return renderUiStateNotice('success', 'Configuración local cargada. Las capacidades sensibles permanecen gobernadas.');
  return renderUiStateNotice('empty', 'Aplique un token local y seleccione Actualizar configuración.');
}

function renderDataCard(
  title: string,
  description: string,
  response?: DevPilotApplicationResponse,
  error?: string,
  duration?: number,
  summaryOnly = false
): HTMLElement {
  const card = document.createElement('article');
  card.className = 'card';
  const badge = document.createElement('span');
  const currentStatus = status(response, error);
  badge.className = `badge ${currentStatus.toLowerCase()}`;
  badge.textContent = currentStatus;
  const heading = document.createElement('h3');
  heading.textContent = title;
  const context = document.createElement('p');
  context.textContent = `${description} ${durationLabel(duration)}`;
  const details = document.createElement('pre');
  details.textContent = error
    ? error
    : JSON.stringify(summaryOnly ? response?.data?.summary ?? {} : response?.data ?? {}, null, 2);
  card.append(badge, heading, context, details);
  return card;
}

function durationLabel(value?: number): string {
  return value === undefined ? 'Duración pendiente.' : `Última consulta: ${value} ms.`;
}
