from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_80_sbom_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog_g = _read("docs/devpilot_backlog_fase_G_productizacion_release.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    for path in [
        "src/devpilot_core/release/sbom.py",
        "docs/03_security/supply_chain_policy.md",
        "docs/audits/func_sprint_80_sbom_supply_chain_audit.md",
        "docs/functional_sprint_80_manifest.json",
        "tests/test_release_sbom.py",
        "tests/test_sprint_80_documentation.py",
    ]:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-96" in readme
    assert "Siguiente hito: `FUNC-SPRINT-97" in readme
    assert "FUNC-SPRINT-80 — SBOM y supply-chain baseline" in readme
    assert "FUNC-SPRINT-80 — Operación de SBOM" in runbook
    assert 'source_repo: "repo_DevPilot_Local_106.zip"' in backlog_g
    assert 'last_completed_sprint: "FUNC-SPRINT-84"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-85"' in backlog_g
    assert 'phase_g_status: "closed"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-97"' in functional_backlog


def test_sprint_80_docs_define_supply_chain_boundaries() -> None:
    policy = _read("docs/03_security/supply_chain_policy.md")
    audit = _read("docs/audits/func_sprint_80_sbom_supply_chain_audit.md")
    release_manifest = _read("docs/05_operations/release_manifest.md")
    changelog = _read("docs/release/CHANGELOG.md")

    for text in [policy, audit, release_manifest, changelog]:
        assert "SBOM" in text
        assert "FUNC-SPRINT-80" in text

    for marker in ["pyproject.toml", "ui/web/package.json", "ui/web/package-lock.json", "CycloneDX", "vulnerability scan", "license scan"]:
        assert marker in policy

    assert "outputs/reports/release_sbom" in policy
    assert "FUNC-SPRINT-80` — `docs/functional_sprint_80_manifest.json`" in changelog


def test_sprint_80_manifest_declares_sbom_scope() -> None:
    manifest = _json("docs/functional_sprint_80_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-80"
    assert manifest["status"] == "implemented"
    assert manifest["phase"] == "FASE-G-PRODUCTIZACION-RELEASE"
    assert manifest["summary"]["fg_level"] == "FG-L5"
    assert manifest["summary"]["release_sbom_cli_added"] is True
    assert manifest["summary"]["release_sbom_model_added"] is True
    assert manifest["summary"]["supply_chain_policy_added"] is True
    assert manifest["summary"]["cyclonedx_compatible_baseline"] is True
    assert manifest["summary"]["network_used"] is False
    assert manifest["summary"]["external_api_used"] is False
    assert manifest["summary"]["vulnerability_scan_performed"] is False
    assert manifest["summary"]["license_scan_performed"] is False
    assert manifest["summary"]["dependencies_added"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-81")
