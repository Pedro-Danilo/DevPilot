from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_74_release_strategy_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog_g = _read("docs/devpilot_backlog_fase_G_productizacion_release.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    for path in [
        "docs/02_architecture/adrs/ADR-0014-release-versioning-packaging.md",
        "docs/05_operations/release_policy.md",
        "docs/05_operations/release_artifacts_matrix.md",
        "docs/audits/func_sprint_74_release_versioning_audit.md",
        "docs/functional_sprint_74_manifest.json",
        "tests/test_sprint_74_documentation.py",
    ]:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-77" in readme
    assert "Siguiente hito: `FUNC-SPRINT-78" in readme
    assert "FUNC-SPRINT-74 — ADR de release, versionado y productización" in readme
    assert "FUNC-SPRINT-74 — Operación de release, versionado y productización" in runbook
    assert 'source_repo: "repo_DevPilot_Local_99.zip"' in backlog_g
    assert 'last_completed_sprint: "FUNC-SPRINT-77"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-78"' in backlog_g
    assert 'phase_g_status: "in_progress"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-78"' in functional_backlog


def test_sprint_74_policy_and_artifact_matrix_define_release_boundaries() -> None:
    adr = _read("docs/02_architecture/adrs/ADR-0014-release-versioning-packaging.md")
    policy = _read("docs/05_operations/release_policy.md")
    matrix = _read("docs/05_operations/release_artifacts_matrix.md")
    audit = _read("docs/audits/func_sprint_74_release_versioning_audit.md")

    for text in [adr, policy, matrix]:
        assert "local-first" in text
        assert "PyPI" in text
        assert ".devpilot/devpilot.db" in text
        assert "outputs/" in text
        assert "SBOM" in text
        assert "checksums" in text

    assert "Publicación externa queda fuera de alcance" in audit
    assert "Veredicto: `PASS`" in audit
    assert "primera versión estratégica" in audit


def test_sprint_74_manifest_declares_strategy_only_no_runtime_commands() -> None:
    manifest = _json("docs/functional_sprint_74_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-74"
    assert manifest["status"] == "implemented"
    assert manifest["phase"] == "FASE-G-PRODUCTIZACION-RELEASE"
    assert manifest["summary"]["release_strategy_defined"] is True
    assert manifest["summary"]["versioning_policy_defined"] is True
    assert manifest["summary"]["artifact_matrix_defined"] is True
    assert manifest["summary"]["external_publication_out_of_scope"] is True
    assert manifest["summary"]["commands_added"] is False
    assert manifest["summary"]["dependencies_added"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-75")
