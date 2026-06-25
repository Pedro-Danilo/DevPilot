---
doc_id: "POST-H-005-ARCHITECTURE-MAP-DESIGN"
title: "POST-H-005 — Modelo e inventario ejecutable de architecture map"
status: "approved"
version: "1.3.0"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
local_first: true
dry_run: true
approval: "internal"
---

# POST-H-005 — Modelo e inventario ejecutable de architecture map

## Propósito

`POST-H-005-A` inicia `POST-H-005 — Architecture map executable / dependency ownership` creando el contrato estructural para un mapa arquitectónico ejecutable, reproducible y gobernado. El objetivo de esta primera entrega es estabilizar el payload antes de implementar inventario AST, análisis de dependencias, scoring de hotspots o enforcement de boundaries.

## Estado

Estado: `implemented-initial / executable inventory, dependency graph, advisory hotspot ranking and final report baseline`.

Esta entrega no ejecuta análisis AST, no calcula fan-in/fan-out real, no mueve módulos, no modifica dependencias, no agrega subgate de quality-gate y no cambia la semántica de comandos. Define el contrato sobre el cual trabajarán `POST-H-005-B/C/D/E`.

## Contrato registrado

```text
schema_id: SCHEMA-DEVPL-ARCHITECTURE-MAP-V1
contract: ArchitectureMap
schema: docs/schemas/architecture_map.schema.json
ownership_registry: .devpilot/architecture/ownership_registry.json
```

## Modelo mental

```text
ArchitectureMap
  ├─ ArchitecturePackage
  ├─ ArchitectureModule
  ├─ DependencyEdge
  ├─ Hotspot
  ├─ OwnershipEntry
  ├─ ownership_gaps
  ├─ recommendations
  └─ safety invariants
```

## Paquetes críticos iniciales

El registry inicial de ownership cubre, como mínimo:

```text
devpilot_core.cli
devpilot_core.policy
devpilot_core.schemas
devpilot_core.agents
devpilot_core.testing
devpilot_core.quality
devpilot_core.industrial
```

También incluye `cli_models`, `application`, `miasi`, `multiagent` e `interfaces` para preparar `POST-H-006` y `POST-H-007`.

## Invariantes de seguridad

El schema exige:

```text
dry_run=true
network_used=false
external_api_used=false
mutations_performed=false
source_mutations_performed=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## Criterios PASS

```text
PASS si ArchitectureMap valida un reporte mínimo.
PASS si el fixture con network_used=true falla.
PASS si ownership_registry cubre cli, policy, schemas, agents, testing, quality e industrial.
PASS si schema_catalog registra ArchitectureMap.
```

## Criterios BLOCK

```text
BLOCK si el schema permite red, APIs externas o mutaciones.
BLOCK si se omite ownership para paquetes críticos.
BLOCK si se implementa inventario AST antes de POST-H-005-B.
BLOCK si se agrega quality-gate/enforcement antes de POST-H-005-E.
```

## Evolución prevista

```text
POST-H-005-B — Inventario AST de paquetes y módulos.
POST-H-005-C — Grafo de dependencias y boundaries.
POST-H-005-D — Hotspot analyzer.
POST-H-005-E — Ownership validation y reporte final.
```

## POST-H-005-B — Inventario AST implementado

Estado: `implemented-initial / AST inventory only`.

`POST-H-005-B` agrega `ArchitectureInventoryBuilder` y el comando:

```powershell
python -m devpilot_core architecture inventory --json
```

El inventario recorre `src/devpilot_core`, parsea cada archivo `.py` con `ast` y calcula evidencia estructural por módulo sin ejecutar código del proyecto:

```text
- module_id y package.
- path relativo.
- LOC no vacías/no comentario.
- clases y funciones detectadas por AST.
- imports internos/externos aproximados.
- exports aproximados por __all__ y símbolos públicos top-level.
- comandos CLI declarados con add_parser.
- handlers CLI por funciones *_command.
- tests relacionados por heurística de naming/path.
```

La salida principal es un `ArchitectureMap` en memoria validado contra `SCHEMA-DEVPL-ARCHITECTURE-MAP-V1`. En esta fase `dependencies` y `hotspots` permanecen vacíos por diseño: `POST-H-005-C` materializará los `DependencyEdge` y `POST-H-005-D` calculará el scoring de hotspots.

## Restricciones del inventario AST

```text
- No importa módulos dinámicamente.
- No ejecuta pytest ni comandos del sistema.
- No genera dependencia en herramientas externas.
- No usa red ni APIs externas.
- No escribe fuentes.
- No activa remote execution, plugin execution ni connector write.
```

## Criterios PASS adicionales de POST-H-005-B

```text
PASS si architecture inventory devuelve ok=true.
PASS si cli.py aparece como is_cli_entrypoint=true.
PASS si se detectan comandos y handlers CLI por AST.
PASS si el payload generado valida contra ArchitectureMap.
PASS si el resumen conserva dry_run=true y network/API/mutations=false.
```

## Límites pendientes

```text
- DependencyEdge real: POST-H-005-C.
- fan-in/fan-out real: POST-H-005-C.
- Hotspot score: POST-H-005-D.
- Reporte final architecture_map.json/.md y quality-gate: POST-H-005-E.
```


## POST-H-005-C — Dependency graph baseline

`POST-H-005-C` adds a schema-backed package-level dependency graph built from Python AST imports. The graph enriches the ArchitectureMap with `DependencyEdge` records, package `direct_dependencies`, `fan_in`, `fan_out`, advisory boundary policy classification and sensitive dependency markers for remote/plugins/connectors.

This baseline remains `implemented-initial`: it is static, local-first and non-mutating. It does not enforce boundaries, move modules, calculate hotspot scores or generate the final architecture map report yet.



## POST-H-005-D — Hotspot analyzer baseline

`POST-H-005-D` adds an advisory hotspot ranking on top of the executable ArchitectureMap baseline. It consumes the AST inventory and dependency graph, then scores package/module subjects using normalized LOC, fan-in, fan-out, function count, CLI command count and criticality. Boundary policy signals from POST-H-005-C are retained as advisory metadata.

The analyzer emits a top 20 list and separates technical debt hotspots from core-domain hotspots through explicit metadata:

```text
technical_hotspot: pressure from LOC, CLI command concentration, fan-out, function density or boundary findings.
core_domain_hotspot: P0/P1 domain package that is strategically important and must be protected before refactor.
hotspot_kind: technical, core-domain or technical-and-core-domain.
```

This baseline remains non-enforcing. It does not refactor modules, execute tests, mutate sources or alter runtime boundaries. `POST-H-005-E` remains responsible for the final `architecture_map.json/.md`, ownership validation and any quality-gate decision.


## POST-H-005-E — Reporte final y ownership validation

`POST-H-005-E` materializa el reporte final ejecutable del hito. El comando `python -m devpilot_core architecture map --write-report --json` escribe un JSON crudo validable por schema y un Markdown humano:

```text
outputs/reports/architecture_map.json
outputs/reports/architecture_map.md
```

El reporte combina paquetes, módulos, dependencias, hotspots, ownership registry, ownership gaps y recomendaciones. La validación queda integrada como subgate `architecture-map` en `quality-gate hardening` e `industrial`.

El baseline sigue siendo advisory: las dependencias `forbidden`/`restricted`, los paquetes sin owner y otros gaps se exponen para revisión y planificación, pero no activan refactor automático ni enforcement blocking.
