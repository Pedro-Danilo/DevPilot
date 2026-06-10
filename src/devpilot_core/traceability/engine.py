from __future__ import annotations

from pathlib import Path
from typing import Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.traceability.extractors import MarkdownTraceabilityExtractor
from devpilot_core.traceability.rules import TraceabilityCoverage, build_coverage


class TraceabilityEngine:
    """Executable SDLC traceability engine for FUNC-SPRINT-26.

    The engine builds on the Sprint 25 conservative extractor. It derives only
    explicit relationships found in local SDLC artifacts, computes coverage and
    emits actionable findings. It does not use LLMs, network calls or mutation.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.extractor = MarkdownTraceabilityExtractor(self.root)

    def validate(self, *, targets: Iterable[str | Path] | None = None) -> CommandResult:
        """Validate explicit traceability gaps without blocking on warnings."""

        scan_result = self.extractor.scan(targets=targets)
        if not scan_result.ok:
            return scan_result
        coverage = self._coverage_from_scan(scan_result)
        findings = [
            Finding(
                id="TRACEABILITY_VALIDATE_PASS",
                message="Traceability validation completed with non-blocking gap findings.",
                severity=Severity.INFO,
                metadata={
                    "requirements_total": coverage.summary()["requirements_total"],
                    "gaps_total": coverage.summary()["gaps_total"],
                    "blocking_findings_total": coverage.summary()["blocking_findings_total"],
                },
            ),
            *coverage.gaps,
        ]
        exit_code = exit_code_for_findings(findings)
        return CommandResult(
            command="traceability validate",
            ok=exit_code == ExitCode.PASS,
            exit_code=exit_code,
            message="Traceability validation completed.",
            data=self._base_data(scan_result, coverage, mode="validate"),
            findings=findings,
        )

    def coverage(self, *, targets: Iterable[str | Path] | None = None) -> CommandResult:
        """Return coverage metrics for explicit traceability evidence."""

        scan_result = self.extractor.scan(targets=targets)
        if not scan_result.ok:
            return scan_result
        coverage = self._coverage_from_scan(scan_result)
        summary = coverage.summary()
        return CommandResult(
            command="traceability coverage",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Traceability coverage metrics generated.",
            data={
                "summary": {
                    **summary,
                    "mode": "coverage",
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                },
                "coverage": coverage.to_dict(),
                "notes": _engine_notes(),
            },
            findings=[
                Finding(
                    id="TRACEABILITY_COVERAGE_PASS",
                    message="Traceability coverage metrics generated from explicit local evidence.",
                    severity=Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def report(self, *, targets: Iterable[str | Path] | None = None) -> CommandResult:
        """Build the consolidated traceability report payload."""

        scan_result = self.extractor.scan(targets=targets)
        if not scan_result.ok:
            return scan_result
        coverage = self._coverage_from_scan(scan_result)
        data = self._base_data(scan_result, coverage, mode="report")
        data["report"] = {
            "title": "FUNC-SPRINT-26 Traceability Report",
            "requirements": coverage.to_dict()["requirements"],
            "links": coverage.to_dict()["links"],
            "gaps": coverage.to_dict()["gaps"],
        }
        return CommandResult(
            command="traceability report",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Traceability report generated.",
            data=data,
            findings=[
                Finding(
                    id="TRACEABILITY_REPORT_PASS",
                    message="Traceability report generated from explicit local evidence.",
                    severity=Severity.INFO,
                    metadata=coverage.summary(),
                ),
                *coverage.gaps,
            ],
        )

    def architecture_drift(self) -> CommandResult:
        """Run the FUNC-SPRINT-27 architecture/code drift detector."""

        from devpilot_core.traceability.architecture_drift import ArchitectureDriftDetector

        return ArchitectureDriftDetector(self.root).detect()

    def _coverage_from_scan(self, scan_result: CommandResult) -> TraceabilityCoverage:
        source_paths = scan_result.data.get("source_paths", []) if scan_result.data else []
        return build_coverage(self.root, source_paths)

    def _base_data(self, scan_result: CommandResult, coverage: TraceabilityCoverage, *, mode: str) -> dict[str, object]:
        summary = coverage.summary()
        return {
            "summary": {
                **summary,
                "mode": mode,
                "scan_entities_total": (scan_result.data or {}).get("summary", {}).get("entities_total", 0),
                "scan_unique_entities_total": (scan_result.data or {}).get("summary", {}).get("unique_entities_total", 0),
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
            },
            "scan_summary": (scan_result.data or {}).get("summary", {}),
            "source_paths": (scan_result.data or {}).get("source_paths", []),
            "coverage": coverage.to_dict(),
            "notes": _engine_notes(),
        }


def _engine_notes() -> list[str]:
    return [
        "FUNC-SPRINT-26 implements explicit traceability coverage, not semantic inference.",
        "Gap findings are warnings in this first engine version and do not block by themselves.",
        "The engine is local-only, deterministic and read-only.",
    ]
