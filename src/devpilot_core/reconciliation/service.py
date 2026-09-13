from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

if TYPE_CHECKING:
    from devpilot_core.application.ui_workspace_context import UiWorkspaceContextResolver

from devpilot_core.guided_sdlc.models import contains_secret_like_material
from devpilot_core.guided_sdlc.repository import WorkspaceEngineeringStateRepository
from devpilot_core.recovery import RecoveryStateError, WorkspaceLockService

SNAPSHOT_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-12-B-WORKSPACE-DRIFT-SNAPSHOT-V1"
REPORT_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-12-B-RECONCILIATION-REPORT-V1"
SCHEMA_VERSION = "1.0"
RECONCILIATION_CLASSES = {
    "NO_CONFLICT",
    "REVALIDATE",
    "REPLAN_REQUIRED",
    "MANUAL_RECONCILIATION_REQUIRED",
    "READ_ONLY_BLOCK",
}
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_IGNORED_PREFIXES = (".git/", "outputs/", ".venv/", "node_modules/", "__pycache__/", ".pytest_cache/")
_RUNTIME_NAMES = ("auth.db", "devpilot.db")


class ReconciliationStateError(RuntimeError):
    pass


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    findings = contains_secret_like_material(payload)
    if findings:
        raise ReconciliationStateError(f"secret-like material forbidden in reconciliation state: {findings[:5]}")
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


