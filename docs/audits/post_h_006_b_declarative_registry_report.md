# POST-H-006-B — Command registry declarativo inicial

Estado: `implemented-initial / declarative baseline`.

## Propósito

Crear una capa declarativa inicial sobre el inventario estático del CLI para que DevPilot pueda gobernar comandos por dominio, riesgo, side effects, tests recomendados y estado de migración sin cambiar la semántica pública del CLI.

## Alcance implementado

```text
- `src/devpilot_core/cli_registry/registry.py` con DeclarativeCliRegistryBuilder.
- Grupos iniciales: workspace, standards, schema, validate, project-state, test-contracts, quality-gate, industrial-readiness.
- Overlay declarativo sobre el inventario AST de POST-H-006-A.
- Métricas declarative_registered_commands_total y legacy_unregistered_commands_total.
- Marcación explícita de comandos legacy-unregistered.
- Overrides de riesgo para workspace.init, test-contracts.migrate-v2 y quality-gate.run.
- Tests focales de completitud, seguridad, cobertura y sincronización documental.
```

## Seguridad

```text
dynamic_handler_loading_enabled = false
remote_execution_enabled = false
connector_write_enabled = false
plugin_execution_enabled = false
handler_migration_performed = false
network_used = false
external_api_used = false
source_mutations_performed = false
```

El registry declarativo no ejecuta comandos, no importa handlers dinámicamente y no cambia flags públicos.

## PASS

```text
PASS si todos los grupos iniciales tienen descriptor declarativo.
PASS si cada comando declarado tiene recommended_tests.
PASS si comandos con writes declaran writes_files=true.
PASS si el reporte identifica legacy_unregistered_commands_total.
PASS si los comandos sensibles dentro de grupos iniciales tienen policy metadata.
```

## BLOCK

```text
BLOCK si falta un grupo inicial.
BLOCK si se ocultan comandos legacy no declarados.
BLOCK si se habilita carga dinámica de handlers.
BLOCK si se habilita remote execution, connector write o plugin execution.
BLOCK si se cambia comportamiento público de comandos.
```

## Limitación industrial explícita

Esta versión es una primera línea de gobierno declarativo. Todavía no desacopla handlers de `cli.py`; la migración física y pruebas de paridad quedan para `POST-H-006-C`.

## Verificación recomendada

```powershell
python -m pytest tests/test_post_h_006_b_declarative_registry.py tests/test_post_h_006_cli_command_registry.py tests/test_cli_command_registry_schema.py tests/test_schema_registry.py tests/test_project_global_state.py -q
python -m devpilot_core cli-registry report --write-report --json
python -m devpilot_core schema validate --schema-id CliCommandRegistry --instance outputs/reports/cli_command_registry.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```
