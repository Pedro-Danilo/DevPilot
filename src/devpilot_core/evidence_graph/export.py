from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.evidence_graph.builder import EvidenceGraphBuilder, EvidenceGraphOptions
from devpilot_core.evidence_graph.claims_dashboard import ClaimsDashboardOptions, ClaimsNoGoDashboardBuilder
from devpilot_core.evidence_graph.gap_actions import GapActionMapBuilder, GapActionOptions
from devpilot_core.evidence_graph.health import OperatorHealthOptions, OperatorHealthSummaryBuilder
from devpilot_core.industrial.production_ready import ProductionReadyFinalDeclaration, ProductionReadyFinalDeclarationOptions
from devpilot_core.observability.export import ObservabilityRedactedExportOptions, ObservabilityRedactedExporter
from devpilot_core.policy.secrets import redact_sensitive_string
from devpilot_core.runtime_state.inventory import RuntimeStateInventoryBuilder, RuntimeStateInventoryOptions

POST_H_031_E_CREATED_BY = "POST-H-031-E"
OPERATOR_EVIDENCE_EXPORT_SCHEMA_ID = "SCHEMA-DEVPL-OPERATOR-EVIDENCE-EXPORT-V1"
OPERATOR_EVIDENCE_EXPORT_CONTRACT = "OperatorEvidenceExport"
OPERATOR_EVIDENCE_EXPORT_ID = "devpilot-operator-evidence-export"
DEFAULT_OPERATOR_EVIDENCE_EXPORT_JSON = Path("outputs/reports/operator_evidence_export.json")
DEFAULT_OPERATOR_EVIDENCE_EXPORT_MARKDOWN = Path("outputs/reports/operator_evidence_export.md")
DEFAULT_OPERATOR_EVIDENCE_EXPORT_DIR = Path("outputs/audit_exports/operator_evidence_export")

_SECTION_FILE_NAMES = {
    "evidence_graph": "evidence_graph_summary.json",
    "operator_health": "operator_health_summary.json",
    "gap_action_map": "gap_action_map_summary.json",
    "claims_no_go_dashboard": "claims_no_go_dashboard_summary.json",
    "observability_redacted_export": "observability_redacted_export_summary.json",
    "runtime_state_inventory": "runtime_state_inventory_summary.json",
    "production_ready_final_declaration": "production_ready_final_declaration_summary.json",
}
_FORBIDDEN_EXPORT_FRAGMENTS = (
    ".env",
    ".devpilot/devpilot.db",
    "devpilot.db",
    "raw_prompt",
    "raw_prompts",
    "raw_output",
    "raw_outputs",
    "prompt_payload",
    "outputs/raw",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _display_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(_json_dumps(payload).encode("utf-8")).hexdigest()


def _safe_summary(result: CommandResult, *, section_id: str) -> dict[str, Any]:
    data = result.data if isinstance(result.data, dict) else {}
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    return {
        "section_id": section_id,
        "command": result.command,
        "ok": bool(result.ok),
        "exit_code": int(result.exit_code),
        "message": result.message,
        "summary": summary,
        "findings": [finding.to_dict() for finding in (result.findings or [])],
    }


def _string_leaf_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_string_leaf_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_string_leaf_values(item))
    elif isinstance(value, str):
        values.append(value)
    return values


def _scrub_forbidden_string_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _scrub_forbidden_string_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub_forbidden_string_values(item) for item in value]
    if not isinstance(value, str):
        return value
    replacements = {
        ".devpilot/devpilot.db": "[REDACTED-SQLITE-METADATA-PATH]",
        "\\.devpilot\\devpilot.db": "[REDACTED-SQLITE-METADATA-PATH]",
        "devpilot.db": "[REDACTED-SQLITE-METADATA-PATH]",
        ".env": "[REDACTED-ENV-PATH]",
        "raw_prompt": "[REDACTED-RAW-PAYLOAD-REFERENCE]",
        "raw_prompts": "[REDACTED-RAW-PAYLOAD-REFERENCE]",
        "raw_output": "[REDACTED-RAW-PAYLOAD-REFERENCE]",
        "raw_outputs": "[REDACTED-RAW-PAYLOAD-REFERENCE]",
        "prompt_payload": "[REDACTED-RAW-PAYLOAD-REFERENCE]",
    }
    scrubbed = value
    for source, replacement in replacements.items():
        scrubbed = scrubbed.replace(source, replacement)
    return scrubbed


