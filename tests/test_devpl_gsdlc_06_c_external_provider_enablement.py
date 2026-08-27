from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jsonschema
import pytest

from devpilot_core.modeling.external_provider_enablement import (
    EnablementGateReport,
    ExternalProviderEnablementService,
    FakeConnectivityResponse,
    ProviderEnablementRequest,
    ProviderEnablementStore,
    REQUIRED_GATE_IDS,
)
from devpilot_core.modeling.provider_credentials import (
    ConsumerSessionAdapter,
    CredentialReferenceType,
    CredentialResolutionError,
    EnvApiKeyAdapter,
    ProviderCredentialReference,
)
from devpilot_core.modeling.providers import ProviderRegistry

ROOT = Path(__file__).resolve().parents[1]


def _iso(delta: timedelta) -> str:
    return (datetime.now(timezone.utc) + delta).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _request(*, provider_id: str = 'openai', route: str = 'openai-api-direct', approval_id: str | None = 'APR-06-C', missing_gate: str | None = None, expired: bool = False, notices: tuple[str, ...] = ('privacy','terms','cost','data_class'), budget: float = 1.0, mode: str = 'fake') -> ProviderEnablementRequest:
    gates = {gate: True for gate in REQUIRED_GATE_IDS}
    if missing_gate:
        gates[missing_gate] = False
    return ProviderEnablementRequest(
        provider_id=provider_id,
        access_route_id=route,
        workspace_id='workspace-06-c',
        credential_reference=ProviderCredentialReference(
            provider_id=provider_id,
            auth_adapter_id='env-api-key-future',
            reference_type=CredentialReferenceType.ENV,
            reference_name='OPENAI_API_KEY' if provider_id == 'openai' else 'GEMINI_API_KEY',
            required=True,
            source='test-reference',
        ),
        gate_report=EnablementGateReport(
            provider_id=provider_id,
            access_route_id=route,
            evidence_observed_at=_iso(timedelta(days=-2) if expired else timedelta(minutes=-5)),
            evidence_expires_at=_iso(timedelta(days=-1) if expired else timedelta(hours=1)),
            gates=gates,
            evidence_refs=('ADR-06-C-FAKE', 'R01-FRESHNESS-FAKE'),
        ),
        notices_acknowledged=notices,
        budget_limit_usd=budget,
        approval_id=approval_id,
        requested_mode=mode,
        reason='hermetic fake-vendor validation',
    )


def _service(tmp_path: Path) -> ExternalProviderEnablementService:
    return ExternalProviderEnablementService(ROOT, store=ProviderEnablementStore(tmp_path))


def _approval(request: ProviderEnablementRequest, **overrides):
    payload = {
        'approval_id': request.approval_id,
        'status': 'approved',
        'expired': False,
        'tool_id': 'model.external_provider.enable',
        'action': 'provider.enablement.external',
        'scope': {
            'provider_id': request.provider_id,
            'access_route_id': request.access_route_id,
            'workspace_id': request.workspace_id,
        },
    }
    payload.update(overrides)
    return payload


def test_credential_reference_contains_reference_not_value():
    reference = _request().credential_reference
    payload = reference.to_dict()
    assert payload['reference_name'] == 'OPENAI_API_KEY'
    assert payload['raw_secret_present'] is False
    assert 'sk_live_' not in json.dumps(payload)


def test_env_api_key_is_execution_boundary_only(monkeypatch):
    reference = _request().credential_reference
    monkeypatch.setenv('OPENAI_API_KEY', 'TEST_CREDENTIAL_VALUE_1234567890')
    material = EnvApiKeyAdapter().resolve(reference)
    assert material.secret == 'TEST_CREDENTIAL_VALUE_1234567890'
    safe = material.safe_dict()
    assert safe['secret_exposed'] is False
    assert 'sk-test-only' not in repr(material)
    assert 'sk-test-only' not in json.dumps(safe)


