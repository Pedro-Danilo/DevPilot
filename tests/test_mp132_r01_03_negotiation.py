from dataclasses import replace
import pytest
from devpilot_core.modeling.contracts import ModelCallRequest, ModelProviderConfig, ModelProviderKind, ModelTask
from devpilot_core.modeling.negotiation import (
    AdapterCapabilities, CapabilityRequest, LocalStubModelAdapter,
    OfflineCapabilityNegotiator, NegotiationBlocked, default_offline_negotiator,
)
from devpilot_core.modeling.providers import DEFAULT_PROVIDER_CONFIGS


def cfg(name):
    return next(p for p in DEFAULT_PROVIDER_CONFIGS if p.provider_id == name)


def test_mock_explicit_generation_no_network():
    n=default_offline_negotiator()
    decision=n.negotiate(CapabilityRequest("mock",ModelTask.GENERATE))
    assert decision.allowed and decision.reason=="ELIGIBLE" and decision.fallback is None
    result=n.execute_mock(CapabilityRequest("mock", ModelTask.GENERATE),ModelCallRequest(task=ModelTask.GENERATE,prompt="hola",provider="mock"))
    assert result.ok and not result.external_api_used and result.cost_estimate_usd==0

@pytest.mark.parametrize("task",[ModelTask.GENERATE,ModelTask.CLASSIFY,ModelTask.EMBED])
def test_mock_tasks(task):
    n=default_offline_negotiator(); req=ModelCallRequest(task=task,provider="mock",text="bug",labels=("bug",))
    assert n.execute_mock(CapabilityRequest("mock",task),req).ok

@pytest.mark.parametrize("kwargs,reason",[
    ({"tools":True},"TOOLS_UNSUPPORTED"),({"streaming":True},"STREAMING_UNSUPPORTED"),
    ({"timeout_seconds":31},"TIMEOUT_UNSUPPORTED"),({"timeout_seconds":0},"TIMEOUT_UNSUPPORTED")])
def test_negotiation_rejects_unavailable_features(kwargs,reason):
    n=default_offline_negotiator();d=n.negotiate(CapabilityRequest("mock", ModelTask.GENERATE,**kwargs))
    assert not d.allowed and d.reason==reason and d.fallback is None

def test_local_reports_supported_but_not_ready_and_no_silent_fallback():
    n=default_offline_negotiator();r=n.negotiate(CapabilityRequest("ollama", ModelTask.GENERATE))
    assert not r.allowed and r.reason=="NOT_CONFIGURED" and r.state["SUPPORTED"]==["generate"]
    assert r.state["ELIGIBLE"] is False and r.fallback is None
    with pytest.raises(NegotiationBlocked):n.execute_mock(CapabilityRequest("ollama",ModelTask.GENERATE),ModelCallRequest(task=ModelTask.GENERATE,provider="ollama"))

def test_local_stub_never_contacts_server():
    stub=LocalStubModelAdapter(cfg("ollama"))
    for t in ModelTask:
        r=getattr(stub,t.value)(ModelCallRequest(task=t,provider="ollama"))
        assert not r.ok and not r.external_api_used and r.metadata["network_used"] is False

def test_unknown_provider_fails_closed():
    n=default_offline_negotiator(); r=n.negotiate(CapabilityRequest("gemini",ModelTask.GENERATE))
    assert not r.allowed and r.reason=="UNKNOWN_PROVIDER" and r.fallback is None

def test_external_api_denied_even_when_config_enabled():
    api=replace(cfg("openai"),enabled=True)
    p=AdapterCapabilities("openai",frozenset({ModelTask.GENERATE}),configured=True,healthy=True,evaluated=True,eligible=True)
    with pytest.raises(ValueError,match="EXTERNAL_PROVIDER_DENIED"):
        OfflineCapabilityNegotiator((api,),(p,))

@pytest.mark.parametrize("url",["http://example.com:1234","https://localhost:1234","http://localhost:1234?a=b","http://user:pass@localhost:1234"])
def test_local_stub_rejects_unsafe_endpoint(url):
    with pytest.raises(ValueError,match="LOCAL_ENDPOINT_LOOPBACK_REQUIRED"):
        LocalStubModelAdapter(replace(cfg("ollama"),endpoint=url))

def test_eligibility_cannot_skip_health_or_evaluation():
    with pytest.raises(ValueError,match="eligible-requires"):
        AdapterCapabilities("mock",frozenset(ModelTask),configured=True,healthy=False,evaluated=True,eligible=True)

def test_no_local_stub_marked_eligible():
    c=replace(cfg("ollama"),enabled=True)
    p=AdapterCapabilities("ollama",frozenset({ModelTask.GENERATE}),configured=True,healthy=True,evaluated=True,eligible=True)
    with pytest.raises(ValueError,match="LOCAL_STUB_CANNOT"):
        OfflineCapabilityNegotiator((c,),(p,))

def test_cannot_claim_configured_when_disabled():
    p=AdapterCapabilities("ollama",frozenset({ModelTask.GENERATE}),configured=True)
    with pytest.raises(ValueError,match="CONFIGURED_BUT_PROVIDER_DISABLED"):
        OfflineCapabilityNegotiator((cfg("ollama"),),(p,))

def test_duplicate_identity_blocked():
    p=AdapterCapabilities("mock",frozenset(ModelTask),configured=True,healthy=True,evaluated=True,eligible=True)
    with pytest.raises(ValueError,match="DUPLICATE_PROVIDER_ID"):
        OfflineCapabilityNegotiator((cfg("mock"),cfg("mock")),(p,))

def test_task_mismatch_never_executes():
    n=default_offline_negotiator()
    with pytest.raises(NegotiationBlocked,match="REQUEST_IDENTITY_MISMATCH"):
        n.execute_mock(CapabilityRequest("mock", ModelTask.GENERATE),ModelCallRequest(task=ModelTask.CLASSIFY,provider="mock"))

def test_capability_status_snapshot_distinct():
    p=default_offline_negotiator().negotiate(CapabilityRequest("mock", ModelTask.GENERATE)).state
    assert (p["CONFIGURED"],p["HEALTHY"],p["EVALUATED"],p["ELIGIBLE"]) == (True,True,True,True)
