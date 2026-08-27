from __future__ import annotations

import ipaddress
import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

DEFAULT_POLICY_PATH = Path('.devpilot/modeling/local_provider_endpoint_policy.json')
DEFAULT_MAX_RESPONSE_BYTES = 262_144
DEFAULT_MAX_MODELS = 128
DEFAULT_TIMEOUT_SECONDS = 1.5


class LocalEndpointPolicyError(ValueError):
    """Fail-closed endpoint/payload policy error for local model routes."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class LocalEndpointDecision:
    ok: bool
    provider_id: str
    normalized_endpoint: str | None
    host: str | None
    port: int | None
    scheme: str | None
    reason: str
    endpoint_class: str = 'local-loopback'
    explicit_allowlist_required: bool = False
    explicit_allowlist_matched: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            'ok': self.ok,
            'provider_id': self.provider_id,
            'normalized_endpoint': self.normalized_endpoint,
            'host': self.host,
            'port': self.port,
            'scheme': self.scheme,
            'reason': self.reason,
            'endpoint_class': self.endpoint_class,
            'explicit_allowlist_required': self.explicit_allowlist_required,
            'explicit_allowlist_matched': self.explicit_allowlist_matched,
        }


@dataclass(frozen=True)
class LocalHttpLimits:
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES
    max_models: int = DEFAULT_MAX_MODELS


class LocalEndpointPolicy:
    """Typed loopback-only endpoint policy for GSDLC-06-B.

    No DNS-based hostname is treated as local. ``localhost`` and literal loopback
    IPs are the only accepted host forms. Generic OpenAI-compatible routes must
    match an explicit allowlisted base endpoint from the policy.
    """

    def __init__(self, payload: dict[str, Any], *, source_path: str = 'in-memory') -> None:
        self.payload = payload
        self.source_path = source_path
        defaults = payload.get('defaults') if isinstance(payload.get('defaults'), dict) else {}
        self.default_limits = LocalHttpLimits(
            timeout_seconds=max(0.05, float(defaults.get('timeout_seconds', DEFAULT_TIMEOUT_SECONDS))),
            max_response_bytes=max(1024, int(defaults.get('max_response_bytes', DEFAULT_MAX_RESPONSE_BYTES))),
            max_models=max(1, int(defaults.get('max_models', DEFAULT_MAX_MODELS))),
        )

    @classmethod
    def load(cls, root: Path, path: str | Path = DEFAULT_POLICY_PATH) -> 'LocalEndpointPolicy':
        root = Path(root).resolve()
        rel = Path(path)
        payload = json.loads((root / rel).read_text(encoding='utf-8'))
        return cls(payload, source_path=rel.as_posix())

    def provider_rule(self, provider_id: str) -> dict[str, Any]:
        providers = self.payload.get('providers') if isinstance(self.payload.get('providers'), list) else []
        for row in providers:
            if isinstance(row, dict) and str(row.get('provider_id', '')).lower() == provider_id.lower():
                return row
        return {}

    def limits_for(self, provider_id: str) -> LocalHttpLimits:
        rule = self.provider_rule(provider_id)
        return LocalHttpLimits(
            timeout_seconds=max(0.05, float(rule.get('timeout_seconds', self.default_limits.timeout_seconds))),
            max_response_bytes=max(1024, int(rule.get('max_response_bytes', self.default_limits.max_response_bytes))),
            max_models=max(1, int(rule.get('max_models', self.default_limits.max_models))),
        )

    def evaluate(self, provider_id: str, endpoint: str | None) -> LocalEndpointDecision:
        rule = self.provider_rule(provider_id)
        require_allowlist = bool(rule.get('require_explicit_endpoint_allowlist', False))
        allowed_endpoints = tuple(str(v) for v in rule.get('allowlisted_endpoints', []) if isinstance(v, str))
        allowed_ports = tuple(int(v) for v in rule.get('allowed_ports', []) if isinstance(v, int) and 1 <= v <= 65535)
        port_mode = str(rule.get('port_mode') or 'configured-loopback')
        decision = evaluate_loopback_endpoint(
            provider_id=provider_id,
            endpoint=endpoint,
            require_explicit_allowlist=require_allowlist,
            allowed_endpoints=allowed_endpoints,
            allowed_ports=allowed_ports if port_mode == 'explicit-allowlist' else (),
        )
        return decision


def evaluate_loopback_endpoint(
    *,
    provider_id: str,
    endpoint: str | None,
    require_explicit_allowlist: bool = False,
    allowed_endpoints: tuple[str, ...] = (),
    allowed_ports: tuple[int, ...] = (),
) -> LocalEndpointDecision:
    if not endpoint or not str(endpoint).strip():
        return _deny(provider_id, 'endpoint-missing', require_explicit_allowlist)
    value = str(endpoint).strip()
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except (ValueError, TypeError):
        return _deny(provider_id, 'endpoint-parse-error', require_explicit_allowlist)
    scheme = parsed.scheme.lower()
    if scheme not in {'http', 'https'}:
        return _deny(provider_id, 'scheme-not-http-s', require_explicit_allowlist, scheme=scheme)
    if parsed.username is not None or parsed.password is not None:
        return _deny(provider_id, 'userinfo-forbidden', require_explicit_allowlist, scheme=scheme)
    if parsed.query or parsed.fragment:
        return _deny(provider_id, 'query-or-fragment-forbidden', require_explicit_allowlist, scheme=scheme)
    if parsed.path not in {'', '/'}:
        return _deny(provider_id, 'base-path-forbidden', require_explicit_allowlist, scheme=scheme)
    raw_host = parsed.hostname
    if not raw_host:
        return _deny(provider_id, 'host-missing', require_explicit_allowlist, scheme=scheme)
    host = raw_host.lower()
    if host.endswith('.') or '%' in host:
        return _deny(provider_id, 'ambiguous-host-forbidden', require_explicit_allowlist, scheme=scheme, host=host)
    if not _is_explicit_loopback(host):
        return _deny(provider_id, 'non-loopback-host', require_explicit_allowlist, scheme=scheme, host=host)
    if port is None:
        port = 443 if scheme == 'https' else 80
    if not (1 <= int(port) <= 65535):
        return _deny(provider_id, 'port-out-of-range', require_explicit_allowlist, scheme=scheme, host=host, port=port)
    if allowed_ports and int(port) not in allowed_ports:
        return _deny(provider_id, 'port-not-allowlisted', require_explicit_allowlist, scheme=scheme, host=host, port=port)
    normalized_host = f'[{host}]' if ':' in host else host
    default_port = 443 if scheme == 'https' else 80
    netloc = normalized_host if int(port) == default_port else f'{normalized_host}:{port}'
    normalized = urlunsplit((scheme, netloc, '', '', ''))
    normalized_allowlist = {_normalize_allowlist_value(item) for item in allowed_endpoints}
    matched = normalized in normalized_allowlist
    if require_explicit_allowlist and not matched:
        return _deny(provider_id, 'endpoint-not-explicitly-allowlisted', True, scheme=scheme, host=host, port=port)
    return LocalEndpointDecision(
        ok=True,
        provider_id=provider_id,
        normalized_endpoint=normalized,
        host=host,
        port=int(port),
        scheme=scheme,
        reason='allowlisted-loopback' if require_explicit_allowlist else 'configured-loopback',
        explicit_allowlist_required=require_explicit_allowlist,
        explicit_allowlist_matched=matched if require_explicit_allowlist else False,
    )


def bounded_json_request(
    *,
    provider_id: str,
    endpoint_decision: LocalEndpointDecision,
    path: str,
    method: str = 'GET',
    payload: dict[str, Any] | None = None,
    limits: LocalHttpLimits | None = None,
) -> tuple[int, dict[str, Any]]:
    if not endpoint_decision.ok or not endpoint_decision.normalized_endpoint:
        raise LocalEndpointPolicyError('endpoint-policy-block', endpoint_decision.reason)
    if not path.startswith('/') or path.startswith('//') or '://' in path:
        raise LocalEndpointPolicyError('request-path-invalid', 'Provider request path must be an absolute local path, not a URL.')
    base = endpoint_decision.normalized_endpoint.rstrip('/') + '/'
    target = urljoin(base, path.lstrip('/'))
    target_decision = evaluate_loopback_endpoint(provider_id=provider_id, endpoint=_origin_only(target))
    if not target_decision.ok:
        raise LocalEndpointPolicyError('target-origin-block', target_decision.reason)
    if (target_decision.host, target_decision.port, target_decision.scheme) != (endpoint_decision.host, endpoint_decision.port, endpoint_decision.scheme):
        raise LocalEndpointPolicyError('target-origin-changed', 'Resolved request target changed endpoint origin.')
    cfg = limits or LocalHttpLimits()
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode('utf-8')
    headers = {'Accept': 'application/json'}
    if body is not None:
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(target, data=body, headers=headers, method=method.upper())
    opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=max(0.05, float(cfg.timeout_seconds))) as response:  # noqa: S310 - target is validated loopback
            content_type = str(response.headers.get('Content-Type') or '').split(';', 1)[0].strip().lower()
            if content_type not in {'application/json', 'application/problem+json'} and not content_type.endswith('+json'):
                raise LocalEndpointPolicyError('content-type-invalid', f'Expected JSON content type, got {content_type or "missing"}.')
            declared_length = response.headers.get('Content-Length')
            if declared_length:
                try:
                    declared_size = int(declared_length)
                except ValueError:
                    raise LocalEndpointPolicyError('content-length-invalid', 'Content-Length must be numeric.') from None
                if declared_size > cfg.max_response_bytes:
                    raise LocalEndpointPolicyError('payload-too-large', 'Declared response body exceeds configured limit.')
            raw = response.read(cfg.max_response_bytes + 1)
            if len(raw) > cfg.max_response_bytes:
                raise LocalEndpointPolicyError('payload-too-large', 'Response body exceeds configured limit.')
            try:
                decoded = raw.decode('utf-8', errors='strict')
                value = json.loads(decoded) if decoded.strip() else {}
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise LocalEndpointPolicyError('invalid-json', 'Local provider returned invalid JSON.') from exc
            if not isinstance(value, dict):
                raise LocalEndpointPolicyError('json-root-not-object', 'Local provider JSON root must be an object.')
            return int(response.status), value
    except urllib.error.HTTPError as exc:
        if 300 <= int(exc.code) < 400:
            raise LocalEndpointPolicyError('redirect-forbidden', 'Redirects are disabled for local provider requests.') from exc
        raise


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def bounded_model_names(payload: dict[str, Any], *, provider_family: str, max_models: int) -> tuple[list[str], bool]:
    if provider_family == 'ollama':
        rows = payload.get('models')
    else:
        rows = payload.get('data')
    if not isinstance(rows, list):
        raise LocalEndpointPolicyError('model-list-malformed', 'Model discovery payload does not contain the expected list.')
    truncated = len(rows) > max_models
    result: list[str] = []
    for item in rows[:max_models]:
        if isinstance(item, dict):
            candidate = item.get('name') or item.get('model') or item.get('id')
        elif isinstance(item, str):
            candidate = item
        else:
            candidate = None
        if candidate:
            text = str(candidate)
            if len(text) <= 256:
                result.append(text)
    return result, truncated


def _origin_only(value: str) -> str:
    parsed = urlsplit(value)
    host = parsed.hostname or ''
    if ':' in host:
        host = f'[{host}]'
    netloc = host
    if parsed.port is not None:
        netloc = f'{host}:{parsed.port}'
    return urlunsplit((parsed.scheme, netloc, '', '', ''))


def _normalize_allowlist_value(value: str) -> str:
    parsed = urlsplit(str(value).strip())
    host = (parsed.hostname or '').lower()
    if ':' in host:
        host = f'[{host}]'
    port = parsed.port
    default_port = 443 if parsed.scheme.lower() == 'https' else 80
    netloc = host if port in {None, default_port} else f'{host}:{port}'
    return urlunsplit((parsed.scheme.lower(), netloc, '', '', ''))


def _is_explicit_loopback(host: str) -> bool:
    if host == 'localhost':
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _deny(provider_id: str, reason: str, required: bool, *, scheme: str | None = None, host: str | None = None, port: int | None = None) -> LocalEndpointDecision:
    return LocalEndpointDecision(False, provider_id, None, host, port, scheme, reason, explicit_allowlist_required=required, explicit_allowlist_matched=False)


def safe_local_error_type(exc: Exception) -> str:
    if isinstance(exc, LocalEndpointPolicyError):
        return exc.code
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return 'timeout'
    if isinstance(exc, urllib.error.HTTPError):
        return 'http_error'
    if isinstance(exc, urllib.error.URLError):
        reason = getattr(exc, 'reason', None)
        if isinstance(reason, (socket.timeout, TimeoutError)):
            return 'timeout'
        return 'connection_error'
    return exc.__class__.__name__


def bounded_json_request_object(request: urllib.request.Request, *, provider_id: str, timeout_seconds: float, max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES) -> tuple[int, dict[str, Any]]:
    """Execute an already-built Request after loopback/origin validation, without redirects."""
    parsed = urlsplit(request.full_url)
    origin = _origin_only(request.full_url)
    decision = evaluate_loopback_endpoint(provider_id=provider_id, endpoint=origin)
    if not decision.ok:
        raise LocalEndpointPolicyError('request-origin-block', decision.reason)
    opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=max(0.05, float(timeout_seconds))) as response:  # noqa: S310 - validated loopback origin
            content_type = str(response.headers.get('Content-Type') or '').split(';', 1)[0].strip().lower()
            if content_type not in {'application/json', 'application/problem+json'} and not content_type.endswith('+json'):
                raise LocalEndpointPolicyError('content-type-invalid', f'Expected JSON content type, got {content_type or "missing"}.')
            declared_length = response.headers.get('Content-Length')
            if declared_length:
                try:
                    declared_size = int(declared_length)
                except ValueError:
                    raise LocalEndpointPolicyError('content-length-invalid', 'Content-Length must be numeric.') from None
                if declared_size > max_response_bytes:
                    raise LocalEndpointPolicyError('payload-too-large', 'Declared response body exceeds configured limit.')
            raw = response.read(max_response_bytes + 1)
            if len(raw) > max_response_bytes:
                raise LocalEndpointPolicyError('payload-too-large', 'Response body exceeds configured limit.')
            try:
                text = raw.decode('utf-8', errors='strict')
                value = json.loads(text) if text.strip() else {}
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise LocalEndpointPolicyError('invalid-json', 'Local provider returned invalid JSON.') from exc
            if not isinstance(value, dict):
                raise LocalEndpointPolicyError('json-root-not-object', 'Local provider JSON root must be an object.')
            return int(response.status), value
    except urllib.error.HTTPError as exc:
        if 300 <= int(exc.code) < 400:
            raise LocalEndpointPolicyError('redirect-forbidden', 'Redirects are disabled for local provider requests.') from exc
        raise
