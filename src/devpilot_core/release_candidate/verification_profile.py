from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.testing.profiles import TestProfileRegistry
from devpilot_core.testing.profiles_v2 import TestContractRegistryV2ValidationOptions, TestContractRegistryV2Validator


DEFAULT_RELEASE_CANDIDATE_PROFILE_ID = "release-candidate-local"
DEFAULT_TEST_PROFILES_PATH = Path(".devpilot/testing/test_profiles.json")
DEFAULT_TCR_V2_PATH = Path(".devpilot/testing/test_contract_registry_v2.json")
DEFAULT_PROFILE_REPORT_JSON_PATH = Path("outputs/reports/release_candidate_verification_profile_report.json")
DEFAULT_PROFILE_REPORT_MARKDOWN_PATH = Path("outputs/reports/release_candidate_verification_profile_report.md")

_REQUIRED_COMMANDS = (
    "project-state validate",
    "docs-governance validate",
    "schema list",
    "test-contracts validate",
    "test-contracts validate-v2",
    "quality-gate run --profile hardening",
    "industrial-readiness production-ready-local-final",
    "release-candidate evidence-freshness",
    "release-candidate ui-api-smoke",
    "release-candidate install-smoke",
)
_REQUIRED_PYTEST_TARGETS = (
    "tests/test_post_h_026_evidence_freshness.py",
    "tests/test_post_h_026_release_candidate_profile.py",
    "tests/test_post_h_026_ui_api_rc_smoke.py",
    "tests/test_post_h_026_ui_api_rc_smoke_contract.py",
    "tests/test_post_h_026_install_smoke.py",
    "tests/test_post_h_025_production_ready_final_declaration.py",
    "tests/test_post_h_025_production_ready_claims_validator.py",
    "tests/test_quality_gate.py",
    "tests/test_schema_registry.py",
    "tests/test_project_global_state.py",
)
_ALLOWED_PROFILE_TAXONOMY = {"always", "impacted", "release-candidate", "full"}


@dataclass(frozen=True)
class ReleaseCandidateVerificationProfileOptions:
    profile_id: str = DEFAULT_RELEASE_CANDIDATE_PROFILE_ID
    test_profiles_path: str = str(DEFAULT_TEST_PROFILES_PATH)
    tcr_v2_path: str = str(DEFAULT_TCR_V2_PATH)
    output_json: str = str(DEFAULT_PROFILE_REPORT_JSON_PATH)
    output_markdown: str = str(DEFAULT_PROFILE_REPORT_MARKDOWN_PATH)
    write_report: bool = False


