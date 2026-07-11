from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.cli_registry.compatibility import CliCompatibilityContractRunner, CliCompatibilityOptions
from devpilot_core.quality import QualityGate, QualityGateOptions

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _matrix_commands() -> dict[str, dict]:
    matrix = _load(".devpilot/cli_registry/command_ownership_matrix.json")
    return {item["command_id"]: item for item in matrix["commands"]}


def _contracts() -> dict[str, dict]:
    fixture = _load(".devpilot/cli_registry/cli_compatibility_contracts.json")
    return {item["command_id"]: item for item in fixture["contracts"]}


def test_post_h_030_e_fixture_covers_migrated_and_high_risk_commands() -> None:
    commands = _matrix_commands()
    contracts = _contracts()
    required = {
        command_id
        for command_id, item in commands.items()
        if item["migration_state"] == "already-migrated" or item["risk_level"] in {"high", "critical"}
    }
    required.update({"cli-registry.guard", "cli-registry.compatibility", "quality-gate.run"})

    assert required <= set(contracts)
    assert len(contracts) >= len(required)
    assert contracts["cli-registry.compatibility"]["tier"] == "tier_0"
    assert contracts["industrial-readiness.production-ready-local"]["tier"] == "tier_0"
    assert contracts["release.manifest"]["tier"] == "tier_0"
    assert contracts["workspace.bootstrap"]["tier"] == "tier_0"


def test_post_h_030_e_contracts_preserve_json_exit_help_and_normalization_policy() -> None:
    contracts = _contracts()
    required_envelope = {"command", "ok", "exit_code", "message", "data", "findings"}
    required_normalization = {"timestamp_fields", "path_fields", "duration_fields", "volatile_metadata_fields"}

    for command_id, contract in contracts.items():
        assert contract["contract_id"] == f"cli-compat:{command_id}"
        assert required_envelope <= set(contract["json_contract"]["required_top_level_keys"])
        assert {0, 1, 2, 3} <= set(contract["exit_code_contract"]["allowed_exit_codes"])
        assert contract["help_contract"]["required_tokens"]
        assert required_normalization <= set(contract["normalization"])
        assert contract["safety"]["network_allowed"] is False
        assert contract["safety"]["external_api_allowed"] is False
        assert contract["safety"]["remote_execution_allowed"] is False
        assert contract["safety"]["connector_write_allowed"] is False
        assert contract["safety"]["plugin_execution_allowed"] is False
        assert contract["safety"]["destructive_execution_allowed"] is False


def test_post_h_030_e_runner_static_validation_passes() -> None:
    result = CliCompatibilityContractRunner(ROOT).run()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["quality_gate_subgate"] == "cli-boundary-hotspot-reduction"
    assert summary["missing_required_contracts_total"] == 0
    assert summary["unsafe_contracts_total"] == 0
    assert summary["non_normalized_contracts_total"] == 0
    assert summary["json_envelope_incomplete_total"] == 0
    assert summary["blocking_findings_total"] == 0
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False


def test_post_h_030_e_cli_command_and_schema_validation_pass(tmp_path: Path) -> None:
    output_json = Path("outputs/test_post_h_030_e/cli_compatibility_report.json")
    output_md = Path("outputs/test_post_h_030_e/cli_compatibility_report.md")
    result = CliCompatibilityContractRunner(
        ROOT,
        CliCompatibilityOptions(write_report=True, output_json=output_json, output_markdown=output_md),
    ).run()

    assert result.ok is True, result.to_dict()
    assert (ROOT / output_json).exists()
    assert (ROOT / output_md).exists()

    exit_code = cli.main(["schema", "validate", "--schema-id", "CliCompatibilityReport", "--instance", str(output_json), "--json"])
    assert exit_code == 0

    cli_exit = cli.main(["cli-registry", "compatibility", "--json"])
    assert cli_exit == 0


def test_post_h_030_e_quality_gate_subgate_is_registered() -> None:
    gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    subgate_ids = [item.id for item in gate._subgates()]

    assert "cli-boundary-hotspot-reduction" in subgate_ids


