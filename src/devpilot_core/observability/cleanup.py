from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.observability.inventory import ObservabilityInventoryBuilder, ObservabilityInventoryOptions
from devpilot_core.observability.retention import DEFAULT_OBSERVABILITY_RETENTION_POLICY
from devpilot_core.policy import PolicyEngine, PolicyRequest

OBSERVABILITY_CLEANUP_PLAN_SCHEMA_ID = "SCHEMA-DEVPL-OBSERVABILITY-CLEANUP-PLAN-V1"
OBSERVABILITY_CLEANUP_PLAN_CONTRACT = "ObservabilityCleanupPlan"
OBSERVABILITY_CLEANUP_PLAN_ID = "devpilot-local-observability-cleanup-plan"
POST_H_010_C_CREATED_BY = "POST-H-010-C"

DEFAULT_OBSERVABILITY_CLEANUP_PLAN_JSON = Path("outputs/reports/observability_cleanup_plan.json")
DEFAULT_OBSERVABILITY_CLEANUP_PLAN_MARKDOWN = Path("outputs/reports/observability_cleanup_plan.md")

FORBIDDEN_SOURCE_PREFIXES = (
    ".git/",
    "src/",
    "docs/",
    "tests/",
    ".github/",
    ".devpilot/testing/",
    ".devpilot/project_state.json",
    ".devpilot/docs_governance/",
    ".devpilot/observability/retention_policy.json",
)

CLEANUP_ACTION_KINDS = ("rotate", "delete", "archive", "redact", "export")


@dataclass(frozen=True)
class ObservabilityCleanupPlanOptions:
    policy_path: str | Path = DEFAULT_OBSERVABILITY_RETENTION_POLICY
    write_report: bool = False
    output_json: str | Path = DEFAULT_OBSERVABILITY_CLEANUP_PLAN_JSON
    output_markdown: str | Path = DEFAULT_OBSERVABILITY_CLEANUP_PLAN_MARKDOWN
    execute: bool = False


