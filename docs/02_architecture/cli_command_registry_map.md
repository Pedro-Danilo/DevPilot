---
title: "CLI command registry map"
doc_id: "ARCH-CLI-COMMAND-REGISTRY-MAP"
version: "0.2.0"
status: "implemented-initial"
approval: "internal"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
sprint: "POST-H-006-B"
local_first: true
dry_run: true
---

# CLI command registry map

## Propósito

Este documento describe la baseline técnica acumulada de `POST-H-006-A/B`: inventario estático de la superficie pública del CLI y overlay declarativo inicial en formato machine-readable y validable por schema.

## Estado

Estado: `implemented-initial / declarative baseline, no handler migration`.

La capacidad actual inventaria el CLI y agrega una capa declarativa inicial para grupos gobernables, pero no migra handlers. La modularización real debe hacerse de forma incremental en micro-sprints posteriores con pruebas de paridad y control de regresión.

## Arquitectura

```text
src/devpilot_core/cli.py
  -> AST parser read-only
  -> StaticCliInventoryExtractor
  -> DeclarativeCliRegistryBuilder
  -> CliCommandRegistry payload
  -> SchemaValidator(CliCommandRegistry)
  -> outputs/reports/cli_command_registry.json
  -> outputs/reports/cli_command_registry.md
```

## Componentes

| Componente | Rol |
|---|---|
| `cli_registry/models.py` | Dataclasses y enums del registry. |
| `cli_registry/builders.py` | `StaticCliInventoryExtractor`: extractor AST y construcción del inventario base. |
| `cli_registry/registry.py` | `DeclarativeCliRegistryBuilder`: overlay declarativo inicial para grupos POST-H-006-B. |
| `cli_registry/report.py` | Builder de `CommandResult`, validación y escritura opcional de reportes. |
| `cli_registry/__init__.py` | API pública interna del paquete. |
| `cli.py` | Expone `cli-registry report` sin cambiar comandos existentes. |
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

- `POST-H-006-C`: migración controlada de handlers de validación/workspace.
- `POST-H-006-D`: reporte de hotspots CLI y ownership por comando.
- `POST-H-006-D/E`: paridad, cobertura y cierre del hito.

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
