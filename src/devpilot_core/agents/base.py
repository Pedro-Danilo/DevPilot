from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from devpilot_core.agents.models import AgentMessage, AgentModelCall, AgentSuggestion
from devpilot_core.cli_models import CommandResult, Finding, Severity
from devpilot_core.modeling import BudgetLedger, ModelAdapterRouter, ModelRouterConfig
from devpilot_core.prompts import PromptRegistry


class ModelAwareAgent:
    """Base helper for mono-agent model calls through governed routing.

    FUNC-SPRINT-51 introduces this class as a reusable, local-first bridge
    between AgentRuntime and the model stack. It never instantiates provider
    adapters directly. All calls go through PromptRegistry + ModelAdapterRouter +
    BudgetLedger and only return redacted metadata to AgentRunResult.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _model_runtime_payload(self, message: AgentMessage) -> dict[str, Any]:
        payload = dict((message.metadata or {}).get("model_runtime") or {})
        return payload if payload.get("enabled") is True else {}

    def _model_runtime_enabled(self, message: AgentMessage) -> bool:
        return bool(self._model_runtime_payload(message))

    def _run_model_generate(
        self,
        message: AgentMessage,
        *,
        default_prompt_id: str,
        default_inputs: dict[str, str],
        suggestion_title: str,
        suggestion_target: str | None = None,
    ) -> tuple[AgentModelCall | None, list[Finding], AgentSuggestion | None]:
        """Render a governed prompt and call ModelAdapterRouter.generate.

        The returned suggestion intentionally avoids raw model content. It only
        tells the operator that model guidance was produced and stores a digest
        in metadata for traceability.
        """

        runtime = self._model_runtime_payload(message)
        if not runtime:
            return None, [], None

        provider = str(runtime.get("provider") or "mock").strip().lower() or "mock"
        model = runtime.get("model") or None
        prompt_id = str(runtime.get("prompt_id") or default_prompt_id)
        prompt_version = runtime.get("prompt_version") or None
        timeout_seconds = float(runtime.get("timeout_seconds") or 3.0)
        fallback_to_mock = bool(runtime.get("fallback_to_mock") or False)
        prompt_inputs = dict(default_inputs)
        prompt_inputs.update({str(k): str(v) for k, v in dict(runtime.get("prompt_inputs") or {}).items()})

        rendered, render_error = PromptRegistry(self.root).render(prompt_id, version=prompt_version, inputs=prompt_inputs)
        if render_error is not None:
            finding = Finding(
                id="AGENT_MODEL_PROMPT_RENDER_BLOCKED",
                message="AgentRuntime v2 blocked a model call because PromptRegistry rendering failed.",
                severity=Severity.BLOCK,
                metadata={"prompt_id": prompt_id, "payload_redacted": True},
            )
            model_call = AgentModelCall(
                provider=provider,
                model=str(model) if model else None,
                task="generate",
                ok=False,
                exit_code=int(render_error.exit_code),
                prompt_id=prompt_id,
                prompt_version=str(prompt_version) if prompt_version else None,
                external_api_used=False,
                metadata={"render_ok": False, "payload_redacted": True},
            )
            return model_call, [finding, *render_error.findings], None

        assert rendered is not None
        command_result = ModelAdapterRouter(
            self.root,
            config=ModelRouterConfig(
                local_timeout_seconds=timeout_seconds,
                fallback_to_mock_on_local_unavailable=fallback_to_mock,
            ),
        ).generate(prompt=rendered.text, provider=provider, model=str(model) if model else None)
        command_result = _attach_prompt_reference(command_result, rendered.reference_payload())
        BudgetLedger(self.root).record_model_result(command_result, source="agent-runtime-v2")
        model_call = _model_call_from_result(command_result, requested_provider=provider)
        findings = list(command_result.findings)
        if not command_result.ok:
            findings.append(
                Finding(
                    id="AGENT_MODEL_CALL_BLOCKED",
                    message="AgentRuntime v2 model call did not pass; the agent kept the failure as controlled metadata.",
                    severity=Severity.BLOCK,
                    metadata={"provider": provider, "prompt_id": prompt_id, "payload_redacted": True},
                )
            )
            return model_call, findings, None

        suggestion = AgentSuggestion(
            title=suggestion_title,
            body="Se ejecutó una llamada model-aware gobernada. El resultado crudo no se expone; revisar model_calls y BudgetLedger para trazabilidad.",
            target=suggestion_target,
            severity="info",
            metadata={
                "provider": model_call.provider,
                "model": model_call.model,
                "prompt_id": model_call.prompt_id,
                "prompt_version": model_call.prompt_version,
                "result_digest": model_call.result_digest,
                "payload_redacted": True,
                "raw_output_stored": False,
            },
        )
        return model_call, findings, suggestion


def _attach_prompt_reference(result: CommandResult, prompt_reference: dict[str, object]) -> CommandResult:
    data = dict(result.data or {})
    summary = dict(data.get("summary") or {})
    data["prompt_reference"] = dict(prompt_reference)
    summary["prompt_id"] = prompt_reference.get("prompt_id")
    summary["prompt_version"] = prompt_reference.get("version")
    summary["prompt_payload_redacted"] = True
    data["summary"] = summary
    return CommandResult(result.command, result.ok, result.exit_code, result.message, data=data, findings=result.findings)


def _model_call_from_result(result: CommandResult, *, requested_provider: str) -> AgentModelCall:
    data = dict(result.data or {})
    summary = dict(data.get("summary") or {})
    result_payload = dict(data.get("result") or {})
    prompt_reference = dict(data.get("prompt_reference") or {})
    provider = str(summary.get("provider") or result_payload.get("provider") or requested_provider)
    metadata = dict(result_payload.get("metadata") or {})
    fallback_applied = bool(summary.get("fallback_applied") or metadata.get("fallback_applied") or provider != requested_provider)
    content_for_digest = result_payload.get("content") or result_payload.get("label") or json.dumps(result_payload.get("embedding") or [], sort_keys=True)
    digest = _digest_payload(str(content_for_digest or ""))
    return AgentModelCall(
        provider=provider,
        model=str(summary.get("model") or result_payload.get("model") or "") or None,
        task=str(summary.get("task") or result_payload.get("task") or "generate"),
        ok=bool(result.ok),
        exit_code=int(result.exit_code),
        prompt_id=str(prompt_reference.get("prompt_id") or summary.get("prompt_id") or "") or None,
        prompt_version=str(prompt_reference.get("version") or summary.get("prompt_version") or "") or None,
        prompt_inputs_used=list(prompt_reference.get("inputs_used") or []),
        prompt_payload_redacted=True,
        tokens_estimated=int(summary.get("tokens_estimated") or result_payload.get("tokens_estimated") or 0),
        cost_estimate_usd=float(summary.get("cost_estimate_usd") or result_payload.get("cost_estimate_usd") or 0.0),
        external_api_used=bool(summary.get("external_api_used") or result_payload.get("external_api_used") or False),
        fallback_applied=fallback_applied,
        fallback_from_provider=str(summary.get("fallback_from_provider") or requested_provider) if fallback_applied else None,
        fallback_to_provider=str(summary.get("fallback_to_provider") or provider) if fallback_applied else None,
        result_digest=digest,
        raw_prompt_stored=False,
        raw_output_stored=False,
        metadata={
            "command": result.command,
            "payload_redacted": True,
            "findings_total": len(result.findings),
        },
    )


def _digest_payload(value: str) -> dict[str, Any]:
    payload = value or ""
    return {
        "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "length": len(payload),
        "payload_redacted": True,
    }
