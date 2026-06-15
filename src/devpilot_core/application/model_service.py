from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.modeling import BudgetLedger, CapabilityMatrix, ModelAdapterRouter, ModelHealthService, ModelRouterConfig


class ModelApplicationService:
    """Application-facing model governance facade.

    The default route remains mock/local-first. External APIs are not required
    and are blocked by lower-level provider and cost policies.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def providers(self) -> CommandResult:
        return ModelAdapterRouter(self.root).providers_status()

    def health(self, *, provider: str = "ollama") -> CommandResult:
        return ModelAdapterRouter(self.root).health(provider=provider)

    def health_all(self) -> CommandResult:
        return ModelHealthService(self.root).check_all()

    def capabilities(self) -> CommandResult:
        return CapabilityMatrix(self.root).build()

    def budget_status(self, *, limit: int = 20) -> CommandResult:
        return BudgetLedger(self.root).status(limit=limit)

    def generate(self, *, prompt: str, provider: str = "mock", model: str | None = None) -> CommandResult:
        return ModelAdapterRouter(self.root, config=ModelRouterConfig(budget_ledger_enabled=True)).generate(prompt=prompt, provider=provider, model=model)

    def classify(self, *, text: str, labels: tuple[str, ...], provider: str = "mock", model: str | None = None) -> CommandResult:
        return ModelAdapterRouter(self.root, config=ModelRouterConfig(budget_ledger_enabled=True)).classify(text=text, labels=labels, provider=provider, model=model)

    def embed(self, *, text: str, provider: str = "mock", model: str | None = None) -> CommandResult:
        return ModelAdapterRouter(self.root, config=ModelRouterConfig(budget_ledger_enabled=True)).embed(text=text, provider=provider, model=model)
