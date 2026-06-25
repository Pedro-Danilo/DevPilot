---
title: "CLI command registry map"
doc_id: "ARCH-CLI-COMMAND-REGISTRY-MAP"
version: "0.5.0"
status: "implemented-initial"
approval: "internal"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
sprint: "POST-H-006-E"
local_first: true
dry_run: true
---

# CLI command registry map

## Propósito

Este documento describe la baseline técnica acumulada de `POST-H-006-A/B/C/D/E`: inventario estático de la superficie pública del CLI y overlay declarativo inicial en formato machine-readable y validable por schema.

## Estado

Estado: `implemented-initial / hotspot ownership report + no-growth gate, no runtime registry router`.

La capacidad actual inventaria el CLI, agrega una capa declarativa inicial para grupos gobernables y migra de forma controlada la lógica de resultado de `workspace.init`, `workspace.status` y `validate` a módulos `cli_commands`. La modularización sigue siendo incremental: el parser público y los wrappers de compatibilidad permanecen en `cli.py`.

## Arquitectura

```text
src/devpilot_core/cli.py
  -> public parser + compatibility wrappers
  -> src/devpilot_core/cli_commands/workspace.py
  -> src/devpilot_core/cli_commands/validation.py
  -> AST parser read-only
  -> StaticCliInventoryExtractor
  -> DeclarativeCliRegistryBuilder
  -> migrated handler metadata
  -> CliCommandRegistry payload
  -> CliHotspotOwnershipReportBuilder
  -> CliNoGrowthGate
  -> legacy_command_allowlist.json
  -> SchemaValidator(CliCommandRegistry)
  -> outputs/reports/cli_command_registry.json
  -> outputs/reports/cli_command_registry.md
```

## Componentes

| Componente | Rol |
|---|---|
| `cli_registry/models.py` | Dataclasses y enums del registry. |
| `cli_registry/builders.py` | `StaticCliInventoryExtractor`: extractor AST y construcción del inventario base. |
| `cli_registry/registry.py` | `DeclarativeCliRegistryBuilder`: overlay declarativo inicial y metadata de handlers migrados POST-H-006-C. |
| `cli_registry/report.py` | Builder de `CommandResult`, validación, hotspot report y escritura opcional de reportes. |
| `cli_registry/hotspots.py` | `CliHotspotOwnershipReportBuilder`: métricas read-only de ownership, riesgos, side effects, gaps TCR y top hotspots por comando. |
| `cli_registry/growth_gate.py` | `CliNoGrowthGate`: gate local que bloquea nuevos comandos legacy-unregistered no cubiertos por allowlist temporal. |
| `.devpilot/cli_registry/legacy_command_allowlist.json` | Allowlist explícita y temporal del legacy conocido para impedir crecimiento monolítico no registrado. |
| `cli_registry/__init__.py` | API pública interna del paquete. |
| `cli.py` | Mantiene parser público, wrappers de compatibilidad, eventos, persistencia y reportes opcionales. |
| `cli_commands/workspace.py` | Handlers migrados de `workspace.init` y `workspace.status` que construyen `CommandResult` sin renderizar salida. |
| `cli_commands/validation.py` | Handler migrado de `validate docs/contracts/all` vía `ValidationGateway`. |
| `cli_command_registry.schema.json` | Contrato estructural del reporte. |

## Invariantes de seguridad

```text
remote_execution_enabled = false
connector_write_enabled = false
plugin_execution_enabled = false
dynamic_handler_loading_enabled = false
network_used = false
external_api_used = false
source_mutations_performed = false
```

## Relación con POST-H-005

`POST-H-005` identificó `src/devpilot_core/cli.py` como hotspot principal. `POST-H-006-A` convierte esa señal en un inventario operativo que permitirá decidir qué grupos migrar primero y qué pruebas focales ejecutar por dominio.

## Próximos pasos

- `POST-H-006-E`: gate de no crecimiento monolítico y allowlist explícita de legacy.
- `POST-H-007`: hardening de ApplicationService boundary usando los gaps del reporte D.
- Cierre posterior del hito: paridad, cobertura y control de crecimiento del CLI.

## POST-H-006-B — Registry declarativo inicial

La segunda etapa introduce `DeclarativeCliRegistryBuilder`, que combina el inventario AST con una lista curada de grupos iniciales:

```text
workspace, standards, schema, validate, project-state, test-contracts, quality-gate, industrial-readiness
```

Cada comando registrado queda anotado con:

```text
registry_phase = declarative-initial
registration_status = registered-declarative
declarative_registered = true
handler_migration_performed = false
```

