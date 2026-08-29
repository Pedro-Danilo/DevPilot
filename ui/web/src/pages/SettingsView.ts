import { renderUoc011BrowserStateFixture } from '../testing/Uoc011BrowserStateFixture';
import {
  DevPilotApiClient,
  DevPilotApiError,
  PROVIDER_PLAN_TIMEOUT_MS,
} from '../api/client';
import type { DevPilotApplicationResponse, SettingsSnapshot } from '../api/types';
import { renderProviderSettings } from '../components/ProviderSettings';
import { redactSecrets, safeJsonForHtml } from '../utils/sanitize';
import { renderContractBadges, renderUiStateNotice } from '../components/ContractBadges';
import { runBounded } from '../utils/async';
import { renderWorkspaceContextPanel } from '../components/WorkspaceContextPanel';
import { renderAIControlCenterShell } from '../components/AIControlCenterView';
import { renderModelSettingsView } from '../components/ModelSettingsView';
import { renderAgentRuntimeView } from '../components/AgentRuntimeView';
import { renderRagProvenanceView } from '../components/RagProvenanceView';
import type { ControlledEvalMode, ProviderActionFeedback } from '../components/ModelSettingsView';

// Provider editor plan-only contract marker retained for compatibility.
type SettingsPhase = 'idle' | 'loading' | 'ready' | 'empty' | 'error';
type ProviderPlanPhase = 'idle' | 'loading' | 'pass' | 'block' | 'timeout' | 'error';

interface SettingsState extends SettingsSnapshot {
  portfolio?: DevPilotApplicationResponse;
  phase: SettingsPhase;
  providerPlanPhase: ProviderPlanPhase;
  errors: Record<string, string>;
  durations: Record<string, number>;
  providerPlanEndpoint?: string;
  providerPlanDurationMs?: number;
  providerPlanTimeoutBudgetMs: number;
  pendingAction?: 'providerPlan' | 'modelEval' | 'providerDisable' | 'providerRevoke';
  modelActionStatus?: string;
  modelEvalMode: ControlledEvalMode;
  modelEvalInputTokens: number;
  modelEvalOutputTokens: number;
  modelEvalHardStop: boolean;
  providerAction?: ProviderActionFeedback;
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
  const uoc011Fixture = renderUoc011BrowserStateFixture('ui.settings');
  if (uoc011Fixture) return uoc011Fixture;
  const state: SettingsState = {
    phase: 'idle',
    providerPlanPhase: 'idle',
    errors: {},
    durations: {},
    providerPlanTimeoutBudgetMs: PROVIDER_PLAN_TIMEOUT_MS,
    modelEvalMode: 'mock',
    modelEvalInputTokens: 900,
    modelEvalOutputTokens: 200,
    modelEvalHardStop: false,
  };

  async function refresh(): Promise<void> {
    state.phase = 'loading';
    state.errors = Object.fromEntries(Object.entries(state.errors).filter(([key]) => key === 'providerPlan' || key === 'modelGatewayEval'));
    draw();
    const fresh = new DevPilotApiClient({ token: token() });
    await runBounded<DevPilotApplicationResponse<any>>([
      { key: 'workspace', run: () => fresh.settingsWorkspace() },
      { key: 'providers', run: () => fresh.settingsProviders() },
      { key: 'policy', run: () => fresh.settingsPolicy() },
      { key: 'securityPosture', run: () => fresh.securityPosture() },
      { key: 'modelGateway', run: () => fresh.settingsModelGateway() },
      { key: 'agentRuntime', run: () => fresh.settingsAgentRuntime() },
      { key: 'ragContext', run: () => fresh.settingsRagContext('requirements') },
      { key: 'portfolio', run: () => fresh.portfolioStatus() },
    ], 2, (result) => {
      state.durations[result.key] = result.durationMs;
      if (result.value) {
        if (result.key === 'workspace') state.workspace = result.value;
        if (result.key === 'providers') state.providers = result.value;
        if (result.key === 'policy') state.policy = result.value;
        if (result.key === 'securityPosture') state.securityPosture = result.value;
        if (result.key === 'modelGateway') state.modelGateway = result.value;
        if (result.key === 'agentRuntime') state.agentRuntime = result.value;
        if (result.key === 'ragContext') state.ragContext = result.value;
        if (result.key === 'portfolio') state.portfolio = result.value;
      }
      if (result.error) state.errors[result.key] = result.error;
      draw();
    });
    const responseKeys = ['workspace', 'providers', 'policy', 'securityPosture', 'modelGateway', 'agentRuntime', 'ragContext', 'portfolio'];
    const responses = [state.workspace, state.providers, state.policy, state.securityPosture, state.modelGateway, state.agentRuntime, state.ragContext, state.portfolio].filter(Boolean);
    if (responseKeys.some((key) => Boolean(state.errors[key]))) state.phase = 'error';
    else if (!responses.length) state.phase = 'empty';
    else state.phase = 'ready';
    draw();
  }

