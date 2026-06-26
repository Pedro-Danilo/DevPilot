from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.observability.inventory import ObservabilityInventoryBuilder, ObservabilityInventoryOptions
from devpilot_core.observability.retention import DEFAULT_OBSERVABILITY_RETENTION_POLICY
from devpilot_core.policy import SecretGuard
from devpilot_core.store import LocalStore

OBSERVABILITY_REDACTED_EXPORT_SCHEMA_ID = "SCHEMA-DEVPL-OBSERVABILITY-REDACTED-EXPORT-V1"
OBSERVABILITY_REDACTED_EXPORT_CONTRACT = "ObservabilityRedactedExport"
OBSERVABILITY_REDACTED_EXPORT_ID = "devpilot-local-observability-redacted-export"
POST_H_010_D_CREATED_BY = "POST-H-010-D"

DEFAULT_OBSERVABILITY_EXPORT_JSON = Path("outputs/reports/observability_redacted_export.json")
DEFAULT_OBSERVABILITY_EXPORT_MARKDOWN = Path("outputs/reports/observability_redacted_export.md")
DEFAULT_OBSERVABILITY_AUDIT_EXPORT_DIR = Path("outputs/audit_exports/observability_redacted_export")

_EVENTS_PATH = Path("outputs/traces/events.jsonl")
_DEVPL_DB_PATH = Path(".devpilot/devpilot.db")
_AGENT_SESSIONS_DIR = Path(".devpilot/agent_sessions")
_REPORTS_DIR = Path("outputs/reports")
_CHECKSUMS_NAME = "checksums.sha256"
_AUDIT_SUMMARY_NAME = "observability_redacted_summary.json"
_AUDIT_SUMMARY_MD_NAME = "observability_redacted_summary.md"

_RAW_PAYLOAD_KEYS = {
    "prompt",
    "prompts",
    "raw_prompt",
    "raw_prompts",
    "rendered_prompt",
    "rendered_prompts",
    "completion",
    "completions",
    "raw_output",
    "raw_outputs",
    "model_output",
    "model_outputs",
    "llm_output",
    "llm_outputs",
    "input_text",
    "output_text",
    "response_text",
    "stdout",
    "stderr",
    "env",
    "environment",
    "dotenv",
}

_TOP_LEVEL_EVENT_FIELDS = (
    "event_type",
    "command",
    "status",
    "ok",
    "exit_code",
    "level",
    "timestamp",
    "trace_id",
    "run_id",
    "span_id",
)

_SAFE_SPAN_FIELDS = (
    "trace_id",
    "run_id",
    "span_id",
    "parent_span_id",
    "name",
    "span_type",
    "status",
    "severity",
    "subject",
    "started_at",
    "ended_at",
    "duration_ms",
)

_SAFE_METRIC_FIELDS = (
    "metric_id",
    "trace_id",
    "run_id",
    "span_id",
    "name",
    "value",
    "unit",
    "category",
    "operation",
    "command",
    "status",
    "ok",
    "severity",
    "provider",
    "model",
    "task",
    "timestamp",
    "estimated",
)


@dataclass(frozen=True)
class ObservabilityRedactedExportOptions:
    policy_path: str | Path = DEFAULT_OBSERVABILITY_RETENTION_POLICY
    redacted: bool = True
    write_report: bool = False
    output_json: str | Path = DEFAULT_OBSERVABILITY_EXPORT_JSON
    output_markdown: str | Path = DEFAULT_OBSERVABILITY_EXPORT_MARKDOWN
    audit_output_dir: str | Path = DEFAULT_OBSERVABILITY_AUDIT_EXPORT_DIR
    limit: int = 100


