// DevPilot UI contract: ui.settings
import type { AgentExecutionSettingsData, DevPilotApplicationResponse } from '../api/types';
import { escapeHtml, safeJsonForHtml } from '../utils/sanitize';

export interface SkillToolPolicyViewState {
  sessionId?: string;
  actionStatus?: string;
  lastResult?: DevPilotApplicationResponse;
  pending?: boolean;
}

export function renderSkillToolPolicyView(data?: AgentExecutionSettingsData, state: SkillToolPolicyViewState = {}): string {
  const summary = data?.summary ?? {};
  const policy = data?.policy ?? {};
  const forbidden = Array.isArray(policy.global_forbidden_tools) ? policy.global_forbidden_tools : [];
  const sessions = Array.isArray(data?.sessions) ? data?.sessions : [];
  const session = state.sessionId ? sessions.find((row: any) => row?.session_id === state.sessionId) : sessions.at(-1);
  const disabled = state.pending ? 'disabled' : '';
  const sessionId = state.sessionId ?? (session as any)?.session_id ?? '';
  return `
    <section class="card skill-tool-policy-view" data-skill-tool-policy-view="true">
      <span class="badge pass">GSDLC-07-D · BOUNDED</span>
      <h3>Skills / Tools · Policy</h3>
      <p>El modelo propone <strong>ToolIntent</strong>; DevPilot emite <strong>ToolExecutionDecision</strong>. ModelRouteDecision nunca concede permiso de tool.</p>
      <div class="grid three-cols">
        <div class="list-item"><strong>Authority</strong><br/><small>${escapeHtml(String((summary as any).decision_authority ?? 'PolicyEngine,RBAC,Approval'))}</small></div>
        <div class="list-item"><strong>Dry-run first</strong><br/><small>${(summary as any).dry_run_first === true ? 'YES' : 'NO'}</small></div>
        <div class="list-item"><strong>Self approval</strong><br/><small>${(summary as any).agent_self_approval === false ? 'NO' : 'BLOCK'}</small></div>
      </div>
      <p><strong>filesystem.delete</strong>: ${forbidden.includes('filesystem.delete') ? 'FORBIDDEN · executable=false · tool_executed=false' : 'POLICY MISSING'}</p>
      <p>Real MCP execution: <strong>NOT ENABLED</strong> · Autonomous recovery: <strong>BLOCK PRODUCTION</strong> · arbitrary shell: <strong>NO</strong>.</p>
      <p>Tool scope inheritance on handoff: <strong>NO</strong> · human checkpoint: <strong>REQUIRED</strong>.</p>
      <div class="action-row">
        <button id="agent-exec-create" ${disabled}>Crear sesión demo</button>
        <button id="agent-exec-safe" ${disabled || !sessionId ? 'disabled' : ''}>policy.check · fake-local</button>
        <button id="agent-exec-delete" ${disabled || !sessionId ? 'disabled' : ''}>filesystem.delete · demostrar BLOCK</button>
        <button id="agent-exec-handoff" ${disabled || !sessionId ? 'disabled' : ''}>Handoff → Review</button>
        <button id="agent-exec-cancel" ${disabled || !sessionId ? 'disabled' : ''}>Cancel</button>
        <button id="agent-exec-kill" ${disabled || !sessionId ? 'disabled' : ''}>KILL</button>
      </div>
      <p class="action-status" role="status" aria-live="polite">${escapeHtml(state.actionStatus ?? 'IDLE · cree una sesión fake-local; no se ejecuta red ni source write.')}</p>
      <p class="muted">Session: ${escapeHtml(sessionId || 'none')} · límites server-side visibles en el snapshot.</p>
      <details><summary>Última ToolExecutionDecision / handoff / control</summary><pre>${safeJsonForHtml(state.lastResult?.data ?? { detail: 'Sin acción todavía.' })}</pre></details>
    </section>`;
}
