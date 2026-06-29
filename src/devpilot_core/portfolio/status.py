from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.workspace.isolation import WorkspaceIsolationValidator
from devpilot_core.workspace.registry_v2 import MultiworkspaceRegistryV2, WorkspaceRegistryV2Options


class PortfolioStatusBuilder:
    """Build a hardened read-only portfolio status for registered local workspaces."""

    def __init__(self, root: Path, *, registry_path: str = ".devpilot/workspaces/workspace_registry.json") -> None:
        self.root = Path(root).resolve()
        self.registry_path = registry_path
        self.registry_v2 = MultiworkspaceRegistryV2(
            self.root,
            options=WorkspaceRegistryV2Options(registry_path=registry_path),
        )
        self.isolation_validator = WorkspaceIsolationValidator(self.root)

    def build(self) -> CommandResult:
        """Build portfolio status from the v2 registry and isolation report without reading state payloads."""

        validation = self.registry_v2.validate()
        if not validation.ok:
            return CommandResult(
                command="portfolio status",
                ok=False,
                exit_code=validation.exit_code,
                message="Portfolio status blocked because Workspace Registry v2 validation failed.",
                data=validation.data,
                findings=validation.findings,
            )

        registry = validation.data["registry"]
        isolation = self.isolation_validator.validate_registry_payload(registry)
        if not isolation.ok:
            summary = {
                "registry_path": validation.data.get("summary", {}).get("registry_path"),
                "workspaces_total": isolation.data.get("summary", {}).get("workspaces_total", 0),
                "workspaces_ready": 0,
                "workspaces_not_ready": isolation.data.get("summary", {}).get("workspaces_total", 0),
                "active_workspace_id": isolation.data.get("summary", {}).get("active_workspace_id"),
                "portfolio_status_read_only": True,
                "registered_workspaces_only": True,
                "unregistered_workspace_policy": "denied",
                "unregistered_workspaces_denied_total": 0,
                "path_isolation_passed": isolation.data.get("summary", {}).get("path_guard_aligned") is True,
                "state_isolation_passed": isolation.data.get("summary", {}).get("state_paths_inside_workspace") is True,
                "outputs_isolation_passed": isolation.data.get("summary", {}).get("outputs_inside_workspace") is True,
                "traces_isolation_passed": isolation.data.get("summary", {}).get("traces_inside_workspace") is True,
                "cross_workspace_refs_detected": isolation.data.get("summary", {}).get("cross_workspace_refs_detected") is True,
                "state_files_read": False,
                "secrets_read": False,
                "network_used": False,
                "external_api_used": False,
                "shell_used": False,
                "remote_execution_used": False,
                "connector_write_used": False,
                "plugin_execution_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "cross_workspace_writes": False,
                "preliminary": True,
            }
            return CommandResult(
                command="portfolio status",
                ok=False,
                exit_code=isolation.exit_code,
                message="Portfolio status blocked because workspace isolation validation failed.",
                data={"summary": summary, "workspaces": [], "isolation": isolation.data},
                findings=isolation.findings,
            )

        workspaces = [entry for entry in registry.get("workspaces", []) if isinstance(entry, dict)]
        isolation_by_id = {
            str(entry.get("workspace_id")): entry
            for entry in isolation.data.get("report", {}).get("workspaces", [])
            if isinstance(entry, dict)
        }
        portfolio_items: list[dict[str, Any]] = []
        findings: list[Finding] = []
        ready_count = 0
        unknown_sources_total = 0
        active_workspace_id = registry.get("active_workspace_id")

        for entry in workspaces:
            workspace_id = str(entry.get("workspace_id"))
            resolved = self._resolve_workspace_root(entry)
            isolation_entry = isolation_by_id.get(workspace_id, {})
            project_file = resolved / str(entry.get("project_file") or ".devpilot/project.yaml")
            docs_dir = resolved / "docs"
            miasi_dir = resolved / ".devpilot" / "miasi"
            state_path = resolved / str(entry.get("state_path") or ".devpilot/devpilot.db")
            reports_dir = resolved / str(entry.get("reports_path") or "outputs/reports")
            traces_dir = resolved / str(entry.get("traces_path") or "outputs/traces")
            readiness_checks = {
                "project_file": _presence(project_file, missing_status="missing"),
                "docs": _presence(docs_dir),
                "miasi": _presence(miasi_dir),
                "state": _presence(state_path),
                "reports": _presence(reports_dir),
                "traces": _presence(traces_dir),
            }
            unknown_sources_total += sum(1 for status in readiness_checks.values() if status == "unknown")
            ready = (
                readiness_checks["project_file"] == "present"
                and readiness_checks["docs"] == "present"
                and readiness_checks["miasi"] == "present"
                and isolation_entry.get("state_path_inside_workspace") is True
                and isolation_entry.get("outputs_inside_workspace") is True
                and isolation_entry.get("traces_inside_workspace") is True
                and isolation_entry.get("cross_workspace_refs_detected") is False
            )
            if ready:
                ready_count += 1
            risk_flags = _risk_flags(entry, readiness_checks, isolation_entry)
            portfolio_items.append(
                {
                    "workspace_id": workspace_id,
                    "project_id": entry.get("project_id"),
                    "name": entry.get("name"),
                    "status": entry.get("status"),
                    "active": workspace_id == active_workspace_id,
                    "is_registered": True,
                    "root_path": entry.get("root_path"),
                    "ready": ready,
                    "readiness": {
                        "status": "ready" if ready else "not_ready",
                        "project_file": readiness_checks["project_file"],
                        "docs": readiness_checks["docs"],
                        "miasi": readiness_checks["miasi"],
                    },
                    "state": {
                        "status": readiness_checks["state"],
                        "path": _rel(self.root, state_path),
                        "read": False,
                    },
                    "reports": {
                        "status": readiness_checks["reports"],
                        "path": _rel(self.root, reports_dir),
                    },
                    "traces": {
                        "status": readiness_checks["traces"],
                        "path": _rel(self.root, traces_dir),
                    },
                    "risks": {
                        "risk_level": entry.get("risk_level") or "unknown",
                        "flags": risk_flags,
                        "findings_total": len(isolation_entry.get("findings", [])) if isinstance(isolation_entry.get("findings"), list) else 0,
                    },
                    "isolation": {
                        "path_guard_root_matches_workspace_root": isolation_entry.get("path_guard_root_matches_workspace_root") is True,
                        "root_path_allowed": isolation_entry.get("root_path_allowed") is True,
                        "state_path_inside_workspace": isolation_entry.get("state_path_inside_workspace") is True,
                        "outputs_inside_workspace": isolation_entry.get("outputs_inside_workspace") is True,
                        "traces_inside_workspace": isolation_entry.get("traces_inside_workspace") is True,
                        "cross_workspace_refs_detected": isolation_entry.get("cross_workspace_refs_detected") is True,
                    },
                    "no_go": {
                        "read_only": True,
                        "source_mutations_performed": False,
                        "cross_workspace_writes": False,
                        "secrets_read": False,
                        "state_files_read": False,
                    },
                    "project_file_present": project_file.is_file(),
                    "docs_present": docs_dir.is_dir(),
                    "miasi_present": miasi_dir.is_dir(),
                    "state_path": _rel(self.root, state_path),
                    "state_file_present": state_path.is_file(),
                    "reports_present": reports_dir.is_dir(),
                    "traces_present": traces_dir.is_dir(),
                    "state_read": False,
                    "secrets_read": False,
                    "network_used": False,
                    "external_api_used": False,
                }
            )
            if not ready:
                findings.append(
                    Finding(
                        "PORTFOLIO_WORKSPACE_NOT_READY",
                        "Registered workspace is not ready or has unknown operational sources.",
                        Severity.WARNING,
                        path=str(entry.get("root_path")),
                        metadata={"workspace_id": workspace_id, "readiness": readiness_checks, "risk_flags": risk_flags},
                    )
                )

        isolation_summary = isolation.data["summary"]
        summary = {
            "registry_path": validation.data.get("summary", {}).get("registry_path"),
            "workspaces_total": len(portfolio_items),
            "workspaces_ready": ready_count,
            "workspaces_not_ready": len(portfolio_items) - ready_count,
            "active_workspace_id": active_workspace_id,
            "portfolio_status_read_only": True,
            "registered_workspaces_only": True,
            "unregistered_workspace_policy": "denied",
            "unregistered_workspaces_denied_total": 0,
            "unknown_sources_total": unknown_sources_total,
            "path_isolation_passed": isolation_summary.get("path_guard_aligned") is True,
            "state_isolation_passed": isolation_summary.get("state_paths_inside_workspace") is True,
            "outputs_isolation_passed": isolation_summary.get("outputs_inside_workspace") is True,
            "traces_isolation_passed": isolation_summary.get("traces_inside_workspace") is True,
            "cross_workspace_refs_detected": isolation_summary.get("cross_workspace_refs_detected") is True,
            "state_files_read": False,
            "secrets_read": False,
            "network_used": False,
            "external_api_used": False,
            "shell_used": False,
            "remote_execution_used": False,
            "connector_write_used": False,
            "plugin_execution_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "cross_workspace_writes": False,
            "preliminary": True,
        }
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        ok = (
            not blocking
            and summary["path_isolation_passed"]
            and summary["state_isolation_passed"]
            and summary["outputs_isolation_passed"]
            and summary["traces_isolation_passed"]
            and not summary["cross_workspace_refs_detected"]
        )
        return CommandResult(
            command="portfolio status",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Portfolio status built in read-only mode." if ok else "Portfolio status detected isolation issues.",
            data={"summary": summary, "workspaces": portfolio_items},
            findings=findings or [Finding("PORTFOLIO_STATUS_PASS", "Portfolio status consolidated registered workspaces without cross-workspace state reads.", Severity.INFO, metadata=summary)],
        )

    def _resolve_workspace_root(self, entry: dict[str, Any]) -> Path:
        root_path = Path(str(entry.get("root_path") or "."))
        return root_path if root_path.is_absolute() else self.root / root_path

    def build_from_registry_payload(self, registry: dict[str, Any]) -> CommandResult:
        """Build status from a prevalidated test/API payload without reading unregistered locations."""

        registry_result = self.registry_v2.validate_payload(registry)
        if not registry_result.ok:
            return CommandResult(
                command="portfolio status",
                ok=False,
                exit_code=registry_result.exit_code,
                message="Portfolio status blocked because supplied Workspace Registry v2 payload failed validation.",
                data=registry_result.data,
                findings=registry_result.findings,
            )
        previous = self.registry_v2
        try:
            class _ValidatedRegistry:
                def validate(self_nonlocal: object) -> CommandResult:
                    return registry_result

            self.registry_v2 = _ValidatedRegistry()  # type: ignore[assignment]
            return self.build()
        finally:
            self.registry_v2 = previous


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _presence(path: Path, *, missing_status: str = "unknown") -> str:
    return "present" if path.exists() else missing_status


def _risk_flags(entry: dict[str, Any], readiness: dict[str, str], isolation: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    if any(status == "unknown" for status in readiness.values()):
        flags.append("unknown_operational_sources")
    if readiness.get("project_file") == "missing":
        flags.append("missing_project_file")
    if entry.get("risk_level") in {"high", "critical"}:
        flags.append(f"risk_level_{entry.get('risk_level')}")
    for field in ("state_path_inside_workspace", "outputs_inside_workspace", "traces_inside_workspace"):
        if isolation.get(field) is False:
            flags.append(field)
    if isolation.get("cross_workspace_refs_detected") is True:
        flags.append("cross_workspace_refs_detected")
    return flags
