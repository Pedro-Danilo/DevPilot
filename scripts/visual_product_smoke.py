#!/usr/bin/env python3
"""Visual Product Quality Gate for DevPilot Fase F closure.

FUNC-SPRINT-73 keeps this gate dependency-light and local-first. The default
mode is dry-run/read-only: it inspects contracts, UI metadata and release
artifacts without starting servers, opening browsers, calling external APIs or
writing runtime outputs.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GateCheck:
    id: str
    ok: bool
    message: str
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {"id": self.id, "ok": self.ok, "message": self.message}
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


EXPECTED_OPENAPI_PATHS = {
    "/api/v1/workspace/status",
    "/api/v1/application/contract",
    "/api/v1/validation/readiness",
    "/api/v1/miasi/status",
    "/api/v1/standards/status",
    "/api/v1/reports",
    "/api/v1/reports/{report_id}",
    "/api/v1/traces",
    "/api/v1/traces/{trace_id}",
    "/api/v1/metrics/summary",
    "/api/v1/approvals",
    "/api/v1/approvals/request",
    "/api/v1/actions/dry-run",
    "/api/v1/settings/workspace",
    "/api/v1/settings/providers",
    "/api/v1/settings/policy",
    "/api/v1/settings/providers/plan",
}

FORBIDDEN_OPENAPI_FRAGMENTS = {
    "/api/v1/patch/apply",
    "/api/v1/rollback/execute",
    "/api/v1/refactor/execute",
    "/api/v1/git/push",
    "/api/v1/deploy",
}

REQUIRED_UI_FLAGS = {
    "apiOnly": True,
    "requiresExternalApi": False,
    "coreImportsAllowed": False,
    "reportViewer": True,
    "traceViewer": True,
    "approvalCenter": True,
    "dryRunActionLauncher": True,
    "criticalActionsBlockedFromUi": True,
    "settingsUi": True,
    "settingsReadOnly": True,
    "providerEditorPlanOnly": True,
    "secretsRedacted": True,
    "phaseFClosed": True,
    "desktopDeferred": True,
    "webRealEvolutionPlanned": True,
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _check(condition: bool, check_id: str, ok_msg: str, fail_msg: str, metadata: dict[str, Any] | None = None) -> GateCheck:
    return GateCheck(check_id, bool(condition), ok_msg if condition else fail_msg, metadata)


def _load_app_contract(root: Path) -> dict[str, Any]:
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from devpilot_core.application import ApplicationService  # noqa: PLC0415

    result = ApplicationService(root).application_contract().to_dict()
    return result["data"]


def run_gate(root: Path, *, run_npm: bool = False) -> dict[str, Any]:
    checks: list[GateCheck] = []
    root = root.resolve()

    required_files = [
        "README.md",
        "docs/devpilot_backlog_fase_F_producto_visual.md",
        "docs/functional_backlog_after_precode.md",
        "docs/05_operations/runbook.md",
        "docs/07_interfaces/openapi_v1.json",
        "docs/07_interfaces/internal_application_contract.md",
        "docs/audits/phase_f_visual_product_closure_report.md",
        "docs/release/release_manifest_visual_mvp.json",
        "docs/functional_sprint_73_manifest.json",
        "ui/web/package.json",
        "ui/web/scripts/smoke-test.mjs",
    ]
    missing = [path for path in required_files if not (root / path).exists()]
    checks.append(_check(not missing, "VISUAL_FILES_EXIST", "Required visual product files exist.", "Required visual product files are missing.", {"missing": missing}))

    readme = _read_text(root / "README.md")
    backlog = _read_text(root / "docs/devpilot_backlog_fase_F_producto_visual.md")
    functional_backlog = _read_text(root / "docs/functional_backlog_after_precode.md")
    checks.append(_check("Último hito: `FUNC-SPRINT-73" in readme and "Siguiente hito: `FUNC-SPRINT-74" in readme, "README_GLOBAL_STATE", "README global state points to Sprint 73 closure and Sprint 74 next.", "README global state is not synchronized."))
    checks.append(_check("phase_f_status: \"closed_visual_mvp_web_first\"" in backlog, "PHASE_F_CLOSED_IN_BACKLOG", "Fase F backlog declares closed visual MVP web-first status.", "Fase F backlog does not declare closed visual MVP status."))
    checks.append(_check("next_sprint: \"FUNC-SPRINT-74\"" in functional_backlog, "FUNCTIONAL_BACKLOG_NEXT", "Functional backlog points to FUNC-SPRINT-74.", "Functional backlog next sprint is not FUNC-SPRINT-74."))

    openapi = _read_json(root / "docs/07_interfaces/openapi_v1.json")
    paths = set(openapi.get("paths", {}))
    missing_paths = sorted(EXPECTED_OPENAPI_PATHS - paths)
    forbidden_paths = sorted(path for path in paths for fragment in FORBIDDEN_OPENAPI_FRAGMENTS if fragment in path)
    x_devpilot = openapi.get("x-devpilot", {})
    checks.append(_check(not missing_paths, "OPENAPI_EXPECTED_PATHS", "OpenAPI contains the expected visual MVP API paths.", "OpenAPI is missing required visual MVP API paths.", {"missing": missing_paths}))
    checks.append(_check(not forbidden_paths, "OPENAPI_NO_DANGEROUS_PATHS", "OpenAPI does not expose dangerous execute/write routes.", "OpenAPI exposes forbidden route fragments.", {"forbidden": forbidden_paths}))
    checks.append(_check(x_devpilot.get("sprint") == "FUNC-SPRINT-73" and x_devpilot.get("desktop_deferred") is True, "OPENAPI_SPRINT73_METADATA", "OpenAPI metadata is synchronized with Sprint 73 closure.", "OpenAPI metadata is not synchronized with Sprint 73 closure.", x_devpilot))

    release = _read_json(root / "docs/release/release_manifest_visual_mvp.json")
    release_summary = release.get("summary", {})
    checks.append(_check(release.get("sprint") == "FUNC-SPRINT-73" and release_summary.get("phase_f_closed") is True, "RELEASE_MANIFEST_PHASE_F", "Visual MVP release manifest closes Fase F.", "Visual MVP release manifest is not synchronized with Fase F closure.", release_summary))
    checks.append(_check(release_summary.get("web_real_evolution_planned") is True and release_summary.get("desktop_deferred") is True, "EVOLUTION_DECISION", "Web real evolution is planned and Desktop remains deferred.", "Evolution decision is missing or unsafe.", release_summary))

    package_json = _read_json(root / "ui/web/package.json")
    devpilot = package_json.get("devpilot", {})
    flag_mismatches = {key: {"expected": expected, "actual": devpilot.get(key)} for key, expected in REQUIRED_UI_FLAGS.items() if devpilot.get(key) is not expected}
    checks.append(_check(package_json.get("version") == "0.5.0-sprint-73" and devpilot.get("sprint") == "FUNC-SPRINT-73", "UI_PACKAGE_SPRINT73", "Web UI package metadata is synchronized with Sprint 73.", "Web UI package metadata is not synchronized with Sprint 73.", {"version": package_json.get("version"), "sprint": devpilot.get("sprint")}))
    checks.append(_check(not flag_mismatches, "UI_SAFETY_FLAGS", "Web UI safety flags are set for API-only local MVP.", "Web UI safety flags are missing or unsafe.", {"mismatches": flag_mismatches}))

    ui_sources = [
        root / "ui/web/src/api/client.ts",
        root / "ui/web/src/pages/Dashboard.ts",
        root / "ui/web/src/pages/ReportTraceView.ts",
        root / "ui/web/src/pages/ApprovalCenterView.ts",
        root / "ui/web/src/pages/SettingsView.ts",
    ]
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in ui_sources if path.exists())
    unsafe_markers = [marker for marker in ["devpilot_core", "child_process", "outputs/", ".devpilot/", "/patch/apply", "/rollback/execute", "/git/push", "/deploy"] if marker in source_text]
    checks.append(_check(not unsafe_markers, "UI_NO_CORE_OR_FILESYSTEM", "Web UI does not import core, spawn processes or read local runtime files.", "Web UI contains unsafe markers.", {"unsafe_markers": unsafe_markers}))

    app_contract = _load_app_contract(root)
    app_summary = app_contract.get("summary", {})
    checks.append(_check(app_summary.get("phase_f_closed") is True and app_summary.get("visual_product_mvp_release") is True, "APP_CONTRACT_PHASE_F", "ApplicationService contract declares Fase F visual MVP closure.", "ApplicationService contract does not declare visual MVP closure.", app_summary))

    agentops = None
    try:
        src = root / "src"
        if str(src) not in sys.path:
            sys.path.insert(0, str(src))
        from devpilot_core.application import ApplicationService  # noqa: PLC0415
        agentops_result = ApplicationService(root).observability.agentops_status(limit=20).to_dict()
        agentops = agentops_result.get("data", {}).get("summary", {})
        checks.append(_check(agentops_result.get("ok") is True, "AGENTOPS_STATUS", "AgentOps status is available for the visual product.", "AgentOps status did not pass.", agentops))
    except Exception as exc:  # pragma: no cover - defensive smoke diagnostic
        checks.append(GateCheck("AGENTOPS_STATUS", False, f"AgentOps status raised {type(exc).__name__}: {exc}"))

    checks.append(_check(not (root / "desktop").exists(), "DESKTOP_DEFERRED_NO_SHELL", "Desktop implementation remains deferred; no desktop shell exists in Fase F.", "Desktop shell exists despite Fase F deferral."))
    checks.append(_check(not (root / "ui/web/node_modules").exists(), "NO_NODE_MODULES_IN_SOURCE", "ui/web/node_modules is not present in source package.", "ui/web/node_modules is present in source package."))
    checks.append(_check(not (root / "package-lock.json").exists(), "NO_ROOT_PACKAGE_LOCK", "No accidental root package-lock.json exists.", "Unexpected root package-lock.json exists."))

    npm_result: dict[str, Any] | None = None
    if run_npm:
        npm = shutil.which("npm.cmd") or shutil.which("npm.exe") or shutil.which("npm")
        if npm is None:
            checks.append(GateCheck("NPM_TEST", False, "npm was requested but is not available in PATH."))
        else:
            completed = subprocess.run([npm, "test"], cwd=root / "ui/web", text=True, capture_output=True, check=False)
            npm_result = {"returncode": completed.returncode, "stdout_tail": completed.stdout[-500:], "stderr_tail": completed.stderr[-500:]}
            checks.append(_check(completed.returncode == 0 and "DEVPL WEB UI SMOKE TEST: PASS" in completed.stdout, "NPM_TEST", "npm smoke test passed.", "npm smoke test failed.", npm_result))

    ok = all(check.ok for check in checks)
    payload = {
        "command": "visual product smoke",
        "ok": ok,
        "exit_code": 0 if ok else 2,
        "message": "Visual product smoke gate passed." if ok else "Visual product smoke gate failed.",
        "data": {
            "summary": {
                "phase": "Fase F — Producto visual",
                "sprint": "FUNC-SPRINT-73",
                "phase_f_closed": ok,
                "web_ui_local_mvp": True,
                "web_real_evolution_planned": True,
                "desktop_deferred": True,
                "checks_total": len(checks),
                "checks_passed": sum(1 for check in checks if check.ok),
                "checks_failed": sum(1 for check in checks if not check.ok),
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "npm_executed": run_npm,
            },
            "checks": [check.to_dict() for check in checks],
            "agentops_summary": agentops,
            "npm_result": npm_result,
        },
        "findings": [
            {
                "id": "VISUAL_PRODUCT_SMOKE_PASS" if ok else "VISUAL_PRODUCT_SMOKE_BLOCK",
                "message": "Visual Product Quality Gate passed." if ok else "Visual Product Quality Gate failed.",
                "severity": "info" if ok else "block",
            }
        ],
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the DevPilot Visual Product Quality Gate.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--dry-run", action="store_true", help="Read-only mode. Kept explicit for Sprint 73 commands.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--run-npm", action="store_true", help="Also execute npm test under ui/web when npm is available.")
    args = parser.parse_args(argv)

    payload = run_gate(Path(args.root), run_npm=args.run_npm)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        status = "PASS" if payload["ok"] else "BLOCK"
        print(f"DEVPL VISUAL PRODUCT SMOKE: {status}")
        for check in payload["data"]["checks"]:
            marker = "PASS" if check["ok"] else "BLOCK"
            print(f"- {marker}: {check['id']} — {check['message']}")
    return int(payload["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
