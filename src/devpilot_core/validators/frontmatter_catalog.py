from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import Finding, Severity
from devpilot_core.schemas import SchemaValidator

POST_H_033_B_CREATED_BY = "POST-H-033-B"
FRONTMATTER_CATALOG_SCHEMA_ID = "SCHEMA-DEVPL-FRONTMATTER-METADATA-V1"
FRONTMATTER_CATALOG_CONTRACT = "FrontmatterMetadata"
DEFAULT_FRONTMATTER_CATALOG_PATH = Path(".devpilot/validation/frontmatter_catalog.json")

FALLBACK_REQUIRED_FRONTMATTER_FIELDS = ("title", "doc_id", "status", "version", "owner", "updated")
FALLBACK_ALLOWED_STATUSES = ("draft", "reviewed", "approved", "deprecated", "closed")
FALLBACK_SEMVER_PATTERN = r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9_.-]+)?$"
FALLBACK_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
FALLBACK_DOC_ID_PATTERN = r"^[A-Z0-9][A-Z0-9_.-]*$"


@dataclass(frozen=True)
class FrontmatterPatternRule:
    pattern_id: str
    field: str
    regex: str
    finding_id: str
    message: str
    severity: Severity
    compiled: re.Pattern[str]


@dataclass(frozen=True)
class FrontmatterCatalog:
    """Versioned frontmatter validation rules loaded from a local catalog.

    POST-H-033-B keeps the parser and defensive fallback in code while moving
    configurable fields, statuses, patterns and severities into a schema-backed
    catalog. The object is immutable so validators can safely read rules without
    mutating runtime state.
    """

    source: str
    catalog_version: str
    rule_source: str
    catalog_valid: bool
    fallback_active: bool
    required_fields: tuple[str, ...]
    allowed_statuses: tuple[str, ...]
    pattern_rules: tuple[FrontmatterPatternRule, ...]
    missing_frontmatter_severity: Severity
    parse_warning_severity: Severity
    approved_without_approval_default_severity: Severity
    approved_without_approval_strict_severity: Severity
    findings: tuple[Finding, ...] = ()

    def metadata(self) -> dict[str, Any]:
        return {
            "rule_source": self.rule_source,
            "catalog_version": self.catalog_version,
            "catalog_valid": self.catalog_valid,
            "fallback_active": self.fallback_active,
        }


def load_frontmatter_catalog(
    root: Path,
    *,
    catalog_path: Path = DEFAULT_FRONTMATTER_CATALOG_PATH,
    emit_fallback_finding: bool = False,
) -> FrontmatterCatalog:
    """Load the frontmatter catalog or return a safe built-in fallback.

    Missing or invalid catalogs must not open a bypass. The fallback reproduces
    the historical frontmatter rules and can optionally emit a finding for
    diagnostic/reporting paths. Runtime validation keeps compatibility by not
    turning a missing catalog into an additional warning for every document.
    """

    root = Path(root).resolve()
    resolved = root / catalog_path
    if not resolved.exists():
        finding = Finding(
            id="FRONTMATTER_CATALOG_MISSING_FALLBACK_ACTIVE",
            message="Frontmatter catalog is missing; built-in compatibility fallback is active.",
            severity=Severity.WARNING,
            path=str(catalog_path).replace("\\", "/"),
            metadata={"fallback_active": True, "created_by": POST_H_033_B_CREATED_BY},
        )
        return _fallback_catalog((finding,) if emit_fallback_finding else ())

    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        finding = Finding(
            id="FRONTMATTER_CATALOG_INVALID_JSON_FALLBACK_ACTIVE",
            message=f"Frontmatter catalog JSON is invalid; built-in compatibility fallback is active: {exc.msg}",
            severity=Severity.WARNING,
            path=str(catalog_path).replace("\\", "/"),
            metadata={"fallback_active": True, "created_by": POST_H_033_B_CREATED_BY},
        )
        return _fallback_catalog((finding,) if emit_fallback_finding else ())

    if not isinstance(payload, dict):
        finding = Finding(
            id="FRONTMATTER_CATALOG_INVALID_PAYLOAD_FALLBACK_ACTIVE",
            message="Frontmatter catalog must be a JSON object; built-in compatibility fallback is active.",
            severity=Severity.WARNING,
            path=str(catalog_path).replace("\\", "/"),
            metadata={"fallback_active": True, "created_by": POST_H_033_B_CREATED_BY},
        )
        return _fallback_catalog((finding,) if emit_fallback_finding else ())

    schema_result = SchemaValidator(root).validate_payload(
        schema=FRONTMATTER_CATALOG_CONTRACT,
        payload=payload,
        instance_label=str(catalog_path).replace("\\", "/"),
    )
    if not schema_result.ok:
        finding = Finding(
            id="FRONTMATTER_CATALOG_SCHEMA_INVALID_FALLBACK_ACTIVE",
            message="Frontmatter catalog does not conform to schema; built-in compatibility fallback is active.",
            severity=Severity.WARNING,
            path=str(catalog_path).replace("\\", "/"),
            metadata={"fallback_active": True, "created_by": POST_H_033_B_CREATED_BY},
        )
        findings = (finding, *schema_result.findings) if emit_fallback_finding else ()
        return _fallback_catalog(findings)

    try:
        return _catalog_from_payload(payload, str(catalog_path).replace("\\", "/"))
    except (KeyError, TypeError, ValueError, re.error) as exc:
        finding = Finding(
            id="FRONTMATTER_CATALOG_RULE_LOAD_FAILED_FALLBACK_ACTIVE",
            message=f"Frontmatter catalog rules could not be loaded; built-in compatibility fallback is active: {exc}",
            severity=Severity.WARNING,
            path=str(catalog_path).replace("\\", "/"),
            metadata={"fallback_active": True, "created_by": POST_H_033_B_CREATED_BY},
        )
        return _fallback_catalog((finding,) if emit_fallback_finding else ())


