"""R01-12: truthfulness, provenance and redaction gates."""
from pathlib import Path
import json
from devpilot_core.application.observability_origin import project_provider_origin
from devpilot_core.application.model_gateway_settings_service import ModelGatewaySettingsService

ROOT = Path(__file__).resolve().parents[1]
H = "a" * 64
Q = "b" * 64

def receipts(cost=0.0, performed=False):
    p = {"request_id":"safe-route", "route_sha256":H,"provenance_sha256":Q, "raw_secret":"s3cr3t"}
    r = {"request_id":"safe-route", "route_sha256":H,"provenance_sha256":Q, "receipt_sha256":H,
         "provider_class":"D", "provider_id":"deterministic", "model_id":None, "outcome":"preview", "cost_usd":cost,
         "execution_attempted":False,"model_call_performed":performed, "metadata":{"api_key":"s3cr3t"},
         "fallback":{"reason":"not-applied"}, "denial_reason":"api_key=s3cr3t"}
    return p,r

def test_deterministic_receipt_explicit_zero_and_redacted():
    p,r=receipts(); row=project_provider_origin(p,r,demonstration=True)
    assert row['cost']=={'status':'ZERO_NO_EXECUTION','usd':0.0}
    assert row['receipt_linked'] is True and row['model']=='NOT_AVAILABLE'
    assert row['error']=='NOT_AVAILABLE'
    assert 's3cr3t' not in json.dumps(row)

def test_unmeasured_model_cost_never_fabricated():
    p,r=receipts(); row=project_provider_origin(p,r)
    assert row['cost']=={'status':'NOT_AVAILABLE','usd':None}

def test_mismatch_no_forged_provenance():
    p,r=receipts();r['route_sha256']='x'*64
    row=project_provider_origin(p,r,demonstration=True)
    assert row['receipt_linked'] is False and row['provider']=='NOT_AVAILABLE'
    assert row['cost']['status']=='NOT_AVAILABLE'

def test_measured_receipt_requires_model_call():
    p,r=receipts(cost=0.42,performed=True);r['execution_attempted']=True
    row=project_provider_origin(p,r)
    assert row['cost']=={'status':'RECEIPT_REPORTED','usd':0.42}
    assert row['model_call_performed'] is True

def test_missing_receipt_and_malicious_identifiers_are_safe():
    assert project_provider_origin(None,None)['status']=='NOT_AVAILABLE'
    p,r=receipts();r['provider_id']='token=SECRET';r['denial_reason']='secret=SECRET';r['fallback']={'reason':'private token SECRET'}
    row=project_provider_origin(p,r)
    assert row['provider']=='REDACTED' and row['fallback']=='NOT_AVAILABLE'
    assert 'SECRET' not in json.dumps(row)

def test_kernel_receipt_linked_in_real_settings_snapshot():
    result=ModelGatewaySettingsService(ROOT).snapshot()
    assert result.ok
    foundation=result.data['multiprovider_foundation']
    row=foundation['origin_observability']
    assert row['receipt_linked'] is True
    assert row['source']=='FOUNDATION_PREVIEW'
    assert row['cost']['status']=='ZERO_NO_EXECUTION'
    assert row['model_call_performed'] is False
    assert 'raw_secret' not in json.dumps(row)

def test_guided_expert_ui_and_unknown_cost():
    text=(ROOT/'ui/web/src/components/ModelSettingsView.ts').read_text()
    agent=(ROOT/'ui/web/src/components/AgentEvalTraceView.ts').read_text()
    assert 'renderOriginObservability(foundation)' in text
    assert 'Expert · hashes y procedencia redactada' in text
    assert 'NOT_AVAILABLE · sin medición real' in text
    assert 'cost known' not in agent
    assert "trace.cost_known === true" in agent
    assert 'cost USD: ${escapeHtml(String(trace.estimated_cost_usd ?? 0))}' not in agent

def test_documentary_active_pointers_only():
    for f in ('.devpilot/docs_governance/source_registry.json','.devpilot/project_state.json'):
        o=json.loads((ROOT/f).read_text())
        # Active pointers are successor-owned; historical R01-12 must not pin current R01-13.
        assert o['current_micro_sprint'].startswith(('MP132-R01-', 'MP132-R02-01/'))
