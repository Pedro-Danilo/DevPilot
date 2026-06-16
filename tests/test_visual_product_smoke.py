from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_visual_product_smoke_gate_passes_in_dry_run_json() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/visual_product_smoke.py", "--dry-run", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    summary = payload["data"]["summary"]
    assert summary["phase_f_closed"] is True
    assert summary["web_ui_local_mvp"] is True
    assert summary["web_real_evolution_planned"] is True
    assert summary["desktop_deferred"] is True
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    check_ids = {check["id"] for check in payload["data"]["checks"]}
    assert "OPENAPI_EXPECTED_PATHS" in check_ids
    assert "UI_SAFETY_FLAGS" in check_ids
    assert "APP_CONTRACT_PHASE_F" in check_ids


def test_visual_product_smoke_script_is_local_first_and_no_dangerous_fragments() -> None:
    script = (ROOT / "scripts" / "visual_product_smoke.py").read_text(encoding="utf-8")
    assert "external_api_used" in script
    assert "mutations_performed" in script
    assert "0.0.0.0" not in script
    assert "patch/apply" in script
    assert "rollback/execute" in script
