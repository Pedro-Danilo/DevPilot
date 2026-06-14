from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.contracts import ModelCallRequest, ModelCallResult, ModelProviderKind, ModelTask
from devpilot_core.modeling.mock_adapter import MockModelAdapter
from devpilot_core.modeling.ollama_adapter import OllamaAdapter
from devpilot_core.modeling.lmstudio_adapter import LMStudioAdapter
from devpilot_core.modeling.providers import ProviderRegistry
from devpilot_core.policy import CostPolicy, PolicyEngine, PolicyRequest, PromptInjectionGuard, SecretGuard, ToolInjectionGuard, load_cost_policy


@dataclass(frozen=True)
class ModelRouterConfig:
    """Runtime knobs for FUNC-SPRINT-17 model routing."""

    allow_external_api: bool = False
    budget_limit_usd: float = 0.0
    budget_used_usd: float = 0.0
    local_timeout_seconds: float = 3.0
    fallback_to_mock_on_local_unavailable: bool = False
    budget_ledger_enabled: bool = True


class ModelAdapterRouter:
    """Route model calls through safe provider adapters and CostGuard.

    Sprint 47 keeps mock as the default route and adds optional Ollama and
    LM Studio localhost adapters. Local providers remain disabled by default
    and external API providers are not called. This preserves local-first
    behavior while allowing controlled fake-server and real-local health/model
    checks.
    """

    def __init__(self, root: Path, *, config: ModelRouterConfig | None = None) -> None:
        self.root = root.resolve()
        self.config = config or ModelRouterConfig()
        self.registry = ProviderRegistry.load(self.root)
        self.secret_guard = SecretGuard()
        self.prompt_injection_guard = PromptInjectionGuard()
        self.tool_injection_guard = ToolInjectionGuard()

    def providers_status(self) -> CommandResult:
        return self.registry.to_result()

    def health(self, *, provider: str = "ollama") -> CommandResult:
        if not self.registry.semantic_valid:
            return CommandResult(
                command="model health",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Model health blocked because provider registry failed safe semantic checks.",
                data={
                    "summary": {
                        "provider_registry_valid": False,
                        "source_path": self.registry.source_path,
                        "external_api_used": False,
                        "preliminary": True,
                    },
                    "provider_registry": self.registry.to_result().data,
                    "preliminary": True,
                },
                findings=list(self.registry.validation_findings),
            )
        provider_id = provider.strip().lower() or "ollama"
        provider_config = self.registry.get(provider_id)
        if provider_config is None:
            return CommandResult(
                command="model health",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Model provider is not registered.",
                data={"summary": {"provider": provider_id, "registered": False, "external_api_used": False}},
                findings=[
                    Finding(
                        id="MODEL_PROVIDER_UNKNOWN",
                        message=f"Provider '{provider_id}' is not declared in the provider registry.",
                        severity=Severity.BLOCK,
                        metadata={"provider": provider_id},
                    )
                ],
            )
        if provider_config.kind == ModelProviderKind.MOCK:
            return CommandResult(
                command="model health",
                ok=True,
                exit_code=ExitCode.PASS,
                message="Mock provider is available without network.",
                data={
                    "summary": {
                        "provider": provider_config.provider_id,
                        "availability": "available",
                        "enabled": provider_config.enabled,
                        "network_scope": "none",
                        "external_api_used": False,
                        "preliminary": True,
                    },
                    "provider": provider_config.to_dict(),
                },
                findings=[Finding(id="MODEL_HEALTH_MOCK_AVAILABLE", message="Mock provider is always available offline.", severity=Severity.INFO)],
            )
        if provider_config.kind == ModelProviderKind.API:
            return CommandResult(
                command="model health",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="External API provider health checks are blocked in Fase D by default.",
                data={
                    "summary": {
                        "provider": provider_config.provider_id,
                        "availability": "blocked",
                        "enabled": provider_config.enabled,
                        "external_api_used": False,
                        "preliminary": True,
                    },
                    "provider": provider_config.to_dict(),
                },
                findings=[Finding(id="MODEL_EXTERNAL_HEALTH_BLOCKED", message="External provider health check would require network/API access and is blocked.", severity=Severity.BLOCK)],
            )
        if provider_config.provider_id == "ollama":
            return OllamaAdapter(provider_config, timeout_seconds=self.config.local_timeout_seconds).health()
        if provider_config.provider_id == "lmstudio":
            return LMStudioAdapter(provider_config, timeout_seconds=self.config.local_timeout_seconds).health()
        return CommandResult(
            command="model health",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local provider health check is not implemented yet and remains controlled.",
            data={
                "summary": {
                    "provider": provider_config.provider_id,
                    "availability": "not_implemented",
                    "enabled": provider_config.enabled,
                    "external_api_used": False,
                    "preliminary": True,
                },
                "provider": provider_config.to_dict(),
            },
            findings=[Finding(id="MODEL_LOCAL_HEALTH_NOT_IMPLEMENTED", message="This local provider health check is planned for a later sprint.", severity=Severity.WARNING)],
        )

    def generate(self, *, prompt: str, provider: str = "mock", model: str | None = None) -> CommandResult:
        return self._run(ModelCallRequest(task=ModelTask.GENERATE, prompt=prompt, provider=provider, model=model))

    def classify(self, *, text: str, labels: tuple[str, ...], provider: str = "mock", model: str | None = None) -> CommandResult:
        return self._run(ModelCallRequest(task=ModelTask.CLASSIFY, text=text, labels=labels, provider=provider, model=model))

    def embed(self, *, text: str, provider: str = "mock", model: str | None = None) -> CommandResult:
        return self._run(ModelCallRequest(task=ModelTask.EMBED, text=text, provider=provider, model=model))

    def _run(self, request: ModelCallRequest) -> CommandResult:
        if not self.registry.semantic_valid:
            return CommandResult(
                command=f"model {request.task.value}",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Model call blocked because provider registry failed safe semantic checks.",
                data={
                    "summary": {
                        "provider_registry_valid": False,
                        "source_path": self.registry.source_path,
                        "external_api_used": False,
                        "preliminary": True,
                    },
                    "provider_registry": self.registry.to_result().data,
                    "preliminary": True,
                },
                findings=list(self.registry.validation_findings),
            )

        provider_id = request.provider.strip().lower() or "mock"
        provider = self.registry.get(provider_id)
        if provider is None:
            return CommandResult(
                command=f"model {request.task.value}",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Model provider is not registered.",
                data={"summary": {"provider": provider_id, "registered": False}},
                findings=[
                    Finding(
                        id="MODEL_PROVIDER_UNKNOWN",
                        message=f"Provider '{provider_id}' is not declared in the provider registry.",
                        severity=Severity.BLOCK,
                        metadata={"provider": provider_id},
                    )
                ],
            )

        text_to_scan = request.prompt if request.task == ModelTask.GENERATE else request.text
        guard_decisions = [
            self.secret_guard.scan_text(text_to_scan, subject=f"model:{request.task.value}"),
            self.prompt_injection_guard.scan_text(text_to_scan, subject=f"model:{request.task.value}"),
            self.tool_injection_guard.scan_text(text_to_scan, subject=f"model:{request.task.value}"),
        ]
        blocking_guard_decisions = [decision for decision in guard_decisions if decision.effect.value == "block"]
        if blocking_guard_decisions:
            return CommandResult(
                command=f"model {request.task.value}",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Model call blocked by local security guards before provider routing.",
                data={
                    "summary": {
                        "provider": provider.provider_id,
                        "task": request.task.value,
                        "external_api_used": False,
                        "cost_estimate_usd": 0.0,
                        "guards": [decision.guard for decision in guard_decisions],
                        "blocking_guards": [decision.guard for decision in blocking_guard_decisions],
                        "preliminary": True,
                    },
                    "provider": provider.to_dict(),
                    "preliminary": True,
                },
                findings=[decision.to_finding() for decision in guard_decisions if decision.effect.value != "allow"],
            )

        estimated_tokens = _estimate_tokens(text_to_scan or "")
        estimated_cost = (estimated_tokens / 1000.0) * provider.estimated_cost_per_1k_tokens_usd
        policy_result = self._policy_result(provider, estimated_cost)
        if not policy_result.ok:
            return CommandResult(
                command=f"model {request.task.value}",
                ok=False,
                exit_code=policy_result.exit_code,
                message="Model call blocked by CostGuard/PolicyEngine before provider execution.",
                data={
                    "summary": {
                        "provider": provider.provider_id,
                        "task": request.task.value,
                        "tokens_estimated": estimated_tokens,
                        "cost_estimate_usd": round(estimated_cost, 8),
                        "external_api_used": False,
                    },
                    "provider": provider.to_dict(),
                    "policy": policy_result.data,
                    "preliminary": True,
                },
                findings=policy_result.findings,
            )

        if provider.kind == ModelProviderKind.MOCK:
            adapter = MockModelAdapter(provider)
            call_result = {
                ModelTask.GENERATE: adapter.generate,
                ModelTask.CLASSIFY: adapter.classify,
                ModelTask.EMBED: adapter.embed,
            }[request.task](request)
            return self._success_result(call_result, provider.to_dict(), policy_result)

        if provider.kind == ModelProviderKind.LOCAL:
            if not provider.enabled:
                return self._blocked_placeholder(
                    request,
                    provider.to_dict(),
                    finding_id="MODEL_PROVIDER_DISABLED",
                    message=f"Local provider '{provider.provider_id}' is disabled by configuration; enable it in .devpilot/providers.yaml to execute model calls.",
                )
            if provider.provider_id == "ollama":
                adapter = OllamaAdapter(provider, timeout_seconds=self.config.local_timeout_seconds)
                call_result = {
                    ModelTask.GENERATE: adapter.generate,
                    ModelTask.CLASSIFY: adapter.classify,
                    ModelTask.EMBED: adapter.embed,
                }[request.task](request)
                if call_result.ok:
                    return self._success_result(call_result, provider.to_dict(), policy_result)
                if self.config.fallback_to_mock_on_local_unavailable:
                    return self._fallback_to_mock_result(request, provider, call_result, policy_result)
                return self._adapter_failure_result(call_result, provider.to_dict(), policy_result)
            if provider.provider_id == "lmstudio":
                adapter = LMStudioAdapter(provider, timeout_seconds=self.config.local_timeout_seconds)
                call_result = {
                    ModelTask.GENERATE: adapter.generate,
                    ModelTask.CLASSIFY: adapter.classify,
                    ModelTask.EMBED: adapter.embed,
                }[request.task](request)
                if call_result.ok:
                    return self._success_result(call_result, provider.to_dict(), policy_result)
                if self.config.fallback_to_mock_on_local_unavailable:
                    return self._fallback_to_mock_result(request, provider, call_result, policy_result)
                return self._adapter_failure_result(call_result, provider.to_dict(), policy_result)
            return self._blocked_placeholder(
                request,
                provider.to_dict(),
                finding_id="MODEL_LOCAL_PROVIDER_NOT_IMPLEMENTED",
                message="Local provider routing is declared but this provider adapter is not implemented yet.",
            )

        return self._blocked_placeholder(
            request,
            provider.to_dict(),
            finding_id="MODEL_EXTERNAL_PROVIDER_STUB_BLOCKED",
            message="External API provider is a disabled placeholder in Sprint 17; no network call was made.",
        )

    def _fallback_to_mock_result(self, request: ModelCallRequest, original_provider, failed_result: ModelCallResult, policy_result: CommandResult) -> CommandResult:
        mock_provider = self.registry.get("mock")
        if mock_provider is None or not mock_provider.enabled:
            return self._adapter_failure_result(failed_result, original_provider.to_dict(), policy_result)
        mock_request = ModelCallRequest(
            task=request.task,
            prompt=request.prompt,
            text=request.text,
            labels=request.labels,
            provider="mock",
            model=mock_provider.default_model,
            dry_run=request.dry_run,
            metadata={**request.metadata, "fallback_from": original_provider.provider_id},
        )
        adapter = MockModelAdapter(mock_provider)
        fallback_result = {
            ModelTask.GENERATE: adapter.generate,
            ModelTask.CLASSIFY: adapter.classify,
            ModelTask.EMBED: adapter.embed,
        }[request.task](mock_request)
        result = self._success_result(fallback_result, mock_provider.to_dict(), policy_result)
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["fallback_applied"] = True
        summary["fallback_from_provider"] = original_provider.provider_id
        summary["fallback_to_provider"] = "mock"
        data["summary"] = summary
        data["fallback"] = {
            "applied": True,
            "from_provider": original_provider.provider_id,
            "to_provider": "mock",
            "reason": failed_result.metadata.get("error_type", "local_provider_unavailable"),
            "original_availability": failed_result.metadata.get("availability", "unavailable"),
            "external_api_used": False,
            "payload_redacted": True,
        }
        findings = list(result.findings) + [
            Finding(
                id="MODEL_FALLBACK_TO_MOCK_APPLIED",
                message="Local provider was unavailable; safe fallback to mock was applied by configuration.",
                severity=Severity.WARNING,
                metadata={"from_provider": original_provider.provider_id, "to_provider": "mock"},
            )
        ]
        return CommandResult(
            command=result.command,
            ok=True,
            exit_code=ExitCode.PASS,
            message="Model call completed through safe fallback to mock.",
            data=data,
            findings=findings,
        )

    def _policy_result(self, provider, estimated_cost: float) -> CommandResult:
        base = load_cost_policy(self.root)
        policy = CostPolicy(
            external_api_allowed=self.config.allow_external_api or base.external_api_allowed,
            budget_limit_usd=self.config.budget_limit_usd if self.config.budget_limit_usd > 0 else base.budget_limit_usd,
            budget_used_usd=self.config.budget_used_usd if self.config.budget_used_usd > 0 else base.budget_used_usd,
            allowed_providers=base.allowed_providers,
        )
        return PolicyEngine(self.root, cost_policy=policy).evaluate(
            PolicyRequest(
                action="external-api" if provider.external_api else "model-call",
                external_api=provider.external_api,
                provider=provider.provider_id,
                estimated_cost_usd=estimated_cost,
                dry_run=True,
                metadata={"component": "ModelAdapterRouter"},
            )
        )

    def _success_result(self, call_result: ModelCallResult, provider_payload: dict, policy_result: CommandResult) -> CommandResult:
        task = call_result.task.value
        data = {
            "summary": {
                "provider": call_result.provider,
                "model": call_result.model,
                "task": task,
                "tokens_estimated": call_result.tokens_estimated,
                "cost_estimate_usd": call_result.cost_estimate_usd,
                "external_api_used": call_result.external_api_used,
                "llm_required": call_result.provider != "mock",
                "metrics_best_effort": True,
                "preliminary": True,
            },
            "result": call_result.to_dict(),
            "provider": provider_payload,
            "policy_summary": (policy_result.data or {}).get("summary", {}),
            "notes": [
                "ModelAdapterRouter enforced provider registry, local guards and CostGuard before provider execution.",
                "No external API was called and no API key was required.",
                "FUNC-SPRINT-59 records local model metrics and FUNC-SPRINT-60 records model-call spans/events best-effort without changing model-call semantics.",
            ],
        }
        result = CommandResult(
            command=f"model {task}",
            ok=True,
            exit_code=ExitCode.PASS,
            message=f"Model {task} completed through safe ModelAdapter routing.",
            data=data,
            findings=[
                Finding(
                    id="MODEL_ADAPTER_PASS",
                    message="ModelAdapter routed the call without external API usage.",
                    severity=Severity.INFO,
                    metadata={"provider": call_result.provider, "task": task},
                )
            ],
        )
        self._record_model_metric(result, call_result)
        return result

    def _record_model_metric(self, result: CommandResult, call_result: ModelCallResult) -> None:
        """Record Sprint 60 model observability without making it mandatory."""

        try:
            from devpilot_core.observability.agentops import AgentOpsInstrumentor

            AgentOpsInstrumentor(self.root).record_model_result(
                result=result,
                provider=call_result.provider,
                model=call_result.model,
                task=call_result.task.value,
                metadata={"component": "ModelAdapterRouter", "provider_kind": str(call_result.provider), "payload_redacted": True},
            )
        except Exception:
            return

    def _adapter_failure_result(self, call_result: ModelCallResult, provider_payload: dict, policy_result: CommandResult) -> CommandResult:
        task = call_result.task.value
        result = CommandResult(
            command=f"model {task}",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Local model adapter call failed in controlled mode.",
            data={
                "summary": {
                    "provider": call_result.provider,
                    "model": call_result.model,
                    "task": task,
                    "availability": call_result.metadata.get("availability", "unavailable"),
                    "tokens_estimated": call_result.tokens_estimated,
                    "cost_estimate_usd": 0.0,
                    "external_api_used": False,
                    "preliminary": True,
                },
                "result": call_result.to_dict(),
                "provider": provider_payload,
                "policy_summary": (policy_result.data or {}).get("summary", {}),
                "notes": [
                    "Local model providers are optional in Fase D; unavailable local servers are reported as structured BLOCK findings for model calls.",
                    "The baseline suite must keep passing without real Ollama or LM Studio servers.",
                ],
            },
            findings=[
                Finding(
                    id="MODEL_LOCAL_PROVIDER_UNAVAILABLE",
                    message="Local model provider was enabled but unavailable or returned an invalid response.",
                    severity=Severity.BLOCK,
                    metadata={
                        "provider": call_result.provider,
                        "error_type": call_result.metadata.get("error_type"),
                        "payload_redacted": True,
                    },
                )
            ],
        )
        self._record_model_metric(result, call_result)
        return result

    def _blocked_placeholder(self, request: ModelCallRequest, provider_payload: dict, *, finding_id: str, message: str) -> CommandResult:
        result = CommandResult(
            command=f"model {request.task.value}",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message=message,
            data={
                "summary": {
                    "provider": provider_payload.get("provider_id"),
                    "model": provider_payload.get("default_model"),
                    "task": request.task.value,
                    "external_api_used": False,
                    "cost_estimate_usd": 0.0,
                    "preliminary": True,
                },
                "provider": provider_payload,
                "notes": [
                    "Provider declared for hybrid architecture and governed by ProviderRegistry.",
                    "Local model calls remain disabled by default unless explicitly enabled in local configuration.",
                ],
            },
            findings=[Finding(id=finding_id, message=message, severity=Severity.BLOCK)],
        )
        try:
            from devpilot_core.observability.agentops import AgentOpsInstrumentor

            AgentOpsInstrumentor(self.root).record_model_result(
                result=result,
                provider=str(provider_payload.get("provider_id") or "unknown"),
                model=provider_payload.get("default_model"),
                task=request.task.value,
                metadata={"component": "ModelAdapterRouter", "blocked_placeholder": True, "payload_redacted": True},
            )
        except Exception:
            pass
        return result


def _estimate_tokens(value: str) -> int:
    return max(1, len((value or "").split()))
