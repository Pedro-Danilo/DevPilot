from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.release_candidate import EvidenceFreshnessOptions, EvidenceFreshnessScanner
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_evidence_freshness_report_schema_accepts_pass_and_blocks_invalid_pass() -> None:
    payload = _report_payload(decision="PASS")
    validator = SchemaValidator(ROOT)

    ok = validator.validate_payload(
        schema="EvidenceFreshnessReport",
        payload=payload,
        instance_label="synthetic-evidence-freshness-pass",
    )
    assert ok.ok, ok.to_dict()

    invalid_pass = dict(payload)
    invalid_pass["critical_stale_total"] = 1
    blocked = validator.validate_payload(
        schema="EvidenceFreshnessReport",
        payload=invalid_pass,
        instance_label="synthetic-evidence-freshness-invalid-pass",
    )
    assert not blocked.ok


def test_evidence_freshness_scanner_reads_current_repo_without_writing_outputs() -> None:
    before = _tracked_snapshot(ROOT)

    result = EvidenceFreshnessScanner(ROOT).scan()

    after = _tracked_snapshot(ROOT)
    assert result.ok, result.to_dict()
    assert before == after
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["critical_stale_total"] == 0
    assert summary["critical_missing_total"] == 0
    assert summary["critical_invalid_total"] == 0
    assert summary["reports_written"] is False
    assert result.data["report"]["repo_version"] == "repo_DevPilot_Local_268_POST_H_026_E.zip"
    assert result.data["safety"]["network_used"] is False
    assert result.data["safety"]["external_api_used"] is False
    assert result.data["safety"]["source_mutations"] is False


def test_evidence_freshness_scanner_blocks_stale_missing_and_invalid_critical_evidence(tmp_path: Path) -> None:
    _write_minimal_workspace(tmp_path)
    criteria = _criteria(
        [
            {
                "evidence_id": "stale-project-state",
                "title": "Stale project state",
                "path": ".devpilot/project_state.json",
                "critical": True,
                "json_required": True,
                "expected_schema_id": "SCHEMA-DEVPL-PROJECT-STATE-V1",
                "expected_fields": {"current_repo": "repo_DevPilot_Local_268_POST_H_026_E.zip"},
            },
            {
                "evidence_id": "missing-critical",
                "title": "Missing critical evidence",
                "path": "missing.json",
                "critical": True,
                "json_required": True,
            },
            {
                "evidence_id": "invalid-critical",
                "title": "Invalid critical evidence",
                "path": "invalid.json",
                "critical": True,
                "json_required": True,
            },
        ]
    )
    (tmp_path / "invalid.json").write_text("{ invalid", encoding="utf-8")
    criteria_path = tmp_path / ".devpilot/release/local_release_candidate_criteria.json"
    criteria_path.parent.mkdir(parents=True)
    criteria_path.write_text(json.dumps(criteria, indent=2), encoding="utf-8")

    result = EvidenceFreshnessScanner(tmp_path).scan()

    assert not result.ok
    assert result.exit_code == ExitCode.BLOCK
    report = result.data["report"]
    assert report["decision"] == "BLOCK"
    assert report["critical_stale_total"] == 1
    assert report["critical_missing_total"] == 1
    assert report["critical_invalid_total"] == 1
    statuses = {item["evidence_id"]: item["status"] for item in report["items"]}
    assert statuses == {
        "stale-project-state": "stale",
        "missing-critical": "missing",
        "invalid-critical": "invalid",
    }


def test_evidence_freshness_optional_runtime_absence_is_not_applicable(tmp_path: Path) -> None:
    _write_minimal_workspace(tmp_path, current_repo="repo_DevPilot_Local_268_POST_H_026_E.zip")
    criteria = _criteria(
        [
            {
                "evidence_id": "optional-runtime",
                "title": "Optional runtime report",
                "path": "outputs/reports/production_ready_local_report.json",
                "critical": False,
                "runtime_optional": True,
                "json_required": True,
            }
        ]
    )
    criteria_path = tmp_path / ".devpilot/release/local_release_candidate_criteria.json"
    criteria_path.parent.mkdir(parents=True)
    criteria_path.write_text(json.dumps(criteria, indent=2), encoding="utf-8")

    result = EvidenceFreshnessScanner(tmp_path).scan()

    assert result.ok, result.to_dict()
    assert result.data["report"]["items"][0]["status"] == "not_applicable"
    assert result.data["report"]["not_applicable_total"] == 1


