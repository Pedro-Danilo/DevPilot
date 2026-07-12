from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import Finding, Severity
from devpilot_core.schemas.validator import SchemaValidator

POST_H_033_F_CREATED_BY = "POST-H-033-F"
DOCS_GOVERNANCE_RULE_REGISTRY_SCHEMA_ID = "SCHEMA-DEVPL-DOCS-GOVERNANCE-RULE-REGISTRY-V1"
DOCS_GOVERNANCE_RULE_REGISTRY_CONTRACT = "DocsGovernanceRuleRegistry"
DEFAULT_DOCS_GOVERNANCE_RULE_REGISTRY = Path(".devpilot/docs_governance/rule_registry.json")
DOCS_GOVERNANCE_RULE_REGISTRY_SCHEMA_PATH = Path("docs/schemas/docs_governance_rule_registry.schema.json")

_FALLBACK_STATUS_FRONTMATTER_REQUIRED = {"approved", "draft", "reviewed", "deprecated"}
_FALLBACK_BLOCKING_SEVERITIES = {"fail", "block", "error"}
_FALLBACK_ALLOWED_CLASSIFICATIONS = {"source-of-truth", "machine-readable-source", "derived", "generated-runtime", "historical", "deprecated"}
_FALLBACK_ALLOWED_LIFECYCLES = {"active", "closed", "historical", "planned", "deprecated"}
_FALLBACK_CRITICALITIES_REQUIRING_TESTS = {"P0", "P1"}
_FALLBACK_CLASSIFICATIONS_REQUIRING_TESTS = {"source-of-truth"}
_FALLBACK_RULE_SOURCE = "python:fallback:docs_governance.rule_registry"


@dataclass(frozen=True)
class DocsGovernanceRuleRegistry:
    source_catalog: str
    catalog_version: str
    registry_valid: bool
    fallback_active: bool
    source_registry_path: str = ".devpilot/docs_governance/source_registry.json"
    status_frontmatter_required: frozenset[str] = field(default_factory=lambda: frozenset(_FALLBACK_STATUS_FRONTMATTER_REQUIRED))
    blocking_severities: frozenset[str] = field(default_factory=lambda: frozenset(_FALLBACK_BLOCKING_SEVERITIES))
    allowed_classifications: frozenset[str] = field(default_factory=lambda: frozenset(_FALLBACK_ALLOWED_CLASSIFICATIONS))
    allowed_lifecycles: frozenset[str] = field(default_factory=lambda: frozenset(_FALLBACK_ALLOWED_LIFECYCLES))
    criticalities_requiring_tests: frozenset[str] = field(default_factory=lambda: frozenset(_FALLBACK_CRITICALITIES_REQUIRING_TESTS))
    classifications_requiring_tests: frozenset[str] = field(default_factory=lambda: frozenset(_FALLBACK_CLASSIFICATIONS_REQUIRING_TESTS))
    historical_active_authority_severity: str = "warning"
    contradiction_severity: str = "block"
    blocking_findings: tuple[Finding, ...] = field(default_factory=tuple)
    nonblocking_findings: tuple[Finding, ...] = field(default_factory=tuple)
    rule_definitions: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    @property
    def has_blocking_registry_findings(self) -> bool:
        return bool(self.blocking_findings)

    def requires_tests(self, *, classification: str, criticality: str) -> bool:
        return classification in self.classifications_requiring_tests or criticality in self.criticalities_requiring_tests

    def metadata(self) -> dict[str, Any]:
        return {
            "rule_source": self.source_catalog,
            "catalog_version": self.catalog_version,
            "registry_valid": self.registry_valid,
            "fallback_active": self.fallback_active,
            "source_registry_path": self.source_registry_path,
            "blocking_findings_total": len(self.blocking_findings),
            "nonblocking_findings_total": len(self.nonblocking_findings),
            "status_frontmatter_required_total": len(self.status_frontmatter_required),
            "rule_definitions_total": len(self.rule_definitions),
        }

    def findings_as_report_items(self) -> list[dict[str, Any]]:
        return [_finding_to_report(finding) for finding in (*self.blocking_findings, *self.nonblocking_findings)]


