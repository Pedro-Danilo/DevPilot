from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from devpl_gsdlc_04_b_fixture_state import inspect_fixture

PROBE_ID = "DEVPL-GSDLC-04-B-FIXTURE-BINDING-PROBE"
VERSION = "1.0.9"
DEFAULT_FIXTURE = r"D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_B_BROWSER"


def _enable_windows_ansi() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def verdict(status: str, message: str) -> None:
    _enable_windows_ansi()
    color = "\x1b[92m" if status == "PASS" else "\x1b[91m"
    print(f"{color}{status} — {message}\x1b[0m", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only 04-B PathGuard/UI workspace binding probe.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--browser-fixture-root", default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    fixture = Path(args.browser_fixture_root).resolve()
    try:
        if not repo.is_dir():
            raise RuntimeError(f"Repo root no existe: {repo}")
        if not fixture.is_dir():
            raise RuntimeError(f"Fixture no existe: {fixture}")
        if "inventory-sales-local" in str(fixture).lower() or "devpilot_workspaces" in str(fixture).lower():
            raise RuntimeError("El probe 04-B no puede usar el workspace piloto real.")
        required = [fixture / "docs" / "manual_authoring.md", fixture / "docs" / "manual_authoring.json"]
        missing = [str(item) for item in required if not item.is_file()]
        if missing:
            raise RuntimeError(f"Fixture incompleto: {missing}")
        fixture_state = inspect_fixture(fixture, phase_policy="pre-open")
        if not fixture_state["git_clean"]:
            raise RuntimeError(f"Fixture Git debe estar limpio antes de Project Entry: {fixture_state['git_status_entries']}")

        os.environ["DEVPILOT_ALLOWED_WORKSPACE_ROOTS"] = str(fixture)
        os.environ["DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT"] = str(fixture)
        os.environ.pop("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", None)

        from devpilot_core.application.ui_workspace_context import UiWorkspaceContextResolver
        from devpilot_core.workspace.project_entry_contracts import ProjectEntryContractService
        from devpilot_core.workspace.project_entry_dry_run import ProjectEntryDryRunService

        intake: dict[str, Any] = {
            "schema_id": "SCHEMA-DEVPL-GSDLC-03-A-PROJECT-INTAKE-V1",
            "schema_version": "1.0",
            "project_id": "gsdlc04b-browser",
            "project_name": "GSDLC 04-B browser fixture",
            "project_type": "agent-assisted-sdlc",
            "entry_mode": "OPEN_EXISTING",
            "target_root": str(fixture),
            "stack": {"frontend": "react-typescript", "backend": "fastapi-python", "database": "sqlite"},
            "standards": ["MIPSoftware", "MIASI"],
            "provider": {"mode": "none", "provider_id": None},
            "restrictions": {
                "arbitrary_shell_allowed": False,
                "silent_network_allowed": False,
                "remote_git_execute_allowed": False,
            },
        }
        contract = ProjectEntryContractService(repo).validate_intake(intake)
        dry = ProjectEntryDryRunService(repo).dry_run(intake=intake)
        context = UiWorkspaceContextResolver(repo).resolve()
        if not contract.ok:
            raise RuntimeError(f"ProjectIntake/PathGuard BLOCK: {contract.to_dict()}")
        if not dry.ok:
            raise RuntimeError(f"Project Entry dry-run precheck BLOCK: {dry.to_dict()}")
        if not context.valid or context.active_workspace_root != fixture:
            raise RuntimeError(f"UI workspace context no resolvió el fixture exacto: {context.summary()}")
        payload = {
            "status": "PASS",
            "probe_id": PROBE_ID,
            "version": VERSION,
            "fixture": str(fixture),
            "project_intake_ok": True,
            "dry_run_ok": True,
            "dry_run_writes_performed": bool(dry.data.get("writes_performed", False)),
            "dry_run_network_used": bool(dry.data.get("network_used", False)),
            "ui_workspace_context": context.summary(),
            "fixture_git_clean": True,
            "fixture_git_head": fixture_state["head"],
            "fixture_git_status_entries": fixture_state["git_status_entries"],
            "pilot_workspace_accessed": False,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        verdict("PASS", "fixture binding + Project Entry dry-run precheck completado")
        return 0
    except Exception as exc:
        payload = {"status": "BLOCK", "probe_id": PROBE_ID, "version": VERSION, "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        verdict("BLOCK", str(exc).splitlines()[0])
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
