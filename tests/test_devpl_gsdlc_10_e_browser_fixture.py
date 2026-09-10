from __future__ import annotations

import os
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _fixture_root() -> Path:
    configured = str(os.environ.get("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT") or "").strip()
    return Path(configured).resolve() if configured else ROOT


def test_gsdlc10e_browser_story_value_is_ready() -> None:
    fixture = _fixture_root() / "tests" / "fixtures" / "gsdlc10e_story_value.py"
    assert fixture.is_file(), f"controlled GSDLC-10-E fixture missing: {fixture}"
    value = runpy.run_path(str(fixture))["CYCLE_VALUE"]
    assert value == "ready", f"controlled GSDLC-10-E story failure: expected ready, got {value}"