  async function planProvider(): Promise<void> {
    if (state.pendingAction) return;
    state.pendingAction = 'providerPlan';
    state.providerPlanPhase = 'loading';
    state.providerPlan = undefined;
    state.providerPlanDurationMs = undefined;
    state.providerPlanEndpoint = '/settings/providers/plan';
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
      const response = await new DevPilotApiClient({ token: token() }).planProviderChange({
        provider_id: providerId,
        changes,
        actor: 'ui-local',
        reason: 'Plan-only provider settings change from Settings UI.',
      });
      state.providerPlan = response;
      state.providerPlanPhase = response.ok ? 'pass' : 'block';
      state.providerPlanEndpoint = response.client_request?.endpoint ?? '/settings/providers/plan';
      state.providerPlanDurationMs = response.client_request?.duration_ms;
      state.providerPlanTimeoutBudgetMs = response.client_request?.timeout_budget_ms ?? PROVIDER_PLAN_TIMEOUT_MS;
    } catch (error) {
      if (error instanceof DevPilotApiError) {
        const payload = isApplicationResponse(error.payload) ? error.payload : undefined;
        state.providerPlan = payload;
        state.providerPlanDurationMs = error.durationMs;
        state.providerPlanEndpoint = error.endpoint || '/settings/providers/plan';
        state.providerPlanPhase = error.status === 408
          ? 'timeout'
          : error.status === 403 && payload
            ? 'block'
            : 'error';
        state.errors.providerPlan = error.message;
      } else {
        state.providerPlanPhase = 'error';
        state.errors.providerPlan = error instanceof Error ? error.message : String(error);
      }
    } finally {
      state.pendingAction = undefined;
    }
    draw();
  }

  async function evaluateModelGateway(): Promise<void> {
    if (state.pendingAction) return;
    const mode = (root.querySelector<HTMLSelectElement>('#model-gateway-eval-mode')?.value || state.modelEvalMode || 'mock') as ControlledEvalMode;
    const inputTokens = Number(root.querySelector<HTMLInputElement>('#model-gateway-input-tokens')?.value ?? state.modelEvalInputTokens);
    const outputTokens = Number(root.querySelector<HTMLInputElement>('#model-gateway-output-tokens')?.value ?? state.modelEvalOutputTokens);
    const hardStop = root.querySelector<HTMLInputElement>('#model-gateway-hard-stop')?.checked ?? state.modelEvalHardStop;
    state.modelEvalMode = mode;
    state.modelEvalInputTokens = Number.isFinite(inputTokens) ? inputTokens : 900;
    state.modelEvalOutputTokens = Number.isFinite(outputTokens) ? outputTokens : 200;
    state.modelEvalHardStop = hardStop;
    state.pendingAction = 'modelEval';
    delete state.errors.modelGatewayEval;
    state.modelActionStatus = `Evaluando ${mode}${hardStop ? ' con hard-stop intencional' : ''} sin red externa…`;
    draw();
    try {
      state.modelGatewayEval = await new DevPilotApiClient({ token: token() }).evaluateModelGateway({
        mode,
        workload_id: `settings-browser-${mode}`,
        estimated_input_tokens: state.modelEvalInputTokens,
        estimated_output_tokens: state.modelEvalOutputTokens,
        hard_stop_case: hardStop,
      });
      state.modelActionStatus = state.modelGatewayEval.ok
        ? `PASS · ${mode} completado; revise ruta solicitada/seleccionada y fallback en el resultado.`
        : `BLOCK · ${state.modelGatewayEval.message}`;
    } catch (error) {
      if (error instanceof DevPilotApiError) {
        const payload = isApplicationResponse(error.payload) ? error.payload : undefined;
        const summary = recordOf(payload?.data?.summary);
        const expectedHardStop = hardStop && error.status === 409 && summary.hard_stop_demonstrated === true;
        if (payload) state.modelGatewayEval = payload;
        if (expectedHardStop) {
          state.modelActionStatus = 'PASS · hard-stop demostrado: el BLOCK esperado ocurrió antes de cualquier ejecución/costo.';
          delete state.errors.modelGatewayEval;
        } else {
          state.errors.modelGatewayEval = error.message;
          state.modelActionStatus = `BLOCK · ${error.message}`;
        }
      } else {
        state.errors.modelGatewayEval = error instanceof Error ? error.message : String(error);
        state.modelActionStatus = `ERROR · ${state.errors.modelGatewayEval}`;
      }
    } finally {
      state.pendingAction = undefined;
    }
    draw();
  }

  async function providerKillSwitch(providerId: string, revoke: boolean): Promise<void> {
    if (state.pendingAction || !providerId) return;
    state.pendingAction = revoke ? 'providerRevoke' : 'providerDisable';
    state.providerAction = {
      providerId,
      action: revoke ? 'revoke' : 'disable',
      phase: 'loading',
      message: `${revoke ? 'Revocando referencia runtime' : 'Deshabilitando runtime'}…`,
    };
    state.modelActionStatus = `${revoke ? 'Revocando referencia runtime' : 'Deshabilitando runtime'} de ${providerId}…`;
    draw();
    try {
      const api = new DevPilotApiClient({ token: token() });
      const response = revoke
        ? await api.revokeExternalProvider(providerId)
        : await api.disableExternalProvider(providerId);
      const phase: ProviderActionFeedback['phase'] = response.ok ? 'pass' : 'block';
      const actionLabel = revoke ? 'referencia runtime revocada' : 'runtime deshabilitado';
      state.providerAction = { providerId, action: revoke ? 'revoke' : 'disable', phase, message: response.ok ? `${actionLabel}; estado actualizado y auditado.` : response.message };
      state.modelActionStatus = response.ok ? `PASS · ${providerId}: ${actionLabel}.` : `BLOCK · ${response.message}`;
      await refresh();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const phase: ProviderActionFeedback['phase'] = error instanceof DevPilotApiError && error.status === 403 ? 'block' : 'error';
      state.providerAction = { providerId, action: revoke ? 'revoke' : 'disable', phase, message };
      state.modelActionStatus = `${phase.toUpperCase()} · ${providerId}: ${message}`;
    } finally {
      state.pendingAction = undefined;
      draw();
    }
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
    root.append(renderWorkspaceContextPanel(state.portfolio, state.errors.portfolio, state.durations.portfolio));

    const grid = document.createElement('div');
    grid.className = 'grid two-cols';
    grid.append(
      renderDataCard('Workspace activo', 'Project.yaml y rutas locales del contexto UI configurado.', state.workspace, state.errors.workspace, state.durations.workspace),
      renderDataCard('Política de plataforma', 'PolicyEngine, CostGuard y MIASI policy matrix de DevPilot.', state.policy, state.errors.policy, state.durations.policy),
      renderDataCard('Postura de seguridad', 'Token requerido, CORS local restrictivo y capacidades sensibles deshabilitadas.', state.securityPosture, state.errors.securityPosture, state.durations.securityPosture, true)
    );
    root.append(grid);

    const providerGrid = document.createElement('div');
    providerGrid.className = 'grid two-cols';
    const providers = document.createElement('article');
    providers.className = 'card';
    providers.innerHTML = `<span class="badge ${status(state.providers, state.errors.providers).toLowerCase()}">${status(state.providers, state.errors.providers)}</span><h3>Providers de plataforma</h3><p>Listado seguro de DevPilot sin secretos ni activación externa accidental. ${durationLabel(state.durations.providers)}</p>${renderProviderSettings(state.providers)}<pre>${safeJsonForHtml(state.providers?.data?.summary ?? { detail: 'Sin providers cargados.' })}</pre>`;

    const loading = state.providerPlanPhase === 'loading';
    const editor = document.createElement('article');
    editor.className = 'card';
    editor.dataset.providerPlanPhase = state.providerPlanPhase;
    editor.innerHTML = `
      <span class="badge ${providerPlanBadge(state.providerPlanPhase)}">${state.providerPlanPhase.toUpperCase()}</span>
      <h3>Editor de provider — plan-only</h3>
      <p>Genera un plan. No escribe el archivo local de providers ni activa APIs externas.</p>
      <label>Provider id<input id="settings-provider-id" value="ollama" ${loading ? 'disabled' : ''} /></label>
      <label>Enabled plan<input id="settings-provider-enabled" type="checkbox" ${loading ? 'disabled' : ''} /></label>
      <label>Default model<input id="settings-provider-model" value="qwen2.5:3b-instruct" ${loading ? 'disabled' : ''} /></label>
      <label>Endpoint<input id="settings-provider-endpoint" value="http://localhost:11434" ${loading ? 'disabled' : ''} /></label>
      <button id="settings-plan-provider" aria-busy="${loading}" ${loading ? 'disabled' : ''}>${loading ? 'Ejecutando…' : providerPlanButtonLabel(state.providerPlanPhase)}</button>
      <p class="action-status" role="status" aria-live="polite">${providerPlanStatusLabel(state)}</p>
      <p class="muted">${providerPlanTelemetry(state)}</p>
      <pre>${safeJsonForHtml(state.providerPlan?.data ?? { detail: 'No existe un plan válido para esta sesión.' })}</pre>
    `;
    editor.querySelector('#settings-plan-provider')?.addEventListener('click', () => void planProvider());
    providerGrid.append(providers, editor);
    root.append(providerGrid);

    const aiControlCenter = document.createElement('section');
    aiControlCenter.innerHTML = renderAIControlCenterShell({
      modelGatewayHtml: renderModelSettingsView(state.modelGateway, state.modelGatewayEval, {
        evaluationMode: state.modelEvalMode,
        evaluationInputTokens: state.modelEvalInputTokens,
        evaluationOutputTokens: state.modelEvalOutputTokens,
        evaluationHardStop: state.modelEvalHardStop,
        evaluationPending: state.pendingAction === 'modelEval',
        evaluationStatus: state.modelActionStatus,
        providerAction: state.providerAction,
      }),
      agentRuntimeStatus: 'Autoridad separada; ejecución de agentes no se habilita desde Settings.',
      agentRuntimeHtml: renderAgentRuntimeView(state.agentRuntime?.data),
      ragProvenanceHtml: renderRagProvenanceView(state.ragContext?.data),
      skillsToolsStatus: 'Policy/RBAC independiente; ModelRouteDecision nunca concede ToolExecutionDecision.',
    });
    if (state.modelActionStatus) {
      const actionStatus = document.createElement('p');
      actionStatus.className = 'action-status';
      actionStatus.setAttribute('role', 'status');
      actionStatus.setAttribute('aria-live', 'polite');
      actionStatus.textContent = state.modelActionStatus;
      aiControlCenter.prepend(actionStatus);
    }
    aiControlCenter.querySelector('#model-gateway-evaluate')?.addEventListener('click', () => void evaluateModelGateway());
    aiControlCenter.querySelectorAll<HTMLElement>('[data-provider-disable]').forEach((button) => {
      button.addEventListener('click', () => void providerKillSwitch(button.dataset.providerDisable || '', false));
    });
    aiControlCenter.querySelectorAll<HTMLElement>('[data-provider-revoke]').forEach((button) => {
      button.addEventListener('click', () => void providerKillSwitch(button.dataset.providerRevoke || '', true));
    });
    root.append(aiControlCenter);
  }

  draw();
  if (client.token) void refresh();
  return root;
}

