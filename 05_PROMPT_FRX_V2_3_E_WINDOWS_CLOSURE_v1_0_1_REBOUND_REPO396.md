---
doc_id: "05_PROMPT_FRX_V2_3_E_WINDOWS_CLOSURE_V1_0_1_REBOUND_REPO396"
title: "FRX-v2.3-E — Windows one-full safe-parallel closure — implementation and Windows validation prompt"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "approved_by_owner"
source_policy: "repo_DevPilot_Local_396_FRX_V2_3_D_BOUNDED_PARALLEL_CANARY_WINDOWS_VALIDATED_CANDIDATE.zip@8b0bc3517c79120eb5ebbaf00e57576d1292a34a"
full_regression_policy: "only micro-sprint authorized to consume one logical full v2.3"
max_workers: 2
---
# FRX-v2.3-E — Windows one-full safe-parallel closure — Prompt

## 0. Fuente de verdad actualizada

- source_repo: `repo_DevPilot_Local_396_FRX_V2_3_D_BOUNDED_PARALLEL_CANARY_WINDOWS_VALIDATED_CANDIDATE.zip`
- source_commit: `8b0bc3517c79120eb5ebbaf00e57576d1292a34a`
- FRX-v2.3-D: `CLOSED/PASS/WINDOWS-VALIDATED`

## 1. Misión

Ejecutar la única full v2.3 con safe bounded parallelism y cerrar la evolución sin confundir mejoras de de-dup/serial normalization con speedup paralelo.

## 2. Precondiciones

- A/B/C/D CLOSED/PASS;
- DocumentationDriftGate PASS;
- normalized serial baseline sellada;
- source guard bounded y duplicate aggregate gate PASS;
- isolation/conflict fingerprints sellados;
- canary workers=2 outcome parity PASS;
- feasibility report aún justifica consumir la full;
- full v2.3 consumida hasta ahora = 0.

## 3. Ejecución

1. Sellar collection + source/environment + isolation registry + duration registry + conflict graph + parallel plan.
2. Parallel-safe waves workers<=2; unsafe/unknown/conflicting serial.
3. Serial lane usa el coarsened manifest-based execution de A, no count50 legacy.
4. Completion-first global; FAIL funcional no stop-on-first-fail.
5. Per-worker live receipts; resume solo UNEXECUTED.
6. Global accounting exactamente una vez por nodeid.
7. `strong_fingerprint_fallbacks=0` esperado en hot path nominal; cualquier fallback queda visible.
8. Registrar wall-clock end-to-end, process count, node runtime, worker utilization, serial fraction, lock contention, startup/source-guard overhead, resumes y flake delta.
9. No segunda full. Correctives usan selective/composite recovery.
10. Packaging Git three-state y cierre documental.

## 4. Performance adjudication obligatoria

El reporte debe publicar tres métricas separadas:

- `total_improvement_vs_v2_2_observed`;
- `serial_normalization_improvement` atribuible a A;
- `incremental_parallel_improvement_vs_normalized_serial` atribuible a C/D/E.

No se permite usar las 10.27 h v2.2 como único denominador para habilitar parallel default.

Default enablement requiere Safety PASS + threshold owner sobre `incremental_parallel_improvement_vs_normalized_serial`. El threshold de referencia sigue siendo 30% solo si feasibility demuestra que es alcanzable y el owner no lo ha cambiado antes de la full.

## 5. PASS

100% accounting, conflicts=0, source drift=0, no new flakes, workers<=2, second_full=false, performance attribution completa. Si safety pasa pero incremental parallel speedup no alcanza threshold, `PASS/AVAILABLE-NOT-DEFAULT`.

## 6. BLOCK

Race/collision; unknown paralelo; fallback strong repetitivo; source drift; outcome mismatch; second full; comparison full adicional; speedup claim que mezcle ahorro A con paralelismo; baseline no sellada.

## 7. Evidencia

Sealed artifacts, per-wave/worker receipts, serial-lane receipts, accounting, conflict/lock audit, dual-baseline performance report, process/source-guard counters, candidate/evidence SHA/CRC y three-state Git.

## 8. Salida

Cierra FRX v2.3. Solo entonces autoriza reanudación funcional en DEVPL-GSDLC-08. Commit sugerido: `close(frx-v2.3): validate cost-normalized safe parallel full on Windows`.
