from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .agents import AgentRuntime, AgentRuntimeConfig
from .approval.models import ApprovalStatus
from .approval.service import ApprovalCliInput, ApprovalService
from .application import ApplicationService
from .cli_models import CommandResult, ExitCode, Finding, Severity
from .errors import DevPilotError
from .evals import EvalRunner
from .observability import AgentOpsGateOptions, AgentOpsQualityGate, EventLogger, MetricsCollector, OTelDryRunExporter, OTelExportOptions, TraceQueryService
from .miasi import MiasiRegistryValidator
from .modeling import BudgetLedger, CapabilityMatrix, ModelAdapterRouter, ModelEvalRunner, ModelEvalRunnerConfig, ModelHealthService, ModelRouterConfig
from .policy import CostPolicy, PolicyEngine, PolicyRequest, load_cost_policy
from .prompts import PromptRegistry
from .quality import QualityGate, QualityGateOptions
from .release import (
    BackupCreateBuilder,
    BackupCreateOptions,
    BackupListBuilder,
    BackupListOptions,
    BackupRestoreBuilder,
    BackupRestoreOptions,
    PackageBuildBuilder,
    PackageBuildOptions,
    InstallPlanBuilder,
    InstallPlanOptions,
    ReleaseChangelogBuilder,
    ReleaseChangelogOptions,
    ReleaseChecksumBuilder,
    ReleaseChecksumOptions,
    ReleaseManifestBuilder,
    ReleaseManifestOptions,
    ReleaseSbomBuilder,
    ReleaseSbomOptions,
    ReleaseSmokeTestBuilder,
    ReleaseSmokeTestOptions,
    ReleaseVerifyBuilder,
    ReleaseVerifyOptions,
    UpgradeCheckBuilder,
    UpgradeCheckOptions,
    checksum_line,
)
from .reports import ReportEngine, build_report_id
from .security import PolicySimulationSuite, SecurityReadiness
from .schemas import BuiltinContractValidator, SchemaRegistry, SchemaValidator
from .schemas.builtins import parse_provider_config_yaml
from .repo import ArchitectureDriftDetector, DependencyGraphBuilder, GitAdapter, RepoAnalyzer, RepoInventory, RepoQualityGate, RepoQualityGateConfig, RepoEngineeringGate, RepoEngineeringGateConfig
from .repo.diff_report import GitDiffReportBuilder
from .refactor import RefactorExecutor, RefactorPlanner
from .review import CodeReviewEngine, PatchPreflightEngine, PatchReviewEngine
from .sandbox import PatchSandboxManager
from .changes import RollbackManager
from .standards.registry import build_standards_status_result
from .store import LocalStore
from .traceability import MarkdownTraceabilityExtractor, TraceabilityEngine
from .testing import TestsRunTool
from .validation import ValidationGateway
from .workspace import WorkspaceManager
from .validators.artifact import validate_artifact_file
from .validators.checklist import validate_precode_checklist
from .validators.frontmatter import validate_frontmatter_file
from .validators.readiness import (
    REQUIRED_MIASI_ARTIFACTS,
    REQUIRED_PRE_CODE_ARTIFACTS,
    build_readiness_result,
    build_strict_readiness_result,
    check_required_artifacts,
    write_readiness_reports,
)

ROOT_MARKERS = ["pyproject.toml", "docs"]


def project_root() -> Path:
    """Return the resolved DevPilot workspace/project root.

    FUNC-SPRINT-08 replaces the earlier current-directory shortcut with
    WorkspaceManager discovery. The fallback still supports bootstrap commands
    before `.devpilot/project.yaml` exists.
    """

    return WorkspaceManager.discover(Path.cwd()).root


def build_miasi_required_result() -> CommandResult:
    """Build the normalized result for the `miasi-required` command."""

    data = {
        "project": "DevPilot Local",
        "miasi_required": True,
        "reason": "La plataforma será agent-assisted y tendrá validadores/agentes para SDLC.",
        "required_artifacts": REQUIRED_MIASI_ARTIFACTS,
    }
    return CommandResult(
        command="miasi-required",
        ok=True,
        exit_code=ExitCode.PASS,
        message="MIASI is required for DevPilot Local.",
        data=data,
        findings=[
            Finding(
                id="MIASI_REQUIRED",
                message="DevPilot Local activates MIASI because it is an agent-assisted SDLC platform.",
                severity=Severity.INFO,
            )
        ],
    )


def print_result(result: CommandResult, *, json_output: bool = False) -> None:
    """Render a CommandResult for CLI users."""

    if json_output:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return

    # Backwards-compatible human output for bootstrap commands.
    if result.command == "readiness-check":
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return
    if result.command == "miasi-required":
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return

    print(result.message)
    reports = (result.data or {}).get("reports")
    if isinstance(reports, dict):
        if reports.get("json"):
            print(f"Report JSON: {reports['json']}")
        if reports.get("markdown"):
            print(f"Report Markdown: {reports['markdown']}")
    for finding in result.findings:
        path = f" [{finding.path}]" if finding.path else ""
        print(f"- {finding.severity.value.upper()}: {finding.id}{path} — {finding.message}")


def _with_report_paths(result: CommandResult, report_paths: dict[str, str]) -> CommandResult:
    """Return a CommandResult with report paths attached to data."""

    data = dict(result.data or {})
    data["reports"] = report_paths
    return CommandResult(
        command=result.command,
        ok=result.ok,
        exit_code=result.exit_code,
        message=result.message,
        data=data,
        findings=result.findings,
    )


def _write_optional_command_report(
    root: Path,
    result: CommandResult,
    *,
    subject: str | Path | None = None,
    report_id: str | None = None,
    write_report: bool = False,
    metadata: dict[str, str] | None = None,
) -> CommandResult:
    """Persist report evidence when requested and attach generated paths."""

    if not write_report:
        return result
    effective_report_id = report_id or build_report_id(result.command, subject=subject)
    paths = ReportEngine(root).write_command_report(
        result,
        report_id=effective_report_id,
        subject=subject,
        metadata={"contract": "EvidenceReport", **(metadata or {})},
    )
    return _with_report_paths(result, paths.to_dict())




def _persist_result(root: Path, result: CommandResult, *, subject: str | Path | None = None) -> CommandResult:
    """Persist command result in LocalStore without changing command semantics.

    FUNC-SPRINT-10 introduces SQLite operational history. Persistence is
    intentionally best-effort for existing gates so a temporary SQLite write
    problem does not convert a previously valid validation command into a
    failed validation. Dedicated `state` commands still surface persistence
    errors directly through their own CommandResult.
    """

    try:
        LocalStore(root).record_command_result(result, subject=subject, metadata={"component": "CLI"})
    except Exception:
        # Existing gates must remain stable. Store diagnostics are handled by
        # `state status`/`state init` and future observability hardening.
        pass
    try:
        MetricsCollector(root).record_command_result(result, subject=subject, metadata={"component": "CLI"})
    except Exception:
        # FUNC-SPRINT-59 metrics are best-effort and must never change command semantics.
        pass
    return result

def _emit_result_event(root: Path, result: CommandResult, *, subject: str | Path | None = None) -> None:
    """Emit a local JSONL gate event for a command result.

    Event logging is part of FUNC-SPRINT-07. It is intentionally local and
    deterministic. If a gate produces a CommandResult, DevPilot records a
    compact, redacted `gate.evaluated` event under outputs/traces/events.jsonl.
    """

    EventLogger(root).emit_result(result, subject=subject)


def readiness_check(*, json_output: bool = False, strict: bool = False, write_report: bool = False) -> int:
    root = project_root()
    result = ApplicationService(root).readiness(strict=strict)

    # Backwards compatibility: readiness-check already generated evidence in
    # FUNC-SPRINT-05. FUNC-SPRINT-06 keeps that behavior but delegates it to the
    # central ReportEngine through write_readiness_reports(). FUNC-SPRINT-18
    # obtains the CommandResult through ApplicationService so future UI shells
    # can reuse the same core boundary.
    report_paths = write_readiness_reports(root, result)
    result = _with_report_paths(result, report_paths)
    _emit_result_event(root, result)
    _persist_result(root, result, subject="readiness-check")

    print_result(result, json_output=json_output)
    return int(result.exit_code)


def miasi_required(*, json_output: bool = False) -> int:
    root = project_root()
    result = build_miasi_required_result()
    _emit_result_event(root, result)
    _persist_result(root, result, subject="miasi-required")
    print_result(result, json_output=json_output)
    return int(result.exit_code)





def _model_router(
    root: Path,
    *,
    allow_external_api: bool = False,
    budget_limit_usd: float = 0.0,
    budget_used_usd: float = 0.0,
    local_timeout_seconds: float = 3.0,
    fallback_to_mock_on_local_unavailable: bool = False,
) -> ModelAdapterRouter:
    """Build a ModelAdapterRouter with explicit cost controls."""

    return ModelAdapterRouter(
        root,
        config=ModelRouterConfig(
            allow_external_api=allow_external_api,
            budget_limit_usd=budget_limit_usd,
            budget_used_usd=budget_used_usd,
            local_timeout_seconds=local_timeout_seconds,
            fallback_to_mock_on_local_unavailable=fallback_to_mock_on_local_unavailable,
        ),
    )