Los comandos fuera de ese alcance se conservan en el reporte con:

```text
registry_phase = legacy-unregistered
declarative_registered = false
```

Esto permite medir cobertura sin ocultar deuda ni cambiar comportamiento público.

## Métricas de cobertura

```text
declarative_registered_groups_total
declarative_registered_commands_total
legacy_unregistered_groups_total
legacy_unregistered_commands_total
```


## POST-H-006-C — Migración incremental de handlers

La tercera etapa introduce el paquete `src/devpilot_core/cli_commands/` como destino inicial para handlers explícitos por dominio. La migración es deliberadamente parcial y segura:

```text
workspace.init   -> cli_commands/workspace.py::handle_workspace_init
workspace.status -> cli_commands/workspace.py::handle_workspace_status
validate         -> cli_commands/validation.py::handle_validate_scope
```

El contrato de compatibilidad queda así:

```text
cli.py
  - conserva argparse y nombres públicos;
  - conserva wrappers `*_command`;
  - conserva `print_result`;
  - conserva `_write_optional_command_report`;
  - conserva `_emit_result_event`;
  - conserva `_persist_result`.

cli_commands/*
  - construyen CommandResult;
  - no imprimen;
  - no escriben reportes;
  - no emiten eventos;
  - no cargan handlers dinámicamente;
  - no habilitan red ni ejecución remota.
```

Métricas nuevas de registry:

```text
migrated_handlers_total = 3
migrated_command_ids = ["validate", "workspace.init", "workspace.status"]
runtime_router_enabled = false
dynamic_handler_loading_enabled = false
```

Esta decisión reduce acoplamiento sin esconder deuda: los comandos no migrados siguen visibles como declarativos o `legacy-unregistered`.


## POST-H-006-D — Hotspot ownership report

La cuarta etapa introduce `CliHotspotOwnershipReportBuilder` en `src/devpilot_core/cli_registry/hotspots.py`. Este builder deriva métricas read-only del registry acumulado y del Test Contract Registry local.

Arquitectura extendida:

```text
CliCommandRegistry payload
  -> CliHotspotOwnershipReportBuilder
  -> Test Contract Registry v1/v2 index
  -> ownership status classifier
  -> command hotspot scorer
  -> outputs/reports/cli_command_registry_report.json
  -> outputs/reports/cli_command_registry_report.md
```

Métricas producidas:

```text
migrated_commands_total
registered_only_commands_total
legacy_commands_total
commands_with_side_effects_total
high_or_critical_risk_commands_total
commands_without_application_service_boundary_total
commands_without_test_contract_total
top_hotspots_total
```

Estados de ownership:

```text
migrated        = handler ya movido a cli_commands con wrapper público preservado.
registered_only = descriptor declarativo existe, pero handler aún no migrado.
legacy          = comando sigue visible únicamente como legacy-unregistered.
```

Limitación industrial explícita: el reporte es advisory y no bloquea cambios. El enforcement de no crecimiento monolítico queda para `POST-H-006-E`; los gaps de ApplicationService boundary alimentan `POST-H-007`.


## POST-H-006-E — No-growth gate

La quinta etapa introduce `CliNoGrowthGate` en `src/devpilot_core/cli_registry/growth_gate.py`. Este componente convierte la visibilidad advisory de POST-H-006-D en una regla operativa bloqueante: todo comando público nuevo debe tener descriptor declarativo o handler migrado.

Arquitectura extendida:

```text
CliCommandRegistry payload
  -> CliNoGrowthGate
  -> .devpilot/cli_registry/legacy_command_allowlist.json
  -> unexpected legacy command detector
  -> CommandResult PASS/BLOCK
  -> outputs/reports/cli_command_registry_no_growth_gate.json
  -> outputs/reports/cli_command_registry_no_growth_gate.md
```

Regla principal:

```text
PASS si set(legacy_unregistered_command_ids) <= set(allowed_legacy_command_ids)
BLOCK si aparece cualquier legacy_unregistered_command_id no allowlisted
```

El comando público es:

```powershell
python -m devpilot_core cli-registry guard --json
```

Invariantes:

```text
- No ejecuta comandos públicos.
- No importa handlers dinámicamente.
- No modifica archivos fuente.
- Solo escribe reportes con --write-report bajo outputs/reports.
- No habilita runtime router, remote execution, connector write ni plugin execution.
```

Limitación industrial explícita: el gate impide crecimiento monolítico no registrado, pero no reduce automáticamente la deuda legacy. La allowlist debe disminuir con nuevas migraciones o descriptors por dominio y la siguiente frontera es `POST-H-007 — ApplicationService boundary hardening`.
