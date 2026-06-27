from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator

POST_H_012_A_CREATED_BY = "POST-H-012-A"
SENSITIVE_ACTION_CATALOG_ID = "devpilot-sensitive-actions"
SENSITIVE_ACTION_CATALOG_SCHEMA_ID = "SCHEMA-DEVPL-SENSITIVE-ACTION-CATALOG-V1"
DEFAULT_SENSITIVE_ACTION_CATALOG = Path(".devpilot/approval/sensitive_action_catalog.json")
DEFAULT_SENSITIVE_ACTION_CATALOG_SCHEMA = Path("docs/schemas/sensitive_action_catalog.schema.json")
DEFAULT_MIASI_POLICY_MATRIX = Path(".devpilot/miasi/policy_matrix.json")
DEFAULT_MIASI_TOOL_REGISTRY = Path(".devpilot/miasi/tool_registry.json")

REQUIRED_SENSITIVE_ACTION_DOMAINS = {
    "patch",
    "refactor",
    "release",
    "connector",
    "plugin",
    "remote",
    "filesystem",
    "model",
    "agent",
    "approval",
    "identity",
}

BLOCKED_CAPABILITY_ACTIONS = {
    "remote": {"remote.execute"},
    "connector": {"connector.write_execute"},
    "plugin": {"plugin.execute_code"},
}


@dataclass(frozen=True)
class SensitiveActionCatalogOptions:
    catalog_path: Path = DEFAULT_SENSITIVE_ACTION_CATALOG
    schema_path: Path = DEFAULT_SENSITIVE_ACTION_CATALOG_SCHEMA
    miasi_policy_matrix_path: Path = DEFAULT_MIASI_POLICY_MATRIX
    miasi_tool_registry_path: Path = DEFAULT_MIASI_TOOL_REGISTRY


