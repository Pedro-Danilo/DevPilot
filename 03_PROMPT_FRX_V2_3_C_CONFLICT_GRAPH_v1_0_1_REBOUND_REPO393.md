---
doc_id: "03_PROMPT_FRX_V2_3_C_CONFLICT_GRAPH_V1_0_1"
title: "FRX-v2.3-C — Conflict graph and shadow parallel scheduler — implementation and Windows validation prompt — rebound repo393"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "approved_by_owner"
source_policy: "repo_DevPilot_Local_393_FRX_V2_3_B_ISOLATION_REGISTRY_WINDOWS_VALIDATED_CANDIDATE.zip"
source_repo: "repo_DevPilot_Local_393_FRX_V2_3_B_ISOLATION_REGISTRY_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "efbcfb72eebc52f0854141f6112f99c2c7c02624"
full_regression_policy: "no full regression"
parallel_workers: 0
---
# FRX-v2.3-C — Conflict graph and shadow parallel scheduler — Prompt

## 1. Misión

Construir conflict graph y shadow waves usando isolation B + duration estimates normalizados A. La ejecución paralela permanece deshabilitada.

## 2. Implementación

1. Conflict graph desde isolation domains/resource lock keys.
2. Unknown/unsafe siempre serial lane.
3. Resource locks son defensa adicional, no sustituto de clasificación.
4. Plan identity: collection SHA + isolation SHA + normalized duration registry SHA + serial baseline SHA.
5. Preview de worker slots=2, ejecución workers=0.
6. Calcular predicted makespan, serial fraction, lock contention y safe coverage ponderada por runtime.
7. Amdahl feasibility report con overhead explícito.
8. Comparar predicted parallel contra **normalized serial baseline**, no contra la full v2.2 contaminada. Mantener además total-improvement projection vs historical observed para reporting.

## 3. Validación

- conflict graph completeness;
- incompatible never same wave;
- unknown serial;
- deterministic planning;
- lock collision fixtures;
- predicted makespan sanity;
- scheduler execution disabled negative test;
- workers=0; full=0.

## 4. PASS

0 conflict violations; deterministic; unknown fallback serial; runtime-weighted safe coverage reproducible; feasibility report separa normalized serial vs historical observed; no worker real.

## 5. BLOCK

Unsafe/unknown en parallel wave; non-determinism; lock collision; worker real; speedup proyectado contra baseline contaminada; full ejecutada.

## 6. Salida

Autoriza FRX-v2.3-D solo si feasibility/ROI permite canary. Commit sugerido: `feat(frx-v2.3): add conflict-aware parallel shadow planner`.
