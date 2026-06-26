from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.docs_governance import DocumentationGovernanceValidationOptions, DocumentationGovernanceValidator

ROOT = Path(__file__).resolve().parents[1]


def test_documentation_governance_sync_passes_baseline() -> None:
    result = DocumentationGovernanceValidator(ROOT).run()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-009-E"
    assert summary["markdown_json_sync_passed"] is True
    assert summary["roadmap_markdown_json_sync_passed"] is True
    assert summary["markdown_json_pairs_checked_total"] >= 7
    assert summary["version_match_checked_total"] == 1
    assert summary["milestones_match_checked_total"] == 1
    assert summary["decisions_match_checked_total"] == 1
    assert summary["closure_status_match_checked_total"] == 1
    assert summary["next_hito_match_checked_total"] >= 3
    assert summary["drift_findings_total"] == 0
    assert summary["blocking_findings_total"] == 0

    sync_checks = result.data["governance"]["sync_checks"]
    milestones_check = next(item for item in sync_checks if item["rule"] == "milestones_match")
    assert milestones_check["critical_milestones_present_in_both"] is True
    assert "POST-H-024" in milestones_check["critical_milestones_checked"]
    assert "POST-H-025" in milestones_check["critical_milestones_checked"]

    decisions_check = next(item for item in sync_checks if item["rule"] == "decisions_match")
    assert decisions_check["critical_decisions_present_in_both"] is True
    assert "DEC-POSTH-008" in decisions_check["critical_decisions_checked"]
    assert "DEC-POSTH-009" in decisions_check["critical_decisions_checked"]


def test_documentation_governance_report_command_writes_sync_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["docs-governance", "report", "--write-report", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "docs-governance report"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["created_by"] == "POST-H-009-E"
    assert payload["data"]["summary"]["reports_written"] is True
    assert payload["data"]["summary"]["markdown_json_sync_passed"] is True
    assert payload["data"]["summary"]["backlog_governance_passed"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/documentation_governance_report.json"
    assert payload["data"]["reports"]["markdown"] == "outputs/reports/documentation_governance_report.md"


def test_documentation_governance_sync_blocks_missing_roadmap_milestone(tmp_path: Path) -> None:
    root = tmp_path
    (root / ".devpilot/docs_governance").mkdir(parents=True)
    (root / ".devpilot/evals").mkdir(parents=True)
    (root / "docs/backlogs").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "tests/test_sync.py").write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")

    (root / "docs/backlogs/post_h_prioritized_roadmap.md").write_text(
        "---\n"
        "doc_id: \"POSTH-ROADMAP-001\"\n"
        "title: \"Roadmap\"\n"
        "status: \"approved\"\n"
        "version: \"1.1.0\"\n"
        "owner: \"Ordóñez\"\n"
        "updated: \"2026-06-26\"\n"
        "approval: \"approved_by_owner\"\n"
        "---\n"
        "# Roadmap\n\nPOST-H-024\nPOST-H-025\nDEC-POSTH-008\nDEC-POSTH-009\n",
        encoding="utf-8",
    )
    (root / ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json").write_text(
        json.dumps(
            {
                "version": "1.1.0",
                "status": "implemented",
                "waves": [{"milestones": ["POST-H-024"]}],
                "executable_backlogs_to_create": [{"milestone": "POST-H-024"}],
                "decisions": [{"id": "DEC-POSTH-008"}, {"id": "DEC-POSTH-009"}],
            }
        ),
        encoding="utf-8",
    )
    registry = {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-DOCUMENTATION-SOURCE-REGISTRY-V1",
        "registry_id": "tmp-docs-registry",
        "created_by": "TEST",
        "status": "implemented-initial",
        "documents": [
            {
                "doc_id": "POSTH-ROADMAP-001",
                "path": "docs/backlogs/post_h_prioritized_roadmap.md",
                "classification": "source-of-truth",
                "domain": "roadmap",
                "owner": "Ordóñez",
                "status_required": "approved",
                "criticality": "P0",
                "required_tests": ["tests/test_sync.py"],
                "machine_readable_counterparts": [".devpilot/evals/post_h_eval_001_prioritized_roadmap.json"],
                "sync_rules": ["version_match", "milestones_match", "decisions_match"],
                "lifecycle": "active",
            }
        ],
        "summary": {},
        "rules": {},
        "safety": {},
    }
    (root / ".devpilot/docs_governance/source_registry.json").write_text(json.dumps(registry), encoding="utf-8")

    result = DocumentationGovernanceValidator(root, DocumentationGovernanceValidationOptions()).run()

    assert not result.ok
    assert result.exit_code.value == 2
    assert any(finding.id == "DOCUMENTATION_SYNC_MILESTONES_MISMATCH" for finding in result.findings)
    assert any(finding.id == "DOCUMENTATION_SYNC_CRITICAL_MILESTONES_MISSING" for finding in result.findings)
