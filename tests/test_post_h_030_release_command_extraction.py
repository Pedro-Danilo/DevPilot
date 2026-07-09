from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_commands import (
    handle_backup_list,
    handle_install_plan,
    handle_package_source_zip_policy,
    handle_release_candidate_profile,
    handle_release_manifest,
    handle_release_sbom,
    handle_upgrade_check,
)
from devpilot_core.cli_registry.registry import DeclarativeCliRegistryBuilder

ROOT = Path(__file__).resolve().parents[1]

POST_H_030_C_COMMANDS = {
    "backup.create",
    "backup.list",
    "backup.restore",
    "install.plan",
    "install.windows-smoke",
    "package.build",
    "package.source-zip-policy",
    "release.artifact-manifest",
    "release.changelog",
    "release.checksum",
    "release.environment-snapshot",
    "release.manifest",
    "release.python-artifact-verify",
    "release.reproducibility-pack",
    "release.reproducibility-verify",
    "release.sbom",
    "release.smoke-test",
    "release.source-archive-manifest",
    "release.upgrade-rollback-dry-run",
    "release.verify",
    "release-candidate.evidence-freshness",
    "release-candidate.final",
    "release-candidate.install-smoke",
    "release-candidate.profile",
    "release-candidate.ui-api-smoke",
    "upgrade.check",
}


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _commands_by_id() -> dict[str, dict]:
    registry = DeclarativeCliRegistryBuilder(ROOT).build_registry().to_dict()
    return {command["command_id"]: command for group in registry["groups"] for command in group["commands"]}


def test_post_h_030_c_release_family_handlers_are_extracted_without_runtime_router() -> None:
    commands = _commands_by_id()

    missing = sorted(POST_H_030_C_COMMANDS - set(commands))
    assert missing == []
    for command_id in sorted(POST_H_030_C_COMMANDS):
        command = commands[command_id]
        metadata = command["metadata"]
        assert command["owner_module"] == "src/devpilot_core/cli_commands/release.py"
        assert command["handler"].startswith("handle_")
        assert command["legacy_cli_owned"] is False
        assert metadata["registry_phase"] == "handler-migrated-incremental"
        assert metadata["registration_status"] == "handler-migrated"
        assert metadata["handler_migration_performed"] is True
        assert metadata["migrated_by"] == "POST-H-030-C"
        assert metadata["runtime_router_enabled"] is False
        assert command["remote_execution_enabled"] is False
        assert command["connector_write_enabled"] is False
        assert command["plugin_execution_enabled"] is False


def test_post_h_030_c_cli_py_preserves_wrappers_but_delegates_result_building() -> None:
    source = (ROOT / "src/devpilot_core/cli.py").read_text(encoding="utf-8")
    module = (ROOT / "src/devpilot_core/cli_commands/release.py").read_text(encoding="utf-8")

    for handler in [
        "handle_release_manifest",
        "handle_release_changelog",
        "handle_release_sbom",
        "handle_release_reproducibility_pack",
        "handle_release_artifact_manifest",
        "handle_package_build",
        "handle_install_windows_smoke",
        "handle_release_candidate_profile",
    ]:
        assert handler in source
        assert f"def {handler}" in module
    assert "runtime_router_enabled = True" not in source
    assert "importlib" not in module
    assert "subprocess.run" not in module


