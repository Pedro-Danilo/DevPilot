from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .cli_models import CommandResult, ExitCode, Finding, Severity
from .errors import DevPilotError
from .observability import EventLogger
from .policy import CostPolicy, PolicyEngine, PolicyRequest, load_cost_policy
from .reports import ReportEngine, build_report_id
from .standards.registry import build_standards_status_result
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

    print_result(result, json_output=json_output)
    return int(result.exit_code)


def miasi_required(*, json_output: bool = False) -> int:
    root = project_root()
    result = build_miasi_required_result()
    _emit_result_event(root, result)
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
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def checklist_pre_code_command(*, json_output: bool = False, strict: bool = True, write_report: bool = False) -> int:
    """Evaluate the executable pre-code checklist gate."""

    root = project_root()
    result = validate_precode_checklist(root, strict=strict)
    result = _write_optional_command_report(root, result, report_id="checklist_pre_code", write_report=write_report)
    _emit_result_event(root, result, subject="docs/checklists/checklist_pre_code.md")
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def standards_status_command(*, json_output: bool = False) -> int:
    """Report local MIPSoftware/MIASI registry status."""

    root = project_root()
    result = build_standards_status_result(root)
    _emit_result_event(root, result, subject="docs/standards")
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

    miasi = sub.add_parser("miasi-required", help="Explain MIASI activation for this project")
    miasi.add_argument("--json", action="store_true", help="Emit normalized JSON command result")

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
