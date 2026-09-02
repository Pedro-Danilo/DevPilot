---
doc_id: "01_PROMPT_FRX_V2_3_A_ISOLATION_REGISTRY_V1_0_0"
title: "FRX-v2.3-A — Isolation contract registry — implementation and Windows validation prompt"
status: "superseded"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "approved_by_owner"
superseded_by: "02_PROMPT_FRX_V2_3_B_ISOLATION_REGISTRY_v1_0_1_REBOUND_REPO392.md"
source_policy: "successor-of-previous-micro-sprint/windows-validated-when-applicable"
full_regression_policy: "only-closing-micro-sprint-may-consume-one-logical-full"
---
# FRX-v2.3-A — Isolation contract registry — Prompt

## 1. Misión

Implementar FRX-v2.3-A — Isolation contract registry de forma acotada, verificable, resumible y sin ampliar el alcance de testing más allá de lo autorizado.

## 2. Fuente y precondiciones

Entrada: FRX v2.2 CLOSED/PASS y successor Windows-validado. workers=0 al inicio.

Precondiciones transversales:
- Git worktree limpio semánticamente: staged diff vacío, unstaged diff vacío, untracked explícitamente clasificado;
- Project State y DocumentationDriftGate PASS;
- no runtime stores/caches en source candidate;
- no modificación manual de `.git`;
- historical evidence y repo386 permanecen inmutables;
- no API externa ni network requeridos para PASS.

## 3. Alcance

Incluye clasificación de aislamiento y recursos compartidos. Excluye ejecutar tests en paralelo.

## 4. Implementación obligatoria

1. Implementar `TestIsolationRegistry` con default `UNCLASSIFIED`, `parallel_safe=false`, `explicit_review_required=true`.
2. Modelar resource hints: fixed paths/outputs, SQLite/DB, Git/worktree, ports/server lifecycle, env/cwd, globals/singletons, subprocess trees, network, clock/time, caches y Windows named resources.
3. Static analyzer puede producir `suggested_hints`, nunca `parallel_safe=true` automáticamente.
4. Parallel-safe requiere contrato/review explícito y evidencia focal.
5. Introducir isolation domains y resource lock keys estables.
6. Tests históricos con shared mutable global state permanecen serial salvo proof successor.
7. Documentar razones de clasificación y owner/review timestamp.

### Diseño de estado y recuperación
- Cada operación mutante debe ser idempotente o transaccional.
- Receipts PASS terminales se reutilizan si commit/fingerprint coinciden.
- `INFRA_ABORT` permite reanudar únicamente trabajo no terminal.
- Un FAIL funcional no se oculta ni se transforma en infra failure.
- No usar hashes físicos CRLF/LF como precondición; usar Git objects, schemas y contenido semántico.

### Documentación incremental
Antes de cerrar el micro-sprint ejecutar `DocImpactPlanner` y reconciliar P0/P1 current-active. No se permite trasladar drift determinista a la full del backlog.

## 5. Pruebas y validación

- fixtures para cada shared resource class;
- unknown remains false;
- static suggestion cannot authorize;
- explicit review positive/negative;
- registry schema/semantic validation;
- doc-impact and drift gate;
- workers=0; full=0.

Reglas:
- completion-first: ejecutar todos los checks planificados salvo unsafe mutation;
- pruebas focales/impactadas únicamente, excepto la única full expresamente autorizada en el sprint de cierre;
- no full por “precaución”;
- no browser si runtime UI/API no cambia;
- comparar comportamiento, contratos y Git content, no representación física del archivo.

## 6. Evidencia obligatoria

- isolation registry;
- classification coverage report;
- unknown/unsafe counts;
- resource hint findings;
- reviewer decisions;
- focal tests.

Toda evidencia machine-readable debe registrar commit, timestamps, counts, PASS/BLOCK, S0/S1, `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed` y número de full runs consumidas.

## 7. Ingeniería del operador Windows

- Preferir un único operador Python resumible con subcomandos por fase de alto nivel, no docenas de scripts.
- PowerShell solo para invocar el operador y verificaciones externas inevitables; cada comando en una sola línea y con PASS verde/BLOCK rojo.
- API/UI foreground y tres consolas solo si este micro-sprint realmente cambia/valida browser runtime.
- No limpiar automáticamente cambios desconocidos. Reconocer estados survivores conocidos, respaldarlos y recuperar transaccionalmente.
- Packaging desde Git (`git archive`) después de validación; excluir outputs, caches, `.venv`, `.git`, runtime DB y secretos.
- Promoción Git posterior a PASS: preflight → fast-forward local → remote ancestry → push sin force → three-state review.

## 8. PASS

No test queda parallel-safe por inferencia accidental; todos los safe tienen evidence/reviewer; unknowns preservan fallback serial; drift P0/P1=0.

## 9. BLOCK

Duration/name implica safe; recurso compartido no clasificado se ejecutaría paralelo; worker >0; full ejecutada.

## 10. Salida y autorización

Autoriza FRX-v2.3-B. Commit: `feat(frx-v2.3): add explicit test isolation registry`.

## 11. Corrective prerequisite inherited from FRX-v2.2-D — 2026-09-02

Antes de implementar A debe verificarse que FRX-v2.2-D cerró por composite recovery sin segunda full y que el bounded Git-semantic source guard/end-to-end accounting de `ADR-FRX-001` está integrado. La clasificación de aislamiento no puede usarse para ocultar overhead de orquestación preexistente. A debe preservar `workers=0`, full=0 y registrar desde el inicio la duración histórica asociada a cada nodeid para permitir coverage ponderada por runtime en B.
