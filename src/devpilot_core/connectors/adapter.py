from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.connectors.registry import ConnectorRegistry, ConnectorRegistryOptions
from devpilot_core.observability import EventLogger
from devpilot_core.policy import PathGuard, PolicyEffect, PolicyEngine, PolicyRequest, SecretGuard

_DEFAULT_REGISTRY_PATH = ".devpilot/connectors/connector_registry.json"
_READ_ONLY_CONNECTORS = {"local.docs"}
_CONNECTOR_ALIASES = {
    "local-docs": "local.docs",
    "local_docs": "local.docs",
    "docs": "local.docs",
    "local.docs": "local.docs",
}
_OPERATION_ALIASES = {
    "list": "list_sources",
    "list_sources": "list_sources",
    "query": "query_sources",
    "query_sources": "query_sources",
}
_ALLOWED_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml"}
_DENIED_PARTS = {".git", ".venv", "node_modules", "outputs", "dist", "__pycache__", ".pytest_cache", "backups", "agent_sessions"}
_DENIED_FILES = {".env", ".env.local", ".env.dev", "devpilot.db", "providers.yaml"}


@dataclass(frozen=True)
class ConnectorCallOptions:
    """Options for a governed Sprint 89 connector call."""

    connector: str
    operation: str
    dry_run: bool = True
    query: str | None = None
    limit: int = 20
    registry_path: str = _DEFAULT_REGISTRY_PATH