def test_post_h_030_c_cli_json_contract_matches_selected_extracted_handlers(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    direct_manifest = handle_release_manifest(ROOT, version="0.1.0").to_dict()
    exit_code = cli.main(["release", "manifest", "--version", "0.1.0", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == direct_manifest["exit_code"] == 0
    assert payload["command"] == direct_manifest["command"] == "release manifest"
    assert payload["data"]["summary"]["version"] == direct_manifest["data"]["summary"]["version"]
    assert payload["data"]["summary"]["network_used"] is False
    assert payload["data"]["summary"]["external_api_used"] is False

    direct_sbom = handle_release_sbom(ROOT, version="0.1.0").to_dict()
    exit_code = cli.main(["release", "sbom", "--version", "0.1.0", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == direct_sbom["exit_code"] == 0
    assert payload["command"] == direct_sbom["command"] == "release sbom"
    assert payload["data"]["summary"]["version"] == direct_sbom["data"]["summary"]["version"]

    direct_install = handle_install_plan(ROOT, mode="all", version="0.1.0").to_dict()
    exit_code = cli.main(["install", "plan", "--mode", "all", "--version", "0.1.0", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == direct_install["exit_code"] == 0
    assert payload["command"] == direct_install["command"] == "install plan"
    assert payload["data"]["install_plan"]["mode"] == "all"

    direct_policy = handle_package_source_zip_policy(ROOT).to_dict()
    exit_code = cli.main(["package", "source-zip-policy", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == direct_policy["exit_code"] == 0
    assert payload["command"] == direct_policy["command"] == "package source-zip-policy"
    assert payload["data"]["summary"]["network_used"] is False

    direct_profile = handle_release_candidate_profile(
        ROOT,
        profile="release-candidate-local",
        test_profiles_path=".devpilot/testing/test_profiles.json",
        tcr_v2_path=".devpilot/testing/test_contract_registry_v2.json",
        output_json="outputs/reports/release_candidate_verification_profile_report.json",
        output_markdown="outputs/reports/release_candidate_verification_profile_report.md",
    ).to_dict()
    exit_code = cli.main(["release-candidate", "profile", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == direct_profile["exit_code"] == 0
    assert payload["command"] == direct_profile["command"] == "release-candidate profile"
    assert payload["data"]["summary"]["profile_id"] == direct_profile["data"]["summary"]["profile_id"]


def test_post_h_030_c_safe_operational_handlers_remain_local_first(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    for result in [
        handle_backup_list(ROOT).to_dict(),
        handle_upgrade_check(ROOT, target_version="0.1.1").to_dict(),
    ]:
        assert result["exit_code"] == 0
        summary = result["data"]["summary"]
        assert summary["network_used"] is False
        assert summary["external_api_used"] is False
        assert summary.get("source_mutations_performed", False) is False

    exit_code = cli.main(["backup", "list", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "backup list"
    assert payload["data"]["summary"]["network_used"] is False

    exit_code = cli.main(["upgrade", "check", "--target-version", "0.1.1", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "upgrade check"
    assert payload["data"]["summary"]["network_used"] is False


def test_post_h_030_c_ownership_matrix_and_extraction_plan_mark_release_family_migrated() -> None:
    matrix = _load(".devpilot/cli_registry/command_ownership_matrix.json")
    plan = _load(".devpilot/cli_registry/cli_extraction_plan.json")
    commands = {item["command_id"]: item for item in matrix["commands"]}

    assert matrix["summary"]["migration_state_counts"]["already-migrated"] >= 34
    for command_id in POST_H_030_C_COMMANDS:
        item = commands[command_id]
        assert item["current_module"] == "src/devpilot_core/cli_commands/release.py"
        assert item["target_module"] == "src/devpilot_core/cli_commands/release.py"
        assert item["migration_state"] == "already-migrated"
        assert item["registry_phase"] == "handler-migrated-incremental"
        assert item["planned_micro_sprint"] == "POST-H-030-C"

    plan_items = {item["plan_id"]: item for item in plan["plan_items"]}
    release_plan = plan_items["post-h-030-c:src/devpilot_core/cli_commands/release.py"]
    assert release_plan["status"] == "already-started"
    assert set(release_plan["command_ids"]) == POST_H_030_C_COMMANDS
    assert release_plan["risk_level"] in {"high", "critical"}
    target_modules = {item["module_path"]: item for item in plan["target_modules"]}
    target = target_modules["src/devpilot_core/cli_commands/release.py"]
    assert target["exists_now"] is True
    assert target["creation_required"] is False


def test_post_h_030_c_governance_artifacts_are_synchronized() -> None:
    state = _load(".devpilot/project_state.json")
    source_registry = _load(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = _load(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _load(".devpilot/testing/test_contract_registry_v2.json")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-030_cli_hotspot_reduction_application_boundaries.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    assert state["current_micro_sprint"] in {"POST-H-030-C", "POST-H-030-D"}
    assert state["next_micro_sprint"] in {"POST-H-030-D", "POST-H-030-E"}
    assert state["current_repo"] in {"repo_DevPilot_Local_286_POST_H_030_C.zip", "repo_DevPilot_Local_287_POST_H_030_D.zip"}
    assert state["post_h_030_status"] in {"active/implemented-initial-post-h-030-c", "active/implemented-initial-post-h-030-d"}
    assert state["post_h_030_release_cli_module"] == "src/devpilot_core/cli_commands/release.py"
    assert state["post_h_030_release_commands_migrated_total"] == len(POST_H_030_C_COMMANDS)
    assert state["post_h_030_release_public_behavior_changed"] is False

    assert any(marker in backlog for marker in ['current_micro_sprint: "POST-H-030-C"', 'current_micro_sprint: "POST-H-030-D"'])
    assert any(marker in backlog for marker in ['next_micro_sprint: "POST-H-030-D"', 'next_micro_sprint: "POST-H-030-E"'])
    assert "POST-H-030-C — Release command extraction" in readme
    assert "POST-H-030-C — Release command extraction" in runbook
    assert "post-h-030-c" in changelog.lower()

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-030-C-RELEASE-CLI-MODULE" in doc_ids
    assert "POST-H-030-C-RELEASE-COMMAND-EXTRACTION-REPORT" in doc_ids
    assert "POST-H-030-C-RELEASE-COMMAND-EXTRACTION-TEST" in doc_ids

    assert any(c["contract_id"] == "post-h-030-release-command-extraction" for c in tcr_v1["contracts"])
    assert any(c["contract_id"] == "post-h-030-release-command-extraction" for c in tcr_v2["contracts"])


def test_post_h_030_c_cli_registry_guard_still_passes() -> None:
    exit_code = cli.main(["cli-registry", "guard", "--json"])

    assert exit_code == 0
