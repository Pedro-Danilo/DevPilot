from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

from devpilot_core.application.pre_code_wizard_service import PreCodeWizardApplicationService
from devpilot_core.generation import (
    DeterministicEquivalenceHarness,
    DeterministicProductDefinitionProvider,
    EquivalenceContract,
    EquivalenceMode,
    GenerationRequest,
    ProviderClass,
    artifact_type_for_stage,
    provider_authority_violations,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/mp1a03_parity.json"


def _semantic_model() -> dict:
    return {
        "schema_id": "devpilot.gsdlc13c01.pre_code_semantic_model.v1",
        "workspace_id": "fixture-ws",
        "source_refs": [],
        "business_context": "A local-first product for governed inventory operations.",
        "actors": [{"id": "ACT-001", "kind": "ACTOR", "statement": "Persona operadora del inventario", "status": "CONFIRMED", "owner_confirmed": True}],
        "outcomes": [{"id": "OUT-001", "kind": "OUTCOME", "statement": "Mantener inventario confiable y trazable", "status": "CONFIRMED", "owner_confirmed": True}],
        "capabilities": [
            {"id": "CAP-001", "kind": "CAPABILITY", "statement": "Registrar productos disponibles", "status": "CONFIRMED", "owner_confirmed": True, "related_item_ids": []},
            {"id": "CAP-002", "kind": "CAPABILITY", "statement": "Consultar existencias actuales por producto", "status": "CONFIRMED", "owner_confirmed": True, "related_item_ids": []},
        ],
        "constraints": [],
        "open_questions": [],
        "decisions": {},
        "owner_semantic_reviewed": True,
    }


def _render_input(stage_id: str, upstream: dict[str, str]) -> dict:
    return {
        "stage_id": stage_id,
        "workspace_id": "fixture-ws",
        "project_name": "Fixture Product",
        "business_need": "Administrar inventario local de forma trazable y gobernada para la persona operadora.",
        "document_date": "2026-10-08",
        "constraints": {"local_first": True, "cloud_required": False, "operator_project_writes_allowed": False},
        "model_policy": {"baseline": "mock-no-api", "local_model": "optional-opt-in", "external_api": "approval-provenance-only"},
        "upstream": upstream,
        "semantic_model": _semantic_model(),
    }


def _request(stage_id: str, upstream: dict[str, str]) -> GenerationRequest:
    hashes = {key: hashlib.sha256(value.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest() for key, value in upstream.items()}
    hashes.setdefault(".devpilot/project.yaml", "a" * 64)
    return GenerationRequest(
        request_id=f"fixture-{stage_id}",
        artifact_type=artifact_type_for_stage(stage_id),
        profile_version="1.1.0",
        dependency_profile_version="1.0.0",
        upstream_hashes=hashes,
        owner_inputs={"semantic_model_sha256": "fixture"},
        preferred_route="deterministic",
        allowed_routes=("deterministic",),
        policy_snapshot={"network": "deny", "external_api": False},
        budget_snapshot={"max_cost_usd": 0.0},
        context_reference=f"fixture:{stage_id}",
    )


def _provider() -> DeterministicProductDefinitionProvider:
    service = object.__new__(PreCodeWizardApplicationService)
    return DeterministicProductDefinitionProvider(lambda value: service._proposal_markdown(**dict(value)))


def test_provider_is_first_class_generation_only_and_deterministic() -> None:
    provider = _provider()
    assert provider.provider_class is ProviderClass.DETERMINISTIC
    assert provider.provider_id == "devpilot-local"
    assert provider_authority_violations(type(provider)) == ()
    assert not hasattr(provider, "apply") and not hasattr(provider, "freeze")


@pytest.mark.parametrize("case", json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"])
def test_canonical_pre_extraction_parity(case: dict) -> None:
    stage_id = case["stage_id"]
    provider = _provider()
    candidate = provider.generate(_request(stage_id, case["upstream"]), _render_input(stage_id, case["upstream"]))
    content = candidate.payload["content"].replace("\r\n", "\n").replace("\r", "\n")
    assert hashlib.sha256(content.encode()).hexdigest() == case["expected_content_sha256"]
    assert candidate.origin.provider_class is ProviderClass.DETERMINISTIC
    assert candidate.provenance.network_used is False
    assert candidate.provenance.external_api_used is False
    assert candidate.evaluation_summary["source_write"] is False
    assert candidate.evaluation_summary["apply_authority"] is False
    assert candidate.evaluation_summary["freeze_authority"] is False


def test_equivalence_harness_reports_exact_structural_parity_for_provider_payload() -> None:
    case = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"][0]
    provider = _provider()
    candidate = provider.generate(_request(case["stage_id"], case["upstream"]), _render_input(case["stage_id"], case["upstream"]))
    content = candidate.payload["content"]
    result = DeterministicEquivalenceHarness().compare(
        baseline={"content": content.replace("\r\n", "\n").replace("\r", "\n")},
        candidate={"content": content},
        contract=EquivalenceContract("mp1a03-c01-eol", EquivalenceMode.STRUCTURAL, normalize_line_endings=True),
    )
    assert result.equivalent is True
    assert result.drift_paths == ()


def test_precode_service_routes_c01_through_generation_provider_without_replacing_lifecycle() -> None:
    source = inspect.getsource(PreCodeWizardApplicationService._derive_local_proposal)
    assert "DeterministicProductDefinitionProvider" in source
    assert "GenerationRequest" in source
    assert "candidate_envelope" in source
    save_source = inspect.getsource(PreCodeWizardApplicationService.save_draft)
    assert "MANUAL" in save_source and "IMPORT" in save_source and "DEVPL_MOCK" in save_source
    assert "self.lifecycle.create_draft" in save_source


def test_ui_source_is_unchanged_provider_extraction_remains_existing_guided_expert_surface() -> None:
    view = (ROOT / "ui/web/src/pages/PreCodeWizardView.ts").read_text(encoding="utf-8")
    assert "DEVPL_MOCK" in view
    assert "MANUAL" in view
    assert "IMPORT" in view
