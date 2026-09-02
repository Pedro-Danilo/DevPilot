---
doc_id: "04_PROMPT_FRX_V2_3_D_WINDOWS_CLOSURE_V1_0_0"
title: "FRX-v2.3-D — Windows one-full safe-parallel closure — implementation and Windows validation prompt"
status: "superseded"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "approved_by_owner"
superseded_by: "05_PROMPT_FRX_V2_3_E_WINDOWS_CLOSURE_v1_0_0.md"
source_policy: "successor-of-previous-micro-sprint/windows-validated-when-applicable"
full_regression_policy: "only-closing-micro-sprint-may-consume-one-logical-full"
---
# FRX-v2.3-D — Windows one-full safe-parallel closure — Prompt

## 1. Misión

Implementar FRX-v2.3-D — Windows one-full safe-parallel closure de forma acotada, verificable, resumible y sin ampliar el alcance de testing más allá de lo autorizado.

## 2. Fuente y precondiciones

Entrada: v2.3-C CLOSED/PASS y canary workers=2 sin contaminación. Esta es la única full v2.3.

Precondiciones transversales:
- Git worktree limpio semánticamente: staged diff vacío, unstaged diff vacío, untracked explícitamente clasificado;
- Project State y DocumentationDriftGate PASS;
- no runtime stores/caches en source candidate;
- no modificación manual de `.git`;
- historical evidence y repo386 permanecen inmutables;
- no API externa ni network requeridos para PASS.

## 3. Alcance

Incluye una full Windows con workers=2 máximo inicial, conflict-aware waves y serial fallback. No ejecutar full secuencial de comparación; usar v2.2 Windows full como baseline.

## 4. Implementación obligatoria

1. Pre-full strict gates incluyendo DocumentationDriftGate=PASS.
2. Sellar collection, isolation registry, duration registry, conflict graph y parallel plan fingerprints.
3. Ejecutar parallel-safe waves con workers<=2; unsafe/unknown/conflicting serial.
4. Completion-first global; worker FAIL no aborta otros workers ni futuras waves ordinarias.
5. Per-worker watchdog/receipt; resume solo nodeids no terminales.
6. Global accounting deduplica nodeids exactamente una vez.
7. Registrar wall-clock, node runtime, worker utilization, safe coverage, serial fraction, lock contention, infra aborts, resume cost y flake delta.
8. Adjudicar default enablement solo si safety PASS y speedup >=30% frente a v2.2, salvo umbral owner explícitamente actualizado antes de la full.
9. No segunda full. Correctives posteriores usan selective bounded recovery.
10. Packaging/Git three-state y documentación final.

### Diseño de estado y recuperación
- Cada operación mutante debe ser idempotente o transaccional.
- Receipts PASS terminales se reutilizan si commit/fingerprint coinciden.
- `INFRA_ABORT` permite reanudar únicamente trabajo no terminal.
- Un FAIL funcional no se oculta ni se transforma en infra failure.
- No usar hashes físicos CRLF/LF como precondición; usar Git objects, schemas y contenido semántico.

### Documentación incremental
Antes de cerrar el micro-sprint ejecutar `DocImpactPlanner` y reconciliar P0/P1 current-active. No se permite trasladar drift determinista a la full del backlog.

## 5. Pruebas y validación

Exactamente una logical full v2.3. Post-finalize focal docs/state only. Browser solo si se modificó UI/API, lo cual debe evitarse.

Reglas:
- completion-first: ejecutar todos los checks planificados salvo unsafe mutation;
- pruebas focales/impactadas únicamente, excepto la única full expresamente autorizada en el sprint de cierre;
- no full por “precaución”;
- no browser si runtime UI/API no cambia;
- comparar comportamiento, contratos y Git content, no representación física del archivo.

## 6. Evidencia obligatoria

- sealed full artifacts;
- per-worker/per-wave receipts;
- conflict/lock audit;
- accounting report;
- performance report vs v2.2;
- flake delta;
- candidate/evidence SHA/CRC;
- three-state Git.

Toda evidencia machine-readable debe registrar commit, timestamps, counts, PASS/BLOCK, S0/S1, `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed` y número de full runs consumidas.

## 7. Ingeniería del operador Windows

- Preferir un único operador Python resumible con subcomandos por fase de alto nivel, no docenas de scripts.
- PowerShell solo para invocar el operador y verificaciones externas inevitables; cada comando en una sola línea y con PASS verde/BLOCK rojo.
- API/UI foreground y tres consolas solo si este micro-sprint realmente cambia/valida browser runtime.
- No limpiar automáticamente cambios desconocidos. Reconocer estados survivores conocidos, respaldarlos y recuperar transaccionalmente.
- Packaging desde Git (`git archive`) después de validación; excluir outputs, caches, `.venv`, `.git`, runtime DB y secretos.
- Promoción Git posterior a PASS: preflight → fast-forward local → remote ancestry → push sin force → three-state review.

## 8. PASS

Safety PASS, 100% accounting, conflicts=0, source drift=0, second_full=false. Default parallel enablement requiere >=30% wall-clock improvement o threshold owner previamente documentado. Si safety pasa y performance no, cerrar `PASS/AVAILABLE-NOT-DEFAULT` y no declarar resuelto el costo.

## 9. BLOCK

Race/collision, outcome mismatch, flake delta, unclassified node paralelo, worker >2 sin evidence, second full, comparison full adicional, speedup claim sin baseline.

## 10. Salida y autorización

Cierra FRX v2.3. Si v2.3 CLOSED/PASS, autoriza reanudación funcional en DEVPL-GSDLC-08. Commit: `close(frx-v2.3): validate bounded safe parallel full regression on Windows`.

## 11. Corrective go/no-go before the single v2.3 full — 2026-09-02

La full v2.3-D solo puede consumirse si A/B/C están CLOSED/PASS, el source-guard corrective de v2.2-D sigue integrado, DocumentationDriftGate PASS y el feasibility report demuestra que el target owner es teóricamente alcanzable con workers=2. La comparación usa wall-clock v2.2 reconciliado end-to-end; queda prohibido usar como baseline la suma incompleta de `duration_seconds` de receipts del intento v2.2-D. Si feasibility no alcanza el target, elevar adjudicación al owner y conservar `AVAILABLE-NOT-DEFAULT` sin gastar una full únicamente para confirmar ese límite matemático.
