from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult, Finding, Severity
from devpilot_core.docs_governance.validator import (
    DocumentationGovernanceValidationOptions,
    DocumentationGovernanceValidator,
)


def run_docs_governance_quality_subgate(root: Path) -> CommandResult:
    """Run documentation governance as a read-only quality-gate subgate.

    POST-H-009-E keeps the source validator as the single source of truth and
    wraps it only to make the quality-gate contract explicit. The wrapper does
    not write reports, mutate source files, call network services, use external
    APIs or rely on an LLM judge.
    """

    result = DocumentationGovernanceValidator(
        Path(root),
        DocumentationGovernanceValidationOptions(write_report=False),
    ).run()
    summary = dict((result.data or {}).get("summary") or {})
    summary.update(
        {
            "quality_gate_subgate": "docs-governance",
            "source_command": result.command,
            "reports_written": False,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "llm_judge_used": False,
            "preliminary": True,
        }
    )
    data = {
        "summary": summary,
        "governance": (result.data or {}).get("governance"),
        "reports": {},
        "notes": [
            "POST-H-009-E integrates docs-governance validate as a deterministic quality-gate subgate.",
            "Generated documentation governance reports remain opt-in through docs-governance report --write-report.",
        ],
    }
    findings = list(result.findings)
    if result.ok and not findings:
        findings = [
            Finding(
                "DOCUMENTATION_GOVERNANCE_QUALITY_SUBGATE_PASS",
                "Documentation governance quality subgate passed.",
                Severity.INFO,
                metadata={"subgate": "docs-governance", "source_command": result.command},
            )
        ]
    return CommandResult(
        command="quality docs-governance",
        ok=result.ok,
        exit_code=result.exit_code,
        message=(
            "Documentation governance quality subgate passed."
            if result.ok
            else "Documentation governance quality subgate found blocking issues."
        ),
        data=data,
        findings=findings,
    )
