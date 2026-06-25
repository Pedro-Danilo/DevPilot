from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PACKAGES = {
    "devpilot_core.cli",
    "devpilot_core.policy",
    "devpilot_core.schemas",
    "devpilot_core.agents",
    "devpilot_core.testing",
    "devpilot_core.quality",
    "devpilot_core.industrial",
}


def test_ownership_registry_contains_critical_initial_packages() -> None:
    from devpilot_core.architecture import load_ownership_registry

    payload = load_ownership_registry(ROOT)
    packages = {item["package"]: item for item in payload["packages"]}

    assert payload["id"] == "DEVPL-ARCHITECTURE-OWNERSHIP"
    assert payload["created_by"] == "POST-H-005-A"
    assert payload["dry_run"] is True
    assert payload["network_used"] is False
    assert REQUIRED_PACKAGES.issubset(packages)
    assert packages["devpilot_core.policy"]["criticality"] == "P0"
    assert packages["devpilot_core.policy"]["risk_level"] == "critical"
    assert "devpilot_core.interfaces" in packages["devpilot_core.policy"]["forbidden_dependencies"]
    assert "post-h-004-miasi-semantic-validator" in packages["devpilot_core.miasi"]["test_contracts"]


def test_ownership_registry_can_be_converted_to_model_entries() -> None:
    from devpilot_core.architecture import load_ownership_registry, ownership_entries_from_payload

    payload = load_ownership_registry(ROOT)
    entries = ownership_entries_from_payload(payload)

    assert len(entries) == len(payload["packages"])
    assert {entry.package for entry in entries}.issuperset(REQUIRED_PACKAGES)
    assert all(entry.owner for entry in entries)
    assert all(entry.preliminary is True for entry in entries)


def test_valid_architecture_map_fixture_carries_ownership_registry() -> None:
    fixture = json.loads((ROOT / "tests/fixtures/architecture_map/valid_minimal_architecture_map.json").read_text(encoding="utf-8"))
    ownership_packages = {item["package"] for item in fixture["ownership_registry"]}
    package_rows = {item["package"] for item in fixture["packages"]}

    assert REQUIRED_PACKAGES.issubset(ownership_packages)
    assert REQUIRED_PACKAGES.issubset(package_rows)
    assert fixture["summary"]["ownership_entries_total"] >= len(REQUIRED_PACKAGES)
    assert fixture["summary"]["unowned_packages_total"] == 0
