from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.schemas import SchemaValidator

POST_H_029_A_CREATED_BY = "POST-H-029-A"
TEST_PROFILE_TAXONOMY_COMMAND = "tests taxonomy"
TEST_PROFILE_TAXONOMY_SCHEMA_ID = "SCHEMA-DEVPL-TEST-PROFILE-TAXONOMY-V1"
TEST_PROFILE_TAXONOMY_CONTRACT = "TestProfileTaxonomy"
DEFAULT_TEST_PROFILE_TAXONOMY_PATH = Path(".devpilot/testing/test_profile_taxonomy.json")
DEFAULT_TEST_PROFILES_PATH = Path(".devpilot/testing/test_profiles.json")
DEFAULT_TAXONOMY_REPORT_JSON = Path("outputs/reports/test_profile_taxonomy_report.json")
DEFAULT_TAXONOMY_REPORT_MARKDOWN = Path("outputs/reports/test_profile_taxonomy_report.md")

REQUIRED_PROFILE_IDS = {
    "always-fast",
    "p0-critical",
    "security",
    "impact",
    "release",
    "release-candidate-local",
    "docs-historical",
    "full",
    "manual",
    "nightly-local",
}
LEGACY_PROFILE_IDS = {"smoke", "unit", "all"}
HIGH_RISK_PROFILE_IDS = {"p0-critical", "security", "release", "release-candidate-local", "full", "nightly-local"}
ALLOWED_COMMAND_PREFIXES = (
    "python -m pytest ",
    "python -m devpilot_core ",
    "npm --prefix ui/web test",
    "npm --prefix ui/web run test:visual",
    "npm --prefix ui/web run test:operator-flows",
    "npm --prefix ui/web run test:route-enforcement",
)
DANGEROUS_SHELL_TOKENS = ("&&", "||", ";", "|", ">", "<", "`", "$(", "curl ", "wget ", "powershell", "pwsh", "cmd.exe")


@dataclass(frozen=True)
class TestProfileTaxonomyOptions:
    taxonomy_path: str | Path = DEFAULT_TEST_PROFILE_TAXONOMY_PATH
    legacy_profiles_path: str | Path = DEFAULT_TEST_PROFILES_PATH
    output_json: str | Path = DEFAULT_TAXONOMY_REPORT_JSON
    output_markdown: str | Path = DEFAULT_TAXONOMY_REPORT_MARKDOWN
    write_report: bool = False


