from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.connectors import ConnectorSandboxPolicyValidator
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_018_a_connector_sandbox_schemas_are_registered() -> None:
    result = SchemaRegistry(ROOT).list()

    assert result.ok, result.to_dict()
    schema_ids = {schema["schema_id"] for schema in result.data["schemas"]}
    assert "SCHEMA-DEVPL-CONNECTOR-SANDBOX-POLICY-V1" in schema_ids
    assert "SCHEMA-DEVPL-CONNECTOR-REPLAY-FIXTURE-V1" in schema_ids
    assert "SCHEMA-DEVPL-CONNECTOR-SANDBOX-REPORT-V1" in schema_ids
    assert "SCHEMA-DEVPL-CONNECTOR-POLICY-EXPOSURE-REPORT-V1" in schema_ids


def test_post_h_018_a_connector_sandbox_policy_schema_validates() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="ConnectorSandboxPolicy",
        instance=".devpilot/connectors/connector_sandbox_policy.json",
    )

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["valid"] is True


def test_post_h_018_a_replay_fixture_and_report_fixtures_validate() -> None:
    replay = SchemaValidator(ROOT).validate(
        schema="ConnectorReplayFixture",
        instance="tests/fixtures/connector_replay_fixture.valid.json",
    )
    report = SchemaValidator(ROOT).validate(
        schema="ConnectorSandboxReport",
        instance="tests/fixtures/connector_sandbox_report.valid.json",
    )

    assert replay.ok, replay.to_dict()
    assert report.ok, report.to_dict()
    assert replay.data["summary"]["valid"] is True
    assert report.data["summary"]["valid"] is True


