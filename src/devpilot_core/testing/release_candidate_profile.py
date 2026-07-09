from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.schemas import SchemaValidator

from .profiles_v2 import TestContractRegistryV2ValidationOptions, TestContractRegistryV2Validator

POST_H_029_D_CREATED_BY = "POST-H-029-D"
RELEASE_CANDIDATE_TEST_PROFILE_COMMAND = "tests release-candidate-profile"
RELEASE_CANDIDATE_TEST_PROFILE_SCHEMA_ID = "SCHEMA-DEVPL-RELEASE-CANDIDATE-TEST-PROFILE-REPORT-V1"
RELEASE_CANDIDATE_TEST_PROFILE_CONTRACT = "ReleaseCandidateTestProfileReport"
DEFAULT_RELEASE_CANDIDATE_TEST_PROFILE_PATH = Path(".devpilot/testing/release_candidate_test_profile.json")
DEFAULT_TEST_PROFILE_TAXONOMY_PATH = Path(".devpilot/testing/test_profile_taxonomy.json")
DEFAULT_TEST_PROFILES_PATH = Path(".devpilot/testing/test_profiles.json")
DEFAULT_TCR_V2_PATH = Path(".devpilot/testing/test_contract_registry_v2.json")
DEFAULT_RC_PROFILE_REPORT_JSON = Path("outputs/reports/release_candidate_test_profile_report.json")
DEFAULT_RC_PROFILE_REPORT_MARKDOWN = Path("outputs/reports/release_candidate_test_profile_report.md")

_REQUIRED_COMMAND_FRAGMENTS = (
    "project-state validate",
    "docs-governance validate",
    "schema list",
    "test-contracts validate",
    "test-contracts validate-v2",
    "quality-gate run --profile hardening",
    "industrial-readiness production-ready-local-final",
    "api shell-gate",
    "api contract-drift",
    "api security-hardening",
    "api ui-route-enforcement",
    "release-candidate final",
    "package source-zip-policy",
    "release artifact-manifest",
    "release upgrade-rollback-dry-run",
)
_REQUIRED_TEST_TARGETS = (
    "tests/test_post_h_029_release_candidate_test_profile.py",
    "tests/test_post_h_029_test_profile_taxonomy.py",
    "tests/test_post_h_029_tcr_v2_impact_rules.py",
    "tests/test_post_h_029_test_impact_cli_recommendations.py",
    "tests/test_post_h_026_release_candidate_profile.py",
    "tests/test_post_h_026_release_candidate_report.py",
    "tests/test_post_h_027_source_zip_policy.py",
    "tests/test_post_h_027_upgrade_rollback_dry_run.py",
    "tests/test_post_h_028_ui_route_registry_enforcement.py",
    "tests/test_post_h_025_production_ready_final_declaration.py",
    "tests/test_quality_gate.py",
    "tests/test_test_contract_registry_v2.py",
    "tests/test_schema_registry.py",
    "tests/test_project_global_state.py",
)
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
class ReleaseCandidateTestProfileOptions:
    profile_path: str | Path = DEFAULT_RELEASE_CANDIDATE_TEST_PROFILE_PATH
    taxonomy_path: str | Path = DEFAULT_TEST_PROFILE_TAXONOMY_PATH
    tests_run_profile_path: str | Path = DEFAULT_TEST_PROFILES_PATH
    tcr_v2_path: str | Path = DEFAULT_TCR_V2_PATH
    output_json: str | Path = DEFAULT_RC_PROFILE_REPORT_JSON
    output_markdown: str | Path = DEFAULT_RC_PROFILE_REPORT_MARKDOWN
    write_report: bool = False


