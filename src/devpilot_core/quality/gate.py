from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity


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

    SUPPORTED_PROFILES = {"fast", "full"}

    def __init__(self, root: Path, *, options: QualityGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or QualityGateOptions()
        self.service = ApplicationService(self.root)

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
            "include_pytest": self.options.include_pytest,
            "pytest_timeout_seconds": self.options.pytest_timeout_seconds if self.options.include_pytest else None,
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
                    "The default profile is read-only and does not run pytest; use --include-pytest for an explicit regression subprocess.",
                    "The gate does not publish packages, deploy, write source files, call network services or use external APIs.",
                    "Optional --write-report is handled by the CLI and writes only under outputs/reports.",
                ],
            },
            findings=aggregated_findings or [Finding("QUALITY_GATE_PASS", "All configured quality subgates passed.", Severity.INFO, metadata={"profile": self.options.profile})],
        )

    def _subgates(self) -> list[QualitySubgate]:
        subgates = [
            QualitySubgate("readiness-strict", "Strict pre-code/readiness validation.", lambda: self.service.readiness(strict=True)),
            QualitySubgate("standards-status", "Local MIPSoftware/MIASI standards registry status.", self.service.standards_status),
            QualitySubgate("miasi-validate", "MIASI agent/tool/policy matrix structural validation.", lambda: self.service.miasi_validate(scope="all")),
            QualitySubgate("eval-harness-ready", "Evaluation harness fixture readiness without executing eval workdir mutations.", self._eval_harness_ready),
            QualitySubgate("app-contract", "ApplicationService v2 contract availability.", self.service.application_contract),
        ]
        if self.options.profile == "full":
            subgates.append(QualitySubgate("validation-gateway-all", "Unified docs/contracts validation gateway.", lambda: self.service.validation.gateway(scope="all")))
            subgates.append(QualitySubgate("visual-product-smoke", "Fase F visual product smoke gate in dry-run JSON mode.", self._visual_product_smoke))
        if self.options.include_pytest:
            subgates.append(QualitySubgate("pytest", "Explicit optional pytest regression subprocess.", self._pytest_run))
        return subgates

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
