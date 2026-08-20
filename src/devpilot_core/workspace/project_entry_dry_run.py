from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import configured_external_workspace_roots
from devpilot_core.workspace.environment_discovery import DEFAULT_TIMEOUT_SECONDS, EnvironmentDiscoveryService
from devpilot_core.workspace.project_entry_contracts import GitSourceKind, ProjectEntryMode, ProjectIntake, stable_sha256

DRY_RUN_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-03-C-PROJECT-ENTRY-DRY-RUN-V1"
APPROVAL_PREVIEW_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-03-C-APPROVAL-PREVIEW-V1"
_MAX_INVENTORY_FILES = 250
_MAX_HASH_BYTES_PER_FILE = 1024 * 1024


class ProjectEntryDryRunService:
    """Read-only GSDLC-03-C preview boundary for Create/Open/Import.

    The service consumes the 03-B BootstrapPlan and adds a bounded preimage
    fingerprint, review projection and typed approval preview. It never creates
    target paths, clones Git, installs dependencies, requests approval or uses
    network.
    """

    def __init__(self, root: Path, *, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.root = Path(root).resolve()
        self.timeout_seconds = max(0.1, min(float(timeout_seconds), 15.0))
        self.planning = EnvironmentDiscoveryService(
            self.root,
            allowed_roots=configured_external_workspace_roots(),
            timeout_seconds=self.timeout_seconds,
        )

    def dry_run(self, *, intake: Mapping[str, Any]) -> CommandResult:
        planned = self.planning.build_bootstrap_plan({"intake": dict(intake)})
        if not planned.ok:
            return CommandResult(
                command="project entry dry-run",
                ok=False,
                exit_code=planned.exit_code,
                message="Dry-run blocked because planning/discovery did not pass.",
                data={"planning": planned.to_dict(), "writes_performed": False, "network_used": False},
                findings=planned.findings,
            )
        normalized = ProjectIntake.from_mapping(intake)
        plan = dict(planned.data["bootstrap_plan"])
        preimage = self._preimage(normalized, planned.data.get("discovery", {}))
        preview = self._approval_preview(normalized, plan, preimage)
        review = self._review_projection(normalized, plan, preimage, preview)
        body_without_hash = {
            "schema_id": DRY_RUN_SCHEMA_ID,
            "schema_version": "1.0",
            "dry_run_version": "1.0.0",
            "entry_mode": normalized.entry_mode.value,
            "project_id": normalized.project_id,
            "plan_hash": plan["plan_hash"],
            "preimage_hash": preimage["preimage_hash"],
            "preimage": preimage,
            "review": review,
            "approval_preview": preview,
            "execution": {"enabled": False, "reason": "Execution is deferred to DEVPL-GSDLC-03-D."},
            "safety": {
                "writes_performed": False,
                "network_used": False,
                "external_api_used": False,
                "remote_git_contacted": False,
                "approval_requested": False,
                "arbitrary_shell_used": False,
                "pilot_workspace_accessed": False,
                "credentials_included": False,
            },
        }
        dry_run = {**body_without_hash, "dry_run_hash": stable_sha256(body_without_hash)}
        return CommandResult(
            command="project entry dry-run",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Create/Open/Import dry-run generated for review; no project writes or network occurred.",
            data={"dry_run": dry_run, "bootstrap_plan": plan, "writes_performed": False, "network_used": False},
            findings=[Finding("PROJECT_ENTRY_DRY_RUN_PASS", "Dry-run is deterministic, reviewable and non-executable.", Severity.INFO)],
        )

    def revalidate(self, *, intake: Mapping[str, Any], expected_plan_hash: str, expected_preimage_hash: str) -> CommandResult:
        current = self.dry_run(intake=intake)
        if not current.ok:
            return current
        dry = current.data["dry_run"]
        plan_match = str(dry["plan_hash"]) == str(expected_plan_hash)
        preimage_match = str(dry["preimage_hash"]) == str(expected_preimage_hash)
        ok = plan_match and preimage_match
        finding = Finding(
            "PROJECT_ENTRY_PREIMAGE_REVALIDATION_PASS" if ok else "PROJECT_ENTRY_PREIMAGE_CHANGED_BLOCK",
            "Plan and preimage are unchanged." if ok else "Plan/preimage changed; future execute requires a new dry-run and approval.",
            Severity.INFO if ok else Severity.BLOCK,
            metadata={"plan_match": plan_match, "preimage_match": preimage_match},
        )
        return CommandResult(
            command="project entry revalidate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message=finding.message,
            data={
                "plan_match": plan_match,
                "preimage_match": preimage_match,
                "current_plan_hash": dry["plan_hash"],
                "current_preimage_hash": dry["preimage_hash"],
                "writes_performed": False,
                "network_used": False,
            },
            findings=[finding],
        )

    def _preimage(self, intake: ProjectIntake, discovery: Mapping[str, Any]) -> dict[str, Any]:
        target = Path(intake.target_root).expanduser().resolve(strict=False)
        source: Path | None = None
        if intake.entry_mode is ProjectEntryMode.IMPORT_GIT and intake.git_source_kind is GitSourceKind.LOCAL_PATH:
            source = Path(intake.git_source_location or "").expanduser().resolve(strict=False)
        if intake.entry_mode is ProjectEntryMode.CREATE_NEW:
            payload = {"mode": intake.entry_mode.value, "target": str(target), "target_exists": target.exists(), "collision_state": discovery.get("target", {}).get("collision_state")}
        elif intake.entry_mode is ProjectEntryMode.OPEN_EXISTING:
            payload = {"mode": intake.entry_mode.value, "target": str(target), "inventory": _bounded_inventory(target), "git": _safe_git_fingerprint(target, self.timeout_seconds)}
        elif source is not None:
            payload = {"mode": intake.entry_mode.value, "target": str(target), "source_kind": "local-path", "source": str(source), "source_inventory": _bounded_inventory(source), "git": _safe_git_fingerprint(source, self.timeout_seconds)}
        else:
            sanitized = str((discovery.get("git") or {}).get("source") or intake.git_source_location or "")
            payload = {"mode": intake.entry_mode.value, "target": str(target), "source_kind": "remote-url", "remote_source": sanitized, "network_contacted": False}
        return {"kind": "bounded-read-only", "payload": payload, "preimage_hash": stable_sha256(payload)}

    @staticmethod
    def _approval_preview(intake: ProjectIntake, plan: Mapping[str, Any], preimage: Mapping[str, Any]) -> dict[str, Any]:
        operation_ids = []
        for group in (plan.get("git_operations", []), plan.get("dependency_jobs", [])):
            for row in group:
                operation_ids.append(str(row.get("operation_id") or row.get("job_id") or ""))
        if plan.get("venv", {}).get("required"):
            operation_ids.append(str(plan["venv"].get("operation_id") or "python.venv.create"))
        registration = plan.get("workspace_registration") or {}
        if registration.get("operation_id"):
            operation_ids.append(str(registration["operation_id"]))
        return {
            "schema_id": APPROVAL_PREVIEW_SCHEMA_ID,
            "preview_only": True,
            "request_created": False,
            "actor_authority": "human-session",
            "tool_id": "project-bootstrap",
            "action": "execute-approved-plan",
            "subject": intake.project_id,
            "scope": {"entry_mode": intake.entry_mode.value, "target_root": intake.target_root},
            "plan_hash": plan["plan_hash"],
            "preimage_hash": preimage["preimage_hash"],
            "typed_operation_ids": sorted(x for x in set(operation_ids) if x),
            "network_required_by_plan": bool(plan.get("network", {}).get("required_by_plan")),
        }

    @staticmethod
    def _review_projection(intake: ProjectIntake, plan: Mapping[str, Any], preimage: Mapping[str, Any], approval: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "entry_mode": intake.entry_mode.value,
            "project_name": intake.project_name,
            "target_root": intake.target_root,
            "plan_hash": plan["plan_hash"],
            "preimage_hash": preimage["preimage_hash"],
            "directories_total": len(plan.get("directories", [])),
            "files_total": len(plan.get("files", [])),
            "git_operations": [row.get("operation_id") for row in plan.get("git_operations", [])],
            "dependency_jobs": [row.get("job_id") for row in plan.get("dependency_jobs", [])],
            "network_required_by_plan": bool(plan.get("network", {}).get("required_by_plan")),
            "runtime_network_used": False,
            "writes_performed": False,
            "approval_required": bool(plan.get("approval", {}).get("required_for_execute")),
            "approval_preview_hash": stable_sha256(approval),
        }


def _bounded_inventory(root: Path) -> dict[str, Any]:
    if not root.exists() or not root.is_dir():
        return {"exists": root.exists(), "files_total": 0, "entries": [], "truncated": False}
    rows: list[dict[str, Any]] = []
    truncated = False
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix().lower()):
        if path.is_symlink():
            continue
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/"):
            continue
        if len(rows) >= _MAX_INVENTORY_FILES:
            truncated = True
            break
        size = path.stat().st_size
        h = hashlib.sha256()
        with path.open("rb") as fh:
            remaining = _MAX_HASH_BYTES_PER_FILE
            while remaining > 0:
                chunk = fh.read(min(65536, remaining))
                if not chunk:
                    break
                h.update(chunk); remaining -= len(chunk)
        rows.append({"path": rel, "size": size, "sha256_prefix_1m": h.hexdigest(), "content_hash_truncated": size > _MAX_HASH_BYTES_PER_FILE})
    return {"exists": True, "files_total": len(rows), "entries": rows, "truncated": truncated}


def _safe_git_fingerprint(root: Path, timeout_seconds: float) -> dict[str, Any]:
    def run(args: list[str]) -> subprocess.CompletedProcess[bytes] | None:
        try:
            return subprocess.run(args, cwd=root, capture_output=True, timeout=timeout_seconds, shell=False, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
    inside = run(["git", "rev-parse", "--is-inside-work-tree"])
    if inside is None or inside.returncode != 0 or inside.stdout.strip() != b"true":
        return {"is_git": False, "head": None, "dirty": None, "status_entries_total": 0}
    head = run(["git", "rev-parse", "HEAD"])
    status = run(["git", "status", "--porcelain=v1", "-z"])
    payload = status.stdout if status and status.returncode == 0 else b""
    entries = [item for item in payload.split(b"\0") if item]
    return {"is_git": True, "head": head.stdout.decode("utf-8", "replace").strip() if head and head.returncode == 0 else None, "dirty": bool(entries), "status_entries_total": len(entries)}
