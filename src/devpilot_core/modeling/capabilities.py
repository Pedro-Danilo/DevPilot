from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.contracts import ModelProviderKind
from devpilot_core.modeling.providers import ProviderRegistry


@dataclass(frozen=True)
class CapabilityMatrix:
    """Static, auditable capability matrix for configured model providers.

    Sprint 48 deliberately keeps this matrix conservative. It reports what the
    adapter boundary supports, what is enabled by configuration and whether a
    provider is local-only or externally blocked. Runtime health is reported by
    ModelHealthService, while this matrix is safe to run without contacting any
    model server.
    """

    root: Path

    def build(self) -> CommandResult:
        registry = ProviderRegistry.load(self.root)
        rows: list[dict[str, Any]] = []
        for provider in registry.providers.values():
            supports = _supports(provider.provider_id, provider.kind)
            rows.append(
                {
                    "provider": provider.provider_id,
                    "kind": provider.kind.value,
                    "enabled_by_default": bool(provider.enabled),
                    "status": provider.status,
                    "default_model": provider.default_model,
                    "endpoint": provider.endpoint,
                    "external_api": bool(provider.external_api),
                    "requires_api_key": bool(provider.requires_api_key),
                    "network_scope": _network_scope(provider.kind),
                    "localhost_only": provider.kind == ModelProviderKind.LOCAL,
                    "supports": supports,
                    "context_window_tokens_estimated": _context_window(provider.provider_id),
                    "monetary_cost_per_1k_tokens_usd": provider.estimated_cost_per_1k_tokens_usd,
                    "fallback_provider": "mock" if provider.kind == ModelProviderKind.LOCAL else None,
                    "governance": {
                        "router_required": True,
                        "policy_engine_required": True,
                        "secret_guard_required": True,
                        "cost_guard_required": True,
                        "external_api_blocked_by_default": provider.kind == ModelProviderKind.API,
                    },
                }
            )
        return CommandResult(
            command="model capabilities",
            ok=registry.semantic_valid,
            exit_code=ExitCode.PASS if registry.semantic_valid else ExitCode.BLOCK,
            message="Model capability matrix built.",
            data={
                "summary": {
                    "providers_total": len(rows),
                    "mock_providers_total": sum(1 for row in rows if row["kind"] == "mock"),
                    "local_providers_total": sum(1 for row in rows if row["kind"] == "local"),
                    "external_providers_total": sum(1 for row in rows if row["kind"] == "api"),
                    "external_api_enabled_total": sum(1 for row in rows if row["external_api"] and row["enabled_by_default"]),
                    "fallback_provider": "mock",
                    "network_used": False,
                    "external_api_used": False,
                    "preliminary": True,
                },
                "capabilities": rows,
                "notes": [
                    "CapabilityMatrix is static and safe: it does not contact local model servers.",
                    "Runtime availability remains the responsibility of model health.",
                ],
            },
            findings=(
                [Finding(id="MODEL_CAPABILITY_MATRIX_PASS", message="Capability matrix reports mock/local/external provider states.", severity=Severity.INFO)]
                if registry.semantic_valid
                else list(registry.validation_findings)
            ),
        )


def _supports(provider_id: str, kind: ModelProviderKind) -> dict[str, bool]:
    if kind == ModelProviderKind.MOCK:
        return {"generate": True, "classify": True, "embed": True, "health": True, "stream": False}
    if kind == ModelProviderKind.LOCAL and provider_id in {"ollama", "lmstudio"}:
        return {"generate": True, "classify": True, "embed": True, "health": True, "stream": False}
    if kind == ModelProviderKind.API:
        return {"generate": False, "classify": False, "embed": False, "health": False, "stream": False}
    return {"generate": False, "classify": False, "embed": False, "health": False, "stream": False}


def _network_scope(kind: ModelProviderKind) -> str:
    if kind == ModelProviderKind.MOCK:
        return "none"
    if kind == ModelProviderKind.LOCAL:
        return "localhost"
    return "blocked_external"


def _context_window(provider_id: str) -> int | None:
    estimates = {
        "mock": 2048,
        "ollama": 8192,
        "lmstudio": 8192,
    }
    return estimates.get(provider_id)