class ReleaseCandidateTestProfileRunner:
    """Validate POST-H-029-D formal local release-candidate test profile.

    The runner is intentionally non-executing. It validates source-controlled
    profile metadata, command allowlists, pytest target existence, taxonomy
    binding, tests.run compatibility and TCR v2 profile selection. Operators
    must execute recommended commands explicitly through governed CLI paths.
    """

    def __init__(self, root: Path, options: ReleaseCandidateTestProfileOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ReleaseCandidateTestProfileOptions()
        self.profile_path = self._resolve(self.options.profile_path)
        self.taxonomy_path = self._resolve(self.options.taxonomy_path)
        self.tests_run_profile_path = self._resolve(self.options.tests_run_profile_path)
        self.tcr_v2_path = self._resolve(self.options.tcr_v2_path)
        self.output_json = self._resolve(self.options.output_json)
        self.output_markdown = self._resolve(self.options.output_markdown)

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        profile = self._load_json(self.profile_path, findings, "RC_TEST_PROFILE")
        taxonomy = self._load_json(self.taxonomy_path, findings, "TEST_PROFILE_TAXONOMY")
        tests_run_profiles = self._load_json(self.tests_run_profile_path, findings, "TESTS_RUN_PROFILES")

        if not isinstance(profile, dict):
            profile = {}
        if not isinstance(taxonomy, dict):
            taxonomy = {}
        if not isinstance(tests_run_profiles, dict):
            tests_run_profiles = {}

        findings.extend(self._profile_findings(profile))
        taxonomy_profile = self._find_profile(taxonomy.get("profiles", []), "profile_id", "release-candidate-local")
        if taxonomy_profile is None:
            findings.append(Finding("RC_TEST_PROFILE_TAXONOMY_BINDING_MISSING", "Taxonomy does not define release-candidate-local.", Severity.BLOCK, path=self._relative(self.taxonomy_path)))
        tests_run_profile = self._find_profile(tests_run_profiles.get("profiles", []), "profile_id", "release-candidate-local")
        findings.extend(self._tests_run_profile_findings(tests_run_profile))

        tcr_result = TestContractRegistryV2Validator(
            self.root,
            TestContractRegistryV2ValidationOptions(registry_path=self.tcr_v2_path),
        ).profile("release-candidate-local")
        findings.extend(tcr_result.findings)
        tcr_contracts = tcr_result.data.get("contracts", []) if isinstance(tcr_result.data, dict) else []
        if not tcr_result.ok:
            findings.append(Finding("RC_TEST_PROFILE_TCR_V2_BLOCKED", "TCR v2 profile release-candidate-local did not validate.", Severity.BLOCK, path=self._relative(self.tcr_v2_path)))
        if len(tcr_contracts) < 1:
            findings.append(Finding("RC_TEST_PROFILE_TCR_V2_PROFILE_EMPTY", "TCR v2 profile release-candidate-local selected no contracts.", Severity.BLOCK, path=self._relative(self.tcr_v2_path)))

        all_commands = self._commands(profile)
        required_commands = self._commands(profile, key="required_commands")
        recommended_commands = self._commands(profile, key="recommended_commands")
        optional_commands = self._commands(profile, key="optional_commands")
        pytest_targets = self._pytest_targets(profile)
        missing_required = self._missing_required_command_fragments(required_commands)
        missing_targets = [target for target in _REQUIRED_TEST_TARGETS if target not in {item.get("path") for item in pytest_targets}]
        unsafe_commands = self._unsafe_commands(all_commands)
        blocking = [f for f in findings if f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        if missing_required:
            blocking.append(Finding("RC_TEST_PROFILE_REQUIRED_COMMANDS_MISSING", "Required RC profile commands are missing.", Severity.BLOCK, path=self._relative(self.profile_path), metadata={"missing_fragments": missing_required}))
        if missing_targets:
            blocking.append(Finding("RC_TEST_PROFILE_REQUIRED_TEST_TARGETS_MISSING", "Required RC profile pytest targets are missing.", Severity.BLOCK, path=self._relative(self.profile_path), metadata={"missing_targets": missing_targets}))
        if unsafe_commands:
            blocking.append(Finding("RC_TEST_PROFILE_UNSAFE_COMMANDS", "RC profile contains unsafe command data.", Severity.BLOCK, path=self._relative(self.profile_path), metadata={"unsafe_commands": unsafe_commands}))
        findings.extend(item for item in blocking if item not in findings)

        decision = "PASS" if not blocking else "BLOCK"
        report = self._build_report(
            profile=profile,
            taxonomy_profile=taxonomy_profile or {},
            tests_run_profile=tests_run_profile or {},
            tcr_contracts=tcr_contracts,
            required_commands=required_commands,
            recommended_commands=recommended_commands,
            optional_commands=optional_commands,
            pytest_targets=pytest_targets,
            missing_required=missing_required,
            missing_targets=missing_targets,
            unsafe_commands=unsafe_commands,
            findings=findings,
            decision=decision,
        )
        schema_result = SchemaValidator(self.root).validate_payload(
            schema=RELEASE_CANDIDATE_TEST_PROFILE_CONTRACT,
            payload=report,
            instance_label="ReleaseCandidateTestProfileReport(payload)",
        )
        findings.extend(schema_result.findings)
        if not schema_result.ok:
            decision = "BLOCK"
            report["status"] = "blocked"
            report["summary"]["decision"] = "BLOCK"
            findings.append(Finding("RC_TEST_PROFILE_REPORT_SCHEMA_INVALID", "Generated RC test profile report does not validate against schema.", Severity.BLOCK, metadata={"exit_code": int(schema_result.exit_code)}))

        if self.options.write_report:
            self._write_report(report)
            report["summary"]["reports_written"] = True
            report["safety"]["reports_written"] = True
        if decision == "PASS":
            findings.append(Finding("RC_TEST_PROFILE_PASS", "Release candidate test profile passed without executing tests.", Severity.INFO, metadata=report["summary"]))
        return CommandResult(
            RELEASE_CANDIDATE_TEST_PROFILE_COMMAND,
            decision == "PASS",
            ExitCode.PASS if decision == "PASS" else exit_code_for_findings(findings),
            "Release candidate test profile passed." if decision == "PASS" else "Release candidate test profile blocked.",
            data={
                "summary": report["summary"],
                "report": report,
                "profile_path": self._relative(self.profile_path),
                "reports": self._report_paths() if self.options.write_report else {},
                "notes": report["notes"],
            },
            findings=findings,
        )

    def _build_report(self, **kwargs: Any) -> dict[str, Any]:
        decision = kwargs["decision"]
        profile = kwargs["profile"]
        full_regression_rules = [str(item) for item in profile.get("full_regression_required_when", []) if str(item).strip()]
        summary = {
            "created_by": POST_H_029_D_CREATED_BY,
            "status": "implemented-initial",
            "decision": decision,
            "profile_id": "release-candidate-local",
            "required_commands_total": len(kwargs["required_commands"]),
            "required_commands_present_total": len(kwargs["required_commands"]) - len(kwargs["missing_required"]),
            "recommended_commands_total": len(kwargs["recommended_commands"]),
            "optional_commands_total": len(kwargs["optional_commands"]),
            "pytest_targets_total": len(kwargs["pytest_targets"]),
            "missing_required_commands_total": len(kwargs["missing_required"]),
            "missing_pytest_targets_total": len(kwargs["missing_targets"]),
            "unsafe_commands_total": len(kwargs["unsafe_commands"]),
            "required_sections_present": all(isinstance(profile.get(key), list) and profile.get(key) for key in ("required_commands", "pytest_targets", "full_regression_required_when", "prerequisites")),
            "full_regression_rules_total": len(full_regression_rules),
            "tcr_v2_contracts_selected_total": len(kwargs["tcr_contracts"]),
            "tests_run_profile_synced": bool(kwargs["tests_run_profile"]),
            "taxonomy_profile_synced": bool(kwargs["taxonomy_profile"]),
            "tests_executed": False,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": self.options.write_report,
            "preliminary": True,
        }
        return {
            "schema_version": "1.0",
            "schema_id": RELEASE_CANDIDATE_TEST_PROFILE_SCHEMA_ID,
            "report_id": "devpilot-release-candidate-test-profile-report",
            "created_by": POST_H_029_D_CREATED_BY,
            "status": "pass" if decision == "PASS" else "blocked",
            "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "summary": summary,
            "profile": profile,
            "required_commands": kwargs["required_commands"],
            "recommended_commands": kwargs["recommended_commands"],
            "optional_commands": kwargs["optional_commands"],
            "pytest_targets": kwargs["pytest_targets"],
            "full_regression_required_when": full_regression_rules,
            "prerequisites": [str(item) for item in profile.get("prerequisites", []) if str(item).strip()],
            "tcr_v2": {"path": self._relative(self.tcr_v2_path), "contracts_selected_total": len(kwargs["tcr_contracts"]), "contract_ids": [item.get("contract_id") for item in kwargs["tcr_contracts"] if isinstance(item, dict)]},
            "taxonomy": {"path": self._relative(self.taxonomy_path), "profile": kwargs["taxonomy_profile"]},
            "tests_run_profile": {"path": self._relative(self.tests_run_profile_path), "profile": kwargs["tests_run_profile"]},
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
                "mutations_performed": False,
                "source_mutations_performed": False,
                "llm_judge_used": False,
                "reports_written": self.options.write_report,
            },
            "findings": [finding.to_dict() for finding in kwargs["findings"]],
            "notes": [
                "POST-H-029-D validates the formal release-candidate-local test profile without executing tests.",
                "The profile groups required, recommended and optional commands; operators must execute them explicitly.",
                "Full regression is preserved and remains mandatory when full_regression_required_when applies; POST-H-029-E will harden closure guard semantics.",
            ],
        }

    def _profile_findings(self, profile: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        if profile.get("profile_id") != "release-candidate-local":
            findings.append(Finding("RC_TEST_PROFILE_ID_INVALID", "Profile id must be release-candidate-local.", Severity.BLOCK, path=self._relative(self.profile_path)))
        if profile.get("created_by") != POST_H_029_D_CREATED_BY:
            findings.append(Finding("RC_TEST_PROFILE_CREATED_BY_INVALID", "Profile must be owned by POST-H-029-D.", Severity.BLOCK, path=self._relative(self.profile_path)))
        if profile.get("taxonomy_profile_id") != "release-candidate-local":
            findings.append(Finding("RC_TEST_PROFILE_TAXONOMY_PROFILE_INVALID", "Profile must bind to taxonomy profile release-candidate-local.", Severity.BLOCK, path=self._relative(self.profile_path)))
        safety = profile.get("safety", {}) if isinstance(profile.get("safety"), dict) else {}
        for key in ("network_used", "external_api_used", "remote_execution_enabled", "connector_write_enabled", "plugin_execution_enabled", "mutations_performed", "source_mutations_performed", "llm_judge_used", "allow_shell", "allow_arbitrary_pytest_args"):
            if safety.get(key) is not False:
                findings.append(Finding("RC_TEST_PROFILE_UNSAFE_FLAG", "Release candidate test profile has unsafe safety flag.", Severity.BLOCK, path=self._relative(self.profile_path), metadata={"flag": key, "value": safety.get(key)}))
        for target in self._pytest_targets(profile):
            path = str(target.get("path", ""))
            if path and not (self.root / path).exists():
                findings.append(Finding("RC_TEST_PROFILE_TEST_TARGET_MISSING", "Release candidate profile declares a missing pytest target.", Severity.BLOCK, path=path))
        return findings

    def _tests_run_profile_findings(self, profile: dict[str, Any] | None) -> list[Finding]:
        findings: list[Finding] = []
        if not profile:
            findings.append(Finding("RC_TEST_PROFILE_TESTS_RUN_PROFILE_MISSING", "tests.run profile release-candidate-local is missing.", Severity.BLOCK, path=self._relative(self.tests_run_profile_path)))
            return findings
        if profile.get("taxonomy_profile_id") != "release-candidate-local":
            findings.append(Finding("RC_TEST_PROFILE_TESTS_RUN_TAXONOMY_DRIFT", "tests.run profile must map to taxonomy release-candidate-local.", Severity.BLOCK, path=self._relative(self.tests_run_profile_path)))
        for key in ("network_allowed", "external_api_allowed", "mutations_allowed", "source_mutations_allowed", "allow_shell", "allow_arbitrary_pytest_args"):
            if profile.get(key) is not False:
                findings.append(Finding("RC_TEST_PROFILE_TESTS_RUN_UNSAFE", "tests.run release-candidate-local profile has unsafe flag.", Severity.BLOCK, path=self._relative(self.tests_run_profile_path), metadata={"flag": key, "value": profile.get(key)}))
        if profile.get("requires_approval_for_pytest") is not True:
            findings.append(Finding("RC_TEST_PROFILE_TESTS_RUN_APPROVAL_REQUIRED", "tests.run release-candidate-local must require approval.", Severity.BLOCK, path=self._relative(self.tests_run_profile_path)))
        return findings

    def _missing_required_command_fragments(self, commands: list[dict[str, Any]]) -> list[str]:
        command_text = "\n".join(str(item.get("command", "")) for item in commands)
        return [fragment for fragment in _REQUIRED_COMMAND_FRAGMENTS if fragment not in command_text]

    def _unsafe_commands(self, commands: list[dict[str, Any]]) -> list[str]:
        unsafe: list[str] = []
        for item in commands:
            command = str(item.get("command", "")).strip()
            lowered = command.lower()
            if not any(command.startswith(prefix) for prefix in _ALLOWED_COMMAND_PREFIXES):
                unsafe.append(command)
                continue
            if any(token in lowered for token in _DANGEROUS_SHELL_TOKENS):
                unsafe.append(command)
        return unsafe

    def _commands(self, profile: dict[str, Any], *, key: str | None = None) -> list[dict[str, Any]]:
        keys = [key] if key else ["required_commands", "recommended_commands", "optional_commands"]
        out: list[dict[str, Any]] = []
        for name in keys:
            for item in profile.get(name, []):
                if isinstance(item, dict):
                    out.append(item)
        return out

    def _pytest_targets(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        return [item for item in profile.get("pytest_targets", []) if isinstance(item, dict)]

    def _load_json(self, path: Path, findings: list[Finding], prefix: str) -> Any:
        if not path.exists():
            findings.append(Finding(f"{prefix}_MISSING", "Required JSON file is missing.", Severity.BLOCK, path=self._relative(path)))
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding(f"{prefix}_INVALID_JSON", "Required JSON file is invalid.", Severity.ERROR, path=self._relative(path), metadata={"error": str(exc)}))
            return None

    def _find_profile(self, payload: Any, key: str, value: str) -> dict[str, Any] | None:
        if not isinstance(payload, list):
            return None
        for item in payload:
            if isinstance(item, dict) and item.get(key) == value:
                return item
        return None

    def _write_report(self, report: dict[str, Any]) -> None:
        self.output_json.parent.mkdir(parents=True, exist_ok=True)
        self.output_markdown.parent.mkdir(parents=True, exist_ok=True)
        self.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.output_markdown.write_text(self._markdown(report), encoding="utf-8")

    def _markdown(self, report: dict[str, Any]) -> str:
        lines = [
            "# Release candidate test profile report",
            "",
            f"- Decision: `{report['summary']['decision']}`",
            f"- Profile: `{report['summary']['profile_id']}`",
            f"- Required commands: `{report['summary']['required_commands_total']}`",
            f"- Pytest targets: `{report['summary']['pytest_targets_total']}`",
            f"- TCR v2 selected contracts: `{report['summary']['tcr_v2_contracts_selected_total']}`",
            f"- Full-regression rules: `{report['summary']['full_regression_rules_total']}`",
            f"- Tests executed: `{report['summary']['tests_executed']}`",
            "",
            "## Required commands",
        ]
        lines.extend(f"- `{item['command']}`" for item in report["required_commands"])
        lines.extend(["", "## Full regression required when"])
        lines.extend(f"- {item}" for item in report["full_regression_required_when"])
        lines.extend(["", "## Notes"])
        lines.extend(f"- {item}" for item in report["notes"])
        return "\n".join(lines) + "\n"

    def _report_paths(self) -> dict[str, str]:
        return {"json": self._relative(self.output_json), "markdown": self._relative(self.output_markdown)}

    def _resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Path escapes project root: {path}") from exc
        return resolved

    def _relative(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")
