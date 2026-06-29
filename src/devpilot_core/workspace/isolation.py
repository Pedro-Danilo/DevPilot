from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect
from devpilot_core.schemas import SchemaValidator
from devpilot_core.workspace.registry_v2 import MultiworkspaceRegistryV2, WorkspaceRegistryV2Options

WORKSPACE_ISOLATION_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-WORKSPACE-ISOLATION-REPORT-V1"
DEFAULT_WORKSPACE_ISOLATION_REPORT_JSON = Path("outputs/reports/workspace_isolation_report.json")
DEFAULT_WORKSPACE_ISOLATION_REPORT_MD = Path("outputs/reports/workspace_isolation_report.md")


@dataclass(frozen=True)
class WorkspaceIsolationOptions:
    """Options for POST-H-016-B local workspace isolation validation."""

    registry_path: str = ".devpilot/workspaces/workspace_registry.json"
    registry_v2_schema_path: str = "docs/schemas/multiworkspace_registry_v2.schema.json"
    report_schema_path: str = "docs/schemas/workspace_isolation_report.schema.json"
    output_json: str | Path = DEFAULT_WORKSPACE_ISOLATION_REPORT_JSON
    output_markdown: str | Path = DEFAULT_WORKSPACE_ISOLATION_REPORT_MD
    write_report: bool = False