def discover_frontmatter_catalog_root(document_path: Path, root: Path | None = None) -> Path:
    """Find a workspace root that contains the frontmatter catalog.

    Existing validators often pass an artifact root rather than repository root.
    This helper walks upward so `validate_frontmatter_file(..., root=fixtures)`
    still resolves the repository catalog while preserving the historical display
    path behavior controlled by the original `root` argument.
    """

    candidates: list[Path] = []
    if root is not None:
        candidates.append(Path(root))
    if str(document_path) != "<memory>":
        candidates.append(Path(document_path).parent)
    candidates.append(Path.cwd())

    for candidate in candidates:
        candidate = candidate.resolve()
        for parent in (candidate, *candidate.parents):
            if (parent / DEFAULT_FRONTMATTER_CATALOG_PATH).exists():
                return parent
    return Path(root or Path.cwd()).resolve()


def _catalog_from_payload(payload: dict[str, Any], rule_source: str) -> FrontmatterCatalog:
    rules = payload["rules"]
    severities = payload["severity_map"]
    pattern_rules: list[FrontmatterPatternRule] = []
    for item in rules["patterns"]:
        pattern_rules.append(
            FrontmatterPatternRule(
                pattern_id=str(item["pattern_id"]),
                field=str(item["field"]),
                regex=str(item["regex"]),
                finding_id=str(item["finding_id"]),
                message=str(item["message"]),
                severity=_severity(str(item["severity"])),
                compiled=re.compile(str(item["regex"])),
            )
        )
    approved_rule = rules["approved_requires_approval"]
    return FrontmatterCatalog(
        source="catalog",
        catalog_version=str(payload["catalog_version"]),
        rule_source=rule_source,
        catalog_valid=True,
        fallback_active=False,
        required_fields=tuple(str(item["field"]) for item in rules["required_fields"]),
        allowed_statuses=tuple(str(item) for item in rules["allowed_statuses"]),
        pattern_rules=tuple(pattern_rules),
        missing_frontmatter_severity=_severity(str(severities["missing_frontmatter"])),
        parse_warning_severity=_severity(str(severities["parse_warning"])),
        approved_without_approval_default_severity=_severity(str(approved_rule["default_severity"])),
        approved_without_approval_strict_severity=_severity(str(approved_rule["strict_severity"])),
    )


def _fallback_catalog(findings: tuple[Finding, ...] = ()) -> FrontmatterCatalog:
    return FrontmatterCatalog(
        source="fallback",
        catalog_version="fallback-compat-1.0.0",
        rule_source="python:fallback:devpilot_core.validators.frontmatter_catalog",
        catalog_valid=False,
        fallback_active=True,
        required_fields=FALLBACK_REQUIRED_FRONTMATTER_FIELDS,
        allowed_statuses=FALLBACK_ALLOWED_STATUSES,
        pattern_rules=(
            FrontmatterPatternRule(
                pattern_id="semver",
                field="version",
                regex=FALLBACK_SEMVER_PATTERN,
                finding_id="FRONTMATTER_INVALID_VERSION",
                message="Version must follow SemVer-like format, for example 1.0.0.",
                severity=Severity.FAIL,
                compiled=re.compile(FALLBACK_SEMVER_PATTERN),
            ),
            FrontmatterPatternRule(
                pattern_id="updated-date",
                field="updated",
                regex=FALLBACK_DATE_PATTERN,
                finding_id="FRONTMATTER_INVALID_UPDATED_DATE",
                message="Updated date must use YYYY-MM-DD format.",
                severity=Severity.FAIL,
                compiled=re.compile(FALLBACK_DATE_PATTERN),
            ),
            FrontmatterPatternRule(
                pattern_id="doc-id",
                field="doc_id",
                regex=FALLBACK_DOC_ID_PATTERN,
                finding_id="FRONTMATTER_INVALID_DOC_ID",
                message="doc_id should use uppercase letters, digits, dots, hyphens or underscores.",
                severity=Severity.WARNING,
                compiled=re.compile(FALLBACK_DOC_ID_PATTERN),
            ),
        ),
        missing_frontmatter_severity=Severity.FAIL,
        parse_warning_severity=Severity.WARNING,
        approved_without_approval_default_severity=Severity.WARNING,
        approved_without_approval_strict_severity=Severity.FAIL,
        findings=findings,
    )


def _severity(raw: str) -> Severity:
    try:
        return Severity(raw)
    except ValueError as exc:
        raise ValueError(f"Unsupported frontmatter severity: {raw}") from exc
