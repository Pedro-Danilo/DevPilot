from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator

DEFAULT_V2_REGISTRY_PATH = Path(".devpilot/testing/test_contract_registry_v2.json")
DEFAULT_V2_SCHEMA_PATH = Path("docs/schemas/test_contract_registry_v2.schema.json")
__test__ = False

_SECURITY_DOMAINS = {
    "governance.policy",
    "governance.miasi",
    "security.approval",
    "security.guards",
    "security.rbac",
    "quality.gate",
}

_PROFILE_IDS = {"p0-critical", "security", "release", "impact", "docs-historical"}
_DANGEROUS_SHELL_TOKENS = ("&&", "||", ";", "|", ">", "<", "`", "$(", "curl ", "wget ", "powershell", "pwsh", "cmd.exe")
_ALLOWED_COMMAND_PREFIXES = ("python -m pytest ", "python -m devpilot_core ", "npm --prefix ui/web test")


@dataclass(frozen=True)
class TestContractRegistryV2ValidationOptions:
    __test__ = False

    registry_path: str | Path = DEFAULT_V2_REGISTRY_PATH
    schema_path: str | Path = DEFAULT_V2_SCHEMA_PATH


class TestContractRegistryV2Validator:
    __test__ = False

    """Validate Test Contract Registry v2 without executing tests.

    POST-H-003-C deliberately separates registry validation and profile
    selection from test execution. The validator reads local JSON, checks the
    v2 schema, validates semantic safety constraints, verifies path existence
    for test files and watched paths, and inspects recommended commands as data
    only. It never shells out and never mutates source files.
    """

    def __init__(self, root: Path, options: TestContractRegistryV2ValidationOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or TestContractRegistryV2ValidationOptions()
        self.registry_path = self._resolve(self.options.registry_path)
        self.schema_path = self._resolve(self.options.schema_path)

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        schema_result = SchemaValidator(self.root).validate(schema=self.schema_path, instance=self.registry_path)
        findings.extend(schema_result.findings)
        if not schema_result.ok:
            return self._result(False, schema_result.exit_code, {}, findings)

        registry = self._load_registry(findings)
        if registry is None:
            return self._result(False, self._exit_code(findings), {}, findings)

        contracts = [item for item in registry.get("contracts", []) if isinstance(item, dict)]
        profiles = [item for item in registry.get("profiles", []) if isinstance(item, dict)]
        findings.extend(self._semantic_findings(registry, contracts, profiles))

        ok = not any(f.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for f in findings)
        if ok:
            findings.append(
                Finding(
                    id="TEST_CONTRACT_REGISTRY_V2_VALIDATION_PASS",
                    message="Test Contract Registry v2 passed schema and semantic validation without executing tests.",
                    severity=Severity.INFO,
                    metadata={
                        "contracts_total": len(contracts),
                        "profiles_total": len(profiles),
                        "tests_executed": False,
                        "network_used": False,
                        "external_api_used": False,
                        "mutations_performed": False,
                    },
                )
            )
        return self._result(ok, ExitCode.PASS if ok else self._exit_code(findings), registry, findings)

    def profile(self, profile_id: str) -> CommandResult:
        validation = self.validate()
        registry = validation.data.get("registry", {}) if isinstance(validation.data, dict) else {}
        contracts = [item for item in registry.get("contracts", []) if isinstance(item, dict)]
        profile_key = str(profile_id).strip()
        findings = list(validation.findings)

        if profile_key not in _PROFILE_IDS:
            findings.append(
                Finding(
                    id="TEST_CONTRACT_REGISTRY_V2_UNKNOWN_PROFILE",
                    message="Requested Test Contract Registry v2 profile is not configured.",
                    severity=Severity.BLOCK,
                    metadata={"profile": profile_key, "known_profiles": sorted(_PROFILE_IDS)},
                )
            )
            return self._profile_result(False, self._exit_code(findings), profile_key, [], findings, registry)

        if not validation.ok:
            return self._profile_result(False, validation.exit_code, profile_key, [], findings, registry)

        selected = [contract for contract in contracts if self._matches_profile(contract, profile_key)]
        if not selected:
            findings.append(
                Finding(
                    id="TEST_CONTRACT_REGISTRY_V2_PROFILE_EMPTY",
                    message="Requested Test Contract Registry v2 profile selected no contracts.",
                    severity=Severity.FAIL,
                    metadata={"profile": profile_key},
                )
            )
        else:
            findings.append(
                Finding(
                    id="TEST_CONTRACT_REGISTRY_V2_PROFILE_SELECTED",
                    message="Test Contract Registry v2 profile selected local contracts without executing tests.",
                    severity=Severity.INFO,
                    metadata={"profile": profile_key, "contracts_selected": len(selected)},
                )
            )
        ok = not any(f.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for f in findings)
        return self._profile_result(ok, ExitCode.PASS if ok else self._exit_code(findings), profile_key, selected, findings, registry)

    def _semantic_findings(self, registry: dict[str, Any], contracts: list[dict[str, Any]], profiles: list[dict[str, Any]]) -> list[Finding]:
        findings: list[Finding] = []
        ids: set[str] = set()
        missing_paths = 0
        unsafe_commands = 0
        safety_exceptions = 0
        needs_review = 0
        p0_total = 0

        if registry.get("created_by") not in {"POST-H-003-B", "POST-H-003-C"}:
            findings.append(
                Finding(
                    id="TEST_CONTRACT_REGISTRY_V2_CREATED_BY_TRANSITIONAL",
                    message="Registry v2 should be produced by POST-H-003-B/C during validator rollout.",
                    severity=Severity.WARNING,
                    metadata={"created_by": registry.get("created_by")},
                )
            )

        profile_ids = {str(profile.get("profile_id", "")).strip() for profile in profiles}
        missing_profiles = _PROFILE_IDS - profile_ids
        if missing_profiles:
            findings.append(
                Finding(
                    id="TEST_CONTRACT_REGISTRY_V2_PROFILE_MISSING",
                    message="Registry v2 is missing one or more required execution profiles.",
                    severity=Severity.FAIL,
                    metadata={"missing_profiles": sorted(missing_profiles)},
                )
            )

        for profile in profiles:
            if profile.get("network_allowed") is not False or profile.get("external_api_allowed") is not False:
                findings.append(
                    Finding(
                        id="TEST_CONTRACT_REGISTRY_V2_PROFILE_UNSAFE_NETWORK",
                        message="Registry v2 profiles must remain local-only in POST-H-003-C.",
                        severity=Severity.BLOCK,
                        metadata={"profile_id": profile.get("profile_id")},
                    )
                )

        for contract in contracts:
            cid = str(contract.get("contract_id", "")).strip()
            if cid in ids:
                findings.append(Finding("TEST_CONTRACT_REGISTRY_V2_DUPLICATE_ID", "Duplicate v2 contract id.", Severity.ERROR, metadata={"contract_id": cid}))
            ids.add(cid)

            if contract.get("criticality") == "P0":
                p0_total += 1
            if contract.get("classification_status") == "needs-review":
                needs_review += 1
                findings.append(
                    Finding(
                        id="TEST_CONTRACT_REGISTRY_V2_CLASSIFICATION_NEEDS_REVIEW",
                        message="Migrated v2 contract still requires classification review.",
                        severity=Severity.WARNING,
                        metadata={"contract_id": cid, "domain": contract.get("domain"), "owner": contract.get("owner")},
                    )
                )

            for field in ("test_files", "watched_paths"):
                for path_value in self._clean_list(contract.get(field, [])):
                    if not self._path_exists(path_value):
                        missing_paths += 1
                        findings.append(
                            Finding(
                                id="TEST_CONTRACT_REGISTRY_V2_PATH_MISSING",
                                message=f"Contract declares a {field} entry that does not exist locally.",
                                severity=Severity.BLOCK if field == "test_files" else Severity.FAIL,
                                path=path_value,
                                metadata={"contract_id": cid, "field": field},
                            )
                        )

            for command in self._clean_list(contract.get("recommended_commands", [])):
                if not self._command_safe(command):
                    unsafe_commands += 1
                    findings.append(
                        Finding(
                            id="TEST_CONTRACT_REGISTRY_V2_UNSAFE_RECOMMENDED_COMMAND",
                            message="Recommended command is outside the local allowlist or contains shell control tokens.",
                            severity=Severity.BLOCK,
                            metadata={"contract_id": cid, "command": command},
                        )
                    )

            safety_sensitive = any(bool(contract.get(flag)) for flag in ("network_allowed", "external_api_allowed", "mutations_allowed", "source_mutations_allowed"))
            if safety_sensitive:
                safety_exceptions += 1
                if not isinstance(contract.get("safety_exception"), dict):
                    findings.append(Finding("TEST_CONTRACT_REGISTRY_V2_SAFETY_EXCEPTION_MISSING", "Safety-sensitive contract must declare safety_exception.", Severity.BLOCK, metadata={"contract_id": cid}))
                if contract.get("requires_human_approval") is not True:
                    findings.append(Finding("TEST_CONTRACT_REGISTRY_V2_HUMAN_APPROVAL_MISSING", "Safety-sensitive contract must require human approval.", Severity.BLOCK, metadata={"contract_id": cid}))
                if contract.get("execution_profile") not in {"manual", "release"}:
                    findings.append(Finding("TEST_CONTRACT_REGISTRY_V2_UNSAFE_EXECUTION_PROFILE", "Safety-sensitive contract must use manual or release execution profile.", Severity.BLOCK, metadata={"contract_id": cid, "execution_profile": contract.get("execution_profile")}))

            if contract.get("network_allowed") is True or contract.get("external_api_allowed") is True:
                findings.append(
                    Finding(
                        id="TEST_CONTRACT_REGISTRY_V2_NETWORK_DENIED_POST_H_003_C",
                        message="POST-H-003-C does not allow network or external API test contracts.",
                        severity=Severity.BLOCK,
                        metadata={"contract_id": cid},
                    )
                )

            if contract.get("criticality") == contract.get("risk_level"):
                findings.append(
                    Finding(
                        id="TEST_CONTRACT_REGISTRY_V2_CRITICALITY_RISK_COLLAPSED",
                        message="Criticality and risk_level must remain separate concepts.",
                        severity=Severity.FAIL,
                        metadata={"contract_id": cid},
                    )
                )

        if p0_total == 0:
            findings.append(Finding("TEST_CONTRACT_REGISTRY_V2_NO_P0_CONTRACTS", "Registry v2 must contain at least one P0 contract.", Severity.BLOCK))

        findings.append(
            Finding(
                id="TEST_CONTRACT_REGISTRY_V2_VALIDATION_SUMMARY",
                message="Test Contract Registry v2 semantic validation completed locally.",
                severity=Severity.INFO,
                metadata={
                    "contracts_total": len(contracts),
                    "p0_total": p0_total,
                    "needs_review_total": needs_review,
                    "missing_paths_total": missing_paths,
                    "unsafe_commands_total": unsafe_commands,
                    "safety_exceptions_total": safety_exceptions,
                },
            )
        )
        return findings

    def _matches_profile(self, contract: dict[str, Any], profile_id: str) -> bool:
        if profile_id == "p0-critical":
            return contract.get("criticality") == "P0"
        if profile_id == "security":
            return bool(contract.get("required_for_security_gate")) or contract.get("domain") in _SECURITY_DOMAINS or contract.get("risk_level") in {"critical", "high"}
        if profile_id == "release":
            return bool(contract.get("required_for_release")) or contract.get("execution_profile") == "release"
        if profile_id == "impact":
            return contract.get("execution_profile") == "impact"
        if profile_id == "docs-historical":
            return contract.get("domain") == "documentation.historical" or contract.get("test_type") == "documentation"
        return False

    def _profile_result(self, ok: bool, exit_code: ExitCode, profile: str, selected: list[dict[str, Any]], findings: list[Finding], registry: dict[str, Any]) -> CommandResult:
        commands = self._unique_commands(selected)
        summary = {
            "profile": profile,
            "registry_path": self.relative(self.registry_path),
            "schema_path": self.relative(self.schema_path),
            "contracts_total": len([item for item in registry.get("contracts", []) if isinstance(item, dict)]) if isinstance(registry, dict) else 0,
            "contracts_selected": len(selected),
            "recommended_commands_total": len(commands),
            "tests_executed": False,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        return CommandResult(
            command="test-contracts profile",
            ok=ok,
            exit_code=exit_code,
            message="Test Contract Registry v2 profile selected." if ok else "Test Contract Registry v2 profile selection failed.",
            data={
                "summary": summary,
                "contracts": selected,
                "recommended_commands": commands,
                "notes": [
                    "Profiles select contracts and recommended commands only; they do not execute pytest or subprocesses.",
                    "Use tests.run or explicit pytest commands only after human/operator review.",
                ],
            },
            findings=findings,
        )

    def _result(self, ok: bool, exit_code: ExitCode, registry: dict[str, Any], findings: list[Finding]) -> CommandResult:
        contracts = [item for item in registry.get("contracts", []) if isinstance(item, dict)] if isinstance(registry, dict) else []
        profiles = [item for item in registry.get("profiles", []) if isinstance(item, dict)] if isinstance(registry, dict) else []
        summary = {
            "registry_path": self.relative(self.registry_path),
            "schema_path": self.relative(self.schema_path),
            "contracts_total": len(contracts),
            "profiles_total": len(profiles),
            "p0_contracts_total": sum(1 for contract in contracts if contract.get("criticality") == "P0"),
            "needs_review_total": sum(1 for contract in contracts if contract.get("classification_status") == "needs-review"),
            "network_allowed_total": sum(1 for contract in contracts if contract.get("network_allowed") is True),
            "external_api_allowed_total": sum(1 for contract in contracts if contract.get("external_api_allowed") is True),
            "mutations_allowed_total": sum(1 for contract in contracts if contract.get("mutations_allowed") is True),
            "source_mutations_allowed_total": sum(1 for contract in contracts if contract.get("source_mutations_allowed") is True),
            "tests_executed": False,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        return CommandResult(
            command="test-contracts validate-v2",
            ok=ok,
            exit_code=exit_code,
            message="Test Contract Registry v2 validation passed." if ok else "Test Contract Registry v2 validation failed.",
            data={"summary": summary, "registry": registry},
            findings=findings,
        )

    def _load_registry(self, findings: list[Finding]) -> dict[str, Any] | None:
        try:
            payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            findings.append(Finding("TEST_CONTRACT_REGISTRY_V2_MISSING", "Test Contract Registry v2 file is missing.", Severity.BLOCK, path=self.relative(self.registry_path)))
            return None
        except json.JSONDecodeError as exc:
            findings.append(Finding("TEST_CONTRACT_REGISTRY_V2_INVALID_JSON", "Test Contract Registry v2 file is invalid JSON.", Severity.ERROR, path=self.relative(self.registry_path), metadata={"error": str(exc)}))
            return None
        if not isinstance(payload, dict):
            findings.append(Finding("TEST_CONTRACT_REGISTRY_V2_INVALID_TYPE", "Test Contract Registry v2 must be a JSON object.", Severity.ERROR, path=self.relative(self.registry_path)))
            return None
        return payload

    def _path_exists(self, path_value: str) -> bool:
        path = self.root / path_value
        return path.exists()

    def _command_safe(self, command: str) -> bool:
        lowered = command.lower()
        if any(token in lowered for token in _DANGEROUS_SHELL_TOKENS):
            return False
        return command.startswith(_ALLOWED_COMMAND_PREFIXES)

    def _unique_commands(self, contracts: list[dict[str, Any]]) -> list[str]:
        seen: set[str] = set()
        commands: list[str] = []
        for contract in contracts:
            for command in self._clean_list(contract.get("recommended_commands", [])):
                if command not in seen:
                    seen.add(command)
                    commands.append(command)
        return commands

    def _clean_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip().replace("\\", "/") for item in value if str(item).strip()]

    def _resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else (self.root / candidate).resolve()

    def relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    def _exit_code(self, findings: list[Finding]) -> ExitCode:
        severities = {finding.severity for finding in findings}
        if Severity.ERROR in severities:
            return ExitCode.ERROR
        if Severity.BLOCK in severities:
            return ExitCode.BLOCK
        if Severity.FAIL in severities:
            return ExitCode.FAIL
        return ExitCode.PASS
