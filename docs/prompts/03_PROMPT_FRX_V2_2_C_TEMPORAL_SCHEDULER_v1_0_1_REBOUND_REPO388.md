---
doc_id: "03_PROMPT_FRX_V2_2_C_TEMPORAL_SCHEDULER_V1_0_1_REBOUND_REPO388"
title: "FRX-v2.2-C — Duration-balanced sequential scheduler — repo388 execution rebound"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "approved_by_owner"
source_repo: "repo_DevPilot_Local_388_FRX_V2_2_B_NODE_DURATION_REGISTRY_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "228d5dbfb19e10584ed00d616126fe34027d1ba8"
source_repo_sha256: "c81f3be309d0fa988372b4979b57cbc3575c966deee16d8fbea1d1b34a4c2f45"
source_role: "execution-authority/windows-validated-frx-v2.2-b-successor"
full_regression_policy: "only-FRX-v2.2-D-may-consume-one-logical-full"
---
# Execution rebound

This successor prompt preserves the approved v1.0.0 functional scope verbatim and rebinds execution authority to repo388 / Windows commit `228d5dbfb19e10584ed00d616126fe34027d1ba8`. Repo386/repo387 remain historical predecessor authorities.

# FRX-v2.2-C — Duration-balanced sequential scheduler — Prompt

## 1. Misión

Implementar FRX-v2.2-C — Duration-balanced sequential scheduler de forma acotada, verificable, resumible y sin ampliar el alcance de testing más allá de lo autorizado.

## 2. Fuente y precondiciones

Entrada: FRX-v2.2-B CLOSED/PASS con NodeDurationRegistry poblado y DocumentationDriftGate PASS.

Precondiciones transversales:
- Git worktree limpio semánticamente: staged diff vacío, unstaged diff vacío, untracked explícitamente clasificado;
- Project State y DocumentationDriftGate PASS;
- no runtime stores/caches en source candidate;
- no modificación manual de `.git`;
- historical evidence y repo386 permanecen inmutables;
- no API externa ni network requeridos para PASS.

## 3. Alcance

Incluye nuevo planning algorithm en shadow mode y canary focal. Sigue workers=1. Excluye full regression y paralelismo.

## 4. Implementación obligatoria

1. Implementar `TemporalShardPlanner` determinístico LPT/bin-packing.
2. Target inicial configurable `target_shard_seconds=300`; no convertirlo en constante contractual histórica.
3. Node estimado > target → slow singleton, no forzar a shard multi-node.
4. Preservar límites `max_nodeids` y `max_command_chars`; nunca generar un argv Windows fuera de límites.
5. Cold-start nodes se distribuyen con stable nodeid order + bounded count/chars.
6. Plan incluye estimated_seconds, confidence, known/unknown count, command chars y provenance del duration registry.
7. Mismo collection SHA/fingerprint que el planner base; 0 nodeids omitidos/duplicados.
8. `shadow compare` calcula max/p95/CV de plan histórico count-based vs temporal usando la misma collection y telemetry, sin ejecutar dos fulls.
9. Scheduler real permanece opt-in y sequential; no cambiar worker runtime.

### Diseño de estado y recuperación
- Cada operación mutante debe ser idempotente o transaccional.
- Receipts PASS terminales se reutilizan si commit/fingerprint coinciden.
- `INFRA_ABORT` permite reanudar únicamente trabajo no terminal.
- Un FAIL funcional no se oculta ni se transforma en infra failure.
- No usar hashes físicos CRLF/LF como precondición; usar Git objects, schemas y contenido semántico.

### Documentación incremental
Antes de cerrar el micro-sprint ejecutar `DocImpactPlanner` y reconciliar P0/P1 current-active. No se permite trasladar drift determinista a la full del backlog.

## 5. Pruebas y validación

- determinism 10 repeated plans;
- no duplicates/omissions;
- command chars/node count bounds;
- slow singleton;
- all-unknown cold start;
- mixed confidence;
- collection/fingerprint mismatch BLOCK;
- canary real focal con plan temporal y workers=1;
- predicted max/p95/CV comparison;
- DocumentationDriftGate PASS;
- full=0.

Reglas:
- completion-first: ejecutar todos los checks planificados salvo unsafe mutation;
- pruebas focales/impactadas únicamente, excepto la única full expresamente autorizada en el sprint de cierre;
- no full por “precaución”;
- no browser si runtime UI/API no cambia;
- comparar comportamiento, contratos y Git content, no representación física del archivo.

## 6. Evidencia obligatoria

- temporal plan sample;
- shadow comparison report;
- canary receipts/JUnit/logs;
- planner determinism report;
- command-length audit;
- test impact + documentation drift reports.

Toda evidencia machine-readable debe registrar commit, timestamps, counts, PASS/BLOCK, S0/S1, `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed` y número de full runs consumidas.

## 7. Ingeniería del operador Windows

- Preferir un único operador Python resumible con subcomandos por fase de alto nivel, no docenas de scripts.
- PowerShell solo para invocar el operador y verificaciones externas inevitables; cada comando en una sola línea y con PASS verde/BLOCK rojo.
- API/UI foreground y tres consolas solo si este micro-sprint realmente cambia/valida browser runtime.
- No limpiar automáticamente cambios desconocidos. Reconocer estados survivores conocidos, respaldarlos y recuperar transaccionalmente.
- Packaging desde Git (`git archive`) después de validación; excluir outputs, caches, `.venv`, `.git`, runtime DB y secretos.
- Promoción Git posterior a PASS: preflight → fast-forward local → remote ancestry → push sin force → three-state review.

## 8. PASS

Plan exacto y determinístico; coverage 100%; workers=1; predicted max shard y dispersion mejoran materialmente frente al count-based baseline o la ausencia de mejora queda demostrada y el algoritmo no se adopta por defecto todavía.

## 9. BLOCK

Omisión/duplicación; source/collection drift; nodeid suffix modificado; command bound excedido; cualquier worker paralelo; full ejecutada.

## 10. Salida y autorización

Autoriza FRX-v2.2-D Windows closure. Commit sugerido: `feat(frx-v2.2): add duration-balanced sequential shard planner`.
