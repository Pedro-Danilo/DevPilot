from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.industrial.production_ready import (
    ProductionReadyEvidenceAggregator,
    ProductionReadyEvidenceAggregatorOptions,
)

ROOT = Path(__file__).resolve().parents[1]


def test_production_ready_evidence_aggregator_reads_current_repo_without_mutation() -> None:
    before = _tracked_snapshot(ROOT)

    result = ProductionReadyEvidenceAggregator(ROOT).aggregate()

    after = _tracked_snapshot(ROOT)
    assert result.ok, result.to_dict()
    assert before == after
    summary = result.data["summary"]
    assert summary["scope"] == "production-ready-local"
    assert summary["production_ready_local_declared"] is False
    assert summary["reports_written"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["required_hitos_total"] == 17
    assert summary["passed_hitos_total"] == 17
    assert summary["blocking_gaps_total"] == 0
    assert summary["score"] >= 90
    assert result.data["intermediate_model"]["claims"]["production_ready_local"] is False
    assert result.data["intermediate_model"]["candidate_decision"] == "PASS_CANDIDATE"


def test_production_ready_evidence_aggregator_marks_missing_required_evidence_as_blocking_gap(tmp_path: Path) -> None:
    criteria = _minimal_criteria(tmp_path)
    criteria_path = tmp_path / ".devpilot/production/production_ready_local_criteria.json"
    criteria_path.parent.mkdir(parents=True)
    criteria_path.write_text(json.dumps(criteria, indent=2), encoding="utf-8")
    before = _tracked_snapshot(tmp_path)

    result = ProductionReadyEvidenceAggregator(
        tmp_path,
        options=ProductionReadyEvidenceAggregatorOptions(
            criteria_path=".devpilot/production/production_ready_local_criteria.json"
        ),
    ).aggregate()

    after = _tracked_snapshot(tmp_path)
    assert result.ok, result.to_dict()
    assert before == after
    summary = result.data["summary"]
    assert summary["candidate_decision"] == "BLOCK_CANDIDATE"
    assert summary["blocking_gaps_total"] == 1
    assert summary["missing_evidence_total"] == 1
    assert summary["score"] == 0
    gap = result.data["gaps"][0]
    assert gap["severity"] == "block"
    assert gap["path"] == "missing_required.json"


def test_production_ready_evidence_aggregator_parses_json_and_detects_schema_mismatch(tmp_path: Path) -> None:
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps({"schema_id": "WRONG-SCHEMA"}), encoding="utf-8")
    criteria = _minimal_criteria(tmp_path, evidence_path="evidence.json")
    criteria["evidence_map"][0]["evidence"][0]["expected_schema_id"] = "EXPECTED-SCHEMA"
    criteria_path = tmp_path / ".devpilot/production/production_ready_local_criteria.json"
    criteria_path.parent.mkdir(parents=True)
    criteria_path.write_text(json.dumps(criteria, indent=2), encoding="utf-8")

    result = ProductionReadyEvidenceAggregator(tmp_path).aggregate()

    assert result.ok, result.to_dict()
    detail = result.data["evidence_details"][0]
    assert detail["status"] == "failed"
    assert detail["reason"] == "schema_id mismatch"
    assert result.data["summary"]["blocking_gaps_total"] == 1
    assert result.data["summary"]["candidate_decision"] == "BLOCK_CANDIDATE"


def test_production_ready_evidence_aggregator_errors_when_criteria_is_missing(tmp_path: Path) -> None:
    result = ProductionReadyEvidenceAggregator(tmp_path).aggregate()

    assert not result.ok
    assert result.exit_code == 3
    assert result.data["summary"]["production_ready_local_declared"] is False
    assert result.data["safety"]["read_only"] is True


def test_production_ready_evidence_aggregator_artifacts_are_synchronized() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-025_production_ready_declaration_gate.md").read_text(encoding="utf-8")
    tcr = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")

    assert (ROOT / "src/devpilot_core/industrial/production_ready.py").exists()
    assert (ROOT / "docs/audits/post_h_025_b_evidence_aggregator_report.md").exists()
    assert (ROOT / "docs/post_h_025_b_manifest.json").exists()
    assert "POST-H-025-B — Evidence aggregator read-only" in readme
    assert "POST-H-025-B — Evidence aggregator read-only" in runbook
    assert 'current_micro_sprint: "POST-H-025-E"' in backlog
    assert 'next_micro_sprint: "POST-H-026"' in backlog
    assert "post-h-025-production-ready-evidence-aggregator" in tcr
    assert "post-h-025-production-ready-evidence-aggregator" in tcr_v2
    assert "production_ready_local_declared=false" in readme


def _minimal_criteria(root: Path, *, evidence_path: str = "missing_required.json") -> dict:
    return {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-PRODUCTION-READY-LOCAL-CRITERIA-V1",
        "criteria_id": "test-criteria",
        "status": "implemented-initial",
        "scope": "production-ready-local",
        "minimum_score": 90,
        "blocking_gaps_allowed": 0,
        "required_hitos": ["POST-H-999"],
        "optional_design_hitos": [],
        "no_go_gates": {
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "external_apis_required": False,
            "compliance_certification_claim": False,
            "enterprise_ready_claim": False,
            "remote_ready_claim": False,
            "saas_ready_claim": False,
        },
        "evidence_map": [
            {
                "hito_id": "POST-H-999",
                "classification": "required",
                "required_for_pass": True,
                "weight": 100,
                "evidence": [
                    {
                        "evidence_id": "required-evidence",
                        "title": "Required evidence",
                        "path": evidence_path,
                        "category": "manifest",
                        "requirement_level": "blocker",
                        "blocker_on_missing": True,
                        "expected_status": "present",
                        "expected_schema_id": None,
                        "producer_sprint": "POST-H-999",
                        "validation_command": "not executed by POST-H-025-B",
                        "notes": [],
                    }
                ],
            }
        ],
    }


def _tracked_snapshot(root: Path) -> set[str]:
    ignored_parts = {".git", ".pytest_cache", "__pycache__", "outputs"}
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not ignored_parts.intersection(path.relative_to(root).parts)
    }
