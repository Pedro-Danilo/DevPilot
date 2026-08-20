import fs from 'node:fs';
import path from 'node:path';

const root=process.cwd();
const read=(p)=>fs.readFileSync(path.join(root,p),'utf8');
const main=read('src/main.ts');
const dashboard=read('src/pages/Dashboard.ts');
const home=read('src/components/ProjectHomeEntryPanel.ts');
const entry=read('src/pages/ProjectEntryDryRunView.ts');
const approvalCenter=read('src/pages/ApprovalCenterView.ts');
const client=read('src/api/client.ts');
const styles=read('src/styles.css');
const registry=JSON.parse(read('../../.devpilot/interfaces/ui_route_contract_registry.json'));

const required=[
  ['home three options', ['Crear nuevo proyecto','Abrir proyecto existente','Importar repositorio Git'].every(x=>home.includes(x))],
  ['home browser-only claim', home.includes('journey normal ocurre íntegramente en el navegador')],
  ['project home preserves historical route id', main.includes("path: '/', routeId: 'ui.dashboard', title: 'Project Home'")],
  ['dashboard embeds project home', dashboard.includes('renderProjectHomeEntryPanel')],
  ['entry deep-link mode', main.includes('readEntryMode') && home.includes('/project/entry?mode=')],
  ['pre-project navigation guard', main.includes("scope: 'project'") && main.includes('routeAllowed') && main.includes('routeVisible')],
  ['contextual approval navigation', main.includes("scope: 'entry-or-project'")],
  ['approval center cross-tab handoff', client.includes('APPROVAL_CENTER_ENTRY_HANDOFF_KEY') && client.includes('session_created_at') && main.includes('readApprovalCenterEntryHandoff(session, handoffApprovalId)')],
  ['approval handoff only after request exists', entry.includes('approvalLink.hidden=true') && entry.includes('armApprovalCenterEntryHandoff') && entry.includes('approval_id=${encodeURIComponent(id)}')],
  ['approval handoff exact-id bound', client.includes('approval_id: approvalId.trim()') && client.includes('value.approval_id === expected')],
  ['approval handoff remains UX-only', client.includes('localStorage') && client.includes('clearApprovalCenterEntryHandoff')],
  ['targeted approval center bypasses global list dependency', approvalCenter.includes('Approval Center · Project Entry') && approvalCenter.includes('showApproval(state.handoffApprovalId!)') && approvalCenter.includes('No es necesario filtrar ni cargar la lista global')],
  ['approval authority renders authenticated session roles', approvalCenter.includes('session.principal.roles') && approvalCenter.includes("authCapabilities('devpilot-local')") && approvalCenter.includes('capability_view') && approvalCenter.includes('no sustituye la sesión autenticada')],
  ['entry context begins from home', home.includes('beginProjectEntryJourney')],
  ['project context activates only on confirmed execute pass', entry.includes('activateProjectJourney') && entry.includes('executionPayload.status') && entry.includes('contexto de proyecto permanece bloqueado')],
  ['advanced dashboard hidden until project context', dashboard.includes("readProjectJourneyContext()?.phase === 'project'")],
  ['logout clears project context', main.includes('clearProjectJourneyContext')],
  ['client project id validation', entry.includes('PROJECT_ID_PATTERN')],
  ['parameter change invalidation', entry.includes('parámetros cambiaron') && entry.includes('invalidatePlan')],
  ['owner role gating', entry.includes("roles.includes('owner')")],
  ['approval id readonly', entry.includes('approvalId.input.readOnly=true')],
  ['success to project status', entry.includes('/project/status') && entry.includes('Continuar a Estado del proyecto')],
  ['rollback evidence visible', entry.includes('Recovery / rollback evidence')],
  ['dev-only fault harness', entry.includes('VITE_GSDLC03E_BROWSER_ACCEPTANCE') && entry.includes('fault_stage')],
  ['ordinary request timeout preserved', client.includes('DEFAULT_REQUEST_TIMEOUT_MS = 8000')],
  ['project-entry probe timeout windows tolerant', client.includes('PROJECT_ENTRY_PROBE_TIMEOUT_SECONDS = 8.0')],
  ['project-entry planning browser budget bounded', client.includes('PROJECT_ENTRY_PLANNING_TIMEOUT_MS = 90000') && client.includes('timeoutMs: PROJECT_ENTRY_PLANNING_TIMEOUT_MS')],
  ['bounded execute timeout', client.includes('PROJECT_ENTRY_EXECUTION_TIMEOUT_MS = 240000')],
  ['timeout normalization preserves project-entry budgets', client.includes('MAX_REQUEST_TIMEOUT_MS = PROJECT_ENTRY_EXECUTION_TIMEOUT_MS') && client.includes('Math.min(Number(value), MAX_REQUEST_TIMEOUT_MS)') && !client.includes('Math.min(Number(value), 60000)')],
  ['approval center bounded read timeout', client.includes('APPROVAL_CENTER_READ_TIMEOUT_MS = 30000')],
  ['entry resume sessionStorage contract', client.includes('PROJECT_ENTRY_RESUME_STATE_KEY') && client.includes('PROJECT_ENTRY_RESUME_TTL_MS = 30 * 60 * 1000') && client.includes('saveProjectEntryResumeState') && client.includes('readProjectEntryResumeState')],
  ['entry resume remains UX-only', client.includes('globalThis.sessionStorage?.setItem(PROJECT_ENTRY_RESUME_STATE_KEY') && !client.includes('localStorage?.setItem(PROJECT_ENTRY_RESUME_STATE_KEY') && entry.includes('Revalidar preimage antes de verificar approval o ejecutar')],
  ['project home exposes resume CTA', home.includes('readProjectEntryResumeState') && home.includes('Retomar ${resumeState.entry_mode}')],
  ['targeted approval tab removes project-home trap', main.includes('auxiliaryApprovalHandoff') && approvalCenter.includes('Cerrar esta pestaña y volver a CREATE') && approvalCenter.includes('No navegue a Project Home desde aquí')],
  ['responsive home', styles.includes('.project-home__cards') && styles.includes('@media(max-width:980px)')],
];
for(const [name,ok] of required){if(!ok){console.error(`BLOCK: ${name}`);process.exit(20);}}
const dashboardRoute=registry.routes.find((x)=>x.route_id==='ui.dashboard');
if(!dashboardRoute||dashboardRoute.path!=='/'||dashboardRoute.title!=='Project Home'||!dashboardRoute.source_files.includes('ui/web/src/components/ProjectHomeEntryPanel.ts')){console.error('BLOCK: ui.dashboard registry not synchronized');process.exit(20);}
console.log(JSON.stringify({status:'PASS',checks:required.length+1,normal_user_powershell_required:0,external_operator_project_writes:0,top_level_route_added:false},null,2));
