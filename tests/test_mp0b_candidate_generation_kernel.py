from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from devpilot_core.generation import (
    ArtifactCandidateEnvelope,
    CandidateComparisonGroup,
    CandidateOrigin,
    CandidateOriginKind,
    CandidateStatus,
    DownstreamAuthorityBinding,
    GenerationProvider,
    GenerationProvenance,
    GenerationRequest,
    LineageReason,
    ProviderClass,
    canonical_sha256,
    create_candidate,
    create_successor_candidate,
    invalidate_stale_authority,
    provider_authority_violations,
    transition_candidate,
    wrap_technical_design_candidate,
)


H1 = "1" * 64
H2 = "2" * 64


def request(*, request_id: str = "req-1", upstream: str = H1) -> GenerationRequest:
    return GenerationRequest(
        request_id=request_id,
        artifact_type="architecture",
        profile_version="architecture/v1",
        dependency_profile_version="architecture-deps/v1",
        upstream_hashes={"requirements": upstream},
        owner_inputs={"decision": "local-first"},
        preferred_route="deterministic",
        allowed_routes=("deterministic", "local-model"),
        policy_snapshot={"external_api": False},
        budget_snapshot={"max_cost_usd": 0.0},
        context_reference="ctx-1",
    )


def provider_origin(provider_id: str = "devpilot-local") -> CandidateOrigin:
    return CandidateOrigin(
        kind=CandidateOriginKind.PROVIDER,
        provider_class=ProviderClass.DETERMINISTIC,
        provider_id=provider_id,
        model_id="deterministic-template-v1",
    )


def test_generation_request_roundtrip_and_canonical_hash_ignore_route_preference() -> None:
    req = request()
    restored = GenerationRequest.from_dict(req.to_dict())
    assert restored.to_dict() == req.to_dict()
    alternate_route = GenerationRequest(
        request_id="req-other-id",
        artifact_type=req.artifact_type,
        profile_version=req.profile_version,
        dependency_profile_version=req.dependency_profile_version,
        upstream_hashes=req.upstream_hashes,
        owner_inputs=req.owner_inputs,
        preferred_route="local-model",
        allowed_routes=("deterministic", "local-model"),
        policy_snapshot=req.policy_snapshot,
        budget_snapshot=req.budget_snapshot,
        context_reference=req.context_reference,
    )
    assert alternate_route.canonical_input_sha256 == req.canonical_input_sha256


def test_candidate_envelope_roundtrip_content_hash_and_identity_are_immutable() -> None:
    candidate = create_candidate(
        request=request(),
        payload={"sections": ["context", "components"]},
        origin=provider_origin(),
        provenance=GenerationProvenance(profile_ref="architecture/v1"),
    )
    assert candidate.content_integrity_ok() is True
    restored = ArtifactCandidateEnvelope.from_dict(candidate.to_dict())
    assert restored.to_dict() == candidate.to_dict()
    with pytest.raises(FrozenInstanceError):
        candidate.candidate_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        candidate.version = 99  # type: ignore[misc]


def test_candidate_lifecycle_allows_only_governed_transitions() -> None:
    candidate = create_candidate(request=request(), payload={"x": 1}, origin=provider_origin())
    validated = transition_candidate(candidate, CandidateStatus.VALIDATED)
    review = transition_candidate(validated, CandidateStatus.UNDER_REVIEW)
    selected = transition_candidate(review, CandidateStatus.SELECTED)
    assert selected.status == CandidateStatus.SELECTED
    with pytest.raises(ValueError, match="illegal candidate lifecycle transition"):
        transition_candidate(candidate, CandidateStatus.SELECTED)
    with pytest.raises(ValueError, match="illegal candidate lifecycle transition"):
        transition_candidate(selected, CandidateStatus.VALIDATED)


@pytest.mark.parametrize(
    ("reason", "origin"),
    [
        (LineageReason.REGENERATION, provider_origin()),
        (
            LineageReason.HUMAN_EDIT,
            CandidateOrigin(kind=CandidateOriginKind.HUMAN_AUTHORED, actor_id="owner-1"),
        ),
        (
            LineageReason.PROVIDER_SWITCH,
            CandidateOrigin(
                kind=CandidateOriginKind.PROVIDER,
                provider_class=ProviderClass.LOCAL_MODEL,
                provider_id="ollama",
                model_id="qwen",
            ),
        ),
        (
            LineageReason.AGENT_ENRICHMENT,
            CandidateOrigin(kind=CandidateOriginKind.AGENT_ENRICHMENT, actor_id="security-review-agent"),
        ),
    ],
)
def test_successor_lineage_preserves_parent_and_never_overwrites(reason: LineageReason, origin: CandidateOrigin) -> None:
    parent = create_candidate(request=request(), payload={"v": 1}, origin=provider_origin())
    child = create_successor_candidate(
        parent=parent,
        payload={"v": 2},
        reason=reason,
        origin=origin,
        actor_id="owner-1" if reason != LineageReason.AGENT_ENRICHMENT else "security-review-agent",
    )
    assert child.candidate_id != parent.candidate_id
    assert child.version == parent.version + 1
    assert child.lineage.parent_candidate_id == parent.candidate_id
    assert child.lineage.parent_version == parent.version
    assert child.lineage.root_candidate_id == parent.candidate_id
    assert parent.payload == {"v": 1}
    assert child.payload == {"v": 2}


