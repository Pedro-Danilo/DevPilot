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


DEFAULT_OLLAMA_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True)
class OllamaAdapter(ModelAdapter):
    """Optional local Ollama adapter for governed model execution.

    FUNC-SPRINT-46 introduces the first real local provider boundary. The
    adapter only accepts localhost endpoints previously validated by
    ProviderRegistry, uses short timeouts, performs no external API calls and
    returns structured failures instead of raising network exceptions.
    """

    provider_config: ModelProviderConfig
    timeout_seconds: float = DEFAULT_OLLAMA_TIMEOUT_SECONDS

    def health(self) -> CommandResult:
        """Probe Ollama `/api/tags` with a bounded localhost-only request."""

        endpoint = _normalize_endpoint(self.provider_config.endpoint)
        if endpoint is None:
            return _health_blocked(
                provider=self.provider_config.provider_id,
                endpoint=self.provider_config.endpoint,
                finding_id="OLLAMA_ENDPOINT_INVALID",
                message="Ollama endpoint is missing or is not a localhost HTTP URL.",
            )

        request = urllib.request.Request(urljoin(endpoint, "/api/tags"), method="GET")
        try:
            status_code, payload = _json_request(request, None, timeout_seconds=self.timeout_seconds)
            models = _extract_model_names(payload)
            return CommandResult(
                command="model health",
                ok=True,
                exit_code=ExitCode.PASS,
                message="Ollama health check completed successfully.",
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
                        "external_api_used": False,
                        "preliminary": True,
                    },
                    "models": models,
                    "provider": self.provider_config.to_dict(),
                    "notes": [
                        "FUNC-SPRINT-46 health checks are local-only and bounded by timeout.",
                        "Provider enabled=false means model calls remain blocked, but health may still inspect local availability.",
                    ],
                },
                findings=[
                    Finding(
                        id="OLLAMA_HEALTH_AVAILABLE",
                        message="Ollama localhost endpoint responded to /api/tags.",
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
        payload = {"model": model, "prompt": prompt, "stream": False}
        response = self._post_json("/api/generate", payload, task=ModelTask.GENERATE)
        if not response.ok:
            return response
        content = str(response.metadata.get("response", ""))
        prompt_tokens = _safe_int(response.metadata.get("prompt_eval_count"))
        eval_tokens = _safe_int(response.metadata.get("eval_count"))
        tokens = prompt_tokens + eval_tokens or _estimate_tokens(prompt) + _estimate_tokens(content)
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
                "route": "ollama",
                "endpoint": _normalize_endpoint(self.provider_config.endpoint),
                "localhost_only": True,
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
                "route": "ollama",
                "labels": list(labels),
                "raw_response_redacted": True,
                "localhost_only": True,
            },
        )

    def embed(self, request: ModelCallRequest) -> ModelCallResult:
        text = request.text or request.prompt or ""
        model = request.model or self.provider_config.default_model
        first = self._post_json("/api/embed", {"model": model, "input": text}, task=ModelTask.EMBED)
        if first.ok:
            vector = _extract_embedding(first.metadata)
        else:
            legacy = self._post_json("/api/embeddings", {"model": model, "prompt": text}, task=ModelTask.EMBED)
            if not legacy.ok:
                return ModelCallResult(
                    ok=False,
                    provider=self.provider_config.provider_id,
                    model=model,
                    task=ModelTask.EMBED,
                    tokens_estimated=_estimate_tokens(text),
                    cost_estimate_usd=0.0,
                    external_api_used=False,
                    metadata={
                        "route": "ollama",
                        "endpoint": _normalize_endpoint(self.provider_config.endpoint),
                        "localhost_only": True,
                        "error": legacy.metadata.get("error"),
                        "error_type": legacy.metadata.get("error_type"),
                        "availability": legacy.metadata.get("availability", "unavailable"),
                    },
                )
            vector = _extract_embedding(legacy.metadata)
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
                    "route": "ollama",
                    "endpoint": _normalize_endpoint(self.provider_config.endpoint),
                    "localhost_only": True,
                    "error": "Ollama embedding response did not contain a usable vector.",
                    "availability": "response_invalid",
                },
            )
        return ModelCallResult(
            ok=True,
            provider=self.provider_config.provider_id,
            model=model,
            task=ModelTask.EMBED,
            embedding=vector,
            tokens_estimated=_estimate_tokens(text),
            cost_estimate_usd=0.0,
            external_api_used=False,
            metadata={
                "route": "ollama",
                "dimensions": len(vector),
                "endpoint": _normalize_endpoint(self.provider_config.endpoint),
                "localhost_only": True,
            },
        )

    def _post_json(self, path: str, payload: dict[str, Any], *, task: ModelTask) -> ModelCallResult:
        endpoint = _normalize_endpoint(self.provider_config.endpoint)
        model = str(payload.get("model") or self.provider_config.default_model)
        if endpoint is None:
            return _model_failure(self.provider_config.provider_id, model, task, "invalid_endpoint", "Ollama endpoint is missing or invalid.")
        request = urllib.request.Request(
            urljoin(endpoint, path),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            _status_code, response_payload = _json_request(request, None, timeout_seconds=self.timeout_seconds)
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


def _json_request(request: urllib.request.Request, payload: bytes | None, *, timeout_seconds: float) -> tuple[int, dict[str, Any]]:
    # `payload` is retained for testability/backwards compatibility with helper calls;
    # urllib takes body data from Request when present.
    del payload
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
    models = payload.get("models") if isinstance(payload, dict) else []
    if not isinstance(models, list):
        return []
    result: list[str] = []
    for item in models:
        if isinstance(item, dict):
            name = item.get("name") or item.get("model")
            if name:
                result.append(str(name))
        elif isinstance(item, str):
            result.append(item)
    return result


def _extract_embedding(payload: dict[str, Any]) -> list[float]:
    candidates: Any = payload.get("embeddings")
    if isinstance(candidates, list) and candidates and isinstance(candidates[0], list):
        return [_as_float(value) for value in candidates[0] if _is_number(value)]
    candidate = payload.get("embedding")
    if isinstance(candidate, list):
        return [_as_float(value) for value in candidate if _is_number(value)]
    return []


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
            "route": "ollama",
            "availability": "unavailable",
            "error_type": error_type,
            "error": message,
            "payload_redacted": True,
            "localhost_only": True,
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
        message="Ollama health check completed with unavailable status.",
        data={
            "summary": {
                "provider": provider.provider_id,
                "availability": "unavailable",
                "enabled": provider.enabled,
                "endpoint": endpoint,
                "models_total": 0,
                "timeout_seconds": timeout_seconds,
                "network_scope": "localhost",
                "external_api_used": False,
                "preliminary": True,
            },
            "models": [],
            "provider": provider.to_dict(),
            "notes": [
                "Ollama is optional in FUNC-SPRINT-46; unavailable local server does not break the baseline suite.",
                "Enable and start Ollama locally only when you want to execute provider-specific model calls.",
            ],
        },
        findings=[
            Finding(
                id="OLLAMA_HEALTH_UNAVAILABLE",
                message="Ollama localhost endpoint is not available or did not respond before timeout.",
                severity=Severity.WARNING,
                metadata={
                    "provider": provider.provider_id,
                    "error_type": _error_type(exc),
                    "payload_redacted": True,
                },
            )
        ],
    )


def _error_type(exc: Exception) -> str:
    if isinstance(exc, socket.timeout):
        return "timeout"
    if isinstance(exc, urllib.error.HTTPError):
        return "http_error"
    if isinstance(exc, urllib.error.URLError):
        return "url_error"
    if isinstance(exc, json.JSONDecodeError):
        return "invalid_json"
    return exc.__class__.__name__


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"HTTP {exc.code} from local Ollama endpoint."
    if isinstance(exc, urllib.error.URLError):
        return "Local Ollama endpoint is unavailable."
    if isinstance(exc, socket.timeout):
        return "Local Ollama request timed out."
    if isinstance(exc, json.JSONDecodeError):
        return "Local Ollama endpoint returned invalid JSON."
    return "Local Ollama request failed in controlled mode."


def _estimate_tokens(value: str) -> int:
    return max(1, len(re.findall(r"\S+", value or "")))


def _safe_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _as_float(value: Any) -> float:
    return round(float(value), 6)
