from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.evals import EvalRunner, EvalRunnerConfig


@dataclass(frozen=True)
class QualityGateOptions:
    """Execution options for the local productization quality gate.

    FUNC-SPRINT-75 keeps the default gate deterministic and read-only with
    respect to the source tree. `include_pytest` is intentionally opt-in because
    pytest may create cache/runtime files and can be slow in local workspaces;
    later Fase G sprints can bind the full profile to CI/release flows.
    """

    profile: str = "fast"
    include_pytest: bool = False
    pytest_timeout_seconds: int = 180


@dataclass(frozen=True)
class QualitySubgate:
    id: str
    description: str
    runner: Callable[[], CommandResult]
    critical: bool = True


class QualityGate:
    """Unified local quality gate for DevPilot release readiness.

    The gate composes existing DevPilot contracts instead of duplicating their
    internals. It returns a CommandResult with one normalized subgate record per
    executed check. By default it performs no source mutations, no external API
    calls, no network calls, no package publishing and no destructive actions.
    Optional report writing remains delegated to the CLI/ReportEngine.
    """

    SUPPORTED_PROFILES = {"fast", "full", "ci", "release", "industrial", "hardening"}

    def __init__(self, root: Path, *, options: QualityGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or QualityGateOptions()
        self._service: Any | None = None


    @property
    def service(self) -> Any:
        from devpilot_core.application import ApplicationService

        if self._service is None:
            self._service = ApplicationService(self.root)
        return self._service

    def run(self) -> CommandResult:
        if self.options.profile not in self.SUPPORTED_PROFILES:
            return CommandResult(
                command="quality-gate run",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Quality gate profile is not supported.",
                data={
                    "summary": {
                        "profile": self.options.profile,
                        "supported_profiles": sorted(self.SUPPORTED_PROFILES),
                        "preliminary": True,
                    }
                },
                findings=[
                    Finding(
                        id="QUALITY_GATE_PROFILE_UNSUPPORTED",
                        message="Requested quality gate profile is not supported.",
                        severity=Severity.ERROR,
                        metadata={"profile": self.options.profile, "supported_profiles": sorted(self.SUPPORTED_PROFILES)},
                    )
                ],
            )

        subgates = self._subgates()
        subgate_records: list[dict[str, Any]] = []
        aggregated_findings: list[Finding] = []
        for subgate in subgates:
            started = time.perf_counter()
            result = self._run_subgate(subgate)
            duration_ms = int((time.perf_counter() - started) * 1000)
            record = self._subgate_record(subgate, result, duration_ms)
            subgate_records.append(record)
            aggregated_findings.extend(self._prefixed_findings(subgate, result))

        exit_code = self._derive_exit_code(subgate_records)
        ok = exit_code == ExitCode.PASS
        blocking_findings = [finding for finding in aggregated_findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        warnings = [finding for finding in aggregated_findings if finding.severity == Severity.WARNING]
        summary = {
            "profile": self.options.profile,
            "subgates_total": len(subgate_records),
            "subgates_passed": sum(1 for item in subgate_records if bool(item["ok"])),
            "subgates_failed": sum(1 for item in subgate_records if not bool(item["ok"])),
            "critical_subgates_failed": sum(1 for item in subgate_records if bool(item["critical"]) and not bool(item["ok"])),
            "findings_total": len(aggregated_findings),
            "warnings_total": len(warnings),
            "blocking_findings_total": len(blocking_findings),
            "include_pytest": self._should_run_pytest(),
            "pytest_timeout_seconds": self.options.pytest_timeout_seconds if self._should_run_pytest() else None,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }
        return CommandResult(
            command="quality-gate run",
            ok=ok,
            exit_code=exit_code,
            message="Quality gate passed." if ok else "Quality gate failed or blocked.",
            data={
                "summary": summary,
                "subgates": subgate_records,
                "notes": [
                    "FUNC-SPRINT-75 implements the first unified local quality gate for Fase G.",
                    "FUNC-SPRINT-76 adds the CI profile as the local source of truth for optional workflow scaffolding.",
                    "FUNC-SPRINT-84 adds the release profile as a dry-run release readiness gate for ReleaseAgent and Fase G closure.",
                    "FUNC-SPRINT-99 adds the industrial profile as the Fase H closure/readiness gate without overclaiming production maturity.",
                    "POST-H-001 adds the hardening profile for test contracts, project state and industrial baseline coherence without running full pytest by default.",
                    "POST-H-002-E adds the maturity-dashboard subgate to hardening/industrial profiles without replacing existing gates.",
                    "POST-H-003-E adds the Test Contract Registry v2 subgate to hardening/industrial profiles while keeping v1 compatibility.",
                    "POST-H-004-E adds the MIASI semantic validator subgate to hardening/industrial profiles without executing agents, tools, evals or tests from JSON.",
                    "POST-H-005-E adds the executable architecture map subgate to hardening/industrial profiles without enforcing refactors or mutating source files.",
                    "POST-H-007-E adds an Application CLI boundary integration subgate to hardening/industrial profiles without enabling runtime registry routing.",
                    "POST-H-010-E adds the observability-retention hygiene subgate to hardening/industrial profiles without requiring runtime outputs, network or external observability services.",
                    "POST-H-011-E adds rag-groundedness-ready to hardening/industrial profiles without requiring providers, web search, external APIs, LLM judge or versioned outputs/evals.",
                    "POST-H-012-E adds approval-rbac-hardening to hardening/industrial profiles to validate sensitive actions, approval binding, RBAC exposure, PolicyEngine enforcement and approval lifecycle docs without enabling side effects.",
                    "POST-H-013-E adds audit-pack-integrity to hardening/industrial profiles to validate manifest policy, no-go gates, redaction, local verification docs and no-certification disclaimers without writing packs.",
                    "POST-H-014-E adds ui-api-industrial-shell to hardening/industrial profiles to validate API/UI contracts, local Web UI smoke, security posture and operational docs without enabling SaaS, remote execution, connector write or plugin execution.",
                    "POST-H-015-E adds operator-dashboard-ready to hardening/industrial profiles to validate the local operator snapshot, no-go gates, next actions and operational runbook without enabling remote control.",
                    "POST-H-016-E adds workspace-portfolio-hardening to hardening/industrial profiles to validate registry v2, isolation, portfolio status, API boundary and onboarding runbook without enabling cross-workspace writes.",
                    "POST-H-017-E adds release-reproducibility to hardening/industrial profiles to generate and verify local dry-run reproducibility pack evidence without publishing, deploying, network, external APIs or source mutations.",
                    "POST-H-018-E adds connector-sandbox to hardening/industrial profiles to validate deny-write, replay, redaction and Policy/Approval/RBAC binding without connector write, network, external APIs, remote execution or plugins.",
                    "POST-H-019-D adds plugin-sandbox-design to hardening/industrial profiles to validate metadata-only plugin registry, permission model, exposure report and plugin-ecosystem eval signal without plugin execution.",
                    "POST-H-020-D adds compliance-mapping-pack to hardening/industrial profiles to validate mappings, evidence, report, audit-pack summary and compliance-pack eval signal without certification claims.",
                    "POST-H-021-D adds remote-readiness-design-only to hardening/industrial profiles to validate remote runner disabled invariants, readiness report and remote-enterprise eval signal without remote execution.",
                    "POST-H-022-D adds enterprise-threat-model-design-only to hardening/industrial profiles to validate enterprise threat model and control matrix blockers without enterprise deployment.",
                    "POST-H-008-E adds runtime-state-hygiene to hardening/industrial profiles to block dirty source/release archives.",
                    "POST-H-009-E adds docs-governance to hardening/industrial profiles to block canonical-source, sync and backlog-governance drift.",
                    "The default and ci profiles do not run pytest implicitly; CI workflows and local checklists run pytest as an explicit step, or use --include-pytest when desired.",
                    "The gate does not publish packages, deploy, write source files, call network services or use external APIs.",
                    "Optional --write-report is handled by the CLI and writes only under outputs/reports.",
                ],
            },
            findings=aggregated_findings or [Finding("QUALITY_GATE_PASS", "All configured quality subgates passed.", Severity.INFO, metadata={"profile": self.options.profile})],
        )

    def _subgates(self) -> list[QualitySubgate]:
        subgates = [
            QualitySubgate("readiness-strict", "Strict pre-code/readiness validation.", lambda: self.service.readiness(strict=True)),
            QualitySubgate("standards-status", "Local MIPSoftware/MIASI standards registry status.", lambda: self.service.standards_status()),
            QualitySubgate("miasi-validate", "MIASI agent/tool/policy matrix structural validation.", lambda: self.service.miasi_validate(scope="all")),
            QualitySubgate("eval-harness-ready", "Evaluation harness fixture readiness without executing eval workdir mutations.", self._eval_harness_ready),
            QualitySubgate("app-contract", "ApplicationService v2 contract availability.", lambda: self.service.application_contract()),
        ]
        if self.options.profile in {"full", "ci", "release", "industrial", "hardening"}:
            subgates.append(QualitySubgate("validation-gateway-all", "Unified docs/contracts validation gateway.", lambda: self.service.validation.gateway(scope="all")))
            subgates.append(QualitySubgate("visual-product-smoke", "Fase F visual product smoke gate in dry-run JSON mode.", self._visual_product_smoke))
        if self.options.profile in {"ci", "release", "industrial", "hardening"}:
            subgates.append(QualitySubgate("ci-workflow-static", "Static safety validation for optional GitHub Actions workflow scaffold.", self._ci_workflow_static))
            subgates.append(QualitySubgate("advanced-evals-safety", "Advanced agentic, red-team, plugin ecosystem, multiworkspace, identity/RBAC, audit-pack, compliance-pack and remote/enterprise safety eval suites meet scoring thresholds.", self._advanced_evals_safety))
        if self.options.profile in {"release", "industrial"}:
            subgates.extend([
                QualitySubgate("release-manifest-static", "Release manifest builder can generate local release evidence.", self._release_manifest_static),
                QualitySubgate("release-changelog-static", "Release changelog builder can generate local changelog evidence.", self._release_changelog_static),
                QualitySubgate("release-package-dry-run", "Package builder can produce a dry-run release package plan.", self._release_package_dry_run),
                QualitySubgate("release-sbom-static", "SBOM builder can generate a local supply-chain baseline.", self._release_sbom_static),
                QualitySubgate("release-install-upgrade-static", "Install plan and upgrade check are available for local release readiness.", self._release_install_upgrade_static),
            ])
        if self.options.profile in {"hardening", "industrial"}:
            subgates.append(QualitySubgate("test-contract-registry", "POST-H-001 test contract registry validation.", self._test_contract_registry))
            subgates.append(QualitySubgate("test-contract-registry-v2", "POST-H-003 Test Contract Registry v2 validation without executing tests.", self._test_contract_registry_v2))
            subgates.append(QualitySubgate("project-global-state", "Centralized mutable project state synchronization.", self._project_global_state))
            subgates.append(QualitySubgate("maturity-dashboard", "POST-H-002 maturity dashboard quality gate.", lambda: self.service.maturity_dashboard_gate()))
            subgates.append(QualitySubgate("miasi-semantic-validate", "POST-H-004 MIASI semantic validator quality gate.", self._miasi_semantic_validate))
            subgates.append(QualitySubgate("architecture-map", "POST-H-005 executable architecture map and ownership validation gate.", self._architecture_map))
            subgates.append(QualitySubgate("application-cli-boundary-integration", "POST-H-007-E CLI registry to ApplicationService operation mapping and API/UI contract gate.", self._application_cli_boundary_integration))
            subgates.append(QualitySubgate("runtime-state-hygiene", "Runtime-state hygiene and source archive readiness gate.", self._runtime_state_hygiene))
            subgates.append(QualitySubgate("docs-governance", "POST-H-009 documentation governance, canonical source sync and backlog governance gate.", self._docs_governance))
            subgates.append(QualitySubgate("observability-retention", "POST-H-010 observability retention, redaction and clean ZIP hygiene gate.", self._observability_retention_hygiene))
            subgates.append(QualitySubgate("rag-groundedness-ready", "POST-H-011 RAG groundedness local readiness gate.", self._rag_groundedness_ready))
            subgates.append(QualitySubgate("approval-rbac-hardening", "POST-H-012 Approval/RBAC hardening operational gate.", self._approval_rbac_hardening))
            subgates.append(QualitySubgate("audit-pack-integrity", "POST-H-013 Audit pack integrity, no-go gates, runbook and disclaimer gate.", self._audit_pack_integrity))
            subgates.append(QualitySubgate("ui-api-industrial-shell", "POST-H-014 UI/API route registries, Web UI smoke, local security posture and operations docs gate.", self._ui_api_industrial_shell))
            subgates.append(QualitySubgate("operator-dashboard-ready", "POST-H-015 local operator dashboard snapshot, CLI, no-go gates and runbook readiness gate.", self._operator_dashboard_ready))
            subgates.append(QualitySubgate("workspace-portfolio-hardening", "POST-H-016 workspace registry, isolation, portfolio status, API boundary and onboarding runbook gate.", self._workspace_portfolio_hardening))
            subgates.append(QualitySubgate("release-reproducibility", "POST-H-017 local release reproducibility pack generation and verification gate.", self._release_reproducibility))
            subgates.append(QualitySubgate("connector-sandbox", "POST-H-018 connector sandbox deny-write, replay, redaction and Policy/Approval/RBAC gate.", self._connector_sandbox))
            subgates.append(QualitySubgate("plugin-sandbox-design", "POST-H-019 plugin registry, permission model, exposure report and eval fixture safety gate.", self._plugin_sandbox_design))
            subgates.append(QualitySubgate("compliance-mapping-pack", "POST-H-020 compliance mapping validator, evidence report, audit-pack summary and compliance-pack eval gate.", self._compliance_mapping_pack))
            subgates.append(QualitySubgate("remote-readiness-design-only", "POST-H-021 remote runner disabled readiness, ADR and eval-signal gate.", self._remote_readiness_design_only))
            subgates.append(QualitySubgate("enterprise-threat-model-design-only", "POST-H-022 enterprise threat model, control matrix and readiness blocker gate.", self._enterprise_threat_model_design_only))
        if self.options.profile == "industrial":
            subgates.append(QualitySubgate("industrial-readiness", "Fase H industrial readiness gate and maturity classification.", self._industrial_readiness))
        if self.options.profile == "hardening":
            subgates.append(QualitySubgate("industrial-readiness", "Industrial baseline remains coherent after test hardening.", self._industrial_readiness))
        if self._should_run_pytest():
            subgates.append(QualitySubgate("pytest", "Explicit pytest regression subprocess for CI/release readiness.", self._pytest_run))
        return subgates

    def _should_run_pytest(self) -> bool:
        return self.options.include_pytest

    def _run_subgate(self, subgate: QualitySubgate) -> CommandResult:
        try:
            return subgate.runner()
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return CommandResult(
                command=f"quality subgate {subgate.id}",
                ok=False,
                exit_code=ExitCode.ERROR,
                message=f"Quality subgate raised {type(exc).__name__}.",
                data={"summary": {"subgate": subgate.id, "preliminary": True}},
                findings=[Finding("QUALITY_SUBGATE_EXCEPTION", str(exc), Severity.ERROR, metadata={"subgate": subgate.id, "exception_type": type(exc).__name__})],
            )

    def _eval_harness_ready(self) -> CommandResult:
        fixture = self.root / "evals" / "fixtures" / "documentation_eval_cases.json"
        findings: list[Finding] = []
        summary: dict[str, Any] = {
            "fixture_path": "evals/fixtures/documentation_eval_cases.json",
            "fixture_exists": fixture.exists(),
            "cases_total": 0,
            "suite_id": None,
            "executes_eval_workdir": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "preliminary": True,
        }
        if not fixture.exists():
            findings.append(Finding("EVAL_FIXTURE_MISSING", "Evaluation fixture is missing.", Severity.BLOCK, path="evals/fixtures/documentation_eval_cases.json"))
            return CommandResult("quality eval-harness-ready", False, ExitCode.BLOCK, "Evaluation harness fixture is missing.", data={"summary": summary}, findings=findings)
        try:
            payload = json.loads(fixture.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("EVAL_FIXTURE_JSON_INVALID", "Evaluation fixture is not valid JSON.", Severity.ERROR, path="evals/fixtures/documentation_eval_cases.json", metadata={"error": str(exc)}))
            return CommandResult("quality eval-harness-ready", False, ExitCode.ERROR, "Evaluation harness fixture JSON is invalid.", data={"summary": summary}, findings=findings)

        cases = payload.get("cases") if isinstance(payload, dict) else None
        summary["suite_id"] = payload.get("suite_id") if isinstance(payload, dict) else None
        summary["cases_total"] = len(cases) if isinstance(cases, list) else 0
        if not isinstance(cases, list) or not cases:
            findings.append(Finding("EVAL_FIXTURE_EMPTY", "Evaluation fixture has no cases.", Severity.BLOCK, path="evals/fixtures/documentation_eval_cases.json"))
        if summary["suite_id"] != "documentation":
            findings.append(Finding("EVAL_FIXTURE_SUITE_UNEXPECTED", "Evaluation fixture suite_id is not documentation.", Severity.FAIL, path="evals/fixtures/documentation_eval_cases.json", metadata={"suite_id": summary["suite_id"]}))
        ok = not findings
        return CommandResult(
            command="quality eval-harness-ready",
            ok=ok,
            exit_code=ExitCode.PASS if ok else self._exit_code_from_findings(findings),
            message="Evaluation harness fixture is ready." if ok else "Evaluation harness fixture readiness failed.",
            data={"summary": summary},
            findings=findings or [Finding("EVAL_HARNESS_READY", "Evaluation fixture is parseable and declares documentation cases.", Severity.INFO, metadata={"cases_total": summary["cases_total"]})],
        )

    def _test_contract_registry(self) -> CommandResult:
        from devpilot_core.testing import TestContractRegistry

        return TestContractRegistry(self.root).validate()

    def _test_contract_registry_v2(self) -> CommandResult:
        from devpilot_core.testing import TestContractRegistryV2Validator

        return TestContractRegistryV2Validator(self.root).validate()

    def _operator_dashboard_ready(self) -> CommandResult:
        from devpilot_core.portfolio import OperatorDashboardReadyGate

        return OperatorDashboardReadyGate(self.root).run()

    def _workspace_portfolio_hardening(self) -> CommandResult:
        from devpilot_core.portfolio import WorkspacePortfolioHardeningGate

        return WorkspacePortfolioHardeningGate(self.root).run()

    def _miasi_semantic_validate(self) -> CommandResult:
        from devpilot_core.miasi import MiasiSemanticValidator

        return MiasiSemanticValidator(self.root).validate()

    def _architecture_map(self) -> CommandResult:
        from devpilot_core.architecture import ArchitectureMapReportBuilder, ArchitectureMapReportOptions

        return ArchitectureMapReportBuilder(self.root, ArchitectureMapReportOptions(write_report=False)).build()

    def _project_global_state(self) -> CommandResult:
        from devpilot_core.testing import TestContractRegistry

        return TestContractRegistry(self.root).project_state()


    def _application_cli_boundary_integration(self) -> CommandResult:
        from devpilot_core.application import CliApplicationBoundaryIntegrationReportBuilder

        return CliApplicationBoundaryIntegrationReportBuilder(self.root).run()

    def _runtime_state_hygiene(self) -> CommandResult:
        from devpilot_core.runtime_state import RuntimeStateHygieneGate, RuntimeStateHygieneOptions

        return RuntimeStateHygieneGate(self.root, RuntimeStateHygieneOptions(write_report=False)).run()


    def _docs_governance(self) -> CommandResult:
        from devpilot_core.docs_governance import run_docs_governance_quality_subgate

        return run_docs_governance_quality_subgate(self.root)

    def _observability_retention_hygiene(self) -> CommandResult:
        from devpilot_core.observability import ObservabilityRetentionHygieneGate, ObservabilityRetentionHygieneOptions

        return ObservabilityRetentionHygieneGate(self.root, ObservabilityRetentionHygieneOptions(write_report=False)).run()

    def _rag_groundedness_ready(self) -> CommandResult:
        from devpilot_core.rag import RagGroundednessReadyGate, RagGroundednessReadyGateOptions

        return RagGroundednessReadyGate(self.root, options=RagGroundednessReadyGateOptions()).run()

    def _approval_rbac_hardening(self) -> CommandResult:
        from devpilot_core.approval import ApprovalRbacHardeningGate

        return ApprovalRbacHardeningGate(self.root).run()

    def _audit_pack_integrity(self) -> CommandResult:
        from devpilot_core.auditpack import AuditPackIntegrityGate

        return AuditPackIntegrityGate(self.root).run()

    def _ui_api_industrial_shell(self) -> CommandResult:
        from devpilot_core.interfaces.api import UiApiIndustrialShellGate, UiApiIndustrialShellGateOptions

        return UiApiIndustrialShellGate(self.root, UiApiIndustrialShellGateOptions(write_report=False)).run()

    def _release_reproducibility(self) -> CommandResult:
        from devpilot_core.release import ReleaseReproducibilityPackBuilder, ReleaseReproducibilityPackOptions

        return ReleaseReproducibilityPackBuilder(
            self.root,
            options=ReleaseReproducibilityPackOptions(write_report=True, verify_after_build=True),
        ).build()

    def _connector_sandbox(self) -> CommandResult:
        from devpilot_core.connectors import ConnectorSandboxQualityGate

        return ConnectorSandboxQualityGate(self.root).run()

    def _plugin_sandbox_design(self) -> CommandResult:
        from devpilot_core.plugins import PluginSandboxQualityGate

        return PluginSandboxQualityGate(self.root).run()

    def _compliance_mapping_pack(self) -> CommandResult:
        from devpilot_core.compliance import ComplianceMappingQualityGate

        return ComplianceMappingQualityGate(self.root).run()

    def _remote_readiness_design_only(self) -> CommandResult:
        from devpilot_core.remote import RemoteReadinessQualityGate

        return RemoteReadinessQualityGate(self.root).run()

    def _enterprise_threat_model_design_only(self) -> CommandResult:
        from devpilot_core.enterprise import EnterpriseThreatModelQualityGate

        return EnterpriseThreatModelQualityGate(self.root).run()

    def _industrial_readiness(self) -> CommandResult:
        from devpilot_core.industrial import IndustrialReadinessGate

        return IndustrialReadinessGate(self.root).check()

    def _advanced_evals_safety(self) -> CommandResult:
        """Consume Sprint 92 advanced/red-team eval results in CI/release gates."""

        runner = EvalRunner(self.root, config=EvalRunnerConfig(workdir=Path("outputs/evals/workdir_quality_gate")))
        suites = ["advanced-agentic", "red-team", "plugin-ecosystem", "multiworkspace-isolation", "identity-rbac", "audit-pack-integrity", "compliance-pack-integrity", "remote-enterprise"]
        results = [runner.run(suite=suite) for suite in suites]
        subresults = [result.to_dict() for result in results]
        blocking_findings = [finding for result in results for finding in result.findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        safety_scores = {
            result.data.get("summary", {}).get("suite_id", suite): result.data.get("summary", {}).get("safety_score")
            for suite, result in zip(suites, results)
        }
        ok = all(result.ok for result in results) and not blocking_findings
        summary = {
            "suites": suites,
            "suites_total": len(suites),
            "suites_passed": sum(1 for result in results if result.ok),
            "safety_scores": safety_scores,
            "blocking_findings_total": len(blocking_findings),
            "network_used": False,
            "external_api_used": False,
            "llm_judge_used": False,
            "source_mutations_performed": False,
            "outputs_written": True,
            "preliminary": True,
        }
        return CommandResult(
            command="quality advanced-evals-safety",
            ok=ok,
            exit_code=ExitCode.PASS if ok else self._exit_code_from_findings(blocking_findings),
            message="Advanced safety eval suites passed." if ok else "Advanced safety eval suites failed or blocked.",
            data={"summary": summary, "subresults": subresults},
            findings=[Finding("ADVANCED_EVALS_SAFETY_PASS", "Advanced agentic/red-team/plugin ecosystem/multiworkspace/identity/audit-pack/compliance-pack/remote-enterprise eval suites meet safety thresholds.", Severity.INFO, metadata=summary)] if ok else blocking_findings,
        )

    def _ci_workflow_static(self) -> CommandResult:
        workflow = self.root / ".github" / "workflows" / "devpilot-ci.yml"
        findings: list[Finding] = []
        summary: dict[str, Any] = {
            "workflow_path": ".github/workflows/devpilot-ci.yml",
            "workflow_exists": workflow.exists(),
            "uses_secrets": False,
            "deploy_or_publish_detected": False,
            "external_api_markers_detected": False,
            "quality_gate_ci_profile_referenced": False,
            "pytest_referenced": False,
            "pull_request_trigger": False,
            "push_trigger": False,
            "permissions_read_only": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "preliminary": True,
        }
        if not workflow.exists():
            findings.append(Finding("CI_WORKFLOW_MISSING", "Optional GitHub Actions workflow scaffold is missing.", Severity.BLOCK, path=".github/workflows/devpilot-ci.yml"))
            return CommandResult("quality ci-workflow-static", False, ExitCode.BLOCK, "CI workflow scaffold is missing.", data={"summary": summary}, findings=findings)

        content = workflow.read_text(encoding="utf-8")
        lowered = content.lower()
        forbidden_markers = [
            "secrets.",
            "ghcr.io",
            "docker/login-action",
            "pypa/gh-action-pypi-publish",
            "twine upload",
            "npm publish",
            "git push",
            "release-action",
            "create-release",
            "upload-release",
            "deploy",
            "publish",
            "production",
            "cloud",
        ]
        summary["uses_secrets"] = "secrets." in lowered
        summary["deploy_or_publish_detected"] = any(marker in lowered for marker in forbidden_markers)
        summary["external_api_markers_detected"] = any(marker in lowered for marker in ["openai_api_key", "gemini_api_key", "anthropic_api_key", "mistral_api_key"])
        summary["quality_gate_ci_profile_referenced"] = "quality-gate run --profile ci" in lowered
        summary["pytest_referenced"] = "pytest -q" in lowered
        summary["pull_request_trigger"] = "pull_request:" in lowered
        summary["push_trigger"] = "push:" in lowered
        summary["permissions_read_only"] = "contents: read" in lowered and "permissions:" in lowered

        if summary["uses_secrets"]:
            findings.append(Finding("CI_WORKFLOW_SECRETS_USED", "CI workflow must not reference GitHub secrets in Sprint 76.", Severity.BLOCK, path=".github/workflows/devpilot-ci.yml"))
        if summary["deploy_or_publish_detected"]:
            findings.append(Finding("CI_WORKFLOW_DEPLOY_OR_PUBLISH", "CI workflow must not deploy or publish artifacts in Sprint 76.", Severity.BLOCK, path=".github/workflows/devpilot-ci.yml"))
        if summary["external_api_markers_detected"]:
            findings.append(Finding("CI_WORKFLOW_EXTERNAL_API_MARKER", "CI workflow must not configure external model API credentials.", Severity.BLOCK, path=".github/workflows/devpilot-ci.yml"))
        if not summary["quality_gate_ci_profile_referenced"]:
            findings.append(Finding("CI_WORKFLOW_QUALITY_GATE_MISSING", "CI workflow must invoke quality-gate run --profile ci.", Severity.FAIL, path=".github/workflows/devpilot-ci.yml"))
        if not summary["pytest_referenced"]:
            findings.append(Finding("CI_WORKFLOW_PYTEST_MISSING", "CI workflow must keep pytest visible in the CI contract.", Severity.FAIL, path=".github/workflows/devpilot-ci.yml"))
        if not summary["pull_request_trigger"]:
            findings.append(Finding("CI_WORKFLOW_PR_TRIGGER_MISSING", "CI workflow should run on pull_request.", Severity.WARNING, path=".github/workflows/devpilot-ci.yml"))
        if not summary["permissions_read_only"]:
            findings.append(Finding("CI_WORKFLOW_PERMISSIONS_NOT_READ_ONLY", "CI workflow should declare read-only contents permission.", Severity.WARNING, path=".github/workflows/devpilot-ci.yml"))

        ok = not any(finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for finding in findings)
        return CommandResult(
            command="quality ci-workflow-static",
            ok=ok,
            exit_code=ExitCode.PASS if ok else self._exit_code_from_findings(findings),
            message="CI workflow scaffold is safe." if ok else "CI workflow scaffold validation failed.",
            data={"summary": summary},
            findings=findings or [Finding("CI_WORKFLOW_STATIC_PASS", "CI workflow scaffold is local-first, read-only and has no deploy/publish/secrets markers.", Severity.INFO, metadata={"workflow_path": ".github/workflows/devpilot-ci.yml"})],
        )

    def _visual_product_smoke(self) -> CommandResult:
        script = self.root / "scripts" / "visual_product_smoke.py"
        if not script.exists():
            return CommandResult(
                "visual product smoke",
                False,
                ExitCode.BLOCK,
                "Visual product smoke script is missing.",
                data={"summary": {"script": "scripts/visual_product_smoke.py", "preliminary": True}},
                findings=[Finding("VISUAL_PRODUCT_SMOKE_SCRIPT_MISSING", "scripts/visual_product_smoke.py is missing.", Severity.BLOCK, path="scripts/visual_product_smoke.py")],
            )
        completed = subprocess.run(
            [sys.executable, str(script), "--dry-run", "--json"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        try:
            payload = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            payload = {}
        ok = completed.returncode == 0 and bool(payload.get("ok"))
        summary = dict((payload.get("data") or {}).get("summary") or {}) if isinstance(payload, dict) else {}
        summary.update({"returncode": completed.returncode, "stdout_parseable": bool(payload), "stderr_tail": completed.stderr[-500:], "preliminary": True})
        return CommandResult(
            command="visual product smoke",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Visual product smoke passed." if ok else "Visual product smoke failed.",
            data={"summary": summary, "payload": payload},
            findings=[Finding("VISUAL_PRODUCT_SMOKE_PASS", "Visual product smoke gate passed.", Severity.INFO)] if ok else [Finding("VISUAL_PRODUCT_SMOKE_BLOCK", "Visual product smoke gate failed.", Severity.BLOCK, metadata={"returncode": completed.returncode})],
        )


    def _release_manifest_static(self) -> CommandResult:
        try:
            from devpilot_core.release import ReleaseManifestBuilder, ReleaseManifestOptions

            return ReleaseManifestBuilder(self.root, options=ReleaseManifestOptions(version=_project_version(self.root))).build()
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return CommandResult(
                command="quality release-manifest-static",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Release manifest static gate failed with an exception.",
                data={"summary": {"preliminary": True, "network_used": False, "external_api_used": False}},
                findings=[Finding("RELEASE_MANIFEST_STATIC_EXCEPTION", str(exc), Severity.ERROR)],
            )

    def _release_changelog_static(self) -> CommandResult:
        try:
            from devpilot_core.release import ReleaseChangelogBuilder, ReleaseChangelogOptions

            return ReleaseChangelogBuilder(self.root, options=ReleaseChangelogOptions(version=_project_version(self.root))).build()
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return CommandResult(
                command="quality release-changelog-static",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Release changelog static gate failed with an exception.",
                data={"summary": {"preliminary": True, "network_used": False, "external_api_used": False}},
                findings=[Finding("RELEASE_CHANGELOG_STATIC_EXCEPTION", str(exc), Severity.ERROR)],
            )

    def _release_package_dry_run(self) -> CommandResult:
        try:
            from devpilot_core.release import PackageBuildBuilder, PackageBuildOptions

            return PackageBuildBuilder(self.root, options=PackageBuildOptions(version=_project_version(self.root), kind="all", execute=False)).build()
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return CommandResult(
                command="quality release-package-dry-run",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Release package dry-run gate failed with an exception.",
                data={"summary": {"preliminary": True, "network_used": False, "external_api_used": False, "execute": False}},
                findings=[Finding("RELEASE_PACKAGE_DRY_RUN_EXCEPTION", str(exc), Severity.ERROR)],
            )

    def _release_sbom_static(self) -> CommandResult:
        try:
            from devpilot_core.release import ReleaseSbomBuilder, ReleaseSbomOptions

            return ReleaseSbomBuilder(self.root, options=ReleaseSbomOptions(version=_project_version(self.root))).build()
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return CommandResult(
                command="quality release-sbom-static",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Release SBOM static gate failed with an exception.",
                data={"summary": {"preliminary": True, "network_used": False, "external_api_used": False}},
                findings=[Finding("RELEASE_SBOM_STATIC_EXCEPTION", str(exc), Severity.ERROR)],
            )

    def _release_install_upgrade_static(self) -> CommandResult:
        try:
            from devpilot_core.release import InstallPlanBuilder, InstallPlanOptions, UpgradeCheckBuilder, UpgradeCheckOptions

            install = InstallPlanBuilder(self.root, options=InstallPlanOptions(mode="all", version=_project_version(self.root))).build()
            upgrade = UpgradeCheckBuilder(self.root, options=UpgradeCheckOptions(target_version=_project_version(self.root))).build()
            findings = [*install.findings, *upgrade.findings]
            ok = install.ok and upgrade.ok
            summary = {
                "install_plan_ok": install.ok,
                "upgrade_check_ok": upgrade.ok,
                "dry_run_default": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "preliminary": True,
            }
            return CommandResult(
                command="quality release-install-upgrade-static",
                ok=ok,
                exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
                message="Release install/upgrade static gate passed." if ok else "Release install/upgrade static gate failed.",
                data={"summary": summary},
                findings=findings or [Finding("RELEASE_INSTALL_UPGRADE_STATIC_PASS", "Install plan and upgrade check are available for release readiness.", Severity.INFO)],
            )
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return CommandResult(
                command="quality release-install-upgrade-static",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Release install/upgrade static gate failed with an exception.",
                data={"summary": {"preliminary": True, "network_used": False, "external_api_used": False}},
                findings=[Finding("RELEASE_INSTALL_UPGRADE_STATIC_EXCEPTION", str(exc), Severity.ERROR)],
            )

    def _pytest_run(self) -> CommandResult:
        timeout = max(10, min(int(self.options.pytest_timeout_seconds), 1800))
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                command="pytest -q",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="pytest timed out during quality gate.",
                data={"summary": {"executed": True, "timed_out": True, "timeout_seconds": timeout, "preliminary": True}},
                findings=[Finding("QUALITY_GATE_PYTEST_TIMEOUT", "pytest timed out during quality gate.", Severity.BLOCK, metadata={"timeout_seconds": timeout, "stdout_tail": (exc.stdout or "")[-500:], "stderr_tail": (exc.stderr or "")[-500:]})],
            )
        ok = completed.returncode == 0
        return CommandResult(
            command="pytest -q",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.FAIL,
            message="pytest completed successfully." if ok else "pytest returned non-zero exit code.",
            data={
                "summary": {
                    "executed": True,
                    "returncode": completed.returncode,
                    "timed_out": timed_out,
                    "timeout_seconds": timeout,
                    "stdout_tail": completed.stdout[-1000:],
                    "stderr_tail": completed.stderr[-1000:],
                    "preliminary": True,
                }
            },
            findings=[Finding("QUALITY_GATE_PYTEST_PASS", "pytest -q passed.", Severity.INFO)] if ok else [Finding("QUALITY_GATE_PYTEST_FAIL", "pytest -q failed.", Severity.FAIL, metadata={"returncode": completed.returncode})],
        )

    @staticmethod
    def _subgate_record(subgate: QualitySubgate, result: CommandResult, duration_ms: int) -> dict[str, Any]:
        severities = [finding.severity for finding in result.findings]
        summary = dict((result.data or {}).get("summary") or {})
        return {
            "id": subgate.id,
            "description": subgate.description,
            "command": result.command,
            "ok": result.ok,
            "exit_code": int(result.exit_code),
            "critical": subgate.critical,
            "duration_ms": duration_ms,
            "findings_total": len(result.findings),
            "warnings_total": sum(1 for severity in severities if severity == Severity.WARNING),
            "blocking_findings_total": sum(1 for severity in severities if severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}),
            "summary": summary,
        }

    @staticmethod
    def _prefixed_findings(subgate: QualitySubgate, result: CommandResult) -> list[Finding]:
        if not result.findings:
            return []
        prefixed: list[Finding] = []
        for finding in result.findings:
            metadata = {"subgate": subgate.id, "source_command": result.command, "source_finding_id": finding.id, **(finding.metadata or {})}
            prefixed.append(
                Finding(
                    id=f"QUALITY_GATE_{subgate.id.upper().replace('-', '_')}_{finding.id}",
                    message=finding.message,
                    severity=finding.severity,
                    path=finding.path,
                    metadata=metadata,
                )
            )
        return prefixed

    @staticmethod
    def _derive_exit_code(subgate_records: list[dict[str, Any]]) -> ExitCode:
        if any(int(item["exit_code"]) == int(ExitCode.ERROR) for item in subgate_records):
            return ExitCode.ERROR
        if any(int(item["exit_code"]) == int(ExitCode.BLOCK) for item in subgate_records):
            return ExitCode.BLOCK
        if any(int(item["exit_code"]) == int(ExitCode.FAIL) for item in subgate_records):
            return ExitCode.FAIL
        return ExitCode.PASS

    @staticmethod
    def _exit_code_from_findings(findings: list[Finding]) -> ExitCode:
        severities = {finding.severity for finding in findings}
        if Severity.ERROR in severities:
            return ExitCode.ERROR
        if Severity.BLOCK in severities:
            return ExitCode.BLOCK
        if Severity.FAIL in severities:
            return ExitCode.FAIL
        return ExitCode.PASS


def _project_version(root: Path) -> str:
    try:
        import tomllib

        payload = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
        return str(project.get("version") or "0.1.0")
    except Exception:
        return "0.1.0"
