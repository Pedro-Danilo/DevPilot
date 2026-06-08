from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

DEFAULT_DB_PATH = ".devpilot/devpilot.db"
SCHEMA_VERSION = "0001_local_store_v0"


@dataclass(frozen=True)
class StorePaths:
    """Resolved paths used by DevPilot local persistence.

    FUNC-SPRINT-10 introduces SQLite persistence as a local-first operational
    state store. The default database lives under `.devpilot/devpilot.db` and is
    generated at runtime, not shipped as a static artifact.
    """

    root: Path
    db_path: Path

    def to_dict(self) -> dict[str, str]:
        return {"root": ".", "db_path": _relative(self.db_path, self.root)}


@dataclass(frozen=True)
class StoreStatus:
    """Current LocalStore status and table counters."""

    paths: StorePaths
    initialized: bool
    schema_version: str | None = None
    tables: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "paths": self.paths.to_dict(),
            "summary": {
                "initialized": self.initialized,
                "schema_version": self.schema_version,
                "tables_total": len(self.tables),
            },
            "tables": self.tables,
            "counts": self.counts,
        }


class LocalStore:
    """SQLite-backed local operational state store.

    The store is deliberately dependency-free and uses Python's standard
    `sqlite3` module. It persists command runs, findings, gate summaries,
    events, approvals and cost events. FUNC-SPRINT-10 is an initial version:
    no encryption, no retention policy, no concurrent writer coordination and
    no remote synchronization are implemented yet.
    """

    def __init__(self, root: Path, *, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.root = root.resolve()
        self.db_path = self._resolve_db_path(db_path)
        self.paths = StorePaths(root=self.root, db_path=self.db_path)

    def initialize(self) -> CommandResult:
        """Create the SQLite database and schema if needed.

        The migration is idempotent. Running this method repeatedly keeps the
        same schema version and does not delete existing operational history.
        """

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            self._apply_schema(conn)
            status = self.status()
        return CommandResult(
            command="state init",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local SQLite store initialized.",
            data=status.data,
            findings=[],
        )

    def status(self) -> CommandResult:
        """Return LocalStore initialization status without forcing writes."""

        if not self.db_path.exists():
            finding = Finding(
                id="LOCAL_STORE_NOT_INITIALIZED",
                message="Local SQLite store does not exist yet. Run state init or any persisted gate command.",
                severity=Severity.WARNING,
                path=_relative(self.db_path, self.root),
            )
            status = StoreStatus(paths=self.paths, initialized=False)
            return CommandResult(
                command="state status",
                ok=True,
                exit_code=ExitCode.PASS,
                message="Local SQLite store is not initialized yet.",
                data=status.to_dict(),
                findings=[finding],
            )

        with self._connect() as conn:
            tables = self._list_tables(conn)
            schema_version = self._schema_version(conn)
            counts = {table: self._count_rows(conn, table) for table in _tracked_tables() if table in tables}
        status = StoreStatus(paths=self.paths, initialized=True, schema_version=schema_version, tables=tables, counts=counts)
        return CommandResult(
            command="state status",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local SQLite store status passed.",
            data=status.to_dict(),
            findings=[],
        )

    def record_command_result(
        self,
        result: CommandResult,
        *,
        subject: str | Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Persist one CommandResult and return its run_id.

        This method is used by CLI gates/validators after report generation and
        event logging. It stores the full redacted command payload plus a query-
        friendly projection for findings and gate summaries.
        """

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        run_id = uuid.uuid4().hex
        now = utc_now_iso()
        subject_text = _display_subject(subject, self.root)
        result_payload = result.to_dict()
        with self._connect() as conn:
            self._apply_schema(conn)
            conn.execute(
                """
                INSERT INTO runs (
                    run_id, command, ok, exit_code, message, subject,
                    started_at, completed_at, metadata_json, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    result.command,
                    int(result.ok),
                    int(result.exit_code),
                    result.message,
                    subject_text,
                    now,
                    now,
                    _json(metadata or {}),
                    _json(result_payload),
                ),
            )
            for finding in result.findings:
                conn.execute(
                    """
                    INSERT INTO findings (
                        run_id, finding_id, severity, message, path, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        finding.id,
                        finding.severity.value,
                        finding.message,
                        finding.path,
                        _json(finding.metadata),
                    ),
                )
            conn.execute(
                """
                INSERT INTO gates (
                    run_id, gate_name, status, ok, subject, summary_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    result.command,
                    _status_from_result(result),
                    int(result.ok),
                    subject_text,
                    _json(_summary_from_result(result)),
                ),
            )
            conn.commit()
        return run_id

    def record_event(
        self,
        *,
        event_type: str,
        command: str,
        status: str | None = None,
        ok: bool | None = None,
        exit_code: int | None = None,
        subject: str | Path | None = None,
        summary: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> str:
        """Persist one event projection in SQLite.

        This is a v0 companion to JSONL EventLog. FUNC-SPRINT-10 exposes the
        table and API but does not yet mirror every JSONL line automatically.
        """

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        event_id = uuid.uuid4().hex
        with self._connect() as conn:
            self._apply_schema(conn)
            conn.execute(
                """
                INSERT INTO events (
                    event_id, run_id, event_type, command, status, ok, exit_code,
                    timestamp, subject, summary_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    run_id,
                    event_type,
                    command,
                    status,
                    None if ok is None else int(ok),
                    exit_code,
                    utc_now_iso(),
                    _display_subject(subject, self.root),
                    _json(summary or {}),
                    _json(metadata or {}),
                ),
            )
            conn.commit()
        return event_id

    def record_cost_event(
        self,
        *,
        provider: str,
        estimated_cost_usd: float = 0.0,
        actual_cost_usd: float = 0.0,
        budget_limit_usd: float = 0.0,
        budget_used_usd: float = 0.0,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Persist a local cost event projection for future CostGuard audits."""

        cost_event_id = uuid.uuid4().hex
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            self._apply_schema(conn)
            conn.execute(
                """
                INSERT INTO cost_events (
                    cost_event_id, run_id, provider, estimated_cost_usd,
                    actual_cost_usd, budget_limit_usd, budget_used_usd,
                    timestamp, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cost_event_id,
                    run_id,
                    provider,
                    estimated_cost_usd,
                    actual_cost_usd,
                    budget_limit_usd,
                    budget_used_usd,
                    utc_now_iso(),
                    _json(metadata or {}),
                ),
            )
            conn.commit()
        return cost_event_id

    def list_runs(self, *, limit: int = 10) -> CommandResult:
        """Return recent runs from local SQLite history."""

        safe_limit = max(1, min(int(limit), 100))
        if not self.db_path.exists():
            return CommandResult(
                command="history list",
                ok=True,
                exit_code=ExitCode.PASS,
                message="No local SQLite history database found.",
                data={"runs": [], "summary": {"runs_returned": 0, "limit": safe_limit}, "paths": self.paths.to_dict()},
                findings=[
                    Finding(
                        id="LOCAL_STORE_NOT_INITIALIZED",
                        message="No history is available until the local store is initialized.",
                        severity=Severity.INFO,
                        path=_relative(self.db_path, self.root),
                    )
                ],
            )
        with self._connect() as conn:
            self._apply_schema(conn)
            rows = conn.execute(
                """
                SELECT run_id, command, ok, exit_code, message, subject,
                       started_at, completed_at
                FROM runs
                ORDER BY completed_at DESC, rowid DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        runs = [dict(row) | {"ok": bool(row["ok"])} for row in rows]
        return CommandResult(
            command="history list",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local history listed.",
            data={"runs": runs, "summary": {"runs_returned": len(runs), "limit": safe_limit}, "paths": self.paths.to_dict()},
            findings=[],
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _apply_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, utc_now_iso()),
        )
        conn.commit()

    def _resolve_db_path(self, db_path: str | Path) -> Path:
        candidate = Path(db_path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("LocalStore database path must remain inside the DevPilot project root.") from exc
        return candidate

    def _list_tables(self, conn: sqlite3.Connection) -> list[str]:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return [str(row["name"]) for row in rows]

    def _schema_version(self, conn: sqlite3.Connection) -> str | None:
        try:
            row = conn.execute("SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1").fetchone()
        except sqlite3.OperationalError:
            return None
        return None if row is None else str(row["version"])

    def _count_rows(self, conn: sqlite3.Connection, table: str) -> int:
        return int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    command TEXT NOT NULL,
    ok INTEGER NOT NULL CHECK (ok IN (0, 1)),
    exit_code INTEGER NOT NULL,
    message TEXT NOT NULL,
    subject TEXT,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_runs_completed_at ON runs(completed_at);
CREATE INDEX IF NOT EXISTS idx_runs_command ON runs(command);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    finding_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    path TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_findings_run_id ON findings(run_id);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);

CREATE TABLE IF NOT EXISTS gates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    gate_name TEXT NOT NULL,
    status TEXT NOT NULL,
    ok INTEGER NOT NULL CHECK (ok IN (0, 1)),
    subject TEXT,
    summary_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_gates_run_id ON gates(run_id);
CREATE INDEX IF NOT EXISTS idx_gates_name ON gates(gate_name);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT,
    event_type TEXT NOT NULL,
    command TEXT NOT NULL,
    status TEXT,
    ok INTEGER CHECK (ok IN (0, 1)),
    exit_code INTEGER,
    timestamp TEXT NOT NULL,
    subject TEXT,
    summary_json TEXT NOT NULL DEFAULT '{}',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    subject TEXT,
    status TEXT NOT NULL,
    requested_at TEXT NOT NULL,
    approved_at TEXT,
    approver TEXT,
    reason TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);

CREATE TABLE IF NOT EXISTS cost_events (
    cost_event_id TEXT PRIMARY KEY,
    run_id TEXT,
    provider TEXT NOT NULL,
    estimated_cost_usd REAL NOT NULL DEFAULT 0.0,
    actual_cost_usd REAL NOT NULL DEFAULT 0.0,
    budget_limit_usd REAL NOT NULL DEFAULT 0.0,
    budget_used_usd REAL NOT NULL DEFAULT 0.0,
    timestamp TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_cost_events_provider ON cost_events(provider);
CREATE INDEX IF NOT EXISTS idx_cost_events_timestamp ON cost_events(timestamp);
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _tracked_tables() -> tuple[str, ...]:
    return ("runs", "findings", "gates", "events", "approvals", "cost_events")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _display_subject(subject: str | Path | None, root: Path) -> str | None:
    if subject is None:
        return None
    candidate = Path(subject)
    if candidate.is_absolute():
        return _relative(candidate, root)
    return str(candidate).replace("\\", "/")


def _status_from_result(result: CommandResult) -> str:
    if result.ok:
        return "PASS"
    if int(result.exit_code) == int(ExitCode.BLOCK):
        return "BLOCK"
    if int(result.exit_code) == int(ExitCode.ERROR):
        return "ERROR"
    return "FAIL"


def _summary_from_result(result: CommandResult) -> dict[str, Any]:
    data = result.data or {}
    if isinstance(data.get("summary"), dict):
        return dict(data["summary"])
    summary: dict[str, Any] = {}
    for key in ("strict", "ok", "path", "status", "has_frontmatter", "heading_count", "h1_count"):
        if key in data:
            summary[key] = data[key]
    for list_key, count_key in (
        ("checks", "checks_total"),
        ("artifacts", "artifacts_total"),
        ("standards", "standards_total"),
        ("runs", "runs_total"),
    ):
        if isinstance(data.get(list_key), list):
            summary[count_key] = len(data[list_key])
    return summary
