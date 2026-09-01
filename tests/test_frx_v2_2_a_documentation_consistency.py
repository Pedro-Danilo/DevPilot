from __future__ import annotations

import hashlib
import json
from pathlib import Path

from devpilot_core.docs_governance import (
    ClosureStateConsistencyValidator,
    DerivedMetadataProjection,
    DocImpactPlanner,
    DocumentationAuthorityGraph,
    DocumentationDriftLedger,
    DocumentationGovernanceValidator,
)
from devpilot_core.validators.frontmatter import parse_frontmatter_file, validate_frontmatter_document

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_NORMALIZED_LF_SHA256_AT_REPO386_CLOSE = "b5808c22f5238865f5bcb06090b067a6a9133cfbb19972d7f7f1a99ce86f1e9b"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_frx_v2_2_a_successor_has_zero_p0_p1_closure_drift() -> None:
    result = ClosureStateConsistencyValidator(ROOT).run()
    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["closure_state_consistency_passed"] is True
    assert summary["drift_p0_p1_open_total"] == 0
    assert summary["full_regression_runs_consumed"] == 1


def test_repo386_style_negative_fixture_is_blocked_before_expensive_testing(tmp_path: Path) -> None:
    # Reproduces the exact class of drift discovered in repo386:
    # Project State CLOSED/PASS while backlog frontmatter remains approved and README says implementation.
    (tmp_path / ".devpilot/docs_governance").mkdir(parents=True)
    (tmp_path / ".devpilot").mkdir(exist_ok=True)
    (tmp_path / "docs/release").mkdir(parents=True)
    (tmp_path / "tests").mkdir()

    backlog = tmp_path / "DEVPL-GSDLC-07_agent_assisted_engineering_and_rag_v1_4_0_APPROVED_REBOUND.md"
    backlog.write_text(
        "---\n"
        "doc_id: \"DEVPL-GSDLC-07\"\n"
        "title: \"Backlog 07\"\n"
        "status: \"approved\"\n"
        "version: \"1.4.0\"\n"
        "owner: \"Ordóñez\"\n"
        "updated: \"2026-08-31\"\n"
        "approval: \"approved_by_owner\"\n"
        "backlog_status: \"approved/executable-design\"\n"
        "---\n# Backlog\n",
        encoding="utf-8",
    )
    final = tmp_path / "DEVPL_GSDLC_07_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md"
    final.write_text(
        "---\n"
        "doc_id: \"DEVPL-GSDLC-07-BACKLOG-CLOSURE-ADJUDICATION\"\n"
        "title: \"Final closure\"\n"
        "status: \"closed\"\n"
        "version: \"1.0.0\"\n"
        "owner: \"Ordóñez\"\n"
        "updated: \"2026-08-31\"\n"
        "approval: \"approved_by_owner\"\n"
        "---\n# Final\n",
        encoding="utf-8",
    )
    proposal = tmp_path / "DEVPL_GSDLC_07_E_OWNER_ADJUDICATION_PROPOSAL_v1_0_0.md"
    proposal.write_text("historical proposal\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("DEVPL-GSDLC-07 está en implementación.\n", encoding="utf-8")
    (tmp_path / "docs/release/CHANGELOG.md").write_text("older changelog\n", encoding="utf-8")

    state = {
        "gsdlc_07_status": "CLOSED/PASS",
        "next_micro_sprint": "FULL-REGRESSION-v2.2-DISTRIBUCION-TEMPORAL-INTELIGENTE",
        "gsdlc_08_status": "authorized/deferred-by-owner",
        "gsdlc_07_e_full_regression_runs_consumed": 1,
    }
    _write_json(tmp_path / ".devpilot/project_state.json", state)

    docs = [
        {
            "doc_id": "DEVPL-GSDLC-07",
            "path": backlog.name,
            "classification": "source-of-truth",
            "domain": "governance.gsdlc",
            "owner": "DEVPL-GSDLC-07",
            "status_required": "approved",
            "criticality": "P0",
            "required_tests": ["tests/test_placeholder.py"],
            "sync_rules": [],
            "lifecycle": "active",
        },
        {
            "doc_id": "DEVPL-GSDLC-07-E-OWNER-ADJUDICATION-PROPOSAL",
            "path": proposal.name,
            "classification": "source-of-truth",
            "domain": "governance.gsdlc",
            "owner": "DEVPL-GSDLC-07-E",
            "status_required": "proposal",
            "criticality": "P0",
            "required_tests": ["tests/test_placeholder.py"],
            "sync_rules": [],
            "lifecycle": "active",
        },
    ]
    (tmp_path / "tests/test_placeholder.py").write_text("def test_placeholder(): assert True\n", encoding="utf-8")
    registry = {
        "documents": docs,
        "summary": DerivedMetadataProjection.source_registry_summary({"documents": docs}),
    }
    _write_json(tmp_path / ".devpilot/docs_governance/source_registry.json", registry)
    _write_json(
        tmp_path / ".devpilot/docs_governance/documentation_drift_ledger.json",
        {"findings": [{"finding_id": "S2-DOC", "severity": "P1", "resolution_status": "open"}]},
    )
    _write_json(
        tmp_path / ".devpilot/docs_governance/documentation_authority_graph.json",
        {
            "nodes": [
                {"node_id": "state", "doc_id": "PROJECT-GLOBAL-STATE", "path": ".devpilot/project_state.json", "subject": "DEVPL-GSDLC-07-closure", "authority_rank": 100, "authority_kind": "current-active", "lifecycle": "active", "classification": "machine-readable-source"},
                {"node_id": "backlog", "doc_id": "DEVPL-GSDLC-07", "path": backlog.name, "subject": "DEVPL-GSDLC-07-closure", "authority_rank": 90, "authority_kind": "current-active", "lifecycle": "active", "classification": "source-of-truth"},
                {"node_id": "proposal", "doc_id": "DEVPL-GSDLC-07-E-OWNER-ADJUDICATION-PROPOSAL", "path": proposal.name, "subject": "DEVPL-GSDLC-07-closure", "authority_rank": 10, "authority_kind": "current-active", "lifecycle": "active", "classification": "source-of-truth"},
                {"node_id": "final", "doc_id": "DEVPL-GSDLC-07-BACKLOG-CLOSURE-ADJUDICATION", "path": final.name, "subject": "DEVPL-GSDLC-07-closure", "authority_rank": 95, "authority_kind": "current-active", "lifecycle": "active", "classification": "source-of-truth"},
                {"node_id": "readme", "doc_id": "README", "path": "README.md", "subject": "DEVPL-GSDLC-07-closure", "authority_rank": 40, "authority_kind": "derived", "lifecycle": "active", "classification": "derived"},
                {"node_id": "changelog", "doc_id": "CHANGELOG", "path": "docs/release/CHANGELOG.md", "subject": "DEVPL-GSDLC-07-closure", "authority_rank": 30, "authority_kind": "derived", "lifecycle": "active", "classification": "derived"},
                {"node_id": "registry", "doc_id": "REGISTRY", "path": ".devpilot/docs_governance/source_registry.json", "subject": "DEVPL-GSDLC-07-closure", "authority_rank": 85, "authority_kind": "current-active", "lifecycle": "active", "classification": "machine-readable-source"},
            ],
            "closure_contracts": [
                {
                    "contract_id": "DEVPL-GSDLC-07",
                    "expected_closure": "CLOSED/PASS",
                    "project_state_field": "gsdlc_07_status",
                    "backlog_path": backlog.name,
                    "backlog_frontmatter_status": "closed",
                    "backlog_state_expected": "CLOSED/PASS",
                    "final_adjudication_path": final.name,
                    "final_adjudication_status": "closed",
                    "source_registry": {
                        "backlog_doc_id": "DEVPL-GSDLC-07",
                        "expected_status_required": "closed",
                        "expected_lifecycle": "closed",
                        "proposal_doc_id": "DEVPL-GSDLC-07-E-OWNER-ADJUDICATION-PROPOSAL",
                        "proposal_expected_classification": "historical",
                        "proposal_expected_lifecycle": "historical",
                        "final_adjudication_doc_id": "DEVPL-GSDLC-07-BACKLOG-CLOSURE-ADJUDICATION"
                    },
                    "readme_required_markers": ["DEVPL-GSDLC-07 = CLOSED/PASS", "FRX-v2.2-A"],
                    "changelog_required_markers": ["FRX-v2.2-A", "DEVPL-GSDLC-07"],
                    "next": {"project_state_expectations": {"next_micro_sprint": "FRX-v2.2-B", "gsdlc_08_status": "authorized/deferred-by-owner"}},
                }
            ],
        },
    )

    result = ClosureStateConsistencyValidator(tmp_path).run()
    assert not result.ok
    ids = {finding.id for finding in result.findings}
    assert any("BACKLOG_FRONTMATTER" in item for item in ids)
    assert any("PROPOSAL_HISTORICAL" in item for item in ids)
    assert any("README" in item for item in ids)
    assert result.data["summary"]["drift_p0_p1_open_total"] == 1


def test_historical_owner_proposal_content_is_preserved_semantically() -> None:
    path = ROOT / "DEVPL_GSDLC_07_E_OWNER_ADJUDICATION_PROPOSAL_v1_0_0.md"
    normalized = path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    assert hashlib.sha256(normalized).hexdigest() == PROPOSAL_NORMALIZED_LF_SHA256_AT_REPO386_CLOSE

    registry = json.loads((ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))
    entry = next(item for item in registry["documents"] if item["doc_id"] == "DEVPL-GSDLC-07-E-OWNER-ADJUDICATION-PROPOSAL")
    assert entry["classification"] == "historical"
    assert entry["lifecycle"] == "historical"


def test_current_source_registry_summary_is_derived_from_live_collection() -> None:
    payload = json.loads((ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))
    assert DerivedMetadataProjection.source_registry_mismatches(payload) == {}

    stale = json.loads(json.dumps(payload))
    stale["documents"].append({"classification": "derived", "criticality": "P2", "required_tests": []})
    mismatches = DerivedMetadataProjection.source_registry_mismatches(stale)
    assert "documents_total" in mismatches
    assert "derived_total" in mismatches


def test_doc_impact_planner_requires_consistency_gate_but_not_full_or_browser() -> None:
    result = DocImpactPlanner(ROOT, [".devpilot/project_state.json", "README.md"]).run()
    assert result.ok
    plan = result.data["plan"]
    assert plan["closure_consistency_required"] is True
    assert plan["full_regression_required"] is False
    assert plan["browser_required"] is False
    assert "tests/test_frx_v2_2_a_documentation_consistency.py" in plan["required_tests"]
    assert plan["summary"]["p0_p1_reconciliation_required"] is True


def test_authority_graph_and_ledger_are_explicit_and_current() -> None:
    graph = DocumentationAuthorityGraph(ROOT)
    assert graph.validate_paths() == []
    proposal = graph.by_node_id()["gsdlc07e-owner-proposal"]
    assert proposal.authority_kind == "historical-freeze"
    assert proposal.lifecycle == "historical"
    assert proposal.successor == "DEVPL_GSDLC_07_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md"

    ledger = DocumentationDriftLedger(ROOT)
    assert ledger.open_blocking_findings() == ()


def test_closed_frontmatter_is_a_governed_status() -> None:
    backlog = parse_frontmatter_file(ROOT / "DEVPL-GSDLC-07_agent_assisted_engineering_and_rag_v1_4_0_APPROVED_REBOUND.md")
    result = validate_frontmatter_document(backlog, root=ROOT)
    assert result.ok, result.to_dict()
    assert backlog.frontmatter["status"] == "closed"


def test_documentation_governance_includes_cross_authority_consistency() -> None:
    result = DocumentationGovernanceValidator(ROOT).run()
    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["closure_state_consistency_configured"] is True
    assert summary["closure_state_consistency_passed"] is True
    assert summary["documentation_drift_p0_p1_open_total"] == 0
