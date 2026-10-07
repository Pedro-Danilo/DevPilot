from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application.model_gateway_settings_service import ModelGatewaySettingsService

ROOT = Path(__file__).resolve().parents[1]

def test_foundation_projection_uses_real_contracts_without_model_or_network() -> None:
    result = ModelGatewaySettingsService(ROOT).snapshot()
    assert result.ok
    foundation = result.data["multiprovider_foundation"]
    assert foundation["schema_id"] == "devpilot.mp-v2.foundation-ux.v1"
    assert foundation["foundation_preview"] is True
    assert foundation["fixture_classification"] == "deterministic-only/no-inference"
    assert foundation["model_call_performed"] is False
    assert foundation["network_used"] is False
    assert foundation["external_api_used"] is False

    choices = {row["provider_class"]: row for row in foundation["route_choices"]}
    assert set(choices) == {"deterministic", "local-model", "external-model"}
    assert choices["deterministic"]["execution_enabled"] is True
    assert choices["deterministic"]["resolved_provider_class"] == "deterministic"
    assert choices["local-model"]["execution_enabled"] is False
    assert choices["local-model"]["disabled_reason"]
    assert choices["external-model"]["execution_enabled"] is False
    assert choices["external-model"]["disabled_reason"] == "external-disabled"
    assert choices["external-model"]["fallback"]["reason"] == "external-never-implicit-fallback"

    candidate = foundation["candidate"]
    assert candidate["version"] == 1
    assert candidate["status"] == "GENERATED"
    assert candidate["origin"]["kind"] == "provider"
    assert candidate["origin"]["provider_class"] == "deterministic"
    assert candidate["lineage"]["reason"] == "initial-generation"

    provenance = foundation["runtime_provenance"]
    receipt = foundation["execution_receipt"]
    assert provenance["provider_class"] == "deterministic"
    assert provenance["network_used"] is False
    assert provenance["external_api_used"] is False
    assert provenance["raw_secret_present"] is False
    assert receipt["execution_attempted"] is False
    assert receipt["model_call_performed"] is False
    assert receipt["network_used"] is False
    assert receipt["external_api_used"] is False
    assert all(value is False for value in receipt["authority_boundary"].values())

    grounding = foundation["grounding"]
    assert grounding["label"] == "ContextPack grounding"
    assert grounding["retrieval_executed"] is False
    assert grounding["agentic_rag"] is False
    assert "separate" in grounding["agentic_rag_note"].lower()


def test_foundation_projection_is_bound_to_existing_api_contract_and_secret_safe() -> None:
    result = ModelGatewaySettingsService(ROOT).snapshot()
    foundation = result.data["multiprovider_foundation"]
    rendered = json.dumps(foundation).lower()
    assert foundation["foundation_preview"] is True
    assert foundation["model_call_performed"] is False
    assert "api_key" not in rendered
    assert "authorization:" not in rendered
    assert "bearer " not in rendered

    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    route = next(row for row in api["routes"] if row["path"] == "/api/v1/settings/model-gateway" and row["method"] == "GET")
    assert route["route_id"] == "api.settings.model-gateway"


def test_existing_model_settings_surface_is_extended_not_duplicated() -> None:
    component = (ROOT / "ui/web/src/components/ModelSettingsView.ts").read_text(encoding="utf-8")
    settings = (ROOT / "ui/web/src/pages/SettingsView.ts").read_text(encoding="utf-8")
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    assert "data-multiprovider-foundation" in component
    assert "Provider, candidate y provenance" in component
    assert "SIN INFERENCIA" in component
    assert "Grounding ≠ Agentic RAG" in component
    assert "Una ruta disabled no ofrece CTA de ejecución" in component
    assert "Expert details · hashes, provenance y receipt" in component
    assert "renderModelSettingsView" in settings
    assert "settingsModelGateway" in client
    # MP-0E extends the existing GET response; no parallel provider-execution API is introduced.
    assert "/settings/multiprovider" not in client
