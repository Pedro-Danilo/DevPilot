// POST-H-014-C contract marker: ui.settings
import type { DevPilotApplicationResponse, ProviderSettingsItem } from '../api/types';
import { escapeHtml } from '../utils/sanitize';

function asProviders(response?: DevPilotApplicationResponse): ProviderSettingsItem[] {
  const data = (response?.data ?? {}) as { providers?: ProviderSettingsItem[] };
  return Array.isArray(data.providers) ? data.providers : [];
}

export function renderProviderSettings(response?: DevPilotApplicationResponse): string {
  const providers = asProviders(response);
  if (providers.length === 0) {
    return '<p>No hay providers para mostrar.</p>';
  }
  return providers
    .map((provider) => {
      const id = escapeHtml(provider.provider_id ?? provider.id ?? 'unknown');
      const enabled = provider.enabled ? 'enabled' : 'disabled';
      const external = provider.external_api ? 'external-api' : 'local/mock';
      const kind = escapeHtml(provider.kind ?? 'unknown');
      const keyEnv = provider.api_key_env ? ` · env=${escapeHtml(provider.api_key_env)}` : '';
      const model = escapeHtml(provider.default_model ?? '');
      const endpoint = escapeHtml(provider.endpoint ?? '');
      return `<div class="list-item"><strong>${id}</strong> · ${kind} · ${enabled} · ${external}${keyEnv}<br/><small>${model} ${endpoint}</small></div>`;
    })
    .join('');
}