def test_env_api_key_missing_and_invalid_fail_closed(monkeypatch):
    reference = _request().credential_reference
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with pytest.raises(CredentialResolutionError) as missing:
        EnvApiKeyAdapter().resolve(reference)
    assert missing.value.code == 'credential-missing'
    monkeypatch.setenv('OPENAI_API_KEY', 'short')
    with pytest.raises(CredentialResolutionError) as invalid:
        EnvApiKeyAdapter().resolve(reference)
    assert invalid.value.code == 'credential-invalid'


def test_consumer_session_adapter_is_explicitly_blocked():
    reference = ProviderCredentialReference('openai','consumer-session-adapter',CredentialReferenceType.CONSUMER_SESSION,'browser-cookie',True,'test')
    with pytest.raises(CredentialResolutionError) as exc:
        ConsumerSessionAdapter().resolve(reference)
    assert exc.value.code == 'consumer-session-blocked'


def test_external_provider_versioned_config_remains_disabled():
    registry = ProviderRegistry.load(ROOT, prefer_example=True)
    external = [provider for provider in registry.providers.values() if provider.external_api]
    assert external
    assert all(provider.enabled is False for provider in external)


@pytest.mark.parametrize('case', ['gate','freshness','notices','budget','real'])
def test_enablement_plan_blocks_incomplete_preconditions(tmp_path, case):
    kwargs = {
        'missing_gate': 'rbac' if case == 'gate' else None,
        'expired': case == 'freshness',
        'notices': ('privacy','terms','cost') if case == 'notices' else ('privacy','terms','cost','data_class'),
        'budget': 0.0 if case == 'budget' else 1.0,
        'mode': 'real' if case == 'real' else 'fake',
    }
    result = _service(tmp_path).plan(_request(**kwargs))
    assert result.ok is False
    assert result.exit_code.value != 0


def test_remote_or_wrong_external_route_is_not_allowlisted(tmp_path):
    request = _request(route='remote-openai-compatible-generic')
    result = _service(tmp_path).plan(request)
    assert not result.ok
    ids = {finding.id for finding in result.findings}
    assert 'PROVIDER_ENABLEMENT_ROUTE_NOT_ALLOWLISTED' in ids or 'PROVIDER_ENABLEMENT_ROUTE_MISMATCH' in ids


def test_fake_connectivity_uses_secret_ephemerally_and_redacts(monkeypatch, tmp_path):
    secret = 'TEST_CREDENTIAL_VALUE_ABCDEFGHIJKLMNOP'
    monkeypatch.setenv('OPENAI_API_KEY', secret)
    seen = {}
    def fake_transport(**kwargs):
        seen['secret'] = kwargs['credential'].secret
        return FakeConnectivityResponse(True, 200, 'ok', 3)
    result = _service(tmp_path).connectivity_test(_request(), transport=fake_transport)
    assert result.ok
    assert seen['secret'] == secret
    rendered = json.dumps(result.data, sort_keys=True)
    assert secret not in rendered
    assert result.data['summary']['network_used'] is False
    assert result.data['summary']['external_api_used'] is False


def test_fake_connectivity_missing_key_blocks_without_exposure(monkeypatch, tmp_path):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    result = _service(tmp_path).connectivity_test(_request(), transport=lambda **_: FakeConnectivityResponse(True,200))
    assert not result.ok
    assert 'OPENAI_API_KEY' in json.dumps(result.data)
    assert 'credential' not in result.message.lower() or 'blocked' in result.message.lower()


def test_no_transport_means_real_network_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv('OPENAI_API_KEY', 'TEST_CREDENTIAL_VALUE_ABCDEFGHIJKLMNOP')
    result = _service(tmp_path).connectivity_test(_request(), transport=None)
    assert not result.ok
    assert result.data['summary']['network_used'] is False
    assert any(f.id == 'PROVIDER_CONNECTIVITY_NETWORK_DISABLED' for f in result.findings)


def test_apply_requires_owner_and_scope_matched_approval(tmp_path):
    service = _service(tmp_path)
    request = _request()
    assert not service.apply_enable(request, approval=None, actor_id='user-1', role_at_execution='owner').ok
    assert not service.apply_enable(request, approval=_approval(request), actor_id='user-1', role_at_execution='developer').ok
    bad = _approval(request)
    bad['scope'] = {**bad['scope'], 'workspace_id': 'other-workspace'}
    assert not service.apply_enable(request, approval=bad, actor_id='user-1', role_at_execution='owner').ok


