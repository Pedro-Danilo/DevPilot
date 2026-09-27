from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application.pre_code_technical_design import (
    C02_MODEL,
    C02_SCHEMA,
    DeterministicTechnicalDesignProvider,
    parse_requirements,
    validate_technical_artifact,
)
from devpilot_core.application.services import ApplicationService
from devpilot_core.modeling import LocalProviderDiscoveryOptions, LocalProviderDiscoveryService

from test_devpl_gsdlc_13_c_01_pre_code_derived_authoring_corrective import (
    _activate,
    _freeze_test_stage,
    _generate_product_vision,
    _platform,
    _workspace,
)

ROOT = Path(__file__).resolve().parents[1]


def _prepare_c01(platform: Path, ws: Path) -> ApplicationService:
    svc = ApplicationService(platform)
    actor = "local-owner"
    vision, _ = _generate_product_vision(svc, ws, actor)
    _freeze_test_stage(platform, ws, "product-vision", "docs/00_product/product_vision.md", vision.data["stage"]["draft_content"])
    scope = svc.guided_pre_code_save_draft(stage_id="scope", content="", mode="DEVPL_MOCK", actor=actor, actor_role="owner", session_principal=actor, effective_roles=["owner"], workspace_scopes=[ws.name])
    assert scope.ok, scope.to_dict()
    _freeze_test_stage(platform, ws, "scope", "docs/00_product/mvp_scope.md", scope.data["stage"]["draft_content"])
    req = svc.guided_pre_code_save_draft(stage_id="requirements", content="", mode="DEVPL_MOCK", actor=actor, actor_role="owner", session_principal=actor, effective_roles=["owner"], workspace_scopes=[ws.name])
    assert req.ok, req.to_dict()
    _freeze_test_stage(platform, ws, "requirements", "docs/01_requirements/requirements_specification.md", req.data["stage"]["draft_content"])
    return svc


def _draft_and_review(svc: ApplicationService, ws: Path, stage_id: str) -> str:
    actor = "local-owner"
    draft = svc.guided_pre_code_save_draft(stage_id=stage_id, content="", mode="DEVPL_MOCK", actor=actor, actor_role="owner", session_principal=actor, effective_roles=["owner"], workspace_scopes=[ws.name])
    assert draft.ok, draft.to_dict()
    row = draft.data["stage"]
    assert row["status"] == "DRAFT" and row["mode"] == "DEVPL_MOCK"
    d = row["derivation"]
    assert d["schema_id"] == C02_SCHEMA and d["model"] == C02_MODEL
    assert d["provider"] == "devpilot-local"
    assert d["network_used"] is False and d["external_api_used"] is False and d["cost_usd"] == 0
    assert d["model_execution_used"] is False and d["agent_execution_used"] is False
    assert d["rag_execution_used"] is True
    review = svc.guided_pre_code_review(stage_id=stage_id, actor=actor, actor_role="owner", session_principal=actor, effective_roles=["owner"])
    assert review.ok, review.to_dict()
    assert review.data["review"]["status"] == "APPROVAL_REQUIRED"
    return row["draft_content"]


def test_c02_catalog_and_ui_expose_governed_deterministic_rag_route_without_faking_agent_authoring():
    catalog = json.loads((ROOT / ".devpilot/gsdlc/pre_code_wizard_catalog.json").read_text(encoding="utf-8"))
    rows = {x["stage_id"]: x for x in catalog["stages"]}
    assert catalog["profile_id"] == "guided-pre-code-manual-v1"  # compatibility identity preserved
    for stage in ("architecture", "security", "test-strategy", "traceability"):
        assert rows[stage]["allowed_modes"][0] == "DEVPL_MOCK"
    view = (ROOT / "ui/web/src/pages/PreCodeWizardView.ts").read_text(encoding="utf-8")
    assert "DevPilot · Diseño local + RAG / sin API" in view
    assert "DevPilot local + RAG" in view
    assert "aún no son providers de primer DRAFT de Pre-code" in view
    assert "c01SemanticStage=stage.order<=3" in view
    assert "LLM ejecutado" in view and "agente ejecutado" in view


def test_c02_generates_reviewable_architecture_security_test_and_traceability(tmp_path, monkeypatch):
    platform = _platform(tmp_path); ws = _workspace(tmp_path); _activate(platform, ws, monkeypatch)
    svc = _prepare_c01(platform, ws)
    status = svc.guided_pre_code_status(effective_roles=["owner"], workspace_scopes=[ws.name])
    assert status.ok and status.data["pre_code"]["current_stage_id"] == "architecture"

    arch = _draft_and_review(svc, ws, "architecture")
    for token in ("## Drivers", "## Componentes", "## ADRs", "ADR-001", "ADR-003", "## Tecnología", "## RAG grounding", "RF-"):
        assert token in arch
    assert not (ws / "docs/02_architecture/architecture_document.md").exists()
    _freeze_test_stage(platform, ws, "architecture", "docs/02_architecture/architecture_document.md", arch)

    sec = _draft_and_review(svc, ws, "security")
    for token in ("## Activos", "## Límites de confianza", "## Amenazas", "SEC-001", "CTRL-001", "## Criterios de bloqueo"):
        assert token in sec
    _freeze_test_stage(platform, ws, "security", "docs/03_security/security_threat_model.md", sec)

    tests = _draft_and_review(svc, ws, "test-strategy")
    for token in ("## Tipos de pruebas", "## Quality gates", "## Test intents", "TEST-001"):
        assert token in tests
    _freeze_test_stage(platform, ws, "test-strategy", "docs/04_quality/test_strategy.md", tests)

    trace = _draft_and_review(svc, ws, "traceability")
    for token in ("## Matriz", "Requirement | Capability/source | Architecture | ADR | Security/control | Test intent", "RF-001"):
        assert token in trace
    assert not (ws / "docs/01_requirements/traceability_matrix.md").exists()


