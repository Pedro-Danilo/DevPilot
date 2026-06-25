from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_FIXTURE = ROOT / "tests/fixtures/architecture_map/valid_minimal_architecture_map.json"
INVALID_NETWORK_FIXTURE = ROOT / "tests/fixtures/architecture_map/invalid_network_architecture_map.json"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_architecture_map_schema_registered_and_validates_minimal_fixture() -> None:
    from devpilot_core.architecture import ARCHITECTURE_MAP_CONTRACT, ARCHITECTURE_MAP_SCHEMA_ID
    from devpilot_core.cli_models import ExitCode
    from devpilot_core.schemas import SchemaValidator

    catalog = _read_json("docs/schemas/schema_catalog.json")
    schemas = {item["schema_id"]: item for item in catalog["schemas"]}

    assert ARCHITECTURE_MAP_SCHEMA_ID in schemas
    assert schemas[ARCHITECTURE_MAP_SCHEMA_ID]["contract"] == ARCHITECTURE_MAP_CONTRACT
    assert schemas[ARCHITECTURE_MAP_SCHEMA_ID]["path"] == "docs/schemas/architecture_map.schema.json"

    result = SchemaValidator(ROOT).validate(schema="ArchitectureMap", instance=VALID_FIXTURE)

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS


def test_architecture_map_schema_rejects_network_usage() -> None:
    from devpilot_core.cli_models import ExitCode
    from devpilot_core.schemas import SchemaValidator

    result = SchemaValidator(ROOT).validate(schema="ArchitectureMap", instance=INVALID_NETWORK_FIXTURE)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)
    assert any(finding.path == "/safety/network_used" or finding.metadata.get("instance_path") == "/safety/network_used" for finding in result.findings)


def test_architecture_model_serializes_expected_contract_shape() -> None:
    from devpilot_core.architecture import (
        ARCHITECTURE_MAP_SCHEMA_ID,
        ArchitectureMap,
        ArchitectureModule,
        ArchitecturePackage,
        DependencyEdge,
        DependencyKind,
        DependencyPolicy,
        Hotspot,
        OwnershipEntry,
    )

    package = ArchitecturePackage(
        package="devpilot_core.policy",
        domain="governance.security",
        owner="architecture/security",
        criticality="P0",
        risk_level="critical",
        modules=("devpilot_core.policy.engine",),
        direct_dependencies=("devpilot_core.cli_models",),
        fan_in=3,
        fan_out=2,
        loc=1200,
        test_contracts=("post-h-004-miasi-semantic-validator",),
    )
    module = ArchitectureModule(
        module_id="devpilot_core.policy.engine",
        package="devpilot_core.policy",
        path="src/devpilot_core/policy/engine.py",
        loc=1200,
        classes_total=2,
        functions_total=10,
        imports_total=5,
    )
    edge = DependencyEdge(
        source="devpilot_core.quality",
        target="devpilot_core.miasi",
        kind=DependencyKind.INTERNAL_IMPORT,
        policy=DependencyPolicy.ALLOW,
        sensitive=True,
        reason="Quality gate consumes semantic validator as a read-only signal.",
    )
    hotspot = Hotspot(
        subject_id="devpilot_core.cli",
        subject_type="module",
        score=99.0,
        criticality="P0",
        reasons=("monolithic CLI",),
        recommendations=("Split CLI handlers in POST-H-006.",),
    )
    owner = OwnershipEntry(
        package="devpilot_core.policy",
        domain="governance.security",
        owner="architecture/security",
        criticality="P0",
        risk_level="critical",
    )

    payload = ArchitectureMap(
        map_id="unit-test-architecture-map",
        created_by="POST-H-005-A",
        packages=(package,),
        modules=(module,),
        dependencies=(edge,),
        hotspots=(hotspot,),
        ownership_registry=(owner,),
    ).to_dict()

    assert payload["schema_id"] == ARCHITECTURE_MAP_SCHEMA_ID
    assert payload["summary"]["packages_total"] == 1
    assert payload["summary"]["modules_total"] == 1
    assert payload["summary"]["dependencies_total"] == 1
    assert payload["summary"]["hotspots_total"] == 1
    assert payload["safety"]["dry_run"] is True
    assert payload["safety"]["network_used"] is False


def test_post_h_005_backlog_and_docs_mark_a_as_implemented_initial() -> None:
    backlog = _read("docs/backlogs/POST-H-005_architecture_map_executable.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    changelog = _read("docs/release/CHANGELOG.md")
    design_doc = _read("docs/02_architecture/current_executable_architecture_map.md")
    audit = _read("docs/audits/post_h_005_a_architecture_map_schema_report.md")

    assert 'status: "approved"' in backlog
    assert 'implementation_status: "in-progress"' in backlog
    assert "POST-H-005-A — Modelos y schema de architecture map" in backlog
    assert "Estado: `implemented-initial`" in backlog
    assert "POST-H-005-A — Modelos y schema de architecture map" in readme
    assert "Último micro-sprint implementado: `POST-H-005-" in readme
    assert "Siguiente micro-sprint: `POST-H-005-" in readme
    assert "POST-H-005-A — Operación del modelo y schema ArchitectureMap" in runbook
    assert "post-h-005-a" in changelog
    assert "SCHEMA-DEVPL-ARCHITECTURE-MAP-V1" in design_doc
    assert "POST-H-005-A" in audit


def test_post_h_005_manifest_records_preliminary_non_executing_scope() -> None:
    from devpilot_core.architecture import ARCHITECTURE_MAP_SCHEMA_ID

    manifest = _read_json("docs/post_h_005_a_manifest.json")

    assert manifest["id"] == "POST-H-005-A"
    assert manifest["status"] == "implemented-initial"
    assert manifest["parent_hito"] == "POST-H-005"
    assert manifest["next_micro_sprint"] == "POST-H-005-B"
    assert manifest["architecture_map_schema_id"] == ARCHITECTURE_MAP_SCHEMA_ID
    assert manifest["inventory_ast_implemented"] is False
    assert manifest["dependency_graph_implemented"] is False
    assert manifest["hotspot_analyzer_implemented"] is False
    assert manifest["quality_gate_subgate_added"] is False
    assert manifest["network_used"] is False
    assert manifest["external_api_used"] is False
    assert manifest["mutations_performed"] is False
