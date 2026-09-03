---
doc_id: "04_PROMPT_FRX_V2_3_D_PARALLEL_CANARY_V1_0_0"
title: "FRX-v2.3-D — Bounded parallel canary — implementation and Windows validation prompt"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "approved_by_owner"
source_policy: "successor-of-FRX-v2.3-C/windows-validated"
full_regression_policy: "no full regression; same-subset sequential/parallel canary allowed"
max_workers: 2
---
# FRX-v2.3-D — Bounded parallel canary — Prompt

## 1. Misión

Probar workers=2 únicamente sobre un subset `PROVEN_PARALLEL_SAFE` y medir speedup incremental real sobre el mismo canary serial ya de-duplicado.

## 2. Precondiciones

- A/B/C CLOSED/PASS;
- no duplicate aggregate cost abierto;
- conflict graph deterministic;
- feasibility report indica valor suficiente para canary;
- no full consumida.

## 3. Implementación/ejecución

1. Seleccionar canary runtime-representative y isolation-diverse.
2. Ejecutar el mismo canary secuencial y luego paralelo workers=2; esto es focal, no full.
3. Namespaces separados por worker para temp/output.
4. Resource locks y conflict plan obligatorios.
5. Per-worker watchdog + live per-node terminal receipts.
6. Comparar outcomes, side effects, runtime artifacts y source state.
7. Medir end-to-end: process startup + coordinator + source guard + locks + node runtime.
8. Calcular incremental parallel speedup vs serial canary; no mezclar ahorro A.

## 4. PASS

Outcome parity exacta; source clean; conflicts=0; no leakage; safe classification validada; incremental speedup positivo y coherente con feasibility; workers<=2; full=0.

## 5. BLOCK

Flake/mismatch, race, shared-resource collision, source/runtime contamination, unknown paralelo, overhead paralelo anula beneficio sin adjudicación, full ejecutada.

## 6. Evidencia

Sequential canary receipt, parallel worker receipts, conflict/lock trace, wall-clock decomposition, outcome parity report, incremental speedup, full_runs=0.

## 7. Salida

Autoriza FRX-v2.3-E solo si safety PASS y feasibility actualizada continúa justificando la única full. Commit sugerido: `perf(frx-v2.3): validate bounded two-worker canary`.