class ReleaseCandidateVerificationProfile:
    """Plan-only verifier for the local release candidate test profile.

    POST-H-026-B deliberately does not run pytest or shell commands. It checks
    that the release-candidate-local profile is versioned, non-networked,
    approval-gated for pytest execution, connected to TCR v2 and complete enough
    to guide an operator through focused RC verification.
    """

    def __init__(self, root: Path, options: ReleaseCandidateVerificationProfileOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ReleaseCandidateVerificationProfileOptions()

    def inspect(self) -> CommandResult:
        started = perf_counter()
        findings: list[Finding] = []
        profile_path = self._resolve(self.options.test_profiles_path)
        tcr_v2_path = self._resolve(self.options.tcr_v2_path)
        profiles_payload = self._load_json(profile_path, findings, finding_prefix="TEST_PROFILE")
        profile = self._find_profile(profiles_payload, self.options.profile_id) if isinstance(profiles_payload, dict) else None
        if profile is None:
            findings.append(
                Finding(
                    "RC_PROFILE_NOT_FOUND",
                    "release-candidate-local profile is not configured in .devpilot/testing/test_profiles.json.",
                    Severity.BLOCK,
                    path=self._relative(profile_path),
                    metadata={"profile_id": self.options.profile_id},
                )
            )
            profile = {}

        findings.extend(self._profile_findings(profile, profile_path))
        tcr_profile_result = TestContractRegistryV2Validator(
            self.root,
            TestContractRegistryV2ValidationOptions(registry_path=tcr_v2_path),
        ).profile(self.options.profile_id)
        tcr_contracts = tcr_profile_result.data.get("contracts", []) if isinstance(tcr_profile_result.data, dict) else []
        findings.extend(tcr_profile_result.findings)
        if not tcr_profile_result.ok:
            findings.append(
                Finding(
                    "RC_PROFILE_TCR_V2_BINDING_BLOCKED",
                    "TCR v2 profile binding failed for release-candidate-local.",
                    Severity.BLOCK,
                    path=self._relative(tcr_v2_path),
                    metadata={"profile_id": self.options.profile_id, "exit_code": int(tcr_profile_result.exit_code)},
                )
            )

        duration_ms = round((perf_counter() - started) * 1000, 3)
        blocking = [f for f in findings if f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        decision = "PASS" if not blocking else "BLOCK"
        profile_commands = [str(item) for item in profile.get("commands", []) if str(item).strip()]
        pytest_targets = [str(item) for item in profile.get("pytest_targets", []) if str(item).strip()]
        report = {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-RELEASE-CANDIDATE-VERIFICATION-PROFILE-V1",
            "report_id": "release-candidate-verification-profile-post_h_026_b",
            "created_by": "POST-H-026-B",
            "created_at": self._now(),
            "scope": "local-release-candidate",
            "profile_id": self.options.profile_id,
            "profile_path": self._relative(profile_path),
            "tcr_v2_path": self._relative(tcr_v2_path),
            "decision": decision,
            "implemented_status": "implemented-initial",
            "execution_mode": "plan-only",
            "taxonomy": profile.get("taxonomy", []),
            "commands_expected": list(_REQUIRED_COMMANDS),
            "commands_configured": profile_commands,
            "commands_executed": [],
            "command_results": [],
            "pytest_targets": pytest_targets,
            "tcr_v2_contracts_selected_total": len(tcr_contracts),
            "tcr_v2_contract_ids": [item.get("contract_id") for item in tcr_contracts if isinstance(item, dict)],
            "duration_ms": duration_ms,
            "network_allowed": profile.get("network_allowed"),
            "external_api_allowed": profile.get("external_api_allowed"),
            "requires_approval_for_pytest": profile.get("requires_approval_for_pytest"),
            "tests_executed": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations": False,
            "reports_written": self.options.write_report,
            "safety": {
                "local_first": True,
                "read_only": True,
                "plan_only": True,
                "tests_executed": False,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations": False,
                "reports_written": self.options.write_report,
            },
            "limitations": [
                "POST-H-026-B defines and validates the RC profile; it does not execute pytest or shell commands.",
                "Install smoke is available in POST-H-026-D; final RC PASS/BLOCK remains planned for POST-H-026-E.",
                "The full pytest suite remains the final backlog-level regression gate; this profile is an operational accelerator, not a replacement.",
            ],
        }
        if self.options.write_report:
            self._write_report(report)

        if not blocking:
            findings.append(
                Finding(
                    "RC_PROFILE_VERIFICATION_PASS",
                    "Local release candidate verification profile is configured without executing tests.",
                    Severity.INFO,
                    metadata={"profile_id": self.options.profile_id, "commands_total": len(profile_commands), "pytest_targets_total": len(pytest_targets)},
                )
            )
        return CommandResult(
            "release-candidate profile",
            decision == "PASS",
            ExitCode.PASS if decision == "PASS" else ExitCode.BLOCK,
            "Release candidate verification profile passed." if decision == "PASS" else "Release candidate verification profile blocked.",
            data={
                "summary": {
                    "decision": decision,
                    "profile_id": self.options.profile_id,
                    "implemented_status": "implemented-initial",
                    "execution_mode": "plan-only",
                    "commands_configured_total": len(profile_commands),
                    "pytest_targets_total": len(pytest_targets),
                    "tcr_v2_contracts_selected_total": len(tcr_contracts),
                    "tests_executed": False,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "reports_written": self.options.write_report,
                },
                "report": report,
                "profile": profile,
                "reports": self._report_paths() if self.options.write_report else {},
            },
            findings=findings,
        )

    def _profile_findings(self, profile: dict[str, Any], profile_path: Path) -> list[Finding]:
        findings: list[Finding] = []
        commands = [str(item) for item in profile.get("commands", []) if str(item).strip()]
        pytest_targets = [str(item) for item in profile.get("pytest_targets", []) if str(item).strip()]
        missing_commands = [command for command in _REQUIRED_COMMANDS if command not in commands]
        missing_targets = [target for target in _REQUIRED_PYTEST_TARGETS if target not in pytest_targets]
        taxonomy = {str(item) for item in profile.get("taxonomy", []) if str(item).strip()}
        missing_taxonomy = _ALLOWED_PROFILE_TAXONOMY - taxonomy
        if missing_commands:
            findings.append(Finding("RC_PROFILE_REQUIRED_COMMANDS_MISSING", "RC profile is missing required commands.", Severity.BLOCK, path=self._relative(profile_path), metadata={"missing_commands": missing_commands}))
        if missing_targets:
            findings.append(Finding("RC_PROFILE_REQUIRED_PYTEST_TARGETS_MISSING", "RC profile is missing required pytest targets.", Severity.FAIL, path=self._relative(profile_path), metadata={"missing_targets": missing_targets}))
        if missing_taxonomy:
            findings.append(Finding("RC_PROFILE_TAXONOMY_INCOMPLETE", "RC profile taxonomy must include always, impacted, release-candidate and full.", Severity.FAIL, path=self._relative(profile_path), metadata={"missing_taxonomy": sorted(missing_taxonomy)}))
        if profile.get("network_allowed") is not False or profile.get("external_api_allowed") is not False:
            findings.append(Finding("RC_PROFILE_NETWORK_NOT_ALLOWED", "RC profile must not allow network or external APIs.", Severity.BLOCK, path=self._relative(profile_path)))
        if profile.get("requires_approval_for_pytest") is not True:
            findings.append(Finding("RC_PROFILE_PYTEST_APPROVAL_REQUIRED", "RC profile must keep pytest execution approval-gated.", Severity.BLOCK, path=self._relative(profile_path)))
        if profile.get("allow_arbitrary_pytest_args") is not False or profile.get("allow_shell") is not False:
            findings.append(Finding("RC_PROFILE_ARBITRARY_EXECUTION_BLOCKED", "RC profile must not allow arbitrary pytest args or shell commands.", Severity.BLOCK, path=self._relative(profile_path)))
        for target in pytest_targets:
            if "*" in target:
                continue
            if not (self.root / target).exists():
                findings.append(Finding("RC_PROFILE_PYTEST_TARGET_MISSING", "RC profile declares a pytest target that does not exist.", Severity.FAIL, path=target))
        return findings

    def _load_json(self, path: Path, findings: list[Finding], *, finding_prefix: str) -> Any:
        if not path.exists():
            findings.append(Finding(f"{finding_prefix}_JSON_MISSING", "Required JSON configuration is missing.", Severity.BLOCK, path=self._relative(path)))
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding(f"{finding_prefix}_JSON_INVALID", "Required JSON configuration is invalid.", Severity.ERROR, path=self._relative(path), metadata={"error": str(exc)}))
            return None

    def _find_profile(self, payload: dict[str, Any], profile_id: str) -> dict[str, Any] | None:
        for item in payload.get("profiles", []):
            if isinstance(item, dict) and item.get("profile_id") == profile_id:
                return item
        return None

    def _write_report(self, report: dict[str, Any]) -> None:
        json_path = self._resolve(self.options.output_json)
        markdown_path = self._resolve(self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(self._markdown(report), encoding="utf-8")

    def _markdown(self, report: dict[str, Any]) -> str:
        lines = [
            "# Release candidate verification profile report",
            "",
            f"- Decision: `{report['decision']}`",
            f"- Profile: `{report['profile_id']}`",
            f"- Execution mode: `{report['execution_mode']}`",
            f"- Commands configured: `{len(report['commands_configured'])}`",
            f"- Pytest targets: `{len(report['pytest_targets'])}`",
            f"- TCR v2 contracts selected: `{report['tcr_v2_contracts_selected_total']}`",
            f"- Tests executed: `{report['tests_executed']}`",
            f"- Network used: `{report['network_used']}`",
            "",
            "## Commands configured",
        ]
        lines.extend(f"- `{command}`" for command in report["commands_configured"])
        lines.extend(["", "## Limitations"])
        lines.extend(f"- {item}" for item in report["limitations"])
        return "\n".join(lines) + "\n"

    def _report_paths(self) -> dict[str, str]:
        return {"json": self._relative(self._resolve(self.options.output_json)), "markdown": self._relative(self._resolve(self.options.output_markdown))}

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

    def _now(self) -> str:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
