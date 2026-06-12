from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from devpilot_core.changes.models import RollbackOperation, RollbackPlan, RollbackPoint, build_rollback_id, file_fingerprint
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.policy import PolicyEngine, PolicyRequest, SecretGuard, redact_sensitive_data
from devpilot_core.store import LocalStore
from devpilot_core.store.local_store import utc_now_iso


class RollbackManager:
    """Manage local rollback plans and backup points for controlled changes.

    Purpose:
        FUNC-SPRINT-42 creates a local rollback metadata and backup layer that
        starts from sandbox ChangeSets. It prepares future execution flows
        without enabling unrestricted productive workspace mutation.

    Functioning:
        The manager reads a ChangeSet JSON, validates workspace-local paths,
        creates a rollback plan, stores file backups under a runtime-only
        `.devpilot/rollback/backups/<rollback_id>/` folder when safe, persists
        a rollback point manifest under `.devpilot/rollback/points/`, and
        exposes read-only list/show commands.

    Integration:
        CLI entrypoints: `rollback plan`, `rollback list`, `rollback show` and
        `rollback execute`. The execute command is approval-gated and remains
        non-mutating in this initial sprint.

    Safety:
        Runtime rollback data is excluded from release ZIPs and Git by
        `.gitignore`. Backups are blocked when a target file contains
        secret-like content; DevPilot does not silently copy secrets into
        rollback storage.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.runtime_root = self.root / ".devpilot" / "rollback"
        self.points_dir = self.runtime_root / "points"
        self.backups_dir = self.runtime_root / "backups"

    def create_plan_from_file(self, changeset_file: str | Path, *, persist: bool = True, backup: bool = True) -> CommandResult:
        changeset_rel, changeset_path, error = self._resolve_changeset_file(changeset_file)
        if error is not None:
            return error
        try:
            changeset = json.loads(changeset_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return CommandResult(
                command="rollback plan",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Rollback plan could not parse the ChangeSet JSON file.",
                data={"summary": {"source": changeset_rel, "created": False, "preliminary": True}},
                findings=[Finding("ROLLBACK_CHANGESET_JSON_INVALID", str(exc), Severity.FAIL, path=changeset_rel)],
            )
        extracted = _extract_changeset_payload(changeset)
        if extracted is None:
            return CommandResult(
                command="rollback plan",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Rollback plan blocked a JSON file without a ChangeSet payload.",
                data={"summary": {"source": changeset_rel, "created": False, "preliminary": True}},
                findings=[Finding("ROLLBACK_CHANGESET_PAYLOAD_MISSING", "Expected a raw ChangeSet object or an evidence report with data.changeset.", Severity.BLOCK, path=changeset_rel)],
            )
        return self.create_plan_from_changeset(extracted, source=changeset_rel, persist=persist, backup=backup)

    def create_plan_from_changeset(self, changeset: dict[str, Any], *, source: str = "inline-changeset", persist: bool = True, backup: bool = True) -> CommandResult:
        validation_findings = _validate_changeset_shape(changeset, source)
        if any(f.severity in {Severity.BLOCK, Severity.FAIL, Severity.ERROR} for f in validation_findings):
            exit_code = exit_code_for_findings(validation_findings)
            return CommandResult(
                command="rollback plan",
                ok=False,
                exit_code=exit_code,
                message="Rollback plan blocked an invalid ChangeSet.",
                data={"summary": {"source": source, "created": False, "preliminary": True}},
                findings=validation_findings,
            )

        files = list(changeset.get("files") or [])
        rollback_id = build_rollback_id(
            changeset_id=str(changeset.get("changeset_id") or "changeset-unknown"),
            source=source,
            files=[str(file.get("path")) for file in files],
        )
        backup_dir = self.backups_dir / rollback_id
        operations: list[RollbackOperation] = []
        findings: list[Finding] = list(validation_findings)
        backed_up_files = 0
        max_backup_bytes = 1_000_000

        for file_entry in files:
            path = str(file_entry.get("path") or "").replace("\\", "/")
            action = str(file_entry.get("action") or "modify")
            target, path_error = self._workspace_file(path)
            if path_error is not None:
                findings.append(path_error)
                continue
            before_sha = file_entry.get("before_sha256")
            after_sha = file_entry.get("after_sha256")
            current_fp = file_fingerprint(target)
            backup_rel: str | None = None
            operation_action = _rollback_action_for(action)
            if action in {"modify", "delete"}:
                if current_fp is None:
                    findings.append(
                        Finding(
                            "ROLLBACK_TARGET_MISSING",
                            "Rollback plan could not back up a target file that is absent in the productive workspace.",
                            Severity.WARNING,
                            path=path,
                        )
                    )
                else:
                    if before_sha and current_fp.get("sha256") != before_sha:
                        findings.append(
                            Finding(
                                "ROLLBACK_SOURCE_HASH_MISMATCH",
                                "Productive file hash differs from ChangeSet before_sha256; rollback is still planned but must be reviewed before future execution.",
                                Severity.WARNING,
                                path=path,
                                metadata={"expected_before_sha256": before_sha, "actual_sha256": current_fp.get("sha256")},
                            )
                        )
                    size = int(current_fp.get("size_bytes") or 0)
                    if size > max_backup_bytes:
                        findings.append(
                            Finding(
                                "ROLLBACK_BACKUP_FILE_TOO_LARGE",
                                "Rollback backup is blocked for a file above the initial size limit.",
                                Severity.BLOCK,
                                path=path,
                                metadata={"size_bytes": size, "max_backup_bytes": max_backup_bytes},
                            )
                        )
                    elif _secret_decision_blocks(target, path):
                        findings.append(
                            Finding(
                                "ROLLBACK_BACKUP_SECRET_BLOCKED",
                                "Rollback backup blocked because target file contains secret-like content; no raw secret backup was written.",
                                Severity.BLOCK,
                                path=path,
                            )
                        )
                    elif backup:
                        backup_target = backup_dir / path
                        backup_target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(target, backup_target)
                        backup_rel = _relative(backup_target, self.root)
                        backed_up_files += 1
            elif action == "add":
                operation_action = "delete_created_file"
            else:
                findings.append(
                    Finding(
                        "ROLLBACK_ACTION_UNKNOWN",
                        "Rollback plan found an unknown ChangeSet action and marked it for manual review.",
                        Severity.WARNING,
                        path=path,
                        metadata={"action": action},
                    )
                )
                operation_action = "manual_review"

            operations.append(
                RollbackOperation(
                    path=path,
                    action=operation_action,
                    backup_path=backup_rel,
                    expected_current_sha256=str(after_sha) if after_sha else None,
                    restore_sha256=str(before_sha) if before_sha else None,
                    before_size_bytes=_optional_int(file_entry.get("before_size_bytes")),
                    after_size_bytes=_optional_int(file_entry.get("after_size_bytes")),
                    notes=_operation_notes(action=action, backup_path=backup_rel),
                )
            )

        if not operations:
            findings.append(Finding("ROLLBACK_PLAN_EMPTY", "Rollback plan contains no operations.", Severity.BLOCK, path=source))

        created_at = utc_now_iso()
        plan = RollbackPlan(
            rollback_id=rollback_id,
            changeset_id=str(changeset.get("changeset_id")),
            source_changeset=source,
            source_patch=str(changeset.get("source_patch") or ""),
            sandbox_id=str(changeset.get("sandbox_id") or ""),
            created_at=created_at,
            operations=tuple(operations),
            backups_dir=_relative(backup_dir, self.root),
            backup_available=backed_up_files > 0,
            approval_required_for_execute=True,
            execute_supported=False,
            metadata={
                "sprint": "FUNC-SPRINT-42",
                "component": "RollbackManager",
                "persist_requested": persist,
                "backup_requested": backup,
                "raw_file_contents_emitted": False,
                "network_used": False,
                "external_api_used": False,
            },
        )
        point = RollbackPoint(
            rollback_id=rollback_id,
            changeset_id=plan.changeset_id,
            created_at=created_at,
            status="planned",
            plan_path=_relative(self.points_dir / f"{rollback_id}.json", self.root),
            backups_dir=plan.backups_dir,
            files_total=len(operations),
            backup_available=plan.backup_available,
            execute_supported=False,
            metadata={"source_changeset": source, "preliminary": True},
        )

        persisted = False
        if persist and not any(f.severity in {Severity.BLOCK, Severity.ERROR} for f in findings):
            self.points_dir.mkdir(parents=True, exist_ok=True)
            (self.points_dir / f"{rollback_id}.json").write_text(
                json.dumps({"point": point.to_dict(), "plan": plan.to_dict()}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            persisted = True
            self._record_rollback_event(point)

        if not findings:
            findings.append(Finding("ROLLBACK_PLAN_CREATED", "Rollback plan and local backup metadata were created.", Severity.INFO, path=point.plan_path if persisted else source))
        exit_code = exit_code_for_findings(findings)
        return CommandResult(
            command="rollback plan",
            ok=exit_code == ExitCode.PASS,
            exit_code=exit_code,
            message="Rollback plan created." if exit_code == ExitCode.PASS else "Rollback plan completed with findings.",
            data=redact_sensitive_data(
                {
                    "summary": {
                        "source": source,
                        "rollback_id": rollback_id,
                        "created": exit_code == ExitCode.PASS,
                        "persisted": persisted,
                        "backup_available": plan.backup_available,
                        "backed_up_files": backed_up_files,
                        "operations_total": len(operations),
                        "execute_supported": False,
                        "approval_required_for_execute": True,
                        "runtime_root": _relative(self.runtime_root, self.root),
                        "network_used": False,
                        "external_api_used": False,
                        "preliminary": True,
                    },
                    "point": point.to_dict(),
                    "plan": plan.to_dict(),
                    "notes": [
                        "FUNC-SPRINT-42 creates rollback metadata and local backups only for controlled future flows.",
                        "rollback execute remains non-mutating and approval-gated in this initial implementation.",
                        "Rollback runtime data is excluded from Git/release ZIPs.",
                    ],
                }
            ),
            findings=findings,
        )

    def list(self, *, limit: int = 100) -> CommandResult:
        points = self._load_points(limit=limit)
        return CommandResult(
            command="rollback list",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Rollback points listed.",
            data={
                "summary": {
                    "points_total": len(points),
                    "limit": max(1, min(int(limit), 500)),
                    "runtime_root": _relative(self.runtime_root, self.root),
                    "read_only": True,
                    "preliminary": True,
                },
                "rollback_points": [point.to_dict() for point in points],
            },
            findings=[Finding("ROLLBACK_POINTS_LISTED", "Rollback points listed in read-only mode.", Severity.INFO, metadata={"points_total": len(points)})],
        )

    def show(self, rollback_id: str) -> CommandResult:
        safe_id = _safe_rollback_id(rollback_id)
        if safe_id is None:
            return CommandResult(
                command="rollback show",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Rollback show blocked an invalid rollback_id.",
                data={"summary": {"found": False, "read_only": True, "preliminary": True}},
                findings=[Finding("ROLLBACK_ID_INVALID", "rollback_id contains unsupported characters.", Severity.BLOCK)],
            )
        path = self.points_dir / f"{safe_id}.json"
        if not path.exists():
            return CommandResult(
                command="rollback show",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Rollback point was not found.",
                data={"summary": {"rollback_id": safe_id, "found": False, "read_only": True, "preliminary": True}},
                findings=[Finding("ROLLBACK_POINT_NOT_FOUND", "Rollback point does not exist.", Severity.FAIL, path=_relative(path, self.root))],
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        return CommandResult(
            command="rollback show",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Rollback point shown.",
            data=redact_sensitive_data({"summary": {"rollback_id": safe_id, "found": True, "read_only": True, "preliminary": True}, **payload}),
            findings=[Finding("ROLLBACK_POINT_SHOWN", "Rollback point loaded in read-only mode.", Severity.INFO, path=_relative(path, self.root))],
        )

    def execute(self, rollback_id: str, *, approval_id: str | None = None) -> CommandResult:
        safe_id = _safe_rollback_id(rollback_id)
        if safe_id is None:
            return CommandResult(
                command="rollback execute",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Rollback execute blocked an invalid rollback_id.",
                data={"summary": {"executed": False, "mutations_performed": False, "preliminary": True}},
                findings=[Finding("ROLLBACK_ID_INVALID", "rollback_id contains unsupported characters.", Severity.BLOCK)],
            )
        policy = PolicyEngine(self.root).evaluate(
            PolicyRequest(
                action="execute",
                path=".devpilot/rollback",
                dry_run=False,
                approval_id=approval_id,
                tool_id="rollback.execute",
                subject=safe_id,
                metadata={"sprint": "FUNC-SPRINT-42", "component": "RollbackManager"},
            )
        )
        if not policy.ok:
            return CommandResult(
                command="rollback execute",
                ok=False,
                exit_code=policy.exit_code,
                message="Rollback execute blocked because approval is missing or invalid.",
                data={"summary": {"rollback_id": safe_id, "executed": False, "mutations_performed": False, "approval_required": True, "preliminary": True}, "policy": policy.to_dict()},
                findings=policy.findings,
            )
        return CommandResult(
            command="rollback execute",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Rollback execute is approval-gated and intentionally non-mutating in FUNC-SPRINT-42.",
            data={"summary": {"rollback_id": safe_id, "executed": False, "mutations_performed": False, "approval_valid": True, "execute_supported": False, "preliminary": True}},
            findings=[Finding("ROLLBACK_EXECUTE_NOT_ENABLED", "Executable rollback is not enabled in FUNC-SPRINT-42; later sprints must add restore semantics and tests.", Severity.BLOCK, path=safe_id)],
        )

    def _resolve_changeset_file(self, changeset_file: str | Path) -> tuple[str, Path, CommandResult | None]:
        candidate = Path(changeset_file)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        display = _relative(candidate, self.root)
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return display, candidate, CommandResult(
                command="rollback plan",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Rollback plan blocked a ChangeSet path outside the workspace.",
                data={"summary": {"source": str(changeset_file), "created": False, "preliminary": True}},
                findings=[Finding("ROLLBACK_CHANGESET_OUTSIDE_ROOT", "ChangeSet path escapes workspace root.", Severity.BLOCK, path=str(changeset_file))],
            )
        policy = PolicyEngine(self.root).evaluate(PolicyRequest(action="read", path=display, dry_run=True, tool_id="rollback.plan", subject=display, metadata={"sprint": "FUNC-SPRINT-42"}))
        if not policy.ok:
            return display, candidate, CommandResult(
                command="rollback plan",
                ok=False,
                exit_code=policy.exit_code,
                message="Rollback plan blocked by policy before reading ChangeSet.",
                data={"summary": {"source": display, "created": False, "preliminary": True}, "policy": policy.to_dict()},
                findings=policy.findings,
            )
        if not candidate.exists() or not candidate.is_file():
            return display, candidate, CommandResult(
                command="rollback plan",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Rollback plan could not find the ChangeSet file.",
                data={"summary": {"source": display, "created": False, "preliminary": True}},
                findings=[Finding("ROLLBACK_CHANGESET_NOT_FOUND", "ChangeSet file does not exist.", Severity.FAIL, path=display)],
            )
        return display, candidate, None

    def _workspace_file(self, path: str) -> tuple[Path, Finding | None]:
        candidate = (self.root / path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return candidate, Finding("ROLLBACK_TARGET_OUTSIDE_ROOT", "Rollback target path escapes workspace root.", Severity.BLOCK, path=path)
        if path.startswith("outputs/") or "/__pycache__/" in f"/{path}/" or path.startswith(".git/") or path.startswith(".venv/"):
            return candidate, Finding("ROLLBACK_TARGET_RUNTIME_PATH_BLOCKED", "Rollback target is a runtime/cache path and cannot become a rollback point.", Severity.BLOCK, path=path)
        return candidate, None

    def _load_points(self, *, limit: int) -> list[RollbackPoint]:
        if not self.points_dir.exists():
            return []
        points: list[RollbackPoint] = []
        for path in sorted(self.points_dir.glob("rollback-*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[: max(1, min(int(limit), 500))]:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                point_payload = payload.get("point") or {}
                points.append(RollbackPoint.from_dict(point_payload))
            except Exception:
                continue
        return points

    def _record_rollback_event(self, point: RollbackPoint) -> None:
        try:
            LocalStore(self.root).record_event(
                event_type="rollback.point.created",
                command="rollback plan",
                status="PASS",
                ok=True,
                exit_code=0,
                subject=point.rollback_id,
                summary=point.to_dict(),
                metadata={"sprint": "FUNC-SPRINT-42", "component": "RollbackManager"},
            )
        except Exception:
            return



def _extract_changeset_payload(payload: Any) -> dict[str, Any] | None:
    """Accept either raw ChangeSet JSON or a DevPilot evidence report."""

    if not isinstance(payload, dict):
        return None
    if isinstance(payload.get("changeset_id"), str) and isinstance(payload.get("files"), list):
        return payload
    data = payload.get("data")
    if isinstance(data, dict) and isinstance(data.get("changeset"), dict):
        return data["changeset"]
    if isinstance(payload.get("changeset"), dict):
        return payload["changeset"]
    return None


def _validate_changeset_shape(changeset: dict[str, Any], source: str) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(changeset, dict):
        return [Finding("ROLLBACK_CHANGESET_INVALID", "ChangeSet must be a JSON object.", Severity.BLOCK, path=source)]
    if not changeset.get("changeset_id"):
        findings.append(Finding("ROLLBACK_CHANGESET_ID_MISSING", "ChangeSet is missing changeset_id.", Severity.BLOCK, path=source))
    if not isinstance(changeset.get("files"), list):
        findings.append(Finding("ROLLBACK_CHANGESET_FILES_MISSING", "ChangeSet is missing a files array.", Severity.BLOCK, path=source))
    return findings


def _rollback_action_for(action: str) -> str:
    if action == "add":
        return "delete_created_file"
    if action == "delete":
        return "restore_deleted_file_from_backup"
    if action == "modify":
        return "restore_modified_file_from_backup"
    return "manual_review"


def _operation_notes(*, action: str, backup_path: str | None) -> tuple[str, ...]:
    if action == "add":
        return ("Future rollback should delete the file created by the controlled apply flow.",)
    if backup_path:
        return ("Future rollback should restore this path from the local backup after verifying expected_current_sha256.",)
    return ("No local backup was written; future execution must require manual review.",)


def _secret_decision_blocks(path: Path, subject: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    return SecretGuard().scan_text(text, subject=subject).effect.value == "block"


def _optional_int(value: Any) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def _safe_rollback_id(value: str) -> str | None:
    value = str(value).strip()
    if not value or not value.startswith("rollback-"):
        return None
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    if any(char not in allowed for char in value):
        return None
    return value


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
