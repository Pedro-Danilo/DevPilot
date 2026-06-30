from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.quality.gate import QualityGate, QualityGateOptions
from devpilot_core.release import ReleaseReproducibilityPackBuilder, ReleaseReproducibilityPackOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_017_e_reproducibility_pack_builder_writes_and_verifies_local_pack() -> None:
    result = ReleaseReproducibilityPackBuilder(
        ROOT,
        options=ReleaseReproducibilityPackOptions(write_report=True, verify_after_build=True),
    ).build()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-017-E"
    assert summary["pack_written"] is True
    assert summary["release_reproducibility_verified"] is True
    assert summary["checksum_mismatches_total"] == 0
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert (ROOT / "outputs/release/reproducibility_pack.json").exists()
    assert (ROOT / "outputs/release/reproducibility_verification.json").exists()

    schema_result = SchemaValidator(ROOT).validate(
        schema="ReleaseReproducibilityPack",
        instance="outputs/release/reproducibility_pack.json",
    )
    assert schema_result.ok, schema_result.to_dict()


def test_post_h_017_e_reproducibility_pack_cli_writes_outputs(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["release", "reproducibility-pack", "--json", "--write-report", "--verify"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "release reproducibility-pack"
    assert payload["ok"] is True
    assert payload["data"]["reports"]["json"] == "outputs/release/reproducibility_pack.json"
    assert payload["data"]["summary"]["release_reproducibility_verified"] is True


def test_post_h_017_e_quality_gate_hardening_includes_release_reproducibility() -> None:
    gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    subgates = {subgate.id: subgate for subgate in gate._subgates()}

    assert "release-reproducibility" in subgates
    assert subgates["release-reproducibility"].critical is True

    result = subgates["release-reproducibility"].runner()
    assert result.ok, result.to_dict()
    assert result.data["summary"]["release_reproducibility_verified"] is True


def test_post_h_017_e_pack_builder_blocks_dirty_git_state(monkeypatch) -> None:
    from devpilot_core.release import reproducibility_pack as pack_module

    monkeypatch.setattr(
        pack_module,
        "_git_state",
        lambda root: {"git_metadata_available": True, "commit": "abc1234", "branch": "main", "dirty": True},
    )

    result = ReleaseReproducibilityPackBuilder(
        ROOT,
        options=ReleaseReproducibilityPackOptions(write_report=False, require_clean_git=True),
    ).build()

    assert not result.ok
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "RELEASE_REPRODUCIBILITY_PACK_DIRTY_REPO" for finding in result.findings)


def test_post_h_017_e_docs_state_and_contracts_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-017_release_reproducibility_pack.md").read_text(encoding="utf-8")
    post_doc = (ROOT / "docs/POST-H-017_release_reproducibility_pack.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    release_runbook = (ROOT / "docs/05_operations/release_reproducibility_runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    source_registry = (ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8")

    assert 'current_micro_sprint: "POST-H-017-E"' in backlog
    assert 'next_micro_sprint: "POST-H-018"' in backlog
    assert "POST-H-017-E — Quality gate y runbook release" in backlog
    assert "POST-H-017-E — Quality gate y runbook release" in post_doc
    assert "release reproducibility-pack --json --write-report --verify" in readme
    assert "release reproducibility-pack --json --write-report --verify" in runbook
    assert "release-reproducibility" in release_runbook
    assert "post-h-017-e" in changelog
    assert state["last_completed_sprint"] == "POST-H-017"
    assert state["next_sprint"] == "POST-H-018"
    assert state["current_micro_sprint"] == "POST-H-017-E"
    assert state["next_micro_sprint"] == "POST-H-018"
    assert "post-h-017-release-reproducibility-gate" in tcr_v1
    assert "post-h-017-release-reproducibility-gate" in tcr_v2
    assert "release_reproducibility_quality_gate_integrated" in source_registry
