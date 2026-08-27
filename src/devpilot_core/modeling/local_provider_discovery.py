from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.local_endpoint_policy import LocalEndpointPolicy
from devpilot_core.modeling.openai_compatible_local_adapter import OpenAICompatibleLocalAdapter
from devpilot_core.modeling.ollama_adapter import OllamaAdapter
from devpilot_core.modeling.lmstudio_adapter import LMStudioAdapter
from devpilot_core.modeling.providers import ProviderRegistry

LOCAL_PROVIDER_IDS_V2 = ('ollama', 'lmstudio', 'openai-compatible-local')
R01_HARDWARE_MATRIX = Path('research/devpl_gsdlc/r01/c/hardware_fit_matrix.json')


@dataclass(frozen=True)
class LocalProviderDiscoveryOptions:
    probe: bool = False
    provider_ids: tuple[str, ...] = LOCAL_PROVIDER_IDS_V2


class LocalProviderDiscoveryService:
    """GSDLC-06-B provider discovery with explicit state separation.

    Discovery is read-only and never changes ``enabled``. With ``probe=False``
    it performs zero network calls and is safe for Settings projection. With
    ``probe=True`` it can contact only endpoints accepted by the loopback policy.
    """

    def __init__(self, root: Path, options: LocalProviderDiscoveryOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or LocalProviderDiscoveryOptions()
        self.registry = ProviderRegistry.load(self.root)
        self.policy = LocalEndpointPolicy.load(self.root)

    def build(self) -> CommandResult:
        findings: list[Finding] = list(self.registry.validation_findings)
        rows = [self._row(pid, findings) for pid in self.options.provider_ids]
        blocking = [f for f in findings if f.severity in {Severity.BLOCK, Severity.ERROR}]
        summary = {
            'micro_sprint': 'DEVPL-GSDLC-06-B',
            'providers_total': len(rows),
            'configured_total': sum(1 for row in rows if row['configured']),
            'reachable_total': sum(1 for row in rows if row['reachable'] is True),
            'healthy_total': sum(1 for row in rows if row['healthy'] is True),
            'model_discovered_total': sum(1 for row in rows if row['model_discovered'] is True),
            'enabled_total': sum(1 for row in rows if row['enabled'] is True),
            'policy_allowed_total': sum(1 for row in rows if row['endpoint_policy']['ok'] is True),
            'probe_requested': self.options.probe,
            'network_scope': 'loopback-only' if self.options.probe else 'none',
            'network_used': bool(self.options.probe and any(row['probe_attempted'] for row in rows)),
            'external_api_used': False,
            'discovery_enables_provider': False,
            'fallback_provider': 'mock',
            'silent_fallback_allowed': False,
            'blocking_findings_total': len(blocking),
        }
        payload = {
            'schema_id': 'devpilot.gsdlc06b.local_provider_health_report.v1',
            'schema_version': '1.0.0',
            'status': 'PASS' if not blocking else 'BLOCK',
            'summary': summary,
            'providers': rows,
            'hardware_fit_hints': self._hardware_hints(),
            'fallback': {
                'provider_id': 'mock',
                'explicit_required': True,
                'silent_fallback_allowed': False,
                'discovery_triggers_fallback': False,
                'runtime_fallback_requires_router_configuration': True,
            },
            'safety': {
                'local_first': True,
                'external_api_used': False,
                'raw_secrets_exposed': False,
                'source_mutated': False,
                'discovery_enables_provider': False,
            },
        }
        if not blocking:
            findings.insert(0, Finding('GSDLC_06_B_LOCAL_DISCOVERY_PASS', 'Local provider discovery contract passed.', Severity.INFO, metadata=summary))
        return CommandResult(command='model local-discovery', ok=not blocking, exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK, message='Local provider discovery passed.' if not blocking else 'Local provider discovery blocked.', data={'summary': summary, 'report': payload}, findings=findings)

    def _row(self, provider_id: str, findings: list[Finding]) -> dict[str, Any]:
        config = self.registry.get(provider_id)
        if config is None:
            decision = self.policy.evaluate(provider_id, None)
            findings.append(Finding('GSDLC_06_B_PROVIDER_MISSING', f'Local provider {provider_id} is missing.', Severity.BLOCK, metadata={'provider_id': provider_id}))
            return {'provider_id': provider_id, 'configured': False, 'reachable': False, 'healthy': False, 'model_discovered': False, 'enabled': False, 'probe_attempted': False, 'models': [], 'models_total': 0, 'endpoint_policy': decision.to_dict(), 'fallback': {'provider_id': 'mock', 'reason': 'provider-missing', 'explicit': True}}
        decision = self.policy.evaluate(provider_id, config.endpoint)
        if not decision.ok:
            findings.append(Finding('GSDLC_06_B_ENDPOINT_POLICY_BLOCK', f'Endpoint policy blocked {provider_id}.', Severity.BLOCK, metadata={'provider_id': provider_id, 'reason': decision.reason}))
        reachable: bool | None = None
        healthy: bool | None = None
        models: list[str] = []
        probe_attempted = False
        probe_status = 'not-requested'
        error_type = None
        if self.options.probe and decision.ok:
            probe_attempted = True
            health = self._adapter(provider_id, config).health()
            hs = dict((health.data or {}).get('summary') or {})
            availability = str(hs.get('availability') or 'unavailable')
            reachable = bool(hs.get('reachable', availability == 'available'))
            healthy = bool(hs.get('healthy', availability == 'available'))
            models = list((health.data or {}).get('models') or [])
            error_type = hs.get('error_type')
            probe_status = availability
        return {
            'provider_id': provider_id,
            'configured': bool(config.endpoint),
            'reachable': reachable,
            'healthy': healthy,
            'model_discovered': bool(models),
            'enabled': bool(config.enabled),
            'probe_attempted': probe_attempted,
            'probe_status': probe_status,
            'models': models[: self.policy.limits_for(provider_id).max_models],
            'models_total': min(len(models), self.policy.limits_for(provider_id).max_models),
            'error_type': error_type,
            'endpoint': decision.normalized_endpoint,
            'endpoint_policy': decision.to_dict(),
            'external_api': False,
            'requires_api_key': bool(config.requires_api_key),
            'discovery_enables_provider': False,
            'fallback': {'provider_id': 'mock', 'reason': None if healthy else ('not-probed' if not self.options.probe else (error_type or 'unavailable')), 'explicit': True},
        }

    def _adapter(self, provider_id: str, config):
        limits = self.policy.limits_for(provider_id)
        if provider_id == 'ollama':
            return OllamaAdapter(config, timeout_seconds=limits.timeout_seconds, max_response_bytes=limits.max_response_bytes, max_models=limits.max_models)
        if provider_id == 'lmstudio':
            return LMStudioAdapter(config, timeout_seconds=limits.timeout_seconds, max_response_bytes=limits.max_response_bytes, max_models=limits.max_models)
        if provider_id == 'openai-compatible-local':
            return OpenAICompatibleLocalAdapter(config, self.policy)
        raise ValueError(provider_id)

    def _hardware_hints(self) -> dict[str, Any]:
        path = self.root / R01_HARDWARE_MATRIX
        if not path.is_file():
            return {'source': R01_HARDWARE_MATRIX.as_posix(), 'status': 'missing/non-blocking', 'authoritative': False, 'recommendations': []}
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
            recs = list((payload.get('hardware_profiles') or {}).get('recommended_for_this_host') or [])
            return {'source': R01_HARDWARE_MATRIX.as_posix(), 'status': 'historical/non-authoritative', 'authoritative': False, 'recommendations': [str(v) for v in recs[:16]], 'note': 'R01 hardware-fit hints are advisory and do not enable providers.'}
        except Exception:
            return {'source': R01_HARDWARE_MATRIX.as_posix(), 'status': 'invalid/non-blocking', 'authoritative': False, 'recommendations': []}
