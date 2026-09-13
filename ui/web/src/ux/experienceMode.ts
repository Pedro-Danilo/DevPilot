export type ExperienceMode = 'guided' | 'expert';

const STORAGE_KEY = 'devpilot.ui.experience-mode.v1';
const MODE_EVENT = 'devpilot:experience-mode-change';

export const EXPERIENCE_MODE_AUTHORITY_CONTRACT = Object.freeze({
  authority: 'server-side-unchanged',
  rbac: 'unchanged',
  approvals: 'unchanged',
  tool_permissions: 'unchanged',
  model_permissions: 'unchanged',
  mutability: 'unchanged',
  browser_storage_role: 'ux-preference-only',
});

export function readExperienceMode(): ExperienceMode {
  try {
    const value = globalThis.localStorage?.getItem(STORAGE_KEY);
    return value === 'expert' ? 'expert' : 'guided';
  } catch {
    return 'guided';
  }
}

export function applyExperienceMode(mode: ExperienceMode): ExperienceMode {
  const safeMode: ExperienceMode = mode === 'expert' ? 'expert' : 'guided';
  try { globalThis.document?.documentElement?.setAttribute('data-experience-mode', safeMode); } catch { /* UX-only. */ }
  return safeMode;
}

export function writeExperienceMode(mode: ExperienceMode): ExperienceMode {
  const safeMode = applyExperienceMode(mode);
  try { globalThis.localStorage?.setItem(STORAGE_KEY, safeMode); } catch { /* UX-only preference; server authority is unaffected. */ }
  try { globalThis.dispatchEvent(new CustomEvent<ExperienceMode>(MODE_EVENT, { detail: safeMode })); } catch { /* no-op outside browser */ }
  return safeMode;
}

export function initializeExperienceMode(): ExperienceMode {
  return applyExperienceMode(readExperienceMode());
}

export function onExperienceModeChange(listener: (mode: ExperienceMode) => void): () => void {
  const handler = (event: Event) => listener((event as CustomEvent<ExperienceMode>).detail === 'expert' ? 'expert' : 'guided');
  globalThis.addEventListener?.(MODE_EVENT, handler);
  return () => globalThis.removeEventListener?.(MODE_EVENT, handler);
}