def _secret_value_redactions_total(payload: Any) -> int:
    # SecretGuard.scan_text on the whole JSON would treat safe field names such as
    # no_secrets=false as secret-like. For export validation we scan string leaf
    # values only, which is the part that can carry leaked payloads.
    total = 0
    for text in _string_leaf_values(payload):
        _redacted, count = redact_sensitive_string(text)
        total += count
    return total


def _ensure_outputs_relative(path: Path) -> Path:
    normalized = Path(str(path).replace("\\", "/"))
    if normalized.is_absolute():
        raise ValueError(f"Operator evidence export path must be relative to project root: {normalized}")
    if not normalized.parts or normalized.parts[0] != "outputs":
        raise ValueError(f"Operator evidence export writes are restricted to outputs/: {normalized}")
    if any(part == ".." for part in normalized.parts):
        raise ValueError(f"Operator evidence export path cannot contain '..': {normalized}")
    return normalized


@dataclass(frozen=True)
class OperatorEvidenceExportOptions:
    redacted: bool = False
    dry_run: bool = True
    write_report: bool = False
    output_json: Path = DEFAULT_OPERATOR_EVIDENCE_EXPORT_JSON
    output_markdown: Path = DEFAULT_OPERATOR_EVIDENCE_EXPORT_MARKDOWN
    package_dir: Path = DEFAULT_OPERATOR_EVIDENCE_EXPORT_DIR
    observability_limit: int = 100