def test_apply_persists_reference_only_and_fake_mode_never_enables_network(tmp_path):
    service = _service(tmp_path)
    request = _request()
    result = service.apply_enable(request, approval=_approval(request), actor_id='owner-1', role_at_execution='owner')
    assert result.ok
    state_path = tmp_path / '.devpilot/runtime/provider_enablement/state.json'
    raw = state_path.read_text(encoding='utf-8')
    assert 'OPENAI_API_KEY' in raw
    assert 'sk_live_' not in raw
    state = json.loads(raw)['providers']['openai']
    assert state['configured_enabled'] is True
    assert state['runtime_network_enabled'] is False
    assert state['raw_secret_present'] is False


def test_disable_and_revoke_are_owner_only_audited_kill_switches(tmp_path):
    service = _service(tmp_path)
    request = _request()
    assert service.apply_enable(request, approval=_approval(request), actor_id='owner-1', role_at_execution='owner').ok
    assert not service.disable(provider_id='openai',actor_id='dev-1',role_at_execution='developer',reason='no',revoke=False).ok
    disabled = service.disable(provider_id='openai',actor_id='owner-1',role_at_execution='owner',reason='kill-switch',revoke=False)
    assert disabled.ok and disabled.data['state']['runtime_network_enabled'] is False
    revoked = service.disable(provider_id='openai',actor_id='owner-1',role_at_execution='owner',reason='revoke',revoke=True)
    assert revoked.ok and revoked.data['state']['credential_reference'] is None
    audit = (tmp_path / '.devpilot/runtime/provider_enablement/audit.jsonl').read_text(encoding='utf-8')
    assert 'provider.enablement.enabled' in audit
    assert 'provider.enablement.disabled' in audit
    assert 'provider.enablement.revoked' in audit
    assert 'sk_live_' not in audit


def test_policy_and_contract_schemas_validate_current_artifacts():
    pairs = [
        ('docs/schemas/external_provider_enablement_policy.schema.json','.devpilot/modeling/external_provider_enablement_policy.json'),
    ]
    for schema_path, instance_path in pairs:
        schema = json.loads((ROOT / schema_path).read_text(encoding='utf-8'))
        instance = json.loads((ROOT / instance_path).read_text(encoding='utf-8'))
        jsonschema.Draft202012Validator(schema).validate(instance)
    ref_schema = json.loads((ROOT / 'docs/schemas/provider_credential_reference.schema.json').read_text(encoding='utf-8'))
    gate_schema = json.loads((ROOT / 'docs/schemas/provider_enablement_gate_report.schema.json').read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator(ref_schema).validate(_request().credential_reference.to_dict())
    jsonschema.Draft202012Validator(gate_schema).validate(_request().gate_report.to_dict())


def test_server_rbac_routes_are_human_session_bound_and_deny_legacy_token():
    payload = json.loads((ROOT / '.devpilot/identity/server_rbac_policy_catalog.json').read_text(encoding='utf-8'))
    targets = [item for item in payload['route_policies'] if item.get('operation','').startswith('settings.providers.') and ('enablement' in item.get('operation','') or item.get('operation') == 'settings.providers.connectivity_test')]
    assert len(targets) == 6
    assert all(item['human_session_required'] is True for item in targets)
    assert all(item['legacy_token_allowed'] is False for item in targets)
    mutation = [item for item in targets if item.get('method') == 'POST']
    assert mutation and all(item['allowed_roles'] == ['owner'] for item in mutation)

def test_external_enablement_api_rejects_legacy_token_authority():
    from fastapi.testclient import TestClient
    from devpilot_core.interfaces.api import create_app
    client = TestClient(create_app(ROOT, api_token='legacy-test-token-06-c'))
    response = client.get(
        '/api/v1/settings/providers/enablement',
        headers={'X-DevPilot-Token':'legacy-test-token-06-c','Origin':'http://127.0.0.1:5173'},
    )
    assert response.status_code in {401,403}
    assert response.json()['ok'] is False
