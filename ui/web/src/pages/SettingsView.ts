import { DevPilotApiClient } from '../api/client';
import type { DevPilotApplicationResponse, SettingsSnapshot } from '../api/types';
import { renderProviderSettings } from '../components/ProviderSettings';
import { escapeHtml, safeJsonForHtml } from '../utils/sanitize';

function pretty(value: unknown): string {
  return safeJsonForHtml(value);
}

function status(response?: DevPilotApplicationResponse): string {
  if (!response) return 'PENDING';
  return response.ok ? 'PASS' : 'BLOCK';
}

export function renderSettingsView(client: DevPilotApiClient, token: () => string): string {
  const state: SettingsSnapshot = {};
  const sectionId = 'settings-viewer';

  async function refresh(): Promise<void> {
    const fresh = new DevPilotApiClient({ token: token() });
    const [workspace, providers, policy, securityPosture] = await Promise.all([
      fresh.settingsWorkspace().catch((error) => error),
      fresh.settingsProviders().catch((error) => error),
      fresh.settingsPolicy().catch((error) => error),
      fresh.securityPosture().catch((error) => error),
    ]);
    if ('operation' in workspace) state.workspace = workspace;
    if ('operation' in providers) state.providers = providers;
    if ('operation' in policy) state.policy = policy;
    if ('operation' in securityPosture) state.securityPosture = securityPosture;
    draw();
  }

  async function planProvider(): Promise<void> {
    const providerId = escapeHtml((document.getElementById('settings-provider-id') as HTMLInputElement | null)?.value || 'ollama');
    const enabled = (document.getElementById('settings-provider-enabled') as HTMLInputElement | null)?.checked ?? false;
    const model = (document.getElementById('settings-provider-model') as HTMLInputElement | null)?.value || '';
    const endpoint = (document.getElementById('settings-provider-endpoint') as HTMLInputElement | null)?.value || '';
    const changes: Record<string, unknown> = { enabled };
    if (model.trim()) changes.default_model = model.trim();
    if (endpoint.trim()) changes.endpoint = endpoint.trim();
    const fresh = new DevPilotApiClient({ token: token() });
    state.providerPlan = await fresh.planProviderChange({
      provider_id: providerId,
      changes,
      actor: 'ui-local',
      reason: 'Plan-only provider settings change from Settings UI.',
    });
    draw();
  }

  function draw(): void {
    const root = document.getElementById(sectionId);
    if (!root) return;
    root.innerHTML = `
      <section class="panel settings-panel" data-devpilot-ui-contract="ui.settings">
        <div class="section-heading-row">
          <div>
            <h2>Settings UI</h2>
            <p>POST-H-014-C · ui.settings · local-first · plan-only/dry-run visible · no-remote · BLOCK/ERROR visibles · secretos redactados.</p>
            <div class="contract-badges" data-devpilot-ui-contract="ui.settings"><span class="contract-badge contract-badge--local-first">Local-first</span><span class="contract-badge contract-badge--dry-run">Plan-only/dry-run visible</span><span class="contract-badge contract-badge--no-remote">No remote</span><span class="contract-badge contract-badge--no-connector-write">No connector write</span><span class="contract-badge contract-badge--no-plugin-execution">No plugin execution</span></div>
            <p class="ui-state ui-state--loading" data-ui-state="loading">POST-H-014-C ui.settings loading state: consulta settings por API local.</p>
            <p class="ui-state ui-state--empty" data-ui-state="empty">POST-H-014-C ui.settings empty state: sin settings cargados todavía.</p>
            <p class="ui-state ui-state--error" data-ui-state="error">POST-H-014-C ui.settings error state: BLOCK/ERROR permanece visible.</p>
          </div>
          <button id="settings-refresh">Actualizar settings</button>
        </div>
        <div class="grid two-cols">
          <article class="card"><span class="badge ${status(state.workspace).toLowerCase()}">${status(state.workspace)}</span><h3>Workspace settings</h3><p>Project.yaml y rutas locales.</p><pre>${pretty(state.workspace?.data)}</pre></article>
          <article class="card"><span class="badge ${status(state.policy).toLowerCase()}">${status(state.policy)}</span><h3>Policy settings</h3><p>Política local, CostGuard y MIASI policy matrix.</p><pre>${pretty(state.policy?.data)}</pre></article>
          <article class="card"><span class="badge ${status(state.securityPosture).toLowerCase()}">${status(state.securityPosture)}</span><h3>Security posture</h3><p>POST-H-014-D · token requerido · CORS local restrictivo · secrets redacted · no remote bind.</p><pre>${pretty(state.securityPosture?.data?.summary)}</pre></article>
        </div>
        <div class="grid two-cols">
          <article class="card"><span class="badge ${status(state.providers).toLowerCase()}">${status(state.providers)}</span><h3>Providers</h3><p>Listado seguro sin secretos ni activación externa accidental.</p>${renderProviderSettings(state.providers)}<pre>${pretty(state.providers?.data?.summary)}</pre></article>
          <article class="card"><h3>Provider editor plan-only</h3><p>No escribe el archivo local de providers. Genera un plan y requiere aprobación futura para cambios reales.</p>
            <label>Provider id<input id="settings-provider-id" value="ollama" /></label>
            <label>Enabled plan<input id="settings-provider-enabled" type="checkbox" /></label>
            <label>Default model<input id="settings-provider-model" value="qwen2.5:3b-instruct" /></label>
            <label>Endpoint<input id="settings-provider-endpoint" value="http://localhost:11434" /></label>
            <button id="settings-plan-provider">Generar plan sin escribir</button>
            <pre>${pretty(state.providerPlan?.data ?? { detail: 'Sin plan generado.' })}</pre>
          </article>
        </div>
      </section>`;
    root.querySelector('#settings-refresh')?.addEventListener('click', () => refresh());
    root.querySelector('#settings-plan-provider')?.addEventListener('click', () => planProvider());
  }

  queueMicrotask(() => {
    draw();
    if (client.token) refresh().catch(() => draw());
  });
  return `<div id="${sectionId}"></div>`;
}