class ConnectorAdapter:
    """Controlled read-only connector adapter for FUNC-SPRINT-89.

    The adapter deliberately avoids a real MCP client/server implementation. It
    reads the Connector Registry, enforces deny-by-default semantics, evaluates
    PolicyEngine before any read-only operation and emits a trace event for every
    attempted connector call. Sprint 89 only supports local documentation
    discovery/query operations in dry-run/read-only mode.
    """

    def __init__(self, root: Path, *, registry_path: str = _DEFAULT_REGISTRY_PATH) -> None:
        self.root = Path(root).resolve()
        self.registry_path = registry_path
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()
        self.policy = PolicyEngine(self.root)

    def call(self, options: ConnectorCallOptions) -> CommandResult:
        connector_id = _canonical_connector(options.connector)
        operation_id = _canonical_operation(options.operation)
        limit = max(1, min(int(options.limit), 100))
        findings: list[Finding] = []

        registry_result = ConnectorRegistry(
            self.root,
            options=ConnectorRegistryOptions(registry_path=options.registry_path),
        ).validate()
        if not registry_result.ok:
            result = CommandResult(
                command="connector call",
                ok=False,
                exit_code=registry_result.exit_code,
                message="Connector call blocked because Connector Registry validation failed.",
                data={"summary": _summary(connector_id, operation_id, options.dry_run, limit, registry_valid=False)},
                findings=[*registry_result.findings, Finding("CONNECTOR_CALL_REGISTRY_INVALID", "Connector Registry must pass before connector calls.", Severity.BLOCK)],
            )
            return self._emit_call_event(result, connector_id=connector_id, operation_id=operation_id)

        registry = self._load_registry(options.registry_path)
        connector = self._find_connector(registry, connector_id)
        if connector is None:
            result = CommandResult(
                command="connector call",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Connector call blocked: connector is not registered.",
                data={"summary": _summary(connector_id, operation_id, options.dry_run, limit, registry_valid=True)},
                findings=[Finding("CONNECTOR_NOT_REGISTERED", "Only registered connectors can be called.", Severity.BLOCK, metadata={"connector": connector_id})],
            )
            return self._emit_call_event(result, connector_id=connector_id, operation_id=operation_id)

        operation = self._find_operation(connector, operation_id)
        if operation is None:
            result = CommandResult(
                command="connector call",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Connector call blocked: operation is not registered for connector.",
                data={"summary": _summary(connector_id, operation_id, options.dry_run, limit, registry_valid=True)},
                findings=[Finding("CONNECTOR_OPERATION_NOT_REGISTERED", "Connector operation must be declared in the registry.", Severity.BLOCK, metadata={"connector": connector_id, "operation": operation_id})],
            )
            return self._emit_call_event(result, connector_id=connector_id, operation_id=operation_id)

        findings.extend(self._governance_findings(connector, operation, dry_run=options.dry_run))
        policy_result = self.policy.evaluate(
            PolicyRequest(
                action="read",
                path="docs",
                text=options.query,
                dry_run=True,
                tool_id="connector.call",
                subject=f"{connector_id}:{operation_id}",
                metadata={
                    "component": "ConnectorAdapter",
                    "sprint": "FUNC-SPRINT-89",
                    "connector_id": connector_id,
                    "operation_id": operation_id,
                    "read_only": True,
                    "network_used": False,
                    "external_api_used": False,
                },
            )
        )
        if not policy_result.ok:
            findings.extend(policy_result.findings)

        if any(f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for f in findings):
            result = CommandResult(
                command="connector call",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Connector call blocked by registry or policy.",
                data={
                    "summary": {
                        **_summary(connector_id, operation_id, options.dry_run, limit, registry_valid=True),
                        "policy_checked": True,
                        "policy_allowed": policy_result.ok,
                        "trace_event_emitted": False,
                    },
                    "connector": _public_connector_metadata(connector),
                    "operation": _public_operation_metadata(operation),
                    "policy": policy_result.data.get("summary", {}),
                },
                findings=findings,
            )
            return self._emit_call_event(result, connector_id=connector_id, operation_id=operation_id)

        payload = self._execute_read_only(connector_id, operation_id, query=options.query, limit=limit)
        result = CommandResult(
            command="connector call",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Connector call completed in governed read-only dry-run mode.",
            data={
                "summary": {
                    **_summary(connector_id, operation_id, options.dry_run, limit, registry_valid=True),
                    "policy_checked": True,
                    "policy_allowed": True,
                    "trace_event_emitted": False,
                    "items_total": payload.get("items_total", 0),
                    "sources_total": payload.get("sources_total", 0),
                    "connector_status": connector.get("status"),
                    "operation_status": operation.get("status"),
                },
                "connector": _public_connector_metadata(connector),
                "operation": _public_operation_metadata(operation),
                "call": {
                    "call_id": f"conncall_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                    "mode": "dry-run-read-only",
                    "simulated": True,
                    "read_only": True,
                    "network_used": False,
                    "external_api_used": False,
                    "shell_used": False,
                    "remote_execution_used": False,
                },
                "result": payload,
                "policy": policy_result.data.get("summary", {}),
            },
            findings=[Finding("CONNECTOR_CALL_DRY_RUN_READ_ONLY", "Connector call passed PolicyEngine and returned local read-only evidence.", Severity.INFO, metadata={"connector": connector_id, "operation": operation_id})],
        )
        return self._emit_call_event(result, connector_id=connector_id, operation_id=operation_id)

    def _load_registry(self, registry_path: str) -> dict[str, Any]:
        path = Path(registry_path)
        if not path.is_absolute():
            path = self.root / path
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _find_connector(registry: dict[str, Any], connector_id: str) -> dict[str, Any] | None:
        for connector in registry.get("connectors", []):
            if isinstance(connector, dict) and connector.get("connector_id") == connector_id:
                return connector
        return None

    @staticmethod
    def _find_operation(connector: dict[str, Any], operation_id: str) -> dict[str, Any] | None:
        for operation in connector.get("allowed_operations", []):
            if isinstance(operation, dict) and operation.get("operation_id") == operation_id:
                return operation
        return None

    def _governance_findings(self, connector: dict[str, Any], operation: dict[str, Any], *, dry_run: bool) -> list[Finding]:
        findings: list[Finding] = []
        connector_id = str(connector.get("connector_id"))
        operation_id = str(operation.get("operation_id"))
        if not dry_run:
            findings.append(Finding("CONNECTOR_CALL_REQUIRES_DRY_RUN", "Sprint 89 connector calls must use --dry-run; execute mode is not implemented.", Severity.BLOCK, metadata={"connector": connector_id, "operation": operation_id}))
        if connector_id not in _READ_ONLY_CONNECTORS:
            findings.append(Finding("CONNECTOR_NOT_READ_ONLY_MVP", "Sprint 89 allows only local read-only connector MVP calls.", Severity.BLOCK, metadata={"connector": connector_id}))
        if connector.get("status") != "implemented":
            findings.append(Finding("CONNECTOR_NOT_IMPLEMENTED", "Connector must be implemented before a governed call can run.", Severity.BLOCK, metadata={"connector": connector_id, "status": connector.get("status")}))
        if operation.get("status") != "implemented":
            findings.append(Finding("CONNECTOR_OPERATION_NOT_IMPLEMENTED", "Connector operation must be implemented before it can run.", Severity.BLOCK, metadata={"connector": connector_id, "operation": operation_id, "status": operation.get("status")}))
        if operation.get("side_effect") not in {"read", "none"}:
            findings.append(Finding("CONNECTOR_OPERATION_NOT_READ_ONLY", "Sprint 89 blocks connector operations that are not read-only.", Severity.BLOCK, metadata={"connector": connector_id, "operation": operation_id, "side_effect": operation.get("side_effect")}))
        for flag in ["network_allowed", "external_api_allowed", "execution_enabled"]:
            if connector.get(flag) is True:
                findings.append(Finding("CONNECTOR_RUNTIME_FLAG_BLOCKED", "Connector runtime flags must stay disabled for Sprint 89 MVP.", Severity.BLOCK, metadata={"connector": connector_id, "flag": flag}))
        if not connector.get("policy_rule_ids"):
            findings.append(Finding("CONNECTOR_POLICY_MISSING", "Connector calls require policy_rule_ids.", Severity.BLOCK, metadata={"connector": connector_id}))
        if connector.get("observability_required") is not True:
            findings.append(Finding("CONNECTOR_OBSERVABILITY_REQUIRED", "Connector calls require observability.", Severity.BLOCK, metadata={"connector": connector_id}))
        return findings

    def _execute_read_only(self, connector_id: str, operation_id: str, *, query: str | None, limit: int) -> dict[str, Any]:
        if connector_id != "local.docs":
            return {"items_total": 0, "sources_total": 0, "items": []}
        if operation_id == "list_sources":
            return self._list_local_docs(limit=limit)
        if operation_id == "query_sources":
            return self._query_local_docs(query=query or "", limit=limit)
        return {"items_total": 0, "sources_total": 0, "items": []}

    def _list_local_docs(self, *, limit: int) -> dict[str, Any]:
        docs_root = self.root / "docs"
        decision = self.path_guard.evaluate(docs_root, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return {"items_total": 0, "sources_total": 0, "items": [], "blocked": True, "reason": decision.reason}
        items: list[dict[str, Any]] = []
        if docs_root.exists():
            for path in sorted(docs_root.rglob("*")):
                if len(items) >= limit:
                    break
                if not path.is_file() or path.suffix.lower() not in _ALLOWED_SUFFIXES:
                    continue
                rel = _rel(self.root, path)
                if _denied(rel):
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                redacted = self.secret_guard.redact(text)
                items.append({
                    "path": rel,
                    "suffix": path.suffix.lower(),
                    "size_bytes": path.stat().st_size,
                    "redactions_total": redacted.redactions,
                })
        return {"items_total": len(items), "sources_total": len(items), "items": items}

    def _query_local_docs(self, *, query: str, limit: int) -> dict[str, Any]:
        terms = {term.lower() for term in query.replace("_", " ").replace("-", " ").split() if len(term) > 2}
        if not terms:
            return {"items_total": 0, "sources_total": 0, "items": [], "query_terms": []}
        docs_root = self.root / "docs"
        items: list[dict[str, Any]] = []
        for path in sorted(docs_root.rglob("*")) if docs_root.exists() else []:
            if len(items) >= limit:
                break
            if not path.is_file() or path.suffix.lower() not in _ALLOWED_SUFFIXES:
                continue
            rel = _rel(self.root, path)
            if _denied(rel):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            redacted = self.secret_guard.redact(text)
            lowered = str(redacted.value).lower()
            matched = sorted(term for term in terms if term in lowered)
            if not matched:
                continue
            line_no = _first_matching_line(str(redacted.value), matched)
            items.append({
                "path": rel,
                "line": line_no,
                "matched_terms": matched,
                "ref": f"{rel}#L{line_no}",
                "redactions_total": redacted.redactions,
            })
        return {"items_total": len(items), "sources_total": len(items), "items": items, "query_terms": sorted(terms)}

    def _emit_call_event(self, result: CommandResult, *, connector_id: str, operation_id: str) -> CommandResult:
        emitted = False
        try:
            EventLogger(self.root).emit_result(result, event_type="connector.call.evaluated", subject=f"{connector_id}:{operation_id}")
            emitted = True
        except Exception:
            emitted = False
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["trace_event_emitted"] = emitted
        data["summary"] = summary
        return CommandResult(command=result.command, ok=result.ok, exit_code=result.exit_code, message=result.message, data=data, findings=result.findings)


def _summary(connector_id: str, operation_id: str, dry_run: bool, limit: int, *, registry_valid: bool) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "connector_id": connector_id,
        "operation_id": operation_id,
        "dry_run": dry_run,
        "limit": limit,
        "registry_valid": registry_valid,
        "read_only": True,
        "policy_checked": False,
        "policy_allowed": False,
        "network_used": False,
        "external_api_used": False,
        "shell_used": False,
        "remote_execution_used": False,
        "mcp_client_used": False,
        "mcp_server_used": False,
        "connector_execution_performed": False,
        "preliminary": True,
    }