def load_docs_governance_rule_registry(root: Path | None = None, registry_path: str | Path = DEFAULT_DOCS_GOVERNANCE_RULE_REGISTRY) -> DocsGovernanceRuleRegistry:
    workspace = Path(root or Path.cwd()).resolve()
    relative_registry_path = Path(registry_path)
    registry_file = workspace / relative_registry_path
    source = str(relative_registry_path).replace("\\", "/")

    if not registry_file.exists():
        finding = Finding(
            id="DOCS_GOVERNANCE_RULE_REGISTRY_MISSING_FALLBACK_ACTIVE",
            message="Docs governance rule registry is missing; deterministic Python fallback rules remain active.",
            severity=Severity.WARNING,
            path=source,
            metadata={"created_by": POST_H_033_F_CREATED_BY, "fallback_active": True},
        )
        return _fallback_registry(nonblocking_findings=[finding], fallback_active=True)

    try:
        payload = json.loads(registry_file.read_text(encoding="utf-8"))
    except Exception as exc:
        return _fallback_registry_with_block(source, "DOCS_GOVERNANCE_RULE_REGISTRY_INVALID_JSON_BLOCKED", f"Docs governance rule registry is invalid JSON: {exc}")

    schema_result = SchemaValidator(workspace).validate(schema=DOCS_GOVERNANCE_RULE_REGISTRY_SCHEMA_PATH, instance=relative_registry_path)
    if not schema_result.ok:
        return _fallback_registry_with_block(
            source,
            "DOCS_GOVERNANCE_RULE_REGISTRY_SCHEMA_INVALID_BLOCKED",
            "Docs governance rule registry failed schema validation; deterministic fallback rules remain active and validation fails closed.",
            metadata={"schema_findings": [finding.to_dict() for finding in schema_result.findings]},
        )

    semantic_findings = _semantic_findings(payload, source)
    if semantic_findings:
        return _fallback_registry(blocking_findings=semantic_findings, fallback_active=True, registry_valid=False)

    rules = payload.get("rules", {})
    classification_policy = rules.get("classification_policy", {})
    required_tests_policy = rules.get("required_tests_policy", {})
    lifecycle_policy = rules.get("lifecycle_policy", {})
    sync_policy = rules.get("sync_policy", {})

    return DocsGovernanceRuleRegistry(
        source_catalog=source,
        catalog_version=str(payload.get("catalog_version", "1.0.0")),
        registry_valid=True,
        fallback_active=False,
        source_registry_path=str(payload.get("source_registry_path", ".devpilot/docs_governance/source_registry.json")),
        status_frontmatter_required=frozenset(str(item) for item in rules.get("status_frontmatter_required", _FALLBACK_STATUS_FRONTMATTER_REQUIRED)),
        blocking_severities=frozenset(str(item) for item in rules.get("blocking_severities", _FALLBACK_BLOCKING_SEVERITIES)),
        allowed_classifications=frozenset(str(item) for item in classification_policy.get("allowed_classifications", _FALLBACK_ALLOWED_CLASSIFICATIONS)),
        allowed_lifecycles=frozenset(str(item) for item in lifecycle_policy.get("allowed_lifecycles", _FALLBACK_ALLOWED_LIFECYCLES)),
        criticalities_requiring_tests=frozenset(str(item) for item in required_tests_policy.get("criticalities_requiring_tests", _FALLBACK_CRITICALITIES_REQUIRING_TESTS)),
        classifications_requiring_tests=frozenset(str(item) for item in required_tests_policy.get("classifications_requiring_tests", _FALLBACK_CLASSIFICATIONS_REQUIRING_TESTS)),
        historical_active_authority_severity=str(lifecycle_policy.get("historical_active_authority_severity", "warning")),
        contradiction_severity=str(sync_policy.get("contradiction_severity", "block")),
        rule_definitions=tuple(item for item in rules.get("rule_definitions", []) if isinstance(item, dict)),
    )


