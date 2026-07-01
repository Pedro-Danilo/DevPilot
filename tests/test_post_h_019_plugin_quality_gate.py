from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.plugins import PluginSandboxQualityGate, PluginSandboxQualityGateOptions
from devpilot_core.quality import QualityGate, QualityGateOptions

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_019_d_plugin_sandbox_quality_gate_passes_metadata_only() -> None:
    result = PluginSandboxQualityGate(ROOT).run()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["quality_gate_subgate"] == "plugin-sandbox-design"
    assert summary["quality_gate_evaluates_plugin_registry"] is True
    assert summary["quality_gate_evaluates_permission_model"] is True
    assert summary["quality_gate_evaluates_exposure_report"] is True
    assert summary["plugin_ecosystem_eval_signal_present"] is True
    assert summary["plugin_ecosystem_suite_id"] == "plugin-ecosystem"
    assert summary["plugin_ecosystem_cases_total"] >= 4
    assert summary["plugin_execution_allowed"] is False
    assert summary["dynamic_import_allowed"] is False
    assert summary["subprocess_allowed"] is False
    assert summary["network_allowed"] is False
    assert summary["external_api_allowed"] is False
    assert summary["filesystem_write_allowed"] is False
    assert summary["pip_install_allowed"] is False
    assert summary["marketplace_enabled"] is False
    assert summary["plugin_code_loaded"] is False
    assert summary["arbitrary_code_execution_performed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["execution_allowed_total"] == 0
    assert summary["all_plugin_manifests_metadata_only"] is True
    assert summary["blocking_findings_total"] == 0


def test_post_h_019_d_quality_gate_profiles_register_plugin_subgate() -> None:
    for profile in ("hardening", "industrial"):
        gate = QualityGate(ROOT, options=QualityGateOptions(profile=profile))
        subgates = {subgate.id: subgate for subgate in gate._subgates()}

        assert "plugin-sandbox-design" in subgates
        assert subgates["plugin-sandbox-design"].critical is True

    result = subgates["plugin-sandbox-design"].runner()
    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["quality_gate_subgate"] == "plugin-sandbox-design"


def test_post_h_019_d_quality_gate_blocks_unsafe_permission_model(tmp_path: Path) -> None:
    unsafe_model = json.loads((ROOT / ".devpilot/plugins/plugin_permission_model.json").read_text(encoding="utf-8"))
    unsafe_model["plugin_execution_allowed"] = True
    unsafe_model["dynamic_import_allowed"] = True
    unsafe_model["permissions"][2]["effect"] = "allow"
    model_path = tmp_path / "plugin_permission_model.json"
    model_path.write_text(json.dumps(unsafe_model, indent=2), encoding="utf-8")

    result = PluginSandboxQualityGate(
        ROOT,
        options=PluginSandboxQualityGateOptions(permission_model_path=str(model_path)),
    ).run()

    assert result.ok is False
    finding_ids = {finding.id for finding in result.findings}
    assert "PLUGIN_SANDBOX_EXECUTION_ENABLED_BLOCKED" in finding_ids
    assert "PLUGIN_SANDBOX_UNSAFE_FLAG_BLOCKED" in finding_ids


def test_post_h_019_d_quality_gate_module_has_no_plugin_execution_loaders() -> None:
    source = (ROOT / "src/devpilot_core/plugins/quality_gate.py").read_text(encoding="utf-8")

    assert "import importlib" not in source
    assert "import subprocess" not in source
    assert "subprocess.run" not in source
    assert "PluginExposureReporter" in source
    assert "PluginRegistry" in source
    assert "PluginPermissionModel" in source
    assert "write_report=False" in source