def _canonical_connector(value: str) -> str:
    normalized = (value or "").strip().lower()
    return _CONNECTOR_ALIASES.get(normalized, normalized)


def _canonical_operation(value: str) -> str:
    normalized = (value or "").strip().lower().replace("-", "_")
    return _OPERATION_ALIASES.get(normalized, normalized)


def _public_connector_metadata(connector: dict[str, Any]) -> dict[str, Any]:
    return {
        "connector_id": connector.get("connector_id"),
        "name": connector.get("name"),
        "type": connector.get("type"),
        "status": connector.get("status"),
        "risk_level": connector.get("risk_level"),
        "policy_rule_ids": connector.get("policy_rule_ids", []),
        "network_allowed": connector.get("network_allowed"),
        "external_api_allowed": connector.get("external_api_allowed"),
        "execution_enabled": connector.get("execution_enabled"),
    }


def _public_operation_metadata(operation: dict[str, Any]) -> dict[str, Any]:
    return {
        "operation_id": operation.get("operation_id"),
        "side_effect": operation.get("side_effect"),
        "status": operation.get("status"),
    }


def _denied(rel_path: str) -> bool:
    path = Path(rel_path)
    return any(part in _DENIED_PARTS for part in path.parts) or path.name in _DENIED_FILES


def _first_matching_line(text: str, terms: list[str]) -> int:
    for index, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        if any(term in lowered for term in terms):
            return index
    return 1


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
