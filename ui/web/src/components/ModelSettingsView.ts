// DevPilot UI contract: ui.settings
import type { DevPilotApplicationResponse, ModelGatewayRouteItem, ModelGatewaySettingsData } from '../api/types';
import { escapeHtml, safeJsonForHtml } from '../utils/sanitize';

export type ControlledEvalMode = 'mock' | 'fake-local' | 'fake-external';
export type ProviderActionPhase = 'idle' | 'loading' | 'pass' | 'block' | 'error';

export interface ProviderActionFeedback {
  providerId: string;
  action: 'disable' | 'revoke';
  phase: ProviderActionPhase;
  message: string;
}

export interface ModelSettingsUiState {
  evaluationMode: ControlledEvalMode;
  evaluationInputTokens: number;
  evaluationOutputTokens: number;
  evaluationHardStop: boolean;
  evaluationPending?: boolean;
  evaluationStatus?: string;
  providerAction?: ProviderActionFeedback;
}

function routesOf(response?: DevPilotApplicationResponse<ModelGatewaySettingsData>): ModelGatewayRouteItem[] {
  const routes = response?.data?.routes;
  return Array.isArray(routes) ? routes : [];
}

function dispositionClass(value: string): string {
  const normalized = value.toLowerCase();
  if (normalized === 'enabled') return 'pass';
  if (normalized === 'blocked' || normalized === 'unknown') return 'block';
  return 'warning';
}

function costLabel(route: ModelGatewayRouteItem): string {
  const state = route.estimated_cost?.cost_state ?? 'unknown';
  const value = route.estimated_cost?.cost_usd;
  if (value === null || value === undefined) return `${state}: unknown`;
  return `${state}: ${route.estimated_cost.currency ?? 'USD'} ${Number(value).toFixed(6)}`;
}

function runtimeCredentialLabel(route: ModelGatewayRouteItem): string {
  if (!route.external_api) return 'no aplica';
  if (route.runtime_credential_state === 'revoked' || route.runtime_revoked) return 'revocada en runtime';
  if (route.runtime_credential_reference_present) return 'referencia presente en runtime';
  return 'sin referencia runtime';
}

function providerActionHtml(route: ModelGatewayRouteItem, feedback?: ProviderActionFeedback): string {
  if (!route.external_api) return '';
  const applies = feedback?.providerId === route.provider_id;
  const phase = applies ? feedback?.phase ?? 'idle' : 'idle';
  const message = applies ? feedback?.message ?? '' : '';
  const loading = phase === 'loading';
  const badge = phase === 'pass' ? 'pass' : phase === 'block' || phase === 'error' ? 'block' : 'pending';
  return `
    <div class="provider-kill-switch" data-provider-id="${escapeHtml(route.provider_id)}">
      <p><strong>Runtime credential state:</strong> ${escapeHtml(runtimeCredentialLabel(route))} · <strong>Runtime network:</strong> ${route.runtime_network_enabled ? 'ENABLED' : 'disabled'} · <strong>Last runtime action:</strong> ${escapeHtml(route.runtime_last_action ?? 'none')}</p>
      <button data-provider-disable="${escapeHtml(route.provider_id)}" ${loading ? 'disabled' : ''}>Deshabilitar runtime</button>
      <button data-provider-revoke="${escapeHtml(route.provider_id)}" ${loading ? 'disabled' : ''}>Revocar referencia runtime</button>
      <p class="provider-action-feedback action-status" data-provider-action-feedback="${escapeHtml(route.provider_id)}" role="status" aria-live="polite"><span class="badge ${badge}">${escapeHtml(phase.toUpperCase())}</span> ${escapeHtml(message || 'Sin acción runtime en esta sesión.')}</p>
      <p class="muted">Deshabilitar apaga esta ruta dentro de DevPilot. Revocar elimina la referencia runtime de DevPilot; ninguna acción revoca una API key en el proveedor externo ni modifica variables de entorno del sistema operativo.</p>
    </div>`;
}

