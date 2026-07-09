from __future__ import annotations

from pathlib import Path

from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import CommandResult
from devpilot_core.industrial import IndustrialReadinessGate, IndustrialReadinessOptions


def handle_industrial_readiness_check(
    root: Path,
    *,
    minimum_score: float = 80.0,
) -> CommandResult:
    """Build the result for ``industrial-readiness check``.

    POST-H-030-B moves the industrial readiness command logic out of
    ``cli.py`` while preserving the public parser, report writing, event
    emission, persistence, exit codes and rendering behavior in the CLI
    wrapper. The handler does not print output, execute shell commands, call
    network services or mutate source files.
    """

    return IndustrialReadinessGate(
        root,
        options=IndustrialReadinessOptions(minimum_score=minimum_score),
    ).check()


def handle_industrial_readiness_production_ready_local(
    root: Path,
    *,
    write_report: bool = False,
    output_json: str = "outputs/reports/production_ready_local_report.json",
    output_markdown: str = "outputs/reports/production_ready_local_report.md",
) -> CommandResult:
    """Build the result for ``industrial-readiness production-ready-local``.

    The command remains anchored to ``ApplicationService`` because it is a
    boundary operation already consumable by CLI/API. This module only owns the
    CLI-side handler extraction; it does not duplicate production-ready rules.
    """

    return ApplicationService(root).production_ready_local_gate(
        write_report=write_report,
        output_json=output_json,
        output_markdown=output_markdown,
    )


def handle_industrial_readiness_production_ready_local_final(
    root: Path,
    *,
    write_report: bool = False,
    write_audit_markdown: bool = False,
    output_json: str = "outputs/reports/production_ready_local_report.json",
    output_markdown: str = "outputs/reports/production_ready_local_report.md",
    audit_markdown: str = "docs/audits/devpilot_local_production_ready_declaration.md",
) -> CommandResult:
    """Build the result for ``industrial-readiness production-ready-local-final``.

    The final declaration continues to use ``ApplicationService`` so the
    production-ready-local claims boundary stays centralized and shared with
    API-level callers.
    """

    return ApplicationService(root).production_ready_local_final_declaration(
        write_report=write_report,
        write_audit_markdown=write_audit_markdown,
        output_json=output_json,
        output_markdown=output_markdown,
        audit_markdown=audit_markdown,
    )
