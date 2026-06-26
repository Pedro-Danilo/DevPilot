from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.docs_governance import DocumentationBacklogGovernanceValidator, DocumentationGovernanceValidator, load_documentation_source_registry

ROOT = Path(__file__).resolve().parents[1]


def test_documentation_backlog_governance_passes_baseline() -> None:
    registry = load_documentation_source_registry(ROOT)
    result = DocumentationBacklogGovernanceValidator(ROOT, registry).run()
    summary = result["summary"]

    assert summary["backlog_governance_passed"] is True
    assert summary["backlogs_expected_total"] == 24
    assert summary["backlogs_checked_total"] == 24
    assert summary["backlogs_registered_total"] == 24
    assert summary["backlogs_existing_total"] == 24
    assert summary["backlogs_planned_missing_total"] == 0
    assert summary["backlog_frontmatter_checked_total"] == 24
    assert summary["backlog_milestone_match_checked_total"] == 24
    assert summary["backlog_governance_blocking_findings_total"] == 0

    checks = result["backlog_checks"]
    by_milestone = {item["milestone"]: item for item in checks}
    assert by_milestone["POST-H-002"]["classification"] == "derived"
    assert by_milestone["POST-H-009"]["classification"] == "source-of-truth"
    assert by_milestone["POST-H-025"]["expected_priority"] == "P0"
    assert by_milestone["POST-H-025"]["frontmatter_priority"] == "P0"


def test_documentation_governance_validate_includes_backlog_governance() -> None:
    result = DocumentationGovernanceValidator(ROOT).run()
    summary = result.data["summary"]

    assert result.ok, result.to_dict()
    assert summary["created_by"] == "POST-H-009-D"
    assert summary["backlog_governance_passed"] is True
    assert summary["backlogs_expected_total"] == 24
    assert summary["backlogs_registered_total"] == 24
    assert summary["backlogs_checked_total"] == 24
    assert len(result.data["governance"]["backlog_checks"]) == 24


def test_documentation_governance_report_command_includes_backlog_checks(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["docs-governance", "report", "--write-report", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "docs-governance report"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["created_by"] == "POST-H-009-D"
    assert payload["data"]["summary"]["backlog_governance_passed"] is True
    assert payload["data"]["summary"]["backlogs_checked_total"] == 24
    assert len(payload["data"]["governance"]["backlog_checks"]) == 24


def test_backlog_governance_reports_missing_future_backlog_as_info(tmp_path: Path) -> None:
    root = tmp_path
    (root / ".devpilot/evals").mkdir(parents=True)
    (root / ".devpilot/docs_governance").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "tests/test_backlog.py").write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")

    (root / ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json").write_text(
        json.dumps(
            {
                "executable_backlogs_to_create": [
                    {"milestone": "POST-H-099", "path": "docs/backlogs/POST-H-099_future_backlog.md", "priority": "P3"}
                ]
            }
        ),
        encoding="utf-8",
    )
    registry_payload = {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-DOCUMENTATION-SOURCE-REGISTRY-V1",
        "registry_id": "tmp-docs-registry",
        "created_by": "TEST",
        "status": "implemented-initial",
        "documents": [
            {
                "doc_id": "POST-H-099-BACKLOG",
                "path": "docs/backlogs/POST-H-099_future_backlog.md",
                "classification": "derived",
                "domain": "roadmap-derived-backlog",
                "owner": "Ordóñez",
                "status_required": "planned",
                "criticality": "P3",
                "required_tests": ["tests/test_backlog.py"],
                "sync_rules": ["backlog_naming", "backlog_frontmatter_minimum", "backlog_milestone_match"],
                "lifecycle": "planned",
            }
        ],
        "summary": {},
        "rules": {},
        "safety": {},
    }
    (root / ".devpilot/docs_governance/source_registry.json").write_text(json.dumps(registry_payload), encoding="utf-8")

    registry = load_documentation_source_registry(root)
    result = DocumentationBacklogGovernanceValidator(root, registry).run()

    assert result["summary"]["backlog_governance_passed"] is True
    assert result["summary"]["backlogs_planned_missing_total"] == 1
    assert any(finding["id"] == "DOCUMENTATION_BACKLOG_PLANNED_MISSING" and finding["severity"] == "info" for finding in result["findings"])


def test_backlog_governance_blocks_priority_drift(tmp_path: Path) -> None:
    root = tmp_path
    (root / ".devpilot/evals").mkdir(parents=True)
    (root / ".devpilot/docs_governance").mkdir(parents=True)
    (root / "docs/backlogs").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "tests/test_backlog.py").write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")
    path = root / "docs/backlogs/POST-H-099_future_backlog.md"
    path.write_text(
        "---\n"
        "doc_id: \"POST-H-099-BACKLOG\"\n"
        "id: \"POST-H-099\"\n"
        "title: \"POST-H-099 — Future backlog\"\n"
        "status: \"draft\"\n"
        "version: \"0.1.0\"\n"
        "owner: \"Ordóñez\"\n"
        "updated: \"2026-06-26\"\n"
        "approval: \"pending_owner_review\"\n"
        "priority: \"P2\"\n"
        "roadmap_source: \"docs/backlogs/post_h_prioritized_roadmap.md\"\n"
        "---\n"
        "# Future backlog\n",
        encoding="utf-8",
    )
    (root / ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json").write_text(
        json.dumps(
            {
                "executable_backlogs_to_create": [
                    {"milestone": "POST-H-099", "path": "docs/backlogs/POST-H-099_future_backlog.md", "priority": "P3"}
                ]
            }
        ),
        encoding="utf-8",
    )
    registry_payload = {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-DOCUMENTATION-SOURCE-REGISTRY-V1",
        "registry_id": "tmp-docs-registry",
        "created_by": "TEST",
        "status": "implemented-initial",
        "documents": [
            {
                "doc_id": "POST-H-099-BACKLOG",
                "path": "docs/backlogs/POST-H-099_future_backlog.md",
                "classification": "derived",
                "domain": "roadmap-derived-backlog",
                "owner": "Ordóñez",
                "status_required": "draft",
                "criticality": "P3",
                "required_tests": ["tests/test_backlog.py"],
                "sync_rules": ["backlog_naming", "backlog_frontmatter_minimum", "backlog_milestone_match"],
                "lifecycle": "planned",
            }
        ],
        "summary": {},
        "rules": {},
        "safety": {},
    }
    (root / ".devpilot/docs_governance/source_registry.json").write_text(json.dumps(registry_payload), encoding="utf-8")

    registry = load_documentation_source_registry(root)
    result = DocumentationBacklogGovernanceValidator(root, registry).run()

    assert result["summary"]["backlog_governance_passed"] is False
    assert any(finding["id"] == "DOCUMENTATION_BACKLOG_PRIORITY_MISMATCH" for finding in result["findings"])
