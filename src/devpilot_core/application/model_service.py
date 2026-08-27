from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling import (
    BudgetLedger,
    CapabilityMatrix,
    ModelAdapterRouter,
    ModelCapabilityCatalog,
    ModelCapabilityCatalogError,
    ModelHealthService,
    ModelRouterConfig,
    ModelRoutingRequest,
)


class ModelApplicationService:
    """Application-facing model governance facade.

    GSDLC-06-A adds a lazy, offline catalog query. Constructing this service
    does not require the new catalog, which preserves historical/minimal
    workspaces that never invoke Model Gateway v2.
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

    def model_catalog(self) -> CommandResult:
        try:
            catalog = ModelCapabilityCatalog(self.root)
        except ModelCapabilityCatalogError as exc:
            return CommandResult(command="model catalog", ok=False, exit_code=ExitCode.BLOCK, message="Model capability catalog is invalid.", findings=[Finding(id="MODEL_CAPABILITY_CATALOG_INVALID", message=str(exc), severity=Severity.BLOCK)])
        snapshot = catalog.snapshot()
        return CommandResult(
            command="model catalog", ok=True, exit_code=ExitCode.PASS, message="Model capability catalog loaded without provider I/O.",
            data={"summary":{"providers_total":len(snapshot["providers"]),"models_total":len(snapshot["models"]),"access_routes_total":len(snapshot["access_routes"]),"network_used":False,"external_api_used":False},"catalog":snapshot},
            findings=[Finding(id="MODEL_CAPABILITY_CATALOG_PASS", message="Provider/model/route/adapter identities are loaded from the versioned catalog.", severity=Severity.INFO)],
        )

    def route_model(self, request: ModelRoutingRequest) -> CommandResult:
        try:
            decision = ModelCapabilityCatalog(self.root).decide(request)
        except ModelCapabilityCatalogError as exc:
            return CommandResult(command="model route", ok=False, exit_code=ExitCode.BLOCK, message="Model routing blocked because catalog authority is invalid.", findings=[Finding(id="MODEL_ROUTE_CATALOG_INVALID", message=str(exc), severity=Severity.BLOCK)])
        payload = decision.to_dict()
        ok = decision.route_status == "selected"
        return CommandResult(
            command="model route", ok=ok, exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Model route selected." if ok else "Model routing blocked safely.",
            data={"request":request.to_dict(),"decision":payload,"summary":{"network_used":False,"external_api_used":False,"tool_execution_authority":False}},
            findings=[Finding(id="MODEL_ROUTE_SELECTED" if ok else "MODEL_ROUTE_BLOCKED", message="Model route decision is capability-based and cannot grant tool execution.", severity=Severity.INFO if ok else Severity.BLOCK)],
        )

    def budget_status(self, *, limit: int = 20) -> CommandResult:
        return BudgetLedger(self.root).status(limit=limit)

    def generate(self, *, prompt: str, provider: str = "mock", model: str | None = None) -> CommandResult:
        return ModelAdapterRouter(self.root, config=ModelRouterConfig(budget_ledger_enabled=True)).generate(prompt=prompt, provider=provider, model=model)

    def classify(self, *, text: str, labels: tuple[str, ...], provider: str = "mock", model: str | None = None) -> CommandResult:
        return ModelAdapterRouter(self.root, config=ModelRouterConfig(budget_ledger_enabled=True)).classify(text=text, labels=labels, provider=provider, model=model)

    def embed(self, *, text: str, provider: str = "mock", model: str | None = None) -> CommandResult:
        return ModelAdapterRouter(self.root, config=ModelRouterConfig(budget_ledger_enabled=True)).embed(text=text, provider=provider, model=model)