function providerPlanStatusLabel(state: SettingsState): string {
  if (state.providerPlanPhase === 'loading') return 'LOADING · generando plan local sin escribir configuración…';
  if (state.providerPlanPhase === 'pass') return 'PASS · plan-only generado con respuesta válida del API.';
  if (state.providerPlanPhase === 'block') return 'BLOCK · la propuesta fue rechazada por los safety gates.';
  if (state.providerPlanPhase === 'timeout') return 'TIMEOUT · no existe plan válido; revise la API local y reintente.';
  if (state.providerPlanPhase === 'error') return `ERROR · ${state.errors.providerPlan ?? 'fallo no clasificado'}`;
  return 'IDLE · plan no ejecutado.';
}

function providerPlanTelemetry(state: SettingsState): string {
  const duration = state.providerPlanDurationMs === undefined ? 'pendiente' : `${state.providerPlanDurationMs} ms`;
  return `Endpoint ${state.providerPlanEndpoint ?? '/settings/providers/plan'} · duración ${duration} · budget ${state.providerPlanTimeoutBudgetMs} ms.`;
}

function providerPlanButtonLabel(phase: ProviderPlanPhase): string {
  return phase === 'timeout' || phase === 'error' ? 'Reintentar plan sin escribir' : 'Generar plan sin escribir';
}

