from __future__ import annotations

import json
import shutil
from pathlib import Path

from jsonschema import Draft202012Validator

from devpilot_core.workspace.environment_discovery import EnvironmentDiscoveryService
from devpilot_core.workspace.project_bootstrap_execution import BootstrapExecutionInput, ProjectBootstrapExecutor
from devpilot_core.workspace.project_entry_contracts import ProjectEntryContractService

ROOT = Path(__file__).resolve().parents[1]

def intake(target: Path) -> dict:
    return {
        "schema_id":"SCHEMA-DEVPL-GSDLC-13-B-PROJECT-INTAKE-V2","schema_version":"2.0",
        "project_id":"inventory-sales-local-greenfield","project_name":"Inventory Sales Local Greenfield",
        "project_type":"agent-assisted-sdlc","entry_mode":"CREATE_NEW","target_root":str(target),
        "business_need":"Gestionar productos, existencias y ventas locales, actualizando inventario y mostrando información operativa básica.",
        "technology_decision_status":"deferred-to-architecture",
        "stack":{"frontend":"undecided","backend":"undecided","database":"undecided"},
        "standards":["MIPSoftware","MIASI"],"provider":{"mode":"mock","provider_id":"mock"},
        "model_policy":{"baseline":"mock-no-api","local_model":"optional-opt-in","external_api":"approval-provenance-only"},
        "project_constraints":{"local_first":True,"cloud_required":False,"operator_project_writes_allowed":False},
        "restrictions":{"arbitrary_shell_allowed":False,"silent_network_allowed":False,"remote_git_execute_allowed":False},
    }

