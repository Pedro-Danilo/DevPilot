"""MP132 R01-01: typed Story bridge, two distinct domains, no second authority."""
from __future__ import annotations

import pytest

from devpilot_core.generation.contracts import ArtifactCandidateEnvelope, GenerationRequest, canonical_sha256
from devpilot_core.generation.story_bridge import project_story_proposal


def _proposal(domain: str):
    context = {"domain": domain, "story": f"Create {domain} resource"}
    architecture = {"stack": "fastapi-sqlite", "domain": domain}
    data = {"files": [f"src/{domain}/domain.py"], "story": context}
    return {
        "proposal_id": f"implementation-proposal-{domain}",
        "proposal_sha256": canonical_sha256(data),
        "story_id": f"story-{domain}", "story_execution_id": f"execution-{domain}",
        "provider": {"provider_id": "devpilot-local", "model_id": "deterministic-v1", "network_used": False, "cost_usd": 0},
        "quality": {"ready_for_draft_materialization": True},
        "files": [{"target_path": f"src/{domain}/domain.py", "operation": "CREATE", "content_sha256": canonical_sha256(data)}],
        "provenance": {"story_context_sha256": canonical_sha256(context), "architecture_sha256": canonical_sha256(architecture), "story_context_pack_id": f"ctx-{domain}"},
        "safety": {"apply_authority": False, "source_mutations_performed": False},
    }


@pytest.mark.parametrize("domain", ["inventory", "appointments"])
def test_typed_adapter_two_domains_no_mutation(domain):
    proposal = _proposal(domain)
    original = repr(proposal)
    result = project_story_proposal(proposal)
    request = GenerationRequest.from_dict(result["generation_request"])
    envelope = ArtifactCandidateEnvelope.from_dict(result["artifact_candidate_envelope"])
    assert envelope.content_integrity_ok()
    assert request.canonical_input_sha256 == envelope.canonical_input_sha256
    assert envelope.payload["story_id"] == f"story-{domain}"
    assert envelope.payload["apply_authority"] is False
    assert envelope.origin.provider_class.value == "deterministic"
    assert result == project_story_proposal(proposal)
    assert repr(proposal) == original


def test_reject_second_authority():
    proposal = _proposal("inventory")
    proposal["safety"]["apply_authority"] = True
    with pytest.raises(ValueError, match="AUTHORITY_BLOCK"):
        project_story_proposal(proposal)


def test_reject_missing_hash_and_quality():
    p = _proposal("appointments")
    p["provenance"]["architecture_sha256"] = "not-a-hash"
    with pytest.raises(ValueError, match="SHA-256"):
        project_story_proposal(p)
    q = _proposal("inventory")
    q["quality"]["ready_for_draft_materialization"] = False
    with pytest.raises(ValueError, match="QUALITY_BLOCK"):
        project_story_proposal(q)


def test_local_route_requires_local_class_without_fallback():
    p = _proposal("appointments")
    p["provider"]["route_kind"] = "enabled-local-model-adapter"
    result = project_story_proposal(p)
    assert result["generation_request"]["preferred_route"] == "local-model"
    assert result["artifact_candidate_envelope"]["origin"]["provider_class"] == "local-model"
    assert result["artifact_candidate_envelope"]["provenance"]["external_api_used"] is False


def test_real_story_service_emits_typed_envelope_without_apply(tmp_path):
    # Exercise the production wiring rather than only the pure projection.
    from test_devpl_gsdlc_13_d_02_implementation_proposal_bridge import _fixture, ROOT
    from devpilot_core.application.story_implementation_candidate_service import StoryImplementationCandidateApplicationService
    from devpilot_core.code_workbench.service import CodeWorkbenchApplicationService
    workspace, resolver = _fixture(tmp_path)
    service = StoryImplementationCandidateApplicationService(
        ROOT, context_resolver=resolver,
        code_workbench=CodeWorkbenchApplicationService(ROOT, context_resolver=resolver))
    result = service.propose(actor='owner-1', actor_role='owner').to_dict()
    assert result['ok']
    proposal = result['data']['proposal']
    typed = proposal['generation_bridge']
    envelope = ArtifactCandidateEnvelope.from_dict(typed['artifact_candidate_envelope'])
    assert envelope.content_integrity_ok()
    assert envelope.payload['proposal_id'] == proposal['proposal_id']
    assert envelope.payload['apply_authority'] is False
    assert not (workspace / 'src').exists()
    assert not (workspace / 'tests').exists()
