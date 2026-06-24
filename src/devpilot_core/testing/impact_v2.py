from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings

from .profiles_v2 import DEFAULT_V2_REGISTRY_PATH, DEFAULT_V2_SCHEMA_PATH, TestContractRegistryV2ValidationOptions, TestContractRegistryV2Validator

__test__ = False

_BROAD_WATCHED_PATHS = {"docs/audits", "docs/audits/"}
_RISK_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}
_CRITICALITY_RANK = {"P0": 4, "P1": 3, "P2": 2, "P3": 1}


@dataclass(frozen=True)
class TestImpactV2Options:
    __test__ = False

    registry_path: str | Path = DEFAULT_V2_REGISTRY_PATH
    schema_path: str | Path = DEFAULT_V2_SCHEMA_PATH
    changed_paths_file: str | Path | None = None
    changed_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class _HeuristicRule:
    id: str
    label: str
    prefixes: tuple[str, ...]
    contract_ids: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    criticalities: tuple[str, ...] = ()
    max_contracts: int | None = None
    tests: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()
    profiles: tuple[str, ...] = ()
    finding_id: str = "TEST_IMPACT_V2_HEURISTIC_APPLIED"


_RULES = (
    _HeuristicRule(
        id="policy-security",
        label="Policy/security-sensitive change",
        prefixes=("src/devpilot_core/policy", ".devpilot/policy", ".devpilot/miasi/policy_matrix", "docs/03_security"),
        contract_ids=("quality-gate-hardening", "test-contract-registry", "post-h-002-maturity-dashboard"),
        criticalities=("P0", "P1"),
        max_contracts=8,
        tests=("tests/test_policy_engine.py", "tests/test_security_readiness.py", "tests/test_miasi_registry.py", "tests/test_quality_gate.py"),
        commands=(
            "python -m pytest tests/test_policy_engine.py tests/test_security_readiness.py tests/test_miasi_registry.py tests/test_quality_gate.py -q",
            "python -m devpilot_core test-contracts validate-v2 --json",
            "python -m devpilot_core quality-gate run --profile hardening --json",
        ),
        profiles=("p0-critical", "security"),
    ),
    _HeuristicRule(
        id="schema-registry",
        label="Schema contract change",
        prefixes=("docs/schemas", "src/devpilot_core/schemas"),
        contract_ids=("schema-registry", "test-contract-registry", "quality-gate-hardening"),
        tests=("tests/test_schema_registry.py", "tests/test_schema_validator.py", "tests/test_contract_schemas.py"),
        commands=(
            "python -m pytest tests/test_schema_registry.py tests/test_schema_validator.py tests/test_contract_schemas.py -q",
            "python -m devpilot_core test-contracts validate-v2 --json",
        ),
        profiles=("p0-critical",),
    ),
    _HeuristicRule(
        id="cli-api-boundary",
        label="CLI/API/Application boundary change",
        prefixes=("src/devpilot_core/cli.py", "src/devpilot_core/application", "src/devpilot_core/interfaces/api", "docs/07_interfaces"),
        contract_ids=("test-impact-analyzer", "post-h-002-maturity-dashboard", "quality-gate-hardening"),
        tests=("tests/test_cli_core.py", "tests/test_application_services.py", "tests/test_api_contract.py", "tests/test_api_security.py"),
        commands=(
            "python -m pytest tests/test_cli_core.py tests/test_application_services.py tests/test_api_contract.py tests/test_api_security.py -q",
            "python -m devpilot_core test-contracts validate-v2 --json",
        ),
        profiles=("impact",),
    ),
    _HeuristicRule(
        id="agentic-runtime",
        label="Agentic/runtime governance change",
        prefixes=("src/devpilot_core/agents", "src/devpilot_core/multiagent", "src/devpilot_core/modeling", "src/devpilot_core/miasi", ".devpilot/miasi"),
        contract_ids=("quality-gate-hardening", "test-contract-registry"),
        tests=("tests/test_miasi_registry.py", "tests/test_quality_gate.py"),
        commands=(
            "python -m pytest tests/test_miasi_registry.py tests/test_quality_gate.py -q",
            "python -m devpilot_core miasi validate --json",
        ),
        profiles=("security", "impact"),
    ),
    _HeuristicRule(
        id="release-packaging",
        label="Release/packaging change",
        prefixes=("src/devpilot_core/release", "docs/release", "pyproject.toml", "package.json", "ui/web/package.json"),
        contract_ids=("schema-registry", "quality-gate-hardening", "test-contract-registry"),
        tests=("tests/test_release_manifest.py", "tests/test_release_sbom.py", "tests/test_release_verification.py", "tests/test_package_builder.py"),
        commands=(
            "python -m pytest tests/test_release_manifest.py tests/test_release_sbom.py tests/test_release_verification.py tests/test_package_builder.py -q",
            "python -m devpilot_core test-contracts profile --profile release --json",
        ),
        profiles=("release",),
    ),
)


