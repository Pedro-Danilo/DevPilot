from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.observability.tracing import TraceContext
from devpilot_core.policy import PathGuard, PolicyEffect, redact_sensitive_data
from devpilot_core.store import LocalStore

DEFAULT_SESSION_DIR = ".devpilot/agent_sessions"
DEFAULT_RETENTION_DAYS = 14
SESSION_ID_PATTERN = re.compile(r"^agsess_[a-f0-9]{32}$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_session_id() -> str:
    return f"agsess_{uuid.uuid4().hex}"


@dataclass(frozen=True)
class AgentSessionEvent:
    """One redacted session event.

    Sprint 86 keeps operational memory narrow: event summaries, references and
    counts only. Raw prompts, model outputs, patches, secrets and large payloads
    must not be stored in AgentSession state.
    """

    event_id: str
    event_type: str
    timestamp: str
    agent_id: str | None = None
    command: str | None = None
    target: str | None = None
    ok: bool | None = None
    dry_run: bool = True
    trace_id: str | None = None
    run_id: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "dry_run": self.dry_run,
        }
        optional = {
            "agent_id": self.agent_id,
            "command": self.command,
            "target": self.target,
            "ok": self.ok,
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "summary": self.summary,
            "metadata": self.metadata,
        }
        for key, value in optional.items():
            if value not in (None, {}, []):
                payload[key] = value
        return redact_sensitive_data(payload)


