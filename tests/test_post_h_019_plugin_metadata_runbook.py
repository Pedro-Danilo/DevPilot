from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict[str, str]:
    assert text.startswith("---")
    raw = text.split("---", 2)[1]
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields


def _post_h_number(value: str) -> int:
    marker = "POST-H-"
    assert marker in value
    return int(value.split(marker, 1)[1].split("-", 1)[0])


def test_post_h_019_e_plugin_metadata_runbook_documents_metadata_only_and_adr_trigger() -> None:
    runbook = _read("docs/05_operations/plugin_metadata_runbook.md")
    fm = _frontmatter(runbook)

    assert fm["doc_id"] == "POST-H-019-PLUGIN-METADATA-RUNBOOK"
    assert fm["status"] == "approved"
    assert fm["plugin_execution_enabled"] == "false"
    for required in [
        "metadata-only / validator-only / dry-run",
        "ADR trigger",
        "Sandbox técnico",
        "RBAC",
        "Approvals",
        "Tests",
        "Observabilidad",
        "Rollback",
        "Quality gate",
        "plugin.code.execute",
        "effect=deny",
    ]:
        assert required in runbook
    for blocked in [
        "NO-GO si se ejecuta código de plugin",
        "NO-GO si se importa dinámicamente",
        "NO-GO si se ejecuta pip install",
        "NO-GO si se usa red o API externa",
        "NO-GO si un manifest válido se interpreta como permiso de ejecución",
    ]:
        assert blocked in runbook
    assert "pip install automático" in runbook


def test_post_h_019_e_closes_backlog_and_advances_project_state_to_post_h_020() -> None:
    backlog = _read("docs/backlogs/POST-H-019_plugin_sandbox_design.md")
    implementation = _read("docs/POST-H-019_plugin_sandbox_design.md")
    state = json.loads(_read(".devpilot/project_state.json"))

    for document in (backlog, implementation):
        fm = _frontmatter(document)
        assert fm["implementation_status"] == "closed"
        assert fm["current_micro_sprint"] == "POST-H-019-E"
        assert fm["next_micro_sprint"] == "POST-H-020"
        assert "Estado acumulativo: `closed / implemented-initial`" in document
        assert "POST-H-019 queda cerrado" in document
        assert "plugin execution real permanece bloqueado" in document

    assert _post_h_number(state["last_completed_sprint"]) >= 19
    assert _post_h_number(state["next_sprint"]) >= 20
    assert _post_h_number(state["current_micro_sprint"]) >= 19
    assert _post_h_number(state["next_micro_sprint"]) >= 20


def test_post_h_019_e_registry_and_contracts_reference_runbook_and_closure() -> None:
    source_registry = _read(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = json.loads(_read(".devpilot/testing/test_contract_registry.json"))
    tcr_v2 = json.loads(_read(".devpilot/testing/test_contract_registry_v2.json"))

    for doc_id in [
        "POST-H-019-PLUGIN-METADATA-RUNBOOK",
        "POST-H-019-E-PLUGIN-SANDBOX-CLOSURE-REPORT",
        "POST-H-019-E-MANIFEST",
    ]:
        assert doc_id in source_registry

    contract_v1 = next(item for item in tcr_v1["contracts"] if item["contract_id"] == "post-h-019-plugin-sandbox-design")
    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-019-plugin-sandbox-design")

    assert "docs/05_operations/plugin_metadata_runbook.md" in contract_v1["validates"]
    assert "tests/test_post_h_019_plugin_metadata_runbook.py" in contract_v1["test_files"]
    assert contract_v2["execution_profile"] == "release"
    assert contract_v2["owner"] == "POST-H-019-E"
    assert "tests/test_post_h_019_plugin_metadata_runbook.py" in contract_v2["test_files"]


def test_post_h_019_e_readme_runbook_changelog_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    changelog = _read("docs/release/CHANGELOG.md")

    for text in (readme, runbook, changelog):
        assert "POST-H-019-E" in text
        assert "POST-H-020" in text
        assert "plugin execution" in text
    assert "POST-H-019 — Plugin sandbox design sin ejecución arbitraria queda cerrado" in readme
    assert "plugin_metadata_runbook.md" in runbook
