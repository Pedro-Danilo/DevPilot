from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO="repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip"

def text(path:str)->str: return (ROOT/path).read_text(encoding="utf-8")
def data(path:str)->dict: return json.loads(text(path))

def test_runtime_corrective_state_is_preserved_after_01_d_closure()->None:
    state=data('.devpilot/project_state.json')
    assert state['post_h_eval_002_01_d_governance_repo']==REPO
    assert state['current_repo'].startswith('repo_DevPilot_Local_')
    assert state['current_micro_sprint'] in {'POST-H-EVAL-002-02-A', 'POST-H-EVAL-002-02-B'}
    assert state['post_h_eval_002_01_d_closed'] is True
    assert state['post_h_eval_002_01_d_required_retest_run_id']=='PILOT-E2E-001-RUN-05B-RERUN-03'
    assert state['post_h_eval_002_01_d_next_authorized'] is True

def test_client_keeps_neg08_default_and_bounds_expensive_operations()->None:
    source=text('ui/web/src/api/client.ts')
    assert 'DEFAULT_REQUEST_TIMEOUT_MS = 8000' in source
    assert 'READINESS_REQUEST_TIMEOUT_MS = 30000' in source
    assert 'ACTION_DRY_RUN_TIMEOUT_MS = 60000' in source
    assert 'PROVIDER_PLAN_TIMEOUT_MS = 60000' in source
    assert 'PROTECTED_WARMUP_TIMEOUT_MS = 15000' in source
    assert 'TRANSIENT_NETWORK_RETRY_DELAYS_MS = [500, 1000]' in source
    assert "error instanceof DevPilotApiError && error.status === 0" in source
    assert "timeoutMs: ACTION_DRY_RUN_TIMEOUT_MS" in source
    assert "timeoutMs: PROVIDER_PLAN_TIMEOUT_MS" in source

def test_dashboard_warms_protected_surface_and_resets_stale_state()->None:
    source=text('ui/web/src/pages/Dashboard.ts')
    assert 'client.protectedWarmup()' in source
    assert 'state.snapshot = {}' in source
    assert 'state.errors = {}' in source
    assert 'state.durations = {}' in source
    assert 'Warm-up protegido' in source

def test_actions_expose_pending_disabled_and_accessible_feedback()->None:
    settings=text('ui/web/src/pages/SettingsView.ts')
    approvals=text('ui/web/src/pages/ApprovalCenterView.ts')
    dry=text('ui/web/src/components/DryRunActionForm.ts')
    assert "pendingAction?: 'providerPlan'" in settings
    assert 'runPending' in approvals
    assert 'Ejecutando…' in settings and 'Ejecutando…' in approvals and 'Ejecutando…' in dry
    assert 'aria-busy' in settings and 'aria-busy' in approvals and 'aria-busy' in dry
    assert 'aria-live' in settings and 'aria-live' in approvals and 'aria-live' in dry

def test_runtime_manifest_preserves_safety_and_run02_block()->None:
    manifest=data('docs/post_h_eval_002_01_d_runtime_corrective_324_manifest.json')
    assert manifest['run_02_forensic']['decision']=='BLOCK'
    assert manifest['safety']['default_timeout_ms']==8000
    assert manifest['safety']['expensive_timeout_ms']==30000
    assert manifest['safety']['network_retry_statuses']==[0]
    assert manifest['validation']['run_id']=='PILOT-E2E-001-RUN-03'
    assert manifest['validation']['closure_allowed'] is False
