export interface ContextualHelpOptions {
  title: string;
  plain: string;
  technical: string;
  nextAction: string;
  evidenceRef: string;
}

export function renderContextualHelp(options: ContextualHelpOptions): HTMLElement {
  const aside = document.createElement('aside');
  aside.className = 'contextual-help';
  aside.setAttribute('aria-label', `Ayuda contextual: ${options.title}`);
  const heading = document.createElement('h3');
  heading.textContent = options.title;
  const plain = document.createElement('p');
  plain.textContent = options.plain;
  const next = document.createElement('p');
  const strong = document.createElement('strong');
  strong.textContent = 'Siguiente acción segura: ';
  next.append(strong, document.createTextNode(options.nextAction));
  const details = document.createElement('details');
  details.className = 'contextual-help__technical';
  const summary = document.createElement('summary');
  summary.textContent = 'Ver detalle técnico';
  const technical = document.createElement('p');
  technical.textContent = options.technical;
  const evidence = document.createElement('p');
  evidence.className = 'contextual-help__evidence';
  evidence.textContent = `Evidence ref: ${options.evidenceRef}`;
  details.append(summary, technical, evidence);
  aside.append(heading, plain, next, details);
  return aside;
}

export function renderAccessibleError(options: {
  title: string;
  plain: string;
  status?: number;
  nextAction: string;
  evidenceRef: string;
}): HTMLElement {
  const article = document.createElement('article');
  article.className = 'panel accessible-error';
  article.setAttribute('role', 'alert');
  article.setAttribute('aria-live', 'assertive');
  article.setAttribute('aria-atomic', 'true');
  const heading = document.createElement('h3');
  heading.tabIndex = -1;
  heading.textContent = options.title;
  const plain = document.createElement('p');
  plain.textContent = options.plain;
  const next = document.createElement('p');
  next.textContent = `Qué hacer ahora: ${options.nextAction}`;
  const details = document.createElement('details');
  const summary = document.createElement('summary');
  summary.textContent = 'Detalle técnico seguro';
  const technical = document.createElement('p');
  technical.textContent = `Estado de transporte: ${typeof options.status === 'number' ? options.status : 'no disponible'}. Evidence ref: ${options.evidenceRef}. No se muestran tokens, payloads sensibles ni rutas locales.`;
  details.append(summary, technical);
  article.append(heading, plain, next, details);
  queueMicrotask(() => heading.focus());
  return article;
}
