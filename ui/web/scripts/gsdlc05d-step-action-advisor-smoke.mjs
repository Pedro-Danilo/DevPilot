import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..', '..', '..');
const read = (rel) => fs.readFileSync(path.join(root, rel), 'utf8');
const json = (rel) => JSON.parse(read(rel));
const assert = (condition, message) => { if (!condition) throw new Error(message); };

const catalog = json('.devpilot/gsdlc/step_action_catalog.json');
const uiRegistry = json('.devpilot/interfaces/ui_route_contract_registry.json');
const apiRegistry = json('.devpilot/interfaces/api_route_contract_registry.json');
const rbac = json('.devpilot/identity/server_rbac_policy_catalog.json');
const component = read('ui/web/src/components/StepActionAdvisor.ts');
const projectStatus = read('ui/web/src/pages/ProjectStatusView.ts');
const client = read('ui/web/src/api/client.ts');
const pkg = json('ui/web/package.json');

const kinds = new Set(['MANUAL','PASTE','UPLOAD_IMPORT','EXTERNAL_EDITOR','AGENT','RAG','TYPED_OPERATION']);
assert(catalog.steps.length === 19, 'catalog must cover the 19 MIP current steps');
for (const step of catalog.steps) {
  const stepKinds = new Set(step.actions.map((row) => row.kind));
  for (const kind of kinds) assert(stepKinds.has(kind), `${step.current_step} missing ${kind}`);
  for (const action of step.actions.filter((row) => row.kind === 'AGENT' || row.kind === 'RAG')) {
    assert(Boolean(action.policy?.forced_unavailable_reason), `${action.action_id} must be forced unavailable in GSDLC-05`);
    assert(action.network_required === false && action.external_api_required === false, `${action.action_id} cannot require network/API`);
    assert(action.cost && action.tokens, `${action.action_id} must expose cost/tokens contract`);
  }
}
assert(catalog.safety.advisor_grants_capability === false, 'advisor cannot grant capability');
assert(catalog.safety.server_policy_authoritative === true, 'server policy must remain authority');
assert(catalog.safety.agent_execution_enabled === false && catalog.safety.rag_execution_enabled === false, 'agent/RAG execution must remain disabled');

const uiProject = uiRegistry.routes.find((row) => row.route_id === 'ui.project-status');
assert(uiProject?.allowed_api_routes?.includes('api.guided-sdlc.step-actions'), 'Project Status UI must map step-actions API');
const apiRoute = apiRegistry.routes.find((row) => row.route_id === 'api.guided-sdlc.step-actions');
assert(apiRoute?.path === '/api/v1/guided-sdlc/step-actions', 'API route registry must contain step-actions path');
const rbacRoute = rbac.route_policies.find((row) => row.route_id === 'api.guided-sdlc.step-actions');
assert(rbacRoute?.human_session_required === true && rbacRoute?.legacy_token_allowed === false, 'step-actions route must require human session and reject legacy-token authority');

for (const token of ['Qué puedes hacer ahora','disabled_reasons','approval_required','side_effects','cost','tokens','navigation_target']) {
  assert(component.includes(token), `StepActionAdvisor component missing ${token}`);
}
assert(!component.includes('innerHTML'), 'StepActionAdvisor must not use innerHTML');
assert(projectStatus.includes(').stepActions()'), 'Project Status must load server StepActionAdvisor');
assert(client.includes('/guided-sdlc/step-actions'), 'API client must call step-actions endpoint');
assert(pkg.devpilot.gsdlc05dServerAuthoritative === true, 'package metadata must declare server authority');
assert(pkg.devpilot.gsdlc05dAgentExecutionEnabled === false && pkg.devpilot.gsdlc05dRagExecutionEnabled === false, 'package metadata must keep agent/RAG disabled');
assert(pkg.devpilot.gsdlc05dFullRegressionRuns === 0, 'GSDLC-05-D cannot consume full regression');

console.log(JSON.stringify({
  status: 'PASS',
  check: 'DEVPL-GSDLC-05-D StepActionAdvisor static smoke',
  current_steps: catalog.steps.length,
  actions_total: catalog.steps.reduce((sum, row) => sum + row.actions.length, 0),
  server_policy_authoritative: true,
  agent_execution_enabled: false,
  rag_execution_enabled: false,
  full_regression_runs: 0
}, null, 2));