class OperatorEvidenceExportBuilder:
    """Build POST-H-031-E redacted operator evidence export UX.

    The export is intentionally a curated package of summaries. It never copies
    arbitrary outputs, .env files, raw prompts/outputs, SQLite bytes or secrets.
    Write mode is explicit and constrained to outputs/audit_exports plus the
    companion outputs/reports JSON/Markdown report.
    """

    def __init__(self, root: Path, options: OperatorEvidenceExportOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or OperatorEvidenceExportOptions()

    def build(self) -> CommandResult:
        if not self.options.redacted:
            finding = Finding(
                "OPERATOR_EVIDENCE_EXPORT_REDACTION_REQUIRED",
                "Operator evidence export requires --redacted; unredacted exports are blocked.",
                Severity.BLOCK,
            )
            return CommandResult(
                command="operator evidence-export",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Operator evidence export blocked because --redacted was not provided.",
                data={"summary": self._base_summary(decision="BLOCK", execution_blocked=True, reports_written=False)},
                findings=[finding],
            )
        if self.options.write_report and self.options.dry_run:
            finding = Finding(
                "OPERATOR_EVIDENCE_EXPORT_DRY_RUN_WRITE_CONFLICT",
                "Dry-run cannot write files. Use --redacted --dry-run for preview or --redacted --write-report for package generation.",
                Severity.BLOCK,
            )
            return CommandResult(
                command="operator evidence-export",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Operator evidence export blocked because --dry-run and --write-report conflict.",
                data={"summary": self._base_summary(decision="BLOCK", execution_blocked=True, reports_written=False)},
                findings=[finding],
            )

        try:
            payload = self._build_payload()
        except Exception as exc:
            finding = Finding(
                "OPERATOR_EVIDENCE_EXPORT_ERROR",
                f"Operator evidence export failed: {exc}",
                Severity.ERROR,
            )
            return CommandResult(
                command="operator evidence-export",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Operator evidence export failed.",
                data={"summary": self._base_summary(decision="ERROR", execution_blocked=True, reports_written=False)},
                findings=[finding],
            )

        findings = self._validate_payload(payload)
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        if self.options.write_report and not blocking:
            payload["summary"]["reports_written"] = True
            payload["summary"]["dry_run"] = False
            payload["summary"]["read_only"] = False
            payload["summary"]["files_written_total"] = len(payload.get("exported_files", []))
            payload["safety"]["reports_written"] = True
            payload["manifest"]["reports_written"] = True
        else:
            payload["summary"]["reports_written"] = False
            payload["summary"]["dry_run"] = True
            payload["summary"]["read_only"] = True
            payload["summary"]["files_written_total"] = 0
            payload["safety"]["reports_written"] = False
            payload["manifest"]["reports_written"] = False

        # Recompute package checksum after write flags are finalized for stable report payload.
        payload["checksums"]["operator_evidence_export.json"] = _sha256_payload(payload)
        payload["summary"]["checksums_total"] = len(payload["checksums"])
        payload["manifest"]["checksums"] = payload["checksums"]
        if self.options.write_report and not blocking:
            self._write_package(payload)
            self._write_report_files(payload)

        summary = dict(payload["summary"])
        ok = not blocking
        result_findings = findings or [
            Finding(
                "OPERATOR_EVIDENCE_EXPORT_READY",
                "Redacted operator evidence export is available.",
                Severity.INFO,
                metadata={"sections_total": summary.get("sections_total", 0), "dry_run": summary.get("dry_run")},
            )
        ]
        return CommandResult(
            command="operator evidence-export",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Operator evidence export built." if ok else "Operator evidence export has blocking findings.",
            data={"summary": summary, "export": payload},
            findings=result_findings,
        )

    def _build_payload(self) -> dict[str, Any]:
        generated_at = _utc_now()
        results = self._collect_results()
        sections = _scrub_forbidden_string_values(self._sections_from_results(results))
        redactions_total = _secret_value_redactions_total(sections)
        checksums = {f"sections/{_SECTION_FILE_NAMES[section_id]}": _sha256_payload(section) for section_id, section in sections.items()}
        export_id = f"operator-evidence-export-{hashlib.sha256(_json_dumps(checksums).encode('utf-8')).hexdigest()[:12]}"
        package_dir = _ensure_outputs_relative(self.options.package_dir)
        output_json = _ensure_outputs_relative(self.options.output_json)
        output_markdown = _ensure_outputs_relative(self.options.output_markdown)
        exported_files = self._planned_files(package_dir, output_json, output_markdown, sections)
        redaction_manifest = {
            "redaction_required": True,
            "redaction_applied": True,
            "redactions_total": redactions_total,
            "secret_value_scan_passed": redactions_total == 0,
            "raw_prompts_exported": False,
            "raw_outputs_exported": False,
            "raw_payloads_exported": False,
            "env_files_exported": False,
            "sqlite_raw_exported": False,
            "devpilot_db_exported": False,
            "outputs_raw_exported": False,
            "sections_metadata_only": True,
            "llm_judge_used": False,
        }
        summary = {
            **self._base_summary(decision="PASS", execution_blocked=False, reports_written=False),
            "export_id": export_id,
            "generated_at_utc": generated_at,
            "sections_total": len(sections),
            "checksums_total": len(checksums),
            "redactions_total": redactions_total,
            "secret_value_scan_passed": redactions_total == 0,
            "package_dir": _display_path(package_dir),
            "output_json": _display_path(output_json),
            "output_markdown": _display_path(output_markdown),
            "files_planned_total": len(exported_files),
            "files_written_total": 0,
        }
        safety = {
            "local_first": True,
            "redacted": True,
            "redaction_required": True,
            "redaction_applied": True,
            "dry_run": bool(self.options.dry_run or not self.options.write_report),
            "read_only_until_write_report": True,
            "write_report_requested": bool(self.options.write_report),
            "reports_written": False,
            "network_used": False,
            "external_api_used": False,
            "source_mutations_performed": False,
            "commands_executed": False,
            "secrets_read": False,
            "raw_payloads_exported": False,
            "raw_prompts_exported": False,
            "raw_outputs_exported": False,
            "env_files_exported": False,
            "devpilot_db_exported": False,
            "sqlite_raw_exported": False,
            "destructive_cleanup_performed": False,
            "claims_mutated": False,
            "no_go_gates_mutated": False,
        }
        manifest = {
            "manifest_id": "operator-evidence-export-manifest",
            "export_id": export_id,
            "created_by": POST_H_031_E_CREATED_BY,
            "generated_at_utc": generated_at,
            "redacted": True,
            "reports_written": False,
            "package_dir": _display_path(package_dir),
            "exported_files": exported_files,
            "checksums": checksums,
            "redaction_manifest": redaction_manifest,
        }
        return {
            "schema_version": "1.0",
            "schema_id": OPERATOR_EVIDENCE_EXPORT_SCHEMA_ID,
            "export_id": export_id,
            "created_by": POST_H_031_E_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": generated_at,
            "redacted": True,
            "dry_run": bool(self.options.dry_run or not self.options.write_report),
            "summary": summary,
            "sections": sections,
            "manifest": manifest,
            "checksums": checksums,
            "redaction_manifest": redaction_manifest,
            "exported_files": exported_files,
            "interpretation": {
                "audience": "internal technical auditor/operator",
                "scope": "local-first operator evidence summary",
                "not_external_certification": True,
                "not_enterprise_ready_claim": True,
                "not_remote_ready_claim": True,
                "not_saas_ready_claim": True,
                "instructions": [
                    "Use this package as a redacted summary of local DevPilot evidence.",
                    "Regenerate runtime reports locally when a section points to missing outputs/reports evidence.",
                    "Treat production-ready-local as bounded to the local-first scope only.",
                    "Do not infer compliance certification, enterprise readiness, remote readiness or SaaS readiness from this package.",
                ],
            },
            "safety": safety,
            "limitations": [
                "OperatorEvidenceExport is a redacted operator/auditor UX package, not a certification artifact.",
                "It exports curated summaries and checksums only; it does not copy arbitrary outputs, prompts, model outputs or databases.",
                "Write mode is explicit and constrained to outputs/reports and outputs/audit_exports/operator_evidence_export.",
                "Formal PASS/BLOCK remains owned by dedicated validators and quality gates.",
            ],
            "findings": [],
            "notes": [
                "POST-H-031-E closes the operator evidence UX layer with a redacted export package.",
                "Runtime outputs remain regenerable and excluded from clean source ZIPs.",
            ],
        }

    def _collect_results(self) -> dict[str, CommandResult]:
        return {
            "evidence_graph": EvidenceGraphBuilder(self.root, EvidenceGraphOptions(write_report=False)).build(),
            "operator_health": OperatorHealthSummaryBuilder(self.root, OperatorHealthOptions(write_report=False)).build(),
            "gap_action_map": GapActionMapBuilder(self.root, GapActionOptions(write_report=False)).build(),
            "claims_no_go_dashboard": ClaimsNoGoDashboardBuilder(self.root, ClaimsDashboardOptions(write_report=False)).build(),
            "observability_redacted_export": ObservabilityRedactedExporter(
                self.root,
                ObservabilityRedactedExportOptions(redacted=True, write_report=False, limit=self.options.observability_limit),
            ).run(),
            "runtime_state_inventory": RuntimeStateInventoryBuilder(self.root, RuntimeStateInventoryOptions(write_report=False)).run(),
            "production_ready_final_declaration": ProductionReadyFinalDeclaration(
                self.root,
                options=ProductionReadyFinalDeclarationOptions(write_report=False, write_audit_markdown=False),
            ).finalize(),
        }

    def _sections_from_results(self, results: dict[str, CommandResult]) -> dict[str, dict[str, Any]]:
        sections: dict[str, dict[str, Any]] = {}
        for section_id, result in results.items():
            section = _safe_summary(result, section_id=section_id)
            section["redacted"] = True
            section["metadata_only"] = True
            section["raw_payload_exported"] = False
            section["source_refs"] = self._section_source_refs(section_id)
            sections[section_id] = section
        return sections

    def _section_source_refs(self, section_id: str) -> list[dict[str, Any]]:
        refs = {
            "evidence_graph": [".devpilot/evidence/evidence_graph_sources.json"],
            "operator_health": [".devpilot/operator/operator_health_config.json"],
            "gap_action_map": [".devpilot/evidence/gap_action_rules.json"],
            "claims_no_go_dashboard": [".devpilot/operator/claims_no_go_dashboard_config.json"],
            "observability_redacted_export": ["docs/schemas/observability_redacted_export.schema.json"],
            "runtime_state_inventory": [".devpilot/runtime_state_policy.json"],
            "production_ready_final_declaration": [".devpilot/production/production_ready_local_criteria.json", "docs/audits/devpilot_local_production_ready_declaration.md"],
        }
        return [
            {
                "path": path,
                "kind": "source" if not path.startswith("outputs/") else "generated-report",
                "required": True,
                "available": (self.root / path).exists(),
                "description": f"Source for {section_id}",
            }
            for path in refs.get(section_id, [])
        ]

    def _planned_files(self, package_dir: Path, output_json: Path, output_markdown: Path, sections: dict[str, Any]) -> list[dict[str, Any]]:
        files = [
            {"path": _display_path(output_json), "kind": "report-json", "redacted": True, "write_mode": "write-report"},
            {"path": _display_path(output_markdown), "kind": "report-markdown", "redacted": True, "write_mode": "write-report"},
            {"path": _display_path(package_dir / "operator_evidence_export.json"), "kind": "package-json", "redacted": True, "write_mode": "write-report"},
            {"path": _display_path(package_dir / "operator_evidence_export_manifest.json"), "kind": "manifest-json", "redacted": True, "write_mode": "write-report"},
            {"path": _display_path(package_dir / "operator_evidence_export_README.md"), "kind": "auditor-readme", "redacted": True, "write_mode": "write-report"},
            {"path": _display_path(package_dir / "checksums.sha256"), "kind": "checksums", "redacted": True, "write_mode": "write-report"},
        ]
        for section_id in sections:
            files.append({"path": _display_path(package_dir / "sections" / _SECTION_FILE_NAMES[section_id]), "kind": "section-json", "redacted": True, "write_mode": "write-report"})
        return files

    def _validate_payload(self, payload: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        text_paths = "\n".join(item.get("path", "") for item in payload.get("exported_files", []) if isinstance(item, dict)).lower()
        for fragment in _FORBIDDEN_EXPORT_FRAGMENTS:
            if fragment.lower() in text_paths:
                findings.append(Finding("OPERATOR_EVIDENCE_EXPORT_FORBIDDEN_PATH", f"Forbidden export path fragment detected: {fragment}", Severity.BLOCK))
        if int(payload.get("redaction_manifest", {}).get("redactions_total", 0)) > 0:
            findings.append(Finding("OPERATOR_EVIDENCE_EXPORT_SECRET_VALUE_DETECTED", "Secret-like string value was detected in export sections.", Severity.BLOCK, metadata={"redactions_total": payload["redaction_manifest"].get("redactions_total")}))
        if not payload.get("redacted"):
            findings.append(Finding("OPERATOR_EVIDENCE_EXPORT_NOT_REDACTED", "Export payload is not marked redacted.", Severity.BLOCK))
        if not payload.get("checksums"):
            findings.append(Finding("OPERATOR_EVIDENCE_EXPORT_CHECKSUMS_MISSING", "Export manifest must include checksums.", Severity.BLOCK))
        if not findings:
            findings.append(Finding("OPERATOR_EVIDENCE_EXPORT_READY", "Redacted operator evidence export package is safe to generate.", Severity.INFO, metadata={"sections_total": payload.get("summary", {}).get("sections_total", 0)}))
        payload["findings"] = [finding.to_dict() for finding in findings]
        return findings

    def _write_package(self, payload: dict[str, Any]) -> None:
        package_dir = self.root / _ensure_outputs_relative(self.options.package_dir)
        sections_dir = package_dir / "sections"
        sections_dir.mkdir(parents=True, exist_ok=True)
        for section_id, section in payload.get("sections", {}).items():
            (sections_dir / _SECTION_FILE_NAMES[section_id]).write_text(_json_dumps(section) + "\n", encoding="utf-8")
        (package_dir / "operator_evidence_export.json").write_text(_json_dumps(payload) + "\n", encoding="utf-8")
        (package_dir / "operator_evidence_export_manifest.json").write_text(_json_dumps(payload["manifest"]) + "\n", encoding="utf-8")
        (package_dir / "operator_evidence_export_README.md").write_text(render_operator_evidence_export_markdown(payload), encoding="utf-8")
        checksums_text = "".join(f"{sha}  {path}\n" for path, sha in sorted(payload.get("checksums", {}).items()))
        (package_dir / "checksums.sha256").write_text(checksums_text, encoding="utf-8")

    def _write_report_files(self, payload: dict[str, Any]) -> None:
        output_json = self.root / _ensure_outputs_relative(self.options.output_json)
        output_markdown = self.root / _ensure_outputs_relative(self.options.output_markdown)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(_json_dumps(payload) + "\n", encoding="utf-8")
        output_markdown.write_text(render_operator_evidence_export_markdown(payload), encoding="utf-8")

    def _base_summary(self, *, decision: str, execution_blocked: bool, reports_written: bool) -> dict[str, Any]:
        return {
            "created_by": POST_H_031_E_CREATED_BY,
            "status": "implemented-initial" if decision != "BLOCK" else "blocked",
            "decision": decision,
            "redacted": bool(self.options.redacted),
            "redaction_required": True,
            "redaction_applied": bool(self.options.redacted),
            "dry_run": bool(self.options.dry_run or not self.options.write_report),
            "write_report_requested": bool(self.options.write_report),
            "execution_blocked": execution_blocked,
            "reports_written": reports_written,
            "read_only": not bool(self.options.write_report),
            "network_used": False,
            "external_api_used": False,
            "commands_executed": False,
            "source_mutations_performed": False,
            "mutations_performed": False,
            "raw_payloads_exported": False,
            "raw_prompts_exported": False,
            "raw_outputs_exported": False,
            "env_files_exported": False,
            "devpilot_db_exported": False,
            "sqlite_raw_exported": False,
            "claims_mutated": False,
            "no_go_gates_mutated": False,
            "preliminary": True,
        }


def render_operator_evidence_export_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    interpretation = payload.get("interpretation", {}) if isinstance(payload.get("interpretation"), dict) else {}
    lines = [
        "# Operator evidence export",
        "",
        f"Export ID: `{payload.get('export_id', '')}`",
        f"Generated at UTC: `{payload.get('generated_at_utc', '')}`",
        f"Created by: `{payload.get('created_by', '')}`",
        f"Decision: `{summary.get('decision', '')}`",
        f"Redacted: `{payload.get('redacted', False)}`",
        f"Dry-run: `{summary.get('dry_run', False)}`",
        f"Reports written: `{summary.get('reports_written', False)}`",
        "",
        "## Scope",
        "",
        str(interpretation.get("scope", "local-first operator evidence summary")),
        "",
        "This package is not an external certification, enterprise-ready declaration, remote-ready declaration or SaaS-ready declaration.",
        "",
        "## Summary",
        "",
        f"- Sections: `{summary.get('sections_total', 0)}`",
        f"- Checksums: `{summary.get('checksums_total', 0)}`",
        f"- Secret-value scan passed: `{summary.get('secret_value_scan_passed', False)}`",
        f"- Files planned: `{summary.get('files_planned_total', 0)}`",
        f"- Files written: `{summary.get('files_written_total', 0)}`",
        "",
        "## Included sections",
        "",
    ]
    sections = payload.get("sections", {}) if isinstance(payload.get("sections"), dict) else {}
    for section_id, section in sorted(sections.items()):
        lines.append(f"- `{section_id}`: command `{section.get('command', '')}`, ok `{section.get('ok', False)}`")
    lines.extend([
        "",
        "## Redaction manifest",
        "",
    ])
    redaction = payload.get("redaction_manifest", {}) if isinstance(payload.get("redaction_manifest"), dict) else {}
    for key in sorted(redaction):
        lines.append(f"- `{key}`: `{redaction[key]}`")
    lines.extend([
        "",
        "## Interpretation instructions",
        "",
    ])
    for instruction in interpretation.get("instructions", []) if isinstance(interpretation.get("instructions"), list) else []:
        lines.append(f"- {instruction}")
    lines.extend([
        "",
        "## Limitations",
        "",
    ])
    for limitation in payload.get("limitations", []) if isinstance(payload.get("limitations"), list) else []:
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"
