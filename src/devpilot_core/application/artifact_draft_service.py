from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import SecretGuard
from devpilot_core.repo.git_adapter import GitAdapter
from devpilot_core.schemas.validator import SchemaValidator

from .workspace_documents_service import WorkspaceDocumentsApplicationService

DEFAULT_DRAFT_ROOT = Path("outputs/drafts/gsdlc_04_b")
MAX_REVISIONS = 50
MAX_DRAFT_BYTES = 1_048_576
_ALLOWED_EXTENSIONS = {".md", ".json"}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ArtifactDraftApplicationService:
    """GSDLC-04-B server-authoritative runtime draft boundary.

    Drafts are runtime state under ``outputs/drafts/gsdlc_04_b`` and therefore
    cannot become approved workspace source merely by being saved. The service
    binds every revision to the current source preimage, authenticated actor and
    session principal, and rejects stale client revisions to prevent lost updates.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        documents: WorkspaceDocumentsApplicationService,
        draft_root: Path = DEFAULT_DRAFT_ROOT,
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.documents = documents
        self.draft_root = self.platform_root / draft_root
        self.secret_guard = SecretGuard(self.platform_root)
        self.schema_validator = SchemaValidator(self.platform_root)
        self._lock = threading.RLock()

    def get(self, *, document_id: str) -> CommandResult:
        command = "workspace artifact draft get"
        source = self._source(document_id, command=command)
        if isinstance(source, CommandResult):
            return source
        workspace_id, document = source
        store = self._load_store(workspace_id, document_id, command=command)
        if isinstance(store, CommandResult):
            return store
        if store is None:
            return CommandResult(
                command,
                True,
                ExitCode.PASS,
                "No persisted runtime draft exists for this document.",
                data={
                    "draft": None,
                    "source": self._source_summary(document),
                    "summary": self._summary(workspace_id, document_id, active=False, revisions_total=0),
                },
                findings=[Finding("GSDLC04B_DRAFT_EMPTY_PASS", "No runtime draft exists; approved source remains authoritative.", Severity.INFO, path=str(document.get("relative_path") or ""))],
            )
        conflict = self._source_conflict(store, document)
        payload = deepcopy(store)
        payload["source_conflict"] = conflict
        return CommandResult(
            command,
            not conflict,
            ExitCode.BLOCK if conflict else ExitCode.PASS,
            "Persisted draft conflicts with the current approved source preimage." if conflict else "Persisted runtime draft loaded.",
            data={
                "draft": payload,
                "source": self._source_summary(document),
                "summary": self._summary(workspace_id, document_id, active=bool(store.get("active")), revisions_total=len(store.get("revisions", [])), conflict=conflict),
            },
            findings=[Finding("GSDLC04B_SOURCE_PREIMAGE_CONFLICT_BLOCK" if conflict else "GSDLC04B_DRAFT_LOAD_PASS", "Approved source changed after the draft was based on it; save/recover is blocked." if conflict else "Draft was recovered from runtime persistence without source mutation.", Severity.BLOCK if conflict else Severity.INFO, path=str(document.get("relative_path") or ""))],
        )

    def history(self, *, document_id: str) -> CommandResult:
        command = "workspace artifact draft history"
        source = self._source(document_id, command=command)
        if isinstance(source, CommandResult):
            return source
        workspace_id, document = source
        store = self._load_store(workspace_id, document_id, command=command)
        if isinstance(store, CommandResult):
            return store
        revisions = list((store or {}).get("revisions", []))
        summaries = [self._revision_summary(revision) for revision in reversed(revisions)]
        return CommandResult(
            command,
            True,
            ExitCode.PASS,
            "Immutable runtime draft history loaded.",
            data={"revisions": summaries, "source": self._source_summary(document), "summary": self._summary(workspace_id, document_id, active=bool((store or {}).get("active")), revisions_total=len(revisions))},
            findings=[Finding("GSDLC04B_DRAFT_HISTORY_PASS", "Draft history is runtime-only and source-non-mutating.", Severity.INFO, path=str(document.get("relative_path") or ""))],
        )

    def save(
        self,
        *,
        document_id: str,
        content: str,
        expected_source_sha256: str,
        expected_revision_sha256: str | None,
        actor: str,
        actor_role: str,
        session_principal: str,
        event: str = "SAVE",
    ) -> CommandResult:
        command = "workspace artifact draft save"
        event = str(event or "SAVE").upper()
        if event not in {"SAVE", "AUTOSAVE"}:
            return self._block(command, "GSDLC04B_DRAFT_EVENT_BLOCK", "Draft save event must be SAVE or AUTOSAVE.")
        source = self._source(document_id, command=command)
        if isinstance(source, CommandResult):
            return source
        workspace_id, document = source
        validation = self._validate_editable(document, content, expected_source_sha256)
        if validation is not None:
            return validation
        if not actor.strip() or not session_principal.strip() or not actor_role.strip():
            return self._block(command, "GSDLC04B_SESSION_ACTOR_REQUIRED_BLOCK", "Authenticated actor, canonical role and session principal are required.")
        secret = self.secret_guard.scan_text(content, subject=str(document.get("relative_path") or document_id))
        if secret.effect.value == "block":
            return self._block(command, "GSDLC04B_SECRET_DRAFT_BLOCK", "Secret-like content is not persisted in the runtime draft store.")

        with self._lock:
            store = self._load_store(workspace_id, document_id, command=command)
            if isinstance(store, CommandResult):
                return store
            current_source_sha = str(document.get("sha256") or "")
            if current_source_sha != expected_source_sha256:
                return self._conflict(command, document, "Approved source preimage changed before draft save.")
            existing = store or self._new_store(workspace_id, document, actor, actor_role, session_principal)
            if self._source_conflict(existing, document):
                return self._conflict(command, document, "Approved source changed after this draft lineage began.")
            current_revision = self._current_revision(existing)
            current_revision_sha = str(current_revision.get("revision_sha256") or "") if current_revision else None
            normalized_expected_revision = str(expected_revision_sha256 or "").strip() or None
            if current_revision_sha != normalized_expected_revision:
                return self._conflict(command, document, "Draft revision is stale; optimistic concurrency rejected a lost update.", metadata={"expected_revision_sha256": normalized_expected_revision, "current_revision_sha256": current_revision_sha})

            content_sha = self._sha(content)
            if current_revision and str(current_revision.get("content_sha256")) == content_sha and bool(existing.get("active")):
                return CommandResult(
                    command,
                    True,
                    ExitCode.PASS,
                    "Draft save is idempotent; identical content did not create another revision.",
                    data={"draft": deepcopy(existing), "source": self._source_summary(document), "summary": self._summary(workspace_id, document_id, active=True, revisions_total=len(existing["revisions"]), idempotent=True)},
                    findings=[Finding("GSDLC04B_AUTOSAVE_IDEMPOTENT_PASS", "Identical autosave content reused the current immutable revision.", Severity.INFO, path=str(document.get("relative_path") or ""))],
                )

            revision = self._revision(existing, content=content, event=event, actor=actor, actor_role=actor_role, session_principal=session_principal, parent_revision_sha256=current_revision_sha)
            existing["active"] = True
            existing["current_revision_sha256"] = revision["revision_sha256"]
            existing["updated_at"] = revision["created_at"]
            existing["author_actor"] = actor
            existing["author_role"] = actor_role
            existing["session_principal"] = session_principal
            existing["revisions"].append(revision)
            existing["revisions"] = existing["revisions"][-MAX_REVISIONS:]
            self._write_store(workspace_id, document_id, existing)

        return CommandResult(
            command,
            True,
            ExitCode.PASS,
            "Runtime draft persisted without overwriting approved source.",
            data={"draft": deepcopy(existing), "source": self._source_summary(document), "summary": self._summary(workspace_id, document_id, active=True, revisions_total=len(existing["revisions"]))},
            findings=[Finding("GSDLC04B_DRAFT_SAVE_PASS", "Manual draft revision persisted in runtime state with MANUAL provenance.", Severity.INFO, path=str(document.get("relative_path") or ""))],
        )

    def discard(
        self,
        *,
        document_id: str,
        expected_source_sha256: str,
        expected_revision_sha256: str | None,
        actor: str,
        actor_role: str,
        session_principal: str,
    ) -> CommandResult:
        command = "workspace artifact draft discard"
        source = self._source(document_id, command=command)
        if isinstance(source, CommandResult):
            return source
        workspace_id, document = source
        if str(document.get("sha256") or "") != expected_source_sha256:
            return self._conflict(command, document, "Approved source preimage changed before discard.")
        with self._lock:
            store = self._load_store(workspace_id, document_id, command=command)
            if isinstance(store, CommandResult):
                return store
            if store is None:
                return CommandResult(command, True, ExitCode.PASS, "No runtime draft existed; discard is idempotent.", data={"draft": None, "source": self._source_summary(document), "summary": self._summary(workspace_id, document_id, active=False, revisions_total=0, idempotent=True)}, findings=[Finding("GSDLC04B_DISCARD_EMPTY_PASS", "Discard completed without source mutation.", Severity.INFO)])
            if self._source_conflict(store, document):
                return self._conflict(command, document, "Approved source changed after this draft lineage began.")
            current = self._current_revision(store)
            current_sha = str(current.get("revision_sha256") or "") if current else None
            expected = str(expected_revision_sha256 or "").strip() or None
            if current_sha != expected:
                return self._conflict(command, document, "Draft revision is stale; discard rejected by optimistic concurrency.", metadata={"expected_revision_sha256": expected, "current_revision_sha256": current_sha})
            store["active"] = False
            store["current_revision_sha256"] = None
            store["updated_at"] = _now()
            store["events"].append(self._event("DISCARD", actor, actor_role, session_principal, source_sha256=expected_source_sha256, revision_sha256=current_sha))
            store["events"] = store["events"][-(MAX_REVISIONS * 2):]
            self._write_store(workspace_id, document_id, store)
        return CommandResult(command, True, ExitCode.PASS, "Active runtime draft discarded; immutable history retained.", data={"draft": deepcopy(store), "source": self._source_summary(document), "summary": self._summary(workspace_id, document_id, active=False, revisions_total=len(store["revisions"]))}, findings=[Finding("GSDLC04B_DRAFT_DISCARD_PASS", "Draft was discarded without workspace source mutation.", Severity.INFO, path=str(document.get("relative_path") or ""))])

    def recover(
        self,
        *,
        document_id: str,
        revision_sha256: str,
        expected_source_sha256: str,
        expected_revision_sha256: str | None,
        actor: str,
        actor_role: str,
        session_principal: str,
    ) -> CommandResult:
        command = "workspace artifact draft recover"
        source = self._source(document_id, command=command)
        if isinstance(source, CommandResult):
            return source
        workspace_id, document = source
        if str(document.get("sha256") or "") != expected_source_sha256:
            return self._conflict(command, document, "Approved source preimage changed before recovery.")
        with self._lock:
            store = self._load_store(workspace_id, document_id, command=command)
            if isinstance(store, CommandResult):
                return store
            if store is None:
                return self._block(command, "GSDLC04B_RECOVERY_MISSING_BLOCK", "No draft history exists for recovery.")
            if self._source_conflict(store, document):
                return self._conflict(command, document, "Approved source changed after this draft lineage began.")
            current = self._current_revision(store)
            current_sha = str(current.get("revision_sha256") or "") if current else None
            expected = str(expected_revision_sha256 or "").strip() or None
            if current_sha != expected:
                return self._conflict(command, document, "Draft revision is stale; recovery rejected by optimistic concurrency.", metadata={"expected_revision_sha256": expected, "current_revision_sha256": current_sha})
            target = next((r for r in store["revisions"] if r.get("revision_sha256") == revision_sha256), None)
            if target is None:
                return self._block(command, "GSDLC04B_RECOVERY_REVISION_BLOCK", "Requested immutable draft revision does not exist.")
            revision = self._revision(store, content=str(target["content"]), event="RECOVER", actor=actor, actor_role=actor_role, session_principal=session_principal, parent_revision_sha256=current_sha, recovered_from_sha256=revision_sha256)
            store["active"] = True
            store["current_revision_sha256"] = revision["revision_sha256"]
            store["updated_at"] = revision["created_at"]
            store["author_actor"] = actor
            store["author_role"] = actor_role
            store["session_principal"] = session_principal
            store["revisions"].append(revision)
            store["revisions"] = store["revisions"][-MAX_REVISIONS:]
            self._write_store(workspace_id, document_id, store)
        return CommandResult(command, True, ExitCode.PASS, "Historical revision recovered as a new immutable draft revision.", data={"draft": deepcopy(store), "source": self._source_summary(document), "summary": self._summary(workspace_id, document_id, active=True, revisions_total=len(store["revisions"]))}, findings=[Finding("GSDLC04B_DRAFT_RECOVER_PASS", "Revision recovery created a new runtime revision and did not rewrite approved source.", Severity.INFO, path=str(document.get("relative_path") or ""))])

    def _source(self, document_id: str, *, command: str) -> tuple[str, dict[str, Any]] | CommandResult:
        result = self.documents.read_document(document_id)
        if not result.ok:
            return CommandResult(command, False, result.exit_code, "Draft operation requires a readable project-scoped workspace document.", data=result.data, findings=result.findings)
        document = result.data.get("document") if isinstance(result.data, dict) else None
        context = result.data.get("ui_workspace_context") if isinstance(result.data, dict) else None
        if not isinstance(document, dict) or not isinstance(context, dict):
            return self._block(command, "GSDLC04B_DOCUMENT_CONTEXT_BLOCK", "Workspace document/context response is incomplete.")
        workspace_id = str(context.get("active_workspace_id") or "").strip()
        if not workspace_id:
            return self._block(command, "GSDLC04B_WORKSPACE_SCOPE_BLOCK", "Draft persistence requires an active server-validated workspace id.")
        return workspace_id, document

    def _validate_editable(self, document: dict[str, Any], content: str, expected_source_sha256: str) -> CommandResult | None:
        extension = str(document.get("extension") or "").lower()
        if extension not in _ALLOWED_EXTENSIONS:
            return self._block("workspace artifact draft save", "GSDLC04B_DRAFT_TYPE_BLOCK", "Manual authoring is limited to Markdown and JSON in GSDLC-04-B.")
        if not isinstance(content, str):
            return self._block("workspace artifact draft save", "GSDLC04B_DRAFT_CONTENT_BLOCK", "Draft content must be UTF-8 text.")
        size = len(content.encode("utf-8"))
        if size > MAX_DRAFT_BYTES:
            return self._block("workspace artifact draft save", "GSDLC04B_DRAFT_SIZE_BLOCK", "Draft exceeds the bounded runtime persistence size.", metadata={"bytes": size, "max_bytes": MAX_DRAFT_BYTES})
        if not _SHA256_RE.fullmatch(str(expected_source_sha256 or "")):
            return self._block("workspace artifact draft save", "GSDLC04B_SOURCE_PREIMAGE_REQUIRED_BLOCK", "An exact approved-source SHA-256 preimage is required.")
        return None

    def _new_store(self, workspace_id: str, document: dict[str, Any], actor: str, actor_role: str, session_principal: str) -> dict[str, Any]:
        now = _now()
        return {
            "schema_id": "devpilot.gsdlc04b.artifact_draft_store_record.v1",
            "workspace_id": workspace_id,
            "document_id": str(document["document_id"]),
            "relative_path": str(document["relative_path"]),
            "extension": str(document["extension"]),
            "source_type": "MANUAL",
            "lifecycle_state": "DRAFT",
            "source_preimage_sha256": str(document["sha256"]),
            "base_commit": self._base_commit(),
            "author_actor": actor,
            "author_role": actor_role,
            "session_principal": session_principal,
            "active": False,
            "current_revision_sha256": None,
            "created_at": now,
            "updated_at": now,
            "revisions": [],
            "events": [],
            "source_mutations_performed": False,
            "approved_evidence": False,
        }

    def _revision(
        self,
        store: dict[str, Any],
        *,
        content: str,
        event: str,
        actor: str,
        actor_role: str,
        session_principal: str,
        parent_revision_sha256: str | None,
        recovered_from_sha256: str | None = None,
    ) -> dict[str, Any]:
        created_at = _now()
        content_sha = self._sha(content)
        ordinal = len(store.get("revisions", [])) + 1
        payload = "\x00".join([store["workspace_id"], store["document_id"], str(ordinal), event, content_sha, parent_revision_sha256 or "", actor, session_principal, created_at])
        revision_sha = self._sha(payload)
        return {
            "revision": ordinal,
            "revision_sha256": revision_sha,
            "parent_revision_sha256": parent_revision_sha256,
            "content_sha256": content_sha,
            "content": content,
            "event": event,
            "source_type": "MANUAL",
            "lifecycle_state": "DRAFT",
            "source_preimage_sha256": store["source_preimage_sha256"],
            "actor": actor,
            "actor_role": actor_role,
            "session_principal": session_principal,
            "created_at": created_at,
            "recovered_from_sha256": recovered_from_sha256,
            "approved_evidence": False,
            "source_mutations_performed": False,
        }

    def _event(self, event: str, actor: str, actor_role: str, session_principal: str, *, source_sha256: str, revision_sha256: str | None) -> dict[str, Any]:
        return {"event": event, "actor": actor, "actor_role": actor_role, "session_principal": session_principal, "source_preimage_sha256": source_sha256, "revision_sha256": revision_sha256, "created_at": _now(), "source_mutations_performed": False}

    @staticmethod
    def _current_revision(store: dict[str, Any]) -> dict[str, Any] | None:
        current = store.get("current_revision_sha256")
        if not current:
            return None
        return next((revision for revision in store.get("revisions", []) if revision.get("revision_sha256") == current), None)

    @staticmethod
    def _source_conflict(store: dict[str, Any], document: dict[str, Any]) -> bool:
        return str(store.get("source_preimage_sha256") or "") != str(document.get("sha256") or "")

    def _store_path(self, workspace_id: str, document_id: str) -> Path:
        workspace_token = hashlib.sha256(workspace_id.encode("utf-8")).hexdigest()[:20]
        document_token = hashlib.sha256(document_id.encode("utf-8")).hexdigest()[:32]
        return self.draft_root / workspace_token / f"{document_token}.json"

    def _load_store(self, workspace_id: str, document_id: str, *, command: str) -> dict[str, Any] | None | CommandResult:
        path = self._store_path(workspace_id, document_id)
        if not path.exists():
            return None
        try:
            raw = path.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return self._block(command, "GSDLC04B_DRAFT_STORE_CORRUPT_BLOCK", "Runtime draft store is unreadable/corrupt; operation fails closed.", metadata={"exception_type": exc.__class__.__name__})
        if not isinstance(payload, dict) or payload.get("schema_id") != "devpilot.gsdlc04b.artifact_draft_store_record.v1" or payload.get("workspace_id") != workspace_id or payload.get("document_id") != document_id or not isinstance(payload.get("revisions"), list):
            return self._block(command, "GSDLC04B_DRAFT_STORE_CORRUPT_BLOCK", "Runtime draft store failed identity/shape validation; operation fails closed.")
        schema_result = self.schema_validator.validate_payload(
            schema="SCHEMA-DEVPL-GSDLC-04-B-ARTIFACT-DRAFT-STORE-RECORD-V1",
            payload=payload,
            instance_label=f"runtime-draft:{workspace_id}:{document_id}",
        )
        if not schema_result.ok:
            return self._block(command, "GSDLC04B_DRAFT_STORE_SCHEMA_BLOCK", "Runtime draft store failed its registered JSON Schema; operation fails closed.")
        return payload

    def _write_store(self, workspace_id: str, document_id: str, payload: dict[str, Any]) -> None:
        schema_result = self.schema_validator.validate_payload(
            schema="SCHEMA-DEVPL-GSDLC-04-B-ARTIFACT-DRAFT-STORE-RECORD-V1",
            payload=payload,
            instance_label=f"runtime-draft:{workspace_id}:{document_id}",
        )
        if not schema_result.ok:
            raise ValueError("GSDLC04B_DRAFT_STORE_SCHEMA_BLOCK")
        path = self._store_path(workspace_id, document_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        temp.write_text(encoded, encoding="utf-8", newline="\n")
        os.replace(temp, path)

    def _base_commit(self) -> str:
        context = self.documents.context_resolver.resolve()
        root = context.active_workspace_root
        if root is None:
            return "0" * 40
        result = GitAdapter(root).log(limit=1)
        if result.ok:
            commits = result.data.get("commits", []) if isinstance(result.data, dict) else []
            if commits and isinstance(commits[0], dict) and re.fullmatch(r"[0-9a-f]{40}", str(commits[0].get("commit") or "")):
                return str(commits[0]["commit"])
        return "0" * 40

    @staticmethod
    def _sha(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _source_summary(document: dict[str, Any]) -> dict[str, Any]:
        return {"document_id": document.get("document_id"), "relative_path": document.get("relative_path"), "extension": document.get("extension"), "sha256": document.get("sha256"), "approved_source_overwritten": False}

    @staticmethod
    def _revision_summary(revision: dict[str, Any]) -> dict[str, Any]:
        return {key: revision.get(key) for key in ("revision", "revision_sha256", "parent_revision_sha256", "content_sha256", "event", "actor", "actor_role", "created_at", "recovered_from_sha256", "lifecycle_state", "source_type")}

    @staticmethod
    def _summary(workspace_id: str, document_id: str, *, active: bool, revisions_total: int, conflict: bool = False, idempotent: bool = False) -> dict[str, Any]:
        return {"workspace_id": workspace_id, "document_id": document_id, "active": active, "revisions_total": revisions_total, "source_type": "MANUAL", "lifecycle_state": "DRAFT", "runtime_persistence": True, "approved_evidence": False, "approved_source_overwritten": False, "source_mutations_performed": False, "network_used": False, "external_api_used": False, "optimistic_concurrency": True, "source_conflict": conflict, "idempotent": idempotent}

    @staticmethod
    def _block(command: str, finding_id: str, message: str, *, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"summary": {"source_mutations_performed": False, "network_used": False, "external_api_used": False}}, findings=[Finding(finding_id, message, Severity.BLOCK, metadata=metadata or {})])

    def _conflict(self, command: str, document: dict[str, Any], message: str, *, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"source": self._source_summary(document), "summary": {"conflict": True, "lost_update_blocked": True, "source_mutations_performed": False, "network_used": False, "external_api_used": False}}, findings=[Finding("GSDLC04B_OPTIMISTIC_CONCURRENCY_CONFLICT_BLOCK", message, Severity.BLOCK, path=str(document.get("relative_path") or ""), metadata=metadata or {})])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