class AdvancedWorkspaceReconciliationService:
    """Read-only Git/filesystem drift detector plus explicit metadata baseline.

    The service never mutates the managed workspace or Git. The only writes are
    platform-local reconciliation metadata under outputs/. Baseline adoption is
    explicit, dry-run by default, lock-protected and refuses unsafe drift.
    """

    BASELINE_CONFIRMATION = "CAPTURE_RECONCILIATION_BASELINE"
    ADOPT_CONFIRMATION = "ADOPT_RECONCILIATION_BASELINE"
    LOCK_ACTION = "reconciliation.baseline.authority"

    def __init__(self, platform_root: Path, *, context_resolver: "UiWorkspaceContextResolver | None" = None) -> None:
        self.root = Path(platform_root).resolve()
        if context_resolver is None:
            from devpilot_core.application.ui_workspace_context import UiWorkspaceContextResolver
            context_resolver = UiWorkspaceContextResolver(self.root)
        self.context_resolver = context_resolver
        self.locks = WorkspaceLockService(self.root, context_resolver=self.context_resolver)

    def inspect(self, *, actor: str, session_created_at: str, rotation_counter: int) -> dict[str, Any]:
        context = self._context()
        workspace_id = str(context.active_workspace_id)
        workspace_root = Path(context.active_workspace_root).resolve()
        current = self._git_identity(workspace_root)
        baseline = self._read_baseline(workspace_id)
        engineering = self._engineering_binding(workspace_id)
        recovery = self._recovery_context(workspace_id)

        if baseline is None:
            snapshot = self._snapshot(
                workspace_id=workspace_id,
                current=current,
                baseline=None,
                changes=self._worktree_changes(workspace_root, baseline_head=None, authority_paths=engineering["authority_paths"]),
                relation="BASELINE_MISSING",
                engineering=engineering,
            )
            return self._report(
                snapshot=snapshot,
                classification="READ_ONLY_BLOCK",
                reason_codes=["RECONCILIATION_BASELINE_MISSING"],
                recovery=recovery,
                authority_invalidations=[],
            )

        self._validate_baseline_binding(baseline, workspace_id=workspace_id, workspace_root=workspace_root)
        relation = self._head_relation(workspace_root, str(baseline.get("head") or ""), str(current.get("head") or ""))
        changes = self._worktree_changes(
            workspace_root,
            baseline_head=str(baseline.get("head") or ""),
            authority_paths=engineering["authority_paths"],
        )
        snapshot = self._snapshot(
            workspace_id=workspace_id,
            current=current,
            baseline=baseline,
            changes=changes,
            relation=relation,
            engineering=engineering,
        )
        classification, reasons = self._classify(snapshot)
        invalidations = self._authority_invalidations(snapshot)
        return self._report(
            snapshot=snapshot,
            classification=classification,
            reason_codes=reasons,
            recovery=recovery,
            authority_invalidations=invalidations,
        )

    def baseline(
        self,
        *,
        actor: str,
        session_created_at: str,
        rotation_counter: int,
        execute: bool,
        confirmation: str,
    ) -> dict[str, Any]:
        context = self._context()
        workspace_id = str(context.active_workspace_id)
        workspace_root = Path(context.active_workspace_root).resolve()
        current = self._git_identity(workspace_root)
        engineering = self._engineering_binding(workspace_id)
        dirty = self._worktree_changes(workspace_root, baseline_head=current["head"], authority_paths=engineering["authority_paths"])
        plan = {
            "operation": "CAPTURE_RECONCILIATION_BASELINE",
            "dry_run": not execute,
            "workspace_id": workspace_id,
            "git_identity": current,
            "worktree_dirty": bool(dirty),
            "source_mutations_performed": False,
            "git_mutations_performed": False,
        }
        if not execute:
            return {"status": "DRY_RUN", "plan": plan, "baseline_written": False}
        if confirmation != self.BASELINE_CONFIRMATION:
            raise ReconciliationStateError("explicit baseline confirmation is required")
        if dirty:
            raise ReconciliationStateError("baseline capture requires a clean reviewed worktree; dirty state cannot become authority silently")
        if current["detached"]:
            raise ReconciliationStateError("baseline capture is blocked while HEAD is detached")
        return self._write_baseline_locked(
            workspace_id=workspace_id,
            workspace_root=workspace_root,
            current=current,
            engineering=engineering,
            actor=actor,
            session_created_at=session_created_at,
            rotation_counter=rotation_counter,
            reason="EXPLICIT_INITIAL_BASELINE",
        )

    def adopt(
        self,
        *,
        actor: str,
        session_created_at: str,
        rotation_counter: int,
        execute: bool,
        confirmation: str,
    ) -> dict[str, Any]:
        report = self.inspect(actor=actor, session_created_at=session_created_at, rotation_counter=rotation_counter)
        classification = str(report.get("classification") or "READ_ONLY_BLOCK")
        plan = {
            "operation": "ADOPT_RECONCILIATION_BASELINE",
            "dry_run": not execute,
            "classification": classification,
            "allowed": classification in {"NO_CONFLICT", "REVALIDATE"} and not report.get("snapshot", {}).get("worktree_dirty"),
            "safe_recovery_plan": report.get("safe_recovery_plan", []),
            "source_mutations_performed": False,
            "git_mutations_performed": False,
        }
        if not execute:
            return {"status": "DRY_RUN", "plan": plan, "baseline_written": False, "report": report}
        if confirmation != self.ADOPT_CONFIRMATION:
            raise ReconciliationStateError("explicit adoption confirmation is required")
        if not plan["allowed"]:
            raise ReconciliationStateError("current drift cannot be adopted automatically; resolve/review it first")
        context = self._context()
        workspace_id = str(context.active_workspace_id)
        workspace_root = Path(context.active_workspace_root).resolve()
        current = self._git_identity(workspace_root)
        engineering = self._engineering_binding(workspace_id)
        return self._write_baseline_locked(
            workspace_id=workspace_id,
            workspace_root=workspace_root,
            current=current,
            engineering=engineering,
            actor=actor,
            session_created_at=session_created_at,
            rotation_counter=rotation_counter,
            reason="EXPLICIT_REVIEWED_ADOPTION",
        )

    def _write_baseline_locked(
        self,
        *,
        workspace_id: str,
        workspace_root: Path,
        current: dict[str, Any],
        engineering: dict[str, Any],
        actor: str,
        session_created_at: str,
        rotation_counter: int,
        reason: str,
    ) -> dict[str, Any]:
        acquired = False
        try:
            self.locks.acquire(
                action_id=self.LOCK_ACTION,
                actor=actor,
                session_created_at=session_created_at,
                rotation_counter=rotation_counter,
                sensitive=True,
                ttl_seconds=120,
            )
            acquired = True
            # Re-read after lock so identity cannot silently change between plan and apply.
            verified = self._git_identity(workspace_root)
            if verified != current:
                raise ReconciliationStateError("Git identity changed after reconciliation plan; retry from a fresh dry-run")
            changes = self._worktree_changes(workspace_root, baseline_head=current["head"], authority_paths=engineering["authority_paths"])
            if changes:
                raise ReconciliationStateError("worktree changed after reconciliation plan; retry after review")
            payload = {
                "schema_id": SNAPSHOT_SCHEMA_ID,
                "schema_version": SCHEMA_VERSION,
                "workspace_id": workspace_id,
                "workspace_root_fingerprint": hashlib.sha256(str(workspace_root).encode("utf-8")).hexdigest(),
                "head": current["head"],
                "tree": current["tree"],
                "branch": current["branch"],
                "engineering_state_fingerprint": engineering["fingerprint"],
                "authority_preimages": self._preimages(workspace_root, current["head"], engineering["authority_paths"]),
                "captured_at_utc": _iso(),
                "captured_by": actor,
                "capture_reason": reason,
                "source_mutations_performed": False,
                "git_mutations_performed": False,
            }
            payload["baseline_sha256"] = _sha(payload)
            path = self._baseline_path(workspace_id)
            _atomic_json(path, payload)
            return {
                "status": "PASS",
                "baseline_written": True,
                "baseline": payload,
                "baseline_path": str(path.relative_to(self.root)).replace("\\", "/"),
                "source_mutations_performed": False,
                "git_mutations_performed": False,
            }
        except RecoveryStateError as exc:
            raise ReconciliationStateError(str(exc)) from exc
        finally:
            if acquired:
                try:
                    self.locks.release(
                        action_id=self.LOCK_ACTION,
                        actor=actor,
                        session_created_at=session_created_at,
                        rotation_counter=rotation_counter,
                    )
                except RecoveryStateError:
                    # Keep original operation result authoritative; stale lock recovery remains explicit.
                    pass

    def _context(self):
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id or not context.active_workspace_root:
            raise ReconciliationStateError("active server-valid workspace context is required")
        return context

    def _baseline_path(self, workspace_id: str) -> Path:
        safe = re.fullmatch(r"[A-Za-z0-9_.-]{1,256}", workspace_id)
        if not safe:
            raise ReconciliationStateError("invalid workspace id")
        path = (self.root / "outputs" / "workspaces" / workspace_id / "reconciliation" / "baseline.json").resolve()
        try:
            path.relative_to(self.root / "outputs" / "workspaces")
        except ValueError as exc:
            raise ReconciliationStateError("reconciliation metadata path escaped platform outputs") from exc
        return path

    def _read_baseline(self, workspace_id: str) -> dict[str, Any] | None:
        path = self._baseline_path(workspace_id)
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReconciliationStateError(f"reconciliation baseline unreadable: {exc}") from exc
        if not isinstance(payload, dict):
            raise ReconciliationStateError("reconciliation baseline root must be an object")
        stored = str(payload.get("baseline_sha256") or "")
        check = dict(payload)
        check.pop("baseline_sha256", None)
        if stored != _sha(check):
            raise ReconciliationStateError("reconciliation baseline integrity hash mismatch")
        return payload

    @staticmethod
    def _validate_baseline_binding(baseline: dict[str, Any], *, workspace_id: str, workspace_root: Path) -> None:
        if str(baseline.get("workspace_id") or "") != workspace_id:
            raise ReconciliationStateError("reconciliation baseline workspace binding mismatch")
        fingerprint = hashlib.sha256(str(workspace_root).encode("utf-8")).hexdigest()
        if str(baseline.get("workspace_root_fingerprint") or "") != fingerprint:
            raise ReconciliationStateError("reconciliation baseline root binding mismatch")

    def _git(self, workspace_root: Path, *args: str, check: bool = True) -> str:
        proc = subprocess.run(
            ["git", "-C", str(workspace_root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
        if check and proc.returncode != 0:
            message = (proc.stderr or proc.stdout or "git command failed").strip()
            raise ReconciliationStateError(message[:500])
        return proc.stdout.strip()

    def _git_identity(self, workspace_root: Path) -> dict[str, Any]:
        inside = self._git(workspace_root, "rev-parse", "--is-inside-work-tree", check=False)
        if inside.lower() != "true":
            raise ReconciliationStateError("active workspace is not a Git worktree")
        head = self._git(workspace_root, "rev-parse", "HEAD")
        tree = self._git(workspace_root, "rev-parse", "HEAD^{tree}")
        if not _GIT_SHA_RE.fullmatch(head) or not _GIT_SHA_RE.fullmatch(tree):
            raise ReconciliationStateError("invalid Git identity returned by repository")
        branch = self._git(workspace_root, "branch", "--show-current", check=False)
        detached = not bool(branch)
        return {"head": head, "tree": tree, "branch": branch or "DETACHED", "detached": detached}

    def _head_relation(self, workspace_root: Path, baseline_head: str, current_head: str) -> str:
        if baseline_head == current_head:
            return "SAME"
        if not _GIT_SHA_RE.fullmatch(baseline_head):
            return "BASELINE_HEAD_INVALID"
        exists = self._git(workspace_root, "cat-file", "-e", f"{baseline_head}^{{commit}}", check=False)
        # cat-file -e emits no stdout; use merge-base directly and distinguish missing by rc.
        proc = subprocess.run(
            ["git", "-C", str(workspace_root), "merge-base", baseline_head, current_head],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
        if proc.returncode != 0:
            return "UNRELATED_OR_BASELINE_MISSING"
        base = proc.stdout.strip()
        if base == baseline_head:
            return "FAST_FORWARD"
        if base == current_head:
            return "REWIND"
        return "DIVERGED"

    def _worktree_changes(self, workspace_root: Path, *, baseline_head: str | None, authority_paths: set[str]) -> list[dict[str, Any]]:
        raw = subprocess.run(
            ["git", "-C", str(workspace_root), "status", "--porcelain=v1", "-z", "--untracked-files=all"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
        if raw.returncode != 0:
            raise ReconciliationStateError(raw.stderr.decode("utf-8", "replace")[:500])
        parts = raw.stdout.decode("utf-8", "surrogateescape").split("\0")
        rows: list[dict[str, Any]] = []
        i = 0
        while i < len(parts):
            entry = parts[i]
            i += 1
            if not entry:
                continue
            xy = entry[:2]
            path = entry[3:].replace("\\", "/")
            old_path: str | None = None
            kind = "MODIFY"
            if xy == "??":
                kind = "UNTRACKED"
            elif "R" in xy:
                kind = "RENAME"
                if i < len(parts):
                    old_path = parts[i].replace("\\", "/")
                    i += 1
            elif "D" in xy:
                kind = "DELETE"
            elif "A" in xy:
                kind = "ADD"
            if self._ignored(path):
                continue
            linked = path in authority_paths or bool(old_path and old_path in authority_paths)
            baseline_hash = self._blob_at(workspace_root, baseline_head, old_path or path) if baseline_head else None
            current_hash = self._file_hash(workspace_root / path) if kind != "DELETE" else None
            rows.append({
                "kind": kind,
                "status": xy,
                "path": path,
                "old_path": old_path,
                "baseline_hash": baseline_hash,
                "current_hash": current_hash,
                "linked_to_engineering_authority": linked,
            })
        return sorted(rows, key=lambda row: (str(row.get("path")), str(row.get("old_path") or "")))

    @staticmethod
    def _ignored(path: str) -> bool:
        normalized = path.replace("\\", "/").lstrip("./")
        if any(normalized.startswith(prefix) for prefix in _IGNORED_PREFIXES):
            return True
        name = normalized.rsplit("/", 1)[-1]
        return any(name == base or name.startswith(base + "-") or name.startswith(base + ".") for base in _RUNTIME_NAMES)

    def _blob_at(self, workspace_root: Path, head: str | None, path: str) -> str | None:
        if not head or not _GIT_SHA_RE.fullmatch(head):
            return None
        proc = subprocess.run(
            ["git", "-C", str(workspace_root), "rev-parse", f"{head}:{path}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
        value = proc.stdout.strip()
        return value if proc.returncode == 0 and _GIT_SHA_RE.fullmatch(value) else None

    @staticmethod
    def _file_hash(path: Path) -> str | None:
        if not path.is_file() or path.is_symlink():
            return None
        digest = hashlib.sha256()
        try:
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError:
            return None
        return digest.hexdigest()

    def _engineering_binding(self, workspace_id: str) -> dict[str, Any]:
        try:
            state = WorkspaceEngineeringStateRepository(self.root).load(workspace_id)
            payload = state.to_payload()
        except (KeyError, RuntimeError, ValueError):
            return {"fingerprint": None, "authority_paths": set(), "available": False}
        authority_paths = self._extract_paths(payload)
        return {"fingerprint": str(getattr(state, "fingerprint", "") or _sha(payload)), "authority_paths": authority_paths, "available": True}

    def _extract_paths(self, payload: Any) -> set[str]:
        result: set[str] = set()
        path_keys = {"path", "file", "source_path", "target_path", "document_path", "relative_path"}
        def visit(value: Any, key: str = "") -> None:
            if isinstance(value, dict):
                for child_key, child in value.items():
                    visit(child, str(child_key))
            elif isinstance(value, list):
                for child in value:
                    visit(child, key)
            elif isinstance(value, str) and key in path_keys:
                candidate = value.replace("\\", "/").lstrip("./")
                if candidate and not candidate.startswith(("http://", "https://", "/")) and ".." not in Path(candidate).parts:
                    result.add(candidate)
        visit(payload)
        return result

    def _preimages(self, workspace_root: Path, head: str, paths: Iterable[str]) -> dict[str, str]:
        result: dict[str, str] = {}
        for path in sorted(set(paths))[:2000]:
            value = self._blob_at(workspace_root, head, path)
            if value:
                result[path] = value
        return result

    def _recovery_context(self, workspace_id: str) -> dict[str, Any]:
        path = self.root / "outputs" / "workspaces" / workspace_id / "recovery" / "checkpoint.json"
        if not path.is_file():
            return {"checkpoint_present": False, "draft_refs": [], "pending_work": []}
        try:
            row = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return {"checkpoint_present": True, "draft_refs": [], "pending_work": [], "checkpoint_unreadable": True}
        return {
            "checkpoint_present": True,
            "draft_refs": [str(value) for value in list(row.get("draft_refs") or [])],
            "pending_work": [dict(value) for value in list(row.get("pending_work") or []) if isinstance(value, dict)],
        }

    def _snapshot(
        self,
        *,
        workspace_id: str,
        current: dict[str, Any],
        baseline: dict[str, Any] | None,
        changes: list[dict[str, Any]],
        relation: str,
        engineering: dict[str, Any],
    ) -> dict[str, Any]:
        baseline_branch = str((baseline or {}).get("branch") or "")
        current_branch = str(current.get("branch") or "")
        baseline_engineering = str((baseline or {}).get("engineering_state_fingerprint") or "")
        current_engineering = str(engineering.get("fingerprint") or "")
        snapshot = {
            "schema_id": SNAPSHOT_SCHEMA_ID,
            "schema_version": SCHEMA_VERSION,
            "workspace_id": workspace_id,
            "observed_at_utc": _iso(),
            "baseline_present": baseline is not None,
            "baseline": {
                "head": (baseline or {}).get("head"),
                "tree": (baseline or {}).get("tree"),
                "branch": (baseline or {}).get("branch"),
                "engineering_state_fingerprint": (baseline or {}).get("engineering_state_fingerprint"),
                "baseline_sha256": (baseline or {}).get("baseline_sha256"),
            },
            "current": current,
            "head_relation": relation,
            "branch_switched": bool(baseline and baseline_branch != current_branch),
            "engineering_state_changed": bool(baseline and baseline_engineering and current_engineering and baseline_engineering != current_engineering),
            "worktree_dirty": bool(changes),
            "changes": changes,
            "change_counts": {kind: sum(1 for row in changes if row["kind"] == kind) for kind in ("MODIFY", "ADD", "DELETE", "RENAME", "UNTRACKED")},
            "authority_linked_change_count": sum(1 for row in changes if row.get("linked_to_engineering_authority")),
        }
        snapshot["snapshot_sha256"] = _sha(snapshot)
        return snapshot

    @staticmethod
    def _classify(snapshot: dict[str, Any]) -> tuple[str, list[str]]:
        current = dict(snapshot.get("current") or {})
        relation = str(snapshot.get("head_relation") or "")
        changes = list(snapshot.get("changes") or [])
        kinds = {str(row.get("kind")) for row in changes}
        linked = int(snapshot.get("authority_linked_change_count") or 0)
        reasons: list[str] = []
        if current.get("detached"):
            return "READ_ONLY_BLOCK", ["DETACHED_HEAD"]
        if relation in {"UNRELATED_OR_BASELINE_MISSING", "BASELINE_HEAD_INVALID"}:
            return "READ_ONLY_BLOCK", ["BASELINE_HEAD_NOT_RESOLVABLE"]
        if relation == "DIVERGED":
            return "MANUAL_RECONCILIATION_REQUIRED", ["HEAD_DIVERGENCE"]
        if relation == "REWIND":
            return "REPLAN_REQUIRED", ["HEAD_REWIND_INVALIDATES_PREIMAGE"]
        if "DELETE" in kinds or "RENAME" in kinds:
            reasons.append("RENAME_OR_DELETE_REQUIRES_MANUAL_REVIEW")
        if snapshot.get("branch_switched") and (changes or relation not in {"SAME", "FAST_FORWARD"}):
            reasons.append("CONFLICTING_BRANCH_SWITCH")
        if reasons:
            return "MANUAL_RECONCILIATION_REQUIRED", reasons
        if linked:
            return "REPLAN_REQUIRED", ["ENGINEERING_AUTHORITY_FILE_CHANGED"]
        if snapshot.get("engineering_state_changed"):
            return "REPLAN_REQUIRED", ["ENGINEERING_STATE_BINDING_CHANGED"]
        if relation == "FAST_FORWARD":
            reasons.append("EXTERNAL_FAST_FORWARD")
        if snapshot.get("branch_switched"):
            reasons.append("BRANCH_SWITCH_REVALIDATION")
        if changes:
            reasons.append("EXTERNAL_WORKTREE_EDIT")
        if reasons:
            return "REVALIDATE", reasons
        return "NO_CONFLICT", ["SOURCE_AND_ENGINEERING_STATE_MATCH_BASELINE"]

    @staticmethod
    def _authority_invalidations(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        relation = str(snapshot.get("head_relation") or "")
        source_changed = relation not in {"SAME", "BASELINE_MISSING"} or bool(snapshot.get("changes")) or bool(snapshot.get("engineering_state_changed"))
        if not source_changed:
            return []
        reason = "SOURCE_OR_ENGINEERING_AUTHORITY_CHANGED"
        return [
            {"authority": "approval", "state": "STALE", "reason_code": reason, "auto_reuse": False},
            {"authority": "preimage", "state": "STALE", "reason_code": reason, "auto_reuse": False},
            {"authority": "plan", "state": "STALE", "reason_code": reason, "auto_reuse": False},
        ]

    def _report(
        self,
        *,
        snapshot: dict[str, Any],
        classification: str,
        reason_codes: list[str],
        recovery: dict[str, Any],
        authority_invalidations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if classification not in RECONCILIATION_CLASSES:
            raise ReconciliationStateError("invalid reconciliation classification")
        next_action = {
            "NO_CONFLICT": "CONTINUE_GOVERNED_WORKFLOW",
            "REVALIDATE": "REVALIDATE_CURRENT_AUTHORITY",
            "REPLAN_REQUIRED": "CREATE_NEW_PLAN_AND_APPROVAL",
            "MANUAL_RECONCILIATION_REQUIRED": "REVIEW_AND_RECONCILE_EXTERNALLY_WITHOUT_DESTRUCTIVE_GIT",
            "READ_ONLY_BLOCK": "RESTORE_REVIEWABLE_GIT_AUTHORITY",
        }[classification]
        plan = [
            "Review branch, HEAD relation and file-level drift before any governed mutation.",
            "Export or copy preserved draft references before intentionally discarding UX state.",
        ]
        if classification == "REVALIDATE":
            plan.append("Revalidate source identity and recapture/adopt a clean reviewed baseline explicitly.")
        elif classification == "REPLAN_REQUIRED":
            plan.append("Create a new plan/preimage/approval bound to the current source identity.")
        elif classification == "MANUAL_RECONCILIATION_REQUIRED":
            plan.append("Resolve rename/delete/divergence manually outside DevPilot; DevPilot will observe but never reset/rebase/overwrite it.")
        elif classification == "READ_ONLY_BLOCK":
            plan.append("Restore a non-detached, resolvable Git state or capture an initial baseline after review.")
        report = {
            "schema_id": REPORT_SCHEMA_ID,
            "schema_version": SCHEMA_VERSION,
            "classification": classification,
            "reason_codes": reason_codes,
            "risk": self._risk(classification),
            "recommended_next_action": next_action,
            "snapshot": snapshot,
            "authority_invalidations": authority_invalidations,
            "draft_recovery": {
                "draft_refs": list(recovery.get("draft_refs") or []),
                "drafts_preserved": True,
                "discard_performed": False,
                "copy_or_export_before_discard": True,
            },
            "pending_recovery_work": list(recovery.get("pending_work") or []),
            "safe_recovery_plan": plan,
            "forbidden_automatic_git_operations": ["hard-reset", "clean", "rebase", "destructive-checkout", "force-push", "silent-overwrite"],
            "safety": {
                "local_only": True,
                "network_used": False,
                "external_api_used": False,
                "secrets_exposed": False,
                "source_mutations_performed": False,
                "git_mutations_performed": False,
                "dry_run_default": True,
            },
        }
        report["report_sha256"] = _sha(report)
        return report

    @staticmethod
    def _risk(classification: str) -> str:
        return {
            "NO_CONFLICT": "LOW",
            "REVALIDATE": "LOW",
            "REPLAN_REQUIRED": "MEDIUM",
            "MANUAL_RECONCILIATION_REQUIRED": "HIGH",
            "READ_ONLY_BLOCK": "HIGH",
        }[classification]
