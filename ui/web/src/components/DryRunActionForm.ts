// POST-H-014-C contract marker: ui.approvals
import { DevPilotApiClient } from '../api/client';
import type { DevPilotApplicationResponse } from '../api/types';

export function renderDryRunActionForm(tokenProvider: () => string, onResult: (response: DevPilotApplicationResponse | undefined, error?: string) => void): HTMLElement {
  const form = document.createElement('form');
  form.className = 'dry-run-form';

  const action = selectField('Acción dry-run', 'action_id', [
    ['readiness', 'Readiness'],
    ['code-review', 'Code review'],
    ['refactor-plan', 'Refactor plan'],
  ]);
  const target = inputField('Target', 'target', 'docs/01_requirements/use_cases.md');
  const goal = inputField('Goal', 'goal', 'Mejorar legibilidad sin ejecutar cambios');
  const button = document.createElement('button');
  button.type = 'submit';
  button.textContent = 'Ejecutar dry-run seguro';

  const note = document.createElement('p');
  note.className = 'muted';
  note.textContent = 'Solo acciones read-only/dry-run. La UI no habilita patch apply, refactor execute, rollback execute, git push ni deploy.';

  form.append(action.wrapper, target.wrapper, goal.wrapper, note, button);
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    button.disabled = true;
    try {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      const response = await client.runDryRunAction({
        action_id: action.input.value,
        target: target.input.value || '.',
        goal: goal.input.value || '',
        strict: true,
        include_code_review: true,
      });
      onResult(response);
    } catch (error) {
      onResult(undefined, error instanceof Error ? error.message : String(error));
    } finally {
      button.disabled = false;
    }
  });
  return form;
}

function inputField(labelText: string, name: string, value: string): { wrapper: HTMLElement; input: HTMLInputElement } {
  const wrapper = document.createElement('label');
  wrapper.textContent = labelText;
  const input = document.createElement('input');
  input.name = name;
  input.value = value;
  wrapper.append(input);
  return { wrapper, input };
}

function selectField(labelText: string, name: string, options: Array<[string, string]>): { wrapper: HTMLElement; input: HTMLSelectElement } {
  const wrapper = document.createElement('label');
  wrapper.textContent = labelText;
  const input = document.createElement('select');
  input.name = name;
  for (const [value, text] of options) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = text;
    input.append(option);
  }
  wrapper.append(input);
  return { wrapper, input };
}
