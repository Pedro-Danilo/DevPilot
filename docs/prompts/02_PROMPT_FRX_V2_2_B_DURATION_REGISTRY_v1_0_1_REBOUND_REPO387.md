---
doc_id: "02_PROMPT_FRX_V2_2_B_DURATION_REGISTRY_V1_0_1_REBOUND_REPO387"
title: "FRX-v2.2-B — NodeDurationRegistry and temporal estimator — implementation and Windows validation prompt"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "approved_by_owner"
source_policy: "successor-of-previous-micro-sprint/windows-validated-when-applicable"
full_regression_policy: "only-closing-micro-sprint-may-consume-one-logical-full"
---
# FRX-v2.2-B — NodeDurationRegistry and temporal estimator — Prompt

## 1. Misión

Implementar FRX-v2.2-B — NodeDurationRegistry and temporal estimator de forma acotada, verificable, resumible y sin ampliar el alcance de testing más allá de lo autorizado.

## 2. Fuente y precondiciones

Entrada: repo_DevPilot_Local_387_FRX_V2_2_A_DOCUMENTATION_CONSISTENCY_WINDOWS_VALIDATED_CANDIDATE.zip, commit Windows 9ae471381a081005e2f282f6dabbb6b10607590f, FRX-v2.2-A CLOSED/PASS. Telemetría inicial autoritativa: `DEVPL_GSDLC_07_E_FRX_V2_2_TEMPORAL_HANDOFF.json`, 2.805 muestras, ~12.952,888 s acumulados, median ~0,022 s, p95 ~10,65 s, max ~774,74 s.

Precondiciones transversales:
- Git worktree limpio semánticamente: staged diff vacío, unstaged diff vacío, untracked explícitamente clasificado;
- Project State y DocumentationDriftGate PASS;
- no runtime stores/caches en source candidate;
- no modificación manual de `.git`;
- historical evidence, repo386 y repo387 Windows-validado permanecen inmutables;
- no API externa ni network requeridos para PASS.

## 3. Alcance

Incluye ingestion, normalización, confidence y estimator temporal. Excluye cambiar el shard planner vigente, habilitar scheduler v2.2 o cualquier paralelismo.

## 4. Implementación obligatoria

1. Implementar `NodeDurationRegistry` versionado/configurable, no runtime output opaco.
2. Clave lógica: pytest nodeid completo preservando suffix después de `::` byte-for-byte + environment fingerprint compatible.
3. Guardar sample_count, median, p95, robust_estimate (EWMA o alternativa justificada), min/max, last_seen, cold/warm classification cuando exista evidencia.
4. Separar muestras por environment/toolchain fingerprint para no mezclar duraciones incompatibles.
5. Ingestion idempotente por receipt hash/source receipt; duplicados no duplican estadística.
6. Corrupt/negative duration → reject finding, nunca valor silencioso.
7. Cold-start sin historia → explicit unknown estimate y fallback estable; no inventar velocidad.
8. CLI/API interna de `duration-registry ingest|status|estimate|preview` o equivalente typed, sin ejecución de tests.
9. Documentar política de aging: historia vieja pierde peso, pero no se borra evidencia sellada.

### Diseño de estado y recuperación
- Cada operación mutante debe ser idempotente o transaccional.
- Receipts PASS terminales se reutilizan si commit/fingerprint coinciden.
- `INFRA_ABORT` permite reanudar únicamente trabajo no terminal.
- Un FAIL funcional no se oculta ni se transforma en infra failure.
- No usar hashes físicos CRLF/LF como precondición; usar Git objects, schemas y contenido semántico.

### Documentación incremental
Antes de cerrar el micro-sprint ejecutar `DocImpactPlanner` y reconciliar P0/P1 current-active. No se permite trasladar drift determinista a la full del backlog.

## 5. Pruebas y validación

- ingest 2.805 samples y validar counts/outcomes;
- duplicate ingestion;
- environment fingerprint mismatch;
- escaped parameter nodeids (`\t`, `\x7f`) preservados;
- cold-start;
- stale sample/aging;
- corrupted sample;
- deterministic estimate;
- DocumentationDriftGate PASS;
- full=0, browser=0.

Reglas:
- completion-first: ejecutar todos los checks planificados salvo unsafe mutation;
- pruebas focales/impactadas únicamente, excepto la única full expresamente autorizada en el sprint de cierre;
- no full por “precaución”;
- no browser si runtime UI/API no cambia;
- comparar comportamiento, contratos y Git content, no representación física del archivo.

## 6. Evidencia obligatoria

- registry snapshot inicial;
- ingestion receipt con 2.805 accepted/rejected;
- estimator report median/p95/confidence;
- nodeid preservation fixtures;
- focal JUnit/logs;
- cost/performance baseline report.

Toda evidencia machine-readable debe registrar commit, timestamps, counts, PASS/BLOCK, S0/S1, `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed` y número de full runs consumidas.

## 7. Ingeniería del operador Windows

- Preferir un único operador Python resumible con subcomandos por fase de alto nivel, no docenas de scripts.
- PowerShell solo para invocar el operador y verificaciones externas inevitables; cada comando en una sola línea y con PASS verde/BLOCK rojo.
- API/UI foreground y tres consolas solo si este micro-sprint realmente cambia/valida browser runtime.
- No limpiar automáticamente cambios desconocidos. Reconocer estados survivores conocidos, respaldarlos y recuperar transaccionalmente.
- Packaging desde Git (`git archive`) después de validación; excluir outputs, caches, `.venv`, `.git`, runtime DB y secretos.
- Promoción Git posterior a PASS: preflight → fast-forward local → remote ancestry → push sin force → three-state review.

## 8. PASS

2.805 muestras reconciliadas o rechazadas explícitamente; estimates determinísticos; nodeids íntegros; scheduler_enabled=false; workers=1; drift P0/P1=0.

## 9. BLOCK

Muestra silenciosamente omitida/duplicada; mezcla de environments incompatibles; nodeid corrupto; duration history usada para autorizar parallel safety; scheduler/worker execution habilitado.

## 10. Salida y autorización

Autoriza FRX-v2.2-C. Commit sugerido: `feat(frx-v2.2): add node duration registry and robust estimator`.
