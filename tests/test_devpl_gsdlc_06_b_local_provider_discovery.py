from __future__ import annotations

import json
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
import jsonschema

from devpilot_core.modeling import LocalEndpointPolicy, LocalProviderDiscoveryOptions, LocalProviderDiscoveryService, ModelAdapterRouter, ModelRouterConfig
from devpilot_core.modeling.local_endpoint_policy import LocalHttpLimits, bounded_json_request, evaluate_loopback_endpoint
from devpilot_core.application.settings_service import SettingsApplicationService


def _write_workspace(root: Path, *, endpoint: str, enabled: bool = False, max_bytes: int = 4096, timeout: float = 0.15) -> Path:
    (root / '.devpilot' / 'modeling').mkdir(parents=True, exist_ok=True)
    (root / 'docs').mkdir(parents=True, exist_ok=True)
    (root / 'pyproject.toml').write_text("[project]\nname='gsdlc-06-b-fixture'\n", encoding='utf-8')
    (root / '.devpilot' / 'providers.yaml').write_text(
        f'''schema_version: "2.0"
providers:
  - id: "mock"
    kind: "mock"
    enabled: true
    default_model: "mock-deterministic-v1"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "implemented"
  - id: "ollama"
    kind: "local"
    enabled: false
    default_model: "fake-ollama"
    endpoint: "{endpoint}"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "implemented-initial"
  - id: "lmstudio"
    kind: "local"
    enabled: false
    default_model: "fake-lmstudio"
    endpoint: "{endpoint}"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "implemented-initial"
  - id: "openai-compatible-local"
    kind: "local"
    enabled: {str(enabled).lower()}
    default_model: "fake-openai-compatible"
    endpoint: "{endpoint}"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "implemented-initial"
''', encoding='utf-8')
    port = int(endpoint.rsplit(':', 1)[1])
    policy = {
        'schema_id': 'devpilot.gsdlc06b.local_provider_endpoint_policy.v1',
        'schema_version': '1.0.0',
        'defaults': {'timeout_seconds': timeout, 'max_response_bytes': max_bytes, 'max_models': 4, 'follow_redirects': False},
        'providers': [
            {'provider_id': 'ollama', 'port_mode': 'configured-loopback', 'require_explicit_endpoint_allowlist': False, 'timeout_seconds': timeout, 'max_response_bytes': max_bytes, 'max_models': 4},
            {'provider_id': 'lmstudio', 'port_mode': 'configured-loopback', 'require_explicit_endpoint_allowlist': False, 'timeout_seconds': timeout, 'max_response_bytes': max_bytes, 'max_models': 4},
            {'provider_id': 'openai-compatible-local', 'port_mode': 'explicit-allowlist', 'allowed_ports': [port], 'require_explicit_endpoint_allowlist': True, 'allowlisted_endpoints': [endpoint], 'timeout_seconds': timeout, 'max_response_bytes': max_bytes, 'max_models': 4},
        ],
        'invariants': {'discovery_enables_provider': False, 'raw_secrets_allowed': False},
    }
    (root / '.devpilot' / 'modeling' / 'local_provider_endpoint_policy.json').write_text(json.dumps(policy, indent=2) + '\n', encoding='utf-8')
    return root


class _Handler(BaseHTTPRequestHandler):
    mode = 'success'
    delay = 0.0
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return
    def do_GET(self) -> None:  # noqa: N802
        if self.delay:
            time.sleep(self.delay)
        if self.mode == 'redirect':
            self.send_response(302); self.send_header('Location', 'http://example.com/v1/models'); self.end_headers(); return
        if self.mode == 'wrong-content-type':
            body=b'{}'; self.send_response(200); self.send_header('Content-Type','text/plain'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        if self.mode == 'oversized':
            body=json.dumps({'data':[{'id':'x'*5000}]}).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        if self.path == '/api/tags': payload={'models':[{'name':'ollama-a'}]}
        elif self.path == '/v1/models': payload={'data':'bad'} if self.mode == 'malformed' else {'data':[{'id':'local-a'},{'id':'local-b'}]}
        else: self.send_error(404); return
        self._json(payload)
    def do_POST(self) -> None:  # noqa: N802
        raw=self.rfile.read(int(self.headers.get('Content-Length','0') or '0')); json.loads(raw.decode() or '{}')
        if self.path == '/v1/chat/completions': self._json({'choices':[{'message':{'content':'local answer'}}], 'usage':{'total_tokens':3}}); return
        if self.path == '/v1/embeddings': self._json({'data':[{'embedding':[0.1,0.2]}], 'usage':{'total_tokens':2}}); return
        self.send_error(404)
    def _json(self,payload):
        body=json.dumps(payload).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)


