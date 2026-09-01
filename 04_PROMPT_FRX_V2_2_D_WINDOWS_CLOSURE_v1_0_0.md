---
doc_id: "04_PROMPT_FRX_V2_2_D_WINDOWS_CLOSURE_V1_0_0"
title: "FRX-v2.2-D — Windows one-full benchmark and closure — implementation and Windows validation prompt"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "approved_by_owner"
source_policy: "successor-of-previous-micro-sprint/windows-validated-when-applicable"
full_regression_policy: "only-closing-micro-sprint-may-consume-one-logical-full"
---
# FRX-v2.2-D — Windows one-full benchmark and closure — Prompt

## 1. Misión

Implementar FRX-v2.2-D — Windows one-full benchmark and closure de forma acotada, verificable, resumible y sin ampliar el alcance de testing más allá de lo autorizado.

## 2. Fuente y precondiciones

Entrada: FRX-v2.2-C CLOSED/PASS. Esta es la única fase autorizada a consumir la logical full de v2.2.

Precondiciones transversales:
- Git worktree limpio semánticamente: staged diff vacío, unstaged diff vacío, untracked explícitamente clasificado;
- Project State y DocumentationDriftGate PASS;
- no runtime stores/caches en source candidate;
- no modificación manual de `.git`;
- historical evidence y repo386 permanecen inmutables;
- no API externa ni network requeridos para PASS.

## 3. Alcance

Incluye Windows benchmark, adjudicación, adopción y packaging. No incluye paralelismo; workers=1. No repetir el runner antiguo como full comparativa: baseline es la evidencia 07-E ya sellada.

## 4. Implementación obligatoria

1. Pre-full: DocumentationDriftGate, Contract Reconciliation Sweep, Project State, Docs Governance, TCR v1/v2 y source/environment fingerprint.
2. Sellar collection + temporal plan + marker `attempt=1,max_attempts=1`.
3. Ejecutar todos los shards secuencialmente completion-first.
4. FAIL/ERROR funcional no detiene shards restantes.
5. INFRA_ABORT permite resume solo de nodeids no terminales bajo mismo fingerprint.
6. Registrar process startup/collection overhead, node runtime, shard wall-clock, max/p95/CV, command chars, resumes.
7. Adjudicar PASS solo con 100% terminal accounting y cero source drift.
8. No iniciar segunda full tras corrective: usar selective/composite recovery siguiendo la política ya aprendida en GSDLC-07-E.
9. Packaging limpio, Git three-state y cierre documental.

### Diseño de estado y recuperación
- Cada operación mutante debe ser idempotente o transaccional.
- Receipts PASS terminales se reutilizan si commit/fingerprint coinciden.
- `INFRA_ABORT` permite reanudar únicamente trabajo no terminal.
- Un FAIL funcional no se oculta ni se transforma en infra failure.
- No usar hashes físicos CRLF/LF como precondición; usar Git objects, schemas y contenido semántico.

### Documentación incremental
Antes de cerrar el micro-sprint ejecutar `DocImpactPlanner` y reconciliar P0/P1 current-active. No se permite trasladar drift determinista a la full del backlog.

## 5. Pruebas y validación

Una única logical full. Además, focal validation de scheduler/registry y post-finalize Project State/Docs. No browser salvo que runtime UI/API haya cambiado, lo cual este backlog debe evitar.

Reglas:
- completion-first: ejecutar todos los checks planificados salvo unsafe mutation;
- pruebas focales/impactadas únicamente, excepto la única full expresamente autorizada en el sprint de cierre;
- no full por “precaución”;
- no browser si runtime UI/API no cambia;
- comparar comportamiento, contratos y Git content, no representación física del archivo.

## 6. Evidencia obligatoria

- full session marker/collection/plan;
- per-shard JUnit/log/receipt;
- aggregate/adjudication;
- performance comparison contra 07-E baseline;
- DocumentationDriftGate pre/post;
- candidate/evidence SHA/CRC;
- three-state Git receipt.

Toda evidencia machine-readable debe registrar commit, timestamps, counts, PASS/BLOCK, S0/S1, `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed` y número de full runs consumidas.

## 7. Ingeniería del operador Windows

- Preferir un único operador Python resumible con subcomandos por fase de alto nivel, no docenas de scripts.
- PowerShell solo para invocar el operador y verificaciones externas inevitables; cada comando en una sola línea y con PASS verde/BLOCK rojo.
- API/UI foreground y tres consolas solo si este micro-sprint realmente cambia/valida browser runtime.
- No limpiar automáticamente cambios desconocidos. Reconocer estados survivores conocidos, respaldarlos y recuperar transaccionalmente.
- Packaging desde Git (`git archive`) después de validación; excluir outputs, caches, `.venv`, `.git`, runtime DB y secretos.
- Promoción Git posterior a PASS: preflight → fast-forward local → remote ancestry → push sin force → three-state review.

## 8. PASS

100% terminal accounting; second_full=false; drift documental descubierto durante full=0; scheduler temporal correcto. Adopción: `PASS/ENABLED` si mejora real justifica default, o `PASS/AVAILABLE-NOT-DEFAULT` si correctitud pasa pero performance no alcanza threshold owner. La métrica no puede maquillarse.

## 9. BLOCK

Segunda full; drift P0/P1 en marker time; source/environment drift no adjudicado; unknown coverage; stop-on-first-fail; browser repetido sin cambio runtime; claims de speedup sin medición.

## 10. Salida y autorización

Cierra FRX v2.2 y autoriza FRX-v2.3-A. Commit sugerido: `close(frx-v2.2): validate temporal full-regression scheduling on Windows`.