def _semantic_findings(payload: dict[str, Any], source: str) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    if payload.get("critical_rules_disable_allowed") is not False:
        findings.append(_catalog_finding(source, "DOCS_GOVERNANCE_RULE_REGISTRY_CRITICAL_DISABLE_BLOCKED", "Rule registry attempted to allow critical rule disabling.", Severity.BLOCK))
    rules = payload.get("rules", {})
    if "source-of-truth" not in set(rules.get("classification_policy", {}).get("allowed_classifications", [])):
        findings.append(_catalog_finding(source, "DOCS_GOVERNANCE_RULE_REGISTRY_SOURCE_OF_TRUTH_NOT_GOVERNED", "Rule registry does not govern source-of-truth documents.", Severity.BLOCK))
    if "P0" not in set(rules.get("required_tests_policy", {}).get("criticalities_requiring_tests", [])):
        findings.append(_catalog_finding(source, "DOCS_GOVERNANCE_RULE_REGISTRY_P0_TESTS_NOT_REQUIRED", "Rule registry does not require tests for P0 documents.", Severity.BLOCK))
    if "approved" not in set(rules.get("status_frontmatter_required", [])):
        findings.append(_catalog_finding(source, "DOCS_GOVERNANCE_RULE_REGISTRY_APPROVED_FRONTMATTER_NOT_REQUIRED", "Rule registry does not require frontmatter for approved Markdown documents.", Severity.BLOCK))
    safety = payload.get("safety", {})
    for key in ("network_used", "external_api_used", "llm_judge_used", "remote_execution_enabled", "connector_write_enabled", "plugin_execution_enabled", "source_mutations_performed"):
        if safety.get(key) is not False:
            findings.append(_catalog_finding(source, "DOCS_GOVERNANCE_RULE_REGISTRY_UNSAFE_FLAG_BLOCKED", f"Rule registry unsafe flag must remain false: {key}.", Severity.BLOCK, {"flag": key}))
    return tuple(findings)


def _fallback_registry(*, blocking_findings: list[Finding] | tuple[Finding, ...] = (), nonblocking_findings: list[Finding] | tuple[Finding, ...] = (), fallback_active: bool = True, registry_valid: bool = False) -> DocsGovernanceRuleRegistry:
    return DocsGovernanceRuleRegistry(
        source_catalog=_FALLBACK_RULE_SOURCE,
        catalog_version="fallback-1.0.0",
        registry_valid=registry_valid,
        fallback_active=fallback_active,
        blocking_findings=tuple(blocking_findings),
        nonblocking_findings=tuple(nonblocking_findings),
    )


def _fallback_registry_with_block(source: str, finding_id: str, message: str, metadata: dict[str, Any] | None = None) -> DocsGovernanceRuleRegistry:
    finding = _catalog_finding(source, finding_id, message, Severity.BLOCK, metadata)
    return _fallback_registry(blocking_findings=[finding], fallback_active=True, registry_valid=False)


def _catalog_finding(source: str, finding_id: str, message: str, severity: Severity, metadata: dict[str, Any] | None = None) -> Finding:
    return Finding(
        id=finding_id,
        message=message,
        severity=severity,
        path=source,
        metadata={"created_by": POST_H_033_F_CREATED_BY, "rule_source": source, "catalog_version": "1.0.0", **(metadata or {})},
    )


def _finding_to_report(finding: Finding) -> dict[str, Any]:
    payload = finding.to_dict()
    return {
        "id": str(payload.get("id", "DOCS_GOVERNANCE_RULE_REGISTRY_FINDING")),
        "message": str(payload.get("message", "Docs governance rule registry finding.")),
        "severity": str(payload.get("severity", "info")),
        **({"path": payload["path"]} if payload.get("path") else {}),
        **({"metadata": payload["metadata"]} if payload.get("metadata") else {}),
    }

