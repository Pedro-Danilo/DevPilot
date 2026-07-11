from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.policy import PathGuard, PolicyEffect, SecretGuard, redact_sensitive_data
from devpilot_core.schemas.validator import SchemaValidator

POST_H_032_E_CREATED_BY = "POST-H-032-E"
AGENT_MEMORY_COMMAND = "agent memory"
AGENT_MEMORY_SCHEMA_ID = "SCHEMA-DEVPL-AGENT-MEMORY-RECORD-V1"
AGENT_MEMORY_CONTRACT = "AgentMemoryRecord"
DEFAULT_AGENT_MEMORY_POLICY_PATH = ".devpilot/agents/agent_memory_policy.json"
DEFAULT_AGENT_MEMORY_DIR = ".devpilot/agents/memory"
DEFAULT_AGENT_MEMORY_REPORT_JSON = "outputs/reports/agent_memory_model_report.json"
DEFAULT_AGENT_MEMORY_REPORT_MARKDOWN = "outputs/reports/agent_memory_model_report.md"
ADR_PATH = "docs/adr/ADR-POSTH-032-E-agent-memory-local-opt-in.md"
FORBIDDEN_RAW_KEYS = {
    "raw_prompt",
    "raw_output",
    "prompt_text",
    "model_output",
    "completion_text",
    "raw_prompts",
    "raw_outputs",
}


@dataclass(frozen=True)
class AgentMemoryModelOptions:
    """Options for POST-H-032-E local opt-in agent memory model commands."""

    policy_path: Path = Path(DEFAULT_AGENT_MEMORY_POLICY_PATH)
    memory_dir: Path = Path(DEFAULT_AGENT_MEMORY_DIR)
    write_report: bool = False
    output_json: Path = Path(DEFAULT_AGENT_MEMORY_REPORT_JSON)
    output_markdown: Path = Path(DEFAULT_AGENT_MEMORY_REPORT_MARKDOWN)
    dry_run: bool = True
    execute: bool = False
    limit: int = 50


