/** R02-02: readiness is informational; availability is not eligibility. */
export function renderLocalReadiness(data: any, busy: boolean, notice: string): HTMLElement {
  const section = document.createElement('section');
  section.className = 'card'; section.dataset.devpilotUiContract = 'ui.local-model-readiness';
  const heading = document.createElement('h3'); heading.textContent = 'Modelos locales · comprobación de disponibilidad';
  const description = document.createElement('p');
  description.textContent = 'SUPPORTED = adapter disponible; CONFIGURED = configuración local válida; HEALTHY = servicio respondió; EVALUATED = pruebas con dataset; ELIGIBLE = aprobado para una tarea. Un health-check no evalúa calidad.';
  section.append(heading, description);
  const host = document.createElement('p');
  const hw = data?.host;
  host.textContent = hw ? `Equipo observado: CPU lógicas ${hw.cpu_logical_count ?? 'N/D'} · RAM ${hw.ram_total_bytes == null ? 'N/D' : (hw.ram_total_bytes / (1024 ** 3)).toFixed(1) + ' GiB'} · GPU/VRAM: no medidos.` : 'Recursos locales todavía no consultados.';
  section.append(host);
  const providers: any[] = Array.isArray(data?.providers) ? data.providers : [];
  if (!providers.length) { const empty = document.createElement('p');empty.textContent = 'Sin datos de readiness.';section.append(empty); }
  for (const provider of providers) {
    const card = document.createElement('article'); card.className = 'settings-local-readiness-row';
    const name = document.createElement('strong');name.textContent = String(provider.provider_id || 'Proveedor local');
    const details = document.createElement('p');
    details.textContent = `SUPPORTED: ${provider.supported ? 'Sí' : 'No'} · CONFIGURED: ${provider.configured ? 'Sí' : 'No'} · HEALTHY: ${provider.healthy_state || 'NOT_TESTED'} · EVALUATED: ${provider.evaluated ? 'Sí' : 'NOT_TESTED'} · ELIGIBLE: ${provider.eligible ? 'Sí' : 'No'}`;
    const reason = document.createElement('p');reason.className = 'muted';reason.textContent = `Motivos: ${(provider.reasons || []).join(', ') || 'Sin observaciones'} · tareas: ${(provider.tasks || []).map((x: any) => x.task_type).join(', ')}`;
    card.append(name, details, reason);section.append(card);
  }
  const action = document.createElement('button');action.type = 'button';action.id='settings-probe-local-models';action.disabled=busy;
  action.textContent=busy?'Comprobando localhost…':'Comprobar proveedores locales (solo loopback)';
  const status=document.createElement('p');status.className='action-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.textContent=notice || 'No se hacen consultas de red al abrir Configuración. Esta comprobación no ejecuta modelos.';
  section.append(action,status);
  return section;
}
