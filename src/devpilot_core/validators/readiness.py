from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.reports import ReportEngine
from devpilot_core.standards.registry import build_standards_status_result
from devpilot_core.validators.artifact import validate_artifact_file
from devpilot_core.validators.checklist import validate_precode_checklist
from devpilot_core.validators.frontmatter import validate_frontmatter_file


REQUIRED_PRE_CODE_ARTIFACTS = [
    "docs/00_product/product_vision.md",
    "docs/00_product/business_case.md",
    "docs/00_product/mvp_scope.md",
    "docs/01_requirements/requirements_specification.md",
    "docs/02_architecture/architecture_document.md",
    "docs/02_architecture/adrs/ADR-0001-adoptar-mipsoftware-y-miasi.md",
    "docs/03_security/security_threat_model.md",
    "docs/04_quality/test_strategy.md",
    "docs/checklists/checklist_pre_code.md",
]

REQUIRED_MIASI_ARTIFACTS = [
    "docs/06_miasi/agent_card.md",
    "docs/06_miasi/tool_card.md",
    "docs/06_miasi/policy_card.md",
    "docs/06_miasi/eval_card.md",
    "docs/06_miasi/human_approval_card.md",
    "docs/06_miasi/observability_card.md",
]

STRICT_REQUIRED_ARTIFACTS = [
    "docs/00_product/product_vision.md",
    "docs/00_product/business_case.md",
    "docs/00_product/mvp_scope.md",
    "docs/01_requirements/requirements_specification.md",
    "docs/01_requirements/user_stories.md",
    "docs/01_requirements/use_cases.md",
    "docs/01_requirements/acceptance_criteria.md",
    "docs/01_requirements/traceability_matrix.md",
    "docs/02_architecture/architecture_document.md",
    "docs/02_architecture/c4_context.md",
    "docs/02_architecture/c4_container.md",
    "docs/03_security/security_threat_model.md",
    "docs/03_security/privacy_assessment.md",
    "docs/04_quality/test_strategy.md",
    "docs/05_operations/observability_plan.md",
    "docs/05_operations/runbook.md",
    *REQUIRED_MIASI_ARTIFACTS,
    "docs/checklists/checklist_pre_code.md",
    "docs/precode_audit_report.md",
    "docs/precode_baseline_decision.md",
]


