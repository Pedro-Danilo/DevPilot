from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .agents import AgentRuntime
from .cli_models import CommandResult, ExitCode, Finding, Severity
from .errors import DevPilotError
from .evals import EvalRunner
from .observability import EventLogger
from .miasi import MiasiRegistryValidator
from .modeling import ModelAdapterRouter, ModelRouterConfig
from .policy import CostPolicy, PolicyEngine, PolicyRequest, load_cost_policy
from .reports import ReportEngine, build_report_id
from .repo import GitAdapter, RepoInventory
from .refactor import RefactorPlanner
from .review import CodeReviewEngine, PatchReviewEngine
from .standards.registry import build_standards_status_result
from .store import LocalStore
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
        return result
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
    result = build_strict_readiness_result(root) if strict else build_readiness_result(root)

    # Backwards compatibility: readiness-check already generated evidence in
    # FUNC-SPRINT-05. FUNC-SPRINT-06 keeps that behavior but delegates it to the
    # central ReportEngine through write_readiness_reports().
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
) -> ModelAdapterRouter:
    """Build a ModelAdapterRouter with explicit cost controls."""

    return ModelAdapterRouter(
        root,
        config=ModelRouterConfig(
            allow_external_api=allow_external_api,
            budget_limit_usd=budget_limit_usd,
            budget_used_usd=budget_used_usd,
        ),
    )


def model_providers_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Report safe ModelAdapter provider configuration.

    FUNC-SPRINT-17 reads provider metadata only. It never reads raw API keys,
    never contacts local model servers and never calls external APIs.
    """

    root = project_root()
    result = _model_router(root).providers_status()
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
    prompt: str,
    provider: str = "mock",
    model: str | None = None,
    allow_external_api: bool = False,
    budget_limit_usd: float = 0.0,
    budget_used_usd: float = 0.0,
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Generate text through the safe ModelAdapter boundary."""

    root = project_root()
    result = _model_router(
        root,
        allow_external_api=allow_external_api,
        budget_limit_usd=budget_limit_usd,
        budget_used_usd=budget_used_usd,
    ).generate(prompt=prompt, provider=provider, model=model)
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
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Classify text through the safe ModelAdapter boundary."""

    root = project_root()
    label_tuple = tuple(label.strip() for label in labels.split(",") if label.strip())
    result = _model_router(root).classify(text=text, labels=label_tuple, provider=provider, model=model)
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
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Generate a deterministic embedding through the safe ModelAdapter boundary."""

    root = project_root()
    result = _model_router(root).embed(text=text, provider=provider, model=model)
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


def repo_inventory_command(*, json_output: bool = False, write_report: bool = False) -> int:
    """Build a read-only repository inventory and risk summary.

    FUNC-SPRINT-14 inventory scans metadata and small text files for synthetic
    secret-like patterns. It never emits raw file contents and excludes runtime
    output/cache folders by default.
    """

    root = project_root()
    result = RepoInventory(root).build()
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
    result = CodeReviewEngine(root).review(target)
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
    result = RefactorPlanner(root).plan(target, goal=goal, include_code_review=True)
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
    result = EvalRunner(root).run(suite=suite, case_id=case_id)
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
    json_output: bool = False,
    write_report: bool = False,
) -> int:
    """Run a local/mock document agent through AgentRuntime.

    FUNC-SPRINT-12 keeps agent execution offline and deterministic. Dry-run is
    the default; `--execute` is only used by PreCodeDocumentationAgent to write
    a new draft under outputs/drafts and never overwrites approved docs.
    """

    root = project_root()
    effective_dry_run = False if execute else dry_run
    result = AgentRuntime(root).run(agent_name, target=target, idea=idea, dry_run=effective_dry_run)
    result = _write_optional_command_report(
        root,
        result,
        subject=target or agent_name,
        report_id=f"agent_run_{agent_name.replace('-', '_').replace('.', '_')}",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-12", "component": "AgentRuntime"},
    )
    _emit_result_event(root, result, subject=target or agent_name)
    _persist_result(root, result, subject=target or agent_name)
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
    target = Path(path)
    if not target.is_absolute():
        target = root / target
    result = validate_frontmatter_file(target, root=root, strict=strict)
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
    target = Path(path)
    if not target.is_absolute():
        target = root / target
    result = validate_artifact_file(target, root=root, strict=strict)
    result = _write_optional_command_report(root, result, subject=path, write_report=write_report)
    _emit_result_event(root, result, subject=path)
    _persist_result(root, result, subject=path)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def checklist_pre_code_command(*, json_output: bool = False, strict: bool = True, write_report: bool = False) -> int:
    """Evaluate the executable pre-code checklist gate."""

    root = project_root()
    result = validate_precode_checklist(root, strict=strict)
    result = _write_optional_command_report(root, result, report_id="checklist_pre_code", write_report=write_report)
    _emit_result_event(root, result, subject="docs/checklists/checklist_pre_code.md")
    _persist_result(root, result, subject="docs/checklists/checklist_pre_code.md")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def standards_status_command(*, json_output: bool = False) -> int:
    """Report local MIPSoftware/MIASI registry status."""

    root = project_root()
    result = build_standards_status_result(root)
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
    result = manager.status()
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


