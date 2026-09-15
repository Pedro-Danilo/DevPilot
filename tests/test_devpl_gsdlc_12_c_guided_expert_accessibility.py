from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def j(rel: str):
    return json.loads(read(rel))


def test_12_c_mode_is_ux_only_and_authority_parity_is_explicit() -> None:
    source = read("ui/web/src/ux/experienceMode.ts")
    for marker in [
        "authority: 'server-side-unchanged'",
        "rbac: 'unchanged'",
        "approvals: 'unchanged'",
        "tool_permissions: 'unchanged'",
        "model_permissions: 'unchanged'",
        "mutability: 'unchanged'",
        "browser_storage_role: 'ux-preference-only'",
    ]:
        assert marker in source
    assert "localStorage" in source
    assert "fetch(" not in source and "request(" not in source


def test_12_c_guided_progressive_disclosure_keeps_recovery_and_conflict_visible() -> None:
    main = read("ui/web/src/main.ts")
    navigation = read("ui/web/src/ux/navigationPresentation.ts") if (ROOT / "ui/web/src/ux/navigationPresentation.ts").exists() else ""
    assert ("primary-nav__advanced" in main and "Más herramientas" in main) or ("primary-nav__group" in main and "Understand & Plan" in navigation and "Diagnostics" in navigation)
    assert "guidedNextAction" in main
    for critical in ["/project/status", "/recovery", "/reconciliation", "/help"]:
        assert critical in main
    assert "blocker" in main.lower()


def test_12_c_expert_diagnostics_add_information_not_actions() -> None:
    recovery = read("ui/web/src/pages/RecoveryView.ts")
    reconciliation = read("ui/web/src/pages/ConflictResolutionView.ts")
    ai = read("ui/web/src/components/AIControlCenterView.ts")
    for source in [recovery, reconciliation]:
        assert "expert-only" in source
    assert "Guided" in ai and "Expert" in ai
    assert "autoridad" in ai.lower() or "authority" in ai.lower()
    policy = j(".devpilot/interfaces/ui_capability_registry.json")
    assert policy["summary"]["gsdlc_12_c_mode_policy_parity"] is True


def test_12_c_accessibility_contract_has_keyboard_focus_live_and_responsive_support() -> None:
    main = read("ui/web/src/main.ts")
    styles = read("ui/web/src/styles.css")
    contextual = read("ui/web/src/components/ContextualHelp.ts")
    recovery = read("ui/web/src/pages/RecoveryView.ts")
    reconciliation = read("ui/web/src/pages/ConflictResolutionView.ts")
    assert "skip-link" in main or ".skip-link" in styles
    assert ":focus-visible" in styles
    assert "prefers-reduced-motion" in styles
    assert "queueMicrotask" in main and ".focus(" in main
    assert "setAttribute('role', 'alert')" in contextual
    assert "setAttribute('aria-live', 'assertive')" in contextual
    assert "aria-label" in recovery and "aria-label" in reconciliation
    assert "@media" in styles and "900px" in styles and "560px" in styles


def test_12_c_help_is_global_read_only_registered_and_safe() -> None:
    main = read("ui/web/src/main.ts")
    help_source = read("ui/web/src/pages/HelpSystemView.ts")
    ui = j(".devpilot/interfaces/ui_route_contract_registry.json")
    caps = j(".devpilot/interfaces/ui_capability_registry.json")
    assert "path: '/help'" in main and "routeId: 'ui.help'" in main
    route = next(r for r in ui["routes"] if r["route_id"] == "ui.help")
    assert route["allowed_api_routes"] == ["api.auth.session"]
    assert route["shows_mutation_controls"] is False
    assert route["remote_execution_allowed"] is False
    cap = next(r for r in caps["ui_routes"] if r["route_id"] == "ui.help")
    assert cap["allowed_api_route_ids"] == ["api.auth.session"] and cap["shows_mutation_controls"] is False
    assert len(ui["routes"]) == ui["summary"]["routes_total"] == 22
    assert len(caps["ui_routes"]) == caps["summary"]["ui_routes_total"] == caps["summary"]["ui_routes_mapped_total"] == 22
    for forbidden in ["sk-", "Bearer ", "api_key="]:
        assert forbidden not in help_source


def test_12_c_recovery_and_reconciliation_are_available_in_both_modes() -> None:
    styles = read("ui/web/src/styles.css")
    main = read("ui/web/src/main.ts")
    assert "[data-experience-mode=\"guided\"] .expert-only" in styles or "data-experience-mode='guided'" in styles or "data-experience-mode=\"guided\"" in styles
    assert "'/recovery'" in main and "'/reconciliation'" in main
    # Mode selector changes the root presentation attribute, not the route/capability authority.
    control = read("ui/web/src/components/ExperienceModeControl.ts")
    assert "writeExperienceMode" in control and "aria-pressed" in control


def test_12_c_state_is_bound_to_repo427_and_full_budget_unconsumed() -> None:
    project = j(".devpilot/project_state.json")
    source = j(".devpilot/docs_governance/source_registry.json")
    expected_repo = "repo_DevPilot_Local_427_DEVPL_GSDLC_12_B_BRANCH_EXTERNAL_EDIT_RECONCILIATION_WINDOWS_VALIDATED_CANDIDATE.zip"
    expected_commit = "d65db36f3f430f2e96357a931a7da14a8ee8a9e5"
    expected_sha = "764fbf23439091a869519c1ccd3963c5e733499ee91523b8b60f47862671d370"
    for doc in [project, source]:
        assert doc["gsdlc_12_b_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
        assert doc["gsdlc_12_c_execution_source_repo"] == expected_repo
        assert doc["gsdlc_12_c_execution_source_commit"] == expected_commit
        assert doc["gsdlc_12_c_execution_source_sha256"] == expected_sha
        assert doc["gsdlc_12_c_full_regression_runs"] == 0
    assert project["gsdlc_12_full_regression_budget_total"] == 1


def test_12_c_evidence_contracts_describe_first_version_limits_and_browser_pending() -> None:
    a11y = j("docs/audits/DEVPL_GSDLC_12_C_A11Y_REPORT.json")
    parity = j("docs/audits/DEVPL_GSDLC_12_C_MODE_POLICY_PARITY.json")
    usability = read("docs/audits/DEVPL_GSDLC_12_C_USABILITY_SESSION_REPORT.md")
    assert str(a11y["status"]).startswith("PASS/")
    assert a11y["browser_manual_status"] == "PASS/REAL-BROWSER"
    assert a11y["first_version_wcag_oriented"] is True
    assert parity["status"] == "PASS/WINDOWS-REAL-BROWSER"
    assert parity["authority_equivalent"] is True
    assert parity["guided"]["server_authority"] == parity["expert"]["server_authority"] == "UNCHANGED"
    assert "PASS/REAL-BROWSER" in usability
