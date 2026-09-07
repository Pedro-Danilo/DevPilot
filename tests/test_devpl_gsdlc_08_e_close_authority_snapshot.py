from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / ".devpilot/testing/fixtures/gsdlc_08_e_close_authority_snapshot.json"


def test_gsdlc_08_e_close_authority_is_frozen_to_repo404_snapshot() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snapshot["authority_scope"] == "historical-freeze"
    assert snapshot["source_commit"] == "c0347423b78c67ed93f9eb4a2af39e0411b1d22f"
    assert snapshot["gsdlc_program_status_at_close"].startswith("closed/GSDLC-08/PASS")
    assert snapshot["gsdlc_current_canonical_repo_at_close"].startswith("repo_DevPilot_Local_404_")
