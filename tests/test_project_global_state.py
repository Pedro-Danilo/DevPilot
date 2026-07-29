from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.testing import TestContractRegistry

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_project_global_state_schema_and_docs_are_synchronized() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    post_h_doc = read("docs/POST-H-001_industrial_hardening_tests_contracts.md")
    post_h_002_backlog = read("docs/backlogs/POST-H-002_maturity_dashboard_local.md")
    post_h_005_backlog = read("docs/backlogs/POST-H-005_architecture_map_executable.md")
    post_h_roadmap = read("docs/backlogs/post_h_prioritized_roadmap.md")
    changelog = read("docs/release/CHANGELOG.md")

    assert state["current_phase"] == "POST-H-EVAL-002"
    assert state["last_completed_sprint"] == "POST-H-034"
    assert state["last_functional_sprint"] == "FUNC-SPRINT-99"
    assert state["next_sprint"] == "POST-H-EVAL-002"
    assert state["phase_h_status"] == "closed_implemented_initial"
    assert state["industrial_baseline_ready"] is True
    assert state["global_state_owner"] == "tests/test_project_global_state.py"

    assert "Último hito cerrado: `POST-H-016" in readme
    assert "Siguiente hito: `POST-H-017" in readme
    assert "POST-H-006 — CLI command registry y desacoplamiento de handlers" in readme
    assert "POST-H-005-E — Operación del reporte final ArchitectureMap" in runbook
    assert 'status: "approved"' in post_h_doc
    assert 'implementation_status: "implemented-initial"' in post_h_doc
    assert 'implementation_status: "closed"' in post_h_002_backlog
    assert 'implementation_status: "closed"' in post_h_005_backlog
    assert "POST-H-008" in readme
    assert "post-h-007-a" in changelog
    assert "post-h-007-b" in changelog
    assert "post-h-007-c" in changelog
    assert "post-h-007-d" in changelog
    assert "post-h-007-e" in changelog
    assert "post-h-008-a" in changelog
    assert "post-h-008-b" in changelog
    assert "post-h-008-d" in changelog
    assert "post-h-008-e" in changelog
    assert "post-h-009-a" in changelog
    assert "post-h-009-b" in changelog
    assert "post-h-009-c" in changelog
    assert "post-h-009-d" in changelog
    assert "post-h-009-e" in changelog
    assert "post-h-010-d" in changelog
    assert "post-h-010-e" in changelog
    assert "post-h-011-b" in changelog
    assert any("POST-H-009-A starts Documentation governance" in note for note in state["notes"])
    assert any("POST-H-009-B adds Documentation governance" in note for note in state["notes"])
    assert any("POST-H-009-C adds Documentation governance" in note for note in state["notes"])
    assert any("POST-H-009-D adds Documentation governance" in note for note in state["notes"])
    assert any("POST-H-009-E closes Documentation governance" in note for note in state["notes"])
    assert "POST-H-008-A — Runtime state lifecycle" in readme
    assert "POST-H-008-B — Runtime state lifecycle" in readme
    assert "POST-H-008-D — Runtime state lifecycle" in readme
    assert "POST-H-008-E — Runtime state lifecycle" in readme
    assert "POST-H-009-A — Documentation governance" in readme
    assert "POST-H-009-B — Documentation governance" in readme
    assert "POST-H-009-C — Documentation governance" in readme
    assert "POST-H-009-D — Documentation governance" in readme
    assert "POST-H-009-E — Documentation governance" in readme
    assert "POST-H-010-A — Observability retention" in readme
    assert "POST-H-010-B — Observability retention" in readme
    assert "POST-H-010-C — Observability retention" in readme
    assert "POST-H-010-D — Observability retention" in readme
    assert "POST-H-010-E — Observability retention" in readme
    assert any("POST-H-010-A starts Observability retention" in note for note in state["notes"])
    assert any("POST-H-010-B adds Observability inventory" in note for note in state["notes"])
    assert any("POST-H-010-C adds Observability cleanup plan" in note for note in state["notes"])
    assert any("POST-H-010-D adds local redacted observability export" in note for note in state["notes"])
    assert any("POST-H-010-E closes Observability retention local" in note for note in state["notes"])
    assert any("POST-H-011-C adds deterministic RAG claim groundedness" in note for note in state["notes"])
    assert any("POST-H-011-E closes RAG groundedness evals" in note for note in state["notes"])
    assert "POST-H-011-E — Gate y documentación de límites RAG" in readme
    assert "POST-H-012-D — PolicyEngine enforcement homogéneo" in readme
    assert "POST-H-012-E — Quality gate y runbook de aprobación" in readme
    assert "POST-H-012-E — Quality gate y runbook de aprobación" in runbook
    assert "POST-H-013-A — Audit pack manifest v2 y policy" in readme
    assert "POST-H-013-A — Audit pack manifest v2 y policy" in runbook
    assert "POST-H-013-B — Builder v2 con checksums y redaction report" in readme
    assert "POST-H-013-B — Builder v2 con checksums y redaction report" in runbook
    assert "POST-H-013-C — Verifier v2 de integridad local" in readme
    assert "POST-H-013-C — Verifier v2 de integridad local" in runbook
    assert "POST-H-013-D — Firma y cifrado local opcional" in readme
    assert "POST-H-013-D — Firma y cifrado local opcional" in runbook
    assert "POST-H-013-E — Quality gate, runbook y disclaimers" in readme
    assert "POST-H-013-E — Quality gate, runbook y disclaimers" in runbook
    assert any("POST-H-013-A starts Audit pack integrity" in note for note in state["notes"])
    assert any("POST-H-013-B adds AuditPackV2Builder" in note for note in state["notes"])
    assert any("POST-H-013-C adds AuditPackV2Verifier" in note for note in state["notes"])
    assert any("POST-H-013-D adds optional local crypto" in note for note in state["notes"])
    assert any("POST-H-013-E closes Audit pack integrity" in note for note in state["notes"])
    assert any("POST-H-014 is the next prioritized hito" in note for note in state["notes"])
    assert state.get("current_micro_sprint") in {"POST-H-033-D", "POST-H-033-E", "POST-H-033-F", "POST-H-034-A", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE", "POST-H-EVAL-002-01-A", "POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state.get("next_micro_sprint") in {"POST-H-033-E", "POST-H-033-F", "POST-H-033-CLOSURE", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE", "POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state.get("source_repo") == "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip"
    assert str(state.get("current_repo", "")).startswith("repo_DevPilot_Local_")
    assert state.get("current_repo") in {"repo_DevPilot_Local_319_POST_H_EVAL_002_01_A.zip", "repo_DevPilot_Local_320_POST_H_EVAL_002_01_B.zip", "repo_DevPilot_Local_321_POST_H_EVAL_002_01_C.zip", "repo_DevPilot_Local_322_POST_H_EVAL_002_01_D_ACCEPTANCE_READY.zip", "repo_DevPilot_Local_323_POST_H_EVAL_002_01_D_UI_ACCEPTANCE_FIX.zip", "repo_DevPilot_Local_324_POST_H_EVAL_002_01_D_RUNTIME_CORRECTIVE.zip", "repo_DevPilot_Local_325_POST_H_EVAL_002_01_D_BROWSER_ACCEPTANCE_CORRECTIVE.zip", "repo_DevPilot_Local_326_POST_H_EVAL_002_01_D_RUN05B_INTEGRAL_CORRECTIVE.zip"}
    assert state.get("current_micro_sprint") in {"POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D"}
    assert state.get("next_micro_sprint") in {"POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state.get("post_h_eval_002_activated") is True
    assert state.get("next_backlog_planned") is True
    assert state.get("post_h_026_status") == "closed/local-release-candidate-pass"
    assert "POST-H-026-C — UI/API local smoke under RC" in readme
    assert "POST-H-026-C — UI/API local smoke under RC" in runbook
    assert "post-h-026-c" in changelog
    assert state.get("post_h_026_c_ui_api_rc_smoke_available") is True
    assert state.get("post_h_026_c_cors_wildcard_enabled") is False
    assert any("POST-H-026-C adds UI/API local RC smoke" in note for note in state["notes"])
    assert "POST-H-026-D — Local install and run verification" in readme
    assert "POST-H-026-D — Local install and run verification" in runbook
    assert "post-h-026-d" in changelog
    assert state.get("post_h_026_d_local_install_smoke_available") is True
    assert state.get("post_h_026_d_install_smoke_read_only") is True
    assert state.get("post_h_026_d_network_used") is False
    assert any("POST-H-026-D adds LocalInstallSmokeRunner" in note for note in state["notes"])

    assert "POST-H-026-E — RC PASS/BLOCK report" in readme
    assert "POST-H-026-E — RC PASS/BLOCK report" in runbook
    assert "post-h-026-e" in changelog
    assert state.get("post_h_026_e_local_release_candidate_report_available") is True
    assert state.get("post_h_026_e_forbidden_claims_detected_total") == 0
    assert state.get("post_h_026_e_no_go_gates_passed") is True
    assert state.get("post_h_026_release_candidate_declared") is True
    assert any("POST-H-026-E adds LocalReleaseCandidateReporter" in note for note in state["notes"])
    assert state.get("post_h_027_status") == "closed/packaging-local-ready"
    assert state.get("post_h_027_source_zip_policy_schema_registered") is True
    assert state.get("post_h_027_source_zip_report_schema_registered") is True
    assert state.get("post_h_027_source_zip_policy_cli_command") == "python -m devpilot_core package source-zip-policy --json"
    assert any("POST-H-027-A starts Packaging reproducible" in note for note in state["notes"])
    assert "POST-H-027-A — Source ZIP release policy hardening" in readme
    assert "POST-H-027-A — Source ZIP release policy hardening" in runbook
    assert "post-h-027-a" in changelog

    assert state.get("post_h_027_python_artifact_install_schema_registered") is True
    assert state.get("post_h_027_python_artifact_install_report_available") is True
    assert state.get("post_h_027_wheel_install_verification_available") is True
    assert state.get("post_h_027_sdist_install_verification_available") is True
    assert state.get("post_h_027_python_artifact_verify_no_network_required") is True
    assert state.get("post_h_027_python_artifact_verify_sdist_build_backend_bridge_fixed") is True
    assert "POST-H-027-B — Wheel/sdist install verification" in readme
    assert "POST-H-027-B — Wheel/sdist install verification" in runbook
    assert "post-h-027-b" in changelog
    assert any("POST-H-027-B adds PythonArtifactInstallVerifier" in note for note in state["notes"])

    assert state.get("post_h_027_artifact_manifest_schema_registered") is True
    assert state.get("post_h_027_artifact_manifest_available") is True
    assert state.get("post_h_027_artifact_checksums_available") is True
    assert state.get("post_h_027_artifact_manifest_no_network_required") is True
    assert state.get("post_h_027_artifact_manifest_source_mutations") is False
    assert "POST-H-027-C — Artifact manifest and checksums" in readme
    assert "POST-H-027-C — Artifact manifest and checksums" in runbook
    assert "post-h-027-c" in changelog
    assert any("POST-H-027-C adds ReleaseArtifactManifest" in note for note in state["notes"])

    assert state.get("post_h_027_windows_install_smoke_schema_registered") is True
    assert state.get("post_h_027_windows_install_smoke_available") is True
    assert state.get("post_h_027_windows_install_smoke_admin_required") is False
    assert state.get("post_h_027_windows_install_smoke_network_used") is False
    assert state.get("post_h_027_windows_install_smoke_source_mutations") is False
    assert "POST-H-027-D — Windows install guide and smoke" in readme
    assert "POST-H-027-D — Windows install guide and smoke" in runbook
    assert "post-h-027-d" in changelog
    assert any("POST-H-027-D adds WindowsInstallSmokeRunner" in note for note in state["notes"])
    assert state.get("post_h_027_upgrade_rollback_dry_run_schema_registered") is True
    assert state.get("post_h_027_upgrade_rollback_dry_run_available") is True
    assert state.get("post_h_027_upgrade_rollback_auto_update_enabled") is False
    assert state.get("post_h_027_upgrade_rollback_restore_performed") is False
    assert state.get("post_h_027_upgrade_rollback_network_used") is False
    assert state.get("post_h_027_packaging_local_ready_quality_gate_enabled") is True
    assert "POST-H-027-E — Upgrade/rollback dry-run" in readme
    assert "POST-H-027-E — Upgrade/rollback dry-run" in runbook
    assert "post-h-027-e" in changelog
    assert any("POST-H-027-E adds UpgradeRollbackDryRunRunner" in note for note in state["notes"])

    assert state.get("post_h_028_ui_visual_smoke_schema_registered") is True
    assert state.get("post_h_028_ui_visual_smoke_available") is True
    assert state.get("post_h_028_ui_visual_smoke_browser_required_for_core") is False
    assert state.get("post_h_028_ui_visual_smoke_screenshots_versioned") is False
    assert "POST-H-028-C — Visual smoke tests" in readme
    assert "POST-H-028-C — Visual smoke tests" in runbook
    assert "post-h-028-c" in changelog.lower()
    assert any("POST-H-028-C adds UiVisualSmokeReporter" in note for note in state["notes"])

    assert state.get("post_h_028_operator_flow_smoke_schema_registered") is True
    assert state.get("post_h_028_operator_flow_smoke_available") is True
    assert state.get("post_h_028_operator_flow_smoke_quality_gate_enabled") is True
    assert state.get("post_h_028_operator_flow_smoke_runtime_sandbox_used") is True
    assert state.get("post_h_028_operator_flow_smoke_network_used") is False
    assert state.get("post_h_028_operator_flow_smoke_source_mutations") is False
    assert "POST-H-028-D — Operator flows and error states" in readme
    assert "POST-H-028-D — Operator flows and error states" in runbook
    assert "post-h-028-d" in changelog.lower()
    assert any("POST-H-028-D adds OperatorFlowSmokeRunner" in note for note in state["notes"])
    assert any("POST-H-027 closes Packaging reproducible" in note for note in state["notes"])
    assert state.get("post_h_028_status") == "closed/ui-api-local-hardening"
    assert state.get("post_h_028_backlog_approved") is True
    assert state.get("post_h_028_current_micro_sprint") == "POST-H-028-E"
    assert state.get("post_h_028_next_micro_sprint") == "POST-H-029"
    assert state.get("post_h_028_api_contract_drift_schema_registered") is True
    assert state.get("post_h_028_api_contract_drift_guard_available") is True
    assert state.get("post_h_028_api_contract_drift_quality_gate_enabled") is True
    assert state.get("post_h_028_api_contract_drift_network_used") is False
    assert state.get("post_h_028_api_contract_drift_source_mutations") is False
    assert state.get("post_h_028_a_backup_artifact_hygiene_corrected") is True
    assert "POST-H-028-A — API contract drift guard" in readme
    assert "POST-H-028-A — API contract drift guard" in runbook
    assert "post-h-028-a" in changelog
    assert any("POST-H-028-A approves UI/API local hardening" in note for note in state["notes"])
    assert any("POST-H-028-A corrective packaging hygiene excludes .devpilot/backups/" in note for note in state["notes"])

    assert state.get("post_h_028_local_api_security_hardening_schema_registered") is True
    assert state.get("post_h_028_local_api_security_hardening_available") is True
    assert state.get("post_h_028_local_api_security_hardening_quality_gate_enabled") is True
    assert state.get("post_h_028_local_api_security_hardening_network_used") is False
    assert state.get("post_h_028_local_api_security_hardening_source_mutations") is False
    assert state.get("post_h_028_cors_wildcard_enabled") is False
    assert state.get("post_h_028_non_local_bind_allowed") is False
    assert "POST-H-028-B — Local auth and CORS hardening" in readme
    assert "POST-H-028-B — Local auth and CORS hardening" in runbook
    assert "post-h-028-b" in changelog.lower()
    assert any("POST-H-028-B adds LocalApiSecurityHardeningRunner" in note for note in state["notes"])

    assert state.get("post_h_028_ui_route_enforcement_schema_registered") is True
    assert state.get("post_h_028_ui_route_enforcement_available") is True
    assert state.get("post_h_028_ui_route_enforcement_quality_gate_enabled") is True
    assert state.get("post_h_028_ui_route_registry_enforcement_passed") is True
    assert state.get("post_h_028_ui_api_local_hardening_quality_gate_enabled") is True
    assert state.get("post_h_028_ui_api_hardening_quality_gate_passed") is True
    assert state.get("post_h_028_forbidden_ui_actions_total") == 0
    assert state.get("post_h_028_unregistered_api_refs_total") == 0
    assert state.get("post_h_028_filesystem_core_imports_total") == 0
    assert state.get("post_h_028_operator_flow_smoke_windows_path_fixed") is True
    assert state.get("post_h_028_closed") is True
    assert "POST-H-028-E — UI route registry enforcement" in readme
    assert "POST-H-028-E — UI route registry enforcement" in runbook
    assert "post-h-028-e" in changelog.lower()
    assert any("POST-H-028-E adds UiRouteEnforcementRunner" in note for note in state["notes"])
    assert any("POST-H-028 closes UI/API local hardening" in note for note in state["notes"])

    assert state.get("post_h_029_backlog_approved") is True
    assert state.get("post_h_029_test_profile_taxonomy_schema_registered") is True
    assert state.get("post_h_029_test_profile_taxonomy_available") is True
    assert state.get("post_h_029_test_profile_taxonomy_valid") is True
    assert state.get("post_h_029_tests_run_approval_gated") is True
    assert state.get("post_h_029_tests_executed_from_taxonomy") is False
    assert state.get("post_h_029_no_arbitrary_shell") is True
    assert state.get("post_h_029_full_regression_preserved") is True
    assert state.get("post_h_029_test_impact_rule_registry_schema_registered") is True
    assert state.get("post_h_029_test_impact_rule_registry_available") is True
    assert state.get("post_h_029_test_impact_rule_registry_valid") is True
    assert state.get("post_h_029_test_impact_rules_unmapped_p0_p1_domains_total") == 0
    assert state.get("post_h_029_test_impact_rules_unsafe_commands_total") == 0
    assert state.get("post_h_029_test_impact_rules_unknown_impact_escalates") is True
    assert state.get("post_h_029_test_impact_analyzer_v2_uses_rule_registry") is True
    assert "POST-H-029-A — Test profile taxonomy" in readme
    assert "POST-H-029-A — Test profile taxonomy" in runbook
    assert "POST-H-029-B — TCR v2 impact rules" in readme
    assert "POST-H-029-B — TCR v2 impact rules" in runbook
    assert "post-h-029-b" in changelog.lower()
    assert any("POST-H-029-B adds TestImpactRuleRegistry" in note for note in state["notes"])

    assert state.get("post_h_029_test_impact_cli_recommendations_available") is True
    assert state.get("post_h_029_test_impact_recommendation_report_schema_registered") is True
    assert state.get("post_h_029_test_impact_cli_recommendations_tests_executed") is False
    assert state.get("post_h_029_test_impact_cli_recommendations_unsafe_commands_total") == 0
    assert state.get("post_h_029_test_impact_cli_recommendations_full_regression_signal_available") is True
    assert "POST-H-029-C — Test impact CLI recommendations" in readme
    assert "POST-H-029-C — Test impact CLI recommendations" in runbook
    assert "post-h-029-c" in changelog.lower()
    assert any("POST-H-029-C adds TestImpactRecommendationReport" in note for note in state["notes"])

    assert state.get("post_h_029_test_impact_cli_recommendations_available") is True
    assert state.get("post_h_029_test_impact_recommendation_report_schema_registered") is True
    assert state.get("post_h_029_test_impact_cli_recommendations_tests_executed") is False
    assert state.get("post_h_029_test_impact_cli_recommendations_unsafe_commands_total") == 0
    assert state.get("post_h_029_test_impact_cli_recommendations_full_regression_signal_available") is True
    assert "POST-H-029-C — Test impact CLI recommendations" in readme
    assert "POST-H-029-C — Test impact CLI recommendations" in runbook
    assert "post-h-029-c" in changelog.lower()
    assert any("POST-H-029-C adds TestImpactRecommendationReport" in note for note in state["notes"])
    assert "post-h-029-a" in changelog.lower()
    assert any("POST-H-029-A starts Testing tiers" in note for note in state["notes"])
    assert "POST-H-014-A — Route Contract Registry y API inventory" in readme
    assert "POST-H-014-B — Response mapping y errores homogéneos" in readme
    assert "POST-H-014-C — UI Route Contract y shell de producto" in readme
    assert "POST-H-014-D — Security hardening local de API/UI" in readme
    assert "POST-H-014-E — Quality gate UI/API industrial shell" in readme
    assert "POST-H-014-A — Route Contract Registry y API inventory" in runbook
    assert "POST-H-014-B — Response mapping y errores homogéneos" in runbook
    assert "POST-H-014-C — UI Route Contract y shell de producto" in runbook
    assert "POST-H-014-D — Security hardening local de API/UI" in runbook
    assert "POST-H-014-E — Quality gate UI/API industrial shell" in runbook
    assert "post-h-014-a" in changelog
    assert "post-h-014-b" in changelog
    assert "post-h-014-c" in changelog
    assert "post-h-014-d" in changelog
    assert "post-h-014-e" in changelog
    assert any("POST-H-014-A approves UI/API industrial shell" in note for note in state["notes"])
    assert any("POST-H-014-B adds homogeneous response mapping" in note for note in state["notes"])
    assert any("POST-H-014-C adds UI Route Contract Registry" in note for note in state["notes"])
    assert any("POST-H-014-D adds local API/UI security hardening" in note for note in state["notes"])
    assert any("POST-H-014-E closes UI/API industrial shell" in note for note in state["notes"])
    assert any("POST-H-015-A approves Local operator dashboard" in note for note in state["notes"])
    assert any("POST-H-015-B adds OperatorDashboardAggregator" in note for note in state["notes"])
    assert any("POST-H-015-C adds OperatorDashboardApplicationService" in note for note in state["notes"])
    assert any("POST-H-015-D adds the Web UI Operator Dashboard" in note for note in state["notes"])
    assert any("POST-H-015-E closes Local operator dashboard" in note for note in state["notes"])
    assert any("POST-H-016-A approves Workspace portfolio hardening" in note for note in state["notes"])
    assert any("POST-H-016-B adds WorkspaceIsolationValidator" in note for note in state["notes"])
    assert any("POST-H-016-C hardens portfolio status" in note for note in state["notes"])
    assert any("POST-H-016-D adds secure CLI/API integration" in note for note in state["notes"])
    assert any("POST-H-016-E closes Workspace portfolio hardening" in note for note in state["notes"])
    assert any("POST-H-017-A approves Release reproducibility pack" in note for note in state["notes"])
    assert any("POST-H-017-A adds local release reproducibility policy" in note for note in state["notes"])
    assert "POST-H-017-A — Release reproducibility schema y policy" in readme
    assert "POST-H-017-A — Release reproducibility schema y policy" in runbook
    assert any("POST-H-017-B adds redacted ReleaseEnvironmentSnapshotBuilder" in note for note in state["notes"])
    assert "POST-H-017-B — Environment snapshot redactado" in readme
    assert "POST-H-017-B — Environment snapshot redactado" in runbook
    assert any("POST-H-017-C adds SourceArchiveManifestBuilder" in note for note in state["notes"])
    assert any("POST-H-017-D adds ReleaseReproducibilityVerifier" in note for note in state["notes"])
    assert any("POST-H-017-E adds ReleaseReproducibilityPackBuilder" in note for note in state["notes"])
    assert "POST-H-017-C — Source archive manifest y checksums" in readme
    assert "POST-H-017-D — Verifier local de reproducibilidad" in readme
    assert "POST-H-017-E — Quality gate y runbook release" in readme
    assert "POST-H-017-C — Source archive manifest y checksums" in runbook
    assert "POST-H-017-D — Verifier local de reproducibilidad" in runbook
    assert "POST-H-017-E — Quality gate y runbook release" in runbook
    assert "post-h-017-a" in changelog
    assert "post-h-017-b" in changelog
    assert "post-h-017-c" in changelog
    assert "post-h-017-d" in changelog
    assert "post-h-017-e" in changelog
    assert any("POST-H-018-A approves Connector sandbox avanzado" in note for note in state["notes"])
    assert any("POST-H-018-B adds ConnectorSandboxRunner" in note for note in state["notes"])
    assert "POST-H-018-A — Connector sandbox policy y schemas" in readme
    assert "POST-H-018-A — Connector sandbox policy y schemas" in runbook
    assert "POST-H-018-B — Sandbox runner read-only/dry-run" in readme
    assert "POST-H-018-B — Sandbox runner read-only/dry-run" in runbook
    assert "post-h-018-a" in changelog
    assert "post-h-018-b" in changelog
    assert any("POST-H-018-C adds ConnectorReplayRunner" in note for note in state["notes"])
    assert "POST-H-018-C — Replay fixtures y redacción" in readme
    assert "POST-H-018-C — Replay fixtures y redacción" in runbook
    assert "post-h-018-c" in changelog
    assert any("POST-H-018-D adds ConnectorPolicyBindingValidator" in note for note in state["notes"])
    assert "POST-H-018-D — Policy/approval/RBAC binding para conectores" in readme
    assert "POST-H-018-D — Policy/approval/RBAC binding para conectores" in runbook
    assert "post-h-018-d" in changelog
    assert any("POST-H-018-E adds ConnectorSandboxQualityGate" in note for note in state["notes"])
    assert any("POST-H-018 closes Connector sandbox avanzado" in note for note in state["notes"])
    assert any("POST-H-019 is the next prioritized hito" in note for note in state["notes"])
    assert "POST-H-018-E — Quality gate, runbook y cierre" in readme
    assert "POST-H-018-E — Quality gate, runbook y cierre" in runbook
    assert "post-h-018-e" in changelog
    assert "Siguiente hito: `POST-H-019" in readme or "Siguiente hito: `POST-H-024" in readme
    assert any("POST-H-019-A approves Plugin sandbox design" in note for note in state["notes"])
    assert any("POST-H-019-B is the next micro-sprint" in note for note in state["notes"])
    assert any("POST-H-019-C adds PluginStaticValidator" in note for note in state["notes"])
    assert any("POST-H-019-D adds plugin-sandbox-design" in note for note in state["notes"])
    assert any("POST-H-019-E closes Plugin sandbox design" in note for note in state["notes"])
    assert any("POST-H-020 is the next prioritized hito" in note for note in state["notes"])
    assert any("POST-H-020-A approves Compliance mapping packs" in note for note in state["notes"])
    assert any("POST-H-020-A adds ComplianceControlMapping" in note for note in state["notes"])
    assert any("POST-H-020-B is the next micro-sprint" in note for note in state["notes"])
    assert any("POST-H-020-B adds ComplianceMappingValidator" in note for note in state["notes"])
    assert any("POST-H-020-C is the next micro-sprint" in note for note in state["notes"])
    assert any("POST-H-020-C adds ComplianceEvidenceCollector" in note for note in state["notes"])
    assert any("POST-H-020-D adds ComplianceMappingQualityGate" in note for note in state["notes"])
    assert any("POST-H-020-D adds non-certifying compliance_mapping summary" in note for note in state["notes"])
    assert any("POST-H-020-E adds compliance mapping runbook" in note for note in state["notes"])
    assert any("POST-H-020 closes Compliance mapping packs" in note for note in state["notes"])
    assert any("POST-H-021 is the next prioritized hito" in note for note in state["notes"])
    assert any("POST-H-021-A approves Remote Runner ADR-2" in note for note in state["notes"])
    assert any("POST-H-021-A inventories remote runner baseline" in note for note in state["notes"])
    assert any("POST-H-021-B adds ADR-POSTH-004" in note for note in state["notes"])
    assert any("POST-H-021-C adds RemoteReadinessChecker" in note for note in state["notes"])
    assert any("POST-H-021-C registers RemoteReadinessReport" in note for note in state["notes"])
    assert any("POST-H-021-D adds RemoteReadinessQualityGate" in note for note in state["notes"])
    assert any("POST-H-021-E closes Remote Runner ADR-2" in note for note in state["notes"])
    assert any("POST-H-022 is the next prioritized hito" in note for note in state["notes"])
    assert any("POST-H-022-A approves Enterprise deployment threat model" in note for note in state["notes"])
    assert any("POST-H-022-A adds EnterpriseThreatModel" in note for note in state["notes"])
    assert any("POST-H-022-B is the next micro-sprint" in note for note in state["notes"])
    assert any("POST-H-022-B adds STRIDE/LINDDUN threat catalog" in note for note in state["notes"])
    assert any("POST-H-022-C is the next micro-sprint" in note for note in state["notes"])
    assert any("POST-H-022-C registers EnterpriseControlMatrix" in note for note in state["notes"])
    assert any("POST-H-022-D is the next micro-sprint" in note for note in state["notes"])
    assert any("POST-H-022-D adds EnterpriseThreatModelValidator" in note for note in state["notes"])
    assert any("POST-H-022-D adds enterprise-threat-model-design-only" in note for note in state["notes"])
    assert any("POST-H-022-E adds enterprise design runbook" in note for note in state["notes"])
    assert any("POST-H-022 closes Enterprise deployment threat model" in note for note in state["notes"])
    assert any("POST-H-023 is the next prioritized hito" in note for note in state["notes"])
    assert any("POST-H-023-A approves Secure transport design" in note for note in state["notes"])
    assert any("POST-H-023-A adds SecureTransportRequirements" in note for note in state["notes"])
    assert any("POST-H-023-B is the next micro-sprint" in note for note in state["notes"])
    assert any("POST-H-023-B adds SecureTransportDesign" in note for note in state["notes"])
    assert any("POST-H-023-C is the next micro-sprint" in note for note in state["notes"])
    assert any("POST-H-023-C adds SecureTransportKeyLifecycle" in note for note in state["notes"])
    assert any("POST-H-023-D is the next micro-sprint" in note for note in state["notes"])
    assert any("POST-H-023-D adds SecureTransportDesignValidator" in note for note in state["notes"])
    assert any("POST-H-023-D adds secure-transport-design-only" in note for note in state["notes"])
    assert any("POST-H-023-E is the next micro-sprint" in note for note in state["notes"])
    assert any("POST-H-023-E adds secure transport design runbook" in note for note in state["notes"])
    assert any("POST-H-023 closes Secure transport design" in note for note in state["notes"])
    assert any("POST-H-024 is the next prioritized hito" in note for note in state["notes"])
    assert "POST-H-023-E — Runbook y cierre" in readme
    assert "POST-H-023-E — Runbook y cierre" in runbook
    assert "post-h-023-e" in changelog

    assert "POST-H-024-A — Playbook de operador" in readme
    assert "POST-H-024-A — Playbook de operador" in runbook
    assert "post-h-024-a" in changelog
    assert any("POST-H-024-A approves Operator onboarding bootstrap" in note for note in state["notes"])
    assert any("POST-H-024-B is the next micro-sprint" in note for note in state["notes"])
    assert "POST-H-024-B — Templates de proyecto nuevo" in readme
    assert "POST-H-024-B — Templates de proyecto nuevo" in runbook
    assert "post-h-024-b" in changelog
    assert any("POST-H-024-B adds versioned new-project" in note for note in state["notes"])
    assert any("POST-H-024-C is the next micro-sprint" in note for note in state["notes"])
    assert "POST-H-024-C — Bootstrap workflow dry-run" in readme
    assert "POST-H-024-C — Bootstrap workflow dry-run" in runbook
    assert "post-h-024-c" in changelog
    assert any("POST-H-024-C adds ProjectBootstrapPlanner" in note for note in state["notes"])
    assert any("POST-H-024-D is the next micro-sprint" in note for note in state["notes"])
    assert "POST-H-023-D — Validator de diseño y no-network invariant" in readme
    assert "POST-H-023-D — Validator de diseño y no-network invariant" in runbook
    assert "post-h-023-d" in changelog
    assert "POST-H-023-C — Key/certificate lifecycle design" in readme
    assert "POST-H-023-C — Key/certificate lifecycle design" in runbook
    assert "post-h-023-c" in changelog
    assert "POST-H-019-A — Threat model y sandbox design" in readme
    assert "POST-H-019-A — Threat model y sandbox design" in runbook
    assert "post-h-019-a" in changelog
    assert "POST-H-019-B — Permission model y manifest hardening" in readme
    assert "POST-H-019-B — Permission model y manifest hardening" in runbook
    assert "POST-H-019-D — Quality gate plugin safety" in readme
    assert "POST-H-019-D — Quality gate plugin safety" in runbook
    assert "POST-H-019-E — Runbook, ADR trigger y cierre" in readme
    assert "POST-H-019-E — Runbook, ADR trigger y cierre" in runbook
    assert "POST-H-020-A — Control mapping schemas y registry" in readme
    assert "POST-H-020-A — Control mapping schemas y registry" in runbook
    assert "POST-H-020-B — Compliance mapping validator" in readme
    assert "POST-H-020-B — Compliance mapping validator" in runbook
    assert "POST-H-020-C — Evidence collector y report generator local" in readme
    assert "POST-H-020-C — Evidence collector y report generator local" in runbook
    assert "POST-H-020-D — Integración con audit packs y quality gate" in readme
    assert "POST-H-020-D — Integración con audit packs y quality gate" in runbook
    assert "POST-H-020-E — Runbook, disclaimers y cierre" in readme
    assert "POST-H-020-E — Runbook, disclaimers y cierre" in runbook
    assert "POST-H-021-A — Inventario remote y baseline de bloqueo" in readme
    assert "POST-H-021-A — Inventario remote y baseline de bloqueo" in runbook
    assert "POST-H-021-B — ADR-2 de Remote Runner" in readme
    assert "POST-H-021-B — ADR-2 de Remote Runner" in runbook
    assert "POST-H-021-C — Remote readiness report read-only" in readme
    assert "POST-H-021-C — Remote readiness report read-only" in runbook
    assert "POST-H-021-D — Quality gate remote disabled" in readme
    assert "POST-H-021-D — Quality gate remote disabled" in runbook
    assert "POST-H-021-E — Runbook y cierre" in readme
    assert "POST-H-021-E — Runbook y cierre" in runbook
    assert "POST-H-022-A — Asset inventory y trust boundaries" in readme
    assert "POST-H-022-A — Asset inventory y trust boundaries" in runbook
    assert "POST-H-022-B — Threat catalog STRIDE/LINDDUN adaptado" in readme
    assert "POST-H-022-B — Threat catalog STRIDE/LINDDUN adaptado" in runbook
    assert "POST-H-022-C — Enterprise control matrix" in readme
    assert "POST-H-022-C — Enterprise control matrix" in runbook
    assert "POST-H-022-D — Validator/report read-only" in readme
    assert "POST-H-022-D — Validator/report read-only" in runbook
    assert "POST-H-022-E — Runbook y cierre" in readme
    assert "POST-H-022-E — Runbook y cierre" in runbook
    assert "POST-H-023-A — Requisitos y amenazas de transporte" in readme
    assert "POST-H-023-A — Requisitos y amenazas de transporte" in runbook
    assert "POST-H-023-B — Protocol decision matrix y ADR" in readme
    assert "POST-H-023-B — Protocol decision matrix y ADR" in runbook
    assert "post-h-023-a" in changelog
    assert "post-h-023-b" in changelog
    assert "post-h-021-a" in changelog
    assert "post-h-021-b" in changelog
    assert "post-h-021-c" in changelog
    assert "post-h-021-d" in changelog
    assert "post-h-021-e" in changelog
    assert "post-h-022-a" in changelog
    assert "post-h-022-b" in changelog
    assert "post-h-022-c" in changelog
    assert "POST-H-020 — Compliance mapping packs ampliados" in readme
    assert "POST-H-021-A — Inventario remote y baseline de bloqueo" in readme
    assert "POST-H-021-A — Inventario remote y baseline de bloqueo" in runbook
    assert "POST-H-021-B — ADR-2 de Remote Runner" in readme
    assert "POST-H-021-B — ADR-2 de Remote Runner" in runbook
    assert "post-h-021-b" in changelog
    assert "post-h-020-a" in changelog
    assert "post-h-020-b" in changelog
    assert "post-h-020-c" in changelog
    assert "post-h-020-d" in changelog
    assert "post-h-021-a" in changelog
    assert "post-h-019-b" in changelog
    assert "post-h-019-c" in changelog
    assert "POST-H-015-A — Dashboard snapshot schema y config" in readme
    assert "POST-H-015-A — Dashboard snapshot schema y config" in runbook
    assert "POST-H-015-B — Aggregator read-only de señales operacionales" in readme
    assert "POST-H-015-B — Aggregator read-only de señales operacionales" in runbook
    assert "POST-H-015-C — ApplicationService/API integration" in readme
    assert "POST-H-015-C — ApplicationService/API integration" in runbook
    assert "POST-H-015-D — UI operator dashboard" in readme
    assert "POST-H-015-D — UI operator dashboard" in runbook
    assert "POST-H-015-E — Quality gate y runbook operacional" in readme
    assert "POST-H-015-E — Quality gate y runbook operacional" in runbook
    assert "POST-H-016-A — Registry v2 y migración compatible" in readme
    assert "POST-H-016-A — Registry v2 y migración compatible" in runbook
    assert "POST-H-016-B — Workspace isolation validator" in readme
    assert "POST-H-016-B — Workspace isolation validator" in runbook
    assert "POST-H-016-C — Portfolio status hardening" in readme
    assert "POST-H-016-C — Portfolio status hardening" in runbook
    assert "POST-H-016-D — CLI/API integration segura" in readme
    assert "POST-H-016-D — CLI/API integration segura" in runbook
    assert "POST-H-016-E — Quality gate y runbook" in readme
    assert "POST-H-016-E — Quality gate y runbook" in runbook
    assert any("POST-H-012-A approves" in note for note in state["notes"])
    assert any("POST-H-012-C adds RBAC exposure reporting" in note for note in state["notes"])
    assert any("POST-H-012-D adds homogeneous PolicyEngine enforcement" in note for note in state["notes"])
    assert any("POST-H-012-E closes Approval/RBAC hardening" in note for note in state["notes"])

    assert any("POST-H-025-A approves Production-ready local declaration gate" in note for note in state["notes"])
    assert any("POST-H-025-C adds industrial-readiness production-ready-local CLI" in note for note in state["notes"])
    assert any("POST-H-025-D adds ProductionReadyClaimsValidator" in note for note in state["notes"])
    assert any("POST-H-025-E adds ProductionReadyFinalDeclaration" in note for note in state["notes"])

    assert state.get("post_h_030_status") == "closed/cli-boundary-hotspot-reduction"
    assert state.get("post_h_030_cli_command_ownership_matrix_schema_registered") is True
    assert state.get("post_h_030_cli_extraction_plan_schema_registered") is True
    assert state.get("post_h_030_cli_command_ownership_matrix_available") is True
    assert state.get("post_h_030_cli_extraction_plan_available") is True
    assert state.get("post_h_030_cli_ownership_coverage_complete") is True
    assert state.get("post_h_030_cli_ownership_missing_owner_total") == 0
    assert state.get("post_h_030_cli_ownership_missing_compatibility_contract_total") == 0
    assert state.get("post_h_030_cli_dynamic_handler_loading_enabled") is False
    assert "POST-H-030-A — CLI command ownership matrix" in readme
    assert "POST-H-030-C — Release command extraction" in readme
    assert "POST-H-030-D — Workspace/onboarding command extraction" in readme
    assert "POST-H-030-A — CLI command ownership matrix" in runbook
    assert "POST-H-030-C — Release command extraction" in runbook
    assert "POST-H-030-D — Workspace/onboarding command extraction" in runbook
    assert "post-h-030-a" in changelog.lower()
    assert "post-h-030-b" in changelog.lower()
    assert "post-h-030-c" in changelog.lower()
    assert "post-h-030-d" in changelog.lower()
    assert any("POST-H-030-A approves CLI hotspot reduction" in note for note in state["notes"])
    assert any("POST-H-030-B extracts industrial-readiness" in note for note in state["notes"])
    assert any("POST-H-030-C extracts release" in note for note in state["notes"])
    assert any("POST-H-030-D extracts workspace" in note for note in state["notes"])
    assert state.get("post_h_030_industrial_readiness_commands_migrated_total") == 3
    assert state.get("post_h_030_industrial_readiness_application_service_preserved") is True
    assert state.get("post_h_030_release_cli_module") == "src/devpilot_core/cli_commands/release.py"
    assert state.get("post_h_030_release_commands_migrated_total") == 26
    assert state.get("post_h_030_release_public_behavior_changed") is False
    assert state.get("post_h_030_workspace_cli_module") == "src/devpilot_core/cli_commands/workspace.py"
    assert state.get("post_h_030_workspace_onboarding_cli_module") == "src/devpilot_core/cli_commands/workspace_onboarding.py"
    assert state.get("post_h_030_workspace_onboarding_commands_migrated_total") == 7
    assert state.get("post_h_030_workspace_onboarding_public_behavior_changed") is False
    assert state["current_micro_sprint"] in {"POST-H-033-D", "POST-H-033-E", "POST-H-033-F", "POST-H-034-A", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE", "POST-H-EVAL-002-01-A", "POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state["next_micro_sprint"] in {"POST-H-033-E", "POST-H-033-F", "POST-H-033-CLOSURE", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE", "POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state.get("post_h_029_test_impact_rule_registry_valid") is True
    assert state.get("post_h_029_test_impact_rules_unknown_impact_escalates") is True
    assert state.get("post_h_029_test_impact_rules_unsafe_commands_total") == 0
    assert "POST-H-025-A — Criteria schema y evidence map" in readme
    assert "POST-H-025-A — Criteria schema y evidence map" in runbook
    assert "POST-H-025-C — Declaration gate CLI/API" in readme
    assert "POST-H-025-C — Declaration gate CLI/API" in runbook
    assert "POST-H-025-D — No-go gates y claims validator" in readme
    assert "POST-H-025-D — No-go gates y claims validator" in runbook
    assert "POST-H-025-E — Declaración final o BLOCK report" in readme
    assert "POST-H-025-E — Declaración final o BLOCK report" in runbook
    assert "post-h-025-a" in changelog
    assert "post-h-025-b" in changelog
    assert "post-h-025-d" in changelog
    assert "post-h-025-e" in changelog


def test_project_global_state_command_result_passes() -> None:
    result = TestContractRegistry(ROOT).project_state()

    assert result.ok, result.to_dict()
    assert result.data["summary"]["last_completed_sprint"] == "POST-H-034"
    assert result.data["summary"]["next_sprint"] == "POST-H-EVAL-002"
    assert result.data["summary"]["checks_passed"] == result.data["summary"]["checks_total"]


def test_post_h_030_e_project_state_closes_cli_hotspot_backlog() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")

    assert state.get("post_h_030_status") == "closed/cli-boundary-hotspot-reduction"
    assert state.get("post_h_030_cli_compatibility_contracts_available") is True
    assert state.get("post_h_030_cli_compatibility_quality_gate_enabled") is True
    assert state.get("post_h_030_closed") is True
    assert "POST-H-030-E — CLI compatibility contract tests" in readme
    assert "POST-H-030-E — CLI compatibility contract tests" in runbook
    assert "post-h-030-e" in changelog.lower()


def test_post_h_031_a_project_state_starts_evidence_graph_model() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-031_observability_evidence_graph_operator.md")

    assert state.get("post_h_031_status") == "closed/redacted-evidence-export-ux"
    assert state.get("post_h_031_backlog_approved") is True
    assert state.get("post_h_031_current_micro_sprint") == "POST-H-031-E"
    assert state.get("post_h_031_next_micro_sprint") == "POST-H-032-A"
    assert state.get("post_h_031_evidence_graph_schema_registered") is True
    assert state.get("post_h_031_evidence_graph_available") is True
    assert state.get("post_h_031_evidence_graph_declares_readiness") is False
    assert state.get("post_h_031_evidence_graph_read_only") is True
    assert state.get("post_h_031_evidence_graph_network_used") is False
    assert state.get("post_h_031_evidence_graph_external_api_used") is False
    assert state.get("post_h_031_evidence_graph_commands_executed") is False
    assert state.get("post_h_031_evidence_graph_secret_reads") is False
    assert state.get("post_h_031_evidence_graph_devpilot_db_read") is False
    assert "POST-H-031-A — Evidence graph model" in readme
    assert "POST-H-031-A — Evidence graph model" in runbook
    assert "post-h-031-a" in changelog.lower()
    assert 'status: approved' in backlog
    assert 'implementation_status: "closed/redacted-evidence-export-ux"' in backlog
    assert any("POST-H-031-A starts Observabilidad" in note for note in state["notes"])


def test_post_h_031_b_project_state_adds_operator_health_summary() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-031_observability_evidence_graph_operator.md")

    assert state.get("post_h_031_status") == "closed/redacted-evidence-export-ux"
    assert state.get("post_h_031_current_micro_sprint") == "POST-H-031-E"
    assert state.get("post_h_031_next_micro_sprint") == "POST-H-032-A"
    assert state.get("post_h_031_operator_health_schema_registered") is True
    assert state.get("post_h_031_operator_health_available") is True
    assert state.get("post_h_031_operator_health_read_only") is True
    assert state.get("post_h_031_operator_health_network_used") is False
    assert state.get("post_h_031_operator_health_external_api_used") is False
    assert state.get("post_h_031_operator_health_commands_executed") is False
    assert state.get("post_h_031_operator_health_secret_reads") is False
    assert state.get("post_h_031_operator_health_devpilot_db_read") is False
    assert state.get("post_h_031_operator_health_replaces_quality_gates") is False
    assert "POST-H-031-B — Operator health summary" in readme
    assert "POST-H-031-B — Operator health summary" in runbook
    assert "post-h-031-b" in changelog.lower()
    assert 'implementation_status: "closed/redacted-evidence-export-ux"' in backlog
    assert any("POST-H-031-B adds OperatorHealthSummary" in note for note in state["notes"])


def test_post_h_031_c_project_state_adds_gap_action_mapping() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-031_observability_evidence_graph_operator.md")

    assert state.get("post_h_031_status") == "closed/redacted-evidence-export-ux"
    assert state.get("post_h_031_current_micro_sprint") == "POST-H-031-E"
    assert state.get("post_h_031_next_micro_sprint") == "POST-H-032-A"
    assert state.get("post_h_031_gap_action_schema_registered") is True
    assert state.get("post_h_031_gap_action_available") is True
    assert state.get("post_h_031_gap_action_read_only") is True
    assert state.get("post_h_031_gap_action_network_used") is False
    assert state.get("post_h_031_gap_action_external_api_used") is False
    assert state.get("post_h_031_gap_action_commands_executed") is False
    assert state.get("post_h_031_gap_action_secret_reads") is False
    assert state.get("post_h_031_gap_action_devpilot_db_read") is False
    assert state.get("post_h_031_gap_action_replaces_quality_gates") is False
    assert state.get("post_h_031_gap_action_executes_recommended_actions") is False
    assert "POST-H-031-C — Gap-to-action mapping" in readme
    assert "POST-H-031-C — Gap-to-action mapping" in runbook
    assert "post-h-031-c" in changelog.lower()
    assert 'implementation_status: "closed/redacted-evidence-export-ux"' in backlog
    assert any("POST-H-031-C adds GapActionMap" in note for note in state["notes"])


def test_post_h_031_d_project_state_adds_claims_no_go_dashboard() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-031_observability_evidence_graph_operator.md")

    assert state.get("post_h_031_status") == "closed/redacted-evidence-export-ux"
    assert state.get("post_h_031_current_micro_sprint") == "POST-H-031-E"
    assert state.get("post_h_031_next_micro_sprint") == "POST-H-032-A"
    assert state.get("post_h_031_claims_no_go_schema_registered") is True
    assert state.get("post_h_031_claims_no_go_available") is True
    assert state.get("post_h_031_claims_no_go_read_only") is True
    assert state.get("post_h_031_claims_no_go_network_used") is False
    assert state.get("post_h_031_claims_no_go_external_api_used") is False
    assert state.get("post_h_031_claims_no_go_commands_executed") is False
    assert state.get("post_h_031_claims_no_go_secret_reads") is False
    assert state.get("post_h_031_claims_no_go_devpilot_db_read") is False
    assert state.get("post_h_031_claims_no_go_replaces_quality_gates") is False
    assert state.get("post_h_031_claims_no_go_mutates_claims") is False
    assert state.get("post_h_031_claims_no_go_mutates_no_go_gates") is False
    assert state.get("post_h_031_claims_no_go_forbidden_claims_blocked") is True
    assert "POST-H-031-D — Claims and no-go dashboard" in readme
    assert "POST-H-031-D — Claims and no-go dashboard" in runbook
    assert "post-h-031-d" in changelog.lower()
    assert 'implementation_status: "closed/redacted-evidence-export-ux"' in backlog
    assert any("POST-H-031-D adds ClaimsNoGoDashboard" in note for note in state["notes"])


def test_post_h_031_e_project_state_closes_redacted_evidence_export_ux() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-031_observability_evidence_graph_operator.md")

    assert state.get("post_h_031_status") == "closed/redacted-evidence-export-ux"
    assert state.get("post_h_031_current_micro_sprint") == "POST-H-031-E"
    assert state.get("post_h_031_next_micro_sprint") == "POST-H-032-A"
    assert state.get("post_h_031_closed") is True
    assert state.get("post_h_031_operator_evidence_export_schema_registered") is True
    assert state.get("post_h_031_operator_evidence_export_available") is True
    assert state.get("post_h_031_operator_evidence_export_redacted_required") is True
    assert state.get("post_h_031_operator_evidence_export_dry_run_default") is True
    assert state.get("post_h_031_operator_evidence_export_network_used") is False
    assert state.get("post_h_031_operator_evidence_export_external_api_used") is False
    assert state.get("post_h_031_operator_evidence_export_commands_executed") is False
    assert state.get("post_h_031_operator_evidence_export_source_mutations") is False
    assert state.get("post_h_031_operator_evidence_export_raw_payloads_exported") is False
    assert state.get("post_h_031_operator_evidence_export_devpilot_db_exported") is False
    assert state.get("post_h_031_operator_evidence_export_replaces_quality_gates") is False
    assert "POST-H-031-E — Redacted evidence export UX" in readme
    assert "POST-H-031-E — Redacted evidence export UX" in runbook
    assert "post-h-031-e" in changelog.lower()
    assert 'implementation_status: "closed/redacted-evidence-export-ux"' in backlog
    assert any("POST-H-031-E adds OperatorEvidenceExport" in note for note in state["notes"])


def test_post_h_032_a_project_state_adds_agent_capability_inventory() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md")

    assert state.get("post_h_032_backlog_approved") is True
    assert state.get("post_h_032_status") in {"active/tool-calling-contract-implemented-initial", "active/mcp-fake-server-evaluation-implemented-initial", "active/multiagent-handoff-hardening-implemented-initial", "closed/advanced-ai-agents-governed"}
    assert state.get("post_h_032_current_micro_sprint") == "POST-H-032-H"
    assert state.get("post_h_032_next_micro_sprint") == "POST-H-033-A"
    assert state.get("post_h_032_agent_capability_inventory_schema_registered") is True
    assert state.get("post_h_032_agent_promotion_criteria_schema_registered") is True
    assert state.get("post_h_032_agent_capability_inventory_available") is True
    assert state.get("post_h_032_agent_promotion_criteria_available") is True
    assert state.get("post_h_032_agents_total") == 14
    assert state.get("post_h_032_implemented_agents_total") >= 13
    assert state.get("post_h_032_external_api_allowed_total") == 0
    assert state.get("post_h_032_memory_enabled_total") == 0
    assert state.get("post_h_032_remote_execution_enabled") is False
    assert state.get("post_h_032_connector_write_enabled") is False
    assert state.get("post_h_032_plugin_execution_enabled") is False
    assert state.get("post_h_032_models_called") is False
    assert state.get("post_h_032_agents_executed") is False
    assert "POST-H-032-A — Agent capability inventory" in readme
    assert "POST-H-032-A — Agent capability inventory" in runbook
    assert "post-h-032-a" in changelog.lower()
    assert "status: approved" in backlog
    assert any(marker in backlog for marker in ['implementation_status: "approved/post-h-032-h-implemented-initial"', 'implementation_status: "closed/advanced-ai-agents-governed"'])
    assert any("POST-H-032-A starts Agentes IA avanzados" in note for note in state["notes"])


def test_post_h_032_b_project_state_adds_local_llm_provider_hardening() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md")

    assert state.get("post_h_032_status") in {"active/tool-calling-contract-implemented-initial", "active/mcp-fake-server-evaluation-implemented-initial", "active/multiagent-handoff-hardening-implemented-initial", "closed/advanced-ai-agents-governed"}
    assert state.get("post_h_032_current_micro_sprint") == "POST-H-032-H"
    assert state.get("post_h_032_next_micro_sprint") == "POST-H-033-A"
    assert state.get("post_h_032_b_local_llm_provider_health_schema_registered") is True
    assert state.get("post_h_032_b_local_llm_provider_health_schema_registered") is True
    assert state.get("post_h_032_b_local_llm_provider_health_policy_path") == ".devpilot/modeling/local_llm_provider_health_policy.json"
    assert state.get("post_h_032_b_local_llm_provider_health_cli_command") == "python -m devpilot_core model local-health --json"
    assert state.get("post_h_032_b_local_llm_provider_health_application_service_method") == "ApplicationService.local_llm_provider_health"
    assert state.get("post_h_032_b_local_providers_total") == 2
    assert state.get("post_h_032_b_required_local_providers_present_total") == 2
    assert state.get("post_h_032_b_local_providers_disabled_by_default") is True
    assert state.get("post_h_032_b_local_enabled_total") == 0
    assert state.get("post_h_032_b_localhost_only") is True
    assert state.get("post_h_032_b_non_localhost_endpoint_total") == 0
    assert state.get("post_h_032_b_requires_api_key_total") == 0
    assert state.get("post_h_032_b_external_api_used") is False
    assert state.get("post_h_032_b_external_api_enabled") is False
    assert state.get("post_h_032_b_real_local_server_required_for_tests") is False
    assert state.get("post_h_032_b_fake_provider_tests_supported") is True
    assert state.get("post_h_032_b_fallback_to_mock_allowed") is True
    assert state.get("post_h_032_b_fallback_to_mock_explicit") is True
    assert state.get("post_h_032_b_budget_ledger_zero_cost_supported") is True
    assert state.get("post_h_032_b_network_used_by_default") is False
    assert state.get("post_h_032_b_models_called_by_health_report") is False
    assert state.get("post_h_032_b_remote_execution_enabled") is False
    assert state.get("post_h_032_b_connector_write_enabled") is False
    assert state.get("post_h_032_b_plugin_execution_enabled") is False
    assert state.get("post_h_032_b_source_mutations") is False
    assert "POST-H-032-B — Local LLM provider hardening" in readme
    assert "POST-H-032-B — Local LLM provider hardening" in runbook
    assert "post-h-032-b" in changelog.lower()
    assert any(marker in backlog for marker in ['implementation_status: "approved/post-h-032-h-implemented-initial"', 'implementation_status: "closed/advanced-ai-agents-governed"'])
    assert any("POST-H-032-B adds LocalLlmProviderHealthReport" in note for note in state["notes"])

def test_post_h_032_c_project_state_adds_external_api_provider_pilot() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md")

    assert state.get("post_h_032_status") in {"active/tool-calling-contract-implemented-initial", "active/mcp-fake-server-evaluation-implemented-initial", "active/multiagent-handoff-hardening-implemented-initial", "closed/advanced-ai-agents-governed"}
    assert state.get("post_h_032_current_micro_sprint") == "POST-H-032-H"
    assert state.get("post_h_032_next_micro_sprint") == "POST-H-033-A"
    assert state.get("post_h_032_c_external_api_provider_pilot_schema_registered") is True
    assert state.get("post_h_032_c_external_api_provider_pilot_policy_path") == ".devpilot/modeling/external_api_provider_pilot_policy.json"
    assert state.get("post_h_032_c_external_api_provider_pilot_adr_path") == "docs/adr/ADR-POSTH-032-C-external-api-provider-gated-pilot.md"
    assert state.get("post_h_032_c_external_api_provider_pilot_module") == "src/devpilot_core/modeling/external_api_pilot.py"
    assert state.get("post_h_032_c_external_api_provider_pilot_cli_command") == "python -m devpilot_core model external-api-pilot --json"
    assert state.get("post_h_032_c_external_api_provider_pilot_application_service_method") == "ApplicationService.external_api_provider_pilot"
    assert state.get("post_h_032_c_api_providers_total") == 2
    assert state.get("post_h_032_c_api_enabled_total") == 0
    assert state.get("post_h_032_c_api_disabled_by_default") is True
    assert state.get("post_h_032_c_api_requires_env_var_total") == 2
    assert state.get("post_h_032_c_api_key_values_in_repo_total") == 0
    assert state.get("post_h_032_c_fake_provider_contract_ok") is True
    assert state.get("post_h_032_c_tests_require_real_api") is False
    assert state.get("post_h_032_c_real_api_call_performed") is False
    assert state.get("post_h_032_c_real_api_call_supported_by_this_sprint") is False
    assert state.get("post_h_032_c_external_api_used") is False
    assert state.get("post_h_032_c_network_used") is False
    assert state.get("post_h_032_c_cost_guard_required") is True
    assert state.get("post_h_032_c_cost_guard_blocks_accidental_external_api") is True
    assert state.get("post_h_032_c_secret_handling_env_only") is True
    assert state.get("post_h_032_c_secrets_read") is False
    assert state.get("post_h_032_c_operator_warning_required") is True
    assert state.get("post_h_032_c_risk_report_required") is True
    assert state.get("post_h_032_c_remote_execution_enabled") is False
    assert state.get("post_h_032_c_connector_write_enabled") is False
    assert state.get("post_h_032_c_plugin_execution_enabled") is False
    assert state.get("post_h_032_c_source_mutations") is False
    assert "POST-H-032-C — External API provider ADR and gated pilot" in readme
    assert "POST-H-032-C — External API provider ADR and gated pilot" in runbook
    assert "post-h-032-c" in changelog.lower()
    assert any(marker in backlog for marker in ['implementation_status: "approved/post-h-032-h-implemented-initial"', 'implementation_status: "closed/advanced-ai-agents-governed"'])
    assert any("POST-H-032-C adds ExternalApiProviderPilot" in note for note in state["notes"])



def test_post_h_032_d_project_state_adds_rag_aware_agents() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")

    assert state.get("post_h_032_status") in {"active/tool-calling-contract-implemented-initial", "active/mcp-fake-server-evaluation-implemented-initial", "active/multiagent-handoff-hardening-implemented-initial", "closed/advanced-ai-agents-governed"}
    assert state.get("post_h_032_current_micro_sprint") == "POST-H-032-H"
    assert state.get("post_h_032_next_micro_sprint") == "POST-H-033-A"
    assert state.get("post_h_032_d_rag_agent_context_schema_registered") is True
    assert state.get("post_h_032_d_rag_agent_bindings_path") == ".devpilot/agents/rag_agent_bindings.json"
    assert state.get("post_h_032_d_rag_agent_context_module") == "src/devpilot_core/agents/rag_context.py"
    assert state.get("post_h_032_d_rag_agent_context_cli_command") == "python -m devpilot_core agent rag-context --json"
    assert state.get("post_h_032_d_rag_agent_context_application_service_method") == "ApplicationService.rag_agent_context"
    assert state.get("post_h_032_d_target_agents_total") == 5
    assert state.get("post_h_032_d_context_pack_sources_required") is True
    assert state.get("post_h_032_d_all_grounded_suggestions_have_sources") is True
    assert state.get("post_h_032_d_insufficient_evidence_behavior_enabled") is True
    assert state.get("post_h_032_d_negative_cases_passed") is True
    assert state.get("post_h_032_d_prohibited_claims_justified_total") == 0
    assert state.get("post_h_032_d_llm_used") is False
    assert state.get("post_h_032_d_external_api_used") is False
    assert state.get("post_h_032_d_network_used") is False
    assert state.get("post_h_032_d_memory_used") is False
    assert state.get("post_h_032_d_tools_executed") is False
    assert state.get("post_h_032_d_source_mutations") is False
    assert "POST-H-032-D — RAG-aware agents" in readme
    assert "POST-H-032-D — RAG-aware agents" in runbook
    assert any("POST-H-032-D adds RAG-aware agent context packs" in note for note in state["notes"])



def test_post_h_032_f_project_state_adds_tool_calling_contract() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md")

    assert state.get("post_h_032_status") in {"active/tool-calling-contract-implemented-initial", "active/mcp-fake-server-evaluation-implemented-initial", "active/multiagent-handoff-hardening-implemented-initial", "closed/advanced-ai-agents-governed"}
    assert state.get("post_h_032_current_micro_sprint") == "POST-H-032-H"
    assert state.get("post_h_032_next_micro_sprint") == "POST-H-033-A"
    assert state.get("post_h_032_f_tool_call_schema_registered") is True
    assert state.get("post_h_032_f_tool_call_policy_path") == ".devpilot/agents/tool_call_policy.json"
    assert state.get("post_h_032_f_tool_call_module") == "src/devpilot_core/agents/tool_calls.py"
    assert state.get("post_h_032_f_tool_call_cli_command") == "python -m devpilot_core agent tool-calls validate --json"
    assert state.get("post_h_032_f_tool_call_application_service_method") == "ApplicationService.agent_tool_call_contract"
    assert state.get("post_h_032_f_contract_only") is True
    assert state.get("post_h_032_f_fake_local_tools_only") is True
    assert state.get("post_h_032_f_dry_run_first_default") is True
    assert state.get("post_h_032_f_allowlist_required") is True
    assert state.get("post_h_032_f_approval_binding_for_risky_tools") is True
    assert state.get("post_h_032_f_tool_injection_guard_enabled") is True
    assert state.get("post_h_032_f_observability_traceable") is True
    assert state.get("post_h_032_f_connector_write_enabled") is False
    assert state.get("post_h_032_f_plugin_execution_enabled") is False
    assert state.get("post_h_032_f_remote_execution_enabled") is False
    assert state.get("post_h_032_f_tools_executed") is False
    assert state.get("post_h_032_f_network_used") is False
    assert state.get("post_h_032_f_external_api_used") is False
    assert state.get("post_h_032_f_llm_used") is False
    assert state.get("post_h_032_f_source_mutations") is False
    assert "POST-H-032-F — Tool calling contract" in readme
    assert "POST-H-032-F — Tool calling contract" in runbook
    assert "post-h-032-f" in changelog.lower()
    assert any(marker in backlog for marker in ['implementation_status: "approved/post-h-032-h-implemented-initial"', 'implementation_status: "closed/advanced-ai-agents-governed"'])
    assert any("POST-H-032-F adds an implemented-initial contract-only agent tool-calling layer" in note for note in state["notes"])

def test_post_h_032_e_project_state_adds_agent_memory_model() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md")

    assert state.get("post_h_032_status") in {"active/tool-calling-contract-implemented-initial", "active/mcp-fake-server-evaluation-implemented-initial", "active/multiagent-handoff-hardening-implemented-initial", "closed/advanced-ai-agents-governed"}
    assert state.get("post_h_032_current_micro_sprint") == "POST-H-032-H"
    assert state.get("post_h_032_next_micro_sprint") == "POST-H-033-A"
    assert state.get("post_h_032_e_agent_memory_schema_registered") is True
    assert state.get("post_h_032_e_agent_memory_policy_path") == ".devpilot/agents/agent_memory_policy.json"
    assert state.get("post_h_032_e_agent_memory_adr_path") == "docs/adr/ADR-POSTH-032-E-agent-memory-local-opt-in.md"
    assert state.get("post_h_032_e_agent_memory_module") == "src/devpilot_core/agents/memory.py"
    assert state.get("post_h_032_e_agent_memory_cli_command") == "python -m devpilot_core agent memory inspect --json"
    assert state.get("post_h_032_e_agent_memory_application_service_method") == "ApplicationService.agent_memory_model"
    assert state.get("post_h_032_e_semantic_memory_enabled") is False
    assert state.get("post_h_032_e_memory_enabled_by_default") is False
    assert state.get("post_h_032_e_raw_prompts_stored") is False
    assert state.get("post_h_032_e_raw_outputs_stored") is False
    assert state.get("post_h_032_e_secrets_stored") is False
    assert state.get("post_h_032_e_external_storage_used") is False
    assert state.get("post_h_032_e_shared_workspace_memory_enabled") is False
    assert state.get("post_h_032_e_export_always_redacted") is True
    assert state.get("post_h_032_e_cleanup_dry_run_default") is True
    assert state.get("post_h_032_e_retention_policy_applied") is True
    assert state.get("post_h_032_e_memory_counts_as_formal_evidence") is False
    assert state.get("post_h_032_e_session_memory_separated") is True
    assert state.get("post_h_032_e_project_memory_separated") is True
    assert state.get("post_h_032_e_report_evidence_separated") is True
    assert state.get("post_h_032_e_network_used") is False
    assert state.get("post_h_032_e_external_api_used") is False
    assert state.get("post_h_032_e_tools_executed") is False
    assert state.get("post_h_032_e_llm_used") is False
    assert state.get("post_h_032_e_source_mutations") is False
    assert "POST-H-032-E — Agent memory model" in readme
    assert "POST-H-032-E — Agent memory model" in runbook
    assert "post-h-032-e" in changelog.lower()
    assert any(marker in backlog for marker in ['implementation_status: "approved/post-h-032-h-implemented-initial"', 'implementation_status: "closed/advanced-ai-agents-governed"'])
    assert any("POST-H-032-E adds local opt-in agent memory model" in note for note in state["notes"])


def test_post_h_032_g_project_state_adds_mcp_fake_server_evaluation() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")

    assert state.get("post_h_032_current_micro_sprint") == "POST-H-032-H"
    assert state.get("post_h_032_next_micro_sprint") == "POST-H-033-A"
    assert state.get("post_h_032_g_mcp_fake_server_schema_registered") is True
    assert state.get("post_h_032_g_mcp_fake_server_contract_path") == ".devpilot/mcp/mcp_fake_server_contract.json"
    assert state.get("post_h_032_g_mcp_fake_server_cli_command") == "python -m devpilot_core agent mcp-fake-server evaluate --json"
    assert state.get("post_h_032_g_mcp_fake_server_application_service_method") == "ApplicationService.mcp_fake_server_evaluation"
    assert state.get("post_h_032_g_mcp_real_enabled") is False
    assert state.get("post_h_032_g_fake_server_only") is True
    assert state.get("post_h_032_g_permission_model_present") is True
    assert state.get("post_h_032_g_threat_model_present") is True
    assert state.get("post_h_032_g_write_execute_tools_require_approval") is True
    assert state.get("post_h_032_g_tool_injection_guard_enabled") is True
    assert state.get("post_h_032_g_connector_write_enabled") is False
    assert state.get("post_h_032_g_plugin_execution_enabled") is False
    assert state.get("post_h_032_g_remote_execution_enabled") is False
    assert state.get("post_h_032_g_network_used") is False
    assert state.get("post_h_032_g_external_api_used") is False
    assert state.get("post_h_032_g_tools_executed") is False
    assert "POST-H-032-H — Multiagent handoff hardening" in readme
    assert "POST-H-032-H — Multiagent handoff hardening" in runbook
    assert any("POST-H-032-H adds implemented-initial deterministic multiagent handoff hardening" in note for note in state["notes"])


def test_post_h_032_h_project_state_adds_multiagent_handoff_hardening() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md")

    assert state.get("post_h_032_status") in {"active/multiagent-handoff-hardening-implemented-initial", "closed/advanced-ai-agents-governed"}
    assert state.get("post_h_032_current_micro_sprint") == "POST-H-032-H"
    assert state.get("post_h_032_next_micro_sprint") == "POST-H-033-A"
    assert state.get("post_h_032_h_multiagent_handoff_schema_registered") is True
    assert state.get("post_h_032_h_multiagent_handoff_policy_path") == ".devpilot/agents/multiagent_handoff_policy.json"
    assert state.get("post_h_032_h_multiagent_handoff_module") == "src/devpilot_core/multiagent/hardening.py"
    assert state.get("post_h_032_h_multiagent_handoff_cli_command") == "python -m devpilot_core multiagent handoff harden --json"
    assert state.get("post_h_032_h_multiagent_handoff_application_service_method") == "ApplicationService.multiagent_handoff_hardening"
    assert state.get("post_h_032_h_workflow_registry_path") == ".devpilot/workflows/sdlc_review.json"
    assert state.get("post_h_032_h_swarm_autonomy_enabled") is False
    assert state.get("post_h_032_h_handoffs_explicit") is True
    assert state.get("post_h_032_h_handoffs_visible") is True
    assert state.get("post_h_032_h_handoffs_traceable") is True
    assert state.get("post_h_032_h_agent_scopes_preserved") is True
    assert state.get("post_h_032_h_child_inherits_unscoped_tools") is False
    assert state.get("post_h_032_h_supervisor_gate_enabled") is True
    assert state.get("post_h_032_h_supervisor_gate_deterministic") is True
    assert state.get("post_h_032_h_supervisor_can_block_insufficient_evidence") is True
    assert state.get("post_h_032_h_human_checkpoints_required") is True
    assert state.get("post_h_032_h_workflow_evals_positive_negative") is True
    assert state.get("post_h_032_h_connector_write_enabled") is False
    assert state.get("post_h_032_h_plugin_execution_enabled") is False
    assert state.get("post_h_032_h_remote_execution_enabled") is False
    assert state.get("post_h_032_h_network_used") is False
    assert state.get("post_h_032_h_external_api_used") is False
    assert state.get("post_h_032_h_llm_used") is False
    assert state.get("post_h_032_h_tools_executed") is False
    assert state.get("post_h_032_h_source_mutations") is False
    assert state.get("post_h_032_backlog_closure_candidate") in {True, False}
    assert "POST-H-032-H — Multiagent handoff hardening" in readme
    assert "POST-H-032-H — Multiagent handoff hardening" in runbook
    assert "post-h-032-h" in changelog.lower()
    assert any(marker in backlog for marker in ['implementation_status: "approved/post-h-032-h-implemented-initial"', 'implementation_status: "closed/advanced-ai-agents-governed"'])
    assert any("POST-H-032-H adds implemented-initial deterministic multiagent handoff hardening" in note for note in state["notes"])



def test_post_h_033_a_project_state_adds_validator_inventory_migration_plan() -> None:
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-033_schema_backed_validators_declarative_semantics.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    assert state["current_micro_sprint"] in {"POST-H-033-D", "POST-H-033-E", "POST-H-033-F", "POST-H-034-A", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE", "POST-H-EVAL-002-01-A", "POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state["next_micro_sprint"] in {"POST-H-033-E", "POST-H-033-F", "POST-H-033-CLOSURE", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE", "POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state["post_h_032_status"] == "closed/advanced-ai-agents-governed"
    assert state["post_h_032_closed"] is True
    assert state["post_h_033_status"] in {"active/readiness-requirements-registry-implemented-initial", "active/miasi-semantic-rules-registry-implemented-initial", "active/policy-guard-pattern-catalogs-implemented-initial", "active/docs-governance-rule-registry-implemented-initial", "closed/schema-backed-validators-declarative-semantics"}
    assert state["post_h_033_backlog_approved"] is True
    assert state["post_h_033_a_closed"] is True
    assert state["post_h_033_a_validator_inventory_available"] is True
    assert state["post_h_033_a_validator_inventory_schema_registered"] is True
    assert state["post_h_033_a_validator_migration_report_schema_registered"] is True
    assert state["post_h_033_a_runtime_behavior_changed"] is False
    assert state["post_h_033_a_llm_judge_required"] is False
    assert state["post_h_033_a_external_dependencies_added"] is False
    assert state["post_h_033_a_no_go_gates_preserved"] is True
    assert state["post_h_033_a_critical_defenses_disable_allowed"] is False
    assert "POST-H-033-A — Validator inventory and migration plan" in readme
    assert "POST-H-033-A — Validator inventory and migration plan" in runbook
    assert any(marker in backlog for marker in ['implementation_status: "active/post-h-033-c-implemented-initial"', 'implementation_status: "active/post-h-033-d-implemented-initial"', 'implementation_status: "active/post-h-033-e-implemented-initial"', 'implementation_status: "active/post-h-033-f-implemented-initial"'])
    assert "post-h-033-a" in changelog.lower()


def test_post_h_033_b_project_state_adds_frontmatter_schema_backed_validator() -> None:
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-033_schema_backed_validators_declarative_semantics.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    assert state["current_micro_sprint"] in {"POST-H-033-D", "POST-H-033-E", "POST-H-033-F", "POST-H-034-A", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE", "POST-H-EVAL-002-01-A", "POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state["next_micro_sprint"] in {"POST-H-033-E", "POST-H-033-F", "POST-H-033-CLOSURE", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE", "POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state["post_h_033_a_closed"] is True
    assert state["post_h_033_status"] in {"active/readiness-requirements-registry-implemented-initial", "active/miasi-semantic-rules-registry-implemented-initial", "active/policy-guard-pattern-catalogs-implemented-initial", "active/docs-governance-rule-registry-implemented-initial", "closed/schema-backed-validators-declarative-semantics"}
    assert state["post_h_033_b_frontmatter_catalog_available"] is True
    assert state["post_h_033_b_frontmatter_metadata_schema_registered"] is True
    assert state["post_h_033_b_frontmatter_validator_integrated"] is True
    assert state["post_h_033_b_catalog_source_primary"] is True
    assert state["post_h_033_b_python_fallback_required"] is True
    assert state["post_h_033_b_parser_dependency_free"] is True
    assert state["post_h_033_b_runtime_behavior_changed"] is False
    assert state["post_h_033_b_finding_ids_preserved"] is True
    assert state["post_h_033_b_no_yaml_dependency_added"] is True
    assert state["post_h_033_b_llm_judge_required"] is False
    assert state["post_h_033_b_network_used"] is False
    assert state["post_h_033_b_external_api_used"] is False
    assert state["post_h_033_b_critical_rules_disable_allowed"] is False
    assert state["post_h_033_b_rule_source_reported"] is True
    assert state["post_h_033_b_catalog_version_reported"] is True
    assert "POST-H-033-B — Frontmatter schema-backed validator" in readme
    assert "POST-H-033-B — Frontmatter schema-backed validator" in runbook
    assert any(marker in backlog for marker in ['implementation_status: "active/post-h-033-c-implemented-initial"', 'implementation_status: "active/post-h-033-d-implemented-initial"', 'implementation_status: "active/post-h-033-e-implemented-initial"', 'implementation_status: "active/post-h-033-f-implemented-initial"'])
    assert "post-h-033-b" in changelog.lower()


def test_post_h_033_c_project_state_adds_readiness_requirements_registry() -> None:
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-033_schema_backed_validators_declarative_semantics.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    assert state["current_micro_sprint"] in {"POST-H-033-D", "POST-H-033-E", "POST-H-033-F", "POST-H-034-A", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE", "POST-H-EVAL-002-01-A", "POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state["next_micro_sprint"] in {"POST-H-033-E", "POST-H-033-F", "POST-H-033-CLOSURE", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE", "POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state["post_h_033_b_closed"] is True
    assert state["post_h_033_status"] in {"active/readiness-requirements-registry-implemented-initial", "active/miasi-semantic-rules-registry-implemented-initial", "active/policy-guard-pattern-catalogs-implemented-initial", "active/docs-governance-rule-registry-implemented-initial", "closed/schema-backed-validators-declarative-semantics"}
    assert state["post_h_033_c_readiness_requirements_available"] is True
    assert state["post_h_033_c_readiness_requirements_schema_registered"] is True
    assert state["post_h_033_c_readiness_validator_integrated"] is True
    assert state["post_h_033_c_registry_source_primary"] is True
    assert state["post_h_033_c_python_fallback_required"] is True
    assert state["post_h_033_c_runtime_behavior_changed"] is False
    assert state["post_h_033_c_required_pre_code_artifacts_preserved"] is True
    assert state["post_h_033_c_required_miasi_artifacts_preserved"] is True
    assert state["post_h_033_c_strict_required_artifacts_preserved"] is True
    assert state["post_h_033_c_miasi_strict_required_preserved"] is True
    assert state["post_h_033_c_invalid_registry_blocks_success"] is True
    assert state["post_h_033_c_llm_judge_required"] is False
    assert state["post_h_033_c_network_used"] is False
    assert state["post_h_033_c_external_api_used"] is False
    assert state["post_h_033_c_critical_rules_disable_allowed"] is False
    assert "POST-H-033-C — Readiness requirements registry" in readme
    assert "POST-H-033-C — Readiness requirements registry" in runbook
    assert any(marker in backlog for marker in ['implementation_status: "active/post-h-033-c-implemented-initial"', 'implementation_status: "active/post-h-033-d-implemented-initial"', 'implementation_status: "active/post-h-033-e-implemented-initial"', 'implementation_status: "active/post-h-033-f-implemented-initial"'])
    assert "post-h-033-c" in changelog.lower()


def test_post_h_033_d_project_state_adds_miasi_semantic_rules_registry() -> None:
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))

    assert state["post_h_033_c_closed"] is True
    assert state["current_micro_sprint"] in {"POST-H-033-D", "POST-H-033-E", "POST-H-033-F", "POST-H-034-A", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE", "POST-H-EVAL-002-01-A", "POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state["next_micro_sprint"] in {"POST-H-033-E", "POST-H-033-F", "POST-H-033-CLOSURE", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE", "POST-H-EVAL-002-01-B", "POST-H-EVAL-002-01-C", "POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A"}
    assert state["post_h_033_d_miasi_semantic_rules_available"] is True
    assert state["post_h_033_d_miasi_semantic_rules_schema_registered"] is True
    assert state["post_h_033_d_miasi_semantic_validator_integrated"] is True
    assert state["post_h_033_d_registry_source_primary"] is True
    assert state["post_h_033_d_python_fallback_required"] is True
    assert state["post_h_033_d_runtime_behavior_changed"] is False
    assert state["post_h_033_d_finding_ids_preserved"] is True
    assert state["post_h_033_d_no_go_gates_preserved"] is True
    assert state["post_h_033_d_eval_fixture_coverage_preserved"] is True
    assert state["post_h_033_d_tokens_versioned"] is True
    assert state["post_h_033_d_guard_mappings_versioned"] is True
    assert state["post_h_033_d_invalid_registry_blocks_success"] is True
    assert state["post_h_033_d_rule_source_reported"] is True
    assert state["post_h_033_d_catalog_version_reported"] is True
    assert state["post_h_033_d_critical_rules_disable_allowed"] is False
    assert state["post_h_033_d_network_used"] is False
    assert state["post_h_033_d_external_api_used"] is False
    assert state["post_h_033_d_remote_execution_enabled"] is False
    assert state["post_h_033_d_connector_write_enabled"] is False
    assert state["post_h_033_d_plugin_execution_enabled"] is False
    assert state["post_h_033_d_source_mutations"] is False


def test_post_h_033_e_project_state_adds_policy_guard_pattern_catalogs() -> None:
    state = json.loads(read(".devpilot/project_state.json"))

    assert state["post_h_033_d_closed"] is True
    assert state["post_h_033_status"] in {"active/policy-guard-pattern-catalogs-implemented-initial", "active/docs-governance-rule-registry-implemented-initial", "closed/schema-backed-validators-declarative-semantics"}
    assert state["post_h_033_current_micro_sprint"] in {"POST-H-033-E", "POST-H-033-F", "POST-H-033-CLOSURE"}
    assert state["post_h_033_next_micro_sprint"] in {"POST-H-033-F", "POST-H-033-CLOSURE", "POST-H-034-A", "POST-H-034-B", "POST-H-034-C"}
    assert state["post_h_033_e_policy_guard_pattern_catalog_available"] is True
    assert state["post_h_033_e_policy_guard_pattern_catalog_schema_registered"] is True
    assert state["post_h_033_e_prompt_guard_integrated"] is True
    assert state["post_h_033_e_tool_injection_guard_integrated"] is True
    assert state["post_h_033_e_secret_guard_integrated"] is True
    assert state["post_h_033_e_registry_source_primary"] is True
    assert state["post_h_033_e_python_fallback_required"] is True
    assert state["post_h_033_e_runtime_behavior_changed"] is False
    assert state["post_h_033_e_finding_ids_preserved"] is True
    assert state["post_h_033_e_payload_redaction_preserved"] is True
    assert state["post_h_033_e_pattern_extensions_allowed"] is True
    assert state["post_h_033_e_critical_patterns_disable_allowed"] is False
    assert state["post_h_033_e_invalid_catalog_blocks_success"] is True
    assert state["post_h_033_e_missing_catalog_uses_fallback"] is True
    assert state["post_h_033_e_rule_source_reported"] is True
    assert state["post_h_033_e_catalog_version_reported"] is True
    assert state["post_h_033_e_llm_judge_required"] is False
    assert state["post_h_033_e_network_used"] is False
    assert state["post_h_033_e_external_api_used"] is False
    assert state["post_h_033_e_remote_execution_enabled"] is False
    assert state["post_h_033_e_connector_write_enabled"] is False
    assert state["post_h_033_e_plugin_execution_enabled"] is False
    assert state["post_h_033_e_source_mutations"] is False


def test_post_h_033_f_project_state_adds_docs_governance_rule_registry() -> None:
    state = json.loads(read(".devpilot/project_state.json"))

    assert state["post_h_033_e_closed"] is True
    assert state["post_h_033_status"] in {"active/docs-governance-rule-registry-implemented-initial", "closed/schema-backed-validators-declarative-semantics"}
    assert state.get("post_h_033_closed") is True
    assert state["post_h_033_current_micro_sprint"] in {"POST-H-033-F", "POST-H-033-CLOSURE"}
    assert state["post_h_033_next_micro_sprint"] in {"POST-H-033-CLOSURE", "POST-H-034-A", "POST-H-034-B", "POST-H-034-C"}
    assert state["post_h_033_f_docs_governance_rule_registry_available"] is True
    assert state["post_h_033_f_docs_governance_rule_registry_schema_registered"] is True
    assert state["post_h_033_f_docs_governance_validator_integrated"] is True
    assert state["post_h_033_f_registry_source_primary"] is True
    assert state["post_h_033_f_source_registry_preserved"] is True
    assert state["post_h_033_f_python_fallback_required"] is True
    assert state["post_h_033_f_runtime_behavior_changed"] is False
    assert state["post_h_033_f_finding_ids_preserved"] is True
    assert state["post_h_033_f_source_of_truth_drift_blocks"] is True
    assert state["post_h_033_f_required_tests_blocks"] is True
    assert state["post_h_033_f_frontmatter_required_preserved"] is True
    assert state["post_h_033_f_historical_active_authority_warns"] is True
    assert state["post_h_033_f_invalid_registry_blocks_success"] is True
    assert state["post_h_033_f_missing_registry_uses_fallback"] is True
    assert state["post_h_033_f_rule_source_reported"] is True
    assert state["post_h_033_f_catalog_version_reported"] is True
    assert state["post_h_033_f_critical_rules_disable_allowed"] is False
    assert state["post_h_033_f_network_used"] is False
    assert state["post_h_033_f_external_api_used"] is False
    assert state["post_h_033_f_remote_execution_enabled"] is False
    assert state["post_h_033_f_connector_write_enabled"] is False
    assert state["post_h_033_f_plugin_execution_enabled"] is False
    assert state["post_h_033_f_source_mutations"] is False


def test_post_h_034_a_project_state_adds_connector_write_adr() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")

    assert state.get("post_h_034_backlog_approved") is True
    assert state.get("post_h_034_current_micro_sprint") in {"POST-H-034-A", "POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE"}
    assert state.get("post_h_034_next_micro_sprint") in {"POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE"}
    assert state.get("post_h_034_a_decision_state") == "continue-blocked"
    assert state.get("post_h_034_a_connector_write_enabled") is False
    assert state.get("post_h_034_a_runtime_write_enabled") is False
    assert state.get("post_h_034_a_network_used") is False
    assert state.get("post_h_034_a_external_api_used") is False
    assert state.get("post_h_034_a_no_go_gates_preserved") is True
    assert state.get("post_h_034_a_requires_future_enablement_adr") is True
    assert "POST-H-034-A — Connector write ADR" in readme
    assert "POST-H-034-A — Operación de ADR connector write" in runbook
    assert "post-h-034-a" in changelog


def test_post_h_034_b_project_state_adds_plugin_execution_adr() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")

    assert state.get("post_h_034_current_micro_sprint") in {"POST-H-034-B", "POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE"}
    assert state.get("post_h_034_next_micro_sprint") in {"POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE"}
    assert state.get("post_h_034_a_closed") is True
    assert state.get("post_h_034_b_decision_state") == "continue-blocked"
    assert state.get("post_h_034_b_plugin_execution_enabled") is False
    assert state.get("post_h_034_b_runtime_execution_enabled") is False
    assert state.get("post_h_034_b_plugin_code_loading_enabled") is False
    assert state.get("post_h_034_b_dynamic_import_allowed") is False
    assert state.get("post_h_034_b_subprocess_allowed") is False
    assert state.get("post_h_034_b_no_go_gates_preserved") is True
    assert state.get("post_h_034_b_requires_future_enablement_adr") is True
    assert "POST-H-034-B — Plugin execution ADR" in readme
    assert "POST-H-034-B — Operación de ADR plugin execution" in runbook



def test_post_h_034_c_project_state_adds_remote_execution_adr3() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")

    assert state.get("post_h_034_current_micro_sprint") in {"POST-H-034-C", "POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE"}
    assert state.get("post_h_034_next_micro_sprint") in {"POST-H-034-D", "POST-H-034-E", "POST-H-034-CLOSURE"}
    assert state.get("post_h_034_b_closed") is True
    assert state.get("post_h_034_c_decision_state") == "continue-blocked"
    assert state.get("post_h_034_c_remote_execution_enabled") is False
    assert state.get("post_h_034_c_remote_runner_enabled") is False
    assert state.get("post_h_034_c_remote_transport_enabled") is False
    assert state.get("post_h_034_c_network_allowed") is False
    assert state.get("post_h_034_c_credentials_required") is False
    assert state.get("post_h_034_c_no_go_gates_preserved") is True
    assert state.get("post_h_034_c_requires_future_enablement_adr") is True
    assert "POST-H-034-C — Remote execution ADR-3" in readme
    assert "POST-H-034-C — Operación de ADR remote execution" in runbook


def test_post_h_034_d_project_state_adds_multiuser_auth_adr() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")

    assert state.get("post_h_034_current_micro_sprint") in {"POST-H-034-D", "POST-H-034-E"}
    assert state.get("post_h_034_next_micro_sprint") in {"POST-H-034-E", "POST-H-034-CLOSURE"}
    assert state.get("post_h_034_c_closed") is True
    assert state.get("post_h_034_d_decision_state") == "continue-blocked"
    assert state.get("post_h_034_d_multiuser_auth_enabled") is False
    assert state.get("post_h_034_d_production_multiuser_enabled") is False
    assert state.get("post_h_034_d_multiuser_runtime_enabled") is False
    assert state.get("post_h_034_d_iam_enterprise_enabled") is False
    assert state.get("post_h_034_d_session_management_enabled") is False
    assert state.get("post_h_034_d_tenancy_enabled") is False
    assert state.get("post_h_034_d_public_api_enabled") is False
    assert state.get("post_h_034_d_network_allowed") is False
    assert state.get("post_h_034_d_credentials_required") is False
    assert state.get("post_h_034_d_no_go_gates_preserved") is True
    assert state.get("post_h_034_d_requires_future_enablement_adr") is True
    assert state.get("production_multiuser") is False
    assert state.get("multiuser_auth_enabled") is False
    assert state.get("public_api_enabled") is False
    assert "POST-H-034-D — Multiuser/auth ADR" in readme
    assert "POST-H-034-D — Operación de ADR multiuser/auth" in runbook


def test_post_h_034_e_project_state_adds_enterprise_saas_boundary_adr() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    backlog = read("docs/backlogs/POST-H-034_sensitive_capabilities_adrs.md")

    assert state.get("post_h_034_current_micro_sprint") == "POST-H-034-E"
    assert state.get("post_h_034_next_micro_sprint") == "POST-H-034-CLOSURE"
    assert state.get("post_h_034_d_closed") is True
    assert state.get("post_h_034_e_decision_state") == "continue-blocked"
    assert state.get("post_h_034_e_enterprise_ready_claimed") is False
    assert state.get("post_h_034_e_enterprise_ready_enabled") is False
    assert state.get("post_h_034_e_enterprise_runtime_enabled") is False
    assert state.get("post_h_034_e_saas_ready_claimed") is False
    assert state.get("post_h_034_e_saas_runtime_enabled") is False
    assert state.get("post_h_034_e_control_plane_enabled") is False
    assert state.get("post_h_034_e_cloud_deployment_enabled") is False
    assert state.get("post_h_034_e_tenancy_enabled") is False
    assert state.get("post_h_034_e_tenant_isolation_implemented") is False
    assert state.get("post_h_034_e_public_api_enabled") is False
    assert state.get("post_h_034_e_compliance_certification_claim") is False
    assert state.get("post_h_034_e_external_audit_claimed") is False
    assert state.get("post_h_034_e_network_allowed") is False
    assert state.get("post_h_034_e_credentials_required") is False
    assert state.get("post_h_034_e_no_go_gates_preserved") is True
    assert state.get("post_h_034_e_requires_future_enablement_adr") is True
    assert state.get("enterprise_ready_claimed") is False
    assert state.get("saas_ready_claimed") is False
    assert state.get("compliance_certification_claim") is False
    assert state.get("control_plane_enabled") is False
    assert state.get("cloud_deployment_enabled") is False
    assert state.get("network_allowed") is False
    assert state.get("external_api_allowed") is False
    assert "POST-H-034-E — Enterprise/SaaS boundary ADR" in readme
    assert "POST-H-034-E — Operación de ADR Enterprise/SaaS boundary" in runbook
    assert 'implementation_status: "closed/full-regression-pass"' in backlog