@contextmanager
def _server(mode='success', delay=0.0):
    handler=type('CaseHandler',(_Handler,),{'mode':mode,'delay':delay})
    srv=HTTPServer(('127.0.0.1',0),handler); t=threading.Thread(target=srv.serve_forever,daemon=True); t.start()
    try: yield f'http://127.0.0.1:{srv.server_address[1]}'
    finally: srv.shutdown(); srv.server_close(); t.join(timeout=2)


def test_endpoint_policy_accepts_literal_and_ipv6_loopback_and_rejects_host_tricks():
    assert evaluate_loopback_endpoint(provider_id='x', endpoint='http://127.0.0.1:11434').ok
    assert evaluate_loopback_endpoint(provider_id='x', endpoint='http://[::1]:11434').ok
    assert evaluate_loopback_endpoint(provider_id='x', endpoint='http://localhost:11434').ok
    for endpoint in ['https://api.openai.com','http://localhost.evil:11434','http://127.0.0.1.nip.io:11434','http://localhost.:11434','ftp://127.0.0.1:11434','http://user@localhost:11434','http://localhost:11434/path','http://localhost:11434?x=1']:
        assert not evaluate_loopback_endpoint(provider_id='x', endpoint=endpoint).ok, endpoint


def test_generic_route_requires_explicit_allowlist(tmp_path: Path):
    with _server() as endpoint:
        root=_write_workspace(tmp_path, endpoint=endpoint)
        policy=json.loads((root/'.devpilot/modeling/local_provider_endpoint_policy.json').read_text())
        policy['providers'][-1]['allowlisted_endpoints']=[]
        (root/'.devpilot/modeling/local_provider_endpoint_policy.json').write_text(json.dumps(policy),encoding='utf-8')
        decision=LocalEndpointPolicy.load(root).evaluate('openai-compatible-local',endpoint)
        assert decision.ok is False and decision.reason == 'endpoint-not-explicitly-allowlisted'


def test_discovery_success_is_bounded_and_does_not_enable_provider(tmp_path: Path):
    with _server() as endpoint:
        root=_write_workspace(tmp_path, endpoint=endpoint, enabled=False)
        result=LocalProviderDiscoveryService(root, LocalProviderDiscoveryOptions(probe=True, provider_ids=('openai-compatible-local',))).build()
        row=result.data['report']['providers'][0]
        assert result.ok is True
        assert row['configured'] is True and row['reachable'] is True and row['healthy'] is True and row['model_discovered'] is True
        assert row['enabled'] is False and row['discovery_enables_provider'] is False
        assert result.data['summary']['enabled_total'] == 0
        assert result.data['summary']['external_api_used'] is False


@pytest.mark.parametrize('mode,expected', [('malformed','model-list-malformed'),('wrong-content-type','content-type-invalid'),('oversized','payload-too-large'),('redirect','redirect-forbidden')])
def test_discovery_fails_closed_for_bad_local_responses(tmp_path: Path, mode: str, expected: str):
    with _server(mode=mode) as endpoint:
        root=_write_workspace(tmp_path, endpoint=endpoint, max_bytes=1024)
        result=LocalProviderDiscoveryService(root, LocalProviderDiscoveryOptions(probe=True, provider_ids=('openai-compatible-local',))).build()
        row=result.data['report']['providers'][0]
        assert result.ok is True
        assert row['healthy'] is False and row['model_discovered'] is False
        assert row['error_type'] == expected
        assert row['fallback']['provider_id'] == 'mock' and row['fallback']['explicit'] is True


def test_discovery_timeout_is_bounded_and_redacted(tmp_path: Path):
    with _server(delay=0.25) as endpoint:
        root=_write_workspace(tmp_path, endpoint=endpoint, timeout=0.05)
        started=time.monotonic(); result=LocalProviderDiscoveryService(root, LocalProviderDiscoveryOptions(probe=True, provider_ids=('openai-compatible-local',))).build(); elapsed=time.monotonic()-started
        row=result.data['report']['providers'][0]
        assert elapsed < 1.0
        assert row['healthy'] is False and row['error_type'] in {'timeout','connection_error'}
        serialized=json.dumps(result.to_dict())
        assert 'OPENAI_API_KEY' not in serialized and 'sk-' not in serialized