class WorkspaceIsolationValidator:
    """Validate workspace root/state/outputs/traces boundaries without reading secrets or state DBs."""

    def __init__(self, root: Path, *, options: WorkspaceIsolationOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or WorkspaceIsolationOptions()
        self.path_guard = PathGuard(self.root)

    def run(self) -> CommandResult:
        registry_result = MultiworkspaceRegistryV2(
            self.root,
            options=WorkspaceRegistryV2Options(
                registry_path=self.options.registry_path,
                schema_path=self.options.registry_v2_schema_path,
            ),
        ).validate()
        if not registry_result.ok:
            return CommandResult(
                command="workspace isolation-check",
                ok=False,
                exit_code=registry_result.exit_code,
                message="Workspace isolation check blocked because registry v2 validation failed.",
                data=registry_result.data,
                findings=registry_result.findings,
            )

        registry = registry_result.data["registry"]
        return self.validate_registry_payload(registry)

    def validate_registry_payload(self, registry: dict[str, Any]) -> CommandResult:
        """Validate an already-built v2 registry payload; used by tests and future API boundaries."""

        workspaces = [entry for entry in registry.get("workspaces", []) if isinstance(entry, dict)]
        active_workspace_id = registry.get("active_workspace_id")
        workspace_roots = {
            str(entry.get("workspace_id")): self._resolve_from_repo(str(entry.get("root_path") or "."))
            for entry in workspaces
        }

        reports: list[dict[str, Any]] = []
        findings: list[Finding] = []
        state_paths: list[str] = []
        outputs_paths: list[str] = []
        traces_paths: list[str] = []

        for entry in workspaces:
            report, entry_findings = self._workspace_report(entry, active_workspace_id=active_workspace_id, workspace_roots=workspace_roots)
            reports.append(report)
            findings.extend(entry_findings)
            state_paths.append(str((workspace_roots[str(entry.get("workspace_id"))] / str(entry.get("state_path") or ".devpilot/devpilot.db")).resolve()))
            outputs_paths.append(str((workspace_roots[str(entry.get("workspace_id"))] / str(entry.get("reports_path") or "outputs/reports")).resolve()))
            traces_paths.append(str((workspace_roots[str(entry.get("workspace_id"))] / str(entry.get("traces_path") or "outputs/traces")).resolve()))

        duplicate_state_paths = sorted(_duplicates(state_paths))
        duplicate_outputs_paths = sorted(_duplicates(outputs_paths))
        duplicate_traces_paths = sorted(_duplicates(traces_paths))
        for duplicate in duplicate_state_paths:
            findings.append(Finding("WORKSPACE_ISOLATION_STATE_PATH_COLLISION", "Two or more workspaces resolve to the same state path.", Severity.BLOCK, path=_rel(self.root, Path(duplicate))))
        for duplicate in duplicate_outputs_paths:
            findings.append(Finding("WORKSPACE_ISOLATION_OUTPUTS_PATH_COLLISION", "Two or more workspaces resolve to the same reports path.", Severity.BLOCK, path=_rel(self.root, Path(duplicate))))
        for duplicate in duplicate_traces_paths:
            findings.append(Finding("WORKSPACE_ISOLATION_TRACES_PATH_COLLISION", "Two or more workspaces resolve to the same traces path.", Severity.BLOCK, path=_rel(self.root, Path(duplicate))))

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        summary = {
            "schema_version": "1.0",
            "schema_id": WORKSPACE_ISOLATION_REPORT_SCHEMA_ID,
            "workspaces_total": len(reports),
            "active_workspace_id": active_workspace_id,
            "registered_workspaces_only": True,
            "path_guard_aligned": all(item["path_guard_root_matches_workspace_root"] for item in reports),
            "state_paths_inside_workspace": all(item["state_path_inside_workspace"] for item in reports),
            "outputs_inside_workspace": all(item["outputs_inside_workspace"] for item in reports),
            "traces_inside_workspace": all(item["traces_inside_workspace"] for item in reports),
            "secrets_shared_detected": any(item["secrets_shared_detected"] for item in reports),
            "cross_workspace_refs_detected": any(item["cross_workspace_refs_detected"] for item in reports) or bool(duplicate_state_paths or duplicate_outputs_paths or duplicate_traces_paths),
            "blocking_findings_total": len(blocking),
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "shell_used": False,
            "remote_execution_used": False,
            "connector_write_used": False,
            "plugin_execution_used": False,
            "secrets_read": False,
            "state_files_read": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }
        report = {
            "schema_version": "1.0",
            "schema_id": WORKSPACE_ISOLATION_REPORT_SCHEMA_ID,
            "report_id": "workspace-isolation-report",
            "created_by": "POST-H-016-B",
            "status": "implemented-initial",
            "generated_at_utc": _utc_now(),
            "registry_path": self.options.registry_path,
            "summary": summary,
            "workspaces": reports,
            "findings": [finding.to_dict() for finding in findings],
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "secrets_read": False,
                "state_files_read": False,
                "source_mutations_performed": False,
            },
        }
        schema_result = SchemaValidator(self.root).validate_payload(
            schema=self.options.report_schema_path,
            payload=report,
            instance_label="workspace_isolation_report:generated-payload",
        )
        if not schema_result.ok:
            findings.extend(schema_result.findings)
            blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
            summary["blocking_findings_total"] = len(blocking)

        report_paths: dict[str, str] = {}
        if self.options.write_report:
            summary["reports_written"] = True
            report["summary"]["reports_written"] = True
            report_paths = self._write_report(report)

        ok = not blocking
        data = {"summary": summary, "report": report, "report_paths": report_paths}
        return CommandResult(
            command="workspace isolation-check",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Workspace isolation check passed." if ok else "Workspace isolation check detected blocking issues.",
            data=data,
            findings=findings
            or [
                Finding(
                    "WORKSPACE_ISOLATION_PASS",
                    "Registered workspaces keep root, state, outputs and traces inside their own workspace boundaries.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _workspace_report(
        self,
        entry: dict[str, Any],
        *,
        active_workspace_id: str | None,
        workspace_roots: dict[str, Path],
    ) -> tuple[dict[str, Any], list[Finding]]:
        findings: list[Finding] = []
        workspace_id = str(entry.get("workspace_id") or "")
        root_path = workspace_roots[workspace_id]
        workspace_guard = PathGuard(root_path)
        root_decision = self.path_guard.evaluate(root_path, action="read")
        root_allowed = root_decision.effect not in {PolicyEffect.BLOCK, PolicyEffect.DENY}
        if not root_allowed:
            findings.append(Finding("WORKSPACE_ISOLATION_ROOT_BLOCKED", root_decision.reason, Severity.BLOCK, path=root_decision.subject, metadata={"workspace_id": workspace_id, **root_decision.metadata}))

        project_file = root_path / str(entry.get("project_file") or ".devpilot/project.yaml")
        state_path = root_path / str(entry.get("state_path") or ".devpilot/devpilot.db")
        reports_path = root_path / str(entry.get("reports_path") or "outputs/reports")
        traces_path = root_path / str(entry.get("traces_path") or "outputs/traces")
        secrets_path = root_path / str(entry.get("secrets_path") or ".devpilot/providers.yaml")

        state_inside = _is_relative_to(state_path.resolve(), root_path)
        outputs_inside = _is_relative_to(reports_path.resolve(), root_path)
        traces_inside = _is_relative_to(traces_path.resolve(), root_path)
        secrets_inside = _is_relative_to(secrets_path.resolve(), root_path)
        cross_refs = []
        for label, path in [("state_path", state_path), ("reports_path", reports_path), ("traces_path", traces_path)]:
            owner = _other_workspace_owner(path.resolve(), workspace_id, workspace_roots)
            if owner:
                cross_refs.append({"path_type": label, "owner_workspace_id": owner, "path": _rel(self.root, path)})

        if not state_inside:
            findings.append(Finding("WORKSPACE_ISOLATION_STATE_PATH_OUTSIDE_ROOT", "state_path must resolve inside the workspace root.", Severity.BLOCK, path=_rel(self.root, state_path), metadata={"workspace_id": workspace_id}))
        if not outputs_inside:
            findings.append(Finding("WORKSPACE_ISOLATION_OUTPUTS_OUTSIDE_ROOT", "reports_path must resolve inside the workspace root.", Severity.BLOCK, path=_rel(self.root, reports_path), metadata={"workspace_id": workspace_id}))
        if not traces_inside:
            findings.append(Finding("WORKSPACE_ISOLATION_TRACES_OUTSIDE_ROOT", "traces_path must resolve inside the workspace root.", Severity.BLOCK, path=_rel(self.root, traces_path), metadata={"workspace_id": workspace_id}))
        if not secrets_inside:
            findings.append(Finding("WORKSPACE_ISOLATION_SECRETS_PATH_OUTSIDE_ROOT", "secrets_path reference must resolve inside the workspace root.", Severity.BLOCK, path=_rel(self.root, secrets_path), metadata={"workspace_id": workspace_id}))
        if cross_refs:
            findings.append(Finding("WORKSPACE_ISOLATION_CROSS_WORKSPACE_REFERENCE", "Workspace metadata points at another registered workspace boundary.", Severity.BLOCK, metadata={"workspace_id": workspace_id, "references": cross_refs}))

        path_guard_root_matches = workspace_guard.root == root_path.resolve()
        return (
            {
                "workspace_id": workspace_id,
                "root_path": _rel(self.root, root_path),
                "is_registered": True,
                "is_active": workspace_id == active_workspace_id,
                "project_file": _rel(self.root, project_file),
                "project_file_exists": project_file.is_file(),
                "path_guard_root": _rel(self.root, workspace_guard.root),
                "path_guard_root_matches_workspace_root": path_guard_root_matches,
                "root_path_allowed": root_allowed,
                "state_path": _rel(self.root, state_path),
                "state_path_inside_workspace": state_inside,
                "outputs_path": _rel(self.root, reports_path),
                "outputs_inside_workspace": outputs_inside,
                "traces_path": _rel(self.root, traces_path),
                "traces_inside_workspace": traces_inside,
                "secrets_path": _rel(self.root, secrets_path),
                "secrets_path_inside_workspace": secrets_inside,
                "secrets_shared_detected": False,
                "cross_workspace_refs_detected": bool(cross_refs),
                "cross_workspace_refs": cross_refs,
                "state_file_read": False,
                "secrets_read": False,
                "findings": [finding.to_dict() for finding in findings],
            },
            findings,
        )

    def _write_report(self, report: dict[str, Any]) -> dict[str, str]:
        output_json = self._resolve_from_repo(self.options.output_json)
        output_markdown = self._resolve_from_repo(self.options.output_markdown)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        output_markdown.write_text(_render_markdown(report), encoding="utf-8")
        return {"json": _rel(self.root, output_json), "markdown": _rel(self.root, output_markdown)}

    def _resolve_from_repo(self, path: str | Path) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else self.root / candidate


def _other_workspace_owner(path: Path, workspace_id: str, roots: dict[str, Path]) -> str | None:
    for other_id, other_root in roots.items():
        if other_id == workspace_id:
            continue
        if _is_relative_to(path, other_root):
            return other_id
    return None


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Workspace Isolation Report",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Workspaces: `{summary.get('workspaces_total')}`",
        f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
        f"- Cross-workspace refs detected: `{summary.get('cross_workspace_refs_detected')}`",
        f"- Secrets read: `{summary.get('secrets_read')}`",
        f"- State files read: `{summary.get('state_files_read')}`",
        "",
        "## Workspaces",
        "",
    ]
    for workspace in report.get("workspaces", []):
        lines.extend(
            [
                f"### {workspace.get('workspace_id')}",
                "",
                f"- root_path: `{workspace.get('root_path')}`",
                f"- state_path_inside_workspace: `{workspace.get('state_path_inside_workspace')}`",
                f"- outputs_inside_workspace: `{workspace.get('outputs_inside_workspace')}`",
                f"- traces_inside_workspace: `{workspace.get('traces_inside_workspace')}`",
                f"- secrets_read: `{workspace.get('secrets_read')}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