def check_required_artifacts(root: Path) -> dict[str, Any]:
    """Compatibility readiness check used by early bootstrap tests."""

    checks = []
    for rel in REQUIRED_PRE_CODE_ARTIFACTS:
        path = root / rel
        checks.append(
            {
                "artifact": rel,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    passed = all(item["exists"] and item["size_bytes"] > 0 for item in checks)
    return {"ok": passed, "checks": checks}


def build_readiness_result(root: Path) -> CommandResult:
    """Build the non-strict compatibility result for readiness-check."""

    legacy_result = check_required_artifacts(root)
    findings: list[Finding] = []
    for item in legacy_result["checks"]:
        if not item["exists"]:
            findings.append(
                Finding(
                    id="READINESS_MISSING_ARTIFACT",
                    message=f"Required artifact is missing: {item['artifact']}",
                    severity=Severity.FAIL,
                    path=item["artifact"],
                )
            )
        elif item["size_bytes"] <= 0:
            findings.append(
                Finding(
                    id="READINESS_EMPTY_ARTIFACT",
                    message=f"Required artifact is empty: {item['artifact']}",
                    severity=Severity.FAIL,
                    path=item["artifact"],
                )
            )

    ok = legacy_result["ok"]
    return CommandResult(
        command="readiness-check",
        ok=ok,
        exit_code=ExitCode.PASS if ok else ExitCode.FAIL,
        message="Pre-code readiness artifacts found." if ok else "Pre-code readiness check failed.",
        data=legacy_result,
        findings=findings,
    )


def build_strict_readiness_result(root: Path) -> CommandResult:
    """Run the executable pre-code readiness gate.

    Strict readiness composes the Sprint 02 frontmatter validator, Sprint 03
    artifact validator, Sprint 04 Standards Registry and Sprint 05 pre-code
    checklist gate. It is local-only and deterministic.
    """

    findings: list[Finding] = []
    artifact_checks: list[dict[str, Any]] = []

    for rel in STRICT_REQUIRED_ARTIFACTS:
        path = root / rel
        item: dict[str, Any] = {
            "artifact": rel,
            "exists": path.exists() and path.is_file(),
            "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
            "frontmatter_ok": None,
            "artifact_ok": None,
            "status": None,
            "exit_code": None,
        }

        if not path.exists() or not path.is_file():
            findings.append(
                Finding(
                    id="READINESS_STRICT_REQUIRED_ARTIFACT_MISSING",
                    message=f"Strict readiness required artifact is missing: {rel}",
                    severity=Severity.BLOCK,
                    path=rel,
                )
            )
            artifact_checks.append(item)
            continue

        if item["size_bytes"] <= 0:
            findings.append(
                Finding(
                    id="READINESS_STRICT_EMPTY_ARTIFACT",
                    message=f"Strict readiness required artifact is empty: {rel}",
                    severity=Severity.BLOCK,
                    path=rel,
                )
            )

        if path.suffix.lower() == ".md":
            frontmatter_result = validate_frontmatter_file(path, root=root, strict=True)
            artifact_result = validate_artifact_file(path, root=root, strict=True)
            item["frontmatter_ok"] = frontmatter_result.ok
            item["artifact_ok"] = artifact_result.ok
            item["status"] = artifact_result.data.get("status")
            item["exit_code"] = int(artifact_result.exit_code)

            # `validate_artifact_file` already composes frontmatter findings;
            # keep the standalone frontmatter result only for counters.
            findings.extend(artifact_result.findings)

            if str(item["status"] or "").lower() != "approved":
                findings.append(
                    Finding(
                        id="READINESS_STRICT_ARTIFACT_NOT_APPROVED",
                        message=f"Strict readiness artifact must be approved: {rel}",
                        severity=Severity.BLOCK,
                        path=rel,
                        metadata={"status": item["status"]},
                    )
                )

        artifact_checks.append(item)

    checklist_result = validate_precode_checklist(root, strict=True)
    standards_result = build_standards_status_result(root)
    findings.extend(checklist_result.findings)
    findings.extend(standards_result.findings)

    miasi_missing = [rel for rel in REQUIRED_MIASI_ARTIFACTS if not (root / rel).exists()]
    for rel in miasi_missing:
        findings.append(
            Finding(
                id="READINESS_STRICT_MIASI_ARTIFACT_MISSING",
                message=f"MIASI is required but artifact is missing: {rel}",
                severity=Severity.BLOCK,
                path=rel,
            )
        )

    exit_code = exit_code_for_findings(findings)
    ok = not any(finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for finding in findings)

    return CommandResult(
        command="readiness-check",
        ok=ok,
        exit_code=ExitCode.PASS if ok else exit_code,
        message="Strict pre-code readiness gate passed." if ok else "Strict pre-code readiness gate blocked.",
        data={
            "strict": True,
            "artifacts": artifact_checks,
            "checklist": {
                "ok": checklist_result.ok,
                "exit_code": int(checklist_result.exit_code),
                "summary": checklist_result.data.get("summary", {}),
            },
            "standards": {
                "ok": standards_result.ok,
                "exit_code": int(standards_result.exit_code),
                "summary": standards_result.data.get("summary", {}),
            },
            "miasi_required": True,
            "summary": {
                "required_artifacts_total": len(artifact_checks),
                "required_artifacts_present": sum(1 for item in artifact_checks if item["exists"]),
                "frontmatter_pass": sum(1 for item in artifact_checks if item["frontmatter_ok"] is True),
                "artifact_validation_pass": sum(1 for item in artifact_checks if item["artifact_ok"] is True),
                "findings_total": len(findings),
            },
        },
        findings=findings,
    )


def write_readiness_reports(root: Path, result: CommandResult) -> dict[str, str]:
    """Persist readiness evidence through the central ReportEngine.

    The public function is kept for compatibility with FUNC-SPRINT-05 tests and
    scripts, but the implementation is now delegated to FUNC-SPRINT-06
    ReportEngine so readiness evidence uses the same contract as other gates.
    """

    paths = ReportEngine(root).write_command_report(
        result,
        report_id="readiness_check",
        metadata={
            "sprint": "FUNC-SPRINT-06",
            "contract": "EvidenceReport",
            "compatibility_boundary": "readiness_check legacy filename preserved",
        },
    )
    return paths.to_dict()