function renderEvaluationResult(evaluation?: DevPilotApplicationResponse): string {
  if (!evaluation) return '<p class="muted">Todavía no existe una evaluación en esta sesión.</p>';
  const summary = (evaluation.data?.summary ?? {}) as Record<string, unknown>;
  const decision = (evaluation.data?.decision ?? {}) as Record<string, unknown>;
  const hardStop = summary.hard_stop_demonstrated === true;
  const status = hardStop
    ? 'PASS · BLOCK esperado: el hard-stop impidió la ejecución antes de gastar tokens/costo.'
    : evaluation.ok
      ? 'PASS · evaluación hermética completada.'
      : `BLOCK · ${evaluation.message ?? 'La política bloqueó la ruta solicitada.'}`;
  return `
    <section class="controlled-eval-result" data-controlled-eval-result="true">
      <p class="action-status" role="status" aria-live="polite">${escapeHtml(status)}</p>
      <dl class="compact-definition-list">
        <dt>Modo solicitado</dt><dd>${escapeHtml(String(summary.mode ?? 'unknown'))}</dd>
        <dt>Ruta solicitada</dt><dd>${escapeHtml(String(summary.requested_access_route_id ?? 'auto/mock'))}</dd>
        <dt>Ruta seleccionada</dt><dd>${escapeHtml(String(summary.selected_access_route_id ?? 'ninguna'))}</dd>
        <dt>Routing status</dt><dd>${escapeHtml(String(summary.route_status ?? 'unknown'))}</dd>
        <dt>Fallback reason</dt><dd>${escapeHtml(String(summary.fallback_reason ?? decision.fallback_reason ?? 'sin fallback'))}</dd>
        <dt>Hard-stop reason</dt><dd>${escapeHtml(String(summary.hard_stop_reason ?? 'no aplica'))}</dd>
        <dt>Tokens estimados</dt><dd>${escapeHtml(String(summary.estimated_total_tokens ?? 'n/a'))} (input ${escapeHtml(String(summary.estimated_input_tokens ?? 'n/a'))} / output ${escapeHtml(String(summary.estimated_output_tokens ?? 'n/a'))})</dd>
        <dt>Request budget</dt><dd>${escapeHtml(String(summary.request_budget_max_tokens ?? 'n/a'))} tokens · ${escapeHtml(String(summary.request_budget_max_cost_usd ?? 'n/a'))} USD</dd>
        <dt>Network / external API</dt><dd>${summary.network_used ? 'USED' : 'no'} / ${summary.external_api_used ? 'USED' : 'no'}</dd>
        <dt>Tool authority</dt><dd>${summary.tool_authority_granted ? 'INVALID-GRANTED' : 'NO — permanece separada.'}</dd>
      </dl>
      <details><summary>Detalle técnico JSON</summary><pre>${safeJsonForHtml({ summary, decision })}</pre></details>
    </section>`;
}

