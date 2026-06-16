from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_45_manifest_adr_and_audit_exist() -> None:
    manifest = json.loads(_read("docs/functional_sprint_45_manifest.json"))
    adr = _read("docs/02_architecture/adrs/ADR-0011-local-model-providers.md")
    audit = _read("docs/audits/func_sprint_45_local_providers_adr_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-45"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is True
    assert "docs/02_architecture/adrs/ADR-0011-local-model-providers.md" in manifest["created_files"]
    assert "tests/test_provider_config_schema.py" in manifest["tests"]
    assert "Proveedores locales de modelos gobernados" in adr
    assert "Accepted" in adr
    assert "implemented-initial" in audit
    assert "OllamaAdapter" in audit
    assert "LMStudioAdapter" in audit


def test_sprint_45_readme_runbook_backlogs_and_test_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog_d = _read("docs/devpilot_backlog_fase_D_ia_local_gobernada.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-69" in readme
    assert "Siguiente hito: `FUNC-SPRINT-70" in readme
    assert "## FUNC-SPRINT-45 — ADR y contratos de proveedores locales" in readme
    assert "python -m devpilot_core model providers --json" in runbook
    assert "## FUNC-SPRINT-45 — ADR y contratos de proveedores locales" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-56"' in backlog_d
    assert 'last_completed_sprint: "FUNC-SPRINT-55"' in backlog_d
    assert 'phase_d_status: "closed"' in backlog_d
    assert "Estado de implementación Sprint 45" in backlog_d
    assert 'next_sprint: "FUNC-SPRINT-70"' in functional_backlog
    assert "Transición posterior a FUNC-SPRINT-45" in functional_backlog
    assert "Actualización FUNC-SPRINT-45 — Pruebas de provider config local-first" in test_strategy


def test_sprint_45_miasi_model_provider_policy_declared() -> None:
    tool_registry = json.loads(_read(".devpilot/miasi/tool_registry.json"))
    policy_matrix = json.loads(_read(".devpilot/miasi/policy_matrix.json"))
    tool_card = _read("docs/06_miasi/tool_card.md")
    policy_card = _read("docs/06_miasi/policy_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")

    tools = {tool["tool_id"]: tool for tool in tool_registry["tools"]}
    rules = {rule["rule_id"]: rule for rule in policy_matrix["rules"]}

    assert tools["model.call.mock"]["status"] == "implemented"
    assert "SECRETS_RAW_DENY" in tools["model.call.mock"]["policy_rule_ids"]
    assert tools["model.call.local"]["status"] == "implemented-initial"
    assert "MODEL_LOCAL_PROVIDER_CONTROLLED" in tools["model.call.local"]["policy_rule_ids"]
    assert tools["model.call.external"]["status"] == "disabled"
    assert "MODEL_EXTERNAL_DENY" in tools["model.call.external"]["policy_rule_ids"]
    assert "MODEL_LOCAL_PROVIDER_CONTROLLED" in rules
    assert rules["MODEL_LOCAL_PROVIDER_CONTROLLED"]["domain"] == "Model"
    assert "Tool Card — Model providers locales gobernados" in tool_card
    assert "MODEL_LOCAL_PROVIDER_CONTROLLED" in policy_card
    assert "Estado operacional Model Providers" in tool_registry_doc


def test_sprint_45_provider_contract_artifacts_are_synchronized() -> None:
    schema = json.loads(_read("docs/schemas/provider_config.schema.json"))
    catalog = json.loads(_read("docs/schemas/schema_catalog.json"))
    providers_example = _read(".devpilot/providers.yaml.example")

    assert schema["x-devpilot-schema-id"] == "SCHEMA-DEVPL-PROVIDER-CONFIG-V2"
    assert schema["x-devpilot-sprint"] == "FUNC-SPRINT-45"
    assert 'schema_version: "2.0"' in providers_example
    assert 'id: "ollama"' in providers_example
    assert 'enabled: false' in providers_example
    assert 'id: "lmstudio"' in providers_example
    provider_schema = next(item for item in catalog["schemas"] if item["contract"] == "ProviderConfig")
    assert provider_schema["schema_id"] == "SCHEMA-DEVPL-PROVIDER-CONFIG-V2"
    assert provider_schema["sprint"] == "FUNC-SPRINT-45"
