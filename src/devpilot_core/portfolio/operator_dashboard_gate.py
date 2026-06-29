from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.portfolio.operator_dashboard import OperatorDashboardAggregator, OperatorDashboardAggregatorOptions
from devpilot_core.schemas import SchemaValidator

POST_H_015_E_CREATED_BY = "POST-H-015-E"
OPERATOR_DASHBOARD_READY_SUBGATE = "operator-dashboard-ready"


@dataclass(frozen=True)
class OperatorDashboardReadyGateOptions:
    """Options for the local operator dashboard quality subgate."""

    generated_at_utc: str | None = None
    write_report: bool = False


class OperatorDashboardReadyGate:
    """Validate the local operator dashboard as an operational quality gate.

    The gate composes the existing read-only aggregator and schema validator.
    It does not call network services, start a server, execute shell commands or
    mutate source files. When ``write_report=True`` it delegates snapshot
    JSON/Markdown writing to the aggregator under ``outputs/reports``.
    """

    def __init__(self, root: Path, options: OperatorDashboardReadyGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or OperatorDashboardReadyGateOptions()

    def run(self) -> CommandResult:
        aggregate = OperatorDashboardAggregator(
            self.root,
            OperatorDashboardAggregatorOptions(
                generated_at_utc=self.options.generated_at_utc,
                write_report=self.options.write_report,
            ),
        ).build()
        snapshot = aggregate.data.get("snapshot") if isinstance(aggregate.data, dict) else None
        findings: list[Finding] = self._prefixed_findings(aggregate, prefix="aggregate")

        schema_result: CommandResult | None = None
        if isinstance(snapshot, dict):
            schema_result = SchemaValidator(self.root).validate_payload(
                schema="OperatorDashboardSnapshot",
                payload=snapshot,
                instance_label="operator-dashboard-ready:snapshot",
            )
            findings.extend(self._prefixed_findings(schema_result, prefix="schema"))
            findings.extend(self._safety_findings(snapshot))
        else:
            findings.append(
                Finding(
                    "OPERATOR_DASHBOARD_READY_SNAPSHOT_MISSING",
                    "Operator dashboard aggregator did not return a snapshot payload.",
                    Severity.BLOCK,
                    metadata={"created_by": POST_H_015_E_CREATED_BY},
                )
            )

        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        ok = aggregate.ok and schema_result is not None and schema_result.ok and not blocking
        summary = self._summary(aggregate=aggregate, schema_result=schema_result, snapshot=snapshot, blocking_total=len(blocking))
        reports = aggregate.data.get("reports", {}) if isinstance(aggregate.data, dict) else {}
        data: dict[str, Any] = {"summary": summary, "reports": reports}
        if isinstance(snapshot, dict):
            data["snapshot"] = snapshot

        return CommandResult(
            command=f"quality {OPERATOR_DASHBOARD_READY_SUBGATE}",
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False),
            message="Operator dashboard readiness gate passed." if ok else "Operator dashboard readiness gate blocked.",
            data=data,
            findings=findings
            or [
                Finding(
                    "OPERATOR_DASHBOARD_READY_PASS",
                    "Operator dashboard snapshot, schema, no-go flags and next actions are ready.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _summary(
        self,
        *,
        aggregate: CommandResult,
        schema_result: CommandResult | None,
        snapshot: Any,
        blocking_total: int,
    ) -> dict[str, Any]:
        snapshot_sections = snapshot.get("sections", {}) if isinstance(snapshot, dict) else {}
        next_actions = snapshot.get("recommended_next_actions", []) if isinstance(snapshot, dict) else []
        aggregate_summary = aggregate.data.get("summary", {}) if isinstance(aggregate.data, dict) else {}
        return {
            "created_by": POST_H_015_E_CREATED_BY,
            "quality_gate_subgate": OPERATOR_DASHBOARD_READY_SUBGATE,
            "operator_dashboard_ready": aggregate.ok and bool(schema_result and schema_result.ok) and blocking_total == 0,
            "aggregate_ok": aggregate.ok,
            "snapshot_schema_ok": bool(schema_result and schema_result.ok),
            "snapshot_status": snapshot.get("status") if isinstance(snapshot, dict) else None,
            "sections_total": len(snapshot_sections) if isinstance(snapshot_sections, dict) else 0,
            "required_sources_missing_total": aggregate_summary.get("required_sources_missing_total"),
            "recommended_next_actions_total": len(next_actions) if isinstance(next_actions, list) else 0,
            "blocking_findings_total": blocking_total,
            "reports_written": bool(aggregate.data.get("reports")) if isinstance(aggregate.data, dict) else False,
            "local_first": True,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "preliminary": True,
        }

    def _safety_findings(self, snapshot: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        expected_flags = {
            "local_first": True,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
        }
        for key, expected in expected_flags.items():
            if snapshot.get(key) is not expected:
                findings.append(
                    Finding(
                        "OPERATOR_DASHBOARD_READY_NO_GO_FLAG_INVALID",
                        "Operator dashboard snapshot violates a no-go gate flag.",
                        Severity.BLOCK,
                        path=key,
                        metadata={"expected": expected, "actual": snapshot.get(key), "created_by": POST_H_015_E_CREATED_BY},
                    )
                )
        sections = snapshot.get("sections")
        if not isinstance(sections, dict) or len(sections) < 10:
            findings.append(
                Finding(
                    "OPERATOR_DASHBOARD_READY_SECTIONS_INCOMPLETE",
                    "Operator dashboard snapshot does not expose all required operational sections.",
                    Severity.BLOCK,
                    metadata={"sections_total": len(sections) if isinstance(sections, dict) else 0},
                )
            )
        for action in snapshot.get("recommended_next_actions", []):
            if not isinstance(action, dict):
                continue
            command = str(action.get("command") or "")
            if action.get("dry_run") is not True:
                findings.append(
                    Finding(
                        "OPERATOR_DASHBOARD_READY_ACTION_NOT_DRY_RUN",
                        "Operator dashboard next action is not explicitly dry-run.",
                        Severity.BLOCK,
                        metadata={"action_id": action.get("action_id"), "command": command},
                    )
                )
            forbidden = ("--execute", " remote ", "connector write", "plugin execute")
            normalized = f" {command.lower()} "
            if any(marker in normalized for marker in forbidden):
                findings.append(
                    Finding(
                        "OPERATOR_DASHBOARD_READY_FORBIDDEN_ACTION",
                        "Operator dashboard next action suggests forbidden execution capability.",
                        Severity.BLOCK,
                        metadata={"action_id": action.get("action_id"), "command": command},
                    )
                )
        return findings

    def _prefixed_findings(self, result: CommandResult, *, prefix: str) -> list[Finding]:
        return [
            Finding(
                id=f"OPERATOR_DASHBOARD_READY_{prefix.upper()}_{finding.id}",
                message=finding.message,
                severity=finding.severity,
                path=finding.path,
                metadata={"source": prefix, **(finding.metadata or {})},
            )
            for finding in result.findings
            if finding.severity in {Severity.WARNING, Severity.FAIL, Severity.BLOCK, Severity.ERROR}
        ]
