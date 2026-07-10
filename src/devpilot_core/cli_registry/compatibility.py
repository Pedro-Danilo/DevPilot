from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

CLI_COMPATIBILITY_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-CLI-COMPATIBILITY-REPORT-V1"
CLI_COMPATIBILITY_REPORT_CONTRACT = "CliCompatibilityReport"
CLI_COMPATIBILITY_SUBGATE = "cli-boundary-hotspot-reduction"
DEFAULT_CONTRACTS_PATH = Path(".devpilot/cli_registry/cli_compatibility_contracts.json")
DEFAULT_MATRIX_PATH = Path(".devpilot/cli_registry/command_ownership_matrix.json")
DEFAULT_REPORT_JSON = Path("outputs/reports/cli_compatibility_report.json")
DEFAULT_REPORT_MARKDOWN = Path("outputs/reports/cli_compatibility_report.md")

REQUIRED_JSON_ENVELOPE_KEYS = ("command", "ok", "exit_code", "message", "data", "findings")
REQUIRED_NORMALIZATION_KEYS = (
    "timestamp_fields",
    "path_fields",
    "duration_fields",
    "volatile_metadata_fields",
)


@dataclass(frozen=True)
class CliCompatibilityOptions:
    contracts_path: Path = DEFAULT_CONTRACTS_PATH
    matrix_path: Path = DEFAULT_MATRIX_PATH
    write_report: bool = False
    output_json: Path = DEFAULT_REPORT_JSON
    output_markdown: Path = DEFAULT_REPORT_MARKDOWN
    run_smoke: bool = False
    smoke_timeout_seconds: int = 30


