from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.policy import PathGuard, PolicyEffect, configured_external_workspace_roots

_WORKSPACE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,256}$")


class WorkspaceBindingError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkspaceBinding:
    workspace_id: str
    project_id: str
    root: Path
    root_fingerprint: str
    registry_schema_version: str
    status: str


class WorkspaceRegistryBindingResolver:
    """Resolve a registered workspace from v1 or v2 registry metadata.

    The resolver is intentionally metadata-only. External workspace access is
    accepted only when the root is explicitly included in
    DEVPILOT_ALLOWED_WORKSPACE_ROOTS and passes PathGuard. Symlinked workspace
    roots are rejected to prevent a registered path from changing target later.
    """

    def __init__(self, platform_root: Path, *, registry_path: str | Path = ".devpilot/workspaces/workspace_registry.json") -> None:
        self.platform_root=Path(platform_root).resolve()
        raw=Path(registry_path)
        self.registry_path=raw if raw.is_absolute() else self.platform_root/raw
        self.registry_path=self.registry_path.resolve()
        self.path_guard=PathGuard(self.platform_root, allowed_external_roots=configured_external_workspace_roots())

    def resolve(self, workspace_id: str) -> WorkspaceBinding:
        if not _WORKSPACE_ID_RE.fullmatch(workspace_id):
            raise WorkspaceBindingError("workspace_id is invalid")
        decision=self.path_guard.evaluate(self.registry_path, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            raise WorkspaceBindingError(f"workspace registry path blocked: {decision.reason}")
        if not self.registry_path.is_file():
            raise WorkspaceBindingError(f"workspace registry is missing: {self.registry_path}")
        try:
            payload=json.loads(self.registry_path.read_text(encoding="utf-8-sig"))
        except (OSError,json.JSONDecodeError) as exc:
            raise WorkspaceBindingError(f"workspace registry is unreadable: {exc}") from exc
        if not isinstance(payload,dict) or not isinstance(payload.get("workspaces"),list):
            raise WorkspaceBindingError("workspace registry has invalid shape")
        schema_version=str(payload.get("schema_version") or "")
        if schema_version not in {"1.0","2.0"}:
            raise WorkspaceBindingError(f"unsupported workspace registry schema_version={schema_version!r}")
        defaults=payload.get("defaults") or {}
        if defaults.get("deny_unregistered_workspaces") is not True:
            raise WorkspaceBindingError("registry must deny unregistered workspaces")
        entries=[x for x in payload["workspaces"] if isinstance(x,dict) and str(x.get("workspace_id"))==workspace_id]
        if len(entries)!=1:
            raise WorkspaceBindingError(f"workspace must be registered exactly once: {workspace_id}")
        entry=entries[0]
        status=str(entry.get("status") or "")
        if status not in {"active","registered"}:
            raise WorkspaceBindingError(f"workspace is not eligible for engineering-state access: status={status}")
        path_key="root_path" if schema_version=="2.0" else "path"
        raw_path=str(entry.get(path_key) or "")
        if not raw_path:
            raise WorkspaceBindingError(f"workspace entry is missing {path_key}")
        path_mode=str(entry.get("path_mode") or "relative-to-registry-root")
        candidate=Path(raw_path)
        if path_mode=="relative-to-registry-root":
            if candidate.is_absolute():
                raise WorkspaceBindingError("relative workspace entry unexpectedly contains absolute path")
            candidate=self.platform_root/candidate
        elif path_mode=="absolute-local":
            if not candidate.is_absolute():
                raise WorkspaceBindingError("absolute-local workspace path must be absolute")
        else:
            raise WorkspaceBindingError(f"unsupported workspace path_mode={path_mode!r}")

        # Reject symlink components before resolving. A symlinked workspace root
        # can otherwise pivot outside the registry-approved root after review.
        self._reject_symlink_components(candidate)
        resolved=candidate.resolve()
        path_decision=self.path_guard.evaluate(resolved, action="read")
        if path_decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            raise WorkspaceBindingError(f"registered workspace root blocked by PathGuard: {path_decision.reason}")
        if not resolved.is_dir():
            raise WorkspaceBindingError(f"registered workspace root does not exist: {resolved}")
        project_id=str(entry.get("project_id") or "")
        if not project_id:
            raise WorkspaceBindingError("registered workspace has no project_id")
        root_hash=hashlib.sha256(os.path.normcase(str(resolved)).encode("utf-8")).hexdigest()
        return WorkspaceBinding(workspace_id, project_id, resolved, root_hash, schema_version, status)

    @staticmethod
    def _reject_symlink_components(path: Path) -> None:
        # Only existing components can be symlinks. Walk from anchor so nested
        # symlink pivots are rejected as well as a symlinked final root.
        current=Path(path.anchor) if path.is_absolute() else Path()
        for part in path.parts[1:] if path.is_absolute() else path.parts:
            current=current/part
            try:
                if current.exists() and current.is_symlink():
                    raise WorkspaceBindingError(f"symlinked workspace path component is not allowed: {current}")
            except OSError as exc:
                raise WorkspaceBindingError(f"cannot inspect workspace path component {current}: {exc}") from exc
