from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.guided_sdlc.models import WorkspaceEngineeringState
from devpilot_core.guided_sdlc.repository import WorkspaceEngineeringStateRepository
from devpilot_core.policy import PathGuard, PolicyEffect
from devpilot_core.workspace.manager import parse_project_yaml_metadata

RUNTIME_REGISTRY_REL = Path("outputs/runtime/active_workspace_registry.json")
GUIDED_REGISTRY_ENV = "DEVPILOT_GUIDED_SDLC_WORKSPACE_REGISTRY_PATH"
UI_ACTIVE_ROOT_ENV = "DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT"
ALLOWED_ROOTS_ENV = "DEVPILOT_ALLOWED_WORKSPACE_ROOTS"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _git_fact(root: Path, *args: str) -> str | None:
    cp = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False, text=True, encoding="utf-8", errors="replace")
    if cp.returncode != 0:
        return None
    return cp.stdout.strip() or None


def _workspace_registry_payload(
    workspace_root: Path,
    *,
    workspace_id: str,
    project_id: str,
    name: str,
    now: str,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = existing if isinstance(existing, dict) else {}
    existing_rows = [item for item in existing.get("workspaces", []) if isinstance(item, dict)]
    preserved = [item for item in existing_rows if str(item.get("workspace_id") or "").strip() != workspace_id]
    active_row = {
            "workspace_id": workspace_id,
            "project_id": project_id,
            "name": name,
            "path": str(workspace_root),
            "path_mode": "absolute-local",
            "status": "active",
            "risk_level": "medium_high",
            "default_effect": "deny",
            "state_path": ".devpilot/devpilot.db",
            "reports_path": "outputs/reports",
            "traces_path": "outputs/traces",
            "secrets_path": ".devpilot/providers.yaml",
            "secret_policy": "reference-only",
            "network_allowed": False,
            "external_api_allowed": False,
            "observability_required": True,
            "eval_required": True,
            "registered_at": now,
            "updated_at": now,
        }
    return {
        "schema_version": "1.0",
        "created_by": str(existing.get("created_by") or "DEVPL-GSDLC-13-B-03"),
        "updated_at": now,
        "active_workspace_id": workspace_id,
        "defaults": {
            "deny_unregistered_workspaces": True,
            "cross_workspace_state_reads": False,
            "secret_sharing_allowed": False,
            "portfolio_status_read_only": True,
        },
        "security": {
            "network_used": False,
            "external_api_used": False,
            "shell_used": False,
            "remote_execution_used": False,
            "mutations_performed": False,
            "secrets_read": False,
        },
        "workspaces": [*preserved, active_row],
    }


def activate_project_runtime_context(
    platform_root: Path,
    workspace_root: Path,
    *,
    allowed_roots: tuple[Path, ...] = (),
    initialize_engineering_state: bool = True,
) -> dict[str, Any]:
    """Persist server-active project context outside managed project source.

    The workspace must already be a PathGuard-approved DevPilot project. Writes
    are limited to platform ``outputs/`` runtime/state stores. Existing
    engineering state is never overwritten.
    """
    platform = Path(platform_root).resolve()
    workspace = Path(workspace_root).resolve()
    guard = PathGuard(platform, allowed_external_roots=tuple(Path(p).resolve() for p in allowed_roots))
    decision = guard.evaluate(workspace, action="read")
    if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
        raise RuntimeError(f"runtime project context root blocked: {decision.reason}")
    project_file = workspace / ".devpilot" / "project.yaml"
    registration_file = workspace / ".devpilot" / "workspace-registration.json"
    if not project_file.is_file() or not registration_file.is_file():
        raise RuntimeError("runtime project context requires project.yaml and workspace-registration.json")
    metadata = parse_project_yaml_metadata(project_file)
    project_id = str(metadata.get("project_id") or "").strip()
    if not project_id:
        raise RuntimeError("project.yaml has no project_id")
    registration = json.loads(registration_file.read_text(encoding="utf-8-sig"))
    workspace_id = str(registration.get("workspace_id") or "").strip()
    registered_project_id = str(registration.get("project_id") or "").strip()
    registered_root = Path(str(registration.get("root_path") or "")).resolve()
    if workspace_id != project_id or registered_project_id != project_id or registered_root != workspace:
        raise RuntimeError("target-local workspace registration does not match project authority")
    now = _utcnow()
    registry_path = platform / RUNTIME_REGISTRY_REL
    state_path = platform / "outputs" / "workspaces" / workspace_id / "engineering_state.json"
    registry_before = registry_path.read_bytes() if registry_path.is_file() else None
    state_before = state_path.read_bytes() if state_path.is_file() else None
    state_created = False
    try:
        existing_registry = None
        if registry_before is not None:
            try:
                decoded = json.loads(registry_before.decode("utf-8-sig"))
                existing_registry = decoded if isinstance(decoded, dict) else None
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise RuntimeError("existing runtime registry is corrupt/unreadable")
        registry_payload = _workspace_registry_payload(
            workspace,
            workspace_id=workspace_id,
            project_id=project_id,
            name=str(metadata.get("project_name") or project_id),
            now=now,
            existing=existing_registry,
        )
        _atomic_json(registry_path, registry_payload)

        if initialize_engineering_state and not state_path.exists():
            # Repository binding needs the same explicit external-root authority.
            old_allowed = os.environ.get(ALLOWED_ROOTS_ENV)
            old_registry = os.environ.get(GUIDED_REGISTRY_ENV)
            os.environ[ALLOWED_ROOTS_ENV] = str(workspace)
            os.environ[GUIDED_REGISTRY_ENV] = str(registry_path)
            try:
                fingerprint = hashlib.sha256(os.path.normcase(str(workspace)).encode("utf-8")).hexdigest()
                state = WorkspaceEngineeringState.new(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    workspace_root_fingerprint=fingerprint,
                    created_at_utc=now,
                    current_step="idea-intake",
                )
                head = _git_fact(workspace, "rev-parse", "HEAD")
                branch = _git_fact(workspace, "branch", "--show-current")
                dirty_text = _git_fact(workspace, "status", "--porcelain", "--untracked-files=all")
                git_payload = {
                    "head": head,
                    "branch": branch,
                    "dirty": bool(dirty_text),
                    "fingerprint": hashlib.sha256(f"{head or ''}|{branch or ''}|{dirty_text or ''}".encode("utf-8")).hexdigest(),
                }
                state = replace(state, git=git_payload)
                repo = WorkspaceEngineeringStateRepository(platform, registry_path=registry_path)
                repo.save(state)
                state_created = True
            finally:
                if old_allowed is None:
                    os.environ.pop(ALLOWED_ROOTS_ENV, None)
                else:
                    os.environ[ALLOWED_ROOTS_ENV] = old_allowed
                if old_registry is None:
                    os.environ.pop(GUIDED_REGISTRY_ENV, None)
                else:
                    os.environ[GUIDED_REGISTRY_ENV] = old_registry
    except Exception:
        if registry_before is None:
            registry_path.unlink(missing_ok=True)
        else:
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.write_bytes(registry_before)
        if state_before is None:
            state_path.unlink(missing_ok=True)
        else:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_bytes(state_before)
        raise

    return {
        "status": "PASS",
        "workspace_id": workspace_id,
        "project_id": project_id,
        "workspace_root": str(workspace),
        "runtime_registry_path": str(registry_path),
        "engineering_state_path": str(state_path),
        "engineering_state_created": state_created,
        "project_source_mutations": 0,
        "network_used": False,
        "external_api_used": False,
    }


@dataclass
class RuntimeEnvironmentBinding:
    applied: dict[str, str]
    previous: dict[str, str | None]

    def restore(self) -> None:
        for key, value in self.previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def bind_persisted_project_runtime(platform_root: Path) -> RuntimeEnvironmentBinding:
    """Load the DevPilot-persisted active project for a standard API launch.

    Explicit operator environment remains authoritative. When no runtime registry
    exists this is a no-op, preserving pre-project/B-01 behavior.
    """
    platform = Path(platform_root).resolve()
    registry_path = platform / RUNTIME_REGISTRY_REL
    if not registry_path.is_file():
        return RuntimeEnvironmentBinding({}, {})
    payload = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    active = str(payload.get("active_workspace_id") or "").strip()
    entries = [x for x in payload.get("workspaces", []) if isinstance(x, dict) and str(x.get("workspace_id") or "") == active]
    if len(entries) != 1:
        raise RuntimeError("persisted runtime registry has no unique active workspace")
    workspace = Path(str(entries[0].get("path") or "")).resolve()
    project_file = workspace / ".devpilot" / "project.yaml"
    registration_file = workspace / ".devpilot" / "workspace-registration.json"
    if not workspace.is_dir() or not project_file.is_file() or not registration_file.is_file():
        raise RuntimeError("persisted active workspace is no longer a valid DevPilot project")
    previous: dict[str, str | None] = {}
    applied: dict[str, str] = {}
    defaults = {
        ALLOWED_ROOTS_ENV: str(workspace),
        UI_ACTIVE_ROOT_ENV: str(workspace),
        GUIDED_REGISTRY_ENV: str(registry_path),
    }
    for key, value in defaults.items():
        if os.environ.get(key, "").strip():
            continue
        previous[key] = None
        os.environ[key] = value
        applied[key] = value
    return RuntimeEnvironmentBinding(applied, previous)
