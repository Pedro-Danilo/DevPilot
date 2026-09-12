from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

if TYPE_CHECKING:
    from devpilot_core.application.ui_workspace_context import UiWorkspaceContextResolver
from devpilot_core.guided_sdlc.models import contains_secret_like_material
from devpilot_core.guided_sdlc.repository import WorkspaceEngineeringStateRepository

RECOVERY_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-12-A-RESUME-CHECKPOINT-V1"
RECOVERY_SCHEMA_VERSION = "1.0"
LOCK_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-12-A-WORKSPACE-LOCK-V1"
LOCK_SCHEMA_VERSION = "1.0"

_WORKSPACE_RE = re.compile(r"^[A-Za-z0-9_.-]{1,256}$")
_ACTION_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,256}$")
_REF_RE = re.compile(r"^[A-Za-z0-9_.:/@+-]{1,512}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_RECOVERY_STATES = {"SAFE_TO_RESUME", "REVALIDATION_REQUIRED", "ABORTED_REQUIRES_REPLAN", "COMPLETED"}


class RecoveryStateError(RuntimeError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    return (value or _utc_now()).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _session_fingerprint(*, actor: str, created_at: str, rotation_counter: int) -> str:
    raw = f"{actor}\0{created_at}\0{int(rotation_counter)}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _canonical_sha(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class _WorkspaceAuthority:
    workspace_id: str
    project_id: str
    workspace_root: Path
    git: dict[str, Any]
    current_step: str
    engineering_state_fingerprint: str | None


class _RecoveryStore:
    def __init__(self, platform_root: Path, workspace_id: str) -> None:
        if not _WORKSPACE_RE.fullmatch(workspace_id):
            raise RecoveryStateError("invalid workspace id")
        self.root = (Path(platform_root).resolve() / "outputs" / "workspaces" / workspace_id / "recovery").resolve()
        self.checkpoint_path = self.root / "checkpoint.json"
        self.lock_root = self.root / "locks"

    def read_checkpoint(self) -> dict[str, Any] | None:
        if not self.checkpoint_path.is_file():
            return None
        return self._read_json(self.checkpoint_path)

    def write_checkpoint(self, payload: dict[str, Any]) -> Path:
        self._assert_safe(payload)
        self._atomic_json(self.checkpoint_path, payload)
        return self.checkpoint_path

    def lock_path(self, action_id: str) -> Path:
        if not _ACTION_RE.fullmatch(action_id):
            raise RecoveryStateError("invalid action id")
        digest = hashlib.sha256(action_id.encode("utf-8")).hexdigest()[:24]
        return self.lock_root / f"{digest}.json"

    def read_lock(self, action_id: str) -> dict[str, Any] | None:
        path = self.lock_path(action_id)
        return self._read_json(path) if path.is_file() else None

    def list_locks(self) -> list[dict[str, Any]]:
        if not self.lock_root.is_dir():
            return []
        rows: list[dict[str, Any]] = []
        for path in sorted(self.lock_root.glob("*.json")):
            try:
                row = self._read_json(path)
            except RecoveryStateError:
                continue
            rows.append(row)
        return rows

    def create_lock_exclusive(self, action_id: str, payload: dict[str, Any]) -> bool:
        self._assert_safe(payload)
        path = self.lock_path(action_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        try:
            fd = os.open(path, flags, 0o600)
        except FileExistsError:
            return False
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return True

    def write_lock(self, action_id: str, payload: dict[str, Any]) -> Path:
        self._assert_safe(payload)
        path = self.lock_path(action_id)
        self._atomic_json(path, payload)
        return path

    def delete_lock(self, action_id: str) -> None:
        self.lock_path(action_id).unlink(missing_ok=True)

    def _atomic_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.parent.resolve().relative_to(self.root)
        except ValueError as exc:
            raise RecoveryStateError("recovery store path escaped root") from exc
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

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RecoveryStateError(f"recovery record unreadable: {path.name}: {exc}") from exc
        if not isinstance(value, dict):
            raise RecoveryStateError("recovery record root must be an object")
        return value

    @staticmethod
    def _assert_safe(payload: dict[str, Any]) -> None:
        findings = contains_secret_like_material(payload)
        if findings:
            raise RecoveryStateError(f"secret-like material forbidden in durable recovery state: {findings[:5]}")


class ResumeService:
    """Durable metadata-only recovery checkpoint service for GSDLC-12-A.

    Browser/session storage is never accepted as authority. Durable state lives
    under platform-local outputs/, while source/Git identity is observed from the
    server-bound active workspace. The service classifies pending work but never
    executes or auto-resumes a mutation.
    """

    def __init__(self, platform_root: Path, *, context_resolver: "UiWorkspaceContextResolver | None" = None) -> None:
        self.root = Path(platform_root).resolve()
        if context_resolver is None:
            from devpilot_core.application.ui_workspace_context import UiWorkspaceContextResolver
            context_resolver = UiWorkspaceContextResolver(self.root)
        self.context_resolver = context_resolver

    def checkpoint(
        self,
        *,
        actor: str,
        session_created_at: str,
        rotation_counter: int,
        draft_refs: Iterable[str] = (),
        pending_work: Iterable[dict[str, Any]] = (),
        evidence_refs: Iterable[str] = (),
        recovery_reason: str = "manual-checkpoint",
    ) -> dict[str, Any]:
        authority = self._authority()
        store = _RecoveryStore(self.root, authority.workspace_id)
        prior = store.read_checkpoint()
        sequence = int((prior or {}).get("sequence", -1)) + 1
        drafts = self._refs(draft_refs, label="draft_refs")
        evidence = self._refs(evidence_refs, label="evidence_refs")
        work = [self._normalize_work(item, authority.git.get("head")) for item in pending_work]
        payload: dict[str, Any] = {
            "schema_id": RECOVERY_SCHEMA_ID,
            "schema_version": RECOVERY_SCHEMA_VERSION,
            "workspace_id": authority.workspace_id,
            "project_id": authority.project_id,
            "sequence": sequence,
            "created_at_utc": str((prior or {}).get("created_at_utc") or _iso()),
            "updated_at_utc": _iso(),
            "session_binding": {
                "actor": actor,
                "session_fingerprint": _session_fingerprint(actor=actor, created_at=session_created_at, rotation_counter=rotation_counter),
                "rotation_counter": int(rotation_counter),
            },
            "authoritative_git": authority.git,
            "engineering_state_fingerprint": authority.engineering_state_fingerprint,
            "current_step": authority.current_step,
            "draft_refs": drafts,
            "safe_pending_work": work,
            "last_verified_evidence_refs": evidence,
            "recovery_reason": str(recovery_reason or "manual-checkpoint")[:256],
            "browser_storage_authority": False,
            "runtime_db_snapshot_used": False,
            "source_mutations_performed": False,
        }
        payload["checkpoint_hash"] = _canonical_sha({k: v for k, v in payload.items() if k != "checkpoint_hash"})
        store.write_checkpoint(payload)
        return payload

    def status(self, *, actor: str, session_created_at: str, rotation_counter: int) -> dict[str, Any]:
        authority = self._authority()
        store = _RecoveryStore(self.root, authority.workspace_id)
        checkpoint = store.read_checkpoint()
        if checkpoint is None:
            return {
                "state": "NO_CHECKPOINT",
                "workspace_id": authority.workspace_id,
                "project_id": authority.project_id,
                "current_step": authority.current_step,
                "checkpoint": None,
                "pending_work": [],
                "session_changed": False,
                "git_match": None,
                "browser_storage_authority": False,
                "runtime_db_snapshot_used": False,
                "next_action": "Create a server-side durable recovery checkpoint before restart testing.",
            }
        current_fp = _session_fingerprint(actor=actor, created_at=session_created_at, rotation_counter=rotation_counter)
        session_binding = dict(checkpoint.get("session_binding") or {})
        session_changed = str(session_binding.get("session_fingerprint") or "") != current_fp
        checkpoint_git = dict(checkpoint.get("authoritative_git") or {})
        git_match = bool(checkpoint_git.get("head")) and checkpoint_git.get("head") == authority.git.get("head") and checkpoint_git.get("tree") == authority.git.get("tree")
        actor_changed = bool(session_binding.get("actor")) and str(session_binding.get("actor")) != actor
        classified = [
            self._classify_work(item, actor=actor, actor_changed=actor_changed, git_match=git_match, current_head=str(authority.git.get("head") or ""))
            for item in list(checkpoint.get("safe_pending_work") or [])
            if isinstance(item, dict)
        ]
        states = {str(item.get("recovery_state")) for item in classified}
        if "ABORTED_REQUIRES_REPLAN" in states:
            state = "ABORTED_REQUIRES_REPLAN"
        elif "REVALIDATION_REQUIRED" in states or not git_match:
            state = "REVALIDATION_REQUIRED"
        else:
            state = "RECOVERED"
        return {
            "state": state,
            "workspace_id": authority.workspace_id,
            "project_id": authority.project_id,
            "current_step": authority.current_step,
            "checkpoint": checkpoint,
            "pending_work": classified,
            "session_changed": session_changed,
            "actor_changed": actor_changed,
            "git_match": git_match,
            "current_git": authority.git,
            "browser_storage_authority": False,
            "runtime_db_snapshot_used": False,
            "auto_resume_mutation": False,
            "next_action": self._next_action(state, session_changed=session_changed),
        }

    def _authority(self) -> _WorkspaceAuthority:
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id or not context.active_workspace_root:
            raise RecoveryStateError("active server-valid workspace context is required")
        workspace_id = str(context.active_workspace_id)
        workspace_root = context.active_workspace_root.resolve()
        project_id = workspace_id
        current_step = "unknown"
        state_fp: str | None = None
        repository = WorkspaceEngineeringStateRepository(self.root)
        try:
            state = repository.load(workspace_id)
            project_id = state.project_id
            current_step = state.current_step
            state_fp = state.fingerprint()
        except (KeyError, RuntimeError, ValueError):
            pass
        return _WorkspaceAuthority(
            workspace_id=workspace_id,
            project_id=project_id,
            workspace_root=workspace_root,
            git=self._git_identity(workspace_root),
            current_step=current_step,
            engineering_state_fingerprint=state_fp,
        )

    @staticmethod
    def _git_identity(root: Path) -> dict[str, Any]:
        def run(*args: str) -> str:
            cp = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=8, check=False)
            if cp.returncode != 0:
                raise RecoveryStateError(f"read-only git identity command failed: {' '.join(args)}")
            return cp.stdout.strip()
        head = run("rev-parse", "HEAD")
        tree = run("rev-parse", "HEAD^{tree}")
        if not _GIT_SHA_RE.fullmatch(head) or not _GIT_SHA_RE.fullmatch(tree):
            raise RecoveryStateError("invalid Git identity returned by active workspace")
        branch = run("branch", "--show-current") or "DETACHED"
        dirty = bool(run("status", "--porcelain", "--untracked-files=no"))
        fingerprint = hashlib.sha256(f"{head}\0{tree}\0{branch}\0{int(dirty)}".encode("utf-8")).hexdigest()
        return {"head": head, "tree": tree, "branch": branch, "dirty": dirty, "fingerprint": fingerprint}

    @staticmethod
    def _refs(values: Iterable[str], *, label: str) -> list[str]:
        rows: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if not text:
                continue
            if not _REF_RE.fullmatch(text):
                raise RecoveryStateError(f"{label} contains an invalid reference")
            if text not in rows:
                rows.append(text)
        return rows[:100]

    @staticmethod
    def _normalize_work(item: dict[str, Any], current_head: Any) -> dict[str, Any]:
        work_id = str(item.get("work_id") or "").strip()
        if not _ACTION_RE.fullmatch(work_id):
            raise RecoveryStateError("pending work requires a bounded work_id")
        kind = str(item.get("kind") or "work").strip()[:64]
        status = str(item.get("status") or "PENDING").strip().upper()[:64]
        sensitive = bool(item.get("sensitive", False))
        safe_to_resume = bool(item.get("safe_to_resume", False)) and not sensitive
        row = {
            "work_id": work_id,
            "kind": kind,
            "status": status,
            "sensitive": sensitive,
            "safe_to_resume": safe_to_resume,
            "approval_id": str(item.get("approval_id") or "")[:256] or None,
            "approval_actor": str(item.get("approval_actor") or "")[:256] or None,
            "approval_expires_at": str(item.get("approval_expires_at") or "")[:64] or None,
            "bound_git_head": str(item.get("bound_git_head") or current_head or "")[:64] or None,
        }
        findings = contains_secret_like_material(row)
        if findings:
            raise RecoveryStateError("pending work contains secret-like material")
        return row

    @staticmethod
    def _classify_work(item: dict[str, Any], *, actor: str, actor_changed: bool, git_match: bool, current_head: str) -> dict[str, Any]:
        row = dict(item)
        status = str(row.get("status") or "").upper()
        if status in {"COMPLETED", "PASS", "DONE"}:
            recovery_state = "COMPLETED"
            reason = "WORK_ALREADY_COMPLETED"
        elif actor_changed or (row.get("approval_actor") and str(row.get("approval_actor")) != actor):
            recovery_state = "ABORTED_REQUIRES_REPLAN"
            reason = "ACTOR_AUTHORITY_CHANGED"
        elif row.get("bound_git_head") and str(row.get("bound_git_head")) != current_head:
            recovery_state = "ABORTED_REQUIRES_REPLAN"
            reason = "SOURCE_IDENTITY_CHANGED"
        elif row.get("approval_expires_at") and (_parse_iso(str(row.get("approval_expires_at"))) or datetime.min.replace(tzinfo=timezone.utc)) <= _utc_now():
            recovery_state = "ABORTED_REQUIRES_REPLAN"
            reason = "APPROVAL_EXPIRED"
        elif bool(row.get("sensitive")) or row.get("approval_id"):
            recovery_state = "REVALIDATION_REQUIRED"
            reason = "SENSITIVE_OR_APPROVAL_BOUND_WORK_REQUIRES_NEW_CONFIRMATION"
        elif not git_match:
            recovery_state = "REVALIDATION_REQUIRED"
            reason = "GIT_REVALIDATION_REQUIRED"
        elif bool(row.get("safe_to_resume")):
            recovery_state = "SAFE_TO_RESUME"
            reason = "SAFE_METADATA_ONLY_WORK_CAN_RESUME"
        else:
            recovery_state = "REVALIDATION_REQUIRED"
            reason = "PENDING_WORK_NOT_EXPLICITLY_SAFE"
        if recovery_state not in _RECOVERY_STATES:
            raise RecoveryStateError("invalid recovery classification")
        row["recovery_state"] = recovery_state
        row["reason_code"] = reason
        row["auto_execute"] = False
        return row

    @staticmethod
    def _next_action(state: str, *, session_changed: bool) -> str:
        if state == "ABORTED_REQUIRES_REPLAN":
            return "Review invalidated work and create a new plan/approval bound to current authority."
        if state == "REVALIDATION_REQUIRED":
            return "Revalidate source/session authority and request new confirmation for sensitive work."
        if state == "RECOVERED" and session_changed:
            return "Context recovered under a new session; continue only SAFE_TO_RESUME work."
        return "Context recovered; continue from the server-authoritative current step."


class WorkspaceLockService:
    """Workspace/action lock service with explicit stale recovery and no lock stealing."""

    def __init__(self, platform_root: Path, *, context_resolver: "UiWorkspaceContextResolver | None" = None) -> None:
        self.root = Path(platform_root).resolve()
        if context_resolver is None:
            from devpilot_core.application.ui_workspace_context import UiWorkspaceContextResolver
            context_resolver = UiWorkspaceContextResolver(self.root)
        self.context_resolver = context_resolver

    def status(self, *, actor: str, session_created_at: str, rotation_counter: int) -> dict[str, Any]:
        workspace_id = self._workspace_id()
        store = _RecoveryStore(self.root, workspace_id)
        current_session = _session_fingerprint(actor=actor, created_at=session_created_at, rotation_counter=rotation_counter)
        rows = [self._decorate(row, current_session=current_session, actor=actor) for row in store.list_locks()]
        return {"workspace_id": workspace_id, "locks": rows, "locks_total": len(rows), "auto_force_unlock": False}

    def acquire(self, *, action_id: str, actor: str, session_created_at: str, rotation_counter: int, sensitive: bool, ttl_seconds: int) -> dict[str, Any]:
        workspace_id = self._workspace_id()
        ttl = max(30, min(int(ttl_seconds), 3600))
        store = _RecoveryStore(self.root, workspace_id)
        session_fp = _session_fingerprint(actor=actor, created_at=session_created_at, rotation_counter=rotation_counter)
        existing = store.read_lock(action_id)
        if existing:
            decorated = self._decorate(existing, current_session=session_fp, actor=actor)
            if decorated["stale"]:
                raise RecoveryStateError("stale lock exists; explicit stale recovery is required before acquire")
            if decorated["owned_by_current_session"]:
                updated = dict(existing)
                updated["heartbeat_at_utc"] = _iso()
                updated["expires_at_utc"] = _iso(_utc_now() + timedelta(seconds=ttl))
                updated["ttl_seconds"] = ttl
                store.write_lock(action_id, updated)
                return self._decorate(updated, current_session=session_fp, actor=actor) | {"reused": True}
            raise RecoveryStateError("active lock is owned by another session/actor")
        now = _utc_now()
        payload = {
            "schema_id": LOCK_SCHEMA_ID,
            "schema_version": LOCK_SCHEMA_VERSION,
            "workspace_id": workspace_id,
            "action_id": action_id,
            "actor": actor,
            "session_fingerprint": session_fp,
            "sensitive": bool(sensitive),
            "acquired_at_utc": _iso(now),
            "heartbeat_at_utc": _iso(now),
            "expires_at_utc": _iso(now + timedelta(seconds=ttl)),
            "ttl_seconds": ttl,
            "state": "ACTIVE",
            "auto_force_unlock": False,
            "source_mutations_performed": False,
        }
        if not store.create_lock_exclusive(action_id, payload):
            raise RecoveryStateError("concurrent lock acquisition detected; retry status before proceeding")
        return self._decorate(payload, current_session=session_fp, actor=actor) | {"reused": False}

    def release(self, *, action_id: str, actor: str, session_created_at: str, rotation_counter: int) -> dict[str, Any]:
        workspace_id = self._workspace_id()
        store = _RecoveryStore(self.root, workspace_id)
        session_fp = _session_fingerprint(actor=actor, created_at=session_created_at, rotation_counter=rotation_counter)
        existing = store.read_lock(action_id)
        if not existing:
            return {"workspace_id": workspace_id, "action_id": action_id, "released": False, "already_absent": True}
        decorated = self._decorate(existing, current_session=session_fp, actor=actor)
        if not decorated["owned_by_current_session"]:
            raise RecoveryStateError("lock release requires exact actor/session ownership")
        store.delete_lock(action_id)
        return {"workspace_id": workspace_id, "action_id": action_id, "released": True, "already_absent": False}

    def recover_stale(self, *, action_id: str, actor: str, roles: Iterable[str], confirmation: str) -> dict[str, Any]:
        if confirmation != "RECOVER_STALE_LOCK":
            raise RecoveryStateError("explicit stale-lock confirmation is required")
        if not ({str(role) for role in roles} & {"owner", "release-manager", "operator"}):
            raise RecoveryStateError("stale lock recovery requires an authorized human role")
        workspace_id = self._workspace_id()
        store = _RecoveryStore(self.root, workspace_id)
        existing = store.read_lock(action_id)
        if not existing:
            return {"workspace_id": workspace_id, "action_id": action_id, "recovered": False, "already_absent": True}
        expires = _parse_iso(str(existing.get("expires_at_utc") or ""))
        stale = bool(expires and expires <= _utc_now())
        if not stale:
            raise RecoveryStateError("active lock cannot be force-recovered")
        store.delete_lock(action_id)
        return {
            "workspace_id": workspace_id,
            "action_id": action_id,
            "recovered": True,
            "already_absent": False,
            "prior_actor": existing.get("actor"),
            "prior_sensitive": bool(existing.get("sensitive")),
            "requires_operation_revalidation": bool(existing.get("sensitive")),
            "auto_execute": False,
        }

    def _workspace_id(self) -> str:
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id:
            raise RecoveryStateError("active server-valid workspace context is required")
        return str(context.active_workspace_id)

    @staticmethod
    def _decorate(row: dict[str, Any], *, current_session: str, actor: str) -> dict[str, Any]:
        expires = _parse_iso(str(row.get("expires_at_utc") or ""))
        stale = bool(expires and expires <= _utc_now())
        payload = dict(row)
        payload["stale"] = stale
        payload["owned_by_current_session"] = str(row.get("session_fingerprint") or "") == current_session and str(row.get("actor") or "") == actor
        payload["recovery_required"] = stale
        return payload
