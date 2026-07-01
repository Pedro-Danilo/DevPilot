from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.remote import RemoteRunnerRegistry, RemoteRunnerStub

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


FORBIDDEN_TRUE_FLAGS = {
    "remote_runner_enabled",
    "remote_execution_used",
    "network_required",
    "external_api_required",
    "secrets_required",
    "credentials_required",
    "mutations_performed",
    "source_mutations_performed",
    "connector_write_enabled",
    "plugin_execution_enabled",
}


def test_remote_readiness_criteria_declares_design_only_disabled_baseline() -> None:
    criteria = _read_json(".devpilot/remote/remote_readiness_criteria.json")

    assert criteria["schema_id"] == "SCHEMA-DEVPL-REMOTE-READINESS-CRITERIA-V1"
    assert criteria["created_by"] == "POST-H-021-A"
    assert criteria["decision_status"] == "design-only"
    assert criteria["remote_execution_allowed"] is False
    assert criteria["remote_runner_enabled"] is False
    assert criteria["requires_future_adr"] is True
    assert len(criteria["required_before_enablement"]) >= 6
    assert "secure_transport_design" in criteria["required_before_enablement"]
    assert "approval_rbac_hardening" in criteria["required_before_enablement"]
    assert "remote_execution_quality_gate" in criteria["required_before_enablement"]

    no_go_gates = criteria["no_go_gates"]
    for flag in FORBIDDEN_TRUE_FLAGS:
        assert no_go_gates[flag] is False, flag

    safety = criteria["safety"]
    assert safety["local_first"] is True
    assert safety["dry_run"] is True
    assert safety["read_only_baseline"] is True
    assert safety["network_used"] is False
    assert safety["external_api_used"] is False
    assert safety["remote_execution_used"] is False
    assert safety["credentials_required"] is False
    assert safety["secrets_read"] is False


def test_remote_readiness_schema_requires_blocking_const_false_flags() -> None:
    schema = _read_json("docs/schemas/remote_readiness_criteria.schema.json")
    properties = schema["properties"]

    assert properties["remote_execution_allowed"]["const"] is False
    assert properties["remote_runner_enabled"]["const"] is False
    assert properties["requires_future_adr"]["const"] is True

    for flag in FORBIDDEN_TRUE_FLAGS:
        assert properties["no_go_gates"]["properties"][flag]["const"] is False, flag

    safety_properties = properties["safety"]["properties"]
    assert safety_properties["network_used"]["const"] is False
    assert safety_properties["external_api_used"]["const"] is False
    assert safety_properties["remote_execution_used"]["const"] is False
    assert safety_properties["credentials_required"]["const"] is False
    assert safety_properties["secrets_read"]["const"] is False


def test_remote_runner_existing_registry_remains_disabled_and_local_only() -> None:
    registry = _read_json(".devpilot/remote/runner_registry.json")
    security = registry["security"]

    assert security["local_first"] is True
    assert security["remote_runner_enabled"] is False
    assert security["execution_allowed"] is False
    assert security["remote_execution_used"] is False
    assert security["cloud_control_plane_enabled"] is False
    assert security["network_used"] is False
    assert security["external_api_used"] is False
    assert security["shell_allowed"] is False
    assert security["arbitrary_command_execution_allowed"] is False
    assert security["credentials_required"] is False
    assert security["secrets_read"] is False

    assert registry["runners"]
    for runner in registry["runners"]:
        assert runner["status"] == "disabled"
        assert runner["execution_allowed"] is False
        assert runner["network_allowed"] is False
        assert runner["external_api_allowed"] is False
        assert runner["cloud_allowed"] is False
        assert runner["requires_credentials"] is False
        assert runner["max_autonomy"] == "A0"


def test_remote_runner_stub_blocks_execute_without_network_or_mutation() -> None:
    result = RemoteRunnerStub(ROOT).execute(runner_id="experimental-disabled", command="echo should-not-run")

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "REMOTE_RUNNER_EXECUTION_BLOCKED" for finding in result.findings)
    summary = result.data["summary"]
    assert summary["remote_runner_enabled"] is False
    assert summary["execution_allowed"] is False
    assert summary["remote_execution_used"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False


def test_remote_registry_validator_blocks_accidental_enablement(tmp_path: Path) -> None:
    registry = _read_json(".devpilot/remote/runner_registry.json")
    mutated = deepcopy(registry)
    mutated["security"]["remote_runner_enabled"] = True
    mutated["security"]["execution_allowed"] = True

    remote_dir = tmp_path / ".devpilot" / "remote"
    schema_dir = tmp_path / "docs" / "schemas"
    remote_dir.mkdir(parents=True)
    schema_dir.mkdir(parents=True)
    (remote_dir / "runner_registry.json").write_text(json.dumps(mutated, indent=2), encoding="utf-8")
    (schema_dir / "remote_runner.schema.json").write_text(
        (ROOT / "docs/schemas/remote_runner.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (schema_dir / "schema_catalog.json").write_text(
        json.dumps(
            {
                "schemas": [
                    {
                        "schema_id": "SCHEMA-DEVPL-REMOTE-RUNNER-REGISTRY-V1",
                        "title": "RemoteRunnerRegistry",
                        "version": "1.0.0",
                        "path": "docs/schemas/remote_runner.schema.json",
                        "description": "Synthetic remote runner schema entry.",
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = RemoteRunnerRegistry(tmp_path).validate()

    assert result.ok is False
    assert any(
        finding.id in {"SCHEMA_VALIDATION_ERROR", "REMOTE_RUNNER_UNSAFE_FLAG_BLOCKED"}
        for finding in result.findings
    )
