from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.release import (
    ReleaseEnvironmentSnapshotBuilder,
    ReleaseEnvironmentSnapshotOptions,
    ReleaseReproducibilityVerifier,
    ReleaseReproducibilityVerifyOptions,
    SourceArchiveManifestBuilder,
    SourceArchiveManifestOptions,
)
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs" / "release"


def _prepare_pack(name: str = "test_reproducibility_pack.json") -> Path:
    ReleaseEnvironmentSnapshotBuilder(
        ROOT,
        options=ReleaseEnvironmentSnapshotOptions(write_report=True),
    ).build()
    SourceArchiveManifestBuilder(
        ROOT,
        options=SourceArchiveManifestOptions(write_report=True),
    ).build()
    payload = json.loads((ROOT / "tests/fixtures/release_reproducibility_pack.valid.json").read_text(encoding="utf-8"))
    payload["artifacts"]["environment_snapshot"] = "outputs/release/environment_snapshot.json"
    payload["artifacts"]["source_archive_manifest"] = "outputs/release/source_archive_manifest.json"
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _pack_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_post_h_017_d_reproducibility_verifier_passes_local_pack() -> None:
    pack = _prepare_pack()

    result = ReleaseReproducibilityVerifier(
        ROOT,
        options=ReleaseReproducibilityVerifyOptions(pack=pack),
    ).verify()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-017-D"
    assert summary["release_reproducibility_verified"] is True
    assert summary["blocking_findings_total"] == 0
    assert summary["checksum_mismatches_total"] == 0
    assert summary["forbidden_entries_total"] == 0
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False


def test_post_h_017_d_reproducibility_verify_cli_writes_schema_valid_report(monkeypatch, capsys) -> None:
    pack = _prepare_pack("test_reproducibility_pack_cli.json")
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["release", "reproducibility-verify", "--pack", str(pack.relative_to(ROOT)), "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "release reproducibility-verify"
    assert payload["ok"] is True
    reports = payload["data"]["reports"]
    assert reports["json"] == "outputs/release/reproducibility_verification.json"
    assert reports["markdown"] == "outputs/release/reproducibility_verification.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()

    schema_result = SchemaValidator(ROOT).validate(
        schema="ReleaseReproducibilityVerification",
        instance=reports["json"],
    )
    assert schema_result.ok, schema_result.to_dict()


def test_post_h_017_d_reproducibility_verifier_blocks_dirty_pack() -> None:
    pack = _prepare_pack("test_reproducibility_pack_dirty.json")
    payload = _pack_payload(pack)
    payload["git"]["dirty"] = True
    pack.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    result = ReleaseReproducibilityVerifier(ROOT, options=ReleaseReproducibilityVerifyOptions(pack=pack)).verify()

    assert not result.ok
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "RELEASE_REPRODUCIBILITY_DIRTY_TRUE" for finding in result.findings)


def test_post_h_017_d_reproducibility_verifier_blocks_secrets_included() -> None:
    pack = _prepare_pack("test_reproducibility_pack_secrets.json")
    payload = _pack_payload(pack)
    payload["safety"]["secrets_included"] = True
    pack.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    result = ReleaseReproducibilityVerifier(ROOT, options=ReleaseReproducibilityVerifyOptions(pack=pack)).verify()

    assert not result.ok
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "RELEASE_REPRODUCIBILITY_SAFETY_FLAGS_INVALID" for finding in result.findings)


def test_post_h_017_d_reproducibility_verifier_blocks_checksum_mismatch() -> None:
    pack = _prepare_pack("test_reproducibility_pack_checksum.json")
    source_manifest = json.loads((ROOT / "outputs/release/source_archive_manifest.json").read_text(encoding="utf-8"))
    tampered = copy.deepcopy(source_manifest)
    tampered["critical_artifacts"]["sha256"][0]["sha256"] = "0" * 64
    tampered_path = OUTPUTS / "test_source_archive_manifest_tampered.json"
    tampered_path.write_text(json.dumps(tampered, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    payload = _pack_payload(pack)
    payload["artifacts"]["source_archive_manifest"] = "outputs/release/test_source_archive_manifest_tampered.json"
    pack.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    result = ReleaseReproducibilityVerifier(ROOT, options=ReleaseReproducibilityVerifyOptions(pack=pack)).verify()

    assert not result.ok
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "RELEASE_REPRODUCIBILITY_CHECKSUM_MISMATCH" for finding in result.findings)


def test_post_h_017_d_docs_state_and_contracts_are_synchronized() -> None:
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
    assert "POST-H-017-D — Verifier local de reproducibilidad" in backlog
    assert "POST-H-017-D — Verifier local de reproducibilidad" in post_doc
    assert "release reproducibility-verify --pack outputs/release/reproducibility_pack.json --json" in readme
    assert "release reproducibility-verify --pack outputs/release/reproducibility_pack.json --json" in runbook
    assert "ReleaseReproducibilityVerification" in release_runbook
    assert "post-h-017-d" in changelog
    assert state["current_micro_sprint"] == "POST-H-017-E"
    assert state["next_micro_sprint"] == "POST-H-018"
    assert "post-h-017-reproducibility-verifier" in tcr_v1
    assert "post-h-017-reproducibility-verifier" in tcr_v2
    assert "release_reproducibility_verifier_enabled" in source_registry
