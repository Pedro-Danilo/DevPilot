from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.docs_governance.backlogs import DocumentationBacklogGovernanceValidator
from devpilot_core.docs_governance.consistency import ClosureStateConsistencyValidator
from devpilot_core.docs_governance.drift import DocumentationSyncValidator
from devpilot_core.docs_governance.registry import DEFAULT_DOCUMENTATION_SOURCE_REGISTRY, load_documentation_source_registry
from devpilot_core.docs_governance.rule_registry import DEFAULT_DOCS_GOVERNANCE_RULE_REGISTRY, load_docs_governance_rule_registry
from devpilot_core.runtime_state.models import utc_now_iso
from devpilot_core.testing.historical_contract_authority import HistoricalContractAuthorityGate
from devpilot_core.testing.full_regression_execution_profile import FullRegressionExecutionProfileRegistry
from devpilot_core.validators.frontmatter import parse_frontmatter_file, validate_frontmatter_document

POST_H_009_B_CREATED_BY = "POST-H-009-B"
POST_H_009_C_CREATED_BY = "POST-H-009-C"
POST_H_009_D_CREATED_BY = "POST-H-009-D"
POST_H_009_E_CREATED_BY = "POST-H-009-E"
POST_H_009_CURRENT_CREATED_BY = POST_H_009_E_CREATED_BY
DOCUMENTATION_GOVERNANCE_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-DOCUMENTATION-GOVERNANCE-REPORT-V1"
DOCUMENTATION_GOVERNANCE_REPORT_ID = "devpilot-documentation-governance-report"
DOCUMENTATION_GOVERNANCE_CONTRACT = "DocumentationGovernanceReport"

DEFAULT_DOCUMENTATION_GOVERNANCE_JSON = Path("outputs/reports/documentation_governance_report.json")
DEFAULT_DOCUMENTATION_GOVERNANCE_MARKDOWN = Path("outputs/reports/documentation_governance_report.md")

STATUS_FRONTMATTER_REQUIRED = {"approved", "draft", "reviewed", "deprecated"}
BLOCKING_SEVERITIES = {Severity.FAIL, Severity.BLOCK, Severity.ERROR}


@dataclass(frozen=True)
class DocumentationGovernanceValidationOptions:
    """Options for POST-H-009-B documentation governance validation."""

    registry_path: str | Path = DEFAULT_DOCUMENTATION_SOURCE_REGISTRY
    write_report: bool = False
    output_json: str | Path = DEFAULT_DOCUMENTATION_GOVERNANCE_JSON
    output_markdown: str | Path = DEFAULT_DOCUMENTATION_GOVERNANCE_MARKDOWN
    strict_frontmatter: bool = False
    rule_registry_path: str | Path = DEFAULT_DOCS_GOVERNANCE_RULE_REGISTRY