def test_redirect_is_never_followed_to_remote(tmp_path: Path):
    with _server(mode='redirect') as endpoint:
        root=_write_workspace(tmp_path, endpoint=endpoint)
        policy=LocalEndpointPolicy.load(root); decision=policy.evaluate('openai-compatible-local',endpoint)
        with pytest.raises(Exception) as exc:
            bounded_json_request(provider_id='openai-compatible-local', endpoint_decision=decision, path='/v1/models', limits=LocalHttpLimits(timeout_seconds=.1,max_response_bytes=4096,max_models=4))
        assert getattr(exc.value,'code',None) == 'redirect-forbidden'


def test_generic_adapter_and_explicit_mock_fallback(tmp_path: Path):
    with _server(mode='malformed') as endpoint:
        root=_write_workspace(tmp_path, endpoint=endpoint, enabled=True)
        result=ModelAdapterRouter(root, config=ModelRouterConfig(local_timeout_seconds=.1, fallback_to_mock_on_local_unavailable=True)).generate(prompt='safe local request', provider='openai-compatible-local')
        # Generate endpoint itself succeeds in this fake; switch to unavailable port to test explicit fallback.
        assert result.ok is True
    dead='http://127.0.0.1:9'; root2=_write_workspace(tmp_path/'dead', endpoint=dead, enabled=True)
    result2=ModelAdapterRouter(root2, config=ModelRouterConfig(local_timeout_seconds=.05, fallback_to_mock_on_local_unavailable=True)).generate(prompt='safe fallback request', provider='openai-compatible-local')
    assert result2.ok is True
    assert result2.data['summary']['fallback_applied'] is True
    assert result2.data['fallback']['reason'] in {'connection_error','timeout'}
    assert result2.data['fallback']['to_provider'] == 'mock'


def test_static_discovery_performs_no_probe_and_exposes_no_secret(tmp_path: Path):
    root=_write_workspace(tmp_path, endpoint='http://127.0.0.1:8000')
    result=LocalProviderDiscoveryService(root, LocalProviderDiscoveryOptions(probe=False, provider_ids=('openai-compatible-local',))).build()
    row=result.data['report']['providers'][0]
    assert result.ok and row['probe_attempted'] is False and row['reachable'] is None and row['healthy'] is None
    serialized=json.dumps(result.to_dict())
    assert 'OPENAI_API_KEY' not in serialized and 'sk-' not in serialized


def test_settings_projection_exposes_static_redacted_local_health_metadata(tmp_path: Path):
    root=_write_workspace(tmp_path, endpoint='http://127.0.0.1:8000')
    result=SettingsApplicationService(root).providers()
    assert result.ok is True
    assert result.data['summary']['local_provider_health_available'] is True
    assert result.data['summary']['local_provider_health_probe_requested'] is False
    report=result.data['local_provider_health']
    assert report['summary']['probe_requested'] is False
    assert report['summary']['external_api_used'] is False
    row=next(x for x in report['providers'] if x['provider_id']=='openai-compatible-local')
    assert row['requires_api_key'] is False
    assert report['safety']['raw_secrets_exposed'] is False
    serialized=json.dumps(result.to_dict())
    assert 'sk-' not in serialized and 'Bearer ' not in serialized


def test_06_b_source_policy_and_static_health_report_validate_against_schemas():
    root=Path(__file__).resolve().parents[1]
    policy=json.loads((root/'.devpilot/modeling/local_provider_endpoint_policy.json').read_text(encoding='utf-8'))
    policy_schema=json.loads((root/'docs/schemas/local_provider_endpoint_policy.schema.json').read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator(policy_schema).validate(policy)
    report=LocalProviderDiscoveryService(root, LocalProviderDiscoveryOptions(probe=False)).build().data['report']
    report_schema=json.loads((root/'docs/schemas/gsdlc_06_b_local_provider_health_report.schema.json').read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator(report_schema).validate(report)
    assert report['status']=='PASS' and report['summary']['providers_total']==3
