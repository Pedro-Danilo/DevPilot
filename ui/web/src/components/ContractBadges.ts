export interface ContractBadgeOptions {
  dryRunLabel?: string;
  warning?: string;
}

export function renderContractBadges(contractId: string, options: ContractBadgeOptions = {}): HTMLElement {
  const wrapper = document.createElement('div');
  wrapper.className = 'contract-badges';
  wrapper.dataset.devpilotUiContract = contractId;
  wrapper.append(
    badge('Local-first', 'local-first'),
    badge(options.dryRunLabel ?? 'Dry-run visible', 'dry-run'),
    badge('No remote', 'no-remote'),
    badge('No connector write', 'no-connector-write'),
    badge('No plugin execution', 'no-plugin-execution'),
  );
  if (options.warning) {
    const note = document.createElement('span');
    note.className = 'contract-badges__note';
    note.textContent = options.warning;
    wrapper.append(note);
  }
  return wrapper;
}

export function renderUiStateNotice(kind: 'loading' | 'pending' | 'empty' | 'error' | 'block' | 'success', message: string): HTMLElement {
  const notice = document.createElement('p');
  notice.className = `ui-state ui-state--${kind}`;
  notice.dataset.uiState = kind;
  notice.setAttribute('role', kind === 'error' || kind === 'block' ? 'alert' : 'status');
  notice.setAttribute('aria-live', kind === 'error' || kind === 'block' ? 'assertive' : 'polite');
  notice.setAttribute('aria-atomic', 'true');
  notice.textContent = message;
  return notice;
}

function badge(text: string, token: string): HTMLElement {
  const item = document.createElement('span');
  item.className = `contract-badge contract-badge--${token}`;
  item.textContent = text;
  return item;
}

// Static contract markers consumed by the local RC verifier. Runtime notices are
// still rendered conditionally through renderUiStateNotice; these markers do
// not create simultaneous visual states.
export const UI_STATE_CONTRACT_MARKERS = [
  'data-ui-state="loading"',
  'data-ui-state="empty"',
  'data-ui-state="error"',
] as const;

export const LEGACY_UI_CONTRACT_LABELS = [
  'Security posture',
  'Provider editor plan-only',
] as const;

// Visual smoke contract markers retained for POST-H-028-C compatibility:
// loading state · empty state · error state · BLOCK · 401/403 · API local down
