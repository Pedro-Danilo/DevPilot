from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.docs_governance import DocumentationGovernanceValidator, load_documentation_source_registry

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read(path))


def test_post_h_011_backlog_is_approved_and_schema_fixtures_are_documented() -> None:
    backlog = read("docs/backlogs/POST-H-011_rag_groundedness_evals.md")
    mirror = read("docs/POST-H-011_rag_groundedness_evals.md")
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")

    assert backlog == mirror
    assert 'status: "approved"' in backlog
    assert 'approval: "approved_by_owner"' in backlog
    assert 'implementation_status: "active"' in backlog
    assert 'current_micro_sprint: "POST-H-011-B"' in backlog
    assert 'next_micro_sprint: "POST-H-011-C"' in backlog
    assert "## 14. Avance de implementación — POST-H-011-A" in backlog
    assert "docs/schemas/rag_groundedness_eval.schema.json" in backlog
    assert "docs/schemas/rag_groundedness_report.schema.json" in backlog
    assert "evals/fixtures/rag_groundedness_post_h_cases.json" in backlog
    assert "tests/test_rag_groundedness_schema.py" in backlog
    assert "src/devpilot_core/rag/citations.py" in backlog
    assert "tests/test_rag_citations_source_coverage.py" in backlog
    assert "## 15. Avance de implementación — POST-H-011-B" in backlog
    assert "POST-H-011-B — Citation extractor y source coverage" in readme
    assert "POST-H-011-B — Citation extractor y source coverage" in runbook
    assert "post-h-011-a" in changelog
    assert "post-h-011-b" in changelog


def test_post_h_011_source_registry_and_docs_governance_pass() -> None:
    registry = load_documentation_source_registry(ROOT)
    by_path = registry.by_path()
    doc = by_path["docs/backlogs/POST-H-011_rag_groundedness_evals.md"]

    assert doc.doc_id == "POST-H-011-BACKLOG"
    assert doc.status_required == "approved"
    assert doc.lifecycle == "active"
    assert "docs/POST-H-011_rag_groundedness_evals.md" in doc.derived_documents
    assert "docs/audits/post_h_011_a_schema_fixtures_report.md" in doc.derived_documents
    assert "docs/post_h_011_a_manifest.json" in doc.derived_documents
    assert "docs/audits/post_h_011_b_citation_source_coverage_report.md" in doc.derived_documents
    assert "docs/post_h_011_b_manifest.json" in doc.derived_documents
    assert "tests/test_rag_groundedness_schema.py" in doc.required_tests
    assert "tests/test_rag_citations_source_coverage.py" in doc.required_tests
    assert "tests/test_post_h_011_rag_groundedness.py" in doc.required_tests
    assert "tests/test_documentation_governance_backlogs.py" in doc.required_tests

    result = DocumentationGovernanceValidator(ROOT).run()
    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["docs_governance_passed"] is True
    assert summary["backlog_governance_passed"] is True
    assert summary["blocking_findings_total"] == 0


def test_post_h_011_a_tcr_contracts_are_registered() -> None:
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-011-rag-groundedness-schema-fixtures")
    assert contract["owner"] == "POST-H-011-A"
    assert "tests/test_rag_groundedness_schema.py" in contract["test_files"]
    assert "evals/fixtures/rag_groundedness_post_h_cases.json" in contract["validates"]
    assert "docs/schemas/rag_groundedness_eval.schema.json" in contract["validates"]
    assert "docs/schemas/rag_groundedness_report.schema.json" in contract["validates"]
    assert contract["mutable_global_state_allowed"] is False

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-011-rag-groundedness-schema-fixtures")
    assert contract_v2["domain"] == "knowledge.rag"
    assert contract_v2["capability"] == "RagGroundednessSchemaFixtures"
    assert contract_v2["criticality"] == "P1"
    assert contract_v2["risk_level"] == "high"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["mutations_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False



def test_post_h_011_b_tcr_contracts_are_registered() -> None:
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-011-rag-citation-source-coverage")
    assert contract["owner"] == "POST-H-011-B"
    assert "tests/test_rag_citations_source_coverage.py" in contract["test_files"]
    assert "src/devpilot_core/rag/citations.py" in contract["validates"]
    assert "docs/audits/post_h_011_b_citation_source_coverage_report.md" in contract["validates"]
    assert contract["mutable_global_state_allowed"] is False

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-011-rag-citation-source-coverage")
    assert contract_v2["domain"] == "knowledge.rag"
    assert contract_v2["capability"] == "RagCitationSourceCoverage"
    assert contract_v2["criticality"] == "P1"
    assert contract_v2["risk_level"] == "high"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["mutations_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False

def test_post_h_011_a_project_state_notes_are_synchronized() -> None:
    state = read_json(".devpilot/project_state.json")
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")

    assert state["last_completed_sprint"] == "POST-H-010"
    assert state["next_sprint"] == "POST-H-011"
    assert state["current_repo"] == "repo_DevPilot_Local_188_POST_H_011_B.zip"
    assert any("POST-H-011-B adds local citation extraction" in note for note in state["notes"])
    assert "Último micro-sprint implementado: `POST-H-011-B" in readme
    assert "POST-H-011-B — Citation extractor y source coverage" in runbook
