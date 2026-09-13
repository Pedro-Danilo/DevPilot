import { renderContextualHelp } from '../components/ContextualHelp';

function glossaryTerm(term: string, meaning: string): HTMLElement {
  const row = document.createElement('div');
  row.className = 'help-glossary__term';
  const dt = document.createElement('dt');
  dt.textContent = term;
  const dd = document.createElement('dd');
  dd.textContent = meaning;
  row.append(dt, dd);
  return row;
}

export function renderHelpSystemView(): HTMLElement {
  const section = document.createElement('section');
  section.className = 'help-system-view';
  section.dataset.uiRouteId = 'ui.help';

  const intro = document.createElement('section');
  intro.className = 'panel help-system-hero';
  const title = document.createElement('h2');
  title.textContent = 'Ayuda y glosario';
  const copy = document.createElement('p');
  copy.textContent = 'Explicaciones operativas sin cambiar permisos ni autoridad. Guided simplifica la presentación; Expert añade diagnósticos, pero ambos obedecen las mismas políticas server-side.';
  intro.append(title, copy);

  const mode = renderContextualHelp({
    title: 'Guided y Expert',
    plain: 'Use Guided para avanzar con la siguiente acción visible y detalles progresivos. Use Expert cuando necesite IDs, hashes y trazas de autoridad.',
    technical: 'La preferencia de modo vive únicamente en almacenamiento browser de UX. No se envía como autorización y no modifica RBAC, approvals, tools, models ni mutability.',
    nextAction: 'Cambie de modo con el selector superior; si una operación está bloqueada, permanecerá bloqueada en ambos modos.',
    evidenceRef: 'ui.mode-policy-parity',
  });

  const recovery = renderContextualHelp({
    title: 'Recuperación y conflictos',
    plain: 'Recovery / Resume recupera contexto durable. Conflict Resolution explica drift de branch o archivos externos sin sobrescribir su trabajo.',
    technical: 'Los checkpoints y baselines son autoridad server-side o metadata local gobernada. El navegador no puede reusar approvals stale ni ejecutar Git destructivo automáticamente.',
    nextAction: 'Ante REVALIDATION_REQUIRED o MANUAL_RECONCILIATION_REQUIRED, revise causa, riesgo y next action antes de cualquier mutación.',
    evidenceRef: 'ui.recovery-reconciliation-help',
  });

  const errors = renderContextualHelp({
    title: 'Cómo leer un error',
    plain: 'Un error debe indicar qué ocurrió, qué impacto tiene y cuál es la siguiente acción segura.',
    technical: 'El detalle técnico de esta primera versión expone únicamente códigos/refs seguros. No muestra tokens, secretos, payloads sensibles ni paths locales.',
    nextAction: 'No fuerce una acción bloqueada; conserve la evidencia y use la ruta de recovery indicada.',
    evidenceRef: 'ui.error-explainability',
  });

  const glossary = document.createElement('section');
  glossary.className = 'panel help-glossary';
  const glossaryTitle = document.createElement('h3');
  glossaryTitle.textContent = 'Glosario';
  const dl = document.createElement('dl');
  dl.append(
    glossaryTerm('Authority', 'Fuente que DevPilot considera válida para decidir si una acción puede continuar.'),
    glossaryTerm('Dry-run', 'Plan o simulación que no ejecuta la mutación.'),
    glossaryTerm('Approval stale', 'Aprobación que ya no puede reutilizarse porque cambió su preimage o autoridad.'),
    glossaryTerm('Revalidation', 'Comprobación obligatoria después de un cambio de contexto, Git o sesión.'),
    glossaryTerm('Blocker', 'Condición que impide continuar de forma segura; Guided nunca debe ocultarla.'),
    glossaryTerm('Evidence ref', 'Identificador seguro para relacionar un mensaje con evidencia sin exponer secretos.'),
  );
  glossary.append(glossaryTitle, dl);

  const limits = document.createElement('section');
  limits.className = 'panel help-system-limits';
  const limitsTitle = document.createElement('h3');
  limitsTitle.textContent = 'Alcance de accesibilidad de esta versión';
  const limitsList = document.createElement('ul');
  for (const text of [
    'Incluye navegación por teclado, foco visible, skip link, landmarks, live regions, labels, foco de errores y responsive layout.',
    'Los checks automatizados son WCAG-oriented y contractuales; no sustituyen una auditoría completa con múltiples screen readers, contraste instrumental y dispositivos reales.',
    'La matriz browser completa y el hardening de performance/security pertenecen a 12-E y 12-D respectivamente.',
  ]) { const li = document.createElement('li'); li.textContent = text; limitsList.append(li); }
  limits.append(limitsTitle, limitsList);

  section.append(intro, mode, recovery, errors, glossary, limits);
  return section;
}
