from __future__ import annotations

from pathlib import Path

from devpilot_core.application import (
    APPLICATION_BOUNDARY_POLICY_REPORT_ID,
    POST_H_007_D_CREATED_BY,
    ApplicationBoundaryPolicy,
    ApplicationRequest,
    ApplicationService,
    InterfaceClient,
    application_boundary_policy_report,
    normalize_interface_client,
)
from devpilot_core.cli_models import ExitCode

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_007_d_boundary_policy_report_declares_clients_and_rules() -> None:
    report = application_boundary_policy_report(ROOT)

    assert report["report_id"] == APPLICATION_BOUNDARY_POLICY_REPORT_ID
    assert report["created_by"] == POST_H_007_D_CREATED_BY
    assert report["status"] == "implemented-initial"
    assert report["clients"] == ["cli", "api", "ui", "automation", "internal"]
    assert report["summary"]["rules_total"] >= 35
    assert report["summary"]["api_allowed_total"] > 0
    assert report["summary"]["ui_allowed_total"] > 0
    assert report["summary"]["sensitive_operations_total"] > 0
    assert report["summary"]["dry_run_default"] is True
    assert report["summary"]["remote_execution_enabled"] is False
    assert report["summary"]["connector_write_enabled"] is False
    assert report["summary"]["plugin_execution_enabled"] is False
    assert "workspace.status" in report["allowed_by_client"]["api"]
    assert "workspace.status" in report["allowed_by_client"]["ui"]


def test_post_h_007_d_api_and_ui_block_operations_without_explicit_exposure() -> None:
    service = ApplicationService(ROOT)

    for client in (InterfaceClient.API.value, InterfaceClient.UI.value):
        response = service.handle(ApplicationRequest(operation="validation.docs", client=client, dry_run=True))
        payload = response.to_dict()

        assert response.ok is False
        assert response.exit_code == int(ExitCode.BLOCK)
        assert payload["operation"] == "validation.docs"
        assert payload["findings"][0]["id"] == "APPLICATION_BOUNDARY_OPERATION_NOT_ALLOWED"
        assert payload["data"]["summary"]["interface_guardrail_applied"] is True


def test_post_h_007_d_api_can_execute_declared_read_only_operation() -> None:
    service = ApplicationService(ROOT)

    response = service.handle(ApplicationRequest(operation="workspace.status", client="api", dry_run=True))
    payload = response.to_dict()

    assert response.ok is True
    assert response.exit_code == int(ExitCode.PASS)
    assert payload["operation"] == "workspace.status"
    assert isinstance(payload["data"], dict)


def test_post_h_007_d_sensitive_operations_require_policy_and_preserve_dry_run() -> None:
    policy = ApplicationBoundaryPolicy(ROOT)

    allowed = policy.evaluate(ApplicationRequest(operation="ui.actions.dry_run", payload={"action_id": "readiness"}, client="ui", dry_run=True))
    assert allowed.allowed is True
    assert allowed.policy_checked is True
    assert allowed.rule is not None
    assert allowed.rule.policy_required is True

    blocked = policy.evaluate(ApplicationRequest(operation="ui.actions.dry_run", payload={"action_id": "readiness"}, client="ui", dry_run=False))
    result = blocked.to_command_result().to_dict()
    assert blocked.allowed is False
    assert result["findings"][0]["id"] == "APPLICATION_BOUNDARY_DRY_RUN_REQUIRED"
    assert result["data"]["summary"]["dry_run_guardrail_applied"] is True


def test_post_h_007_d_unknown_local_clients_are_internal_compatible_not_public() -> None:
    service = ApplicationService(ROOT)

    assert normalize_interface_client("post-h-007-c-test") == "internal"
    response = service.handle(ApplicationRequest(operation="validation.docs", client="post-h-007-c-test", dry_run=True))

    assert response.operation == "validation.docs"
    assert response.exit_code in {int(ExitCode.PASS), int(ExitCode.FAIL), int(ExitCode.BLOCK), int(ExitCode.ERROR)}