class DocumentationGovernanceValidator:
    """Validate documentation source metadata declared in the canonical registry.

    POST-H-009-B is intentionally deterministic and read-only for source files.
    It validates the minimum metadata layer: path existence, registry ownership,
    required test existence, Markdown frontmatter for approved documents, doc_id
    consistency and status consistency when the governed file exposes status.
    POST-H-009-C extends the same command with deterministic Markdown/JSON
    synchronization checks for roadmap, decisions, closure status and next hito.
    POST-H-009-D adds backlog governance and POST-H-009-E binds the validator
    to the hardening/industrial quality-gate process without changing the
    validator into a mutating tool.
    """

    def __init__(self, root: Path, options: DocumentationGovernanceValidationOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or DocumentationGovernanceValidationOptions()

    def run(self) -> CommandResult:
        try:
            registry = load_documentation_source_registry(self.root, self.options.registry_path)
            report = self.build_report(registry)
        except Exception as exc:
            finding = Finding(
                "DOCUMENTATION_GOVERNANCE_ERROR",
                f"Documentation governance validation could not be evaluated: {exc}",
                Severity.ERROR,
            )
            return CommandResult(
                "docs-governance validate",
                False,
                ExitCode.ERROR,
                "Documentation governance validation failed with an unexpected error.",
                data={"summary": {"created_by": POST_H_009_CURRENT_CREATED_BY, "preliminary": True}},
                findings=[finding],
            )

        reports: dict[str, str] = {}
        if self.options.write_report:
            report["summary"]["reports_written"] = True
            report["summary"]["output_json"] = _rel(self.root, self.root / self.options.output_json)
            report["summary"]["output_markdown"] = _rel(self.root, self.root / self.options.output_markdown)
            reports = self._write_reports(report)
        else:
            report["summary"]["reports_written"] = False
            report["summary"]["output_json"] = None
            report["summary"]["output_markdown"] = None

        findings = _findings_from_report(report)
        blocking = [finding for finding in findings if finding.severity in BLOCKING_SEVERITIES]
        ok = not blocking
        return CommandResult(
            "docs-governance validate",
            ok,
            ExitCode.PASS if ok else exit_code_for_findings(blocking),
            "Documentation governance validation passed." if ok else "Documentation governance validation found blocking metadata issues.",
            data={"summary": report["summary"], "governance": report, "reports": reports},
            findings=findings,
        )

    def build_report(self, registry: Any) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        document_checks: list[dict[str, Any]] = []
        frontmatter_checked_total = 0
        required_tests_checked_total = 0
        source_of_truth_checked_total = 0
        machine_readable_checked_total = 0
        historical_current_authority_total = 0
        rule_registry = load_docs_governance_rule_registry(self.root, self.options.rule_registry_path)
        rule_registry_metadata = rule_registry.metadata()
        findings.extend(rule_registry.findings_as_report_items())

        expected_registry_path = _posix(self.options.registry_path)
        if rule_registry.source_registry_path != expected_registry_path:
            findings.append(
                _finding(
                    "DOCUMENTATION_RULE_REGISTRY_SOURCE_REGISTRY_MISMATCH",
                    "Docs governance rule registry references a different source registry path than the active validator options.",
                    rule_registry.contradiction_severity,
                    rule_registry.source_catalog,
                    {"expected_source_registry_path": expected_registry_path, "actual_source_registry_path": rule_registry.source_registry_path, **rule_registry_metadata},
                )
            )

        for document in registry.documents:
            path = self.root / document.path
            check: dict[str, Any] = {
                "doc_id": document.doc_id,
                "path": document.path,
                "classification": document.classification,
                "domain": document.domain,
                "owner": document.owner,
                "status_required": document.status_required,
                "criticality": document.criticality,
                "exists": path.exists(),
                "frontmatter_checked": False,
                "status_checked": False,
                "required_tests_checked": False,
                "ok": True,
                "rule_source": rule_registry.source_catalog,
                "catalog_version": rule_registry.catalog_version,
                "rule_registry_valid": rule_registry.registry_valid,
                "rule_registry_fallback_active": rule_registry.fallback_active,
            }
            if document.is_source_of_truth:
                source_of_truth_checked_total += 1
            if document.is_machine_readable_source:
                machine_readable_checked_total += 1

            if document.classification not in rule_registry.allowed_classifications:
                findings.append(_finding("DOCUMENTATION_CLASSIFICATION_NOT_GOVERNED", "Registry document classification is not governed by the docs rule registry.", rule_registry.contradiction_severity, document.path, {"doc_id": document.doc_id, "classification": document.classification, **rule_registry_metadata}))
                check["ok"] = False
            if document.lifecycle not in rule_registry.allowed_lifecycles:
                findings.append(_finding("DOCUMENTATION_LIFECYCLE_NOT_GOVERNED", "Registry document lifecycle is not governed by the docs rule registry.", rule_registry.contradiction_severity, document.path, {"doc_id": document.doc_id, "lifecycle": document.lifecycle, **rule_registry_metadata}))
                check["ok"] = False

            if not document.owner.strip():
                findings.append(_finding("DOCUMENTATION_OWNER_MISSING", "Registry document owner is missing.", "block", document.path, {"doc_id": document.doc_id, **rule_registry_metadata}))
                check["ok"] = False
            if not document.status_required.strip():
                findings.append(_finding("DOCUMENTATION_STATUS_REQUIRED_MISSING", "Registry document status_required is missing.", "block", document.path, {"doc_id": document.doc_id, **rule_registry_metadata}))
                check["ok"] = False

            if not path.exists():
                findings.append(_finding("DOCUMENTATION_SOURCE_MISSING", "Governed documentation source path does not exist.", "block", document.path, {"doc_id": document.doc_id, **rule_registry_metadata}))
                check["ok"] = False
                document_checks.append(check)
                continue

            if document.classification == "historical" and document.lifecycle == "active":
                historical_current_authority_total += 1
                findings.append(_finding("DOCUMENTATION_HISTORICAL_ACTIVE_REVIEW", "Historical document is registered as active authority; review classification/lifecycle before treating it as current source.", rule_registry.historical_active_authority_severity, document.path, {"doc_id": document.doc_id, **rule_registry_metadata}))

            required_tests = list(document.required_tests)
            if rule_registry.requires_tests(classification=document.classification, criticality=document.criticality):
                check["required_tests_checked"] = True
                required_tests_checked_total += len(required_tests)
                if not required_tests:
                    findings.append(_finding("DOCUMENTATION_REQUIRED_TESTS_MISSING", "Critical/source-of-truth document has no required_tests in registry.", "block", document.path, {"doc_id": document.doc_id, **rule_registry_metadata}))
                    check["ok"] = False
                for test_path in required_tests:
                    if not (self.root / test_path).exists():
                        findings.append(_finding("DOCUMENTATION_REQUIRED_TEST_MISSING", "Required test declared by registry does not exist.", "block", test_path, {"doc_id": document.doc_id, "source_path": document.path, **rule_registry_metadata}))
                        check["ok"] = False

            if path.suffix.lower() == ".md" and document.status_required in rule_registry.status_frontmatter_required:
                check["frontmatter_checked"] = True
                check["status_checked"] = True
                frontmatter_checked_total += 1
                frontmatter_result = self._validate_markdown_frontmatter(path, document)
                check.update(frontmatter_result["check"])
                findings.extend(frontmatter_result["findings"])
                if not frontmatter_result["ok"]:
                    check["ok"] = False
            elif path.suffix.lower() in {".json", ".yaml", ".yml"}:
                status_result = self._validate_structured_status(path, document)
                check.update(status_result["check"])
                findings.extend(status_result["findings"])
                if not status_result["ok"]:
                    check["ok"] = False
            else:
                if path.suffix.lower() == ".md":
                    findings.append(_finding("DOCUMENTATION_FRONTMATTER_NOT_REQUIRED", "Markdown document is registered with a non-frontmatter status requirement; frontmatter is not mandatory in POST-H-009-B.", "info", document.path, {"doc_id": document.doc_id, "status_required": document.status_required}))

            document_checks.append(check)

        sync_result = DocumentationSyncValidator(self.root, registry).run()
        sync_checks = list(sync_result["sync_checks"])
        sync_summary = dict(sync_result["summary"])
        findings.extend(sync_result["findings"])

        backlog_result = DocumentationBacklogGovernanceValidator(self.root, registry).run()
        backlog_checks = list(backlog_result["backlog_checks"])
        backlog_summary = dict(backlog_result["summary"])
        findings.extend(backlog_result["findings"])

        closure_consistency = ClosureStateConsistencyValidator(self.root).run()
        closure_summary = dict(closure_consistency.data.get("summary", {}))
        closure_report = dict(closure_consistency.data.get("report", {})) if isinstance(closure_consistency.data.get("report"), dict) else {}
        for finding in closure_consistency.findings:
            findings.append(_finding(finding.id, finding.message, finding.severity.value, finding.path, dict(finding.metadata)))

        authority_result = HistoricalContractAuthorityGate(self.root).run()
        authority_summary = dict((authority_result.data or {}).get("summary") or {})
        for finding in authority_result.findings:
            findings.append(_finding(finding.id, finding.message, finding.severity.value, finding.path, dict(finding.metadata or {})))

        frx_profile_result = FullRegressionExecutionProfileRegistry(self.root).validate()
        frx_profile_summary = dict((frx_profile_result.data or {}).get("summary") or {})
        for finding in frx_profile_result.findings:
            findings.append(_finding(finding.id, finding.message, finding.severity.value, finding.path, dict(finding.metadata or {})))

        blocking_total = sum(1 for item in findings if item["severity"] in {"fail", "block", "error"})
        warnings_total = sum(1 for item in findings if item["severity"] == "warning")
        info_total = sum(1 for item in findings if item["severity"] == "info")
        ok = blocking_total == 0
        summary = {
            "created_by": POST_H_009_CURRENT_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "rule_source": rule_registry.source_catalog,
            "catalog_version": rule_registry.catalog_version,
            "rule_registry_valid": rule_registry.registry_valid,
            "rule_registry_fallback_active": rule_registry.fallback_active,
            "rule_registry_blocking_findings_total": len(rule_registry.blocking_findings),
            "rule_registry_nonblocking_findings_total": len(rule_registry.nonblocking_findings),
            "source_registry_and_rule_registry_validated_together": True,
            "documents_total": len(registry.documents),
            "documents_checked_total": len(document_checks),
            "frontmatter_checked_total": frontmatter_checked_total,
            "status_checked_total": sum(1 for item in document_checks if item.get("status_checked")),
            "source_of_truth_checked_total": source_of_truth_checked_total,
            "machine_readable_checked_total": machine_readable_checked_total,
            "required_tests_checked_total": required_tests_checked_total,
            "markdown_json_pairs_checked_total": sync_summary.get("sync_checks_total", 0),
            "drift_findings_total": sync_summary.get("sync_findings_total", 0),
            "historical_current_authority_total": historical_current_authority_total,
            "findings_total": len(findings),
            "info_total": info_total,
            "warnings_total": warnings_total,
            "blocking_findings_total": blocking_total,
            "docs_governance_passed": ok,
            "frontmatter_status_ownership_passed": ok and sync_summary.get("sync_passed", False),
            "markdown_json_sync_passed": sync_summary.get("sync_passed", False),
            "roadmap_markdown_json_sync_passed": sync_summary.get("roadmap_markdown_json_sync_passed", False),
            "version_match_checked_total": sync_summary.get("version_match_checked_total", 0),
            "milestones_match_checked_total": sync_summary.get("milestones_match_checked_total", 0),
            "decisions_match_checked_total": sync_summary.get("decisions_match_checked_total", 0),
            "closure_status_match_checked_total": sync_summary.get("closure_status_match_checked_total", 0),
            "next_hito_match_checked_total": sync_summary.get("next_hito_match_checked_total", 0),
            "backlogs_expected_total": backlog_summary.get("backlogs_expected_total", 0),
            "backlogs_checked_total": backlog_summary.get("backlogs_checked_total", 0),
            "backlogs_registered_total": backlog_summary.get("backlogs_registered_total", 0),
            "backlogs_existing_total": backlog_summary.get("backlogs_existing_total", 0),
            "backlogs_planned_missing_total": backlog_summary.get("backlogs_planned_missing_total", 0),
            "backlog_naming_checked_total": backlog_summary.get("backlog_naming_checked_total", 0),
            "backlog_frontmatter_checked_total": backlog_summary.get("backlog_frontmatter_checked_total", 0),
            "backlog_milestone_match_checked_total": backlog_summary.get("backlog_milestone_match_checked_total", 0),
            "backlog_governance_passed": backlog_summary.get("backlog_governance_passed", False),
            "backlog_governance_findings_total": backlog_summary.get("backlog_governance_findings_total", 0),
            "closure_state_consistency_configured": closure_summary.get("configured", False),
            "closure_state_consistency_passed": closure_summary.get("closure_state_consistency_passed", True),
            "closure_state_consistency_checks_total": closure_summary.get("checks_total", 0),
            "documentation_drift_p0_p1_open_total": closure_summary.get("drift_p0_p1_open_total", 0),
            "historical_contract_authority_passed": authority_result.ok,
            "historical_contract_authority_contracts_total": authority_summary.get("authority_contracts_total", 0),
            "historical_current_leakage_total": authority_summary.get("historical_current_leakage_total", 0),
            "frx_registry_schema_errors_total": authority_summary.get("registry_schema_errors_total", 0),
            "full_regression_execution_profile_passed": frx_profile_result.ok,
            "full_regression_current_profile_id": frx_profile_summary.get("current_profile_id"),
            "full_regression_current_profile_sha256": frx_profile_summary.get("current_profile_sha256"),
            "full_regression_profile_consumer_locked": frx_profile_summary.get("consumer_contract_locked", False),
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "llm_judge_used": False,
        }
        return {
            "schema_version": "1.0",
            "schema_id": DOCUMENTATION_GOVERNANCE_REPORT_SCHEMA_ID,
            "report_id": DOCUMENTATION_GOVERNANCE_REPORT_ID,
            "created_by": POST_H_009_CURRENT_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": utc_now_iso(),
            "registry_path": _posix(self.options.registry_path),
            "rule_registry_path": _posix(self.options.rule_registry_path),
            "rule_registry": rule_registry_metadata,
            "summary": summary,
            "document_checks": document_checks,
            "sync_checks": sync_checks,
            "backlog_checks": backlog_checks,
            "closure_state_consistency": closure_report,
            "historical_contract_authority": (authority_result.data or {}),
            "full_regression_execution_profile": (frx_profile_result.data or {}),
            "findings": findings,
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "llm_judge_used": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
            },
            "notes": [
                "POST-H-009-B validates minimum documentation metadata declared by the canonical source registry.",
                "POST-H-009-C adds deterministic Markdown/JSON sync checks for roadmap, decisions, closure status and next hito.",
                "POST-H-009-D adds deterministic governance for executable backlogs derived from the roadmap.",
                "This validator is deterministic and read-only; it does not use LLM judge, network or external APIs.",
                "POST-H-009-E integrates this validator as the docs-governance quality-gate subgate.",
                "POST-H-033-F adds a schema-backed docs governance rule registry for auditable severities, lifecycle and required-tests policies while preserving the source registry as canonical document inventory.",
                "FRX-v2.2-A adds cross-authority closure consistency, derived metadata projection and incremental documentation impact planning before expensive testing.",
                "FRX-v2.4-A adds deterministic historical/current authority scope, lifecycle disambiguation and complete FRX registry schema checks without executing pytest.",
            ],
        }

    def _validate_markdown_frontmatter(self, path: Path, document: Any) -> dict[str, Any]:
        parsed = parse_frontmatter_file(path)
        result = validate_frontmatter_document(parsed, root=self.root, strict=self.options.strict_frontmatter)
        path_str = _rel(self.root, path)
        findings: list[dict[str, Any]] = []
        for finding in result.findings:
            severity = "warning" if finding.severity == Severity.FAIL and finding.id == "FRONTMATTER_APPROVED_WITHOUT_APPROVAL" else finding.severity.value
            findings.append(
                _finding(
                    f"DOCUMENTATION_{finding.id}",
                    finding.message,
                    severity,
                    finding.path or path_str,
                    {"doc_id": document.doc_id, **finding.metadata},
                )
            )
        check = {
            "frontmatter_present": parsed.has_frontmatter,
            "frontmatter_status": parsed.frontmatter.get("status") if parsed.has_frontmatter else None,
            "frontmatter_owner": parsed.frontmatter.get("owner") if parsed.has_frontmatter else None,
            "frontmatter_doc_id": parsed.frontmatter.get("doc_id") if parsed.has_frontmatter else None,
        }
        ok = True
        if not parsed.has_frontmatter:
            findings.append(_finding("DOCUMENTATION_FRONTMATTER_REQUIRED", "Approved Markdown source requires frontmatter.", "block", path_str, {"doc_id": document.doc_id}))
            ok = False
        else:
            frontmatter_doc_id = str(parsed.frontmatter.get("doc_id", "")).strip()
            frontmatter_status = str(parsed.frontmatter.get("status", "")).strip()
            frontmatter_owner = str(parsed.frontmatter.get("owner", "")).strip()
            if frontmatter_doc_id != document.doc_id:
                findings.append(_finding("DOCUMENTATION_DOC_ID_MISMATCH", "Markdown frontmatter doc_id does not match registry doc_id.", "block", path_str, {"registry_doc_id": document.doc_id, "frontmatter_doc_id": frontmatter_doc_id}))
                ok = False
            if frontmatter_status != document.status_required:
                findings.append(_finding("DOCUMENTATION_STATUS_MISMATCH", "Markdown frontmatter status does not match registry status_required.", "block", path_str, {"doc_id": document.doc_id, "status_required": document.status_required, "actual_status": frontmatter_status}))
                ok = False
            if not frontmatter_owner:
                findings.append(_finding("DOCUMENTATION_FRONTMATTER_OWNER_MISSING", "Markdown frontmatter owner is missing.", "block", path_str, {"doc_id": document.doc_id}))
                ok = False
        return {"ok": ok and not any(item["severity"] in {"fail", "block", "error"} for item in findings), "check": check, "findings": findings}

    def _validate_structured_status(self, path: Path, document: Any) -> dict[str, Any]:
        path_str = _rel(self.root, path)
        check = {"status_checked": False, "structured_status": None}
        findings: list[dict[str, Any]] = []
        try:
            if path.suffix.lower() != ".json":
                return {"ok": True, "check": check, "findings": findings}
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(_finding("DOCUMENTATION_STRUCTURED_SOURCE_PARSE_ERROR", f"Structured source could not be parsed: {exc}", "block", path_str, {"doc_id": document.doc_id}))
            return {"ok": False, "check": check, "findings": findings}
        actual_status = None
        if isinstance(payload, dict):
            for key in ("status", "implementation_status", "closure_status"):
                if key in payload:
                    actual_status = str(payload.get(key))
                    break
        if actual_status is None:
            findings.append(_finding("DOCUMENTATION_STRUCTURED_STATUS_NOT_DECLARED", "Structured source has no top-level status field; registry status_required is treated as external metadata for this source.", "info", path_str, {"doc_id": document.doc_id, "status_required": document.status_required}))
            return {"ok": True, "check": check, "findings": findings}
        check.update({"status_checked": True, "structured_status": actual_status})
        if document.status_required in {"current", "approved"}:
            # 'current' is a registry lifecycle requirement, not a literal JSON status.
            return {"ok": True, "check": check, "findings": findings}
        if actual_status != document.status_required:
            findings.append(_finding("DOCUMENTATION_STRUCTURED_STATUS_MISMATCH", "Structured source status does not match registry status_required.", "block", path_str, {"doc_id": document.doc_id, "status_required": document.status_required, "actual_status": actual_status}))
            return {"ok": False, "check": check, "findings": findings}
        return {"ok": True, "check": check, "findings": findings}

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(render_documentation_governance_markdown(report), encoding="utf-8")
        return {"json": _rel(self.root, json_path), "markdown": _rel(self.root, markdown_path)}


