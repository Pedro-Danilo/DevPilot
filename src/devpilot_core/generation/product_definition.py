from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .contracts import (
    ArtifactCandidateEnvelope,
    CandidateOrigin,
    CandidateOriginKind,
    CandidateStatus,
    GenerationProvenance,
    GenerationRequest,
    ProviderClass,
    create_candidate,
)


_STAGE_TO_ARTIFACT = {
    "product-vision": "product-vision",
    "scope": "mvp-scope",
    "requirements": "requirements-specification",
}


class DeterministicProductDefinitionProvider:
    """First-class deterministic C-01 provider over the legacy proven renderer.

    The provider deliberately owns generation only. Review, approval, source write,
    apply and FROZEN transitions remain in the inherited server-authoritative
    artifact lifecycle. This extraction is intentionally semantic-preserving.
    """

    provider_id = "devpilot-local"
    provider_class = ProviderClass.DETERMINISTIC
    model_id = "deterministic-semantic-model-template-v3"

    def __init__(self, renderer: Callable[[Mapping[str, Any]], str]) -> None:
        self._renderer = renderer

    def generate(
        self,
        request: GenerationRequest,
        authoritative_input: Mapping[str, Any],
    ) -> ArtifactCandidateEnvelope[dict[str, Any]]:
        if request.preferred_route != ProviderClass.DETERMINISTIC.value:
            raise ValueError("deterministic product-definition provider requires deterministic preferred_route")
        if tuple(request.allowed_routes) != (ProviderClass.DETERMINISTIC.value,):
            raise ValueError("deterministic product-definition provider does not accept model routes")
        stage_id = str(authoritative_input.get("stage_id") or "")
        artifact_type = _STAGE_TO_ARTIFACT.get(stage_id)
        if artifact_type is None or artifact_type != request.artifact_type:
            raise ValueError("stage/artifact_type mismatch for deterministic product-definition provider")
        content = str(self._renderer(authoritative_input))
        if not content.strip():
            raise ValueError("deterministic product-definition provider produced empty content")
        payload = {
            "stage_id": stage_id,
            "content": content,
        }
        return create_candidate(
            request=request,
            payload=payload,
            origin=CandidateOrigin(
                kind=CandidateOriginKind.PROVIDER,
                provider_class=ProviderClass.DETERMINISTIC,
                provider_id=self.provider_id,
                model_id=self.model_id,
            ),
            provenance=GenerationProvenance(
                profile_ref=request.profile_version,
                context_ref=request.context_reference,
                network_used=False,
                external_api_used=False,
                cost_usd=0.0,
                evidence_refs=tuple(sorted(str(key) for key in request.upstream_hashes)),
            ),
            status=CandidateStatus.GENERATED,
            evaluation_summary={
                "route": "deterministic",
                "provider_authority": "generation-only",
                "source_write": False,
                "apply_authority": False,
                "freeze_authority": False,
            },
        )


def artifact_type_for_stage(stage_id: str) -> str:
    try:
        return _STAGE_TO_ARTIFACT[str(stage_id)]
    except KeyError as exc:
        raise ValueError(f"unsupported Product Definition stage: {stage_id}") from exc
