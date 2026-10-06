"""Shared Multiprovider v2 candidate/generation contracts.

MP-0B adds a provider-neutral candidate kernel only. Runtime routing, provider
health/cost selection, ArtifactProfile/DependencyProfile and UI remain owned by
later MP-0 micro-sprints and by existing DevPilot authority services.
"""

from .compatibility import wrap_technical_design_candidate
from .contracts import (
    ArtifactCandidateEnvelope,
    CandidateComparisonGroup,
    CandidateLineage,
    CandidateOrigin,
    CandidateOriginKind,
    CandidateReference,
    CandidateStatus,
    DownstreamAuthorityBinding,
    GenerationProvider,
    GenerationProvenance,
    GenerationRequest,
    LEGAL_TRANSITIONS,
    LineageReason,
    ProviderClass,
    canonical_sha256,
    create_candidate,
    create_successor_candidate,
    invalidate_stale_authority,
    provider_authority_violations,
    transition_candidate,
)

__all__ = [
    "ArtifactCandidateEnvelope",
    "CandidateComparisonGroup",
    "CandidateLineage",
    "CandidateOrigin",
    "CandidateOriginKind",
    "CandidateReference",
    "CandidateStatus",
    "DownstreamAuthorityBinding",
    "GenerationProvider",
    "GenerationProvenance",
    "GenerationRequest",
    "LEGAL_TRANSITIONS",
    "LineageReason",
    "ProviderClass",
    "canonical_sha256",
    "create_candidate",
    "create_successor_candidate",
    "invalidate_stale_authority",
    "provider_authority_violations",
    "transition_candidate",
    "wrap_technical_design_candidate",
]
