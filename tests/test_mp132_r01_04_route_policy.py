"""R01-04: policy planning only; never make model/network/provider calls."""
from pathlib import Path
import pytest
from devpilot_core.generation import (
    FallbackQuality, TaskRouteRule, WorkloadEstimate, GenerationRoutePolicy,
    GenerationRequest, GenerationRouteResolver, ProviderSelectionPolicy,
    ProviderClass, ProviderAvailability, ProviderHealthSnapshot,
)
ROOT=Path(__file__).resolve().parents[1]
D=ProviderClass.DETERMINISTIC
L=ProviderClass.LOCAL_MODEL
E=ProviderClass.EXTERNAL_MODEL

def request(preferred='deterministic', allowed=None, *, task='architecture', budget=None):
    return GenerationRequest(request_id='r01-04-probe',artifact_type=task,profile_version='architecture-v1',
        dependency_profile_version='architecture-deps-v1',upstream_hashes={'requirements':'a'*64},
        preferred_route=preferred,allowed_routes=allowed or (preferred,),
        policy_snapshot={'privacy_class':'internal','offline_required':True},budget_snapshot=budget or {})

def rule(mode=FallbackQuality.EQUIVALENT, *, classes=(D,L), cost=0.0):
    return TaskRouteRule('review',('architecture',),classes,mode,
        equivalence_evidence='approved-fixture-equivalence-001' if mode==FallbackQuality.EQUIVALENT else None,
        max_input_tokens=100,max_output_tokens=40,max_cost_usd=cost,max_timeout_seconds=10)

def policy(classes=(D,L), fallback=True):
    return ProviderSelectionPolicy(allowed_provider_classes=classes,
        execution_enabled_classes=(D,L),allow_local_to_deterministic_fallback=fallback)

def estimate(tokens=10,cost=0.0,timeout=5):return WorkloadEstimate(tokens,10,cost,timeout)

def planner(r=None):return GenerationRoutePolicy(GenerationRouteResolver(ROOT), {'review':r or rule()})

def health(available=False):
    return ProviderHealthSnapshot(access_route_id='ollama-localhost-mistral7b',provider_id='ollama',
        provider_class=L,model_id='mistral:7b',availability=ProviderAvailability.AVAILABLE if available else ProviderAvailability.UNAVAILABLE,
        configured=True,enabled=True,structured_output_supported=True,locality='loopback',source='fixture/no-probe',benchmark_score=1.0)

def test_default_deny_unknown_task_and_artifact():
    p=planner()
    assert p.plan(request(),task_type='unknown',estimate=estimate(),selection_policy=policy()).reason=='TASK_NOT_REGISTERED'
    assert p.plan(request(task='requirements'),task_type='review',estimate=estimate(),selection_policy=policy()).reason=='ARTIFACT_NOT_ALLOWED_FOR_TASK'

def test_deterministic_route_offline_with_trace():
    d=planner().plan(request(),task_type='review',estimate=estimate(),selection_policy=policy())
    assert d.status=='SELECTED_DETERMINISTIC' and d.execution_allowed
    assert not d.model_call_performed and not d.network_used and not d.external_api_used
    assert d.rule_sha256 and d.request_sha256 and d.gateway_route_sha256
    assert d.to_dict()['trace'][-1]=='gateway:selected'

def test_external_denied_before_any_resolver():
    class Trap:
        def resolve(self,*a,**kw):raise AssertionError('provider gate reached')
    p=GenerationRoutePolicy(Trap(),{'review':rule(classes=(D,L,E))})
    d=p.plan(request('external-model'),task_type='review',estimate=estimate(),selection_policy=policy((D,L,E)))
    assert d.reason=='EXTERNAL_EGRESS_DENIED'

def test_negative_cost_token_timeout_and_invalid_estimates():
    p=planner();req=request()
    for workload,reason in ((estimate(tokens=101),'TOKEN_BUDGET_EXCEEDED'),
        (estimate(cost=1.1),'COST_BUDGET_EXCEEDED'),(estimate(timeout=11),'TIMEOUT_BUDGET_EXCEEDED')):
        assert p.plan(req,task_type='review',estimate=workload,selection_policy=policy()).reason==reason
    for kw in ({'input_tokens':-1},{'cost_usd':float('nan')},{'timeout_seconds':float('inf')}):
        with pytest.raises(ValueError):WorkloadEstimate(**(dict(input_tokens=0,output_tokens=0,cost_usd=0.0,timeout_seconds=1.0) | kw))

