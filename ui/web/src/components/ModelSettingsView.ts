// DevPilot UI contract: ui.settings
import type { DevPilotApplicationResponse, ModelGatewayRouteItem, ModelGatewaySettingsData, MultiproviderFoundationData, MultiproviderRouteChoice } from '../api/types';
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

function routeChoiceBadge(choice: MultiproviderRouteChoice): string {
  if (choice.execution_enabled) return 'pass';
  if (choice.status === 'blocked') return 'block';
  return 'warning';
}

function routeChoiceLabel(choice: MultiproviderRouteChoice): string {
  if (choice.execution_enabled) return 'EXECUTABLE';
  if (choice.status === 'blocked') return 'BLOCKED';
  return 'VISIBLE · NO EXECUTION';
}

function renderMultiproviderFoundation(foundation?: MultiproviderFoundationData): string {
  if (!foundation) {
    return `
      <article class="card multiprovider-foundation" data-multiprovider-foundation="missing">
        <span class="badge block">BLOCK</span>
        <h4>Multiprovider foundation</h4>
        <p>No existe una proyección Multiprovider autoritativa en la respuesta actual.</p>
      </article>`;
  }
  const choices = Array.isArray(foundation.route_choices) ? foundation.route_choices : [];
  const candidate = (foundation.candidate ?? {}) as Record<string, unknown>;
  const origin = (candidate.origin ?? {}) as Record<string, unknown>;
  const lineage = (candidate.lineage ?? {}) as Record<string, unknown>;
  const runtime = (foundation.runtime_provenance ?? {}) as Record<string, unknown>;
  const receipt = (foundation.execution_receipt ?? {}) as Record<string, unknown>;
  const grounding = (foundation.grounding ?? {}) as Record<string, unknown>;
  const guided = (foundation.guided_summary ?? {}) as Record<string, unknown>;
  const cards = choices.map((choice) => `
    <article class="card multiprovider-route-choice" data-provider-class="${escapeHtml(choice.provider_class)}" data-execution-enabled="${choice.execution_enabled ? 'true' : 'false'}">
      <div class="section-heading-row">
        <div>
          <span class="badge ${routeChoiceBadge(choice)}">${escapeHtml(routeChoiceLabel(choice))}</span>
          <h5>${escapeHtml(choice.provider_class)}</h5>
        </div>
        <span class="badge ${choice.network_classification.includes('external') ? 'warning' : 'pass'}">${escapeHtml(choice.network_classification)}</span>
      </div>
      <dl class="compact-definition-list">
        <dt>Requested → resolved</dt><dd>${escapeHtml(choice.requested_provider_class)} → ${escapeHtml(choice.resolved_provider_class ?? 'none')}</dd>
        <dt>Provider / model</dt><dd>${escapeHtml(choice.provider_id ?? 'none')} / ${escapeHtml(choice.model_id ?? 'n/a')}</dd>
        <dt>Status</dt><dd>${escapeHtml(choice.status)}</dd>
        <dt>Disabled reason</dt><dd>${escapeHtml(choice.disabled_reason ?? 'none')}</dd>
        <dt>Cost class</dt><dd>${escapeHtml(choice.cost_classification)}</dd>
        <dt>Fallback</dt><dd>${escapeHtml(String((choice.fallback ?? {}).reason ?? 'not-applied'))}</dd>
      </dl>
    </article>`).join('');
  return `
    <section class="multiprovider-foundation" data-multiprovider-foundation="ready">
      <article class="card">
        <div class="section-heading-row">
          <div>
            <span class="badge pass">MP-0E · FOUNDATION PREVIEW</span>
            <h4>Provider, candidate y provenance</h4>
          </div>
          <span class="badge warning">SIN INFERENCIA</span>
        </div>
        <p>${escapeHtml(String(guided.message ?? 'Vista de foundation sin model calls.'))}</p>
        <p class="muted"><strong>Clasificación:</strong> ${escapeHtml(foundation.fixture_classification)} · model call: ${foundation.model_call_performed ? 'YES' : 'NO'} · network: ${foundation.network_used ? 'USED' : 'no'} · external API: ${foundation.external_api_used ? 'USED' : 'no'}.</p>
        <p class="muted">Las rutas Local/External se muestran como opciones gobernadas, no como ejecuciones. Una ruta disabled no ofrece CTA de ejecución.</p>
      </article>
      <div class="grid three-cols multiprovider-route-choice-grid">${cards || '<article class="card"><span class="badge block">EMPTY</span><p>No hay route choices.</p></article>'}</div>
      <article class="card multiprovider-candidate-card" data-candidate-id="${escapeHtml(String(candidate.candidate_id ?? 'none'))}">
        <div class="section-heading-row">
          <div>
            <span class="badge warning">${escapeHtml(String(candidate.status ?? 'UNKNOWN'))}</span>
            <h5>Candidate determinístico de demostración contractual</h5>
          </div>
          <span class="badge pass">NO LLM</span>
        </div>
        <dl class="compact-definition-list">
          <dt>Candidate</dt><dd>${escapeHtml(String(candidate.candidate_id ?? 'n/a'))}</dd>
          <dt>Version</dt><dd>${escapeHtml(String(candidate.version ?? 'n/a'))}</dd>
          <dt>Artifact</dt><dd>${escapeHtml(String(candidate.artifact_type ?? 'n/a'))}</dd>
          <dt>Origin</dt><dd>${escapeHtml(String(origin.kind ?? 'n/a'))} · ${escapeHtml(String(origin.provider_class ?? 'n/a'))}</dd>
          <dt>Provider / model</dt><dd>${escapeHtml(String(origin.provider_id ?? 'n/a'))} / ${escapeHtml(String(origin.model_id ?? 'n/a'))}</dd>
          <dt>Lineage</dt><dd>${escapeHtml(String(lineage.reason ?? 'n/a'))} · root ${escapeHtml(String(lineage.root_candidate_id ?? 'n/a'))}</dd>
          <dt>Canonical input</dt><dd><code>${escapeHtml(String(candidate.canonical_input_sha256 ?? 'n/a'))}</code></dd>
          <dt>Content hash</dt><dd><code>${escapeHtml(String(candidate.content_sha256 ?? 'n/a'))}</code></dd>
        </dl>
      </article>
      <article class="card">
        <h5>Grounding ≠ Agentic RAG</h5>
        <p><strong>${escapeHtml(String(grounding.label ?? 'ContextPack grounding'))}:</strong> ${escapeHtml(String(grounding.context_reference ?? 'n/a'))}. Retrieval executed: ${grounding.retrieval_executed ? 'yes' : 'no'}.</p>
        <p class="muted">${escapeHtml(String(grounding.agentic_rag_note ?? 'Agentic RAG permanece separado.'))}</p>
      </article>
      <details class="card multiprovider-expert-details">
        <summary>Expert details · hashes, provenance y receipt</summary>
        <dl class="compact-definition-list">
          <dt>Route hash</dt><dd><code>${escapeHtml(String(runtime.route_sha256 ?? 'n/a'))}</code></dd>
          <dt>Provenance hash</dt><dd><code>${escapeHtml(String(runtime.provenance_sha256 ?? 'n/a'))}</code></dd>
          <dt>Receipt hash</dt><dd><code>${escapeHtml(String(receipt.receipt_sha256 ?? 'n/a'))}</code></dd>
          <dt>Profile</dt><dd>${escapeHtml(String(runtime.profile_version ?? 'n/a'))}</dd>
          <dt>Dependency profile</dt><dd>${escapeHtml(String(runtime.dependency_profile_version ?? 'n/a'))}</dd>
          <dt>Fallback visible</dt><dd>${escapeHtml(String(((runtime.fallback ?? {}) as Record<string, unknown>).reason ?? 'not-applied'))}</dd>
        </dl>
        <pre>${safeJsonForHtml({ runtime_provenance: runtime, execution_receipt: receipt, authority_boundary: foundation.authority_boundary })}</pre>
      </details>
    </section>`;
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
  const foundation = response?.data?.multiprovider_foundation;
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
        <p>Resumen Guided de disponibilidad y gobierno de generación. La configuración persistente, las acciones runtime y el diagnóstico conservan authority separada; esta vista no habilita providers por sí sola.</p>
        <p class="muted"><strong>Scope:</strong> instalación DevPilot · <strong>Persistencia:</strong> lectura/proyección · <strong>Authority:</strong> Model Gateway + policy · <strong>Efecto:</strong> ninguno al consultar.</p>
        <details><summary>Expert · Model Gateway summary JSON</summary><pre>${safeJsonForHtml(summary)}</pre></details>
      </header>
      ${renderMultiproviderFoundation(foundation)}
      <details class="card controlled-model-eval">
        <summary>Diagnóstico runtime · simulación de routing controlada</summary>
        <h4>Evaluación hermética sin inferencia</h4>
        <p>Simulación hermética de routing: mock prueba la ruta segura; fake-local simula una ruta loopback registrada; fake-external simula gobernanza/fallback externo sin red real. No genera contenido LLM y la API real no es requisito.</p>
        <label>Modo
          <select id="model-gateway-eval-mode" ${uiState.evaluationPending ? 'disabled' : ''}>
            <option value="mock" ${selected('mock')}>deterministic/mock</option>
            <option value="fake-local" ${selected('fake-local')}>local · simulado, sin daemon</option>
            <option value="fake-external" ${selected('fake-external')}>external · simulado, sin API</option>
          </select>
        </label>
        <label>Input tokens<input id="model-gateway-input-tokens" type="number" min="0" value="${Number(uiState.evaluationInputTokens)}" ${uiState.evaluationPending ? 'disabled' : ''} /></label>
        <label>Output tokens<input id="model-gateway-output-tokens" type="number" min="0" value="${Number(uiState.evaluationOutputTokens)}" ${uiState.evaluationPending ? 'disabled' : ''} /></label>
        <label><input id="model-gateway-hard-stop" type="checkbox" ${uiState.evaluationHardStop ? 'checked' : ''} ${uiState.evaluationPending ? 'disabled' : ''} /> Probar hard-stop de budget</label>
        <button id="model-gateway-evaluate" ${uiState.evaluationPending ? 'disabled' : ''}>${uiState.evaluationPending ? 'Evaluando…' : 'Ejecutar evaluación controlada'}</button>
        <p class="action-status" role="status" aria-live="polite">${escapeHtml(uiState.evaluationStatus ?? (evaluation ? evaluation.message ?? 'Evaluación completada.' : 'Sin evaluación en esta sesión.'))}</p>
        ${renderEvaluationResult(evaluation)}
      </details>
      <details class="card provider-runtime-catalog">
        <summary>Expert · Provider catalog y controles runtime</summary>
        <p class="muted"><strong>Scope:</strong> runtime/provider · <strong>Persistencia:</strong> depende de la acción · <strong>Authority:</strong> provider enablement governance. Blocked/unknown nunca se ocultan.</p>
        <div class="grid two-cols model-route-grid">${cards}</div>
      </details>
    </section>`;
}