def render_documentation_governance_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Documentation Governance Report",
        "",
        f"Generated: `{report.get('generated_at_utc')}`",
        f"Created by: `{report.get('created_by')}`",
        f"Status: `{report.get('status')}`",
        "",
        "## Summary",
        "",
        f"- Documents checked: `{summary.get('documents_checked_total')}` / `{summary.get('documents_total')}`",
        f"- Rule source: `{summary.get('rule_source')}`",
        f"- Rule catalog version: `{summary.get('catalog_version')}`",
        f"- Rule registry valid: `{summary.get('rule_registry_valid')}`",
        f"- Frontmatter checked: `{summary.get('frontmatter_checked_total')}`",
        f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
        f"- Warnings: `{summary.get('warnings_total')}`",
        f"- Markdown/JSON sync checks: `{summary.get('markdown_json_pairs_checked_total')}`",
        f"- Markdown/JSON sync passed: `{summary.get('markdown_json_sync_passed')}`",
        f"- Roadmap Markdown/JSON sync passed: `{summary.get('roadmap_markdown_json_sync_passed')}`",
        f"- Backlogs checked: `{summary.get('backlogs_checked_total')}` / `{summary.get('backlogs_expected_total')}`",
        f"- Backlog governance passed: `{summary.get('backlog_governance_passed')}`",
        f"- Passed: `{summary.get('docs_governance_passed')}`",
        "",
        "## Safety",
        "",
        "- Local-first: `true`",
        "- Read-only: `true`",
        "- Network used: `false`",
        "- External APIs used: `false`",
        "- LLM judge used: `false`",
        "",
        "## Findings",
        "",
    ]
    findings = report.get("findings", [])
    if not findings:
        lines.append("No findings emitted.")
    else:
        for finding in findings:
            path = f" — `{finding.get('path')}`" if finding.get("path") else ""
            lines.append(f"- `{finding.get('severity')}` `{finding.get('id')}`{path}: {finding.get('message')}")
    lines.extend(["", "## Sync checks", ""])
    sync_checks = report.get("sync_checks", [])
    if not sync_checks:
        lines.append("No sync checks executed.")
    else:
        for check in sync_checks:
            lines.append(
                f"- `{check.get('rule')}` `{check.get('source_path')}` ↔ `{check.get('counterpart_path')}`: ok=`{check.get('ok')}`"
            )
    lines.extend(["", "## Backlog checks", ""])
    backlog_checks = report.get("backlog_checks", [])
    if not backlog_checks:
        lines.append("No backlog checks executed.")
    else:
        for check in backlog_checks:
            lines.append(
                f"- `{check.get('milestone')}` `{check.get('path')}`: registered=`{check.get('registered')}`, exists=`{check.get('exists')}`, ok=`{check.get('ok')}`"
            )
    lines.extend([
        "",
        "## Notes",
        "",
    ])
    for note in report.get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def _findings_from_report(report: dict[str, Any]) -> list[Finding]:
    return [
        Finding(
            id=str(item.get("id", "DOCUMENTATION_GOVERNANCE_FINDING")),
            message=str(item.get("message", "Documentation governance finding.")),
            severity=Severity(str(item.get("severity", "info"))) if str(item.get("severity", "info")) in {severity.value for severity in Severity} else Severity.INFO,
            path=item.get("path"),
            metadata=dict(item.get("metadata", {})),
        )
        for item in report.get("findings", [])
        if isinstance(item, dict)
    ]


def _finding(id: str, message: str, severity: str, path: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    data: dict[str, Any] = {"id": id, "message": message, "severity": severity}
    if path:
        data["path"] = path
    if metadata:
        data["metadata"] = metadata
    return data


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _posix(path: str | Path) -> str:
    return str(path).replace("\\", "/")
