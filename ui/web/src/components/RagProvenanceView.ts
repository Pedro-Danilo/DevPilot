// DevPilot UI contract: ui.settings
import { escapeHtml } from '../utils/sanitize';
import type { RagContextSettingsData } from '../api/types';

export function renderRagProvenanceView(data?: RagContextSettingsData): string {
  const pack = data?.context_pack ?? {};
  const summary = data?.summary ?? {};
  const candidates = Array.isArray(pack.candidate_sources) ? pack.candidate_sources : [];
  const selected = Array.isArray(pack.sources) ? pack.sources : [];
  const budget = pack.budget ?? {};
  const plan = budget.plan ?? {};
  const sourceRows = selected.map((source) => `
    <article class="list-item rag-source-row" data-rag-source="${escapeHtml(source.source_id)}">
      <strong>${escapeHtml(source.path)}</strong><br/>
      <small>${escapeHtml(source.citation_ref)} · trust ${escapeHtml(source.trust_tag)} · freshness ${escapeHtml(String(source.freshness?.status ?? 'unknown'))}</small><br/>
      <small>sha256 ${escapeHtml(source.content_sha256.slice(0, 16))}… · ${escapeHtml(String(source.estimated_tokens))} tokens · ${escapeHtml(source.selection_reason)}</small>
    </article>`).join('');
  return `
    <section class="card rag-provenance-view" data-rag-provenance-view="true">
      <div class="section-heading-row">
        <div><span class="badge pass">RAG PROVENANCE</span><h4>ContextPack v2 · selección grounded</h4></div>
        <div class="badge ${summary.status === 'grounded' ? 'pass' : 'warn'}">${escapeHtml(String(summary.status ?? 'UNKNOWN'))}</div>
      </div>
      <p>07-B prepara contexto local verificable; no ejecuta agentes ni APIs externas.</p>
      <div class="grid two-cols">
        <div class="list-item"><strong>Antes del presupuesto</strong><br/><small>${escapeHtml(String(summary.candidate_sources_total ?? candidates.length))} fuentes candidatas policy-filtered.</small></div>
        <div class="list-item"><strong>Pack sellado</strong><br/><small>${escapeHtml(String(summary.sources_total ?? selected.length))} fuentes · ${escapeHtml(String(summary.selected_tokens ?? 0))} tokens · strategy ${escapeHtml(String(summary.budget_strategy ?? plan.strategy ?? 'unknown'))}.</small></div>
      </div>
      <div class="list-item"><strong>Budget</strong><br/><small>top-k ${escapeHtml(String(summary.top_k ?? '?'))} · max input ${escapeHtml(String((budget.context_budget ?? {}).max_input_tokens ?? '?'))} · trimmed ${budget.trimmed ? 'YES' : 'NO'}.</small></div>
      <div class="rag-provenance-sources">${sourceRows || '<div class="list-item">insufficient evidence · no authoritative context selected.</div>'}</div>
      <div class="list-item"><strong>Frontera</strong><br/><small>hash parity ${summary.source_hash_parity === true ? 'PASS' : 'BLOCK'} · citation parity ${summary.citation_source_parity === true ? 'PASS' : 'BLOCK'} · network/API/embeddings: NO/NO/NO.</small></div>
    </section>`;
}
