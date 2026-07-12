from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import Finding, Severity
from devpilot_core.schemas import SchemaValidator

POST_H_033_C_CREATED_BY = "POST-H-033-C"
READINESS_REQUIREMENTS_SCHEMA_ID = "SCHEMA-DEVPL-READINESS-REQUIREMENTS-V1"
READINESS_REQUIREMENTS_CONTRACT = "ReadinessRequirements"
DEFAULT_READINESS_REQUIREMENTS_PATH = Path(".devpilot/readiness/readiness_requirements.json")

FALLBACK_REQUIRED_PRE_CODE_ARTIFACTS = (
    "docs/00_product/product_vision.md",
    "docs/00_product/business_case.md",
    "docs/00_product/mvp_scope.md",
    "docs/01_requirements/requirements_specification.md",
    "docs/02_architecture/architecture_document.md",
    "docs/02_architecture/adrs/ADR-0001-adoptar-mipsoftware-y-miasi.md",
    "docs/03_security/security_threat_model.md",
    "docs/04_quality/test_strategy.md",
    "docs/checklists/checklist_pre_code.md",
)

FALLBACK_REQUIRED_MIASI_ARTIFACTS = (
    "docs/06_miasi/agent_card.md",
    "docs/06_miasi/tool_card.md",
    "docs/06_miasi/policy_card.md",
    "docs/06_miasi/eval_card.md",
    "docs/06_miasi/human_approval_card.md",
    "docs/06_miasi/observability_card.md",
)

FALLBACK_STRICT_REQUIRED_ARTIFACTS = (
    "docs/00_product/product_vision.md",
    "docs/00_product/business_case.md",
    "docs/00_product/mvp_scope.md",
    "docs/01_requirements/requirements_specification.md",
    "docs/01_requirements/user_stories.md",
    "docs/01_requirements/use_cases.md",
    "docs/01_requirements/acceptance_criteria.md",
    "docs/01_requirements/traceability_matrix.md",
    "docs/02_architecture/architecture_document.md",
    "docs/02_architecture/c4_context.md",
    "docs/02_architecture/c4_container.md",
    "docs/03_security/security_threat_model.md",
    "docs/03_security/privacy_assessment.md",
    "docs/04_quality/test_strategy.md",
    "docs/05_operations/observability_plan.md",
    "docs/05_operations/runbook.md",
    *FALLBACK_REQUIRED_MIASI_ARTIFACTS,
    "docs/checklists/checklist_pre_code.md",
    "docs/precode_audit_report.md",
    "docs/precode_baseline_decision.md",
)


@dataclass(frozen=True)
class ReadinessArtifactRequirement:
    artifact: str
    artifact_type: str
    requires_frontmatter: bool
    requires_approval_status: bool
    severity_if_missing: Severity
    fallback_compatibility_group: str
    profiles: tuple[str, ...]
    critical: bool
    cannot_disable_without_adr: bool


@dataclass(frozen=True)
class ReadinessRequirementsRegistry:
    """Versioned readiness requirements loaded from a local registry.

    POST-H-033-C moves configurable readiness artifact lists out of
    ``validators/readiness.py`` while keeping the validation engine,
    frontmatter parser and defensive fallback in Python. Invalid registries do
    not open a bypass: the fallback is loaded for diagnostics and compatibility,
    but a BLOCK finding prevents a false PASS.
    """

    source: str
    catalog_version: str
    rule_source: str
    registry_valid: bool
    fallback_active: bool
    profile_id: str
    required_pre_code_artifacts: tuple[str, ...]
    required_miasi_artifacts: tuple[str, ...]
    strict_required_artifacts: tuple[str, ...]
    optional_artifacts: tuple[str, ...]
    requirements: tuple[ReadinessArtifactRequirement, ...]
    findings: tuple[Finding, ...] = ()

    def metadata(self) -> dict[str, Any]:
        return {
            "rule_source": self.rule_source,
            "catalog_version": self.catalog_version,
            "registry_valid": self.registry_valid,
            "fallback_active": self.fallback_active,
            "profile_id": self.profile_id,
            "required_pre_code_artifacts_total": len(self.required_pre_code_artifacts),
            "required_miasi_artifacts_total": len(self.required_miasi_artifacts),
            "strict_required_artifacts_total": len(self.strict_required_artifacts),
        }