def test_successor_schemas_and_catalogs_are_registered_and_neutral() -> None:
    schema=json.loads((ROOT/'docs/schemas/project_intake_gsdlc13_v2.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    tech=json.loads((ROOT/'.devpilot/workspaces/technology_catalog_gsdlc13_v2.json').read_text())
    planning=json.loads((ROOT/'.devpilot/workspaces/bootstrap_planning_catalog_gsdlc13_v2.json').read_text())
    Draft202012Validator(schema).validate(intake(Path('/tmp/devpilot-greenfield')))
    profile=tech['profiles'][0]
    assert profile['profile_id']=='greenfield-neutral-shell'
    assert (profile['frontend'],profile['backend'],profile['database'])==('undecided','undecided','undecided')
    assert [row['tool_id'] for row in profile['tool_requirements']]==['git']
    assert planning['profiles'][0]['venv_required'] is False
    assert planning['profiles'][0]['dependency_jobs']==[]
    files={row['relative_path'] for row in planning['profiles'][0]['files']}
    assert 'frontend/package.json' not in files and 'backend/requirements.txt' not in files
    ids={row['schema_id'] for row in json.loads((ROOT/'docs/schemas/schema_catalog.json').read_text())['schemas']}
    assert {'SCHEMA-DEVPL-GSDLC-13-B-PROJECT-INTAKE-V2','SCHEMA-DEVPL-GSDLC-13-B-TECHNOLOGY-CATALOG-V2','SCHEMA-DEVPL-GSDLC-13-B-BOOTSTRAP-PLANNING-CATALOG-V2'} <= ids

def test_v2_requires_business_need_and_blocks_premature_stack(tmp_path: Path) -> None:
    allowed=tmp_path/'workspaces'; allowed.mkdir(); target=allowed/'pilot'
    service=ProjectEntryContractService(ROOT,allowed_roots=(allowed,)); payload=intake(target)
    assert service.validate_intake(payload).ok
    missing=dict(payload); missing['business_need']='short'
    assert 'PROJECT_INTAKE_BUSINESS_NEED_BLOCKED' in {f.id for f in service.validate_intake(missing).findings}
    premature=json.loads(json.dumps(payload)); premature['stack']['frontend']='react-typescript'
    assert 'PROJECT_INTAKE_PREMATURE_STACK_BLOCKED' in {f.id for f in service.validate_intake(premature).findings}

def test_v2_plan_discovers_git_only_and_has_no_venv_dependencies_or_network(tmp_path: Path) -> None:
    allowed=tmp_path/'workspaces'; allowed.mkdir(); target=allowed/'pilot'; payload=intake(target)
    service=EnvironmentDiscoveryService(ROOT,allowed_roots=(allowed,))
    discovery=service.discover(payload); assert discovery.ok, discovery.to_dict()
    assert [row['tool_id'] for row in discovery.data['report']['tools']]==['git']
    planned=service.build_bootstrap_plan(payload); assert planned.ok, planned.to_dict(); plan=planned.data['bootstrap_plan']
    assert plan['venv']['required'] is False
    assert plan['dependency_jobs']==[]
    assert plan['network']['required_by_plan'] is False
    runtime_effects=[row for row in plan['expected_side_effects'] if row.get('kind')=='platform-runtime-state-write']
    assert {row['operation_id'] for row in runtime_effects}=={'project.runtime-context.register','project.engineering-state.initialize'}
    assert {row['subject'] for row in runtime_effects}=={
        'outputs/runtime/active_workspace_registry.json',
        'outputs/workspaces/inventory-sales-local-greenfield/engineering_state.json',
    }
    assert not any(str(row.get('relative_path','')).startswith(('frontend/','backend/')) for row in plan['files'])

def test_v2_executor_materializes_neutral_clean_project_shell(tmp_path: Path) -> None:
    if shutil.which('git') is None:
        return
    allowed=tmp_path/'workspaces'; allowed.mkdir(); target=allowed/'pilot'; payload=intake(target)
    service=EnvironmentDiscoveryService(ROOT,allowed_roots=(allowed,)); planned=service.build_bootstrap_plan(payload); assert planned.ok
    plan=planned.data['bootstrap_plan']
    platform=tmp_path/'platform'; platform.mkdir()
    result=ProjectBootstrapExecutor(platform,allowed_roots=(allowed,)).execute(BootstrapExecutionInput(intake=payload,bootstrap_plan=plan,plan_hash=plan['plan_hash'],preimage_hash='test-preimage',approval_id='test-approval',actor_id='local-owner',role_at_decision='owner'))
    assert result.ok, result.to_dict()
    verify=result.data['execution']['verification']; assert verify['git_clean'] is True and verify['venv_required'] is False and verify['network_used'] is False
    assert not (target/'.venv').exists()
    assert not (target/'frontend/package.json').exists() and not (target/'backend/requirements.txt').exists()
    project=(target/'.devpilot/project.yaml').read_text(encoding='utf-8')
    assert 'business_need:' in project and 'technology_decision_status: deferred-to-architecture' in project
    assert 'baseline: "mock-no-api"' in project
    runtime=result.data['execution']['project_context_runtime']; assert runtime['status']=='PASS'
    assert Path(runtime['runtime_registry_path']).is_file()
    assert Path(runtime['engineering_state_path']).is_file()
    assert result.data['execution']['platform_runtime_state_writes']==2
    assert result.data['execution']['controlled_platform_state_writes']==2
    assert result.data['execution']['project_writes_outside_workspace']==0

def test_project_entry_ui_exposes_need_constraints_model_policy_and_deferred_technology() -> None:
    source=(ROOT/'ui/web/src/pages/ProjectEntryDryRunView.ts').read_text(encoding='utf-8')
    assert 'Necesidad de negocio / problema a resolver *' in source
    assert 'Confirmo constraints del piloto' in source
    assert 'Model policy del proyecto' in source
    assert "schema_id:'SCHEMA-DEVPL-GSDLC-13-B-PROJECT-INTAKE-V2'" in source
    assert "technology_decision_status:'deferred-to-architecture'" in source
    assert "stack:{frontend:'undecided',backend:'undecided',database:'undecided'}" in source
    assert 'este bootstrap no crea frontend/backend/.venv ni manifests tecnológicos' in source

def test_prompt_boundary_uses_domain_input_not_unbounded_tool_authority() -> None:
    registry=(ROOT/'src/devpilot_core/prompts/registry.py').read_text(encoding='utf-8')
    adr=(ROOT/'docs/02_architecture/adrs/ADR-DEVPL-GSDLC-13-B-02-neutral-project-shell-before-architecture.md').read_text(encoding='utf-8')
    assert 'PromptRegistry' in registry and 'PROMPT_INPUT_REQUIRED_MISSING' in registry and 'PROMPT_RAW_STORAGE_DENIED' in registry
    assert 'domain input' in adr and 'nunca conceder tools/permisos por texto libre' in adr
