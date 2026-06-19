from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.workspace.registry import MultiworkspaceRegistry, WorkspaceRegistryOptions


class PortfolioStatusBuilder:
    """Build read-only local portfolio status for registered workspaces.

    Sprint 94 deliberately keeps this report read-only: it reads only registered
    workspace metadata and minimal project markers, never secrets and never a
    workspace database. This prevents cross-workspace state mixing while giving
    operators a portfolio-level readiness view.
    """

    def __init__(self, root: Path, *, registry_path: str = ".devpilot/workspaces/workspace_registry.json") -> None:
        self.root = Path(root).resolve()
        self.registry = MultiworkspaceRegistry(self.root, options=WorkspaceRegistryOptions(registry_path=registry_path))

    def build(self) -> CommandResult:
        validation = self.registry.validate()
        if not validation.ok:
            return CommandResult(
                command="portfolio status",
                ok=False,
                exit_code=validation.exit_code,
                message="Portfolio status blocked because Multiworkspace Registry validation failed.",
                data=validation.data,
                findings=validation.findings,
            )

        workspaces = validation.data.get("workspaces", []) if validation.data else []
        portfolio_items: list[dict[str, Any]] = []
        findings: list[Finding] = []
        ready_count = 0
        active_workspace_id = validation.data.get("summary", {}).get("active_workspace_id")
        state_paths: list[str] = []

        for entry in workspaces:
            if not isinstance(entry, dict):
                continue
            resolved = self.registry.resolve_registered_workspace(entry)
            workspace_id = str(entry.get("workspace_id"))
            if resolved is None:
                portfolio_items.append({"workspace_id": workspace_id, "ready": False, "path_allowed": False})
                continue
            project_file = resolved / ".devpilot" / "project.yaml"
            docs_dir = resolved / "docs"
            miasi_dir = resolved / ".devpilot" / "miasi"
            state_path = resolved / ".devpilot" / "devpilot.db"
            reports_dir = resolved / "outputs" / "reports"
            traces_dir = resolved / "outputs" / "traces"
            state_paths.append(str(state_path.resolve()))
            ready = project_file.is_file() and docs_dir.is_dir() and miasi_dir.is_dir()
            if ready:
                ready_count += 1
            portfolio_items.append(
                {
                    "workspace_id": workspace_id,
                    "name": entry.get("name"),
                    "status": entry.get("status"),
                    "active": workspace_id == active_workspace_id,
                    "path": entry.get("path"),
                    "ready": ready,
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
                findings.append(Finding("PORTFOLIO_WORKSPACE_NOT_READY", "Registered workspace is not ready.", Severity.WARNING, path=str(entry.get("path")), metadata={"workspace_id": workspace_id}))

        state_isolation_passed = len(state_paths) == len(set(state_paths))
        if not state_isolation_passed:
            findings.append(Finding("PORTFOLIO_STATE_PATH_COLLISION", "Portfolio status detected duplicate state paths across workspaces.", Severity.BLOCK))
        summary = {
            "registry_path": validation.data.get("summary", {}).get("registry_path"),
            "workspaces_total": len(portfolio_items),
            "workspaces_ready": ready_count,
            "workspaces_not_ready": len(portfolio_items) - ready_count,
            "active_workspace_id": active_workspace_id,
            "portfolio_status_read_only": True,
            "path_isolation_passed": validation.data.get("summary", {}).get("path_isolation_passed") is True,
            "state_isolation_passed": state_isolation_passed and validation.data.get("summary", {}).get("state_isolation_passed") is True,
            "state_files_read": False,
            "secrets_read": False,
            "network_used": False,
            "external_api_used": False,
            "shell_used": False,
            "remote_execution_used": False,
            "mutations_performed": False,
            "preliminary": True,
        }
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        ok = not blocking and summary["path_isolation_passed"] and summary["state_isolation_passed"]
        return CommandResult(
            command="portfolio status",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Portfolio status built in read-only mode." if ok else "Portfolio status detected isolation issues.",
            data={"summary": summary, "workspaces": portfolio_items},
            findings=findings or [Finding("PORTFOLIO_STATUS_PASS", "Portfolio status consolidated registered workspaces without cross-workspace state reads.", Severity.INFO, metadata=summary)],
        )


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