def test_successor_with_changed_authoritative_inputs_records_new_input_hash() -> None:
    parent = create_candidate(request=request(), payload={"v": 1}, origin=provider_origin())
    successor_request = request(request_id="req-2", upstream=H2)
    child = create_successor_candidate(
        parent=parent,
        payload={"v": 2},
        reason=LineageReason.REGENERATION,
        origin=provider_origin(),
        actor_id="owner-1",
        request=successor_request,
    )
    assert child.canonical_input_sha256 == successor_request.canonical_input_sha256
    assert child.canonical_input_sha256 != parent.canonical_input_sha256


def test_comparison_group_requires_same_canonical_inputs_and_owner_selection() -> None:
    req = request()
    deterministic = create_candidate(request=req, payload={"proposal": "D"}, origin=provider_origin())
    local = create_candidate(
        request=req,
        payload={"proposal": "L"},
        origin=CandidateOrigin(
            kind=CandidateOriginKind.PROVIDER,
            provider_class=ProviderClass.LOCAL_MODEL,
            provider_id="ollama",
            model_id="qwen",
        ),
    )
    group = CandidateComparisonGroup.create(
        group_id="cmp-1",
        artifact_type="architecture",
        canonical_input_sha256=req.canonical_input_sha256,
    ).add(deterministic).add(local)
    assert len(group.candidates) == 2
    with pytest.raises(PermissionError, match="Owner"):
        group.select(candidate_id=local.candidate_id, actor_id="dev-1", actor_role="developer")
    selected = group.select(candidate_id=local.candidate_id, actor_id="owner-1", actor_role="owner")
    assert selected.selected_candidate_id == local.candidate_id
    other = create_candidate(request=request(request_id="req-x", upstream=H2), payload={"proposal": "X"}, origin=provider_origin())
    with pytest.raises(ValueError, match="canonical inputs"):
        group.add(other)


def test_content_or_input_hash_change_invalidates_plan_diff_and_approval() -> None:
    parent = create_candidate(request=request(), payload={"v": 1}, origin=provider_origin())
    binding = DownstreamAuthorityBinding(
        content_sha256=parent.content_sha256,
        canonical_input_sha256=parent.canonical_input_sha256,
        plan_id="plan-1",
        diff_id="diff-1",
        approval_id="approval-1",
    )
    assert invalidate_stale_authority(binding, parent) is binding
    edited = create_successor_candidate(
        parent=parent,
        payload={"v": 2},
        reason=LineageReason.HUMAN_EDIT,
        origin=CandidateOrigin(kind=CandidateOriginKind.HUMAN_AUTHORED, actor_id="owner-1"),
        actor_id="owner-1",
    )
    invalidated = invalidate_stale_authority(binding, edited)
    assert invalidated.valid is False
    assert invalidated.plan_id is None and invalidated.diff_id is None and invalidated.approval_id is None
    assert invalidated.invalidated_reason == "content-hash-changed"

    changed_inputs = create_successor_candidate(
        parent=parent,
        payload=parent.payload,
        reason=LineageReason.REGENERATION,
        origin=provider_origin(),
        actor_id="owner-1",
        request=request(request_id="req-2", upstream=H2),
    )
    invalidated_inputs = invalidate_stale_authority(binding, changed_inputs)
    assert invalidated_inputs.valid is False
    assert invalidated_inputs.invalidated_reason == "canonical-input-hash-changed"


def test_generation_provider_contract_exposes_generation_not_authority_operations() -> None:
    protocol_names = {name for name in GenerationProvider.__dict__ if not name.startswith("_")}
    assert "generate" in protocol_names
    assert protocol_names.isdisjoint({"apply", "approve", "freeze", "source_write", "git_commit", "stage"})

    class BadProvider:
        provider_id = "bad"
        provider_class = ProviderClass.DETERMINISTIC
        model_id = None

        def generate(self, request, authoritative_input):
            raise NotImplementedError

        def freeze(self):
            raise AssertionError

    assert provider_authority_violations(BadProvider) == ("freeze",)


def test_human_origin_is_not_modeled_as_provider() -> None:
    human = CandidateOrigin(kind=CandidateOriginKind.HUMAN_AUTHORED, actor_id="owner-1")
    assert human.provider_class is None
    assert human.provider_id is None
    with pytest.raises(ValueError, match="not a provider"):
        CandidateOrigin(
            kind=CandidateOriginKind.HUMAN_AUTHORED,
            actor_id="owner-1",
            provider_class=ProviderClass.DETERMINISTIC,
            provider_id="devpilot-local",
        )


def test_technical_design_compatibility_seam_preserves_legacy_payload() -> None:
    req = request()
    legacy_derivation = {
        "schema_id": "devpilot.gsdlc13c02.technical_design_derivation.v1",
        "provider": "devpilot-local",
        "model": "deterministic-technical-design-template-v1",
        "network_used": False,
        "external_api_used": False,
        "cost_usd": 0.0,
        "model_execution_used": False,
        "rag_source_refs": [{"path": "docs/x.md", "sha256": H1}],
    }
    before = {"content": "# Architecture\n", "derivation": dict(legacy_derivation)}
    wrapped = wrap_technical_design_candidate(
        request=req,
        content=before["content"],
        derivation=legacy_derivation,
    )
    assert wrapped.payload == before
    assert wrapped.origin.provider_class == ProviderClass.DETERMINISTIC
    assert wrapped.origin.provider_id == "devpilot-local"
    assert wrapped.provenance.network_used is False
    assert legacy_derivation == before["derivation"]
    assert wrapped.content_sha256 == canonical_sha256(before)
