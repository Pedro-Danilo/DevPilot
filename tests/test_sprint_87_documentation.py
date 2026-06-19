from __future__ import annotations

import json
from pathlib import Path


def test_sprint_87_artifacts_exist_and_are_synced() -> None:
    root = Path.cwd()
    expected = [
        "src/devpilot_core/rag/__init__.py",
        "src/devpilot_core/rag/indexer.py",
        "src/devpilot_core/rag/retriever.py",
        "docs/06_miasi/rag_card.md",
        "docs/audits/func_sprint_87_rag_local_audit.md",
        "docs/functional_sprint_87_manifest.json",
        "tests/test_rag_local.py",
    ]
    for rel in expected:
        assert (root / rel).exists(), rel

    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "Último hito: `FUNC-SPRINT-96" in readme
    assert "Siguiente hito: `FUNC-SPRINT-97" in readme
    assert "rag index" in readme
    assert "rag query" in readme

    backlog = (root / "docs/devpilot_backlog_fase_H_capacidades_avanzadas.md").read_text(encoding="utf-8")
    assert 'last_completed_sprint: "FUNC-SPRINT-96"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-97"' in backlog
    assert "Estado de implementación Sprint 87" in backlog


def test_sprint_87_manifest_declares_rag_boundaries() -> None:
    manifest = json.loads(Path("docs/functional_sprint_87_manifest.json").read_text(encoding="utf-8"))
    summary = manifest["summary"]
    assert manifest["sprint"] == "FUNC-SPRINT-87"
    assert summary["rag_indexer_added"] is True
    assert summary["rag_cli_query_added"] is True
    assert summary["citations_required"] is True
    assert summary["secret_guard_integrated"] is True
    assert summary["path_guard_integrated"] is True
    assert summary["lexical_index"] is True
    assert summary["embeddings_enabled"] is False
    assert summary["external_api_used"] is False
    assert summary["dependencies_added"] is False


def test_sprint_87_docs_define_pass_block_and_security() -> None:
    card = Path("docs/06_miasi/rag_card.md").read_text(encoding="utf-8")
    audit = Path("docs/audits/func_sprint_87_rag_local_audit.md").read_text(encoding="utf-8")
    runbook = Path("docs/05_operations/runbook.md").read_text(encoding="utf-8")
    assert "Criterios PASS" in card
    assert "Criterios BLOCK" in card
    assert "fuentes" in card.lower()
    assert "SecretGuard" in card
    assert "LocalRagIndexer" in audit
    assert "rag index" in runbook
    assert "rag query" in runbook


def test_sprint_87_miasi_registry_declares_rag_tools_and_policy() -> None:
    tools = json.loads(Path(".devpilot/miasi/tool_registry.json").read_text(encoding="utf-8"))["tools"]
    rules = json.loads(Path(".devpilot/miasi/policy_matrix.json").read_text(encoding="utf-8"))["rules"]
    assert any(tool["tool_id"] == "rag.index" for tool in tools)
    assert any(tool["tool_id"] == "rag.query" for tool in tools)
    assert any(rule["rule_id"] == "RAG_INDEX_LOCAL_ALLOW" for rule in rules)
    assert any(rule["rule_id"] == "RAG_QUERY_LOCAL_ALLOW" for rule in rules)


def test_sprint_87_changelog_and_functional_backlog_are_synced() -> None:
    changelog = Path("docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    functional = Path("docs/functional_backlog_after_precode.md").read_text(encoding="utf-8")
    assert "FUNC-SPRINT-87" in changelog
    assert "RAG documental local" in changelog
    assert 'next_sprint: "FUNC-SPRINT-97"' in functional
    assert "Transición posterior a FUNC-SPRINT-87" in functional
