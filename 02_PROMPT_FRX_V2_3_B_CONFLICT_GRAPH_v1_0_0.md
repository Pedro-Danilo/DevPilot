---
doc_id: "02_PROMPT_FRX_V2_3_B_CONFLICT_GRAPH_V1_0_0"
title: "FRX-v2.3-B — Conflict graph and shadow parallel scheduler — implementation and Windows validation prompt"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "approved_by_owner"
source_policy: "successor-of-previous-micro-sprint/windows-validated-when-applicable"
full_regression_policy: "only-closing-micro-sprint-may-consume-one-logical-full"
---
# FRX-v2.3-B — Conflict graph and shadow parallel scheduler — Prompt

## 1. Misión

Implementar FRX-v2.3-B — Conflict graph and shadow parallel scheduler de forma acotada, verificable, resumible y sin ampliar el alcance de testing más allá de lo autorizado.

## 2. Fuente y precondiciones

Entrada: FRX-v2.3-A CLOSED/PASS + duration registry v2.2.

Precondiciones transversales:
- Git worktree limpio semánticamente: staged diff vacío, unstaged diff vacío, untracked explícitamente clasificado;
- Project State y DocumentationDriftGate PASS;
- no runtime stores/caches en source candidate;
- no modificación manual de `.git`;
- historical evidence y repo386 permanecen inmutables;
- no API externa ni network requeridos para PASS.

## 3. Alcance

Incluye shadow scheduling de waves; workers reales continúan 0.

## 4. Implementación obligatoria

1. Crear conflict graph desde isolation domains/resource lock keys.
2. Integrar duration estimates para balancear cada wave sin violar conflictos.
3. UNCLASSIFIED/unsafe entra en serial lane.
4. Resource locks son defensa adicional; no sustituyen clasificación.
5. Plan determinístico: collection SHA + isolation registry SHA + duration registry SHA.
6. Modelar worker slots inicialmente 2 solo para preview; ejecución permanece disabled.
7. Calcular predicted parallel makespan, serial fraction, lock contention y safe coverage.
8. Verificar command/node bounds por worker.

### Diseño de estado y recuperación
- Cada operación mutante debe ser idempotente o transaccional.
- Receipts PASS terminales se reutilizan si commit/fingerprint coinciden.
- `INFRA_ABORT` permite reanudar únicamente trabajo no terminal.
- Un FAIL funcional no se oculta ni se transforma en infra failure.
- No usar hashes físicos CRLF/LF como precondición; usar Git objects, schemas y contenido semántico.

### Documentación incremental
Antes de cerrar el micro-sprint ejecutar `DocImpactPlanner` y reconciliar P0/P1 current-active. No se permite trasladar drift determinista a la full del backlog.

## 5. Pruebas y validación

- conflict graph completeness;
- incompatible never same wave;
- unknown serial;
- deterministic planning;
- lock key collision fixtures;
- predicted makespan sanity;
- scheduler disabled execution negative test;
- full=0.

Reglas:
- completion-first: ejecutar todos los checks planificados salvo unsafe mutation;
- pruebas focales/impactadas únicamente, excepto la única full expresamente autorizada en el sprint de cierre;
- no full por “precaución”;
- no browser si runtime UI/API no cambia;
- comparar comportamiento, contratos y Git content, no representación física del archivo.

## 6. Evidencia obligatoria

- conflict graph report;
- shadow parallel plan;
- predicted speedup/serial fraction;
- lock contention projection;
- negative execution receipt.

Toda evidencia machine-readable debe registrar commit, timestamps, counts, PASS/BLOCK, S0/S1, `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed` y número de full runs consumidas.

## 7. Ingeniería del operador Windows

- Preferir un único operador Python resumible con subcomandos por fase de alto nivel, no docenas de scripts.
- PowerShell solo para invocar el operador y verificaciones externas inevitables; cada comando en una sola línea y con PASS verde/BLOCK rojo.
- API/UI foreground y tres consolas solo si este micro-sprint realmente cambia/valida browser runtime.
- No limpiar automáticamente cambios desconocidos. Reconocer estados survivores conocidos, respaldarlos y recuperar transaccionalmente.
- Packaging desde Git (`git archive`) después de validación; excluir outputs, caches, `.venv`, `.git`, runtime DB y secretos.
- Promoción Git posterior a PASS: preflight → fast-forward local → remote ancestry → push sin force → three-state review.

## 8. PASS

0 conflict violations; plan determinístico; execution disabled; unknown safe fallback; predicted metrics reproducibles.

## 9. BLOCK

Cualquier unsafe/unknown en parallel wave; non-deterministic plan; resource lock name collision; worker real iniciado.

## 10. Salida y autorización

Autoriza FRX-v2.3-C. Commit: `feat(frx-v2.3): add conflict-aware parallel shadow scheduler`.
