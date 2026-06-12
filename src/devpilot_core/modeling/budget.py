from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.store import LocalStore


@dataclass(frozen=True)
class BudgetLedger:
    """Local model budget ledger backed by LocalStore cost_events.

    Sprint 48 records monetary and compute estimates without storing prompts or
    raw model payloads. Local providers normally produce zero monetary cost;
    external providers remain disabled by default.
    """

    root: Path

    def record_model_result(self, result: CommandResult, *, source: str = "model-cli") -> str | None:
        data = result.data or {}
        summary = dict(data.get("summary") or {})
        provider_payload = dict(data.get("provider") or {})
        result_payload = dict(data.get("result") or {})
        provider = str(summary.get("provider") or provider_payload.get("provider_id") or result_payload.get("provider") or "unknown")
        if not provider or provider == "unknown":
            return None
        task = str(summary.get("task") or result_payload.get("task") or "unknown")
        model = str(summary.get("model") or result_payload.get("model") or provider_payload.get("default_model") or "unknown")
        tokens = int(summary.get("tokens_estimated") or result_payload.get("tokens_estimated") or 0)
        monetary_cost = float(summary.get("cost_estimate_usd") or result_payload.get("cost_estimate_usd") or 0.0)
        metadata = {
            "source": source,
            "task": task,
            "model": model,
            "tokens_estimated": tokens,
            "monetary_cost_estimate_usd": monetary_cost,
            "compute_estimate_units": tokens,
            "result_ok": bool(result.ok),
            "exit_code": int(result.exit_code),
            "external_api_used": bool(summary.get("external_api_used") or result_payload.get("external_api_used") or False),
            "payload_redacted": True,
            "prompt_stored": False,
            "content_stored": False,
            "preliminary": True,
        }
        return LocalStore(self.root).record_cost_event(
            provider=provider,
            estimated_cost_usd=monetary_cost,
            actual_cost_usd=0.0,
            budget_limit_usd=0.0,
            budget_used_usd=0.0,
            metadata=metadata,
        )

    def status(self, *, limit: int = 20) -> CommandResult:
        store = LocalStore(self.root)
        summary = store.cost_events_summary()
        events = store.list_cost_events(limit=limit)
        unsafe_events = [event for event in events if _metadata_has_prompt_or_secret(event.get("metadata", {}))]
        findings = [Finding(id="MODEL_BUDGET_LEDGER_STATUS_PASS", message="Model budget ledger status computed from local cost_events.", severity=Severity.INFO)]
        if unsafe_events:
            findings.append(
                Finding(
                    id="MODEL_BUDGET_LEDGER_UNSAFE_METADATA_BLOCKED",
                    message="One or more cost_events appear to contain prompt/secret-like metadata.",
                    severity=Severity.BLOCK,
                    metadata={"unsafe_events_total": len(unsafe_events)},
                )
            )
        ok = not unsafe_events
        return CommandResult(
            command="model budget status",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Model budget ledger status passed." if ok else "Model budget ledger contains unsafe metadata.",
            data={
                "summary": {
                    **summary,
                    "events_returned": len(events),
                    "unsafe_events_total": len(unsafe_events),
                    "external_api_used": False,
                    "preliminary": True,
                },
                "events": events,
                "notes": [
                    "BudgetLedger records local monetary estimates and compute units only.",
                    "Prompts, completions and raw secrets are not stored in cost_events metadata.",
                ],
            },
            findings=findings,
        )


def _metadata_has_prompt_or_secret(metadata: dict[str, Any]) -> bool:
    suspicious_keys = {"prompt", "completion", "content", "raw_prompt", "raw_response", "api_key", "secret", "password", "token"}
    keys = {str(key).lower() for key in metadata.keys()}
    if keys & suspicious_keys:
        return True
    text = str(metadata).lower()
    return any(marker in text for marker in ("sk-", "api_key=", "password=", "secret="))
