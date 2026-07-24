// POST-H-014-C contract marker: ui.approvals
import {
  ACTION_DRY_RUN_TIMEOUT_MS,
  DevPilotApiClient,
  DevPilotApiError,
} from '../api/client';
import type { DevPilotApplicationResponse } from '../api/types';

export type DryRunPhase = 'idle' | 'loading' | 'pass' | 'block' | 'timeout' | 'error';

export interface DryRunUiOutcome {
  phase: DryRunPhase;
  response?: DevPilotApplicationResponse;
  error?: string;
  endpoint: string;
  durationMs?: number;
  timeoutBudgetMs: number;
}

export function renderDryRunActionForm(
  tokenProvider: () => string,
  onResult: (outcome: DryRunUiOutcome) => void,
  current: DryRunUiOutcome = idleOutcome(),
): HTMLElement {
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
  button.textContent = current.phase === 'timeout' || current.phase === 'error'
    ? 'Reintentar dry-run seguro'
    : 'Ejecutar dry-run seguro';

  const status = document.createElement('p');
  status.className = 'action-status';
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  status.dataset.phase = current.phase;
  status.textContent = outcomeLabel(current);

  const telemetry = document.createElement('p');
  telemetry.className = 'muted';
  telemetry.textContent = telemetryLabel(current);

  const note = document.createElement('p');
  note.className = 'muted';
  note.dataset.contract = 'critical_actions_blocked';
  note.textContent = 'Solo acciones read-only/dry-run. La UI no habilita patch apply, refactor execute, rollback execute, git push ni deploy. POST-H-028-D: acción prohibida => BLOCK visible, nunca éxito silencioso.';

  form.append(action.wrapper, target.wrapper, goal.wrapper, note, button, status, telemetry);
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    setLoading(true);
    status.dataset.phase = 'loading';
    status.textContent = 'Ejecutando dry-run local seguro…';
    telemetry.textContent = `Endpoint /actions/dry-run · budget ${ACTION_DRY_RUN_TIMEOUT_MS} ms · duración pendiente.`;
    try {
      const client = new DevPilotApiClient({ token: tokenProvider() });
      const response = await client.runDryRunAction({
        action_id: action.input.value,
        target: target.input.value || '.',
        goal: goal.input.value || '',
        strict: true,
        include_code_review: true,
      });
      const request = response.client_request;
      onResult({
        phase: response.ok ? 'pass' : 'block',
        response,
        endpoint: request?.endpoint ?? '/actions/dry-run',
        durationMs: request?.duration_ms,
        timeoutBudgetMs: request?.timeout_budget_ms ?? ACTION_DRY_RUN_TIMEOUT_MS,
      });
    } catch (error) {
      if (error instanceof DevPilotApiError) {
        const payload = isApplicationResponse(error.payload) ? error.payload : undefined;
        const phase: DryRunPhase = error.status === 408
          ? 'timeout'
          : error.status === 403 && payload
            ? 'block'
            : 'error';
        onResult({
          phase,
          response: payload,
          error: error.message,
          endpoint: error.endpoint || '/actions/dry-run',
          durationMs: error.durationMs,
          timeoutBudgetMs: ACTION_DRY_RUN_TIMEOUT_MS,
        });
      } else {
        onResult({
          phase: 'error',
          error: error instanceof Error ? error.message : String(error),
          endpoint: '/actions/dry-run',
          timeoutBudgetMs: ACTION_DRY_RUN_TIMEOUT_MS,
        });
      }
    } finally {
      setLoading(false);
    }
  });
  return form;

  function setLoading(loading: boolean): void {
    button.disabled = loading;
    action.input.disabled = loading;
    target.input.disabled = loading;
    goal.input.disabled = loading;
    button.textContent = loading ? 'Ejecutando…' : 'Ejecutar dry-run seguro';
    button.setAttribute('aria-busy', String(loading));
  }
}

export function idleOutcome(): DryRunUiOutcome {
  return {
    phase: 'idle',
    endpoint: '/actions/dry-run',
    timeoutBudgetMs: ACTION_DRY_RUN_TIMEOUT_MS,
  };
}

function outcomeLabel(outcome: DryRunUiOutcome): string {
  if (outcome.phase === 'loading') return 'Ejecutando dry-run local seguro…';
  if (outcome.phase === 'pass') return 'PASS · dry-run completado con respuesta válida del API.';
  if (outcome.phase === 'block') return 'BLOCK · la política o el contrato rechazó la operación.';
  if (outcome.phase === 'timeout') return 'TIMEOUT · el API no respondió dentro del presupuesto. No existe resultado PASS.';
  if (outcome.phase === 'error') return 'ERROR · el dry-run no produjo una respuesta válida.';
  return 'IDLE · dry-run no ejecutado.';
}

function telemetryLabel(outcome: DryRunUiOutcome): string {
  const duration = outcome.durationMs === undefined ? 'pendiente' : `${outcome.durationMs} ms`;
  return `Endpoint ${outcome.endpoint} · duración ${duration} · budget ${outcome.timeoutBudgetMs} ms.`;
}

function isApplicationResponse(value: unknown): value is DevPilotApplicationResponse {
  return Boolean(value && typeof value === 'object' && (value as { contract?: unknown }).contract === 'DevPilotApplicationResponse');
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
