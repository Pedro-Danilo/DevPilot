// DevPilot UI contract: ui.settings
import { escapeHtml } from '../utils/sanitize';

export interface AIControlCenterShellOptions {
  modelGatewayHtml: string;
  agentRuntimeStatus?: string;
  agentRuntimeHtml?: string;
  ragProvenanceHtml?: string;
  agentEvalHtml?: string;
  skillsToolsHtml?: string;
  skillsToolsStatus?: string;
}

function renderSettingsSectionDisclosure(id: string, label: string, html: string | undefined, open = false): string {
  if (!html?.trim()) return '';
  return `<details class="progressive-evidence settings-section-disclosure" data-settings-section="${escapeHtml(id)}"${open ? ' open' : ''}>
    <summary>${escapeHtml(label)}</summary>
    <div class="settings-section-disclosure__body">${html}</div>
  </details>`;
}

export function renderAIControlCenterShell(options: AIControlCenterShellOptions): string {
  return `
    <section class="ai-control-center" data-ai-control-center="true">
      <header class="card">
        <span class="badge pass">AI CONTROL CENTER</span>
        <h3>Centro de control de IA</h3>
        <p>Administra Model Gateway sin mezclar la autoridad de Agent Runtime ni Skills/Tools.</p>
        <p class="mode-policy-parity-note" data-mode-policy-parity="server-authority-identical"><strong>Guided/Expert parity:</strong> el modo de experiencia cambia presentación y diagnósticos; nunca concede provider, model, tool, approval ni mutability adicionales.</p>
        <div class="grid three-cols authority-boundaries">
          <div class="list-item"><strong>Model Gateway</strong><br/><small>provider/model/access-route, costo, budget y fallback.</small></div>
          <div class="list-item"><strong>Agent Runtime</strong><br/><small>${escapeHtml(options.agentRuntimeStatus ?? 'Autoridad separada; no gestionada desde esta sub-vista.')}</small></div>
          <div class="list-item"><strong>Skills / Tools</strong><br/><small>${escapeHtml(options.skillsToolsStatus ?? 'Permisos separados; ModelRouteDecision no concede ToolExecutionDecision.')}</small></div>
        </div>
      </header>
      ${renderSettingsSectionDisclosure('agent-runtime', 'Agent Runtime', options.agentRuntimeHtml)}
      ${renderSettingsSectionDisclosure('grounding-rag', 'Grounding / RAG', options.ragProvenanceHtml)}
      ${renderSettingsSectionDisclosure('agent-evals', 'Evals / trazas', options.agentEvalHtml)}
      ${renderSettingsSectionDisclosure('skills-tools', 'Skills / Tools', options.skillsToolsHtml)}
      ${renderSettingsSectionDisclosure('model-gateway', 'Model Gateway · MP-0 foundation', options.modelGatewayHtml, true)}
    </section>`;
}
