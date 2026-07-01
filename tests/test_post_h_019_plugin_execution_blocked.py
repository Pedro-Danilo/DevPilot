from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.plugins import PluginStaticValidator, PluginStaticValidatorOptions

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_019_c_install_dry_run_blocks_importable_entrypoint() -> None:
    registry = _read_json(".devpilot/plugins/plugin_registry.json")
    bad_registry = copy.deepcopy(registry)
    bad_registry["plugins"][0]["entrypoint"] = "devpilot_malicious_plugin:main"
    bad_registry["plugins"][0]["loading_mode"] = "runtime"
    bad_registry_dir = ROOT / "outputs" / "test_tmp"
    bad_registry_dir.mkdir(parents=True, exist_ok=True)
    bad_registry_path = bad_registry_dir / "plugin_registry.importable.json"
    bad_registry_path.write_text(json.dumps(bad_registry, indent=2), encoding="utf-8")

    result = PluginStaticValidator(
        ROOT,
        options=PluginStaticValidatorOptions(registry_path=str(bad_registry_path)),
    ).validate()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    finding_ids = {finding.id for finding in result.findings}
    assert "PLUGIN_ENTRYPOINT_UNSAFE_BLOCKED" in finding_ids or "PLUGIN_STATIC_METADATA_ONLY_BLOCKED" in finding_ids
    summary = result.data["summary"]
    assert summary["plugin_code_loaded"] is False
    assert summary["arbitrary_code_execution_performed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False


def test_post_h_019_c_dry_run_all_requires_dry_run_flag(capsys) -> None:
    exit_code = cli.main(["plugin", "dry-run", "--all", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == int(ExitCode.BLOCK)
    assert payload["ok"] is False
    assert any(finding["id"] == "PLUGIN_DRY_RUN_REQUIRED" for finding in payload["findings"])
    assert payload["data"]["summary"]["plugin_code_loaded"] is False
    assert payload["data"]["summary"]["network_used"] is False
    assert payload["data"]["summary"]["external_api_used"] is False
    assert payload["data"]["summary"]["mutations_performed"] is False


def test_post_h_019_c_plugin_id_alias_keeps_single_plugin_dry_run_non_executable(capsys) -> None:
    exit_code = cli.main([
        "plugin",
        "dry-run",
        "--plugin-id",
        "local.docs.plugin",
        "--operation",
        "metadata",
        "--dry-run",
        "--json",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    summary = payload["data"]["summary"]
    assert summary["plugin_id"] == "local.docs.plugin"
    assert summary["canonical_permission_id"] == "plugin.metadata.read"
    assert summary["plugin_code_loaded"] is False
    assert summary["arbitrary_code_execution_performed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
