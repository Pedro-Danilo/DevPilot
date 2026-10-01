from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.code_workbench.service import CodeWorkbenchApplicationService
from devpilot_core.story_execution import StoryExecutionStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _slug(value: str, *, fallback: str) -> str:
    text = str(value or "").lower()
    text = (
        text.replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    )
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or fallback


class StoryImplementationCandidateApplicationService:
    """13-D-02 deterministic implementation proposal for an empty greenfield source tree.

    The proposal is runtime-only and consumes the already-authoritative StoryExecution,
    StoryContextPack and frozen Architecture document.  It deliberately does not call a
    model, execute tools, install dependencies or mutate source.  Human ACCEPT creates
    SourceDraftBuffer records only; 09-C remains the sole source mutation boundary.
    """

    SCHEMA_ID = "DEVPL-GSDLC-13-D-02-IMPLEMENTATION-CANDIDATE-V1"

    def __init__(self, root: Path, *, context_resolver, code_workbench: CodeWorkbenchApplicationService) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver
        self.code = code_workbench
        self._lock = RLock()

    def propose(self, *, actor: str, actor_role: str) -> CommandResult:
        command = "story implementation candidate propose"
        if actor_role not in {"owner", "developer"} or not str(actor).strip():
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_ROLE_BLOCK", "Owner/developer human session is required.")
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id:
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_CONTEXT_BLOCK", "Active server-valid project context is required.")
        workspace = Path(context.effective_workspace_root)
        workspace_id = str(context.active_workspace_id)
        store = StoryExecutionStore(workspace, workspace_id=workspace_id)
        state = store.load_state()
        story_context = store.load_context()
        if state is None or not isinstance(story_context, dict) or str(state.status.value) != "IN_PROGRESS":
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_STORY_BLOCK", "Implementation proposal requires StoryExecution IN_PROGRESS with StoryContextPack.")

        sources = self.code.list_sources()
        if not sources.ok:
            return self._dependency_block(command, sources, "GSDLC13D02_IMPLEMENTATION_SOURCE_DISCOVERY_BLOCK")
        if int(((sources.data or {}).get("summary") or {}).get("sources_total") or 0) != 0:
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_EMPTY_SOURCE_ONLY_BLOCK", "Deterministic bootstrap proposal is only for a source-empty greenfield; use bounded EDIT/agent proposal for existing source.")

        architecture_path = workspace / "docs/02_architecture/architecture_document.md"
        if not architecture_path.is_file():
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_ARCHITECTURE_MISSING_BLOCK", "Frozen Architecture document is required before source bootstrap.")
        architecture = architecture_path.read_text(encoding="utf-8-sig")
        technology = self._technology(architecture)
        if technology["backend"] != "fastapi-python" or technology["database"] != "sqlite":
            return self._block(
                command,
                "GSDLC13D02_IMPLEMENTATION_PROFILE_BLOCK",
                "Deterministic implementation provider currently supports the approved fastapi-python + sqlite profile only; do not guess another stack.",
                metadata={"technology": technology},
            )

        story = story_context.get("story") if isinstance(story_context.get("story"), dict) else {}
        story_id = str(story.get("id") or state.story_id)
        title = str(story.get("title") or story_id)
        requirement = self._fragment(story_context, "requirement")
        acceptance = self._fragment(story_context, "acceptance")
        test_intent = self._fragment(story_context, "test-intent")
        namespace = _slug(workspace_id, fallback="app")
        story_slug = _slug(story_id, fallback="story")
        module_path = f"src/{namespace}/application/{story_slug}.py"
        repository_path = f"src/{namespace}/infrastructure/sqlite_{story_slug}_repository.py"
        test_path = f"tests/test_{story_slug}.py"

        files = [
            self._file(module_path, self._application_module(story_id, title, requirement, acceptance)),
            self._file(repository_path, self._repository_module(story_id, namespace, story_slug)),
            self._file(test_path, self._test_module(story_id, namespace, story_slug, acceptance)),
        ]
        stable = {
            "workspace_id": workspace_id,
            "story_execution_id": state.execution_id,
            "story_id": story_id,
            "story_context_sha256": story_context.get("context_sha256"),
            "architecture_sha256": _sha_text(architecture),
            "technology": technology,
            "files": [{k: row[k] for k in ("target_path", "content_sha256", "operation")} for row in files],
        }
        proposal_hash = _sha(stable)
        proposal_id = "implementation-proposal-" + proposal_hash[:24]
        existing = self._load(workspace, workspace_id, proposal_id)
        if isinstance(existing, dict) and str(existing.get("proposal_sha256") or "") == proposal_hash:
            return self._pass(
                command,
                "Existing deterministic implementation proposal recovered without reopening its human decision; source/draft mutations=false.",
                {"proposal": existing, "recovered": True},
            )
        proposal = {
            "schema_id": self.SCHEMA_ID,
            "schema_version": "1.0.0",
            "proposal_id": proposal_id,
            "proposal_sha256": proposal_hash,
            "workspace_id": workspace_id,
            "story_execution_id": state.execution_id,
            "story_id": story_id,
            "story_title": title,
            "status": "PROPOSED",
            "provider": {
                "provider_id": "devpilot-local",
                "model_id": "deterministic-story-implementation-template-v1",
                "preliminary": True,
                "network_used": False,
                "external_api_used": False,
                "cost_usd": 0.0,
            },
            "technology": technology,
            "rationale": [
                "StoryContextPack is IN_PROGRESS and the source tree is empty.",
                "The frozen Architecture selected fastapi-python + sqlite; the first bounded slice therefore uses Python application and SQLite persistence boundaries.",
                "The Story is allocated to ARC-C02/ARC-C03/ARC-C04; this preliminary slice materializes application/domain behavior and local persistence without inventing an ARC-C01 presentation contract that is not required by the StoryContextPack.",
                "D03 quality/remediation may require a successor change if targeted tests expose a missing boundary or insufficient behavior.",
                "Manual authoring remains available; this proposal is a reviewable default, not authority to write source.",
            ],
            "files": files,
            "provenance": {
                "story_context_pack_id": story_context.get("context_pack_id"),
                "story_context_sha256": story_context.get("context_sha256"),
                "architecture_path": "docs/02_architecture/architecture_document.md",
                "architecture_sha256": _sha_text(architecture),
                "requirement_source_ref": requirement.get("source_ref"),
                "test_intent_source_ref": test_intent.get("source_ref"),
            },
            "safety": {
                "proposal_only": True,
                "human_review_required": True,
                "source_mutations_performed": False,
                "draft_mutations_performed": False,
                "apply_authority": False,
                "approval_authority": False,
                "git_authority": False,
                "network_used": False,
                "external_api_used": False,
            },
            "created_at_utc": _now(),
            "human_decision": None,
            "draft_ids": [],
        }
        self._save(workspace, workspace_id, proposal)
        return self._pass(command, "Deterministic implementation proposal created from StoryContextPack + frozen Architecture; source/draft mutations=false.", {"proposal": proposal})

    def decide(self, *, proposal_id: str, proposal_sha256: str, decision: str, actor: str, actor_role: str) -> CommandResult:
        command = "story implementation candidate decision"
        decision = str(decision or "").upper().strip()
        if actor_role not in {"owner", "developer"} or not str(actor).strip():
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_DECISION_ROLE_BLOCK", "Owner/developer human session is required.")
        if decision not in {"ACCEPT", "REJECT"}:
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_DECISION_BLOCK", "Decision must be ACCEPT or REJECT.")
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id:
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_CONTEXT_BLOCK", "Active server-valid project context is required.")
        workspace = Path(context.effective_workspace_root)
        workspace_id = str(context.active_workspace_id)
        proposal = self._load(workspace, workspace_id, proposal_id)
        if proposal is None:
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_PROPOSAL_MISSING_BLOCK", "Implementation proposal was not found.")
        if str(proposal.get("proposal_sha256")) != str(proposal_sha256 or ""):
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_PROPOSAL_HASH_BLOCK", "Implementation proposal SHA-256 changed; refresh before decision.")
        if proposal.get("status") != "PROPOSED":
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_PROPOSAL_DECIDED_BLOCK", "Implementation proposal already has a terminal human decision.")
        if decision == "REJECT":
            proposal["status"] = "REJECTED"
            proposal["human_decision"] = {"decision": decision, "actor": actor, "actor_role": actor_role, "decided_at_utc": _now()}
            self._save(workspace, workspace_id, proposal)
            return self._pass(command, "Implementation proposal rejected; source/draft mutations=false.", {"proposal": proposal, "drafts": []})

        store = StoryExecutionStore(workspace, workspace_id=workspace_id)
        state = store.load_state()
        if state is None or str(state.execution_id) != str(proposal.get("story_execution_id")) or str(state.status.value) != "IN_PROGRESS":
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_STALE_STORY_BLOCK", "StoryExecution changed after proposal generation; regenerate proposal.")
        current_context = store.load_context() or {}
        if str(current_context.get("context_sha256") or "") != str((proposal.get("provenance") or {}).get("story_context_sha256") or ""):
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_CONTEXT_DRIFT_BLOCK", "StoryContextPack changed after proposal generation; regenerate proposal.")
        architecture_path = workspace / str((proposal.get("provenance") or {}).get("architecture_path") or "docs/02_architecture/architecture_document.md")
        if not architecture_path.is_file() or _sha_text(architecture_path.read_text(encoding="utf-8-sig")) != str((proposal.get("provenance") or {}).get("architecture_sha256") or ""):
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_ARCHITECTURE_DRIFT_BLOCK", "Frozen Architecture changed after proposal generation; regenerate proposal.")
        current_sources = self.code.list_sources()
        if not current_sources.ok or int((((current_sources.data or {}).get("summary") or {}).get("sources_total") or 0)) != 0:
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_SOURCE_DRIFT_BLOCK", "Source tree changed after proposal generation; regenerate proposal before materializing drafts.")

        listed = self.code.list_drafts()
        if not listed.ok:
            return self._dependency_block(command, listed, "GSDLC13D02_IMPLEMENTATION_DRAFT_RECONCILIATION_BLOCK")
        expected_files = {str(row.get("target_path") or ""): row for row in proposal.get("files") or []}
        drafts: list[dict[str, Any]] = []
        for current in (listed.data or {}).get("drafts") or []:
            target_path = str(current.get("target_path") or "")
            expected_row = expected_files.get(target_path)
            if (
                expected_row is None
                or str(current.get("operation") or "") != "CREATE"
                or str(current.get("content_sha256") or "") != str(expected_row.get("content_sha256") or "")
            ):
                return self._block(
                    command,
                    "GSDLC13D02_IMPLEMENTATION_DRAFT_STATE_DRIFT_BLOCK",
                    "Existing runtime drafts do not match the accepted deterministic proposal; inspect/discard explicitly before retry.",
                    metadata={"unexpected_draft_id": current.get("draft_id"), "target_path": target_path},
                )
            drafts.append(deepcopy(current))
        existing_targets = {str(row.get("target_path") or "") for row in drafts}
        created_this_attempt: list[dict[str, Any]] = []
        for row in proposal.get("files") or []:
            if str(row.get("target_path") or "") in existing_targets:
                continue
            result = self.code.save_draft(
                operation="CREATE",
                content=str(row.get("content") or ""),
                target_path=str(row.get("target_path") or ""),
                source_id=None,
                expected_source_sha256=None,
                expected_revision_sha256=None,
                actor=actor,
                actor_role=actor_role,
            )
            if not result.ok:
                rollback_findings: list[dict[str, Any]] = []
                for prior in reversed(created_this_attempt):
                    cleanup = self.code.discard_draft(
                        str(prior.get("draft_id") or ""),
                        expected_revision_sha256=str(prior.get("revision_sha256") or ""),
                        actor_role=actor_role,
                    )
                    if not cleanup.ok:
                        rollback_findings.append(cleanup.to_dict())
                blocked = self._dependency_block(command, result, "GSDLC13D02_IMPLEMENTATION_DRAFT_MATERIALIZATION_BLOCK")
                if rollback_findings:
                    blocked.data["draft_rollback_failures"] = rollback_findings
                return blocked
            created = deepcopy((result.data or {}).get("draft") or {})
            drafts.append(created)
            created_this_attempt.append(created)
        proposal["status"] = "ACCEPTED"
        proposal["draft_ids"] = [str(x.get("draft_id")) for x in drafts]
        proposal["human_decision"] = {
            "decision": "ACCEPT",
            "actor": actor,
            "actor_role": actor_role,
            "decided_at_utc": _now(),
            "effect": "materialize-runtime-source-draft-set-only",
            "source_write_authorized": False,
        }
        proposal["safety"]["draft_mutations_performed"] = True
        self._save(workspace, workspace_id, proposal)
        return self._pass(command, "Human ACCEPT materialized a runtime-only SourceDraftBuffer set; source remains unchanged.", {"proposal": proposal, "drafts": drafts, "source_mutations_performed": False})

    @staticmethod
    def _technology(text: str) -> dict[str, str]:
        def capture(label: str) -> str:
            match = re.search(rf"-\s*{re.escape(label)}:\s*`([^`]+)`", text, re.I)
            return str(match.group(1)).strip().lower() if match else "unknown"
        profile = re.search(r"Perfil propuesto para decisión Owner:\*\*\s*`([^`]+)`", text, re.I)
        return {
            "profile_id": str(profile.group(1)).strip() if profile else "unknown",
            "frontend": capture("Frontend"),
            "backend": capture("Backend"),
            "database": capture("Database"),
        }

    @staticmethod
    def _fragment(context: dict[str, Any], kind: str) -> dict[str, Any]:
        for row in context.get("fragments") or []:
            if isinstance(row, dict) and str(row.get("kind")) == kind:
                return row
        return {}

    @staticmethod
    def _file(target_path: str, content: str) -> dict[str, Any]:
        return {
            "operation": "CREATE",
            "target_path": target_path,
            "content": content,
            "content_sha256": _sha_text(content),
            "rationale": "Generated as one bounded file in the first architecture-aligned implementation slice.",
        }

    @staticmethod
    def _application_module(story_id: str, title: str, requirement: dict[str, Any], acceptance: dict[str, Any]) -> str:
        req = " ".join(str(requirement.get("content") or "").split())[:500]
        ac = " ".join(str(acceptance.get("content") or "").split())[:400]
        return f'''"""Application boundary for {story_id}: {title}.

Requirement context: {req}
Acceptance oracle: {ac}
Generated by DevPilot deterministic-story-implementation-template-v1.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class AuthorizationRequired(PermissionError):
    """Raised when the caller has not crossed the authorization boundary."""


class StoryRepository(Protocol):
    def create(self, payload: Mapping[str, Any]) -> str: ...
    def get(self, record_id: str) -> Mapping[str, Any] | None: ...


def execute(*, actor_authorized: bool, payload: Mapping[str, Any], repository: StoryRepository) -> str:
    """Create one durable record and verify it can be observed afterwards."""
    if not actor_authorized:
        raise AuthorizationRequired("authorized actor required")
    normalized = dict(payload)
    if not normalized:
        raise ValueError("valid non-empty payload required")
    record_id = repository.create(normalized)
    if repository.get(record_id) is None:
        raise RuntimeError("record was not observable after create")
    return record_id
'''

    @staticmethod
    def _repository_module(story_id: str, namespace: str, story_slug: str) -> str:
        table = re.sub(r"[^a-z0-9_]+", "_", story_slug.lower()) + "_records"
        return f'''"""SQLite persistence adapter for {story_id}."""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Mapping
from typing import Any


class SQLiteStoryRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS {table} (record_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL)"
        )
        self.connection.commit()

    def create(self, payload: Mapping[str, Any]) -> str:
        record_id = uuid.uuid4().hex
        self.connection.execute(
            "INSERT INTO {table}(record_id, payload_json) VALUES (?, ?)",
            (record_id, json.dumps(dict(payload), sort_keys=True, ensure_ascii=False)),
        )
        self.connection.commit()
        return record_id

    def get(self, record_id: str) -> Mapping[str, Any] | None:
        row = self.connection.execute(
            "SELECT payload_json FROM {table} WHERE record_id = ?", (record_id,)
        ).fetchone()
        return json.loads(row[0]) if row else None
'''

    @staticmethod
    def _test_module(story_id: str, namespace: str, story_slug: str, acceptance: dict[str, Any]) -> str:
        ac = " ".join(str(acceptance.get("content") or "").split())[:400]
        return f'''"""Acceptance-focused tests for {story_id}.

Oracle: {ac}
"""

import sqlite3

import pytest

from src.{namespace}.application.{story_slug} import AuthorizationRequired, execute
from src.{namespace}.infrastructure.sqlite_{story_slug}_repository import SQLiteStoryRepository


def test_authorization_is_required() -> None:
    repository = SQLiteStoryRepository(sqlite3.connect(":memory:"))
    with pytest.raises(AuthorizationRequired):
        execute(actor_authorized=False, payload={{"name": "sample"}}, repository=repository)


def test_valid_data_is_recorded_and_observable() -> None:
    repository = SQLiteStoryRepository(sqlite3.connect(":memory:"))
    record_id = execute(actor_authorized=True, payload={{"name": "sample"}}, repository=repository)
    assert repository.get(record_id) == {{"name": "sample"}}
'''

    def _store_path(self, workspace: Path, workspace_id: str) -> Path:
        safe = _slug(workspace_id, fallback="workspace")
        return workspace / "outputs" / "story_implementation" / "gsdlc_13_d_02" / safe / "proposals.json"

    def _save(self, workspace: Path, workspace_id: str, proposal: dict[str, Any]) -> None:
        path = self._store_path(workspace, workspace_id)
        with self._lock:
            payload = {"schema_version": "1.0.0", "proposals": {}}
            if path.is_file():
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise RuntimeError(f"implementation proposal store is unreadable: {path}") from exc
                if not isinstance(loaded, dict) or not isinstance(loaded.get("proposals", {}), dict):
                    raise RuntimeError(f"implementation proposal store has invalid structure: {path}")
                payload = loaded
            payload.setdefault("proposals", {})[str(proposal["proposal_id"])] = proposal
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix(".tmp")
            temp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
            temp.replace(path)

    def _load(self, workspace: Path, workspace_id: str, proposal_id: str) -> dict[str, Any] | None:
        path = self._store_path(workspace, workspace_id)
        with self._lock:
            if not path.is_file():
                return None
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None
            row = (payload.get("proposals") or {}).get(str(proposal_id))
            return deepcopy(row) if isinstance(row, dict) else None

    @staticmethod
    def _pass(command: str, message: str, data: dict[str, Any]) -> CommandResult:
        return CommandResult(command, True, ExitCode.PASS, message, data=data, findings=[Finding("GSDLC13D02_IMPLEMENTATION_PASS", message, Severity.INFO)])

    @staticmethod
    def _block(command: str, code: str, message: str, *, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data=metadata or {}, findings=[Finding(code, message, Severity.BLOCK, metadata=metadata or {})])

    @staticmethod
    def _dependency_block(command: str, result: CommandResult, code: str) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, "Dependency blocked deterministic implementation proposal.", data={"dependency": result.to_dict()}, findings=[Finding(code, "Dependency blocked deterministic implementation proposal.", Severity.BLOCK), *result.findings])