def history_list_command(*, json_output: bool = False, limit: int = 10, write_report: bool = False) -> int:
    """List recent local command runs from SQLite history."""

    root = project_root()
    result = LocalStore(root).list_runs(limit=limit)
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
    )
    result = engine.evaluate(request)
    result = _write_optional_command_report(
        root,
        result,
        subject=path or action,
        report_id="policy_check",
        write_report=write_report,
        metadata={"sprint": "FUNC-SPRINT-09", "component": "PolicyEngine"},
    )
    _emit_result_event(root, result, subject=path or action)
    _persist_result(root, result, subject=path or action)
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

    eval_parser = sub.add_parser("eval", help="Run deterministic offline evaluation suites")
    eval_sub = eval_parser.add_subparsers(dest="eval_command")
    eval_run = eval_sub.add_parser("run", help="Run an offline evaluation suite")
    eval_run.add_argument("--suite", default="documentation", help="Evaluation suite id; default: documentation")
    eval_run.add_argument("--case-id", default=None, help="Optional single case id to run")
    eval_run.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    eval_run.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")


    model_parser = sub.add_parser("model", help="Inspect and use safe ModelAdapter providers")
    model_sub = model_parser.add_subparsers(dest="model_command")

    model_providers = model_sub.add_parser("providers", help="Show ModelAdapter provider registry status")
    model_providers.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    model_providers.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    model_generate = model_sub.add_parser("generate", help="Generate text through ModelAdapter")
    model_generate.add_argument("--prompt", required=True, help="Prompt text to generate from")
    model_generate.add_argument("--provider", default="mock", help="Provider id; default: mock")
    model_generate.add_argument("--model", default=None, help="Optional model id override")
    model_generate.add_argument("--allow-external-api", action="store_true", help="Simulate explicit external API budget permission")
    model_generate.add_argument("--budget-limit-usd", type=float, default=0.0, help="Simulated CostGuard budget limit")
    model_generate.add_argument("--budget-used-usd", type=float, default=0.0, help="Simulated CostGuard budget already used")
    model_generate.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    model_generate.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    model_classify = model_sub.add_parser("classify", help="Classify text through ModelAdapter")
    model_classify.add_argument("--text", required=True, help="Text to classify")
    model_classify.add_argument("--labels", required=True, help="Comma-separated labels")
    model_classify.add_argument("--provider", default="mock", help="Provider id; default: mock")
    model_classify.add_argument("--model", default=None, help="Optional model id override")
    model_classify.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    model_classify.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    model_embed = model_sub.add_parser("embed", help="Embed text through ModelAdapter")
    model_embed.add_argument("--text", required=True, help="Text to embed")
    model_embed.add_argument("--provider", default="mock", help="Provider id; default: mock")
    model_embed.add_argument("--model", default=None, help="Optional model id override")
    model_embed.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    model_embed.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    git_status = sub.add_parser("git-status", help="Collect read-only Git status and diff statistics")
    git_status.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    git_status.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    repo_inventory = sub.add_parser("repo-inventory", help="Generate read-only repository inventory and risk summary")
    repo_inventory.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    repo_inventory.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

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

    agent = sub.add_parser("agent", help="Run local/mock DevPilot agents")
    agent_sub = agent.add_subparsers(dest="agent_command")
    agent_run = agent_sub.add_parser("run", help="Run a registered local/mock agent")
    agent_run.add_argument("agent_name", help="Agent alias, for example documentation-audit or precode-documentation")
    agent_run.add_argument("--target", default=None, help="Optional target path for audit agents")
    agent_run.add_argument("--idea", default=None, help="Idea text for pre-code documentation drafts")
    agent_run.add_argument("--dry-run", action="store_true", help="Preview without writing files; this is the default")
    agent_run.add_argument("--execute", action="store_true", help="Allow safe draft output writes under outputs/drafts when supported")
    agent_run.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    agent_run.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

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
    policy_check.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    policy_check.add_argument("--write-report", action="store_true", help="Persist JSON/Markdown evidence report")

    standards = sub.add_parser("standards", help="Inspect local MIPSoftware/MIASI standards registry")
    standards_sub = standards.add_subparsers(dest="standards_command")
    standards_status = standards_sub.add_parser("status", help="Show local standards registry status")
    standards_status.add_argument("--json", action="store_true", help="Emit normalized JSON command result")

    return parser


def _command_name_from_args(args: argparse.Namespace) -> str:
    """Return a stable command name for observability events."""

    if getattr(args, "version", False):
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
    if command == "agent":
        subcommand = getattr(args, "agent_command", None)
        return f"agent {subcommand}" if subcommand else "agent"
    if command == "eval":
        subcommand = getattr(args, "eval_command", None)
        return f"eval {subcommand}" if subcommand else "eval"
    if command == "model":
        subcommand = getattr(args, "model_command", None)
        return f"model {subcommand}" if subcommand else "model"
    return command or "help"


def _dispatch(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Dispatch parsed CLI args without observability wrapper concerns."""

    if args.version:
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
    if args.command == "model":
        if args.model_command == "providers":
            return model_providers_command(json_output=args.json, write_report=args.write_report)
        if args.model_command == "generate":
            return model_generate_command(
                prompt=args.prompt,
                provider=args.provider,
                model=args.model,
                allow_external_api=args.allow_external_api,
                budget_limit_usd=args.budget_limit_usd,
                budget_used_usd=args.budget_used_usd,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.model_command == "classify":
            return model_classify_command(
                text=args.text,
                labels=args.labels,
                provider=args.provider,
                model=args.model,
                json_output=args.json,
                write_report=args.write_report,
            )
        if args.model_command == "embed":
            return model_embed_command(
                text=args.text,
                provider=args.provider,
                model=args.model,
                json_output=args.json,
                write_report=args.write_report,
            )
        parser.print_help()
        return int(ExitCode.FAIL)
    if args.command == "git-status":
        return git_status_command(json_output=args.json, write_report=args.write_report)
    if args.command == "repo-inventory":
        return repo_inventory_command(json_output=args.json, write_report=args.write_report)
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
                json_output=args.json,
                write_report=args.write_report,
            )
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
