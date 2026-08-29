from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application.model_gateway_settings_service import ModelGatewaySettingsService
from devpilot_core.application.services import ApplicationService
from devpilot_core.cli_models import CommandResult, ExitCode
from devpilot_core.identity.auth_models import AuthenticatedPrincipal, SessionContext

ROOT = Path(__file__).resolve().parents[1]


def _principal(role: str = "owner") -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal("actor-gsdlc06e", "gsdlc06e", "GSDLC 06-E", (role,), ("devpilot-local",))


def _session(role: str = "owner") -> SessionContext:
    p = _principal(role)
    return SessionContext(p, "2026-08-27T00:00:00Z", "2026-08-27T00:00:00Z", "2026-08-28T00:00:00Z", 3600, 0)


def test_model_gateway_settings_projection_is_complete_redacted_and_tool_safe():
    result = ModelGatewaySettingsService(ROOT).snapshot()
    assert result.ok
    summary = result.data["summary"]
    assert summary["routes_total"] == 17
    assert summary["mock_routes_total"] == 1
    assert summary["local_routes_total"] == 4
    assert summary["external_routes_total"] == 12
    assert summary["external_runtime_network_enabled_total"] == 0
    assert summary["raw_credentials_exposed"] is False
    assert summary["tool_authority_granted"] is False
    for route in result.data["routes"]:
        assert route["provider_id"] and route["model_id"] and route["access_route_id"]
        assert "estimated_cost" in route and "request_budget" in route and "fallback_policy" in route
        assert "runtime_credential_state" in route and "runtime_credential_reference_present" in route
        assert route["tool_execution_authority"] is False
        cred = route.get("credential_reference") or {}
        assert cred.get("raw_secret_present", False) is False


def test_controlled_eval_mock_and_fake_local_are_hermetic_and_tool_safe():
    service = ModelGatewaySettingsService(ROOT)
    for mode in ("mock", "fake-local"):
        result = service.controlled_evaluation(mode=mode)
        assert result.ok, result.message
        assert result.data["summary"]["network_used"] is False
        assert result.data["summary"]["external_api_used"] is False
        assert result.data["summary"]["tool_authority_granted"] is False
        assert result.data["summary"]["estimated_total_tokens"] == 1100
        assert result.data["summary"]["request_budget_max_tokens"] == 8192
        assert result.data["decision"]["route_status"] == "selected"


def test_fake_external_is_governance_simulation_without_real_network():
    result = ModelGatewaySettingsService(ROOT).controlled_evaluation(mode="fake-external")
    assert result.ok, result.message
    assert result.data["summary"]["mode"] == "fake-external"
    assert result.data["summary"]["network_used"] is False
    assert result.data["summary"]["real_api_called"] is False
    assert result.data["summary"]["tool_authority_granted"] is False


def test_browser_hard_stop_case_blocks_before_model_call():
    result = ModelGatewaySettingsService(ROOT).controlled_evaluation(mode="mock", hard_stop_case=True)
    assert not result.ok
    assert result.data["summary"]["hard_stop_demonstrated"] is True
    assert result.data["summary"]["hard_stop_reason"] == "hard-token-budget-exceeded"
    assert result.data["summary"]["estimated_input_tokens"] == 8193
    assert result.data["summary"]["network_used"] is False
    assert result.data["decision"]["route_status"] == "blocked"
    assert any("hard-token-budget-exceeded" in json.dumps(row) for row in result.data["decision"]["decision_trace"])


def test_controlled_evaluation_application_boundary_requires_authorized_human_role():
    service = ApplicationService(ROOT)
    ok = service.settings_model_gateway_evaluate_authenticated(payload={"mode": "mock"}, principal=_principal("developer"), session=_session("developer"))
    blocked = service.settings_model_gateway_evaluate_authenticated(payload={"mode": "mock"}, principal=_principal("viewer"), session=_session("viewer"))
    assert ok.ok
    assert not blocked.ok
    assert any(f.id == "MODEL_GATEWAY_EVAL_RBAC_BLOCK" for f in blocked.findings)



def test_model_gateway_snapshot_surfaces_runtime_disable_revoke_state_without_secret_values(monkeypatch):
    service = ModelGatewaySettingsService(ROOT)
    monkeypatch.setattr(
        service.enablement,
        "status",
        lambda: CommandResult(
            command="provider enablement status",
            ok=True,
            exit_code=ExitCode.PASS,
            message="runtime state",
            data={
                "providers": [
                    {
                        "provider_id": "openai",
                        "configured_enabled": False,
                        "runtime_network_enabled": False,
                        "credential_reference": None,
                        "revoked": True,
                        "last_action": "credential-reference-revoked",
                    }
                ]
            },
        ),
    )
    result = service.snapshot()
    assert result.ok
    row = next(route for route in result.data["routes"] if route["provider_id"] == "openai")
    assert row["runtime_state_present"] is True
    assert row["runtime_credential_reference_present"] is False
    assert row["runtime_credential_state"] == "revoked"
    assert row["runtime_revoked"] is True
    assert row["runtime_last_action"] == "credential-reference-revoked"
    assert row["credential_reference"]["raw_secret_present"] is False

def test_model_gateway_api_rbac_and_ui_contract_are_registered_and_human_session_bound():
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    ui = json.loads((ROOT / ".devpilot/interfaces/ui_route_contract_registry.json").read_text(encoding="utf-8"))
    api_pairs = {(row["method"], row["path"]) for row in api["routes"]}
    assert ("GET", "/api/v1/settings/model-gateway") in api_pairs
    assert ("POST", "/api/v1/settings/model-gateway/evaluate") in api_pairs
    policies = {(row["method"], row["path"]): row for row in rbac["route_policies"]}
    for pair in (("GET", "/api/v1/settings/model-gateway"), ("POST", "/api/v1/settings/model-gateway/evaluate")):
        assert policies[pair]["human_session_required"] is True
        assert policies[pair]["legacy_token_allowed"] is False
    settings = next(row for row in ui["routes"] if row["route_id"] == "ui.settings")
    assert "api.settings.model-gateway" in settings["allowed_api_routes"]
    assert "api.settings.model-gateway.evaluate" in settings["allowed_api_routes"]