def model_health_command(
    *,
    provider: str | None = None,
    timeout_seconds: float = 3.0,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run bounded local-only provider health checks.

    Without --provider, FUNC-SPRINT-48 reports the whole governed provider
    fleet. With --provider, it preserves the Sprint 46/47 single-provider
    health behavior. External providers are never contacted.
    """

    root = project_root()
    if provider:
        result = _model_router(root, local_timeout_seconds=timeout_seconds).health(provider=provider)
        subject = f"provider:{provider}"
    else:
        result = ModelHealthService(root, timeout_seconds=timeout_seconds).check_all()
        subject = "providers:all"
    result = _write_optional_command_report(
        root,
        result,
        subject=subject,
        report_id="model_health",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-48", "component": "ModelHealthService"},
    )
    _emit_result_event(root, result, subject=subject)
    _persist_result(root, result, subject=subject)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def model_capabilities_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Report the governed model capability matrix without contacting servers."""

    root = project_root()
    result = CapabilityMatrix(root).build()
    result = _write_optional_command_report(
        root,
        result,
        subject="providers:capabilities",
        report_id="model_capabilities",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-48", "component": "CapabilityMatrix"},
    )
    _emit_result_event(root, result, subject="providers:capabilities")
    _persist_result(root, result, subject="providers:capabilities")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def model_budget_status_command(*, limit: int = 20, json_output: bool = False, write_report: bool = False) -> int:
    """Report the local model budget ledger from SQLite cost_events."""

    root = project_root()
    result = BudgetLedger(root).status(limit=limit)
    result = _write_optional_command_report(
        root,
        result,
        subject="model:budget",
        report_id="model_budget_status",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-48", "component": "BudgetLedger"},
    )
    _emit_result_event(root, result, subject="model:budget")
    _persist_result(root, result, subject="model:budget")
    print_result(result, json_output=json_output)
    return int(result.exit_code)

def trace_report_command(
    *,
    limit: int = 20,
    include_events: bool = True,
    include_metrics: bool = True,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Generate a bounded local trace report without requiring UI or network."""

    root = project_root()
    result = ApplicationService(root).trace_report(limit=limit, include_events=include_events, include_metrics=include_metrics)
    result = _write_optional_command_report(
        root,
        result,
        subject="observability:traces",
        report_id="trace_report",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-61", "component": "TraceQueryService"},
    )
    _emit_result_event(root, result, subject="observability:traces")
    _persist_result(root, result, subject="observability:traces")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def trace_inspect_command(
    trace_id: str,
    *,
    limit: int = 100,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Inspect one local trace id and return a tree of spans."""

    root = project_root()
    result = TraceQueryService(root).inspect(trace_id, limit=limit)
    result = _write_optional_command_report(
        root,
        result,
        subject=f"trace:{trace_id}",
        report_id=f"trace_inspect_{trace_id}",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-61", "component": "TraceQueryService"},
    )
    _emit_result_event(root, result, subject=f"trace:{trace_id}")
    _persist_result(root, result, subject=f"trace:{trace_id}")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def metrics_summary_command(
    *,
    category: str | None = None,
    limit: int = 50,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Summarize local AgentOps metrics without requiring UI or network."""

    root = project_root()
    result = ApplicationService(root).metrics_summary(category=category, limit=limit)
    result = _write_optional_command_report(
        root,
        result,
        subject="observability:metrics",
        report_id="metrics_summary",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-61", "component": "TraceQueryService"},
    )
    _emit_result_event(root, result, subject="observability:metrics")
    _persist_result(root, result, subject="observability:metrics")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def telemetry_export_command(
    *,
    format: str = "otlp",
    dry_run: bool = True,
    trace_id: str | None = None,
    limit: int = 20,
    include_metrics: bool = True,
    endpoint: str | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Generate an OpenTelemetry-compatible local dry-run payload.

    FUNC-SPRINT-62 intentionally does not send telemetry to a collector. Any
    remote endpoint or non-dry-run intent is evaluated and blocked by policy.
    """

    root = project_root()
    result = OTelDryRunExporter(root).export(
        OTelExportOptions(
            format=format,
            dry_run=dry_run,
            trace_id=trace_id,
            limit=limit,
            include_metrics=include_metrics,
            endpoint=endpoint,
        )
    )
    result = _write_optional_command_report(
        root,
        result,
        subject="observability:otel-dry-run",
        report_id="telemetry_export_otel_dry_run",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-62", "component": "OTelDryRunExporter"},
    )
    _emit_result_event(root, result, subject="observability:otel-dry-run")
    _persist_result(root, result, subject="observability:otel-dry-run")
    print_result(result, json_output=json_output)
    return int(result.exit_code)

def agentops_status_command(
    *,
    limit: int = 100,
    strict_runtime_signals: bool = False,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run the local AgentOps Quality Gate and Phase E closure status.

    FUNC-SPRINT-63 consolidates local trace/span/event/metric evidence and
    MIASI observability declarations. The command is read-only with respect to
    project source files; optional report writing is the only controlled side
    effect. It never requires UI, network, remote telemetry or external APIs.
    """

    root = project_root()
    result = AgentOpsQualityGate(root).status(
        AgentOpsGateOptions(limit=limit, strict_runtime_signals=strict_runtime_signals)
    )
    result = _write_optional_command_report(
        root,
        result,
        subject="observability:agentops-quality-gate",
        report_id="agentops_status",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-63", "component": "AgentOpsQualityGate"},
    )
    _emit_result_event(root, result, subject="observability:agentops-quality-gate")
    _persist_result(root, result, subject="observability:agentops-quality-gate")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def model_providers_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Report safe ModelAdapter provider configuration.

    FUNC-SPRINT-17 reads provider metadata only. It never reads raw API keys,
    never contacts local model servers and never calls external APIs.
    """

    root = project_root()
    result = ApplicationService(root).model_providers()
    result = _write_optional_command_report(
        root,
        result,
        subject=".devpilot/providers.yaml.example",
        report_id="model_providers",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-17", "component": "ProviderRegistry"},
    )
    _emit_result_event(root, result, subject=".devpilot/providers.yaml.example")
    _persist_result(root, result, subject=".devpilot/providers.yaml.example")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def model_generate_command(
    *,
    prompt: str | None = None,
    prompt_id: str | None = None,
    prompt_version: str | None = None,
    prompt_inputs: list[str] | None = None,
    provider: str = "mock",
    model: str | None = None,
    allow_external_api: bool = False,
    budget_limit_usd: float = 0.0,
    budget_used_usd: float = 0.0,
    timeout_seconds: float = 3.0,
    fallback_to_mock: bool = False,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Generate text through the safe ModelAdapter boundary."""

    root = project_root()
    prompt_reference: dict[str, object] | None = None
    effective_prompt = prompt
    if prompt_id:
        try:
            rendered, render_error = PromptRegistry(root).render(
                prompt_id,
                version=prompt_version,
                inputs=_parse_prompt_inputs(prompt_inputs),
            )
        except ValueError as exc:
            render_error = CommandResult(
                command="prompt render",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Prompt render blocked by invalid CLI input format.",
                data={"summary": {"prompt_id": prompt_id, "payload_redacted": True, "external_api_used": False, "preliminary": True}},
                findings=[Finding(id="PROMPT_INPUT_FORMAT_INVALID", message=str(exc), severity=Severity.BLOCK, metadata={"prompt_id": prompt_id, "payload_redacted": True})],
            )
            rendered = None
        if render_error is not None:
            result = render_error
            result = _write_optional_command_report(
                root,
                result,
                subject=f"prompt:{prompt_id}",
                report_id="model_generate_prompt_render",
                write_report=write_report,
                metadata={"sprint": "FUNC-SPRINT-49", "component": "PromptRegistry"},
            )
            _emit_result_event(root, result, subject=f"prompt:{prompt_id}")
            _persist_result(root, result, subject=f"prompt:{prompt_id}")
            print_result(result, json_output=json_output)
            return int(result.exit_code)
        assert rendered is not None
        effective_prompt = rendered.text
        prompt_reference = rendered.reference_payload()
    if not effective_prompt:
        result = CommandResult(
            command="model generate",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Model generate requires either --prompt or --prompt-id with valid inputs.",
            data={"summary": {"provider": provider, "prompt_id": prompt_id, "payload_redacted": True, "external_api_used": False, "preliminary": True}},
            findings=[Finding(id="MODEL_GENERATE_PROMPT_REQUIRED", message="No prompt payload or prompt_id was provided.", severity=Severity.BLOCK, metadata={"prompt_id": prompt_id})],
        )
        print_result(result, json_output=json_output)
        return int(result.exit_code)
    result = _model_router(
        root,
        allow_external_api=allow_external_api,
        budget_limit_usd=budget_limit_usd,
        budget_used_usd=budget_used_usd,
        local_timeout_seconds=timeout_seconds,
        fallback_to_mock_on_local_unavailable=fallback_to_mock,
    ).generate(prompt=effective_prompt, provider=provider, model=model)
    result = _attach_prompt_reference(result, prompt_reference)
    BudgetLedger(root).record_model_result(result, source="model-generate-cli")
    result = _write_optional_command_report(
        root,
        result,
        subject=f"provider:{provider}",
        report_id="model_generate",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-17", "component": "ModelAdapterRouter"},
    )
    _emit_result_event(root, result, subject=f"provider:{provider}")
    _persist_result(root, result, subject=f"provider:{provider}")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def model_classify_command(
    *,
    text: str,
    labels: str,
    provider: str = "mock",
    model: str | None = None,
    timeout_seconds: float = 3.0,
    fallback_to_mock: bool = False,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Classify text through the safe ModelAdapter boundary."""

    root = project_root()
    label_tuple = tuple(label.strip() for label in labels.split(",") if label.strip())
    result = _model_router(root, local_timeout_seconds=timeout_seconds, fallback_to_mock_on_local_unavailable=fallback_to_mock).classify(text=text, labels=label_tuple, provider=provider, model=model)
    BudgetLedger(root).record_model_result(result, source="model-classify-cli")
    result = _write_optional_command_report(
        root,
        result,
        subject=f"provider:{provider}",
        report_id="model_classify",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-17", "component": "ModelAdapterRouter"},
    )
    _emit_result_event(root, result, subject=f"provider:{provider}")
    _persist_result(root, result, subject=f"provider:{provider}")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def model_embed_command(
    *,
    text: str,
    provider: str = "mock",
    model: str | None = None,
    timeout_seconds: float = 3.0,
    fallback_to_mock: bool = False,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Generate a deterministic embedding through the safe ModelAdapter boundary."""

    root = project_root()
    result = _model_router(root, local_timeout_seconds=timeout_seconds, fallback_to_mock_on_local_unavailable=fallback_to_mock).embed(text=text, provider=provider, model=model)
    BudgetLedger(root).record_model_result(result, source="model-embed-cli")
    result = _write_optional_command_report(
        root,
        result,
        subject=f"provider:{provider}",
        report_id="model_embed",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-17", "component": "ModelAdapterRouter"},
    )
    _emit_result_event(root, result, subject=f"provider:{provider}")
    _persist_result(root, result, subject=f"provider:{provider}")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def _parse_prompt_inputs(items: list[str] | None) -> dict[str, str]:
    """Parse key=value CLI prompt inputs without logging values elsewhere."""

    inputs: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"Prompt input must use key=value format: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("Prompt input key cannot be empty.")
        inputs[key] = value
    return inputs


def _attach_prompt_reference(result: CommandResult, prompt_reference: dict[str, object] | None) -> CommandResult:
    """Return result enriched with prompt id/version metadata only."""

    if not prompt_reference:
        return result
    data = dict(result.data or {})
    data["prompt_reference"] = dict(prompt_reference)
    summary = dict(data.get("summary") or {})
    summary["prompt_id"] = prompt_reference.get("prompt_id")
    summary["prompt_version"] = prompt_reference.get("version")
    summary["prompt_payload_redacted"] = True
    data["summary"] = summary
    return CommandResult(
        command=result.command,
        ok=result.ok,
        exit_code=result.exit_code,
        message=result.message,
        data=data,
        findings=result.findings,
    )


def prompt_list_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """List versioned prompt contracts in read-only mode."""

    root = project_root()
    result = PromptRegistry(root).list()
    result = _write_optional_command_report(
        root,
        result,
        subject="docs/prompts",
        report_id="prompt_list",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-49", "component": "PromptRegistry"},
    )
    _emit_result_event(root, result, subject="docs/prompts")
    _persist_result(root, result, subject="docs/prompts")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def prompt_validate_command(*, prompt_id: str | None = None, json_output: bool = False, write_report: bool = False) -> int:
    """Validate prompt schema, semantics and basic safety findings."""

    root = project_root()
    result = PromptRegistry(root).validate(prompt_id=prompt_id)
    result = _write_optional_command_report(
        root,
        result,
        subject=prompt_id or "docs/prompts",
        report_id="prompt_validate",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-49", "component": "PromptRegistry"},
    )
    _emit_result_event(root, result, subject=prompt_id or "docs/prompts")
    _persist_result(root, result, subject=prompt_id or "docs/prompts")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def prompt_show_command(*, prompt_id: str, version: str | None = None, json_output: bool = False, write_report: bool = False) -> int:
    """Show one prompt contract with redacted template content."""

    root = project_root()
    result = PromptRegistry(root).show(prompt_id, version=version)
    result = _write_optional_command_report(
        root,
        result,
        subject=f"prompt:{prompt_id}",
        report_id="prompt_show",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-49", "component": "PromptRegistry"},
    )
    _emit_result_event(root, result, subject=f"prompt:{prompt_id}")
    _persist_result(root, result, subject=f"prompt:{prompt_id}")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def model_eval_run_command(
    *,
    suite: str = "model-local-smoke",
    provider: str = "mock",
    model: str | None = None,
    case_id: str | None = None,
    timeout_seconds: float = 3.0,
    fallback_to_mock: bool = False,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run governed local model evaluation matrix suites.

    FUNC-SPRINT-50 evaluates mock/local providers through ModelEvalRunner.
    The default suite is hermetic and passes with mock without Ollama,
    LM Studio or external APIs. Reports are redacted and do not store raw
    prompts or completions.
    """

    root = project_root()
    result = ModelEvalRunner(
        root,
        config=ModelEvalRunnerConfig(
            timeout_seconds=timeout_seconds,
            fallback_to_mock=fallback_to_mock,
        ),
    ).run(suite=suite, provider=provider, model=model, case_id=case_id, write_report=write_report)
    _emit_result_event(root, result, subject=f"model-eval:{suite}:{provider}")
    _persist_result(root, result, subject=f"model-eval:{suite}:{provider}")
    print_result(result, json_output=json_output)
    return int(result.exit_code)

def git_status_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Collect read-only Git status information.

    FUNC-SPRINT-14 only executes an allowlist of read-only Git commands. It
    never performs add, commit, checkout, reset, merge, tag, push or any other
    mutation of repository state.
    """

    root = project_root()
    result = GitAdapter(root).status()
    result = _write_optional_command_report(
        root,
        result,
        subject=".",
        report_id="git_status",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-14", "component": "GitAdapter"},
    )
    _emit_result_event(root, result, subject=".")
    _persist_result(root, result, subject=".")
    print_result(result, json_output=json_output)
    return int(result.exit_code)



def git_v2_command(
    action: str,
    *,
    limit: int = 20,
    max_files: int = 200,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run GitAdapter v2 read-only commands for Fase C.

    FUNC-SPRINT-35 adds branches, tags, bounded log and structured
    diff-report commands. The implementation remains strictly read-only: no
    add/commit/checkout/reset/tag creation/push and no shell execution.
    """

    root = project_root()
    adapter = GitAdapter(root)
    if action == "branches":
        result = adapter.branches()
    elif action == "tags":
        result = adapter.tags()
    elif action == "log":
        result = adapter.log(limit=limit)
    elif action == "diff-report":
        result = GitDiffReportBuilder(root).build(max_files=max_files)
    else:
        result = CommandResult(
            command=f"git {action}",
            ok=False,
            exit_code=ExitCode.FAIL,
            message="Unsupported GitAdapter v2 action.",
            findings=[Finding(id="GIT_V2_ACTION_UNSUPPORTED", message=f"Unsupported git action: {action}.", severity=Severity.FAIL)],
        )
    result = _write_optional_command_report(
        root,
        result,
        subject=".",
        report_id=f"git_{action.replace('-', '_')}",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-35", "component": "GitAdapterV2", "action": action},
    )
    _emit_result_event(root, result, subject=".")
    _persist_result(root, result, subject=".")
    print_result(result, json_output=json_output)
    return int(result.exit_code)

def repo_inventory_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Build a read-only repository inventory and risk summary.

    FUNC-SPRINT-14 inventory scans metadata and small text files for synthetic
    secret-like patterns. It never emits raw file contents and excludes runtime
    output/cache folders by default.
    """

    root = project_root()
    result = ApplicationService(root).repo_inventory()
    result = _write_optional_command_report(
        root,
        result,
        subject=".",
        report_id="repo_inventory",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-14", "component": "RepoInventory"},
    )
    _emit_result_event(root, result, subject=".")
    _persist_result(root, result, subject=".")
    print_result(result, json_output=json_output)
    return int(result.exit_code)






def repo_dependency_graph_command(
    *,
    target: str = "src/devpilot_core",
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Build a Python import dependency graph in read-only mode.

    FUNC-SPRINT-36 parses Python files with AST. It never imports or executes
    analyzed modules, never calls network/API providers and never mutates the
    repository. Dynamic imports remain a documented limitation.
    """

    root = project_root()
    result = DependencyGraphBuilder(root).build(target=target)
    result = _write_optional_command_report(
        root,
        result,
        subject=target,
        report_id="repo_dependency_graph",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-36", "component": "DependencyGraphBuilder"},
    )
    _emit_result_event(root, result, subject=target)
    _persist_result(root, result, subject=target)
    print_result(result, json_output=json_output)
    return int(result.exit_code)



def repo_analyze_command(
    *,
    target: str = ".",
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run RepoAnalyzer v2 in local read-only mode.

    FUNC-SPRINT-37 consolidates repo-inventory, DependencyGraph and
    GitAdapter signals into a heuristic repository health summary. It excludes
    runtime folders, never emits raw secret values and does not modify files.
    """

    root = project_root()
    result = ApplicationService(root).repo_analyze(target=target)
    result = _write_optional_command_report(
        root,
        result,
        subject=target,
        report_id="repo_analyze",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-37", "component": "RepoAnalyzer"},
    )
    _emit_result_event(root, result, subject=target)
    _persist_result(root, result, subject=target)
    print_result(result, json_output=json_output)
    return int(result.exit_code)



def repo_architecture_drift_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Detect architecture/code drift from docs and source structure.

    FUNC-SPRINT-38 keeps this analysis read-only and heuristic. It compares
    architecture Markdown components against top-level Python modules, includes
    confidence per row, and never mutates documentation or source files.
    """

    root = project_root()
    result = ArchitectureDriftDetector(root).detect()
    result = _write_optional_command_report(
        root,
        result,
        subject="repo:architecture-drift",
        report_id="repo_architecture_drift",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-38", "component": "ArchitectureDriftDetector"},
    )
    _emit_result_event(root, result, subject="repo:architecture-drift")
    _persist_result(root, result, subject="repo:architecture-drift")
    print_result(result, json_output=json_output)
    return int(result.exit_code)



def repo_engineering_gate_command(
    *,
    profile: str = "quick",
    target: str = ".",
    code_target: str | None = None,
    patch_file: str | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run the FUNC-SPRINT-44 repository engineering gate.

    The gate consolidates Phase C signals from Git read-only, dependency graph,
    RepoAnalyzer, ArchitectureDrift, RepoQualityGate and MIASI declaration
    checks. It is read-only and does not apply patches, execute productive
    refactors, use Git write, deploy, use LLMs or call network APIs.
    """

    root = project_root()
    result = RepoEngineeringGate(
        root,
        config=RepoEngineeringGateConfig(
            profile=profile,
            target=target,
            code_target=code_target,
            patch_file=patch_file,
        ),
    ).run()
    result = _write_optional_command_report(
        root,
        result,
        subject=target,
        report_id="repo_engineering_gate",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-44", "component": "RepoEngineeringGate", "profile": profile},
    )
    _emit_result_event(root, result, subject="repo:engineering-gate")
    _persist_result(root, result, subject="repo:engineering-gate")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def repo_quality_gate_command(
    *,
    target: str = ".",
    code_target: str | None = None,
    patch_file: str | None = None,
    patch_text: str | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run the Sprint 39 repository quality gate in dry-run mode.

    The gate integrates RepoAnalyzer, CodeReviewEngine, optional
    PatchReviewEngine and PolicyEngine through versioned ReviewRulePacks. It
    emits PASS/FAIL/BLOCK evidence without mutating files, applying patches,
    calling Git write commands, using LLMs, using APIs or opening network
    connections.
    """

    root = project_root()
    result = RepoQualityGate(
        root,
        config=RepoQualityGateConfig(
            target=target,
            code_target=code_target,
            patch_file=patch_file,
            patch_text=patch_text,
        ),
    ).run()
    result = _write_optional_command_report(
        root,
        result,
        subject=target,
        report_id="repo_quality_gate",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-39", "component": "RepoQualityGate"},
    )
    _emit_result_event(root, result, subject="repo:quality-gate")
    _persist_result(root, result, subject="repo:quality-gate")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def patch_check_command(
    *,
    patch_file: str,
    approval_id: str | None = None,
    timeout_seconds: int = 10,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run Sprint 40 patch preflight without applying the patch.

    The command combines PatchReviewEngine risk checks with `git apply
    --check` through SafeSubprocessRunner. It is strictly dry-run: no patch is
    applied, no Git write command is executed and no workspace file is mutated
    except optional evidence reports when --write-report is requested.
    """

    root = project_root()
    result = PatchPreflightEngine(root).check(
        patch_file=patch_file,
        approval_id=approval_id,
        timeout_seconds=timeout_seconds,
    )
    result = _write_optional_command_report(
        root,
        result,
        subject=patch_file,
        report_id="patch_preflight",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-40", "component": "PatchPreflightEngine"},
    )
    _emit_result_event(root, result, subject=patch_file)
    _persist_result(root, result, subject=patch_file)
    print_result(result, json_output=json_output)
    return int(result.exit_code)

def patch_sandbox_command(
    *,
    patch_file: str,
    run_tests: bool = False,
    test_profile: str = "smoke",
    approval_id: str | None = None,
    cleanup: bool = False,
    timeout_seconds: int = 30,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run Sprint 41 patch sandbox and ChangeSet generation.

    The command applies a preflight-approved patch only to a sandbox copy under
    outputs/sandbox, generates a ChangeSet with hashes and never mutates the
    productive workspace. Optional sandbox tests are fixed-profile and approval
    gated.
    """

    root = project_root()
    result = PatchSandboxManager(root).apply(
        patch_file=patch_file,
        run_tests=run_tests,
        test_profile=test_profile,
        approval_id=approval_id,
        cleanup=cleanup,
        timeout_seconds=timeout_seconds,
    )
    result = _write_optional_command_report(
        root,
        result,
        subject=patch_file,
        report_id="patch_sandbox",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-41", "component": "PatchSandboxManager"},
    )
    _emit_result_event(root, result, subject=patch_file)
    _persist_result(root, result, subject=patch_file)
    print_result(result, json_output=json_output)
    return int(result.exit_code)



def rollback_command(
    action: str,
    *,
    rollback_id: str | None = None,
    changeset_file: str | None = None,
    approval_id: str | None = None,
    limit: int = 100,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run FUNC-SPRINT-42 rollback plan/list/show/execute commands.

    The initial RollbackManager creates auditable rollback plans and runtime
    backup points from sandbox ChangeSets. list/show are read-only. execute is
    approval-gated and intentionally non-mutating in Sprint 42.
    """

    root = project_root()
    manager = RollbackManager(root)
    if action == "plan":
        if not changeset_file:
            result = CommandResult(
                command="rollback plan",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="rollback plan requires --changeset-file.",
                data={"summary": {"created": False, "preliminary": True}},
                findings=[Finding("ROLLBACK_CHANGESET_FILE_REQUIRED", "Provide --changeset-file for rollback plan.", Severity.BLOCK)],
            )
        else:
            result = manager.create_plan_from_file(changeset_file)
        report_id = "rollback_plan"
        subject = changeset_file or "rollback:plan"
    elif action == "list":
        result = manager.list(limit=limit)
        report_id = "rollback_list"
        subject = "rollback:list"
    elif action == "show":
        result = manager.show(rollback_id or "")
        report_id = "rollback_show"
        subject = rollback_id or "rollback:show"
    elif action == "execute":
        result = manager.execute(rollback_id or "", approval_id=approval_id)
        report_id = "rollback_execute"
        subject = rollback_id or "rollback:execute"
    else:
        result = CommandResult(
            command=f"rollback {action}",
            ok=False,
            exit_code=ExitCode.FAIL,
            message="Unsupported rollback action.",
            findings=[Finding("ROLLBACK_ACTION_UNSUPPORTED", f"Unsupported rollback action: {action}.", Severity.FAIL)],
        )
        report_id = "rollback"
        subject = "rollback:unsupported"
    result = _write_optional_command_report(
        root,
        result,
        subject=subject,
        report_id=report_id,
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-42", "component": "RollbackManager", "action": action},
    )
    _emit_result_event(root, result, subject=subject)
    _persist_result(root, result, subject=subject)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def patch_review_command(
    *,
    patch_file: str | None = None,
    patch_text: str | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Review a unified diff/patch without applying it.

    FUNC-SPRINT-15 is strictly dry-run: DevPilot parses the patch, evaluates
    referenced paths through PolicyEngine, scans additions for secrets/risky
    code patterns and never invokes git apply or writes into the repository.
    """

    root = project_root()
    result = PatchReviewEngine(root).review(patch_file=patch_file, patch_text=patch_text)
    result = _write_optional_command_report(
        root,
        result,
        subject=patch_file or "inline-patch",
        report_id="patch_review",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-15", "component": "PatchReviewEngine"},
    )
    _emit_result_event(root, result, subject=patch_file or "inline-patch")
    _persist_result(root, result, subject=patch_file or "inline-patch")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def code_review_command(
    *,
    target: str = ".",
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run deterministic static code review without modifying files.

    FUNC-SPRINT-15 keeps this review local-only: no external linters, no LLMs,
    no network, no file changes and no raw source emission in command output.
    """

    root = project_root()
    result = ApplicationService(root).code_review(target=target)
    result = _write_optional_command_report(
        root,
        result,
        subject=target,
        report_id="code_review",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-15", "component": "CodeReviewEngine"},
    )
    _emit_result_event(root, result, subject=target)
    _persist_result(root, result, subject=target)
    print_result(result, json_output=json_output)
    return int(result.exit_code)



def refactor_plan_command(
    *,
    target: str = ".",
    goal: str = "",
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Generate a safe refactor plan without modifying code.

    FUNC-SPRINT-16 is plan-only: it analyzes allowed targets, proposes
    reversible steps, declares tests and rollback guidance, and never writes
    patches or edits source files.
    """

    root = project_root()
    result = ApplicationService(root).refactor_plan(target=target, goal=goal, include_code_review=True)
    result = _write_optional_command_report(
        root,
        result,
        subject=target,
        report_id="refactor_plan",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-16", "component": "RefactorPlanner"},
    )
    _emit_result_event(root, result, subject=target)
    _persist_result(root, result, subject=target)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def refactor_sandbox_command(
    *,
    target: str,
    plan_id: str,
    approval_id: str | None,
    run_tests: bool = False,
    test_profile: str = "smoke",
    tests_approval_id: str | None = None,
    cleanup: bool = False,
    timeout_seconds: int = 30,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run FUNC-SPRINT-43 controlled refactor execution in sandbox.

    RefactorExecutor requires scoped approval for sandbox side effects, applies
    only deterministic mechanical transformations under outputs/sandbox, emits
    a ChangeSet and creates a rollback plan. Optional tests require a separate
    tests.run approval.
    """

    root = project_root()
    result = RefactorExecutor(root).sandbox(
        target=target,
        plan_id=plan_id,
        approval_id=approval_id,
        run_tests=run_tests,
        test_profile=test_profile,
        tests_approval_id=tests_approval_id,
        cleanup=cleanup,
        timeout_seconds=timeout_seconds,
    )
    result = _write_optional_command_report(
        root,
        result,
        subject=target,
        report_id="refactor_sandbox",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-43", "component": "RefactorExecutor", "plan_id": plan_id},
    )
    _emit_result_event(root, result, subject=target)
    _persist_result(root, result, subject=target)
    print_result(result, json_output=json_output)
    return int(result.exit_code)

def miasi_validate_command(
    *,
    scope: str = "all",
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Validate executable MIASI Agent/Tool/Policy registries.

    FUNC-SPRINT-11 keeps this command deterministic and non-executing: it
    validates declarations only; it does not run agents, tools, models or
    filesystem actions.
    """

    root = project_root()
    validator = MiasiRegistryValidator(root)
    if scope == "agents":
        result = validator.validate_agents()
        report_id = "miasi_validate_registry"
        subject = ".devpilot/miasi/agent_registry.json"
    elif scope == "tools":
        result = validator.validate_tools()
        report_id = "miasi_validate_tools"
        subject = ".devpilot/miasi/tool_registry.json"
    elif scope == "policy":
        result = validator.validate_policy_matrix()
        report_id = "miasi_validate_policy_matrix"
        subject = ".devpilot/miasi/policy_matrix.json"
    else:
        result = validator.validate_all()
        report_id = "miasi_validate"
        subject = ".devpilot/miasi"
    result = _write_optional_command_report(
        root,
        result,
        subject=subject,
        report_id=report_id,
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-11", "component": "MiasiRegistryValidator"},
    )
    _emit_result_event(root, result, subject=subject)
    _persist_result(root, result, subject=subject)
    print_result(result, json_output=json_output)
    return int(result.exit_code)



def eval_run_command(
    *,
    suite: str = "documentation",
    case_id: str | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run deterministic offline evaluations for validators and agents.

    FUNC-SPRINT-13 keeps evaluation local-first: synthetic fixtures, no LLM
    judges, no external APIs and no network access. Runtime materials are
    generated under outputs/evals and evidence reports are optional.
    """

    root = project_root()
    result = ApplicationService(root).eval_run(suite=suite, case_id=case_id)
    result = _write_optional_command_report(
        root,
        result,
        subject=f"evals/fixtures/{suite}",
        report_id=f"eval_run_{suite}",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-13", "component": "EvalRunner"},
    )
    _emit_result_event(root, result, subject=f"evals/fixtures/{suite}")
    _persist_result(root, result, subject=f"evals/fixtures/{suite}")
    print_result(result, json_output=json_output)
    return int(result.exit_code)

def agent_run_command(
    agent_name: str,
    *,
    target: str | None = None,
    idea: str | None = None,
    dry_run: bool = True,
    execute: bool = False,
    provider: str | None = None,
    model: str | None = None,
    prompt_id: str | None = None,
    prompt_version: str | None = None,
    prompt_inputs: list[str] | None = None,
    patch_file: str | None = None,
    timeout_seconds: float = 3.0,
    fallback_to_mock: bool = False,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run one mono-agent through AgentRuntime v2.

    Existing deterministic agents remain model-free by default. FUNC-SPRINT-51
    adds opt-in model-aware execution via ModelAdapterRouter and PromptRegistry
    when --provider or --prompt-id is supplied.
    """

    root = project_root()
    effective_dry_run = False if execute else dry_run
    try:
        parsed_prompt_inputs = _parse_prompt_inputs(prompt_inputs)
    except ValueError as exc:
        result = CommandResult(
            command="agent run",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="AgentRuntime v2 prompt input parsing failed.",
            data={"summary": {"payload_redacted": True, "external_api_used": False, "preliminary": True}},
            findings=[Finding(id="AGENT_PROMPT_INPUT_FORMAT_INVALID", message=str(exc), severity=Severity.BLOCK, metadata={"payload_redacted": True})],
        )
        print_result(result, json_output=json_output)
        return int(result.exit_code)
    runtime_config = AgentRuntimeConfig(
        model_provider=provider,
        model=model,
        prompt_id=prompt_id,
        prompt_version=prompt_version,
        prompt_inputs=parsed_prompt_inputs,
        fallback_to_mock=fallback_to_mock,
        local_timeout_seconds=timeout_seconds,
    )
    result = AgentRuntime(root, config=runtime_config).run(
        agent_name,
        target=target,
        idea=idea,
        dry_run=effective_dry_run,
        provider=provider,
        model=model,
        prompt_id=prompt_id,
        prompt_version=prompt_version,
        prompt_inputs=parsed_prompt_inputs,
        timeout_seconds=timeout_seconds,
        fallback_to_mock=fallback_to_mock,
        patch_file=patch_file,
    )
    result = _write_optional_command_report(
        root,
        result,
        subject=target or agent_name,
        report_id=f"agent_run_{agent_name.replace('-', '_').replace('.', '_')}",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-51", "component": "AgentRuntime v2 model-aware"},
    )
    _emit_result_event(root, result, subject=target or agent_name)
    _persist_result(root, result, subject=target or agent_name)
    print_result(result, json_output=json_output)
    return int(result.exit_code)



def quality_gate_run_command(
    *,
    profile: str = "fast",
    include_pytest: bool = False,
    pytest_timeout_seconds: int = 180,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run the FUNC-SPRINT-75/76 unified local quality gate."""

    root = project_root()
    result = QualityGate(
        root,
        options=QualityGateOptions(
            profile=profile,
            include_pytest=include_pytest,
            pytest_timeout_seconds=pytest_timeout_seconds,
        ),
    ).run()
    result = _write_optional_command_report(
        root,
        result,
        subject="release:quality-gate",
        report_id="quality_gate",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-76" if profile == "ci" else "FUNC-SPRINT-75", "component": "QualityGate", "profile": profile},
    )
    if write_report and isinstance((result.data or {}).get("reports"), dict):
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["reports_written"] = True
        data["summary"] = summary
        result = CommandResult(
            command=result.command,
            ok=result.ok,
            exit_code=result.exit_code,
            message=result.message,
            data=data,
            findings=result.findings,
        )
    _emit_result_event(root, result, subject="release:quality-gate")
    _persist_result(root, result, subject="release:quality-gate")
    print_result(result, json_output=json_output)
    return int(result.exit_code)



def release_manifest_command(
    *,
    version: str,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Generate the FUNC-SPRINT-77 local release manifest."""

    root = project_root()
    result = ReleaseManifestBuilder(root, options=ReleaseManifestOptions(version=version)).build()
    result = _write_optional_command_report(
        root,
        result,
        subject=f"release:{version}",
        report_id="release_manifest",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-77", "component": "ReleaseManifest", "version": version},
    )
    if write_report and isinstance((result.data or {}).get("reports"), dict):
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["reports_written"] = True
        data["summary"] = summary
        result = CommandResult(
            command=result.command,
            ok=result.ok,
            exit_code=result.exit_code,
            message=result.message,
            data=data,
            findings=result.findings,
        )
    _emit_result_event(root, result, subject="release:manifest")
    _persist_result(root, result, subject="release:manifest")
    print_result(result, json_output=json_output)
    return int(result.exit_code)



def release_changelog_command(
    *,
    version: str,
    from_sprint: str = "FUNC-SPRINT-74",
    to_sprint: str | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Generate the FUNC-SPRINT-78 local release changelog."""

    root = project_root()
    result = ReleaseChangelogBuilder(
        root,
        options=ReleaseChangelogOptions(version=version, from_sprint=from_sprint, to_sprint=to_sprint),
    ).build()
    result = _write_optional_command_report(
        root,
        result,
        subject=f"release:{version}:changelog",
        report_id="release_changelog",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-78", "component": "ReleaseChangelog", "version": version},
    )
    if write_report and isinstance((result.data or {}).get("reports"), dict):
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["reports_written"] = True
        data["summary"] = summary
        result = CommandResult(
            command=result.command,
            ok=result.ok,
            exit_code=result.exit_code,
            message=result.message,
            data=data,
            findings=result.findings,
        )
    _emit_result_event(root, result, subject="release:changelog")
    _persist_result(root, result, subject="release:changelog")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def release_sbom_command(
    *,
    version: str | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Generate the FUNC-SPRINT-80 local SBOM and supply-chain baseline."""

    root = project_root()
    result = ReleaseSbomBuilder(root, options=ReleaseSbomOptions(version=version)).build()
    effective_version = ((result.data or {}).get("summary") or {}).get("version") or version or "unknown"
    result = _write_optional_command_report(
        root,
        result,
        subject=f"release:{effective_version}:sbom",
        report_id="release_sbom",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-80", "component": "ReleaseSbom", "version": effective_version},
    )
    if write_report and isinstance((result.data or {}).get("reports"), dict):
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["reports_written"] = True
        data["summary"] = summary
        result = CommandResult(
            command=result.command,
            ok=result.ok,
            exit_code=result.exit_code,
            message=result.message,
            data=data,
            findings=result.findings,
        )
    _emit_result_event(root, result, subject="release:sbom")
    _persist_result(root, result, subject="release:sbom")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def _attach_reports_written(result: CommandResult, *, write_report: bool) -> CommandResult:
    if not write_report and not isinstance((result.data or {}).get("reports"), dict):
        return result
    data = dict(result.data or {})
    summary = dict(data.get("summary") or {})
    summary["reports_written"] = True
    data["summary"] = summary
    return CommandResult(command=result.command, ok=result.ok, exit_code=result.exit_code, message=result.message, data=data, findings=result.findings)


def _write_checksum_text_report(root: Path, result: CommandResult, *, write_report: bool) -> CommandResult:
    if not write_report:
        return result
    line = checksum_line(result)
    if not line:
        return result
    report_path = root / "outputs" / "reports" / "checksums.sha256"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(line, encoding="utf-8")
    data = dict(result.data or {})
    reports = dict(data.get("reports") or {})
    reports["sha256"] = "outputs/reports/checksums.sha256"
    data["reports"] = reports
    summary = dict(data.get("summary") or {})
    summary["checksum_report_written"] = True
    data["summary"] = summary
    return CommandResult(command=result.command, ok=result.ok, exit_code=result.exit_code, message=result.message, data=data, findings=result.findings)


def release_checksum_command(
    *,
    artifact: str,
    version: str | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Generate FUNC-SPRINT-81 SHA256 evidence for one local release artifact."""

    root = project_root()
    result = ReleaseChecksumBuilder(root, options=ReleaseChecksumOptions(artifact=artifact, version=version)).build()
    effective_version = ((result.data or {}).get("summary") or {}).get("version") or version or "unknown"
    result = _write_optional_command_report(
        root,
        result,
        subject=f"release:{effective_version}:checksum",
        report_id="release_checksum",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-81", "component": "ReleaseChecksum", "version": effective_version},
    )
    result = _write_checksum_text_report(root, result, write_report=write_report)
    result = _attach_reports_written(result, write_report=write_report)
    _emit_result_event(root, result, subject="release:checksum")
    _persist_result(root, result, subject="release:checksum")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def release_smoke_test_command(
    *,
    artifact: str,
    version: str | None = None,
    timeout_seconds: int = 30,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run FUNC-SPRINT-81 local smoke checks for one release artifact."""

    root = project_root()
    result = ReleaseSmokeTestBuilder(root, options=ReleaseSmokeTestOptions(artifact=artifact, version=version, timeout_seconds=timeout_seconds)).build()
    effective_version = ((result.data or {}).get("summary") or {}).get("version") or version or "unknown"
    result = _write_optional_command_report(
        root,
        result,
        subject=f"release:{effective_version}:smoke-test",
        report_id="release_smoke_test",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-81", "component": "ReleaseSmokeTest", "version": effective_version},
    )
    result = _attach_reports_written(result, write_report=write_report)
    _emit_result_event(root, result, subject="release:smoke-test")
    _persist_result(root, result, subject="release:smoke-test")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def release_verify_command(
    *,
    artifact: str,
    version: str | None = None,
    timeout_seconds: int = 30,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Consolidate FUNC-SPRINT-81 checksum and smoke-test release evidence."""

    root = project_root()
    result = ReleaseVerifyBuilder(root, options=ReleaseVerifyOptions(artifact=artifact, version=version, timeout_seconds=timeout_seconds)).build()
    effective_version = ((result.data or {}).get("summary") or {}).get("version") or version or "unknown"
    result = _write_optional_command_report(
        root,
        result,
        subject=f"release:{effective_version}:verify",
        report_id="release_verification",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-81", "component": "ReleaseVerification", "version": effective_version},
    )
    result = _write_checksum_text_report(root, result, write_report=write_report)
    result = _attach_reports_written(result, write_report=write_report)
    _emit_result_event(root, result, subject="release:verify")
    _persist_result(root, result, subject="release:verify")
    print_result(result, json_output=json_output)
    return int(result.exit_code)



def install_plan_command(
    *,
    mode: str = "all",
    version: str | None = None,
    artifact: str | None = None,
    python_executable: str = "python",
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Generate the FUNC-SPRINT-82 local installation strategy and dry-run plan."""

    root = project_root()
    result = InstallPlanBuilder(
        root,
        options=InstallPlanOptions(
            mode=mode,
            version=version,
            artifact=artifact,
            python_executable=python_executable,
        ),
    ).build()
    effective_version = ((result.data or {}).get("summary") or {}).get("version") or version or "unknown"
    result = _write_optional_command_report(
        root,
        result,
        subject=f"install:{mode}:{effective_version}",
        report_id="install_plan",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-82", "component": "InstallPlan", "version": effective_version, "mode": mode},
    )
    if write_report and isinstance((result.data or {}).get("reports"), dict):
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["reports_written"] = True
        data["summary"] = summary
        result = CommandResult(
            command=result.command,
            ok=result.ok,
            exit_code=result.exit_code,
            message=result.message,
            data=data,
            findings=result.findings,
        )
    _emit_result_event(root, result, subject="install:plan")
    _persist_result(root, result, subject="install:plan")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def backup_create_command(
    *,
    dry_run: bool = True,
    execute: bool = False,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Create a FUNC-SPRINT-83 local backup plan or artifact."""

    root = project_root()
    result = BackupCreateBuilder(root, options=BackupCreateOptions(dry_run=dry_run, execute=execute)).build()
    backup_id = ((result.data or {}).get("summary") or {}).get("backup_id") or "unknown"
    result = _write_optional_command_report(
        root,
        result,
        subject=f"backup:create:{backup_id}",
        report_id="backup_create",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-83", "component": "BackupCreate", "backup_id": str(backup_id)},
    )
    if write_report and isinstance((result.data or {}).get("reports"), dict):
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["reports_written"] = True
        data["summary"] = summary
        result = CommandResult(result.command, result.ok, result.exit_code, result.message, data, result.findings)
    _emit_result_event(root, result, subject="backup:create")
    _persist_result(root, result, subject="backup:create")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def backup_list_command(*, limit: int = 50, json_output: bool = False, write_report: bool = False) -> int:
    """List local FUNC-SPRINT-83 backups."""

    root = project_root()
    result = BackupListBuilder(root, options=BackupListOptions(limit=limit)).build()
    result = _write_optional_command_report(
        root,
        result,
        subject="backup:list",
        report_id="backup_list",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-83", "component": "BackupList"},
    )
    if write_report and isinstance((result.data or {}).get("reports"), dict):
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["reports_written"] = True
        data["summary"] = summary
        result = CommandResult(result.command, result.ok, result.exit_code, result.message, data, result.findings)
    _emit_result_event(root, result, subject="backup:list")
    _persist_result(root, result, subject="backup:list")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def backup_restore_command(
    *,
    backup_id: str,
    dry_run: bool = True,
    execute: bool = False,
    confirm_restore: bool = False,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Plan or execute a controlled FUNC-SPRINT-83 local restore."""

    root = project_root()
    result = BackupRestoreBuilder(
        root,
        options=BackupRestoreOptions(
            backup_id=backup_id,
            dry_run=dry_run,
            execute=execute,
            confirm_restore=confirm_restore,
        ),
    ).build()
    result = _write_optional_command_report(
        root,
        result,
        subject=f"backup:restore:{backup_id}",
        report_id="backup_restore",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-83", "component": "BackupRestore", "backup_id": backup_id},
    )
    if write_report and isinstance((result.data or {}).get("reports"), dict):
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["reports_written"] = True
        data["summary"] = summary
        result = CommandResult(result.command, result.ok, result.exit_code, result.message, data, result.findings)
    _emit_result_event(root, result, subject="backup:restore")
    _persist_result(root, result, subject="backup:restore")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def upgrade_check_command(*, target_version: str | None = None, json_output: bool = False, write_report: bool = False) -> int:
    """Generate a FUNC-SPRINT-83 local upgrade readiness plan."""

    root = project_root()
    result = UpgradeCheckBuilder(root, options=UpgradeCheckOptions(target_version=target_version)).build()
    effective_target = ((result.data or {}).get("summary") or {}).get("target_version") or target_version or "unknown"
    result = _write_optional_command_report(
        root,
        result,
        subject=f"upgrade:check:{effective_target}",
        report_id="upgrade_check",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-83", "component": "UpgradeCheck", "target_version": str(effective_target)},
    )
    if write_report and isinstance((result.data or {}).get("reports"), dict):
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["reports_written"] = True
        data["summary"] = summary
        result = CommandResult(result.command, result.ok, result.exit_code, result.message, data, result.findings)
    _emit_result_event(root, result, subject="upgrade:check")
    _persist_result(root, result, subject="upgrade:check")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def package_build_command(
    *,
    kind: str,
    version: str,
    execute: bool = False,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Build or plan FUNC-SPRINT-79 local release packages.

    The command is dry-run by default. ``--execute`` writes local artifacts
    under dist/ only; it never publishes to PyPI, deploys, signs artifacts or
    tags Git. Optional reports are written under outputs/reports.
    """

    root = project_root()
    result = PackageBuildBuilder(
        root,
        options=PackageBuildOptions(version=version, kind=kind, execute=execute),
    ).build()
    result = _write_optional_command_report(
        root,
        result,
        subject=f"package:{kind}:{version}",
        report_id="package_build",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-79", "component": "PackageBuild", "version": version, "kind": kind},
    )
    if write_report and isinstance((result.data or {}).get("reports"), dict):
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["reports_written"] = True
        data["summary"] = summary
        result = CommandResult(
            command=result.command,
            ok=result.ok,
            exit_code=result.exit_code,
            message=result.message,
            data=data,
            findings=result.findings,
        )
    _emit_result_event(root, result, subject="package:build")
    _persist_result(root, result, subject="package:build")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def validate_frontmatter_command(
    path: str,
    *,
    json_output: bool = False,
    strict: bool = False,
    write_report: bool = False,
) -> int:
    """Validate frontmatter metadata for one Markdown artifact."""

    root = project_root()
    result = ApplicationService(root).validate_frontmatter(path, strict=strict)
    result = _write_optional_command_report(root, result, subject=path, write_report=write_report)
    _emit_result_event(root, result, subject=path)
    _persist_result(root, result, subject=path)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def validate_artifact_command(
    path: str,
    *,
    json_output: bool = False,
    strict: bool = False,
    write_report: bool = False,
) -> int:
    """Validate one Markdown artifact against its MIPSoftware/MIASI profile."""

    root = project_root()
    result = ApplicationService(root).validate_artifact(path, strict=strict)
    result = _write_optional_command_report(root, result, subject=path, write_report=write_report)
    _emit_result_event(root, result, subject=path)
    _persist_result(root, result, subject=path)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def checklist_pre_code_command(*, json_output: bool = False, strict: bool = True, write_report: bool = False) -> int:
    """Evaluate the executable pre-code checklist gate."""

    root = project_root()
    result = ApplicationService(root).checklist_pre_code(strict=strict)
    result = _write_optional_command_report(root, result, report_id="checklist_pre_code", write_report=write_report)
    _emit_result_event(root, result, subject="docs/checklists/checklist_pre_code.md")
    _persist_result(root, result, subject="docs/checklists/checklist_pre_code.md")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def standards_status_command(*, json_output: bool = False) -> int:
    """Report local MIPSoftware/MIASI registry status."""

    root = project_root()
    result = ApplicationService(root).standards_status()
    _emit_result_event(root, result, subject="docs/standards")
    _persist_result(root, result, subject="docs/standards")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def workspace_init_command(
    *,
    json_output: bool = False,
    execute: bool = False,
    write_report: bool = False,
    project_id: str | None = None,
    project_name: str | None = None,
    project_type: str | None = None,
) -> int:
    """Initialize `.devpilot/project.yaml` in dry-run mode unless executed."""

    root = project_root()
    manager = WorkspaceManager(root)
    result = manager.init_workspace(
        execute=execute,
        project_id=project_id or "devpilot-local",
        project_name=project_name or "DevPilot Local",
        project_type=project_type or "agent-assisted-sdlc",
    )
    result = _write_optional_command_report(
        root,
        result,
        subject=".devpilot/project.yaml",
        report_id="workspace_init",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-08", "component": "WorkspaceManager"},
    )
    _emit_result_event(root, result, subject=".devpilot/project.yaml")
    _persist_result(root, result, subject=".devpilot/project.yaml")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def workspace_status_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Report the current DevPilot workspace status."""

    root = project_root()
    manager = WorkspaceManager(root)
    result = ApplicationService(root).workspace_status()
    result = _write_optional_command_report(
        root,
        result,
        subject=".devpilot/project.yaml",
        report_id="workspace_status",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-08", "component": "WorkspaceManager"},
    )
    _emit_result_event(root, result, subject=".devpilot/project.yaml")
    _persist_result(root, result, subject=".devpilot/project.yaml")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def state_init_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Initialize the local SQLite operational state store."""

    root = project_root()
    result = LocalStore(root).initialize()
    result = _write_optional_command_report(
        root,
        result,
        subject=".devpilot/devpilot.db",
        report_id="state_init",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-10", "component": "LocalStore"},
    )
    _emit_result_event(root, result, subject=".devpilot/devpilot.db")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def state_status_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Report local SQLite operational state status."""

    root = project_root()
    result = LocalStore(root).status()
    result = _write_optional_command_report(
        root,
        result,
        subject=".devpilot/devpilot.db",
        report_id="state_status",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-10", "component": "LocalStore"},
    )
    _emit_result_event(root, result, subject=".devpilot/devpilot.db")
    print_result(result, json_output=json_output)
    return int(result.exit_code)




def approval_request_command(
    *,
    tool_id: str,
    action: str,
    subject: str,
    actor: str,
    reason: str,
    scope: str | None = None,
    expires_at: str | None = None,
    ttl_minutes: int = 60,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Create a local human approval request without authorizing execution."""

    root = project_root()
    result = ApprovalService(root).request(
        ApprovalCliInput(
            tool_id=tool_id,
            action=action,
            subject=subject,
            actor=actor,
            reason=reason,
            scope=scope,
            expires_at=expires_at,
            ttl_minutes=ttl_minutes,
        )
    )
    approval_data = (result.data or {}).get("approval")
    approval_id = approval_data.get("approval_id") if isinstance(approval_data, dict) else None
    result = _write_optional_command_report(
        root,
        result,
        subject=approval_id or subject,
        report_id="approval_request",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-29", "component": "ApprovalService"},
    )
    _emit_result_event(root, result, subject=approval_id or subject)
    _persist_result(root, result, subject=approval_id or subject)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def approval_list_command(
    *,
    status: str | None = None,
    tool_id: str | None = None,
    action: str | None = None,
    limit: int = 100,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """List local approval records with safe optional filters."""

    root = project_root()
    result = ApprovalService(root).list(status=status, tool_id=tool_id, action=action, limit=limit)
    result = _write_optional_command_report(
        root,
        result,
        subject="approval:list",
        report_id="approval_list",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-29", "component": "ApprovalService"},
    )
    _emit_result_event(root, result, subject="approval:list")
    _persist_result(root, result, subject="approval:list")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def approval_show_command(*, approval_id: str, json_output: bool = False, write_report: bool = False) -> int:
    """Show one local approval record by ID."""

    root = project_root()
    result = ApprovalService(root).show(approval_id)
    result = _write_optional_command_report(
        root,
        result,
        subject=approval_id,
        report_id="approval_show",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-29", "component": "ApprovalService"},
    )
    _emit_result_event(root, result, subject=approval_id)
    _persist_result(root, result, subject=approval_id)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def approval_decision_command(
    action: str,
    *,
    approval_id: str,
    actor: str,
    reason: str,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Approve, deny or revoke one approval through controlled transitions."""

    root = project_root()
    service = ApprovalService(root)
    if action == "approve":
        result = service.approve(approval_id, actor=actor, reason=reason)
    elif action == "deny":
        result = service.deny(approval_id, actor=actor, reason=reason)
    elif action == "revoke":
        result = service.revoke(approval_id, actor=actor, reason=reason)
    else:
        result = CommandResult(
            command=f"approval {action}",
            ok=False,
            exit_code=ExitCode.FAIL,
            message="Unsupported approval action.",
            data={"summary": {"supported": ["approve", "deny", "revoke"]}},
            findings=[Finding("APPROVAL_ACTION_UNSUPPORTED", f"Unsupported approval action: {action}.", Severity.FAIL)],
        )
    result = _write_optional_command_report(
        root,
        result,
        subject=approval_id,
        report_id=f"approval_{action}",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-29", "component": "ApprovalService"},
    )
    _emit_result_event(root, result, subject=approval_id)
    _persist_result(root, result, subject=approval_id)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def history_list_command(*, json_output: bool = False, limit: int = 10, write_report: bool = False) -> int:
    """List recent local command runs from SQLite history."""

    root = project_root()
    result = ApplicationService(root).history_list(limit=limit)
    result = _write_optional_command_report(
        root,
        result,
        subject=".devpilot/devpilot.db",
        report_id="history_list",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-10", "component": "LocalStore"},
    )
    _emit_result_event(root, result, subject=".devpilot/devpilot.db")
    print_result(result, json_output=json_output)
    return int(result.exit_code)



def validate_gateway_command(scope: str, *, json_output: bool = False, write_report: bool = False) -> int:
    """Run the FUNC-SPRINT-24 validation gateway for docs/contracts/all.

    The gateway is an orchestration facade. It preserves findings from the
    underlying validators, emits CommandResult, writes optional EvidenceReport
    output and performs no destructive action.
    """

    root = project_root()
    result = ValidationGateway(root).validate_scope(scope)
    result = _write_optional_command_report(
        root,
        result,
        subject=f"validation:{scope}",
        report_id=f"validate_{scope}",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-24", "component": "ValidationGateway", "scope": scope},
    )
    _emit_result_event(root, result, subject=f"validation:{scope}")
    _persist_result(root, result, subject=f"validation:{scope}")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def traceability_scan_command(
    *,
    targets: list[str] | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Extract conservative SDLC traceability entities from local docs.

    FUNC-SPRINT-25 is read-only and heuristic: it detects explicit ID patterns
    such as FR-*, REQ-*, US-*, AC-*, TEST-* and ADR-*; it reports malformed or
    duplicated IDs; and it does not infer traceability relationships.
    """

    root = project_root()
    result = MarkdownTraceabilityExtractor(root).scan(targets=targets)
    result = _write_optional_command_report(
        root,
        result,
        subject="traceability:scan",
        report_id="traceability_scan",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-25", "component": "MarkdownTraceabilityExtractor"},
    )
    _emit_result_event(root, result, subject="traceability:scan")
    _persist_result(root, result, subject="traceability:scan")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def traceability_engine_command(
    action: str,
    *,
    targets: list[str] | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run the FUNC-SPRINT-26 traceability engine actions.

    The engine is deterministic, read-only and local-first. Gaps are reported
    as warning findings in the initial implementation and do not block by
    themselves.
    """

    root = project_root()
    engine = TraceabilityEngine(root)
    if action == "validate":
        result = engine.validate(targets=targets)
    elif action == "coverage":
        result = engine.coverage(targets=targets)
    elif action == "report":
        result = engine.report(targets=targets)
    else:
        result = CommandResult(
            command=f"traceability {action}",
            ok=False,
            exit_code=ExitCode.FAIL,
            message="Unsupported traceability engine action.",
            findings=[
                Finding(
                    id="TRACEABILITY_ACTION_UNSUPPORTED",
                    message=f"Unsupported traceability action: {action}.",
                    severity=Severity.FAIL,
                )
            ],
        )
    result = _write_optional_command_report(
        root,
        result,
        subject=f"traceability:{action}",
        report_id=f"traceability_{action}",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-26", "component": "TraceabilityEngine", "action": action},
    )
    _emit_result_event(root, result, subject=f"traceability:{action}")
    _persist_result(root, result, subject=f"traceability:{action}")
    print_result(result, json_output=json_output)
    return int(result.exit_code)

def traceability_architecture_drift_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Run the FUNC-SPRINT-27 architecture/code drift detector.

    The detector is read-only and heuristic. It compares top-level
    `src/devpilot_core/*` modules against controlled C4/architecture docs and
    emits non-destructive findings for review.
    """

    root = project_root()
    result = TraceabilityEngine(root).architecture_drift()
    result = _write_optional_command_report(
        root,
        result,
        subject="traceability:architecture-drift",
        report_id="traceability_architecture_drift",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-27", "component": "ArchitectureDriftDetector"},
    )
    _emit_result_event(root, result, subject="traceability:architecture-drift")
    _persist_result(root, result, subject="traceability:architecture-drift")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def schema_list_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """List registered DevPilot schemas without validating instances.

    FUNC-SPRINT-21 introduces the dependency-free Schema Registry. The command
    verifies catalog integrity, duplicate IDs and missing schema files, then
    returns a normalized CommandResult. Full JSON instance validation remains
    explicitly deferred to FUNC-SPRINT-22.
    """

    root = project_root()
    result = SchemaRegistry(root).list()
    result = _write_optional_command_report(
        root,
        result,
        subject="docs/schemas/schema_catalog.json",
        report_id="schema_list",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-21", "component": "SchemaRegistry"},
    )
    _emit_result_event(root, result, subject="docs/schemas/schema_catalog.json")
    _persist_result(root, result, subject="docs/schemas/schema_catalog.json")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def schema_validate_command(
    *,
    schema: str,
    instance: str,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Validate one JSON/YAML-owned instance against a local DevPilot JSON Schema.

    FUNC-SPRINT-22 introduces SchemaValidator using the ADR-governed
    `jsonschema` dependency. The command remains local-first: it reads only
    local files, emits CommandResult, can persist an EvidenceReport, and never
    calls external APIs or network resources.
    """

    root = project_root()
    instance_path = Path(instance)
    if instance_path.suffix.lower() in {".yaml", ".yml"} or str(instance_path).lower().endswith((".yaml.example", ".yml.example")):
        try:
            schema_path = SchemaValidator(root).resolve_schema_path(schema)
            schema_payload = json.loads(schema_path.read_text(encoding="utf-8"))
        except Exception:
            schema_payload = {}
        if (
            str(schema).lower() in {"providerconfig", "schema-devpl-provider-config-v2"}
            or str(schema).replace("\\", "/").endswith("provider_config.schema.json")
            or schema_payload.get("x-devpilot-schema-id") in {"SCHEMA-DEVPL-PROVIDER-CONFIG-V1", "SCHEMA-DEVPL-PROVIDER-CONFIG-V2"}
            or schema_payload.get("contract") == "ProviderConfig"
        ):
            payload = parse_provider_config_yaml((root / instance_path) if not instance_path.is_absolute() else instance_path)
            result = SchemaValidator(root).validate_payload(schema=schema, payload=payload, instance_label=instance)
        else:
            result = SchemaValidator(root).validate(schema=schema, instance=instance)
    else:
        result = SchemaValidator(root).validate(schema=schema, instance=instance)
    result = _write_optional_command_report(
        root,
        result,
        subject=instance,
        report_id="schema_validation",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-22", "component": "SchemaValidator", "schema": schema},
    )
    _emit_result_event(root, result, subject=instance)
    _persist_result(root, result, subject=instance)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def schema_validate_miasi_command(
    *,
    scope: str = "all",
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Validate MIASI registries structurally before semantic MIASI rules.

    FUNC-SPRINT-23 adds JSON Schemas for Agent Registry, Tool Registry and
    Policy Matrix. This command validates structure only, keeps execution
    local-first, and does not replace `miasi validate` business-rule checks.
    """

    root = project_root()
    result = BuiltinContractValidator(root).validate_miasi(scope=scope)
    result = _write_optional_command_report(
        root,
        result,
        subject=".devpilot/miasi",
        report_id="schema_validate_miasi",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-23", "component": "BuiltinContractValidator"},
    )
    _emit_result_event(root, result, subject=".devpilot/miasi")
    _persist_result(root, result, subject=".devpilot/miasi")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def schema_validate_workspace_command(
    *,
    path: str = ".devpilot/project.yaml",
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Validate `.devpilot/project.yaml` after dependency-free YAML parsing.

    FUNC-SPRINT-23 validates the known DevPilot workspace config shape through
    `workspace_project.schema.json`. This is structural validation only; it does
    not replace WorkspaceManager readiness/status checks.
    """

    root = project_root()
    result = BuiltinContractValidator(root).validate_workspace(path=path)
    result = _write_optional_command_report(
        root,
        result,
        subject=path,
        report_id="schema_validate_workspace",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-23", "component": "BuiltinContractValidator"},
    )
    _emit_result_event(root, result, subject=path)
    _persist_result(root, result, subject=path)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def schema_validate_providers_command(
    *,
    path: str = ".devpilot/providers.yaml.example",
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Validate provider metadata without reading secrets or contacting providers.

    FUNC-SPRINT-23 validates provider configuration shape and blocks raw secret
    fields structurally. It reads metadata only; no API keys are loaded from the
    environment and no endpoint is contacted.
    """

    root = project_root()
    result = BuiltinContractValidator(root).validate_providers(path=path)
    result = _write_optional_command_report(
        root,
        result,
        subject=path,
        report_id="schema_validate_providers",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-23", "component": "BuiltinContractValidator"},
    )
    _emit_result_event(root, result, subject=path)
    _persist_result(root, result, subject=path)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def schema_validate_manifest_command(
    manifest: str,
    *,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Validate one functional sprint manifest against its structural contract."""

    root = project_root()
    result = BuiltinContractValidator(root).validate_manifest(manifest)
    result = _write_optional_command_report(
        root,
        result,
        subject=manifest,
        report_id="schema_validate_manifest",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-23", "component": "BuiltinContractValidator"},
    )
    _emit_result_event(root, result, subject=manifest)
    _persist_result(root, result, subject=manifest)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def app_contract_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Expose the internal application-service contract for future UI shells."""

    root = project_root()
    result = ApplicationService(root).application_contract()
    result = _write_optional_command_report(
        root,
        result,
        subject="docs/07_interfaces/internal_application_contract.md",
        report_id="app_contract",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-65", "component": "ApplicationService v2"},
    )
    _emit_result_event(root, result, subject="docs/07_interfaces/internal_application_contract.md")
    _persist_result(root, result, subject="docs/07_interfaces/internal_application_contract.md")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def api_serve_command(
    *,
    host: str = "127.0.0.1",
    port: int = 8787,
    dry_run: bool = True,
    execute: bool = False,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Prepare or run the secured local API MVP from FUNC-SPRINT-68.

    Dry-run is the default. Real serving requires --execute and remains
    localhost-only. Sprint 68 requires token, restricted CORS and policy binding
    but still does not implement enterprise RBAC or remote serving.
    """

    root = project_root()
    allowed_hosts = {"127.0.0.1", "localhost"}
    if host not in allowed_hosts:
        result = CommandResult(
            command="api serve",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Secured API local MVP only allows localhost hosts.",
            data={
                "summary": {
                    "host": host,
                    "port": port,
                    "allowed_hosts": sorted(allowed_hosts),
                    "server_started": False,
                    "api_implemented": True,
                    "api_security_implemented": True,
                    "sprint": "FUNC-SPRINT-68",
                }
            },
            findings=[
                Finding(
                    id="API_HOST_NOT_LOCALHOST_BLOCK",
                    message="Refusing to bind secured local API to a non-localhost host.",
                    severity=Severity.BLOCK,
                    metadata={"host": host},
                )
            ],
        )
    else:
        from .interfaces.api import DEFAULT_API_HOST, DEFAULT_API_PORT, api_route_paths, api_security_summary, create_app

        app = create_app(root)
        route_paths = api_route_paths(app)
        security_summary = api_security_summary(app)
        data = {
            "summary": {
                "host": host,
                "port": port,
                "default_host": DEFAULT_API_HOST,
                "default_port": DEFAULT_API_PORT,
                "dry_run": dry_run or not execute,
                "execute": execute,
                "server_started": False,
                "api_implemented": True,
                "api_status": "secured-initial",
                "api_security_implemented": True,
                "routes_total": len(route_paths),
                "dangerous_routes_total": len([p for p in route_paths if any(fragment in p for fragment in ["apply", "execute", "rollback/execute", "refactor/execute"])]),
                "external_api_used": False,
                "network_used": False,
                "preliminary": True,
                **security_summary,
            },
            "routes": route_paths,
            "notes": [
                "Dry-run is the default for this CLI command.",
                "Use --execute only to start the local uvicorn server on localhost.",
                "Sprint 68 requires token for protected endpoints and restricts CORS by default.",
                "Use `python -m devpilot_core api token --json` to generate a session token, then set DEVPILOT_API_TOKEN before serving.",
            ],
        }
        result = CommandResult(
            command="api serve",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Secured local API configuration is valid; dry-run did not start a server." if not execute else "Starting secured local API on localhost.",
            data=data,
            findings=[
                Finding(
                    id="API_LOCAL_SECURITY_READY",
                    message="FastAPI local MVP is protected by token, restricted CORS and policy binding.",
                    severity=Severity.INFO,
                    metadata={"host": host, "port": port, "routes_total": len(route_paths), "token_required": True},
                )
            ],
        )

        if execute and security_summary.get("token_source") == "generated-ephemeral":
            result = CommandResult(
                command="api serve",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Set DEVPILOT_API_TOKEN before starting the secured local API with --execute.",
                data={"summary": {**data["summary"], "server_started": False, "token_source": "generated-ephemeral"}},
                findings=[
                    Finding(
                        id="API_EXECUTE_REQUIRES_EXPLICIT_TOKEN_BLOCK",
                        message="The secured API cannot be started with an unknown generated token. Generate a token and set DEVPILOT_API_TOKEN first.",
                        severity=Severity.BLOCK,
                    )
                ],
            )

        if execute and not dry_run and result.ok:
            result.data["summary"]["server_started"] = True
            print_result(result, json_output=json_output)
            try:
                import uvicorn
            except Exception as exc:  # pragma: no cover - dependency guard
                error = CommandResult(
                    command="api serve",
                    ok=False,
                    exit_code=ExitCode.ERROR,
                    message="uvicorn is required to execute the API server. Install devpilot-local[api].",
                    findings=[Finding(id="API_UVICORN_MISSING", message=str(exc), severity=Severity.ERROR)],
                )
                print_result(error, json_output=json_output)
                return int(error.exit_code)
            uvicorn.run(app, host=host, port=port)
            return int(ExitCode.PASS)

    result = _write_optional_command_report(
        root,
        result,
        subject="api-local",
        report_id="api_serve",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-68", "component": "LocalAPI Security"},
    )
    _emit_result_event(root, result, subject="api-local")
    _persist_result(root, result, subject="api-local")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def api_token_command(*, json_output: bool = False) -> int:
    """Generate a local API token for one user-controlled session.

    This command intentionally does not emit observability events, write reports
    or persist LocalStore history because the raw token is a secret.
    """

    from .interfaces.api import API_TOKEN_ENV_VAR, generate_api_token, redact_token

    token = generate_api_token()
    result = CommandResult(
        command="api token",
        ok=True,
        exit_code=ExitCode.PASS,
        message="Generated a local API session token. Store it in DEVPILOT_API_TOKEN; it is not persisted by DevPilot.",
        data={
            "summary": {
                "token_generated": True,
                "token_redacted": redact_token(token),
                "token_env_var": API_TOKEN_ENV_VAR,
                "persisted": False,
                "write_report_supported": False,
                "preliminary": True,
            },
            "token": token,
            "powershell": f"$env:{API_TOKEN_ENV_VAR} = '{token}'",
        },
        findings=[Finding(id="API_TOKEN_GENERATED", message="A local API token was generated and must be handled as a secret.", severity=Severity.INFO)],
    )
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def security_readiness_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Run the Fase B operational security readiness gate."""

    root = project_root()
    result = SecurityReadiness(root).run()
    result = _write_optional_command_report(
        root,
        result,
        subject="FASE-B-SEGURIDAD-OPERACIONAL",
        report_id="security_readiness",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-34", "component": "SecurityReadiness"},
    )
    _emit_result_event(root, result, subject="security readiness")
    _persist_result(root, result, subject="security readiness")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def policy_check_command(
    action: str,
    *,
    path: str | None = None,
    text: str | None = None,
    external_api: bool = False,
    provider: str | None = None,
    estimated_cost_usd: float = 0.0,
    allow_external_api: bool = False,
    budget_limit_usd: float = 0.0,
    budget_used_usd: float = 0.0,
    approval_id: str | None = None,
    tool_id: str | None = None,
    subject: str | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Evaluate a simulated action through PolicyEngine/guards.

    FUNC-SPRINT-09 keeps this command non-destructive. It evaluates policy only;
    it does not execute the requested action, read remote services or call LLMs.
    """

    root = project_root()
    base_cost_policy = load_cost_policy(root)
    engine = PolicyEngine(
        root,
        cost_policy=CostPolicy(
            external_api_allowed=allow_external_api or base_cost_policy.external_api_allowed,
            budget_limit_usd=budget_limit_usd if budget_limit_usd > 0 else base_cost_policy.budget_limit_usd,
            budget_used_usd=budget_used_usd if budget_used_usd > 0 else base_cost_policy.budget_used_usd,
            allowed_providers=base_cost_policy.allowed_providers,
        ),
    )
    request = PolicyRequest(
        action=action,
        path=path,
        text=text,
        external_api=external_api,
        provider=provider,
        estimated_cost_usd=estimated_cost_usd,
        dry_run=True,
        approval_id=approval_id,
        tool_id=tool_id,
        subject=subject,
        metadata={"source": "policy-check-cli", "sprint": "FUNC-SPRINT-30"} if approval_id or tool_id or subject else {},
    )
    result = engine.evaluate(request)
    result = _write_optional_command_report(
        root,
        result,
        subject=path or action,
        report_id="policy_check",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-30", "component": "PolicyEngine", "approval_binding": bool(approval_id)},
    )
    _emit_result_event(root, result, subject=path or action)
    _persist_result(root, result, subject=path or action)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def policy_simulate_command(
    *,
    tool_id: str | None = None,
    action: str | None = None,
    subject: str | None = None,
    path: str | None = None,
    approval_id: str | None = None,
    matrix: str | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Simulate policy decisions or run a standard policy matrix."""

    root = project_root()
    if matrix:
        result = PolicySimulationSuite(root).run(matrix=matrix)
        report_id = f"policy_simulate_{matrix}"
        report_subject = f"policy-simulation:{matrix}"
        metadata = {"sprint": "FUNC-SPRINT-34", "component": "PolicySimulationSuite", "matrix": matrix}
    else:
        if not tool_id or not action or not subject:
            result = CommandResult(
                command="policy simulate",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="policy simulate requires either --matrix or --tool/--action/--subject.",
                data={"summary": {"matrix": None, "missing": [name for name, value in {"tool": tool_id, "action": action, "subject": subject}.items() if not value]}},
                findings=[Finding("POLICY_SIMULATE_INPUT_REQUIRED", "Provide --matrix standard or --tool/--action/--subject.", Severity.BLOCK)],
            )
            result = _write_optional_command_report(root, result, subject="policy-simulate:invalid", report_id="policy_simulate", write_report=write_report, metadata={"sprint": "FUNC-SPRINT-34", "component": "PolicyEngine"})
            _emit_result_event(root, result, subject="policy-simulate:invalid")
            _persist_result(root, result, subject="policy-simulate:invalid")
            print_result(result, json_output=json_output)
            return int(result.exit_code)
        engine = PolicyEngine(root, cost_policy=load_cost_policy(root))
        evaluated = engine.evaluate(
            PolicyRequest(
                action=action,
                path=path,
                dry_run=True,
                approval_id=approval_id,
                tool_id=tool_id,
                subject=subject,
                metadata={"source": "policy-simulate-cli", "sprint": "FUNC-SPRINT-30"},
            )
        )
        result = CommandResult(
            command="policy simulate",
            ok=evaluated.ok,
            exit_code=evaluated.exit_code,
            message=evaluated.message,
            data=evaluated.data,
            findings=evaluated.findings,
        )
        report_id = "policy_simulate"
        report_subject = approval_id or f"{tool_id}:{action}:{subject}"
        metadata = {"sprint": "FUNC-SPRINT-30", "component": "PolicyEngine", "approval_binding": bool(approval_id)}
    result = _write_optional_command_report(
        root,
        result,
        subject=report_subject,
        report_id=report_id,
        write_report=write_report,
        metadata=metadata,
    )
    _emit_result_event(root, result, subject=report_subject)
    _persist_result(root, result, subject=report_subject)
    print_result(result, json_output=json_output)
    return int(result.exit_code)

def tests_profiles_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """List configured tests.run profiles without executing subprocesses."""

    root = project_root()
    result = TestsRunTool(root).list_profiles()
    result = _write_optional_command_report(
        root,
        result,
        subject=".devpilot/testing/test_profiles.json",
        report_id="tests_profiles",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-32", "component": "TestsRunTool"},
    )
    _emit_result_event(root, result, subject="tests.run profiles")
    _persist_result(root, result, subject="tests.run profiles")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def tests_run_command(
    *,
    profile: str,
    approval_id: str | None = None,
    timeout_seconds: int | None = None,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Execute one controlled pytest profile through tests.run.

    FUNC-SPRINT-32 implements tests.run as an approval-gated MIASI tool. This
    command evaluates policy first and executes only fixed pytest profiles via
    SafeSubprocessRunner.
    """

    root = project_root()
    result = TestsRunTool(root).run(profile_id=profile, approval_id=approval_id, timeout_seconds=timeout_seconds)
    result = _write_optional_command_report(
        root,
        result,
        subject=f"tests.run:{profile}",
        report_id=f"tests_run_{profile}",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-32", "component": "TestsRunTool", "profile": profile},
    )
    _emit_result_event(root, result, subject=f"tests.run:{profile}")
    _persist_result(root, result, subject=f"tests.run:{profile}")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devpilot", description="DevPilot Local CLI")
    parser.add_argument("--version", action="store_true", help="Show version")
    sub = parser.add_subparsers(dest="command")

    readiness = sub.add_parser("readiness-check", help="Check pre-code readiness artifacts")
    readiness.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    readiness.add_argument("--strict", action="store_true", help="Run strict executable pre-code gate")
    readiness.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    checklist = sub.add_parser("checklist-pre-code", help="Evaluate the executable pre-code checklist gate")
    checklist.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    checklist.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    miasi_required_parser = sub.add_parser("miasi-required", help="Explain MIASI activation for this project")
    miasi_required_parser.add_argument("--json", action="store_true", help="Emit normalized JSON command result")

    miasi = sub.add_parser("miasi", help="Validate executable MIASI registries and policy matrix")
    miasi_sub = miasi.add_subparsers(dest="miasi_command")
    miasi_validate = miasi_sub.add_parser("validate", help="Validate Agent Registry, Tool Registry and Policy Matrix")
    miasi_validate.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    miasi_validate.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")
    miasi_validate_registry = miasi_sub.add_parser("validate-registry", help="Validate executable Agent Registry")
    miasi_validate_registry.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    miasi_validate_registry.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")
    miasi_validate_tools = miasi_sub.add_parser("validate-tools", help="Validate executable Tool Registry")
    miasi_validate_tools.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    miasi_validate_tools.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")
    miasi_validate_policy = miasi_sub.add_parser("validate-policy-matrix", help="Validate executable Policy Matrix")
    miasi_validate_policy.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    miasi_validate_policy.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    frontmatter = sub.add_parser("validate-frontmatter", help="Validate Markdown frontmatter metadata")
    frontmatter.add_argument("path", help="Markdown document path to validate")
    frontmatter.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    frontmatter.add_argument("--strict", action="store_true", help="Treat approved documents without approval as failures")
    frontmatter.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    artifact = sub.add_parser("validate-artifact", help="Validate Markdown artifact structure by profile")
    artifact.add_argument("path", help="Markdown document path to validate")
    artifact.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    artifact.add_argument("--strict", action="store_true", help="Run strict frontmatter validation before structure checks")
    artifact.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    workspace = sub.add_parser("workspace", help="Manage local DevPilot workspaces")
    workspace_sub = workspace.add_subparsers(dest="workspace_command")

    workspace_init = workspace_sub.add_parser("init", help="Initialize .devpilot/project.yaml")
    workspace_init.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    workspace_init.add_argument("--dry-run", action="store_true", help="Preview initialization without writing files; this is the default")
    workspace_init.add_argument("--execute", action="store_true", help="Explicitly create .devpilot/project.yaml")
    workspace_init.add_argument("--project-id", default=None, help="Project id written to project.yaml")
    workspace_init.add_argument("--project-name", default=None, help="Project name written to project.yaml")
    workspace_init.add_argument("--project-type", default=None, help="Project type written to project.yaml")
    workspace_init.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    workspace_status = workspace_sub.add_parser("status", help="Show current workspace status")
    workspace_status.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    workspace_status.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    state = sub.add_parser("state", help="Manage local SQLite operational state")
    state_sub = state.add_subparsers(dest="state_command")
    state_init = state_sub.add_parser("init", help="Initialize .devpilot/devpilot.db")
    state_init.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    state_init.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")
    state_status = state_sub.add_parser("status", help="Show local SQLite store status")
    state_status.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    state_status.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    history = sub.add_parser("history", help="Inspect local SQLite command history")
    history_sub = history.add_subparsers(dest="history_command")
    history_list = history_sub.add_parser("list", help="List recent persisted command runs")
    history_list.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    history_list.add_argument("--limit", type=int, default=10, help="Maximum number of runs to list, capped at 100")
    history_list.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    trace = sub.add_parser("trace", help="Inspect local AgentOps traces and spans")
    trace_sub = trace.add_subparsers(dest="trace_command")
    trace_report = trace_sub.add_parser("report", help="List and summarize recent local traces")
    trace_report.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    trace_report.add_argument("--limit", type=int, default=20, help="Maximum number of traces to list, capped at 100")
    trace_report.add_argument("--without-events", action="store_true", help="Exclude event projections from the report")
    trace_report.add_argument("--without-metrics", action="store_true", help="Exclude metric projections from the report")
    trace_report.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    trace_inspect = trace_sub.add_parser("inspect", help="Inspect one trace id and return its span tree")
    trace_inspect.add_argument("trace_id", help="Trace id to inspect")
    trace_inspect.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    trace_inspect.add_argument("--limit", type=int, default=100, help="Maximum spans/events to inspect, capped at 500")
    trace_inspect.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    metrics = sub.add_parser("metrics", help="Inspect local AgentOps metrics")
    metrics_sub = metrics.add_subparsers(dest="metrics_command")
    metrics_summary = metrics_sub.add_parser("summary", help="Aggregate local command/agent/tool/model metrics")
    metrics_summary.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    metrics_summary.add_argument("--category", default=None, help="Optional metric category filter such as command, agent, tool, policy, approval or model")
    metrics_summary.add_argument("--limit", type=int, default=50, help="Maximum recent metrics to include, capped at 500")
    metrics_summary.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    telemetry = sub.add_parser("telemetry", help="Generate local dry-run telemetry export payloads")
    telemetry_sub = telemetry.add_subparsers(dest="telemetry_command")
    telemetry_export = telemetry_sub.add_parser("export", help="Generate an OpenTelemetry-compatible dry-run payload")
    telemetry_export.add_argument("--format", choices=["otlp", "otlp-json"], default="otlp", help="Dry-run export payload format")
    telemetry_export.add_argument("--dry-run", action="store_true", default=True, help="Generate local payload only; this is the default and only supported Sprint 62 mode")
    telemetry_export.add_argument("--trace-id", default=None, help="Optional trace id to export")
    telemetry_export.add_argument("--limit", type=int, default=20, help="Maximum spans to project, capped by exporter")
    telemetry_export.add_argument("--without-metrics", action="store_true", help="Exclude metric projections from the dry-run payload")
    telemetry_export.add_argument("--endpoint", default=None, help="Blocked in Sprint 62; present only for explicit policy validation")
    telemetry_export.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    telemetry_export.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    agentops = sub.add_parser("agentops", help="Run local AgentOps quality gates and readiness checks")
    agentops_sub = agentops.add_subparsers(dest="agentops_command")
    agentops_status = agentops_sub.add_parser("status", help="Evaluate local AgentOps evidence and Phase E closure readiness")
    agentops_status.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    agentops_status.add_argument("--limit", type=int, default=100, help="Maximum local observability records to inspect, capped at 500")
    agentops_status.add_argument("--strict-runtime-signals", action="store_true", help="Convert missing runtime spans/metrics from warning to BLOCK")
    agentops_status.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    approval = sub.add_parser("approval", help="Manage local human approval workflow records")
    approval_sub = approval.add_subparsers(dest="approval_command")

    approval_request = approval_sub.add_parser("request", help="Create a local approval request")
    approval_request.add_argument("--tool", dest="tool_id", required=True, help="Tool identifier, e.g. tests.run")
    approval_request.add_argument("--action", required=True, help="Requested action, e.g. execute")
    approval_request.add_argument("--subject", required=True, help="Subject/scope target, e.g. pytest or unit")
    approval_request.add_argument("--reason", required=True, help="Human-readable justification")
    approval_request.add_argument("--actor", required=True, help="Local declarative actor requesting approval")
    approval_request.add_argument("--scope", default=None, help="Optional JSON object merged into derived tool/action/subject scope")
    approval_request.add_argument("--expires-at", default=None, help="Optional ISO-8601 expiration timestamp; default uses --ttl-minutes")
    approval_request.add_argument("--ttl-minutes", type=int, default=60, help="Expiration TTL when --expires-at is omitted")
    approval_request.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    approval_request.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    approval_list = approval_sub.add_parser("list", help="List local approval records")
    approval_list.add_argument("--status", choices=[status.value for status in ApprovalStatus], default=None, help="Optional approval status filter")
    approval_list.add_argument("--tool", dest="tool_id", default=None, help="Optional tool_id filter")
    approval_list.add_argument("--action", default=None, help="Optional action filter")
    approval_list.add_argument("--limit", type=int, default=100, help="Maximum records to return")
    approval_list.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    approval_list.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    approval_show = approval_sub.add_parser("show", help="Show one approval record")
    approval_show.add_argument("approval_id", help="Approval ID")
    approval_show.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    approval_show.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    for action_name in ("approve", "deny", "revoke"):
        approval_decision = approval_sub.add_parser(action_name, help=f"{action_name.capitalize()} one approval record")
        approval_decision.add_argument("approval_id", help="Approval ID")
        approval_decision.add_argument("--actor", required=True, help="Local declarative actor making the decision")
        approval_decision.add_argument("--reason", required=True, help="Decision reason")
        approval_decision.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
        approval_decision.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    security = sub.add_parser("security", help="Run operational security readiness gates")
    security_sub = security.add_subparsers(dest="security_command")
    security_readiness = security_sub.add_parser("readiness", help="Run Fase B security readiness gate")
    security_readiness.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    security_readiness.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    tests_parser = sub.add_parser("tests", help="Run controlled local test profiles through MIASI tests.run")
    tests_sub = tests_parser.add_subparsers(dest="tests_command")
    tests_profiles = tests_sub.add_parser("profiles", help="List configured tests.run profiles")
    tests_profiles.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    tests_profiles.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    tests_run = tests_sub.add_parser("run", help="Execute one approval-gated pytest profile")
    tests_run.add_argument("--profile", choices=["smoke", "unit", "all"], default="smoke", help="Configured pytest profile to execute")
    tests_run.add_argument("--approval-id", required=True, help="Approved approval_id scoped to tests.run/execute/<profile>")
    tests_run.add_argument("--timeout-seconds", type=int, default=None, help="Optional timeout not exceeding profile/allowlist maximum")
    tests_run.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    tests_run.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    eval_parser = sub.add_parser("eval", help="Run deterministic offline evaluation suites")
    eval_sub = eval_parser.add_subparsers(dest="eval_command")
    eval_run = eval_sub.add_parser("run", help="Run an offline evaluation suite")
    eval_run.add_argument("--suite", default="documentation", help="Evaluation suite id; default: documentation")
    eval_run.add_argument("--case-id", default=None, help="Optional single case id to run")
    eval_run.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    eval_run.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")



    prompt_parser = sub.add_parser("prompt", help="Inspect governed Prompt Registry contracts")
    prompt_sub = prompt_parser.add_subparsers(dest="prompt_command")

    prompt_list = prompt_sub.add_parser("list", help="List versioned prompt contracts")
    prompt_list.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    prompt_list.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    prompt_validate = prompt_sub.add_parser("validate", help="Validate prompt schema, semantics and basic safety")
    prompt_validate.add_argument("--prompt-id", default=None, help="Optional prompt id to validate")
    prompt_validate.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    prompt_validate.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    prompt_show = prompt_sub.add_parser("show", help="Show one prompt contract with redacted template")
    prompt_show.add_argument("prompt_id", help="Prompt id to show")
    prompt_show.add_argument("--version", default=None, help="Optional exact prompt version")
    prompt_show.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    prompt_show.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    model_parser = sub.add_parser("model", help="Inspect and use safe ModelAdapter providers")
    model_sub = model_parser.add_subparsers(dest="model_command")

    model_providers = model_sub.add_parser("providers", help="Show ModelAdapter provider registry status")
    model_providers.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    model_providers.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    model_health = model_sub.add_parser("health", help="Run bounded provider health checks; all providers by default")
    model_health.add_argument("--provider", default=None, help="Optional provider id, for example ollama or lmstudio; omit to report all providers")
    model_health.add_argument("--timeout-seconds", type=float, default=3.0, help="Local health timeout; default: 3 seconds")
    model_health.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    model_health.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    model_capabilities = model_sub.add_parser("capabilities", help="Show governed model capability matrix")
    model_capabilities.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    model_capabilities.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    model_budget = model_sub.add_parser("budget", help="Inspect local model budget ledger")
    model_budget_sub = model_budget.add_subparsers(dest="model_budget_command")
    model_budget_status = model_budget_sub.add_parser("status", help="Show local model budget ledger status")
    model_budget_status.add_argument("--limit", type=int, default=20, help="Recent cost events to include; default: 20")
    model_budget_status.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    model_budget_status.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    model_eval = model_sub.add_parser("eval", help="Run governed local model evaluation matrix")
    model_eval_sub = model_eval.add_subparsers(dest="model_eval_command")
    model_eval_run = model_eval_sub.add_parser("run", help="Run local model eval suite through ModelEvalRunner")
    model_eval_run.add_argument("--suite", default="model-local-smoke", help="Model eval suite id; default: model-local-smoke")
    model_eval_run.add_argument("--provider", default="mock", help="Provider id to evaluate; default: mock")
    model_eval_run.add_argument("--model", default=None, help="Optional model id override")
    model_eval_run.add_argument("--case-id", default=None, help="Optional model eval case id")
    model_eval_run.add_argument("--timeout-seconds", type=float, default=3.0, help="Local provider timeout; default: 3 seconds")
    model_eval_run.add_argument("--fallback-to-mock", action="store_true", help="Fallback to mock for enabled unavailable local providers")
    model_eval_run.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    model_eval_run.add_argument("--write-report", action="store_true", help="Persist redacted model eval matrix evidence")

    model_generate = model_sub.add_parser("generate", help="Generate text through ModelAdapter")
    model_generate.add_argument("--prompt", default=None, help="Prompt text to generate from; mutually optional with --prompt-id")
    model_generate.add_argument("--prompt-id", default=None, help="Optional Prompt Registry id to render and route")
    model_generate.add_argument("--prompt-version", default=None, help="Optional exact prompt version for --prompt-id")
    model_generate.add_argument("--prompt-input", action="append", default=[], help="Prompt input as key=value; repeat for multiple inputs")
    model_generate.add_argument("--provider", default="mock", help="Provider id; default: mock")
    model_generate.add_argument("--model", default=None, help="Optional model id override")
    model_generate.add_argument("--allow-external-api", action="store_true", help="Simulate explicit external API budget permission")
    model_generate.add_argument("--budget-limit-usd", type=float, default=0.0, help="Simulated CostGuard budget limit")
    model_generate.add_argument("--budget-used-usd", type=float, default=0.0, help="Simulated CostGuard budget already used")
    model_generate.add_argument("--timeout-seconds", type=float, default=3.0, help="Local provider timeout; default: 3 seconds")
    model_generate.add_argument("--fallback-to-mock", action="store_true", help="Fallback to mock if enabled local provider is unavailable")
    model_generate.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    model_generate.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    model_classify = model_sub.add_parser("classify", help="Classify text through ModelAdapter")
    model_classify.add_argument("--text", required=True, help="Text to classify")
    model_classify.add_argument("--labels", required=True, help="Comma-separated labels")
    model_classify.add_argument("--provider", default="mock", help="Provider id; default: mock")
    model_classify.add_argument("--model", default=None, help="Optional model id override")
    model_classify.add_argument("--timeout-seconds", type=float, default=3.0, help="Local provider timeout; default: 3 seconds")
    model_classify.add_argument("--fallback-to-mock", action="store_true", help="Fallback to mock if enabled local provider is unavailable")
    model_classify.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    model_classify.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    model_embed = model_sub.add_parser("embed", help="Embed text through ModelAdapter")
    model_embed.add_argument("--text", required=True, help="Text to embed")
    model_embed.add_argument("--provider", default="mock", help="Provider id; default: mock")
    model_embed.add_argument("--model", default=None, help="Optional model id override")
    model_embed.add_argument("--timeout-seconds", type=float, default=3.0, help="Local provider timeout; default: 3 seconds")
    model_embed.add_argument("--fallback-to-mock", action="store_true", help="Fallback to mock if enabled local provider is unavailable")
    model_embed.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    model_embed.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    git_status = sub.add_parser("git-status", help="Collect read-only Git status and diff statistics")
    git_status.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    git_status.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    git_group = sub.add_parser("git", help="Run GitAdapter v2 read-only commands")
    git_sub = git_group.add_subparsers(dest="git_command")

    git_branches = git_sub.add_parser("branches", help="List Git branches in read-only mode")
    git_branches.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    git_branches.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    git_tags = git_sub.add_parser("tags", help="List Git tags in read-only mode")
    git_tags.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    git_tags.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    git_log = git_sub.add_parser("log", help="List recent Git commits in read-only mode")
    git_log.add_argument("--limit", type=int, default=20, help="Maximum commits to return, 1..200")
    git_log.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    git_log.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    git_diff_report = git_sub.add_parser("diff-report", help="Generate structured read-only Git diff report")
    git_diff_report.add_argument("--max-files", type=int, default=200, help="Maximum changed files to include, 1..1000")
    git_diff_report.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    git_diff_report.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    repo_inventory = sub.add_parser("repo-inventory", help="Generate read-only repository inventory and risk summary")
    repo_inventory.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    repo_inventory.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    repo_parser = sub.add_parser("repo", help="Run repository engineering read-only analyzers")
    repo_sub = repo_parser.add_subparsers(dest="repo_command")
    dependency_graph = repo_sub.add_parser("dependency-graph", help="Build Python import dependency graph without executing code")
    dependency_graph.add_argument("--target", default="src/devpilot_core", help="Target file or directory to analyze; default: src/devpilot_core")
    dependency_graph.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    dependency_graph.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    repo_analyze = repo_sub.add_parser("analyze", help="Analyze repository structure, dependencies, Git state and maintainability risks")
    repo_analyze.add_argument("--target", default=".", help="Target file or directory to analyze; default: workspace root")
    repo_analyze.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    repo_analyze.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    architecture_drift = repo_sub.add_parser("architecture-drift", help="Detect initial architecture/code drift from docs and source modules")
    architecture_drift.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    architecture_drift.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    quality_gate = repo_sub.add_parser("quality-gate", help="Run repository quality gate in dry-run mode")
    quality_gate.add_argument("--target", default=".", help="Repository target for RepoAnalyzer; default: workspace root")
    quality_gate.add_argument("--code-target", default=None, help="Optional code target for CodeReviewEngine; default: src/devpilot_core/repo when present")
    quality_gate.add_argument("--patch-file", default=None, help="Optional patch/diff file to review without applying it")
    quality_gate.add_argument("--patch-text", default=None, help="Optional inline patch text to review without applying it")
    quality_gate.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    quality_gate.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    engineering_gate = repo_sub.add_parser("engineering-gate", help="Run Phase C repository engineering closure gate")
    engineering_gate.add_argument("--profile", choices=["quick", "full"], default="quick", help="Gate profile; quick is default, full adds closure/runtime invariants")
    engineering_gate.add_argument("--target", default=".", help="Repository target for RepoAnalyzer; default: workspace root")
    engineering_gate.add_argument("--code-target", default=None, help="Optional code target for RepoQualityGate")
    engineering_gate.add_argument("--patch-file", default=None, help="Optional patch/diff file to review without applying it")
    engineering_gate.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    engineering_gate.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    patch = sub.add_parser("patch", help="Run patch safety commands")
    patch_sub = patch.add_subparsers(dest="patch_command")
    patch_check = patch_sub.add_parser("check", help="Run patch preflight with git apply --check without applying")
    patch_check.add_argument("--patch-file", required=True, help="Patch/diff file to check within the workspace")
    patch_check.add_argument("--approval-id", default=None, help="Optional scoped approval id for future gated variants")
    patch_check.add_argument("--timeout-seconds", type=int, default=10, help="Timeout for git apply --check, bounded by SafeSubprocessRunner allowlist")
    patch_check.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    patch_check.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    patch_sandbox = patch_sub.add_parser("sandbox", help="Apply a patch only inside an outputs/sandbox workspace and emit a ChangeSet")
    patch_sandbox.add_argument("--patch-file", required=True, help="Patch/diff file to apply inside sandbox")
    patch_sandbox.add_argument("--run-tests", action="store_true", help="Run fixed sandbox tests after patch application; requires approval-id")
    patch_sandbox.add_argument("--test-profile", choices=["smoke", "unit"], default="smoke", help="Fixed sandbox pytest profile to run when --run-tests is set")
    patch_sandbox.add_argument("--approval-id", default=None, help="Approval id required for optional sandbox tests.run execution")
    patch_sandbox.add_argument("--cleanup", action="store_true", help="Remove the sandbox directory after generating ChangeSet evidence")
    patch_sandbox.add_argument("--timeout-seconds", type=int, default=30, help="Timeout for sandbox git apply and optional test subprocesses")
    patch_sandbox.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    patch_sandbox.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")


    rollback = sub.add_parser("rollback", help="Manage local rollback plans and backup points")
    rollback_sub = rollback.add_subparsers(dest="rollback_command")

    rollback_plan = rollback_sub.add_parser("plan", help="Create a rollback plan from a sandbox ChangeSet JSON")
    rollback_plan.add_argument("--changeset-file", required=True, help="ChangeSet JSON file produced by patch sandbox report/evidence")
    rollback_plan.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    rollback_plan.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    rollback_list = rollback_sub.add_parser("list", help="List rollback points in read-only mode")
    rollback_list.add_argument("--limit", type=int, default=100, help="Maximum rollback points to return")
    rollback_list.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    rollback_list.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    rollback_show = rollback_sub.add_parser("show", help="Show one rollback point in read-only mode")
    rollback_show.add_argument("rollback_id", help="Rollback point id")
    rollback_show.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    rollback_show.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    rollback_execute = rollback_sub.add_parser("execute", help="Prepared gated rollback execution; non-mutating in Sprint 42")
    rollback_execute.add_argument("rollback_id", help="Rollback point id")
    rollback_execute.add_argument("--approval-id", default=None, help="Approval id required before any future rollback execution")
    rollback_execute.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    rollback_execute.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    patch_review = sub.add_parser("patch-review", help="Review a unified diff/patch in dry-run mode")
    patch_review.add_argument("--patch-file", default=None, help="Patch/diff file to read within the workspace")
    patch_review.add_argument("--patch-text", default=None, help="Inline patch text for small synthetic reviews")
    patch_review.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    patch_review.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    code_review = sub.add_parser("code-review", help="Run deterministic local code review in dry-run mode")
    code_review.add_argument("--target", default=".", help="File or directory to review; default: workspace root")
    code_review.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    code_review.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    refactor_plan = sub.add_parser("refactor-plan", help="Generate a safe refactor plan without modifying code")
    refactor_plan.add_argument("--target", default=".", help="File or directory to analyze; default: workspace root")
    refactor_plan.add_argument("--goal", default="", help="Optional human-readable refactor goal")
    refactor_plan.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    refactor_plan.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    refactor = sub.add_parser("refactor", help="Run controlled refactor commands")
    refactor_sub = refactor.add_subparsers(dest="refactor_command")
    refactor_sandbox = refactor_sub.add_parser("sandbox", help="Execute a deterministic refactor plan only inside sandbox")
    refactor_sandbox.add_argument("--target", required=True, help="File or directory to refactor in sandbox")
    refactor_sandbox.add_argument("--plan-id", required=True, help="Plan step id emitted by refactor-plan, for example RF-001")
    refactor_sandbox.add_argument("--approval-id", required=True, help="Approval id scoped to refactor.sandbox/execute/refactor:<plan-id>:<target>")
    refactor_sandbox.add_argument("--run-tests", action="store_true", help="Run fixed sandbox tests after refactor; requires --tests-approval-id")
    refactor_sandbox.add_argument("--test-profile", choices=["smoke", "unit"], default="smoke", help="Fixed sandbox pytest profile to run when --run-tests is set")
    refactor_sandbox.add_argument("--tests-approval-id", default=None, help="Approval id scoped to tests.run/execute/sandbox:<profile>")
    refactor_sandbox.add_argument("--cleanup", action="store_true", help="Remove the sandbox directory after generating ChangeSet evidence")
    refactor_sandbox.add_argument("--timeout-seconds", type=int, default=30, help="Timeout for optional sandbox test subprocesses")
    refactor_sandbox.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    refactor_sandbox.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    agent = sub.add_parser("agent", help="Run local/mock DevPilot agents")
    agent_sub = agent.add_subparsers(dest="agent_command")
    agent_run = agent_sub.add_parser("run", help="Run a registered local/mock agent")
    agent_run.add_argument("agent_name", help="Agent alias, for example documentation-audit or precode-documentation")
    agent_run.add_argument("--target", default=None, help="Optional target path for audit agents")
    agent_run.add_argument("--patch-file", default=None, help="Optional patch file for PatchReviewAgent")
    agent_run.add_argument("--idea", default=None, help="Idea text for pre-code documentation drafts")
    agent_run.add_argument("--dry-run", action="store_true", help="Preview without writing files; this is the default")
    agent_run.add_argument("--execute", action="store_true", help="Allow safe draft output writes under outputs/drafts when supported")
    agent_run.add_argument("--provider", default=None, help="Optional model provider id for AgentRuntime v2 model-aware mode; default keeps agents model-free")
    agent_run.add_argument("--model", default=None, help="Optional model id override for model-aware agent calls")
    agent_run.add_argument("--prompt-id", default=None, help="Optional Prompt Registry id for model-aware agent guidance")
    agent_run.add_argument("--prompt-version", default=None, help="Optional exact prompt version for --prompt-id")
    agent_run.add_argument("--prompt-input", action="append", default=[], help="Prompt input as key=value; repeat for multiple inputs")
    agent_run.add_argument("--timeout-seconds", type=float, default=3.0, help="Local provider timeout for model-aware agent calls")
    agent_run.add_argument("--fallback-to-mock", action="store_true", help="Fallback to mock if enabled local provider is unavailable")
    agent_run.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    agent_run.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    quality_gate = sub.add_parser("quality-gate", help="Run local productization quality gates")
    quality_gate_sub = quality_gate.add_subparsers(dest="quality_gate_command")
    quality_gate_run = quality_gate_sub.add_parser("run", help="Run the unified local quality gate")
    quality_gate_run.add_argument("--profile", choices=["fast", "full", "ci", "release"], default="fast", help="Gate profile to execute")
    quality_gate_run.add_argument("--include-pytest", action="store_true", help="Explicitly include pytest -q as an optional subgate")
    quality_gate_run.add_argument("--pytest-timeout-seconds", type=int, default=180, help="Timeout for the optional pytest subgate")
    quality_gate_run.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    quality_gate_run.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")


    release = sub.add_parser("release", help="Generate and verify local release metadata")
    release_sub = release.add_subparsers(dest="release_command")
    release_manifest = release_sub.add_parser("manifest", help="Generate a local release manifest")
    release_manifest.add_argument("--version", dest="release_version", required=True, help="SemVer release version, for example 0.1.0")
    release_manifest.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    release_manifest.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")
    release_changelog = release_sub.add_parser("changelog", help="Generate a human-readable release changelog from local manifests")
    release_changelog.add_argument("--version", dest="release_version", required=True, help="SemVer release version, for example 0.1.0")
    release_changelog.add_argument("--from-sprint", default="FUNC-SPRINT-74", help="First sprint included in the changelog range")
    release_changelog.add_argument("--to-sprint", default=None, help="Optional last sprint included in the changelog range")
    release_changelog.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    release_changelog.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")
    release_sbom = release_sub.add_parser("sbom", help="Generate a local SBOM and supply-chain baseline")
    release_sbom.add_argument("--version", dest="release_version", default=None, help="Optional SemVer release version; defaults to pyproject.toml")
    release_sbom.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    release_sbom.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    release_checksum = release_sub.add_parser("checksum", help="Generate SHA256 evidence for one local release artifact")
    release_checksum.add_argument("--artifact", required=True, help="Local release artifact to checksum, for example dist/release/devpilot-local-0.1.0-source.zip")
    release_checksum.add_argument("--version", dest="release_version", default=None, help="Optional SemVer release version; defaults to pyproject.toml")
    release_checksum.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    release_checksum.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report and checksums.sha256")
    release_smoke = release_sub.add_parser("smoke-test", help="Run local smoke checks for one release artifact")
    release_smoke.add_argument("--artifact", required=True, help="Local release artifact to smoke-test")
    release_smoke.add_argument("--version", dest="release_version", default=None, help="Optional SemVer release version; defaults to pyproject.toml")
    release_smoke.add_argument("--timeout-seconds", type=int, default=30, help="Timeout for minimal local CLI smoke command")
    release_smoke.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    release_smoke.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")
    release_verify = release_sub.add_parser("verify", help="Consolidate checksum and smoke-test evidence for one local release artifact")
    release_verify.add_argument("--artifact", required=True, help="Local release artifact to verify")
    release_verify.add_argument("--version", dest="release_version", default=None, help="Optional SemVer release version; defaults to pyproject.toml")
    release_verify.add_argument("--timeout-seconds", type=int, default=30, help="Timeout for minimal local CLI smoke command")
    release_verify.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    release_verify.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown release verification evidence")

    install = sub.add_parser("install", help="Plan safe local DevPilot installation")
    install_sub = install.add_subparsers(dest="install_command")
    install_plan = install_sub.add_parser("plan", help="Generate local installation strategy and dry-run plan")
    install_plan.add_argument("--mode", choices=["editable", "wheel", "zip", "desktop-bridge", "all"], default="all", help="Installation mode to plan")
    install_plan.add_argument("--version", dest="install_version", default=None, help="Optional SemVer version; defaults to pyproject.toml")
    install_plan.add_argument("--artifact", default=None, help="Optional local wheel or ZIP artifact path for mode-specific validation")
    install_plan.add_argument("--python-executable", default="python", help="Python executable name used in generated plan commands")
    install_plan.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    install_plan.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    backup = sub.add_parser("backup", help="Create, list and restore governed local backups")
    backup_sub = backup.add_subparsers(dest="backup_command")
    backup_create = backup_sub.add_parser("create", help="Create a backup plan or local backup artifact")
    backup_create.add_argument("--dry-run", action="store_true", default=True, help="Preview backup creation without writing artifacts; this is the default")
    backup_create.add_argument("--execute", action="store_true", help="Write the local backup ZIP and manifest under .devpilot/backups")
    backup_create.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    backup_create.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")
    backup_list = backup_sub.add_parser("list", help="List local backup sidecar manifests")
    backup_list.add_argument("--limit", type=int, default=50, help="Maximum backup records to return")
    backup_list.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    backup_list.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")
    backup_restore = backup_sub.add_parser("restore", help="Plan or execute a controlled local restore")
    backup_restore.add_argument("--backup-id", required=True, help="Backup id to restore, for example backup-20260617T220000Z-abc12345")
    backup_restore.add_argument("--dry-run", action="store_true", default=True, help="Preview restore without overwriting files; this is the default")
    backup_restore.add_argument("--execute", action="store_true", help="Perform restore; requires --confirm-restore")
    backup_restore.add_argument("--confirm-restore", action="store_true", help="Explicitly confirm restore overwrites when --execute is used")
    backup_restore.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    backup_restore.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    upgrade = sub.add_parser("upgrade", help="Plan local upgrade readiness")
    upgrade_sub = upgrade.add_subparsers(dest="upgrade_command")
    upgrade_check = upgrade_sub.add_parser("check", help="Generate local upgrade readiness plan")
    upgrade_check.add_argument("--target-version", default=None, help="Optional SemVer target version; defaults to pyproject.toml")
    upgrade_check.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    upgrade_check.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    package = sub.add_parser("package", help="Build local clean release packages")
    package_sub = package.add_subparsers(dest="package_command")
    package_build = package_sub.add_parser("build", help="Plan or build local clean release packages")
    package_build.add_argument("--kind", choices=["repo-zip", "python", "all"], default="repo-zip", help="Package kind to build or plan")
    package_build.add_argument("--version", dest="package_version", required=True, help="SemVer package version, for example 0.1.0")
    package_build.add_argument("--execute", action="store_true", help="Write local artifacts under dist/; default is dry-run")
    package_build.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    package_build.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    validate = sub.add_parser("validate", help="Run unified DevPilot validation gateway")
    validate.add_argument("scope", choices=["docs", "contracts", "all"], help="Validation group to execute")
    validate.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    validate.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    traceability = sub.add_parser("traceability", help="Inspect local SDLC traceability entities")
    traceability_sub = traceability.add_subparsers(dest="traceability_command")
    traceability_scan = traceability_sub.add_parser("scan", help="Extract explicit traceability IDs from local docs")
    traceability_scan.add_argument("--target", action="append", default=None, help="Optional file or directory to scan; can be repeated")
    traceability_scan.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    traceability_scan.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    traceability_validate = traceability_sub.add_parser("validate", help="Validate explicit traceability coverage gaps")
    traceability_validate.add_argument("--target", action="append", default=None, help="Optional file or directory to validate; can be repeated")
    traceability_validate.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    traceability_validate.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    traceability_coverage = traceability_sub.add_parser("coverage", help="Compute traceability coverage metrics")
    traceability_coverage.add_argument("--target", action="append", default=None, help="Optional file or directory to analyze; can be repeated")
    traceability_coverage.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    traceability_coverage.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    traceability_report = traceability_sub.add_parser("report", help="Generate a consolidated traceability report")
    traceability_report.add_argument("--target", action="append", default=None, help="Optional file or directory to report; can be repeated")
    traceability_report.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    traceability_report.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    traceability_architecture_drift = traceability_sub.add_parser("architecture-drift", help="Detect initial architecture/code drift without modifying files")
    traceability_architecture_drift.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    traceability_architecture_drift.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    schema = sub.add_parser("schema", help="Inspect local DevPilot schema registry")
    schema_sub = schema.add_subparsers(dest="schema_command")
    schema_list = schema_sub.add_parser("list", help="List registered versioned schemas")
    schema_list.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    schema_list.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    schema_validate = schema_sub.add_parser("validate", help="Validate a JSON instance or owned provider YAML against a local schema")
    schema_validate.add_argument("--schema", required=True, help="Schema path, schema_id or contract name")
    schema_validate.add_argument("--instance", required=True, help="JSON instance file to validate")
    schema_validate.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    schema_validate.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")


    schema_validate_miasi = schema_sub.add_parser("validate-miasi", help="Validate MIASI registries against structural schemas")
    schema_validate_miasi.add_argument("--scope", choices=["all", "agents", "tools", "policy"], default="all", help="MIASI contract scope to validate")
    schema_validate_miasi.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    schema_validate_miasi.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    schema_validate_workspace = schema_sub.add_parser("validate-workspace", help="Validate .devpilot/project.yaml against workspace schema")
    schema_validate_workspace.add_argument("--path", default=".devpilot/project.yaml", help="Workspace project YAML path")
    schema_validate_workspace.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    schema_validate_workspace.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    schema_validate_providers = schema_sub.add_parser("validate-providers", help="Validate provider metadata against provider schema")
    schema_validate_providers.add_argument("--path", default=".devpilot/providers.yaml.example", help="Provider YAML metadata path")
    schema_validate_providers.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    schema_validate_providers.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    schema_validate_manifest = schema_sub.add_parser("validate-manifest", help="Validate a functional sprint manifest")
    schema_validate_manifest.add_argument("manifest", help="Manifest JSON file, e.g. docs/functional_sprint_23_manifest.json")
    schema_validate_manifest.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    schema_validate_manifest.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    app = sub.add_parser("app", help="Expose application-service contracts for future desktop/web shells")
    app_sub = app.add_subparsers(dest="app_command")
    app_contract = app_sub.add_parser("contract", help="Show internal ApplicationService/DTO contract")
    app_contract.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    app_contract.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    api = sub.add_parser("api", help="Run, inspect or secure the local API MVP")
    api_sub = api.add_subparsers(dest="api_command")
    api_serve = api_sub.add_parser("serve", help="Dry-run or start the local API server")
    api_serve.add_argument("--host", default="127.0.0.1", help="Bind host; localhost only")
    api_serve.add_argument("--port", type=int, default=8787, help="Bind port for the local API")
    api_serve.add_argument("--dry-run", action="store_true", help="Validate API configuration without starting the server")
    api_serve.add_argument("--execute", action="store_true", help="Actually start uvicorn on localhost")
    api_serve.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    api_serve.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    api_token = api_sub.add_parser("token", help="Generate a local API session token without persisting it")
    api_token.add_argument("--json", action="store_true", help="Emit normalized JSON command result")

    policy = sub.add_parser("policy", help="Evaluate deterministic DevPilot safety policies")
    policy_sub = policy.add_subparsers(dest="policy_command")
    policy_check = policy_sub.add_parser("check", help="Evaluate a simulated action through PolicyEngine")
    policy_check.add_argument("action", help="Simulated action, for example read/write/delete/external-api")
    policy_check.add_argument("--path", default=None, help="Optional path subject for PathGuard")
    policy_check.add_argument("--text", default=None, help="Optional text payload scanned by SecretGuard")
    policy_check.add_argument("--external-api", action="store_true", help="Mark the request as external API usage")
    policy_check.add_argument("--provider", default=None, help="Provider name for CostGuard, for example mock/local/openai")
    policy_check.add_argument("--estimated-cost-usd", type=float, default=0.0, help="Estimated cost used by CostGuard")
    policy_check.add_argument("--allow-external-api", action="store_true", help="Explicitly simulate a local policy that allows external APIs")
    policy_check.add_argument("--budget-limit-usd", type=float, default=0.0, help="Local simulated budget limit")
    policy_check.add_argument("--budget-used-usd", type=float, default=0.0, help="Local simulated budget already used")
    policy_check.add_argument("--approval-id", default=None, help="Optional human approval ID for approval-gated actions")
    policy_check.add_argument("--tool", dest="tool_id", default=None, help="Optional MIASI tool ID used for approval scope matching")
    policy_check.add_argument("--subject", default=None, help="Optional tool subject used for approval scope matching")
    policy_check.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    policy_check.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    policy_simulate = policy_sub.add_parser("simulate", help="Simulate a tool/action decision with optional approval binding")
    policy_simulate.add_argument("--tool", dest="tool_id", default=None, help="MIASI tool identifier, e.g. tests.run")
    policy_simulate.add_argument("--action", default=None, help="Tool action, e.g. execute")
    policy_simulate.add_argument("--subject", default=None, help="Tool subject, e.g. pytest or unit")
    policy_simulate.add_argument("--path", default=None, help="Optional path subject for PathGuard")
    policy_simulate.add_argument("--approval-id", default=None, help="Optional human approval ID")
    policy_simulate.add_argument("--matrix", choices=["standard"], default=None, help="Run a predefined policy simulation matrix")
    policy_simulate.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    policy_simulate.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    standards = sub.add_parser("standards", help="Inspect local MIPSoftware/MIASI standards registry")
    standards_sub = standards.add_subparsers(dest="standards_command")
    standards_status = standards_sub.add_parser("status", help="Show local standards registry status")
    standards_status.add_argument("--json", action="store_true", help="Emit normalized JSON command result")

    return parser


def _command_name_from_args(args: argparse.Namespace) -> str:
    """Return a stable command name for observability events."""

    if getattr(args, "version", False) is True:
        return "version"
    command = getattr(args, "command", None)
    if command == "standards":
        subcommand = getattr(args, "standards_command", None)
        return "standards status" if subcommand == "status" else "standards"
    if command == "workspace":
        subcommand = getattr(args, "workspace_command", None)
        return f"workspace {subcommand}" if subcommand else "workspace"
    if command == "policy":
        subcommand = getattr(args, "policy_command", None)
        return f"policy {subcommand}" if subcommand else "policy"
    if command == "miasi":
        subcommand = getattr(args, "miasi_command", None)
        return f"miasi {subcommand}" if subcommand else "miasi"
    if command == "state":
        subcommand = getattr(args, "state_command", None)
        return f"state {subcommand}" if subcommand else "state"
    if command == "history":
        subcommand = getattr(args, "history_command", None)
        return f"history {subcommand}" if subcommand else "history"
    if command == "trace":
        subcommand = getattr(args, "trace_command", None)
        return f"trace {subcommand}" if subcommand else "trace"
    if command == "metrics":
        subcommand = getattr(args, "metrics_command", None)
        return f"metrics {subcommand}" if subcommand else "metrics"
    if command == "approval":
        subcommand = getattr(args, "approval_command", None)
        return f"approval {subcommand}" if subcommand else "approval"
    if command == "tests":
        subcommand = getattr(args, "tests_command", None)
        return f"tests {subcommand}" if subcommand else "tests"
    if command == "security":
        subcommand = getattr(args, "security_command", None)
        return f"security {subcommand}" if subcommand else "security"
    if command == "agent":
        subcommand = getattr(args, "agent_command", None)
        return f"agent {subcommand}" if subcommand else "agent"
    if command == "quality-gate":
        subcommand = getattr(args, "quality_gate_command", None)
        return f"quality-gate {subcommand}" if subcommand else "quality-gate"
    if command == "validate":
        scope = getattr(args, "scope", None)
        return f"validate {scope}" if scope else "validate"
    if command == "traceability":
        subcommand = getattr(args, "traceability_command", None)
        return f"traceability {subcommand}" if subcommand else "traceability"
    if command == "schema":
        subcommand = getattr(args, "schema_command", None)
        return f"schema {subcommand}" if subcommand else "schema"
    if command == "eval":
        subcommand = getattr(args, "eval_command", None)
        return f"eval {subcommand}" if subcommand else "eval"
    if command == "model":
        subcommand = getattr(args, "model_command", None)
        return f"model {subcommand}" if subcommand else "model"
    if command == "repo":
        subcommand = getattr(args, "repo_command", None)
        return f"repo {subcommand}" if subcommand else "repo"
    if command == "patch":
        subcommand = getattr(args, "patch_command", None)
        return f"patch {subcommand}" if subcommand else "patch"
    return command or "help"


def _dispatch(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Dispatch parsed CLI args without observability wrapper concerns."""

    if getattr(args, "version", False) is True:
        print(f"devpilot-local {__version__}")
        return int(ExitCode.PASS)
    if args.command == "readiness-check":
        return readiness_check(json_output=args.json, strict=args.strict, write_report=args.write_report)
    if args.command == "checklist-pre-code":
        return checklist_pre_code_command(json_output=args.json, write_report=args.write_report)
    if args.command == "miasi-required":
        return miasi_required(json_output=args.json)
    if args.command == "miasi":
        if args.miasi_command == "validate":
            return miasi_validate_command(scope="all", json_output=args.json, write_report=args.write_report)
        if args.miasi_command == "validate-registry":
            return miasi_validate_command(scope="agents", json_output=args.json, write_report=args.write_report)
        if args.miasi_command == "validate-tools":
            return miasi_validate_command(scope="tools", json_output=args.json, write_report=args.write_report)
        if args.miasi_command == "validate-policy-matrix":
            return miasi_validate_command(scope="policy", json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "validate-frontmatter":
        return validate_frontmatter_command(
            args.path,
            json_output=args.json,
            strict=args.strict,
            write_report=args.write_report,
        )
    if args.command == "validate-artifact":
        return validate_artifact_command(
            args.path,
            json_output=args.json,
            strict=args.strict,
            write_report=args.write_report,
        )
    if args.command == "workspace":
        if args.workspace_command == "init":
            return workspace_init_command(
                json_output=args.json,
                execute=args.execute,
                write_report=args.write_report,
                project_id=args.project_id,
                project_name=args.project_name,
                project_type=args.project_type,
            )
        if args.workspace_command == "status":
            return workspace_status_command(json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "state":
        if args.state_command == "init":
            return state_init_command(json_output=args.json, write_report=args.write_report)
        if args.state_command == "status":
            return state_status_command(json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "history":
        if args.history_command == "list":
            return history_list_command(json_output=args.json, limit=args.limit, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "trace":
        if args.trace_command == "report":
            return trace_report_command(
                limit=args.limit,
                include_events=not args.without_events,
                include_metrics=not args.without_metrics,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.trace_command == "inspect":
            return trace_inspect_command(args.trace_id, limit=args.limit, json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "metrics":
        if args.metrics_command == "summary":
            return metrics_summary_command(category=args.category, limit=args.limit, json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "telemetry":
        if args.telemetry_command == "export":
            return telemetry_export_command(
                format=args.format,
                dry_run=args.dry_run,
                trace_id=args.trace_id,
                limit=args.limit,
                include_metrics=not args.without_metrics,
                endpoint=args.endpoint,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "agentops":
        if args.agentops_command == "status":
            return agentops_status_command(
                limit=args.limit,
                strict_runtime_signals=args.strict_runtime_signals,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "approval":
        if args.approval_command == "request":
            return approval_request_command(
                tool_id=args.tool_id,
                action=args.action,
                subject=args.subject,
                actor=args.actor,
                reason=args.reason,
                scope=args.scope,
                expires_at=args.expires_at,
                ttl_minutes=args.ttl_minutes,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.approval_command == "list":
            return approval_list_command(
                status=args.status,
                tool_id=args.tool_id,
                action=args.action,
                limit=args.limit,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.approval_command == "show":
            return approval_show_command(approval_id=args.approval_id, json_output=args.json, write_report=args.write_report)
        if args.approval_command in {"approve", "deny", "revoke"}:
            return approval_decision_command(
                args.approval_command,
                approval_id=args.approval_id,
                actor=args.actor,
                reason=args.reason,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "security":
        if args.security_command == "readiness":
            return security_readiness_command(json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "tests":
        if args.tests_command == "profiles":
            return tests_profiles_command(json_output=args.json, write_report=args.write_report)
        if args.tests_command == "run":
            return tests_run_command(
                profile=args.profile,
                approval_id=args.approval_id,
                timeout_seconds=args.timeout_seconds,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "prompt":
        if args.prompt_command == "list":
            return prompt_list_command(json_output=args.json, write_report=args.write_report)
        if args.prompt_command == "validate":
            return prompt_validate_command(prompt_id=args.prompt_id, json_output=args.json, write_report=args.write_report)
        if args.prompt_command == "show":
            return prompt_show_command(prompt_id=args.prompt_id, version=args.version, json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "model":
        if args.model_command == "providers":
            return model_providers_command(json_output=args.json, write_report=args.write_report)
        if args.model_command == "health":
            return model_health_command(
                provider=args.provider,
                timeout_seconds=args.timeout_seconds,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.model_command == "capabilities":
            return model_capabilities_command(json_output=args.json, write_report=args.write_report)
        if args.model_command == "budget":
            if args.model_budget_command == "status":
                return model_budget_status_command(limit=args.limit, json_output=args.json, write_report=args.write_report)
            parser.print_help()
            return int(ExitCode.FAIL)
        if args.model_command == "generate":
            return model_generate_command(
                prompt=args.prompt,
                prompt_id=args.prompt_id,
                prompt_version=args.prompt_version,
                prompt_inputs=args.prompt_input,
                provider=args.provider,
                model=args.model,
                allow_external_api=args.allow_external_api,
                budget_limit_usd=args.budget_limit_usd,
                budget_used_usd=args.budget_used_usd,
                timeout_seconds=args.timeout_seconds,
                fallback_to_mock=args.fallback_to_mock,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.model_command == "classify":
            return model_classify_command(
                text=args.text,
                labels=args.labels,
                provider=args.provider,
                model=args.model,
                timeout_seconds=args.timeout_seconds,
                fallback_to_mock=args.fallback_to_mock,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.model_command == "embed":
            return model_embed_command(
                text=args.text,
                provider=args.provider,
                model=args.model,
                timeout_seconds=args.timeout_seconds,
                fallback_to_mock=args.fallback_to_mock,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.model_command == "eval":
            if args.model_eval_command == "run":
                return model_eval_run_command(
                    suite=args.suite,
                    provider=args.provider,
                    model=args.model,
                    case_id=args.case_id,
                    timeout_seconds=args.timeout_seconds,
                    fallback_to_mock=args.fallback_to_mock,
                    json_output=args.json,
                    write_report=args.write_report,
                )
            parser.print_help()
            return int(ExitCode.FAIL)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "git-status":
        return git_status_command(json_output=args.json, write_report=args.write_report)
    if args.command == "git":
        if args.git_command in {"branches", "tags"}:
            return git_v2_command(args.git_command, json_output=args.json, write_report=args.write_report)
        if args.git_command == "log":
            return git_v2_command("log", limit=args.limit, json_output=args.json, write_report=args.write_report)
        if args.git_command == "diff-report":
            return git_v2_command("diff-report", max_files=args.max_files, json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "repo-inventory":
        return repo_inventory_command(json_output=args.json, write_report=args.write_report)
    if args.command == "repo":
        if args.repo_command == "dependency-graph":
            return repo_dependency_graph_command(target=args.target, json_output=args.json, write_report=args.write_report)
        if args.repo_command == "analyze":
            return repo_analyze_command(target=args.target, json_output=args.json, write_report=args.write_report)
        if args.repo_command == "architecture-drift":
            return repo_architecture_drift_command(json_output=args.json, write_report=args.write_report)
        if args.repo_command == "quality-gate":
            return repo_quality_gate_command(
                target=args.target,
                code_target=args.code_target,
                patch_file=args.patch_file,
                patch_text=args.patch_text,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.repo_command == "engineering-gate":
            return repo_engineering_gate_command(
                profile=args.profile,
                target=args.target,
                code_target=args.code_target,
                patch_file=args.patch_file,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "patch":
        if args.patch_command == "check":
            return patch_check_command(
                patch_file=args.patch_file,
                approval_id=args.approval_id,
                timeout_seconds=args.timeout_seconds,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.patch_command == "sandbox":
            return patch_sandbox_command(
                patch_file=args.patch_file,
                run_tests=args.run_tests,
                test_profile=args.test_profile,
                approval_id=args.approval_id,
                cleanup=args.cleanup,
                timeout_seconds=args.timeout_seconds,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "rollback":
        if args.rollback_command == "plan":
            return rollback_command("plan", changeset_file=args.changeset_file, json_output=args.json, write_report=args.write_report)
        if args.rollback_command == "list":
            return rollback_command("list", limit=args.limit, json_output=args.json, write_report=args.write_report)
        if args.rollback_command == "show":
            return rollback_command("show", rollback_id=args.rollback_id, json_output=args.json, write_report=args.write_report)
        if args.rollback_command == "execute":
            return rollback_command("execute", rollback_id=args.rollback_id, approval_id=args.approval_id, json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "patch-review":
        return patch_review_command(
            patch_file=args.patch_file,
            patch_text=args.patch_text,
            json_output=args.json,
            write_report=args.write_report,
        )
    if args.command == "code-review":
        return code_review_command(target=args.target, json_output=args.json, write_report=args.write_report)
    if args.command == "refactor-plan":
        return refactor_plan_command(target=args.target, goal=args.goal, json_output=args.json, write_report=args.write_report)
    if args.command == "refactor":
        if args.refactor_command == "sandbox":
            return refactor_sandbox_command(
                target=args.target,
                plan_id=args.plan_id,
                approval_id=args.approval_id,
                run_tests=args.run_tests,
                test_profile=args.test_profile,
                tests_approval_id=args.tests_approval_id,
                cleanup=args.cleanup,
                timeout_seconds=args.timeout_seconds,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "eval":
        if args.eval_command == "run":
            return eval_run_command(
                suite=args.suite,
                case_id=args.case_id,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "agent":
        if args.agent_command == "run":
            return agent_run_command(
                args.agent_name,
                target=args.target,
                idea=args.idea,
                dry_run=True,
                execute=args.execute,
                provider=args.provider,
                model=args.model,
                prompt_id=args.prompt_id,
                prompt_version=args.prompt_version,
                prompt_inputs=args.prompt_input,
                patch_file=args.patch_file,
                timeout_seconds=args.timeout_seconds,
                fallback_to_mock=args.fallback_to_mock,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "quality-gate":
        if args.quality_gate_command == "run":
            return quality_gate_run_command(
                profile=args.profile,
                include_pytest=args.include_pytest,
                pytest_timeout_seconds=args.pytest_timeout_seconds,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)

    if args.command == "release":
        if args.release_command == "manifest":
            return release_manifest_command(version=args.release_version, json_output=args.json, write_report=args.write_report)
        if args.release_command == "changelog":
            return release_changelog_command(
                version=args.release_version,
                from_sprint=args.from_sprint,
                to_sprint=args.to_sprint,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.release_command == "sbom":
            return release_sbom_command(version=args.release_version, json_output=args.json, write_report=args.write_report)
        if args.release_command == "checksum":
            return release_checksum_command(artifact=args.artifact, version=args.release_version, json_output=args.json, write_report=args.write_report)
        if args.release_command == "smoke-test":
            return release_smoke_test_command(
                artifact=args.artifact,
                version=args.release_version,
                timeout_seconds=args.timeout_seconds,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.release_command == "verify":
            return release_verify_command(
                artifact=args.artifact,
                version=args.release_version,
                timeout_seconds=args.timeout_seconds,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "install":
        if args.install_command == "plan":
            return install_plan_command(
                mode=args.mode,
                version=args.install_version,
                artifact=args.artifact,
                python_executable=args.python_executable,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "backup":
        if args.backup_command == "create":
            return backup_create_command(dry_run=args.dry_run, execute=args.execute, json_output=args.json, write_report=args.write_report)
        if args.backup_command == "list":
            return backup_list_command(limit=args.limit, json_output=args.json, write_report=args.write_report)
        if args.backup_command == "restore":
            return backup_restore_command(
                backup_id=args.backup_id,
                dry_run=args.dry_run,
                execute=args.execute,
                confirm_restore=args.confirm_restore,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "upgrade":
        if args.upgrade_command == "check":
            return upgrade_check_command(target_version=args.target_version, json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "package":
        if args.package_command == "build":
            return package_build_command(
                kind=args.kind,
                version=args.package_version,
                execute=args.execute,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "validate":
        return validate_gateway_command(args.scope, json_output=args.json, write_report=args.write_report)
    if args.command == "traceability":
        if args.traceability_command == "scan":
            return traceability_scan_command(targets=args.target, json_output=args.json, write_report=args.write_report)
        if args.traceability_command in {"validate", "coverage", "report"}:
            return traceability_engine_command(
                args.traceability_command,
                targets=args.target,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.traceability_command == "architecture-drift":
            return traceability_architecture_drift_command(json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "schema":
        if args.schema_command == "list":
            return schema_list_command(json_output=args.json, write_report=args.write_report)
        if args.schema_command == "validate":
            return schema_validate_command(
                schema=args.schema,
                instance=args.instance,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.schema_command == "validate-miasi":
            return schema_validate_miasi_command(scope=args.scope, json_output=args.json, write_report=args.write_report)
        if args.schema_command == "validate-workspace":
            return schema_validate_workspace_command(path=args.path, json_output=args.json, write_report=args.write_report)
        if args.schema_command == "validate-providers":
            return schema_validate_providers_command(path=args.path, json_output=args.json, write_report=args.write_report)
        if args.schema_command == "validate-manifest":
            return schema_validate_manifest_command(args.manifest, json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "app":
        if args.app_command == "contract":
            return app_contract_command(json_output=args.json, write_report=args.write_report)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "api":
        if args.api_command == "serve":
            return api_serve_command(
                host=args.host,
                port=args.port,
                dry_run=args.dry_run or not args.execute,
                execute=args.execute,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.api_command == "token":
            return api_token_command(json_output=args.json)
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "policy":
        if args.policy_command == "check":
            return policy_check_command(
                args.action,
                path=args.path,
                text=args.text,
                external_api=args.external_api,
                provider=args.provider,
                estimated_cost_usd=args.estimated_cost_usd,
                allow_external_api=args.allow_external_api,
                budget_limit_usd=args.budget_limit_usd,
                budget_used_usd=args.budget_used_usd,
                approval_id=args.approval_id,
                tool_id=args.tool_id,
                subject=args.subject,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.policy_command == "simulate":
            return policy_simulate_command(
                tool_id=args.tool_id,
                action=args.action,
                subject=args.subject,
                path=args.path,
                approval_id=args.approval_id,
                matrix=args.matrix,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "standards":
        if args.standards_command == "status":
            return standards_status_command(json_output=args.json)
        parser.print_help()
        return int(ExitCode.FAIL)
    parser.print_help()
    return int(ExitCode.PASS)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command_name = _command_name_from_args(args)
    root = project_root()
    logger = EventLogger(root)
    logger.emit_started(command_name, argv=argv if argv is not None else sys.argv[1:])

    try:
        exit_code = _dispatch(args, parser)
        logger.emit_completed(command_name, exit_code=exit_code, ok=exit_code == int(ExitCode.PASS))
        return exit_code
    except DevPilotError as exc:
        logger.emit_error(command_name, error=exc, exit_code=int(exc.exit_code))
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        return int(exc.exit_code)
    except Exception as exc:  # defensive boundary for CLI users
        logger.emit_error(command_name, error=exc, exit_code=int(ExitCode.ERROR))
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        return int(ExitCode.ERROR)
