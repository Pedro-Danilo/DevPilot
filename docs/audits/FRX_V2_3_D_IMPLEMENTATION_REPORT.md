---
doc_id: "FRX-V2-3-D-IMPLEMENTATION-REPORT"
title: "FRX-v2.3-D — Bounded parallel canary — implementation report"
status: "implemented/windows-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "local-focal-pass/windows-canary-required"
---
# FRX-v2.3-D — Implementation report

## Objetivo

Validar con workers=2 un subset pequeño y runtime-representative que ya fue promovido por BR a `PROVEN_PARALLEL_SAFE`, comparando exactamente el mismo canary serial y paralelo sobre el código de-duplicado de v2.3-A.

## Capacidades implementadas

- `BoundedParallelCanaryRunner`: coordinador acotado sin scheduler genérico.
- Canary manifest sellado con exactamente dos nodeids, dos contratos BR distintos y `max_workers=2`.
- Fresh Git clone por job y namespace temporal por worker.
- Resource lock table determinística y conflict-plan obligatorio.
- Live terminal receipts mediante el plugin de full-regression ya existente.
- Per-worker watchdog y proceso-tree kill en timeout.
- Outcome parity, artifact-shape parity, source guards y secret leakage checks.
- Medición end-to-end serial/paralela e incremental speedup sin atribuir a D el ahorro de A.
- CLI `tests parallel-canary` en preview por defecto y `--execute` explícito.

## Selección del canary

1. `LOCAL_CLONE_PER_WORKER_V1`: `test_post_h_020_d_compliance_mapping_quality_gate_passes` — estimación BR 11.326610 s.
2. `READ_ONLY_REPO_V1`: `test_post_h_018_e_connector_sandbox_quality_gate_passes_without_network_or_write` — estimación BR 15.513317 s.

Los dos nodeids están `PROVEN_PARALLEL_SAFE` en repo395, poseen evidence IDs BR y no presentan arista de conflicto.

## Validación local

- contrato focal D: `10/10 PASS`;
- preview: PASS/PREVIEW, 2 jobs, workers=2, full=0, conflicts=0;
- ejecución diagnóstica local de los dos modos: serial 32.828994 s; paralelo 17.936076 s; `2/2 PASS` en ambos modos; `max_workers_observed=2` en paralelo; reducción observada aproximada 45.36%.

La medición local anterior es **referencial** y no sustituye Windows. Hubo corridas diagnósticas en el contenedor donde procesos pytest terminaron sus artefactos pero el entorno de ejecución externo suspendió/retuvo el coordinator. Por ello el bundle Windows incorpora watchdog externo de process-tree además del watchdog interno. La autoridad de cierre será exclusivamente la ejecución Windows.

## Riesgos y limitaciones

- Primera versión de canary real: no constituye scheduler de producción.
- Dos nodeids no prueban que todos los 112 candidatos puedan compartir una misma wave; E debe respetar conflict graph y lane serial.
- El beneficio del canary no garantiza el speedup de la full completa.
- Windows puede adjudicar BLOCK por timeout, flake, mismatch, contaminación o speedup no positivo.
- Paralelismo por defecto permanece deshabilitado hasta una decisión posterior a E.

## Criterios PASS/BLOCK

PASS Windows requiere outcome parity, source clean, artifact parity, conflicts=0, leakage=false, workers<=2, full=0 y speedup incremental >0.

Cualquier violación anterior produce BLOCK y **no autoriza FRX-v2.3-E**.
