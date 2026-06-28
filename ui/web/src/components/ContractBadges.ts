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

export function renderUiStateNotice(kind: 'loading' | 'empty' | 'error' | 'block', message: string): HTMLElement {
  const notice = document.createElement('p');
  notice.className = `ui-state ui-state--${kind}`;
  notice.dataset.uiState = kind;
  notice.textContent = message;
  return notice;
}

function badge(text: string, token: string): HTMLElement {
  const item = document.createElement('span');
  item.className = `contract-badge contract-badge--${token}`;
  item.textContent = text;
  return item;
}