class SensitiveActionCatalogValidator:
    """Validate the POST-H-012-A sensitive action catalog.

    The catalog is deliberately declarative. It does not authorize execution,
    does not change PolicyEngine behavior, does not perform mutations and does
    not activate connector writes, plugin execution or remote execution.
    """

    def __init__(self, root: Path, *, options: SensitiveActionCatalogOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SensitiveActionCatalogOptions()

    @property
    def catalog_path(self) -> Path:
        return self.root / self.options.catalog_path

    @property
    def schema_path(self) -> Path:
        return self.root / self.options.schema_path

    @property
    def miasi_policy_matrix_path(self) -> Path:
        return self.root / self.options.miasi_policy_matrix_path

    @property
    def miasi_tool_registry_path(self) -> Path:
        return self.root / self.options.miasi_tool_registry_path

    def load(self) -> dict[str, Any]:
        return _load_json(self.catalog_path)

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        if not self.catalog_path.exists():
            findings.append(
                Finding(
                    id="SENSITIVE_ACTION_CATALOG_MISSING",
                    message="Sensitive action catalog is missing.",
                    severity=Severity.BLOCK,
                    path=_rel(self.catalog_path, self.root),
                )
            )
            return self._result(False, findings, {}, [])

        try:
            payload = self.load()
        except Exception as exc:
            findings.append(
                Finding(
                    id="SENSITIVE_ACTION_CATALOG_INVALID_JSON",
                    message=f"Sensitive action catalog could not be parsed: {exc}",
                    severity=Severity.ERROR,
                    path=_rel(self.catalog_path, self.root),
                )
            )
            return self._result(False, findings, {}, [])

        schema_result = SchemaValidator(self.root).validate(schema=self.options.schema_path, instance=self.options.catalog_path)
        if not schema_result.ok:
            findings.extend(schema_result.findings)

        actions = [item for item in payload.get("actions", []) if isinstance(item, dict)]
        action_ids = [str(action.get("action_id", "")).strip() for action in actions]
        duplicate_action_ids = sorted({action_id for action_id in action_ids if action_ids.count(action_id) > 1})
        for action_id in duplicate_action_ids:
            findings.append(
                Finding(
                    id="SENSITIVE_ACTION_DUPLICATE_ID",
                    message="Sensitive action catalog contains a duplicate action_id.",
                    severity=Severity.BLOCK,
                    metadata={"action_id": action_id},
                )
            )

        domains = {str(action.get("domain", "")).strip() for action in actions}
        required_domains = set(payload.get("required_domains", []))
        missing_domains = sorted(REQUIRED_SENSITIVE_ACTION_DOMAINS - domains)
        missing_required_domains = sorted(REQUIRED_SENSITIVE_ACTION_DOMAINS - required_domains)
        for domain in missing_domains:
            findings.append(
                Finding(
                    id="SENSITIVE_ACTION_DOMAIN_MISSING",
                    message="Required sensitive action domain is not covered by any action.",
                    severity=Severity.BLOCK,
                    metadata={"domain": domain},
                )
            )
        for domain in missing_required_domains:
            findings.append(
                Finding(
                    id="SENSITIVE_ACTION_REQUIRED_DOMAIN_MISSING",
                    message="Required sensitive action domain is missing from required_domains.",
                    severity=Severity.BLOCK,
                    metadata={"domain": domain},
                )
            )

        policy_rule_ids = self._miasi_policy_rule_ids()
        tool_ids = self._miasi_tool_ids()
        miasi_links_total = 0
        for action in actions:
            action_id = str(action.get("action_id", ""))
            risk = str(action.get("risk_level", ""))
            domain = str(action.get("domain", ""))
            default_effect = str(action.get("default_effect", ""))
            status = str(action.get("status", ""))
            executable = bool(action.get("executable"))
            requires_approval = bool(action.get("requires_approval"))
            requires_rbac_role = str(action.get("requires_rbac_role", "")).strip()
            requires_tool_call_binding = bool(action.get("requires_tool_call_binding"))
            requires_command_binding = bool(action.get("requires_command_binding"))
            if risk == "critical" and (not requires_approval or not requires_rbac_role):
                findings.append(
                    Finding(
                        id="SENSITIVE_ACTION_CRITICAL_WITHOUT_APPROVAL_RBAC",
                        message="Critical sensitive action must require both approval and RBAC.",
                        severity=Severity.BLOCK,
                        path=action_id,
                        metadata={"action_id": action_id, "requires_approval": requires_approval, "requires_rbac_role": requires_rbac_role},
                    )
                )
            if risk == "critical" and (not requires_tool_call_binding or not requires_command_binding):
                findings.append(
                    Finding(
                        id="SENSITIVE_ACTION_CRITICAL_WITHOUT_STRONG_BINDING",
                        message="Critical sensitive action must require tool_call and command binding.",
                        severity=Severity.BLOCK,
                        path=action_id,
                        metadata={"action_id": action_id},
                    )
                )
            if domain in {"remote", "plugin", "connector"} and (executable or status != "blocked" or default_effect not in {"block", "deny"}):
                findings.append(
                    Finding(
                        id="SENSITIVE_ACTION_DANGEROUS_CAPABILITY_NOT_BLOCKED",
                        message="Remote/plugin/connector write capabilities must remain blocked and non-executable.",
                        severity=Severity.BLOCK,
                        path=action_id,
                        metadata={"action_id": action_id, "domain": domain, "status": status, "default_effect": default_effect, "executable": executable},
                    )
                )
            for rule_id in action.get("miasi_policy_rule_ids", []):
                miasi_links_total += 1
                if rule_id not in policy_rule_ids:
                    findings.append(
                        Finding(
                            id="SENSITIVE_ACTION_MIASI_POLICY_RULE_UNKNOWN",
                            message="Sensitive action references a missing MIASI policy rule.",
                            severity=Severity.BLOCK,
                            path=action_id,
                            metadata={"action_id": action_id, "rule_id": rule_id},
                        )
                    )
            for tool_id in action.get("tool_ids", []):
                if tool_id not in tool_ids:
                    findings.append(
                        Finding(
                            id="SENSITIVE_ACTION_MIASI_TOOL_UNKNOWN",
                            message="Sensitive action references a missing MIASI tool.",
                            severity=Severity.BLOCK,
                            path=action_id,
                            metadata={"action_id": action_id, "tool_id": tool_id},
                        )
                    )

        for domain, required_action_ids in BLOCKED_CAPABILITY_ACTIONS.items():
            present = {str(action.get("action_id", "")) for action in actions if str(action.get("domain", "")) == domain}
            for action_id in sorted(required_action_ids - present):
                findings.append(
                    Finding(
                        id="SENSITIVE_ACTION_BLOCKED_CAPABILITY_ACTION_MISSING",
                        message="Catalog must explicitly declare the blocked capability action.",
                        severity=Severity.BLOCK,
                        metadata={"domain": domain, "action_id": action_id},
                    )
                )

        safety = payload.get("safety", {}) if isinstance(payload.get("safety"), dict) else {}
        for flag in ("remote_execution_enabled", "connector_write_enabled", "plugin_execution_enabled", "network_used", "external_api_used", "mutations_performed", "source_mutations_performed"):
            if safety.get(flag) is not False:
                findings.append(Finding("SENSITIVE_ACTION_SAFETY_FLAG_NOT_FALSE", "Sensitive action catalog safety flag must remain false.", Severity.BLOCK, metadata={"flag": flag}))
        if safety.get("dry_run_default") is not True or safety.get("deny_by_default") is not True:
            findings.append(Finding("SENSITIVE_ACTION_SAFETY_BASELINE_INVALID", "Sensitive action catalog must be dry-run and deny-by-default.", Severity.BLOCK))

        summary = self._build_summary(payload, actions, miasi_links_total)
        ok = not any(finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for finding in findings)
        findings.append(
            Finding(
                id="SENSITIVE_ACTION_CATALOG_PASS" if ok else "SENSITIVE_ACTION_CATALOG_BLOCK",
                message="Sensitive action catalog validation passed." if ok else "Sensitive action catalog validation failed.",
                severity=Severity.INFO if ok else Severity.BLOCK,
                metadata=summary,
            )
        )
        return self._result(ok, findings, summary, actions)

    def _result(self, ok: bool, findings: list[Finding], summary: dict[str, Any], actions: list[dict[str, Any]]) -> CommandResult:
        return CommandResult(
            command="policy sensitive-actions validate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Sensitive action catalog validation passed." if ok else "Sensitive action catalog validation failed.",
            data={
                "summary": summary,
                "catalog_path": str(self.options.catalog_path).replace("\\", "/"),
                "schema_path": str(self.options.schema_path).replace("\\", "/"),
                "actions": actions,
                "safety": {
                    "local_first": True,
                    "dry_run": True,
                    "network_used": False,
                    "external_api_used": False,
                    "llm_judge_used": False,
                    "remote_execution_enabled": False,
                    "connector_write_enabled": False,
                    "plugin_execution_enabled": False,
                    "mutations_performed": False,
                    "source_mutations_performed": False,
                },
            },
            findings=findings,
        )

    def _build_summary(self, payload: dict[str, Any], actions: list[dict[str, Any]], miasi_links_total: int) -> dict[str, Any]:
        domains = {str(action.get("domain", "")) for action in actions}
        return {
            "created_by": POST_H_012_A_CREATED_BY,
            "status": payload.get("status"),
            "preliminary": True,
            "catalog_id": payload.get("catalog_id"),
            "actions_total": len(actions),
            "domains_total": len(domains),
            "required_domains_total": len(REQUIRED_SENSITIVE_ACTION_DOMAINS),
            "required_domains_covered_total": len(REQUIRED_SENSITIVE_ACTION_DOMAINS & domains),
            "critical_actions_total": sum(1 for action in actions if action.get("risk_level") == "critical"),
            "actions_requiring_approval_total": sum(1 for action in actions if action.get("requires_approval") is True),
            "actions_requiring_rbac_total": sum(1 for action in actions if str(action.get("requires_rbac_role", "")).strip()),
            "blocked_actions_total": sum(1 for action in actions if action.get("status") == "blocked" or action.get("default_effect") in {"block", "deny"}),
            "remote_actions_blocked_total": sum(1 for action in actions if action.get("domain") == "remote" and action.get("status") == "blocked" and action.get("executable") is False),
            "connector_write_actions_blocked_total": sum(1 for action in actions if action.get("action_id") == "connector.write_execute" and action.get("status") == "blocked" and action.get("executable") is False),
            "plugin_execution_actions_blocked_total": sum(1 for action in actions if action.get("action_id") == "plugin.execute_code" and action.get("status") == "blocked" and action.get("executable") is False),
            "miasi_policy_links_total": miasi_links_total,
            "catalog_path": str(self.options.catalog_path).replace("\\", "/"),
            "schema_path": str(self.options.schema_path).replace("\\", "/"),
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

    def _miasi_policy_rule_ids(self) -> set[str]:
        payload = _load_json(self.miasi_policy_matrix_path) if self.miasi_policy_matrix_path.exists() else {}
        return {str(rule.get("rule_id", "")) for rule in payload.get("rules", []) if isinstance(rule, dict)}

    def _miasi_tool_ids(self) -> set[str]:
        payload = _load_json(self.miasi_tool_registry_path) if self.miasi_tool_registry_path.exists() else {}
        return {str(tool.get("tool_id", "")) for tool in payload.get("tools", []) if isinstance(tool, dict)}


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"JSON root must be an object: {_rel(path, path.parent)}")
    return loaded


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")
