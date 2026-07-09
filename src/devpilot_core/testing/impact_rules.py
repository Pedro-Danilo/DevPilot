from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.schemas import SchemaValidator

from .profiles_v2 import DEFAULT_V2_REGISTRY_PATH, DEFAULT_V2_SCHEMA_PATH, TestContractRegistryV2ValidationOptions, TestContractRegistryV2Validator

__test__ = False

POST_H_029_B_CREATED_BY = "POST-H-029-B"
TEST_IMPACT_RULES_COMMAND = "test-impact rules"
DEFAULT_TEST_IMPACT_RULES_PATH = Path(".devpilot/testing/test_impact_rules.json")
DEFAULT_TEST_IMPACT_RULES_SCHEMA = Path("docs/schemas/test_impact_rule_registry.schema.json")
DEFAULT_TEST_PROFILE_TAXONOMY_PATH = Path(".devpilot/testing/test_profile_taxonomy.json")
DEFAULT_TEST_PROFILE_TAXONOMY_SCHEMA = Path("docs/schemas/test_profile_taxonomy.schema.json")
DEFAULT_TEST_IMPACT_RULES_REPORT_JSON = Path("outputs/reports/test_impact_rule_registry_report.json")
DEFAULT_TEST_IMPACT_RULES_REPORT_MD = Path("outputs/reports/test_impact_rule_registry_report.md")

_REQUIRED_RULE_IDS = {
    "policy-security",
    "schema-contracts",
    "project-state-docs-governance",
    "cli-application-boundary",
    "ui-api-local-hardening",
    "release-packaging-rc",
    "runtime-observability-workspace",
    "agentic-rag-governance",
    "connectors-plugins-sandbox",
    "remote-enterprise-design",
    "production-readiness-claims",
    "testing-infra",
}
_DANGEROUS_SHELL_TOKENS = ("&&", "||", ";", "|", ">", "<", "`", "$(", "curl ", "wget ", "powershell", "pwsh", "cmd.exe")
_ALLOWED_COMMAND_PREFIXES = (
    "python -m pytest ",
    "python -m devpilot_core ",
    "npm --prefix ui/web test",
    "npm --prefix ui/web run test:visual",
    "npm --prefix ui/web run test:operator-flows",
    "npm --prefix ui/web run test:route-enforcement",
)


@dataclass(frozen=True)
class TestImpactRuleRegistryOptions:
    __test__ = False

    registry_path: str | Path = DEFAULT_TEST_IMPACT_RULES_PATH
    schema_path: str | Path = DEFAULT_TEST_IMPACT_RULES_SCHEMA
    tcr_v2_registry_path: str | Path = DEFAULT_V2_REGISTRY_PATH
    tcr_v2_schema_path: str | Path = DEFAULT_V2_SCHEMA_PATH
    taxonomy_path: str | Path = DEFAULT_TEST_PROFILE_TAXONOMY_PATH
    taxonomy_schema_path: str | Path = DEFAULT_TEST_PROFILE_TAXONOMY_SCHEMA
    write_report: bool = False


