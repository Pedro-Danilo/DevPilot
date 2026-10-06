"""Shared Multiprovider v2 candidate/generation contracts.

MP-0B adds the provider-neutral candidate kernel. MP-0C extends the same
foundation with artifact/dependency contracts and deterministic equivalence,
while runtime routing, provider health/cost selection and UI remain later scope.
"""

from .compatibility import wrap_technical_design_candidate
from .dependencies import (
    ArtifactAuthorityRecord,
    ArtifactDependencyProfile,
    ArtifactDependencyResolutionError,
    ArtifactDependencyResolver,
    DependencyRequirement,
    ResolvedArtifactContext,
)
from .equivalence import (
    DeterministicEquivalenceHarness,
    EquivalenceContract,
    EquivalenceMode,
    EquivalenceResult,
)
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
    "ArtifactAuthorityRecord",
    "ArtifactDependencyProfile",
    "ArtifactDependencyResolutionError",
    "ArtifactDependencyResolver",
    "DependencyRequirement",
    "ResolvedArtifactContext",
    "DeterministicEquivalenceHarness",
    "EquivalenceContract",
    "EquivalenceMode",
    "EquivalenceResult",
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
