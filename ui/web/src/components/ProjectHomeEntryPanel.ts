// DevPilot UI route contract: ui.dashboard
import type { AuthSessionContext } from '../api/types';
import { beginProjectEntryJourney, readProjectEntryResumeState, readProjectJourneyContext } from '../api/client';

interface EntryCard {
  mode: 'CREATE_NEW' | 'OPEN_EXISTING' | 'IMPORT_GIT';
  title: string;
  description: string;
  outcome: string;
}

const ENTRY_CARDS: EntryCard[] = [
  {
    mode: 'CREATE_NEW',
    title: 'Crear nuevo proyecto',
    description: 'Define el workspace, revisa el plan exacto y materializa Git/.venv/metadata solo después de approval.',
    outcome: 'Workspace nuevo, verificado y registrado.',
  },
  {
    mode: 'OPEN_EXISTING',
    title: 'Abrir proyecto existente',
    description: 'Inspecciona un Git worktree local, conserva su source y registra DevPilot mediante un plan revisable.',
    outcome: 'Proyecto existente incorporado sin reescribir su contenido.',
  },
  {
    mode: 'IMPORT_GIT',
    title: 'Importar repositorio Git',
    description: 'Importa un repositorio Git local. Remote Git permanece deshabilitado por defecto y nunca contacta red silenciosamente.',
    outcome: 'Copia local aislada con bootstrap y evidencia.',
  },
];

export function renderProjectHomeEntryPanel(session: AuthSessionContext): HTMLElement {
  const section = document.createElement('section');
  section.className = 'project-home';
  section.dataset.gsdlc03e = 'post-login-home';
  section.setAttribute('aria-labelledby', 'project-home-title');

  const header = document.createElement('div');
  header.className = 'project-home__header';
  const eyebrow = document.createElement('p');
  eyebrow.className = 'project-home__eyebrow';
  eyebrow.textContent = 'GSDLC-03-E · inicio de proyecto';
  const title = document.createElement('h1');
  title.id = 'project-home-title';
  title.textContent = '¿Qué quieres hacer?';
  const intro = document.createElement('p');
  intro.textContent = 'El journey normal ocurre íntegramente en el navegador: elige una opción, revisa el plan, solicita approval cuando corresponda y continúa al Estado del proyecto.';
  header.append(eyebrow, title, intro);

  const security = document.createElement('div');
  security.className = 'project-home__security';
  security.setAttribute('role', 'note');
  const isOwner = session.principal.roles.includes('owner');
  security.textContent = isOwner
    ? 'Sesión owner: dry-run, approval y ejecución gobernada disponibles. Local-first · sin shell · remote/network disabled-by-default.'
    : `Sesión ${session.principal.roles.join(', ') || 'sin rol'}: puedes revisar el journey permitido, pero la ejecución bootstrap requiere owner y permanece bloqueada server-side.`;

  const cards = document.createElement('div');
  cards.className = 'project-home__cards';
  for (const item of ENTRY_CARDS) {
    const link = document.createElement('a');
    link.className = 'project-home-card';
    link.href = `/project/entry?mode=${encodeURIComponent(item.mode)}`;
    link.dataset.entryMode = item.mode;
    link.setAttribute('aria-label', `${item.title}. ${item.description}`);
    link.addEventListener('click', () => beginProjectEntryJourney(item.mode));

    const mode = document.createElement('span');
    mode.className = 'project-home-card__mode';
    mode.textContent = item.mode.replace('_', ' ');
    const heading = document.createElement('h2');
    heading.textContent = item.title;
    const description = document.createElement('p');
    description.textContent = item.description;
    const outcome = document.createElement('p');
    outcome.className = 'project-home-card__outcome';
    outcome.textContent = item.outcome;
    const cta = document.createElement('strong');
    cta.textContent = 'Revisar opciones →';
    link.append(mode, heading, description, outcome, cta);
    cards.append(link);
  }

  const journeyContext = readProjectJourneyContext();
  const resumeState = journeyContext?.phase === 'entry' && journeyContext.entry_mode
    ? readProjectEntryResumeState(session, journeyContext.entry_mode)
    : null;
  const disclosure = document.createElement('div');
  disclosure.className = 'project-home__disclosure';
  disclosure.setAttribute('role', 'note');
  if (journeyContext?.phase === 'project') {
    disclosure.textContent = `Contexto de proyecto activo: ${journeyContext.project_id || 'proyecto local'}. Estado del proyecto y superficies operacionales están habilitados; usa una tarjeta para cambiar de contexto mediante un nuevo journey gobernado.`;
  } else if (journeyContext?.phase === 'entry') {
    disclosure.textContent = resumeState
      ? `Journey ${resumeState.entry_mode} en curso. El plan/preimage están conservados solo como estado UX de esta pestaña; DevPilot exigirá revalidación server-side antes de verify/execute.`
      : 'Journey de entrada en curso. Approval Center se habilita de forma contextual; las demás superficies de proyecto permanecen ocultas hasta que Create/Open/Import termine PASS.';
  } else {
    disclosure.textContent = 'Primero crea, abre o importa un proyecto. Estado del proyecto, Documentos, Reportes, Trazas, Jobs, Calidad/Tests e IA/RAG se habilitan después de completar el journey de entrada.';
  }

  const resume = document.createElement('div');
  resume.className = 'project-home__resume';
  if (resumeState) {
    const strong = document.createElement('strong');
    strong.textContent = `Journey recuperable · ${resumeState.entry_mode}`;
    const detail = document.createElement('span');
    detail.textContent = resumeState.approval_id
      ? `Approval ${resumeState.approval_id} registrado. Retome el journey y revalide antes de verificarlo.`
      : 'Plan/preimage disponibles. Retome el journey y revalide antes de continuar.';
    const link = document.createElement('a');
    link.href = `/project/entry?mode=${encodeURIComponent(resumeState.entry_mode)}&resume=1`;
    link.className = 'button-link';
    link.textContent = `Retomar ${resumeState.entry_mode} →`;
    link.dataset.resumeProjectEntry = 'true';
    resume.append(strong, detail, link);
  }

  const steps = document.createElement('ol');
  steps.className = 'project-home__steps';
  for (const text of ['Define parámetros', 'Revisa dry-run y preimage', 'Aprueba si hay mutación', 'Ejecuta y verifica', 'Continúa a Estado del proyecto']) {
    const li = document.createElement('li');
    li.textContent = text;
    steps.append(li);
  }

  section.append(header, security, disclosure);
  if (resumeState) section.append(resume);
  section.append(cards, steps);
  return section;
}
