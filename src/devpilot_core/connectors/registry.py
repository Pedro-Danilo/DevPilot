from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect, SecretGuard
from devpilot_core.schemas import SchemaValidator

_DEFAULT_REGISTRY_PATH = ".devpilot/connectors/connector_registry.json"
_DEFAULT_SCHEMA_PATH = "docs/schemas/connector_registry.schema.json"
_VALID_STATUSES = {"disabled", "planned", "implemented", "experimental"}


@dataclass(frozen=True)
class ConnectorRegistryOptions:
    """Options for validating the local Connector Registry."""

    registry_path: str = _DEFAULT_REGISTRY_PATH
    schema_path: str = _DEFAULT_SCHEMA_PATH


class ConnectorRegistry:
    """Validate the FUNC-SPRINT-88 deny-by-default connector registry.

    Sprint 88 intentionally implements discovery/validation only. It does not
    create a MCP client, MCP server, connector adapter or any connector call
    execution path. The registry is a local JSON contract used by later sprints
    to prevent allow-by-default connector growth.
    """

    def __init__(self, root: Path, *, options: ConnectorRegistryOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ConnectorRegistryOptions()
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()

    @property
    def registry_path(self) -> Path:
        candidate = Path(self.options.registry_path)
        return candidate if candidate.is_absolute() else self.root / candidate

    @property
    def schema_path(self) -> Path:
        candidate = Path(self.options.schema_path)
        return candidate if candidate.is_absolute() else self.root / candidate

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        registry_display = _rel(self.root, self.registry_path)
        schema_display = _rel(self.root, self.schema_path)

        for path, label in [(self.registry_path, "registry"), (self.schema_path, "schema")]:
            decision = self.path_guard.evaluate(path, action="read")
            if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
                return CommandResult(
                    command="connector validate",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message=f"Connector {label} path was blocked by PathGuard.",
                    data={"summary": _summary_template(registry_display, schema_display, path_allowed=False)},
                    findings=[Finding("CONNECTOR_REGISTRY_PATH_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata)],
                )
            if not path.exists():
                return CommandResult(
                    command="connector validate",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message=f"Connector {label} file is missing.",
                    data={"summary": _summary_template(registry_display, schema_display, path_allowed=True)},
                    findings=[Finding("CONNECTOR_REGISTRY_FILE_MISSING", f"Missing connector {label}: {_rel(self.root, path)}", Severity.BLOCK, path=_rel(self.root, path))],
                )

        try:
            registry_text = self.registry_path.read_text(encoding="utf-8")
            registry = json.loads(registry_text)
        except json.JSONDecodeError as exc:
            return CommandResult(
                command="connector validate",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Connector registry is not valid JSON.",
                data={"summary": _summary_template(registry_display, schema_display, path_allowed=True)},
                findings=[Finding("CONNECTOR_REGISTRY_INVALID_JSON", str(exc), Severity.ERROR, path=registry_display)],
            )

        redaction = self.secret_guard.redact(registry_text)
        if redaction.redactions:
            findings.append(
                Finding(
                    "CONNECTOR_REGISTRY_SECRET_RISK_BLOCKED",
                    "SecretGuard detected secret-like material in Connector Registry; store references, not secrets.",
                    Severity.BLOCK,
                    path=registry_display,
                    metadata={"redactions_total": redaction.redactions},
                )
            )

        schema_result = SchemaValidator(self.root).validate(schema=self.options.schema_path, instance=self.options.registry_path)
        if not schema_result.ok:
            findings.extend(schema_result.findings)

        connectors = registry.get("connectors") if isinstance(registry, dict) else []
        if not isinstance(connectors, list):
            connectors = []
        status_counts = Counter()
        policy_missing: list[str] = []
        enabled_by_default: list[str] = []
        executable: list[str] = []
        network_enabled: list[str] = []
        external_enabled: list[str] = []
        invalid_status: list[str] = []
        implemented_connectors: list[str] = []
        approved_without_observability: list[str] = []

        for connector in connectors:
            connector_id = str(connector.get("connector_id", "<missing>")) if isinstance(connector, dict) else "<invalid>"
            status = connector.get("status") if isinstance(connector, dict) else None
            if status in _VALID_STATUSES:
                status_counts[str(status)] += 1
            else:
                invalid_status.append(connector_id)
            if not connector.get("policy_rule_ids"):
                policy_missing.append(connector_id)
            if connector.get("default_effect") != "deny":
                enabled_by_default.append(connector_id)
            if connector.get("execution_enabled") is True:
                executable.append(connector_id)
            if connector.get("network_allowed") is True:
                network_enabled.append(connector_id)
            if connector.get("external_api_allowed") is True:
                external_enabled.append(connector_id)
            if connector.get("status") == "implemented":
                implemented_connectors.append(connector_id)
            if connector.get("observability_required") is not True:
                approved_without_observability.append(connector_id)

        mcp = registry.get("mcp", {}) if isinstance(registry, dict) else {}
        defaults = registry.get("defaults", {}) if isinstance(registry, dict) else {}
        security = registry.get("security", {}) if isinstance(registry, dict) else {}

        if mcp.get("enabled_by_default") is not False:
            findings.append(Finding("MCP_ENABLED_BY_DEFAULT_BLOCKED", "MCP must remain disabled by default in Sprint 88.", Severity.BLOCK, path=registry_display))
        if mcp.get("client_implemented") is True or mcp.get("server_implemented") is True:
            findings.append(Finding("MCP_RUNTIME_PREMATURE_BLOCKED", "Sprint 88 must not implement MCP client/server runtime.", Severity.BLOCK, path=registry_display))
        if defaults.get("connector_default_effect") != "deny":
            findings.append(Finding("CONNECTOR_DEFAULT_EFFECT_BLOCKED", "Connector default effect must be deny.", Severity.BLOCK, path=registry_display))
        if defaults.get("deny_unregistered_connectors") is not True:
            findings.append(Finding("UNREGISTERED_CONNECTORS_NOT_DENIED", "Unregistered connectors must be denied.", Severity.BLOCK, path=registry_display))
        if security.get("connector_execution_performed") is not False:
            findings.append(Finding("CONNECTOR_EXECUTION_PERFORMED_BLOCKED", "Sprint 88 validation must not execute connectors.", Severity.BLOCK, path=registry_display))

        for finding_id, paths, message in [
            ("CONNECTOR_POLICY_MISSING", policy_missing, "Every connector must declare policy_rule_ids."),
            ("CONNECTOR_ALLOW_BY_DEFAULT_BLOCKED", enabled_by_default, "Every connector must be deny-by-default."),
            ("CONNECTOR_EXECUTION_ENABLED_BLOCKED", executable, "Sprint 88 must not enable connector execution."),
            ("CONNECTOR_NETWORK_ENABLED_BLOCKED", network_enabled, "Connectors must not enable network by default."),
            ("CONNECTOR_EXTERNAL_API_ENABLED_BLOCKED", external_enabled, "External API connectors must remain disabled."),
            ("CONNECTOR_STATUS_INVALID", invalid_status, "Connector status must be disabled/planned/implemented/experimental."),
            ("CONNECTOR_OBSERVABILITY_MISSING", approved_without_observability, "Every connector must require observability."),
        ]:
            if paths:
                findings.append(Finding(finding_id, message, Severity.BLOCK, path=registry_display, metadata={"connectors": paths[:50], "total": len(paths)}))

        if not findings or all(f.severity == Severity.INFO for f in findings):
            findings.append(
                Finding(
                    "CONNECTOR_REGISTRY_VALIDATED",
                    "Connector Registry is structurally valid and keeps MCP/connectors deny-by-default.",
                    Severity.INFO,
                    metadata={"connectors_total": len(connectors), "statuses": dict(status_counts)},
                )
            )

        has_block = any(f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for f in findings)
        summary = {
            **_summary_template(registry_display, schema_display, path_allowed=True),
            "schema_valid": schema_result.ok,
            "connectors_total": len(connectors),
            "status_counts": {status: status_counts.get(status, 0) for status in sorted(_VALID_STATUSES)},
            "policy_rules_missing_total": len(policy_missing),
            "enabled_by_default_total": len(enabled_by_default),
            "execution_enabled_total": len(executable),
            "implemented_connectors_total": len(implemented_connectors),
            "network_enabled_total": len(network_enabled),
            "external_api_enabled_total": len(external_enabled),
            "mcp_enabled_by_default": mcp.get("enabled_by_default"),
            "mcp_client_implemented": mcp.get("client_implemented"),
            "mcp_server_implemented": mcp.get("server_implemented"),
            "connector_execution_performed": security.get("connector_execution_performed"),
            "network_used": False,
            "external_api_used": False,
            "secret_guard_used": True,
            "path_guard_used": True,
            "redactions_total": redaction.redactions,
            "preliminary": True,
        }
        return CommandResult(
            command="connector validate",
            ok=not has_block,
            exit_code=ExitCode.PASS if not has_block else ExitCode.BLOCK,
            message="Connector Registry validation passed." if not has_block else "Connector Registry validation blocked.",
            data={
                "summary": summary,
                "registry": {
                    "registry_id": registry.get("registry_id") if isinstance(registry, dict) else None,
                    "status": registry.get("status") if isinstance(registry, dict) else None,
                    "mcp": mcp,
                    "defaults": defaults,
                    "connectors": connectors,
                },
                "notes": [
                    "FUNC-SPRINT-88 validates registry/schema/threat-model only; no connector or MCP runtime is executed.",
                    "Sprint 89 may add a read-only adapter, but only after this registry remains PASS.",
                ],
            },
            findings=findings,
        )


def _summary_template(registry_path: str, schema_path: str, *, path_allowed: bool) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "registry_path": registry_path,
        "schema_path": schema_path,
        "path_allowed": path_allowed,
        "deny_by_default_required": True,
        "mcp_runtime_enabled": False,
        "connector_calls_enabled": False,
        "network_used": False,
        "external_api_used": False,
        "preliminary": True,
    }


def _rel(root: Path, path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return p.as_posix()
