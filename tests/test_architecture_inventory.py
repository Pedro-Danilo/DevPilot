from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _inventory_result():
    from devpilot_core.architecture.inventory import ArchitectureInventoryBuilder

    return ArchitectureInventoryBuilder(ROOT).build()


def test_architecture_inventory_builder_discovers_ast_modules_without_execution() -> None:
    from devpilot_core.cli_models import ExitCode

    result = _inventory_result()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["modules_total"] >= 150
    assert summary["packages_total"] >= 20
    assert summary["parse_errors_total"] == 0
    assert summary["cli_commands_total"] >= 100
    assert summary["cli_handlers_total"] >= 100
    assert summary["related_tests_total"] >= 50
    assert summary["dry_run"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False


def test_architecture_inventory_payload_validates_against_architecture_map_schema() -> None:
    result = _inventory_result()
    architecture_map = result.data["architecture_map"]
    modules = {module["module_id"]: module for module in architecture_map["modules"]}
    packages = {package["package"]: package for package in architecture_map["packages"]}

    assert "devpilot_core.cli" in modules
    assert "devpilot_core.cli" in packages
    assert "devpilot_core.policy" in packages
    assert "devpilot_core.schemas" in packages
    assert "devpilot_core.testing" in packages
    assert modules["devpilot_core.cli"]["is_cli_entrypoint"] is True
    assert modules["devpilot_core.cli"]["metadata"]["cli_commands"]
    assert packages["devpilot_core.cli"]["metadata"]["cli_commands_total"] >= 100
    assert packages["devpilot_core.cli"]["metadata"]["cli_handlers_total"] >= 100
    assert packages["devpilot_core.policy"]["owner"] == "architecture/security"
    assert packages["devpilot_core.policy"]["ownership_status"] == "declared"
    assert architecture_map["dependencies"] == []
    assert architecture_map["hotspots"] == []
    assert architecture_map["safety"]["dry_run"] is True
    assert architecture_map["safety"]["network_used"] is False

    assert result.data["schema_validation"]["valid"] is True
    assert result.data["schema_validation"]["errors_total"] == 0


def test_architecture_inventory_cli_parser_is_registered_in_cli_source() -> None:
    cli_source = _read("src/devpilot_core/cli.py")

    assert 'sub.add_parser("architecture"' in cli_source
    assert 'architecture_sub.add_parser("inventory"' in cli_source
    assert "architecture_inventory_command" in cli_source
    assert "ArchitectureInventoryBuilder" in cli_source


def test_post_h_005_b_docs_and_manifest_are_synchronized() -> None:
    backlog = _read("docs/backlogs/POST-H-005_architecture_map_executable.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    changelog = _read("docs/release/CHANGELOG.md")
    audit = _read("docs/audits/post_h_005_b_architecture_inventory_report.md")
    manifest = _read_json("docs/post_h_005_b_manifest.json")

    assert "POST-H-005-B — Inventario AST de paquetes y módulos" in backlog
    assert "Estado: `implemented-initial`" in backlog
    assert "Último micro-sprint implementado: `POST-H-005-" in readme
    assert "Siguiente micro-sprint: `POST-H-005-" in readme
    assert "POST-H-005-B — Operación del inventario AST ArchitectureMap" in runbook
    assert "post-h-005-b" in changelog
    assert "architecture inventory --json" in audit
    assert manifest["id"] == "POST-H-005-B"
    assert manifest["status"] == "implemented-initial"
    assert manifest["inventory_ast_implemented"] is True
    assert manifest["dependency_graph_implemented"] is False
    assert manifest["hotspot_analyzer_implemented"] is False
    assert manifest["quality_gate_subgate_added"] is False
    assert manifest["network_used"] is False
    assert manifest["external_api_used"] is False
    assert manifest["source_mutations_performed"] is False
