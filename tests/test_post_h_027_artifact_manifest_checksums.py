from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.release import PackageBuildBuilder, PackageBuildOptions, ReleaseArtifactManifestBuilder, ReleaseArtifactManifestOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _clean_runtime() -> None:
    for rel in ("dist", "outputs/release"):
        path = ROOT / rel
        if path.exists():
            shutil.rmtree(path)


def _build_all_artifacts() -> None:
    result = PackageBuildBuilder(ROOT, options=PackageBuildOptions(version="0.1.0", kind="all", execute=True)).build()
    assert result.ok, result.to_dict()


def test_release_artifact_manifest_passes_and_writes_checksums() -> None:
    _clean_runtime()
    _build_all_artifacts()

    result = ReleaseArtifactManifestBuilder(
        ROOT,
        options=ReleaseArtifactManifestOptions(version="0.1.0", verify_checksums=True, write_report=True),
    ).build()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["required_missing_total"] == 0
    assert summary["checksum_mismatch_total"] == 0
    assert summary["checksums_verified"] is True
    manifest = result.data["manifest"]
    required = [item for item in manifest["artifacts"] if item["required"]]
    assert {item["artifact_id"] for item in required} == {"source-zip", "python-wheel", "python-sdist"}
    assert all(item["exists"] and item["sha256"] for item in required)
    checksums = (ROOT / "outputs/release/checksums.sha256").read_text(encoding="utf-8")
    for item in required:
        assert f"{item['sha256']}  {item['path']}" in checksums


def test_release_artifact_manifest_blocks_missing_required_artifact() -> None:
    _clean_runtime()
    _build_all_artifacts()
    (ROOT / "dist/devpilot_local-0.1.0-py3-none-any.whl").unlink()

    result = ReleaseArtifactManifestBuilder(ROOT, options=ReleaseArtifactManifestOptions(version="0.1.0")).build()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["required_missing_total"] == 1
    assert any(finding.id == "RELEASE_ARTIFACT_MANIFEST_REQUIRED_MISSING" for finding in result.findings)


def test_release_artifact_manifest_detects_checksum_mismatch(monkeypatch) -> None:
    _clean_runtime()
    _build_all_artifacts()
    builder = ReleaseArtifactManifestBuilder(ROOT, options=ReleaseArtifactManifestOptions(version="0.1.0", verify_checksums=True))
    manifest = builder._build_manifest(builder._load_policy()[0])  # noqa: SLF001 - intentional fixture-level corruption check
    wheel = ROOT / "dist/devpilot_local-0.1.0-py3-none-any.whl"
    wheel.write_bytes(wheel.read_bytes() + b"\npost-h-027-c-corruption-fixture\n")

    findings = builder._verify_manifest_checksums(manifest)  # noqa: SLF001

    assert findings == [] or all(finding.severity.value == "info" for finding in findings)
    assert manifest["checksums"]["mismatches"]
    assert manifest["checksums"]["mismatches"][0]["path"] == "dist/devpilot_local-0.1.0-py3-none-any.whl"


def test_release_artifact_manifest_schema_validation() -> None:
    _clean_runtime()
    _build_all_artifacts()
    result = ReleaseArtifactManifestBuilder(ROOT, options=ReleaseArtifactManifestOptions(version="0.1.0", verify_checksums=True, write_report=True)).build()
    assert result.ok, result.to_dict()

    validation = SchemaValidator(ROOT).validate(
        schema="ReleaseArtifactManifest",
        instance=Path("outputs/release/release_artifact_manifest.json"),
    )

    assert validation.ok is True
    assert validation.exit_code == ExitCode.PASS


def test_release_artifact_manifest_cli_json(monkeypatch, capsys) -> None:
    _clean_runtime()
    _build_all_artifacts()
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["release", "artifact-manifest", "--version", "0.1.0", "--verify-checksums", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "release artifact-manifest"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == "PASS"
    assert payload["data"]["reports"]["checksums"] == "outputs/release/checksums.sha256"



def test_release_artifact_manifest_normalizes_windows_report_paths() -> None:
    _clean_runtime()
    _build_all_artifacts()

    result = ReleaseArtifactManifestBuilder(
        ROOT,
        options=ReleaseArtifactManifestOptions(
            version="0.1.0",
            output_json="outputs\\release\\release_artifact_manifest.json",
            output_markdown="outputs\\release\\release_artifact_manifest.md",
            output_checksums="outputs\\release\\checksums.sha256",
            verify_checksums=True,
            write_report=True,
        ),
    ).build()

    assert result.ok, result.to_dict()
    assert result.data["reports"] == {
        "json": "outputs/release/release_artifact_manifest.json",
        "markdown": "outputs/release/release_artifact_manifest.md",
        "checksums": "outputs/release/checksums.sha256",
    }
    assert result.data["manifest"]["checksums_file"] == "outputs/release/checksums.sha256"
    assert (ROOT / "outputs/release/checksums.sha256").is_file()

def test_release_artifact_manifest_policy_is_local_first() -> None:
    policy = json.loads((ROOT / ".devpilot/release/local_artifact_manifest_policy.json").read_text(encoding="utf-8"))

    assert policy["created_by"] == "POST-H-027-C"
    assert policy["safety"]["network_allowed"] is False
    assert policy["safety"]["publish_allowed"] is False
    assert len(policy["required_artifacts"]) == 3
