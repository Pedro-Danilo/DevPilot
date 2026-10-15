"""Typed, side-effect-free adapter for governed Story implementation proposals.

This is a projection into the existing candidate contract, not an apply authority.
The existing Story implementation service remains the sole owner of human
review/draft materialization, and 09-C remains the only source mutation path.
"""
from __future__ import annotations

from typing import Any, Mapping

from devpilot_core.generation.contracts import (
    CandidateOrigin, CandidateOriginKind, GenerationProvenance, GenerationRequest,
    ProviderClass, create_candidate,
)


def project_story_proposal(proposal: Mapping[str, Any]) -> dict[str, Any]:
    """Create a typed request and candidate reference from one reviewed proposal.

    This is deterministic and has no filesystem, model, network, approval or
    source-write effects. An envelope references the original proposal and
    file hashes, rather than duplicating source content or applying a patch.
    """
    identity = str(proposal.get("proposal_id") or "").strip()
    provenance = proposal.get("provenance") or {}
    provider = proposal.get("provider") or {}
    quality = proposal.get("quality") or {}
    files = proposal.get("files") or []
    if not identity or not proposal.get("proposal_sha256"):
        raise ValueError("STORY_PROPOSAL_IDENTITY_REQUIRED")
    if not quality.get("ready_for_draft_materialization") or not files:
        raise ValueError("STORY_PROPOSAL_QUALITY_BLOCK")
    if provider.get("external_api_used") or proposal.get("safety", {}).get("apply_authority"):
        raise ValueError("STORY_PROPOSAL_AUTHORITY_BLOCK")
    context_hash = str(provenance.get("story_context_sha256") or "")
    architecture_hash = str(provenance.get("architecture_sha256") or "")
    proposal_hash = str(proposal["proposal_sha256"])
    route_kind = str(provider.get("route_kind") or "")
    provider_class = (ProviderClass.LOCAL_MODEL if "local-model" in route_kind else ProviderClass.DETERMINISTIC)
    route = "local-model" if provider_class is ProviderClass.LOCAL_MODEL else "deterministic"
    request = GenerationRequest(
        request_id=identity,
        artifact_type="story-implementation-proposal-reference",
        profile_version="mp132-r01-01/story-proposal-v1",
        dependency_profile_version="gsdlc-story-context-and-frozen-architecture-v1",
        upstream_hashes={"story_context": context_hash, "architecture": architecture_hash, "proposal": proposal_hash},
        owner_inputs={"story_id": str(proposal.get("story_id") or ""), "story_execution_id": str(proposal.get("story_execution_id") or "")},
        preferred_route=route, allowed_routes=(route,),
        policy_snapshot={"approval_authority": False, "apply_authority": False, "git_authority": False, "external_egress": "DENY"},
        budget_snapshot={"max_external_cost_usd": 0.0},
        context_reference=str(provenance.get("story_context_pack_id") or "") or None,
    )
    rows = []
    for row in files:
        if not isinstance(row, Mapping) or not row.get("target_path") or not row.get("content_sha256"):
            raise ValueError("STORY_PROPOSAL_FILE_IDENTITY_BLOCK")
        rows.append({key: row.get(key) for key in (
            "target_path", "operation", "content_sha256", "source_id", "source_preimage_sha256")})
    payload = {
        "proposal_id": identity,
        "proposal_sha256": proposal_hash,
        "story_id": str(proposal.get("story_id") or ""),
        "files": rows,
        "quality_accepted_for_draft_review": True,
        "source_mutations_performed": False,
        "apply_authority": False,
    }
    origin = CandidateOrigin(
        kind=CandidateOriginKind.PROVIDER, provider_class=provider_class,
        provider_id=str(provider.get("provider_id") or "devpilot-local"),
        model_id=str(provider.get("model_id") or "") or None,
    )
    candidate = create_candidate(
        request=request, payload=payload, origin=origin,
        provenance=GenerationProvenance(
            profile_ref=request.profile_version,
            context_ref=request.context_reference,
            network_used=bool(provider.get("network_used", False)),
            external_api_used=False,
            cost_usd=float(provider.get("cost_usd") or 0.0),
            evidence_refs=(identity,),
        ),
        evaluation_summary={"quality_status": "READY_FOR_HUMAN_REVIEW", "no_apply_authority": True},
    )
    if not candidate.content_integrity_ok():
        raise ValueError("STORY_ENVELOPE_CONTENT_DRIFT")
    return {"generation_request": request.to_dict(), "artifact_candidate_envelope": candidate.to_dict(), "execution_posture": "PROPOSAL_ONLY_NO_APPLY"}
