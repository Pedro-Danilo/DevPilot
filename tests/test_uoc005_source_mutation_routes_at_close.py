from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_uoc005_source_mutation_routes_remain_two_at_close() -> None:
    payload = json.loads((ROOT / ".devpilot/testing/fixtures/uoc005_source_mutation_routes_at_close.json").read_text(encoding="utf-8"))
    assert set(payload["source_mutation_route_ids"]) == {
        "api.workspace.edit-plans.apply",
        "api.workspace.edit-executions.rollback",
    }
