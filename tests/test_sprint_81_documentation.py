from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_81_release_verification_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog_g = _read("docs/devpilot_backlog_fase_G_productizacion_release.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    for path in [
        "src/devpilot_core/release/verification.py",
        "docs/05_operations/release_verification.md",
        "docs/audits/func_sprint_81_release_verification_audit.md",
        "docs/functional_sprint_81_manifest.json",
        "tests/test_release_verification.py",
        "tests/test_sprint_81_documentation.py",
    ]:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-87" in readme
    assert "Siguiente hito: `FUNC-SPRINT-88" in readme
    assert "FUNC-SPRINT-83 — Backup, restore y upgrade local" in readme
    assert "FUNC-SPRINT-81 — Operación de checksums" in runbook
    assert 'source_repo: "repo_DevPilot_Local_106.zip"' in backlog_g
    assert 'last_completed_sprint: "FUNC-SPRINT-84"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-85"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-88"' in functional_backlog


def test_sprint_81_docs_define_verification_boundaries() -> None:
    verification_doc = _read("docs/05_operations/release_verification.md")
    audit = _read("docs/audits/func_sprint_81_release_verification_audit.md")
    release_manifest = _read("docs/05_operations/release_manifest.md")
    artifacts_matrix = _read("docs/05_operations/release_artifacts_matrix.md")
    changelog = _read("docs/release/CHANGELOG.md")

    for text in [verification_doc, audit, release_manifest, artifacts_matrix, changelog]:
        assert "FUNC-SPRINT-81" in text

    for marker in [
        "release checksum",
        "release smoke-test",
        "release verify",
        "outputs/reports/checksums.sha256",
        "exit code",
        "no firma",
        "no publica",
        "no despliega",
    ]:
        assert marker in verification_doc

    assert "FUNC-SPRINT-81` — `docs/functional_sprint_81_manifest.json`" in changelog
    assert "RELEASE-VERIFICATION" in release_manifest


def test_sprint_81_manifest_declares_release_verification_scope() -> None:
    manifest = _json("docs/functional_sprint_81_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-81"
    assert manifest["status"] == "implemented"
    assert manifest["phase"] == "FASE-G-PRODUCTIZACION-RELEASE"
    assert manifest["summary"]["fg_level"] == "FG-L6"
    assert manifest["summary"]["release_checksum_cli_added"] is True
    assert manifest["summary"]["release_smoke_test_cli_added"] is True
    assert manifest["summary"]["release_verify_cli_added"] is True
    assert manifest["summary"]["sha256_supported"] is True
    assert manifest["summary"]["artifact_required"] is True
    assert manifest["summary"]["real_local_artifact_verified"] is True
    assert manifest["summary"]["smoke_test_exit_codes_observed"] is True
    assert manifest["summary"]["network_used"] is False
    assert manifest["summary"]["external_api_used"] is False
    assert manifest["summary"]["publishes_artifacts"] is False
    assert manifest["summary"]["deploys_artifacts"] is False
    assert manifest["summary"]["dependencies_added"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-82")