class TestImpactAnalyzerV2:
    __test__ = False

    """Recommend local test plans from Test Contract Registry v2 impact metadata.

    POST-H-003-D keeps this analyzer read-only and non-executing. It validates
    the registry v2, crosses changed paths with contract watched paths, applies
    explicit safety heuristics for policy/security/schemas/CLI/API/release
    hotspots, and returns a deterministic test plan. It never invokes pytest,
    subprocesses, network calls or external APIs.
    """

    def __init__(self, root: Path, options: TestImpactV2Options | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or TestImpactV2Options()
        self.registry_path = self._resolve(self.options.registry_path)
        self.schema_path = self._resolve(self.options.schema_path)

    def analyze(self) -> CommandResult:
        findings: list[Finding] = []
        validator = TestContractRegistryV2Validator(
            self.root,
            TestContractRegistryV2ValidationOptions(registry_path=self.registry_path, schema_path=self.schema_path),
        )
        validation = validator.validate()
        findings.extend(validation.findings)
        if not validation.ok:
            return self._result(False, validation.exit_code, [], [], [], [], findings, {})

        registry = validation.data.get("registry", {}) if isinstance(validation.data, dict) else {}
        contracts = [item for item in registry.get("contracts", []) if isinstance(item, dict)]
        changed_paths = self._load_changed_paths(findings)
        if not changed_paths:
            findings.append(
                Finding(
                    id="TEST_IMPACT_V2_CHANGED_PATHS_REQUIRED",
                    message="Provide at least one changed path to run impact analysis v2.",
                    severity=Severity.BLOCK,
                )
            )
            return self._result(False, exit_code_for_findings(findings), [], [], [], [], findings, registry)

        matched_by_id: dict[str, dict[str, Any]] = {}
        unmatched: list[str] = []
        for changed in changed_paths:
            direct_matches = self._direct_matches(changed, contracts)
            heuristic_matches = self._heuristic_matches(changed, contracts, findings)
            combined = direct_matches + [item for item in heuristic_matches if item["contract"]["contract_id"] not in {match["contract"]["contract_id"] for match in direct_matches}]
            if not combined:
                unmatched.append(changed)
                continue
            for match in combined:
                contract = match["contract"]
                cid = str(contract.get("contract_id"))
                entry = matched_by_id.setdefault(
                    cid,
                    {
                        "contract": contract,
                        "matched_paths": [],
                        "match_reasons": [],
                        "priority_score": self._priority_score(contract),
                    },
                )
                if changed not in entry["matched_paths"]:
                    entry["matched_paths"].append(changed)
                for reason in match["reasons"]:
                    if reason not in entry["match_reasons"]:
                        entry["match_reasons"].append(reason)

        recommendations = self._heuristic_recommendations(changed_paths)
        recommended_tests = self._unique(
            [path for entry in matched_by_id.values() for path in self._clean_list(entry["contract"].get("test_files", []))]
            + [item for recommendation in recommendations for item in recommendation["tests"] if self._path_exists(item)]
        )
        recommended_commands = self._unique(
            [cmd for entry in matched_by_id.values() for cmd in self._clean_list(entry["contract"].get("recommended_commands", []))]
            + [cmd for recommendation in recommendations for cmd in recommendation["commands"]]
            + ["python -m devpilot_core test-contracts validate-v2 --json"]
        )
        recommended_profiles = self._unique([profile for recommendation in recommendations for profile in recommendation["profiles"]])
        if not recommended_profiles and matched_by_id:
            recommended_profiles = self._derive_profiles([entry["contract"] for entry in matched_by_id.values()])

        if unmatched:
            findings.append(
                Finding(
                    id="TEST_IMPACT_V2_UNMATCHED_PATHS_REVIEW_REQUIRED",
                    message="Some changed paths did not map to v2 contracts or heuristics; review is required before assuming coverage.",
                    severity=Severity.WARNING,
                    metadata={"unmatched_paths": unmatched},
                )
            )
        if matched_by_id or recommendations:
            findings.append(
                Finding(
                    id="TEST_IMPACT_V2_ANALYSIS_PASS",
                    message="Test Impact Analyzer v2 produced a local non-executing test plan.",
                    severity=Severity.INFO,
                    metadata={
                        "changed_paths_total": len(changed_paths),
                        "matched_contracts_total": len(matched_by_id),
                        "heuristic_recommendations_total": len(recommendations),
                        "tests_executed": False,
                    },
                )
            )
        else:
            findings.append(
                Finding(
                    id="TEST_IMPACT_V2_NO_MATCHES",
                    message="No v2 contract matched the changed paths; run manual review and consider p0-critical profile.",
                    severity=Severity.WARNING,
                )
            )
            recommended_commands = self._unique(recommended_commands + ["python -m devpilot_core test-contracts profile --profile p0-critical --json"])
            recommended_profiles = self._unique(recommended_profiles + ["p0-critical"])

        ok = not any(f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for f in findings)
        return self._result(
            ok,
            ExitCode.PASS if ok else exit_code_for_findings(findings),
            changed_paths,
            list(matched_by_id.values()),
            recommendations,
            recommended_profiles,
            findings,
            registry,
            recommended_tests=recommended_tests,
            recommended_commands=recommended_commands,
            unmatched=unmatched,
        )

    def _direct_matches(self, changed: str, contracts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        for contract in contracts:
            reasons: list[str] = []
            candidates = (
                [("test_files", item) for item in self._clean_list(contract.get("test_files", []))]
                + [("watched_paths", item) for item in self._clean_list(contract.get("watched_paths", []))]
                + [("validates", item) for item in self._clean_list(contract.get("validates", []))]
            )
            for field, candidate in candidates:
                if self._path_matches(changed, candidate):
                    reasons.append(f"direct:{field}:{candidate}")
            if reasons:
                matches.append({"contract": contract, "reasons": sorted(set(reasons))})
        return matches

    def _heuristic_matches(self, changed: str, contracts: list[dict[str, Any]], findings: list[Finding]) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        for rule in _RULES:
            if not any(changed == prefix or changed.startswith(prefix.rstrip("/") + "/") or changed.startswith(prefix.rstrip("/")) for prefix in rule.prefixes):
                continue
            selected: list[dict[str, Any]] = []
            for contract in contracts:
                if contract.get("contract_id") in rule.contract_ids:
                    selected.append(contract)
                elif rule.domains and contract.get("domain") in rule.domains:
                    selected.append(contract)
                elif rule.criticalities and contract.get("criticality") in rule.criticalities and len(selected) < (rule.max_contracts or 999):
                    selected.append(contract)
            selected = self._unique_contracts(selected)
            for contract in selected[: rule.max_contracts or len(selected)]:
                matches.append({"contract": contract, "reasons": [f"heuristic:{rule.id}"]})
            findings.append(
                Finding(
                    id=rule.finding_id,
                    message=f"Applied Test Impact Analyzer v2 heuristic: {rule.label}.",
                    severity=Severity.INFO,
                    metadata={"rule_id": rule.id, "changed_path": changed, "contracts_selected": len(selected[: rule.max_contracts or len(selected)])},
                )
            )
        return matches

    def _heuristic_recommendations(self, changed_paths: list[str]) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []
        seen: set[str] = set()
        for changed in changed_paths:
            for rule in _RULES:
                if any(changed == prefix or changed.startswith(prefix.rstrip("/") + "/") or changed.startswith(prefix.rstrip("/")) for prefix in rule.prefixes):
                    if rule.id in seen:
                        continue
                    seen.add(rule.id)
                    recommendations.append(
                        {
                            "rule_id": rule.id,
                            "label": rule.label,
                            "tests": [test for test in rule.tests if self._path_exists(test)],
                            "commands": list(rule.commands),
                            "profiles": list(rule.profiles),
                        }
                    )
        return recommendations

    def _result(
        self,
        ok: bool,
        exit_code: ExitCode,
        changed_paths: list[str],
        matched_entries: list[dict[str, Any]],
        heuristic_recommendations: list[dict[str, Any]],
        recommended_profiles: list[str],
        findings: list[Finding],
        registry: dict[str, Any],
        *,
        recommended_tests: list[str] | None = None,
        recommended_commands: list[str] | None = None,
        unmatched: list[str] | None = None,
    ) -> CommandResult:
        recommended_tests = recommended_tests or []
        recommended_commands = recommended_commands or []
        unmatched = unmatched or []
        sorted_entries = sorted(matched_entries, key=lambda item: (-int(item.get("priority_score", 0)), str(item["contract"].get("contract_id", ""))))
        matched_contracts = [
            {
                "contract_id": entry["contract"].get("contract_id"),
                "domain": entry["contract"].get("domain"),
                "criticality": entry["contract"].get("criticality"),
                "risk_level": entry["contract"].get("risk_level"),
                "test_type": entry["contract"].get("test_type"),
                "matched_paths": entry.get("matched_paths", []),
                "match_reasons": entry.get("match_reasons", []),
                "recommended_commands": self._clean_list(entry["contract"].get("recommended_commands", [])),
                "test_files": self._clean_list(entry["contract"].get("test_files", [])),
                "priority_score": entry.get("priority_score", 0),
            }
            for entry in sorted_entries
        ]
        selected_contracts = [entry["contract"] for entry in sorted_entries]
        summary = {
            "registry_path": self.relative(self.registry_path),
            "schema_path": self.relative(self.schema_path),
            "changed_paths_total": len(changed_paths),
            "contracts_total": len([item for item in registry.get("contracts", []) if isinstance(item, dict)]) if isinstance(registry, dict) else 0,
            "matched_contracts_total": len(matched_contracts),
            "p0_selected_total": sum(1 for item in selected_contracts if item.get("criticality") == "P0"),
            "p1_selected_total": sum(1 for item in selected_contracts if item.get("criticality") == "P1"),
            "heuristic_recommendations_total": len(heuristic_recommendations),
            "recommended_tests_total": len(recommended_tests),
            "recommended_commands_total": len(recommended_commands),
            "recommended_profiles": recommended_profiles,
            "unmatched_paths_total": len(unmatched),
            "tests_executed": False,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        return CommandResult(
            command="test-impact analyze-v2",
            ok=ok,
            exit_code=exit_code,
            message=("Test Impact Analyzer v2 completed without executing tests." if ok else "Test Impact Analyzer v2 failed or requires blocking review."),
            data={
                "summary": summary,
                "changed_paths": changed_paths,
                "matched_contracts": matched_contracts,
                "heuristic_recommendations": heuristic_recommendations,
                "unmatched_paths": unmatched,
                "recommended_tests": recommended_tests,
                "recommended_commands": recommended_commands,
                "execution_plan": {
                    "tests_executed": False,
                    "operator_must_run_commands_manually": True,
                    "recommended_profiles": recommended_profiles,
                    "commands": recommended_commands,
                },
            },
            findings=findings,
        )

    def _load_changed_paths(self, findings: list[Finding]) -> list[str]:
        items = [self._normalize(item) for item in self.options.changed_paths if self._normalize(item)]
        if self.options.changed_paths_file:
            file_path = self._resolve(self.options.changed_paths_file)
            if not file_path.exists():
                findings.append(Finding("TEST_IMPACT_V2_CHANGED_PATHS_FILE_MISSING", "Changed paths file does not exist.", Severity.BLOCK, path=self.relative(file_path)))
            else:
                items.extend(self._normalize(line) for line in file_path.read_text(encoding="utf-8").splitlines() if self._normalize(line))
        return self._unique(items)

    def _path_matches(self, changed: str, candidate: str) -> bool:
        token = self._normalize(candidate).rstrip("*")
        if not token:
            return False
        if token in _BROAD_WATCHED_PATHS:
            return changed == token.rstrip("/")
        stripped = token.rstrip("/")
        if changed == stripped or changed == token:
            return True
        if token.endswith("/") and changed.startswith(token):
            return True
        if changed.startswith(stripped + "/"):
            return True
        if stripped.startswith(changed.rstrip("/") + "/"):
            return True
        return False

    def _derive_profiles(self, contracts: list[dict[str, Any]]) -> list[str]:
        profiles: list[str] = []
        if any(item.get("criticality") == "P0" for item in contracts):
            profiles.append("p0-critical")
        if any(item.get("risk_level") in {"critical", "high"} for item in contracts):
            profiles.append("security")
        if any(item.get("required_for_release") is True or item.get("execution_profile") == "release" for item in contracts):
            profiles.append("release")
        if any(item.get("execution_profile") == "impact" for item in contracts):
            profiles.append("impact")
        if any(item.get("domain") == "documentation.historical" for item in contracts):
            profiles.append("docs-historical")
        return self._unique(profiles)

    def _priority_score(self, contract: dict[str, Any]) -> int:
        return (_CRITICALITY_RANK.get(str(contract.get("criticality")), 0) * 10) + _RISK_RANK.get(str(contract.get("risk_level")), 0)

    def _clean_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip().replace("\\", "/") for item in value if str(item).strip()]

    def _unique(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        output: list[str] = []
        for item in items:
            if item and item not in seen:
                seen.add(item)
                output.append(item)
        return output

    def _unique_contracts(self, contracts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        output: list[dict[str, Any]] = []
        for contract in contracts:
            cid = str(contract.get("contract_id", ""))
            if cid and cid not in seen:
                seen.add(cid)
                output.append(contract)
        return output

    def _path_exists(self, value: str) -> bool:
        return (self.root / value).exists()

    def _normalize(self, value: str | Path) -> str:
        return str(value).strip().replace("\\", "/").rstrip("/")

    def _resolve(self, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = self.root / path
        return path.resolve()

    def relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()
