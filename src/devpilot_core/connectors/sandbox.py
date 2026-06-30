from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.connectors.replay import (
    DEFAULT_CONNECTOR_REDACTION_REPORT_JSON,
    DEFAULT_CONNECTOR_REDACTION_REPORT_MD,
    DEFAULT_CONNECTOR_REPLAY_FIXTURES_PATH,
    ConnectorReplayOptions,
    ConnectorReplayRequest,
    ConnectorReplayRunner,
)
from devpilot_core.connectors.policy_binding import (
    ConnectorPolicyBindingOptions,
    ConnectorPolicyBindingRequest,
    ConnectorPolicyBindingValidator,
)
from devpilot_core.connectors.sandbox_policy import (
    DEFAULT_CONNECTOR_REGISTRY_PATH,
    DEFAULT_SANDBOX_POLICY_PATH,
    ConnectorSandboxPolicyOptions,
    ConnectorSandboxPolicyValidator,
)
from devpilot_core.policy import PolicyEngine, PolicyRequest

CONNECTOR_SANDBOX_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-CONNECTOR-SANDBOX-REPORT-V1"
DEFAULT_CONNECTOR_SANDBOX_REPORT_JSON = Path("outputs/reports/connector_sandbox_report.json")
DEFAULT_CONNECTOR_SANDBOX_REPORT_MD = Path("outputs/reports/connector_sandbox_report.md")
_ALLOWED_MODES = {"validate", "dry-run", "replay"}
_WRITE_LIKE_MODES = {"write", "execute", "real", "mutate", "apply", "commit", "push"}
_POLICY_CHECK_RISKS = {"medium", "medium_high", "high", "critical"}


@dataclass(frozen=True)
class ConnectorSandboxRequest:
    """Input contract for the POST-H-018-D connector sandbox runner.

    The request is intentionally small and safe. It selects a connector,
    operation label and sandbox mode, but it does not authorize real connector
    writes, network calls, external APIs, remote execution or plugin execution.
    """

    connector_id: str = "local.docs"
    operation: str = "list_sources"
    mode: str = "validate"
    dry_run: bool = True
    input_payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class ConnectorSandboxOptions:
    """Runtime options for local sandbox report generation."""

    policy_path: Path | str = DEFAULT_SANDBOX_POLICY_PATH
    registry_path: Path | str = DEFAULT_CONNECTOR_REGISTRY_PATH
    output_json: Path | str = DEFAULT_CONNECTOR_SANDBOX_REPORT_JSON
    output_markdown: Path | str = DEFAULT_CONNECTOR_SANDBOX_REPORT_MD
    replay_fixtures_path: Path | str = DEFAULT_CONNECTOR_REPLAY_FIXTURES_PATH
    redaction_output_json: Path | str = DEFAULT_CONNECTOR_REDACTION_REPORT_JSON
    redaction_output_markdown: Path | str = DEFAULT_CONNECTOR_REDACTION_REPORT_MD
    write_report: bool = False


@dataclass(frozen=True)
class ConnectorSandboxResult:
    """Serializable result envelope returned by the sandbox runner."""

    report: dict[str, Any]
    summary: dict[str, Any]
    findings: list[Finding]
    policy_result: CommandResult | None = None


