from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.plugins import PluginPermissionModel, PluginRegistry, PluginRegistryOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_019_b_permission_model_schema_and_semantics_pass() -> None:
    schema_result = SchemaValidator(ROOT).validate(
        schema="PluginPermissionModel",
        instance=".devpilot/plugins/plugin_permission_model.json",
    )
    assert schema_result.ok, schema_result.to_dict()

    result = PluginPermissionModel(ROOT).validate()
    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-019-B"
    assert summary["default_effect"] == "deny"
    assert summary["unknown_permissions_effect"] == "deny"
    assert summary["plugin_execution_allowed"] is False
    assert summary["dynamic_import_allowed"] is False
    assert summary["subprocess_allowed"] is False
    assert summary["network_allowed"] is False
    assert summary["filesystem_write_allowed"] is False
    assert summary["blocked_permissions_total"] >= 6
    assert summary["blocking_findings_total"] == 0

    model = _read_json(".devpilot/plugins/plugin_permission_model.json")
    permissions = {item["permission_id"]: item for item in model["permissions"]}
    assert permissions["plugin.code.execute"]["effect"] == "deny"
    assert permissions["plugin.code.execute"]["risk_level"] == "critical"
    assert permissions["plugin.code.execute"]["requires_approval"] is True
    assert permissions["plugin.code.execute"]["blocked_until"] == "future-adr"


def test_post_h_019_b_plugin_registry_is_bound_to_permission_model() -> None:
    result = PluginRegistry(ROOT).validate()
    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["permission_model_valid"] is True
    assert summary["permission_model_path"] == ".devpilot/plugins/plugin_permission_model.json"
    assert summary["unknown_permissions_effect"] == "deny"
    assert summary["blocked_findings_total"] == 0

    registry = _read_json(".devpilot/plugins/plugin_registry.json")
    assert registry["permission_model_path"] == ".devpilot/plugins/plugin_permission_model.json"
    assert registry["defaults"]["permission_model_required"] is True
    assert registry["defaults"]["unknown_permissions_effect"] == "deny"
    assert registry["defaults"]["critical_permissions_require_future_adr"] is True
    for flag in [
        "dynamic_import_allowed",
        "subprocess_allowed",
        "filesystem_write_allowed",
        "pip_install_allowed",
        "marketplace_enabled",
    ]:
        assert registry["security"][flag] is False

    declared_permissions = {
        permission["permission_id"]
        for plugin in registry["plugins"]
        for permission in plugin["permissions"]
    }
    assert declared_permissions <= {"plugin.metadata.read", "plugin.connector.read"}
    assert "plugin.code.execute" not in declared_permissions


def test_post_h_019_b_unknown_manifest_permission_blocks(tmp_path: Path) -> None:
    registry = _read_json(".devpilot/plugins/plugin_registry.json")
    bad_registry = copy.deepcopy(registry)
    bad_registry["plugins"][0]["permissions"][0]["permission_id"] = "plugin.unknown.permission"
    bad_registry_dir = ROOT / "outputs" / "test_tmp"
    bad_registry_dir.mkdir(parents=True, exist_ok=True)
    bad_registry_path = bad_registry_dir / "plugin_registry.bad.json"
    bad_registry_path.write_text(json.dumps(bad_registry, indent=2), encoding="utf-8")

    result = PluginRegistry(
        ROOT,
        options=PluginRegistryOptions(registry_path=str(bad_registry_path)),
    ).validate()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "PLUGIN_PERMISSION_UNKNOWN_BLOCKED" for finding in result.findings)


def test_post_h_019_b_execution_permission_in_manifest_blocks(tmp_path: Path) -> None:
    registry = _read_json(".devpilot/plugins/plugin_registry.json")
    bad_registry = copy.deepcopy(registry)
    bad_registry["plugins"][0]["permissions"].append(
        {
            "permission_id": "plugin.code.execute",
            "capability": "Attempt to execute plugin code.",
            "description": "This synthetic permission must never be accepted by metadata-only manifests.",
            "side_effect": "execute",
            "allowed": True,
            "policy_rule_ids": ["PLUGIN_EXECUTE_DENY"],
        }
    )
    bad_registry_dir = ROOT / "outputs" / "test_tmp"
    bad_registry_dir.mkdir(parents=True, exist_ok=True)
    bad_registry_path = bad_registry_dir / "plugin_registry.execute.json"
    bad_registry_path.write_text(json.dumps(bad_registry, indent=2), encoding="utf-8")

    result = PluginRegistry(
        ROOT,
        options=PluginRegistryOptions(registry_path=str(bad_registry_path)),
    ).validate()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    finding_ids = {finding.id for finding in result.findings}
    assert "PLUGIN_PERMISSION_DENIED_REQUESTED_BLOCKED" in finding_ids or "SCHEMA_VALIDATION_ERROR" in finding_ids


def test_post_h_019_b_dry_run_accepts_legacy_metadata_alias(capsys) -> None:
    exit_code = cli.main(["plugin", "dry-run", "--plugin", "local.docs.plugin", "--operation", "metadata", "--dry-run", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["operation_id"] == "metadata"
    assert payload["data"]["summary"]["canonical_permission_id"] == "plugin.metadata.read"
    assert payload["data"]["summary"]["plugin_code_loaded"] is False
    assert payload["data"]["summary"]["arbitrary_code_execution_performed"] is False
    assert payload["data"]["summary"]["network_used"] is False
