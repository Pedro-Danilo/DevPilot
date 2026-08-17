from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest

from .approval_service import ApprovalApplicationService
from .dtos import ApplicationRequest, ApplicationResponse, InterfaceRouteContract, ServiceCapability
from .dto_normalization import normalize_priority_application_request
from .evals_service import EvaluationApplicationService
from .history_service import HistoryApplicationService
from .miasi_service import MiasiApplicationService
from .maturity_service import MaturityApplicationService
from .model_service import ModelApplicationService
from .observability_service import ObservabilityApplicationService
from .operator_dashboard_service import OperatorDashboardApplicationService
from .portfolio_service import PortfolioApplicationService
from .policy import ApplicationBoundaryPolicy
from .refactor_service import RefactorApplicationService
from .repo_service import RepoApplicationService
from .reports_service import ReportsApplicationService
from .settings_service import SettingsApplicationService
from .review_service import ReviewApplicationService
from .validation_service import ValidationApplicationService
from .workspace_service import WorkspaceApplicationService
from .workspace_documents_service import WorkspaceDocumentsApplicationService
from .workspace_document_inspection_service import WorkspaceDocumentInspectionApplicationService
from .workspace_validation_service import WorkspaceValidationApplicationService
from .workspace_edit_plan_service import WorkspaceEditPlanApplicationService
from .workspace_edit_execution_service import WorkspaceEditExecutionApplicationService
from .workspace_git_operations_service import WorkspaceGitOperationsApplicationService
from .governed_job_capability_registry import GovernedJobCapabilityRegistry
from .governed_job_operations import GovernedJobOperationsApplicationService
from .quality_operations import QualityOperationsApplicationService
from .ai_operations import AiOperationsApplicationService
from .governed_jobs import GovernedJobFramework
from .guided_sdlc_service import GuidedSDLCApplicationService
from .ui_workspace_context import UiWorkspaceContextResolver


def _display_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


