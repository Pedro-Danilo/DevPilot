from __future__ import annotations

import ast
import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.plugins import PluginExposureReporter, PluginStaticValidator
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_019_c_static_validator_metadata_only_install_simulation_passes() -> None:
    result = PluginStaticValidator(ROOT).validate()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-019-C"
    assert summary["plugins_total"] == 2
    assert summary["metadata_only_total"] == summary["plugins_total"]
    assert summary["install_simulated_total"] == summary["plugins_total"]
    assert summary["execution_allowed_total"] == 0
    assert summary["plugin_code_loaded"] is False
    assert summary["arbitrary_code_execution_performed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["dependencies_installed"] is False
    assert summary["marketplace_used"] is False
    assert summary["arbitrary_files_read"] is False
    assert summary["blocking_findings_total"] == 0

    for plugin in result.data["plugins"]:
        assert plugin["metadata_only"] is True
        assert plugin["install_simulated"] is True
        assert plugin["install_state"] == "metadata-only-simulated"
        assert plugin["executable_state"] == "blocked"
        assert plugin["execution_allowed"] is False
        assert plugin["plugin_code_loaded"] is False
        assert plugin["arbitrary_code_execution_performed"] is False
        assert plugin["dependencies_installed"] is False
        assert plugin["marketplace_used"] is False
        assert plugin["arbitrary_files_read"] is False


def test_post_h_019_c_exposure_report_schema_and_cli_all_write_report(capsys) -> None:
    direct = PluginExposureReporter(ROOT).build(write_report=False)
    assert direct.ok, direct.to_dict()
    report = direct.data["report"]
    schema_result = SchemaValidator(ROOT).validate_payload(
        schema="PluginSandboxDesignReport",
        payload=report,
        instance_label="in-memory-plugin-exposure-report",
    )
    assert schema_result.ok, schema_result.to_dict()
    assert report["summary"]["execution_allowed_total"] == 0
    assert report["summary"]["blocked_permissions_total"] >= 6
    assert report["summary"]["network_used"] is False
    assert report["summary"]["external_api_used"] is False
    assert report["summary"]["mutations_performed"] is False

    exit_code = cli.main(["plugin", "dry-run", "--all", "--dry-run", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    summary = payload["data"]["summary"]
    assert summary["created_by"] == "POST-H-019-C"
    assert summary["plugins_total"] == 2
    assert summary["metadata_only_total"] == 2
    assert summary["install_simulated_total"] == 2
    assert summary["execution_allowed_total"] == 0
    assert summary["plugin_code_loaded"] is False
    assert summary["arbitrary_code_execution_performed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert payload["data"]["reports"]["json"] == "outputs/reports/plugin_exposure_report.json"

    file_schema_result = SchemaValidator(ROOT).validate(
        schema="PluginSandboxDesignReport",
        instance="outputs/reports/plugin_exposure_report.json",
    )
    assert file_schema_result.ok, file_schema_result.to_dict()


def test_post_h_019_c_static_validator_source_uses_no_runtime_plugin_execution_primitives() -> None:
    source = (ROOT / "src/devpilot_core/plugins/static_validator.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module.split(".", 1)[0])
    assert "subprocess" not in imported_modules
    assert "importlib" not in imported_modules
    assert "pip" not in source.lower()
