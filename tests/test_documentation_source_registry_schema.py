from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_documentation_source_registry_validates_against_schema() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="DocumentationSourceRegistry",
        instance=".devpilot/docs_governance/source_registry.json",
    )

    assert result.ok, result.to_dict()
    assert result.data["summary"]["valid"] is True
    assert result.data["summary"]["errors_total"] == 0


def test_documentation_governance_report_schema_is_registered_for_future_sprints() -> None:
    catalog = read_json("docs/schemas/schema_catalog.json")
    ids = {item["schema_id"] for item in catalog["schemas"]}

    assert "SCHEMA-DEVPL-DOCUMENTATION-SOURCE-REGISTRY-V1" in ids
    assert "SCHEMA-DEVPL-DOCUMENTATION-GOVERNANCE-REPORT-V1" in ids
    assert (ROOT / "docs/schemas/documentation_source_registry.schema.json").exists()
    assert (ROOT / "docs/schemas/documentation_governance_report.schema.json").exists()


def test_source_of_truth_entries_have_owner_status_and_tests() -> None:
    registry = read_json(".devpilot/docs_governance/source_registry.json")
    source_entries = [item for item in registry["documents"] if item["classification"] == "source-of-truth"]

    assert source_entries
    for item in source_entries:
        assert item["owner"]
        assert item["status_required"]
        assert item["required_tests"]
        for test_path in item["required_tests"]:
            assert (ROOT / test_path).exists(), test_path


def test_roadmap_markdown_and_json_pair_are_declared() -> None:
    registry = read_json(".devpilot/docs_governance/source_registry.json")
    by_path = {item["path"]: item for item in registry["documents"]}

    roadmap = by_path["docs/backlogs/post_h_prioritized_roadmap.md"]
    roadmap_json = by_path[".devpilot/evals/post_h_eval_001_prioritized_roadmap.json"]

    assert ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json" in roadmap["machine_readable_counterparts"]
    assert "docs/backlogs/post_h_prioritized_roadmap.md" in roadmap_json["human_readable_counterparts"]
    assert "milestones_match" in roadmap["sync_rules"]
    assert "decisions_match" in roadmap["sync_rules"]


def test_documentation_source_registry_paths_exist() -> None:
    registry = read_json(".devpilot/docs_governance/source_registry.json")
    referenced_paths: set[str] = set()
    for item in registry["documents"]:
        referenced_paths.add(item["path"])
        for key in (
            "machine_readable_counterparts",
            "human_readable_counterparts",
            "derived_documents",
            "required_tests",
            "related_adrs",
        ):
            referenced_paths.update(item.get(key, []))

    # Runtime evidence under outputs/ is intentionally generated on demand and
    # omitted from clean source ZIPs. Source registry path-existence checks must
    # therefore cover versioned engineering artifacts while allowing reproducible
    # runtime outputs to be absent before their corresponding commands run.
    missing = sorted(
        path
        for path in referenced_paths
        if not path.startswith("outputs/") and not (ROOT / path).exists()
    )
    assert missing == []
