---
title: "POST-H-006-C — Handler migration audit"
doc_id: "AUDIT-POST-H-006-C-HANDLER-MIGRATION"
status: "implemented-initial"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
---

# POST-H-006-C — Migración incremental de handlers de validación/workspace

## Propósito

Documentar la primera migración real de handlers del CLI hacia módulos explícitos por dominio, preservando compatibilidad pública y evitando una reescritura masiva de `src/devpilot_core/cli.py`.

## Alcance implementado

```text
src/devpilot_core/cli_commands/workspace.py
  - handle_workspace_init
  - handle_workspace_status

src/devpilot_core/cli_commands/validation.py
  - handle_validate_scope
```

## Funcionamiento técnico

`cli.py` mantiene el parser público y los wrappers `workspace_init_command`, `workspace_status_command` y `validate_gateway_command`. Esos wrappers delegan la construcción de `CommandResult` a `cli_commands`, luego aplican el mismo flujo preexistente:

```text
_write_optional_command_report
_emit_result_event
_persist_result
print_result
return exit_code
```

## Seguridad

```text
runtime_router_enabled = false
dynamic_handler_loading_enabled = false
remote_execution_enabled = false
connector_write_enabled = false
plugin_execution_enabled = false
network_used = false
external_api_used = false
source_mutations_performed = false
```

## Criterios PASS

```text
PASS si workspace init --dry-run no escribe project.yaml.
PASS si workspace status conserva CommandResult equivalente.
PASS si validate docs/contracts/all conserva semántica.
PASS si el registry marca migrated handlers sin habilitar router runtime.
PASS si los contratos v1/v2 y documentación quedan sincronizados.
```

## Limitaciones

Esta entrega es `implemented-initial`. No elimina wrappers legacy de `cli.py`, no activa registry runtime, no migra grupos de alto riesgo y no pretende cerrar toda la deuda del hotspot CLI.

## Verificación recomendada

```powershell
python -m pytest tests/test_post_h_006_c_handler_migration.py tests/test_post_h_006_b_declarative_registry.py tests/test_post_h_006_cli_command_registry.py tests/test_cli_command_registry_schema.py -q
python -m devpilot_core cli-registry report --write-report --json
python -m devpilot_core schema validate --schema-id CliCommandRegistry --instance outputs/reports/cli_command_registry.json --json
```
