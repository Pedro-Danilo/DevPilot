import type { DevPilotApplicationResponse, ProviderSettingsItem } from '../api/types';

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
      const id = provider.provider_id ?? provider.id ?? 'unknown';
      const enabled = provider.enabled ? 'enabled' : 'disabled';
      const external = provider.external_api ? 'external-api' : 'local/mock';
      const keyEnv = provider.api_key_env ? ` · env=${provider.api_key_env}` : '';
      return `<div class="list-item"><strong>${id}</strong> · ${provider.kind ?? 'unknown'} · ${enabled} · ${external}${keyEnv}<br/><small>${provider.default_model ?? ''} ${provider.endpoint ?? ''}</small></div>`;
    })
    .join('');
}
