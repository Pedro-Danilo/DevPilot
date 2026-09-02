from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.docs_governance import run_docs_governance_quality_subgate
from devpilot_core.quality import QualityGate, QualityGateOptions

ROOT = Path(__file__).resolve().parents[1]


def test_docs_governance_quality_subgate_wraps_validator_read_only() -> None:
    result = run_docs_governance_quality_subgate(ROOT)

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    assert result.command == "quality docs-governance"
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-009-E"
    assert summary["quality_gate_subgate"] == "docs-governance"
    assert summary["docs_governance_passed"] is True
    assert summary["frontmatter_status_ownership_passed"] is True
    assert summary["markdown_json_sync_passed"] is True
    assert summary["roadmap_markdown_json_sync_passed"] is True
    assert summary["backlog_governance_passed"] is True
    assert summary["blocking_findings_total"] == 0
    assert summary["reports_written"] is False
    assert summary["read_only"] is True
    assert summary["dry_run"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["llm_judge_used"] is False


def test_quality_gate_hardening_includes_docs_governance_subgate() -> None:
    plan = QualityGate(ROOT, options=QualityGateOptions(profile="hardening")).describe_plan().to_dict()
    subgates = {item["id"]: item for item in plan["subgates"]}
    assert "docs-governance" in subgates
    assert subgates["docs-governance"]["critical"] is True
    assert subgates["docs-governance"]["execution_mode"] == "component"

