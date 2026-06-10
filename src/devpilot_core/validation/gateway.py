from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.reports import build_report_id
from devpilot_core.schemas import BuiltinContractValidator, SchemaRegistry
from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry
from devpilot_core.validators.readiness import build_strict_readiness_result


@dataclass(frozen=True)
class GatewayStep:
    """One validation step orchestrated by ValidationGateway."""

    id: str
    result: CommandResult


class ValidationGateway:
    """Unified validation facade for deterministic DevPilot gates.

    FUNC-SPRINT-24 introduces a conservative facade over existing validators.
    It does not replace the underlying validators; it composes them and preserves
    their findings, severities and exit semantics. The initial scopes are:

    - `docs`: data-driven artifact profiles + strict readiness gate.
    - `contracts`: schema catalog + MIASI/workspace/providers/manifests.
    - `all`: docs + contracts.

    The gateway performs no mutation outside optional evidence reports handled
    by the CLI. It does not call external services, use API keys, execute agents,
    apply patches or run destructive commands.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def validate_docs(self) -> CommandResult:
        profile_result = ArtifactProfileRegistry(self.root).status()
        readiness_result = build_strict_readiness_result(self.root)
        return self._combine(
            command="validate docs",
            scope="docs",
            steps=[GatewayStep("artifact-profile-registry", profile_result), GatewayStep("readiness-strict", readiness_result)],
            message_ok="Documentation validation gateway passed.",
            message_block="Documentation validation gateway blocked.",
            notes=[
                "FUNC-SPRINT-24 keeps existing frontmatter/artifact/checklist/standards validators as source of truth.",
                "Artifact profiles are loaded from JSON with Python fallback during the migration window.",
            ],
        )

    def validate_contracts(self) -> CommandResult:
        schema_registry = SchemaRegistry(self.root).list()
        contracts = BuiltinContractValidator(self.root)
        results: list[GatewayStep] = [
            GatewayStep("schema-registry", schema_registry),
            GatewayStep("miasi-contracts", contracts.validate_miasi()),
            GatewayStep("workspace-contract", contracts.validate_workspace()),
            GatewayStep("provider-contract", contracts.validate_providers()),
        ]
        for manifest in self._phase_a_manifests():
            results.append(GatewayStep(f"manifest:{manifest.as_posix()}", contracts.validate_manifest(manifest)))
        return self._combine(
            command="validate contracts",
            scope="contracts",
            steps=results,
            message_ok="Contract validation gateway passed.",
            message_block="Contract validation gateway blocked.",
            notes=[
                "FUNC-SPRINT-24 routes structural contract checks through a single facade.",
                "Schema checks remain structural and do not replace business validators.",
            ],
        )

    def validate_all(self) -> CommandResult:
        docs_result = self.validate_docs()
        contracts_result = self.validate_contracts()
        return self._combine(
            command="validate all",
            scope="all",
            steps=[GatewayStep("docs", docs_result), GatewayStep("contracts", contracts_result)],
            message_ok="Validation gateway passed all configured groups.",
            message_block="Validation gateway blocked at least one configured group.",
            notes=[
                "FUNC-SPRINT-24 unifies docs and contracts validation without duplicating validator internals.",
                "Warnings are preserved as warnings and do not block by themselves.",
            ],
        )

    def validate_scope(self, scope: str) -> CommandResult:
        if scope == "docs":
            return self.validate_docs()
        if scope == "contracts":
            return self.validate_contracts()
        if scope == "all":
            return self.validate_all()
        finding = Finding(id="VALIDATION_GATEWAY_UNKNOWN_SCOPE", message=f"Unknown validation scope: {scope}", severity=Severity.ERROR, metadata={"scope": scope})
        return CommandResult(command=f"validate {scope}", ok=False, exit_code=ExitCode.ERROR, message="Validation gateway scope is unknown.", data={"summary": {"scope": scope}}, findings=[finding])

    def _phase_a_manifests(self) -> list[Path]:
        manifests: list[Path] = []
        for path in sorted((self.root / "docs").glob("functional_sprint_*.json")):
            parts = path.stem.split("_")
            try:
                number = int(parts[2]) if len(parts) >= 3 else -1
            except ValueError:
                continue
            if number >= 19:
                manifests.append(Path("docs") / path.name)
        return manifests

    def _combine(self, *, command: str, scope: str, steps: Iterable[GatewayStep], message_ok: str, message_block: str, notes: list[str]) -> CommandResult:
        step_list = list(steps)
        findings: list[Finding] = []
        details: list[dict[str, object]] = []
        for step in step_list:
            details.append({"id": step.id, "result": step.result.to_dict()})
            for finding in step.result.findings:
                metadata = dict(finding.metadata or {})
                metadata.setdefault("gateway_step", step.id)
                metadata.setdefault("source_command", step.result.command)
                findings.append(Finding(id=finding.id, message=finding.message, severity=finding.severity, path=finding.path, metadata=metadata))

        ok = all(step.result.ok for step in step_list)
        exit_code = self._exit_code_from_results(step.result for step in step_list)
        blocking_findings = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
        summary = {
            "scope": scope,
            "validations_total": len(step_list),
            "validations_passed": sum(1 for step in step_list if step.result.ok),
            "validations_failed": sum(1 for step in step_list if not step.result.ok),
            "findings_total": len(findings),
            "warnings_total": len(warnings),
            "blocking_findings_total": len(blocking_findings),
            "preliminary": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
        }
        return CommandResult(
            command=command,
            ok=ok,
            exit_code=exit_code,
            message=message_ok if ok else message_block,
            data={"summary": summary, "validations": details, "notes": notes},
            findings=findings,
        )

    @staticmethod
    def _exit_code_from_results(results: Iterable[CommandResult]) -> ExitCode:
        codes = {result.exit_code for result in results}
        if ExitCode.ERROR in codes:
            return ExitCode.ERROR
        if ExitCode.BLOCK in codes:
            return ExitCode.BLOCK
        if ExitCode.FAIL in codes:
            return ExitCode.FAIL
        return ExitCode.PASS
