---
title: "CLI command registry map"
doc_id: "ARCH-CLI-COMMAND-REGISTRY-MAP"
version: "0.1.0"
status: "implemented-initial"
approval: "internal"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
sprint: "POST-H-006-A"
local_first: true
dry_run: true
---

# CLI command registry map

## Propósito

Este documento describe la baseline técnica de `POST-H-006-A` para registrar la superficie pública del CLI de DevPilot en un formato machine-readable y validable por schema.

## Estado

Estado: `implemented-initial / read-only static inventory`.

La capacidad actual inventaria el CLI, pero no migra handlers. La modularización real debe hacerse de forma incremental en micro-sprints posteriores con pruebas de paridad y control de regresión.

## Arquitectura

```text
src/devpilot_core/cli.py
  -> AST parser read-only
  -> StaticCliInventoryExtractor
  -> CliCommandRegistry payload
  -> SchemaValidator(CliCommandRegistry)
  -> outputs/reports/cli_command_registry.json
  -> outputs/reports/cli_command_registry.md
```

## Componentes

| Componente | Rol |
|---|---|
| `cli_registry/models.py` | Dataclasses y enums del registry. |
| `cli_registry/builders.py` | `StaticCliInventoryExtractor`: extractor AST y construcción del payload. |
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

- `POST-H-006-B`: registry declarativo inicial para comandos de bajo riesgo.
- `POST-H-006-C`: migración controlada de handlers de validación/workspace.
- `POST-H-006-D/E`: paridad, cobertura y cierre del hito.
