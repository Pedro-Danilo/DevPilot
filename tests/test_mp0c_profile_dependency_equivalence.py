from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from devpilot_core.generation import (
    ArtifactAuthorityRecord,
    ArtifactDependencyProfile,
    ArtifactDependencyResolutionError,
    ArtifactDependencyResolver,
    DependencyRequirement,
    DeterministicEquivalenceHarness,
    EquivalenceContract,
    EquivalenceMode,
    GenerationRequest,
    wrap_technical_design_candidate,
)
from devpilot_core.validation import ArtifactProfileRegistry
from devpilot_core.validators.artifact_profiles import ArtifactProfile

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 6, tzinfo=timezone.utc)


def _record(
    artifact_type: str,
    artifact_id: str,
    content: str,
    *,
    rank: int = 100,
    namespace: str = "project",
    lifecycle: str = "FROZEN",
    updated: str | None = "2026-10-05T00:00:00Z",
    source_path: str | None = None,
) -> ArtifactAuthorityRecord:
    return ArtifactAuthorityRecord(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        content=content,
        authority_rank=rank,
        namespace=namespace,
        lifecycle=lifecycle,
        updated_at_utc=updated,
        citation_ref=f"{artifact_id}#authority",
        source_path=source_path,
    )


def test_artifact_profile_foundation_extends_existing_registry_without_parallel_catalog() -> None:
    profile = ArtifactProfileRegistry(ROOT).select(ROOT / "docs/02_architecture/architecture_document.md")
    assert profile.id == "architecture-document"
    assert profile.profile_version == "1.0.0"
    assert profile.purpose == profile.description
    assert profile.required_sections == profile.required_headings
    assert profile.optional_sections == profile.recommended_headings
    contract = profile.foundation_contract()
    assert contract["artifact_type"] == "architecture-document"
    assert contract["migration_policy"] == "compatible-additive"
    assert contract["assumptions_policy"] == "explicit"

    with pytest.raises(ValueError, match="profile_version"):
        ArtifactProfile(id="bad", description="Bad profile", profile_version="v1")


def test_dependency_resolver_fails_closed_when_required_authority_is_missing() -> None:
    profile = ArtifactDependencyProfile(
        profile_id="architecture-inputs",
        artifact_type="architecture",
        required_upstream=(DependencyRequirement("requirements", min_authority_rank=80),),
    )
    with pytest.raises(ArtifactDependencyResolutionError, match="requirements"):
        ArtifactDependencyResolver(ROOT).resolve(profile=profile, records=(), as_of=NOW)


def test_dependency_resolver_uses_authority_rank_freshness_and_rejects_excluded_sources() -> None:
    profile = ArtifactDependencyProfile(
        profile_id="architecture-inputs",
        artifact_type="architecture",
        required_upstream=(DependencyRequirement("requirements", min_authority_rank=80, max_age_days=30),),
        optional_supporting=(DependencyRequirement("decision-register", min_authority_rank=10, max_age_days=30),),
        allowed_namespaces=("project",),
        excluded_sources=("outputs/*", "*draft-noise*"),
        max_context_tokens=500,
    )
    records = (
        _record("requirements", "REQ-low", "lower authority", rank=81),
        _record("requirements", "REQ-high", "authoritative requirements", rank=100),
        _record("requirements", "REQ-stale", "stale requirements", rank=200, updated="2025-01-01T00:00:00Z"),
        _record("decision-register", "DEC-good", "owner decision", rank=20),
        _record("decision-register", "DEC-draft-noise", "noise", rank=999, source_path="outputs/draft-noise.md"),
    )
    result = ArtifactDependencyResolver(ROOT).resolve(profile=profile, records=records, as_of=NOW)
    ids = [row["artifact_id"] for row in result.selected_sources]
    assert ids == ["REQ-high", "DEC-good"]
    assert any(row["reason"] == "stale" for row in result.rejected_sources)
    assert any(row["reason"] == "excluded-source" for row in result.rejected_sources)


def test_dependency_context_budget_is_fail_closed_for_required_sources_and_bounded_for_optional() -> None:
    required = _record("requirements", "REQ-1", "alpha " * 500)
    profile = ArtifactDependencyProfile(
        profile_id="architecture-small-budget",
        artifact_type="architecture",
        required_upstream=(DependencyRequirement("requirements"),),
        max_context_tokens=10,
    )
    with pytest.raises(ArtifactDependencyResolutionError, match="context budget"):
        ArtifactDependencyResolver(ROOT).resolve(profile=profile, records=(required,), as_of=NOW)

    bounded = ArtifactDependencyProfile(
        profile_id="architecture-bounded",
        artifact_type="architecture",
        required_upstream=(DependencyRequirement("requirements"),),
        optional_supporting=(DependencyRequirement("decision-register"),),
        max_context_tokens=80,
    )
    req = _record("requirements", "REQ-2", "required concise input")
    optional = _record("decision-register", "DEC-large", "optional " * 500)
    result = ArtifactDependencyResolver(ROOT).resolve(profile=bounded, records=(req, optional), as_of=NOW)
    assert [row["artifact_id"] for row in result.selected_sources] == ["REQ-2"]
    assert any(row["artifact_id"] == "DEC-large" and row["reason"] == "context-budget" for row in result.rejected_sources)


