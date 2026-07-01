from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.remote.runner import RemoteRunnerRegistry, RemoteRunnerStatusOptions
from devpilot_core.schemas import SchemaValidator

DEFAULT_REMOTE_READINESS_CRITERIA = ".devpilot/remote/remote_readiness_criteria.json"
DEFAULT_REMOTE_READINESS_CRITERIA_SCHEMA = "docs/schemas/remote_readiness_criteria.schema.json"
DEFAULT_REMOTE_RUNNER_REGISTRY = ".devpilot/remote/runner_registry.json"
DEFAULT_REMOTE_RUNNER_SCHEMA = "docs/schemas/remote_runner.schema.json"
DEFAULT_REMOTE_READINESS_REPORT_SCHEMA = "RemoteReadinessReport"
_BLOCKING_SEVERITIES = {Severity.BLOCK, Severity.ERROR, Severity.FAIL}


@dataclass(frozen=True)
class RemoteReadinessOptions:
    """Options for POST-H-021-C remote readiness reporting."""

    criteria_path: str = DEFAULT_REMOTE_READINESS_CRITERIA
    criteria_schema_path: str = DEFAULT_REMOTE_READINESS_CRITERIA_SCHEMA
    registry_path: str = DEFAULT_REMOTE_RUNNER_REGISTRY
    registry_schema_path: str = DEFAULT_REMOTE_RUNNER_SCHEMA


