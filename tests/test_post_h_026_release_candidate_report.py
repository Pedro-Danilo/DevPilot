from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import CommandResult, ExitCode
from devpilot_core.quality import QualityGate, QualityGateOptions
from devpilot_core.release_candidate import LocalReleaseCandidateOptions, LocalReleaseCandidateReporter
from devpilot_core.schemas.validator import SchemaValidator
from devpilot_core.testing import TestContractRegistryV2Validator
from devpilot_core.testing.impact_v2 import TestImpactAnalyzerV2, TestImpactV2Options

ROOT = Path(__file__).resolve().parents[1]


def test_local_release_candidate_report_passes_without_network_or_shell() -> None:
    result = LocalReleaseCandidateReporter(ROOT).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["evidence_freshness_passed"] is True
    assert summary["release_candidate_profile_passed"] is True
    assert summary["ui_api_smoke_passed"] is True
    assert summary["install_smoke_passed"] is True
    assert summary["production_ready_local_final_passed"] is True
    assert summary["docs_governance_passed"] is True
    assert summary["tcr_v1_v2_passed"] is True
    assert summary["schemas_valid"] is True
    assert summary["forbidden_claims_detected_total"] == 0
    assert summary["no_go_gates_passed"] is True
    assert summary["blocking_gaps_total"] == 0
    safety = result.data["report"]["safety"]
    assert safety["subprocess_executed"] is False
    assert safety["pytest_executed"] is False
    assert safety["network_used"] is False
    assert safety["external_api_used"] is False
    assert safety["remote_execution_enabled"] is False
    assert safety["connector_write_enabled"] is False
    assert safety["plugin_execution_enabled"] is False
    assert safety["source_mutations"] is False
    assert any(finding.id == "LOCAL_RELEASE_CANDIDATE_PASS" for finding in result.findings)


def test_local_release_candidate_report_write_report_validates_schema(monkeypatch) -> None:
    output_json = ROOT / "outputs/test_fixtures/post_h_026_e/local_release_candidate_report.json"
    output_markdown = ROOT / "outputs/test_fixtures/post_h_026_e/local_release_candidate_report.md"
    reporter = LocalReleaseCandidateReporter(ROOT, LocalReleaseCandidateOptions(output_json=str(output_json), output_markdown=str(output_markdown), write_report=True))
    def cheap_component(key, runner, input_signature="default"):
        summary = {"clean_package_policy_passed": True} if key == "rc-install-smoke" else {}
        return CommandResult(key, True, ExitCode.PASS, "stubbed structural component", data={"summary": summary}, findings=[]), False
    monkeypatch.setattr(reporter, "_execute_component", cheap_component)
    result = reporter.run()
    assert result.ok, result.to_dict()
    report = json.loads(output_json.read_text(encoding="utf-8"))
    validation = SchemaValidator(ROOT).validate_payload(schema="LocalReleaseCandidateReport", payload=report, instance_label="memory:local-release-candidate-report")
    assert validation.ok, validation.to_dict()
    assert report["decision"] == "PASS"


def test_local_release_candidate_report_blocks_forbidden_claim_fixture(tmp_path: Path, monkeypatch) -> None:
    criteria = json.loads((ROOT / ".devpilot/release/local_release_candidate_criteria.json").read_text(encoding="utf-8"))
    criteria["no_go_gates"]["enterprise_ready_claim"] = True
    criteria_path = ROOT / "outputs/test_fixtures/post_h_026_e/bad_local_release_candidate_criteria.json"
    criteria_path.parent.mkdir(parents=True, exist_ok=True)
    criteria_path.write_text(json.dumps(criteria, indent=2), encoding="utf-8")
    reporter = LocalReleaseCandidateReporter(ROOT, LocalReleaseCandidateOptions(criteria_path=str(criteria_path)))
    monkeypatch.setattr(reporter, "_execute_component", lambda key, runner, input_signature="default": (CommandResult(key, True, ExitCode.PASS, "stubbed", data={"summary": {"clean_package_policy_passed": True}}, findings=[]), False))
    result = reporter.run()
    assert not result.ok
    assert any(gap["gap_id"] == "forbidden-claims-enabled" for gap in result.data["report"]["blocking_gaps"])


def test_local_release_candidate_cli_command_is_available(capsys, monkeypatch) -> None:
    fake = CommandResult("release-candidate final", True, ExitCode.PASS, "ok", data={"summary": {"decision": "PASS", "network_used": False, "source_mutations": False}}, findings=[])
    monkeypatch.setattr(LocalReleaseCandidateReporter, "run", lambda self: fake)
    exit_code = cli.main(["release-candidate", "final", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "release-candidate final"
    assert payload["ok"] is True


def test_local_release_candidate_registered_in_tcr_v2_impact_and_quality_gate() -> None:
    profile = TestContractRegistryV2Validator(ROOT).profile("release-candidate-local")
    assert profile.ok, profile.to_dict()
    impact = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("src/devpilot_core/release_candidate/report.py",))).analyze()
    assert impact.ok, impact.to_dict()
    plan = QualityGate(ROOT, options=QualityGateOptions(profile="hardening")).describe_plan().to_dict()
    assert "local-release-candidate" in set(plan["ordered_subgate_ids"])


def test_post_h_026_e_documentation_is_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "docs/post_h_026_e_manifest.json").read_text(encoding="utf-8"))

    assert "POST-H-026-E — RC PASS/BLOCK report" in backlog
    assert "implementation_status: \"closed\"" in backlog
    assert "release-candidate final" in readme
    assert "release-candidate final" in runbook
    assert "post-h-026-e" in changelog
    assert manifest["micro_sprint"] == "POST-H-026-E"
    assert manifest["status"] == "closed"
    assert manifest["tests_execute_from_json"] is False