def test_post_h_030_e_governance_artifacts_are_synchronized() -> None:
    state = _load(".devpilot/project_state.json")
    source_registry = _load(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = _load(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _load(".devpilot/testing/test_contract_registry_v2.json")
    catalog = _load("docs/schemas/schema_catalog.json")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-030_cli_hotspot_reduction_application_boundaries.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    assert state["current_micro_sprint"] in {"POST-H-031-A", "POST-H-031-B", "POST-H-031-C", "POST-H-031-D", "POST-H-031-E", "POST-H-032-A", "POST-H-032-B", "POST-H-032-C", "POST-H-032-D", "POST-H-032-E", "POST-H-032-F", "POST-H-032-G", "POST-H-032-H", "POST-H-033-A", "POST-H-033-B"}
    assert state["next_micro_sprint"] in {"POST-H-031-B", "POST-H-031-C", "POST-H-031-D", "POST-H-031-E", "POST-H-032-A", "POST-H-032-B", "POST-H-032-C", "POST-H-032-D", "POST-H-032-E", "POST-H-032-F", "POST-H-032-G", "POST-H-032-H", "POST-H-033-A", "POST-H-033-B"}
    assert state["current_repo"] in {"repo_DevPilot_Local_289_POST_H_031_A.zip", "repo_DevPilot_Local_290_POST_H_031_B.zip", "repo_DevPilot_Local_291_POST_H_031_C.zip", "repo_DevPilot_Local_292_POST_H_031_D.zip", "repo_DevPilot_Local_293_POST_H_031_E.zip", "repo_DevPilot_Local_294_POST_H_032_A.zip", "repo_DevPilot_Local_295_POST_H_032_B.zip", "repo_DevPilot_Local_296_POST_H_032_C.zip", "repo_DevPilot_Local_297_POST_H_032_D.zip", "repo_DevPilot_Local_298_POST_H_032_E.zip", "repo_DevPilot_Local_299_POST_H_032_F.zip", "repo_DevPilot_Local_300_POST_H_032_G.zip", "repo_DevPilot_Local_301_POST_H_032_H.zip", "repo_DevPilot_Local_302_POST_H_033_A.zip"}
    assert state["post_h_030_status"] == "closed/cli-boundary-hotspot-reduction"
    assert state["post_h_030_cli_compatibility_contracts_available"] is True
    assert state["post_h_030_cli_compatibility_quality_gate_enabled"] is True
    assert state["post_h_030_closed"] is True

    assert 'current_micro_sprint: "POST-H-030-E"' in backlog
    assert 'next_micro_sprint: "POST-H-031-A"' in backlog
    assert 'implementation_status: "closed/cli-boundary-hotspot-reduction"' in backlog
    assert "POST-H-030-E — CLI compatibility contract tests" in readme
    assert "POST-H-030-E — CLI compatibility contract tests" in runbook
    assert "post-h-030-e" in changelog.lower()
    assert "actualizar snapshots" in backlog.lower()
    assert "no ocultar breaking changes" in backlog.lower()

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-030-E-CLI-COMPATIBILITY-CONTRACTS" in doc_ids
    assert "POST-H-030-E-CLI-COMPATIBILITY-SCHEMA" in doc_ids
    assert "POST-H-030-E-CLI-COMPATIBILITY-REPORT" in doc_ids
    assert "POST-H-030-E-MANIFEST" in doc_ids
    assert "POST-H-030-E-CLI-COMPATIBILITY-TEST" in doc_ids

    schema_ids = {item["schema_id"] for item in catalog["schemas"]}
    assert "SCHEMA-DEVPL-CLI-COMPATIBILITY-REPORT-V1" in schema_ids

    assert any(c["contract_id"] == "post-h-030-cli-compatibility-contracts" for c in tcr_v1["contracts"])
    contract_v2 = next(c for c in tcr_v2["contracts"] if c["contract_id"] == "post-h-030-cli-compatibility-contracts")
    assert contract_v2["subgate_id"] == "cli-boundary-hotspot-reduction"
    assert "SCHEMA-DEVPL-CLI-COMPATIBILITY-REPORT-V1" in contract_v2["schema_ids"]


def test_post_h_030_e_cli_registry_guard_still_passes() -> None:
    exit_code = cli.main(["cli-registry", "guard", "--json"])

    assert exit_code == 0