function providerPlanBadge(phase: ProviderPlanPhase): string {
  if (phase === 'pass') return 'pass';
  if (phase === 'block') return 'block';
  if (phase === 'timeout' || phase === 'error') return 'error';
  return 'pending';
}

function recordOf(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function isApplicationResponse(value: unknown): value is DevPilotApplicationResponse {
  return Boolean(value && typeof value === 'object' && (value as { contract?: unknown }).contract === 'DevPilotApplicationResponse');
}

function renderPhaseNotice(state: SettingsState): HTMLElement {
  if (state.phase === 'loading') return renderUiStateNotice('loading', 'Consultando configuración local con máximo dos solicitudes simultáneas.');
  if (state.phase === 'empty') return renderUiStateNotice('empty', 'No se recibió configuración. Verifique el workspace activo y vuelva a intentar.');
  if (state.phase === 'error') {
    const readErrors = Object.entries(state.errors).filter(([key]) => key !== 'providerPlan');
    return renderUiStateNotice('error', `Configuración degradada: ${readErrors.map(([key, value]) => `${key}: ${value}`).join(' | ')}`);
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
    : JSON.stringify(redactSecrets(summaryOnly ? response?.data?.summary ?? {} : response?.data ?? {}), null, 2);
  card.append(badge, heading, context, details);
  return card;
}

function durationLabel(value?: number): string {
  return value === undefined ? 'Duración pendiente.' : `Última consulta: ${value} ms.`;
}