def test_c02_owner_edit_preserves_technical_derivation_identity(tmp_path, monkeypatch):
    platform = _platform(tmp_path); ws = _workspace(tmp_path); _activate(platform, ws, monkeypatch)
    svc = _prepare_c01(platform, ws)
    actor = "local-owner"
    first = svc.guided_pre_code_save_draft(stage_id="architecture", content="", mode="DEVPL_MOCK", actor=actor, actor_role="owner", session_principal=actor, effective_roles=["owner"], workspace_scopes=[ws.name])
    assert first.ok
    content = first.data["stage"]["draft_content"] + "\n<!-- Owner review note -->\n"
    edited = svc.guided_pre_code_save_draft(stage_id="architecture", content=content, mode="DEVPL_MOCK", actor=actor, actor_role="owner", session_principal=actor, effective_roles=["owner"], workspace_scopes=[ws.name])
    assert edited.ok, edited.to_dict()
    d = edited.data["stage"]["derivation"]
    assert d["schema_id"] == C02_SCHEMA and d["model"] == C02_MODEL
    assert d["owner_edited"] is True
    assert d["model_execution_used"] is False and d["agent_execution_used"] is False and d["rag_execution_used"] is True


def test_c02_provider_is_generic_and_does_not_hardcode_pilot_domain():
    requirements = """# Requirements Specification\n\n## Requerimientos funcionales del MVP\n\n### RF-001\n- **Tipo:** FR.\n- **Statement:** El sistema debe permitir al recepcionista registrar pacientes en una cola de atención.\n- **Fuente:** CAP-101.\n- **Prioridad:** MUST.\n- **Criterio de aceptación:** Una alta válida queda registrada y consultable.\n- **Método de verificación:** TEST.\n\n### RF-002\n- **Tipo:** FR.\n- **Statement:** El sistema debe permitir al recepcionista consultar el siguiente turno.\n- **Fuente:** CAP-102.\n- **Prioridad:** MUST.\n- **Criterio de aceptación:** La consulta devuelve el turno sin modificar el estado.\n- **Método de verificación:** TEST.\n"""
    provider = DeterministicTechnicalDesignProvider()
    content, derivation = provider.derive(
        root=ROOT, stage_id="architecture", workspace_id="clinic-queue", project_name="Clinic Queue", document_date="2026-09-25",
        project_metadata={"project_constraints": {"local_first": True, "cloud_required": False}, "model_policy": {"baseline": "mock-no-api"}},
        upstream={"product-vision":"# Vision\nClinic Queue", "scope":"# Scope\nQueue MVP", "requirements":requirements}, semantic_model=None,
    )
    assert derivation["model"] == C02_MODEL and derivation["rag_execution_used"] is True
    assert "CAP-101" in content and "RF-001" in content and "Clinic Queue" in content
    lowered = content.lower()
    for forbidden in ("inventario", "ventas", "producto disponible", "stock bajo"):
        assert forbidden not in lowered
    assert not validate_technical_artifact("architecture", content, requirements)


def test_requirements_parser_and_quality_gate_are_requirement_id_driven():
    sample = """### RF-101\n- **Tipo:** FR.\n- **Statement:** El sistema debe registrar una cita.\n- **Fuente:** CAP-201.\n- **Prioridad:** MUST.\n- **Criterio de aceptación:** La cita queda disponible.\n- **Método de verificación:** TEST.\n"""
    rows = parse_requirements(sample)
    assert len(rows) == 1 and rows[0].requirement_id == "RF-101" and rows[0].sources == ("CAP-201",)
    bad = "# Traceability Matrix\n\n## Propósito\nX\n\n## Matriz\n\n| Requirement | Architecture | ADR | Security | Test intent |\n|---|---|---|---|---|\n"
    findings = validate_technical_artifact("traceability", bad, sample)
    assert any(x["id"] == "GSDLC13C02_TRACE_COVERAGE_BLOCK" for x in findings)


def test_versioned_provider_example_declares_all_three_local_provider_contracts():
    cfg = (ROOT / ".devpilot/providers.yaml.example").read_text(encoding="utf-8")
    for provider_id in ("ollama", "lmstudio", "openai-compatible-local"):
        assert f'id: "{provider_id}"' in cfg
    assert 'id: "openai-compatible-local"' in cfg and 'enabled: false' in cfg


def test_optional_unconfigured_local_provider_is_nonblocking_and_schema_complete():
    result = LocalProviderDiscoveryService(
        ROOT,
        LocalProviderDiscoveryOptions(probe=False, provider_ids=("openai-compatible-local",)),
    ).build()
    assert result.ok is True
    row = result.data["report"]["providers"][0]
    assert row["provider_id"] == "openai-compatible-local"
    assert row["configured"] is False and row["enabled"] is False
    assert row["external_api"] is False and row["requires_api_key"] is False
    assert row["discovery_enables_provider"] is False
    assert row["fallback"]["provider_id"] == "mock"
