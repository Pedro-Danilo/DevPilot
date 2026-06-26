from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_runtime_state_policy_schema_validates_policy() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="RuntimeStatePolicy",
        instance=".devpilot/runtime_state_policy.json",
    )

    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["valid"] is True
    assert result.data["summary"]["errors_total"] == 0


def test_runtime_state_policy_enforces_clean_zip_and_cleanup_safety() -> None:
    policy = read_json(".devpilot/runtime_state_policy.json")
    must_exclude = set(policy["zip_hygiene"]["must_exclude"])
    classes = {item["class_id"]: item for item in policy["artifact_classes"]}

    assert policy["policy_id"] == "devpilot-runtime-state-policy"
    assert policy["created_by"] == "POST-H-008-A"
    assert policy["default_mode"] == "dry-run"
    assert policy["safety"]["destructive_cleanup_default"] is False
    assert policy["safety"]["requires_execute_flag"] is True
    assert policy["safety"]["source_of_truth_never_delete"] is True
    assert policy["safety"]["network_required"] is False
    assert policy["safety"]["external_api_required"] is False
    assert policy["safety"]["remote_backup_enabled"] is False

    assert "outputs/" in must_exclude
    assert ".devpilot/devpilot.db" in must_exclude
    assert ".devpilot/agent_sessions/" in must_exclude
    assert ".pytest_cache/" in must_exclude
    assert "__pycache__/" in must_exclude
    assert policy["zip_hygiene"]["git_archive_required"] is True
    assert policy["zip_hygiene"]["clean_zip_required"] is True
    assert policy["zip_hygiene"]["runtime_artifacts_allowed_in_release_zip"] is False

    for class_id in ["source-code", "engineering-docs", "runtime-policy", "release-evidence"]:
        assert classes[class_id]["source_of_truth"] is True
        assert classes[class_id]["cleanup_allowed"] is False
        assert classes[class_id]["never_delete"] is True

    for class_id in ["generated-reports", "trace-events", "eval-outputs", "draft-outputs", "agent-sessions"]:
        assert classes[class_id]["source_of_truth"] is False
        assert classes[class_id]["versionable"] is False

    assert classes["local-db"]["versionable"] is False
    assert classes["local-db"]["cleanup_allowed"] is False
    assert classes["rag-index"]["classification"] == "conditional-source"


def test_runtime_state_inventory_schema_accepts_minimal_read_only_payload() -> None:
    payload = {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-RUNTIME-STATE-INVENTORY-V1",
        "inventory_id": "synthetic-runtime-state-inventory",
        "generated_at_utc": "2026-06-25T00:00:00Z",
        "policy_id": "devpilot-runtime-state-policy",
        "artifacts_total": 0,
        "by_class": {},
        "violations": [],
        "summary": {
            "policy_loaded": True,
            "read_only": True,
            "blocking_violations_total": 0,
            "warnings_total": 0,
            "preliminary": True,
        },
        "safety": {
            "mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
            "destructive_cleanup_performed": False,
        },
    }

    result = SchemaValidator(ROOT).validate_payload(
        schema="RuntimeStateInventory",
        payload=payload,
        instance_label="memory:runtime-state-inventory",
    )

    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["valid"] is True
    assert result.data["summary"]["errors_total"] == 0
