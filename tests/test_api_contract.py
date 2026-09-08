from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.interfaces.api.contract_drift import ApiContractDriftGuard

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / "docs" / "07_interfaces" / "openapi_v1.json"
REGISTRY_PATH = ROOT / ".devpilot" / "interfaces" / "api_route_contract_registry.json"
MAPPING_PATH = ROOT / "docs" / "07_interfaces" / "api_service_mapping.md"


def _openapi() -> dict:
    return json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _route_key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def test_visual_mvp_historical_metadata_remains_preserved() -> None:
    """Historical FUNC-SPRINT-73 product facts remain frozen at top level.

    The current route-level authority is POST-H-028 ApiContractDriftGuard; old
    per-operation x-devpilot metadata is not a current-active contract.
    """

    spec = _openapi()
    meta = spec["x-devpilot"]

    assert spec["openapi"] == "3.1.0"
    assert meta["sprint"] == "FUNC-SPRINT-73"
    assert meta["status"] == "visual-mvp-closed"
    assert meta["api_implemented"] is True
    assert meta["server_implemented"] is True
    assert meta["ui_implemented"] is True
    assert meta["desktop_deferred"] is True
    assert meta["api_security_implemented"] is True
    assert meta["token_required"] is True
    assert meta["cors_wildcard_enabled"] is False
    assert meta["policy_binding_enabled"] is True
    assert meta["web_ui_mvp_implemented"] is True
    assert meta["web_ui_consumer"] == "ui/web"


def test_current_api_contract_uses_post_h_028_drift_guard() -> None:
    result = ApiContractDriftGuard(ROOT).run()
    assert result.ok is True
    summary = result.data["report"]["summary"]
    assert summary["decision"] == "PASS"
    assert summary["checks_passed"] == summary["checks_total"] == 5
    assert summary["unregistered_runtime_routes_total"] == 0
    assert summary["stale_registry_routes_total"] == 0
    assert summary["protected_routes_missing_policy_total"] == 0
    assert summary["response_contract_violations_total"] == 0
    assert summary["no_go_violations_total"] == 0
    assert summary["mutating_routes_without_justification_total"] == 0
    assert summary["openapi_extra_paths_total"] == 0
    assert summary["openapi_missing_non_public_paths_total"] == 0


def test_static_openapi_tracks_current_registry_without_false_transport_block() -> None:
    spec = _openapi()
    registry = _registry()

    static_keys = {
        _route_key(method, path)
        for path, methods in spec["paths"].items()
        for method in methods
    }
    registry_keys = {
        _route_key(route["method"], route["path"])
        for route in registry["routes"]
    }

    # FastAPI public docs/openapi transport may intentionally be absent from the
    # checked static payload. No protected route may be missing.
    optional_public_transport = {
        "GET /api/v1/docs",
        "GET /api/v1/openapi.json",
    }
    assert static_keys - registry_keys == set()
    assert (registry_keys - static_keys) <= optional_public_transport

    # GSDLC-09-D successor routes must be represented by the current static
    # OpenAPI and registry without granting source-write authority.
    for key in {
        "POST /api/v1/story/code/agent-assist/proposals",
        "GET /api/v1/story/code/agent-assist/proposals/{proposal_id}",
        "POST /api/v1/story/code/agent-assist/proposals/{proposal_id}/decision",
    }:
        assert key in static_keys
        assert key in registry_keys


def test_current_api_security_and_source_mutation_authority_are_explicit() -> None:
    registry = _registry()
    routes = registry["routes"]

    source_mutations = {
        route["route_id"]
        for route in routes
        if route.get("source_mutation_allowed") is True
    }
    assert "api.story-source-change.apply" in source_mutations
    assert "api.story-source-change.rollback" in source_mutations
    assert not any(route.get("remote_execution_allowed") for route in routes)
    assert not any(route.get("connector_write_allowed") for route in routes)
    assert not any(route.get("plugin_execution_allowed") for route in routes)
    assert not any(route.get("external_api_allowed") for route in routes)
    assert not any(route.get("destructive_action_allowed") for route in routes)

    # Agent-assist is proposal-only: all three routes are source-non-mutating.
    agent_ops = {
        "story.agent-assist.proposal.create",
        "story.agent-assist.proposal.get",
        "story.agent-assist.proposal.decision",
    }
    found = [route for route in routes if route.get("operation") in agent_ops]
    assert {route["operation"] for route in found} == agent_ops
    assert all(route.get("source_mutation_allowed") is False for route in found)
    assert all(route.get("application_service_required") is True for route in found)
    assert all(route.get("auth_required") is True for route in found)
    assert all(route.get("policy_check_required") is True for route in found)


def test_api_service_mapping_retains_governed_boundary_documentation() -> None:
    mapping = MAPPING_PATH.read_text(encoding="utf-8")
    assert "ApplicationService" in mapping
    assert "Policy/gate" in mapping
    assert "no patch execution" in mapping or "plan-only" in mapping
