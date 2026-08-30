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

export function renderAIControlCenterShell(options: AIControlCenterShellOptions): string {
  return `
    <section class="ai-control-center" data-ai-control-center="true">
      <header class="card">
        <span class="badge pass">AI CONTROL CENTER</span>
        <h3>Centro de control de IA</h3>
        <p>Administra Model Gateway sin mezclar la autoridad de Agent Runtime ni Skills/Tools.</p>
        <div class="grid three-cols authority-boundaries">
          <div class="list-item"><strong>Model Gateway</strong><br/><small>provider/model/access-route, costo, budget y fallback.</small></div>
          <div class="list-item"><strong>Agent Runtime</strong><br/><small>${escapeHtml(options.agentRuntimeStatus ?? 'Autoridad separada; no gestionada desde esta sub-vista.')}</small></div>
          <div class="list-item"><strong>Skills / Tools</strong><br/><small>${escapeHtml(options.skillsToolsStatus ?? 'Permisos separados; ModelRouteDecision no concede ToolExecutionDecision.')}</small></div>
        </div>
      </header>
      ${options.agentRuntimeHtml ?? ""}
      ${options.ragProvenanceHtml ?? ""}
      ${options.agentEvalHtml ?? ""}
      ${options.skillsToolsHtml ?? ""}
      ${options.modelGatewayHtml}
    </section>`;
}