def test_evidence_freshness_cli_writes_report_only_when_requested(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    output_json = ROOT / "outputs/reports/evidence_freshness_report.json"
    output_md = ROOT / "outputs/reports/evidence_freshness_report.md"
    output_json.unlink(missing_ok=True)
    output_md.unlink(missing_ok=True)

    default_exit = cli.main(["release-candidate", "evidence-freshness", "--json"])
    default_payload = json.loads(capsys.readouterr().out)

    assert default_exit == 0
    assert default_payload["data"]["summary"]["reports_written"] is False
    assert not output_json.exists()
    assert not output_md.exists()

    write_exit = cli.main(["release-candidate", "evidence-freshness", "--json", "--write-report"])
    write_payload = json.loads(capsys.readouterr().out)

    assert write_exit == 0
    assert write_payload["data"]["summary"]["reports_written"] is True
    assert output_json.exists()
    assert output_md.exists()
    validation = SchemaValidator(ROOT).validate(
        schema="EvidenceFreshnessReport",
        instance="outputs/reports/evidence_freshness_report.json",
    )
    assert validation.ok, validation.to_dict()


def test_post_h_026_a_artifacts_are_synchronized() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    tcr = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")

    assert (ROOT / "src/devpilot_core/release_candidate/evidence_freshness.py").exists()
    assert (ROOT / "docs/schemas/evidence_freshness_report.schema.json").exists()
    assert (ROOT / ".devpilot/release/local_release_candidate_criteria.json").exists()
    assert (ROOT / "docs/audits/post_h_026_a_evidence_freshness_report.md").exists()
    assert (ROOT / "docs/post_h_026_a_manifest.json").exists()
    assert "POST-H-026-A — Evidence freshness model" in readme
    assert "POST-H-026-A — Evidence freshness model" in runbook
    assert 'implementation_status: "closed"' in backlog
    assert 'next_micro_sprint: "POST-H-027"' in backlog
    assert "post-h-026-a" in changelog
    assert "post-h-026-evidence-freshness" in tcr
    assert "post-h-026-evidence-freshness" in tcr_v2


def _report_payload(*, decision: str) -> dict:
    return {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-EVIDENCE-FRESHNESS-REPORT-V1",
        "report_id": "evidence-freshness-test",
        "created_by": "POST-H-026-A",
        "created_at": "2026-07-07T00:00:00Z",
        "scope": "local-release-candidate",
        "decision": decision,
        "repo_version": "repo_DevPilot_Local_268_POST_H_026_E.zip",
        "criteria_id": "test",
        "criteria_path": ".devpilot/release/local_release_candidate_criteria.json",
        "evidence_total": 1,
        "fresh_total": 1 if decision == "PASS" else 0,
        "stale_total": 0 if decision == "PASS" else 1,
        "missing_total": 0,
        "invalid_total": 0,
        "not_applicable_total": 0,
        "critical_total": 1,
        "critical_stale_total": 0 if decision == "PASS" else 1,
        "critical_missing_total": 0,
        "critical_invalid_total": 0,
        "no_go_gates_passed": True,
        "no_go_gates": {},
        "items": [
            {
                "evidence_id": "sample",
                "title": "Sample",
                "path": "sample.json",
                "critical": True,
                "runtime_optional": False,
                "status": "fresh" if decision == "PASS" else "stale",
                "reason": "synthetic",
                "checks": [],
                "metadata": {},
            }
        ],
        "summary": {"preliminary": True},
        "safety": {
            "local_first": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "source_mutations": False,
        },
        "limitations": ["Synthetic test payload."],
    }


def _criteria(evidence: list[dict]) -> dict:
    return {
        "schema_version": "1.0",
        "criteria_id": "test-criteria",
        "expected_current_repo": "repo_DevPilot_Local_268_POST_H_026_E.zip",
        "scope": "local-release-candidate",
        "no_go_gates": {
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "external_apis_required": False,
        },
        "evidence": evidence,
    }


def _write_minimal_workspace(tmp_path: Path, *, current_repo: str = "repo_DevPilot_Local_OLD.zip") -> None:
    state_path = tmp_path / ".devpilot/project_state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps(
            {
                "schema_id": "SCHEMA-DEVPL-PROJECT-STATE-V1",
                "source_repo": "repo_DevPilot_Local_263_POST_H_025.zip",
                "current_repo": current_repo,
                "last_completed_sprint": "POST-H-025",
                "next_sprint": "POST-H-026",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _tracked_snapshot(root: Path) -> set[str]:
    ignored_parts = {".git", ".pytest_cache", "__pycache__", "outputs"}
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not ignored_parts.intersection(path.relative_to(root).parts)
    }
