import { escapeHtml } from '../utils/sanitize';

function recordOf(value: unknown): Record<string, any> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, any> : {};
}

function rowsOf(value: unknown): Array<Record<string, any>> {
  return Array.isArray(value) ? value.filter((item) => item && typeof item === 'object') as Array<Record<string, any>> : [];
}

function badge(ok: boolean): string {
  return `<span class="badge ${ok ? 'pass' : 'block'}">${ok ? 'PASS' : 'BLOCK'}</span>`;
}

export function renderAgentEvalTraceView(data?: unknown): string {
  const payload = recordOf(data);
  const summary = recordOf(payload.summary);
  const traces = rowsOf(payload.traces);
  const rates = recordOf(summary.human_decision_rates_percent);
  const status = String(summary.status ?? 'PENDING');
  const ok = status.startsWith('PASS') && traces.length > 0;
  const traceCards = traces.map((trace) => {
    const sources = rowsOf(trace.sources);
    return `<article class="list-item agent-eval-trace" data-trace-id="${escapeHtml(String(trace.trace_id ?? 'unknown'))}">
      <strong>${escapeHtml(String(trace.step_id ?? 'step'))} · ${escapeHtml(String(trace.human_decision ?? 'PENDING'))}</strong><br/>
      <small>agent/runtime: ${escapeHtml(String(trace.agent_role ?? 'unknown'))} / ${escapeHtml(String(trace.runtime_agent ?? 'unknown'))}</small><br/>
      <small>provider/model/access-route: ${escapeHtml(String(trace.provider ?? 'unknown'))} / ${escapeHtml(String(trace.model ?? 'unknown'))} / ${escapeHtml(String(trace.access_route ?? 'unknown'))}</small><br/>
      <small>tokens: ${escapeHtml(String(trace.tokens_total ?? 0))} · cost known: ${trace.cost_known === true ? 'YES' : 'NO'} · cost USD: ${escapeHtml(String(trace.estimated_cost_usd ?? 0))}</small><br/>
      <small>sources: ${escapeHtml(sources.map((item) => `${item.path}@${String(item.sha256 ?? '').slice(0, 12)}`).join(' · ') || 'none')}</small><br/>
      <small>auto approval: ${trace.auto_approval === true ? 'YES' : 'NO'} · source write: ${trace.source_write === true ? 'YES' : 'NO'} · tool authority granted: ${trace.tool_authority_granted === true ? 'YES' : 'NO'}</small>
    </article>`;
  }).join('');
  return `<section class="card agent-eval-trace-view" data-agent-eval-trace-view="true">
    ${badge(ok)}
    <h3>Agent evals / traces</h3>
    <p><strong>GSDLC-07-E · ${escapeHtml(status)}</strong> · ${escapeHtml(String(summary.journey ?? 'Product Vision -> PRE_CODE_READY'))}</p>
    <div class="grid three-cols">
      <div class="list-item"><strong>Human decisions</strong><br/><small>ACCEPT ${escapeHtml(String(rates.ACCEPT ?? 0))}% · MODIFY ${escapeHtml(String(rates.MODIFY ?? 0))}% · REJECT ${escapeHtml(String(rates.REJECT ?? 0))}%</small></div>
      <div class="list-item"><strong>Execution authority</strong><br/><small>ToolIntent → PolicyEngine / RBAC / Approval → ToolExecutionDecision</small><br/><small>Model route grants tool permission: NO</small></div>
      <div class="list-item"><strong>Safety / next</strong><br/><small>forbidden tool: ${summary.forbidden_tool_containment === true ? 'PASS' : 'BLOCK'} · hard-stop: ${summary.hard_stop === true ? 'PASS' : 'BLOCK'} · bounded handoff: ${summary.bounded_handoff === true ? 'PASS' : 'BLOCK'}</small><br/><small>v2.2 next: ${summary.v2_2_next === true ? 'YES' : 'NO'} · v2.3 enabled: ${summary.v2_3_prepared_not_enabled === true ? 'NO (prepared)' : 'UNKNOWN'} · workers: ${escapeHtml(String(summary.parallel_workers ?? 0))}</small></div>
    </div>
    <p class="muted">Read-only sealed evidence. No model, tool, external API or source write is executed by this view.</p>
    <div class="list">${traceCards || '<p class="muted">No sealed traces available.</p>'}</div>
  </section>`;
}