class ObservabilityRedactedExporter:
    """Build a local redacted export of observability evidence.

    POST-H-010-D is local-only and evidence-first. It exports summaries of
    events, spans, metrics, agent sessions and runtime report metadata without
    emitting raw prompts, raw outputs, secrets, .env content or SQLite bytes.
    Report and audit-export files are written only when --write-report is
    explicit; no remote export, network call, source mutation or cleanup is
    performed.
    """

    def __init__(self, root: Path, options: ObservabilityRedactedExportOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ObservabilityRedactedExportOptions()
        self.secret_guard = SecretGuard()

    def run(self) -> CommandResult:
        if not self.options.redacted:
            finding = Finding(
                id="OBSERVABILITY_EXPORT_REDACTION_REQUIRED",
                message="Observability export requires --redacted; raw observability export is a no-go gate.",
                severity=Severity.BLOCK,
            )
            return CommandResult(
                command="observability export",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Observability export blocked because redaction was not requested.",
                data={"summary": self._base_summary(redacted=False, execution_blocked=True)},
                findings=[finding],
            )

        try:
            payload = self.build_export()
        except Exception as exc:  # defensive CLI boundary
            finding = Finding(
                id="OBSERVABILITY_EXPORT_ERROR",
                message=f"Observability redacted export could not be built: {exc}",
                severity=Severity.ERROR,
            )
            return CommandResult(
                command="observability export",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Observability redacted export failed.",
                data={"summary": self._base_summary(redacted=True, execution_blocked=True)},
                findings=[finding],
            )

        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._planned_report_paths()
            payload["summary"]["reports_written"] = True
            payload["summary"]["output_json"] = reports["json"]
            payload["summary"]["output_markdown"] = reports["markdown"]
            payload["summary"]["audit_export_written"] = True
            payload["summary"]["audit_export_path"] = reports["audit_export_dir"]
            self._write_reports(payload, reports)
        else:
            payload["summary"]["reports_written"] = False
            payload["summary"]["output_json"] = None
            payload["summary"]["output_markdown"] = None
            payload["summary"]["audit_export_written"] = False
            payload["summary"]["audit_export_path"] = None

        findings = _findings_from_export(payload)
        blocking = [item for item in findings if item.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        return CommandResult(
            command="observability export",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Observability redacted export passed." if not blocking else "Observability redacted export has blocking findings.",
            data={"summary": payload["summary"], "export": payload, "reports": reports},
            findings=findings,
        )

    def build_export(self) -> dict[str, Any]:
        inventory_result = ObservabilityInventoryBuilder(
            self.root,
            ObservabilityInventoryOptions(policy_path=self.options.policy_path, write_report=False),
        ).run()
        if not inventory_result.ok or not inventory_result.data or "inventory" not in inventory_result.data:
            raise ValueError("observability inventory is required before export")

        inventory = inventory_result.data["inventory"]
        now = utc_now_iso()
        limit = _safe_limit(self.options.limit)

        event_export = self._event_summary(limit=limit)
        span_export = self._span_summary(limit=limit)
        metric_export = self._metric_summary(limit=limit)
        session_export = self._agent_session_summary()
        report_export = self._report_metadata_summary()
        target_exports = self._target_exports(inventory)

        sections = {
            "events": event_export,
            "spans": span_export,
            "metrics": metric_export,
            "agent_sessions": session_export,
            "reports": report_export,
        }
        sanitized_sections, redaction_counts = self._redact_sections(sections)
        checksums = self._build_checksums(sanitized_sections)
        total_records = (
            int(event_export["summary"].get("events_sampled_total", 0))
            + int(span_export["summary"].get("spans_sampled_total", 0))
            + int(metric_export["summary"].get("metrics_sampled_total", 0))
            + int(session_export["summary"].get("session_files_total", 0))
            + int(report_export["summary"].get("report_files_total", 0))
        )

        raw_payload_fields_removed_total = sum(int(dict(item.get("summary", {})).get("raw_payload_fields_removed", 0)) for item in sanitized_sections.values() if isinstance(item, dict))
        redactions_total = sum(redaction_counts.values())
        export_id = _stable_export_id(sanitized_sections, checksums)
        summary = {
            **self._base_summary(redacted=True, execution_blocked=False),
            "generated_at_utc": now,
            "export_id": export_id,
            "policy_id": inventory.get("policy_id", "devpilot-local-observability-retention"),
            "policy_path": inventory.get("policy_path", str(self.options.policy_path).replace("\\", "/")),
            "inventory_id": inventory.get("inventory_id", "devpilot-local-observability-inventory"),
            "targets_total": int(inventory.get("targets_total", 0)),
            "target_exports_total": len(target_exports),
            "sections_total": len(sanitized_sections),
            "events_exported_total": int(event_export["summary"].get("events_sampled_total", 0)),
            "spans_exported_total": int(span_export["summary"].get("spans_sampled_total", 0)),
            "metrics_exported_total": int(metric_export["summary"].get("metrics_sampled_total", 0)),
            "agent_sessions_exported_total": int(session_export["summary"].get("session_files_total", 0)),
            "report_metadata_exported_total": int(report_export["summary"].get("report_files_total", 0)),
            "records_exported_total": total_records,
            "redactions_total": redactions_total,
            "raw_payload_fields_removed_total": raw_payload_fields_removed_total,
            "checksums_total": len(checksums),
            "redaction_applied": True,
            "raw_prompts_exported": False,
            "raw_outputs_exported": False,
            "secrets_exported": False,
            "env_files_exported": False,
            "sqlite_raw_exported": False,
            "remote_export_enabled": False,
            "export_execution_enabled": True,
            "redaction_execution_enabled": True,
            "cleanup_execution_enabled": False,
            "mutations_performed": False,
            "destructive_cleanup_performed": False,
            "source_mutations_performed": False,
            "raw_payloads_read": False,
            "network_used": False,
            "external_api_used": False,
            "reports_written": False,
            "audit_export_written": False,
            "audit_export_path": None,
            "output_json": None,
            "output_markdown": None,
            "limit": limit,
        }
        return {
            "schema_version": "1.0",
            "schema_id": OBSERVABILITY_REDACTED_EXPORT_SCHEMA_ID,
            "export_id": export_id,
            "created_by": POST_H_010_D_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": now,
            "policy_id": summary["policy_id"],
            "policy_path": summary["policy_path"],
            "inventory_id": summary["inventory_id"],
            "redacted": True,
            "redaction_applied": True,
            "target_exports": target_exports,
            "sections": sanitized_sections,
            "checksums": checksums,
            "findings": [],
            "summary": summary,
            "safety": {
                "local_first": True,
                "redaction_required": True,
                "redaction_applied": True,
                "no_raw_prompts": True,
                "no_raw_outputs": True,
                "no_secrets": True,
                "no_env_files": True,
                "metadata_only_for_sqlite": True,
                "metadata_only_for_agent_sessions": True,
                "network_used": False,
                "external_api_used": False,
                "remote_export_enabled": False,
                "cleanup_execution_enabled": False,
                "destructive_cleanup_performed": False,
                "source_mutations_performed": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
            },
            "notes": [
                "POST-H-010-D exports only redacted/local observability evidence.",
                "Events, spans and metrics are summarized with bounded samples and raw payload fields removed.",
                "SQLite and agent session targets are exported as metadata-only summaries; raw bytes and raw session payloads are not exported.",
                "Remote export, external APIs and network access remain disabled.",
                "Quality-gate integration remains POST-H-010-E scope.",
            ],
        }

    def _event_summary(self, *, limit: int) -> dict[str, Any]:
        path = self.root / _EVENTS_PATH
        counters = {
            "event_types": Counter(),
            "commands": Counter(),
            "statuses": Counter(),
            "levels": Counter(),
            "exit_codes": Counter(),
        }
        samples: list[dict[str, Any]] = []
        malformed = 0
        lines_total = 0
        raw_removed = 0
        if path.exists() and path.is_file():
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    lines_total += 1
                    if len(samples) >= limit and lines_total > limit * 20:
                        # Keep command bounded even for very large event files.
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        malformed += 1
                        continue
                    if not isinstance(obj, dict):
                        malformed += 1
                        continue
                    safe, removed = _strip_raw_payload_fields(obj)
                    raw_removed += removed
                    counters["event_types"][str(safe.get("event_type") or "unknown")] += 1
                    counters["commands"][str(safe.get("command") or "unknown")] += 1
                    counters["statuses"][str(safe.get("status") or "unknown")] += 1
                    counters["levels"][str(safe.get("level") or "unknown")] += 1
                    counters["exit_codes"][str(safe.get("exit_code") or "unknown")] += 1
                    if len(samples) < limit:
                        samples.append({field: safe.get(field) for field in _TOP_LEVEL_EVENT_FIELDS if safe.get(field) is not None})
        return {
            "summary": {
                "source_path": _EVENTS_PATH.as_posix(),
                "exists": path.exists(),
                "events_seen_total": lines_total,
                "events_sampled_total": len(samples),
                "malformed_lines_total": malformed,
                "raw_payload_fields_removed": raw_removed,
                "metadata_only": False,
            },
            "aggregates": {key: dict(sorted(counter.items())) for key, counter in counters.items()},
            "sample": samples,
        }

    def _span_summary(self, *, limit: int) -> dict[str, Any]:
        store = LocalStore(self.root)
        spans = store.list_spans(limit=limit)
        safe_spans: list[dict[str, Any]] = []
        raw_removed = 0
        for span in spans:
            safe, removed = _strip_raw_payload_fields(span)
            raw_removed += removed
            safe_spans.append({field: safe.get(field) for field in _SAFE_SPAN_FIELDS if safe.get(field) is not None})
        span_types = Counter(str(item.get("span_type") or "unknown") for item in safe_spans)
        statuses = Counter(str(item.get("status") or "unknown") for item in safe_spans)
        names = Counter(str(item.get("name") or "unknown") for item in safe_spans)
        return {
            "summary": {
                "source_path": _DEVPL_DB_PATH.as_posix(),
                "exists": (self.root / _DEVPL_DB_PATH).exists(),
                "spans_sampled_total": len(safe_spans),
                "raw_payload_fields_removed": raw_removed,
                "metadata_only": True,
            },
            "aggregates": {
                "span_types": dict(sorted(span_types.items())),
                "statuses": dict(sorted(statuses.items())),
                "names": dict(sorted(names.items())),
            },
            "sample": safe_spans,
        }

    def _metric_summary(self, *, limit: int) -> dict[str, Any]:
        store = LocalStore(self.root)
        metrics = store.list_metrics(limit=limit)
        safe_metrics: list[dict[str, Any]] = []
        raw_removed = 0
        for metric in metrics:
            safe, removed = _strip_raw_payload_fields(metric)
            raw_removed += removed
            safe_metrics.append({field: safe.get(field) for field in _SAFE_METRIC_FIELDS if safe.get(field) is not None})
        categories = Counter(str(item.get("category") or "unknown") for item in safe_metrics)
        operations = Counter(str(item.get("operation") or item.get("name") or "unknown") for item in safe_metrics)
        statuses = Counter(str(item.get("status") or "UNKNOWN") for item in safe_metrics)
        return {
            "summary": {
                "source_path": _DEVPL_DB_PATH.as_posix(),
                "exists": (self.root / _DEVPL_DB_PATH).exists(),
                "metrics_sampled_total": len(safe_metrics),
                "raw_payload_fields_removed": raw_removed,
                "metadata_only": True,
            },
            "aggregates": {
                "categories": dict(sorted(categories.items())),
                "operations": dict(sorted(operations.items())),
                "statuses": dict(sorted(statuses.items())),
            },
            "sample": safe_metrics,
        }

    def _agent_session_summary(self) -> dict[str, Any]:
        directory = self.root / _AGENT_SESSIONS_DIR
        files: list[dict[str, Any]] = []
        total_bytes = 0
        if directory.exists():
            for path in sorted(item for item in directory.rglob("*") if item.is_file()):
                try:
                    rel = path.resolve().relative_to(self.root).as_posix()
                except ValueError:
                    continue
                size = path.stat().st_size
                total_bytes += size
                files.append(
                    {
                        "path": rel,
                        "size_bytes": size,
                        "sha256": _sha256_file(path),
                        "metadata_only": True,
                        "raw_payload_exported": False,
                    }
                )
        return {
            "summary": {
                "source_path": _AGENT_SESSIONS_DIR.as_posix(),
                "exists": directory.exists(),
                "session_files_total": len(files),
                "size_bytes_total": total_bytes,
                "raw_payload_fields_removed": 0,
                "metadata_only": True,
            },
            "files": files,
        }

    def _report_metadata_summary(self) -> dict[str, Any]:
        directory = self.root / _REPORTS_DIR
        files: list[dict[str, Any]] = []
        total_bytes = 0
        if directory.exists():
            for path in sorted(item for item in directory.rglob("*") if item.is_file()):
                try:
                    rel = path.resolve().relative_to(self.root).as_posix()
                except ValueError:
                    continue
                size = path.stat().st_size
                total_bytes += size
                files.append(
                    {
                        "path": rel,
                        "size_bytes": size,
                        "sha256": _sha256_file(path),
                        "metadata_only": True,
                        "raw_payload_exported": False,
                    }
                )
        return {
            "summary": {
                "source_path": _REPORTS_DIR.as_posix(),
                "exists": directory.exists(),
                "report_files_total": len(files),
                "size_bytes_total": total_bytes,
                "raw_payload_fields_removed": 0,
                "metadata_only": True,
            },
            "files": files,
        }

    def _target_exports(self, inventory: dict[str, Any]) -> list[dict[str, Any]]:
        target_exports: list[dict[str, Any]] = []
        for target in inventory.get("target_checks", []):
            rel_path = str(target.get("path") or "").replace("\\", "/")
            export_mode = "metadata-only" if target.get("kind") in {"sqlite", "sqlite-table", "directory"} else "summary-only"
            target_exports.append(
                {
                    "target_id": str(target.get("target_id") or ""),
                    "path": rel_path,
                    "kind": str(target.get("kind") or ""),
                    "exists": bool(target.get("exists", False)),
                    "size_bytes": int(target.get("size_bytes") or 0),
                    "records_estimated": int(target.get("records_estimated") or 0),
                    "redaction_required": bool(target.get("redaction_required", False)),
                    "contains_sensitive_payloads": bool(target.get("contains_sensitive_payloads", False)),
                    "clean_zip_excluded": bool(target.get("clean_zip_excluded", False)),
                    "export_allowed": bool(target.get("export_allowed", False)),
                    "export_mode": export_mode,
                    "raw_payload_exported": False,
                }
            )
        return target_exports

    def _redact_sections(self, sections: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
        sanitized: dict[str, Any] = {}
        counts: dict[str, int] = {}
        for name, section in sections.items():
            redaction = self.secret_guard.redact(section)
            sanitized[name] = redaction.value
            counts[name] = redaction.redactions
            if isinstance(sanitized[name], dict):
                sanitized[name]["redaction"] = {
                    "redaction_applied": True,
                    "redactions_total": redaction.redactions,
                    "raw_prompts_exported": False,
                    "raw_outputs_exported": False,
                    "secrets_exported": False,
                }
        return sanitized, counts

    def _build_checksums(self, sections: dict[str, Any]) -> dict[str, str]:
        checksums: dict[str, str] = {}
        for name, section in sections.items():
            payload = json.dumps(section, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
            checksums[f"sections/{name}.json"] = hashlib.sha256(payload).hexdigest()
        return checksums

    def _write_reports(self, payload: dict[str, Any], reports: dict[str, str]) -> None:
        json_path = self.root / reports["json"]
        md_path = self.root / reports["markdown"]
        audit_dir = self.root / reports["audit_export_dir"]
        json_path.parent.mkdir(parents=True, exist_ok=True)
        audit_dir.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        markdown = render_observability_redacted_export_markdown(payload)
        md_path.write_text(markdown, encoding="utf-8")
        (audit_dir / _AUDIT_SUMMARY_NAME).write_text(json.dumps(_audit_summary_payload(payload), indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        (audit_dir / _AUDIT_SUMMARY_MD_NAME).write_text(markdown, encoding="utf-8")
        checksums_text = "".join(f"{sha}  {path}\n" for path, sha in sorted(payload.get("checksums", {}).items()))
        (audit_dir / _CHECKSUMS_NAME).write_text(checksums_text, encoding="utf-8")

    def _planned_report_paths(self) -> dict[str, str]:
        return {
            "json": str(self.options.output_json).replace("\\", "/"),
            "markdown": str(self.options.output_markdown).replace("\\", "/"),
            "audit_export_dir": str(self.options.audit_output_dir).replace("\\", "/"),
        }

    def _base_summary(self, *, redacted: bool, execution_blocked: bool) -> dict[str, Any]:
        return {
            "created_by": POST_H_010_D_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "redacted": redacted,
            "execution_blocked": execution_blocked,
            "redaction_required": True,
            "redaction_applied": bool(redacted),
            "raw_prompts_exported": False,
            "raw_outputs_exported": False,
            "secrets_exported": False,
            "env_files_exported": False,
            "sqlite_raw_exported": False,
            "remote_export_enabled": False,
            "network_used": False,
            "external_api_used": False,
            "cleanup_execution_enabled": False,
            "mutations_performed": False,
            "destructive_cleanup_performed": False,
            "source_mutations_performed": False,
        }


def render_observability_redacted_export_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# Observability redacted export",
        "",
        f"Export ID: `{payload.get('export_id', '')}`",
        f"Generated at UTC: `{payload.get('generated_at_utc', '')}`",
        f"Created by: `{payload.get('created_by', '')}`",
        f"Status: `{payload.get('status', '')}`",
        "",
        "## Summary",
        "",
        f"- Redaction applied: `{summary.get('redaction_applied', False)}`",
        f"- Events exported total: `{summary.get('events_exported_total', 0)}`",
        f"- Spans exported total: `{summary.get('spans_exported_total', 0)}`",
        f"- Metrics exported total: `{summary.get('metrics_exported_total', 0)}`",
        f"- Agent sessions metadata total: `{summary.get('agent_sessions_exported_total', 0)}`",
        f"- Report metadata total: `{summary.get('report_metadata_exported_total', 0)}`",
        f"- Redactions total: `{summary.get('redactions_total', 0)}`",
        f"- Raw payload fields removed: `{summary.get('raw_payload_fields_removed_total', 0)}`",
        f"- Checksums total: `{summary.get('checksums_total', 0)}`",
        "",
        "## Safety",
        "",
        f"- Raw prompts exported: `{summary.get('raw_prompts_exported', False)}`",
        f"- Raw outputs exported: `{summary.get('raw_outputs_exported', False)}`",
        f"- Secrets exported: `{summary.get('secrets_exported', False)}`",
        f"- SQLite raw exported: `{summary.get('sqlite_raw_exported', False)}`",
        f"- Network used: `{summary.get('network_used', False)}`",
        f"- External API used: `{summary.get('external_api_used', False)}`",
        f"- Remote export enabled: `{summary.get('remote_export_enabled', False)}`",
        "",
        "## Target export modes",
        "",
        "| target_id | path | export_mode | raw_payload_exported |",
        "|---|---|---:|---:|",
    ]
    for target in payload.get("target_exports", []):
        lines.append(
            f"| `{target.get('target_id', '')}` | `{target.get('path', '')}` | `{target.get('export_mode', '')}` | `{target.get('raw_payload_exported', False)}` |"
        )
    lines.extend([
        "",
        "## Notes",
        "",
    ])
    for note in payload.get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def _audit_summary_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": payload.get("schema_version"),
        "schema_id": payload.get("schema_id"),
        "export_id": payload.get("export_id"),
        "created_by": payload.get("created_by"),
        "status": payload.get("status"),
        "generated_at_utc": payload.get("generated_at_utc"),
        "summary": payload.get("summary"),
        "target_exports": payload.get("target_exports"),
        "sections": payload.get("sections"),
        "checksums": payload.get("checksums"),
        "safety": payload.get("safety"),
        "notes": payload.get("notes"),
    }


def _findings_from_export(payload: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    summary = payload.get("summary", {})
    if not summary.get("redaction_applied", False):
        findings.append(Finding("OBSERVABILITY_EXPORT_REDACTION_MISSING", "Redaction must be applied to observability export.", Severity.BLOCK))
    if summary.get("raw_prompts_exported") or summary.get("raw_outputs_exported"):
        findings.append(Finding("OBSERVABILITY_EXPORT_RAW_PAYLOAD_LEAK", "Raw prompts/outputs must not be exported.", Severity.BLOCK))
    if summary.get("secrets_exported"):
        findings.append(Finding("OBSERVABILITY_EXPORT_SECRET_LEAK", "Secrets must not be exported.", Severity.BLOCK))
    if summary.get("remote_export_enabled") or summary.get("network_used") or summary.get("external_api_used"):
        findings.append(Finding("OBSERVABILITY_EXPORT_REMOTE_BLOCKED", "Observability export must remain local-only.", Severity.BLOCK))
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    secret_scan = SecretGuard().scan_text(rendered, subject="observability export")
    if secret_scan.effect.value == "block":
        findings.append(Finding("OBSERVABILITY_EXPORT_SECRET_SCAN_FAILED", "SecretGuard detected secret-like content in export payload.", Severity.BLOCK, metadata=secret_scan.metadata))
    if not findings:
        findings.append(Finding("OBSERVABILITY_REDACTED_EXPORT_PASS", "Observability redacted export completed without blocking findings.", Severity.INFO, metadata={"records_exported_total": summary.get("records_exported_total", 0)}))
    return findings


def _strip_raw_payload_fields(value: Any) -> tuple[Any, int]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        removed = 0
        for key, item in value.items():
            if _is_raw_payload_key(str(key)):
                result[key] = "[REDACTED_RAW_PAYLOAD_FIELD]"
                removed += 1
                continue
            child, child_removed = _strip_raw_payload_fields(item)
            result[key] = child
            removed += child_removed
        return result, removed
    if isinstance(value, list):
        result = []
        removed = 0
        for item in value:
            child, child_removed = _strip_raw_payload_fields(item)
            result.append(child)
            removed += child_removed
        return result, removed
    return value, 0


def _is_raw_payload_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return normalized in _RAW_PAYLOAD_KEYS


def _safe_limit(limit: int) -> int:
    try:
        parsed = int(limit)
    except (TypeError, ValueError):
        parsed = 100
    return max(1, min(parsed, 500))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_export_id(sections: dict[str, Any], checksums: dict[str, str]) -> str:
    payload = json.dumps(
        {
            "checksums": checksums,
            "section_names": sorted(sections.keys()),
        },
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return f"observability-redacted-export-{hashlib.sha256(payload).hexdigest()[:12]}"


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
