---
doc_id: "03_PROMPT_FRX_V2_3_C_PARALLEL_CANARY_V1_0_0"
title: "FRX-v2.3-C — Bounded parallel canary — implementation and Windows validation prompt"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "approved_by_owner"
source_policy: "successor-of-previous-micro-sprint/windows-validated-when-applicable"
full_regression_policy: "only-closing-micro-sprint-may-consume-one-logical-full"
---
# FRX-v2.3-C — Bounded parallel canary — Prompt

## 1. Misión

Implementar FRX-v2.3-C — Bounded parallel canary de forma acotada, verificable, resumible y sin ampliar el alcance de testing más allá de lo autorizado.

## 2. Fuente y precondiciones

Entrada: FRX-v2.3-B CLOSED/PASS con una población explícita PROVEN_PARALLEL_SAFE. Este sprint no consume la full.

Precondiciones transversales:
- Git worktree limpio semánticamente: staged diff vacío, unstaged diff vacío, untracked explícitamente clasificado;
- Project State y DocumentationDriftGate PASS;
- no runtime stores/caches en source candidate;
- no modificación manual de `.git`;
- historical evidence y repo386 permanecen inmutables;
- no API externa ni network requeridos para PASS.

## 3. Alcance

Incluye canary controlado workers=2. Excluye full y auto-escalado.

## 4. Implementación obligatoria

1. Crear worker runtime con subprocess argv tipado, `shell=False`.
2. Aislar temp dirs, pytest cache, output dirs, env whitelist y correlation/session ids por worker.
3. Process tree cleanup y watchdog por worker.
4. Ejecutar un mismo canary safe en modalidad secuencial y workers=2; como subset focal, no full.
5. Comparar exact nodeid outcomes, skips, logs y side-effect manifests.
6. Detectar orphan processes, file collisions, port conflicts y shared DB writes.
7. Fallo de un worker no cancela otros; accounting completion-first.
8. workers máximo=2.

### Diseño de estado y recuperación
- Cada operación mutante debe ser idempotente o transaccional.
- Receipts PASS terminales se reutilizan si commit/fingerprint coinciden.
- `INFRA_ABORT` permite reanudar únicamente trabajo no terminal.
- Un FAIL funcional no se oculta ni se transforma en infra failure.
- No usar hashes físicos CRLF/LF como precondición; usar Git objects, schemas y contenido semántico.

### Documentación incremental
Antes de cerrar el micro-sprint ejecutar `DocImpactPlanner` y reconciliar P0/P1 current-active. No se permite trasladar drift determinista a la full del backlog.

## 5. Pruebas y validación

- sequential canary vs parallel canary outcome parity;
- injected collision negative tests;
- orphan cleanup;
- timeout/resume;
- worker crash;
- output namespace isolation;
- resource lock contention;
- flake repeat bounded solo dentro del canary design, no rerun para esconder FAIL;
- full=0.

Reglas:
- completion-first: ejecutar todos los checks planificados salvo unsafe mutation;
- pruebas focales/impactadas únicamente, excepto la única full expresamente autorizada en el sprint de cierre;
- no full por “precaución”;
- no browser si runtime UI/API no cambia;
- comparar comportamiento, contratos y Git content, no representación física del archivo.

## 6. Evidencia obligatoria

- sequential/parallel canary receipts;
- outcome diff=0;
- collision audit;
- process cleanup audit;
- speedup canary;
- worker utilization.

Toda evidencia machine-readable debe registrar commit, timestamps, counts, PASS/BLOCK, S0/S1, `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed` y número de full runs consumidas.

## 7. Ingeniería del operador Windows

- Preferir un único operador Python resumible con subcomandos por fase de alto nivel, no docenas de scripts.
- PowerShell solo para invocar el operador y verificaciones externas inevitables; cada comando en una sola línea y con PASS verde/BLOCK rojo.
- API/UI foreground y tres consolas solo si este micro-sprint realmente cambia/valida browser runtime.
- No limpiar automáticamente cambios desconocidos. Reconocer estados survivores conocidos, respaldarlos y recuperar transaccionalmente.
- Packaging desde Git (`git archive`) después de validación; excluir outputs, caches, `.venv`, `.git`, runtime DB y secretos.
- Promoción Git posterior a PASS: preflight → fast-forward local → remote ancestry → push sin force → three-state review.

## 8. PASS

Outcome parity exacta; contamination=0; orphan=0; workers=2 bounded; canary speedup medido; unknown/conflicting remain serial.

## 9. BLOCK

Nueva flake; collision; output overwrite; orphan process; resource policy bypass; auto-escalado >2; full ejecutada.

## 10. Salida y autorización

Autoriza FRX-v2.3-D. Commit: `feat(frx-v2.3): validate two-worker safe parallel canary`.
