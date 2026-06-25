---
title: "POST-H-005-D — Architecture hotspot analyzer report"
doc_id: "POST-H-005-D-AUDIT"
version: "1.0.0"
status: "approved"
approval: "internal"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
sprint: "POST-H-005-D"
local_first: true
dry_run: true
---

# POST-H-005-D — Hotspot analyzer

## Propósito

Implementar una primera versión ejecutable del analizador de hotspots arquitectónicos de DevPilot usando únicamente la evidencia local generada por `POST-H-005-B` y `POST-H-005-C`: inventario AST, grafo de dependencias paquete→paquete, fan-in/fan-out, ownership y señales advisory de boundaries.

## Estado

`implemented-initial / advisory hotspot ranking`.

## Alcance implementado

```text
- Builder `ArchitectureHotspotsBuilder`.
- CLI `python -m devpilot_core architecture hotspots --json`.
- Reutilización del grafo `ArchitectureDependenciesBuilder` sin ejecutar módulos del proyecto.
- Scoring por LOC, fan-in, fan-out, funciones, comandos CLI y criticality.
- Señal advisory adicional por dependencias forbidden/restricted/sensitive ya detectadas por POST-H-005-C.
- Top 20 hotspots reproducible.
- Diferenciación explícita entre `technical_hotspot` y `core_domain_hotspot` en metadata.
- Recomendaciones por hotspot para POST-H-006/007 y hardening posterior.
- Validación del payload contra `SCHEMA-DEVPL-ARCHITECTURE-MAP-V1`.
```

## Fuera de alcance explícito

```text
- No refactoriza CLI ni mueve módulos.
- No cambia ApplicationService ni boundaries runtime.
- No ejecuta pytest desde el analizador.
- No convierte hotspots en blockers de quality-gate.
- No genera `architecture_map.json/.md` final; queda para POST-H-005-E.
- No habilita remote execution, connector write ni plugin execution.
```

## Funcionamiento técnico

El builder ejecuta primero `ArchitectureDependenciesBuilder`, que a su vez reutiliza el inventario AST. Con ese payload calcula candidatos de hotspot a nivel `package` y `module`.

La fórmula v1 es advisory y normalizada por tipo de sujeto:

```text
score = LOC + fan-in + fan-out + functions + CLI commands + criticality + policy_signal

Pesos base:
- LOC: 35
- fan-in: 15
- fan-out: 15
- functions: 15
- CLI commands: 10
- criticality: hasta 10
- policy_signal: hasta 8, derivado de forbidden/restricted/sensitive edges
```

La clasificación se conserva en metadata:

```text
technical_hotspot=true cuando hay presión técnica: CLI monolítico, alto LOC, alta densidad funcional, alto fan-out o boundary findings.
core_domain_hotspot=true cuando el dominio y criticality indican que el componente es estratégico y debe protegerse antes de refactor.
hotspot_kind puede ser technical, core-domain o technical-and-core-domain.
```

## Criterios PASS

```text
PASS si `architecture hotspots --json` devuelve ok=true.
PASS si el top 20 contiene `devpilot_core.cli` o `src/devpilot_core/cli.py` como hotspot.
PASS si existen hotspots técnicos y core-domain diferenciados.
PASS si cada hotspot incluye reasons, recommendations y raw_metrics.
PASS si el payload generado valida contra `ArchitectureMap`.
PASS si safety conserva dry_run=true y network/API/mutations=false.
```

## Criterios BLOCK

```text
BLOCK si el comando importa módulos del proyecto dinámicamente.
BLOCK si ejecuta pruebas, subprocesses, red o APIs externas.
BLOCK si muta fuentes o cambia boundaries runtime.
BLOCK si omite cli.py como hotspot.
BLOCK si no emite recomendaciones accionables por hotspot.
BLOCK si no valida el payload contra el schema ArchitectureMap.
```

## Riesgos y limitaciones

```text
- El scoring v1 es heurístico y advisory; no debe usarse como único criterio de refactor.
- El cálculo no mide complejidad ciclomática ni call graph.
- La cobertura de tests se usa como metadata aproximada; no se ejecutan pruebas desde el analizador.
- Las señales forbidden/restricted/sensitive dependen de la calidad del ownership registry v1.
- La integración con quality-gate y reporte final queda diferida a POST-H-005-E.
```

## Comandos de validación

```powershell
$env:PYTHONPATH="src"

python -m pytest tests/test_architecture_hotspots.py tests/test_architecture_dependencies.py tests/test_architecture_inventory.py tests/test_post_h_005_architecture_map.py tests/test_architecture_ownership_registry.py tests/test_schema_registry.py -q
python -m devpilot_core architecture hotspots --json
python -m devpilot_core validate docs --json
python -m devpilot_core project-state validate --json
python -m devpilot_core quality-gate run --profile hardening --json
```
