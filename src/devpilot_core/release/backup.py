from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, SecretGuard
from devpilot_core.policy.decisions import PolicyEffect

_BACKUP_ID_RE = re.compile(r"^backup-\d{8}T\d{6}Z-[0-9a-f]{8}$")

_DEFAULT_INCLUDE_PATTERNS: tuple[str, ...] = (
    ".devpilot/project.yaml",
    ".devpilot/policy.yaml",
    ".devpilot/providers.yaml",
    ".devpilot/providers.yaml.example",
    ".devpilot/devpilot.db",
    ".devpilot/miasi/agent_registry.json",
    ".devpilot/miasi/tool_registry.json",
    ".devpilot/miasi/policy_matrix.json",
    ".devpilot/execution/command_allowlist.json",
    ".devpilot/testing/test_profiles.json",
)

_FORBIDDEN_PREFIXES: tuple[str, ...] = (
    ".git/",
    ".venv/",
    "node_modules/",
    "outputs/",
    "dist/",
    "__pycache__/",
    ".pytest_cache/",
)

_BINARY_SUFFIXES = {".db", ".sqlite", ".sqlite3"}


@dataclass(frozen=True)
class BackupCreateOptions:
    """Options for FUNC-SPRINT-83 local backup creation.

    Backup creation is dry-run by default. Passing ``execute=True`` writes a
    local ZIP plus a JSON sidecar manifest under ``.devpilot/backups``. Secret
    looking textual content is redacted before being placed in the backup.
    """

    dry_run: bool = True
    execute: bool = False
    include_sqlite_state: bool = True
    redact_secrets: bool = True


@dataclass(frozen=True)
class BackupListOptions:
    """Options for listing local backup sidecar manifests."""

    limit: int = 50


@dataclass(frozen=True)
class BackupRestoreOptions:
    """Options for restoring a local backup.

    Restore is dry-run by default. A real restore requires both ``execute=True``
    and ``confirm_restore=True``. This deliberately prevents accidental
    overwrites while still allowing a controlled local recovery path.
    """

    backup_id: str
    dry_run: bool = True
    execute: bool = False
    confirm_restore: bool = False


