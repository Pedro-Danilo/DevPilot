from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import ApplicationRequest, ApplicationResponse, ApplicationService
from devpilot_core.cli_models import ExitCode

ROOT = Path(__file__).resolve().parents[1]


def test_application_service_v2_contract_lists_domain_facades() -> None:
    result = ApplicationService(ROOT).application_contract()
    payload = result.to_dict()["data"]

    assert result.ok is True
    assert payload["summary"]["schema_version"] == "2.0"
    assert payload["summary"]["application_service_v2"] is True
    assert payload["summary"]["domain_facades_enabled"] is True
    assert payload["summary"]["api_implemented"] is True
    assert payload["summary"]["ui_implemented"] is True
    assert payload["summary"]["web_ui_local_implemented"] is True
    assert payload["summary"]["desktop_deferred"] is True
    assert payload["summary"]["phase_f_closed"] is True
    assert payload["summary"]["visual_product_quality_gate"] is True

    domains = {row["domain"] for row in payload["domains"]}
    assert {
        "workspace",
        "validation",
        "miasi",
        "evals",
        "repo",
        "review",
        "refactor",
        "model",
        "history",
        "observability",
    }.issubset(domains)

    operations = {row["operation"] for row in payload["capabilities"]}
    assert "workspace.status" in operations
    assert "validation.gateway" in operations
    assert "miasi.validate" in operations
    assert "repo.inventory" in operations
    assert "review.code" in operations
    assert "refactor.plan" in operations
    assert "model.providers" in operations
    assert "observability.trace_report" in operations
    assert "validators.validate_frontmatter" in operations  # legacy alias retained
    assert json.dumps(payload, ensure_ascii=False)


def test_application_service_v2_handles_requests_as_application_response() -> None:
    service = ApplicationService(ROOT)
    response = service.handle(ApplicationRequest(operation="workspace.status", client="future-api-local"))

    assert isinstance(response, ApplicationResponse)
    assert response.operation == "workspace.status"
    assert response.ok is True
    assert response.exit_code == int(ExitCode.PASS)
    assert response.to_dict()["contract"] == "DevPilotApplicationResponse"


def test_application_service_v2_blocks_unexposed_operations() -> None:
    service = ApplicationService(ROOT)
    result = service.execute(ApplicationRequest(operation="repo.patch.apply", payload={"path": "x.patch"}))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.findings[0].id == "APPLICATION_OPERATION_NOT_EXPOSED"
    assert "repo.patch.apply" not in result.data["supported_operations"]


def test_application_service_v2_delegates_selected_domain_methods() -> None:
    service = ApplicationService(ROOT)

    readiness = service.validation.gateway(scope="docs")
    miasi = service.miasi_validate(scope="all")
    providers = service.model_providers()
    metrics = service.metrics_summary(limit=5)

    assert readiness.ok is True
    assert miasi.ok is True
    assert providers.ok is True
    assert metrics.ok is True
    assert readiness.command == "validate docs"
    assert miasi.command == "miasi validate"
    assert providers.command == "model providers"
    assert metrics.command == "metrics summary"
