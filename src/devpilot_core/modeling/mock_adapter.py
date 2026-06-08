from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from devpilot_core.modeling.contracts import ModelAdapter, ModelCallRequest, ModelCallResult, ModelProviderConfig, ModelTask


@dataclass(frozen=True)
class MockModelAdapter(ModelAdapter):
    """Deterministic offline ModelAdapter used as the default route.

    It does not call a model server, does not access the network and does not
    need API keys. Its purpose is to test provider routing, CostGuard and agent
    integration before real local/API adapters are enabled.
    """

    provider_config: ModelProviderConfig

    def generate(self, request: ModelCallRequest) -> ModelCallResult:
        prompt = (request.prompt or request.text or "").strip()
        summary = _compact(prompt, max_words=28) or "empty prompt"
        content = (
            "[mock-deterministic] Propuesta local generada sin LLM externo. "
            f"Resumen de entrada: {summary}. Próximo paso sugerido: validar con policy, tests y revisión humana."
        )
        return ModelCallResult(
            ok=True,
            provider=self.provider_config.provider_id,
            model=request.model or self.provider_config.default_model,
            task=ModelTask.GENERATE,
            content=content,
            tokens_estimated=_estimate_tokens(prompt) + _estimate_tokens(content),
            cost_estimate_usd=0.0,
            external_api_used=False,
            metadata={"deterministic": True, "route": "mock"},
        )

    def classify(self, request: ModelCallRequest) -> ModelCallResult:
        text = (request.text or request.prompt or "").lower()
        labels = tuple(label.strip() for label in request.labels if label.strip()) or ("unknown",)
        selected = labels[0]
        for label in labels:
            label_tokens = re.findall(r"[a-zA-Z0-9_áéíóúñÁÉÍÓÚÑ]+", label.lower())
            if any(token and token in text for token in label_tokens):
                selected = label
                break
        return ModelCallResult(
            ok=True,
            provider=self.provider_config.provider_id,
            model=request.model or self.provider_config.default_model,
            task=ModelTask.CLASSIFY,
            label=selected,
            tokens_estimated=_estimate_tokens(text) + sum(_estimate_tokens(label) for label in labels),
            cost_estimate_usd=0.0,
            external_api_used=False,
            metadata={"labels": list(labels), "deterministic": True, "route": "mock"},
        )

    def embed(self, request: ModelCallRequest) -> ModelCallResult:
        text = (request.text or request.prompt or "").encode("utf-8")
        digest = hashlib.sha256(text).digest()
        vector = [round((digest[index] / 255.0) * 2 - 1, 6) for index in range(8)]
        return ModelCallResult(
            ok=True,
            provider=self.provider_config.provider_id,
            model=request.model or self.provider_config.default_model,
            task=ModelTask.EMBED,
            embedding=vector,
            tokens_estimated=_estimate_tokens(text.decode("utf-8", errors="ignore")),
            cost_estimate_usd=0.0,
            external_api_used=False,
            metadata={"dimensions": len(vector), "deterministic": True, "route": "mock"},
        )


def _estimate_tokens(value: str) -> int:
    return max(1, len(re.findall(r"\S+", value or "")))


def _compact(value: str, *, max_words: int) -> str:
    words = re.findall(r"\S+", value or "")
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]) + " ..."
