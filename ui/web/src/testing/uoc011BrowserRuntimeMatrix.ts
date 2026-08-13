import { UOC011_BROWSER_RUNTIME_STATES } from './Uoc011BrowserStateFixture';

const ROUTES = [
  ['ui.dashboard', '/'],
  ['ui.workspace-documents', '/workspace/documents'],
  ['ui.reports', '/reports'],
  ['ui.traces', '/traces'],
  ['ui.approvals', '/approvals'],
  ['ui.jobs', '/jobs'],
  ['ui.quality', '/quality'],
  ['ui.ai', '/ai'],
  ['ui.settings', '/settings'],
] as const;

interface CaseResult {
  route_id: string;
  path: string;
  state: string;
  status: 'PASS' | 'BLOCK';
  marker?: string;
  error?: string;
}

const host = document.querySelector<HTMLElement>('#probe-host');
const output = document.querySelector<HTMLElement>('#uoc011-runtime-matrix-report');
const statusNode = document.querySelector<HTMLElement>('#status');
if (!host || !output || !statusNode) throw new Error('UOC-011 runtime matrix harness DOM incompleto.');

function loadCase(routeId: string, path: string, stateName: string): Promise<CaseResult> {
  return new Promise((resolve) => {
    const iframe = document.createElement('iframe');
    iframe.width = '1280';
    iframe.height = '900';
    iframe.setAttribute('title', `${routeId} ${stateName}`);
    iframe.style.position = 'absolute';
    iframe.style.left = '-20000px';
    iframe.style.top = '0';
    const timer = globalThis.setTimeout(() => {
      iframe.remove();
      resolve({ route_id: routeId, path, state: stateName, status: 'BLOCK', error: 'timeout-load' });
    }, 15000);
    iframe.addEventListener('load', () => {
      globalThis.clearTimeout(timer);
      try {
        const doc = iframe.contentDocument;
        if (!doc) throw new Error('missing-content-document');
        const fixture = doc.querySelector<HTMLElement>(`[data-uoc011-runtime-route="${routeId}"][data-uoc011-runtime-state="${stateName}"]`);
        const main = doc.querySelector<HTMLElement>('#route-main[role="main"]');
        const active = doc.querySelector<HTMLElement>(`[data-route-id="${routeId}"][aria-current="page"]`);
        if (!fixture) throw new Error('missing-route-state-fixture');
        if (!main) throw new Error('missing-main-landmark');
        if (!active) throw new Error('missing-active-navigation');
        if (fixture.dataset.uoc011RuntimeEvidence !== 'browser-runtime-controlled-fixture') throw new Error('wrong-evidence-mode');
        const marker = fixture.querySelector<HTMLElement>('[data-uoc011-expected-state]')?.textContent?.trim() ?? fixture.textContent?.trim() ?? '';
        resolve({ route_id: routeId, path, state: stateName, status: 'PASS', marker });
      } catch (error) {
        resolve({ route_id: routeId, path, state: stateName, status: 'BLOCK', error: error instanceof Error ? error.message : String(error) });
      } finally {
        iframe.remove();
      }
    }, { once: true });
    const qs = new URLSearchParams({ __uoc011_matrix: '1', __uoc011_route: routeId, __uoc011_state: stateName });
    iframe.src = `${path}?${qs.toString()}`;
    host.append(iframe);
  });
}

async function run(): Promise<void> {
  const cases: CaseResult[] = [];
  // Twelve same-route states execute concurrently; routes stay sequential to keep resource use bounded.
  for (const [routeId, path] of ROUTES) {
    const routeCases = await Promise.all(UOC011_BROWSER_RUNTIME_STATES.map((stateName) => loadCase(routeId, path, stateName)));
    cases.push(...routeCases);
  }
  const failed = cases.filter((item) => item.status !== 'PASS');
  const report = {
    schema_id: 'devpilot.uoc011.browser_runtime_matrix.v1',
    status: failed.length ? 'BLOCK' : 'PASS',
    execution_mode: 'headless-real-browser-controlled-fixture',
    fixture_scope: 'presentation-only-dev-opt-in-no-api-no-source-mutation',
    fixture_activation: 'VITE_UOC011_BROWSER_MATRIX=1+reserved-query-parameters',
    routes_total: ROUTES.length,
    states_total: UOC011_BROWSER_RUNTIME_STATES.length,
    cases_total: cases.length,
    cases_passed: cases.length - failed.length,
    cases_failed: failed.length,
    failures: failed,
    cases,
  };
  output.textContent = JSON.stringify(report);
  output.dataset.status = report.status;
  statusNode.textContent = report.status === 'PASS' ? 'PASS 108/108' : `BLOCK ${report.cases_passed}/${report.cases_total}`;
  document.body.dataset.uoc011RuntimeMatrixStatus = report.status;
  document.title = `UOC011_MATRIX_${report.status}`;
}

void run();
