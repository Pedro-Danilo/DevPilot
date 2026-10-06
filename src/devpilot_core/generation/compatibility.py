from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .contracts import (
    ArtifactCandidateEnvelope,
    CandidateOrigin,
    CandidateOriginKind,
    GenerationProvenance,
    GenerationRequest,
    ProviderClass,
    create_candidate,
)


def wrap_technical_design_candidate(
    *,
    request: GenerationRequest,
    content: str,
    derivation: Mapping[str, Any],
) -> ArtifactCandidateEnvelope[dict[str, Any]]:
    """Wrap the existing C-02 provider output without migrating or mutating it.

    The historical provider keeps returning ``(content, derivation)``. MP-0B only
    creates a typed envelope seam so later waves can adopt the common candidate
    lifecycle without rewriting frozen C-02 artifacts or changing provider output.
    """

    provider_id = str(derivation.get("provider") or "devpilot-local")
    model_id = str(derivation.get("model") or "") or None
    model_execution_used = bool(derivation.get("model_execution_used", False))
    external_api_used = bool(derivation.get("external_api_used", False))
    if external_api_used:
        provider_class = ProviderClass.EXTERNAL_MODEL
    elif model_execution_used:
        provider_class = ProviderClass.LOCAL_MODEL
    else:
        provider_class = ProviderClass.DETERMINISTIC

    payload = {
        "content": str(content),
        "derivation": deepcopy(dict(derivation)),
    }
    return create_candidate(
        request=request,
        payload=payload,
        origin=CandidateOrigin(
            kind=CandidateOriginKind.PROVIDER,
            provider_class=provider_class,
            provider_id=provider_id,
            model_id=model_id,
        ),
        provenance=GenerationProvenance(
            profile_ref=request.profile_version,
            context_ref=request.context_reference,
            network_used=bool(derivation.get("network_used", False)),
            external_api_used=external_api_used,
            cost_usd=float(derivation.get("cost_usd", 0.0)),
            evidence_refs=tuple(str(item) for item in derivation.get("rag_source_refs") or ()),
        ),
    )