def test_request_budget_stricter_and_invalid():
    p=planner(rule(cost=10.0))
    d=p.plan(request(budget={'max_cost_usd':0.2}),task_type='review',estimate=estimate(cost=0.3),selection_policy=policy())
    assert d.reason=='REQUEST_BUDGET_EXCEEDED'
    d=p.plan(request(budget={'max_input_tokens':float('nan')}),task_type='review',estimate=estimate(),selection_policy=policy())
    assert d.reason=='INVALID_REQUEST_BUDGET'

def test_local_unavailable_requires_explicit_fallback_consent():
    req=request('local-model',('local-model','deterministic'))
    d=planner().plan(req,task_type='review',estimate=estimate(),selection_policy=policy(),health_snapshots=(health(),))
    assert d.status=='DENIED' and d.reason=='FALLBACK_CONSENT_MISSING'

def test_equivalent_requires_documented_evidence_and_consent():
    with pytest.raises(ValueError,match='EQUIVALENCE_EVIDENCE_REQUIRED'):
        TaskRouteRule('review',('architecture',),fallback_quality=FallbackQuality.EQUIVALENT)
    req=request('local-model',('local-model','deterministic'))
    d=planner().plan(req,task_type='review',estimate=estimate(),selection_policy=policy(),health_snapshots=(health(),),fallback_consent=True)
    assert d.status=='FALLBACK_EQUIVALENT' and d.fallback_quality=='EQUIVALENT' and d.fallback_reason
    assert not d.model_call_performed and not d.network_used

def test_reduced_fallback_has_quality_downgrade_trace():
    req=request('local-model',('local-model','deterministic'))
    d=planner(rule(FallbackQuality.REDUCED)).plan(req,task_type='review',estimate=estimate(),selection_policy=policy(),health_snapshots=(health(),),fallback_consent=True)
    assert d.status=='FALLBACK_REDUCED' and 'local-rejection:' in '|'.join(d.trace)

def test_model_required_blocks_fallback_and_deterministic_route():
    p=planner(rule(FallbackQuality.MODEL_REQUIRED))
    req=request('local-model',('local-model','deterministic'))
    assert p.plan(req,task_type='review',estimate=estimate(),selection_policy=policy(),health_snapshots=(health(),),fallback_consent=True).reason=='MODEL_REQUIRED_NO_FALLBACK'
    assert p.plan(request(),task_type='review',estimate=estimate(),selection_policy=policy()).reason=='MODEL_REQUIRED_DETERMINISTIC_NOT_EQUIVALENT'

def test_local_route_never_marked_executable_even_with_enabled_selection_policy():
    req=request('local-model',('local-model','deterministic'))
    d=planner().plan(req,task_type='review',estimate=estimate(),selection_policy=policy(),health_snapshots=(health(True),))
    assert d.status in {'PLANNED_LOCAL_NOT_EXECUTABLE','DENIED'}
    assert not d.execution_allowed and not d.model_call_performed

def test_no_implicit_fallback_if_task_disallows_deterministic():
    req=request('local-model',('local-model','deterministic'))
    p=planner(rule(FallbackQuality.REDUCED,classes=(L,)))
    d=p.plan(req,task_type='review',estimate=estimate(),selection_policy=policy(),health_snapshots=(health(),),fallback_consent=True)
    assert d.reason=='FALLBACK_CLASS_NOT_ALLOWED'

def test_reject_policy_mutation_and_class_unknown():
    d=planner().plan(request('foo'),task_type='review',estimate=estimate(),selection_policy=policy())
    assert d.status=='DENIED'
    assert planner().rules['review'].allowed_classes==(D,L)


def test_request_timeout_stricter_than_task_and_mode_guard():
    d=planner().plan(request(budget={'max_timeout_seconds':1}),task_type='review',estimate=estimate(timeout=5),selection_policy=policy())
    assert d.reason=='REQUEST_BUDGET_EXCEEDED'
    with pytest.raises(ValueError,match='FALLBACK_MODE_INVALID'):
        TaskRouteRule('review',('architecture',),fallback_quality='EQUIVALENT')
