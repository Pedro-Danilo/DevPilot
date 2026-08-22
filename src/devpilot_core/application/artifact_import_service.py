from __future__ import annotations

import base64
import binascii
import difflib
import hashlib
import json
import os
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import SecretGuard
from devpilot_core.repo.git_adapter import GitAdapter
from devpilot_core.schemas.validator import SchemaValidator

from .artifact_lifecycle_service import ArtifactLifecycleService
from .workspace_documents_service import WorkspaceDocumentsApplicationService

DEFAULT_IMPORT_ROOT = Path("outputs/imports/gsdlc_04_c")
MAX_IMPORT_BYTES = 1_048_576
ALLOWED_IMPORT_EXTENSIONS = {".md", ".json"}
ALLOWED_SOURCE_TYPES = {"PASTE", "UPLOAD", "IMPORT"}
ALLOWED_MIME_BY_EXTENSION = {
    ".md": {"text/markdown", "text/plain"},
    ".json": {"application/json", "text/json", "text/plain"},
}
_WINDOWS_DEVICE = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.IGNORECASE)
_DRIVE = re.compile(r"^[A-Za-z]:")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class PreparedImport:
    source_type: str
    workspace_id: str
    workspace_root: Path
    relative_path: str
    extension: str
    original_filename: str | None
    declared_mime: str | None
    original_size_bytes: int
    source_label: str | None
    source_reference: str | None
    original_sha256: str
    normalized_sha256: str
    encoding: str
    normalized_content: str
    destination_exists: bool
    destination_preimage_sha256: str | None
    diff: str
    preview_sha256: str
    secret_warning: bool
    secret_rule_id: str


