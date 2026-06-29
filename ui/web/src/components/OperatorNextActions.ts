// POST-H-015-D contract marker: ui.dashboard
import type { OperatorNextAction } from '../api/types';

export function renderOperatorNextActions(actions: OperatorNextAction[] = []): HTMLElement {
  const panel = document.createElement('section');
  panel.className = 'operator-next-actions';

  const title = document.createElement('h3');
  title.textContent = 'Next actions';

  const description = document.createElement('p');
  description.textContent = 'Solo se muestran comandos locales/dry-run recomendados por el snapshot.';

  const list = document.createElement('ol');
  list.className = 'operator-next-actions__list';

  for (const action of actions) {
    const item = document.createElement('li');
    const command = document.createElement('code');
    command.textContent = action.command;
    const reason = document.createElement('p');
    reason.textContent = `${action.priority ?? 'P?'} · ${action.reason}`;
    item.append(command, reason);
    list.append(item);
  }

  if (!actions.length) {
    const item = document.createElement('li');
    item.textContent = 'Sin acciones recomendadas por el snapshot actual.';
    list.append(item);
  }

  panel.append(title, description, list);
  return panel;
}