class BackupCreateBuilder:
    """Create a governed backup plan or backup artifact for local state."""

    def __init__(self, root: Path, *, options: BackupCreateOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()

    def build(self) -> CommandResult:
        execute = bool(self.options.execute)
        dry_run = not execute or bool(self.options.dry_run and not execute)
        candidates = self._collect_candidates()
        findings: list[Finding] = []
        entries: list[dict[str, Any]] = []
        redactions_total = 0

        for relative_path in candidates:
            absolute = self.root / relative_path
            decision = self.path_guard.evaluate(relative_path, action="read")
            if decision.effect == PolicyEffect.BLOCK:
                findings.append(decision.to_finding())
                continue
            if not absolute.exists() or not absolute.is_file():
                entries.append(
                    {
                        "path": relative_path,
                        "exists": False,
                        "included": False,
                        "reason": "missing",
                    }
                )
                continue
            if _is_forbidden_path(relative_path):
                findings.append(
                    Finding(
                        "BACKUP_FORBIDDEN_PATH_EXCLUDED",
                        "Backup excluded a forbidden runtime/cache/build path.",
                        Severity.WARNING,
                        path=relative_path,
                    )
                )
                entries.append(
                    {
                        "path": relative_path,
                        "exists": True,
                        "included": False,
                        "reason": "forbidden-path",
                    }
                )
                continue

            size_bytes = absolute.stat().st_size
            entry: dict[str, Any] = {
                "path": relative_path,
                "exists": True,
                "included": True,
                "size_bytes": size_bytes,
                "binary": _is_binary_like(absolute),
                "redacted": False,
            }
            if entry["binary"]:
                if execute:
                    entry["sha256"] = _sha256_file(absolute)
                else:
                    entry["sha256"] = None
                    entry["sha256_computed"] = False
                    entry["reason"] = "hash-skipped-in-dry-run"
            else:
                text = absolute.read_text(encoding="utf-8", errors="replace")
                redacted_result = self.secret_guard.redact(text)
                if redacted_result.changed:
                    redactions_total += redacted_result.redactions
                    entry["redacted"] = True
                    entry["redactions"] = redacted_result.redactions
                    findings.append(
                        Finding(
                            "BACKUP_SECRET_REDACTED",
                            "SecretGuard redacted secret-like textual content before backup packaging.",
                            Severity.WARNING,
                            path=relative_path,
                            metadata={"redactions": redacted_result.redactions, "raw_secret_not_stored": True},
                        )
                    )
                entry["sha256"] = hashlib.sha256(str(redacted_result.value if redacted_result.changed else text).encode("utf-8")).hexdigest()
            entries.append(entry)

        included_entries = [entry for entry in entries if entry.get("included")]
        seed = "|".join(f"{entry['path']}:{entry.get('sha256', '')}" for entry in included_entries)
        backup_id = _backup_id(seed)
        backup_dir = self.root / ".devpilot" / "backups"
        backup_zip = backup_dir / f"{backup_id}.zip"
        backup_manifest = backup_dir / f"{backup_id}.manifest.json"

        security = _security_summary()
        summary = {
            "backup_id": backup_id,
            "schema_version": "1.0.0",
            "preliminary": True,
            "dry_run": dry_run,
            "execute_requested": execute,
            "backup_created": False,
            "backup_dir": _rel(backup_dir, self.root),
            "backup_zip": _rel(backup_zip, self.root),
            "backup_manifest": _rel(backup_manifest, self.root),
            "candidate_files_total": len(entries),
            "included_files_total": len(included_entries),
            "missing_files_total": len([entry for entry in entries if entry.get("reason") == "missing"]),
            "redactions_total": redactions_total,
            "sqlite_state_included": any(entry.get("path") == ".devpilot/devpilot.db" and entry.get("included") for entry in entries),
            "forbidden_defaults_excluded": True,
            **security,
        }
        manifest = {
            "schema_version": "1.0.0",
            "backup_id": backup_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "workspace_root_name": self.root.name,
            "entries": entries,
            "security": security,
            "restore_policy": {
                "dry_run_default": True,
                "execute_requires_confirm_restore": True,
                "overwrite_requires_explicit_execution": True,
            },
            "limitations": [
                "Secret-like textual values are redacted before being stored in backup artifacts.",
                "Restore is controlled and dry-run by default.",
                "The backup is a local safety baseline, not an encrypted offsite backup.",
            ],
        }

        if execute:
            write_decision = self.path_guard.evaluate(backup_zip, action="create")
            if not write_decision.ok:
                findings.append(write_decision.to_finding())
                return CommandResult(
                    command="backup create",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message="Backup creation blocked by PathGuard.",
                    data={"summary": summary, "backup_manifest": manifest},
                    findings=findings,
                )
            backup_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(backup_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for entry in included_entries:
                    src = self.root / str(entry["path"])
                    if entry.get("binary"):
                        zf.write(src, _zip_name(str(entry["path"])))
                    else:
                        text = src.read_text(encoding="utf-8", errors="replace")
                        redacted_result = self.secret_guard.redact(text)
                        stored = str(redacted_result.value) if redacted_result.changed else text
                        zf.writestr(_zip_name(str(entry["path"])), stored)
                zf.writestr("backup_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
            manifest["artifact"] = {
                "zip": _rel(backup_zip, self.root),
                "manifest": _rel(backup_manifest, self.root),
                "zip_sha256": _sha256_file(backup_zip),
                "zip_size_bytes": backup_zip.stat().st_size,
            }
            backup_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
            summary["backup_created"] = True
            summary["zip_sha256"] = manifest["artifact"]["zip_sha256"]
            findings.append(
                Finding(
                    "BACKUP_CREATED",
                    "Local backup artifact and sidecar manifest were created under .devpilot/backups.",
                    Severity.INFO,
                    path=_rel(backup_zip, self.root),
                )
            )
        else:
            findings.append(
                Finding(
                    "BACKUP_DRY_RUN",
                    "Backup create ran in dry-run mode; no backup artifact was written.",
                    Severity.INFO,
                    metadata={"execute_to_create": True},
                )
            )

        return CommandResult(
            command="backup create",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local backup plan generated." if dry_run else "Local backup created.",
            data={"summary": summary, "backup_manifest": manifest},
            findings=findings,
        )

    def _collect_candidates(self) -> list[str]:
        selected: list[str] = []
        for item in _DEFAULT_INCLUDE_PATTERNS:
            if item == ".devpilot/devpilot.db" and not self.options.include_sqlite_state:
                continue
            if (self.root / item).exists():
                selected.append(item)
        # Keep the allowlist intentionally narrow; Sprint 83 protects local state,
        # not arbitrary repository content.
        return sorted(dict.fromkeys(selected))


class BackupListBuilder:
    """List local backups without extracting or mutating them."""

    def __init__(self, root: Path, *, options: BackupListOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options

    def build(self) -> CommandResult:
        backup_dir = self.root / ".devpilot" / "backups"
        manifests: list[dict[str, Any]] = []
        for manifest_path in sorted(backup_dir.glob("*.manifest.json"), reverse=True):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception as exc:  # pragma: no cover - defensive only
                manifests.append({"path": _rel(manifest_path, self.root), "read_error": str(exc)})
                continue
            artifact = manifest.get("artifact") or {}
            entries = manifest.get("entries") or []
            manifests.append(
                {
                    "backup_id": manifest.get("backup_id"),
                    "created_at_utc": manifest.get("created_at_utc"),
                    "zip": artifact.get("zip"),
                    "manifest": _rel(manifest_path, self.root),
                    "zip_sha256": artifact.get("zip_sha256"),
                    "entries_total": len(entries),
                    "redacted_entries_total": len([entry for entry in entries if entry.get("redacted")]),
                }
            )
        limit = max(1, min(int(self.options.limit), 500))
        backups = manifests[:limit]
        return CommandResult(
            command="backup list",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local backup catalog listed.",
            data={
                "summary": {
                    "backups_total": len(manifests),
                    "returned_total": len(backups),
                    "backup_dir": _rel(backup_dir, self.root),
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                "backups": backups,
            },
            findings=[],
        )


class BackupRestoreBuilder:
    """Plan or execute a controlled restore from one local backup."""

    def __init__(self, root: Path, *, options: BackupRestoreOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options
        self.path_guard = PathGuard(self.root)

    def build(self) -> CommandResult:
        backup_id = self.options.backup_id.strip()
        if not _BACKUP_ID_RE.match(backup_id):
            return CommandResult(
                command="backup restore",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Backup restore failed because the backup id is invalid.",
                data={"summary": {"backup_id": backup_id, "valid_backup_id": False, "preliminary": True}},
                findings=[Finding("BACKUP_ID_INVALID", "Backup id does not match the expected local backup id format.", Severity.ERROR)],
            )

        backup_dir = self.root / ".devpilot" / "backups"
        manifest_path = backup_dir / f"{backup_id}.manifest.json"
        zip_path = backup_dir / f"{backup_id}.zip"
        if not manifest_path.exists() or not zip_path.exists():
            return CommandResult(
                command="backup restore",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Backup restore blocked because the requested backup artifact is missing.",
                data={
                    "summary": {
                        "backup_id": backup_id,
                        "manifest_exists": manifest_path.exists(),
                        "zip_exists": zip_path.exists(),
                        "preliminary": True,
                    }
                },
                findings=[Finding("BACKUP_NOT_FOUND", "Requested backup manifest or ZIP artifact was not found.", Severity.BLOCK)],
            )

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        restore_entries = self._inspect_zip(zip_path)
        findings: list[Finding] = []
        if any(entry.get("blocked") for entry in restore_entries):
            findings.append(
                Finding(
                    "BACKUP_RESTORE_UNSAFE_ENTRY",
                    "Restore blocked because at least one backup entry is unsafe or outside the allowed local state boundary.",
                    Severity.BLOCK,
                    metadata={"blocked_entries": [entry for entry in restore_entries if entry.get("blocked")][:20]},
                )
            )
            ok = False
            exit_code = ExitCode.BLOCK
        else:
            ok = True
            exit_code = ExitCode.PASS

        execute = bool(self.options.execute)
        dry_run = not execute or bool(self.options.dry_run and not execute)
        if execute and not self.options.confirm_restore:
            findings.append(
                Finding(
                    "BACKUP_RESTORE_CONFIRMATION_REQUIRED",
                    "A real restore requires --execute and --confirm-restore to make overwrites explicit.",
                    Severity.BLOCK,
                )
            )
            ok = False
            exit_code = ExitCode.BLOCK

        restored_total = 0
        if ok and execute and self.options.confirm_restore:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for entry in restore_entries:
                    if entry["path"] == "backup_manifest.json":
                        continue
                    target = self.root / entry["path"]
                    decision = self.path_guard.evaluate(target, action="write")
                    if not decision.ok:
                        findings.append(decision.to_finding())
                        ok = False
                        exit_code = ExitCode.BLOCK
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(zf.read(entry["zip_name"]))
                    restored_total += 1
            if ok:
                findings.append(
                    Finding(
                        "BACKUP_RESTORED",
                        "Backup was restored after explicit execution and confirmation.",
                        Severity.INFO,
                        metadata={"restored_total": restored_total},
                    )
                )
        elif ok:
            findings.append(
                Finding(
                    "BACKUP_RESTORE_DRY_RUN",
                    "Backup restore ran in dry-run mode; no files were overwritten.",
                    Severity.INFO,
                    metadata={"execute_requires_confirm_restore": True},
                )
            )

        summary = {
            "backup_id": backup_id,
            "preliminary": True,
            "dry_run": dry_run,
            "execute_requested": execute,
            "confirm_restore": self.options.confirm_restore,
            "restore_performed": restored_total > 0,
            "restored_files_total": restored_total,
            "restore_entries_total": len([entry for entry in restore_entries if entry["path"] != "backup_manifest.json"]),
            "blocked_entries_total": len([entry for entry in restore_entries if entry.get("blocked")]),
            "source_backup_zip": _rel(zip_path, self.root),
            "source_manifest": _rel(manifest_path, self.root),
            "network_used": False,
            "external_api_used": False,
            "publishes_artifacts": False,
            "deploys_artifacts": False,
            "git_tagging_performed": False,
            "restore_overwrites_require_confirmation": True,
        }
        return CommandResult(
            command="backup restore",
            ok=ok,
            exit_code=exit_code,
            message="Backup restore plan generated." if dry_run else ("Backup restored." if ok else "Backup restore blocked."),
            data={"summary": summary, "restore_plan": restore_entries, "backup_manifest": manifest},
            findings=findings,
        )

    def _inspect_zip(self, zip_path: Path) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                name = info.filename.replace("\\", "/")
                normalized = str(PurePosixPath(name))
                blocked = False
                reason = None
                if normalized.startswith("../") or normalized.startswith("/") or ".." in PurePosixPath(normalized).parts:
                    blocked = True
                    reason = "path-traversal"
                elif normalized != "backup_manifest.json" and not normalized.startswith(".devpilot/"):
                    blocked = True
                    reason = "outside-devpilot-local-state"
                elif _is_forbidden_path(normalized):
                    blocked = True
                    reason = "forbidden-path"
                entries.append(
                    {
                        "zip_name": info.filename,
                        "path": normalized,
                        "size_bytes": info.file_size,
                        "blocked": blocked,
                        "block_reason": reason,
                        "will_overwrite": normalized != "backup_manifest.json" and (self.root / normalized).exists(),
                    }
                )
        return entries


def _backup_id(seed: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(f"{now}:{seed}".encode("utf-8")).hexdigest()[:8]
    return f"backup-{now}-{digest}"


def _security_summary() -> dict[str, Any]:
    return {
        "network_used": False,
        "external_api_used": False,
        "publishes_artifacts": False,
        "deploys_artifacts": False,
        "git_tagging_performed": False,
        "source_mutations_performed": False,
        "caches_excluded_by_default": True,
        "outputs_excluded_by_default": True,
        "venv_excluded_by_default": True,
        "git_dir_excluded_by_default": True,
        "secrets_redacted_by_default": True,
    }


def _rel(path: Path, root: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _zip_name(relative_path: str) -> str:
    return str(PurePosixPath(relative_path.replace("\\", "/")))


def _is_forbidden_path(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    return any(normalized.startswith(prefix) for prefix in _FORBIDDEN_PREFIXES)


def _is_binary_like(path: Path) -> bool:
    return path.suffix.lower() in _BINARY_SUFFIXES


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
