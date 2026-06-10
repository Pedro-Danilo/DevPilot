from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "release" / "release_manifest_v0.1.0.json"


# FUNC-SPRINT-20/22 compatibility note:
# release_manifest_v0.1.0 stores point-in-time checksums from the internal
# technical release. Some operational documents are intentionally living
# docs-as-code artifacts and are updated by later reconciliation sprints.
# FUNC-SPRINT-22 also updates pyproject.toml to declare the ADR-governed
# jsonschema dependency required by SchemaValidator.
# Their historical checksums must remain in the manifest, but this regression
# test must not block legitimate post-release documentation updates.
MUTABLE_POST_RELEASE_ARTIFACTS = {
    "README.md",
    "docs/05_operations/runbook.md",
    "docs/functional_backlog_after_precode.md",
    "docs/devpilot_backlog_fase_A_baseline_industrial_minima.md",
    "pyproject.toml",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_release_manifest_exists_and_declares_sprint_19_release() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert payload["release_version"] == "0.1.0"
    assert payload["sprint"] == "FUNC-SPRINT-19"
    assert payload["cycle_closed"] == "FUNC-SPRINT-00..FUNC-SPRINT-18"
    assert payload["status"] == "internal-technical-release"
    assert payload["next_sprint"].startswith("FUNC-SPRINT-20")


def test_release_manifest_references_required_artifacts() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    required_paths = {
        "docs/audits/functional_cycle_00_18_closure_report.md",
        "docs/release/release_notes_v0.1.0.md",
        "docs/functional_sprint_19_manifest.json",
        "scripts/verify_release_v0_1_0.py",
        "README.md",
        "docs/05_operations/runbook.md",
    }

    artifacts = set(payload["source_artifacts"])
    assert required_paths <= artifacts
    for artifact in required_paths:
        assert (ROOT / artifact).is_file(), artifact


def test_release_manifest_does_not_reference_runtime_outputs_as_sources() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    blocked_prefixes = (
        "outputs/",
        ".pytest_cache/",
        "__pycache__/",
        ".venv/",
        ".git/",
    )
    blocked_exact = {".devpilot/devpilot.db"}

    for artifact in payload["source_artifacts"]:
        assert artifact not in blocked_exact
        assert not artifact.startswith(blocked_prefixes), artifact

    for excluded in ["outputs/", ".pytest_cache/", "__pycache__/", ".venv/", ".git/", ".devpilot/devpilot.db"]:
        assert excluded in payload["scope"]["excludes"]


def test_release_manifest_checksums_match_existing_files() -> None:
    """Validate stable release artifacts while allowing living docs to evolve.

    Purpose: keep Sprint 19 release integrity checks useful after Sprint 20.
    Integration: Sprint 20 updates README/runbook/backlogs by design; Sprint 22 updates pyproject.toml for SchemaValidator.
    PASS: immutable release artifacts still match their recorded checksum.
    BLOCK: generated release notes, closure reports, scripts or manifests drift silently.
    Risk: mutable documentation checksums remain historical evidence, not current-state validation.
    """

    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for artifact, digest in payload["file_checksums_sha256"].items():
        if digest.startswith("self-checksum-excluded"):
            continue
        path = ROOT / artifact
        assert path.is_file(), artifact
        if artifact in MUTABLE_POST_RELEASE_ARTIFACTS:
            assert len(digest) == 64, artifact
            continue
        assert _sha256(path) == digest, artifact


def test_release_manifest_contains_required_smoke_commands() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    commands = set(payload["smoke_commands"])
    required_commands = {
        "python -m pytest -q",
        "python -m devpilot_core --version",
        "python -m devpilot_core workspace status --json",
        "python -m devpilot_core standards status --json",
        "python -m devpilot_core readiness-check --strict --json",
        "python -m devpilot_core miasi validate --json",
        "python -m devpilot_core eval run --json",
        "python -m devpilot_core app contract --json",
        "python scripts/verify_release_v0_1_0.py --json",
    }

    assert required_commands <= commands


def test_closure_report_and_release_notes_have_required_frontmatter() -> None:
    for relative_path in [
        "docs/audits/functional_cycle_00_18_closure_report.md",
        "docs/release/release_notes_v0.1.0.md",
    ]:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert text.startswith("---\n")
        for field in ["doc_id:", "title:", "status:", "version:", "owner:", "updated:", "approval:"]:
            assert field in text, f"{field} missing in {relative_path}"


def test_sprint_19_manifest_is_present_and_scoped_to_documentary_release() -> None:
    payload = json.loads((ROOT / "docs" / "functional_sprint_19_manifest.json").read_text(encoding="utf-8"))

    assert payload["sprint"] == "FUNC-SPRINT-19"
    assert payload["status"] == "implemented"
    assert "docs/release/release_manifest_v0.1.0.json" in payload["created_files"]
    assert "tests/test_release_manifest.py" in payload["tests"]
    assert payload["next_sprint"].startswith("FUNC-SPRINT-20")
