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

    assert state["current_phase"] == "POST-FASE-H"
    assert state["last_completed_sprint"] == "POST-H-030"
    assert state["last_functional_sprint"] == "FUNC-SPRINT-99"
    assert state["next_sprint"] == "POST-H-031"
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
    assert state.get("current_micro_sprint") == "POST-H-031-C"
    assert state.get("next_micro_sprint") == "POST-H-031-D"
    assert state.get("source_repo") == "repo_DevPilot_Local_263_POST_H_025.zip"
    assert state.get("current_repo") == "repo_DevPilot_Local_291_POST_H_031_C.zip"
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
    assert state["current_micro_sprint"] == "POST-H-031-C"
    assert state["next_micro_sprint"] == "POST-H-031-D"
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
    assert result.data["summary"]["last_completed_sprint"] == "POST-H-030"
    assert result.data["summary"]["next_sprint"] == "POST-H-031"
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

    assert state.get("post_h_031_status") == "active/implemented-initial-post-h-031-c"
    assert state.get("post_h_031_backlog_approved") is True
    assert state.get("post_h_031_current_micro_sprint") == "POST-H-031-C"
    assert state.get("post_h_031_next_micro_sprint") == "POST-H-031-D"
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
    assert 'implementation_status: "active/implemented-initial-post-h-031-c"' in backlog
    assert any("POST-H-031-A starts Observabilidad" in note for note in state["notes"])


def test_post_h_031_b_project_state_adds_operator_health_summary() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-031_observability_evidence_graph_operator.md")

    assert state.get("post_h_031_status") == "active/implemented-initial-post-h-031-c"
    assert state.get("post_h_031_current_micro_sprint") == "POST-H-031-C"
    assert state.get("post_h_031_next_micro_sprint") == "POST-H-031-D"
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
    assert 'implementation_status: "active/implemented-initial-post-h-031-c"' in backlog
    assert any("POST-H-031-B adds OperatorHealthSummary" in note for note in state["notes"])


def test_post_h_031_c_project_state_adds_gap_action_mapping() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    backlog = read("docs/backlogs/POST-H-031_observability_evidence_graph_operator.md")

    assert state.get("post_h_031_status") == "active/implemented-initial-post-h-031-c"
    assert state.get("post_h_031_current_micro_sprint") == "POST-H-031-C"
    assert state.get("post_h_031_next_micro_sprint") == "POST-H-031-D"
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
    assert 'implementation_status: "active/implemented-initial-post-h-031-c"' in backlog
    assert any("POST-H-031-C adds GapActionMap" in note for note in state["notes"])
