from __future__ import annotations

import json
from pathlib import Path

PRECODE = (
    (".devpilot/project.yaml", "project"),
    ("docs/00_product/product_vision.md", "product_vision"),
    ("docs/00_product/mvp_scope.md", "mvp_scope"),
    ("docs/01_requirements/requirements_specification.md", "requirements"),
    ("docs/02_architecture/architecture_document.md", "architecture"),
    ("docs/03_security/security_threat_model.md", "security"),
    ("docs/04_quality/test_strategy.md", "quality"),
    ("docs/onboarding/workspace_onboarding_baseline.md", "onboarding"),
)


def create_uoc003_workspace(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for relative, role in PRECODE:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".yaml":
            path.write_text("project_id: inventory-sales-local\nname: Inventory Sales Local\n", encoding="utf-8")
            continue
        links = ""
        trace = ""
        if role == "requirements":
            links = "\nSee [architecture](../02_architecture/architecture_document.md#architecture).\n"
            trace = "\n| FR-001 | US-001 | RISK-001 | CTRL-001 | TEST-001 test_inventory_sales |\n"
        if role == "architecture":
            links = "\nSee [requirements](../01_requirements/requirements_specification.md).\n"
        path.write_text(
            "---\n"
            f'doc_id: "UOC003-{role.upper()}"\n'
            f'title: "UOC-003 {role}"\n'
            'status: "approved"\n'
            'version: "1.0.0"\n'
            'owner: "Test"\n'
            'updated: "2026-08-06"\n'
            'approval: "approved_by_owner"\n'
            "---\n\n"
            f"# {role.replace('_', ' ').title()}\n\n"
            "## Purpose\n\nThis approved deterministic local artifact contains enough engineering content for UOC-003 validation tests.\n"
            "\n## Architecture\n\nLocal-first, read-only source validation with bounded runtime evidence.\n"
            f"{links}{trace}",
            encoding="utf-8",
        )
    miasi = root / ".devpilot/miasi"
    miasi.mkdir(parents=True, exist_ok=True)
    (miasi / "agent_registry.json").write_text(json.dumps({"schema_version": "1.0", "agents": []}), encoding="utf-8")
    (miasi / "tool_registry.json").write_text(json.dumps({"schema_version": "1.0", "tools": []}), encoding="utf-8")
    (miasi / "policy_matrix.json").write_text(json.dumps({"schema_version": "1.0", "rules": []}), encoding="utf-8")
    return root


def source_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and "outputs" not in path.parts and ".git" not in path.parts
    }
