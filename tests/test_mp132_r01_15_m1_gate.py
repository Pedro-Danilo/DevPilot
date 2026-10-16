"""R01-15: historical attestation gate and a real offline service integration smoke."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import pytest
from devpilot_core.maturity.r01_m1_gate import R01M1Gate, R01M1EvidenceError
from devpilot_core.generation import (GenerationRequest, GenerationRouteResolver,
    GenerationRoutePolicy, ProviderSelectionPolicy, ProviderClass,
    TaskRouteRule, FallbackQuality, WorkloadEstimate)
from devpilot_core.evals.candidate_harness import CandidateEvaluationHarness
from devpilot_core.docs_governance.markdown_publication import GovernedMarkdownPublisher,MarkdownPublication
from devpilot_core.application.persistent_settings import PersistentSettingsStore,SettingsDenied
ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'evals/fixtures/r01_m1_evidence_v1.json'
BASE='feaac2723c1f8a467f5cdb7d456e4e7679dd0f82'

def source():return json.loads(FIX.read_text(encoding='utf-8'))
def test_first_vertical_maturity_gate_limited_and_deterministic():
    a=R01M1Gate.evaluate_file(FIX,expected_head=BASE)
    b=R01M1Gate.evaluate_file(FIX,expected_head=BASE)
    assert a==b and a['decision']=='PASS_WITH_FINDINGS'
    assert a['first_vertical']=='VERTICAL_INTEGRATED_DETERMINISTIC_WITH_BROWSER'
    assert a['multi_model_production']=='FOUNDATION_PRESENT_NOT_VALIDATED'
    assert a['receipt_count']==14 and a['browser_owner_attestations']==3
    assert a['model_calls']==0 and a['external_api_calls']==0 and a['next']=='R2_NOT_AUTHORIZED'

@pytest.mark.parametrize('mutant', ['baseline','chain','missing','order','tampered-receipt','fake-browser','fake-local','fake-external','fake-semantic','wrong-scope','no-findings'])
def test_false_maturity_claims_fail_closed(mutant):
    e=source()
    if mutant=='baseline':e['baseline_head']='a'*40
    elif mutant=='chain':e['attestations'][6]['base']='a'*40
    elif mutant=='missing':e['attestations'].pop()
    elif mutant=='order':e['attestations'][3]['sprint']='R01-02'
    elif mutant=='tampered-receipt':e['attestations'][3]['evidence_zip_sha256']='invalid'
    elif mutant=='fake-browser':e['attestations'][10]['browser']='NOT_REQUIRED_NO_UI_CHANGE'
    elif mutant=='fake-local':e['levels']['model_local_real']='PRODUCTION_VALIDATED'
    elif mutant=='fake-external':e['levels']['model_external_real']='ENABLED'
    elif mutant=='fake-semantic':e['levels']['semantic_llm_judge']='VALIDATED'
    elif mutant=='wrong-scope':e['successor']='R2_APPROVED'
    else:e['known_findings']=[]
    with pytest.raises(R01M1EvidenceError):R01M1Gate.evaluate(e,expected_head=BASE)

def test_report_cannot_mutate_evidence():
    e=source();before=copy.deepcopy(e)
    R01M1Gate.evaluate(e,expected_head=BASE)
    assert e==before

def test_offline_integrated_candidate_policy_docs_settings_preview(tmp_path):
    """A real bounded multi-service smoke, not an E2E production/model test."""
    # Candidate evaluation; fixture uses mock route and has adversarial negative controls.
    candidate=CandidateEvaluationHarness.evaluate_file(ROOT/'evals/fixtures/candidate_eval_v1.json',baseline_head=BASE)
    assert candidate['summary']['matched']==6 and candidate['summary']['negative_cases']==4
    assert candidate['summary']['network_calls']==0
    # Policy selection and explicit external denial, before any model/provider call.
    rule=TaskRouteRule('review',('architecture',),(ProviderClass.DETERMINISTIC,),FallbackQuality.REDUCED,
                       max_input_tokens=100,max_output_tokens=40,max_cost_usd=0.0,max_timeout_seconds=10)
    planner=GenerationRoutePolicy(GenerationRouteResolver(ROOT),{'review':rule})
    def req(route):return GenerationRequest(request_id='m1-audit',artifact_type='architecture',profile_version='architecture-v1',
       dependency_profile_version='architecture-deps-v1',upstream_hashes={'requirements':'a'*64},
       preferred_route=route,allowed_routes=(route,),policy_snapshot={'offline_required':True,'privacy_class':'internal'},budget_snapshot={})
    policy=ProviderSelectionPolicy(allowed_provider_classes=(ProviderClass.DETERMINISTIC,ProviderClass.EXTERNAL_MODEL),
                                    execution_enabled_classes=(ProviderClass.DETERMINISTIC,))
    estimate=WorkloadEstimate(10,10,0.0,5)
    selected=planner.plan(req('deterministic'),task_type='review',estimate=estimate,selection_policy=policy)
    assert selected.status=='SELECTED_DETERMINISTIC' and selected.execution_allowed
    rejected=planner.plan(req('external-model'),task_type='review',estimate=estimate,selection_policy=policy)
    assert rejected.status=='DENIED' and rejected.reason=='EXTERNAL_EGRESS_DENIED'
    # Governed documentation preview only; no publication or source-registry write.
    g=tmp_path/'.devpilot/docs_governance';g.mkdir(parents=True)
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/test_m1.py').write_text('pass\n')
    (g/'source_registry.json').write_text(json.dumps({'documents':[],'summary':{},'registry_id':'m1','schema_id':'DocumentationSourceRegistry'}))
    (g/'documentation_authority_graph.json').write_text(json.dumps({'nodes':[],'graph_id':'m1'}))
    (g/'rebaseline_p0_overlay.json').write_text(json.dumps({'authority':{'mp_registry_state':'PROGRAM_132_PUBLISHED/0_ENTRIES'}}))
    before=(g/'source_registry.json').read_bytes()
    doc=MarkdownPublication('docs/published/architecture/m1.md','DOC-M1','Owner',
       '---\ndoc_id: DOC-M1\nstatus: approved\nowner: Owner\n---\n# M1\nEvidence-bound approved document.\n',('tests/test_m1.py',),True)
    preview=GovernedMarkdownPublisher(tmp_path).publish(doc,expected_registry_sha256=hashlib.sha256(before).hexdigest())
    assert preview['status']=='PREVIEW_APPROVED' and (g/'source_registry.json').read_bytes()==before
    assert not (tmp_path/'docs/published/architecture/m1.md').exists()
    # Settings plan: values do not imply runtime authority and remain read-only.
    setting=PersistentSettingsStore(tmp_path)
    planned=setting.plan(scope='platform',scope_id='platform',key='ui.detail_level',value='expert',expected_revision=0)
    assert planned.permitted and not planned.write_performed and not setting.database.exists()
    with pytest.raises(SettingsDenied):
        setting.plan(scope='platform',scope_id='platform',key='governance.external_network',value='ALLOW',expected_revision=0)
    assert not setting.database.exists()