class ArtifactImportApplicationService:
    """GSDLC-04-C runtime import boundary.

    PASTE/UPLOAD/IMPORT inputs are validated, normalized and previewed before any
    persistence. Persist writes only a runtime-ephemeral import DRAFT under
    ``outputs/imports/gsdlc_04_c``. It never writes the workspace destination,
    never fetches source_reference URLs and never grants APPROVED/FROZEN status.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        documents: WorkspaceDocumentsApplicationService,
        lifecycle: ArtifactLifecycleService | None = None,
        import_root: Path = DEFAULT_IMPORT_ROOT,
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.documents = documents
        self.lifecycle = lifecycle or ArtifactLifecycleService(self.platform_root)
        self.import_root = self.platform_root / import_root
        self.secret_guard = SecretGuard(self.platform_root)
        self.schemas = SchemaValidator(self.platform_root)
        self._lock = threading.RLock()

    def preview(
        self,
        *,
        source_type: str,
        destination_path: str,
        actor: str,
        actor_role: str,
        session_principal: str,
        source_label: str | None = None,
        source_reference: str | None = None,
        original_filename: str | None = None,
        declared_mime: str | None = None,
        text_content: str | None = None,
        content_base64: str | None = None,
    ) -> CommandResult:
        command = "workspace artifact import preview"
        prepared = self._prepare(
            command=command,
            source_type=source_type,
            destination_path=destination_path,
            actor=actor,
            actor_role=actor_role,
            session_principal=session_principal,
            source_label=source_label,
            source_reference=source_reference,
            original_filename=original_filename,
            declared_mime=declared_mime,
            text_content=text_content,
            content_base64=content_base64,
        )
        if isinstance(prepared, CommandResult):
            return prepared
        data = self._preview_payload(prepared)
        findings = [
            Finding(
                "GSDLC04C_IMPORT_PREVIEW_PASS",
                "External source passed bounded local preview; no workspace/source write occurred.",
                Severity.INFO,
                path=prepared.relative_path,
            )
        ]
        if prepared.secret_warning:
            findings.append(
                Finding(
                    "GSDLC04C_SECRET_WARNING",
                    "Secret-like content was detected. Preview is redacted and DRAFT persistence is blocked until the source is redacted.",
                    Severity.WARNING,
                    path=prepared.relative_path,
                    metadata={"rule_id": prepared.secret_rule_id, "secret_value_exposed": False},
                )
            )
        return CommandResult(command, True, ExitCode.PASS, "External source preview generated without persistence or network access.", data=data, findings=findings)

    def persist(
        self,
        *,
        source_type: str,
        destination_path: str,
        expected_preview_sha256: str,
        actor: str,
        actor_role: str,
        session_principal: str,
        source_label: str | None = None,
        source_reference: str | None = None,
        original_filename: str | None = None,
        declared_mime: str | None = None,
        text_content: str | None = None,
        content_base64: str | None = None,
    ) -> CommandResult:
        command = "workspace artifact import persist"
        if not _SHA256.fullmatch(str(expected_preview_sha256 or "")):
            return self._block(command, "GSDLC04C_PREVIEW_HASH_REQUIRED_BLOCK", "An exact preview SHA-256 is required before import persistence.")
        prepared = self._prepare(
            command=command,
            source_type=source_type,
            destination_path=destination_path,
            actor=actor,
            actor_role=actor_role,
            session_principal=session_principal,
            source_label=source_label,
            source_reference=source_reference,
            original_filename=original_filename,
            declared_mime=declared_mime,
            text_content=text_content,
            content_base64=content_base64,
        )
        if isinstance(prepared, CommandResult):
            return prepared
        if prepared.preview_sha256 != expected_preview_sha256:
            return self._block(
                command,
                "GSDLC04C_PREVIEW_STALE_BLOCK",
                "Import input changed after preview; generate a new preview before persisting.",
                metadata={"expected_preview_sha256": expected_preview_sha256, "current_preview_sha256": prepared.preview_sha256},
            )
        if prepared.secret_warning:
            return self._block(command, "GSDLC04C_SECRET_IMPORT_BLOCK", "Secret-like content must be redacted before it can be persisted as an import DRAFT.")

        base_commit = self._base_commit(prepared.workspace_root)
        artifact_id = f"artifact_{prepared.normalized_sha256[:24]}"
        lifecycle = self.lifecycle.create_draft(
            artifact_id=artifact_id,
            relative_path=prepared.relative_path,
            content=prepared.normalized_content,
            source_type=prepared.source_type,
            base_commit=base_commit,
            actor=actor,
            actor_role=actor_role,
            session_principal=session_principal,
            reviewer=actor,
            reviewer_role=actor_role,
            source_label=prepared.source_label,
            source_reference=prepared.source_reference,
        )
        if not lifecycle.ok:
            return CommandResult(command, False, lifecycle.exit_code, "Artifact lifecycle/provenance rejected the import DRAFT.", data=lifecycle.data, findings=lifecycle.findings)

        timestamp = _now()
        import_id = f"imp_{prepared.preview_sha256[:32]}"
        record = {
            "schema_id": "devpilot.gsdlc04c.artifact_import_record.v1",
            "import_id": import_id,
            "workspace_id": prepared.workspace_id,
            "relative_path": prepared.relative_path,
            "extension": prepared.extension,
            "source_type": prepared.source_type,
            "lifecycle_state": "DRAFT",
            "original_filename": prepared.original_filename,
            "declared_mime": prepared.declared_mime,
            "original_size_bytes": prepared.original_size_bytes,
            "source_label": prepared.source_label,
            "source_reference": prepared.source_reference,
            "original_sha256": prepared.original_sha256,
            "normalized_sha256": prepared.normalized_sha256,
            "encoding": prepared.encoding,
            "normalized_content": prepared.normalized_content,
            "destination_exists": prepared.destination_exists,
            "destination_preimage_sha256": prepared.destination_preimage_sha256,
            "preview_sha256": prepared.preview_sha256,
            "diff": prepared.diff,
            "artifact": lifecycle.data["artifact"],
            "created_at": timestamp,
            "updated_at": timestamp,
            "source_mutations_performed": False,
            "workspace_writes_performed": False,
            "runtime_store_write": True,
            "network_used": False,
            "external_api_used": False,
            "secret_warning": False,
        }
        validation = self.schemas.validate_payload(
            schema="SCHEMA-DEVPL-GSDLC-04-C-ARTIFACT-IMPORT-RECORD-V1",
            payload=record,
            instance_label=f"runtime-import:{prepared.workspace_id}:{import_id}",
        )
        if not validation.ok:
            return self._block(command, "GSDLC04C_IMPORT_RECORD_SCHEMA_BLOCK", "Generated import DRAFT failed its registered JSON Schema.")
        lifecycle_validation = self.lifecycle.validate_record(record["artifact"])
        if not lifecycle_validation.ok:
            return CommandResult(command, False, lifecycle_validation.exit_code, "Generated lifecycle record failed validation.", data=lifecycle_validation.data, findings=lifecycle_validation.findings)

        with self._lock:
            path = self._record_path(prepared.workspace_id, import_id)
            if path.exists():
                try:
                    existing = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    return self._block(command, "GSDLC04C_IMPORT_STORE_CORRUPT_BLOCK", "Existing runtime import record is unreadable; persistence fails closed.")
                if existing == record:
                    pass
                elif existing.get("preview_sha256") == prepared.preview_sha256 and existing.get("normalized_sha256") == prepared.normalized_sha256:
                    record = existing
                else:
                    return self._block(command, "GSDLC04C_IMPORT_ID_COLLISION_BLOCK", "Runtime import identity collision detected; persistence fails closed.")
            else:
                self._write_record(path, record)

        return CommandResult(
            command,
            True,
            ExitCode.PASS,
            "External source persisted as runtime DRAFT with provenance; workspace source remains unchanged.",
            data={"import": record, "preview": self._preview_payload(prepared), "summary": self._summary(prepared, import_id=import_id, persisted=True)},
            findings=[Finding("GSDLC04C_IMPORT_DRAFT_PERSIST_PASS", "Import is DRAFT-only and provenance-bearing; no workspace source write occurred.", Severity.INFO, path=prepared.relative_path)],
        )

    def recent(self, *, limit: int = 20) -> CommandResult:
        command = "workspace artifact imports recent"
        context = self.documents.context_resolver.resolve()
        if not context.configured or not context.valid or context.active_workspace_root is None or not context.active_workspace_id:
            return self._block(command, "GSDLC04C_PROJECT_CONTEXT_REQUIRED_BLOCK", "Artifact import requires a valid project-scoped active workspace context.")
        safe_limit = max(1, min(int(limit), 50))
        directory = self._workspace_store_dir(context.active_workspace_id)
        records: list[dict[str, Any]] = []
        if directory.exists():
            for path in sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime_ns, reverse=True)[:safe_limit]:
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    return self._block(command, "GSDLC04C_IMPORT_STORE_CORRUPT_BLOCK", "Runtime import record is unreadable; listing fails closed.")
                validation = self.schemas.validate_payload(schema="SCHEMA-DEVPL-GSDLC-04-C-ARTIFACT-IMPORT-RECORD-V1", payload=payload, instance_label=str(path))
                if not validation.ok:
                    return self._block(command, "GSDLC04C_IMPORT_STORE_SCHEMA_BLOCK", "Runtime import record failed schema validation; listing fails closed.")
                records.append({k: payload.get(k) for k in ("import_id", "relative_path", "source_type", "lifecycle_state", "original_sha256", "normalized_sha256", "source_label", "source_reference", "created_at")})
        return CommandResult(command, True, ExitCode.PASS, "Recent runtime import DRAFTs loaded.", data={"imports": records, "summary": {"workspace_id": context.active_workspace_id, "returned_total": len(records), "runtime_only": True, "source_mutations_performed": False, "network_used": False, "external_api_used": False}}, findings=[])

    def _prepare(
        self,
        *,
        command: str,
        source_type: str,
        destination_path: str,
        actor: str,
        actor_role: str,
        session_principal: str,
        source_label: str | None,
        source_reference: str | None,
        original_filename: str | None,
        declared_mime: str | None,
        text_content: str | None,
        content_base64: str | None,
    ) -> PreparedImport | CommandResult:
        normalized_type = str(source_type or "").strip().upper()
        if normalized_type not in ALLOWED_SOURCE_TYPES:
            return self._block(command, "GSDLC04C_SOURCE_TYPE_BLOCK", "Import source type must be PASTE, UPLOAD or IMPORT.")
        if not actor.strip() or not actor_role.strip() or not session_principal.strip():
            return self._block(command, "GSDLC04C_SESSION_ACTOR_REQUIRED_BLOCK", "Authenticated actor, canonical role and session principal are required.")
        context = self.documents.context_resolver.resolve()
        if not context.configured or not context.valid or context.active_workspace_root is None or not context.active_workspace_id:
            return self._block(command, "GSDLC04C_PROJECT_CONTEXT_REQUIRED_BLOCK", "Artifact import requires a valid project-scoped active workspace context.")
        workspace_root = context.active_workspace_root.resolve()
        relative = self._safe_destination(workspace_root, destination_path)
        if isinstance(relative, CommandResult):
            return relative
        extension = PurePosixPath(relative).suffix.lower()
        if extension not in ALLOWED_IMPORT_EXTENSIONS:
            return self._block(command, "GSDLC04C_EXTENSION_BLOCK", "Only Markdown (.md) and JSON (.json) imports are allowed in GSDLC-04-C.", metadata={"extension": extension})

        filename = self._safe_filename(original_filename) if original_filename else None
        if isinstance(filename, CommandResult):
            return filename
        if normalized_type in {"UPLOAD", "IMPORT"} and not filename:
            return self._block(command, "GSDLC04C_FILENAME_REQUIRED_BLOCK", "UPLOAD/IMPORT requires a safe original filename.")
        if filename and Path(filename).suffix.lower() not in ALLOWED_IMPORT_EXTENSIONS:
            return self._block(command, "GSDLC04C_UPLOAD_EXTENSION_BLOCK", "Uploaded/imported filename extension is not allowlisted.", metadata={"filename": filename})
        mime = _optional(declared_mime)
        if normalized_type == "PASTE" and mime is not None:
            return self._block(command, "GSDLC04C_PASTE_MIME_BLOCK", "PASTE does not accept a declared file MIME authority.")
        if normalized_type in {"UPLOAD", "IMPORT"} and mime:
            file_extension = Path(filename or "").suffix.lower()
            if mime.lower() not in ALLOWED_MIME_BY_EXTENSION.get(file_extension, set()):
                return self._block(
                    command,
                    "GSDLC04C_MIME_MISMATCH_BLOCK",
                    "Declared MIME type does not match the allowlisted document extension.",
                    metadata={"extension": file_extension, "declared_mime": mime.lower()},
                )

        decoded = self._decode_input(normalized_type, text_content=text_content, content_base64=content_base64, command=command)
        if isinstance(decoded, CommandResult):
            return decoded
        raw, encoding, text = decoded
        if len(raw) > MAX_IMPORT_BYTES:
            return self._block(command, "GSDLC04C_OVERSIZE_BLOCK", "Import exceeds the server-side 1 MiB limit.", metadata={"size_bytes": len(raw), "max_bytes": MAX_IMPORT_BYTES})
        if b"\x00" in raw and encoding == "utf-8":
            return self._block(command, "GSDLC04C_BINARY_BLOCK", "Binary-like uploads are not accepted as governed text artifacts.")
        normalized_content = text.replace("\r\n", "\n").replace("\r", "\n")
        if extension == ".json":
            try:
                json.loads(normalized_content)
            except json.JSONDecodeError as exc:
                return self._block(command, "GSDLC04C_JSON_SYNTAX_BLOCK", "Imported JSON must be syntactically valid before DRAFT persistence.", metadata={"line": exc.lineno, "column": exc.colno})

        original_sha = hashlib.sha256(raw).hexdigest()
        normalized_bytes = normalized_content.encode("utf-8")
        normalized_sha = hashlib.sha256(normalized_bytes).hexdigest()
        target = workspace_root / Path(relative)
        destination_exists = target.is_file()
        destination_preimage = None
        existing_text = ""
        if target.exists():
            if target.is_symlink():
                return self._block(command, "GSDLC04C_SYMLINK_BLOCK", "Destination is a symlink/reparse-like path; import fails closed.")
            if not target.is_file():
                return self._block(command, "GSDLC04C_DESTINATION_TYPE_BLOCK", "Destination exists but is not a regular file.")
            try:
                existing_raw = target.read_bytes()
                existing_text = existing_raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
                destination_preimage = hashlib.sha256(existing_raw).hexdigest()
            except (OSError, UnicodeDecodeError):
                return self._block(command, "GSDLC04C_DESTINATION_READ_BLOCK", "Existing destination could not be safely read as UTF-8 text.")

        secret = self.secret_guard.scan_text(normalized_content, subject=relative)
        secret_warning = secret.effect.value == "block"
        diff = ""
        if not secret_warning:
            diff = "".join(difflib.unified_diff(existing_text.splitlines(True), normalized_content.splitlines(True), fromfile=f"a/{relative}" if destination_exists else "/dev/null", tofile=f"b/{relative}", n=3))
            diff = diff[:65536]
        preview_material = {
            "source_type": normalized_type,
            "workspace_id": context.active_workspace_id,
            "relative_path": relative,
            "original_filename": filename,
            "declared_mime": mime,
            "source_label": _optional(source_label),
            "source_reference": _optional(source_reference),
            "original_sha256": original_sha,
            "normalized_sha256": normalized_sha,
            "destination_preimage_sha256": destination_preimage,
            "secret_warning": secret_warning,
        }
        preview_sha = hashlib.sha256(json.dumps(preview_material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
        return PreparedImport(
            source_type=normalized_type,
            workspace_id=context.active_workspace_id,
            workspace_root=workspace_root,
            relative_path=relative,
            extension=extension,
            original_filename=filename,
            declared_mime=mime,
            original_size_bytes=len(raw),
            source_label=_optional(source_label),
            source_reference=_optional(source_reference),
            original_sha256=original_sha,
            normalized_sha256=normalized_sha,
            encoding=encoding,
            normalized_content=normalized_content,
            destination_exists=destination_exists,
            destination_preimage_sha256=destination_preimage,
            diff=diff,
            preview_sha256=preview_sha,
            secret_warning=secret_warning,
            secret_rule_id=str(secret.rule_id or "SECRETGUARD_PASS"),
        )

    def _decode_input(self, source_type: str, *, text_content: str | None, content_base64: str | None, command: str) -> tuple[bytes, str, str] | CommandResult:
        if source_type == "PASTE":
            if content_base64 not in {None, ""}:
                return self._block(command, "GSDLC04C_PASTE_BINARY_BLOCK", "PASTE accepts text only; base64 upload data is not allowed.")
            text = str(text_content or "")
            raw = text.encode("utf-8")
            if not raw:
                return self._block(command, "GSDLC04C_EMPTY_SOURCE_BLOCK", "Import content cannot be empty.")
            return raw, "utf-8", text
        if text_content not in {None, ""}:
            return self._block(command, "GSDLC04C_UPLOAD_TEXT_AMBIGUOUS_BLOCK", "UPLOAD/IMPORT accepts encoded file bytes only; do not send a second text authority.")
        if not content_base64:
            return self._block(command, "GSDLC04C_UPLOAD_CONTENT_REQUIRED_BLOCK", "UPLOAD/IMPORT requires base64-encoded file bytes.")
        try:
            raw = base64.b64decode(content_base64, validate=True)
        except (binascii.Error, ValueError):
            return self._block(command, "GSDLC04C_BASE64_BLOCK", "Uploaded/imported content is not valid base64.")
        if not raw:
            return self._block(command, "GSDLC04C_EMPTY_SOURCE_BLOCK", "Import content cannot be empty.")
        if len(raw) > MAX_IMPORT_BYTES:
            return self._block(command, "GSDLC04C_OVERSIZE_BLOCK", "Import exceeds the server-side 1 MiB limit.", metadata={"size_bytes": len(raw), "max_bytes": MAX_IMPORT_BYTES})
        if raw.startswith(b"\xef\xbb\xbf"):
            try: return raw, "utf-8-sig", raw.decode("utf-8-sig")
            except UnicodeDecodeError: pass
        if raw.startswith(b"\xff\xfe"):
            try: return raw, "utf-16-le-bom", raw[2:].decode("utf-16-le")
            except UnicodeDecodeError: pass
        if raw.startswith(b"\xfe\xff"):
            try: return raw, "utf-16-be-bom", raw[2:].decode("utf-16-be")
            except UnicodeDecodeError: pass
        try:
            return raw, "utf-8", raw.decode("utf-8")
        except UnicodeDecodeError:
            return self._block(command, "GSDLC04C_ENCODING_BLOCK", "Only UTF-8 or BOM-qualified UTF-16 text imports are accepted.")

    def _safe_destination(self, root: Path, value: str) -> str | CommandResult:
        command = "workspace artifact import"
        raw = str(value or "").strip().replace("\\", "/")
        if not raw or raw.startswith(("/", "//")) or _DRIVE.match(raw) or "\x00" in raw:
            return self._block(command, "GSDLC04C_PATH_BLOCK", "Destination must be a relative workspace path.")
        path = PurePosixPath(raw)
        if any(part in {"", ".", ".."} for part in path.parts):
            return self._block(command, "GSDLC04C_TRAVERSAL_BLOCK", "Destination path traversal is not allowed.")
        for part in path.parts:
            if ":" in part or _WINDOWS_DEVICE.fullmatch(part.rstrip(" .")):
                return self._block(command, "GSDLC04C_WINDOWS_PATH_BLOCK", "Windows ADS/device names are not allowed in artifact destinations.")
        candidate = root.joinpath(*path.parts)
        # Inspect lexical parents before resolving so symlink/reparse traversal is
        # classified explicitly instead of being collapsed into a generic path escape.
        current = root
        for part in path.parts[:-1]:
            current = current / part
            if current.exists() and current.is_symlink():
                return self._block(command, "GSDLC04C_SYMLINK_BLOCK", "Destination traverses a symlink/reparse-like directory.")
        if candidate.exists() and candidate.is_symlink():
            return self._block(command, "GSDLC04C_SYMLINK_BLOCK", "Destination is a symlink/reparse-like path; import fails closed.")
        try:
            candidate.resolve(strict=False).relative_to(root.resolve())
        except ValueError:
            return self._block(command, "GSDLC04C_PATH_ESCAPE_BLOCK", "Destination escapes the authorized workspace root.")
        return str(path)

    def _safe_filename(self, value: str | None) -> str | CommandResult:
        command = "workspace artifact import"
        raw = str(value or "").strip()
        if not raw or raw in {".", ".."} or "/" in raw or "\\" in raw or ":" in raw or "\x00" in raw:
            return self._block(command, "GSDLC04C_FILENAME_BLOCK", "Upload filename must be a simple basename without path, ADS or traversal syntax.")
        if _WINDOWS_DEVICE.fullmatch(raw.rstrip(" .")):
            return self._block(command, "GSDLC04C_WINDOWS_DEVICE_BLOCK", "Windows reserved device filenames are not accepted.")
        if len(raw) > 128:
            return self._block(command, "GSDLC04C_FILENAME_LENGTH_BLOCK", "Upload filename exceeds 128 characters.")
        return raw

    def _preview_payload(self, prepared: PreparedImport) -> dict[str, Any]:
        preview_content = "[REDACTED: secret-like content detected]" if prepared.secret_warning else prepared.normalized_content
        diff = "[REDACTED: secret-like content detected]" if prepared.secret_warning else prepared.diff
        return {
            "preview": {
                "preview_sha256": prepared.preview_sha256,
                "source_type": prepared.source_type,
                "relative_path": prepared.relative_path,
                "extension": prepared.extension,
                "original_filename": prepared.original_filename,
                "declared_mime": prepared.declared_mime,
                "original_size_bytes": prepared.original_size_bytes,
                "encoding": prepared.encoding,
                "source_label": prepared.source_label,
                "source_reference": prepared.source_reference,
                "original_sha256": prepared.original_sha256,
                "normalized_sha256": prepared.normalized_sha256,
                "destination_exists": prepared.destination_exists,
                "destination_preimage_sha256": prepared.destination_preimage_sha256,
                "normalized_content": preview_content,
                "diff": diff,
                "secret_warning": prepared.secret_warning,
                "secret_values_exposed": False,
            },
            "summary": self._summary(prepared, persisted=False),
        }

    def _summary(self, prepared: PreparedImport, *, import_id: str | None = None, persisted: bool) -> dict[str, Any]:
        return {
            "workspace_id": prepared.workspace_id,
            "import_id": import_id,
            "source_type": prepared.source_type,
            "lifecycle_state": "DRAFT",
            "preview_generated": True,
            "persisted_runtime_draft": persisted,
            "source_mutations_performed": False,
            "workspace_writes_performed": False,
            "writes_outside_authorized_runtime_store": 0,
            "network_used": False,
            "external_api_used": False,
            "url_fetch_performed": False,
            "allowlisted_extensions": sorted(ALLOWED_IMPORT_EXTENSIONS),
            "max_import_bytes": MAX_IMPORT_BYTES,
            "secret_warning": prepared.secret_warning,
        }

    def _workspace_store_dir(self, workspace_id: str) -> Path:
        token = hashlib.sha256(workspace_id.encode("utf-8")).hexdigest()[:20]
        return self.import_root / token

    def _record_path(self, workspace_id: str, import_id: str) -> Path:
        return self._workspace_store_dir(workspace_id) / f"{import_id}.json"

    def _write_record(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        os.replace(tmp, path)

    @staticmethod
    def _base_commit(root: Path) -> str:
        result = GitAdapter(root).log(limit=1)
        if result.ok:
            commits = result.data.get("commits", []) if isinstance(result.data, dict) else []
            if commits and isinstance(commits[0], dict):
                value = str(commits[0].get("commit") or "")
                if re.fullmatch(r"[0-9a-f]{40}", value):
                    return value
        return "0" * 40

    @staticmethod
    def _block(command: str, finding_id: str, message: str, *, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"summary": {"source_mutations_performed": False, "workspace_writes_performed": False, "network_used": False, "external_api_used": False}}, findings=[Finding(finding_id, message, Severity.BLOCK, metadata=metadata or {})])


def _optional(value: str | None) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
