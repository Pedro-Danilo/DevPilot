from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B_INITIAL_GROUPS = {
    "workspace",
    "standards",
    "schema",
    "validate",
    "project-state",
    "test-contracts",
    "quality-gate",
    "industrial-readiness",
}
CURRENT_DECLARATIVE_GROUPS = {
    *B_INITIAL_GROUPS,
    "cli-registry",
    "runtime-state",
    "docs-governance",
    "observability",
    "api",
    "operator",
    "portfolio",
    "audit-pack",
    "release",
    "enterprise",
}


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _registry_result():
    from devpilot_core.cli_registry.report import CliCommandRegistryReportBuilder

    return CliCommandRegistryReportBuilder(ROOT).build()


def _commands_by_id() -> dict[str, dict]:
    registry = _registry_result().data["registry"]
    return {command["command_id"]: command for group in registry["groups"] for command in group["commands"]}


def test_post_h_006_b_declarative_overlay_registers_initial_groups_and_coverage() -> None:
    result = _registry_result()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    registry = result.data["registry"]
    groups = {group["group_id"]: group for group in registry["groups"]}

    assert registry["created_by"] == "POST-H-006-E"
    assert registry["generated_from"] == "static-cli-parser-ast-plus-declarative-descriptors-plus-migrated-handlers-plus-hotspot-ownership-report-plus-no-growth-gate"
    assert registry["metadata"]["handler_migration_performed"] is True
    assert summary["declarative_registered_groups_total"] == len(CURRENT_DECLARATIVE_GROUPS)
    assert summary["declarative_missing_groups_total"] == 0
    assert summary["declarative_registered_commands_total"] >= 20
    assert summary["legacy_unregistered_commands_total"] > 0
    assert set(summary["registered_command_ids"]) >= {
        "workspace.status",
        "standards.status",
        "schema.validate",
        "validate",
        "project-state.validate",
        "test-contracts.validate-v2",
        "quality-gate.run",
        "industrial-readiness.check",
        "cli-registry.report",
        "cli-registry.guard",
        "runtime-state.inventory",
        "runtime-state.cleanup-plan",
        "runtime-state.cleanup",
        "runtime-state.export",
        "runtime-state.hygiene",
        "docs-governance.validate",
        "observability.inventory",
        "observability.cleanup-plan",
        "observability.export",
        "api.shell-gate",
        "operator.dashboard",
        "portfolio.status",
        "portfolio.hardening-gate",
        "audit-pack.build-v2",
        "audit-pack.verify-v2",
        "release.environment-snapshot",
        "release.source-archive-manifest",
    }
    for group_id in CURRENT_DECLARATIVE_GROUPS:
        assert group_id in groups


def test_post_h_006_b_registered_descriptors_are_complete_safe_and_not_dynamic() -> None:
    registry = _registry_result().data["registry"]

    for group in registry["groups"]:
        for command in group["commands"]:
            metadata = command["metadata"]
            if metadata.get("declarative_registered") is not True:
                continue
            assert metadata["registry_phase"] in {"declarative-initial", "handler-migrated-incremental"}
            assert metadata["registration_status"] in {"registered-declarative", "handler-migrated"}
            assert metadata["declarative_descriptor_source"] == "src/devpilot_core/cli_registry/registry.py"
            assert isinstance(metadata["handler_migration_performed"], bool)
            assert command["handler"]
            assert command["returns"] == "CommandResult"
            assert command["domain"]
            assert command["owner_module"].startswith("src/devpilot_core/")
            assert command["recommended_tests"]
            assert command["remote_execution_enabled"] is False
            assert command["connector_write_enabled"] is False
            assert command["plugin_execution_enabled"] is False
            if any(effect in command["side_effects"] for effect in ["write-report", "write-files", "mutate-state", "execute-subprocess"]):
                assert command["writes_files"] is True


def test_post_h_006_b_governs_risky_commands_inside_initial_groups() -> None:
    commands = _commands_by_id()

    workspace_init = commands["workspace.init"]
    assert workspace_init["risk_level"] == "high"
    assert workspace_init["policy_check_required"] is True
    assert workspace_init["dry_run_supported"] is True
    assert "mutate-state" in workspace_init["side_effects"]

    migration = commands["test-contracts.migrate-v2"]
    assert migration["risk_level"] == "high"
    assert migration["policy_check_required"] is True
    assert migration["dry_run_supported"] is True
    assert "write-files" in migration["side_effects"]

    quality_gate = commands["quality-gate.run"]
    assert quality_gate["risk_level"] == "high"
    assert quality_gate["policy_check_required"] is True
    assert "execute-subprocess" in quality_gate["side_effects"]


def test_post_h_006_b_legacy_commands_are_marked_unregistered_without_being_hidden() -> None:
    summary = _registry_result().data["summary"]
    commands = _commands_by_id()

    assert "architecture.map" in commands
    assert commands["architecture.map"]["metadata"]["registry_phase"] == "legacy-unregistered"
    assert commands["architecture.map"]["metadata"]["declarative_registered"] is False
    assert "architecture.map" in summary["legacy_unregistered_command_ids"]
    assert summary["legacy_unregistered_commands_total"] + summary["declarative_registered_commands_total"] == summary["commands_total"]


def test_post_h_006_b_docs_manifest_and_contracts_are_synchronized() -> None:
    backlog = _read("docs/backlogs/POST-H-006_cli_command_registry.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    architecture_doc = _read("docs/02_architecture/cli_command_registry_map.md")
    audit = _read("docs/audits/post_h_006_b_declarative_registry_report.md")
    manifest = _read_json("docs/post_h_006_b_manifest.json")
    changelog = _read("docs/release/CHANGELOG.md")
    v1 = _read_json(".devpilot/testing/test_contract_registry.json")
    v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    v1_contracts = {item["contract_id"]: item for item in v1["contracts"]}
    v2_contracts = {item["contract_id"]: item for item in v2["contracts"]}

    assert "POST-H-006-B — Command registry declarativo inicial" in backlog
    assert "POST-H-006-E" in readme
    assert "POST-H-007" in readme
    assert "POST-H-006-B — Operación del registry declarativo inicial" in runbook
    assert "DeclarativeCliRegistryBuilder" in architecture_doc
    assert "legacy_unregistered_commands_total" in audit
    assert "post-h-006-b" in changelog
    assert manifest["id"] == "POST-H-006-B"
    assert manifest["initial_declarative_groups"] == sorted(B_INITIAL_GROUPS)
    assert manifest["handler_migration_performed"] is False
    assert manifest["dynamic_handler_loading_enabled"] is False
    assert "post-h-006-declarative-cli-registry" in v1_contracts
    assert "post-h-006-declarative-cli-registry" in v2_contracts
    assert v1_contracts["post-h-006-declarative-cli-registry"]["owner"] == "POST-H-006-B"
    assert v2_contracts["post-h-006-declarative-cli-registry"]["domain"] == "interface.cli"
    assert v2_contracts["post-h-006-declarative-cli-registry"]["owner"] == "POST-H-006-B"
