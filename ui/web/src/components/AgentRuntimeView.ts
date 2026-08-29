// DevPilot UI contract: ui.settings
import { escapeHtml } from '../utils/sanitize';
import type { AgentRuntimeSettingsData } from '../api/types';

export function renderAgentRuntimeView(data?: AgentRuntimeSettingsData): string {
  const roles = Array.isArray(data?.roles) ? data?.roles ?? [] : [];
  const summary = data?.summary ?? {};
  const boundary = data?.runtime_boundary ?? {};
  const toolAuthority = (boundary.tool_authority ?? {}) as Record<string, unknown>;
  const cards = roles.map((role) => `
    <article class="list-item agent-runtime-role" data-agent-role="${escapeHtml(role.role_id)}">
      <strong>${escapeHtml(role.display_name)}</strong>
      <div class="badge ${role.enabled ? 'pass' : 'warn'}">${role.enabled ? 'BOUND' : 'DISABLED'}</div>
      <small>runtime: ${escapeHtml(role.runtime_agent_id)}</small><br/>
      <small>capabilities: ${escapeHtml((role.required_model_capabilities ?? []).join(', ') || 'none')}</small><br/>
      <small>limits: ${escapeHtml(String(role.limits?.max_steps ?? '?'))} steps · ${escapeHtml(String(role.limits?.wall_time_seconds ?? '?'))}s · ${escapeHtml(String(role.limits?.max_input_tokens ?? '?'))}/${escapeHtml(String(role.limits?.max_output_tokens ?? '?'))} tokens · $${escapeHtml(String(role.limits?.max_cost_usd ?? 0))}</small><br/>
      <small>policy: ${escapeHtml(role.policy_status)}</small>
    </article>`).join('');
  return `
    <section class="card agent-runtime-view" data-agent-runtime-view="true">
      <div class="section-heading-row">
        <div><span class="badge pass">AGENT RUNTIME</span><h4>Roles contextuales y límites</h4></div>
        <div class="badge ${summary.validation_status === 'PASS' ? 'pass' : 'warn'}">${escapeHtml(String(summary.validation_status ?? 'UNKNOWN'))}</div>
      </div>
      <p>07-A registra bindings y límites; no habilita ejecución autónoma ni aprobación humana.</p>
      <div class="grid two-cols">${cards || '<div class="list-item">Sin roles disponibles.</div>'}</div>
      <div class="list-item authority-boundary-note">
        <strong>Frontera de autoridad</strong><br/>
        <small>ToolIntent → ${escapeHtml(String(toolAuthority.execution_decision_contract ?? 'ToolExecutionDecision'))} por PolicyEngine/RBAC/Approval.</small><br/>
        <small>Model route grants tool permission: ${toolAuthority.model_route_can_grant_tool_permission === false ? 'NO' : 'BLOCK/UNKNOWN'} · Agent role can approve: ${toolAuthority.agent_role_can_approve === false ? 'NO' : 'BLOCK/UNKNOWN'}.</small>
      </div>
    </section>`;
}
