import { EXPERIENCE_MODE_AUTHORITY_CONTRACT, onExperienceModeChange, readExperienceMode, writeExperienceMode, type ExperienceMode } from '../ux/experienceMode';

function modeButton(mode: ExperienceMode, label: string): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'experience-mode-control__button';
  button.dataset.mode = mode;
  button.textContent = label;
  return button;
}

export function renderExperienceModeControl(): HTMLElement {
  const section = document.createElement('section');
  section.className = 'experience-mode-control';
  section.setAttribute('aria-label', 'Modo de experiencia');
  section.dataset.authorityImpact = 'none';
  section.dataset.browserStorageRole = EXPERIENCE_MODE_AUTHORITY_CONTRACT.browser_storage_role;

  const copy = document.createElement('div');
  copy.className = 'experience-mode-control__copy';
  const title = document.createElement('strong');
  title.textContent = 'Modo de experiencia';
  const note = document.createElement('span');
  note.textContent = 'Cambia la presentación, no permisos, approvals ni autoridad server-side.';
  copy.append(title, note);

  const group = document.createElement('div');
  group.className = 'experience-mode-control__group';
  group.setAttribute('role', 'group');
  group.setAttribute('aria-label', 'Seleccionar Guided o Expert');
  const guided = modeButton('guided', 'Guided');
  const expert = modeButton('expert', 'Expert');
  group.append(guided, expert);

  const status = document.createElement('span');
  status.className = 'experience-mode-control__status';
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  status.setAttribute('aria-atomic', 'true');

  const sync = (mode: ExperienceMode) => {
    guided.setAttribute('aria-pressed', String(mode === 'guided'));
    expert.setAttribute('aria-pressed', String(mode === 'expert'));
    guided.classList.toggle('is-active', mode === 'guided');
    expert.classList.toggle('is-active', mode === 'expert');
    status.textContent = mode === 'guided'
      ? 'Guided activo: foco en la siguiente acción y detalles progresivos.'
      : 'Expert activo: diagnósticos y trazas visibles; la autoridad no cambia.';
    document.querySelectorAll<HTMLDetailsElement>('details.primary-nav__advanced').forEach((details) => { details.open = mode === 'expert'; });
  };

  const activate = (mode: ExperienceMode, button: HTMLButtonElement) => {
    sync(writeExperienceMode(mode));
    button.focus();
  };
  guided.addEventListener('click', () => activate('guided', guided));
  expert.addEventListener('click', () => activate('expert', expert));
  onExperienceModeChange(sync);
  sync(readExperienceMode());

  section.append(copy, group, status);
  return section;
}
