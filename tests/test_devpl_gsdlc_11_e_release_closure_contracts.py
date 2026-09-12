from __future__ import annotations
import json
from pathlib import Path
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def test_11e_routes_policy_rbac_ui_are_coherent():
    api=load('.devpilot/interfaces/api_route_contract_registry.json'); rbac=load('.devpilot/identity/server_rbac_policy_catalog.json'); ui=load('.devpilot/interfaces/ui_route_contract_registry.json')
    ids={x['route_id'] for x in api['routes']}; policies={x['route_id'] for x in rbac['route_policies']}
    assert {'api.release.closure.status','api.release.closure.finalize'} <= ids & policies
    assert ('GET','/api/v1/release/closure') in API_ROUTE_POLICIES and ('POST','/api/v1/release/closure/finalize') in API_ROUTE_POLICIES
    route=next(x for x in ui['routes'] if x['route_id']=='ui.release-closure'); assert route['path']=='/release/closure'; assert route['mutation_controls']['publish_enabled'] is False

def test_11e_full_regression_closure_fact_is_frozen_after_successor_activation():
    state=load('.devpilot/project_state.json'); assert state['gsdlc_11_full_regression_budget_total']==1; assert state['gsdlc_11_full_regression_budget_consumed']==1; assert state['gsdlc_11_full_regression_reserved_for'] is None; assert state['gsdlc_11_e_full_regression_runs']==1; assert state['gsdlc_11_e_second_full_regression_runs']==0; assert state['gsdlc_11_e_status']=='CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY'
    prompt=(ROOT/'05_PROMPT_DEVPL_GSDLC_11_E_v1_0_1_REBOUND_REPO424.md').read_text(encoding='utf-8'); assert 'exactly 1 logical Full' in prompt; assert 'NO RERUN' in prompt
