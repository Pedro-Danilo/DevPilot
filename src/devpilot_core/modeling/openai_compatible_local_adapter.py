from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.contracts import ModelAdapter, ModelCallRequest, ModelCallResult, ModelProviderConfig, ModelTask
from devpilot_core.modeling.local_endpoint_policy import LocalEndpointPolicy, LocalHttpLimits, bounded_json_request, bounded_model_names, safe_local_error_type


@dataclass(frozen=True)
class OpenAICompatibleLocalAdapter(ModelAdapter):
    """Generic local OpenAI-compatible route guarded by explicit endpoint allowlist."""

    provider_config: ModelProviderConfig
    endpoint_policy: LocalEndpointPolicy

    def _decision(self):
        return self.endpoint_policy.evaluate(self.provider_config.provider_id, self.provider_config.endpoint)

    def _limits(self) -> LocalHttpLimits:
        return self.endpoint_policy.limits_for(self.provider_config.provider_id)

    def health(self) -> CommandResult:
        decision = self._decision()
        if not decision.ok:
            return CommandResult(
                command='model health', ok=False, exit_code=ExitCode.BLOCK,
                message='Generic OpenAI-compatible local endpoint blocked by endpoint policy.',
                data={'summary': {'provider': self.provider_config.provider_id, 'availability': 'blocked', 'configured': bool(self.provider_config.endpoint), 'reachable': False, 'healthy': False, 'model_discovered': False, 'enabled': self.provider_config.enabled, 'endpoint_policy': decision.to_dict(), 'external_api_used': False}},
                findings=[Finding('MODEL_LOCAL_ENDPOINT_POLICY_BLOCK', 'Local endpoint did not satisfy explicit allowlist policy.', Severity.BLOCK, metadata={'provider': self.provider_config.provider_id, 'reason': decision.reason})],
            )
        try:
            status, payload = bounded_json_request(provider_id=self.provider_config.provider_id, endpoint_decision=decision, path='/v1/models', limits=self._limits())
            models, truncated = bounded_model_names(payload, provider_family='openai-compatible', max_models=self._limits().max_models)
            return CommandResult(
                command='model health', ok=True, exit_code=ExitCode.PASS,
                message='Generic local OpenAI-compatible health/discovery completed.',
                data={'summary': {'provider': self.provider_config.provider_id, 'availability': 'available', 'configured': True, 'reachable': True, 'healthy': True, 'model_discovered': bool(models), 'enabled': self.provider_config.enabled, 'models_total': len(models), 'models_truncated': truncated, 'status_code': status, 'endpoint': decision.normalized_endpoint, 'endpoint_policy': decision.to_dict(), 'network_scope': 'loopback-only', 'external_api_used': False}, 'models': models, 'provider': self.provider_config.to_dict()},
                findings=[Finding('MODEL_OPENAI_COMPAT_LOCAL_HEALTH_PASS', 'Explicitly allowlisted local OpenAI-compatible endpoint responded.', Severity.INFO, metadata={'models_total': len(models)})],
            )
        except Exception as exc:
            error_type = safe_local_error_type(exc)
            return CommandResult(
                command='model health', ok=True, exit_code=ExitCode.PASS,
                message='Generic local OpenAI-compatible health completed with unavailable status.',
                data={'summary': {'provider': self.provider_config.provider_id, 'availability': 'unavailable', 'configured': True, 'reachable': False, 'healthy': False, 'model_discovered': False, 'enabled': self.provider_config.enabled, 'models_total': 0, 'endpoint': decision.normalized_endpoint, 'endpoint_policy': decision.to_dict(), 'error_type': error_type, 'network_scope': 'loopback-only', 'external_api_used': False}, 'models': [], 'provider': self.provider_config.to_dict()},
                findings=[Finding('MODEL_OPENAI_COMPAT_LOCAL_UNAVAILABLE', 'Allowlisted local OpenAI-compatible endpoint is unavailable or invalid.', Severity.WARNING, metadata={'error_type': error_type, 'payload_redacted': True})],
            )

    def generate(self, request: ModelCallRequest) -> ModelCallResult:
        model = request.model or self.provider_config.default_model
        prompt = request.prompt or request.text or ''
        response = self._post('/v1/chat/completions', {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'stream': False}, task=ModelTask.GENERATE)
        if not response.ok:
            return response
        content = _chat_content(response.metadata)
        if content is None:
            return _failure(self.provider_config.provider_id, model, ModelTask.GENERATE, 'response-invalid')
        return ModelCallResult(ok=True, provider=self.provider_config.provider_id, model=model, task=ModelTask.GENERATE, content=content, tokens_estimated=_usage_tokens(response.metadata), cost_estimate_usd=0.0, external_api_used=False, metadata={'route': 'openai-compatible-local', 'payload_redacted': True, 'localhost_only': True, 'openai_compatible': True})

    def classify(self, request: ModelCallRequest) -> ModelCallResult:
        labels = tuple(x.strip() for x in request.labels if x.strip()) or ('unknown',)
        prompt = f"Classify into one label only: {', '.join(labels)}\n\n{request.text or request.prompt or ''}"
        generated = self.generate(ModelCallRequest(task=ModelTask.GENERATE, prompt=prompt, provider=request.provider, model=request.model))
        if not generated.ok:
            return ModelCallResult(ok=False, provider=self.provider_config.provider_id, model=generated.model, task=ModelTask.CLASSIFY, external_api_used=False, metadata=generated.metadata)
        lowered = (generated.content or '').strip().lower()
        selected = next((label for label in labels if label.lower() in lowered), labels[0])
        return ModelCallResult(ok=True, provider=self.provider_config.provider_id, model=generated.model, task=ModelTask.CLASSIFY, label=selected, tokens_estimated=generated.tokens_estimated, cost_estimate_usd=0.0, external_api_used=False, metadata={'route': 'openai-compatible-local', 'labels': list(labels), 'raw_response_redacted': True})

    def embed(self, request: ModelCallRequest) -> ModelCallResult:
        model = request.model or self.provider_config.default_model
        text = request.text or request.prompt or ''
        response = self._post('/v1/embeddings', {'model': model, 'input': text}, task=ModelTask.EMBED)
        if not response.ok:
            return response
        vector = _embedding(response.metadata)
        if not vector:
            return _failure(self.provider_config.provider_id, model, ModelTask.EMBED, 'response-invalid')
        return ModelCallResult(ok=True, provider=self.provider_config.provider_id, model=model, task=ModelTask.EMBED, embedding=vector, tokens_estimated=_usage_tokens(response.metadata), cost_estimate_usd=0.0, external_api_used=False, metadata={'route': 'openai-compatible-local', 'dimensions': len(vector), 'localhost_only': True})

    def _post(self, path: str, payload: dict[str, Any], *, task: ModelTask) -> ModelCallResult:
        model = str(payload.get('model') or self.provider_config.default_model)
        decision = self._decision()
        if not decision.ok:
            return _failure(self.provider_config.provider_id, model, task, decision.reason)
        try:
            _status, response = bounded_json_request(provider_id=self.provider_config.provider_id, endpoint_decision=decision, path=path, method='POST', payload=payload, limits=self._limits())
            return ModelCallResult(ok=True, provider=self.provider_config.provider_id, model=model, task=task, external_api_used=False, metadata=response)
        except Exception as exc:
            return _failure(self.provider_config.provider_id, model, task, safe_local_error_type(exc))


def _failure(provider: str, model: str, task: ModelTask, error_type: str) -> ModelCallResult:
    return ModelCallResult(ok=False, provider=provider, model=model, task=task, tokens_estimated=0, cost_estimate_usd=0.0, external_api_used=False, metadata={'route': 'openai-compatible-local', 'availability': 'unavailable', 'error_type': error_type, 'payload_redacted': True, 'localhost_only': True})


def _chat_content(payload: dict[str, Any]) -> str | None:
    choices = payload.get('choices')
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return None
    message = choices[0].get('message')
    return str(message.get('content')) if isinstance(message, dict) and message.get('content') is not None else None


def _embedding(payload: dict[str, Any]) -> list[float]:
    data = payload.get('data')
    if isinstance(data, list) and data and isinstance(data[0], dict) and isinstance(data[0].get('embedding'), list):
        return [float(v) for v in data[0]['embedding'] if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return []


def _usage_tokens(payload: dict[str, Any]) -> int:
    usage = payload.get('usage') if isinstance(payload.get('usage'), dict) else {}
    try:
        return max(0, int(usage.get('total_tokens') or 0))
    except (TypeError, ValueError):
        return 0
