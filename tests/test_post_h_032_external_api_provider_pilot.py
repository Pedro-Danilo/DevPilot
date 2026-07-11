from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.application.services import ApplicationService
from devpilot_core.modeling import ExternalApiProviderPilotReporter, FakeExternalApiProvider
from devpilot_core.schemas import SchemaValidator


def test_external_api_provider_pilot_default_is_fake_and_disabled() -> None:
    result = ExternalApiProviderPilotReporter(Path.cwd()).build()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-032-C"
    assert summary["decision"] == "PASS"
    assert summary["api_enabled_total"] == 0
    assert summary["api_disabled_by_default_total"] >= 1
    assert summary["api_requires_env_var_total"] >= 1
    assert summary["api_key_values_in_repo_total"] == 0
    assert summary["fake_provider_contract_ok"] is True
    assert summary["tests_require_real_api"] is False
    assert summary["real_api_call_performed"] is False
    assert summary["external_api_used"] is False
    assert summary["network_used"] is False
    assert summary["cost_guard_blocks_accidental_external_api"] is True
    assert summary["secret_handling_env_only"] is True
    assert summary["blocking_findings_total"] == 0


def test_external_api_provider_pilot_schema_and_adr_exist() -> None:
    root = Path.cwd()
    result = ExternalApiProviderPilotReporter(root).build()

    assert (root / "docs/adr/ADR-POSTH-032-C-external-api-provider-gated-pilot.md").is_file()
    assert (root / ".devpilot/modeling/external_api_provider_pilot_policy.json").is_file()
    validation = SchemaValidator(root).validate_payload(
        schema="ExternalApiProviderPilot",
        payload=result.data["report"],
        instance_label="external-api-provider-pilot-test",
    )
    assert validation.ok is True


def test_external_api_fake_provider_contract_never_uses_network_or_secret() -> None:
    fake = FakeExternalApiProvider("openai", "gpt-placeholder")

    payload = fake.generate(prompt="safe fake provider smoke")

    assert payload["ok"] is True
    assert payload["fake_provider"] is True
    assert payload["external_api_used"] is False
    assert payload["network_used"] is False
    assert payload["api_key_read"] is False
    assert payload["raw_prompt_stored"] is False
    assert payload["raw_output_stored"] is False


def test_external_api_real_call_request_is_gated_and_blocked_without_local_opt_in() -> None:
    result = ExternalApiProviderPilotReporter(Path.cwd()).build()
    default_gate = result.data["report"]["real_call_gate"]
    assert default_gate["requested"] is False
    assert default_gate["allowed"] is False
    assert default_gate["real_call_performed"] is False

    from devpilot_core.modeling.external_api_pilot import ExternalApiProviderPilotOptions

    gated = ExternalApiProviderPilotReporter(
        Path.cwd(),
        ExternalApiProviderPilotOptions(allow_real_api=True, acknowledge_risk=True, budget_limit_usd=1.0),
    ).build()
    assert gated.ok is False
    gate = gated.data["report"]["real_call_gate"]
    assert gate["requested"] is True
    assert gate["allowed"] is False
    assert gate["real_call_performed"] is False
    assert "real_calls_not_supported_by_this_sprint" in gate["missing_gates"]
    assert any(finding.id == "EXTERNAL_API_REAL_CALL_GATED_BLOCKED" for finding in gated.findings)


def test_external_api_provider_pilot_cli_and_application_service_are_synchronized(capsys) -> None:
    service_result = ApplicationService(Path.cwd()).external_api_provider_pilot()
    assert service_result.ok is True
    assert service_result.data["summary"]["external_api_used"] is False

    exit_code = cli.main(["model", "external-api-pilot", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["created_by"] == "POST-H-032-C"
    assert payload["data"]["summary"]["external_api_used"] is False


def test_external_api_provider_pilot_write_report_outputs_only(tmp_path: Path) -> None:
    output_json = tmp_path / "external_api_provider_pilot_report.json"
    output_md = tmp_path / "external_api_provider_pilot_report.md"

    from devpilot_core.modeling.external_api_pilot import ExternalApiProviderPilotOptions

    result = ExternalApiProviderPilotReporter(
        Path.cwd(),
        ExternalApiProviderPilotOptions(write_report=True, output_json=output_json, output_markdown=output_md),
    ).build()

    assert result.ok is True
    assert output_json.is_file()
    assert output_md.is_file()
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["summary"]["reports_written"] is True
    assert payload["safety"]["read_only"] is False
    assert payload["safety"]["external_api_used"] is False
    assert payload["safety"]["network_used"] is False