class TestProfileTaxonomyRunner:
    """Validate the POST-H-029-A operational test profile taxonomy.

    The runner is deliberately read-only. It validates profile metadata, legacy
    tests.run aliases, command allowlists and safety flags, but it never executes
    pytest/npm commands. Real test execution remains approval-gated through
    tests.run or explicit operator commands.
    """

    def __init__(self, root: Path, options: TestProfileTaxonomyOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or TestProfileTaxonomyOptions()
        self.taxonomy_path = Path(self.options.taxonomy_path)
        self.legacy_profiles_path = Path(self.options.legacy_profiles_path)

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        taxonomy = self._load_json(self.taxonomy_path, findings, "TEST_PROFILE_TAXONOMY_LOAD_ERROR")
        legacy_profiles = self._load_json(self.legacy_profiles_path, findings, "TEST_PROFILE_TAXONOMY_LEGACY_PROFILES_LOAD_ERROR")

        schema_result = SchemaValidator(self.root).validate(
            schema=TEST_PROFILE_TAXONOMY_CONTRACT,
            instance=self.taxonomy_path,
        )
        if not schema_result.ok:
            findings.extend(self._prefixed_findings(schema_result, "TEST_PROFILE_TAXONOMY_SCHEMA"))

        profiles = [item for item in taxonomy.get("profiles", []) if isinstance(item, dict)]
        aliases = [item for item in taxonomy.get("legacy_aliases", []) if isinstance(item, dict)]
        legacy_runtime_profiles = [item for item in legacy_profiles.get("profiles", []) if isinstance(item, dict)]

        checks = {
            "schema": self._schema_check(schema_result),
            "required_profiles": self._required_profiles_check(profiles, findings),
            "profile_semantics": self._profile_semantics_check(profiles, findings),
            "legacy_aliases": self._legacy_aliases_check(aliases, legacy_runtime_profiles, findings),
            "command_allowlist": self._command_allowlist_check(profiles, findings),
            "safety_flags": self._safety_flags_check(taxonomy, profiles, findings),
        }

        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
        ok = all(bool(item.get("ok")) for item in checks.values()) and not blocking
        summary = {
            "created_by": POST_H_029_A_CREATED_BY,
            "status": "implemented-initial",
            "decision": "PASS" if ok else "BLOCK",
            "test_profile_taxonomy_valid": ok,
            "profiles_total": len(profiles),
            "required_profiles_total": len(REQUIRED_PROFILE_IDS),
            "required_profiles_present_total": int(checks["required_profiles"].get("required_profiles_present_total", 0)),
            "legacy_aliases_total": len(aliases),
            "legacy_aliases_present_total": int(checks["legacy_aliases"].get("legacy_aliases_present_total", 0)),
            "allowed_commands_total": int(checks["command_allowlist"].get("allowed_commands_total", 0)),
            "unsafe_commands_total": int(checks["command_allowlist"].get("unsafe_commands_total", 0)),
            "profiles_requiring_approval_total": int(checks["profile_semantics"].get("profiles_requiring_approval_total", 0)),
            "high_risk_without_approval_total": int(checks["profile_semantics"].get("high_risk_without_approval_total", 0)),
            "full_regression_profile_present": "full" in {str(item.get("profile_id")) for item in profiles},
            "release_candidate_local_present": "release-candidate-local" in {str(item.get("profile_id")) for item in profiles},
            "checks_total": len(checks),
            "checks_passed": sum(1 for item in checks.values() if bool(item.get("ok"))),
            "findings_total": len(findings),
            "warnings_total": len(warnings),
            "blocking_findings_total": len(blocking),
            "reports_written": False,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "tests_executed": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        report = {
            "schema_version": "1.0",
            "report_id": "devpilot-test-profile-taxonomy-report",
            "created_by": POST_H_029_A_CREATED_BY,
            "status": "pass" if ok else "blocked",
            "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary": summary,
            "checks": checks,
            "taxonomy_path": str(self.taxonomy_path).replace("\\", "/"),
            "legacy_profiles_path": str(self.legacy_profiles_path).replace("\\", "/"),
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
                "POST-H-029-A defines an operational test profile taxonomy; it does not execute tests.",
                "Real pytest execution remains approval-gated by tests.run or explicit operator commands.",
                "Full regression remains available and required by future regression guard rules; it is not removed by tiers.",
                "This is implemented-initial taxonomy; POST-H-029-B/C/D/E add impact rules, recommendations, RC profile and historical guard.",
            ],
        }
        reports: dict[str, str] = {}
        if self.options.write_report:
            report["summary"]["reports_written"] = True
            reports = self._write_reports(report)
        return CommandResult(
            command=TEST_PROFILE_TAXONOMY_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False),
            message="Test profile taxonomy passed." if ok else "Test profile taxonomy has blocking findings.",
            data={"summary": report["summary"], "report": report, "reports": reports, "notes": report["notes"]},
            findings=findings or [Finding("TEST_PROFILE_TAXONOMY_PASS", "Test profile taxonomy passed.", Severity.INFO, metadata=summary)],
        )

    def _load_json(self, path: Path, findings: list[Finding], finding_id: str) -> dict[str, Any]:
        try:
            return json.loads((self.root / path).read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(Finding(finding_id, f"Could not load {path}: {exc}", Severity.ERROR, path=str(path).replace("\\", "/")))
            return {}

    def _schema_check(self, result: CommandResult) -> dict[str, Any]:
        return {"ok": result.ok, "command": result.command, "exit_code": int(result.exit_code)}

    def _required_profiles_check(self, profiles: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        profile_ids = {str(item.get("profile_id")) for item in profiles}
        missing = sorted(REQUIRED_PROFILE_IDS - profile_ids)
        for profile_id in missing:
            findings.append(Finding("TEST_PROFILE_TAXONOMY_REQUIRED_PROFILE_MISSING", f"Required test profile is missing: {profile_id}", Severity.BLOCK, path=str(self.taxonomy_path), metadata={"profile_id": profile_id}))
        return {"ok": not missing, "required_profiles": sorted(REQUIRED_PROFILE_IDS), "missing_profiles": missing, "required_profiles_present_total": len(REQUIRED_PROFILE_IDS) - len(missing)}

    def _profile_semantics_check(self, profiles: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        high_without_approval: list[str] = []
        approval_total = 0
        bad_timeouts: list[str] = []
        missing_full_rules: list[str] = []
        for profile in profiles:
            profile_id = str(profile.get("profile_id"))
            timeout = int(profile.get("timeout_seconds", 0) or 0)
            if timeout <= 0:
                bad_timeouts.append(profile_id)
                findings.append(Finding("TEST_PROFILE_TAXONOMY_TIMEOUT_INVALID", f"Profile has invalid timeout: {profile_id}", Severity.BLOCK, path=str(self.taxonomy_path), metadata={"profile_id": profile_id}))
            if profile.get("requires_approval_for_execution") is True:
                approval_total += 1
            if profile_id in HIGH_RISK_PROFILE_IDS and profile.get("requires_approval_for_execution") is not True:
                high_without_approval.append(profile_id)
                findings.append(Finding("TEST_PROFILE_TAXONOMY_HIGH_RISK_APPROVAL_REQUIRED", f"High-risk profile must require approval for execution: {profile_id}", Severity.BLOCK, path=str(self.taxonomy_path), metadata={"profile_id": profile_id}))
            if profile_id in {"full", "release", "release-candidate-local"} and not profile.get("full_regression_rules"):
                missing_full_rules.append(profile_id)
                findings.append(Finding("TEST_PROFILE_TAXONOMY_FULL_REGRESSION_RULES_MISSING", f"Profile must document full regression rules: {profile_id}", Severity.BLOCK, path=str(self.taxonomy_path), metadata={"profile_id": profile_id}))
        return {"ok": not high_without_approval and not bad_timeouts and not missing_full_rules, "profiles_requiring_approval_total": approval_total, "high_risk_without_approval_total": len(high_without_approval), "bad_timeouts": bad_timeouts, "profiles_missing_full_regression_rules": missing_full_rules}

    def _legacy_aliases_check(self, aliases: list[dict[str, Any]], runtime_profiles: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        alias_ids = {str(item.get("legacy_profile_id")) for item in aliases}
        runtime_ids = {str(item.get("profile_id")) for item in runtime_profiles}
        missing_aliases = sorted(LEGACY_PROFILE_IDS - alias_ids)
        missing_runtime = sorted(LEGACY_PROFILE_IDS - runtime_ids)
        for profile_id in missing_aliases:
            findings.append(Finding("TEST_PROFILE_TAXONOMY_LEGACY_ALIAS_MISSING", f"Legacy test profile alias is missing: {profile_id}", Severity.BLOCK, path=str(self.taxonomy_path), metadata={"profile_id": profile_id}))
        for profile_id in missing_runtime:
            findings.append(Finding("TEST_PROFILE_TAXONOMY_RUNTIME_PROFILE_MISSING", f"tests.run legacy runtime profile is missing: {profile_id}", Severity.BLOCK, path=str(self.legacy_profiles_path), metadata={"profile_id": profile_id}))
        return {"ok": not missing_aliases and not missing_runtime, "legacy_aliases_required": sorted(LEGACY_PROFILE_IDS), "missing_aliases": missing_aliases, "missing_runtime_profiles": missing_runtime, "legacy_aliases_present_total": len(LEGACY_PROFILE_IDS) - len(missing_aliases)}

    def _command_allowlist_check(self, profiles: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        unsafe: list[dict[str, str]] = []
        allowed_total = 0
        for profile in profiles:
            profile_id = str(profile.get("profile_id"))
            for command in profile.get("allowed_commands", []) or []:
                command_text = str(command)
                if self._is_safe_command(command_text):
                    allowed_total += 1
                    continue
                item = {"profile_id": profile_id, "command": command_text}
                unsafe.append(item)
                findings.append(Finding("TEST_PROFILE_TAXONOMY_UNSAFE_COMMAND", f"Profile contains unsafe or non-allowlisted command: {profile_id}", Severity.BLOCK, path=str(self.taxonomy_path), metadata=item))
        return {"ok": not unsafe, "allowed_commands_total": allowed_total, "unsafe_commands_total": len(unsafe), "unsafe_commands": unsafe}

    def _safety_flags_check(self, taxonomy: dict[str, Any], profiles: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        bad_flags: list[dict[str, Any]] = []
        for key in ("network_used", "external_api_used", "remote_execution_enabled", "connector_write_enabled", "plugin_execution_enabled", "tests_executed_from_taxonomy"):
            expected = False
            value = (taxonomy.get("safety") or {}).get(key)
            if value is not expected:
                item = {"scope": "taxonomy", "flag": key, "value": value}
                bad_flags.append(item)
                findings.append(Finding("TEST_PROFILE_TAXONOMY_SAFETY_FLAG_UNSAFE", f"Taxonomy safety flag must be false: {key}", Severity.BLOCK, path=str(self.taxonomy_path), metadata=item))
        for profile in profiles:
            profile_id = str(profile.get("profile_id"))
            for key in ("network_allowed", "external_api_allowed", "mutations_allowed", "source_mutations_allowed", "allow_shell"):
                if profile.get(key) is not False:
                    item = {"profile_id": profile_id, "flag": key, "value": profile.get(key)}
                    bad_flags.append(item)
                    findings.append(Finding("TEST_PROFILE_TAXONOMY_PROFILE_SAFETY_FLAG_UNSAFE", f"Profile safety flag must be false: {profile_id}.{key}", Severity.BLOCK, path=str(self.taxonomy_path), metadata=item))
        return {"ok": not bad_flags, "unsafe_flags_total": len(bad_flags), "unsafe_flags": bad_flags}

    def _is_safe_command(self, command: str) -> bool:
        normalized = re.sub(r"\s+", " ", command.strip())
        lower = normalized.lower()
        if not normalized:
            return False
        if any(token in lower for token in DANGEROUS_SHELL_TOKENS):
            return False
        return any(normalized.startswith(prefix) for prefix in ALLOWED_COMMAND_PREFIXES)

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        md_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(self._render_markdown(report), encoding="utf-8")
        return {"json": str(self.options.output_json).replace("\\", "/"), "markdown": str(self.options.output_markdown).replace("\\", "/")}

    def _render_markdown(self, report: dict[str, Any]) -> str:
        summary = report["summary"]
        lines = ["# POST-H-029-A — Test profile taxonomy report", "", f"Decision: **{summary['decision']}**", "", "## Summary", ""]
        for key in sorted(summary):
            lines.append(f"- `{key}`: `{summary[key]}`")
        lines.extend(["", "## Notes", ""])
        for note in report.get("notes", []):
            lines.append(f"- {note}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _prefixed_findings(result: CommandResult, prefix: str) -> list[Finding]:
        out: list[Finding] = []
        for finding in result.findings:
            if finding.severity == Severity.INFO:
                continue
            out.append(Finding(id=f"{prefix}_{finding.id}", message=finding.message, severity=finding.severity, path=finding.path, metadata={"source_command": result.command, "source_finding_id": finding.id, **(finding.metadata or {})}))
        return out


def run_test_profile_taxonomy(root: Path, options: TestProfileTaxonomyOptions | None = None) -> CommandResult:
    return TestProfileTaxonomyRunner(root, options).run()