export function renderModelSettingsView(
  response?: DevPilotApplicationResponse<ModelGatewaySettingsData>,
  evaluation?: DevPilotApplicationResponse,
  uiState: ModelSettingsUiState = {
    evaluationMode: 'mock',
    evaluationInputTokens: 900,
    evaluationOutputTokens: 200,
    evaluationHardStop: false,
  },
): string {
  const routes = routesOf(response);
  const summary = response?.data?.summary ?? {};
  const cards = routes.length
    ? routes.map((route) => `
      <article class="card model-route-card" data-access-route-id="${escapeHtml(route.access_route_id)}" data-route-disposition="${escapeHtml(route.disposition)}">
        <div class="section-heading-row">
          <div>
            <span class="badge ${dispositionClass(route.disposition)}">${escapeHtml(route.disposition.toUpperCase())}</span>
            <h4>${escapeHtml(route.provider_id)} / ${escapeHtml(route.model_id)}</h4>
          </div>
          <span class="badge ${route.external_api ? 'warning' : 'pass'}">${route.external_api ? 'EXTERNAL' : escapeHtml(route.locality.toUpperCase())}</span>
        </div>
        <dl class="compact-definition-list">
          <dt>Access route</dt><dd>${escapeHtml(route.access_route_id)}</dd>
          <dt>Enabled / health</dt><dd>${route.configured_enabled ? 'configured' : 'disabled'} · ${escapeHtml(route.health)}</dd>
          <dt>Privacy / data</dt><dd>${escapeHtml(route.privacy_data_class)}</dd>
          <dt>Region</dt><dd>${escapeHtml((route.target_region_display ?? []).join(', ') || 'n/a')}</dd>
          <dt>Auth adapter</dt><dd>${escapeHtml(route.auth_adapter_type)} · ${escapeHtml(route.auth_adapter_status)}</dd>
          <dt>Credential catalog metadata</dt><dd>${escapeHtml(route.credential_reference?.masked_display ?? 'no secret required')}</dd>
          <dt>Runtime credential state</dt><dd>${escapeHtml(runtimeCredentialLabel(route))}</dd>
          <dt>Freshness</dt><dd>${escapeHtml(route.evidence_freshness?.state ?? 'unknown')} · ${escapeHtml(route.evidence_freshness?.raw ?? '')}</dd>
          <dt>Cost preview</dt><dd>${escapeHtml(costLabel(route))} · ${route.estimated_tokens ?? 0} tokens</dd>
          <dt>Request budget</dt><dd>${route.request_budget?.max_tokens ?? 'n/a'} tokens · ${route.request_budget?.max_cost_usd ?? 'n/a'} USD</dd>
          <dt>Fallback</dt><dd>${escapeHtml(route.fallback_policy)}</dd>
        </dl>
        <p><strong>Capabilities:</strong> ${escapeHtml(Object.entries(route.capabilities ?? {}).filter(([, state]) => String(state).startsWith('supported')).map(([name]) => name).join(', ') || 'ninguna confirmada')}</p>
        <p class="authority-boundary"><strong>Tool authority:</strong> ${route.tool_execution_authority ? 'INVALID-GRANTED' : 'NO — ToolExecutionDecision permanece separado.'}</p>
        ${providerActionHtml(route, uiState.providerAction)}
      </article>`).join('')
    : '<article class="card"><span class="badge warning">EMPTY</span><p>No hay rutas de Model Gateway disponibles.</p></article>';

  const selected = (mode: ControlledEvalMode) => uiState.evaluationMode === mode ? 'selected' : '';
  return `
    <section class="model-settings-view" data-model-settings-view="true">
      <header class="card">
        <span class="badge pass">MODEL GATEWAY</span>
        <h3>Provider Settings y routing controlado</h3>
        <p>Las tarjetas se proyectan dinámicamente desde Model Capability Catalog + estado runtime; no son botones que habiliten modelos por sí mismos. Visibilidad de provider/model/access-route, costo, freshness y fallback. Blocked/unknown nunca se ocultan.</p>
        <pre>${safeJsonForHtml(summary)}</pre>
      </header>
      <article class="card controlled-model-eval">
        <h4>Evaluación controlada</h4>
        <p>Simulación hermética de routing: mock prueba la ruta segura; fake-local simula una ruta loopback registrada; fake-external simula gobernanza/fallback externo sin red real. No genera contenido LLM y la API real no es requisito.</p>
        <label>Modo
          <select id="model-gateway-eval-mode" ${uiState.evaluationPending ? 'disabled' : ''}>
            <option value="mock" ${selected('mock')}>mock</option>
            <option value="fake-local" ${selected('fake-local')}>fake-local</option>
            <option value="fake-external" ${selected('fake-external')}>fake-external</option>
          </select>
        </label>
        <label>Input tokens<input id="model-gateway-input-tokens" type="number" min="0" value="${Number(uiState.evaluationInputTokens)}" ${uiState.evaluationPending ? 'disabled' : ''} /></label>
        <label>Output tokens<input id="model-gateway-output-tokens" type="number" min="0" value="${Number(uiState.evaluationOutputTokens)}" ${uiState.evaluationPending ? 'disabled' : ''} /></label>
        <label><input id="model-gateway-hard-stop" type="checkbox" ${uiState.evaluationHardStop ? 'checked' : ''} ${uiState.evaluationPending ? 'disabled' : ''} /> Probar hard-stop de budget</label>
        <button id="model-gateway-evaluate" ${uiState.evaluationPending ? 'disabled' : ''}>${uiState.evaluationPending ? 'Evaluando…' : 'Ejecutar evaluación controlada'}</button>
        <p class="action-status" role="status" aria-live="polite">${escapeHtml(uiState.evaluationStatus ?? (evaluation ? evaluation.message ?? 'Evaluación completada.' : 'Sin evaluación en esta sesión.'))}</p>
        ${renderEvaluationResult(evaluation)}
      </article>
      <div class="grid two-cols model-route-grid">${cards}</div>
    </section>`;
}
