from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _frontmatter_fields(relative_path: str) -> dict[str, str]:
    text = _read(relative_path)
    assert text.startswith("---\n"), relative_path
    end = text.split("\n---\n", 1)[0]
    fields: dict[str, str] = {}
    for line in end.splitlines()[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    return fields


def test_sprint_20_reconciliation_artifacts_exist_with_required_frontmatter() -> None:
    """Validate the documentary contract created by FUNC-SPRINT-20.

    Purpose: ensure the reconciliation artifacts are present and traceable.
    Integration: these artifacts synchronize README, runbook, roadmap and C4.
    PASS: each artifact has doc_id, title, status, version, owner, updated and approval.
    BLOCK: missing metadata would make the sprint non-auditable.
    Risk: this is structural validation, not semantic proof of all statements.
    """

    for relative_path in [
        "docs/audits/capability_status_matrix_after_sprint_18.md",
        "docs/audits/roadmap_reconciliation_after_sprint_18.md",
        "docs/02_architecture/c4_component.md",
    ]:
        fields = _frontmatter_fields(relative_path)
        for key in ["doc_id", "title", "status", "version", "owner", "updated", "approval"]:
            assert key in fields, f"{key} missing in {relative_path}"
        assert fields["phase"] == "FUNC-SPRINT-20"


def test_readme_and_runbook_preserve_sprint_20_reconciliation_context() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")

    # Sprint 20 is now historical once later Fase A sprints advance. The
    # regression should protect the reconciliation section and handoff, not
    # freeze README/runbook forever at Sprint 20 as the latest hito.
    assert "## Reconciliación documental post-18 — FUNC-SPRINT-20" in readme
    assert "FUNC-SPRINT-20` reconcilió README" in readme
    assert "## FUNC-SPRINT-20 — Reconciliación documental post-18 y roadmap vivo" in runbook
    assert "FUNC-SPRINT-21 — Schema Registry" in runbook
    assert "implemented`, `implemented-initial`, `partial`, `planned`, `disabled` y `future`" in runbook


def test_capability_matrix_declares_required_state_taxonomy() -> None:
    text = _read("docs/audits/capability_status_matrix_after_sprint_18.md")
    for state in ["implemented", "implemented-initial", "partial", "planned", "disabled", "future"]:
        assert f"`{state}`" in text

    assert "ModelAdapter" in text
    assert "`partial`" in text
    assert "External APIs" in text or "APIs externas" in text
    assert "`disabled`" in text
    assert "Desktop/Web" in text
    assert "`future`" in text


def test_roadmap_reconciliation_maps_historical_names_to_real_status() -> None:
    text = _read("docs/audits/roadmap_reconciliation_after_sprint_18.md")
    required_fragments = [
        "`policy-check`",
        "`policy check ... --json`",
        "`repo-scan`",
        "`repo-inventory --json`",
        "`review-code --dry-run`",
        "`code-review --target <path> --json`",
        "`git-diff-report`",
        "No implementado",
        "`validate-schema`",
        "`approval request/list/approve`",
    ]
    for fragment in required_fragments:
        assert fragment in text


def test_c4_views_expose_reconciled_states() -> None:
    for relative_path in [
        "docs/02_architecture/c4_context.md",
        "docs/02_architecture/c4_container.md",
        "docs/02_architecture/c4_component.md",
    ]:
        text = _read(relative_path)
        assert "FUNC-SPRINT-20" in text
        for state in ["implemented", "planned", "disabled", "future"]:
            assert f"`{state}`" in text or f"{state}]" in text or f"{state}<" in text

    component = _read("docs/02_architecture/c4_component.md")
    assert "ModelAdapter" in component
    assert "MockModelAdapter" in component
    assert "External APIs" in component
    assert "Desktop UI" in component
    assert "Web UI/API" in component


def test_sprint_20_manifest_is_scoped_to_documentation_reconciliation() -> None:
    payload = json.loads(_read("docs/functional_sprint_20_manifest.json"))

    assert payload["sprint"] == "FUNC-SPRINT-20"
    assert payload["status"] == "implemented"
    assert payload["adr_required"] is False
    assert "docs/02_architecture/c4_component.md" in payload["created_files"]
    assert "README.md" in payload["modified_files"]
    assert payload["next_sprint"].startswith("FUNC-SPRINT-21")
    assert any("does not implement schemas" in note.lower() for note in payload["preliminary_notes"])


def test_product_roadmap_is_marked_as_historical_and_reconciled() -> None:
    text = _read("docs/00_product/product_roadmap.md")

    assert "roadmap histórico + reconciliado" in text.lower()
    assert "docs/audits/roadmap_reconciliation_after_sprint_18.md" in text
    assert "policy-check" in text
    assert "no deben asumirse como comandos implementados" in text
