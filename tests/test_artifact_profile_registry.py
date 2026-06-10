from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.validation import ArtifactProfileRegistry
from devpilot_core.validators.artifact_profiles import ARTIFACT_PROFILES, select_artifact_profile

ROOT = Path(__file__).resolve().parents[1]


def test_artifact_profile_registry_loads_json_profiles_equivalent_to_python_catalog() -> None:
    registry = ArtifactProfileRegistry(ROOT)
    profiles, generic, fallback_used = registry.load_profiles(allow_fallback=False)

    assert fallback_used is False
    assert generic.id == "generic-markdown"
    assert {profile.id for profile in profiles} == {profile.id for profile in ARTIFACT_PROFILES}
    assert len(profiles) == len(ARTIFACT_PROFILES)


def test_artifact_profile_registry_status_validates_schema_and_compatibility() -> None:
    result = ArtifactProfileRegistry(ROOT).status()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["profiles_total"] == len(ARTIFACT_PROFILES)
    assert result.data["summary"]["fallback_used"] is False
    assert result.data["summary"]["missing_from_json"] == []
    assert any(finding.id == "ARTIFACT_PROFILE_REGISTRY_PASS" for finding in result.findings)


def test_select_artifact_profile_uses_data_driven_registry_with_python_fallback_semantics() -> None:
    assert select_artifact_profile(ROOT / "docs/00_product/product_vision.md", root=ROOT).id == "product-vision"
    assert select_artifact_profile(ROOT / "docs/02_architecture/adrs/ADR-0010-schema-validation-dependency.md", root=ROOT).id == "adr"
    assert select_artifact_profile(ROOT / "docs/unknown_document.md", root=ROOT).id == "generic-markdown"


def test_artifact_profile_catalog_has_required_metadata() -> None:
    payload = json.loads((ROOT / "docs/validation/artifact_profiles.json").read_text(encoding="utf-8"))

    assert payload["contract"] == "ArtifactProfiles"
    assert payload["sprint"] == "FUNC-SPRINT-24"
    assert payload["generic_profile"]["id"] == "generic-markdown"
    assert all(item["description"] for item in payload["profiles"])
    assert all("required_headings" in item for item in payload["profiles"])