def load_readiness_requirements(
    root: Path,
    *,
    registry_path: Path = DEFAULT_READINESS_REQUIREMENTS_PATH,
    emit_fallback_finding: bool = False,
) -> ReadinessRequirementsRegistry:
    """Load readiness requirements or return a safe built-in fallback."""

    root = Path(root).resolve()
    resolved = root / registry_path
    display_path = str(registry_path).replace("\\", "/")
    if not resolved.exists():
        finding = Finding(
            id="READINESS_REQUIREMENTS_REGISTRY_MISSING_FALLBACK_ACTIVE",
            message="Readiness requirements registry is missing; built-in compatibility fallback is active.",
            severity=Severity.WARNING,
            path=display_path,
            metadata={"fallback_active": True, "created_by": POST_H_033_C_CREATED_BY},
        )
        return _fallback_registry((finding,) if emit_fallback_finding else ())

    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        finding = Finding(
            id="READINESS_REQUIREMENTS_REGISTRY_INVALID_JSON_BLOCKED",
            message=f"Readiness requirements registry JSON is invalid; built-in compatibility fallback is active but PASS is blocked: {exc.msg}",
            severity=Severity.BLOCK,
            path=display_path,
            metadata={"fallback_active": True, "created_by": POST_H_033_C_CREATED_BY},
        )
        return _fallback_registry((finding,) if emit_fallback_finding else ())

    if not isinstance(payload, dict):
        finding = Finding(
            id="READINESS_REQUIREMENTS_REGISTRY_INVALID_PAYLOAD_BLOCKED",
            message="Readiness requirements registry must be a JSON object; built-in compatibility fallback is active but PASS is blocked.",
            severity=Severity.BLOCK,
            path=display_path,
            metadata={"fallback_active": True, "created_by": POST_H_033_C_CREATED_BY},
        )
        return _fallback_registry((finding,) if emit_fallback_finding else ())

    schema_result = SchemaValidator(root).validate_payload(
        schema=READINESS_REQUIREMENTS_CONTRACT,
        payload=payload,
        instance_label=display_path,
    )
    if not schema_result.ok:
        finding = Finding(
            id="READINESS_REQUIREMENTS_REGISTRY_SCHEMA_INVALID_BLOCKED",
            message="Readiness requirements registry does not conform to schema; built-in compatibility fallback is active but PASS is blocked.",
            severity=Severity.BLOCK,
            path=display_path,
            metadata={"fallback_active": True, "created_by": POST_H_033_C_CREATED_BY},
        )
        findings = (finding, *schema_result.findings) if emit_fallback_finding else ()
        return _fallback_registry(findings)

    try:
        return _registry_from_payload(payload, display_path)
    except (KeyError, TypeError, ValueError) as exc:
        finding = Finding(
            id="READINESS_REQUIREMENTS_REGISTRY_LOAD_FAILED_BLOCKED",
            message=f"Readiness requirements registry could not be loaded; built-in compatibility fallback is active but PASS is blocked: {exc}",
            severity=Severity.BLOCK,
            path=display_path,
            metadata={"fallback_active": True, "created_by": POST_H_033_C_CREATED_BY},
        )
        return _fallback_registry((finding,) if emit_fallback_finding else ())


def _registry_from_payload(payload: dict[str, Any], rule_source: str) -> ReadinessRequirementsRegistry:
    requirements = tuple(_requirement_from_payload(item) for item in payload["requirements"])
    _assert_registry_equivalence(payload, requirements)
    return ReadinessRequirementsRegistry(
        source="registry",
        catalog_version=str(payload["catalog_version"]),
        rule_source=rule_source,
        registry_valid=True,
        fallback_active=False,
        profile_id=str(payload["profile_id"]),
        required_pre_code_artifacts=tuple(str(item) for item in payload["required_artifacts"]),
        required_miasi_artifacts=tuple(str(item) for item in payload["required_miasi_artifacts"]),
        strict_required_artifacts=tuple(str(item) for item in payload["strict_required_artifacts"]),
        optional_artifacts=tuple(str(item) for item in payload.get("optional_artifacts", ())),
        requirements=requirements,
    )


