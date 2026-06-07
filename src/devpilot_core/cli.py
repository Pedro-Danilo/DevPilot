from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .cli_models import CommandResult, ExitCode, Finding, Severity
from .errors import DevPilotError
from .reports import ReportEngine, build_report_id
from .standards.registry import build_standards_status_result
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
    """Return the current working directory as DevPilot project root.

    A later Workspace Manager sprint will replace this compatibility boundary
    with explicit workspace discovery and `.devpilot/` metadata.
    """

    return Path.cwd()


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
) -> CommandResult:
    """Persist report evidence when requested and attach generated paths."""

    if not write_report:
        return result
    effective_report_id = report_id or build_report_id(result.command, subject=subject)
    paths = ReportEngine(root).write_command_report(
        result,
        report_id=effective_report_id,
        subject=subject,
        metadata={"sprint": "FUNC-SPRINT-06", "contract": "EvidenceReport"},
    )
    return _with_report_paths(result, paths.to_dict())


def readiness_check(*, json_output: bool = False, strict: bool = False, write_report: bool = False) -> int:
    root = project_root()
    result = build_strict_readiness_result(root) if strict else build_readiness_result(root)

    # Backwards compatibility: readiness-check already generated evidence in
    # FUNC-SPRINT-05. FUNC-SPRINT-06 keeps that behavior but delegates it to the
    # central ReportEngine through write_readiness_reports().
    report_paths = write_readiness_reports(root, result)
    result = _with_report_paths(result, report_paths)

    print_result(result, json_output=json_output)
    return int(result.exit_code)


def miasi_required(*, json_output: bool = False) -> int:
    result = build_miasi_required_result()
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
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def checklist_pre_code_command(*, json_output: bool = False, strict: bool = True, write_report: bool = False) -> int:
    """Evaluate the executable pre-code checklist gate."""

    root = project_root()
    result = validate_precode_checklist(root, strict=strict)
    result = _write_optional_command_report(root, result, report_id="checklist_pre_code", write_report=write_report)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def standards_status_command(*, json_output: bool = False) -> int:
    """Report local MIPSoftware/MIASI registry status."""

    root = project_root()
    result = build_standards_status_result(root)
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

    standards = sub.add_parser("standards", help="Inspect local MIPSoftware/MIASI standards registry")
    standards_sub = standards.add_subparsers(dest="standards_command")
    standards_status = standards_sub.add_parser("status", help="Show local standards registry status")
    standards_status.add_argument("--json", action="store_true", help="Emit normalized JSON command result")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
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
        if args.command == "standards":
            if args.standards_command == "status":
                return standards_status_command(json_output=args.json)
            parser.print_help()
            return int(ExitCode.FAIL)
        parser.print_help()
        return int(ExitCode.PASS)
    except DevPilotError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        return int(exc.exit_code)
    except Exception as exc:  # defensive boundary for CLI users
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        return int(ExitCode.ERROR)
