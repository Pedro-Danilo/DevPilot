from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_78_changelog_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog_g = _read("docs/devpilot_backlog_fase_G_productizacion_release.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    for path in [
        "src/devpilot_core/release/changelog.py",
        "docs/05_operations/change_policy.md",
        "docs/release/CHANGELOG.md",
        "docs/audits/func_sprint_78_changelog_audit.md",
        "docs/functional_sprint_78_manifest.json",
        "tests/test_release_changelog.py",
        "tests/test_sprint_78_documentation.py",
    ]:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-92" in readme
    assert "Siguiente hito: `FUNC-SPRINT-93" in readme
    assert "FUNC-SPRINT-78 — Changelog generator y política de cambios" in readme
    assert "FUNC-SPRINT-78 — Operación de Changelog" in runbook
    assert 'source_repo: "repo_DevPilot_Local_106.zip"' in backlog_g
    assert 'last_completed_sprint: "FUNC-SPRINT-84"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-85"' in backlog_g
    assert 'phase_g_status: "closed"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-93"' in functional_backlog


def test_sprint_78_docs_define_changelog_policy_boundaries() -> None:
    policy = _read("docs/05_operations/change_policy.md")
    changelog = _read("docs/release/CHANGELOG.md")
    audit = _read("docs/audits/func_sprint_78_changelog_audit.md")

    for text in [policy, changelog, audit]:
        assert "Keep a Changelog" in text
        assert "Added" in text
        assert "Changed" in text
        assert "Security" in text
        assert "no invent" in text.lower() or "no debe inventar" in text.lower()
        assert "no publica" in text or "no publicar" in text or "publish" in text
        assert "no despliega" in text or "deploy" in text

    assert "docs/functional_sprint_78_manifest.json" in changelog
    assert "outputs/reports" in policy


def test_sprint_78_manifest_declares_changelog_scope() -> None:
    manifest = _json("docs/functional_sprint_78_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-78"
    assert manifest["status"] == "implemented"
    assert manifest["phase"] == "FASE-G-PRODUCTIZACION-RELEASE"
    assert manifest["summary"]["fg_level"] == "FG-L4"
    assert manifest["summary"]["release_changelog_cli_added"] is True
    assert manifest["summary"]["release_changelog_model_added"] is True
    assert manifest["summary"]["change_policy_added"] is True
    assert manifest["summary"]["overwrites_canonical_changelog"] is False
    assert manifest["summary"]["network_used"] is False
    assert manifest["summary"]["external_api_used"] is False
    assert manifest["summary"]["publishes_artifacts"] is False
    assert manifest["summary"]["deploys_artifacts"] is False
    assert manifest["summary"]["dependencies_added"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-79")
