from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.identity import IdentityRegistry, IdentityRegistryOptions
from devpilot_core.policy.sensitive_actions import (
    DEFAULT_MIASI_POLICY_MATRIX,
    DEFAULT_SENSITIVE_ACTION_CATALOG,
    SensitiveActionCatalogOptions,
    SensitiveActionCatalogValidator,
)
from devpilot_core.schemas import SchemaValidator

POST_H_012_C_CREATED_BY = "POST-H-012-C"
RBAC_EXPOSURE_COMMAND = "identity exposure"
RBAC_EXPOSURE_SCHEMA_ID = "SCHEMA-DEVPL-RBAC-EXPOSURE-REPORT-V1"
RBAC_EXPOSURE_REPORT_ID = "devpilot-approval-rbac-exposure"
DEFAULT_RBAC_EXPOSURE_REPORT_JSON = Path("outputs/reports/approval_rbac_exposure.json")
DEFAULT_RBAC_EXPOSURE_REPORT_MARKDOWN = Path("outputs/reports/approval_rbac_exposure.md")
DEFAULT_RBAC_EXPOSURE_SCHEMA = Path("docs/schemas/rbac_exposure_report.schema.json")
DEFAULT_INTERFACES = ("cli", "api", "ui", "agent", "multiagent", "remote", "connector", "plugin")
DANGEROUS_DOMAINS = {"remote", "plugin", "connector"}


@dataclass(frozen=True)
class RbacExposureOptions:
    identity_registry_path: Path = Path(".devpilot/identity/identity_registry.json")
    sensitive_action_catalog_path: Path = DEFAULT_SENSITIVE_ACTION_CATALOG
    policy_matrix_path: Path = DEFAULT_MIASI_POLICY_MATRIX
    schema_path: Path = DEFAULT_RBAC_EXPOSURE_SCHEMA
    output_json: Path = DEFAULT_RBAC_EXPOSURE_REPORT_JSON
    output_markdown: Path = DEFAULT_RBAC_EXPOSURE_REPORT_MARKDOWN
    write_report: bool = False