class RemoteReadinessChecker:
    """Build a local read-only readiness report for disabled remote runner design.

    The checker reads only source-controlled remote metadata and schemas. It does
    not execute commands, open network transports, read secrets, contact remote
    services or mutate source files. A report is evidence of design readiness
    only, not execution authorization.
    """

    def __init__(self, root: Path, *, options: RemoteReadinessOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RemoteReadinessOptions()

    def check(self) -> CommandResult:
        findings: list[Finding] = []
        criteria = self._read_json(self.options.criteria_path, findings, required=True)
        runner_status = RemoteRunnerRegistry(
            self.root,
            options=RemoteRunnerStatusOptions(
                registry_path=self.options.registry_path,
                schema_path=self.options.registry_schema_path,
            ),
        ).validate()
        if not runner_status.ok:
            findings.extend(runner_status.findings)

        criteria_schema = SchemaValidator(self.root).validate(
            schema=self.options.criteria_schema_path,
            instance=self.options.criteria_path,
        )
        if not criteria_schema.ok:
            findings.extend(criteria_schema.findings)

        report = self._report(criteria=criteria, runner_status=runner_status, findings=findings)
        report_schema = SchemaValidator(self.root).validate_payload(
            schema=DEFAULT_REMOTE_READINESS_REPORT_SCHEMA,
            payload=report,
            instance_label="remote_readiness_report",
        )
        if not report_schema.ok:
            findings.extend(report_schema.findings)

        blocking = _blocking(findings)
        report["blocking_findings_total"] = len(blocking)
        report["summary"]["blocking_findings_total"] = len(blocking)
        report["summary"]["schema_valid"] = bool(report_schema.ok)

        ok = not blocking and bool(report_schema.ok)
        return CommandResult(
            "remote runner readiness",
            ok,
            ExitCode.PASS if ok else _exit_code(blocking),
            "Remote readiness report confirms design-only disabled baseline." if ok else "Remote readiness report found blocking findings.",
            data={
                "summary": report["summary"],
                "report": report,
                "criteria": criteria,
                "runner_status": runner_status.data,
            },
            findings=findings
            or [
                Finding(
                    "REMOTE_READINESS_REPORT_PASS",
                    "Remote readiness report confirms remote runner remains disabled, read-only and design-only.",
                    Severity.INFO,
                    metadata=report["summary"],
                )
            ],
        )

    def _report(self, *, criteria: dict[str, Any], runner_status: CommandResult, findings: list[Finding]) -> dict[str, Any]:
        runner_summary = runner_status.data.get("summary", {}) if isinstance(runner_status.data, dict) else {}
        no_go = criteria.get("no_go_gates", {}) if isinstance(criteria, dict) else {}
        safety = criteria.get("safety", {}) if isinstance(criteria, dict) else {}
        required_before_enablement = list(criteria.get("required_before_enablement", [])) if isinstance(criteria, dict) else []
        readiness_level = "remote-design-only"
        blocking = _blocking(findings)
        summary = {
            "created_by": "POST-H-021-C",
            "status": "implemented-initial",
            "preliminary": True,
            "readiness_level": readiness_level,
            "decision_status": criteria.get("decision_status"),
            "remote_execution_allowed": criteria.get("remote_execution_allowed") is True,
            "remote_runner_enabled": bool(runner_summary.get("remote_runner_enabled", False)),
            "execution_allowed": bool(runner_summary.get("execution_allowed", False)),
            "remote_execution_used": bool(runner_summary.get("remote_execution_used", False)),
            "network_used": bool(runner_summary.get("network_used", False)),
            "external_api_used": bool(runner_summary.get("external_api_used", False)),
            "credentials_required": bool(runner_summary.get("credentials_required", False)) or bool(safety.get("credentials_required", False)),
            "secrets_read": bool(runner_summary.get("secrets_read", False)) or bool(safety.get("secrets_read", False)),
            "mutations_performed": False,
            "source_mutations_performed": False,
            "requires_future_adr": criteria.get("requires_future_adr") is True,
            "required_before_enablement_total": len(required_before_enablement),
            "runner_registry_valid": runner_status.ok,
            "blocking_findings_total": len(blocking),
            "schema_valid": False,
        }
        for flag in (
            "remote_runner_enabled",
            "remote_execution_used",
            "network_required",
            "external_api_required",
            "secrets_required",
            "credentials_required",
            "mutations_performed",
            "source_mutations_performed",
            "connector_write_enabled",
            "plugin_execution_enabled",
        ):
            if no_go.get(flag) is not False:
                findings.append(
                    Finding(
                        "REMOTE_READINESS_NO_GO_GATE_BLOCKED",
                        "Remote readiness no-go gate is not explicitly false.",
                        Severity.BLOCK,
                        path=self.options.criteria_path,
                        metadata={"flag": flag},
                    )
                )
        for flag in (
            "remote_execution_allowed",
            "remote_runner_enabled",
            "execution_allowed",
            "remote_execution_used",
            "network_used",
            "external_api_used",
            "credentials_required",
            "secrets_read",
        ):
            if summary[flag]:
                findings.append(
                    Finding(
                        "REMOTE_READINESS_UNSAFE_FLAG_BLOCKED",
                        "Remote readiness report observed an unsafe remote flag.",
                        Severity.BLOCK,
                        metadata={"flag": flag},
                    )
                )
        blocking = _blocking(findings)
        summary["blocking_findings_total"] = len(blocking)
        return {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-REMOTE-READINESS-REPORT-V1",
            "report_id": "devpilot-remote-readiness-report",
            "created_by": "POST-H-021-C",
            "status": "implemented-initial",
            "generated_at_utc": _now_utc(),
            "ok": not blocking,
            "decision_status": criteria.get("decision_status"),
            "future_adr_required": criteria.get("requires_future_adr") is True,
            "readiness_level": readiness_level,
            "remote_runner_enabled": summary["remote_runner_enabled"],
            "remote_execution_used": summary["remote_execution_used"],
            "network_used": summary["network_used"],
            "external_api_used": summary["external_api_used"],
            "credentials_required": summary["credentials_required"],
            "secrets_read": summary["secrets_read"],
            "blocking_findings_total": len(blocking),
            "summary": summary,
            "required_before_enablement": required_before_enablement,
            "no_go_gates": no_go,
            "findings": [finding.to_dict() for finding in findings],
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "remote_execution_enabled": False,
                "remote_runner_enabled": False,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "credentials_required": False,
                "secrets_read": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
            },
            "notes": [
                "POST-H-021-C readiness report is read-only design evidence.",
                "The report does not authorize remote execution, transport, credentials, network or shell.",
                "Future enablement remains blocked pending POST-H-022, POST-H-023 and a future ADR.",
            ],
        }

    def _read_json(self, path: str, findings: list[Finding], *, required: bool) -> dict[str, Any]:
        resolved = self._resolve(path)
        if not resolved.exists():
            if required:
                findings.append(Finding("REMOTE_READINESS_SOURCE_MISSING", "Remote readiness source file is missing.", Severity.BLOCK, path=path))
            return {}
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("REMOTE_READINESS_SOURCE_INVALID_JSON", "Remote readiness source file is invalid JSON.", Severity.ERROR, path=path, metadata={"error": str(exc)}))
            return {}
        return payload if isinstance(payload, dict) else {}

    def _resolve(self, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = self.root / path
        return path.resolve()


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _blocking(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in _BLOCKING_SEVERITIES]


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS
