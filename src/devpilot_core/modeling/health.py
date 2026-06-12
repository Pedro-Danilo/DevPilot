from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.providers import ProviderRegistry


@dataclass(frozen=True)
class ModelHealthService:
    """Governed health facade for all configured model providers.

    FUNC-SPRINT-48 centralizes provider availability reporting. The service is
    intentionally local-first: mock is reported offline, local providers are
    checked only through localhost-bound adapters, and external API providers
    are reported as blocked without any network call.
    """

    root: Path
    timeout_seconds: float = 3.0

    def check_all(self) -> CommandResult:
        from devpilot_core.modeling.router import ModelAdapterRouter, ModelRouterConfig

        registry = ProviderRegistry.load(self.root)
        if not registry.semantic_valid:
            return CommandResult(
                command="model health",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Model health blocked because provider registry failed semantic validation.",
                data={
                    "summary": {
                        "providers_total": len(registry.providers),
                        "available_total": 0,
                        "blocked_total": 0,
                        "unavailable_total": 0,
                        "external_api_used": False,
                        "preliminary": True,
                    },
                    "providers": [],
                    "provider_registry": registry.to_result().data,
                },
                findings=list(registry.validation_findings),
            )

        router = ModelAdapterRouter(
            self.root,
            config=ModelRouterConfig(local_timeout_seconds=self.timeout_seconds, budget_ledger_enabled=False),
        )
        health_rows: list[dict[str, Any]] = []
        findings: list[Finding] = []
        for provider_id in registry.providers:
            result = router.health(provider=provider_id)
            summary = dict((result.data or {}).get("summary", {}))
            provider_payload = dict((result.data or {}).get("provider", {}))
            health_rows.append(
                {
                    "provider": provider_id,
                    "kind": provider_payload.get("kind"),
                    "enabled": provider_payload.get("enabled"),
                    "status": provider_payload.get("status"),
                    "availability": summary.get("availability", "unknown"),
                    "models_total": summary.get("models_total", 0),
                    "network_scope": summary.get("network_scope", "none"),
                    "external_api_used": bool(summary.get("external_api_used", False)),
                    "ok": bool(result.ok),
                    "exit_code": int(result.exit_code),
                }
            )
            findings.extend(result.findings)

        available_total = sum(1 for row in health_rows if row["availability"] == "available")
        blocked_total = sum(1 for row in health_rows if row["availability"] == "blocked" or row["exit_code"] == int(ExitCode.BLOCK))
        unavailable_total = sum(1 for row in health_rows if row["availability"] == "unavailable")
        local_total = sum(1 for row in health_rows if row.get("kind") == "local")
        external_total = sum(1 for row in health_rows if row.get("kind") == "api")
        return CommandResult(
            command="model health",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Model health governance report completed.",
            data={
                "summary": {
                    "providers_total": len(health_rows),
                    "local_providers_total": local_total,
                    "external_providers_total": external_total,
                    "available_total": available_total,
                    "blocked_total": blocked_total,
                    "unavailable_total": unavailable_total,
                    "timeout_seconds": self.timeout_seconds,
                    "external_api_used": False,
                    "preliminary": True,
                },
                "providers": health_rows,
                "notes": [
                    "FUNC-SPRINT-48 reports all provider health through governed adapters.",
                    "External API providers are reported as blocked; no external network call is made.",
                ],
            },
            findings=[Finding(id="MODEL_HEALTH_GOVERNANCE_PASS", message="Model health governance report completed without external API usage.", severity=Severity.INFO)] + findings,
        )