def test_post_h_018_a_policy_covers_all_registered_connectors_and_denies_write() -> None:
    result = ConnectorSandboxPolicyValidator(ROOT).validate()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-018-A"
    assert summary["policy_coverage_complete"] is True
    assert summary["connectors_total"] == summary["registry_connectors_total"]
    assert summary["network_allowed_by_default"] is False
    assert summary["external_api_allowed_by_default"] is False
    assert summary["mutation_allowed_by_default"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["connector_write_used"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False

    policy = result.data["policy"]
    assert policy["default_mode"] == "deny-write"
    assert set(policy["allowed_modes"]) == {"validate", "dry-run", "replay"}
    assert {connector["connector_id"] for connector in policy["connectors"]} == {
        "local.docs",
        "local.git.readonly",
        "mcp.local.prototype",
        "external.api.placeholder",
    }
    assert all(connector["network_allowed"] is False for connector in policy["connectors"])
    assert all(connector["external_api_allowed"] is False for connector in policy["connectors"])
    assert all(connector["mutations_allowed"] is False for connector in policy["connectors"])
    assert all(connector["write_allowed"] is False for connector in policy["connectors"])


def test_post_h_018_a_policy_blocks_missing_connector_and_write_enablement() -> None:
    policy = json.loads((ROOT / ".devpilot/connectors/connector_sandbox_policy.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / ".devpilot/connectors/connector_registry.json").read_text(encoding="utf-8"))
    bad_policy = copy.deepcopy(policy)
    bad_policy["connector_write_enabled"] = True
    bad_policy["connectors"] = bad_policy["connectors"][:-1]
    bad_policy["connectors"][0]["write_allowed"] = True

    findings = ConnectorSandboxPolicyValidator(ROOT).validate_payloads(bad_policy, registry)

    finding_ids = {finding.id for finding in findings}
    assert "CONNECTOR_SANDBOX_WRITE_ENABLED_BLOCKED" in finding_ids
    assert "CONNECTOR_SANDBOX_POLICY_COVERAGE_MISSING" in finding_ids
    assert "CONNECTOR_SANDBOX_CONNECTOR_WRITE_BLOCKED" in finding_ids
    assert any(finding.severity.value == "block" for finding in findings)


def test_post_h_018_a_docs_state_and_contracts_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-018_connector_sandbox.md").read_text(encoding="utf-8")
    post_doc = (ROOT / "docs/POST-H-018_connector_sandbox.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    source_registry = (ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8")

    assert 'status: "approved"' in backlog
    assert 'approval: "approved_by_owner"' in backlog
    assert 'implementation_status: "closed"' in backlog
    assert 'current_micro_sprint: "POST-H-018-E"' in backlog
    assert 'next_micro_sprint: "POST-H-019"' in backlog
    assert 'status: "approved"' in post_doc
    assert "POST-H-018-A — Connector sandbox policy y schemas" in backlog
    assert "POST-H-018-A — Connector sandbox policy y schemas" in post_doc
    assert "ConnectorSandboxPolicy" in readme
    assert "connector_sandbox_policy.schema.json" in runbook
    assert "post-h-018-a" in changelog
    assert state["last_completed_sprint"] == "POST-H-018"
    assert state["next_sprint"] == "POST-H-019"
    assert state["current_micro_sprint"] == "POST-H-019-C"
    assert state["next_micro_sprint"] == "POST-H-019-D"
    assert "post-h-018-connector-sandbox-policy-schemas" in tcr_v1
    assert "post-h-018-connector-sandbox-policy-schemas" in tcr_v2
    assert "post-h-018-connector-sandbox-runner" in tcr_v1
    assert "post-h-018-connector-sandbox-runner" in tcr_v2
    assert "POST-H-018-IMPLEMENTATION" in source_registry
    assert "POST-H-018-CONNECTOR-SANDBOX-POLICY" in source_registry
    assert "POST-H-018-B-CONNECTOR-SANDBOX-RUNNER-REPORT" in source_registry
    assert "POST-H-018-B-MANIFEST" in source_registry
    assert "POST-H-018-CONNECTOR-REPLAY-CASES" in source_registry
    assert "POST-H-018-C-CONNECTOR-REPLAY-REDACTION-REPORT" in source_registry
    assert "POST-H-018-C-MANIFEST" in source_registry
    assert "POST-H-018-D-CONNECTOR-POLICY-BINDING-REPORT" in source_registry
    assert "POST-H-018-D-MANIFEST" in source_registry
    assert "POST-H-018-CONNECTOR-POLICY-EXPOSURE-SCHEMA" in source_registry
    assert "post-h-018-connector-replay-redaction" in tcr_v1
    assert "post-h-018-connector-replay-redaction" in tcr_v2
    assert "post-h-018-connector-policy-binding" in tcr_v1
    assert "post-h-018-connector-policy-binding" in tcr_v2
    assert "POST-H-018-C — Replay fixtures y redacción" in readme
    assert "POST-H-018-C — Replay fixtures y redacción" in runbook
    assert "post-h-018-c" in changelog
    assert "POST-H-018-D — Policy/approval/RBAC binding para conectores" in readme
    assert "POST-H-018-D — Policy/approval/RBAC binding para conectores" in runbook
    assert "post-h-018-d" in changelog
    assert "POST-H-018-E — Quality gate, runbook y cierre" in readme
    assert "POST-H-018-E — Quality gate, runbook y cierre" in runbook
    assert "post-h-018-e" in changelog
    assert "post-h-018-connector-sandbox" in tcr_v1
    assert "post-h-018-connector-sandbox" in tcr_v2
    assert "POST-H-018-CONNECTOR-SANDBOX-RUNBOOK" in source_registry
    assert "POST-H-018-CONNECTOR-SANDBOX-THREAT-MODEL" in source_registry
    assert "POST-H-018-E-CONNECTOR-SANDBOX-GATE-REPORT" in source_registry
    assert "POST-H-018-E-MANIFEST" in source_registry
    assert "POST-H-019-PLUGIN-SANDBOX-THREAT-MODEL" in source_registry
    assert "POST-H-019-PLUGIN-SANDBOX-DESIGN" in source_registry
    assert "POST-H-019-A-MANIFEST" in source_registry
    assert "POST-H-019-PLUGIN-SANDBOX-DESIGN-REPORT-SCHEMA" in source_registry
    assert "POST-H-019-C-MANIFEST" in source_registry
