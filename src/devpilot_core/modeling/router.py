from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.contracts import ModelCallRequest, ModelCallResult, ModelProviderKind, ModelTask
from devpilot_core.modeling.mock_adapter import MockModelAdapter
from devpilot_core.modeling.providers import ProviderRegistry
from devpilot_core.policy import CostPolicy, PolicyEngine, PolicyRequest, PromptInjectionGuard, SecretGuard, ToolInjectionGuard, load_cost_policy


@dataclass(frozen=True)
class ModelRouterConfig:
    """Runtime knobs for FUNC-SPRINT-17 model routing."""

    allow_external_api: bool = False
    budget_limit_usd: float = 0.0
    budget_used_usd: float = 0.0


class ModelAdapterRouter:
    """Route model calls through safe provider adapters and CostGuard.

    Sprint 17 implements only the mock adapter. Local and external providers are
    represented in the registry, but local servers are not contacted and API
    providers are not called. This preserves local-first behavior and makes cost
    controls executable before real providers are added.
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
            return self._blocked_placeholder(
                request,
                provider.to_dict(),
                finding_id="MODEL_LOCAL_PROVIDER_NOT_IMPLEMENTED",
                message="Local provider routing is declared but not implemented in Sprint 17; no local server was contacted.",
            )

        return self._blocked_placeholder(
            request,
            provider.to_dict(),
            finding_id="MODEL_EXTERNAL_PROVIDER_STUB_BLOCKED",
            message="External API provider is a disabled placeholder in Sprint 17; no network call was made.",
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
                "llm_required": False,
                "preliminary": True,
            },
            "result": call_result.to_dict(),
            "provider": provider_payload,
            "policy_summary": (policy_result.data or {}).get("summary", {}),
            "notes": [
                "FUNC-SPRINT-45 keeps MockModelAdapter as the mandatory default provider.",
                "No external API was called and no API key was required.",
            ],
        }
        return CommandResult(
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

    def _blocked_placeholder(self, request: ModelCallRequest, provider_payload: dict, *, finding_id: str, message: str) -> CommandResult:
        return CommandResult(
            command=f"model {request.task.value}",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message=message,
            data={
                "summary": {
                    "provider": provider_payload.get("provider_id"),
                    "task": request.task.value,
                    "external_api_used": False,
                    "cost_estimate_usd": 0.0,
                    "preliminary": True,
                },
                "provider": provider_payload,
                "notes": [
                    "Provider declared for hybrid architecture only.",
                    "Sprint 45 defines provider contracts only; local model adapters are implemented in later sprints.",
                ],
            },
            findings=[Finding(id=finding_id, message=message, severity=Severity.BLOCK)],
        )


def _estimate_tokens(value: str) -> int:
    return max(1, len((value or "").split()))
