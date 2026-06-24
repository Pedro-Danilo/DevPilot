from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.testing import TestContractRegistry

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_test_contract_registry_exists_and_is_semantically_valid() -> None:
    result = TestContractRegistry(ROOT).validate()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["contracts_total"] >= 20
    assert summary["historical_contracts_total"] == 78
    assert summary["global_state_contracts_total"] == 1
    assert "historical-sprint" in summary["scope_counts"]


def test_historical_sprint_contracts_do_not_own_mutable_global_state() -> None:
    registry = read_json(".devpilot/testing/test_contract_registry.json")
    historical = [item for item in registry["contracts"] if item["scope"] == "historical-sprint"]

    assert len(historical) == 78
    for item in historical:
        assert item["mutable_global_state_allowed"] is False
        assert item["global_state_source"] is None
        assert item["test_files"]


def test_test_contract_schema_catalog_registration() -> None:
    catalog = read_json("docs/schemas/schema_catalog.json")
    ids = {item["schema_id"] for item in catalog["schemas"]}

    assert "SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V1" in ids
    assert "SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V2" in ids
    assert "SCHEMA-DEVPL-PROJECT-STATE-V1" in ids
    assert "SCHEMA-DEVPL-POST-H-MANIFEST-V1" in ids
