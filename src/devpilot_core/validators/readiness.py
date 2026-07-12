from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.reports import ReportEngine
from devpilot_core.standards.registry import build_standards_status_result
from devpilot_core.validators.artifact import validate_artifact_file
from devpilot_core.validators.checklist import validate_precode_checklist
from devpilot_core.validators.frontmatter import validate_frontmatter_file
from devpilot_core.validators.readiness_requirements import (
    FALLBACK_REQUIRED_MIASI_ARTIFACTS,
    FALLBACK_REQUIRED_PRE_CODE_ARTIFACTS,
    FALLBACK_STRICT_REQUIRED_ARTIFACTS,
    load_readiness_requirements,
)


REQUIRED_PRE_CODE_ARTIFACTS = list(FALLBACK_REQUIRED_PRE_CODE_ARTIFACTS)
REQUIRED_MIASI_ARTIFACTS = list(FALLBACK_REQUIRED_MIASI_ARTIFACTS)
STRICT_REQUIRED_ARTIFACTS = list(FALLBACK_STRICT_REQUIRED_ARTIFACTS)


def _registry_blocking_findings(registry: Any) -> list[Finding]:
    return [
        finding
        for finding in registry.findings
        if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}
    ]


def _check_required_artifacts_with_registry(root: Path, registry: Any) -> dict[str, Any]:
    checks = []
    for rel in registry.required_pre_code_artifacts:
        path = root / rel
        checks.append(
            {
                "artifact": rel,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    passed = all(item["exists"] and item["size_bytes"] > 0 for item in checks)
    passed = passed and not _registry_blocking_findings(registry)
    return {"ok": passed, "checks": checks, "registry": registry.metadata()}


def check_required_artifacts(root: Path) -> dict[str, Any]:
    """Compatibility readiness check used by early bootstrap tests."""

    registry = load_readiness_requirements(root, emit_fallback_finding=True)
    return _check_required_artifacts_with_registry(root, registry)


def build_readiness_result(root: Path) -> CommandResult:
    """Build the non-strict compatibility result for readiness-check."""

    registry = load_readiness_requirements(root, emit_fallback_finding=True)
    legacy_result = _check_required_artifacts_with_registry(root, registry)
    findings: list[Finding] = list(registry.findings)
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

    registry = load_readiness_requirements(root, emit_fallback_finding=True)
    findings: list[Finding] = list(registry.findings)
    artifact_checks: list[dict[str, Any]] = []

    for rel in registry.strict_required_artifacts:
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

    miasi_missing = [rel for rel in registry.required_miasi_artifacts if not (root / rel).exists()]
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
            "registry": registry.metadata(),
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
