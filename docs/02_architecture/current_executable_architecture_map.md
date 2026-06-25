---
doc_id: "POST-H-005-A-ARCHITECTURE-MAP-DESIGN"
title: "POST-H-005-A — Modelo ejecutable de architecture map"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-24"
phase: "POST-FASE-H"
local_first: true
dry_run: true
approval: "internal"
---

# POST-H-005-A — Modelo ejecutable de architecture map

## Propósito

`POST-H-005-A` inicia `POST-H-005 — Architecture map executable / dependency ownership` creando el contrato estructural para un mapa arquitectónico ejecutable, reproducible y gobernado. El objetivo de esta primera entrega es estabilizar el payload antes de implementar inventario AST, análisis de dependencias, scoring de hotspots o enforcement de boundaries.

## Estado

Estado: `implemented-initial / schema-only`.

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
