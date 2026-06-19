from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.compliance.registry import CompliancePackRegistry, ComplianceRegistryOptions
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.schemas import SchemaRegistry


@dataclass(frozen=True)
class ComplianceRunOptions:
    """Options for running one local declarative compliance pack."""

    pack: str = "baseline"
    registry_path: str = ".devpilot/compliance/packs.json"
    schema_path: str = "docs/schemas/compliance_pack.schema.json"


class CompliancePackRunner:
    """Execute compliance packs by composing existing local gates only.

    The runner does not execute arbitrary commands declared in the pack. Each
    check references a small allowlist of internal DevPilot validators/gates. It
    uses PolicyEngine before running pack checks and returns explicit gaps per
    pack instead of replacing MIASI, PolicyEngine or the validation gateway.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.service = ApplicationService(self.root)

    def run(self, options: ComplianceRunOptions | None = None) -> CommandResult:
        options = options or ComplianceRunOptions()
        registry = CompliancePackRegistry(self.root, options=ComplianceRegistryOptions(registry_path=options.registry_path, schema_path=options.schema_path))
        validation = registry.validate()
        if not validation.ok:
            return CommandResult("compliance run", False, validation.exit_code, "Compliance run blocked by invalid registry.", data={"summary": {"pack_id": options.pack, "registry_valid": False, "preliminary": True}}, findings=validation.findings)
        pack = registry.get_pack(options.pack)
        if not pack:
            finding = Finding("COMPLIANCE_PACK_NOT_FOUND", "Requested compliance pack was not found.", Severity.BLOCK, path=options.registry_path, metadata={"pack_id": options.pack})
            return CommandResult("compliance run", False, ExitCode.BLOCK, "Compliance pack not found.", data={"summary": {"pack_id": options.pack, "registry_valid": True, "preliminary": True}}, findings=[finding])

        policy = PolicyEngine(self.root).evaluate(
            PolicyRequest(
                action="read",
                path=options.registry_path,
                dry_run=True,
                tool_id="compliance.run",
                subject=options.pack,
                actor="local-owner",
                metadata={"component": "CompliancePackRunner", "sprint": "FUNC-SPRINT-97", "policy_engine_required": True},
            )
        )
        if not policy.ok:
            return CommandResult("compliance run", False, policy.exit_code, "Compliance run blocked by PolicyEngine.", data={"summary": {"pack_id": options.pack, "policy_engine_used": True, "policy_allowed": False, "preliminary": True}}, findings=policy.findings)

        checks = pack.get("checks", []) or []
        check_results: list[dict[str, Any]] = []
        findings: list[Finding] = []
        declared_only = True
        for check in checks:
            check_id = str(check.get("check_id", "")).strip()
            runner_id = str(check.get("runner", "")).strip()
            required = bool(check.get("required", True))
            result = self._run_declared_runner(runner_id)
            if result is None:
                declared_only = False
                findings.append(Finding("COMPLIANCE_PACK_RUNNER_UNDECLARED_BLOCK", "Compliance run blocked an undeclared runner.", Severity.BLOCK, metadata={"check_id": check_id, "runner": runner_id, "pack_id": options.pack}))
                check_results.append({"check_id": check_id, "runner": runner_id, "ok": False, "required": required, "gaps": ["runner undeclared"]})
                continue
            blocking = [finding for finding in result.findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
            gaps = [finding.id for finding in blocking]
            if required and (not result.ok or blocking):
                findings.append(Finding("COMPLIANCE_CHECK_GAP", "Compliance check reported a required gap.", Severity.BLOCK, metadata={"check_id": check_id, "runner": runner_id, "source_command": result.command, "gaps": gaps}))
            check_results.append({
                "check_id": check_id,
                "runner": runner_id,
                "required": required,
                "ok": bool(result.ok and not blocking),
                "exit_code": int(result.exit_code),
                "source_command": result.command,
                "gaps": gaps,
                "summary": result.data.get("summary", {}) if isinstance(result.data, dict) else {},
            })

        blocking_findings = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        ok = not blocking_findings and declared_only
        summary = {
            "pack_id": options.pack,
            "pack_title": pack.get("title"),
            "profile": pack.get("profile"),
            "registry_valid": True,
            "packs_are_declarative": True,
            "declared_checks_only": declared_only,
            "policy_engine_used": True,
            "policy_engine_replaced": False,
            "checks_total": len(check_results),
            "checks_passed": sum(1 for check in check_results if check["ok"]),
            "checks_failed": sum(1 for check in check_results if not check["ok"]),
            "gaps_total": sum(len(check["gaps"]) for check in check_results),
            "blocking_findings_total": len(blocking_findings),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        if ok:
            findings.append(Finding("COMPLIANCE_PACK_PASS", "Compliance pack passed using existing declared DevPilot gates.", Severity.INFO, metadata={"pack_id": options.pack, "checks_total": len(check_results)}))
        return CommandResult(
            command="compliance run",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking_findings),
            message="Compliance pack passed." if ok else "Compliance pack failed or blocked.",
            data={"summary": summary, "pack": pack, "checks": check_results, "policy": policy.data},
            findings=findings,
        )

    def _run_declared_runner(self, runner_id: str) -> CommandResult | None:
        runners: dict[str, Callable[[], CommandResult]] = {
            "schema.registry.list": lambda: SchemaRegistry(self.root).list(),
            "validation.gateway.all": lambda: self.service.validation.gateway(scope="all"),
            "miasi.validate.all": lambda: self.service.miasi_validate(scope="all"),
            "readiness.strict": lambda: self.service.readiness(strict=True),
            "standards.status": self.service.standards_status,
        }
        runner = runners.get(runner_id)
        return runner() if runner else None


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS
