from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.observability import (
    CRITICAL_TARGETS,
    ObservabilityRetentionPolicyValidator,
    load_observability_retention_policy,
)
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_observability_retention_policy_schema_is_registered() -> None:
    catalog = read_json("docs/schemas/schema_catalog.json")
    entries = {item["schema_id"]: item for item in catalog["schemas"]}

    assert "SCHEMA-DEVPL-OBSERVABILITY-RETENTION-POLICY-V1" in entries
    entry = entries["SCHEMA-DEVPL-OBSERVABILITY-RETENTION-POLICY-V1"]
    assert entry["path"] == "docs/schemas/observability_retention_policy.schema.json"
    assert entry["contract"] == "ObservabilityRetentionPolicy"
    assert entry["sprint"] == "POST-H-010-A"
    assert (ROOT / entry["path"]).exists()

    registry_result = SchemaRegistry(ROOT).list()
    assert registry_result.ok, registry_result.to_dict()
    assert "SCHEMA-DEVPL-OBSERVABILITY-RETENTION-POLICY-V1" in {
        item["schema_id"] for item in registry_result.data["schemas"]
    }


def test_observability_retention_policy_validates_against_schema() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="ObservabilityRetentionPolicy",
        instance=".devpilot/observability/retention_policy.json",
    )

    assert result.ok, result.to_dict()
    assert result.data["summary"]["valid"] is True


def test_observability_retention_policy_loads_defaults() -> None:
    policy = load_observability_retention_policy(ROOT)
    by_target = policy.by_target_id()

    assert policy.schema_id == "SCHEMA-DEVPL-OBSERVABILITY-RETENTION-POLICY-V1"
    assert policy.created_by == "POST-H-010-A"
    assert policy.status == "approved"
    assert policy.local_first is True
    assert policy.remote_export_enabled is False
    assert policy.default_mode == "dry-run"
    assert set(by_target) >= CRITICAL_TARGETS
    assert by_target["events-jsonl"].path == "outputs/traces/events.jsonl"
    assert by_target["devpilot-db"].path == ".devpilot/devpilot.db"
    assert by_target["agent-sessions"].path == ".devpilot/agent_sessions/"
    assert by_target["generated-reports"].path == "outputs/reports/"
    assert by_target["metrics-local-store"].logical_scope == "metrics"


def test_observability_retention_policy_semantic_no_go_gates_pass() -> None:
    result = ObservabilityRetentionPolicyValidator(ROOT).validate()
    summary = result.data["summary"]

    assert result.ok, result.to_dict()
    assert summary["created_by"] == "POST-H-010-A"
    assert summary["targets_total"] >= 6
    assert summary["critical_targets_present_total"] == summary["critical_targets_total"]
    assert summary["remote_export_enabled"] is False
    assert summary["default_mode"] == "dry-run"
    assert summary["raw_prompts_allowed"] is False
    assert summary["raw_outputs_allowed"] is False
    assert summary["secrets_allowed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False


def test_runtime_targets_are_not_versionable_and_are_clean_zip_excluded() -> None:
    policy = load_observability_retention_policy(ROOT)

    for target in policy.targets:
        assert target.source_of_truth is False
        assert target.versionable is False
        assert target.raw_payload_storage_allowed is False
        if target.path.startswith("outputs/") or target.path in {".devpilot/devpilot.db", ".devpilot/agent_sessions/"}:
            assert target.clean_zip_excluded is True
        if target.contains_sensitive_payloads:
            assert target.redaction_required is True
