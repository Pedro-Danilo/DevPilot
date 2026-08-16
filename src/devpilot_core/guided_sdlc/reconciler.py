from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping, Sequence

from .models import (
    ArtifactLifecycleStatus,
    EngineeringLifecycleStatus,
    RevalidationStatus,
    WorkspaceEngineeringState,
    contains_secret_like_material,
)
from .repository import WorkspaceEngineeringStateRepository


RECONCILIATION_SCHEMA_ID = "SCHEMA-DEVPL-GUIDED-SDLC-RECONCILIATION-REPORT-V1"
RECONCILIATION_SCHEMA_VERSION = "1.0"

_ALLOWED_GIT_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("rev-parse", "HEAD"),
    ("branch", "--show-current"),
    ("status", "--porcelain=v1", "--untracked-files=normal"),
    ("diff", "--name-status", "-M"),
    ("diff", "--cached", "--name-status", "-M"),
)
_FORBIDDEN_GIT_TOKENS = {
    "reset", "checkout", "restore", "clean", "rebase", "merge", "stash", "add", "commit",
}
_REVALIDATION_ARTIFACT_LIFECYCLES = {
    ArtifactLifecycleStatus.APPROVED.value,
    ArtifactLifecycleStatus.FROZEN.value,
}


class ReconciliationError(RuntimeError):
    pass


class GitObservationError(ReconciliationError):
    pass


@dataclass(frozen=True)
class ReconciliationLimits:
    max_governed_files: int = 512
    max_file_bytes: int = 16 * 1024 * 1024
    git_timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        if self.max_governed_files < 1 or self.max_governed_files > 10000:
            raise ReconciliationError("max_governed_files must be within 1..10000")
        if self.max_file_bytes < 1 or self.max_file_bytes > 1024 * 1024 * 1024:
            raise ReconciliationError("max_file_bytes must be within 1 byte..1 GiB")
        if self.git_timeout_seconds <= 0 or self.git_timeout_seconds > 60:
            raise ReconciliationError("git_timeout_seconds must be within (0, 60]")


@dataclass(frozen=True)
class GitObservation:
    head: str
    branch: str
    dirty: bool
    status_lines: tuple[str, ...]
    rename_pairs: tuple[tuple[str, str], ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "head": self.head,
            "branch": self.branch,
            "dirty": self.dirty,
            "status_lines": list(self.status_lines),
            "rename_pairs": [{"old": old, "new": new} for old, new in self.rename_pairs],
        }


@dataclass(frozen=True)
class DriftEntry:
    drift_id: str
    kind: str
    severity: str
    reason_code: str
    source_ref: str | None
    artifact_id: str | None
    old_fingerprint: str | None
    new_fingerprint: str | None
    required_revalidation: bool
    recommended_recovery: str
    source_refs: tuple[str, ...]
    metadata: Mapping[str, Any]

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "drift_id": self.drift_id,
            "kind": self.kind,
            "severity": self.severity,
            "reason_code": self.reason_code,
            "source_ref": self.source_ref,
            "artifact_id": self.artifact_id,
            "old_fingerprint": self.old_fingerprint,
            "new_fingerprint": self.new_fingerprint,
            "required_revalidation": self.required_revalidation,
            "recommended_recovery": self.recommended_recovery,
            "source_refs": list(self.source_refs),
            "metadata": dict(self.metadata),
        }
        findings = contains_secret_like_material(payload)
        if findings:
            raise ReconciliationError(f"secret-like material forbidden in reconciliation drift entry: {findings[:5]}")
        return payload