@dataclass(frozen=True)
class AgentSession:
    """Local operational session state for one or more controlled agent runs."""

    session_id: str
    created_at: str
    updated_at: str
    status: str = "active"
    retention_days: int = DEFAULT_RETENTION_DAYS
    workspace: str = "."
    agent_ids: list[str] = field(default_factory=list)
    events: list[AgentSessionEvent] = field(default_factory=list)
    memory: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return redact_sensitive_data(
            {
                "session_id": self.session_id,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "status": self.status,
                "retention_days": self.retention_days,
                "workspace": self.workspace,
                "agent_ids": list(self.agent_ids),
                "events": [event.to_dict() for event in self.events],
                "memory": self.memory,
                "metadata": self.metadata,
                "summary": {
                    "events_total": len(self.events),
                    "agents_total": len(set(self.agent_ids)),
                    "memory_items_total": len(self.memory),
                    "raw_prompts_stored": False,
                    "raw_outputs_stored": False,
                    "semantic_memory_enabled": False,
                    "rag_enabled": False,
                    "local_only": True,
                },
            }
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AgentSession":
        events = [
            AgentSessionEvent(
                event_id=str(item.get("event_id") or uuid.uuid4().hex),
                event_type=str(item.get("event_type") or "agent.session.event"),
                timestamp=str(item.get("timestamp") or utc_now_iso()),
                agent_id=item.get("agent_id"),
                command=item.get("command"),
                target=item.get("target"),
                ok=item.get("ok"),
                dry_run=bool(item.get("dry_run", True)),
                trace_id=item.get("trace_id"),
                run_id=item.get("run_id"),
                summary=dict(item.get("summary") or {}),
                metadata=dict(item.get("metadata") or {}),
            )
            for item in payload.get("events", [])
            if isinstance(item, dict)
        ]
        return cls(
            session_id=str(payload["session_id"]),
            created_at=str(payload.get("created_at") or utc_now_iso()),
            updated_at=str(payload.get("updated_at") or utc_now_iso()),
            status=str(payload.get("status") or "active"),
            retention_days=int(payload.get("retention_days") or DEFAULT_RETENTION_DAYS),
            workspace=str(payload.get("workspace") or "."),
            agent_ids=[str(value) for value in payload.get("agent_ids", [])],
            events=events,
            memory=dict(payload.get("memory") or {}),
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass(frozen=True)
class AgentSessionInspectOptions:
    session_id: str
    include_events: bool = True
    limit: int = 20


class AgentSessionStore:
    """Filesystem + LocalStore backed session state for controlled agents.

    The canonical inspectable record is a redacted JSON document below
    `.devpilot/agent_sessions`. LocalStore receives event projections so session
    activity can be queried through existing operational telemetry. The store is
    local-only and does not implement semantic memory, embeddings or RAG.
    """

    def __init__(self, root: Path, *, session_dir: str | Path = DEFAULT_SESSION_DIR) -> None:
        self.root = root.resolve()
        self.session_dir = self._resolve_session_dir(session_dir)
        self.path_guard = PathGuard(self.root)

    def start_session(
        self,
        *,
        agent_id: str,
        requested_agent: str,
        target: str | None,
        dry_run: bool,
        session_id: str | None = None,
        trace_context: TraceContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentSession:
        effective_session_id = self._normalize_or_create_session_id(session_id)
        existing = self._load_optional(effective_session_id)
        now = utc_now_iso()
        event = AgentSessionEvent(
            event_id=uuid.uuid4().hex,
            event_type="agent.session.started",
            timestamp=now,
            agent_id=agent_id,
            command="agent run",
            target=target,
            dry_run=dry_run,
            trace_id=trace_context.trace_id if trace_context else None,
            run_id=trace_context.run_id if trace_context else None,
            summary={"requested_agent": requested_agent, "session_created": existing is None},
            metadata={"sprint": "FUNC-SPRINT-86", **(metadata or {})},
        )
        if existing is None:
            session = AgentSession(
                session_id=effective_session_id,
                created_at=now,
                updated_at=now,
                agent_ids=[agent_id],
                events=[event],
                memory={
                    "operational_context": {
                        "last_agent_id": agent_id,
                        "last_target": target,
                        "last_dry_run": dry_run,
                    }
                },
                metadata={
                    "retention_policy": "local-short-lived-operational-memory",
                    "semantic_memory_enabled": False,
                    "rag_enabled": False,
                    "raw_prompts_stored": False,
                    "raw_outputs_stored": False,
                    "redaction_applied": True,
                },
            )
        else:
            agent_ids = list(dict.fromkeys([*existing.agent_ids, agent_id]))
            memory = dict(existing.memory)
            memory["operational_context"] = {
                "last_agent_id": agent_id,
                "last_target": target,
                "last_dry_run": dry_run,
            }
            session = AgentSession(
                session_id=existing.session_id,
                created_at=existing.created_at,
                updated_at=now,
                status=existing.status,
                retention_days=existing.retention_days,
                workspace=existing.workspace,
                agent_ids=agent_ids,
                events=[*existing.events, event],
                memory=memory,
                metadata={**existing.metadata, "redaction_applied": True},
            )
        self._write_session(session)
        self._record_localstore_event(session, event)
        return session

    def complete_session(
        self,
        *,
        session_id: str,
        agent_id: str,
        ok: bool,
        dry_run: bool,
        target: str | None,
        trace_context: TraceContext | None = None,
        findings_total: int = 0,
        suggestions_total: int = 0,
        tool_calls_total: int = 0,
        model_calls_total: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> AgentSession:
        session = self._load(session_id)
        now = utc_now_iso()
        event = AgentSessionEvent(
            event_id=uuid.uuid4().hex,
            event_type="agent.session.completed",
            timestamp=now,
            agent_id=agent_id,
            command="agent run",
            target=target,
            ok=ok,
            dry_run=dry_run,
            trace_id=trace_context.trace_id if trace_context else None,
            run_id=trace_context.run_id if trace_context else None,
            summary={
                "findings_total": findings_total,
                "suggestions_total": suggestions_total,
                "tool_calls_total": tool_calls_total,
                "model_calls_total": model_calls_total,
            },
            metadata={"sprint": "FUNC-SPRINT-86", **(metadata or {})},
        )
        memory = dict(session.memory)
        memory["last_result"] = {
            "agent_id": agent_id,
            "ok": bool(ok),
            "findings_total": int(findings_total),
            "suggestions_total": int(suggestions_total),
            "tool_calls_total": int(tool_calls_total),
            "model_calls_total": int(model_calls_total),
        }
        updated = AgentSession(
            session_id=session.session_id,
            created_at=session.created_at,
            updated_at=now,
            status="completed" if ok else "completed_with_findings",
            retention_days=session.retention_days,
            workspace=session.workspace,
            agent_ids=session.agent_ids,
            events=[*session.events, event],
            memory=memory,
            metadata={**session.metadata, "redaction_applied": True},
        )
        self._write_session(updated)
        self._record_localstore_event(updated, event)
        return updated

    def inspect(self, options: AgentSessionInspectOptions) -> CommandResult:
        if not _valid_session_id(options.session_id):
            finding = Finding(
                id="AGENT_SESSION_INVALID_ID",
                message="Session id must match agsess_<32 lowercase hex characters>.",
                severity=Severity.BLOCK,
                metadata={"session_id": options.session_id},
            )
            return CommandResult(
                command="agent session inspect",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Agent session inspection blocked because the session id is invalid.",
                data={"summary": {"session_found": False}},
                findings=[finding],
            )
        path = self._session_path(options.session_id)
        if not path.exists():
            finding = Finding(
                id="AGENT_SESSION_NOT_FOUND",
                message="Requested AgentSession does not exist in the local workspace.",
                severity=Severity.BLOCK,
                path=_relative(path, self.root),
            )
            return CommandResult(
                command="agent session inspect",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Agent session was not found.",
                data={"summary": {"session_found": False, "session_id": options.session_id}},
                findings=[finding],
            )
        session = self._load(options.session_id)
        payload = session.to_dict()
        if options.include_events:
            safe_limit = max(1, min(int(options.limit), 200))
            payload["events"] = payload.get("events", [])[-safe_limit:]
            payload["summary"]["events_returned"] = len(payload["events"])
            payload["summary"]["events_total"] = len(session.events)
        else:
            payload.pop("events", None)
            payload["summary"]["events_returned"] = 0
            payload["summary"]["events_total"] = len(session.events)
        payload["summary"].update(
            {
                "session_found": True,
                "storage_path": _relative(path, self.root),
                "localstore_projection_used": True,
                "tracestore_compatible": True,
                "redaction_applied": True,
            }
        )
        return CommandResult(
            command="agent session inspect",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Agent session inspection passed.",
            data=payload,
            findings=[],
        )

    def list_sessions(self, *, limit: int = 20) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 200))
        if not self.session_dir.exists():
            return []
        rows: list[dict[str, Any]] = []
        for path in sorted(self.session_dir.glob("agsess_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:safe_limit]:
            try:
                session = AgentSession.from_dict(json.loads(path.read_text(encoding="utf-8")))
                payload = session.to_dict()
                payload.pop("events", None)
                rows.append(payload)
            except Exception:
                continue
        return rows

    def _write_session(self, session: AgentSession) -> None:
        path = self._session_path(session.session_id)
        decision = self.path_guard.evaluate(path, action="write")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            raise ValueError(f"PathGuard blocked AgentSession persistence: {decision.reason}")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(session.to_dict(), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    def _record_localstore_event(self, session: AgentSession, event: AgentSessionEvent) -> None:
        try:
            LocalStore(self.root).record_event(
                event_type=event.event_type,
                command=event.command or "agent session",
                status="PASS" if event.ok is not False else "FAIL",
                ok=event.ok,
                exit_code=0 if event.ok is not False else 1,
                subject=session.session_id,
                summary={"session_id": session.session_id, **event.summary},
                metadata={"component": "AgentSessionStore", **event.metadata},
                run_id=event.run_id,
                trace_id=event.trace_id,
            )
        except Exception:
            # Session JSON remains the source of truth. SQLite projection must not
            # change agent execution semantics.
            pass

    def _load_optional(self, session_id: str) -> AgentSession | None:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        return self._load(session_id)

    def _load(self, session_id: str) -> AgentSession:
        if not _valid_session_id(session_id):
            raise ValueError("Invalid AgentSession id.")
        path = self._session_path(session_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return AgentSession.from_dict(payload)

    def _session_path(self, session_id: str) -> Path:
        if not _valid_session_id(session_id):
            raise ValueError("Invalid AgentSession id.")
        return (self.session_dir / f"{session_id}.json").resolve()

    def _resolve_session_dir(self, session_dir: str | Path) -> Path:
        candidate = Path(session_dir)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("AgentSessionStore only writes inside the DevPilot workspace root.") from exc
        return candidate

    def _normalize_or_create_session_id(self, session_id: str | None) -> str:
        if session_id is None or str(session_id).strip() == "":
            return new_session_id()
        candidate = str(session_id).strip()
        if not _valid_session_id(candidate):
            raise ValueError("Invalid AgentSession id.")
        return candidate


def inspect_agent_session(root: Path, *, session_id: str, include_events: bool = True, limit: int = 20) -> CommandResult:
    return AgentSessionStore(root).inspect(AgentSessionInspectOptions(session_id=session_id, include_events=include_events, limit=limit))


def _valid_session_id(session_id: str) -> bool:
    return bool(SESSION_ID_PATTERN.match(str(session_id)))


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
