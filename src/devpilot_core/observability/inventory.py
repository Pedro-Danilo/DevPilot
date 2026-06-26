from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.observability.retention import (
    DEFAULT_OBSERVABILITY_RETENTION_POLICY,
    ObservabilityRetentionPolicy,
    ObservabilityRetentionPolicyValidator,
    ObservabilityRetentionTarget,
    load_observability_retention_policy,
)

OBSERVABILITY_INVENTORY_SCHEMA_ID = "SCHEMA-DEVPL-OBSERVABILITY-INVENTORY-V1"
OBSERVABILITY_INVENTORY_CONTRACT = "ObservabilityInventory"
OBSERVABILITY_INVENTORY_ID = "devpilot-local-observability-inventory"
POST_H_010_B_CREATED_BY = "POST-H-010-B"
DEFAULT_OBSERVABILITY_INVENTORY_JSON = Path("outputs/reports/observability_inventory.json")
DEFAULT_OBSERVABILITY_INVENTORY_MARKDOWN = Path("outputs/reports/observability_inventory.md")


@dataclass(frozen=True)
class ObservabilityInventoryOptions:
    policy_path: str | Path = DEFAULT_OBSERVABILITY_RETENTION_POLICY
    write_report: bool = False
    output_json: str | Path = DEFAULT_OBSERVABILITY_INVENTORY_JSON
    output_markdown: str | Path = DEFAULT_OBSERVABILITY_INVENTORY_MARKDOWN


