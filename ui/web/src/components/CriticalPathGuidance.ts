export interface CriticalPathStep {
  label: string;
  state?: 'done' | 'current' | 'upcoming';
}

export interface CriticalPathGuidanceOptions {
  eyebrow: string;
  title: string;
  summary: string;
  steps: CriticalPathStep[];
  nextAction?: string;
  blocker?: string;
  approvalEffect?: string;
  recoveryHref?: string;
}

export function renderCriticalPathGuidance(options: CriticalPathGuidanceOptions): HTMLElement {
  const section = document.createElement('section');
  section.className = 'critical-path-guidance panel';
  section.dataset.uxP0C = 'critical-path-guidance';

  const header = document.createElement('div');
  header.className = 'critical-path-guidance__header';
  const eyebrow = document.createElement('p');
  eyebrow.className = 'critical-path-guidance__eyebrow';
  eyebrow.textContent = options.eyebrow;
  const title = document.createElement('h2');
  title.textContent = options.title;
  const summary = document.createElement('p');
  summary.className = 'critical-path-guidance__summary';
  summary.textContent = options.summary;
  header.append(eyebrow, title, summary);

  const steps = document.createElement('ol');
  steps.className = 'critical-path-guidance__steps';
  steps.setAttribute('aria-label', 'Progreso del recorrido');
  for (const [index, item] of options.steps.entries()) {
    const li = document.createElement('li');
    li.className = `critical-path-guidance__step critical-path-guidance__step--${item.state ?? 'upcoming'}`;
    li.dataset.stepState = item.state ?? 'upcoming';
    const number = document.createElement('span');
    number.className = 'critical-path-guidance__step-number';
    number.textContent = String(index + 1);
    const label = document.createElement('span');
    label.textContent = item.label;
    li.append(number, label);
    steps.append(li);
  }

  const decisions = document.createElement('div');
  decisions.className = 'critical-path-guidance__decisions';
  if (options.nextAction) decisions.append(guidanceFact('Siguiente acción', options.nextAction, 'next'));
  if (options.blocker) decisions.append(guidanceFact('Bloqueo', options.blocker, 'blocker'));
  if (options.approvalEffect) decisions.append(guidanceFact('Qué cambia al aprobar', options.approvalEffect, 'effect'));
  if (options.recoveryHref) {
    const link = document.createElement('a');
    link.className = 'button-secondary critical-path-guidance__recovery';
    link.href = options.recoveryHref;
    link.textContent = 'Retomar contexto seguro';
    decisions.append(link);
  }

  section.append(header, steps);
  if (decisions.childElementCount) section.append(decisions);
  return section;
}

export function renderTechnicalDisclosure(summaryText: string, bodyText: string): HTMLElement {
  const details = document.createElement('details');
  details.className = 'critical-path-technical-disclosure';
  const summary = document.createElement('summary');
  summary.textContent = summaryText;
  const body = document.createElement('p');
  body.textContent = bodyText;
  details.append(summary, body);
  return details;
}

function guidanceFact(labelText: string, valueText: string, kind: string): HTMLElement {
  const item = document.createElement('div');
  item.className = `critical-path-guidance__fact critical-path-guidance__fact--${kind}`;
  const label = document.createElement('span');
  label.className = 'critical-path-guidance__fact-label';
  label.textContent = labelText;
  const value = document.createElement('strong');
  value.textContent = valueText;
  item.append(label, value);
  return item;
}
