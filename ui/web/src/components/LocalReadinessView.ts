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

/** One-shot synthetic evaluation only; a candidate is never a FROZEN document. */
export function renderOllamaCandidatePanel(busy: boolean, notice: string, receipt: any): HTMLElement {
  const section=document.createElement('section');section.className='card';section.dataset.devpilotUiContract='ui.ollama-real-candidate';
  const title=document.createElement('h3');title.textContent='Laboratorio Ollama real · Product Definition';
  const intro=document.createElement('p');intro.textContent='Ensayo opcional con datos ficticios. Requiere Ollama iniciado y el modelo ya instalado. No activa proveedores, no escribe documentos del proyecto y no publica FROZEN.';
  const modelLabel=document.createElement('label');modelLabel.textContent='Modelo Ollama instalado (escríbelo exactamente)';
  const input=document.createElement('input');input.id='r0203-model';input.value='qwen2.5:3b-instruct';input.autocomplete='off';input.disabled=busy;modelLabel.append(input);
  const caseLabel=document.createElement('label');caseLabel.textContent='Caso sintético';
  const selection=document.createElement('select');selection.id='r0203-case';selection.disabled=busy;
  for(const [id,label] of [['vision','Vision'],['scope','MVP Scope'],['requirements','Requirements']]){ const option=document.createElement('option');option.value=id;option.textContent=label;selection.append(option); }
  caseLabel.append(selection);
  const button=document.createElement('button');button.id='r0203-run';button.type='button';button.disabled=busy;button.textContent=busy?'Esperando al modelo…':'Ejecutar un candidato real (solo localhost)';
  const status=document.createElement('p');status.id='r0203-result';status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.textContent=notice || 'IDLE · Sin inferencia. Cada clic ejecuta como máximo una solicitud si el modelo está instalado.';
  section.append(title,intro,modelLabel,caseLabel,button,status);
  if(receipt){ const summary=document.createElement('pre');summary.id='r0203-receipt';summary.textContent=JSON.stringify({status:receipt.status,stage:receipt.stage,model:receipt.model,candidate_id:receipt.candidate?.candidate_id,latency_ms:receipt.latency_ms,source_writes:receipt.source_writes,external_api_calls:receipt.external_api_calls,content_sha256:receipt.candidate_sha256},null,2);section.append(summary); const preview=document.createElement('pre');preview.id='r0203-content';preview.className='r0203-preview';preview.textContent=String(receipt.candidate?.payload?.content || 'Sin contenido acreditado'); section.append(preview); }
  return section;
}

export function renderLmstudioCandidatePanel(busy: boolean, notice: string, receipt: any): HTMLElement {
  const section=document.createElement('section');section.className='card';section.dataset.devpilotUiContract='ui.lmstudio-real-candidate';
  const title=document.createElement('h3');title.textContent='Laboratorio LM Studio real · Product Definition';
  const intro=document.createElement('p');intro.textContent='Ensayo opcional con datos ficticios. Requiere LM Studio iniciado y el modelo ya instalado. No activa proveedores, no escribe documentos del proyecto y no publica FROZEN.';
  const modelLabel=document.createElement('label');modelLabel.textContent='Modelo LM Studio cargado (escríbelo exactamente)';
  const input=document.createElement('input');input.id='r0204-model';input.value='';input.autocomplete='off';input.disabled=busy;modelLabel.append(input);
  const caseLabel=document.createElement('label');caseLabel.textContent='Caso sintético';
  const selection=document.createElement('select');selection.id='r0204-case';selection.disabled=busy;
  for(const [id,label] of [['vision','Vision'],['scope','MVP Scope'],['requirements','Requirements']]){ const option=document.createElement('option');option.value=id;option.textContent=label;selection.append(option); }
  caseLabel.append(selection);
  const button=document.createElement('button');button.id='r0204-run';button.type='button';button.disabled=busy;button.textContent=busy?'Esperando al modelo…':'Ejecutar un candidato real (solo localhost)';
  const status=document.createElement('p');status.id='r0204-result';status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.textContent=notice || 'IDLE · Sin inferencia. Cada clic ejecuta como máximo una solicitud si el modelo está instalado.';
  section.append(title,intro,modelLabel,caseLabel,button,status);
  if(receipt){ const summary=document.createElement('pre');summary.id='r0204-receipt';summary.textContent=JSON.stringify({status:receipt.status,stage:receipt.stage,model:receipt.model,candidate_id:receipt.candidate?.candidate_id,latency_ms:receipt.latency_ms,source_writes:receipt.source_writes,external_api_calls:receipt.external_api_calls,content_sha256:receipt.candidate_sha256},null,2);section.append(summary); const preview=document.createElement('pre');preview.id='r0204-content';preview.className='r0204-preview';preview.textContent=String(receipt.candidate?.payload?.content || 'Sin contenido acreditado'); section.append(preview); }
  return section;
}
