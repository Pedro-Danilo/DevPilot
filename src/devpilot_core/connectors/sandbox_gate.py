from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

from .policy_binding import ConnectorPolicyBindingOptions, ConnectorPolicyBindingValidator
from .sandbox import ConnectorSandboxOptions, ConnectorSandboxRequest, ConnectorSandboxRunner
from .sandbox_policy import DEFAULT_CONNECTOR_REGISTRY_PATH, DEFAULT_SANDBOX_POLICY_PATH


@dataclass(frozen=True)
class ConnectorSandboxGateOptions:
    """Options for the POST-H-018-E connector-sandbox quality subgate.

    The gate is intentionally report-read/validation-only. It runs the exposure
    validator and the fixture-backed sandbox replay with write_report=False so
    quality-gate executions do not materialize connector evidence unless the
    operator invokes the dedicated connector commands explicitly.
    """

    policy_path: Path | str = DEFAULT_SANDBOX_POLICY_PATH
    registry_path: Path | str = DEFAULT_CONNECTOR_REGISTRY_PATH
    replay_fixtures_path: Path | str = "evals/fixtures/connector_replay_cases.json"


class ConnectorSandboxQualityGate:
    """POST-H-018-E quality gate for connector sandbox safety.

    This gate does not execute real connectors. It validates that the existing
    sandbox policy, replay runner and Policy/Approval/RBAC binding collectively
    preserve the no-go rules required before any future connector evolution:
    deny-write, local-first, no network, no external APIs, no mutation, fixture
    replay and high-risk RBAC exposure.
    """

    def __init__(self, root: Path, *, options: ConnectorSandboxGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ConnectorSandboxGateOptions()

    def run(self) -> CommandResult:
        findings: list[Finding] = []

        exposure = ConnectorPolicyBindingValidator(
            self.root,
            options=ConnectorPolicyBindingOptions(
                policy_path=self.options.policy_path,
                registry_path=self.options.registry_path,
                write_report=False,
            ),
        ).exposure_report()
        sandbox = ConnectorSandboxRunner(
            self.root,
            options=ConnectorSandboxOptions(
                policy_path=self.options.policy_path,
                registry_path=self.options.registry_path,
                replay_fixtures_path=self.options.replay_fixtures_path,
                write_report=False,
            ),
        ).run(ConnectorSandboxRequest(connector_id="local.docs", operation="list_sources", mode="replay"))

        exposure_summary = dict((exposure.data or {}).get("summary") or {})
        sandbox_summary = dict((sandbox.data or {}).get("summary") or {})

        if not exposure.ok:
            findings.extend(_prefixed_findings("EXPOSURE", exposure.findings))
            findings.append(
                Finding(
                    "CONNECTOR_SANDBOX_GATE_EXPOSURE_BLOCK",
                    "Connector sandbox quality gate is blocked because the Policy/Approval/RBAC exposure report did not pass.",
                    Severity.BLOCK,
                )
            )
        if not sandbox.ok:
            findings.extend(_prefixed_findings("RUNNER", sandbox.findings))
            findings.append(
                Finding(
                    "CONNECTOR_SANDBOX_GATE_RUNNER_BLOCK",
                    "Connector sandbox quality gate is blocked because fixture-backed replay did not pass.",
                    Severity.BLOCK,
                )
            )

        self._check_exposure_summary(exposure_summary, findings)
        self._check_sandbox_summary(sandbox_summary, findings)
        self._check_safety_flags("exposure", exposure_summary, findings)
        self._check_safety_flags("sandbox", sandbox_summary, findings)

        blocking = sum(1 for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL})
        ok = blocking == 0
        summary = {
            "created_by": "POST-H-018-E",
            "status": "implemented-initial",
            "preliminary": True,
            "quality_gate_subgate": "connector-sandbox",
            "exposure_ok": bool(exposure.ok),
            "sandbox_replay_ok": bool(sandbox.ok),
            "connectors_total": int(exposure_summary.get("connectors_total", 0)),
            "write_future_blocked_total": int(exposure_summary.get("write_future_blocked_total", 0)),
            "policy_coverage_complete": bool(exposure_summary.get("policy_coverage_complete", False)),
            "all_high_risk_rbac_evaluated": bool(exposure_summary.get("all_high_risk_rbac_evaluated", False)),
            "all_side_effecting_future_write_blocked": bool(exposure_summary.get("all_side_effecting_future_write_blocked", False)),
            "connector_binding_checked": bool(sandbox_summary.get("connector_binding_checked", False)),
            "connector_binding_passed": bool(sandbox_summary.get("connector_binding_passed", False)),
            "policy_engine_invoked": bool(sandbox_summary.get("policy_engine_invoked", False)),
            "fixtures_total": int(sandbox_summary.get("fixtures_total", 0)),
            "fixtures_passed": int(sandbox_summary.get("fixtures_passed", 0)),
            "redaction_passed": bool(sandbox_summary.get("redaction_passed", False)),
            "deterministic_replay": bool(sandbox_summary.get("deterministic_replay", False)),
            "blocking_findings_total": blocking,
            "findings_total": len(findings),
            "reports_written": False,
            "local_first": True,
            "dry_run": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "connector_write_used": False,
            "remote_execution_used": False,
            "plugin_execution_used": False,
            "secrets_included": False,
        }
        data = {
            "summary": summary,
            "exposure_summary": exposure_summary,
            "sandbox_summary": sandbox_summary,
            "notes": [
                "POST-H-018-E validates connector sandbox evidence through a quality-gate subgate only; it does not execute real connectors.",
                "connector.write_future must remain blocked until a future ADR/backlog explicitly authorizes connector write with stronger controls.",
            ],
        }
        if ok:
            findings.append(
                Finding(
                    "CONNECTOR_SANDBOX_GATE_PASS",
                    "Connector sandbox quality gate passed with deny-write, fixture replay, Policy/Approval/RBAC binding and no network/external API/mutation/write flags.",
                    Severity.INFO,
                    metadata={"connectors_total": summary["connectors_total"]},
                )
            )
            data["summary"]["findings_total"] = len(findings)

        return CommandResult(
            command="quality connector-sandbox",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Connector sandbox quality gate passed." if ok else "Connector sandbox quality gate blocked.",
            data=data,
            findings=findings,
        )

    def _check_exposure_summary(self, summary: dict[str, Any], findings: list[Finding]) -> None:
        connectors_total = int(summary.get("connectors_total", 0))
        write_blocked_total = int(summary.get("write_future_blocked_total", 0))
        checks = {
            "policy_coverage_complete": bool(summary.get("policy_coverage_complete", False)),
            "all_high_risk_rbac_evaluated": bool(summary.get("all_high_risk_rbac_evaluated", False)),
            "all_side_effecting_future_write_blocked": bool(summary.get("all_side_effecting_future_write_blocked", False)),
            "write_future_blocked_for_all": connectors_total > 0 and write_blocked_total == connectors_total,
        }
        for key, passed in checks.items():
            if not passed:
                findings.append(
                    Finding(
                        "CONNECTOR_SANDBOX_GATE_EXPOSURE_INVARIANT_BLOCK",
                        "Connector sandbox exposure invariant failed.",
                        Severity.BLOCK,
                        metadata={"invariant": key, "connectors_total": connectors_total, "write_future_blocked_total": write_blocked_total},
                    )
                )

    def _check_sandbox_summary(self, summary: dict[str, Any], findings: list[Finding]) -> None:
        checks = {
            "policy_engine_invoked": bool(summary.get("policy_engine_invoked", False)),
            "connector_binding_checked": bool(summary.get("connector_binding_checked", False)),
            "connector_binding_passed": bool(summary.get("connector_binding_passed", False)),
            "write_future_blocked": bool(summary.get("write_future_blocked", False)),
            "fixtures_available": int(summary.get("fixtures_total", 0)) > 0,
            "fixtures_passed": int(summary.get("fixtures_passed", 0)) == int(summary.get("fixtures_total", 0)) and int(summary.get("fixtures_total", 0)) > 0,
            "redaction_passed": bool(summary.get("redaction_passed", False)),
            "deterministic_replay": bool(summary.get("deterministic_replay", False)),
        }
        for key, passed in checks.items():
            if not passed:
                findings.append(
                    Finding(
                        "CONNECTOR_SANDBOX_GATE_REPLAY_INVARIANT_BLOCK",
                        "Connector sandbox replay invariant failed.",
                        Severity.BLOCK,
                        metadata={"invariant": key},
                    )
                )

    def _check_safety_flags(self, source: str, summary: dict[str, Any], findings: list[Finding]) -> None:
        for flag in [
            "network_used",
            "external_api_used",
            "mutations_performed",
            "source_mutations_performed",
            "connector_write_used",
            "remote_execution_used",
            "plugin_execution_used",
            "secrets_included",
        ]:
            if bool(summary.get(flag, False)):
                findings.append(
                    Finding(
                        "CONNECTOR_SANDBOX_GATE_SAFETY_FLAG_BLOCK",
                        "Connector sandbox quality gate blocks unsafe safety flags.",
                        Severity.BLOCK,
                        metadata={"source": source, "flag": flag, "value": summary.get(flag)},
                    )
                )


def _prefixed_findings(prefix: str, findings: list[Finding]) -> list[Finding]:
    return [
        Finding(
            id=f"CONNECTOR_SANDBOX_GATE_{prefix}_{finding.id}",
            message=finding.message,
            severity=finding.severity,
            path=finding.path,
            metadata=finding.metadata,
        )
        for finding in findings
        if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}
    ]
