from __future__ import annotations

import json
import re
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.contracts import ModelAdapter, ModelCallRequest, ModelCallResult, ModelProviderConfig, ModelTask


DEFAULT_LMSTUDIO_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True)
class LMStudioAdapter(ModelAdapter):
    """Optional local LM Studio adapter using OpenAI-compatible endpoints.

    FUNC-SPRINT-47 introduces the second real local provider boundary. The
    adapter accepts only localhost HTTP base URLs, uses short timeouts and
    converts every network/protocol problem into structured DevPilot results.
    It never calls OpenAI or any external API: LM Studio is treated strictly as
    a local OpenAI-compatible server.
    """

    provider_config: ModelProviderConfig
    timeout_seconds: float = DEFAULT_LMSTUDIO_TIMEOUT_SECONDS

    def health(self) -> CommandResult:
        """Probe local `/v1/models` with a bounded localhost-only request."""

        endpoint = _normalize_endpoint(self.provider_config.endpoint)
        if endpoint is None:
            return _health_blocked(
                provider=self.provider_config.provider_id,
                endpoint=self.provider_config.endpoint,
                finding_id="LMSTUDIO_ENDPOINT_INVALID",
                message="LM Studio endpoint is missing or is not a localhost HTTP URL.",
            )

        request = urllib.request.Request(urljoin(endpoint, "/v1/models"), method="GET")
        try:
            status_code, payload = _json_request(request, timeout_seconds=self.timeout_seconds)
            models = _extract_model_names(payload)
            return CommandResult(
                command="model health",
                ok=True,
                exit_code=ExitCode.PASS,
                message="LM Studio health check completed successfully.",
                data={
                    "summary": {
                        "provider": self.provider_config.provider_id,
                        "availability": "available",
                        "enabled": self.provider_config.enabled,
                        "endpoint": endpoint,
                        "models_total": len(models),
                        "status_code": status_code,
                        "timeout_seconds": self.timeout_seconds,
                        "network_scope": "localhost",
                        "openai_compatible": True,
                        "external_api_used": False,
                        "preliminary": True,
                    },
                    "models": models,
                    "provider": self.provider_config.to_dict(),
                    "notes": [
                        "FUNC-SPRINT-47 health checks are local-only and bounded by timeout.",
                        "LM Studio is treated as a localhost OpenAI-compatible provider, not as OpenAI API.",
                        "Provider enabled=false means model calls remain blocked, but health may still inspect local availability.",
                    ],
                },
                findings=[
                    Finding(
                        id="LMSTUDIO_HEALTH_AVAILABLE",
                        message="LM Studio localhost endpoint responded to /v1/models.",
                        severity=Severity.INFO,
                        metadata={"provider": self.provider_config.provider_id, "models_total": len(models)},
                    )
                ],
            )
        except Exception as exc:  # intentionally converted to structured diagnostics
            return _health_unavailable(
                provider=self.provider_config,
                endpoint=endpoint,
                timeout_seconds=self.timeout_seconds,
                exc=exc,
            )

    def generate(self, request: ModelCallRequest) -> ModelCallResult:
        prompt = request.prompt or request.text or ""
        model = request.model or self.provider_config.default_model
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": 0.0,
        }
        response = self._post_json("/v1/chat/completions", payload, task=ModelTask.GENERATE)
        if not response.ok:
            return response
        content = _extract_chat_content(response.metadata)
        if content is None:
            return _model_failure(
                self.provider_config.provider_id,
                model,
                ModelTask.GENERATE,
                "response_invalid",
                "LM Studio chat completion response did not contain choices[0].message.content.",
            )
        tokens = _extract_usage_tokens(response.metadata) or _estimate_tokens(prompt) + _estimate_tokens(content)
        return ModelCallResult(
            ok=True,
            provider=self.provider_config.provider_id,
            model=model,
            task=ModelTask.GENERATE,
            content=content,
            tokens_estimated=tokens,
            cost_estimate_usd=0.0,
            external_api_used=False,
            metadata={
                "route": "lmstudio",
                "endpoint": _normalize_endpoint(self.provider_config.endpoint),
                "localhost_only": True,
                "openai_compatible": True,
                "prompt_redacted": True,
                "response_keys": sorted(str(key) for key in response.metadata.keys()),
            },
        )

    def classify(self, request: ModelCallRequest) -> ModelCallResult:
        labels = tuple(label.strip() for label in request.labels if label.strip()) or ("unknown",)
        text = request.text or request.prompt or ""
        prompt = (
            "Clasifica el texto en exactamente una de estas etiquetas: "
            f"{', '.join(labels)}. Responde solo la etiqueta.\n\nTexto:\n{text}"
        )
        generated = self.generate(ModelCallRequest(task=ModelTask.GENERATE, prompt=prompt, provider=request.provider, model=request.model))
        if not generated.ok:
            return ModelCallResult(
                ok=False,
                provider=self.provider_config.provider_id,
                model=request.model or self.provider_config.default_model,
                task=ModelTask.CLASSIFY,
                tokens_estimated=generated.tokens_estimated,
                cost_estimate_usd=0.0,
                external_api_used=False,
                metadata={**generated.metadata, "labels": list(labels), "classification_failed": True},
            )
        content = generated.content or ""
        selected = _select_label(content, labels)
        return ModelCallResult(
            ok=True,
            provider=self.provider_config.provider_id,
            model=generated.model,
            task=ModelTask.CLASSIFY,
            label=selected,
            tokens_estimated=generated.tokens_estimated,
            cost_estimate_usd=0.0,
            external_api_used=False,
            metadata={
                "route": "lmstudio",
                "labels": list(labels),
                "raw_response_redacted": True,
                "localhost_only": True,
                "openai_compatible": True,
            },
        )

    def embed(self, request: ModelCallRequest) -> ModelCallResult:
        text = request.text or request.prompt or ""
        model = request.model or self.provider_config.default_model
        response = self._post_json("/v1/embeddings", {"model": model, "input": text}, task=ModelTask.EMBED)
        if not response.ok:
            return response
        vector = _extract_embedding(response.metadata)
        if not vector:
            return ModelCallResult(
                ok=False,
                provider=self.provider_config.provider_id,
                model=model,
                task=ModelTask.EMBED,
                tokens_estimated=_estimate_tokens(text),
                cost_estimate_usd=0.0,
                external_api_used=False,
                metadata={
                    "route": "lmstudio",
                    "endpoint": _normalize_endpoint(self.provider_config.endpoint),
                    "localhost_only": True,
                    "openai_compatible": True,
                    "error": "LM Studio embedding response did not contain data[0].embedding.",
                    "availability": "response_invalid",
                },
            )
        tokens = _extract_usage_tokens(response.metadata) or _estimate_tokens(text)
        return ModelCallResult(
            ok=True,
            provider=self.provider_config.provider_id,
            model=model,
            task=ModelTask.EMBED,
            embedding=vector,
            tokens_estimated=tokens,
            cost_estimate_usd=0.0,
            external_api_used=False,
            metadata={
                "route": "lmstudio",
                "dimensions": len(vector),
                "endpoint": _normalize_endpoint(self.provider_config.endpoint),
                "localhost_only": True,
                "openai_compatible": True,
            },
        )

    def _post_json(self, path: str, payload: dict[str, Any], *, task: ModelTask) -> ModelCallResult:
        endpoint = _normalize_endpoint(self.provider_config.endpoint)
        model = str(payload.get("model") or self.provider_config.default_model)
        if endpoint is None:
            return _model_failure(self.provider_config.provider_id, model, task, "invalid_endpoint", "LM Studio endpoint is missing or invalid.")
        request = urllib.request.Request(
            urljoin(endpoint, path),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            _status_code, response_payload = _json_request(request, timeout_seconds=self.timeout_seconds)
            return ModelCallResult(
                ok=True,
                provider=self.provider_config.provider_id,
                model=model,
                task=task,
                external_api_used=False,
                metadata=response_payload if isinstance(response_payload, dict) else {"response": response_payload},
            )
        except Exception as exc:
            return _model_failure(
                self.provider_config.provider_id,
                model,
                task,
                _error_type(exc),
                _safe_error_message(exc),
            )


def _json_request(request: urllib.request.Request, *, timeout_seconds: float) -> tuple[int, dict[str, Any]]:
    with urllib.request.urlopen(request, timeout=max(float(timeout_seconds), 0.1)) as response:  # noqa: S310 - localhost only after endpoint validation
        raw = response.read().decode("utf-8", errors="replace")
        if not raw.strip():
            return int(response.status), {}
        data = json.loads(raw)
        if not isinstance(data, dict):
            return int(response.status), {"response": data}
        return int(response.status), data


def _normalize_endpoint(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "http" or host not in {"localhost", "127.0.0.1", "::1"}:
        return None
    return value.rstrip("/") + "/"


def _extract_model_names(payload: dict[str, Any]) -> list[str]:
    data = payload.get("data") if isinstance(payload, dict) else []
    if not isinstance(data, list):
        return []
    result: list[str] = []
    for item in data:
        if isinstance(item, dict):
            name = item.get("id") or item.get("name") or item.get("model")
            if name:
                result.append(str(name))
        elif isinstance(item, str):
            result.append(item)
    return result


def _extract_chat_content(payload: dict[str, Any]) -> str | None:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    message = first.get("message")
    if isinstance(message, dict) and message.get("content") is not None:
        return str(message.get("content"))
    if first.get("text") is not None:
        return str(first.get("text"))
    return None


def _extract_embedding(payload: dict[str, Any]) -> list[float]:
    data = payload.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        candidate = data[0].get("embedding")
        if isinstance(candidate, list):
            return [_as_float(value) for value in candidate if _is_number(value)]
    candidate = payload.get("embedding")
    if isinstance(candidate, list):
        return [_as_float(value) for value in candidate if _is_number(value)]
    return []


def _extract_usage_tokens(payload: dict[str, Any]) -> int:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return 0
    for key in ("total_tokens", "total_token_count"):
        if key in usage:
            return _safe_int(usage.get(key))
    return _safe_int(usage.get("prompt_tokens")) + _safe_int(usage.get("completion_tokens"))


def _select_label(content: str, labels: tuple[str, ...]) -> str:
    lowered = content.strip().lower()
    normalized = re.sub(r"[^a-z0-9_áéíóúñ-]+", " ", lowered)
    for label in labels:
        if label.lower() == lowered or re.search(rf"\b{re.escape(label.lower())}\b", normalized):
            return label
    return labels[0]


def _model_failure(provider: str, model: str, task: ModelTask, error_type: str, message: str) -> ModelCallResult:
    return ModelCallResult(
        ok=False,
        provider=provider,
        model=model,
        task=task,
        tokens_estimated=0,
        cost_estimate_usd=0.0,
        external_api_used=False,
        metadata={
            "route": "lmstudio",
            "availability": "unavailable",
            "error_type": error_type,
            "error": message,
            "payload_redacted": True,
            "localhost_only": True,
            "openai_compatible": True,
        },
    )


def _health_blocked(*, provider: str, endpoint: str | None, finding_id: str, message: str) -> CommandResult:
    return CommandResult(
        command="model health",
        ok=False,
        exit_code=ExitCode.BLOCK,
        message=message,
        data={
            "summary": {
                "provider": provider,
                "availability": "blocked",
                "endpoint": endpoint,
                "network_scope": "none",
                "external_api_used": False,
                "preliminary": True,
            }
        },
        findings=[Finding(id=finding_id, message=message, severity=Severity.BLOCK, metadata={"provider": provider})],
    )


def _health_unavailable(*, provider: ModelProviderConfig, endpoint: str, timeout_seconds: float, exc: Exception) -> CommandResult:
    return CommandResult(
        command="model health",
        ok=True,
        exit_code=ExitCode.PASS,
        message="LM Studio health check completed with unavailable status.",
        data={
            "summary": {
                "provider": provider.provider_id,
                "availability": "unavailable",
                "enabled": provider.enabled,
                "endpoint": endpoint,
                "models_total": 0,
                "timeout_seconds": timeout_seconds,
                "network_scope": "localhost",
                "openai_compatible": True,
                "external_api_used": False,
                "preliminary": True,
            },
            "models": [],
            "provider": provider.to_dict(),
            "notes": [
                "LM Studio is optional in FUNC-SPRINT-47; unavailable local server does not break the baseline suite.",
                "Enable and start LM Studio locally only when you want to execute provider-specific model calls.",
            ],
        },
        findings=[
            Finding(
                id="LMSTUDIO_HEALTH_UNAVAILABLE",
                message="LM Studio localhost endpoint is not available or did not respond before timeout.",
                severity=Severity.WARNING,
                metadata={
                    "provider": provider.provider_id,
                    "error_type": _error_type(exc),
                    "payload_redacted": True,
                },
            )
        ],
    )


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, TimeoutError):
        return "Local LM Studio request timed out."
    if isinstance(exc, socket.timeout):
        return "Local LM Studio request timed out."
    if isinstance(exc, urllib.error.HTTPError):
        return f"Local LM Studio endpoint returned HTTP {exc.code}."
    if isinstance(exc, urllib.error.URLError):
        reason = getattr(exc, "reason", None)
        if isinstance(reason, TimeoutError) or isinstance(reason, socket.timeout):
            return "Local LM Studio request timed out."
        return "Local LM Studio endpoint is unavailable."
    if isinstance(exc, json.JSONDecodeError):
        return "Local LM Studio endpoint returned non-JSON response."
    return "Local LM Studio request failed in controlled mode."


def _error_type(exc: Exception) -> str:
    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(exc, socket.timeout):
        return "timeout"
    if isinstance(exc, urllib.error.HTTPError):
        return "http_error"
    if isinstance(exc, urllib.error.URLError):
        reason = getattr(exc, "reason", None)
        if isinstance(reason, TimeoutError) or isinstance(reason, socket.timeout):
            return "timeout"
        return "connection_error"
    if isinstance(exc, json.JSONDecodeError):
        return "invalid_json"
    return exc.__class__.__name__


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _estimate_tokens(value: str) -> int:
    return max(1, len(re.findall(r"\S+", value or "")))


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _as_float(value: Any) -> float:
    return round(float(value), 6)
