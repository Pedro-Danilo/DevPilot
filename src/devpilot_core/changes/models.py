from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ChangeSetFile:
    """One file-level change observed after applying a patch in sandbox.

    The model deliberately stores metadata and hashes, not raw file contents.
    This keeps ChangeSet evidence auditable without leaking source or secrets.
    """

    path: str
    action: str
    before_sha256: str | None = None
    after_sha256: str | None = None
    before_size_bytes: int | None = None
    after_size_bytes: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "path": self.path,
            "action": self.action,
            "before_sha256": self.before_sha256,
            "after_sha256": self.after_sha256,
            "before_size_bytes": self.before_size_bytes,
            "after_size_bytes": self.after_size_bytes,
        }
        return payload


@dataclass(frozen=True)
class RollbackPlanPreview:
    """Preliminary rollback instructions derived from a sandbox ChangeSet.

    FUNC-SPRINT-41 does not implement executable rollback. The preview gives the
    next sprint enough structured metadata to build RollbackManager without
    overclaiming production rollback.
    """

    available: bool
    strategy: str
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "strategy": self.strategy,
            "notes": list(self.notes),
            "preliminary": True,
        }


@dataclass(frozen=True)
class ChangeSet:
    """Serializable ChangeSet produced by PatchSandboxManager.

    Purpose:
        Represent what a patch changed after being applied to a sandbox copy of
        the workspace.

    Functioning:
        Stores patch metadata, sandbox location, file-level actions and
        before/after hashes from sandbox files. It does not store raw patch body
        or file contents.

    Integration:
        Emitted by `patch sandbox` and intended as input for future rollback and
        refactor execution sprints.
    """

    changeset_id: str
    source_patch: str
    sandbox_id: str
    sandbox_workspace: str
    files: tuple[ChangeSetFile, ...]
    tests_requested: bool = False
    tests_result_summary: dict[str, Any] | None = None
    rollback_plan: RollbackPlanPreview | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "changeset_id": self.changeset_id,
            "source_patch": self.source_patch,
            "sandbox_id": self.sandbox_id,
            "sandbox_workspace": self.sandbox_workspace,
            "files_total": len(self.files),
            "files": [item.to_dict() for item in self.files],
            "tests_requested": self.tests_requested,
            "tests_result_summary": self.tests_result_summary,
            "rollback_plan": self.rollback_plan.to_dict() if self.rollback_plan else None,
            "metadata": self.metadata,
            "preliminary": True,
        }


@dataclass(frozen=True)
class RollbackOperation:
    """One rollback operation derived from a ChangeSet file entry.

    The operation is metadata-only in FUNC-SPRINT-42. It references local backup
    paths and hashes but never stores raw file contents in command output.
    """

    path: str
    action: str
    backup_path: str | None = None
    expected_current_sha256: str | None = None
    restore_sha256: str | None = None
    before_size_bytes: int | None = None
    after_size_bytes: int | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "action": self.action,
            "backup_path": self.backup_path,
            "expected_current_sha256": self.expected_current_sha256,
            "restore_sha256": self.restore_sha256,
            "before_size_bytes": self.before_size_bytes,
            "after_size_bytes": self.after_size_bytes,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class RollbackPlan:
    """Auditable rollback plan generated from a sandbox ChangeSet.

    FUNC-SPRINT-42 intentionally separates plan/backup creation from execution.
    The plan is serializable and suitable for review, but execute remains gated
    and non-mutating in this initial sprint.
    """

    rollback_id: str
    changeset_id: str
    source_changeset: str
    source_patch: str
    sandbox_id: str
    created_at: str
    operations: tuple[RollbackOperation, ...]
    backups_dir: str
    backup_available: bool
    approval_required_for_execute: bool = True
    execute_supported: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rollback_id": self.rollback_id,
            "changeset_id": self.changeset_id,
            "source_changeset": self.source_changeset,
            "source_patch": self.source_patch,
            "sandbox_id": self.sandbox_id,
            "created_at": self.created_at,
            "operations_total": len(self.operations),
            "operations": [operation.to_dict() for operation in self.operations],
            "backups_dir": self.backups_dir,
            "backup_available": self.backup_available,
            "approval_required_for_execute": self.approval_required_for_execute,
            "execute_supported": self.execute_supported,
            "metadata": self.metadata,
            "preliminary": True,
        }


@dataclass(frozen=True)
class RollbackPoint:
    """Persisted rollback point index entry."""

    rollback_id: str
    changeset_id: str
    created_at: str
    status: str
    plan_path: str
    backups_dir: str
    files_total: int
    backup_available: bool
    execute_supported: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rollback_id": self.rollback_id,
            "changeset_id": self.changeset_id,
            "created_at": self.created_at,
            "status": self.status,
            "plan_path": self.plan_path,
            "backups_dir": self.backups_dir,
            "files_total": self.files_total,
            "backup_available": self.backup_available,
            "execute_supported": self.execute_supported,
            "metadata": self.metadata,
            "preliminary": True,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RollbackPoint":
        return cls(
            rollback_id=str(payload.get("rollback_id") or ""),
            changeset_id=str(payload.get("changeset_id") or ""),
            created_at=str(payload.get("created_at") or ""),
            status=str(payload.get("status") or "unknown"),
            plan_path=str(payload.get("plan_path") or ""),
            backups_dir=str(payload.get("backups_dir") or ""),
            files_total=int(payload.get("files_total") or 0),
            backup_available=bool(payload.get("backup_available")),
            execute_supported=bool(payload.get("execute_supported")),
            metadata=dict(payload.get("metadata") or {}),
        )


def file_fingerprint(path: Path) -> dict[str, Any] | None:
    """Return hash/size metadata for a file, or None when it does not exist."""

    if not path.exists() or not path.is_file():
        return None
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}


def build_changeset_id(*, patch_rel: str, sandbox_id: str, files: list[ChangeSetFile]) -> str:
    """Build a stable opaque ChangeSet id from metadata only."""

    digest = hashlib.sha256()
    digest.update(patch_rel.encode("utf-8", errors="replace"))
    digest.update(sandbox_id.encode("utf-8", errors="replace"))
    for item in files:
        digest.update(item.path.encode("utf-8", errors="replace"))
        digest.update(item.action.encode("utf-8", errors="replace"))
        digest.update(str(item.before_sha256).encode("utf-8", errors="replace"))
        digest.update(str(item.after_sha256).encode("utf-8", errors="replace"))
    return f"changeset-{digest.hexdigest()[:16]}"



def build_rollback_id(*, changeset_id: str, source: str, files: list[str]) -> str:
    """Build a stable opaque rollback id from ChangeSet metadata only."""

    digest = hashlib.sha256()
    digest.update(changeset_id.encode("utf-8", errors="replace"))
    digest.update(source.encode("utf-8", errors="replace"))
    for path in sorted(files):
        digest.update(path.encode("utf-8", errors="replace"))
    return f"rollback-{digest.hexdigest()[:16]}"