class AgentMemoryModelManager:
    """Inspect, export and cleanup the governed local agent memory model.

    POST-H-032-E deliberately does not enable semantic memory. It validates the
    memory contract, reads only local JSON records when present, redacts exports,
    plans retention cleanup and executes cleanup only for explicit memory-record
    files when the operator requests `execute`.
    """

    def __init__(self, root: Path, options: AgentMemoryModelOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or AgentMemoryModelOptions()
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()

    def inspect(self) -> CommandResult:
        return self._build("inspect")

    def export(self) -> CommandResult:
        return self._build("export")

    def cleanup(self) -> CommandResult:
        return self._build("cleanup")

    def _build(self, action: str) -> CommandResult:
        findings: list[Finding] = []
        policy = self._load_policy(findings)
        records = self._load_records(policy, findings)
        sample_record = _sample_record(policy)
        sample_validation = SchemaValidator(self.root).validate_payload(
            schema=AGENT_MEMORY_CONTRACT,
            payload=self._report_payload(
                action=action,
                policy=policy,
                records=[sample_record],
                cleanup_plan=_empty_cleanup_plan(dry_run=True),
                findings=[],
                reports_written=False,
                schema_valid=True,
            ),
            instance_label="in-memory-agent-memory-record-sample",
        )
        if not sample_validation.ok:
            findings.extend(_prefixed_findings(sample_validation, "AGENT_MEMORY_SAMPLE_SCHEMA"))

        cleanup_plan = self._cleanup_plan(records, action=action, findings=findings)
        report = self._report_payload(
            action=action,
            policy=policy,
            records=records,
            cleanup_plan=cleanup_plan,
            findings=findings,
            reports_written=False,
            schema_valid=True,
        )
        schema_result = SchemaValidator(self.root).validate_payload(
            schema=AGENT_MEMORY_CONTRACT,
            payload=report,
            instance_label="in-memory-agent-memory-model-report",
        )
        if not schema_result.ok:
            findings.extend(_prefixed_findings(schema_result, "AGENT_MEMORY_SCHEMA"))
            report["summary"]["schema_valid"] = False
            report["summary"]["decision"] = "BLOCK"
            report["summary"]["status"] = "blocked"
            report["status"] = "blocked"
        else:
            report["summary"]["schema_valid"] = True

        reports: dict[str, str] = {}
        if self.options.write_report:
            report["summary"]["reports_written"] = True
            report["export"]["report_paths_requested"] = True
            reports = self._write_reports(report)

        blocking = _blocking_findings(findings)
        report["summary"]["blocking_findings_total"] = len(blocking)
        report["summary"]["findings_total"] = len(findings)
        if blocking:
            report["summary"]["decision"] = "BLOCK"
            report["summary"]["status"] = "blocked"
            report["status"] = "blocked"
        report["findings"] = [finding.to_dict() for finding in findings] or [
            Finding(
                "AGENT_MEMORY_MODEL_PASS",
                "Agent memory model passed with disabled-by-default local redacted memory controls.",
                Severity.INFO,
                metadata=report["summary"],
            ).to_dict()
        ]
        ok = not blocking
        return CommandResult(
            command=f"{AGENT_MEMORY_COMMAND} {action}",
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False),
            message="Agent memory model passed." if ok else "Agent memory model has blocking findings.",
            data={"summary": report["summary"], "report": report, "policy": policy, "reports": reports},
            findings=[] if ok else findings,
        )

    def _load_policy(self, findings: list[Finding]) -> dict[str, Any]:
        path = _resolve_workspace_path(self.root, self.options.policy_path)
        decision = self.path_guard.evaluate(path, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            findings.append(Finding("AGENT_MEMORY_POLICY_PATH_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata))
            return _default_policy()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(Finding("AGENT_MEMORY_POLICY_LOAD_ERROR", f"Could not load agent memory policy: {exc}", Severity.BLOCK, path=_relative(path, self.root)))
            return _default_policy()
        if not isinstance(payload, dict):
            findings.append(Finding("AGENT_MEMORY_POLICY_INVALID", "Agent memory policy root must be an object.", Severity.BLOCK, path=_relative(path, self.root)))
            return _default_policy()
        defaults = dict(payload.get("defaults") or {})
        if defaults.get("semantic_memory_enabled") is not False:
            findings.append(Finding("AGENT_MEMORY_SEMANTIC_ENABLED_BY_DEFAULT", "semantic_memory_enabled must remain false by default.", Severity.BLOCK, path=_relative(path, self.root)))
        if defaults.get("memory_enabled_by_default") is not False:
            findings.append(Finding("AGENT_MEMORY_ENABLED_BY_DEFAULT", "Agent memory must not be enabled by default.", Severity.BLOCK, path=_relative(path, self.root)))
        return payload

    def _load_records(self, policy: dict[str, Any], findings: list[Finding]) -> list[dict[str, Any]]:
        memory_dir = _resolve_workspace_path(self.root, self.options.memory_dir)
        try:
            memory_dir.relative_to(self.root)
        except ValueError:
            findings.append(Finding("AGENT_MEMORY_DIR_OUTSIDE_WORKSPACE", "Agent memory directory must stay inside the workspace root.", Severity.BLOCK, path=str(memory_dir)))
            return []
        if not memory_dir.exists():
            return []
        decision = self.path_guard.evaluate(memory_dir, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            findings.append(Finding("AGENT_MEMORY_DIR_READ_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata))
            return []
        records: list[dict[str, Any]] = []
        for path in sorted(memory_dir.glob("*.json"))[: _safe_limit(self.options.limit)]:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                findings.append(Finding("AGENT_MEMORY_RECORD_LOAD_ERROR", f"Could not load memory record: {exc}", Severity.BLOCK, path=_relative(path, self.root)))
                continue
            if not isinstance(payload, dict):
                findings.append(Finding("AGENT_MEMORY_RECORD_INVALID", "Memory record root must be an object.", Severity.BLOCK, path=_relative(path, self.root)))
                continue
            record = self._normalize_record(payload, policy=policy, path=path, findings=findings)
            records.append(record)
        return records

    def _normalize_record(self, payload: dict[str, Any], *, policy: dict[str, Any], path: Path, findings: list[Finding]) -> dict[str, Any]:
        raw_keys = sorted(_find_forbidden_raw_keys(payload))
        secret_result = self.secret_guard.redact(payload)
        redacted_payload = secret_result.value if isinstance(secret_result.value, dict) else {}
        if raw_keys:
            findings.append(Finding("AGENT_MEMORY_RAW_PROMPT_OR_OUTPUT_BLOCKED", "Memory record contains raw prompt/output fields.", Severity.BLOCK, path=_relative(path, self.root), metadata={"keys": raw_keys}))
        if secret_result.redactions:
            findings.append(Finding("AGENT_MEMORY_SECRET_PERSISTENCE_BLOCKED", "Memory record contains secret-like content and cannot be accepted as safe memory.", Severity.BLOCK, path=_relative(path, self.root), metadata={"redactions": secret_result.redactions}))
        defaults = dict(policy.get("defaults") or {})
        now = _now_utc()
        created_at = str(redacted_payload.get("created_at_utc") or redacted_payload.get("created_at") or now)
        updated_at = str(redacted_payload.get("updated_at_utc") or redacted_payload.get("updated_at") or created_at)
        retention_days = int(redacted_payload.get("retention", {}).get("retention_days") or defaults.get("retention_days") or 14) if isinstance(redacted_payload.get("retention"), dict) else int(defaults.get("retention_days") or 14)
        expires_at = _expires_at(created_at, retention_days)
        cleanup_eligible = _parse_utc(expires_at) <= datetime.now(timezone.utc)
        memory_type = str(redacted_payload.get("memory_type") or "session_memory")
        if memory_type not in {"session_memory", "project_memory"}:
            findings.append(Finding("AGENT_MEMORY_TYPE_INVALID", "Memory records may only use session_memory or project_memory; report_evidence is separate.", Severity.BLOCK, path=_relative(path, self.root), metadata={"memory_type": memory_type}))
            memory_type = "session_memory"
        record = {
            "schema_version": "1.0",
            "schema_id": AGENT_MEMORY_SCHEMA_ID,
            "record_id": str(redacted_payload.get("record_id") or path.stem),
            "created_by": POST_H_032_E_CREATED_BY,
            "status": "cleanup-eligible" if cleanup_eligible else "active",
            "created_at_utc": created_at,
            "updated_at_utc": updated_at,
            "agent_id": str(redacted_payload.get("agent_id") or "unknown.agent"),
            "workspace_id": str(redacted_payload.get("workspace_id") or "local-workspace"),
            "memory_type": memory_type,
            "scope": "project" if memory_type == "project_memory" else "session",
            "content_redacted": _content_redacted(redacted_payload),
            "source_refs": [str(item) for item in redacted_payload.get("source_refs", []) if isinstance(item, str)],
            "retention": {
                "retention_days": retention_days,
                "expires_at_utc": expires_at,
                "cleanup_eligible": cleanup_eligible,
                "cleanup_policy": "explicit-execute-required",
                "storage_path": _relative(path, self.root),
            },
            "policy": {
                "semantic_memory_enabled": False,
                "memory_enabled_by_default": False,
                "export_redacted": True,
                "counts_as_formal_evidence": False,
            },
            "safety": {
                "raw_prompt_stored": False,
                "raw_output_stored": False,
                "secret_values_stored": False,
                "external_storage_used": False,
                "shared_across_workspaces": False,
            },
        }
        validation = SchemaValidator(self.root).validate_payload(schema=AGENT_MEMORY_CONTRACT, payload=self._record_validation_report(policy, record), instance_label=f"agent-memory-record:{record['record_id']}")
        if not validation.ok:
            findings.extend(_prefixed_findings(validation, "AGENT_MEMORY_RECORD_SCHEMA"))
        return record

    def _record_validation_report(self, policy: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
        return self._report_payload(action="inspect", policy=policy, records=[record], cleanup_plan=_empty_cleanup_plan(dry_run=True), findings=[], reports_written=False, schema_valid=True)

    def _cleanup_plan(self, records: list[dict[str, Any]], *, action: str, findings: list[Finding]) -> dict[str, Any]:
        execute_requested = action == "cleanup" and self.options.execute
        dry_run = not execute_requested
        items: list[dict[str, Any]] = []
        deleted = 0
        for record in records:
            retention = dict(record.get("retention") or {})
            if not retention.get("cleanup_eligible"):
                continue
            storage_path = str(retention.get("storage_path") or "")
            item = {"record_id": record.get("record_id"), "storage_path": storage_path, "action": "delete", "executed": False}
            if execute_requested:
                path = _resolve_workspace_path(self.root, storage_path)
                try:
                    path.relative_to(self.root)
                    if path.exists() and path.parent == _resolve_workspace_path(self.root, self.options.memory_dir):
                        path.unlink()
                        item["executed"] = True
                        deleted += 1
                    else:
                        item["blocked_reason"] = "path-missing-or-not-in-memory-dir"
                except Exception as exc:
                    item["blocked_reason"] = str(exc)
                    findings.append(Finding("AGENT_MEMORY_CLEANUP_DELETE_FAILED", f"Could not cleanup memory record: {exc}", Severity.BLOCK, path=storage_path))
            items.append(item)
        return {"dry_run": dry_run, "execute_requested": execute_requested, "eligible_records_total": len(items), "deleted_records_total": deleted, "items": items}

    def _report_payload(
        self,
        *,
        action: str,
        policy: dict[str, Any],
        records: list[dict[str, Any]],
        cleanup_plan: dict[str, Any],
        findings: list[Finding],
        reports_written: bool,
        schema_valid: bool,
    ) -> dict[str, Any]:
        defaults = dict(policy.get("defaults") or {})
        memory_classes = list(policy.get("memory_classes") or _default_policy().get("memory_classes", []))
        blocking = _blocking_findings(findings)
        expired_total = sum(1 for record in records if record.get("retention", {}).get("cleanup_eligible") is True)
        summary = {
            "created_by": POST_H_032_E_CREATED_BY,
            "status": "implemented-initial" if not blocking else "blocked",
            "decision": "PASS" if not blocking else "BLOCK",
            "action": action,
            "semantic_memory_enabled": False,
            "memory_enabled_by_default": False,
            "records_total": len(records),
            "records_valid_total": len(records) if not blocking else max(0, len(records) - len(blocking)),
            "records_invalid_total": len(blocking),
            "records_expired_total": expired_total,
            "cleanup_plan_items_total": int(cleanup_plan.get("eligible_records_total", 0)),
            "cleanup_deleted_total": int(cleanup_plan.get("deleted_records_total", 0)),
            "inspect_available": True,
            "cleanup_available": True,
            "export_redacted": True,
            "retention_policy_applied": True,
            "no_raw_prompts": True,
            "no_raw_outputs": True,
            "no_secrets": True,
            "external_storage_used": False,
            "shared_workspace_memory_enabled": False,
            "memory_counts_as_formal_evidence": False,
            "session_memory_separated": True,
            "project_memory_separated": True,
            "report_evidence_separated": True,
            "schema_valid": schema_valid,
            "reports_written": reports_written,
            "blocking_findings_total": len(blocking),
            "findings_total": len(findings),
            "preliminary": True,
        }
        report = {
            "schema_version": "1.0",
            "schema_id": AGENT_MEMORY_SCHEMA_ID,
            "report_id": "devpilot-agent-memory-model-report",
            "created_by": POST_H_032_E_CREATED_BY,
            "status": summary["status"],
            "generated_at_utc": _now_utc(),
            "action": action,
            "adr_path": ADR_PATH,
            "policy_path": _posix(self.options.policy_path),
            "memory_dir": _posix(self.options.memory_dir),
            "summary": summary,
            "memory_classes": memory_classes,
            "records": records,
            "cleanup_plan": cleanup_plan,
            "export": {
                "redacted": True,
                "secrets_in_export": False,
                "raw_prompts_in_export": False,
                "raw_outputs_in_export": False,
                "records_exported_total": len(records),
                "report_paths_requested": reports_written,
            },
            "safety": {
                "local_first": True,
                "dry_run_default": True,
                "semantic_memory_enabled": False,
                "memory_enabled_by_default": False,
                "raw_prompts_stored": False,
                "raw_outputs_stored": False,
                "secrets_stored": False,
                "external_storage_used": False,
                "shared_across_workspaces": False,
                "memory_counts_as_formal_evidence": False,
                "memory_mutations_performed": bool(cleanup_plan.get("deleted_records_total", 0)),
                "source_mutations_performed": False,
                "network_used": False,
                "external_api_used": False,
                "tools_executed": False,
                "llm_used": False,
            },
            "findings": [finding.to_dict() for finding in findings],
            "notes": list(policy.get("notes") or _default_policy().get("notes", [])),
            "limitations": list(policy.get("limitations") or _default_policy().get("limitations", [])),
        }
        return report

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = _resolve_workspace_path(self.root, self.options.output_json)
        markdown_path = _resolve_workspace_path(self.root, self.options.output_markdown)
        _ensure_output_path(self.root, json_path)
        _ensure_output_path(self.root, markdown_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        markdown_path.write_text(_markdown(report), encoding="utf-8")
        return {"json": _relative(json_path, self.root), "markdown": _relative(markdown_path, self.root)}


def _sample_record(policy: dict[str, Any]) -> dict[str, Any]:
    now = _now_utc()
    retention_days = int((policy.get("defaults") or {}).get("retention_days") or 14)
    return {
        "schema_version": "1.0",
        "schema_id": AGENT_MEMORY_SCHEMA_ID,
        "record_id": "synthetic-redacted-agent-memory-record",
        "created_by": POST_H_032_E_CREATED_BY,
        "status": "synthetic-sample",
        "created_at_utc": now,
        "updated_at_utc": now,
        "agent_id": "requirements.agent",
        "workspace_id": "local-workspace",
        "memory_type": "session_memory",
        "scope": "session",
        "content_redacted": {"summary": "Synthetic redacted memory record for schema validation only.", "tags": ["synthetic", "redacted", "opt-in"]},
        "source_refs": ["docs/backlogs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md#POST-H-032-E"],
        "retention": {"retention_days": retention_days, "expires_at_utc": _expires_at(now, retention_days), "cleanup_eligible": False, "cleanup_policy": "explicit-execute-required"},
        "policy": {"semantic_memory_enabled": False, "memory_enabled_by_default": False, "export_redacted": True, "counts_as_formal_evidence": False},
        "safety": {"raw_prompt_stored": False, "raw_output_stored": False, "secret_values_stored": False, "external_storage_used": False, "shared_across_workspaces": False},
    }


def _default_policy() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "policy_id": "devpilot-agent-memory-policy",
        "created_by": POST_H_032_E_CREATED_BY,
        "status": "implemented-initial",
        "defaults": {
            "semantic_memory_enabled": False,
            "memory_enabled_by_default": False,
            "storage_dir": DEFAULT_AGENT_MEMORY_DIR,
            "external_storage_allowed": False,
            "raw_prompts_allowed": False,
            "raw_outputs_allowed": False,
            "secrets_allowed": False,
            "shared_workspace_memory_allowed": False,
            "redaction_required": True,
            "export_always_redacted": True,
            "inspect_allowed": True,
            "cleanup_allowed": True,
            "retention_days": 14,
            "memory_counts_as_formal_evidence": False,
            "report_evidence_is_separate": True,
        },
        "memory_classes": [
            {"memory_type": "session_memory", "enabled_by_default": False, "counts_as_formal_evidence": False},
            {"memory_type": "project_memory", "enabled_by_default": False, "counts_as_formal_evidence": False},
            {"memory_type": "report_evidence", "enabled_by_default": False, "counts_as_formal_evidence": True, "excluded_from_memory_store": True},
        ],
        "notes": ["Fallback policy used only when source policy cannot be read."],
        "limitations": ["Fallback policy indicates configuration load failure through findings."],
    }


def _content_redacted(payload: dict[str, Any]) -> dict[str, Any]:
    content = payload.get("content_redacted") or payload.get("content") or {}
    if isinstance(content, dict):
        result = dict(content)
    else:
        result = {"summary": str(content)}
    for key in list(result.keys()):
        if str(key).lower() in FORBIDDEN_RAW_KEYS:
            result.pop(key, None)
    if "summary" not in result:
        result["summary"] = "Redacted memory record."
    return redact_sensitive_data(result)


def _find_forbidden_raw_keys(value: Any, *, prefix: str = "") -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            current = f"{prefix}.{key_text}" if prefix else key_text
            if key_lower in FORBIDDEN_RAW_KEYS:
                found.add(current)
            found.update(_find_forbidden_raw_keys(item, prefix=current))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            found.update(_find_forbidden_raw_keys(item, prefix=f"{prefix}[{idx}]"))
    return found


def _expires_at(created_at: str, retention_days: int) -> str:
    created = _parse_utc(created_at)
    return (created + timedelta(days=max(0, min(int(retention_days), 3650)))).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    raw = str(value).strip()
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _empty_cleanup_plan(*, dry_run: bool) -> dict[str, Any]:
    return {"dry_run": dry_run, "execute_requested": False, "eligible_records_total": 0, "deleted_records_total": 0, "items": []}


def _ensure_output_path(root: Path, path: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Report paths must stay inside the workspace root.") from exc
    rel = _relative(path, root)
    if not rel.startswith("outputs/"):
        raise ValueError("Agent memory reports may only be written below outputs/.")


def _markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# POST-H-032-E — Agent memory model report",
        "",
        f"- Decision: `{summary.get('decision')}`",
        f"- Action: `{summary.get('action')}`",
        f"- Semantic memory enabled: `{summary.get('semantic_memory_enabled')}`",
        f"- Memory enabled by default: `{summary.get('memory_enabled_by_default')}`",
        f"- Records total: `{summary.get('records_total')}`",
        f"- Cleanup eligible: `{summary.get('cleanup_plan_items_total')}`",
        f"- Deleted records: `{summary.get('cleanup_deleted_total')}`",
        f"- Export redacted: `{summary.get('export_redacted')}`",
        f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
        "",
        "## Notes",
    ]
    for note in report.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    lines.append("## Limitations")
    for limitation in report.get("limitations", []):
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


def _prefixed_findings(result: CommandResult, prefix: str) -> list[Finding]:
    return [
        Finding(
            id=f"{prefix}_{finding.id}",
            message=finding.message,
            severity=finding.severity,
            path=finding.path,
            metadata=finding.metadata,
        )
        for finding in result.findings
        if finding.severity in {Severity.BLOCK, Severity.ERROR}
    ]


def _blocking_findings(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]


def _resolve_workspace_path(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _posix(path: str | Path) -> str:
    return Path(path).as_posix()


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_limit(value: int) -> int:
    return max(1, min(int(value), 500))
