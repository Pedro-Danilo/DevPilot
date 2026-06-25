---
doc_id: "POST-H-005-B-AUDIT"
title: "POST-H-005-B — Architecture AST inventory audit"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
local_first: true
dry_run: true
approval: "internal"
---

# POST-H-005-B — Architecture AST inventory audit

## Propósito

Auditar la implementación de `POST-H-005-B — Inventario AST de paquetes y módulos`, cuyo objetivo es convertir el código Python de `src/devpilot_core` en evidencia estructural reproducible para el futuro mapa arquitectónico ejecutable.

## Estado

Estado: `implemented-initial`.

La entrega es una primera versión de inventario AST. No implementa todavía grafo de dependencias, fan-in/fan-out real, scoring de hotspots, reporte final `architecture_map.json/.md` ni subgate de `quality-gate`.

## Alcance implementado

```text
src/devpilot_core/architecture/inventory.py
python -m devpilot_core architecture inventory --json
tests/test_architecture_inventory.py
docs/post_h_005_b_manifest.json
```

El inventario calcula por módulo:

```text
- module_id, package y path relativo.
- LOC no vacías/no comentario.
- clases, funciones e imports vía AST.
- exports aproximados.
- comandos CLI declarados con add_parser.
- handlers CLI por funciones *_command.
- tests relacionados por heurística de nombre/ruta.
```

## Funcionamiento

`ArchitectureInventoryBuilder` recorre `src/devpilot_core`, excluye caches/venv/outputs, parsea archivos `.py` con `ast.parse` y construye un `ArchitectureMap` en memoria. El payload se valida con `SchemaValidator.validate_payload(schema="ArchitectureMap", ...)`.

El comando no importa módulos dinámicamente, no ejecuta tests, no llama subprocesses, no usa red, no usa APIs externas y no escribe fuentes.

## Integración dentro de DevPilot

La implementación se integra en la CLI mediante:

```powershell
python -m devpilot_core architecture inventory --json
```

Opcionalmente puede persistir evidencia de comando bajo `outputs/reports/`:

```powershell
python -m devpilot_core architecture inventory --json --write-report
```

## Criterios PASS

```text
PASS si el comando devuelve ok=true.
PASS si modules_total y packages_total son mayores que cero.
PASS si cli.py se marca como is_cli_entrypoint=true.
PASS si se detectan comandos y handlers CLI.
PASS si el ArchitectureMap en memoria valida contra el schema registrado.
PASS si dry_run=true y network/API/mutations=false.
```

## Criterios BLOCK

```text
BLOCK si src/devpilot_core no existe.
BLOCK si el inventario ejecuta código del proyecto para descubrir módulos.
BLOCK si el inventario usa red, APIs externas o subprocesses.
BLOCK si muta fuentes.
BLOCK si pretende cerrar dependencias/hotspots antes de POST-H-005-C/D.
```

## Riesgos y limitaciones

```text
- El matching de tests es heurístico y puede producir falsos positivos/negativos.
- Los imports se almacenan como metadata; DependencyEdge se materializa en POST-H-005-C.
- direct_dependencies/fan-in/fan-out se mantienen sin enforcement hasta el grafo de dependencias.
- Los paquetes sin ownership explícito no bloquean en B; se tratarán en POST-H-005-E.
```

## Comandos de validación

```powershell
python -m pytest tests/test_architecture_inventory.py tests/test_post_h_005_architecture_map.py tests/test_architecture_ownership_registry.py tests/test_schema_registry.py -q
python -m devpilot_core architecture inventory --json
python -m devpilot_core validate docs --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## No-go gates

```text
NO-GO si se mueve código físico.
NO-GO si se refactoriza CLI.
NO-GO si se modifica ApplicationService.
NO-GO si se habilita remote/plugin/connector execution.
NO-GO si se agrega enforcement blocking agresivo antes del baseline completo.
```
