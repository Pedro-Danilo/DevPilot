from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))

def test_routes_and_rbac_are_project_scoped_and_role_bound():
    api=load('.devpilot/interfaces/api_route_contract_registry.json')
    routes={r['route_id']:r for r in api['routes']}
    assert routes['api.release.package.status']['source_mutation_allowed'] is False
    assert routes['api.release.package.plan']['policy_action']=='plan'
    assert routes['api.release.package.execute']['policy_action']=='execute'
    assert routes['api.release.package.execute']['external_api_allowed'] is False
    rbac=load('.devpilot/identity/server_rbac_policy_catalog.json')
    policies={r['route_id']:r for r in rbac['route_policies']}
    assert policies['api.release.package.execute']['allowed_roles']==['owner','release-manager']
    assert policies['api.release.package.execute']['human_session_required'] is True
    assert policies['api.release.package.execute']['workspace_scope_required'] is True
    assert policies['api.release.package.execute']['legacy_token_allowed'] is False


def test_ui_contract_is_typed_plan_bound_local_only_and_no_shell():
    ui=load('.devpilot/interfaces/ui_route_contract_registry.json')
    route=next(r for r in ui['routes'] if r['route_id']=='ui.release-package')
    assert route['path']=='/release/package'
    assert route['mutation_controls']['typed_plan_required'] is True
    assert route['mutation_controls']['source_write_enabled'] is False
    assert route['mutation_controls']['publish_enabled'] is False
    main=(ROOT/'ui/web/src/main.ts').read_text(encoding='utf-8')
    page=(ROOT/'ui/web/src/pages/ReleasePackageView.ts').read_text(encoding='utf-8')
    assert "path: '/release/package'" in main and "scope: 'project'" in main
    assert 'renderReleasePackageView' in main
    assert 'arbitrary shell' not in page.lower()
    assert 'SBOM' in page and 'Local-only' in page


def test_11a_is_frozen_at_close_and_11b_is_current_active():
    state=load('.devpilot/project_state.json')
    assert state['gsdlc_11_a_status_at_close']=='CLOSED/PASS/WINDOWS-VALIDATED'
    assert state['gsdlc_11_a_successor_repo_at_close']=='repo_DevPilot_Local_421_DEVPL_GSDLC_11_A_RELEASE_READINESS_WINDOWS_VALIDATED_CANDIDATE.zip'
    assert state['gsdlc_11_a_successor_commit_at_close']=='01c28e73994b74699802dcbac9bb06d686841b89'
    assert state['current_repo']=='repo_DevPilot_Local_421_DEVPL_GSDLC_11_A_RELEASE_READINESS_WINDOWS_VALIDATED_CANDIDATE.zip'
    assert state['current_micro_sprint']=='DEVPL-GSDLC-11-B'
    assert state['gsdlc_11_b_full_regression_runs']==0
    assert state['gsdlc_11_full_regression_budget_consumed']==0
    assert state['gsdlc_11_full_regression_budget_total']==1
    assert state['gsdlc_11_c_authorized'] is False


def test_new_schemas_and_test_contract_are_registered():
    catalog=load('docs/schemas/schema_catalog.json')
    contracts={row.get('contract') for row in catalog['schemas']}
    assert 'GSDLC11BReleaseArtifactManifest' in contracts
    assert 'GSDLC11BSbomBaseline' in contracts
    tcr=load('.devpilot/testing/test_contract_registry_v2.json')
    c=next(row for row in tcr['contracts'] if row['contract_id']=='gsdlc11b-release-package-reproducibility')
    assert c['source_mutations_allowed'] is False and c['network_allowed'] is False
    assert 'Full Regression remains 0 in GSDLC-11-B; backlog budget remains 0/1' in c['validates']


def test_release_artifact_manifest_schema_covers_current_exclusions_contract():
    schema = json.loads((ROOT / "docs/schemas/gsdlc11b_release_artifact_manifest.schema.json").read_text(encoding="utf-8"))
    assert "exclusions" in schema["required"]
    exclusions = schema["properties"]["exclusions"]
    assert exclusions["additionalProperties"] is False
    assert {"forbidden_markers", "forbidden_exact", "runtime_state_excluded", "outputs_excluded", "git_excluded"}.issubset(set(exclusions["required"]))