class ApplicationService:
    """Application-service facade for CLI, future API local and Web UI shells.

    FUNC-SPRINT-65 upgrades the earlier validator-only facade into a domain
    facade. It keeps presentation layers away from DevPilot Core internals by
    grouping reusable operations under explicit domain services:

    - workspace
    - validation
    - MIASI
    - evaluations
    - repository
    - review
    - refactor
    - model governance
    - history
    - observability / AgentOps

    The service remains local-only, deterministic by default and dependency-free.
    It does not implement an HTTP server, Web UI or Desktop shell. It exposes
    CommandResult for existing CLI compatibility and ApplicationResponse for the
    future API/Web boundary.
    """

    def __init__(self, root: Path, *, enforce_workspace_paths: bool = False) -> None:
        self.root = root.resolve()
        self.enforce_workspace_paths = enforce_workspace_paths
        self.ui_workspace_context = UiWorkspaceContextResolver(self.root)
        self.guided_sdlc = GuidedSDLCApplicationService(self.root)
        self.workspace = WorkspaceApplicationService(self.root)
        self.workspace_documents = WorkspaceDocumentsApplicationService(self.root, context_resolver=self.ui_workspace_context)
        self.workspace_document_inspection = WorkspaceDocumentInspectionApplicationService(self.workspace_documents, self.root)
        self.workspace_validation = WorkspaceValidationApplicationService(self.root, context_resolver=self.ui_workspace_context, documents=self.workspace_documents)
        self.workspace_edit_planning = WorkspaceEditPlanApplicationService(self.root, documents=self.workspace_documents)
        self.workspace_edit_execution = WorkspaceEditExecutionApplicationService(self.root, documents=self.workspace_documents, plans=self.workspace_edit_planning)
        self.workspace_git_operations = WorkspaceGitOperationsApplicationService(self.root, context_resolver=self.ui_workspace_context, documents=self.workspace_documents)
        self.governed_job_capabilities = GovernedJobCapabilityRegistry(self.root)
        self.governed_jobs = GovernedJobFramework(self.root, registry=self.governed_job_capabilities)
        self.validation = ValidationApplicationService(self.root, enforce_workspace_paths=enforce_workspace_paths)
        self.miasi = MiasiApplicationService(self.root)
        self.maturity = MaturityApplicationService(self.root)
        self.evals = EvaluationApplicationService(self.root)
        self.repo = RepoApplicationService(self.root)
        self.reports = ReportsApplicationService(self.root, context_resolver=self.ui_workspace_context)
        self.approvals = ApprovalApplicationService(self.root)
        self.settings = SettingsApplicationService(self.root, context_resolver=self.ui_workspace_context)
        self.review = ReviewApplicationService(self.root)
        self.refactor = RefactorApplicationService(self.root)
        self.model = ModelApplicationService(self.root)
        self.history = HistoryApplicationService(self.root)
        self.observability = ObservabilityApplicationService(self.root, context_resolver=self.ui_workspace_context)
        self.governed_job_operations = GovernedJobOperationsApplicationService(self.root)
        self.quality_operations = QualityOperationsApplicationService(self.root)
        self.ai_operations = AiOperationsApplicationService(self.root)
        self.operator_dashboard = OperatorDashboardApplicationService(self.root)
        self.portfolio = PortfolioApplicationService(self.root, context_resolver=self.ui_workspace_context)
        self.boundary_policy = ApplicationBoundaryPolicy(self.root)

    def evidence_graph(
        self,
        *,
        sources_path: str = ".devpilot/evidence/evidence_graph_sources.json",
        write_report: bool = False,
        output_json: str = "outputs/reports/evidence_graph.json",
        output_markdown: str = "outputs/reports/evidence_graph.md",
    ) -> CommandResult:
        """Build the POST-H-031-A local evidence graph model.

        The graph is read-only by default and does not declare readiness. It
        models evidence, gaps, claims and no-go gates for operator visibility.
        """

        from devpilot_core.evidence_graph import EvidenceGraphBuilder, EvidenceGraphOptions

        return EvidenceGraphBuilder(
            self.root,
            EvidenceGraphOptions(
                sources_path=Path(sources_path),
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
            ),
        ).build()


    def operator_health_summary(
        self,
        *,
        config_path: str = ".devpilot/operator/operator_health_config.json",
        write_report: bool = False,
        output_json: str = "outputs/reports/operator_health_summary.json",
        output_markdown: str = "outputs/reports/operator_health_summary.md",
    ) -> CommandResult:
        """Build the POST-H-031-B local operator health summary.

        The summary is read-only and derives health from EvidenceGraph and
        source-controlled metadata. It does not execute recommended commands.
        """

        from devpilot_core.evidence_graph import OperatorHealthOptions, OperatorHealthSummaryBuilder

        return OperatorHealthSummaryBuilder(
            self.root,
            OperatorHealthOptions(
                config_path=Path(config_path),
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
            ),
        ).build()

    def gap_action_map(
        self,
        *,
        rules_path: str = ".devpilot/evidence/gap_action_rules.json",
        evidence_graph_sources_path: str = ".devpilot/evidence/evidence_graph_sources.json",
        operator_health_config_path: str = ".devpilot/operator/operator_health_config.json",
        write_report: bool = False,
        output_json: str = "outputs/reports/gap_action_map.json",
        output_markdown: str = "outputs/reports/gap_action_map.md",
    ) -> CommandResult:
        """Build the POST-H-031-C local gap-to-action map.

        The map is advisory and read-only. It converts stable evidence and
        operator health gaps into concrete, verifiable actions without running
        those actions.
        """

        from devpilot_core.evidence_graph import GapActionMapBuilder, GapActionOptions

        return GapActionMapBuilder(
            self.root,
            GapActionOptions(
                rules_path=Path(rules_path),
                evidence_graph_sources_path=Path(evidence_graph_sources_path),
                operator_health_config_path=Path(operator_health_config_path),
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
            ),
        ).build()

    def claims_no_go_dashboard(
        self,
        *,
        config_path: str = ".devpilot/operator/claims_no_go_dashboard_config.json",
        write_report: bool = False,
        output_json: str = "outputs/reports/claims_no_go_dashboard.json",
        output_markdown: str = "outputs/reports/claims_no_go_dashboard.md",
    ) -> CommandResult:
        """Build the POST-H-031-D local claims/no-go dashboard.

        The dashboard is read-only and derives claim/gate state from POST-H-025
        criteria, project state, EvidenceGraph and ProductionReadyClaimsValidator.
        It does not mutate claims, no-go gates or readiness declarations.
        """

        from devpilot_core.evidence_graph import ClaimsDashboardOptions, ClaimsNoGoDashboardBuilder

        return ClaimsNoGoDashboardBuilder(
            self.root,
            ClaimsDashboardOptions(
                config_path=Path(config_path),
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
            ),
        ).build()

    def operator_evidence_export(
        self,
        *,
        redacted: bool = False,
        dry_run: bool = True,
        write_report: bool = False,
        output_json: str = "outputs/reports/operator_evidence_export.json",
        output_markdown: str = "outputs/reports/operator_evidence_export.md",
        package_dir: str = "outputs/audit_exports/operator_evidence_export",
        observability_limit: int = 100,
    ) -> CommandResult:
        """Build the POST-H-031-E redacted operator evidence export package.

        The export is an operator/auditor UX over existing evidence summaries.
        It requires redaction, writes only when requested, and constrains all
        generated files to outputs/reports or outputs/audit_exports.
        """

        from devpilot_core.evidence_graph import OperatorEvidenceExportBuilder, OperatorEvidenceExportOptions

        return OperatorEvidenceExportBuilder(
            self.root,
            OperatorEvidenceExportOptions(
                redacted=redacted,
                dry_run=dry_run,
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
                package_dir=Path(package_dir),
                observability_limit=observability_limit,
            ),
        ).build()


    def agent_capability_inventory(
        self,
        *,
        agent_registry_path: str = ".devpilot/miasi/agent_registry.json",
        tool_registry_path: str = ".devpilot/miasi/tool_registry.json",
        policy_matrix_path: str = ".devpilot/miasi/policy_matrix.json",
        inventory_path: str = ".devpilot/agents/agent_capability_inventory.json",
        promotion_criteria_path: str = ".devpilot/agents/agent_promotion_criteria.json",
        write_report: bool = False,
        output_json: str = "outputs/reports/agent_capability_inventory.json",
        output_markdown: str = "outputs/reports/agent_capability_inventory.md",
    ) -> CommandResult:
        """Build the POST-H-032-A governed agent capability inventory.

        The inventory is read-only over runtime behavior: it classifies MIASI
        agents, allowlisted tools, risk levels, promotion candidates and no-go
        gates without executing agents, tools, providers, RAG or memory.
        """

        from devpilot_core.agents import AgentCapabilityInventoryBuilder, AgentCapabilityInventoryOptions

        return AgentCapabilityInventoryBuilder(
            self.root,
            AgentCapabilityInventoryOptions(
                agent_registry_path=Path(agent_registry_path),
                tool_registry_path=Path(tool_registry_path),
                policy_matrix_path=Path(policy_matrix_path),
                inventory_path=Path(inventory_path),
                promotion_criteria_path=Path(promotion_criteria_path),
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
            ),
        ).build()





    def multiagent_handoff_hardening(
        self,
        *,
        policy_path: str = ".devpilot/agents/multiagent_handoff_policy.json",
        agent_inventory_path: str = ".devpilot/agents/agent_capability_inventory.json",
        tool_call_policy_path: str = ".devpilot/agents/tool_call_policy.json",
        workflow_path: str = ".devpilot/workflows/sdlc_review.json",
        write_report: bool = False,
        output_json: str = "outputs/reports/multiagent_handoff_hardening_report.json",
        output_markdown: str = "outputs/reports/multiagent_handoff_hardening_report.md",
    ) -> CommandResult:
        """Evaluate POST-H-032-H deterministic multiagent handoff hardening.

        This boundary validates visible handoffs, supervisor gate, human
        checkpoints, scope isolation and observability. It is report-only and
        does not enable swarm autonomy, tools, network, external APIs, LLMs,
        connector write, plugin execution, remote execution or source mutation.
        """

        from devpilot_core.multiagent import MultiagentHandoffHardeningManager, MultiagentHandoffHardeningOptions

        return MultiagentHandoffHardeningManager(
            self.root,
            MultiagentHandoffHardeningOptions(
                policy_path=Path(policy_path),
                agent_inventory_path=Path(agent_inventory_path),
                tool_call_policy_path=Path(tool_call_policy_path),
                workflow_path=Path(workflow_path),
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
            ),
        ).evaluate()

    def mcp_fake_server_evaluation(
        self,
        *,
        contract_path: str = ".devpilot/mcp/mcp_fake_server_contract.json",
        tool_registry_path: str = ".devpilot/miasi/tool_registry.json",
        tool_call_policy_path: str = ".devpilot/agents/tool_call_policy.json",
        write_report: bool = False,
        output_json: str = "outputs/reports/mcp_fake_server_evaluation_report.json",
        output_markdown: str = "outputs/reports/mcp_fake_server_evaluation_report.md",
    ) -> CommandResult:
        """Evaluate POST-H-032-G MCP design through a local fake server.

        The boundary is design/fake-server only. It validates MCP threat model,
        MCP-to-MIASI mapping, permission model and audit trail without enabling
        real MCP, network transports, external APIs or tool execution.
        """

        from devpilot_core.mcp import McpFakeServerEvaluationManager, McpFakeServerEvaluationOptions

        return McpFakeServerEvaluationManager(
            self.root,
            McpFakeServerEvaluationOptions(
                contract_path=Path(contract_path),
                tool_registry_path=Path(tool_registry_path),
                tool_call_policy_path=Path(tool_call_policy_path),
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
            ),
        ).evaluate()

    def agent_tool_call_contract(
        self,
        *,
        policy_path: str = ".devpilot/agents/tool_call_policy.json",
        agent_inventory_path: str = ".devpilot/agents/agent_capability_inventory.json",
        tool_registry_path: str = ".devpilot/miasi/tool_registry.json",
        policy_matrix_path: str = ".devpilot/miasi/policy_matrix.json",
        limit: int = 200,
        write_report: bool = False,
        output_json: str = "outputs/reports/agent_tool_call_contract_report.json",
        output_markdown: str = "outputs/reports/agent_tool_call_contract_report.md",
    ) -> CommandResult:
        """Validate the POST-H-032-F governed agent tool-calling contract.

        The boundary is contract-only: it derives MIASI executable subset,
        validates agent/tool allowlists, enforces dry-run-first and approval
        requirements for risky tools, and does not execute real tools.
        """

        from devpilot_core.agents import AgentToolCallingContractManager, AgentToolCallingContractOptions

        return AgentToolCallingContractManager(
            self.root,
            AgentToolCallingContractOptions(
                policy_path=Path(policy_path),
                agent_inventory_path=Path(agent_inventory_path),
                tool_registry_path=Path(tool_registry_path),
                policy_matrix_path=Path(policy_matrix_path),
                limit=limit,
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
            ),
        ).validate()

    def agent_memory_model(
        self,
        *,
        action: str = "inspect",
        policy_path: str = ".devpilot/agents/agent_memory_policy.json",
        memory_dir: str = ".devpilot/agents/memory",
        limit: int = 50,
        execute: bool = False,
        write_report: bool = False,
        output_json: str = "outputs/reports/agent_memory_model_report.json",
        output_markdown: str = "outputs/reports/agent_memory_model_report.md",
    ) -> CommandResult:
        """Inspect, export or cleanup the POST-H-032-E local opt-in memory model.

        The boundary keeps semantic memory disabled by default, redacts exports,
        separates memory from formal evidence and performs cleanup only when the
        caller explicitly requests execute.
        """

        from devpilot_core.agents import AgentMemoryModelManager, AgentMemoryModelOptions

        manager = AgentMemoryModelManager(
            self.root,
            AgentMemoryModelOptions(
                policy_path=Path(policy_path),
                memory_dir=Path(memory_dir),
                limit=limit,
                execute=execute,
                dry_run=not execute,
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
            ),
        )
        if action == "inspect":
            return manager.inspect()
        if action == "export":
            return manager.export()
        if action == "cleanup":
            return manager.cleanup()
        return CommandResult(
            command="agent memory",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Unsupported agent memory action.",
            data={"summary": {"action": action}},
            findings=[Finding("AGENT_MEMORY_ACTION_UNSUPPORTED", "Unsupported agent memory action.", Severity.BLOCK, metadata={"action": action})],
        )

    def rag_agent_context(
        self,
        *,
        agent_id: str | None = None,
        query: str | None = None,
        target: str | None = None,
        bindings_path: str = ".devpilot/agents/rag_agent_bindings.json",
        index_path: str = ".devpilot/rag/docs_index.json",
        top_k: int = 5,
        write_report: bool = False,
        output_json: str = "outputs/reports/rag_agent_context_pack.json",
        output_markdown: str = "outputs/reports/rag_agent_context_pack.md",
    ) -> CommandResult:
        """Build the POST-H-032-D RAG-aware agent context pack.

        This boundary prepares deterministic local RAG context for selected
        agents with source ids, citations, freshness and insufficient-evidence
        behavior. It does not call an LLM, use network, read/write memory or
        execute tools.
        """

        from devpilot_core.agents import RagAgentContextOptions, RagAwareAgentContextBuilder

        return RagAwareAgentContextBuilder(
            self.root,
            RagAgentContextOptions(
                agent_id=agent_id,
                query=query,
                target=target,
                bindings_path=Path(bindings_path),
                index_path=Path(index_path),
                top_k=top_k,
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
            ),
        ).build()

    def local_llm_provider_health(
        self,
        *,
        policy_path: str = ".devpilot/modeling/local_llm_provider_health_policy.json",
        timeout_seconds: float = 0.2,
        probe_enabled_local: bool = False,
        write_report: bool = False,
        output_json: str = "outputs/reports/local_llm_provider_health_report.json",
        output_markdown: str = "outputs/reports/local_llm_provider_health_report.md",
    ) -> CommandResult:
        """Build the POST-H-032-B local LLM provider hardening report.

        This boundary validates Ollama/LM Studio provider governance without
        requiring real local model servers. Network probes are opt-in and only
        apply to enabled localhost providers.
        """

        from devpilot_core.modeling import LocalLlmProviderHealthOptions, LocalLlmProviderHealthReporter

        return LocalLlmProviderHealthReporter(
            self.root,
            LocalLlmProviderHealthOptions(
                policy_path=Path(policy_path),
                timeout_seconds=timeout_seconds,
                probe_enabled_local=probe_enabled_local,
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
            ),
        ).build()

    def external_api_provider_pilot(
        self,
        *,
        policy_path: str = ".devpilot/modeling/external_api_provider_pilot_policy.json",
        provider: str = "openai",
        estimated_cost_usd: float = 0.01,
        budget_limit_usd: float = 0.0,
        budget_used_usd: float = 0.0,
        allow_real_api: bool = False,
        acknowledge_risk: bool = False,
        write_report: bool = False,
        output_json: str = "outputs/reports/external_api_provider_pilot_report.json",
        output_markdown: str = "outputs/reports/external_api_provider_pilot_report.md",
    ) -> CommandResult:
        """Build the POST-H-032-C external API provider gated-pilot report.

        This boundary is ADR-backed and fake-provider-only by default. It does
        not perform real external API calls, read API key values or use network.
        Real-call options only evaluate gates and remain blocked unless future
        enablement work changes policy explicitly.
        """

        from devpilot_core.modeling import ExternalApiProviderPilotOptions, ExternalApiProviderPilotReporter

        return ExternalApiProviderPilotReporter(
            self.root,
            ExternalApiProviderPilotOptions(
                policy_path=Path(policy_path),
                provider=provider,
                estimated_cost_usd=estimated_cost_usd,
                budget_limit_usd=budget_limit_usd,
                budget_used_usd=budget_used_usd,
                allow_real_api=allow_real_api,
                acknowledge_risk=acknowledge_risk,
                write_report=write_report,
                output_json=Path(output_json),
                output_markdown=Path(output_markdown),
            ),
        ).build()

    # Backward-compatible validator facade from Sprint 18.
    def validate_frontmatter(self, path: str | Path, *, strict: bool = False) -> CommandResult:
        return self.validation.validate_frontmatter(path, strict=strict)

    def validate_artifact(self, path: str | Path, *, strict: bool = False) -> CommandResult:
        return self.validation.validate_artifact(path, strict=strict)

    def checklist_pre_code(self, *, strict: bool = True) -> CommandResult:
        return self.validation.checklist_pre_code(strict=strict)

    def readiness(self, *, strict: bool = False) -> CommandResult:
        return self.validation.readiness(strict=strict)

    def standards_status(self) -> CommandResult:
        return self.validation.standards_status()

    # Domain shortcuts intended for CLI reuse and future API route handlers.
    def guided_sdlc_transition_evaluate(
        self,
        *,
        workspace_id: str,
        transition_id: str,
        evidence: dict[str, Any] | None = None,
    ) -> CommandResult:
        return self.guided_sdlc.evaluate_transition(
            workspace_id=workspace_id,
            transition_id=transition_id,
            evidence=evidence,
        )

    def guided_sdlc_transition_preview(
        self,
        *,
        workspace_id: str,
        transition_id: str,
        evidence: dict[str, Any] | None = None,
        updated_at_utc: str,
    ) -> CommandResult:
        return self.guided_sdlc.preview_transition(
            workspace_id=workspace_id,
            transition_id=transition_id,
            evidence=evidence,
            updated_at_utc=updated_at_utc,
        )

    def guided_sdlc_project_status(
        self,
        *,
        workspace_id: str,
        observed_at_utc: str,
        expected_state_fingerprint: str | None = None,
    ) -> CommandResult:
        return self.guided_sdlc.project_status(
            workspace_id=workspace_id,
            observed_at_utc=observed_at_utc,
            expected_state_fingerprint=expected_state_fingerprint,
        )

    def guided_sdlc_next_action(
        self,
        *,
        workspace_id: str,
        observed_at_utc: str,
        expected_state_fingerprint: str | None = None,
    ) -> CommandResult:
        return self.guided_sdlc.next_action(
            workspace_id=workspace_id,
            observed_at_utc=observed_at_utc,
            expected_state_fingerprint=expected_state_fingerprint,
        )

    def guided_sdlc_project_status_primary(
        self,
        *,
        workspace_id: str | None,
        observed_at_utc: str,
        expected_state_fingerprint: str | None = None,
    ) -> CommandResult:
        return self.guided_sdlc.project_status_primary(
            workspace_id=workspace_id,
            observed_at_utc=observed_at_utc,
            expected_state_fingerprint=expected_state_fingerprint,
        )

    def guided_sdlc_reconcile_preview(
        self,
        *,
        workspace_id: str,
        updated_at_utc: str,
        observed_at_utc: str,
    ) -> CommandResult:
        return self.guided_sdlc.reconcile_preview(
            workspace_id=workspace_id,
            updated_at_utc=updated_at_utc,
            observed_at_utc=observed_at_utc,
        )

    def guided_sdlc_reconcile_execute(
        self,
        *,
        workspace_id: str,
        updated_at_utc: str,
        observed_at_utc: str,
    ) -> CommandResult:
        return self.guided_sdlc.reconcile_execute(
            workspace_id=workspace_id,
            updated_at_utc=updated_at_utc,
            observed_at_utc=observed_at_utc,
        )

    def workspace_status(self) -> CommandResult:
        return self.workspace.status()

    def miasi_validate(self, *, scope: str = "all") -> CommandResult:
        return self.miasi.validate(scope=scope)

    def eval_run(self, *, suite: str = "documentation", case_id: str | None = None, write_report: bool = False) -> CommandResult:
        return self.evals.run_documentation(suite=suite, case_id=case_id, write_report=write_report)

    def repo_inventory(self) -> CommandResult:
        return self.repo.inventory()

    def repo_analyze(self, *, target: str | Path = ".") -> CommandResult:
        return self.repo.analyze(target=target)

    def code_review(self, *, target: str | Path = ".") -> CommandResult:
        return self.review.code_review(target=target)

    def refactor_plan(self, *, target: str | Path = ".", goal: str = "", include_code_review: bool = True) -> CommandResult:
        return self.refactor.plan(target=target, goal=goal, include_code_review=include_code_review)

    def model_providers(self) -> CommandResult:
        return self.model.providers()

    def maturity_dashboard(self, *, write_report: bool = False) -> CommandResult:
        return self.maturity.dashboard(write_report=write_report)

    def maturity_dashboard_gate(self, *, write_report: bool = False) -> CommandResult:
        return self.maturity.dashboard_gate(write_report=write_report)

    def operator_dashboard_snapshot(self, *, write_report: bool = False) -> CommandResult:
        return self.operator_dashboard.dashboard(write_report=write_report)

    def production_ready_local_gate(
        self,
        *,
        write_report: bool = False,
        output_json: str = "outputs/reports/production_ready_local_report.json",
        output_markdown: str = "outputs/reports/production_ready_local_report.md",
    ) -> CommandResult:
        """Run the POST-H-025-C local production-ready declaration gate."""

        from devpilot_core.industrial.production_ready import ProductionReadyDeclarationGate, ProductionReadyDeclarationGateOptions

        return ProductionReadyDeclarationGate(
            self.root,
            options=ProductionReadyDeclarationGateOptions(
                write_report=write_report,
                output_json=output_json,
                output_markdown=output_markdown,
            ),
        ).check()

    def production_ready_local_final_declaration(
        self,
        *,
        write_report: bool = False,
        write_audit_markdown: bool = False,
        output_json: str = "outputs/reports/production_ready_local_report.json",
        output_markdown: str = "outputs/reports/production_ready_local_report.md",
        audit_markdown: str = "docs/audits/devpilot_local_production_ready_declaration.md",
    ) -> CommandResult:
        """Run the POST-H-025-E final production-ready-local declaration package."""

        from devpilot_core.industrial.production_ready import (
            ProductionReadyFinalDeclaration,
            ProductionReadyFinalDeclarationOptions,
        )

        return ProductionReadyFinalDeclaration(
            self.root,
            options=ProductionReadyFinalDeclarationOptions(
                write_report=write_report,
                write_audit_markdown=write_audit_markdown,
                output_json=output_json,
                output_markdown=output_markdown,
                audit_markdown=audit_markdown,
            ),
        ).finalize()


    def local_release_candidate_final(
        self,
        *,
        write_report: bool = False,
        criteria_path: str = ".devpilot/release/local_release_candidate_criteria.json",
        output_json: str = "outputs/reports/local_release_candidate_report.json",
        output_markdown: str = "outputs/reports/local_release_candidate_report.md",
    ) -> CommandResult:
        """Run the POST-H-026-E final local release candidate PASS/BLOCK report."""

        from devpilot_core.release_candidate import LocalReleaseCandidateOptions, LocalReleaseCandidateReporter

        return LocalReleaseCandidateReporter(
            self.root,
            LocalReleaseCandidateOptions(
                criteria_path=criteria_path,
                output_json=output_json,
                output_markdown=output_markdown,
                write_report=write_report,
            ),
        ).run()

    def portfolio_status(self, *, registry_path: str | None = None) -> CommandResult:
        return self.portfolio.status(registry_path=registry_path)

    def settings_workspace(self) -> CommandResult:
        return self.settings.workspace()

    def settings_providers(self, *, prefer_example: bool = False) -> CommandResult:
        return self.settings.providers(prefer_example=prefer_example)

    def settings_policy(self) -> CommandResult:
        return self.settings.policy()

    def settings_status(self) -> CommandResult:
        """Read-only aggregate settings status for POST-H-007-C DTO normalization."""

        steps = [
            ("workspace", self.settings_workspace()),
            ("providers", self.settings_providers()),
            ("policy", self.settings_policy()),
        ]
        findings: list[Finding] = []
        projections: dict[str, Any] = {}
        for step_id, result in steps:
            projections[step_id] = result.to_dict()
            for finding in result.findings:
                metadata = dict(finding.metadata or {})
                metadata.setdefault("settings_step", step_id)
                metadata.setdefault("source_command", result.command)
                findings.append(Finding(finding.id, finding.message, finding.severity, path=finding.path, metadata=metadata))
        codes = {result.exit_code for _, result in steps}
        if ExitCode.ERROR in codes:
            exit_code = ExitCode.ERROR
        elif ExitCode.BLOCK in codes:
            exit_code = ExitCode.BLOCK
        elif ExitCode.FAIL in codes:
            exit_code = ExitCode.FAIL
        else:
            exit_code = ExitCode.PASS
        ok = all(result.ok for _, result in steps)
        summary = {
            "operation": "settings.status",
            "steps_total": len(steps),
            "steps_passed": sum(1 for _, result in steps if result.ok),
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        return CommandResult(
            command="settings status",
            ok=ok,
            exit_code=exit_code,
            message="Settings status aggregate passed." if ok else "Settings status aggregate reported blocking findings.",
            data={"summary": summary, "settings": projections},
            findings=findings,
        )

    def settings_provider_plan(self, *, provider_id: str, changes: dict[str, Any] | None = None, actor: str = "ui-local", reason: str = "Settings UI plan-only provider change") -> CommandResult:
        return self.settings.provider_plan(provider_id=provider_id, changes=changes, actor=actor, reason=reason)

    def approvals_list(self, *, status: str | None = None, tool_id: str | None = None, action: str | None = None, limit: int = 100) -> CommandResult:
        return self.approvals.list(status=status, tool_id=tool_id, action=action, limit=limit)

    def approvals_show(self, *, approval_id: str) -> CommandResult:
        return self.approvals.show(approval_id=approval_id)

    def approvals_request(
        self,
        *,
        tool_id: str,
        action: str,
        subject: str,
        actor: str,
        reason: str,
        scope: str | None = None,
        expires_at: str | None = None,
        ttl_minutes: int = 60,
    ) -> CommandResult:
        return self.approvals.request(tool_id=tool_id, action=action, subject=subject, actor=actor, reason=reason, scope=scope, expires_at=expires_at, ttl_minutes=ttl_minutes)

    def approvals_decide(self, *, approval_id: str, decision: str, actor: str, reason: str) -> CommandResult:
        return self.approvals.decide(approval_id=approval_id, decision=decision, actor=actor, reason=reason)

    def ui_action_dry_run(self, *, action_id: str, payload: dict[str, Any] | None = None) -> CommandResult:
        """Run a UI-launched safe action in dry-run/read-only mode only.

        The UI may trigger only deterministic read/dry-run actions. Critical
        execution actions are evaluated through PolicyEngine and then blocked by
        the Sprint 71 UI contract even when an approval id is supplied; actual
        execution remains CLI/API governed by later explicit workflows.
        """

        action_payload = dict(payload or {})
        normalized = str(action_id or action_payload.get("action_id") or "").strip().lower()
        target = str(action_payload.get("target") or ".")
        goal = str(action_payload.get("goal") or "")
        approval_id = str(action_payload.get("approval_id") or "").strip() or None
        safe_actions = {
            "readiness": ("validation.readiness", lambda: self.readiness(strict=bool(action_payload.get("strict", True))), "readiness-check"),
            "validation.readiness": ("validation.readiness", lambda: self.readiness(strict=bool(action_payload.get("strict", True))), "readiness-check"),
            "code-review": ("review.code", lambda: self.code_review(target=target), "code-review"),
            "review.code": ("review.code", lambda: self.code_review(target=target), "code-review"),
            "refactor-plan": ("refactor.plan", lambda: self.refactor_plan(target=target, goal=goal, include_code_review=bool(action_payload.get("include_code_review", True))), "safe-refactor-plan"),
            "refactor.plan": ("refactor.plan", lambda: self.refactor_plan(target=target, goal=goal, include_code_review=bool(action_payload.get("include_code_review", True))), "safe-refactor-plan"),
        }
        critical_actions = {
            "patch-apply": "patch.apply",
            "patch.apply": "patch.apply",
            "refactor-execute": "refactor.execute",
            "refactor.execute": "refactor.execute",
            "rollback-execute": "rollback.execute",
            "rollback.execute": "rollback.execute",
            "tests-run-execute": "tests.run",
            "tests.run.execute": "tests.run",
            "git-push": "git.push",
            "deploy": "deploy",
        }
        if normalized in safe_actions:
            operation, runner, tool_id = safe_actions[normalized]
            policy_result = PolicyEngine(self.root).evaluate(
                PolicyRequest(
                    action="read",
                    path=target if target else None,
                    dry_run=True,
                    approval_id=approval_id,
                    tool_id=tool_id,
                    subject=operation,
                    metadata={"component": "WebUIActionLauncher", "sprint": "FUNC-SPRINT-71", "api_operation": "ui.actions.dry_run", "ui_dry_run": True},
                )
            )
            if not policy_result.ok:
                return CommandResult(
                    command="ui action dry-run",
                    ok=False,
                    exit_code=policy_result.exit_code,
                    message="PolicyEngine blocked the UI dry-run action.",
                    data={"summary": {"action_id": normalized, "operation": operation, "dry_run": True, "policy_allowed": False, "preliminary": True}, "policy": policy_result.data},
                    findings=policy_result.findings,
                )
            result = runner()
            merged_data = dict(result.data or {})
            merged_data["action_launcher"] = {
                "action_id": normalized,
                "operation": operation,
                "tool_id": tool_id,
                "dry_run": True,
                "critical": False,
                "policy_binding": True,
                "policy_allowed": True,
                "approval_id_provided": bool(approval_id),
                "ui_execution_enabled": False,
                "preliminary": True,
            }
            return CommandResult(command="ui action dry-run", ok=result.ok, exit_code=result.exit_code, message=result.message, data=merged_data, findings=result.findings)

        if normalized in critical_actions:
            tool_id = critical_actions[normalized]
            policy_result = PolicyEngine(self.root).evaluate(
                PolicyRequest(
                    action="execute",
                    path=target if target else None,
                    dry_run=True,
                    approval_id=approval_id,
                    tool_id=tool_id,
                    subject=tool_id,
                    metadata={"component": "WebUIActionLauncher", "sprint": "FUNC-SPRINT-71", "critical_action_requested": True},
                )
            )
            findings = list(policy_result.findings) + [
                Finding(
                    "UI_CRITICAL_ACTION_DISABLED_BLOCK",
                    "The Web UI cannot execute critical actions; use governed CLI/API workflows with explicit approval in future sprints.",
                    Severity.BLOCK,
                    metadata={"action_id": normalized, "tool_id": tool_id, "dry_run": True, "approval_id_provided": bool(approval_id)},
                )
            ]
            return CommandResult(
                command="ui action dry-run",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Critical actions are blocked from the Web UI.",
                data={"summary": {"action_id": normalized, "tool_id": tool_id, "dry_run": True, "critical": True, "policy_binding": True, "policy_allowed": policy_result.ok, "ui_execution_enabled": False, "preliminary": True}, "policy": policy_result.data},
                findings=findings,
            )

        return CommandResult(
            command="ui action dry-run",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Requested UI action is not exposed by the Sprint 71 dry-run contract.",
            data={"summary": {"action_id": normalized, "supported": False, "dry_run": True, "preliminary": True}, "supported_actions": sorted(safe_actions)},
            findings=[Finding("UI_ACTION_NOT_EXPOSED_BLOCK", "The requested action is not exposed by the UI dry-run launcher.", Severity.BLOCK, metadata={"action_id": normalized})],
        )

    def workspace_documents_list(self, *, limit: int = 50, offset: int = 0, query: str | None = None, extension: str | None = None, category: str | None = None) -> CommandResult:
        return self.workspace_documents.list_documents(limit=limit, offset=offset, query=query, extension=extension, category=category)

    def workspace_documents_read(self, *, document_id: str) -> CommandResult:
        return self.workspace_documents.read_document(document_id)

    def workspace_documents_metadata(self, *, document_id: str) -> CommandResult:
        return self.workspace_document_inspection.metadata(document_id)

    def workspace_documents_history(self, *, document_id: str, limit: int = 20, offset: int = 0) -> CommandResult:
        return self.workspace_document_inspection.history(document_id, limit=limit, offset=offset)

    def workspace_documents_diff(self, *, document_id: str, base_ref: str = "HEAD", max_bytes: int = 262144) -> CommandResult:
        return self.workspace_document_inspection.diff(document_id, base_ref=base_ref, max_bytes=max_bytes)

    def workspace_documents_search(self, *, query: str, limit: int = 50, offset: int = 0) -> CommandResult:
        return self.workspace_document_inspection.search(query=query, limit=limit, offset=offset)

    def workspace_documents_links(self, *, document_id: str) -> CommandResult:
        return self.workspace_document_inspection.links(document_id)

    def workspace_validations_plan(
        self,
        *,
        scopes: list[str] | None = None,
        document_ids: list[str] | None = None,
        strict: bool = True,
        timeout_seconds: int = 45,
    ) -> CommandResult:
        return self.workspace_validation.plan(scopes=scopes, document_ids=document_ids, strict=strict, timeout_seconds=timeout_seconds)

    def workspace_validations_execute(self, *, plan_id: str, plan_hash: str, plan: dict[str, Any] | None = None) -> CommandResult:
        return self.workspace_validation.execute(plan_id=plan_id, plan_hash=plan_hash, plan=plan)

    def workspace_validations_status(self, *, job_id: str) -> CommandResult:
        return self.workspace_validation.get_job(job_id=job_id)

    def workspace_traceability(self) -> CommandResult:
        return self.workspace_validation.traceability()

    def workspace_edit_plan(self, *, document_id: str, document_sha_before: str, proposed_content: str) -> CommandResult:
        return self.workspace_edit_planning.plan(document_id=document_id, document_sha_before=document_sha_before, proposed_content=proposed_content)

    def workspace_edit_plan_status(self, *, plan_id: str) -> CommandResult:
        return self.workspace_edit_planning.get_plan(plan_id=plan_id)

    def workspace_edit_plan_recheck(self, *, plan_id: str, plan_hash: str) -> CommandResult:
        return self.workspace_edit_planning.recheck(plan_id=plan_id, plan_hash=plan_hash)

    def workspace_edit_apply_approval_request(self, *, plan_id: str, plan_hash: str, actor: str, reason: str, ttl_minutes: int = 15) -> CommandResult:
        return self.workspace_edit_execution.request_apply_approval(plan_id=plan_id, plan_hash=plan_hash, actor=actor, reason=reason, ttl_minutes=ttl_minutes)

    def workspace_edit_apply(self, *, plan_id: str, plan_hash: str, approval_id: str, actor: str) -> CommandResult:
        return self.workspace_edit_execution.apply(plan_id=plan_id, plan_hash=plan_hash, approval_id=approval_id, actor=actor)

    def workspace_edit_execution_status(self, *, execution_id: str) -> CommandResult:
        return self.workspace_edit_execution.get_execution(execution_id=execution_id)

    def workspace_edit_rollback_approval_request(self, *, execution_id: str, actor: str, reason: str, ttl_minutes: int = 15) -> CommandResult:
        return self.workspace_edit_execution.request_rollback_approval(execution_id=execution_id, actor=actor, reason=reason, ttl_minutes=ttl_minutes)

    def workspace_edit_rollback(self, *, execution_id: str, approval_id: str, actor: str) -> CommandResult:
        return self.workspace_edit_execution.rollback(execution_id=execution_id, approval_id=approval_id, actor=actor)

    def workspace_git_status(self) -> CommandResult:
        return self.workspace_git_operations.status()

    def workspace_git_history(self, *, limit: int = 20) -> CommandResult:
        return self.workspace_git_operations.history(limit=limit)

    def workspace_git_compare(self, *, base_ref: str = "HEAD", head_ref: str = "HEAD") -> CommandResult:
        return self.workspace_git_operations.compare(base_ref=base_ref, head_ref=head_ref)

    def workspace_git_plan(self, *, document_ids: list[str], commit_message: str, author_name: str, author_email: str) -> CommandResult:
        return self.workspace_git_operations.plan_commit(document_ids=document_ids, commit_message=commit_message, author_name=author_name, author_email=author_email)

    def workspace_git_plan_status(self, *, plan_id: str) -> CommandResult:
        return self.workspace_git_operations.get_plan(plan_id=plan_id)

    def workspace_git_stage_approval_request(self, *, plan_id: str, plan_hash: str, actor: str, reason: str, ttl_minutes: int = 15) -> CommandResult:
        return self.workspace_git_operations.request_stage_approval(plan_id=plan_id, plan_hash=plan_hash, actor=actor, reason=reason, ttl_minutes=ttl_minutes)

    def workspace_git_stage(self, *, plan_id: str, plan_hash: str, approval_id: str, actor: str) -> CommandResult:
        return self.workspace_git_operations.stage(plan_id=plan_id, plan_hash=plan_hash, approval_id=approval_id, actor=actor)

    def workspace_git_execution_status(self, *, execution_id: str) -> CommandResult:
        return self.workspace_git_operations.get_execution(execution_id=execution_id)

    def workspace_git_commit_approval_request(self, *, stage_execution_id: str, actor: str, reason: str, ttl_minutes: int = 15) -> CommandResult:
        return self.workspace_git_operations.request_commit_approval(stage_execution_id=stage_execution_id, actor=actor, reason=reason, ttl_minutes=ttl_minutes)

    def workspace_git_commit(self, *, stage_execution_id: str, approval_id: str, actor: str) -> CommandResult:
        return self.workspace_git_operations.commit(stage_execution_id=stage_execution_id, approval_id=approval_id, actor=actor)

    def workspace_git_branch_plan(self, *, branch_name: str) -> CommandResult:
        return self.workspace_git_operations.plan_branch_create(branch_name=branch_name)

    def workspace_git_branch_approval_request(self, *, plan_id: str, plan_hash: str, actor: str, reason: str, ttl_minutes: int = 15) -> CommandResult:
        return self.workspace_git_operations.request_branch_approval(plan_id=plan_id, plan_hash=plan_hash, actor=actor, reason=reason, ttl_minutes=ttl_minutes)

    def workspace_git_branch_create(self, *, plan_id: str, plan_hash: str, approval_id: str, actor: str) -> CommandResult:
        return self.workspace_git_operations.create_branch(plan_id=plan_id, plan_hash=plan_hash, approval_id=approval_id, actor=actor)

    def reports_list(self, *, limit: int = 50, offset: int = 0, severity: str | None = None, status: str | None = None, command: str | None = None, query: str | None = None, scope: str | None = None) -> CommandResult:
        return self.reports.list_reports(limit=limit, offset=offset, severity=severity, status=status, command=command, query=query, scope=scope)

    def reports_read(self, *, report_id: str, format: str = "json", max_chars: int = 20000) -> CommandResult:
        return self.reports.read_report(report_id, format=format, max_chars=max_chars)

    def jobs_list(self, *, workspace_id: str | None = None, capability_id: str | None = None, status: str | None = None, limit: int = 50, offset: int = 0) -> CommandResult:
        return self.governed_job_operations.list_jobs(workspace_id=workspace_id, capability_id=capability_id, status=status, limit=limit, offset=offset)

    def jobs_inspect(self, *, job_id: str) -> CommandResult:
        return self.governed_job_operations.inspect(job_id=job_id)

    def jobs_logs(self, *, job_id: str, cursor: int = 0, limit: int = 100) -> CommandResult:
        return self.governed_job_operations.read_logs(job_id=job_id, cursor=cursor, limit=limit)

    def jobs_cancel(self, *, job_id: str, actor: str, reason: str) -> CommandResult:
        return self.governed_job_operations.request_cancel(job_id=job_id, actor=actor, reason=reason)

    def jobs_retry(self, *, job_id: str, actor: str, reason: str) -> CommandResult:
        return self.governed_job_operations.retry(job_id=job_id, actor=actor, reason=reason)

    def jobs_reconcile(self, *, stale_after_seconds: int = 120) -> CommandResult:
        return self.governed_job_operations.reconcile_orphans(stale_after_seconds=stale_after_seconds)

    def jobs_record_progress(self, *, job_id: str, phase: str, progress_percent: int, worker_pid: int | None = None, message: str | None = None) -> CommandResult:
        return self.governed_job_operations.record_progress(job_id=job_id, phase=phase, progress_percent=progress_percent, worker_pid=worker_pid, message=message)

    def quality_operations_catalog(self) -> CommandResult:
        return self.quality_operations.catalog()

    def quality_baseline(self) -> CommandResult:
        return self.quality_operations.baseline()

    def quality_test_impact_plan(self, *, changed_paths: list[str]) -> CommandResult:
        return self.quality_operations.test_impact_plan(changed_paths=changed_paths)

    def quality_job_plan(self, *, operation_id: str, workspace_id: str, parameters: dict[str, Any], idempotency_key: str, approval_id: str | None = None, full_regression_confirmation: str | None = None) -> CommandResult:
        return self.quality_operations.plan_job(operation_id=operation_id, workspace_id=workspace_id, parameters=parameters, idempotency_key=idempotency_key, approval_id=approval_id, full_regression_confirmation=full_regression_confirmation)

    def quality_job_execute(self, *, job_id: str) -> CommandResult:
        return self.quality_operations.execute_job(job_id=job_id)

    def quality_evidence_package(self, *, limit: int = 100) -> CommandResult:
        return self.quality_operations.package_evidence(limit=limit)

    def ai_operations_catalog(self) -> CommandResult:
        return self.ai_operations.catalog()

    def ai_status(self) -> CommandResult:
        return self.ai_operations.status()

    def ai_job_plan(self, *, operation_id: str, workspace_id: str, parameters: dict[str, Any], idempotency_key: str, approval_id: str | None = None) -> CommandResult:
        return self.ai_operations.plan_job(operation_id=operation_id, workspace_id=workspace_id, parameters=parameters, idempotency_key=idempotency_key, approval_id=approval_id)

    def ai_job_execute(self, *, job_id: str) -> CommandResult:
        return self.ai_operations.execute_job(job_id=job_id)

    def ai_job_result(self, *, job_id: str) -> CommandResult:
        return self.ai_operations.result(job_id=job_id)

    def ai_evidence_package(self, *, limit: int = 100) -> CommandResult:
        return self.ai_operations.package_evidence(limit=limit)

    def trace_report(self, *, limit: int = 20, include_events: bool = True, include_metrics: bool = True, scope: str = "active") -> CommandResult:
        return self.observability.trace_report(limit=limit, include_events=include_events, include_metrics=include_metrics, scope=scope)

    def trace_inspect(self, trace_id: str, *, limit: int = 100, scope: str = "active") -> CommandResult:
        return self.observability.trace_inspect(trace_id, limit=limit, scope=scope)

    def metrics_summary(self, *, category: str | None = None, limit: int = 50, scope: str = "active") -> CommandResult:
        return self.observability.metrics_summary(category=category, limit=limit, scope=scope)

    def history_list(self, *, limit: int = 10) -> CommandResult:
        return self.history.list_runs(limit=limit)

    def as_application_response(self, result: CommandResult, *, operation: str | None = None) -> ApplicationResponse:
        return ApplicationResponse.from_command_result(result, operation=operation)

    def handle(self, request: ApplicationRequest) -> ApplicationResponse:
        """Execute a supported ApplicationRequest and return ApplicationResponse.

        This is intentionally a local in-process dispatcher, not an HTTP router.
        Sprint 66/67 can map API endpoints to these operations without allowing
        future UI code to import validators, repo engines, AgentOps or model
        internals directly.
        """

        result = self.execute(request)
        return self.as_application_response(result, operation=request.operation)

    def execute(self, request: ApplicationRequest) -> CommandResult:
        request = normalize_priority_application_request(request)
        operation = request.operation.strip()
        payload = dict(request.payload or {})
        dispatch = _operation_dispatch(self)
        handler = dispatch.get(operation)
        if handler is None:
            return CommandResult(
                command="app execute",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="ApplicationService operation is not exposed by the v2 contract.",
                data={
                    "summary": {
                        "operation": operation,
                        "supported": False,
                        "preliminary": True,
                        "external_api_used": False,
                        "network_used": False,
                    },
                    "supported_operations": sorted(dispatch),
                },
                findings=[
                    Finding(
                        id="APPLICATION_OPERATION_NOT_EXPOSED",
                        message="Requested operation is not part of the ApplicationService v2 contract.",
                        severity=Severity.BLOCK,
                        metadata={"operation": operation},
                    )
                ],
            )

        boundary_decision = self.boundary_policy.evaluate(request)
        if not boundary_decision.allowed:
            return boundary_decision.to_command_result()
        return handler(payload)

    def application_contract(self) -> CommandResult:
        capabilities = _capabilities()
        routes = _routes()
        domains = _domain_summaries()
        data: dict[str, Any] = {
            "summary": {
                "contract": "DevPilotApplicationServiceContract",
                "schema_version": "2.0",
                "capabilities_total": len(capabilities),
                "routes_total": len(routes),
                "domains_total": len(domains),
                "ui_implemented": True,
                "api_implemented": True,
                "api_local_mvp_implemented": True,
                "api_security_implemented": True,
                "api_token_required": True,
                "api_cors_restricted": True,
                "api_cors_wildcard_enabled": False,
                "api_policy_binding_enabled": True,
                "api_security_status": "secured-initial",
                "api_consumed_by_web_ui": True,
                "api_default_host": "127.0.0.1",
                "api_default_port": 8787,
                "api_contract_defined": True,
                "api_contract_version": "v1",
                "openapi_contract_defined": True,
                "openapi_contract_path": "docs/07_interfaces/openapi_v1.json",
                "api_service_mapping_path": "docs/07_interfaces/api_service_mapping.md",
                "visual_strategy": "web_ui_first",
                "api_local_planned": True,
                "web_ui_local_planned": True,
                "web_ui_local_implemented": True,
                "web_ui_status": "implemented-initial",
                "web_ui_path": "ui/web",
                "web_ui_api_only": True,
                "web_ui_read_only": False,
                "web_ui_source_write_mode": "approval-gated-atomic-uoc005",
                "web_ui_generic_patch_apply_enabled": False,
                "web_ui_generic_rollback_enabled": False,
                "web_ui_governed_git_write_enabled": True,
                "web_ui_governed_git_write_mode": "approval-gated-typed-local-uoc006",
                "web_ui_generic_git_write_enabled": False,
                "web_ui_git_push_enabled": False,
                "web_ui_git_force_push_enabled": False,
                "web_ui_git_reset_hard_enabled": False,
                "web_ui_git_rebase_enabled": False,
                "web_ui_git_branch_delete_enabled": False,
                "web_ui_real_future": True,
                "desktop_deferred": True,
                "desktop_ready_for_shell": False,
                "web_ready_for_shell": True,
                "web_dashboard_ready": True,
                "report_viewer_implemented": True,
                "trace_viewer_implemented": True,
                "report_trace_viewer_status": "implemented-initial",
                "approval_center_implemented": True,
                "approval_center_status": "implemented-initial",
                "dry_run_action_launcher_implemented": True,
                "web_ui_actions_dry_run_only": False,
                "web_ui_critical_actions_blocked": False,
                "web_ui_critical_actions_governed": True,
                "web_ui_unregistered_critical_actions_blocked": True,
                "settings_ui_implemented": True,
                "settings_ui_status": "implemented-initial",
                "settings_ui_read_only": True,
                "settings_provider_editor_plan_only": True,
                "settings_policy_editor_enabled": False,
                "settings_secrets_redacted": True,
                "web_ui_reports_api_only": True,
                "web_ui_traces_api_only": True,
                "external_api_required": False,
                "application_service_v2": True,
                "domain_facades_enabled": True,
                "phase_f_closed": True,
                "visual_product_mvp_release": True,
                "visual_product_quality_gate": True,
                "visual_product_quality_gate_path": "scripts/visual_product_smoke.py",
                "visual_product_release_manifest_path": "docs/release/release_manifest_visual_mvp.json",
                "phase_f_closure_report_path": "docs/audits/phase_f_visual_product_closure_report.md",
                "web_real_evolution_planned": True,
                "next_phase": "FASE-G-PRODUCTIZACION-RELEASE",
                "next_sprint": "FUNC-SPRINT-74",
                "preliminary": True,
            },
            "domains": domains,
            "capabilities": [capability.to_dict() for capability in capabilities],
            "routes": [route.to_dict() for route in routes],
            "dto_contracts": {
                "request": "ApplicationRequest",
                "response": "ApplicationResponse",
                "capability": "ServiceCapability",
                "route": "InterfaceRouteContract",
            },
            "preliminary": True,
            "notes": [
                "FUNC-SPRINT-73 closes Fase F with a Visual Product Quality Gate, visual MVP release manifest and Web-real evolution decision.",
                "FUNC-SPRINT-72 adds Settings UI for workspace/providers/policy in read-only and provider plan-only mode with secret redaction.",
                "FUNC-SPRINT-71 adds Approval Center and a dry-run Action Launcher; critical execution remains blocked from the Web UI.",
                "FUNC-SPRINT-70 adds Report Viewer and Trace Viewer over local API only; the UI does not read outputs/ directly.",
                "FUNC-SPRINT-69 adds a local Web UI MVP under ui/web that consumes only /api/v1 and remains read-only.",
                "FUNC-SPRINT-65 exposes domain application services for future API local and Web UI integration.",
                "FUNC-SPRINT-66 defines static API Contract v1 and OpenAPI preliminary artifacts without implementing an HTTP server.",
                "FUNC-SPRINT-67 implements the local FastAPI MVP in src/devpilot_core/interfaces/api, still without Web frontend or Desktop shell.",
                "FUNC-SPRINT-68 adds local API security controls: token, restricted CORS, security headers and PolicyEngine binding.",
                "API route handlers call ApplicationService/DomainService methods instead of importing DevPilot Core modules directly.",
                "Operations with side effects remain dry-run/report-only and protected by token/policy gates before future UI consumption.",
            ],
        }
        return CommandResult(
            command="app contract",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Application service v2 contract is available for CLI, secured local API MVP, Web UI viewers, Approval Center, Settings UI and Fase F visual MVP closure; desktop is deferred.",
            data=data,
            findings=[
                Finding(
                    id="APP_CONTRACT_V2_PASS",
                    message="ApplicationService v2 exposes domain facades plus secured local API route contracts, Web UI viewers, Approval Center, Settings UI and Fase F visual MVP closure.",
                    severity=Severity.INFO,
                    metadata={"domains_total": len(domains), "capabilities_total": len(capabilities)},
                )
            ],
        )

    def _resolve_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        if self.enforce_workspace_paths:
            try:
                candidate.relative_to(self.root)
            except ValueError as exc:
                raise ValueError(f"ApplicationService only accepts paths inside the workspace: {_display_path(path)}") from exc
        return candidate


OperationHandler = Callable[[dict[str, Any]], CommandResult]


def _operation_dispatch(service: ApplicationService) -> dict[str, OperationHandler]:
    return {
        "workspace.status": lambda payload: service.workspace_status(),
        "workspace.documents.list": lambda payload: service.workspace_documents_list(limit=int(payload.get("limit", 50)), offset=int(payload.get("offset", 0)), query=payload.get("query"), extension=payload.get("extension"), category=payload.get("category")),
        "workspace.documents.read": lambda payload: service.workspace_documents_read(document_id=str(payload.get("document_id", ""))),
        "workspace.documents.metadata": lambda payload: service.workspace_documents_metadata(document_id=str(payload.get("document_id", ""))),
        "workspace.documents.history": lambda payload: service.workspace_documents_history(document_id=str(payload.get("document_id", "")), limit=int(payload.get("limit", 20)), offset=int(payload.get("offset", 0))),
        "workspace.documents.diff": lambda payload: service.workspace_documents_diff(document_id=str(payload.get("document_id", "")), base_ref=str(payload.get("base_ref", "HEAD")), max_bytes=int(payload.get("max_bytes", 262144))),
        "workspace.documents.search": lambda payload: service.workspace_documents_search(query=str(payload.get("query", "")), limit=int(payload.get("limit", 50)), offset=int(payload.get("offset", 0))),
        "workspace.documents.links": lambda payload: service.workspace_documents_links(document_id=str(payload.get("document_id", ""))),
        "workspace.validations.plan": lambda payload: service.workspace_validations_plan(
            scopes=list(payload.get("scopes", [])) if isinstance(payload.get("scopes"), list) else None,
            document_ids=list(payload.get("document_ids", [])) if isinstance(payload.get("document_ids"), list) else None,
            strict=bool(payload.get("strict", True)),
            timeout_seconds=int(payload.get("timeout_seconds", 45)),
        ),
        "workspace.validations.execute": lambda payload: service.workspace_validations_execute(
            plan_id=str(payload.get("plan_id", "")),
            plan_hash=str(payload.get("plan_hash", "")),
            plan=payload.get("plan") if isinstance(payload.get("plan"), dict) else None,
        ),
        "workspace.validations.status": lambda payload: service.workspace_validations_status(job_id=str(payload.get("job_id", ""))),
        "workspace.traceability": lambda payload: service.workspace_traceability(),
        "workspace.edits.plan": lambda payload: service.workspace_edit_plan(
            document_id=str(payload.get("document_id", "")),
            document_sha_before=str(payload.get("document_sha_before", "")),
            proposed_content=str(payload.get("proposed_content", "")),
        ),
        "workspace.edits.status": lambda payload: service.workspace_edit_plan_status(plan_id=str(payload.get("plan_id", ""))),
        "workspace.edits.recheck": lambda payload: service.workspace_edit_plan_recheck(
            plan_id=str(payload.get("plan_id", "")),
            plan_hash=str(payload.get("plan_hash", "")),
        ),
        "workspace.edits.approval_request": lambda payload: service.workspace_edit_apply_approval_request(
            plan_id=str(payload.get("plan_id", "")), plan_hash=str(payload.get("plan_hash", "")), actor=str(payload.get("actor", "local-owner")), reason=str(payload.get("reason", "")), ttl_minutes=int(payload.get("ttl_minutes", 15))
        ),
        "workspace.edits.apply": lambda payload: service.workspace_edit_apply(
            plan_id=str(payload.get("plan_id", "")), plan_hash=str(payload.get("plan_hash", "")), approval_id=str(payload.get("approval_id", "")), actor=str(payload.get("actor", "local-owner"))
        ),
        "workspace.edits.execution_status": lambda payload: service.workspace_edit_execution_status(execution_id=str(payload.get("execution_id", ""))),
        "workspace.edits.rollback_approval_request": lambda payload: service.workspace_edit_rollback_approval_request(
            execution_id=str(payload.get("execution_id", "")), actor=str(payload.get("actor", "local-owner")), reason=str(payload.get("reason", "")), ttl_minutes=int(payload.get("ttl_minutes", 15))
        ),
        "workspace.edits.rollback": lambda payload: service.workspace_edit_rollback(
            execution_id=str(payload.get("execution_id", "")), approval_id=str(payload.get("approval_id", "")), actor=str(payload.get("actor", "local-owner"))
        ),
        "workspace.git.status": lambda payload: service.workspace_git_status(),
        "workspace.git.history": lambda payload: service.workspace_git_history(limit=int(payload.get("limit", 20))),
        "workspace.git.compare": lambda payload: service.workspace_git_compare(base_ref=str(payload.get("base_ref", "HEAD")), head_ref=str(payload.get("head_ref", "HEAD"))),
        "workspace.git.plan": lambda payload: service.workspace_git_plan(document_ids=list(payload.get("document_ids") or []), commit_message=str(payload.get("commit_message", "")), author_name=str(payload.get("author_name", "")), author_email=str(payload.get("author_email", ""))),
        "workspace.git.plan_status": lambda payload: service.workspace_git_plan_status(plan_id=str(payload.get("plan_id", ""))),
        "workspace.git.stage_approval_request": lambda payload: service.workspace_git_stage_approval_request(plan_id=str(payload.get("plan_id", "")), plan_hash=str(payload.get("plan_hash", "")), actor=str(payload.get("actor", "local-owner")), reason=str(payload.get("reason", "")), ttl_minutes=int(payload.get("ttl_minutes", 15))),
        "workspace.git.stage": lambda payload: service.workspace_git_stage(plan_id=str(payload.get("plan_id", "")), plan_hash=str(payload.get("plan_hash", "")), approval_id=str(payload.get("approval_id", "")), actor=str(payload.get("actor", "local-owner"))),
        "workspace.git.execution_status": lambda payload: service.workspace_git_execution_status(execution_id=str(payload.get("execution_id", ""))),
        "workspace.git.commit_approval_request": lambda payload: service.workspace_git_commit_approval_request(stage_execution_id=str(payload.get("stage_execution_id", "")), actor=str(payload.get("actor", "local-owner")), reason=str(payload.get("reason", "")), ttl_minutes=int(payload.get("ttl_minutes", 15))),
        "workspace.git.commit": lambda payload: service.workspace_git_commit(stage_execution_id=str(payload.get("stage_execution_id", "")), approval_id=str(payload.get("approval_id", "")), actor=str(payload.get("actor", "local-owner"))),
        "workspace.git.branch_plan": lambda payload: service.workspace_git_branch_plan(branch_name=str(payload.get("branch_name", ""))),
        "workspace.git.branch_approval_request": lambda payload: service.workspace_git_branch_approval_request(plan_id=str(payload.get("plan_id", "")), plan_hash=str(payload.get("plan_hash", "")), actor=str(payload.get("actor", "local-owner")), reason=str(payload.get("reason", "")), ttl_minutes=int(payload.get("ttl_minutes", 15))),
        "workspace.git.branch_create": lambda payload: service.workspace_git_branch_create(plan_id=str(payload.get("plan_id", "")), plan_hash=str(payload.get("plan_hash", "")), approval_id=str(payload.get("approval_id", "")), actor=str(payload.get("actor", "local-owner"))),
        "app.contract": lambda payload: service.application_contract(),
        "standards.status": lambda payload: service.standards_status(),
        "validators.validate_frontmatter": lambda payload: service.validate_frontmatter(str(payload.get("path", "")), strict=bool(payload.get("strict", False))),
        "validators.validate_artifact": lambda payload: service.validate_artifact(str(payload.get("path", "")), strict=bool(payload.get("strict", False))),
        "validators.readiness": lambda payload: service.readiness(strict=bool(payload.get("strict", False))),
        "validation.frontmatter": lambda payload: service.validate_frontmatter(str(payload.get("path", "")), strict=bool(payload.get("strict", False))),
        "validation.artifact": lambda payload: service.validate_artifact(str(payload.get("path", "")), strict=bool(payload.get("strict", False))),
        "validation.readiness": lambda payload: service.readiness(strict=bool(payload.get("strict", False))),
        "validation.gateway": lambda payload: service.validation.gateway(scope=str(payload.get("scope", "all"))),
        "validation.docs": lambda payload: service.validation.gateway(scope="docs"),
        "validation.contracts": lambda payload: service.validation.gateway(scope="contracts"),
        "miasi.validate": lambda payload: service.miasi_validate(scope=str(payload.get("scope", "all"))),
        "maturity.dashboard": lambda payload: service.maturity_dashboard(write_report=bool(payload.get("write_report", False))),
        "maturity.dashboard_gate": lambda payload: service.maturity_dashboard_gate(write_report=bool(payload.get("write_report", False))),
        "operator.dashboard": lambda payload: service.operator_dashboard_snapshot(write_report=bool(payload.get("write_report", False))),
        "evidence.graph": lambda payload: service.evidence_graph(
            sources_path=str(payload.get("sources_path", ".devpilot/evidence/evidence_graph_sources.json")),
            write_report=bool(payload.get("write_report", False)),
            output_json=str(payload.get("output_json", "outputs/reports/evidence_graph.json")),
            output_markdown=str(payload.get("output_markdown", "outputs/reports/evidence_graph.md")),
        ),
        "operator.health": lambda payload: service.operator_health_summary(
            config_path=str(payload.get("config_path", ".devpilot/operator/operator_health_config.json")),
            write_report=bool(payload.get("write_report", False)),
            output_json=str(payload.get("output_json", "outputs/reports/operator_health_summary.json")),
            output_markdown=str(payload.get("output_markdown", "outputs/reports/operator_health_summary.md")),
        ),
        "operator.gaps": lambda payload: service.gap_action_map(
            rules_path=str(payload.get("rules_path", ".devpilot/evidence/gap_action_rules.json")),
            evidence_graph_sources_path=str(payload.get("evidence_graph_sources_path", ".devpilot/evidence/evidence_graph_sources.json")),
            operator_health_config_path=str(payload.get("operator_health_config_path", ".devpilot/operator/operator_health_config.json")),
            write_report=bool(payload.get("write_report", False)),
            output_json=str(payload.get("output_json", "outputs/reports/gap_action_map.json")),
            output_markdown=str(payload.get("output_markdown", "outputs/reports/gap_action_map.md")),
        ),
        "operator.claims_no_go": lambda payload: service.claims_no_go_dashboard(
            config_path=str(payload.get("config_path", ".devpilot/operator/claims_no_go_dashboard_config.json")),
            write_report=bool(payload.get("write_report", False)),
            output_json=str(payload.get("output_json", "outputs/reports/claims_no_go_dashboard.json")),
            output_markdown=str(payload.get("output_markdown", "outputs/reports/claims_no_go_dashboard.md")),
        ),
        "operator.evidence_export": lambda payload: service.operator_evidence_export(
            redacted=bool(payload.get("redacted", False)),
            dry_run=bool(payload.get("dry_run", True)),
            write_report=bool(payload.get("write_report", False)),
            output_json=str(payload.get("output_json", "outputs/reports/operator_evidence_export.json")),
            output_markdown=str(payload.get("output_markdown", "outputs/reports/operator_evidence_export.md")),
            package_dir=str(payload.get("package_dir", "outputs/audit_exports/operator_evidence_export")),
            observability_limit=int(payload.get("observability_limit", 100)),
        ),
        "portfolio.status": lambda payload: service.portfolio_status(registry_path=(str(payload.get("registry_path")) if payload.get("registry_path") else None)),
        "guided_sdlc.transition.evaluate": lambda payload: service.guided_sdlc_transition_evaluate(workspace_id=str(payload.get("workspace_id", "")), transition_id=str(payload.get("transition_id", "")), evidence=dict(payload.get("evidence") or {})),
        "guided_sdlc.transition.preview": lambda payload: service.guided_sdlc_transition_preview(workspace_id=str(payload.get("workspace_id", "")), transition_id=str(payload.get("transition_id", "")), evidence=dict(payload.get("evidence") or {}), updated_at_utc=str(payload.get("updated_at_utc", ""))),
        "guided_sdlc.project.status": lambda payload: service.guided_sdlc_project_status(workspace_id=str(payload.get("workspace_id", "")), observed_at_utc=str(payload.get("observed_at_utc", "")), expected_state_fingerprint=(str(payload.get("expected_state_fingerprint")) if payload.get("expected_state_fingerprint") else None)),
        "guided_sdlc.next_action": lambda payload: service.guided_sdlc_next_action(workspace_id=str(payload.get("workspace_id", "")), observed_at_utc=str(payload.get("observed_at_utc", "")), expected_state_fingerprint=(str(payload.get("expected_state_fingerprint")) if payload.get("expected_state_fingerprint") else None)),
        "guided_sdlc.project_status": lambda payload: service.guided_sdlc_project_status_primary(workspace_id=(str(payload.get("workspace_id")) if payload.get("workspace_id") else None), observed_at_utc=str(payload.get("observed_at_utc", "")), expected_state_fingerprint=(str(payload.get("expected_state_fingerprint")) if payload.get("expected_state_fingerprint") else None)),
        "guided_sdlc.reconcile.preview": lambda payload: service.guided_sdlc_reconcile_preview(workspace_id=str(payload.get("workspace_id", "")), updated_at_utc=str(payload.get("updated_at_utc", "")), observed_at_utc=str(payload.get("observed_at_utc", ""))),
        "guided_sdlc.reconcile.execute": lambda payload: service.guided_sdlc_reconcile_execute(workspace_id=str(payload.get("workspace_id", "")), updated_at_utc=str(payload.get("updated_at_utc", "")), observed_at_utc=str(payload.get("observed_at_utc", ""))),
                "evals.documentation.run": lambda payload: service.eval_run(suite=str(payload.get("suite", "documentation")), case_id=payload.get("case_id")),
        "repo.inventory": lambda payload: service.repo_inventory(),
        "reports.list": lambda payload: service.reports_list(limit=int(payload.get("limit", 50)), offset=int(payload.get("offset", 0)), severity=payload.get("severity"), status=payload.get("status"), command=payload.get("command"), query=payload.get("query"), scope=payload.get("scope")),
        "reports.read": lambda payload: service.reports_read(report_id=str(payload.get("report_id", "")), format=str(payload.get("format", "json")), max_chars=int(payload.get("max_chars", 20000))),
        "approvals.list": lambda payload: service.approvals_list(status=payload.get("status"), tool_id=payload.get("tool_id"), action=payload.get("action"), limit=int(payload.get("limit", 100))),
        "approvals.show": lambda payload: service.approvals_show(approval_id=str(payload.get("approval_id", ""))),
        "approvals.request": lambda payload: service.approvals_request(tool_id=str(payload.get("tool_id", "")), action=str(payload.get("action", "")), subject=str(payload.get("subject", "")), actor=str(payload.get("actor", "ui-local")), reason=str(payload.get("reason", "Requested from UI.")), scope=payload.get("scope"), expires_at=payload.get("expires_at"), ttl_minutes=int(payload.get("ttl_minutes", 60))),
        "approvals.approve": lambda payload: service.approvals_decide(approval_id=str(payload.get("approval_id", "")), decision="approved", actor=str(payload.get("actor", "ui-local")), reason=str(payload.get("reason", "Approved from UI."))),
        "approvals.deny": lambda payload: service.approvals_decide(approval_id=str(payload.get("approval_id", "")), decision="denied", actor=str(payload.get("actor", "ui-local")), reason=str(payload.get("reason", "Denied from UI."))),
        "ui.actions.dry_run": lambda payload: service.ui_action_dry_run(action_id=str(payload.get("action_id", "")), payload=payload),
        "settings.workspace": lambda payload: service.settings_workspace(),
        "settings.providers": lambda payload: service.settings_providers(prefer_example=bool(payload.get("prefer_example", False))),
        "settings.policy": lambda payload: service.settings_policy(),
        "settings.status": lambda payload: service.settings_status(),
        "settings.providers.plan": lambda payload: service.settings_provider_plan(provider_id=str(payload.get("provider_id", "")), changes=dict(payload.get("changes") or {}), actor=str(payload.get("actor", "ui-local")), reason=str(payload.get("reason", "Settings UI plan-only provider change"))),
        "repo.analyze": lambda payload: service.repo_analyze(target=str(payload.get("target", "."))),
        "review.code": lambda payload: service.code_review(target=str(payload.get("target", "."))),
        "refactor.plan": lambda payload: service.refactor_plan(target=str(payload.get("target", ".")), goal=str(payload.get("goal", "")), include_code_review=bool(payload.get("include_code_review", True))),
        "model.providers": lambda payload: service.model_providers(),
        "jobs.list": lambda payload: service.jobs_list(workspace_id=payload.get("workspace_id"), capability_id=payload.get("capability_id"), status=payload.get("status"), limit=int(payload.get("limit", 50)), offset=int(payload.get("offset", 0))),
        "jobs.inspect": lambda payload: service.jobs_inspect(job_id=str(payload.get("job_id", ""))),
        "jobs.logs": lambda payload: service.jobs_logs(job_id=str(payload.get("job_id", "")), cursor=int(payload.get("cursor", 0)), limit=int(payload.get("limit", 100))),
        "jobs.cancel": lambda payload: service.jobs_cancel(job_id=str(payload.get("job_id", "")), actor=str(payload.get("actor", "local-owner")), reason=str(payload.get("reason", "Operator cancellation"))),
        "jobs.retry": lambda payload: service.jobs_retry(job_id=str(payload.get("job_id", "")), actor=str(payload.get("actor", "local-owner")), reason=str(payload.get("reason", "Operator retry"))),
        "jobs.reconcile": lambda payload: service.jobs_reconcile(stale_after_seconds=int(payload.get("stale_after_seconds", 120))),
        "quality.operations": lambda payload: service.quality_operations_catalog(),
        "quality.baseline": lambda payload: service.quality_baseline(),
        "quality.test_impact_plan": lambda payload: service.quality_test_impact_plan(changed_paths=list(payload.get("changed_paths", []))),
        "quality.jobs.plan": lambda payload: service.quality_job_plan(operation_id=str(payload.get("operation_id", "")), workspace_id=str(payload.get("workspace_id", "devpilot-local")), parameters=dict(payload.get("parameters", {})), idempotency_key=str(payload.get("idempotency_key", "")), approval_id=(str(payload["approval_id"]) if payload.get("approval_id") else None), full_regression_confirmation=(str(payload["full_regression_confirmation"]) if payload.get("full_regression_confirmation") else None)),
        "quality.jobs.execute": lambda payload: service.quality_job_execute(job_id=str(payload.get("job_id", ""))),
        "quality.evidence_package": lambda payload: service.quality_evidence_package(limit=int(payload.get("limit", 100))),
        "ai.operations": lambda payload: service.ai_operations_catalog(),
        "ai.status": lambda payload: service.ai_status(),
        "ai.jobs.plan": lambda payload: service.ai_job_plan(operation_id=str(payload.get("operation_id", "")), workspace_id=str(payload.get("workspace_id", "devpilot-local")), parameters=dict(payload.get("parameters", {})), idempotency_key=str(payload.get("idempotency_key", "")), approval_id=(str(payload["approval_id"]) if payload.get("approval_id") else None)),
        "ai.jobs.execute": lambda payload: service.ai_job_execute(job_id=str(payload.get("job_id", ""))),
        "ai.jobs.result": lambda payload: service.ai_job_result(job_id=str(payload.get("job_id", ""))),
        "ai.evidence_package": lambda payload: service.ai_evidence_package(limit=int(payload.get("limit", 100))),
        "observability.trace_report": lambda payload: service.trace_report(limit=int(payload.get("limit", 20)), include_events=bool(payload.get("include_events", True)), include_metrics=bool(payload.get("include_metrics", True)), scope=str(payload.get("scope", "active"))),
        "observability.traces": lambda payload: service.trace_report(limit=int(payload.get("limit", 20)), include_events=bool(payload.get("include_events", True)), include_metrics=bool(payload.get("include_metrics", True)), scope=str(payload.get("scope", "active"))),
        "observability.trace_inspect": lambda payload: service.trace_inspect(str(payload.get("trace_id", "")), limit=int(payload.get("limit", 100)), scope=str(payload.get("scope", "active"))),
        "observability.metrics_summary": lambda payload: service.metrics_summary(category=payload.get("category"), limit=int(payload.get("limit", 50)), scope=str(payload.get("scope", "active"))),
        "history.runs": lambda payload: service.history_list(limit=int(payload.get("limit", 10))),
        "maturity.dashboard": lambda payload: service.maturity_dashboard(write_report=bool(payload.get("write_report", False))),
    }


def _domain_summaries() -> list[dict[str, Any]]:
    return [
        {"domain": "workspace", "service": "WorkspaceApplicationService", "status": "implemented-initial", "side_effects": "read_or_dry_run_plan"},
        {"domain": "workspace-validation", "service": "WorkspaceValidationApplicationService", "status": "implemented-initial", "side_effects": "source_read_only_runtime_trace_report"},
        {"domain": "workspace-edit-execution", "service": "WorkspaceEditExecutionApplicationService", "status": "implemented-initial-uoc-005", "side_effects": "approval_bound_atomic_document_write_with_precommit_rollback"},
        {"domain": "workspace-documents", "service": "WorkspaceDocumentsApplicationService", "status": "implemented-initial-uoc-001", "side_effects": "bounded_read_only"},
        {"domain": "validation", "service": "ValidationApplicationService", "status": "implemented", "side_effects": "none_or_explicit_report_by_adapter"},
        {"domain": "miasi", "service": "MiasiApplicationService", "status": "implemented", "side_effects": "none"},
        {"domain": "maturity", "service": "MaturityApplicationService", "status": "implemented-initial", "side_effects": "explicit_outputs_reports_only"},
        {"domain": "evals", "service": "EvaluationApplicationService", "status": "implemented-initial", "side_effects": "bounded_local_outputs_for_eval_workdir"},
        {"domain": "repo", "service": "RepoApplicationService", "status": "implemented-initial", "side_effects": "read_only"},
        {"domain": "reports", "service": "ReportsApplicationService", "status": "implemented-initial", "side_effects": "read_only_redacted_outputs_reports"},
        {"domain": "approvals", "service": "ApprovalApplicationService", "status": "implemented-initial", "side_effects": "approval_store_state_transition_audited"},
        {"domain": "settings", "service": "SettingsApplicationService", "status": "implemented-initial", "side_effects": "read_only_and_provider_plan_only"},
        {"domain": "review", "service": "ReviewApplicationService", "status": "implemented-initial", "side_effects": "dry_run_static_analysis"},
        {"domain": "refactor", "service": "RefactorApplicationService", "status": "implemented-initial", "side_effects": "plan_only"},
        {"domain": "model", "service": "ModelApplicationService", "status": "implemented-initial", "side_effects": "mock_or_local_governed_calls"},
        {"domain": "history", "service": "HistoryApplicationService", "status": "implemented-initial", "side_effects": "read_only"},
        {"domain": "observability", "service": "ObservabilityApplicationService", "status": "implemented-initial", "side_effects": "read_or_dry_run_export"},
        {"domain": "operator", "service": "OperatorDashboardApplicationService", "status": "implemented-initial", "side_effects": "read_only_optional_outputs_reports"},
        {"domain": "portfolio", "service": "PortfolioApplicationService", "status": "implemented-initial", "side_effects": "read_only"},
        {"domain": "quality-operations", "service": "QualityOperationsApplicationService", "status": "implemented-initial-uoc-009", "side_effects": "typed_local_jobs_outputs_only"},
    ]


def _capabilities() -> list[ServiceCapability]:
    rows = [
        ("workspace.status", "Report workspace initialization/readiness state.", "none", True, "python -m devpilot_core workspace status --json"),
        ("guided_sdlc.transition.evaluate", "Evaluate one versioned Guided SDLC transition deterministically without mutating engineering state.", "none", True, "ApplicationService read-only; no HTTP route in GSDLC-01-B"),
        ("guided_sdlc.transition.preview", "Preview the exact successor WorkspaceEngineeringState for one allowed transition without persisting it.", "none", True, "ApplicationService read-only preview; no HTTP route in GSDLC-01-B"),
        ("guided_sdlc.project.status", "Derive deterministic ProjectStatus from authoritative WorkspaceEngineeringState without direct Git/filesystem reads.", "none", True, "ApplicationService read-only projection; HTTP route deferred to GSDLC-01-E"),
        ("guided_sdlc.next_action", "Derive deterministic explainable NextAction recommendation without executing or persisting it.", "none", True, "ApplicationService read-only recommendation; execution surfaces deferred"),
        ("guided_sdlc.project_status", "Expose actor-neutral Project Status + NextAction through the ApplicationService for local API/UI consumption without mutating state.", "none", True, "GSDLC-01-E read-only Project Status API boundary; no direct filesystem/Git/UI-core access"),
        ("guided_sdlc.reconcile.preview", "Inspect registered workspace filesystem/Git drift and project its REVALIDATION_REQUIRED successor without persisting state.", "none", True, "Bounded read-only filesystem/Git observation; no HTTP route in GSDLC-01-D"),
        ("guided_sdlc.reconcile.execute", "Persist only the reconciled WorkspaceEngineeringState through the atomic local state repository after bounded read-only drift inspection.", "engineering_state_only", False, "No managed workspace source or Git mutation; explicit internal execution only; HTTP/UI deferred"),
        ("workspace.documents.list", "List a bounded read-only document index for the explicit active workspace.", "none", True, "GET /api/v1/workspace/documents"),
        ("workspace.documents.read", "Read one allowlisted UTF-8 workspace document by opaque identifier.", "none", True, "GET /api/v1/workspace/documents/{document_id}"),
        ("workspace.documents.metadata", "Read deterministic metadata for one opaque workspace document identifier.", "none", True, "GET /api/v1/workspace/documents/{document_id}/metadata"),
        ("workspace.documents.history", "Read bounded Git history for one opaque workspace document identifier.", "none", True, "GET /api/v1/workspace/documents/{document_id}/history"),
        ("workspace.documents.diff", "Read a bounded document diff against HEAD or an immutable commit id.", "none", True, "GET /api/v1/workspace/documents/{document_id}/diff"),
        ("workspace.documents.search", "Search active-workspace document content through an incremental in-memory index.", "none", True, "GET /api/v1/workspace/documents/search"),
        ("workspace.documents.links", "Read incoming and outgoing document relationships within the active workspace.", "none", True, "GET /api/v1/workspace/documents/{document_id}/links"),
        ("workspace.validations.plan", "Build an immutable bounded UOC-003 validation plan for the active workspace.", "none", True, "POST /api/v1/workspace/validations/plan"),
        ("workspace.validations.execute", "Execute deterministic UOC-003 validators as a source-read-only job with local trace/report evidence.", "runtime_evidence_only", False, "POST /api/v1/workspace/validations/execute"),
        ("workspace.validations.status", "Read one bounded UOC-003 validation job by opaque job id.", "none", True, "GET /api/v1/workspace/validations/{job_id}"),
        ("workspace.traceability", "Read the explicit-only requirement-story-risk/control-test traceability matrix.", "none", True, "GET /api/v1/workspace/traceability"),
        ("workspace.init_plan", "Build a workspace initialization plan without writing files.", "none", True, "python -m devpilot_core workspace init --json"),
        ("validators.validate_frontmatter", "Legacy alias: validate Markdown frontmatter metadata for one artifact.", "none", True, "python -m devpilot_core validate-frontmatter <path> --json"),
        ("validators.validate_artifact", "Legacy alias: validate Markdown structure against MIPSoftware/MIASI profiles.", "none", True, "python -m devpilot_core validate-artifact <path> --json"),
        ("validators.checklist_pre_code", "Legacy alias: evaluate the executable pre-code checklist gate.", "none", True, "python -m devpilot_core checklist-pre-code --json"),
        ("validators.readiness", "Legacy alias: evaluate readiness gates for baseline artifacts.", "report_when_adapter_requests_it", True, "python -m devpilot_core readiness-check --strict --json"),
        ("workspace.edits.plan", "Create immutable UOC-004 document edit plan, complete diff, preview and risk/policy without source mutation.", "plan_only", True, "POST /api/v1/workspace/edit-plans/plan"),
        ("workspace.edits.status", "Inspect one in-memory immutable UOC-004 edit plan.", "none", True, "GET /api/v1/workspace/edit-plans/{plan_id}"),
        ("workspace.edits.recheck", "Recheck base SHA optimistic concurrency for an immutable UOC-004 edit plan.", "none", True, "POST /api/v1/workspace/edit-plans/{plan_id}/recheck"),
        ("workspace.edits.approval_request", "Request exact human approval for one immutable UOC-004 plan before UOC-005 apply.", "approval_store_write", False, "POST /api/v1/workspace/edit-plans/{plan_id}/approval-request"),
        ("workspace.edits.apply", "Apply one approved immutable document plan atomically with backup, recheck and post-validation.", "approval_gated_source_write", False, "POST /api/v1/workspace/edit-plans/{plan_id}/apply"),
        ("workspace.edits.execution_status", "Inspect one UOC-005 governed document execution record.", "none", True, "GET /api/v1/workspace/edit-executions/{execution_id}"),
        ("workspace.edits.rollback_approval_request", "Request separate human approval for bounded pre-commit rollback.", "approval_store_write", False, "POST /api/v1/workspace/edit-executions/{execution_id}/rollback-approval-request"),
        ("workspace.edits.rollback", "Restore the exact pre-apply backup before Git stage/commit after separate approval.", "approval_gated_source_write", False, "POST /api/v1/workspace/edit-executions/{execution_id}/rollback"),
        ("quality.operations", "List registered UOC-009 quality/test/release operations and budgets.", "none", True, "GET /api/v1/quality/operations"),
        ("quality.baseline", "Inspect current project/release baseline and recent manifests read-only.", "none", True, "GET /api/v1/quality/baseline"),
        ("quality.test_impact_plan", "Build Test Impact v2 plan from repository-relative changed paths without executing tests.", "none", True, "POST /api/v1/quality/test-impact/plan"),
        ("quality.jobs.plan", "Plan one typed quality/test/release job by registered operation/profile id.", "runtime_plan_only", False, "POST /api/v1/quality/jobs/plan"),
        ("quality.jobs.execute", "Start the fixed UOC-009 typed worker for an approved/eligible governed job.", "governed_runtime_outputs_only", False, "POST /api/v1/quality/jobs/{job_id}/execute"),
        ("quality.evidence_package", "Create a bounded local evidence package from UOC-009 runtime results.", "local_outputs_only", False, "POST /api/v1/quality/evidence/package"),
        ("validation.frontmatter", "Validate Markdown frontmatter metadata for one artifact.", "none", True, "python -m devpilot_core validate-frontmatter <path> --json"),
        ("validation.artifact", "Validate Markdown structure against MIPSoftware/MIASI profiles.", "none", True, "python -m devpilot_core validate-artifact <path> --json"),
        ("validation.checklist_pre_code", "Evaluate the executable pre-code checklist gate.", "none", True, "python -m devpilot_core checklist-pre-code --json"),
        ("validation.readiness", "Evaluate readiness gates for baseline artifacts.", "report_when_adapter_requests_it", True, "python -m devpilot_core readiness-check --strict --json"),
        ("validation.gateway", "Run docs/contracts/all validation gateway.", "report_when_adapter_requests_it", True, "python -m devpilot_core validate all --json"),
        ("standards.status", "Report local MIPSoftware and MIASI registry status.", "none", True, "python -m devpilot_core standards status --json"),
        ("miasi.validate", "Validate MIASI executable registries.", "none", True, "python -m devpilot_core miasi validate --json"),
        ("evals.documentation.run", "Run offline deterministic evaluation suite.", "local_eval_workdir", True, "python -m devpilot_core eval run --suite documentation --json"),
        ("repo.inventory", "Build local repository inventory.", "none", True, "python -m devpilot_core repo inventory --json"),
        ("reports.list", "List redacted local evidence reports under outputs/reports.", "none", True, "python -m devpilot_core reports list --json"),
        ("reports.read", "Read one redacted local evidence report by id and format.", "none", True, "python -m devpilot_core reports read <report_id> --json"),
        ("approvals.list", "List local human approval records for Approval Center.", "read_only", True, "python -m devpilot_core approval list --json"),
        ("approvals.show", "Show one local approval record by id.", "read_only", True, "python -m devpilot_core approval show <approval_id> --json"),
        ("approvals.request", "Create an audited local approval request from Approval Center.", "approval_store_write", False, "python -m devpilot_core approval request --tool <tool> --action <action> --subject <subject> --reason <reason> --actor <actor> --json"),
        ("approvals.approve", "Approve one local approval request through controlled transition.", "approval_store_write", False, "python -m devpilot_core approval approve <approval_id> --actor <actor> --reason <reason> --json"),
        ("approvals.deny", "Deny one local approval request through controlled transition.", "approval_store_write", False, "python -m devpilot_core approval deny <approval_id> --actor <actor> --reason <reason> --json"),
        ("ui.actions.dry_run", "Launch safe UI actions in read-only/dry-run mode only.", "dry_run_only", True, "UI Action Launcher: readiness/code-review/refactor-plan"),
        ("settings.workspace", "Read workspace project settings without exposing filesystem writes.", "none", True, "Settings UI: workspace panel"),
        ("settings.providers", "Read provider settings with secret redaction and external providers disabled by default.", "none", True, "Settings UI: providers panel"),
        ("settings.policy", "Read local policy and MIASI policy matrix summaries without editing policy.", "none", True, "Settings UI: policy panel"),
        ("settings.providers.plan", "Create a provider configuration change plan without writing .devpilot/providers.yaml.", "plan_only", True, "Settings UI: provider plan-only editor"),
        ("repo.analyze", "Run read-only repository analysis.", "none", True, "python -m devpilot_core repo analyze --json"),
        ("review.code", "Run deterministic code review in dry-run mode.", "none", True, "python -m devpilot_core code-review . --json"),
        ("refactor.plan", "Create plan-only safe refactor proposal.", "none", True, "python -m devpilot_core refactor-plan . --json"),
        ("model.providers", "List governed model providers without external API calls.", "none", True, "python -m devpilot_core model providers --json"),
        ("model.health", "Check provider health through governed model router.", "localhost_or_none", True, "python -m devpilot_core model health --provider mock --json"),
        ("model.local_health", "Build POST-H-032-B local LLM provider hardening evidence for Ollama/LM Studio without requiring real local servers.", "read_only_optional_outputs_reports", True, "python -m devpilot_core model local-health --json"),
        ("model.external_api_pilot", "Build POST-H-032-C ADR-backed external API fake/gated pilot evidence without real external API calls or secret reads.", "read_only_optional_outputs_reports", True, "python -m devpilot_core model external-api-pilot --json"),
        ("agent.rag_context", "Build POST-H-032-D deterministic RAG-aware agent context packs with citations and insufficient-evidence behavior.", "read_only_optional_outputs_reports", True, "python -m devpilot_core agent rag-context --json"),
        ("agent.mcp_fake_server_evaluation", "Evaluate POST-H-032-G MCP design and local fake-server contract without enabling real MCP, network transports or tool execution.", "read_only_optional_outputs_reports", True, "python -m devpilot_core agent mcp-fake-server evaluate --json"),
        ("multiagent.handoff_hardening", "Evaluate POST-H-032-H deterministic multiagent handoff hardening without swarm autonomy, tool execution, network, external APIs or source mutation.", "read_only_optional_outputs_reports", True, "python -m devpilot_core multiagent handoff harden --json"),
        ("agent.tool_call_contract", "Validate POST-H-032-F governed tool-calling contracts with allowlists, dry-run-first, approval binding and injection guards.", "read_only_optional_outputs_reports", True, "python -m devpilot_core agent tool-calls validate --json"),
        ("model.capabilities", "Build static model capability matrix.", "none", True, "python -m devpilot_core model capabilities --json"),
        ("history.runs", "List local command history from LocalStore.", "none", True, "python -m devpilot_core history list --json"),
        ("observability.trace_report", "Read bounded local trace report.", "none", True, "python -m devpilot_core trace report --json"),
        ("observability.trace_inspect", "Inspect one trace id as a span tree.", "none", True, "python -m devpilot_core trace inspect <trace_id> --json"),
        ("observability.metrics_summary", "Read bounded local metrics summary.", "none", True, "python -m devpilot_core metrics summary --json"),
        ("observability.agentops_status", "Evaluate AgentOps quality gate.", "report_when_adapter_requests_it", True, "python -m devpilot_core agentops status --json"),
        ("maturity.dashboard", "Generate the local POST-H maturity dashboard from evidence.", "explicit_outputs_reports_only", True, "python -m devpilot_core maturity dashboard --json"),
        ("maturity.dashboard_gate", "Run the POST-H-002 maturity dashboard quality gate.", "explicit_outputs_reports_only", True, "python -m devpilot_core maturity gate --json"),
        ("operator.dashboard", "Build the local operator dashboard snapshot through ApplicationService.", "read_only_optional_outputs_reports", True, "GET /api/v1/operator/dashboard"),
        ("agent.capability_inventory", "Build the POST-H-032-A governed agent capability inventory through ApplicationService.", "read_only_optional_outputs_reports", True, "python -m devpilot_core agent capability-inventory --json"),
        ("portfolio.status", "Build hardened registered-workspace portfolio status through ApplicationService.", "read_only", True, "python -m devpilot_core portfolio status --json / GET /api/v1/portfolio/status"),
    ]
    return [
        ServiceCapability(
            operation=operation,
            description=description,
            side_effect=side_effect,
            dry_run_default=dry_run_default,
            command_equivalent=command_equivalent,
        )
        for operation, description, side_effect, dry_run_default, command_equivalent in rows
    ]


def _routes() -> list[InterfaceRouteContract]:
    route_specs = [
        ("APP-ROUTE-GSDLC-02-B-AUTH-BOOTSTRAP-STATUS", "GET", "/api/v1/auth/bootstrap/status", "auth.bootstrap.status", ["GSDLC-02-B public localhost-only bootstrap status; exposes no credential/session secret."]),
        ("APP-ROUTE-GSDLC-02-B-AUTH-BOOTSTRAP-OWNER", "POST", "/api/v1/auth/bootstrap/owner", "auth.bootstrap.owner", ["GSDLC-02-B first-run owner bootstrap through AuthApplicationService; local runtime auth state only."]),
        ("APP-ROUTE-GSDLC-02-B-AUTH-LOGIN", "POST", "/api/v1/auth/login", "auth.login", ["GSDLC-02-B local credential verification through AuthApplicationService; opaque secrets delivered only as cookies."]),
        ("APP-ROUTE-GSDLC-02-B-AUTH-SESSION", "GET", "/api/v1/auth/session", "auth.session.inspect", ["GSDLC-02-B human-session inspection; safe principal/session metadata only."]),
        ("APP-ROUTE-GSDLC-02-B-AUTH-ROTATE", "POST", "/api/v1/auth/session/rotate", "auth.session.rotate", ["GSDLC-02-B session rotation; old token revoked before opaque replacement is issued."]),
        ("APP-ROUTE-GSDLC-02-B-AUTH-LOGOUT", "POST", "/api/v1/auth/logout", "auth.logout", ["GSDLC-02-B current-session logout/revocation with cookie clearing."]),
        ("APP-ROUTE-GSDLC-02-B-AUTH-REVOKE", "POST", "/api/v1/auth/session/revoke", "auth.session.revoke", ["GSDLC-02-B explicit current-session revocation; administrative revocation remains future."]),
        ("APP-ROUTE-GSDLC-01-E", "GET", "/api/v1/guided-sdlc/status", "guided_sdlc.project_status", ["GSDLC-01-E actor-neutral read-only Project Status + NextAction route; all semantics delegate through ApplicationService."]),
        ("APP-ROUTE-001", "GET", "/api/v1/workspace/status", "workspace.status", ["Active local API MVP route in FUNC-SPRINT-67."]),
        ("APP-ROUTE-UOC-001-A", "GET", "/api/v1/workspace/documents", "workspace.documents.list", ["UOC-001 bounded read-only active-workspace document index."]),
        ("APP-ROUTE-UOC-001-B", "GET", "/api/v1/workspace/documents/{document_id}", "workspace.documents.read", ["UOC-001 opaque-id document viewer; no path authority accepted from browser."]),
        ("APP-ROUTE-UOC-001-C", "GET", "/api/v1/workspace/documents/{document_id}/metadata", "workspace.documents.metadata", ["UOC-001 read-only document metadata contract."]),
        ("APP-ROUTE-UOC-002-A", "GET", "/api/v1/workspace/documents/{document_id}/history", "workspace.documents.history", ["UOC-002 bounded path-specific Git history through typed read-only adapter methods."]),
        ("APP-ROUTE-UOC-002-B", "GET", "/api/v1/workspace/documents/{document_id}/diff", "workspace.documents.diff", ["UOC-002 bounded read-only diff against HEAD or a hexadecimal commit id."]),
        ("APP-ROUTE-UOC-002-C", "GET", "/api/v1/workspace/documents/search", "workspace.documents.search", ["UOC-002 local full-text search with active-workspace in-memory cache."]),
        ("APP-ROUTE-UOC-002-D", "GET", "/api/v1/workspace/documents/{document_id}/links", "workspace.documents.links", ["UOC-002 incoming/outgoing document relationship inspection."]),
        ("APP-ROUTE-UOC-003-A", "POST", "/api/v1/workspace/validations/plan", "workspace.validations.plan", ["UOC-003 immutable bounded plan; no source mutation or runtime evidence write."]),
        ("APP-ROUTE-UOC-003-B", "POST", "/api/v1/workspace/validations/execute", "workspace.validations.execute", ["UOC-003 synchronous preliminary job; writes only local runtime trace/report evidence."]),
        ("APP-ROUTE-UOC-003-C", "GET", "/api/v1/workspace/validations/{job_id}", "workspace.validations.status", ["UOC-003 bounded status lookup by opaque job id."]),
        ("APP-ROUTE-UOC-003-D", "GET", "/api/v1/workspace/traceability", "workspace.traceability", ["UOC-003 explicit-only traceability matrix with finding navigation."]),
        ("APP-ROUTE-UOC-004-A", "POST", "/api/v1/workspace/edit-plans/plan", "workspace.edits.plan", ["UOC-004 immutable source-non-mutating edit plan with complete unified diff and base SHA binding."]),
        ("APP-ROUTE-UOC-004-B", "GET", "/api/v1/workspace/edit-plans/{plan_id}", "workspace.edits.status", ["UOC-004 in-memory immutable plan inspection; no source write."]),
        ("APP-ROUTE-UOC-004-C", "POST", "/api/v1/workspace/edit-plans/{plan_id}/recheck", "workspace.edits.recheck", ["UOC-004 optimistic concurrency recheck against current document SHA."]),
        ("APP-ROUTE-UOC-005-A", "POST", "/api/v1/workspace/edit-plans/{plan_id}/approval-request", "workspace.edits.approval_request", ["UOC-005 exact approval request bound to immutable plan/hash/base/actor/scope/TTL; local approval state only."]),
        ("APP-ROUTE-UOC-005-B", "POST", "/api/v1/workspace/edit-plans/{plan_id}/apply", "workspace.edits.apply", ["UOC-005 narrow approval-gated atomic document source write; generic patch.apply remains blocked."]),
        ("APP-ROUTE-UOC-005-C", "GET", "/api/v1/workspace/edit-executions/{execution_id}", "workspace.edits.execution_status", ["UOC-005 read-only execution/evidence status by opaque execution id."]),
        ("APP-ROUTE-UOC-005-D", "POST", "/api/v1/workspace/edit-executions/{execution_id}/rollback-approval-request", "workspace.edits.rollback_approval_request", ["UOC-005 separate approval request for bounded pre-commit rollback; local approval state only."]),
        ("APP-ROUTE-UOC-005-E", "POST", "/api/v1/workspace/edit-executions/{execution_id}/rollback", "workspace.edits.rollback", ["UOC-005 approval-gated exact backup restore before Git stage/commit; generic rollback remains blocked."]),
        ("APP-ROUTE-UOC-006-A", "GET", "/api/v1/workspace/git/status", "workspace.git.status", ["UOC-006 typed read-only Git status/diff projection; no free-form Git arguments."]),
        ("APP-ROUTE-UOC-006-B", "GET", "/api/v1/workspace/git/history", "workspace.git.history", ["UOC-006 bounded read-only commit history."]),
        ("APP-ROUTE-UOC-006-C", "GET", "/api/v1/workspace/git/compare", "workspace.git.compare", ["UOC-006 bounded compare over HEAD or immutable hexadecimal object identifiers."]),
        ("APP-ROUTE-UOC-006-D", "POST", "/api/v1/workspace/git/plans", "workspace.git.plan", ["UOC-006 immutable staging/commit plan using opaque document ids and explicit commit identity; zero Git mutation."]),
        ("APP-ROUTE-UOC-006-E", "GET", "/api/v1/workspace/git/plans/{plan_id}", "workspace.git.plan_status", ["UOC-006 immutable Git plan inspection."]),
        ("APP-ROUTE-UOC-006-F", "POST", "/api/v1/workspace/git/plans/{plan_id}/stage-approval-request", "workspace.git.stage_approval_request", ["UOC-006 exact stage approval request; mutates only local ApprovalStore."]),
        ("APP-ROUTE-UOC-006-G", "POST", "/api/v1/workspace/git/plans/{plan_id}/stage", "workspace.git.stage", ["UOC-006 exact approval-bound staging of allowlisted documents with compensation on failed pre-commit checks."]),
        ("APP-ROUTE-UOC-006-H", "GET", "/api/v1/workspace/git/executions/{execution_id}", "workspace.git.execution_status", ["UOC-006 read-only execution record inspection."]),
        ("APP-ROUTE-UOC-006-I", "POST", "/api/v1/workspace/git/stage-executions/{execution_id}/commit-approval-request", "workspace.git.commit_approval_request", ["UOC-006 second human approval bound to exact staged index fingerprint and commit intent."]),
        ("APP-ROUTE-UOC-006-J", "POST", "/api/v1/workspace/git/stage-executions/{execution_id}/commit", "workspace.git.commit", ["UOC-006 approval-bound local commit with explicit identity, no hooks and verified parent/files/index; push remains blocked."]),
        ("APP-ROUTE-UOC-006-K", "POST", "/api/v1/workspace/git/branches/plan", "workspace.git.branch_plan", ["UOC-006 controlled local branch-ref plan from clean current HEAD; no checkout."]),
        ("APP-ROUTE-UOC-006-L", "POST", "/api/v1/workspace/git/branches/{plan_id}/approval-request", "workspace.git.branch_approval_request", ["UOC-006 approval request bound to exact branch plan/hash."]),
        ("APP-ROUTE-UOC-006-M", "POST", "/api/v1/workspace/git/branches/{plan_id}/create", "workspace.git.branch_create", ["UOC-006 approval-bound local branch-ref creation only; no checkout, delete, push or force operation."]),
        ("APP-ROUTE-UOC-009-A", "GET", "/api/v1/quality/operations", "quality.operations", ["UOC-009 typed quality/test/release operation catalog; no shell text or executable selection."]),
        ("APP-ROUTE-UOC-009-B", "GET", "/api/v1/quality/baseline", "quality.baseline", ["UOC-009 read-only baseline/manifest inspection."]),
        ("APP-ROUTE-UOC-009-C", "POST", "/api/v1/quality/test-impact/plan", "quality.test_impact_plan", ["UOC-009 Test Impact plan-only operation over repository-relative changed paths."]),
        ("APP-ROUTE-UOC-009-D", "POST", "/api/v1/quality/jobs/plan", "quality.jobs.plan", ["UOC-009 governed quality job plan by registered operation/profile identifiers."]),
        ("APP-ROUTE-UOC-009-E", "POST", "/api/v1/quality/jobs/{job_id}/execute", "quality.jobs.execute", ["UOC-009 fixed typed worker execution; approvals/confirmation/budgets enforced; no arbitrary shell."]),
        ("APP-ROUTE-UOC-009-F", "POST", "/api/v1/quality/evidence/package", "quality.evidence_package", ["UOC-009 bounded local evidence packaging under outputs only."]),
        ("APP-ROUTE-UOC-010-A", "GET", "/api/v1/ai/operations", "ai.operations", ["UOC-010 typed RAG/agent/handoff catalog; no free shell/tools/provider secrets."]),
        ("APP-ROUTE-UOC-010-B", "GET", "/api/v1/ai/status", "ai.status", ["UOC-010 provider/RAG/tool/memory/handoff governance status; read-only and local-first."]),
        ("APP-ROUTE-UOC-010-C", "POST", "/api/v1/ai/jobs/plan", "ai.jobs.plan", ["UOC-010 immutable typed AI job plan with approval binding where required."]),
        ("APP-ROUTE-UOC-010-D", "POST", "/api/v1/ai/jobs/{job_id}/execute", "ai.jobs.execute", ["UOC-010 fixed local typed worker; external APIs and arbitrary shell blocked."]),
        ("APP-ROUTE-UOC-010-E", "GET", "/api/v1/ai/jobs/{job_id}/result", "ai.jobs.result", ["UOC-010 bounded AI result projection with citations/provider/cost/memory/handoff governance."]),
        ("APP-ROUTE-UOC-010-F", "POST", "/api/v1/ai/evidence/package", "ai.evidence_package", ["UOC-010 bounded local AI evidence packaging; memory never counts as formal evidence."]),
        ("APP-ROUTE-UOC-008-A", "GET", "/api/v1/jobs", "jobs.list", ["UOC-008 bounded local Job Console index with workspace/capability/status filters."]),
        ("APP-ROUTE-UOC-008-B", "GET", "/api/v1/jobs/{job_id}", "jobs.inspect", ["UOC-008 governed-job detail projection with heartbeat/progress/stale metadata and internal hashes removed."]),
        ("APP-ROUTE-UOC-008-C", "GET", "/api/v1/jobs/{job_id}/logs", "jobs.logs", ["UOC-008 bounded sanitized local job-log polling by opaque job id and cursor."]),
        ("APP-ROUTE-UOC-008-D", "POST", "/api/v1/jobs/{job_id}/cancel", "jobs.cancel", ["UOC-008 policy-bound cancellation request with fixed-argv process-tree control; no arbitrary shell."]),
        ("APP-ROUTE-UOC-008-E", "POST", "/api/v1/jobs/{job_id}/retry", "jobs.retry", ["UOC-008 governed retry creates a fresh job within retry budget and never autoexecutes it."]),
        ("APP-ROUTE-002", "POST", "/api/v1/validation/frontmatter", "validation.frontmatter", ["Active local API MVP route for Web UI validators."]),
        ("APP-ROUTE-003", "POST", "/api/v1/validation/artifact", "validation.artifact", ["Active local API MVP route for Web UI validators."]),
        ("APP-ROUTE-004", "POST", "/api/v1/validation/readiness", "validation.readiness", ["Active local API MVP route; report writes remain explicit in lower layers."]),
        ("APP-ROUTE-005", "GET", "/api/v1/miasi/status", "miasi.validate", ["Active read-only MIASI status projection."]),
        ("APP-ROUTE-006", "GET", "/api/v1/repo/inventory", "repo.inventory", ["Active read-only repository summary route."]),
        ("APP-ROUTE-007", "POST", "/api/v1/review/code", "review.code", ["Active dry-run review route; no mutation."]),
        ("APP-ROUTE-008", "POST", "/api/v1/refactor/plan", "refactor.plan", ["Active plan-only route; no patch execution."]),
        ("APP-ROUTE-009", "GET", "/api/v1/model/providers", "model.providers", ["Active governed model provider listing; no external API call."]),
        ("APP-ROUTE-010", "GET", "/api/v1/observability/traces", "observability.trace_report", ["Active bounded local trace viewer route."]),
        ("APP-ROUTE-011", "GET", "/api/v1/observability/metrics", "observability.metrics_summary", ["Active bounded local metric viewer route."]),
        ("APP-ROUTE-012", "GET", "/api/v1/history/runs", "history.runs", ["Active bounded LocalStore history route."]),
        ("APP-ROUTE-013", "GET", "/api/v1/application/contract", "app.contract", ["Active bootstrap route for API/Web UI clients."]),
        ("APP-ROUTE-014", "GET", "/api/v1/standards/status", "standards.status", ["Active standards status route added by FUNC-SPRINT-67."]),
        ("APP-ROUTE-015", "GET", "/api/v1/reports", "reports.list", ["Active Sprint 70 report index route; API reads outputs/reports, UI never reads filesystem."]),
        ("APP-ROUTE-016", "GET", "/api/v1/reports/{report_id}", "reports.read", ["Active Sprint 70 report detail route with redaction and safe basename validation."]),
        ("APP-ROUTE-017", "GET", "/api/v1/traces", "observability.trace_report", ["Active Sprint 70 trace index route; bounded and empty-safe."]),
        ("APP-ROUTE-018", "GET", "/api/v1/traces/{trace_id}", "observability.trace_inspect", ["Active Sprint 70 trace detail route rendered as span tree."]),
        ("APP-ROUTE-019", "GET", "/api/v1/metrics/summary", "observability.metrics_summary", ["Active Sprint 70 metrics summary alias for visual dashboard."]),
        ("APP-ROUTE-020", "GET", "/api/v1/approvals", "approvals.list", ["Active Sprint 71 Approval Center route; lists approval records through ApprovalService."]),
        ("APP-ROUTE-021", "GET", "/api/v1/approvals/{approval_id}", "approvals.show", ["Active Sprint 71 approval detail route with safe local token policy."]),
        ("APP-ROUTE-022", "POST", "/api/v1/approvals/request", "approvals.request", ["Active Sprint 71 audited approval request route; writes only approval store records."]),
        ("APP-ROUTE-023", "POST", "/api/v1/approvals/{approval_id}/approve", "approvals.approve", ["Active Sprint 71 controlled approval transition route."]),
        ("APP-ROUTE-024", "POST", "/api/v1/approvals/{approval_id}/deny", "approvals.deny", ["Active Sprint 71 controlled denial transition route."]),
        ("APP-ROUTE-025", "POST", "/api/v1/actions/dry-run", "ui.actions.dry_run", ["Active Sprint 71 dry-run Action Launcher route; critical actions remain blocked from UI."]),
        ("APP-ROUTE-026", "GET", "/api/v1/settings/workspace", "settings.workspace", ["Active Sprint 72 Settings route; read-only workspace projection."]),
        ("APP-ROUTE-027", "GET", "/api/v1/settings/providers", "settings.providers", ["Active Sprint 72 Settings route; providers are redacted and read-only."]),
        ("APP-ROUTE-028", "GET", "/api/v1/settings/policy", "settings.policy", ["Active Sprint 72 Settings route; policy summary is read-only."]),
        ("APP-ROUTE-029", "POST", "/api/v1/settings/providers/plan", "settings.providers.plan", ["Active Sprint 72 Settings route; provider edits are plan-only and never write files."]),
        ("APP-ROUTE-030", "GET", "/api/v1/operator/dashboard", "operator.dashboard", ["Active POST-H-015-C local operator dashboard snapshot route; read-only by default and ApplicationService-bound."]),
        ("APP-ROUTE-031", "GET", "/api/v1/portfolio/status", "portfolio.status", ["Active POST-H-016-D portfolio status route; read-only, policy-bound and does not change active workspace."]),
        ("APP-ROUTE-032", "GET", "/api/v1/operator/health", "operator.health", ["Active POST-H-031-B operator health summary route; read-only and ApplicationService-bound."]),
        ("APP-ROUTE-033", "GET", "/api/v1/operator/gaps", "operator.gaps", ["Active POST-H-031-C gap-to-action mapping route; advisory/read-only and does not execute recommended commands."]),
        ("APP-ROUTE-034", "GET", "/api/v1/operator/claims-no-go", "operator.claims_no_go", ["Active POST-H-031-D claims/no-go dashboard route; read-only and does not mutate claims or gates."]),
        ("APP-ROUTE-035", "GET", "/api/v1/operator/evidence-export", "operator.evidence_export", ["Active POST-H-031-E redacted evidence export route; dry-run by default and writes only redacted package under outputs when explicit."]),
    ]
    return [InterfaceRouteContract(route_id=rid, method=method, path=path, operation=operation, status="secured-initial", notes=notes) for rid, method, path, operation, notes in route_specs]
