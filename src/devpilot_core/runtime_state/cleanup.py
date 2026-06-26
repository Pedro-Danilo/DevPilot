from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.runtime_state.inventory import RuntimeStateInventoryBuilder, RuntimeStateInventoryOptions
from devpilot_core.runtime_state.models import RuntimeStatePolicy, utc_now_iso
from devpilot_core.runtime_state.policy import RuntimeStatePolicyLoader

RUNTIME_STATE_CLEANUP_PLAN_SCHEMA_ID = "SCHEMA-DEVPL-RUNTIME-STATE-CLEANUP-PLAN-V1"
RUNTIME_STATE_CLEANUP_PLAN_ID = "devpilot-runtime-state-cleanup-plan"
POST_H_008_C_CREATED_BY = "POST-H-008-C"

DEFAULT_CLEANUP_PLAN_JSON = Path("outputs/reports/runtime_state_cleanup_plan.json")
DEFAULT_CLEANUP_PLAN_MARKDOWN = Path("outputs/reports/runtime_state_cleanup_plan.md")

FORBIDDEN_SOURCE_PREFIXES = (
    "src/",
    "docs/",
    "tests/",
    ".github/",
    ".devpilot/testing/",
    ".devpilot/project_state.json",
    ".devpilot/runtime_state_policy.json",
)


@dataclass(frozen=True)
class RuntimeStateCleanupOptions:
    policy_path: str | Path = ".devpilot/runtime_state_policy.json"
    write_report: bool = False
    output_json: str | Path = DEFAULT_CLEANUP_PLAN_JSON
    output_markdown: str | Path = DEFAULT_CLEANUP_PLAN_MARKDOWN
    execute: bool = False
    confirm_cleanup: bool = False