class ObservabilityInventoryBuilder:
    """Build a local read-only inventory of observability runtime targets.

    POST-H-010-B deliberately inspects metadata only: path existence, size,
    modification time, estimated record/file counts and policy-derived risk. It
    does not read raw prompt/output payloads, does not mutate runtime files and
    only writes evidence reports when --write-report is explicitly requested.
    """

    def __init__(self, root: Path, options: ObservabilityInventoryOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ObservabilityInventoryOptions()

    def run(self) -> CommandResult:
        try:
            policy_validation = ObservabilityRetentionPolicyValidator(self.root, policy_path=self.options.policy_path).validate()
            policy = load_observability_retention_policy(self.root, self.options.policy_path)
            payload = self.build_inventory(policy, policy_validation)
        except Exception as exc:  # defensive boundary for CLI users
            finding = Finding(
                id="OBSERVABILITY_INVENTORY_ERROR",
                message=f"Observability inventory could not be built: {exc}",
                severity=Severity.ERROR,
            )
            return CommandResult(
                command="observability inventory",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Observability inventory failed.",
                data={"summary": {"policy_loaded": False, "read_only": True, "preliminary": True}},
                findings=[finding],
            )

        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._planned_report_paths()
            payload["summary"]["reports_written"] = True
            payload["summary"]["output_json"] = reports["json"]
            payload["summary"]["output_markdown"] = reports["markdown"]
            self._write_reports(payload)
        else:
            payload["summary"]["reports_written"] = False
            payload["summary"]["output_json"] = None
            payload["summary"]["output_markdown"] = None

        findings = _findings_from_inventory(payload)
        blocking = [item for item in findings if item.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        return CommandResult(
            command="observability inventory",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Observability inventory passed." if not blocking else "Observability inventory found blocking findings.",
            data={"summary": payload["summary"], "inventory": payload, "reports": reports},
            findings=findings,
        )

    def build_inventory(
        self,
        policy: ObservabilityRetentionPolicy,
        policy_validation: CommandResult | None = None,
    ) -> dict[str, Any]:
        policy_findings = list(policy_validation.findings if policy_validation else [])
        target_checks = [self._target_check(target) for target in policy.targets]
        findings = self._detect_findings(policy, target_checks, policy_findings)

        warning_total = sum(1 for item in findings if item["severity"] == "warning")
        blocking_total = sum(1 for item in findings if item["severity"] in {"block", "error", "fail"})
        existing_targets = [item for item in target_checks if item["exists"]]
        missing_required = [item for item in target_checks if item["required"] and not item["exists"]]
        rotation_recommended = [item for item in target_checks if item["rotation_recommended"]]
        expired = [item for item in target_checks if item["expired"]]
        sensitive_existing = [item for item in existing_targets if item["contains_sensitive_payloads"]]
        clean_zip_risks = [item for item in target_checks if item["clean_zip_risk"]]

        summary = {
            "policy_loaded": True,
            "created_by": POST_H_010_B_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "read_only": True,
            "targets_total": len(target_checks),
            "targets_existing_total": len(existing_targets),
            "targets_missing_total": len(target_checks) - len(existing_targets),
            "required_targets_missing_total": len(missing_required),
            "targets_expired_total": len(expired),
            "rotation_recommended_total": len(rotation_recommended),
            "redaction_required_total": sum(1 for item in target_checks if item["redaction_required"]),
            "sensitive_existing_targets_total": len(sensitive_existing),
            "clean_zip_excluded_total": sum(1 for item in target_checks if item["clean_zip_excluded"]),
            "clean_zip_risks_total": len(clean_zip_risks),
            "bytes_total": sum(int(item["size_bytes"] or 0) for item in target_checks),
            "records_estimated_total": sum(int(item["records_estimated"] or 0) for item in target_checks),
            "warnings_total": warning_total,
            "blocking_findings_total": blocking_total,
            "policy_validation_passed": bool(policy_validation.ok if policy_validation else True),
            "policy_id": policy.policy_id,
            "policy_path": _rel(self.root, self.root / self.options.policy_path),
            "cleanup_execution_enabled": False,
            "export_execution_enabled": False,
            "redaction_execution_enabled": False,
            "raw_payloads_read": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "destructive_cleanup_performed": False,
            "source_mutations_performed": False,
        }

        return {
            "schema_version": "1.0",
            "schema_id": OBSERVABILITY_INVENTORY_SCHEMA_ID,
            "inventory_id": OBSERVABILITY_INVENTORY_ID,
            "created_by": POST_H_010_B_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": _utc_now_iso(),
            "policy_id": policy.policy_id,
            "policy_path": _rel(self.root, self.root / self.options.policy_path),
            "targets_total": len(target_checks),
            "target_checks": target_checks,
            "findings": findings,
            "summary": summary,
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "raw_payloads_read": False,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "destructive_cleanup_performed": False,
                "source_mutations_performed": False,
                "cleanup_execution_enabled": False,
                "export_execution_enabled": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
            },
            "notes": [
                "POST-H-010-B inventory is read-only: it inspects filesystem and SQLite metadata only.",
                "Missing runtime artifacts in a clean source checkout are warnings, not blocking findings.",
                "Reports are written only when --write-report is explicitly provided and always under outputs/reports/.",
            ],
        }

    def _target_check(self, target: ObservabilityRetentionTarget) -> dict[str, Any]:
        rel_path = target.path
        resolved = (self.root / rel_path).resolve()
        inside_workspace = _is_inside(self.root, resolved)
        exists = inside_workspace and resolved.exists()
        stat = resolved.stat() if exists else None
        is_dir = bool(exists and resolved.is_dir())
        size_bytes = _safe_size_bytes(resolved) if exists else 0
        modified_at = _mtime_iso(resolved) if exists else None
        latest_child_modified_at = _latest_child_mtime_iso(resolved) if is_dir else None
        effective_modified_at = latest_child_modified_at or modified_at
        age_days = _age_days(effective_modified_at)
        expired = bool(exists and age_days is not None and age_days > target.retention_days)
        max_size_bytes = int(float(target.max_size_mb) * 1024 * 1024)
        size_exceeded = bool(exists and max_size_bytes > 0 and size_bytes > max_size_bytes)
        rotation_recommended = bool(exists and target.rotation.enabled and (expired or size_exceeded))
        records_estimated = _estimate_records(resolved, target) if exists else 0
        clean_zip_risk = bool(exists and _is_runtime_path(rel_path) and not target.clean_zip_excluded)
        risk_level = _risk_level(target, exists=exists, clean_zip_risk=clean_zip_risk, expired=expired, size_exceeded=size_exceeded, inside_workspace=inside_workspace)

        return {
            "target_id": target.target_id,
            "path": rel_path,
            "kind": target.kind,
            "classification": target.classification,
            "required": target.required,
            "exists": exists,
            "inside_workspace": inside_workspace,
            "size_bytes": int(size_bytes),
            "modified_at": modified_at,
            "latest_child_modified_at": latest_child_modified_at,
            "records_estimated": int(records_estimated),
            "retention_days": target.retention_days,
            "age_days": age_days,
            "expired": expired,
            "max_size_mb": target.max_size_mb,
            "size_exceeded": size_exceeded,
            "rotation_enabled": target.rotation.enabled,
            "rotation_strategy": target.rotation.strategy,
            "rotation_recommended": rotation_recommended,
            "redaction_required": target.redaction_required,
            "contains_sensitive_payloads": target.contains_sensitive_payloads,
            "clean_zip_excluded": target.clean_zip_excluded,
            "clean_zip_risk": clean_zip_risk,
            "export_allowed": target.export_allowed,
            "cleanup_allowed": target.cleanup_allowed,
            "source_of_truth": target.source_of_truth,
            "versionable": target.versionable,
            "raw_payload_storage_allowed": target.raw_payload_storage_allowed,
            "logical_scope": target.logical_scope,
            "risk_level": risk_level,
        }

    def _detect_findings(
        self,
        policy: ObservabilityRetentionPolicy,
        target_checks: list[dict[str, Any]],
        policy_findings: list[Finding],
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for finding in policy_findings:
            if finding.severity != Severity.INFO:
                findings.append(finding.to_dict())

        if policy.remote_export_enabled:
            findings.append(_finding_dict("OBSERVABILITY_REMOTE_EXPORT_ENABLED", "Remote observability export is not allowed for POST-H-010-B inventory.", "block"))
        if not policy.local_first:
            findings.append(_finding_dict("OBSERVABILITY_POLICY_NOT_LOCAL_FIRST", "Observability inventory requires a local-first policy.", "block"))

        for item in target_checks:
            if not item["inside_workspace"]:
                findings.append(_finding_dict("OBSERVABILITY_TARGET_PATH_ESCAPE", "Observability target resolves outside workspace.", "block", path=item["path"], metadata={"target_id": item["target_id"]}))
            if not item["exists"]:
                severity = "warning" if item["required"] else "info"
                findings.append(_finding_dict("OBSERVABILITY_TARGET_MISSING", "Observability runtime target is not present in this checkout; this is expected for clean source archives but must be present in runtime workspaces when used.", severity, path=item["path"], metadata={"target_id": item["target_id"], "required": item["required"]}))
            if item["clean_zip_risk"]:
                findings.append(_finding_dict("OBSERVABILITY_CLEAN_ZIP_RISK", "Runtime observability target exists but is not marked clean_zip_excluded=true.", "block", path=item["path"], metadata={"target_id": item["target_id"]}))
            if item["versionable"] or item["source_of_truth"]:
                findings.append(_finding_dict("OBSERVABILITY_RUNTIME_TARGET_VERSIONABLE", "Runtime observability targets must not be source-of-truth or versionable.", "block", path=item["path"], metadata={"target_id": item["target_id"]}))
            if item["raw_payload_storage_allowed"]:
                findings.append(_finding_dict("OBSERVABILITY_RAW_PAYLOAD_STORAGE_ALLOWED", "Raw payload storage is forbidden for observability retention targets.", "block", path=item["path"], metadata={"target_id": item["target_id"]}))
            if item["rotation_recommended"]:
                findings.append(_finding_dict("OBSERVABILITY_ROTATION_RECOMMENDED", "Target exceeds age/size retention thresholds; POST-H-010-C should plan rotation/cleanup in dry-run.", "warning", path=item["path"], metadata={"target_id": item["target_id"], "age_days": item["age_days"], "size_exceeded": item["size_exceeded"]}))
        return findings

    def _planned_report_paths(self) -> dict[str, str]:
        return {
            "json": _rel(self.root, self.root / self.options.output_json),
            "markdown": _rel(self.root, self.root / self.options.output_markdown),
        }

    def _write_reports(self, payload: dict[str, Any]) -> None:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(render_observability_inventory_markdown(payload), encoding="utf-8")


def render_observability_inventory_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# DevPilot Observability Inventory",
        "",
        f"- Schema: `{payload.get('schema_id')}`",
        f"- Created by: `{payload.get('created_by')}`",
        f"- Status: `{payload.get('status')}`",
        f"- Generated: `{payload.get('generated_at_utc')}`",
        f"- Policy: `{payload.get('policy_path')}`",
        "",
        "## Summary",
        "",
        f"- Targets: {summary.get('targets_total', 0)}",
        f"- Existing targets: {summary.get('targets_existing_total', 0)}",
        f"- Missing targets: {summary.get('targets_missing_total', 0)}",
        f"- Warnings: {summary.get('warnings_total', 0)}",
        f"- Blocking findings: {summary.get('blocking_findings_total', 0)}",
        f"- Read only: {summary.get('read_only')}",
        f"- Raw payloads read: {summary.get('raw_payloads_read')}",
        "",
        "## Target checks",
        "",
        "| Target | Path | Exists | Size bytes | Records estimated | Expired | Rotation | Risk |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in payload.get("target_checks", []):
        lines.append(
            "| {target_id} | `{path}` | {exists} | {size_bytes} | {records_estimated} | {expired} | {rotation_recommended} | {risk_level} |".format(**item)
        )
    lines.extend(["", "## Findings", ""])
    findings = payload.get("findings", [])
    if not findings:
        lines.append("No findings.")
    else:
        for finding in findings:
            path = f" `{finding.get('path')}`" if finding.get("path") else ""
            lines.append(f"- **{finding.get('severity')}** `{finding.get('id')}`{path}: {finding.get('message')}")
    lines.extend([
        "",
        "## Safety",
        "",
        "```json",
        json.dumps(payload.get("safety", {}), indent=2, ensure_ascii=False),
        "```",
        "",
    ])
    return "\n".join(lines)


def _findings_from_inventory(payload: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for item in payload.get("findings", []):
        severity = _severity_from_string(str(item.get("severity", "info")))
        findings.append(
            Finding(
                id=str(item.get("id", "OBSERVABILITY_INVENTORY_FINDING")),
                message=str(item.get("message", "Observability inventory finding.")),
                severity=severity,
                path=str(item["path"]) if item.get("path") else None,
                metadata=dict(item.get("metadata", {})),
            )
        )
    if not findings:
        findings.append(
            Finding(
                id="OBSERVABILITY_INVENTORY_PASS",
                message="Observability inventory completed without blocking findings.",
                severity=Severity.INFO,
                metadata={"targets_total": payload.get("summary", {}).get("targets_total", 0)},
            )
        )
    return findings


def _finding_dict(id_: str, message: str, severity: str, *, path: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"id": id_, "message": message, "severity": severity}
    if path:
        payload["path"] = path
    if metadata:
        payload["metadata"] = metadata
    return payload


def _severity_from_string(value: str) -> Severity:
    return {
        "info": Severity.INFO,
        "warning": Severity.WARNING,
        "warn": Severity.WARNING,
        "block": Severity.BLOCK,
        "fail": Severity.FAIL,
        "error": Severity.ERROR,
    }.get(value, Severity.INFO)


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    if path.is_dir():
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total += item.stat().st_size
                except OSError:
                    continue
    return total


def _mtime_iso(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except OSError:
        return None


def _latest_child_mtime_iso(path: Path) -> str | None:
    if not path.exists() or not path.is_dir():
        return None
    latest: float | None = None
    for item in path.rglob("*"):
        try:
            mtime = item.stat().st_mtime
        except OSError:
            continue
        latest = mtime if latest is None else max(latest, mtime)
    if latest is None:
        return _mtime_iso(path)
    return datetime.fromtimestamp(latest, UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _age_days(iso_value: str | None) -> int | None:
    if not iso_value:
        return None
    try:
        dt = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0, int((datetime.now(UTC) - dt).total_seconds() // 86400))


def _estimate_records(path: Path, target: ObservabilityRetentionTarget) -> int:
    if not path.exists():
        return 0
    if path.is_dir():
        return sum(1 for item in path.rglob("*") if item.is_file())
    if target.kind == "jsonl":
        # Count line boundaries only. This avoids loading or parsing raw payloads.
        try:
            with path.open("rb") as handle:
                return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))
        except OSError:
            return 0
    if target.kind in {"sqlite", "sqlite-table"}:
        return _sqlite_row_count_metadata_only(path)
    return 1 if path.is_file() else 0


def _sqlite_row_count_metadata_only(path: Path) -> int:
    try:
        conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    except sqlite3.Error:
        return 0
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        table_names = [str(row[0]) for row in cursor.fetchall()]
        total = 0
        for name in table_names:
            if not name.replace("_", "").replace("-", "").isalnum():
                continue
            try:
                total += int(conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
            except sqlite3.Error:
                continue
        return total
    finally:
        conn.close()


def _is_runtime_path(path: str) -> bool:
    return path.startswith("outputs/") or path in {".devpilot/devpilot.db", ".devpilot/agent_sessions/"} or path.startswith(".devpilot/agent_sessions/")


def _risk_level(
    target: ObservabilityRetentionTarget,
    *,
    exists: bool,
    clean_zip_risk: bool,
    expired: bool,
    size_exceeded: bool,
    inside_workspace: bool,
) -> str:
    if not inside_workspace or clean_zip_risk or target.raw_payload_storage_allowed or target.versionable or target.source_of_truth:
        return "high"
    if exists and target.contains_sensitive_payloads:
        return "medium-high" if target.redaction_required else "high"
    if exists and (expired or size_exceeded):
        return "medium"
    if not exists:
        return "low"
    return "low"