class ConnectorSandboxRunner:
    """Run local read-only/dry-run connector sandbox validation.

    POST-H-018-D extends the runner boundary, not connector write
    or a real external connector runtime. The runner validates the sandbox
    policy, checks per-connector mode permissions, invokes PolicyEngine for
    medium/high risk connectors before any simulated operation and materializes
    a ConnectorSandboxReport when requested.
    """

    def __init__(self, root: Path, *, options: ConnectorSandboxOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ConnectorSandboxOptions()

    @property
    def policy_path(self) -> Path:
        path = Path(self.options.policy_path)
        return path if path.is_absolute() else self.root / path

    @property
    def registry_path(self) -> Path:
        path = Path(self.options.registry_path)
        return path if path.is_absolute() else self.root / path

    def run(self, request: ConnectorSandboxRequest) -> CommandResult:
        connector_id = _normalize_id(request.connector_id)
        operation = _normalize_operation(request.operation)
        mode = _normalize_mode(request.mode)
        findings: list[Finding] = []
        policy_result: CommandResult | None = None
        replay_result: CommandResult | None = None
        binding_result: CommandResult | None = None

        policy_validator = ConnectorSandboxPolicyValidator(
            self.root,
            options=ConnectorSandboxPolicyOptions(
                policy_path=self.options.policy_path,
                registry_path=self.options.registry_path,
            ),
        )
        policy_validation = policy_validator.validate()
        if not policy_validation.ok:
            findings.extend(policy_validation.findings)
            findings.append(
                Finding(
                    "CONNECTOR_SANDBOX_POLICY_INVALID",
                    "Connector sandbox runner is blocked until the sandbox policy validates.",
                    Severity.BLOCK,
                    path=_rel(self.root, self.policy_path),
                )
            )
            result = self._build_result(
                connector_id=connector_id,
                operation=operation,
                mode=mode if mode in _ALLOWED_MODES else "validate",
                requested_mode=mode,
                policy_connector=None,
                policy_validation=policy_validation,
                policy_result=None,
                replay_result=None,
                binding_result=None,
                findings=findings,
                reports_written=False,
            )
            return result

        policy = self._load_json(self.policy_path)
        policy_connector = _find_policy_connector(policy, connector_id)
        if mode not in _ALLOWED_MODES:
            severity = Severity.BLOCK
            finding_id = "CONNECTOR_SANDBOX_WRITE_MODE_BLOCKED" if mode in _WRITE_LIKE_MODES else "CONNECTOR_SANDBOX_MODE_BLOCKED"
            findings.append(
                Finding(
                    finding_id,
                    "Connector sandbox runner only accepts validate, dry-run or replay; write/execute modes remain blocked.",
                    severity,
                    metadata={"connector_id": connector_id, "requested_mode": mode, "allowed_modes": sorted(_ALLOWED_MODES)},
                )
            )
        if policy_connector is None:
            findings.append(
                Finding(
                    "CONNECTOR_SANDBOX_CONNECTOR_NOT_REGISTERED",
                    "Connector is not declared in connector_sandbox_policy.json and cannot be sandboxed.",
                    Severity.BLOCK,
                    metadata={"connector_id": connector_id},
                )
            )
        elif mode in _ALLOWED_MODES:
            allowed_modes = set(policy_connector.get("allowed_modes") or [])
            if mode not in allowed_modes:
                findings.append(
                    Finding(
                        "CONNECTOR_SANDBOX_CONNECTOR_MODE_NOT_ALLOWED",
                        "Requested sandbox mode is not allowed for this connector by policy.",
                        Severity.BLOCK,
                        metadata={"connector_id": connector_id, "requested_mode": mode, "connector_allowed_modes": sorted(allowed_modes)},
                    )
                )
            findings.extend(_connector_safety_findings(policy_connector))
            if _requires_policy_engine(policy_connector):
                policy_result = self._evaluate_policy(
                    connector_id=connector_id,
                    operation=operation,
                    mode=mode,
                    policy_connector=policy_connector,
                    input_payload=request.input_payload,
                )
                if not policy_result.ok:
                    findings.extend(_prefix_findings(policy_result.findings, prefix="POLICY_ENGINE_"))
                else:
                    findings.append(
                        Finding(
                            "CONNECTOR_SANDBOX_POLICY_ENGINE_PASS",
                            "PolicyEngine evaluated the sandbox request before any simulated connector operation.",
                            Severity.INFO,
                            metadata={"connector_id": connector_id, "mode": mode, "risk_level": policy_connector.get("risk_level")},
                        )
                    )
            binding_result = ConnectorPolicyBindingValidator(
                self.root,
                options=ConnectorPolicyBindingOptions(
                    policy_path=self.options.policy_path,
                    registry_path=self.options.registry_path,
                ),
            ).evaluate_request(
                ConnectorPolicyBindingRequest(
                    connector_id=connector_id,
                    operation=operation,
                    mode=mode,
                    input_payload=request.input_payload,
                )
            )
            if not binding_result.ok:
                findings.extend(_prefix_findings(binding_result.findings, prefix="BINDING_"))
            else:
                findings.append(
                    Finding(
                        "CONNECTOR_SANDBOX_BINDING_PASS",
                        "Connector Policy/Approval/RBAC binding was evaluated before accepting sandbox evidence.",
                        Severity.INFO,
                        metadata={"connector_id": connector_id, "mode": mode},
                    )
                )

        has_block = any(item.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for item in findings)
        if not has_block and mode == "replay":
            replay_result = ConnectorReplayRunner(
                self.root,
                options=ConnectorReplayOptions(
                    fixtures_path=self.options.replay_fixtures_path,
                    output_json=self.options.redaction_output_json,
                    output_markdown=self.options.redaction_output_markdown,
                    write_report=self.options.write_report,
                ),
            ).run(
                ConnectorReplayRequest(
                    connector_id=connector_id,
                    operation=operation,
                    mode="replay",
                    input_payload=request.input_payload,
                )
            )
            findings.extend(_prefix_findings(replay_result.findings, prefix="REPLAY_"))
            has_block = any(item.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for item in findings)
        if not has_block:
            pass_message = (
                "Connector sandbox runner completed local fixture-backed replay and redaction without network, external APIs or mutations."
                if mode == "replay"
                else "Connector sandbox runner completed local validate/dry-run simulation without network, external APIs or mutations."
            )
            findings.append(
                Finding(
                    "CONNECTOR_SANDBOX_RUNNER_PASS",
                    pass_message,
                    Severity.INFO,
                    metadata={"connector_id": connector_id, "operation": operation, "mode": mode},
                )
            )

        result = self._build_result(
            connector_id=connector_id,
            operation=operation,
            mode=mode if mode in _ALLOWED_MODES else "validate",
            requested_mode=mode,
            policy_connector=policy_connector,
            policy_validation=policy_validation,
            policy_result=policy_result,
            replay_result=replay_result,
            binding_result=binding_result,
            findings=findings,
            reports_written=False,
        )
        if self.options.write_report and "report" in result.data:
            reports = self._write_report(result.data["report"])
            data = dict(result.data)
            summary = dict(data.get("summary") or {})
            summary["reports_written"] = True
            summary["output_json"] = reports["json"]
            summary["output_markdown"] = reports["markdown"]
            data["summary"] = summary
            report = dict(data["report"])
            report_summary = dict(report.get("summary") or {})
            report_summary["reports_written"] = True
            report_summary["output_json"] = reports["json"]
            report_summary["output_markdown"] = reports["markdown"]
            report["summary"] = report_summary
            data["report"] = report
            data["reports"] = reports
            # Persist the updated report payload so the JSON file mirrors CLI output.
            self._write_report(report)
            result = CommandResult(
                command=result.command,
                ok=result.ok,
                exit_code=result.exit_code,
                message=result.message,
                data=data,
                findings=result.findings,
            )
        return result

    def _evaluate_policy(
        self,
        *,
        connector_id: str,
        operation: str,
        mode: str,
        policy_connector: dict[str, Any],
        input_payload: dict[str, Any] | None,
    ) -> CommandResult:
        text = json.dumps(input_payload or {}, ensure_ascii=False, sort_keys=True)
        return PolicyEngine(self.root).evaluate(
            PolicyRequest(
                action="read",
                path="docs",
                text=text,
                dry_run=True,
                external_api=False,
                tool_id="connector.sandbox.run",
                subject=f"{connector_id}:{operation}:{mode}",
                interface="connector",
                command_id="connector.sandbox.run",
                metadata={
                    "component": "ConnectorSandboxRunner",
                    "sprint": "POST-H-018-C",
                    "connector_id": connector_id,
                    "operation": operation,
                    "mode": mode,
                    "side_effect": policy_connector.get("side_effect"),
                    "risk_level": policy_connector.get("risk_level"),
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "connector_write_used": False,
                    "remote_execution_used": False,
                    "plugin_execution_used": False,
                },
            )
        )

    def _build_result(
        self,
        *,
        connector_id: str,
        operation: str,
        mode: str,
        requested_mode: str,
        policy_connector: dict[str, Any] | None,
        policy_validation: CommandResult,
        policy_result: CommandResult | None,
        replay_result: CommandResult | None,
        binding_result: CommandResult | None,
        findings: list[Finding],
        reports_written: bool,
    ) -> CommandResult:
        blocking = sum(1 for item in findings if item.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL})
        ok = blocking == 0
        status = "passed" if ok else "blocked"
        policy_summary = (policy_result.data or {}).get("summary", {}) if policy_result is not None else {}
        replay_summary = (replay_result.data or {}).get("summary", {}) if replay_result is not None else {}
        binding_summary = (binding_result.data or {}).get("summary", {}) if binding_result is not None else {}
        policy_checked = policy_result is not None
        policy_passed = bool(policy_result.ok) if policy_result is not None else (policy_connector is not None and ok)
        approval_required = bool(policy_connector.get("approval_required")) if isinstance(policy_connector, dict) else False
        rbac_required = bool(policy_connector.get("rbac_required")) if isinstance(policy_connector, dict) else False
        created_by = "POST-H-018-D" if binding_result is not None else ("POST-H-018-C" if replay_result is not None else "POST-H-018-B")
        fixtures_total = int(replay_summary.get("fixtures_total", 0)) if replay_result is not None else 0
        fixtures_passed = int(replay_summary.get("fixtures_passed", 0)) if replay_result is not None else 0
        redaction_passed = bool(replay_summary.get("redaction_passed", False)) if replay_result is not None else None
        redaction_findings_total = int(replay_summary.get("redaction_findings_total", 0)) if replay_result is not None else 0
        summary: dict[str, Any] = {
            "created_by": created_by,
            "status": "implemented-initial",
            "preliminary": True,
            "connector_id": connector_id,
            "operation": operation,
            "mode": mode,
            "requested_mode": requested_mode,
            "policy_path": _rel(self.root, self.policy_path),
            "registry_path": _rel(self.root, self.registry_path),
            "policy_valid": policy_validation.ok,
            "policy_checked": policy_checked,
            "policy_engine_invoked": policy_checked,
            "policy_passed": policy_passed,
            "policy_allowed": policy_passed,
            "connector_binding_checked": binding_result is not None,
            "connector_binding_passed": bool(binding_result.ok) if binding_result is not None else False,
            "binding_rules": binding_summary.get("binding_rules", []),
            "write_future_blocked": bool(binding_summary.get("write_future_blocked", False)) if binding_result is not None else False,
            "approval_required": bool(binding_summary.get("approval_required", approval_required)),
            "approval_policy_checked": bool(binding_summary.get("approval_policy_checked", False)) if binding_result is not None else False,
            "approval_missing_blocks": bool(binding_summary.get("approval_missing_blocks", False)) if binding_result is not None else False,
            "rbac_required": rbac_required,
            "rbac_evaluated": bool(binding_summary.get("rbac_evaluated", False)) if binding_result is not None else False,
            "rbac_allowed": binding_summary.get("rbac_allowed") if binding_result is not None else None,
            "connector_status": policy_connector.get("status") if isinstance(policy_connector, dict) else None,
            "risk_level": policy_connector.get("risk_level") if isinstance(policy_connector, dict) else None,
            "side_effect": policy_connector.get("side_effect") if isinstance(policy_connector, dict) else None,
            "allowed_modes": policy_connector.get("allowed_modes", []) if isinstance(policy_connector, dict) else [],
            "fixtures_total": fixtures_total,
            "fixtures_passed": fixtures_passed,
            "redaction_passed": redaction_passed,
            "redaction_findings_total": redaction_findings_total,
            "deterministic_replay": bool(replay_summary.get("deterministic_replay", False)) if replay_result is not None else False,
            "redaction_report_json": (replay_result.data.get("reports", {}) or {}).get("json") if replay_result is not None else None,
            "redaction_report_markdown": (replay_result.data.get("reports", {}) or {}).get("markdown") if replay_result is not None else None,
            "blocking_findings_total": blocking,
            "findings_total": len(findings),
            "reports_written": reports_written,
            "output_json": None,
            "output_markdown": None,
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
        report = {
            "schema_version": "1.0",
            "schema_id": CONNECTOR_SANDBOX_REPORT_SCHEMA_ID,
            "report_id": _report_id(connector_id, operation, mode),
            "created_by": created_by,
            "status": status,
            "connector_id": connector_id,
            "mode": mode,
            "ok": ok,
            "summary": dict(summary),
            "safety": _safety(),
            "findings": [finding.to_dict() for finding in findings],
            "preliminary": True,
        }
        data = {
            "summary": summary,
            "report": report,
            "policy": {
                "connector": _public_policy_connector(policy_connector),
                "policy_validation": (policy_validation.data or {}).get("summary", {}),
                "policy_engine": policy_summary,
            },
            "binding": (binding_result.data if binding_result is not None else {}),
            "replay": (replay_result.data if replay_result is not None else {}),
            "notes": [
                "POST-H-018-D runs local sandbox replay with deterministic fixtures plus Policy/Approval/RBAC binding checks; it does not perform connector write, network, external APIs, remote execution or plugin execution.",
                "The final connector-sandbox quality gate remains POST-H-018-E scope.",
            ],
        }
        return CommandResult(
            command="connector sandbox run",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Connector sandbox run passed." if ok else "Connector sandbox run blocked.",
            data=data,
            findings=findings,
        )

    def _write_report(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = _resolve(self.root, self.options.output_json)
        markdown_path = _resolve(self.root, self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(_render_markdown(report), encoding="utf-8")
        return {"json": _rel(self.root, json_path), "markdown": _rel(self.root, markdown_path)}

    def _load_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))


def _connector_safety_findings(connector: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    connector_id = str(connector.get("connector_id"))
    for flag in ("network_allowed", "external_api_allowed", "mutations_allowed", "write_allowed", "execution_allowed"):
        if connector.get(flag) is not False:
            findings.append(
                Finding(
                    "CONNECTOR_SANDBOX_RUNTIME_FLAG_BLOCKED",
                    f"Connector sandbox policy must keep {flag}=false before any sandbox operation.",
                    Severity.BLOCK,
                    metadata={"connector_id": connector_id, "flag": flag},
                )
            )
    return findings


def _requires_policy_engine(connector: dict[str, Any]) -> bool:
    risk = str(connector.get("risk_level") or "").lower()
    return risk in _POLICY_CHECK_RISKS or bool(connector.get("policy_rules"))


def _prefix_findings(findings: list[Finding], *, prefix: str) -> list[Finding]:
    return [
        Finding(
            id=f"{prefix}{finding.id}",
            message=finding.message,
            severity=finding.severity,
            path=finding.path,
            metadata=dict(finding.metadata or {}),
        )
        for finding in findings
    ]


def _find_policy_connector(policy: dict[str, Any], connector_id: str) -> dict[str, Any] | None:
    for connector in policy.get("connectors", []):
        if isinstance(connector, dict) and connector.get("connector_id") == connector_id:
            return connector
    return None


def _public_policy_connector(connector: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(connector, dict):
        return {}
    return {
        "connector_id": connector.get("connector_id"),
        "status": connector.get("status"),
        "allowed_modes": connector.get("allowed_modes", []),
        "side_effect": connector.get("side_effect"),
        "risk_level": connector.get("risk_level"),
        "data_sensitivity": connector.get("data_sensitivity"),
        "network_allowed": connector.get("network_allowed"),
        "external_api_allowed": connector.get("external_api_allowed"),
        "mutations_allowed": connector.get("mutations_allowed"),
        "write_allowed": connector.get("write_allowed"),
        "execution_allowed": connector.get("execution_allowed"),
        "approval_required": connector.get("approval_required"),
        "rbac_required": connector.get("rbac_required"),
        "policy_rules": connector.get("policy_rules", []),
    }


def _safety() -> dict[str, Any]:
    return {
        "local_first": True,
        "dry_run": True,
        "network_used": False,
        "external_api_used": False,
        "mutations_performed": False,
        "connector_write_used": False,
        "remote_execution_used": False,
        "plugin_execution_used": False,
        "secrets_included": False,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    lines = [
        "# Connector Sandbox Report",
        "",
        f"- Report ID: `{report.get('report_id')}`",
        f"- Generated by: `{report.get('created_by')}`",
        f"- Status: `{report.get('status')}`",
        f"- Connector: `{report.get('connector_id')}`",
        f"- Mode: `{report.get('mode')}`",
        f"- OK: `{report.get('ok')}`",
        f"- Policy passed: `{summary.get('policy_passed')}`",
        f"- PolicyEngine invoked: `{summary.get('policy_engine_invoked')}`",
        f"- Network used: `{summary.get('network_used')}`",
        f"- External API used: `{summary.get('external_api_used')}`",
        f"- Mutations performed: `{summary.get('mutations_performed')}`",
        f"- Fixtures total: `{summary.get('fixtures_total')}`",
        f"- Fixtures passed: `{summary.get('fixtures_passed')}`",
        f"- Redaction passed: `{summary.get('redaction_passed')}`",
        f"- Redaction report JSON: `{summary.get('redaction_report_json')}`",
        f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
        "",
        "## Findings",
    ]
    findings = report.get("findings", [])
    if findings:
        for finding in findings:
            lines.append(f"- `{finding.get('severity')}` `{finding.get('id')}` — {finding.get('message')}")
    else:
        lines.append("- No findings.")
    lines.append("")
    lines.append("This report is local-first and dry-run only. It is not permission for connector write, network, external APIs, remote execution or plugin execution.\n")
    return "\n".join(lines)


def _report_id(connector_id: str, operation: str, mode: str) -> str:
    safe = f"{connector_id}-{operation}-{mode}".replace(".", "-").replace("_", "-")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"connector-sandbox-{safe}-{stamp}"


def _normalize_id(value: str) -> str:
    return str(value or "").strip().lower().replace(" ", "-") or "local.docs"


def _normalize_operation(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_") or "list_sources"


def _normalize_mode(value: str) -> str:
    return str(value or "").strip().lower()


def _resolve(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _rel(root: Path, path: Path | str) -> str:
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return candidate.as_posix()