def _requirement_from_payload(item: dict[str, Any]) -> ReadinessArtifactRequirement:
    return ReadinessArtifactRequirement(
        artifact=str(item["artifact"]),
        artifact_type=str(item["artifact_type"]),
        requires_frontmatter=bool(item["requires_frontmatter"]),
        requires_approval_status=bool(item["requires_approval_status"]),
        severity_if_missing=_severity(str(item["severity_if_missing"])),
        fallback_compatibility_group=str(item["fallback_compatibility_group"]),
        profiles=tuple(str(profile) for profile in item["profiles"]),
        critical=bool(item["critical"]),
        cannot_disable_without_adr=bool(item["cannot_disable_without_adr"]),
    )


def _assert_registry_equivalence(payload: dict[str, Any], requirements: tuple[ReadinessArtifactRequirement, ...]) -> None:
    requirement_paths = {item.artifact for item in requirements}
    strict_paths = set(str(item) for item in payload["strict_required_artifacts"])
    pre_code_paths = set(str(item) for item in payload["required_artifacts"])
    miasi_paths = set(str(item) for item in payload["required_miasi_artifacts"])
    if not strict_paths.issubset(requirement_paths):
        missing = sorted(strict_paths - requirement_paths)
        raise ValueError(f"Strict artifacts missing from requirements list: {missing}")
    if not pre_code_paths.issubset(requirement_paths):
        missing = sorted(pre_code_paths - requirement_paths)
        raise ValueError(f"Pre-code artifacts missing from requirements list: {missing}")
    if not miasi_paths.issubset(strict_paths):
        missing = sorted(miasi_paths - strict_paths)
        raise ValueError(f"MIASI artifacts must be included in strict requirements: {missing}")
    for item in requirements:
        if item.critical and not item.cannot_disable_without_adr:
            raise ValueError(f"Critical readiness artifact can be disabled without ADR: {item.artifact}")


def _fallback_registry(findings: tuple[Finding, ...] = ()) -> ReadinessRequirementsRegistry:
    requirements = tuple(
        ReadinessArtifactRequirement(
            artifact=artifact,
            artifact_type="miasi" if artifact in FALLBACK_REQUIRED_MIASI_ARTIFACTS else ("checklist" if artifact.endswith("checklist_pre_code.md") else "markdown"),
            requires_frontmatter=artifact.endswith(".md"),
            requires_approval_status=artifact.endswith(".md"),
            severity_if_missing=Severity.BLOCK,
            fallback_compatibility_group="miasi" if artifact in FALLBACK_REQUIRED_MIASI_ARTIFACTS else ("pre-code" if artifact in FALLBACK_REQUIRED_PRE_CODE_ARTIFACTS else "strict"),
            profiles=("strict",) if artifact not in FALLBACK_REQUIRED_PRE_CODE_ARTIFACTS and artifact not in FALLBACK_REQUIRED_MIASI_ARTIFACTS else tuple(
                profile for profile, enabled in (
                    ("compatibility", artifact in FALLBACK_REQUIRED_PRE_CODE_ARTIFACTS),
                    ("strict", artifact in FALLBACK_STRICT_REQUIRED_ARTIFACTS),
                    ("miasi", artifact in FALLBACK_REQUIRED_MIASI_ARTIFACTS),
                ) if enabled
            ),
            critical=True,
            cannot_disable_without_adr=True,
        )
        for artifact in FALLBACK_STRICT_REQUIRED_ARTIFACTS
    )
    return ReadinessRequirementsRegistry(
        source="fallback",
        catalog_version="fallback-compat-1.0.0",
        rule_source="python:fallback:devpilot_core.validators.readiness_requirements",
        registry_valid=False,
        fallback_active=True,
        profile_id="devpilot-precode-readiness-fallback",
        required_pre_code_artifacts=FALLBACK_REQUIRED_PRE_CODE_ARTIFACTS,
        required_miasi_artifacts=FALLBACK_REQUIRED_MIASI_ARTIFACTS,
        strict_required_artifacts=FALLBACK_STRICT_REQUIRED_ARTIFACTS,
        optional_artifacts=(),
        requirements=requirements,
        findings=findings,
    )


def _severity(raw: str) -> Severity:
    try:
        return Severity(raw)
    except ValueError as exc:
        raise ValueError(f"Unsupported readiness severity: {raw}") from exc