class RbacExposureReporter:
    """Build the POST-H-012-C local RBAC exposure report.

    The report is read-only and deterministic: it reads the local identity
    registry, sensitive action catalog and MIASI policy matrix, then materializes
    a matrix of actor/role/action/interface/effect. It does not grant access,
    execute actions, call remote services or mutate source files. Optional report
    writing is explicit and limited to outputs/reports.
    """

    def __init__(self, root: Path, *, options: RbacExposureOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RbacExposureOptions()

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        identity_result = IdentityRegistry(
            self.root,
            options=IdentityRegistryOptions(registry_path=str(self.options.identity_registry_path)),
        ).validate()
        if not identity_result.ok:
            findings.extend(identity_result.findings)

        catalog_validator = SensitiveActionCatalogValidator(
            self.root,
            options=SensitiveActionCatalogOptions(
                catalog_path=self.options.sensitive_action_catalog_path,
                miasi_policy_matrix_path=self.options.policy_matrix_path,
            ),
        )
        catalog_result = catalog_validator.run()
        if not catalog_result.ok:
            findings.extend(catalog_result.findings)

        identity = self._load_json(self.options.identity_registry_path)
        catalog = self._load_json(self.options.sensitive_action_catalog_path)
        policy_matrix = self._load_json(self.options.policy_matrix_path)
        roles = [item for item in identity.get("roles", []) if isinstance(item, dict)]
        actors = [item for item in identity.get("actors", []) if isinstance(item, dict)]
        actions = [item for item in catalog.get("actions", []) if isinstance(item, dict)]
        role_ids = {str(role.get("role_id", "")).strip() for role in roles}
        policy_by_id = {str(rule.get("rule_id", "")).strip(): rule for rule in policy_matrix.get("rules", []) if isinstance(rule, dict)}

        matrix = self._build_matrix(actors, roles, actions, policy_by_id)
        findings.extend(self._semantic_findings(actions, matrix, role_ids))
        summary = self._summary(actors, roles, actions, matrix, findings)
        report = self._report(summary, matrix, findings)

        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._write_reports(report)
            summary["reports_written"] = True
            summary["output_json"] = reports["json"]
            summary["output_markdown"] = reports["markdown"]
            report["summary"] = summary
            report["source_paths"]["report_json"] = reports["json"]
            report["source_paths"]["report_markdown"] = reports["markdown"]
            self._write_json(report, self.root / self.options.output_json)

        ok = not any(finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for finding in findings)
        findings.append(
            Finding(
                id="RBAC_EXPOSURE_REPORT_PASS" if ok else "RBAC_EXPOSURE_REPORT_BLOCK",
                message="RBAC exposure report passed." if ok else "RBAC exposure report blocked.",
                severity=Severity.INFO if ok else Severity.BLOCK,
                metadata=summary,
            )
        )
        report["findings"] = [finding.to_dict() for finding in findings]
        if self.options.write_report:
            self._write_json(report, self.root / self.options.output_json)
            self._write_markdown(report, self.root / self.options.output_markdown)

        data: dict[str, Any] = {"summary": summary, "report": report}
        if reports:
            data["reports"] = reports
        return CommandResult(
            command=RBAC_EXPOSURE_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="RBAC exposure report passed." if ok else "RBAC exposure report blocked.",
            data=data,
            findings=findings,
        )

    def validate_report(self, report_path: Path | None = None) -> CommandResult:
        instance = report_path or self.options.output_json
        return SchemaValidator(self.root).validate(schema=self.options.schema_path, instance=instance)

    def _build_matrix(
        self,
        actors: list[dict[str, Any]],
        roles: list[dict[str, Any]],
        actions: list[dict[str, Any]],
        policy_by_id: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        role_map = {str(role.get("role_id", "")).strip(): role for role in roles}
        matrix: list[dict[str, Any]] = []
        for actor in actors:
            actor_id = str(actor.get("actor_id", "")).strip()
            actor_status = str(actor.get("status", "")).strip() or "unknown"
            actor_roles = [str(role_id).strip() for role_id in actor.get("roles", []) if str(role_id).strip()]
            for role_id in actor_roles:
                role = role_map.get(role_id, {})
                permissions = set(str(item).strip() for item in role.get("permissions", []) if str(item).strip())
                for action in actions:
                    action_id = str(action.get("action_id", "")).strip()
                    domain = str(action.get("domain", "")).strip()
                    required_role = str(action.get("requires_rbac_role", "")).strip()
                    allowed = {str(item).strip() for item in action.get("allowed_interfaces", [])}
                    blocked = {str(item).strip() for item in action.get("blocked_interfaces", [])}
                    interfaces = sorted(set(DEFAULT_INTERFACES) | allowed | blocked)
                    for interface in interfaces:
                        effect, reason = self._effect_for_entry(
                            role_id=role_id,
                            actor_status=actor_status,
                            permissions=permissions,
                            action=action,
                            interface=interface,
                            required_role=required_role,
                            allowed_interfaces=allowed,
                            blocked_interfaces=blocked,
                        )
                        policy_rules = [policy_by_id.get(str(rule_id), {}) for rule_id in action.get("miasi_policy_rule_ids", [])]
                        matrix.append(
                            {
                                "actor_id": actor_id,
                                "actor_status": actor_status,
                                "actor_roles": actor_roles,
                                "role_id": role_id,
                                "role_declared": role_id in role_map,
                                "role_permissions_total": len(permissions),
                                "action_id": action_id,
                                "domain": domain,
                                "risk_level": str(action.get("risk_level", "")),
                                "status": str(action.get("status", "")),
                                "interface": interface,
                                "effect": effect,
                                "reason": reason,
                                "requires_approval": bool(action.get("requires_approval")),
                                "requires_rbac_role": required_role,
                                "required_role_declared": required_role in role_map,
                                "role_matches_required": role_id == required_role or "*" in permissions,
                                "requires_command_binding": bool(action.get("requires_command_binding")),
                                "requires_tool_call_binding": bool(action.get("requires_tool_call_binding")),
                                "interface_declared_allowed": interface in allowed,
                                "interface_declared_blocked": interface in blocked,
                                "default_effect": str(action.get("default_effect", "")),
                                "executable": bool(action.get("executable")),
                                "source_mutation_allowed": bool(action.get("source_mutation_allowed")),
                                "miasi_policy_rule_ids": [str(rule_id) for rule_id in action.get("miasi_policy_rule_ids", [])],
                                "policy_matrix_effects": [str(rule.get("default_effect", "")) for rule in policy_rules if rule],
                            }
                        )
        return matrix

    def _effect_for_entry(
        self,
        *,
        role_id: str,
        actor_status: str,
        permissions: set[str],
        action: dict[str, Any],
        interface: str,
        required_role: str,
        allowed_interfaces: set[str],
        blocked_interfaces: set[str],
    ) -> tuple[str, str]:
        action_id = str(action.get("action_id", ""))
        status = str(action.get("status", ""))
        default_effect = str(action.get("default_effect", ""))
        executable = bool(action.get("executable"))
        source_mutation_allowed = bool(action.get("source_mutation_allowed"))
        if actor_status != "active":
            return "block", "actor is not active"
        if interface in blocked_interfaces:
            return "block", "interface is explicitly blocked by SensitiveActionCatalog"
        if status == "blocked" or default_effect in {"block", "deny"} or not executable:
            return "block" if default_effect != "deny" else "deny", "action remains non-executable and deny/block-by-default in SensitiveActionCatalog"
        if required_role and role_id != required_role and "*" not in permissions:
            return "block", "role does not match required RBAC role"
        if interface not in allowed_interfaces:
            return "block", "interface is not declared as allowed"
        if source_mutation_allowed:
            return "block", "source mutation remains blocked until POST-H-012-D/E enforcement"
        return "allow", f"role {role_id} can access {action_id} through {interface}"

    def _semantic_findings(self, actions: list[dict[str, Any]], matrix: list[dict[str, Any]], role_ids: set[str]) -> list[Finding]:
        findings: list[Finding] = []
        for action in actions:
            action_id = str(action.get("action_id", ""))
            risk = str(action.get("risk_level", ""))
            domain = str(action.get("domain", ""))
            required_role = str(action.get("requires_rbac_role", "")).strip()
            if risk == "critical" and not required_role:
                findings.append(Finding("RBAC_EXPOSURE_CRITICAL_ACTION_WITHOUT_ROLE", "Critical action has no required RBAC role.", Severity.BLOCK, path=action_id, metadata={"action_id": action_id}))
            if required_role and required_role not in role_ids:
                findings.append(Finding("RBAC_EXPOSURE_REQUIRED_ROLE_UNKNOWN", "Sensitive action references a role that is not declared in the Identity Registry.", Severity.WARNING, path=action_id, metadata={"action_id": action_id, "requires_rbac_role": required_role}))
            exposed = [entry for entry in matrix if entry["action_id"] == action_id and entry["effect"] == "allow"]
            if risk == "critical" and any(not entry["requires_rbac_role"] for entry in exposed):
                findings.append(Finding("RBAC_EXPOSURE_CRITICAL_EXPOSED_WITHOUT_ROLE", "Critical action is exposed without RBAC role binding.", Severity.BLOCK, path=action_id, metadata={"action_id": action_id}))
            if risk == "critical" and any(entry["interface"] in {"api", "ui"} for entry in exposed):
                findings.append(Finding("RBAC_EXPOSURE_API_UI_CRITICAL_ACTION_ALLOWED", "API/UI must not expose critical sensitive actions in POST-H-012-C.", Severity.BLOCK, path=action_id, metadata={"action_id": action_id}))
            if domain in DANGEROUS_DOMAINS and exposed:
                findings.append(Finding("RBAC_EXPOSURE_DANGEROUS_CAPABILITY_ALLOWED", "Remote/plugin/connector write capability must remain blocked.", Severity.BLOCK, path=action_id, metadata={"action_id": action_id, "domain": domain}))
        if not any(f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for f in findings):
            findings.append(Finding("RBAC_EXPOSURE_DANGEROUS_SURFACES_BLOCKED", "Remote, plugin and connector write surfaces remain blocked in the exposure matrix.", Severity.INFO))
            findings.append(Finding("RBAC_EXPOSURE_API_UI_CRITICAL_SURFACES_BLOCKED", "API/UI critical action exposure is blocked by the exposure matrix.", Severity.INFO))
        return findings

    def _summary(self, actors: list[dict[str, Any]], roles: list[dict[str, Any]], actions: list[dict[str, Any]], matrix: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        critical_actions = [a for a in actions if a.get("risk_level") == "critical"]
        role_ids = {str(role.get("role_id", "")).strip() for role in roles}
        exposed = [entry for entry in matrix if entry["effect"] == "allow"]
        dangerous_action_ids = {str(action.get("action_id")) for action in actions if str(action.get("domain")) in DANGEROUS_DOMAINS}
        remote_plugin_connector = [entry for entry in matrix if entry["action_id"] in dangerous_action_ids]
        summary = {
            "created_by": POST_H_012_C_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "actions_total": len(actions),
            "critical_actions_total": len(critical_actions),
            "domains_total": len({str(a.get("domain", "")) for a in actions}),
            "actors_total": len(actors),
            "roles_total": len(roles),
            "interfaces_total": len(DEFAULT_INTERFACES),
            "matrix_entries_total": len(matrix),
            "allow_entries_total": len(exposed),
            "blocked_entries_total": sum(1 for entry in matrix if entry["effect"] in {"block", "deny"}),
            "critical_actions_without_required_role_total": sum(1 for a in critical_actions if not str(a.get("requires_rbac_role", "")).strip()),
            "missing_required_role_refs_total": sum(1 for a in actions if str(a.get("requires_rbac_role", "")).strip() and str(a.get("requires_rbac_role", "")).strip() not in role_ids),
            "critical_exposed_without_role_total": sum(1 for entry in exposed if entry["risk_level"] == "critical" and not entry["requires_rbac_role"]),
            "api_ui_exposed_critical_total": sum(1 for entry in exposed if entry["risk_level"] == "critical" and entry["interface"] in {"api", "ui"}),
            "dangerous_capability_exposed_total": sum(1 for entry in exposed if entry["action_id"] in dangerous_action_ids),
            "remote_plugin_connector_write_blocked_total": sum(1 for entry in remote_plugin_connector if entry["effect"] in {"block", "deny"}),
            "findings_total": len(findings),
            "blocking_findings_total": sum(1 for f in findings if f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}),
            "warning_findings_total": sum(1 for f in findings if f.severity == Severity.WARNING),
            "identity_registry_read": True,
            "sensitive_action_catalog_read": True,
            "policy_matrix_read": True,
            "reports_written": False,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "llm_judge_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
        }
        return summary

    def _report(self, summary: dict[str, Any], matrix: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "schema_id": RBAC_EXPOSURE_SCHEMA_ID,
            "report_id": RBAC_EXPOSURE_REPORT_ID,
            "created_by": POST_H_012_C_CREATED_BY,
            "status": "implemented-initial" if summary.get("blocking_findings_total", 0) == 0 else "blocked",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "preliminary": True,
            "source_paths": {
                "identity_registry": str(self.options.identity_registry_path).replace("\\", "/"),
                "sensitive_action_catalog": str(self.options.sensitive_action_catalog_path).replace("\\", "/"),
                "policy_matrix": str(self.options.policy_matrix_path).replace("\\", "/"),
            },
            "summary": summary,
            "matrix": matrix,
            "findings": [finding.to_dict() for finding in findings],
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "llm_judge_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
            },
            "notes": [
                "POST-H-012-C is an exposure report only; it does not grant permissions or execute actions.",
                "All sensitive actions remain non-executable until later PolicyEngine enforcement and quality gate work.",
                "outputs/reports/approval_rbac_exposure.json is runtime evidence and must not be versioned as a source-of-truth artifact.",
            ],
        }

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        md_path = self.root / self.options.output_markdown
        self._write_json(report, json_path)
        self._write_markdown(report, md_path)
        return {"json": self._rel(json_path), "markdown": self._rel(md_path)}

    def _write_json(self, payload: dict[str, Any], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _write_markdown(self, report: dict[str, Any], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        summary = report["summary"]
        lines = [
            "# Approval/RBAC exposure report",
            "",
            f"Generated by: `{POST_H_012_C_CREATED_BY}`",
            f"Status: `{report['status']}`",
            "",
            "## Summary",
            "",
            f"- Actions: {summary['actions_total']}",
            f"- Actors: {summary['actors_total']}",
            f"- Roles: {summary['roles_total']}",
            f"- Matrix entries: {summary['matrix_entries_total']}",
            f"- Allowed entries: {summary['allow_entries_total']}",
            f"- Blocked entries: {summary['blocked_entries_total']}",
            f"- API/UI critical exposures: {summary['api_ui_exposed_critical_total']}",
            f"- Dangerous capability exposures: {summary['dangerous_capability_exposed_total']}",
            "",
            "## Safety",
            "",
            "- Local-first: true",
            "- Dry-run: true",
            "- Network used: false",
            "- External APIs used: false",
            "- Remote execution enabled: false",
            "- Connector write enabled: false",
            "- Plugin execution enabled: false",
            "",
            "## Notes",
            "",
            "This report is implemented-initial and read-only. It is evidence for POST-H-012-C, not an authorization mechanism.",
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _load_json(self, rel_path: Path) -> dict[str, Any]:
        path = self.root / rel_path
        if not path.exists():
            return {}
        loaded = json.loads(path.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else {}

    def _rel(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root)).replace("\\", "/")
        except Exception:
            return str(path).replace("\\", "/")