@dataclass(frozen=True)
class ReconciliationReport:
    workspace_id: str
    project_id: str
    decision: str
    drift_entries: tuple[DriftEntry, ...]
    prior_git: Mapping[str, Any]
    observed_git: GitObservation
    required_revalidation: bool
    source_refs: tuple[str, ...]
    mutation_declaration: Mapping[str, Any]
    schema_id: str = RECONCILIATION_SCHEMA_ID
    schema_version: str = RECONCILIATION_SCHEMA_VERSION

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "decision": self.decision,
            "drift_entries": [row.to_payload() for row in self.drift_entries],
            "prior_git": dict(self.prior_git),
            "observed_git": self.observed_git.to_payload(),
            "required_revalidation": self.required_revalidation,
            "source_refs": list(self.source_refs),
            "mutation_declaration": dict(self.mutation_declaration),
            "network_used": False,
            "external_api_used": False,
            "source_mutations_performed": False,
        }
        findings = contains_secret_like_material(payload)
        if findings:
            raise ReconciliationError(f"secret-like material forbidden in ReconciliationReport: {findings[:5]}")
        return payload

    def fingerprint(self) -> str:
        raw = json.dumps(self.to_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReconciliationResult:
    report: ReconciliationReport
    current_state: WorkspaceEngineeringState
    successor_state: WorkspaceEngineeringState
    state_changed: bool
    state_persisted: bool

    def to_payload(self) -> dict[str, Any]:
        return {
            "report": self.report.to_payload(),
            "current_state_fingerprint": self.current_state.fingerprint(),
            "successor_state": self.successor_state.to_payload(),
            "successor_state_fingerprint": self.successor_state.fingerprint(),
            "state_changed": self.state_changed,
            "state_persisted": self.state_persisted,
        }


class ReadOnlyGitObserver:
    """Bounded Git observer.

    Only a fixed allow-list of read operations can be executed. Any command with
    a destructive/mutating token is rejected before subprocess invocation.
    """

    def __init__(
        self,
        *,
        timeout_seconds: float = 5.0,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.runner = runner
        self.commands_executed: list[tuple[str, ...]] = []

    def _run(self, workspace_root: Path, args: Sequence[str]) -> str:
        normalized = tuple(str(x) for x in args)
        if any(token in _FORBIDDEN_GIT_TOKENS for token in normalized):
            raise GitObservationError(f"mutating/destructive Git command is forbidden: {normalized}")
        allowed = normalized in _ALLOWED_GIT_COMMANDS or (
            len(normalized) == 4
            and normalized[:3] == ("diff", "--name-status", "-M")
            and normalized[3].count("..") == 1
        )
        if not allowed:
            raise GitObservationError(f"Git observation command is not allow-listed: {normalized}")
        cmd = ["git", *normalized]
        self.commands_executed.append(tuple(cmd))
        try:
            cp = self.runner(
                cmd,
                cwd=str(workspace_root),
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise GitObservationError(f"Git observation timed out after {self.timeout_seconds}s: {normalized}") from exc
        except OSError as exc:
            raise GitObservationError(f"Git observation failed to start: {exc}") from exc
        if cp.returncode != 0:
            raise GitObservationError(
                f"Git observation failed rc={cp.returncode}: {normalized}; stderr={(cp.stderr or '').strip()[:512]}"
            )
        return cp.stdout

    def observe(self, workspace_root: Path, prior_head: str | None = None) -> GitObservation:
        root = Path(workspace_root).resolve()
        head = self._run(root, ("rev-parse", "HEAD")).strip()
        branch = self._run(root, ("branch", "--show-current")).strip()
        status = self._run(root, ("status", "--porcelain=v1", "--untracked-files=normal"))
        working_diff = self._run(root, ("diff", "--name-status", "-M"))
        staged_diff = self._run(root, ("diff", "--cached", "--name-status", "-M"))
        rename_pairs = list(_parse_renames(working_diff)) + list(_parse_renames(staged_diff))
        if prior_head and prior_head != head:
            committed_diff = self._run(root, ("diff", "--name-status", "-M", f"{prior_head}..{head}"))
            rename_pairs.extend(_parse_renames(committed_diff))
        return GitObservation(
            head=head,
            branch=branch,
            dirty=bool(status.strip()),
            status_lines=tuple(line[:1024] for line in status.splitlines() if line.strip()),
            rename_pairs=tuple(sorted(set(rename_pairs))),
        )


def _parse_renames(text: str) -> Iterable[tuple[str, str]]:
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0].startswith("R"):
            yield parts[-2].replace("\\", "/"), parts[-1].replace("\\", "/")


def _stable_drift_id(kind: str, source_ref: str | None, artifact_id: str | None, old: str | None, new: str | None) -> str:
    raw = "|".join(str(x or "") for x in (kind, source_ref, artifact_id, old, new))
    return "drift-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _git_fingerprint(observed: GitObservation) -> str:
    raw = json.dumps(
        {
            "head": observed.head,
            "branch": observed.branch,
            "dirty": observed.dirty,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class WorkspaceReconciler:
    """Deterministic filesystem/Git reconciliation for a registered workspace.

    Inspection is read-only. `execute=True` is implemented by GuidedSDLCService
    and may persist only the successor WorkspaceEngineeringState via its atomic
    repository; this reconciler never writes to managed workspace source.
    """

    def __init__(
        self,
        repository: WorkspaceEngineeringStateRepository,
        *,
        limits: ReconciliationLimits | None = None,
        git_observer: ReadOnlyGitObserver | None = None,
    ) -> None:
        self.repository = repository
        self.limits = limits or ReconciliationLimits()
        self.git_observer = git_observer or ReadOnlyGitObserver(timeout_seconds=self.limits.git_timeout_seconds)

    def inspect(self, state: WorkspaceEngineeringState, *, updated_at_utc: str) -> ReconciliationResult:
        binding = self.repository.binding(state.workspace_id)
        if state.project_id != binding.project_id or state.workspace_root_fingerprint != binding.root_fingerprint:
            raise ReconciliationError("engineering state does not match registered workspace binding")

        governed_refs = self._governed_refs(state)
        if len(governed_refs) > self.limits.max_governed_files:
            raise ReconciliationError(
                f"governed artifact count {len(governed_refs)} exceeds max_governed_files={self.limits.max_governed_files}"
            )

        prior_head = _optional_text(state.git.get("head"))
        observed_git = self.git_observer.observe(binding.root, prior_head=prior_head)
        drifts: list[DriftEntry] = []
        prior_branch = _optional_text(state.git.get("branch"))

        if prior_head and observed_git.head != prior_head:
            drifts.append(self._drift(
                kind="HEAD_CHANGE", severity="BLOCK", reason_code="GIT_HEAD_CHANGED",
                source_ref=None, artifact_id=None, old=prior_head, new=observed_git.head,
                recovery="Review external commit(s), reconcile affected governed artifacts, then revalidate.",
                metadata={},
            ))
        if prior_branch and observed_git.branch != prior_branch:
            drifts.append(self._drift(
                kind="BRANCH_SWITCH", severity="BLOCK", reason_code="GIT_BRANCH_CHANGED",
                source_ref=None, artifact_id=None, old=prior_branch, new=observed_git.branch,
                recovery="Review the branch switch and confirm the intended branch before revalidation.",
                metadata={},
            ))
        if observed_git.dirty:
            drifts.append(self._drift(
                kind="DIRTY_WORKSPACE", severity="WARN", reason_code="GIT_WORKTREE_DIRTY",
                source_ref=None, artifact_id=None, old="clean", new="dirty",
                recovery="Review working-tree changes; do not auto-reset or discard them.",
                metadata={"status_entries": len(observed_git.status_lines)},
            ))

        artifact_by_ref = {
            str(row.get("source_ref")): dict(row)
            for row in state.artifacts
            if row.get("source_ref")
        }
        source_fp = {
            str(row.get("source_ref")): str(row.get("sha256"))
            for row in state.source_fingerprints
            if row.get("source_ref") and row.get("sha256")
        }
        rename_map = dict(observed_git.rename_pairs)

        changed_artifacts: set[str] = set()
        for ref in governed_refs:
            prior = source_fp.get(ref)
            artifact = artifact_by_ref.get(ref)
            artifact_id = str(artifact.get("artifact_id")) if artifact else None
            if ref in rename_map:
                drifts.append(self._drift(
                    kind="RENAME", severity="BLOCK", reason_code="GOVERNED_ARTIFACT_RENAMED",
                    source_ref=ref, artifact_id=artifact_id, old=prior, new=None,
                    recovery="Review and explicitly rebind the governed artifact to the new path; history is preserved.",
                    metadata={"renamed_to": rename_map[ref]},
                ))
                if artifact_id:
                    changed_artifacts.add(artifact_id)

            path = self._safe_governed_path(binding.root, ref)
            if not path.exists():
                drifts.append(self._drift(
                    kind="MISSING_ARTIFACT", severity="BLOCK", reason_code="GOVERNED_ARTIFACT_MISSING",
                    source_ref=ref, artifact_id=artifact_id, old=prior, new=None,
                    recovery="Restore or explicitly replace the governed artifact, then revalidate.",
                    metadata={},
                ))
                if artifact_id:
                    changed_artifacts.add(artifact_id)
                continue
            if not path.is_file():
                raise ReconciliationError(f"governed source_ref is not a regular file: {ref}")
            size = path.stat().st_size
            if size > self.limits.max_file_bytes:
                raise ReconciliationError(
                    f"governed file exceeds max_file_bytes={self.limits.max_file_bytes}: {ref}"
                )
            current = _sha256_path(path)
            if prior and current != prior:
                lifecycle = str((artifact or {}).get("lifecycle") or "")
                kind = "APPROVED_ARTIFACT_DRIFT" if lifecycle in _REVALIDATION_ARTIFACT_LIFECYCLES else "EXTERNAL_EDIT"
                reason = "APPROVED_ARTIFACT_HASH_CHANGED" if kind == "APPROVED_ARTIFACT_DRIFT" else "SOURCE_FINGERPRINT_CHANGED"
                severity = "BLOCK" if kind == "APPROVED_ARTIFACT_DRIFT" else "WARN"
                drifts.append(self._drift(
                    kind=kind, severity=severity, reason_code=reason,
                    source_ref=ref, artifact_id=artifact_id, old=prior, new=current,
                    recovery="Review the external edit and rerun the governed validation/approval path.",
                    metadata={"prior_lifecycle": lifecycle or None},
                ))
                if artifact_id:
                    changed_artifacts.add(artifact_id)
            elif not prior and artifact and artifact.get("fingerprint") and current != artifact.get("fingerprint"):
                drifts.append(self._drift(
                    kind="STALE_SOURCE_FINGERPRINT", severity="WARN", reason_code="ARTIFACT_FINGERPRINT_CHANGED",
                    source_ref=ref, artifact_id=artifact_id, old=str(artifact.get("fingerprint")), new=current,
                    recovery="Reconcile the artifact fingerprint through the governed revalidation path.",
                    metadata={"prior_lifecycle": artifact.get("lifecycle")},
                ))
                if artifact_id:
                    changed_artifacts.add(artifact_id)

        drifts = sorted(drifts, key=lambda row: (
            {"BLOCK": 0, "WARN": 1, "INFO": 2}.get(row.severity, 9),
            row.reason_code,
            row.source_ref or "",
            row.artifact_id or "",
            row.drift_id,
        ))
        existing_required = state.lifecycle_status == EngineeringLifecycleStatus.REVALIDATION_REQUIRED or state.revalidation.get("status") in {
            RevalidationStatus.REQUIRED.value,
            RevalidationStatus.IN_PROGRESS.value,
        }
        required = bool(drifts) or existing_required
        successor = self._successor_state(
            state,
            observed_git=observed_git,
            drifts=drifts,
            changed_artifacts=changed_artifacts,
            updated_at_utc=updated_at_utc,
        )
        state_changed = successor.fingerprint() != state.fingerprint()
        decision = "REVALIDATION_REQUIRED" if required else "NO_DRIFT"
        report = ReconciliationReport(
            workspace_id=state.workspace_id,
            project_id=state.project_id,
            decision=decision,
            drift_entries=tuple(drifts),
            prior_git=dict(state.git),
            observed_git=observed_git,
            required_revalidation=required,
            source_refs=tuple(sorted(governed_refs)),
            mutation_declaration={
                "filesystem_source_written": False,
                "git_mutating_command_executed": False,
                "engineering_state_save_allowed": True,
                "engineering_state_saved": False,
            },
        )
        return ReconciliationResult(
            report=report,
            current_state=state,
            successor_state=successor,
            state_changed=state_changed,
            state_persisted=False,
        )

    def _governed_refs(self, state: WorkspaceEngineeringState) -> list[str]:
        refs = {
            str(row.get("source_ref"))
            for row in state.source_fingerprints
            if row.get("source_ref")
        }
        refs.update(
            str(row.get("source_ref"))
            for row in state.artifacts
            if row.get("source_ref")
        )
        return sorted(refs)

    def _safe_governed_path(self, root: Path, source_ref: str) -> Path:
        normalized = source_ref.replace("\\", "/")
        pure = PurePosixPath(normalized)
        if pure.is_absolute() or ".." in pure.parts or not pure.parts:
            raise ReconciliationError(f"governed source_ref escapes workspace boundary: {source_ref}")
        candidate = Path(root)
        for part in pure.parts:
            candidate = candidate / part
            if candidate.exists() and candidate.is_symlink():
                raise ReconciliationError(f"governed source_ref contains symlink component: {source_ref}")
        try:
            resolved = candidate.resolve(strict=False)
            resolved.relative_to(Path(root).resolve())
        except ValueError as exc:
            raise ReconciliationError(f"governed source_ref escapes registered workspace: {source_ref}") from exc
        return resolved

    def _drift(
        self,
        *,
        kind: str,
        severity: str,
        reason_code: str,
        source_ref: str | None,
        artifact_id: str | None,
        old: str | None,
        new: str | None,
        recovery: str,
        metadata: Mapping[str, Any],
    ) -> DriftEntry:
        return DriftEntry(
            drift_id=_stable_drift_id(kind, source_ref, artifact_id, old, new),
            kind=kind,
            severity=severity,
            reason_code=reason_code,
            source_ref=source_ref,
            artifact_id=artifact_id,
            old_fingerprint=old,
            new_fingerprint=new,
            required_revalidation=True,
            recommended_recovery=recovery,
            source_refs=tuple(x for x in (source_ref,) if x),
            metadata=dict(metadata),
        )

    def _successor_state(
        self,
        state: WorkspaceEngineeringState,
        *,
        observed_git: GitObservation,
        drifts: Sequence[DriftEntry],
        changed_artifacts: set[str],
        updated_at_utc: str,
    ) -> WorkspaceEngineeringState:
        existing_required = state.lifecycle_status == EngineeringLifecycleStatus.REVALIDATION_REQUIRED or state.revalidation.get("status") in {
            RevalidationStatus.REQUIRED.value,
            RevalidationStatus.IN_PROGRESS.value,
        }
        if not drifts and not existing_required:
            return state

        reasons = sorted({
            *(str(x) for x in state.revalidation.get("reason_codes", []) if x),
            *(row.reason_code for row in drifts),
        })
        artifacts: list[dict[str, Any]] = []
        for row in state.artifacts:
            item = dict(row)
            if str(item.get("artifact_id")) in changed_artifacts and str(item.get("lifecycle")) in _REVALIDATION_ARTIFACT_LIFECYCLES:
                item["lifecycle"] = ArtifactLifecycleStatus.REVALIDATION_REQUIRED.value
            artifacts.append(item)

        new_git = {
            "head": observed_git.head,
            "branch": observed_git.branch,
            "dirty": observed_git.dirty,
            "fingerprint": _git_fingerprint(observed_git),
        }
        return replace(
            state,
            lifecycle_status=EngineeringLifecycleStatus.REVALIDATION_REQUIRED,
            sequence=state.sequence + 1,
            updated_at_utc=updated_at_utc,
            git=new_git,
            artifacts=tuple(artifacts),
            revalidation={
                "status": RevalidationStatus.REQUIRED.value,
                "reason_codes": reasons or ["EXISTING_REVALIDATION_REQUIRED"],
            },
        )


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
