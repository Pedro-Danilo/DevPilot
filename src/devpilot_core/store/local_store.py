from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Iterable, Iterator

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

DEFAULT_DB_PATH = ".devpilot/devpilot.db"
SCHEMA_VERSION = "0004_metrics_collector_v1"


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
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> str:
        """Persist one event projection in SQLite.

        FUNC-SPRINT-58 keeps the historical event projection compatible while
        adding optional trace/span correlation columns. Callers that do not
        provide trace metadata get the exact v1 behavior.
        """

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        event_id = uuid.uuid4().hex
        with self._connect() as conn:
            self._apply_schema(conn)
            if run_id:
                self._ensure_run_exists(conn, run_id=run_id, command=command, ok=ok, exit_code=exit_code, status=status)
            conn.execute(
                """
                INSERT INTO events (
                    event_id, run_id, trace_id, span_id, parent_span_id,
                    event_type, command, status, ok, exit_code,
                    timestamp, subject, summary_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    run_id,
                    trace_id,
                    span_id,
                    parent_span_id,
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

    def record_span(self, span: Any) -> str:
        """Persist one redacted SpanRecord-compatible payload.

        The method accepts a SpanRecord or a plain dictionary with the same
        serialized shape. It is intentionally dependency-light to avoid a hard
        coupling from the store package back into observability models.
        """

        payload = span.to_dict() if hasattr(span, "to_dict") else dict(span)
        span_id = str(payload["span_id"])
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            self._apply_schema(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO spans (
                    span_id, trace_id, run_id, parent_span_id, name, span_type,
                    status, severity, subject, started_at, ended_at, duration_ms,
                    payload_json, metadata_json, findings_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    span_id,
                    str(payload["trace_id"]),
                    payload.get("run_id"),
                    payload.get("parent_span_id"),
                    str(payload["name"]),
                    str(payload["span_type"]),
                    str(payload["status"]),
                    str(payload.get("severity") or "info"),
                    payload.get("subject"),
                    str(payload["started_at"]),
                    payload.get("ended_at"),
                    payload.get("duration_ms"),
                    _json(payload.get("payload") or {}),
                    _json(payload.get("metadata") or {}),
                    _json(payload.get("findings") or []),
                ),
            )
            conn.commit()
        return span_id

    def list_spans(self, *, trace_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent spans, optionally scoped by trace id."""

        safe_limit = max(1, min(int(limit), 100))
        if not self.db_path.exists():
            return []
        with self._connect() as conn:
            self._apply_schema(conn)
            if trace_id:
                rows = conn.execute(
                    """
                    SELECT * FROM spans
                    WHERE trace_id = ?
                    ORDER BY started_at ASC, rowid ASC
                    LIMIT ?
                    """,
                    (trace_id, safe_limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM spans
                    ORDER BY started_at DESC, rowid DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
        return [_span_row_to_dict(row) for row in rows]

    def list_events(self, *, trace_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent event projections, optionally scoped by trace id."""

        safe_limit = max(1, min(int(limit), 100))
        if not self.db_path.exists():
            return []
        with self._connect() as conn:
            self._apply_schema(conn)
            if trace_id:
                rows = conn.execute(
                    """
                    SELECT * FROM events
                    WHERE trace_id = ?
                    ORDER BY timestamp ASC, rowid ASC
                    LIMIT ?
                    """,
                    (trace_id, safe_limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM events
                    ORDER BY timestamp DESC, rowid DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
        return [_event_row_to_dict(row) for row in rows]

    def record_metric(self, metric: Any) -> str:
        """Persist one MetricRecord-compatible payload.

        FUNC-SPRINT-59 stores metrics as local SQLite projections. The method
        accepts a MetricRecord or a dictionary to keep LocalStore independent
        from the observability model layer.
        """

        payload = metric.to_dict() if hasattr(metric, "to_dict") else dict(metric)
        metric_id = str(payload.get("metric_id") or uuid.uuid4().hex)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            self._apply_schema(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO metrics (
                    metric_id, trace_id, run_id, span_id, name, value, unit,
                    category, operation, command, status, ok, severity,
                    provider, model, task, timestamp, estimated, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metric_id,
                    payload.get("trace_id"),
                    payload.get("run_id"),
                    payload.get("span_id"),
                    str(payload["name"]),
                    float(payload.get("value") or 0.0),
                    payload.get("unit"),
                    str(payload.get("category") or "command"),
                    payload.get("operation"),
                    payload.get("command"),
                    payload.get("status"),
                    None if payload.get("ok") is None else int(bool(payload.get("ok"))),
                    str(payload.get("severity") or "info"),
                    payload.get("provider"),
                    payload.get("model"),
                    payload.get("task"),
                    str(payload.get("timestamp") or utc_now_iso()),
                    int(bool(payload.get("estimated", False))),
                    _json(payload.get("metadata") or {}),
                ),
            )
            conn.commit()
        return metric_id

    def list_metrics(self, *, category: str | None = None, name: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent metrics, optionally filtered by category or name."""

        safe_limit = max(1, min(int(limit), 500))
        if not self.db_path.exists():
            return []
        filters: list[str] = []
        values: list[Any] = []
        if category:
            filters.append("category = ?")
            values.append(category)
        if name:
            filters.append("name = ?")
            values.append(name)
        where = " WHERE " + " AND ".join(filters) if filters else ""
        query = f"""
            SELECT * FROM metrics
            {where}
            ORDER BY timestamp DESC, rowid DESC
            LIMIT ?
        """
        values.append(safe_limit)
        with self._connect() as conn:
            self._apply_schema(conn)
            rows = conn.execute(query, tuple(values)).fetchall()
        return [_metric_row_to_dict(row) for row in rows]

    def metrics_summary(self) -> dict[str, Any]:
        """Return aggregate local metric counters for AgentOps dashboards."""

        if not self.db_path.exists():
            return {
                "initialized": False,
                "metrics_total": 0,
                "operations_total": 0,
                "categories": {},
                "statuses": {},
                "providers": {},
                "estimated_cost_total_usd": 0.0,
                "tokens_estimated_total": 0,
            }
        with self._connect() as conn:
            self._apply_schema(conn)
            total_row = conn.execute("SELECT COUNT(*) AS metrics_total FROM metrics").fetchone()
            category_rows = conn.execute(
                "SELECT category, COUNT(*) AS total FROM metrics GROUP BY category ORDER BY category"
            ).fetchall()
            status_rows = conn.execute(
                """
                SELECT COALESCE(status, 'UNKNOWN') AS status, COALESCE(SUM(value), 0.0) AS total
                FROM metrics
                WHERE unit = 'count'
                GROUP BY COALESCE(status, 'UNKNOWN')
                ORDER BY status
                """
            ).fetchall()
            provider_rows = conn.execute(
                """
                SELECT provider, COUNT(*) AS total
                FROM metrics
                WHERE provider IS NOT NULL AND provider != ''
                GROUP BY provider
                ORDER BY provider
                """
            ).fetchall()
            operations_row = conn.execute(
                "SELECT COALESCE(SUM(value), 0.0) AS total FROM metrics WHERE unit = 'count'"
            ).fetchone()
            cost_row = conn.execute(
                "SELECT COALESCE(SUM(value), 0.0) AS total FROM metrics WHERE name = 'devpilot.model.cost_estimate_usd'"
            ).fetchone()
            token_row = conn.execute(
                "SELECT COALESCE(SUM(value), 0.0) AS total FROM metrics WHERE name = 'devpilot.model.tokens_estimated'"
            ).fetchone()
        return {
            "initialized": True,
            "metrics_total": int(total_row["metrics_total"] or 0),
            "operations_total": int(operations_row["total"] or 0),
            "categories": {str(row["category"]): int(row["total"] or 0) for row in category_rows},
            "statuses": {str(row["status"]): int(row["total"] or 0) for row in status_rows},
            "providers": {str(row["provider"]): int(row["total"] or 0) for row in provider_rows},
            "estimated_cost_total_usd": round(float(cost_row["total"] or 0.0), 8),
            "tokens_estimated_total": int(token_row["total"] or 0),
        }

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

    def list_cost_events(self, *, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent model budget/cost events without raw prompt payloads.

        FUNC-SPRINT-48 exposes a read path for the existing `cost_events`
        projection. The method returns metadata after JSON parsing, but it never
        joins against full command results, so prompts/completions stored
        elsewhere are not surfaced by the budget ledger.
        """

        safe_limit = max(1, min(int(limit), 100))
        if not self.db_path.exists():
            return []
        with self._connect() as conn:
            self._apply_schema(conn)
            rows = conn.execute(
                """
                SELECT cost_event_id, run_id, provider, estimated_cost_usd,
                       actual_cost_usd, budget_limit_usd, budget_used_usd,
                       timestamp, metadata_json
                FROM cost_events
                ORDER BY timestamp DESC, rowid DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            {
                "cost_event_id": str(row["cost_event_id"]),
                "run_id": row["run_id"],
                "provider": str(row["provider"]),
                "estimated_cost_usd": float(row["estimated_cost_usd"] or 0.0),
                "actual_cost_usd": float(row["actual_cost_usd"] or 0.0),
                "budget_limit_usd": float(row["budget_limit_usd"] or 0.0),
                "budget_used_usd": float(row["budget_used_usd"] or 0.0),
                "timestamp": str(row["timestamp"]),
                "metadata": _load_json(row["metadata_json"], {}),
            }
            for row in rows
        ]

    def cost_events_summary(self) -> dict[str, Any]:
        """Return aggregate budget ledger status for local model governance."""

        if not self.db_path.exists():
            return {
                "initialized": False,
                "events_total": 0,
                "providers_total": 0,
                "estimated_cost_total_usd": 0.0,
                "actual_cost_total_usd": 0.0,
                "external_cost_total_usd": 0.0,
                "local_cost_total_usd": 0.0,
                "compute_estimate_units_total": 0,
            }
        with self._connect() as conn:
            self._apply_schema(conn)
            row = conn.execute(
                """
                SELECT COUNT(*) AS events_total,
                       COUNT(DISTINCT provider) AS providers_total,
                       COALESCE(SUM(estimated_cost_usd), 0.0) AS estimated_cost_total_usd,
                       COALESCE(SUM(actual_cost_usd), 0.0) AS actual_cost_total_usd
                FROM cost_events
                """
            ).fetchone()
            events = conn.execute("SELECT provider, metadata_json FROM cost_events").fetchall()
        compute_units = 0
        external_cost = 0.0
        local_cost = 0.0
        for event in events:
            metadata = _load_json(event["metadata_json"], {})
            compute_units += int(metadata.get("compute_estimate_units") or 0)
            estimated = float(metadata.get("monetary_cost_estimate_usd") or 0.0)
            if metadata.get("external_api_used"):
                external_cost += estimated
            else:
                local_cost += estimated
        return {
            "initialized": True,
            "events_total": int(row["events_total"] or 0),
            "providers_total": int(row["providers_total"] or 0),
            "estimated_cost_total_usd": round(float(row["estimated_cost_total_usd"] or 0.0), 8),
            "actual_cost_total_usd": round(float(row["actual_cost_total_usd"] or 0.0), 8),
            "external_cost_total_usd": round(external_cost, 8),
            "local_cost_total_usd": round(local_cost, 8),
            "compute_estimate_units_total": compute_units,
        }

    def create_approval(self, record: dict[str, Any]) -> tuple[bool, "ApprovalRecord"]:
        """Persist an approval record idempotently and return (created, record).

        FUNC-SPRINT-28 strengthens the old structural approvals table into an
        operational approval store. A duplicate approval_id returns the existing
        row unchanged; it never overwrites approval state implicitly.
        """

        from devpilot_core.approval.models import ApprovalRecord

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            self._apply_schema(conn)
            existing = self._get_approval_row(conn, str(record["approval_id"]))
            if existing is not None:
                return False, ApprovalRecord.from_dict(existing)
            conn.execute(
                """
                INSERT INTO approvals (
                    approval_id, subject, tool_id, action, status, actor, reason,
                    scope_json, created_at, updated_at, expires_at, decision_at,
                    decided_by, metadata_json, requested_at, approved_at, approver
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["approval_id"],
                    record["subject"],
                    record["tool_id"],
                    record["action"],
                    record["status"],
                    record["actor"],
                    record["reason"],
                    _json(record.get("scope") or {}),
                    record["created_at"],
                    record["updated_at"],
                    record["expires_at"],
                    record.get("decision_at"),
                    record.get("decided_by"),
                    _json(record.get("metadata") or {}),
                    record["created_at"],
                    record.get("decision_at") if record.get("status") == "approved" else None,
                    record.get("decided_by"),
                ),
            )
            conn.commit()
            stored = self._get_approval_row(conn, str(record["approval_id"]))
        assert stored is not None
        return True, ApprovalRecord.from_dict(stored)

    def get_approval(self, approval_id: str) -> "ApprovalRecord | None":
        """Return one approval record by ID, or None when absent."""

        from devpilot_core.approval.models import ApprovalRecord

        if not self.db_path.exists():
            return None
        with self._connect() as conn:
            self._apply_schema(conn)
            row = self._get_approval_row(conn, approval_id)
        return None if row is None else ApprovalRecord.from_dict(row)

    def list_approvals(
        self,
        *,
        status: str | None = None,
        tool_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list["ApprovalRecord"]:
        """List approval records with optional filters."""

        from devpilot_core.approval.models import ApprovalRecord

        if not self.db_path.exists():
            return []
        filters: list[str] = []
        values: list[Any] = []
        if status:
            filters.append("status = ?")
            values.append(status)
        if tool_id:
            filters.append("tool_id = ?")
            values.append(tool_id)
        if action:
            filters.append("action = ?")
            values.append(action)
        where = " WHERE " + " AND ".join(filters) if filters else ""
        safe_limit = max(1, min(int(limit), 500))
        query = f"""
            SELECT * FROM approvals
            {where}
            ORDER BY created_at DESC, approval_id DESC
            LIMIT ?
        """
        values.append(safe_limit)
        with self._connect() as conn:
            self._apply_schema(conn)
            rows = conn.execute(query, tuple(values)).fetchall()
        return [ApprovalRecord.from_dict(self._approval_row_to_dict(row)) for row in rows]

    def update_approval(self, record: dict[str, Any]) -> "ApprovalRecord":
        """Persist a controlled approval state transition."""

        from devpilot_core.approval.models import ApprovalRecord

        with self._connect() as conn:
            self._apply_schema(conn)
            conn.execute(
                """
                UPDATE approvals
                SET status = ?, reason = ?, updated_at = ?, expires_at = ?,
                    decision_at = ?, decided_by = ?, approved_at = ?, approver = ?,
                    metadata_json = ?
                WHERE approval_id = ?
                """,
                (
                    record["status"],
                    record["reason"],
                    record["updated_at"],
                    record["expires_at"],
                    record.get("decision_at"),
                    record.get("decided_by"),
                    record.get("decision_at") if record.get("status") == "approved" else None,
                    record.get("decided_by"),
                    _json(record.get("metadata") or {}),
                    record["approval_id"],
                ),
            )
            conn.commit()
            stored = self._get_approval_row(conn, str(record["approval_id"]))
        if stored is None:
            raise KeyError(f"Approval not found: {record['approval_id']}")
        return ApprovalRecord.from_dict(stored)

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

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Open a SQLite connection and always close it after use.

        Python's sqlite3 connection context manager commits or rolls back the
        transaction, but it does not close the file handle. On Windows this can
        leave `.devpilot/devpilot.db` locked long enough to break cleanup of
        temporary security-readiness workspaces. DevPilot therefore wraps the
        connection in an explicit closing context manager.
        """

        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _apply_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(SCHEMA_SQL)
        self._migrate_approvals_v1(conn)
        self._migrate_observability_v2(conn)
        self._migrate_metrics_v1(conn)
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, utc_now_iso()),
        )
        conn.commit()

    def _ensure_run_exists(
        self,
        conn: sqlite3.Connection,
        *,
        run_id: str,
        command: str,
        ok: bool | None = None,
        exit_code: int | None = None,
        status: str | None = None,
    ) -> None:
        """Create a minimal run row when trace-only events reference run_id.

        The events table keeps its historical foreign key to runs. TraceStore
        can receive a TraceContext before a full CommandResult exists, so Sprint
        58 records a minimal placeholder run rather than dropping correlation.
        """

        exists = conn.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if exists:
            return
        now = utc_now_iso()
        ok_value = True if ok is None else bool(ok)
        exit_value = 0 if exit_code is None else int(exit_code)
        message = status or ("PASS" if ok_value else "FAIL")
        conn.execute(
            """
            INSERT INTO runs (
                run_id, command, ok, exit_code, message, subject,
                started_at, completed_at, metadata_json, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                command,
                int(ok_value),
                exit_value,
                f"TraceStore placeholder run: {message}",
                None,
                now,
                now,
                _json({"component": "TraceStore", "placeholder": True}),
                _json({"command": command, "ok": ok_value, "exit_code": exit_value, "message": message}),
            ),
        )

    def _migrate_approvals_v1(self, conn: sqlite3.Connection) -> None:
        """Add Sprint 28 operational approval columns without deleting old data."""

        columns = {str(row["name"]) for row in conn.execute("PRAGMA table_info(approvals)").fetchall()}
        additions: dict[str, str] = {
            "tool_id": "TEXT NOT NULL DEFAULT ''",
            "actor": "TEXT NOT NULL DEFAULT ''",
            "scope_json": "TEXT NOT NULL DEFAULT '{}'",
            "created_at": "TEXT",
            "updated_at": "TEXT",
            "expires_at": "TEXT",
            "decision_at": "TEXT",
            "decided_by": "TEXT",
        }
        for column, definition in additions.items():
            if column not in columns:
                conn.execute(f"ALTER TABLE approvals ADD COLUMN {column} {definition}")
        conn.execute("UPDATE approvals SET tool_id = action WHERE tool_id = '' OR tool_id IS NULL")
        conn.execute("UPDATE approvals SET actor = COALESCE(approver, '') WHERE actor = '' OR actor IS NULL")
        conn.execute("UPDATE approvals SET created_at = requested_at WHERE created_at IS NULL")
        conn.execute("UPDATE approvals SET updated_at = COALESCE(approved_at, requested_at) WHERE updated_at IS NULL")
        conn.execute("UPDATE approvals SET decision_at = approved_at WHERE decision_at IS NULL AND approved_at IS NOT NULL")
        conn.execute("UPDATE approvals SET decided_by = approver WHERE decided_by IS NULL AND approver IS NOT NULL")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_approvals_tool_action ON approvals(tool_id, action)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_approvals_expires_at ON approvals(expires_at)")

    def _migrate_observability_v2(self, conn: sqlite3.Connection) -> None:
        """Add Sprint 58 trace correlation columns idempotently."""

        event_columns = {str(row["name"]) for row in conn.execute("PRAGMA table_info(events)").fetchall()}
        additions: dict[str, str] = {
            "trace_id": "TEXT",
            "span_id": "TEXT",
            "parent_span_id": "TEXT",
        }
        for column, definition in additions.items():
            if column not in event_columns:
                conn.execute(f"ALTER TABLE events ADD COLUMN {column} {definition}")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_trace_id ON events(trace_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spans_parent_span_id ON spans(parent_span_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_trace_id ON metrics(trace_id)")

    def _migrate_metrics_v1(self, conn: sqlite3.Connection) -> None:
        """Add Sprint 59 metric projection columns idempotently."""

        metric_columns = {str(row["name"]) for row in conn.execute("PRAGMA table_info(metrics)").fetchall()}
        additions: dict[str, str] = {
            "span_id": "TEXT",
            "category": "TEXT NOT NULL DEFAULT 'command'",
            "operation": "TEXT",
            "command": "TEXT",
            "status": "TEXT",
            "ok": "INTEGER CHECK (ok IN (0, 1))",
            "severity": "TEXT NOT NULL DEFAULT 'info'",
            "provider": "TEXT",
            "model": "TEXT",
            "task": "TEXT",
            "estimated": "INTEGER NOT NULL DEFAULT 0 CHECK (estimated IN (0, 1))",
        }
        for column, definition in additions.items():
            if column not in metric_columns:
                conn.execute(f"ALTER TABLE metrics ADD COLUMN {column} {definition}")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_category ON metrics(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_status ON metrics(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_provider ON metrics(provider)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_run_id ON metrics(run_id)")

    def _get_approval_row(self, conn: sqlite3.Connection, approval_id: str) -> dict[str, Any] | None:
        row = conn.execute("SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)).fetchone()
        return None if row is None else self._approval_row_to_dict(row)

    def _approval_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        metadata = _load_json(row["metadata_json"], {})
        scope = _load_json(row["scope_json"], {})
        return {
            "approval_id": row["approval_id"],
            "subject": row["subject"] or "",
            "tool_id": row["tool_id"] or row["action"] or "",
            "action": row["action"] or "",
            "status": row["status"],
            "actor": row["actor"] or row["approver"] or "",
            "reason": row["reason"] or "",
            "scope": scope,
            "created_at": row["created_at"] or row["requested_at"],
            "updated_at": row["updated_at"] or row["approved_at"] or row["requested_at"],
            "expires_at": row["expires_at"] or "1970-01-01T00:00:00Z",
            "decision_at": row["decision_at"] or row["approved_at"],
            "decided_by": row["decided_by"] or row["approver"],
            "metadata": metadata,
        }

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
    trace_id TEXT,
    span_id TEXT,
    parent_span_id TEXT,
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

CREATE TABLE IF NOT EXISTS spans (
    span_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    run_id TEXT,
    parent_span_id TEXT,
    name TEXT NOT NULL,
    span_type TEXT NOT NULL,
    status TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info',
    subject TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration_ms INTEGER,
    payload_json TEXT NOT NULL DEFAULT '{}',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    findings_json TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_parent_span_id ON spans(parent_span_id);
CREATE INDEX IF NOT EXISTS idx_spans_type ON spans(span_type);

CREATE TABLE IF NOT EXISTS metrics (
    metric_id TEXT PRIMARY KEY,
    trace_id TEXT,
    run_id TEXT,
    span_id TEXT,
    name TEXT NOT NULL,
    value REAL NOT NULL DEFAULT 0.0,
    unit TEXT,
    category TEXT NOT NULL DEFAULT 'command',
    operation TEXT,
    command TEXT,
    status TEXT,
    ok INTEGER CHECK (ok IN (0, 1)),
    severity TEXT NOT NULL DEFAULT 'info',
    provider TEXT,
    model TEXT,
    task TEXT,
    timestamp TEXT NOT NULL,
    estimated INTEGER NOT NULL DEFAULT 0 CHECK (estimated IN (0, 1)),
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_metrics_trace_id ON metrics(trace_id);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    subject TEXT,
    tool_id TEXT NOT NULL DEFAULT '',
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT '',
    reason TEXT,
    scope_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT,
    updated_at TEXT,
    expires_at TEXT,
    decision_at TEXT,
    decided_by TEXT,
    requested_at TEXT NOT NULL,
    approved_at TEXT,
    approver TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    CHECK (status IN ('requested', 'approved', 'denied', 'revoked', 'expired'))
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


def _metric_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "metric_id": str(row["metric_id"]),
        "trace_id": row["trace_id"],
        "run_id": row["run_id"],
        "span_id": row["span_id"] if "span_id" in row.keys() else None,
        "name": str(row["name"]),
        "value": float(row["value"] or 0.0),
        "unit": row["unit"],
        "category": str(row["category"] or "command") if "category" in row.keys() else "command",
        "operation": row["operation"] if "operation" in row.keys() else None,
        "command": row["command"] if "command" in row.keys() else None,
        "status": row["status"] if "status" in row.keys() else None,
        "ok": None if "ok" not in row.keys() or row["ok"] is None else bool(row["ok"]),
        "severity": str(row["severity"] or "info") if "severity" in row.keys() else "info",
        "provider": row["provider"] if "provider" in row.keys() else None,
        "model": row["model"] if "model" in row.keys() else None,
        "task": row["task"] if "task" in row.keys() else None,
        "timestamp": str(row["timestamp"]),
        "estimated": bool(row["estimated"]) if "estimated" in row.keys() else False,
        "metadata": _load_json(row["metadata_json"], {}),
    }


def _span_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "span_id": str(row["span_id"]),
        "trace_id": str(row["trace_id"]),
        "run_id": row["run_id"],
        "parent_span_id": row["parent_span_id"],
        "name": str(row["name"]),
        "span_type": str(row["span_type"]),
        "status": str(row["status"]),
        "severity": str(row["severity"]),
        "subject": row["subject"],
        "started_at": str(row["started_at"]),
        "ended_at": row["ended_at"],
        "duration_ms": row["duration_ms"],
        "payload": _load_json(row["payload_json"], {}),
        "metadata": _load_json(row["metadata_json"], {}),
        "findings": _load_json(row["findings_json"], []),
    }


def _event_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "event_id": str(row["event_id"]),
        "run_id": row["run_id"],
        "trace_id": row["trace_id"],
        "span_id": row["span_id"],
        "parent_span_id": row["parent_span_id"],
        "event_type": str(row["event_type"]),
        "command": str(row["command"]),
        "status": row["status"],
        "ok": None if row["ok"] is None else bool(row["ok"]),
        "exit_code": row["exit_code"],
        "timestamp": str(row["timestamp"]),
        "subject": row["subject"],
        "summary": _load_json(row["summary_json"], {}),
        "metadata": _load_json(row["metadata_json"], {}),
    }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _tracked_tables() -> tuple[str, ...]:
    return ("runs", "findings", "gates", "events", "spans", "metrics", "approvals", "cost_events")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _load_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


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