class RuntimeStateCleanupPlanner:
    """Build and optionally execute a tightly-scoped runtime cleanup plan.

    POST-H-008-C is dry-run by default. The planner classifies every artifact
    detected by the POST-H-008-B inventory into safe-cleanup, requires-approval,
    never-delete or retained. It never classifies source-of-truth artifacts as
    deletable and refuses execution unless `execute=True` and
    `confirm_cleanup=True` are both supplied.
    """

    def __init__(self, root: Path, options: RuntimeStateCleanupOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RuntimeStateCleanupOptions()

    def run(self) -> CommandResult:
        try:
            policy = RuntimeStatePolicyLoader(self.root, self.options.policy_path).load()
            inventory_result = RuntimeStateInventoryBuilder(
                self.root,
                RuntimeStateInventoryOptions(policy_path=self.options.policy_path, write_report=False),
            ).run()
            if not inventory_result.data or "inventory" not in inventory_result.data:
                return inventory_result
            inventory = inventory_result.data["inventory"]
            payload = self.build_plan(policy, inventory)
        except Exception as exc:
            finding = Finding(
                id="RUNTIME_STATE_CLEANUP_PLAN_ERROR",
                message=f"Runtime-state cleanup plan could not be built: {exc}",
                severity=Severity.ERROR,
            )
            return CommandResult(
                command=self._command_name(),
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Runtime-state cleanup plan failed.",
                data={"summary": {"dry_run": not self.options.execute, "preliminary": True}},
                findings=[finding],
            )

        execution_findings: list[Finding] = []
        if self.options.execute:
            execution_findings = self._execute_safe_cleanup(payload)
        else:
            payload["summary"]["deletions_performed_total"] = 0
            payload["summary"]["deletion_errors_total"] = 0
            payload["summary"]["destructive_cleanup_performed"] = False

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

        findings = _findings_from_cleanup_plan(payload) + execution_findings
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        return CommandResult(
            command=self._command_name(),
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Runtime-state cleanup plan passed." if not blocking else "Runtime-state cleanup plan has blocking findings.",
            data={"summary": payload["summary"], "cleanup_plan": payload, "reports": reports},
            findings=findings,
        )

    def build_plan(self, policy: RuntimeStatePolicy, inventory: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        policy_by_class = policy.class_by_id()
        items = [_plan_item_from_artifact(self.root, artifact, policy_by_class.get(str(artifact.get("class_id")))) for artifact in inventory.get("artifacts", [])]
        groups = {
            "safe_cleanup": [item for item in items if item["decision"] == "safe-cleanup"],
            "requires_approval": [item for item in items if item["decision"] == "requires-approval"],
            "never_delete": [item for item in items if item["decision"] == "never-delete"],
            "retained": [item for item in items if item["decision"] == "retained"],
        }
        safe_bytes = sum(int(item.get("size_bytes", 0)) for item in groups["safe_cleanup"])
        requires_approval_bytes = sum(int(item.get("size_bytes", 0)) for item in groups["requires_approval"])
        never_delete_bytes = sum(int(item.get("size_bytes", 0)) for item in groups["never_delete"])
        retained_bytes = sum(int(item.get("size_bytes", 0)) for item in groups["retained"])
        execute_allowed = self.options.execute and self.options.confirm_cleanup
        blocked_execution = self.options.execute and not self.options.confirm_cleanup
        summary = {
            "created_by": POST_H_008_C_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "dry_run": not execute_allowed,
            "execute_requested": self.options.execute,
            "execute_allowed": execute_allowed,
            "explicit_confirmation_required": self.options.execute,
            "explicit_confirmation_provided": self.options.confirm_cleanup,
            "execution_blocked": blocked_execution,
            "read_only_plan": True,
            "source_of_truth_never_delete": True,
            "safe_cleanup_total": len(groups["safe_cleanup"]),
            "requires_approval_total": len(groups["requires_approval"]),
            "never_delete_total": len(groups["never_delete"]),
            "retained_total": len(groups["retained"]),
            "items_total": len(items),
            "eligible_for_automatic_cleanup_total": len(groups["safe_cleanup"]),
            "requires_human_approval_total": len(groups["requires_approval"]),
            "never_delete_bytes_total": never_delete_bytes,
            "safe_cleanup_bytes_total": safe_bytes,
            "requires_approval_bytes_total": requires_approval_bytes,
            "retained_bytes_total": retained_bytes,
            "deletions_planned_total": len(groups["safe_cleanup"]) if execute_allowed else 0,
            "deletions_performed_total": 0,
            "deletion_errors_total": 0,
            "cleanup_execution_enabled": execute_allowed,
            "export_execution_enabled": False,
            "redaction_execution_enabled": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "destructive_cleanup_performed": False,
            "source_mutations_performed": False,
        }
        return {
            "schema_version": "1.0",
            "schema_id": RUNTIME_STATE_CLEANUP_PLAN_SCHEMA_ID,
            "cleanup_plan_id": RUNTIME_STATE_CLEANUP_PLAN_ID,
            "created_by": POST_H_008_C_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": now,
            "policy_id": policy.policy_id,
            "policy_path": _rel(self.root, self.root / self.options.policy_path),
            "inventory_id": inventory.get("inventory_id"),
            "execution_mode": "execute" if self.options.execute else "dry-run",
            "groups": groups,
            "summary": summary,
            "safety": {
                "dry_run_default": True,
                "execute_requires_confirmation": True,
                "only_safe_cleanup_execute_allowed": True,
                "source_of_truth_never_delete": True,
                "forbidden_source_prefixes": list(FORBIDDEN_SOURCE_PREFIXES),
                "mutations_performed": False,
                "network_used": False,
                "external_api_used": False,
                "destructive_cleanup_performed": False,
                "source_mutations_performed": False,
                "cleanup_execution_enabled": execute_allowed,
                "export_execution_enabled": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
            },
            "notes": [
                "POST-H-008-C produces a cleanup plan in dry-run mode by default.",
                "Source-of-truth artifacts, docs, src, tests and policy files are always classified as never-delete.",
                "Sensitive cleanup-allowed artifacts require human approval and are not removed by automatic safe cleanup.",
                "Actual export/redaction workflows remain out of scope until POST-H-008-D.",
            ],
        }

    def _execute_safe_cleanup(self, payload: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        summary = payload["summary"]
        if not self.options.confirm_cleanup:
            findings.append(
                Finding(
                    id="RUNTIME_STATE_CLEANUP_CONFIRMATION_REQUIRED",
                    message="--execute requires --confirm-cleanup; no files were deleted.",
                    severity=Severity.BLOCK,
                    metadata={"execute_requested": True, "confirm_cleanup": False},
                )
            )
            summary["cleanup_execution_enabled"] = False
            summary["dry_run"] = True
            return findings

        deleted = 0
        errors = 0
        for item in payload.get("groups", {}).get("safe_cleanup", []):
            rel_path = str(item.get("path", ""))
            if _is_forbidden_source_path(rel_path):
                errors += 1
                findings.append(
                    Finding(
                        id="RUNTIME_STATE_CLEANUP_FORBIDDEN_SOURCE_PATH",
                        message=f"Refused to delete source-controlled or protected path: {rel_path}",
                        severity=Severity.BLOCK,
                        path=rel_path,
                    )
                )
                continue
            target = (self.root / rel_path).resolve()
            if not _is_relative_to(target, self.root):
                errors += 1
                findings.append(
                    Finding(
                        id="RUNTIME_STATE_CLEANUP_PATH_ESCAPE",
                        message=f"Refused to delete path outside workspace root: {rel_path}",
                        severity=Severity.BLOCK,
                        path=rel_path,
                    )
                )
                continue
            try:
                if target.exists() and target.is_file():
                    target.unlink()
                    item["execution_status"] = "deleted"
                    deleted += 1
                else:
                    item["execution_status"] = "missing"
            except OSError as exc:
                errors += 1
                item["execution_status"] = "error"
                findings.append(
                    Finding(
                        id="RUNTIME_STATE_CLEANUP_DELETE_ERROR",
                        message=f"Could not delete {rel_path}: {exc}",
                        severity=Severity.ERROR,
                        path=rel_path,
                    )
                )
        summary["deletions_performed_total"] = deleted
        summary["deletion_errors_total"] = errors
        summary["mutations_performed"] = deleted > 0
        summary["destructive_cleanup_performed"] = deleted > 0
        payload["safety"]["mutations_performed"] = deleted > 0
        payload["safety"]["destructive_cleanup_performed"] = deleted > 0
        return findings

    def _planned_report_paths(self) -> dict[str, str]:
        return {
            "json": _rel(self.root, self.root / self.options.output_json),
            "markdown": _rel(self.root, self.root / self.options.output_markdown),
        }

    def _write_reports(self, payload: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        md_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(render_runtime_state_cleanup_plan_markdown(payload), encoding="utf-8")
        return self._planned_report_paths()

    def _command_name(self) -> str:
        return "runtime-state cleanup" if self.options.execute else "runtime-state cleanup-plan"


def render_runtime_state_cleanup_plan_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    groups = payload.get("groups", {})
    lines = [
        "# Runtime state cleanup plan",
        "",
        f"Cleanup plan ID: `{payload.get('cleanup_plan_id', '')}`",
        f"Generated at UTC: `{payload.get('generated_at_utc', '')}`",
        f"Created by: `{payload.get('created_by', '')}`",
        f"Status: `{payload.get('status', '')}`",
        f"Execution mode: `{payload.get('execution_mode', '')}`",
        "",
        "## Summary",
        "",
        f"- Safe cleanup total: `{summary.get('safe_cleanup_total', 0)}`",
        f"- Requires approval total: `{summary.get('requires_approval_total', 0)}`",
        f"- Never delete total: `{summary.get('never_delete_total', 0)}`",
        f"- Retained total: `{summary.get('retained_total', 0)}`",
        f"- Dry-run: `{summary.get('dry_run', True)}`",
        f"- Execute requested: `{summary.get('execute_requested', False)}`",
        f"- Explicit confirmation provided: `{summary.get('explicit_confirmation_provided', False)}`",
        f"- Deletions performed total: `{summary.get('deletions_performed_total', 0)}`",
        "",
    ]
    for group_key, title in [
        ("safe_cleanup", "Safe cleanup"),
        ("requires_approval", "Requires approval"),
        ("never_delete", "Never delete"),
        ("retained", "Retained"),
    ]:
        items = groups.get(group_key, [])
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("No items in this group.")
            lines.append("")
            continue
        lines.extend(["| Path | Class | Size | Age days | Retention days | Reason |", "|---|---|---:|---:|---:|---|"])
        for item in sorted(items, key=lambda row: str(row.get("path", "")))[:200]:
            lines.append(
                f"| `{item.get('path', '')}` | `{item.get('class_id', '')}` | {item.get('size_bytes', 0)} | "
                f"{item.get('age_days', 0)} | {item.get('retention_days', 0)} | {item.get('reason', '')} |"
            )
        if len(items) > 200:
            lines.append(f"| ... | ... | ... | ... | ... | {len(items) - 200} additional items omitted from Markdown view; JSON contains the full plan. |")
        lines.append("")
    lines.extend(
        [
            "## Safety",
            "",
            "Dry-run is the default. Automatic execution only applies to `safe-cleanup` items and requires explicit confirmation. Source-of-truth paths, docs, src, tests, runtime policy and test contracts are never deleted by this planner.",
            "",
        ]
    )
    return "\n".join(lines)


def _plan_item_from_artifact(root: Path, artifact: dict[str, Any], artifact_class: Any | None) -> dict[str, Any]:
    path = str(artifact.get("path", ""))
    rel_path = path.replace("\\", "/")
    retention_days = int(getattr(artifact_class, "retention_days", int(artifact.get("retention_days", 0) or 0))) if artifact_class else 0
    target = root / rel_path
    age_days = _file_age_days(target)
    source_of_truth = bool(artifact.get("source_of_truth", False))
    never_delete = bool(artifact.get("never_delete", False))
    cleanup_allowed = bool(artifact.get("cleanup_allowed", False))
    sensitive = bool(artifact.get("sensitive", False))
    versionable = bool(artifact.get("versionable", False))
    git_tracked = bool(artifact.get("git_tracked", False))

    decision = "retained"
    reason = "Artifact is within retention window."
    execute_allowed = False
    if _is_forbidden_source_path(rel_path) or source_of_truth or never_delete or versionable or not cleanup_allowed:
        decision = "never-delete"
        reason = "Protected source-of-truth/versionable/non-cleanup artifact."
    elif retention_days > 0 and age_days < retention_days:
        decision = "retained"
        reason = f"Artifact age {age_days}d is below retention {retention_days}d."
    elif sensitive:
        decision = "requires-approval"
        reason = "Sensitive runtime artifact requires human approval and/or redaction workflow."
    else:
        decision = "safe-cleanup"
        reason = "Non-sensitive runtime artifact exceeds retention and is eligible for automatic safe cleanup."
        execute_allowed = True

    return {
        "path": rel_path,
        "class_id": str(artifact.get("class_id", "")),
        "classification": str(artifact.get("classification", "")),
        "decision": decision,
        "reason": reason,
        "size_bytes": int(artifact.get("size_bytes", 0) or 0),
        "age_days": age_days,
        "retention_days": retention_days,
        "source_of_truth": source_of_truth,
        "versionable": versionable,
        "sensitive": sensitive,
        "cleanup_allowed": cleanup_allowed,
        "never_delete": never_delete,
        "git_tracked": git_tracked,
        "execute_allowed": execute_allowed,
        "execution_status": "planned" if execute_allowed else "not-applicable",
    }


def _file_age_days(path: Path) -> int:
    try:
        stat = path.stat()
    except OSError:
        return 0
    from time import time

    return max(0, int((time() - stat.st_mtime) // 86400))


def _findings_from_cleanup_plan(payload: dict[str, Any]) -> list[Finding]:
    summary = payload.get("summary", {})
    findings: list[Finding] = []
    if summary.get("execution_blocked"):
        findings.append(
            Finding(
                id="RUNTIME_STATE_CLEANUP_CONFIRMATION_REQUIRED",
                message="Cleanup execute mode requires --confirm-cleanup; plan remained dry-run and no files were deleted.",
                severity=Severity.BLOCK,
            )
        )
    # Defensive invariant: source-of-truth artifacts must never appear in safe cleanup.
    unsafe = [
        item
        for item in payload.get("groups", {}).get("safe_cleanup", [])
        if item.get("source_of_truth") or _is_forbidden_source_path(str(item.get("path", "")))
    ]
    for item in unsafe:
        findings.append(
            Finding(
                id="RUNTIME_STATE_CLEANUP_UNSAFE_SAFE_GROUP",
                message=f"Protected artifact was incorrectly classified as safe-cleanup: {item.get('path')}",
                severity=Severity.BLOCK,
                path=str(item.get("path")),
            )
        )
    if not findings:
        findings.append(
            Finding(
                id="RUNTIME_STATE_CLEANUP_PLAN_PASS",
                message="Runtime-state cleanup plan passed dry-run safety invariants.",
                severity=Severity.INFO,
                metadata={
                    "safe_cleanup_total": summary.get("safe_cleanup_total", 0),
                    "requires_approval_total": summary.get("requires_approval_total", 0),
                    "never_delete_total": summary.get("never_delete_total", 0),
                },
            )
        )
    return findings


def _is_forbidden_source_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in FORBIDDEN_SOURCE_PREFIXES)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


__all__ = [
    "DEFAULT_CLEANUP_PLAN_JSON",
    "DEFAULT_CLEANUP_PLAN_MARKDOWN",
    "POST_H_008_C_CREATED_BY",
    "RUNTIME_STATE_CLEANUP_PLAN_ID",
    "RUNTIME_STATE_CLEANUP_PLAN_SCHEMA_ID",
    "RuntimeStateCleanupOptions",
    "RuntimeStateCleanupPlanner",
    "render_runtime_state_cleanup_plan_markdown",
]
