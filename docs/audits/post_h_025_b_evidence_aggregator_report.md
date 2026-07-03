---
doc_id: "POST-H-025-B-EVIDENCE-AGGREGATOR-REPORT"
title: "POST-H-025-B — Evidence aggregator read-only"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-03"
approval: "approved_by_owner"
created_by: "POST-H-025-B"
phase: "POST-FASE-H"
local_first: true
dry_run: true
read_only: true
---

# POST-H-025-B — Evidence aggregator read-only

## Resultado

POST-H-025-B queda implementado como `implemented-initial / evidence-aggregator-read-only`.

## Implementacion

Se agrega `ProductionReadyEvidenceAggregator` en `src/devpilot_core/industrial/production_ready.py`. El agregador carga el criteria JSON versionado, recorre el `evidence_map`, verifica la existencia de artefactos locales, parsea JSON cuando corresponde, detecta mismatch de `schema_id`, clasifica evidencias y produce un modelo intermedio.

El modelo intermedio incluye:

```text
- candidate_decision: PASS_CANDIDATE o BLOCK_CANDIDATE;
- production_ready_local_declared=false;
- score y minimum_score;
- resultados por hito;
- detalles por evidencia;
- gaps con severity block/warning/info;
- no-go gates;
- banderas safety local-first/read-only/no-network/no-mutations;
- limitaciones explicitas.
```

## Criterio industrial aplicado

El agregador es deliberadamente conservador. Un `PASS_CANDIDATE` no es una declaracion `production-ready-local`; solo indica que las evidencias requeridas mapeadas existen y no presentan fallos estructurales basicos. La decision formal PASS/BLOCK, escritura de reportes y salida CLI/API pertenecen a POST-H-025-C/E.

## Seguridad

POST-H-025-B no ejecuta comandos declarados en el evidence map, no llama red, no usa APIs externas, no habilita remote execution, no habilita connector write, no habilita plugin execution y no escribe archivos. Las evidencias faltantes se reportan como gaps sin mutar el repositorio.

## Limitaciones

Esta primera version no valida freshness/timestamps ni ejecuta validaciones CLI de cada evidencia. Tampoco inspecciona claims documentales; esa responsabilidad queda para POST-H-025-D. El reporte `outputs/reports/production_ready_local_report.json` no se genera en este micro-sprint.