class TestImpactRuleRegistryRunner:
    __test__ = False

    """Validate POST-H-029-B declarative impact rules without executing tests."""

    def __init__(self, root: Path, options: TestImpactRuleRegistryOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or TestImpactRuleRegistryOptions()
        self.registry_path = self._resolve(self.options.registry_path)
        self.schema_path = self._resolve(self.options.schema_path)
        self.tcr_v2_registry_path = self._resolve(self.options.tcr_v2_registry_path)
        self.tcr_v2_schema_path = self._resolve(self.options.tcr_v2_schema_path)
        self.taxonomy_path = self._resolve(self.options.taxonomy_path)
        self.taxonomy_schema_path = self._resolve(self.options.taxonomy_schema_path)

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        schema_result = SchemaValidator(self.root).validate(schema=self.schema_path, instance=self.registry_path)
        if not schema_result.ok:
            findings.extend(self._prefixed_findings(schema_result, "TEST_IMPACT_RULE_REGISTRY_SCHEMA"))

        tcr_result = TestContractRegistryV2Validator(
            self.root,
            TestContractRegistryV2ValidationOptions(registry_path=self.tcr_v2_registry_path, schema_path=self.tcr_v2_schema_path),
        ).validate()
        if not tcr_result.ok:
            findings.extend(self._prefixed_findings(tcr_result, "TEST_IMPACT_RULE_REGISTRY_TCR_V2"))

        taxonomy_schema_result = SchemaValidator(self.root).validate(schema=self.taxonomy_schema_path, instance=self.taxonomy_path)
        if not taxonomy_schema_result.ok:
            findings.extend(self._prefixed_findings(taxonomy_schema_result, "TEST_IMPACT_RULE_REGISTRY_TAXONOMY"))

        registry = self._load_json(self.registry_path, findings, "TEST_IMPACT_RULE_REGISTRY_LOAD_FAILED")
        taxonomy = self._load_json(self.taxonomy_path, findings, "TEST_IMPACT_RULE_REGISTRY_TAXONOMY_LOAD_FAILED")
        tcr_registry = tcr_result.data.get("registry", {}) if isinstance(tcr_result.data, dict) else {}

        rules = [item for item in registry.get("rules", []) if isinstance(item, dict)] if isinstance(registry, dict) else []
        contracts = [item for item in tcr_registry.get("contracts", []) if isinstance(item, dict)] if isinstance(tcr_registry, dict) else []
        taxonomy_profiles = {str(item.get("profile_id")) for item in taxonomy.get("profiles", []) if isinstance(item, dict)} if isinstance(taxonomy, dict) else set()

        checks = {
            "schema": {"ok": schema_result.ok, "command": schema_result.command, "exit_code": int(schema_result.exit_code)},
            "tcr_v2": {"ok": tcr_result.ok, "command": tcr_result.command, "exit_code": int(tcr_result.exit_code)},
            "taxonomy": {"ok": taxonomy_schema_result.ok, "command": taxonomy_schema_result.command, "exit_code": int(taxonomy_schema_result.exit_code)},
            "required_rules": self._required_rules_check(rules, findings),
            "p0_p1_domain_coverage": self._domain_coverage_check(rules, contracts, findings),
            "command_allowlist": self._command_allowlist_check(rules, findings),
            "rule_semantics": self._rule_semantics_check(rules, taxonomy_profiles, findings),
            "unmatched_policy": self._unmatched_policy_check(registry, findings),
            "critical_cost_metadata": self._critical_cost_metadata_check(contracts, findings),
            "safety_flags": self._safety_flags_check(registry, rules, findings),
        }
        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
        ok = all(bool(check.get("ok")) for check in checks.values()) and not blocking
        summary = {
            "created_by": POST_H_029_B_CREATED_BY,
            "status": "implemented-initial",
            "decision": "PASS" if ok else "BLOCK",
            "test_impact_rule_registry_valid": ok,
            "rules_total": len(rules),
            "required_rules_total": len(_REQUIRED_RULE_IDS),
            "required_rules_present_total": int(checks["required_rules"].get("required_rules_present_total", 0)),
            "p0_p1_domains_total": int(checks["p0_p1_domain_coverage"].get("p0_p1_domains_total", 0)),
            "p0_p1_domains_mapped_total": int(checks["p0_p1_domain_coverage"].get("p0_p1_domains_mapped_total", 0)),
            "unmapped_p0_p1_domains_total": int(checks["p0_p1_domain_coverage"].get("unmapped_p0_p1_domains_total", 0)),
            "unsafe_commands_total": int(checks["command_allowlist"].get("unsafe_commands_total", 0)),
            "unknown_impact_escalates": bool(checks["unmatched_policy"].get("unknown_impact_escalates")),
            "sensitive_unmatched_full_regression": bool(checks["unmatched_policy"].get("sensitive_unmatched_full_regression")),
            "critical_contracts_without_cost_total": int(checks["critical_cost_metadata"].get("critical_contracts_without_cost_total", 0)),
            "checks_total": len(checks),
            "checks_passed": sum(1 for item in checks.values() if bool(item.get("ok"))),
            "findings_total": len(findings),
            "warnings_total": len(warnings),
            "blocking_findings_total": len(blocking),
            "reports_written": False,
            "read_only": True,
            "dry_run": True,
            "tests_executed": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        report = {
            "schema_version": "1.0",
            "report_id": "devpilot-test-impact-rule-registry-report",
            "created_by": POST_H_029_B_CREATED_BY,
            "status": "pass" if ok else "blocked",
            "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary": summary,
            "checks": checks,
            "registry_path": self.relative(self.registry_path),
            "tcr_v2_registry_path": self.relative(self.tcr_v2_registry_path),
            "taxonomy_path": self.relative(self.taxonomy_path),
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "tests_executed": False,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "source_mutations_performed": False,
                "llm_judge_used": False,
            },
            "findings": [finding.to_dict() for finding in findings],
            "notes": [
                "POST-H-029-B validates declarative TCR v2 impact rules without running tests.",
                "Rules map changed paths to domains, profiles, recommended tests and escalation while preserving full regression as a required option.",
                "Unmatched paths escalate to review or full regression; POST-H-029-C will expose richer recommendations and POST-H-029-E will make closure guard semantics blocking.",
            ],
        }
        reports: dict[str, str] = {}
        if self.options.write_report:
            report["summary"]["reports_written"] = True
            reports = self._write_reports(report)
        return CommandResult(
            command=TEST_IMPACT_RULES_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False),
            message="Test impact rule registry passed." if ok else "Test impact rule registry has blocking findings.",
            data={"summary": report["summary"], "report": report, "reports": reports, "notes": report["notes"]},
            findings=findings or [Finding("TEST_IMPACT_RULE_REGISTRY_PASS", "Test impact rule registry passed.", Severity.INFO, metadata=summary)],
        )

    def _required_rules_check(self, rules: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        ids = {str(rule.get("rule_id")) for rule in rules}
        missing = sorted(_REQUIRED_RULE_IDS - ids)
        duplicate_total = len(ids) != len(rules)
        for rule_id in missing:
            findings.append(Finding("TEST_IMPACT_RULE_REQUIRED_RULE_MISSING", f"Required impact rule is missing: {rule_id}", Severity.BLOCK, path=self.relative(self.registry_path), metadata={"rule_id": rule_id}))
        if duplicate_total:
            findings.append(Finding("TEST_IMPACT_RULE_DUPLICATE_ID", "Impact rule ids must be unique.", Severity.BLOCK, path=self.relative(self.registry_path)))
        return {"ok": not missing and not duplicate_total, "required_rules": sorted(_REQUIRED_RULE_IDS), "missing_rules": missing, "required_rules_present_total": len(_REQUIRED_RULE_IDS) - len(missing)}

    def _domain_coverage_check(self, rules: list[dict[str, Any]], contracts: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        p0_p1_domains = sorted({str(contract.get("domain")) for contract in contracts if contract.get("criticality") in {"P0", "P1"} and str(contract.get("domain"))})
        mapped_domains = sorted({domain for rule in rules for domain in self._clean_list(rule.get("domains", []))})
        missing = sorted(set(p0_p1_domains) - set(mapped_domains))
        for domain in missing:
            findings.append(Finding("TEST_IMPACT_RULE_P0_P1_DOMAIN_UNMAPPED", f"P0/P1 TCR v2 domain has no impact rule mapping: {domain}", Severity.BLOCK, path=self.relative(self.registry_path), metadata={"domain": domain}))
        return {"ok": not missing, "p0_p1_domains": p0_p1_domains, "mapped_domains": mapped_domains, "missing_p0_p1_domains": missing, "p0_p1_domains_total": len(p0_p1_domains), "p0_p1_domains_mapped_total": len(p0_p1_domains) - len(missing), "unmapped_p0_p1_domains_total": len(missing)}

    def _command_allowlist_check(self, rules: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        unsafe: list[dict[str, str]] = []
        commands_total = 0
        for rule in rules:
            for command in self._clean_list(rule.get("recommended_commands", [])):
                commands_total += 1
                if not self._command_safe(command):
                    unsafe.append({"rule_id": str(rule.get("rule_id")), "command": command})
                    findings.append(Finding("TEST_IMPACT_RULE_UNSAFE_RECOMMENDED_COMMAND", "Impact rule recommended command is outside the local allowlist or contains shell control tokens.", Severity.BLOCK, path=self.relative(self.registry_path), metadata={"rule_id": rule.get("rule_id"), "command": command}))
        return {"ok": not unsafe, "recommended_commands_total": commands_total, "unsafe_commands_total": len(unsafe), "unsafe_commands": unsafe}

    def _rule_semantics_check(self, rules: list[dict[str, Any]], taxonomy_profiles: set[str], findings: list[Finding]) -> dict[str, Any]:
        bad_profiles: list[dict[str, str]] = []
        missing_patterns: list[str] = []
        missing_tests: list[dict[str, str]] = []
        for rule in rules:
            rid = str(rule.get("rule_id"))
            if not self._clean_list(rule.get("path_patterns", [])):
                missing_patterns.append(rid)
                findings.append(Finding("TEST_IMPACT_RULE_PATH_PATTERNS_MISSING", "Impact rule must declare path patterns.", Severity.BLOCK, path=self.relative(self.registry_path), metadata={"rule_id": rid}))
            for profile in self._clean_list(rule.get("profiles", [])):
                if profile not in taxonomy_profiles:
                    bad_profiles.append({"rule_id": rid, "profile": profile})
                    findings.append(Finding("TEST_IMPACT_RULE_UNKNOWN_PROFILE", "Impact rule references a profile missing from TestProfileTaxonomy.", Severity.BLOCK, path=self.relative(self.registry_path), metadata={"rule_id": rid, "profile": profile}))
            for test_file in self._clean_list(rule.get("recommended_tests", [])):
                if not (self.root / test_file).exists():
                    missing_tests.append({"rule_id": rid, "test_file": test_file})
                    findings.append(Finding("TEST_IMPACT_RULE_TEST_FILE_MISSING", "Impact rule references a recommended test file that does not exist locally.", Severity.BLOCK, path=test_file, metadata={"rule_id": rid}))
        return {"ok": not bad_profiles and not missing_patterns and not missing_tests, "unknown_profiles": bad_profiles, "missing_path_pattern_rules": missing_patterns, "missing_test_files": missing_tests}

    def _unmatched_policy_check(self, registry: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
        policy = registry.get("unmatched_path_policy", {}) if isinstance(registry, dict) else {}
        unknown = policy.get("unknown_path_escalates") is True
        sensitive_full = policy.get("sensitive_path_default") == "full-regression-required"
        p0_full = policy.get("p0_p1_unmatched_default") == "full-regression-required"
        if not unknown:
            findings.append(Finding("TEST_IMPACT_RULE_UNKNOWN_IMPACT_MUST_ESCALATE", "Unmatched path policy must escalate unknown impact.", Severity.BLOCK, path=self.relative(self.registry_path)))
        if not sensitive_full:
            findings.append(Finding("TEST_IMPACT_RULE_SENSITIVE_UNMATCHED_FULL_REQUIRED", "Sensitive unmatched paths must require full regression.", Severity.BLOCK, path=self.relative(self.registry_path)))
        if not p0_full:
            findings.append(Finding("TEST_IMPACT_RULE_P0_P1_UNMATCHED_FULL_REQUIRED", "P0/P1 unmatched paths must require full regression.", Severity.BLOCK, path=self.relative(self.registry_path)))
        return {"ok": unknown and sensitive_full and p0_full, "unknown_impact_escalates": unknown, "sensitive_unmatched_full_regression": sensitive_full, "p0_p1_unmatched_full_regression": p0_full}

    def _critical_cost_metadata_check(self, contracts: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        missing: list[str] = []
        for contract in contracts:
            if contract.get("criticality") not in {"P0", "P1"}:
                continue
            if not contract.get("cost_class") or int(contract.get("expected_duration_seconds", 0) or 0) <= 0:
                cid = str(contract.get("contract_id"))
                missing.append(cid)
                findings.append(Finding("TEST_IMPACT_RULE_CRITICAL_COST_METADATA_MISSING", "P0/P1 TCR v2 contract must carry actionable cost metadata.", Severity.BLOCK, metadata={"contract_id": cid}))
        return {"ok": not missing, "critical_contracts_total": sum(1 for item in contracts if item.get("criticality") in {"P0", "P1"}), "critical_contracts_without_cost_total": len(missing), "critical_contracts_without_cost": missing}

    def _safety_flags_check(self, registry: dict[str, Any], rules: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        unsafe: list[dict[str, Any]] = []
        root_safety = registry.get("safety", {}) if isinstance(registry, dict) else {}
        expected_root = {
            "local_first": True,
            "read_only": True,
            "dry_run_default": True,
            "tests_executed_from_registry": False,
            "network_used": False,
            "external_api_used": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "source_mutations_performed": False,
            "llm_judge_used": False,
        }
        for key, expected in expected_root.items():
            if root_safety.get(key) is not expected:
                unsafe.append({"scope": "registry", "key": key, "value": root_safety.get(key)})
        for rule in rules:
            safety = rule.get("safety", {}) if isinstance(rule.get("safety"), dict) else {}
            for key in ("network_allowed", "external_api_allowed", "mutations_allowed", "source_mutations_allowed", "tests_executed_from_rule"):
                if safety.get(key) is not False:
                    unsafe.append({"scope": str(rule.get("rule_id")), "key": key, "value": safety.get(key)})
        for item in unsafe:
            findings.append(Finding("TEST_IMPACT_RULE_UNSAFE_SAFETY_FLAG", "Impact rule registry safety flags must remain local-first, read-only and non-executing.", Severity.BLOCK, path=self.relative(self.registry_path), metadata=item))
        return {"ok": not unsafe, "unsafe_flags_total": len(unsafe), "unsafe_flags": unsafe}

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / DEFAULT_TEST_IMPACT_RULES_REPORT_JSON
        md_path = self.root / DEFAULT_TEST_IMPACT_RULES_REPORT_MD
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        summary = report.get("summary", {})
        md_path.write_text(
            "# POST-H-029-B — Test impact rule registry report\n\n"
            f"- Decision: `{summary.get('decision')}`\n"
            f"- Rules total: `{summary.get('rules_total')}`\n"
            f"- P0/P1 domains mapped: `{summary.get('p0_p1_domains_mapped_total')}/{summary.get('p0_p1_domains_total')}`\n"
            f"- Unsafe commands: `{summary.get('unsafe_commands_total')}`\n"
            f"- Unknown impact escalates: `{summary.get('unknown_impact_escalates')}`\n"
            f"- Tests executed: `{summary.get('tests_executed')}`\n"
            f"- Network used: `{summary.get('network_used')}`\n"
            f"- External APIs used: `{summary.get('external_api_used')}`\n",
            encoding="utf-8",
        )
        return {"json": str(DEFAULT_TEST_IMPACT_RULES_REPORT_JSON).replace("\\", "/"), "markdown": str(DEFAULT_TEST_IMPACT_RULES_REPORT_MD).replace("\\", "/")}

    def _load_json(self, path: Path, findings: list[Finding], finding_id: str) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(Finding(finding_id, f"Could not load {self.relative(path)}: {exc}", Severity.ERROR, path=self.relative(path)))
            return {}
        if not isinstance(value, dict):
            findings.append(Finding(finding_id, f"Expected JSON object at {self.relative(path)}.", Severity.ERROR, path=self.relative(path)))
            return {}
        return value

    def _prefixed_findings(self, result: CommandResult, prefix: str) -> list[Finding]:
        return [Finding(f"{prefix}_{finding.id}", finding.message, finding.severity, path=finding.path, metadata=finding.metadata) for finding in result.findings]

    def _command_safe(self, command: str) -> bool:
        lowered = command.lower()
        if any(token in lowered for token in _DANGEROUS_SHELL_TOKENS):
            return False
        return command.startswith(_ALLOWED_COMMAND_PREFIXES)

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


def load_impact_rule_registry(root: Path, rules_path: str | Path = DEFAULT_TEST_IMPACT_RULES_PATH) -> dict[str, Any]:
    path = Path(rules_path)
    if not path.is_absolute():
        path = Path(root) / path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def match_impact_rules(changed_path: str, registry: dict[str, Any]) -> list[dict[str, Any]]:
    rules = [item for item in registry.get("rules", []) if isinstance(item, dict)] if isinstance(registry, dict) else []
    changed = changed_path.replace("\\", "/").strip().lstrip("./")
    matches: list[dict[str, Any]] = []
    for rule in rules:
        patterns = [str(item).strip().replace("\\", "/").rstrip("/") for item in rule.get("path_patterns", []) if str(item).strip()]
        if any(changed == pattern or changed.startswith(pattern + "/") or changed.startswith(pattern) for pattern in patterns):
            matches.append(rule)
    return matches
