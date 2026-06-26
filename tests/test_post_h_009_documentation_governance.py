from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.docs_governance import load_documentation_source_registry

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read(path))


def test_post_h_009_backlog_is_approved_and_source_registry_is_documented() -> None:
    backlog = read("docs/backlogs/POST-H-009_documentation_governance.md")
    canonical_doc = read("docs/POST-H-009_documentation_governance.md")
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")
    manifest = read_json("docs/post_h_009_a_manifest.json")

    assert 'status: "approved"' in backlog
    assert 'implementation_status: "in-progress"' in backlog
    assert "## 14. Avance de implementación — POST-H-009-A" in backlog
    assert "## 15. Avance de implementación — POST-H-009-B" in backlog
    assert "## 16. Avance de implementación — POST-H-009-C" in backlog
    assert canonical_doc == backlog
    assert "POST-H-009-A — Documentation governance" in readme
    assert "POST-H-009-B — Documentation governance" in readme
    assert "POST-H-009-C — Documentation governance" in readme
    assert "POST-H-009-A — Source registry y schema" in runbook
    assert "POST-H-009-B — Validator de frontmatter/status/ownership" in runbook
    assert "POST-H-009-C — Sync validator Markdown ↔ JSON" in runbook
    assert "post-h-009-a" in changelog
    assert "post-h-009-b" in changelog
    assert "post-h-009-c" in changelog
    assert manifest["id"] == "POST-H-009-A"
    assert manifest["post_h_id"] == "POST-H-009"
    assert manifest["status"] == "implemented-initial"
    assert manifest["next_sprint"] == "POST-H-009"


def test_post_h_009_a_registry_model_loads_expected_canonical_sources() -> None:
    registry = load_documentation_source_registry(ROOT)
    by_path = registry.by_path()

    assert registry.registry_id == "devpilot-documentation-source-registry"
    assert registry.schema_id == "SCHEMA-DEVPL-DOCUMENTATION-SOURCE-REGISTRY-V1"
    assert registry.status == "implemented-initial"
    assert "docs/backlogs/post_h_prioritized_roadmap.md" in by_path
    assert ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json" in by_path
    assert "docs/backlogs/POST-H-009_documentation_governance.md" in by_path
    assert by_path["docs/backlogs/post_h_prioritized_roadmap.md"].is_source_of_truth
    assert by_path[".devpilot/project_state.json"].is_machine_readable_source


def test_post_h_009_a_contract_is_registered_in_tcr() -> None:
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-009-documentation-source-registry")
    assert contract["owner"] == "POST-H-009-A"
    assert "tests/test_documentation_source_registry_schema.py" in contract["test_files"]
    assert ".devpilot/docs_governance/source_registry.json" in contract["validates"]
    assert contract["mutable_global_state_allowed"] is False

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-009-documentation-source-registry")
    assert contract_v2["capability"] == "DocumentationSourceRegistry"
    assert contract_v2["required_for_release"] is True
    assert contract_v2["required_for_security_gate"] is True
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["mutations_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False


def test_post_h_009_b_validator_contract_is_registered_in_tcr() -> None:
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-009-documentation-governance-validator")
    assert contract["owner"] == "POST-H-009-B"
    assert "tests/test_documentation_governance_validator.py" in contract["test_files"]
    assert "src/devpilot_core/docs_governance/validator.py" in contract["validates"]
    assert "python -m devpilot_core docs-governance validate --json" in contract["recommended_commands"]

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-009-documentation-governance-validator")
    assert contract_v2["capability"] == "DocumentationGovernanceValidator"
    assert contract_v2["required_for_release"] is True
    assert contract_v2["required_for_security_gate"] is True
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["mutations_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False


def test_post_h_009_c_sync_validator_contract_is_registered_in_tcr() -> None:
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-009-documentation-sync-validator")
    assert contract["owner"] == "POST-H-009-C"
    assert "tests/test_documentation_governance_sync.py" in contract["test_files"]
    assert "src/devpilot_core/docs_governance/drift.py" in contract["validates"]
    assert "python -m devpilot_core docs-governance report --write-report --json" in contract["recommended_commands"]

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-009-documentation-sync-validator")
    assert contract_v2["capability"] == "DocumentationSyncValidator"
    assert contract_v2["required_for_release"] is True
    assert contract_v2["required_for_security_gate"] is True
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["mutations_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False
