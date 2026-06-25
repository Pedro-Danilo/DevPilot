from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_cli_command_registry_schema_is_registered_and_validates_report_payload() -> None:
    from devpilot_core.cli_registry import CLI_REGISTRY_CONTRACT, CLI_REGISTRY_SCHEMA_ID
    from devpilot_core.cli_registry.report import CliCommandRegistryReportBuilder
    from devpilot_core.schemas import SchemaValidator

    catalog = _read_json("docs/schemas/schema_catalog.json")
    schemas = {item["schema_id"]: item for item in catalog["schemas"]}

    assert CLI_REGISTRY_SCHEMA_ID in schemas
    assert schemas[CLI_REGISTRY_SCHEMA_ID]["contract"] == CLI_REGISTRY_CONTRACT
    assert schemas[CLI_REGISTRY_SCHEMA_ID]["path"] == "docs/schemas/cli_command_registry.schema.json"

    result = CliCommandRegistryReportBuilder(ROOT).build()
    assert result.ok, result.to_dict()

    validation = SchemaValidator(ROOT).validate_payload(
        schema="CliCommandRegistry",
        payload=result.data["registry"],
        instance_label="unit-test:cli-command-registry",
    )
    assert validation.ok is True, validation.to_dict()


def test_cli_command_registry_schema_rejects_unsafe_dynamic_loader() -> None:
    from copy import deepcopy

    from devpilot_core.cli_registry.report import CliCommandRegistryReportBuilder
    from devpilot_core.schemas import SchemaValidator

    payload = deepcopy(CliCommandRegistryReportBuilder(ROOT).build().data["registry"])
    payload["safety"]["dynamic_handler_loading_enabled"] = True
    payload["summary"]["dynamic_handler_loading_enabled"] = True

    result = SchemaValidator(ROOT).validate_payload(
        schema="CliCommandRegistry",
        payload=payload,
        instance_label="unit-test:unsafe-cli-command-registry",
    )

    assert result.ok is False
    assert result.data["summary"]["valid"] is False