class ObservabilityCleanupPlanner:
    """Build a local dry-run cleanup/rotation/redaction plan for observability.

    POST-H-010-C is deliberately plan-only. It consumes the POST-H-010-B
    metadata inventory and computes would_* actions without deleting, rotating,
    archiving, redacting or exporting files. Potential destructive operations
    include embedded PolicyEngine simulations so operators can see which actions
    would require approval before any future execute-capable workflow.
    """

    def __init__(self, root: Path, options: ObservabilityCleanupPlanOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ObservabilityCleanupPlanOptions()

    def run(self) -> CommandResult:
        try:
            inventory_result = ObservabilityInventoryBuilder(
                self.root,
                ObservabilityInventoryOptions(policy_path=self.options.policy_path, write_report=False),
            ).run()
            if not inventory_result.data or "inventory" not in inventory_result.data:
                return inventory_result
            payload = self.build_plan(inventory_result.data["inventory"])
        except Exception as exc:  # defensive CLI boundary
            finding = Finding(
                id="OBSERVABILITY_CLEANUP_PLAN_ERROR",
                message=f"Observability cleanup plan could not be built: {exc}",
                severity=Severity.ERROR,
            )
            return CommandResult(
                command="observability cleanup-plan",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Observability cleanup plan failed.",
                data={"summary": {"dry_run": True, "preliminary": True, "mutations_performed": False}},
                findings=[finding],
            )

        if self.options.write_report:
            reports = self._planned_report_paths()
            payload["summary"]["reports_written"] = True
            payload["summary"]["output_json"] = reports["json"]
            payload["summary"]["output_markdown"] = reports["markdown"]
            self._write_reports(payload)
        else:
            reports = {}
            payload["summary"]["reports_written"] = False
            payload["summary"]["output_json"] = None
            payload["summary"]["output_markdown"] = None

        findings = _findings_from_cleanup_plan(payload)
        blocking = [item for item in findings if item.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        return CommandResult(
            command="observability cleanup-plan",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Observability cleanup plan passed." if not blocking else "Observability cleanup plan has blocking findings.",
            data={"summary": payload["summary"], "cleanup_plan": payload, "reports": reports},
            findings=findings,
        )

    def build_plan(self, inventory: dict[str, Any]) -> dict[str, Any]:
        target_checks = list(inventory.get("target_checks", []))
        actions: list[dict[str, Any]] = []
        findings: list[dict[str, Any]] = []

        for target in target_checks:
            target_actions, target_findings = self._actions_for_target(target)
            actions.extend(target_actions)
            findings.extend(target_findings)

        blocked_actions = [action for action in actions if action.get("blocked")]
        required_approval_ids = sorted({str(action.get("required_approval_id")) for action in actions if action.get("required_approval_id")})
        action_counts = Counter(str(action.get("action_kind")) for action in actions)
        actions_by_kind = {kind: int(action_counts.get(kind, 0)) for kind in CLEANUP_ACTION_KINDS}
        blocking_findings_total = sum(1 for item in findings if item.get("severity") in {"block", "error", "fail"})
        warnings_total = sum(1 for item in findings if item.get("severity") == "warning")

        summary = {
            "created_by": POST_H_010_C_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "policy_id": inventory.get("policy_id"),
            "policy_path": inventory.get("policy_path"),
            "inventory_id": inventory.get("inventory_id"),
            "dry_run": True,
            "execute_requested": bool(self.options.execute),
            "execute_allowed": False,
            "execution_blocked": bool(self.options.execute),
            "explicit_execute_required_for_mutations": True,
            "read_only_plan": True,
            "actions_total": len(actions),
            "actions_by_kind": actions_by_kind,
            "would_rotate": actions_by_kind["rotate"],
            "would_delete": actions_by_kind["delete"],
            "would_archive": actions_by_kind["archive"],
            "would_redact": actions_by_kind["redact"],
            "would_export": actions_by_kind["export"],
            "blocked_actions_total": len(blocked_actions),
            "required_approval_ids_total": len(required_approval_ids),
            "targets_total": len(target_checks),
            "targets_with_actions_total": len({action["target_id"] for action in actions}),
            "policy_evaluations_total": sum(1 for action in actions if action.get("policy_evaluation") is not None),
            "warnings_total": warnings_total,
            "blocking_findings_total": blocking_findings_total,
            "mutations_performed": False,
            "destructive_cleanup_performed": False,
            "source_mutations_performed": False,
            "cleanup_execution_enabled": False,
            "export_execution_enabled": False,
            "redaction_execution_enabled": False,
            "raw_payloads_read": False,
            "network_used": False,
            "external_api_used": False,
        }

        if self.options.execute:
            findings.append(_finding_dict(
                "OBSERVABILITY_CLEANUP_PLAN_EXECUTE_NOT_SUPPORTED",
                "observability cleanup-plan is a planning command and never mutates files; future execution requires an explicit cleanup command and valid PolicyEngine approval.",
                "block",
                metadata={"execute_requested": True},
            ))
            summary["blocking_findings_total"] = summary["blocking_findings_total"] + 1

        return {
            "schema_version": "1.0",
            "schema_id": OBSERVABILITY_CLEANUP_PLAN_SCHEMA_ID,
            "cleanup_plan_id": OBSERVABILITY_CLEANUP_PLAN_ID,
            "created_by": POST_H_010_C_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": _utc_now_iso(),
            "policy_id": inventory.get("policy_id"),
            "policy_path": inventory.get("policy_path"),
            "inventory_id": inventory.get("inventory_id"),
            "execution_mode": "dry-run",
            "actions": actions,
            "blocked_actions": blocked_actions,
            "required_approval_ids": required_approval_ids,
            "findings": findings,
            "summary": summary,
            "safety": {
                "local_first": True,
                "dry_run_default": True,
                "plan_only": True,
                "execute_requires_approval": True,
                "policy_engine_required_for_mutations": True,
                "forbidden_source_prefixes": list(FORBIDDEN_SOURCE_PREFIXES),
                "mutations_performed": False,
                "destructive_cleanup_performed": False,
                "source_mutations_performed": False,
                "raw_payloads_read": False,
                "network_used": False,
                "external_api_used": False,
                "cleanup_execution_enabled": False,
                "export_execution_enabled": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
            },
            "notes": [
                "POST-H-010-C computes would_rotate/would_delete/would_archive/would_redact/would_export actions without performing them.",
                "PolicyEngine is evaluated with observability disabled to avoid creating runtime artifacts while planning cleanup.",
                "Actions outside the workspace, under .git/src/docs/tests or against source-of-truth targets are blocking findings.",
                "Actual destructive cleanup remains disabled in this micro-sprint; export/redaction execution remains POST-H-010-D scope.",
            ],
        }

    def _actions_for_target(self, target: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        actions: list[dict[str, Any]] = []
        findings: list[dict[str, Any]] = []
        path = str(target.get("path") or "")
        target_id = str(target.get("target_id") or path or "unknown")
        inside = bool(target.get("inside_workspace", False))
        exists = bool(target.get("exists", False))
        forbidden = _matches_forbidden_source_prefix(path)

        if not inside:
            findings.append(_finding_dict(
                "OBSERVABILITY_CLEANUP_PATH_ESCAPE",
                "Cleanup planning target resolves outside workspace and is blocked.",
                "block",
                path=path,
                metadata={"target_id": target_id},
            ))
        if forbidden:
            findings.append(_finding_dict(
                "OBSERVABILITY_CLEANUP_FORBIDDEN_SOURCE_PATH",
                "Cleanup plan must not include .git, src, docs, tests or governed source metadata as runtime cleanup targets.",
                "block",
                path=path,
                metadata={"target_id": target_id},
            ))

        if not exists:
            return actions, findings

        if bool(target.get("source_of_truth")) or bool(target.get("versionable")):
            findings.append(_finding_dict(
                "OBSERVABILITY_CLEANUP_SOURCE_OF_TRUTH_TARGET",
                "Source-of-truth/versionable observability target is never eligible for cleanup actions.",
                "block",
                path=path,
                metadata={"target_id": target_id},
            ))
            return actions, findings

        if bool(target.get("rotation_recommended")) and bool(target.get("cleanup_allowed")):
            actions.append(self._action(target, "rotate", "Target exceeds retention size/age thresholds and rotation is enabled."))

        if bool(target.get("expired")) and bool(target.get("cleanup_allowed")):
            if bool(target.get("contains_sensitive_payloads")):
                actions.append(self._action(target, "archive", "Expired sensitive observability target should be archived before deletion."))
            actions.append(self._action(target, "delete", "Expired observability target is eligible for future delete after approval."))

        if bool(target.get("redaction_required")) and bool(target.get("export_allowed")):
            actions.append(self._action(target, "redact", "Target requires redaction before any local export or audit package use."))

        if bool(target.get("export_allowed")) and bool(target.get("redaction_required")):
            actions.append(self._action(target, "export", "Target can be included only in a future redacted local export."))

        return actions, findings

    def _action(self, target: dict[str, Any], action_kind: str, reason: str) -> dict[str, Any]:
        path = str(target.get("path") or "")
        target_id = str(target.get("target_id") or path)
        approval_id = f"approval:observability-cleanup:{target_id}:{action_kind}"
        policy = self._policy_evaluation(action_kind, path, target_id, approval_id)
        policy_summary = dict((policy.data or {}).get("summary", {}))
        policy_findings = [finding.to_dict() for finding in policy.findings]
        blocked = action_kind in {"rotate", "delete", "archive"} and not bool(policy_summary.get("allowed", False))
        execution_status = "blocked" if blocked else "planned"
        return {
            "action_id": f"observability-{action_kind}-{target_id}",
            "action_kind": action_kind,
            "target_id": target_id,
            "path": path,
            "reason": reason,
            "exists": bool(target.get("exists", False)),
            "size_bytes": int(target.get("size_bytes") or 0),
            "age_days": target.get("age_days"),
            "retention_days": int(target.get("retention_days") or 0),
            "risk_level": str(target.get("risk_level") or "low"),
            "redaction_required": bool(target.get("redaction_required", False)),
            "contains_sensitive_payloads": bool(target.get("contains_sensitive_payloads", False)),
            "clean_zip_excluded": bool(target.get("clean_zip_excluded", False)),
            "requires_execute": action_kind in {"rotate", "delete", "archive"},
            "requires_policy_engine": action_kind in {"rotate", "delete", "archive"},
            "requires_approval": action_kind in {"rotate", "delete", "archive"},
            "required_approval_id": approval_id if action_kind in {"rotate", "delete", "archive"} else None,
            "blocked": blocked,
            "execution_status": execution_status,
            "mutations_performed": False,
            "policy_evaluation": {
                "command": policy.command,
                "ok": bool(policy.ok),
                "exit_code": int(policy.exit_code),
                "summary": policy_summary,
                "findings": policy_findings,
            } if action_kind in {"rotate", "delete", "archive"} else None,
        }

    def _policy_evaluation(self, action_kind: str, path: str, target_id: str, approval_id: str) -> CommandResult:
        action = "delete" if action_kind == "delete" else "overwrite"
        return PolicyEngine(self.root, observability_enabled=False).evaluate(
            PolicyRequest(
                action=action,
                path=path,
                dry_run=True,
                approval_id=None,
                tool_id="observability.cleanup-plan",
                subject=f"observability:{target_id}:{action_kind}",
                metadata={
                    "component": "ObservabilityCleanupPlanner",
                    "target_id": target_id,
                    "action_kind": action_kind,
                    "approval_id_required": approval_id,
                    "plan_only": True,
                },
            )
        )

    def _planned_report_paths(self) -> dict[str, str]:
        return {
            "json": _rel(self.root, self.root / self.options.output_json),
            "markdown": _rel(self.root, self.root / self.options.output_markdown),
        }

    def _write_reports(self, payload: dict[str, Any]) -> None:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(render_observability_cleanup_plan_markdown(payload), encoding="utf-8")


def render_observability_cleanup_plan_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# DevPilot Observability Cleanup Plan",
        "",
        f"- Schema: `{payload.get('schema_id')}`",
        f"- Created by: `{payload.get('created_by')}`",
        f"- Status: `{payload.get('status')}`",
        f"- Generated: `{payload.get('generated_at_utc')}`",
        f"- Execution mode: `{payload.get('execution_mode')}`",
        "",
        "## Summary",
        "",
        f"- Actions total: {summary.get('actions_total', 0)}",
        f"- Would rotate: {summary.get('would_rotate', 0)}",
        f"- Would delete: {summary.get('would_delete', 0)}",
        f"- Would archive: {summary.get('would_archive', 0)}",
        f"- Would redact: {summary.get('would_redact', 0)}",
        f"- Would export: {summary.get('would_export', 0)}",
        f"- Blocked actions: {summary.get('blocked_actions_total', 0)}",
        f"- Mutations performed: {summary.get('mutations_performed')}",
        "",
        "## Planned actions",
        "",
        "| Action | Target | Path | Blocked | Requires approval | Reason |",
        "|---|---|---|---:|---:|---|",
    ]
    for action in payload.get("actions", []):
        lines.append(
            "| {action_kind} | {target_id} | `{path}` | {blocked} | {requires_approval} | {reason} |".format(**action)
        )
    if not payload.get("actions"):
        lines.append("| none | none | none | false | false | No cleanup actions are currently recommended. |")
    lines.extend(["", "## Findings", ""])
    findings = payload.get("findings", [])
    if not findings:
        lines.append("No findings.")
    else:
        for finding in findings:
            path = f" `{finding.get('path')}`" if finding.get("path") else ""
            lines.append(f"- **{finding.get('severity')}** `{finding.get('id')}`{path}: {finding.get('message')}")
    lines.extend([
        "",
        "## Safety",
        "",
        "```json",
        json.dumps(payload.get("safety", {}), indent=2, ensure_ascii=False),
        "```",
        "",
    ])
    return "\n".join(lines)


def _findings_from_cleanup_plan(payload: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for item in payload.get("findings", []):
        findings.append(
            Finding(
                id=str(item.get("id", "OBSERVABILITY_CLEANUP_PLAN_FINDING")),
                message=str(item.get("message", "Observability cleanup plan finding.")),
                severity=_severity_from_string(str(item.get("severity", "info"))),
                path=str(item["path"]) if item.get("path") else None,
                metadata=dict(item.get("metadata", {})),
            )
        )
    if not findings:
        findings.append(
            Finding(
                id="OBSERVABILITY_CLEANUP_PLAN_PASS",
                message="Observability cleanup plan completed without blocking findings.",
                severity=Severity.INFO,
                metadata={"actions_total": payload.get("summary", {}).get("actions_total", 0)},
            )
        )
    return findings


def _finding_dict(id_: str, message: str, severity: str, *, path: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"id": id_, "message": message, "severity": severity}
    if path:
        payload["path"] = path
    if metadata:
        payload["metadata"] = metadata
    return payload


def _severity_from_string(value: str) -> Severity:
    return {
        "info": Severity.INFO,
        "warning": Severity.WARNING,
        "warn": Severity.WARNING,
        "block": Severity.BLOCK,
        "fail": Severity.FAIL,
        "error": Severity.ERROR,
    }.get(value, Severity.INFO)


def _utc_now_iso() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _matches_forbidden_source_prefix(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized == ".git" or any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in FORBIDDEN_SOURCE_PREFIXES)
