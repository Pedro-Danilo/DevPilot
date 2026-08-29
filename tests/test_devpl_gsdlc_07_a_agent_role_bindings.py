from __future__ import annotations
import json
from pathlib import Path
import jsonschema
from devpilot_core.agents import AgentRoleBindingCatalog
from devpilot_core.application import ApplicationService
from devpilot_core.guided_sdlc import AdvisorContext, ExecutionModeAdvisor
from devpilot_core.modeling.model_router_v2 import GovernedModelRouteDecision
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))
def ctx(step): return AdvisorContext(workspace_id="devpilot-local",current_step=step,effective_roles=("owner",),workspace_scopes=("devpilot-local",),artifact_readiness="READY",miasi_gate_status="PASS",provider_status="AVAILABLE",budget_status="PASS",active_project_context=True)

def test_07_a_schemas_catalog_and_all_19_bindings_pass():
 c=load('.devpilot/agents/agent_role_binding_catalog.json'); jsonschema.Draft202012Validator(load('docs/schemas/agent_role_binding_catalog.schema.json')).validate(c)
 b=load('.devpilot/agents/step_agent_bindings.json'); jsonschema.Draft202012Validator(load('docs/schemas/step_agent_binding.schema.json')).validate(b)
 boundary=load('.devpilot/agents/agent_runtime_boundary.json'); jsonschema.Draft202012Validator(load('docs/schemas/agent_runtime_boundary.schema.json')).validate(boundary)
 result=AgentRoleBindingCatalog(ROOT).validate(); assert result['status']=='PASS'; assert result['roles_total']==8; assert result['steps_total']==result['mip_steps_total']==19

def test_07_a_every_supported_step_has_explicit_agent_or_none():
 cat=AgentRoleBindingCatalog(ROOT); mip=load('.devpilot/gsdlc/mip_workflow_registry.json')
 for phase in mip['phases']:
  b=cat.binding(phase['current_step']); assert b is not None; assert (b.agent_role_id is not None) != b.explicit_none

def test_07_a_least_privilege_tool_allowlists_are_subsets_and_no_approval_tool():
 cat=AgentRoleBindingCatalog(ROOT); assert cat.validate()['status']=='PASS'
 for rid in ['product','requirements','architecture','security','test','planning','coding','review']:
  role=cat.role(rid); assert role and role.tool_allowlist; assert not role.can_approve; assert all('approval' not in t for t in role.tool_allowlist)

def test_07_a_forbidden_tool_negative_cannot_expand_step_scope():
 cat=AgentRoleBindingCatalog(ROOT); b=cat.binding('requirements'); assert b; assert 'git.workspace.commit' not in b.tool_allowlist; assert 'rollback.execute' not in b.tool_allowlist

def test_07_a_missing_capability_exposes_fallback_without_tool_authority():
 d=AgentRoleBindingCatalog(ROOT).descriptor_for_step('implementation',available_model_capabilities={'text_generation'}); assert d; assert 'coding' in d['missing_model_capabilities']; assert d['fallback']['mode']=='degrade-to-plan-only'; assert d['tool_execution_authority'] is False

def test_07_a_model_route_decision_never_grants_tool_permission():
 # Existing GSDLC-06 contract and 07-A binding must agree on authority separation.
 decision=GovernedModelRouteDecision(workload_id='07-a',route_status='selected',provider_id='devpilot-local',model_id='mock-deterministic-v1')
 payload=decision.to_dict(); assert 'tool_execution_authority' not in payload and 'tool_permission' not in payload
 d=AgentRoleBindingCatalog(ROOT).descriptor_for_step('requirements'); assert d and d['model_route_grants_tool_permission'] is False

def test_07_a_framework_candidates_cannot_bypass_policy_engine():
 boundary=load('.devpilot/agents/agent_runtime_boundary.json'); assert boundary['safety']['policy_engine_final_authority'] is True
 assert all(not x['dependency_adopted'] for x in boundary['framework_candidates']); assert boundary['tool_authority']['decision_authority']==['PolicyEngine','RBAC','Approval']

def test_07_a_agent_role_never_becomes_human_approval_role():
 cat=AgentRoleBindingCatalog(ROOT); assert cat.validate()['agent_role_can_approve'] is False
 for b in load('.devpilot/agents/step_agent_bindings.json')['bindings']: assert b['human_review_required'] is True and b['approval_authority']=='human-only'

def test_07_a_step_action_advisor_exposes_descriptor_but_keeps_05d_execution_freeze():
 decision=ExecutionModeAdvisor(ROOT).advise(ctx('requirements')); row=next(x for x in decision.actions if x.kind=='AGENT')
 assert row.agent_descriptor['agent_role_id']=='requirements'; assert 'Requirements Agent'==row.agent_descriptor['display_name']; assert row.agent_descriptor['execution_enabled_in_07_a'] is False
 assert row.executable is False and row.availability=='UNAVAILABLE'; assert 'GSDLC_05_AGENT_EXECUTION_OUT_OF_SCOPE' in {r.code for r in row.disabled_reasons}

def test_07_a_settings_agent_runtime_snapshot_is_read_only_and_safe():
 result=ApplicationService(ROOT).settings_agent_runtime(); assert result.ok is True; assert result.data['summary']['roles_total']==8; assert result.data['summary']['bindings_total']==19
 assert result.data['summary']['execution_enabled_in_07_a'] is False; assert result.data['summary']['external_api_used'] is False; assert result.data['summary']['model_route_grants_tool_permission'] is False

def test_07_a_api_rbac_openapi_ui_registry_are_in_parity():
 api=load('.devpilot/interfaces/api_route_contract_registry.json'); rb=load('.devpilot/identity/server_rbac_policy_catalog.json'); ui=load('.devpilot/interfaces/ui_route_contract_registry.json'); op=load('docs/07_interfaces/openapi_v1.json')
 route=next(x for x in api['routes'] if x['route_id']=='api.settings.agent-runtime'); policy=next(x for x in rb['route_policies'] if x['route_id']==route['route_id']); settings=next(x for x in ui['routes'] if x['route_id']=='ui.settings')
 assert route['method']=='GET' and route['mutations_allowed'] is False and route['external_api_allowed'] is False; assert policy['human_session_required'] is True and policy['legacy_token_allowed'] is False
 assert route['route_id'] in settings['allowed_api_routes']; assert '/api/v1/settings/agent-runtime' in op['paths']

def test_07_a_agent_binding_matrix_is_complete_and_non_authoritative_for_approval():
 m=load('docs/audits/DEVPL_GSDLC_07_A_AGENT_BINDING_MATRIX.json'); assert m['roles_total']==8 and m['steps_total']==19; assert m['safety']['agent_role_can_approve'] is False; assert all(x['agent_can_approve'] is False for x in m['bindings'])