class CliCompatibilityContractRunner:
    """Validate CLI compatibility contracts without dynamic handler routing.

    POST-H-030-E deliberately keeps compatibility checks metadata-first. The
    runner reads source-controlled contracts and the ownership matrix, validates
    coverage for migrated/high-risk commands, and optionally runs only curated
    safe smoke commands declared in the fixture. It never accepts arbitrary shell
    command text from users and keeps smoke execution opt-in.
    """

    def __init__(self, root: Path, options: CliCompatibilityOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or CliCompatibilityOptions()

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        contracts_payload = self._load_json(self.options.contracts_path, findings, "CLI_COMPATIBILITY_CONTRACTS")
        matrix_payload = self._load_json(self.options.matrix_path, findings, "CLI_OWNERSHIP_MATRIX")
        if contracts_payload is None or matrix_payload is None:
            report = self._report({}, [], findings, status="blocked", smoke_results=[])
            return self._result(report, findings)

        commands = {item.get("command_id"): item for item in matrix_payload.get("commands", []) if item.get("command_id")}
        contracts = [item for item in contracts_payload.get("contracts", []) if isinstance(item, dict)]
        contract_by_command = {item.get("command_id"): item for item in contracts if item.get("command_id")}

        required_ids = self._required_command_ids(commands)
        missing_required = sorted(required_ids - set(contract_by_command))
        extra_contracts = sorted(set(contract_by_command) - set(commands))
        duplicate_contracts = sorted(self._duplicates([item.get("command_id") for item in contracts]))
        invalid_contract_ids = self._invalid_contracts(contracts, commands)
        unsafe_contracts = self._unsafe_contracts(contracts)
        non_normalized_contracts = self._non_normalized_contracts(contracts)
        missing_json_envelope = self._missing_json_envelope(contracts)
        smoke_results: list[dict[str, Any]] = []

        for command_id in missing_required:
            findings.append(
                Finding(
                    id="CLI_COMPAT_REQUIRED_CONTRACT_MISSING",
                    message="A migrated, high/critical or required governance command lacks a compatibility contract.",
                    severity=Severity.BLOCK,
                    metadata={"command_id": command_id},
                )
            )
        for command_id in extra_contracts:
            findings.append(Finding("CLI_COMPAT_UNKNOWN_COMMAND", "Compatibility contract references an unknown CLI command.", Severity.BLOCK, metadata={"command_id": command_id}))
        for command_id in duplicate_contracts:
            findings.append(Finding("CLI_COMPAT_DUPLICATE_CONTRACT", "Duplicate compatibility contract detected.", Severity.BLOCK, metadata={"command_id": command_id}))
        for command_id in invalid_contract_ids:
            findings.append(Finding("CLI_COMPAT_INVALID_CONTRACT_ID", "Contract id must be cli-compat:<command_id>.", Severity.BLOCK, metadata={"command_id": command_id}))
        for command_id in unsafe_contracts:
            findings.append(Finding("CLI_COMPAT_UNSAFE_CONTRACT", "Compatibility contracts must forbid network, external APIs and destructive execution.", Severity.BLOCK, metadata={"command_id": command_id}))
        for command_id in non_normalized_contracts:
            findings.append(Finding("CLI_COMPAT_NORMALIZATION_MISSING", "Compatibility contract lacks required normalization keys for volatile fields.", Severity.BLOCK, metadata={"command_id": command_id}))
        for command_id in missing_json_envelope:
            findings.append(Finding("CLI_COMPAT_JSON_ENVELOPE_INCOMPLETE", "Compatibility contract must require the CommandResult JSON envelope keys.", Severity.BLOCK, metadata={"command_id": command_id}))

        if self.options.run_smoke and not any(finding.severity in {Severity.BLOCK, Severity.ERROR} for finding in findings):
            smoke_results = self._run_smoke_contracts(contracts, findings)

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        status = "pass" if not blocking else "blocked"
        if not findings:
            findings.append(
                Finding(
                    id="CLI_COMPATIBILITY_CONTRACTS_PASS",
                    message="CLI compatibility contracts cover migrated/high-risk commands and preserve local-first safety invariants.",
                    severity=Severity.INFO,
                    metadata={"contracts_total": len(contracts), "required_contracts_total": len(required_ids)},
                )
            )

        summary = {
            "created_by": "POST-H-030-E",
            "status": "implemented-initial",
            "decision": "PASS" if status == "pass" else "BLOCK",
            "quality_gate_subgate": CLI_COMPATIBILITY_SUBGATE,
            "contracts_path": str(self.options.contracts_path).replace("\\", "/"),
            "matrix_path": str(self.options.matrix_path).replace("\\", "/"),
            "commands_total": len(commands),
            "contracts_total": len(contracts),
            "required_contracts_total": len(required_ids),
            "required_contracts_present_total": len(required_ids - set(missing_required)),
            "migrated_commands_total": sum(1 for item in commands.values() if item.get("migration_state") == "already-migrated"),
            "high_or_critical_commands_total": sum(1 for item in commands.values() if item.get("risk_level") in {"high", "critical"}),
            "tier_0_contracts_total": sum(1 for item in contracts if item.get("tier") == "tier_0"),
            "tier_1_contracts_total": sum(1 for item in contracts if item.get("tier") == "tier_1"),
            "tier_2_contracts_total": sum(1 for item in contracts if item.get("tier") == "tier_2"),
            "missing_required_contracts_total": len(missing_required),
            "unknown_contract_commands_total": len(extra_contracts),
            "duplicate_contracts_total": len(duplicate_contracts),
            "invalid_contract_ids_total": len(invalid_contract_ids),
            "unsafe_contracts_total": len(unsafe_contracts),
            "non_normalized_contracts_total": len(non_normalized_contracts),
            "json_envelope_incomplete_total": len(missing_json_envelope),
            "smoke_enabled": self.options.run_smoke,
            "smoke_contracts_total": sum(1 for item in contracts if item.get("smoke", {}).get("enabled") is True),
            "smoke_executed_total": len(smoke_results),
            "smoke_failed_total": sum(1 for item in smoke_results if not item.get("ok")),
            "blocking_findings_total": len(blocking),
            "tests_executed": False,
            "dry_run": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": bool(self.options.write_report),
            "preliminary": True,
        }
        report = self._report(summary, contracts, findings, status=status, smoke_results=smoke_results)
        if self.options.write_report:
            paths = self._write_report(report)
            report["summary"]["report_paths"] = paths
        return self._result(report, findings)

    def _load_json(self, relative_path: Path, findings: list[Finding], label: str) -> dict[str, Any] | None:
        path = self.root / relative_path
        if not path.exists():
            findings.append(Finding(f"{label}_MISSING", f"Required CLI compatibility input is missing: {relative_path}", Severity.BLOCK, path=str(relative_path).replace("\\", "/")))
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(Finding(f"{label}_INVALID_JSON", f"Required CLI compatibility input is not valid JSON: {exc}", Severity.ERROR, path=str(relative_path).replace("\\", "/")))
            return None
        if not isinstance(payload, dict):
            findings.append(Finding(f"{label}_INVALID_SHAPE", "Required CLI compatibility input must be a JSON object.", Severity.ERROR, path=str(relative_path).replace("\\", "/")))
            return None
        return payload

    def _required_command_ids(self, commands: dict[str, dict[str, Any]]) -> set[str]:
        required = {
            command_id
            for command_id, item in commands.items()
            if item.get("migration_state") == "already-migrated" or item.get("risk_level") in {"high", "critical"}
        }
        required.update({"cli-registry.guard", "cli-registry.compatibility", "quality-gate.run"})
        return required

    def _invalid_contracts(self, contracts: list[dict[str, Any]], commands: dict[str, dict[str, Any]]) -> list[str]:
        invalid: list[str] = []
        for item in contracts:
            command_id = item.get("command_id")
            if not command_id or command_id not in commands:
                continue
            if item.get("contract_id") != f"cli-compat:{command_id}":
                invalid.append(command_id)
        return sorted(invalid)

    def _unsafe_contracts(self, contracts: list[dict[str, Any]]) -> list[str]:
        invalid: list[str] = []
        for item in contracts:
            safety = item.get("safety", {})
            if not isinstance(safety, dict):
                invalid.append(item.get("command_id", "unknown"))
                continue
            if (
                safety.get("network_allowed") is not False
                or safety.get("external_api_allowed") is not False
                or safety.get("remote_execution_allowed") is not False
                or safety.get("connector_write_allowed") is not False
                or safety.get("plugin_execution_allowed") is not False
                or safety.get("destructive_execution_allowed") is not False
            ):
                invalid.append(item.get("command_id", "unknown"))
        return sorted(invalid)

    def _non_normalized_contracts(self, contracts: list[dict[str, Any]]) -> list[str]:
        invalid: list[str] = []
        for item in contracts:
            normalization = item.get("normalization", {})
            if not isinstance(normalization, dict) or any(key not in normalization for key in REQUIRED_NORMALIZATION_KEYS):
                invalid.append(item.get("command_id", "unknown"))
        return sorted(invalid)

    def _missing_json_envelope(self, contracts: list[dict[str, Any]]) -> list[str]:
        invalid: list[str] = []
        for item in contracts:
            required = set(item.get("json_contract", {}).get("required_top_level_keys", []))
            if not set(REQUIRED_JSON_ENVELOPE_KEYS).issubset(required):
                invalid.append(item.get("command_id", "unknown"))
        return sorted(invalid)

    def _run_smoke_contracts(self, contracts: list[dict[str, Any]], findings: list[Finding]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        env = dict(os.environ)
        src_path = str((self.root / "src").resolve())
        env["PYTHONPATH"] = src_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        for contract in contracts:
            smoke = contract.get("smoke", {})
            if not isinstance(smoke, dict) or smoke.get("enabled") is not True:
                continue
            argv = smoke.get("argv", [])
            command_id = contract.get("command_id", "unknown")
            if not isinstance(argv, list) or not all(isinstance(part, str) for part in argv):
                findings.append(Finding("CLI_COMPAT_SMOKE_ARGV_INVALID", "Smoke contract argv must be a string list.", Severity.BLOCK, metadata={"command_id": command_id}))
                continue
            if smoke.get("safe") is not True:
                findings.append(Finding("CLI_COMPAT_SMOKE_NOT_MARKED_SAFE", "Smoke contract must be explicitly marked safe.", Severity.BLOCK, metadata={"command_id": command_id}))
                continue
            try:
                completed = subprocess.run(
                    [sys.executable, "-m", "devpilot_core", *argv],
                    cwd=self.root,
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=self.options.smoke_timeout_seconds,
                    check=False,
                )
                parsed = json.loads(completed.stdout)
                top_level_ok = set(REQUIRED_JSON_ENVELOPE_KEYS).issubset(parsed)
                expected_codes = contract.get("exit_code_contract", {}).get("allowed_exit_codes", [0, 1, 2, 3])
                ok = completed.returncode in expected_codes and top_level_ok
                results.append({
                    "command_id": command_id,
                    "argv": argv,
                    "returncode": completed.returncode,
                    "ok": ok,
                    "json_envelope_ok": top_level_ok,
                })
                if not ok:
                    findings.append(Finding("CLI_COMPAT_SMOKE_FAILED", "Smoke command did not preserve expected exit code or JSON envelope.", Severity.BLOCK, metadata={"command_id": command_id, "returncode": completed.returncode, "json_envelope_ok": top_level_ok}))
            except Exception as exc:
                results.append({"command_id": command_id, "argv": argv, "ok": False, "error": str(exc)})
                findings.append(Finding("CLI_COMPAT_SMOKE_ERROR", f"Smoke command failed to execute deterministically: {exc}", Severity.ERROR, metadata={"command_id": command_id}))
        return results

    def _report(self, summary: dict[str, Any], contracts: list[dict[str, Any]], findings: list[Finding], *, status: str, smoke_results: list[dict[str, Any]]) -> dict[str, Any]:
        if not summary:
            summary = {
                "created_by": "POST-H-030-E",
                "status": "implemented-initial",
                "decision": "BLOCK",
                "quality_gate_subgate": CLI_COMPATIBILITY_SUBGATE,
                "contracts_total": 0,
                "required_contracts_total": 0,
                "blocking_findings_total": sum(1 for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}),
                "tests_executed": False,
                "dry_run": True,
                "read_only": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "reports_written": False,
                "preliminary": True,
            }
        return {
            "schema_version": "1.0",
            "schema_id": CLI_COMPATIBILITY_REPORT_SCHEMA_ID,
            "report_id": "devpilot-cli-compatibility-report",
            "created_by": "POST-H-030-E",
            "status": status,
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary": summary,
            "contracts": contracts,
            "smoke_results": smoke_results,
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "source_mutations_performed": False,
            },
            "findings": [finding.to_dict() for finding in findings],
            "notes": [
                "POST-H-030-E implements compatibility contracts as source-controlled fixtures and schema-backed reports.",
                "Smoke execution is opt-in and limited to safe argv declared in the fixture; static validation remains the default.",
                "Updating fixtures after expected changes requires audit documentation and source review; snapshots must not hide breaking changes.",
            ],
        }

    def _write_report(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(render_cli_compatibility_markdown(report), encoding="utf-8")
        return {
            "json": str(self.options.output_json).replace("\\", "/"),
            "markdown": str(self.options.output_markdown).replace("\\", "/"),
        }

    def _result(self, report: dict[str, Any], findings: list[Finding]) -> CommandResult:
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        ok = not blocking
        return CommandResult(
            command="cli-registry compatibility",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="CLI compatibility contracts passed." if ok else "CLI compatibility contracts blocked.",
            data={"summary": report.get("summary", {}), "report": report},
            findings=findings,
        )

    @staticmethod
    def _duplicates(values: list[Any]) -> list[Any]:
        seen: set[Any] = set()
        duplicates: set[Any] = set()
        for value in values:
            if value in seen:
                duplicates.add(value)
            seen.add(value)
        return sorted(item for item in duplicates if item is not None)


def render_cli_compatibility_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# CLI Compatibility Report",
        "",
        f"- Created by: `{report.get('created_by')}`",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{summary.get('decision')}`",
        f"- Subgate: `{summary.get('quality_gate_subgate')}`",
        f"- Contracts total: `{summary.get('contracts_total')}`",
        f"- Required contracts total: `{summary.get('required_contracts_total')}`",
        f"- Missing required contracts: `{summary.get('missing_required_contracts_total')}`",
        f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
        f"- Smoke enabled: `{summary.get('smoke_enabled')}`",
        "",
        "## Safety",
        "",
        "- Local-first: `true`",
        "- Network used: `false`",
        "- External API used: `false`",
        "- Remote execution enabled: `false`",
        "- Connector write enabled: `false`",
        "- Plugin execution enabled: `false`",
        "",
        "## Notes",
        "",
    ]
    for note in report.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)
