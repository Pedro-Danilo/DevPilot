from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from devpilot_core.rag import LocalRagIndexer, LocalRagRetriever, RagIndexOptions, RagQueryOptions
from devpilot_core.release.package_builder import _is_excluded
from devpilot_core.release.verification import _contains_forbidden_marker

ROOT = Path(__file__).resolve().parents[1]


def test_rag_indexer_creates_local_lexical_index_with_sources(tmp_path: Path) -> None:
    root = tmp_path
    docs = root / "docs"
    docs.mkdir()
    (docs / "readiness.md").write_text("# Readiness strict\n\nReadiness strict valida documentos, estándares y MIASI.\n", encoding="utf-8")
    (root / ".env").write_text("SECRET=sk-test-secret-value", encoding="utf-8")

    result = LocalRagIndexer(root, options=RagIndexOptions(target="docs", index_path=".devpilot/rag/docs_index.json", chunk_lines=10)).build()

    assert result.ok is True
    assert result.data["summary"]["network_used"] is False
    assert result.data["summary"]["external_api_used"] is False
    assert result.data["summary"]["embeddings_enabled"] is False
    index_path = root / ".devpilot/rag/docs_index.json"
    assert index_path.exists()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["summary"]["chunks_total"] >= 1
    assert index["chunks"][0]["source"]["path"] == "docs/readiness.md"
    assert "SECRET" not in json.dumps(index, ensure_ascii=False)


def test_rag_query_returns_grounded_sources(tmp_path: Path) -> None:
    root = tmp_path
    docs = root / "docs"
    docs.mkdir()
    (docs / "readiness.md").write_text(
        "# Readiness strict\n\nReadiness strict valida documentos aprobados, estándares, checklist y MIASI.\n",
        encoding="utf-8",
    )
    LocalRagIndexer(root, options=RagIndexOptions(target="docs", index_path=".devpilot/rag/docs_index.json", chunk_lines=10)).build()

    result = LocalRagRetriever(root, options=RagQueryOptions(query="Qué valida readiness strict", index_path=".devpilot/rag/docs_index.json", top_k=3)).query()

    assert result.ok is True
    assert result.data["summary"]["grounded"] is True
    assert result.data["summary"]["sources_total"] >= 1
    assert result.data["answer"]["source_refs"]
    first = result.data["sources"][0]
    assert first["path"] == "docs/readiness.md"
    assert first["line_start"] >= 1
    assert first["ref"].startswith("docs/readiness.md#L")


def test_rag_query_fails_closed_without_sources(tmp_path: Path) -> None:
    root = tmp_path
    docs = root / "docs"
    docs.mkdir()
    (docs / "x.md").write_text("# Arquitectura\n\nComponentes locales.", encoding="utf-8")
    LocalRagIndexer(root, options=RagIndexOptions(target="docs", index_path=".devpilot/rag/docs_index.json", chunk_lines=10)).build()

    result = LocalRagRetriever(root, options=RagQueryOptions(query="zzzinexistente", index_path=".devpilot/rag/docs_index.json")).query()

    assert result.ok is False
    assert result.data["summary"]["answer_generated"] is False
    assert result.data["sources"] == []
    assert result.findings[0].id == "RAG_QUERY_NO_SOURCES"


def test_rag_cli_index_and_query_json(tmp_path: Path) -> None:
    # The CLI contract must never regenerate the tracked repository index.
    # A dedicated disposable workspace makes the mutation explicit and isolated.
    root = tmp_path / "rag-cli-workspace"
    docs = root / "docs"
    docs.mkdir(parents=True)
    (docs / "readiness.md").write_text(
        "# Readiness strict\n\nReadiness strict valida documentos aprobados, estándares, checklist y MIASI.\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")

    index = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "rag", "index", "--target", "docs", "--json"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert index.returncode == 0, index.stderr or index.stdout
    index_payload = json.loads(index.stdout)
    assert index_payload["ok"] is True
    assert index_payload["data"]["summary"]["chunks_total"] > 0
    assert (root / ".devpilot/rag/docs_index.json").is_file()

    query = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "rag", "query", "Qué valida readiness strict", "--json"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert query.returncode == 0, query.stderr or query.stdout
    query_payload = json.loads(query.stdout)
    assert query_payload["ok"] is True
    assert query_payload["data"]["summary"]["sources_total"] > 0
    assert query_payload["data"]["answer"]["source_refs"]


def test_rag_runtime_index_is_excluded_from_release_package() -> None:
    assert _is_excluded(".devpilot/rag/docs_index.json") is True
    assert _contains_forbidden_marker("devpilot/.devpilot/rag/docs_index.json") is True
