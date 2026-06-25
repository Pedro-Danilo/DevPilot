---
doc_id: "POST-H-005-A-AUDIT"
title: "POST-H-005-A — Modelos y schema de architecture map"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-24"
phase: "POST-FASE-H"
local_first: true
dry_run: true
approval: "internal"
---

# POST-H-005-A — Modelos y schema de architecture map

## Propósito

Implementar la base contractual de `POST-H-005 — Architecture map executable / dependency ownership` sin introducir inventario AST ni enforcement prematuro.

## Estado

Estado del micro-sprint: `implemented-initial`.

Estado del hito padre: `in-progress`.

## Alcance implementado

```text
- Paquete src/devpilot_core/architecture creado.
- Modelos ArchitectureMap, ArchitectureModule, ArchitecturePackage, DependencyEdge, Hotspot y OwnershipEntry.
- Schema docs/schemas/architecture_map.schema.json.
- Registro SCHEMA-DEVPL-ARCHITECTURE-MAP-V1 en schema_catalog.
- Registry inicial .devpilot/architecture/ownership_registry.json.
- Fixtures válidos e inválidos para validar el contrato.
- Pruebas focales de schema, modelo y ownership.
```

## Alcance no implementado

```text
- No inventory AST.
- No architecture dependencies CLI.
- No hotspot analyzer.
- No report builder final.
- No quality-gate subgate.
- No refactor ni movimiento de módulos.
```

## Funcionamiento

`POST-H-005-A` estabiliza el payload que usarán los siguientes micro-sprints. El reporte mínimo se valida con `schema validate --schema-id ArchitectureMap` y el registry de ownership declara propietarios, dominios, criticidad, riesgo, dependencias permitidas/restringidas/prohibidas y contratos de prueba asociados.

## Criterios PASS

```text
PASS si el schema valida tests/fixtures/architecture_map/valid_minimal_architecture_map.json.
PASS si el schema rechaza tests/fixtures/architecture_map/invalid_network_architecture_map.json.
PASS si ownership_registry contiene paquetes críticos iniciales.
PASS si schema list incluye ArchitectureMap.
```

## Criterios BLOCK

```text
BLOCK si el schema permite network/API/mutaciones.
BLOCK si falta ownership para cli/policy/schemas/agents/testing/quality/industrial.
BLOCK si se implementa inventario AST o CLI antes de POST-H-005-B.
BLOCK si se declara production-ready-local.
```

## Riesgos y límites

```text
- El ownership inicial es declarativo y puede requerir ajustes al aparecer métricas AST reales.
- No hay cálculo real de fan-in/fan-out todavía.
- No hay enforcement de boundaries todavía.
- No hay integración con quality-gate todavía.
```

## Comandos de validación

```powershell
python -m pytest tests/test_post_h_005_architecture_map.py tests/test_architecture_ownership_registry.py tests/test_schema_registry.py -q
python -m devpilot_core schema validate --schema-id ArchitectureMap --instance tests/fixtures/architecture_map/valid_minimal_architecture_map.json --json
python -m devpilot_core schema validate --schema-id ArchitectureMap --instance tests/fixtures/architecture_map/invalid_network_architecture_map.json --json
```
