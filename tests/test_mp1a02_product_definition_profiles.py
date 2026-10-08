from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from devpilot_core.generation import (
    ArtifactAuthorityRecord,
    ArtifactDependencyResolutionError,
    ArtifactDependencyResolver,
    load_product_definition_dependency_profiles,
    select_product_definition_dependency_profile,
)
from devpilot_core.schemas import SchemaValidator
from devpilot_core.validation import ArtifactProfileRegistry
from devpilot_core.validators.artifact_profiles import ARTIFACT_PROFILES

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 8, tzinfo=timezone.utc)


def record(kind: str, ident: str, *, lifecycle: str = "FROZEN", rank: int = 100) -> ArtifactAuthorityRecord:
    return ArtifactAuthorityRecord(
        artifact_type=kind,
        artifact_id=ident,
        content=f"authority {ident}",
        authority_rank=rank,
        namespace="project",
        lifecycle=lifecycle,
        updated_at_utc="2026-10-08T00:00:00Z",
        citation_ref=f"{ident}#source",
        source_path=f"docs/{ident}.md",
    )


def test_mp1a02_professional_profiles_extend_existing_registry_and_fallback_without_legacy_selection_drift() -> None:
    registry = ArtifactProfileRegistry(ROOT)
    result = registry.status()
    assert result.ok is True
    json_profiles, _, _ = registry.load_profiles(allow_fallback=False)
    fallback = {p.id: p for p in ARTIFACT_PROFILES}
    selected = {p.id: p for p in json_profiles if p.id in {"product-vision", "mvp-scope", "requirements-specification"}}
    assert set(selected) == {"product-vision", "mvp-scope", "requirements-specification"}
    for profile_id, profile in selected.items():
        py = fallback[profile_id]
        assert (profile.filename, profile.path_contains, profile.required_headings, profile.recommended_headings) == (
            py.filename,
            py.path_contains,
            py.required_headings,
            py.recommended_headings,
        )
        assert profile.profile_version == "1.1.0"
        assert profile.payload_schema_ref and (ROOT / profile.payload_schema_ref).exists()
        assert profile.upstream_trace_required is True
        assert profile.semantic_rules and profile.completeness_rules
        assert profile.prohibited_unsupported_claims and profile.human_review_checklist and profile.downstream_semantics
        assert profile.foundation_contract() == py.foundation_contract()


def test_mp1a02_payload_schemas_accept_grounded_fixtures_and_reject_unsupported_claims() -> None:
    fixtures = json.loads((ROOT / "tests/fixtures/mp1a02_product_definition_profiles.json").read_text(encoding="utf-8"))
    refs = {
        "product-vision": "ProductVisionPayload",
        "mvp-scope": "MvpScopePayload",
        "requirements-specification": "RequirementsPayload",
    }
    for key, schema in refs.items():
        assert SchemaValidator(ROOT).validate_payload(
            schema=schema,
            payload=fixtures["valid_payloads"][key],
            instance_label=key,
        ).ok is True
    assert SchemaValidator(ROOT).validate_payload(
        schema="ProductVisionPayload",
        payload=fixtures["invalid_payloads"]["product-vision-unsupported-claim"],
        instance_label="bad-claim",
    ).ok is False
    assert SchemaValidator(ROOT).validate_payload(
        schema="RequirementsPayload",
        payload=fixtures["invalid_payloads"]["requirements-missing-acceptance"],
        instance_label="bad-acceptance",
    ).ok is False


def test_mp1a02_dependency_profile_catalog_is_exact_and_fail_closed() -> None:
    profiles = load_product_definition_dependency_profiles(ROOT)
    assert [p.artifact_type for p in profiles] == ["product-vision", "mvp-scope", "requirements-specification"]
    assert select_product_definition_dependency_profile(ROOT, "mvp-scope").required_upstream[0].artifact_type == "product-vision"
    with pytest.raises(ArtifactDependencyResolutionError, match="unavailable or ambiguous"):
        select_product_definition_dependency_profile(ROOT, "architecture")


def test_mp1a02_dependency_resolution_enforces_frozen_lineage_and_required_inputs() -> None:
    resolver = ArtifactDependencyResolver(ROOT)
    vision = select_product_definition_dependency_profile(ROOT, "product-vision")
    records = [
        record("project-context", "ctx"),
        record("business-need", "need"),
        record("owner-constraints", "owner"),
    ]
    resolved = resolver.resolve(profile=vision, records=records, as_of=NOW)
    assert [x["artifact_type"] for x in resolved.selected_sources] == ["project-context", "business-need", "owner-constraints"]
    with pytest.raises(ArtifactDependencyResolutionError, match="owner-constraints"):
        resolver.resolve(profile=vision, records=records[:-1], as_of=NOW)

    scope = select_product_definition_dependency_profile(ROOT, "mvp-scope")
    scope_records = [
        record("product-vision", "vision", lifecycle="DRAFT"),
        record("project-context", "ctx"),
        record("owner-decision-register", "decisions"),
    ]
    with pytest.raises(ArtifactDependencyResolutionError, match="product-vision"):
        resolver.resolve(profile=scope, records=scope_records, as_of=NOW)


def test_mp1a02_dependency_profile_catalog_schema_and_schema_registry_pass() -> None:
    assert SchemaValidator(ROOT).validate(
        schema="ProductDefinitionDependencyProfiles",
        instance="docs/validation/product_definition_dependency_profiles.json",
    ).ok is True
    from devpilot_core.schemas.registry import SchemaRegistry

    assert SchemaRegistry(ROOT).list().ok is True
