---
doc_id: "02_PROMPT_FRX_V2_3_B_ISOLATION_REGISTRY_V1_0_1"
title: "FRX-v2.3-B — Isolation contract registry — implementation and Windows validation prompt"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "approved_by_owner_rebound_repo392"
source_repo: "repo_DevPilot_Local_392_FRX_V2_3_A_COST_DEDUP_SERIAL_BASELINE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "e5b0d53b3e6d40dca334b9fe38f8d4f368ff035b"
source_policy: "successor-of-FRX-v2.3-A/windows-validated"
full_regression_policy: "no full regression"
parallel_workers: 0
---
# FRX-v2.3-B — Isolation contract registry — Prompt

## 1. Misión
Clasificar aislamiento y recursos compartidos sobre la suite ya de-duplicada por A. No ejecutar tests en paralelo.

## 2. Precondiciones
- FRX-v2.3-A `CLOSED/PASS/WINDOWS-VALIDATED` sobre repo392 y commit `e5b0d53b3e6d40dca334b9fe38f8d4f368ff035b`;
- normalized serial baseline disponible;
- aggregate duplication P0 cerrado;
- bounded Git source seal integrado;
- serial planner desacoplado del command-line limit;
- workers=0; full=0.

## 3. Implementación
1. `TestIsolationRegistry` default `UNCLASSIFIED`, `parallel_safe=false`, `explicit_review_required=true`.
2. Resource hints: fixed paths/outputs, SQLite/DB, Git/worktree, ports/server lifecycle, env/cwd, globals/singletons, subprocess trees, network, clock/time, caches y Windows named resources.
3. Static analyzer solo produce `suggested_hints`; nunca `parallel_safe=true` automático.
4. Safe requiere contrato/review explícito y evidencia focal.
5. Isolation domains y resource lock keys estables.
6. Shared mutable global state permanece serial salvo proof successor.
7. Registrar owner/reason/review timestamp.
8. Asociar runtime estimate normalizado; cuando exista evidencia successor de A, esta prevalece sobre duración histórica anterior.

## 4. Validación
- fixture por resource class;
- unknown remains false;
- suggestion cannot authorize;
- explicit review positive/negative;
- schema/semantic validation;
- runtime-weighted classification coverage report;
- collection identity exacta y sin duplicados;
- workers=0; full=0.

## 5. PASS/BLOCK
PASS: ningún test safe por inferencia accidental; safe con evidence/reviewer; unknown serial; drift P0/P1=0. BLOCK: duration/name implica safe, recurso no clasificado podría ir paralelo, worker>0 o full>0.

## 6. Operador/evidencia
Un único operador Python resumible de fase alta, sin browser. No repetir gates terminales. Comparar contenido semántico/Git y no representación LF/CRLF. Evidencia: registry, coverage ponderada por runtime, unknown/unsafe counts, resource hints, reviewer workflow, focal tests, `full_runs=0`, `workers=0`.

## 7. Salida
Autoriza FRX-v2.3-C — Conflict graph and parallel shadow scheduler. Commit sugerido: `feat(frx-v2.3): add explicit test isolation registry`.
