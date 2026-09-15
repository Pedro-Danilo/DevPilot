import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const src = (rel) => fs.readFileSync(path.join(root, rel), 'utf8');
const checks = [];
const check = (id, ok, detail) => checks.push({ id, status: ok ? 'PASS' : 'BLOCK', detail });

const main = src('src/main.ts');
const navigationPresentation = src('src/ux/navigationPresentation.ts');
const styles = src('src/styles.css');
const mode = src('src/ux/experienceMode.ts');
const control = src('src/components/ExperienceModeControl.ts');
const help = src('src/pages/HelpSystemView.ts');
const contextual = src('src/components/ContextualHelp.ts');
const recovery = src('src/pages/RecoveryView.ts');
const reconciliation = src('src/pages/ConflictResolutionView.ts');
const ai = src('src/components/AIControlCenterView.ts');

check('mode-authority-parity', [/rbac:\s*'unchanged'/i, /approvals:\s*'unchanged'/i, /tool_permissions:\s*'unchanged'/i, /model_permissions:\s*'unchanged'/i, /mutability:\s*'unchanged'/i].every((r) => r.test(mode)), 'UX mode contract does not alter server authority');
check('guided-expert-control', control.includes('aria-pressed') && control.includes('Guided') && control.includes('Expert'), 'mode selector exposes accessible pressed state');
check('help-route', main.includes("path: '/help'") && main.includes("routeId: 'ui.help'") && main.includes('HelpSystemView'), 'global help route registered');
check('progressive-disclosure', (main.includes('primary-nav__advanced') && main.includes('Más herramientas')) || (main.includes('primary-nav__group') && navigationPresentation.includes('Understand & Plan') && navigationPresentation.includes('Diagnostics')), 'historical advanced disclosure or successor grouped disclosure is present');
check('blockers-remain-core', ['/recovery', '/reconciliation'].every((p) => main.includes(p)), 'recovery/conflict surfaces remain directly reachable');
check('route-focus', main.includes('queueMicrotask') && main.includes('.focus('), 'route change restores programmatic focus');
check('skip-link', main.includes('skip-link') || styles.includes('.skip-link'), 'skip link remains present');
check('visible-focus', styles.includes(':focus-visible'), 'visible keyboard focus styling present');
check('reduced-motion', styles.includes('prefers-reduced-motion'), 'reduced motion preference honored');
check('responsive-layout', styles.includes('@media') && styles.includes('900px') && styles.includes('560px'), 'responsive breakpoints defined');
check('live-errors', contextual.includes("setAttribute('role', 'alert')") && contextual.includes("setAttribute('aria-live', 'assertive')") && recovery.includes('renderAccessibleError') && reconciliation.includes('renderAccessibleError'), 'errors use accessible live alert and focus path');
check('labeled-controls', recovery.includes('aria-label') && reconciliation.includes('aria-label'), 'critical recovery/reconciliation controls have accessible labels');
check('context-help', help.includes('Glosario') && contextual.includes('Siguiente acción segura') && contextual.includes('Evidence ref'), 'plain-language help + technical/evidence details implemented');
check('expert-diagnostics', reconciliation.includes('expert-only') && recovery.includes('expert-only'), 'expert diagnostics are presentation-only additions');
check('ai-policy-parity', /Guided.*Expert/i.test(ai) && /autoridad|authority/i.test(ai), 'AI Control Center states mode policy parity');
const combined = [main, mode, control, help, contextual, recovery, reconciliation, ai].join('\n');
check('secret-literal-negative', !/(sk-[A-Za-z0-9]{12,}|Bearer\s+[A-Za-z0-9._-]{12,}|api[_-]?key\s*[:=]\s*["'][^"']{8,})/i.test(combined), 'no obvious credential literal in mode/help surfaces');

const blocked = checks.filter((c) => c.status !== 'PASS');
console.log(JSON.stringify({ status: blocked.length ? 'BLOCK' : 'PASS', checks_total: checks.length, pass: checks.length - blocked.length, block: blocked.length, checks }, null, 2));
process.exit(blocked.length ? 2 : 0);
