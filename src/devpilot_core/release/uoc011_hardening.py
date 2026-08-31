from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devpilot_core.interfaces.api.security import SECURITY_HEADERS

REQUIRED_UI_ROUTES = {
    "ui.dashboard", "ui.workspace-documents", "ui.reports", "ui.traces", "ui.approvals",
    "ui.jobs", "ui.quality", "ui.ai", "ui.settings",
}
REQUIRED_STATES = {
    "loading", "empty", "ready", "warn", "block", "error", "api_down", "unauthorized",
    "forbidden", "timeout", "cancelled", "stale_data",
}


def _load(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def evaluate_uoc011_hardening(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    checks: list[dict[str, Any]] = []

    def record(check_id: str, ok: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if ok else "BLOCK", "detail": detail})

    profile = _load(root, ".devpilot/interfaces/uoc011_operational_hardening_profile.json")
    matrix = _load(root, ".devpilot/interfaces/uoc011_browser_state_matrix.json")
    routes = _load(root, ".devpilot/interfaces/ui_route_contract_registry.json")
    flags = _load(root, ".devpilot/interfaces/ui_operational_console_flags.json")
    state = _load(root, ".devpilot/project_state.json")
    package = _load(root, "ui/web/package.json")
    capabilities = _load(root, ".devpilot/interfaces/ui_capability_registry.json")
    governed_capabilities = _load(root, ".devpilot/interfaces/governed_job_capability_registry.json")
    manifest = _load(root, "docs/post_h_eval_002_uoc_011_manifest.json")

    route_items = {item["route_id"]: item for item in routes.get("routes", [])}
    record("ui-route-coverage", REQUIRED_UI_ROUTES <= set(route_items), "All nine operational UI routes are governed.")
    state_ok = True
    for route_id in REQUIRED_UI_ROUTES:
        contract = (route_items.get(route_id) or {}).get("state_contract") or {}
        if not all(contract.get(key) is True for key in REQUIRED_STATES):
            state_ok = False
            break
    record("ui-state-matrix-contract", state_ok, "Each operational route declares the twelve UOC-011 product states.")

    matrix_routes = {item.get("route_id") for item in matrix.get("routes", [])}
    matrix_states = set(matrix.get("required_states", []))
    runtime_matrix_ok = matrix_routes == REQUIRED_UI_ROUTES and matrix_states == REQUIRED_STATES and matrix.get("summary", {}).get("cases_total") == 108 and matrix.get("summary", {}).get("runtime_execution_required") is True and matrix.get("summary", {}).get("contract_only_is_sufficient") is False
    runtime_matrix_ok = runtime_matrix_ok and all((item.get("evidence") == "browser-runtime-controlled-fixture" and item.get("runtime_required") is True) for route in matrix.get("routes", []) for item in (route.get("states") or {}).values())
    record("browser-state-matrix", runtime_matrix_ok, "Browser matrix is 9 routes x 12 states = 108 runtime-required browser cases; contract-only evidence is insufficient.")

    required_headers = set(profile["security"]["required_response_headers"])
    record("api-security-headers", required_headers <= set(SECURITY_HEADERS), "API header set includes CSP and the UOC-011 required security headers.")

    client_source = (root / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    record("token-session-lifecycle", all(marker in client_source for marker in ("TOKEN_SESSION_TTL_MS", "TOKEN_STORED_AT_KEY", "clearExpiredStoredToken")), "Browser token session has bounded TTL and explicit expiry cleanup.")

    vite_source = (root / "ui/web/vite.config.ts").read_text(encoding="utf-8")
    record("ui-csp-security-headers", "Content-Security-Policy" in vite_source and "frame-ancestors 'none'" in vite_source, "Vite dev/preview expose local CSP/security headers.")

    styles = (root / "ui/web/src/styles.css").read_text(encoding="utf-8")
    record("wcag-keyboard-focus", ":focus-visible" in styles and ".skip-link" in styles and "prefers-reduced-motion" in styles, "Keyboard focus, skip link and reduced-motion contracts are present.")

    scripts = package.get("scripts", {})
    record("ui-hardening-smokes", all(name in scripts for name in ("test:accessibility", "test:performance", "test:state-matrix", "test:browser-runtime-matrix-contract")), "Accessibility, performance, state-matrix and runtime-matrix contract smokes are registered.")

    safety = flags.get("safety", {})
    record("no-go-preserved", all(safety.get(key) is False for key in ("arbitrary_shell_allowed", "remote_execution_enabled", "connector_write_enabled", "plugin_execution_enabled")) and safety.get("uoc_010_external_api_enabled") is False, "No-go invariants remain engaged.")

    release_paths = [
        "docs/05_operations/install_guide.md",
        "docs/05_operations/backup_restore_upgrade.md",
        "src/devpilot_core/release/backup.py",
        "src/devpilot_core/release/upgrade_rollback_dry_run.py",
        "docs/05_operations/uoc_011_release_operator_runbook.md",
        "docs/release/uoc_011_release_notes.md",
    ]
    record("release-recovery-assets", all((root / path).is_file() for path in release_paths), "Install, backup/restore, upgrade/rollback, runbook and release notes are present.")

    record("project-lifecycle", state.get("uoc_011_authorized") is True and state.get("uoc_011_status") in {"implemented-initial/pending-windows-closure", "closed/PASS"}, "UOC-011 lifecycle is explicit without advancing pilot micro-sprint pointers.")
    parity_actual: dict[str, int] = {}
    for capability in capabilities.get("capabilities", []):
        key = str(capability.get("parity_status")); parity_actual[key] = parity_actual.get(key, 0) + 1
    capability_summary = capabilities.get("summary", {})
    governed_summary = governed_capabilities.get("summary", {})
    historical_total = int(governed_summary.get("uoc_011_capabilities_total_at_close", 0))
    current_total = len(capabilities.get("capabilities", []))
    parity_ok = (
        historical_total == 193
        and current_total >= historical_total
        and sum(parity_actual.values()) == current_total
        and capability_summary.get("cli_commands_total") == current_total
        and capability_summary.get("cli_commands_classified_total") == current_total
        and capability_summary.get("parity_status_counts", {}) == parity_actual
        and capability_summary.get("uoc_007_governed_job_capabilities_total") == current_total
        and capability_summary.get("uoc_007_governed_job_capabilities_total_at_close") == historical_total
        and capability_summary.get("uoc_011_authorized") is True
    )
    record(
        "capability-parity-derived",
        parity_ok,
        f"UOC-011 historical capability floor remains {historical_total}; current parity summary is derived from all {current_total} active registry entries.",
    )
    record("uoc011-historical-closure-recorded", manifest.get("closure_commit") == "4ce3c2f851bc572a7b014b5e7aed423f15e3e30c" and manifest.get("status") == "closed/PASS", "UOC-011 manifest records its authoritative historical closure commit instead of null.")

    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "BLOCK"
    return {
        "schema_id": "SCHEMA-DEVPL-UOC011-HARDENING-REPORT-V1",
        "status": status,
        "checks": checks,
        "summary": {
            "checks_total": len(checks),
            "checks_passed": sum(1 for item in checks if item["status"] == "PASS"),
            "routes_total": len(REQUIRED_UI_ROUTES),
            "browser_matrix_cases_total": 108,
            "preliminary": True,
        },
        "safety": {
            "local_first": True,
            "network_used": False,
            "external_api_used": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "source_mutations_performed": False,
        },
        "limitations": profile.get("limitations", []),
    }