def test_dependency_context_hash_is_order_and_crlf_stable() -> None:
    profile = ArtifactDependencyProfile(
        profile_id="test-inputs",
        artifact_type="test-strategy",
        required_upstream=(DependencyRequirement("requirements"), DependencyRequirement("architecture")),
        max_context_tokens=500,
    )
    records_a = (
        _record("requirements", "REQ-1", "line one\r\nline two"),
        _record("architecture", "ARC-1", "component A\r\ncomponent B"),
    )
    records_b = (
        _record("architecture", "ARC-1", "component A\ncomponent B"),
        _record("requirements", "REQ-1", "line one\nline two"),
    )
    resolver = ArtifactDependencyResolver(ROOT)
    left = resolver.resolve(profile=profile, records=records_a, as_of=NOW)
    right = resolver.resolve(profile=profile, records=records_b, as_of=NOW)
    assert left.context_sha256 == right.context_sha256
    assert [row["artifact_id"] for row in left.selected_sources] == ["REQ-1", "ARC-1"]


def test_dependency_resolver_composes_existing_contextpack_v2_without_second_rag() -> None:
    profile = ArtifactDependencyProfile(
        profile_id="architecture-grounded",
        artifact_type="architecture",
        required_upstream=(DependencyRequirement("requirements"),),
        max_context_tokens=400,
        grounding_step_id="architecture",
        grounding_required=False,
    )
    req = _record("requirements", "REQ-1", "Architecture shall remain local-first and traceable.")
    result = ArtifactDependencyResolver(ROOT).resolve(
        profile=profile,
        records=(req,),
        as_of=datetime(2026, 8, 29, tzinfo=timezone.utc),
        grounding_query="architecture application service boundary ADR guided sdlc",
    )
    payload = result.to_dict()
    assert payload["terminology"]["context_pack_v2"] == "supplementary local grounding"
    assert payload["terminology"]["agentic_rag"] is False
    assert result.grounding["network_used"] is False
    assert result.grounding["external_api_used"] is False
    assert result.grounding["status"] in {"grounded", "insufficient-evidence"}


def test_equivalence_harness_does_not_make_exact_prose_snapshot_universal() -> None:
    harness = DeterministicEquivalenceHarness()
    exact = EquivalenceContract("exact", EquivalenceMode.EXACT_HASH)
    structural = EquivalenceContract("structural", EquivalenceMode.STRUCTURAL)
    semantic = EquivalenceContract("semantic", EquivalenceMode.SEMANTIC_PROJECTION)

    baseline = {"title": "Architecture", "body": "Line one\r\nLine two", "requirements": ["RF-001"]}
    reformatted = {"title": "Architecture", "body": "Line one\nLine two", "requirements": ["RF-001"]}
    assert harness.compare(baseline=baseline, candidate=reformatted, contract=exact).equivalent is False
    assert harness.compare(baseline=baseline, candidate=reformatted, contract=structural).equivalent is True

    projector = lambda value: {"title": value["title"], "requirements": value["requirements"]}
    prose_variant = {"title": "Architecture", "body": "Completely different prose", "requirements": ["RF-001"]}
    assert harness.compare(baseline=baseline, candidate=prose_variant, contract=semantic, projector=projector).equivalent is True
    true_drift = {"title": "Architecture", "body": "Different", "requirements": ["RF-999"]}
    result = harness.compare(baseline=baseline, candidate=true_drift, contract=semantic, projector=projector)
    assert result.equivalent is False
    assert any("requirements" in path for path in result.drift_paths)


def test_equivalence_harness_can_probe_existing_deterministic_technical_design_seam() -> None:
    request = GenerationRequest(
        request_id="req-mp0c-technical",
        artifact_type="architecture",
        profile_version="1.0.0",
        dependency_profile_version="1.0.0",
        upstream_hashes={"requirements": "a" * 64},
    )
    derivation = {
        "schema_id": "devpilot.gsdlc13c02.technical_design_derivation.v1",
        "provider": "devpilot-local",
        "model": "deterministic-technical-design-template-v1",
        "model_execution_used": False,
        "external_api_used": False,
        "network_used": False,
        "cost_usd": 0.0,
        "canonical_input_sha256": "b" * 64,
    }
    baseline = wrap_technical_design_candidate(request=request, content="# Architecture\n\nOriginal prose.\n", derivation=derivation)
    variant = wrap_technical_design_candidate(request=request, content="# Architecture\n\nReformatted prose.\n", derivation=derivation)
    projector = lambda envelope: {
        "artifact_type": envelope.artifact_type,
        "provider": envelope.origin.provider_id,
        "canonical_input_sha256": envelope.payload["derivation"]["canonical_input_sha256"],
        "schema_id": envelope.payload["derivation"]["schema_id"],
    }
    harness = DeterministicEquivalenceHarness()
    contract = EquivalenceContract("c02-seam-semantic", EquivalenceMode.SEMANTIC_PROJECTION)
    assert harness.compare(baseline=baseline, candidate=variant, contract=contract, projector=projector).equivalent is True

    drift_derivation = dict(derivation)
    drift_derivation["canonical_input_sha256"] = "c" * 64
    drift = wrap_technical_design_candidate(request=request, content="# Architecture\n\nReformatted prose.\n", derivation=drift_derivation)
    assert harness.compare(baseline=baseline, candidate=drift, contract=contract, projector=projector).equivalent is False
