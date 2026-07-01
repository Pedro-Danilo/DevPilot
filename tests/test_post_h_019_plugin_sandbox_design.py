from __future__ import annotations

import json
import re
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.plugins import PluginRegistry
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict[str, str]:
    assert text.startswith("---")
    raw = text.split("---", 2)[1]
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields


def test_post_h_019_backlog_is_approved_and_tracks_micro_sprint() -> None:
    backlog = _read("docs/backlogs/POST-H-019_plugin_sandbox_design.md")
    implementation = _read("docs/POST-H-019_plugin_sandbox_design.md")
    state = json.loads(_read(".devpilot/project_state.json"))

    backlog_fm = _frontmatter(backlog)
    implementation_fm = _frontmatter(implementation)

    assert backlog_fm["status"] == "approved"
    assert backlog_fm["approval"] == "approved_by_owner"
    assert backlog_fm["implementation_status"] == "active"
    assert backlog_fm["current_micro_sprint"] == "POST-H-019-D"
    assert backlog_fm["next_micro_sprint"] == "POST-H-019-E"
    assert implementation_fm["doc_id"] == "POST-H-019-IMPLEMENTATION"
    assert implementation_fm["status"] == "approved"
    assert state["last_completed_sprint"] == "POST-H-018"
    assert state["next_sprint"] == "POST-H-019"
    assert state["current_micro_sprint"] == "POST-H-019-D"
    assert state["next_micro_sprint"] == "POST-H-019-E"


def test_post_h_019_a_threat_model_covers_required_plugin_risks() -> None:
    threat_model = _read("docs/03_security/plugin_sandbox_threat_model.md")
    fm = _frontmatter(threat_model)

    assert fm["doc_id"] == "POST-H-019-PLUGIN-SANDBOX-THREAT-MODEL"
    assert fm["status"] == "approved"
    assert fm["approval"] == "approved_by_owner"
    assert len(set(re.findall(r"PLG-T\d{2}", threat_model))) >= 10
    for required in [
        "Arbitrary code execution",
        "Dependency confusion",
        "Secret exfiltration",
        "Path traversal",
        "Persistencia local",
        "Network abuse",
        "Sandbox escape",
        "filesystem_write_allowed=false",
        "NO-GO si plugin_execution_allowed=true",
    ]:
        assert required in threat_model


def test_post_h_019_a_sandbox_design_is_metadata_only_and_non_executable() -> None:
    design = _read("docs/02_architecture/plugin_sandbox_design.md")
    fm = _frontmatter(design)

    assert fm["doc_id"] == "POST-H-019-PLUGIN-SANDBOX-DESIGN"
    assert fm["status"] == "approved"
    for invariant in [
        "plugin_execution_allowed=false",
        "dynamic_import_allowed=false",
        "subprocess_allowed=false",
        "network_allowed=false",
        "external_api_allowed=false",
        "filesystem_write_allowed=false",
        "pip_install_allowed=false",
        "marketplace_enabled=false",
        "metadata_only=true",
        "validator_only=true",
        "registered != installable != executable",
    ]:
        assert invariant in design
    assert "BLOCK si el diseño habilita ejecución" in design
    assert "ADR futura" in design


def test_post_h_019_a_manifest_and_governance_sources_are_synchronized() -> None:
    manifest = json.loads(_read("docs/post_h_019_a_manifest.json"))
    registry = _read(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = _read(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _read(".devpilot/testing/test_contract_registry_v2.json")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    changelog = _read("docs/release/CHANGELOG.md")

    schema_result = SchemaValidator(ROOT).validate(schema="PostHManifest", instance="docs/post_h_019_a_manifest.json")
    assert schema_result.ok, schema_result.to_dict()
    assert manifest["created_by"] == "POST-H-019-A"
    assert manifest["plugin_execution_enabled"] is False
    for doc_id in [
        "POST-H-019-IMPLEMENTATION",
        "POST-H-019-PLUGIN-SANDBOX-THREAT-MODEL",
        "POST-H-019-PLUGIN-SANDBOX-DESIGN",
        "POST-H-019-A-PLUGIN-SANDBOX-DESIGN-REPORT",
        "POST-H-019-A-MANIFEST",
    ]:
        assert doc_id in registry
    assert "post-h-019-plugin-sandbox-design" in tcr_v1
    assert "post-h-019-plugin-sandbox-design" in tcr_v2
    assert "POST-H-019-A — Threat model y sandbox design" in readme
    assert "POST-H-019-A — Threat model y sandbox design" in runbook
    assert "post-h-019-a" in changelog


def test_post_h_019_a_plugin_registry_remains_non_executable(capsys) -> None:
    result = PluginRegistry(ROOT).validate()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["plugin_code_loaded"] is False
    assert summary["arbitrary_code_execution_performed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["shell_used"] is False
    assert summary["remote_execution_used"] is False

    exit_code = cli.main(["plugin", "validate", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["plugin_code_loaded"] is False
