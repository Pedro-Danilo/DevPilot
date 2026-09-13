---
doc_id: "DEVPL-GSDLC-12-D-INDUSTRIAL-HARDENING-REPORT"
title: "DEVPL-GSDLC-12-D — Performance, security red-team and resource/cost hardening report"
status: "implemented-local-qualified"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-13"
approval: "local-qualification/windows-validation-pending"
---

# Objetivo

Endurecer DevPilot frente a carga, abuso de recursos y ataques realistas usando únicamente pruebas locales, mocks/fakes y políticas determinísticas.

# Fuente de ejecución

- Repo: `repo_DevPilot_Local_428_DEVPL_GSDLC_12_C_GUIDED_EXPERT_ACCESSIBILITY_HELP_WINDOWS_VALIDATED_CANDIDATE.zip`.
- Commit: `de3f3008dcc0fcbc6071462bffb70a18e2ab6109`.
- SHA-256: `4aba885046eacaf2a6c2f3e6b33bec3c40aba845d65522ae440a9c6c94a52c1e`.
- GSDLC-12-C: `CLOSED/PASS/WINDOWS-VALIDATED`.

# Implementación

Se incorpora `industrial_hardening_policy.json` como current-active policy y `IndustrialHardeningEvaluator` como verificador determinístico. Evalúa budgets de performance, path/archive safety, auth/session/CSRF, ModelRouteDecision vs ToolExecutionDecision, MCP fake-local, provider freshness/fallback, token/cost ceilings, supply-chain y parity Guided/Expert. No habilita ninguna capacidad peligrosa nueva.

# Seguridad

- Network: deshabilitada.
- External API: deshabilitada.
- Real MCP write: deshabilitado.
- `filesystem.delete`: bloqueado.
- autonomous recovery: bloqueado.
- model route no concede tool permission.
- S0/S1 abiertos: 0/0 localmente.

# Performance y recursos

Los budgets current-active son una primera versión industrial conservadora y no sobrescriben snapshots históricos. El hard ceiling es explícito; una desviación de budget que permanezca por debajo del hard ceiling debe justificarse, mientras superar el hard ceiling bloquea. La validación browser 12-C se reutiliza hash-bound porque 12-D no cambia UX/control surfaces.

# Pruebas

Se ejecutan focal 12-D + selección acumulativa de seguridad/model/provider/MCP/approval y Test Impact. Full Regression permanece 0, reservada para 12-E.

# Riesgos y limitaciones

La medición de browser responsiveness en 12-D usa evidencia browser previa y proxies estáticos/locales porque no se modifica UI. La matriz browser completa y la única Full pertenecen a 12-E. Los ceilings actuales son primera versión y deben recalibrarse con telemetría de RC sin relajar hard stops de seguridad.

# PASS / BLOCK

**PASS local:** performance dentro de hard ceilings, S0/S1=0, no authority escalation, no hidden external fallback, recursos/costo acotados, no network/external API, Full=0.

**BLOCK:** auth/RBAC bypass, path escape, destructive filesystem/Git, model→tool escalation, hidden external fallback, recurso/costo ilimitado, supply-chain bypass o cualquier S0/S1 abierto.

# Criterio Windows

12-D solo cierra después de validar el bundle Windows sobre repo428. 12-E permanece no autorizado hasta ese PASS.

# Finding corregida en 12-D

El red-team detectó `CONSUMER-SESSION-PIGGYBACK`: `AgentExecutionPolicy` permitía consumir/cancelar una sesión con un `actor_id` distinto del actor que la creó. 12-D liga ahora `evaluate_intent()` y `cancel()` al actor de la sesión y bloquea con `AGENT_EXECUTION_SESSION_ACTOR_MISMATCH`. El retest demuestra que el actor legítimo conserva operación normal y el consumidor cruzado queda bloqueado.

# Verificación ampliada

La baseline incluye assembly/startup de FastAPI, latencia p95 in-process de health, workspace settings y Project Status, inventario de repo/docs/UI/workbenches, large fixture y peak-memory separado para no distorsionar latencia. El red-team incluye session fixation/revoke, cross-workspace, CSRF, path/symlink/archive traversal, stale preimage/approval binding, duplicate execute idempotency, prompt→forbidden-tool, model-route→tool separation, autonomous recovery, consumer-session piggyback, fake-local MCP write, provider freshness/fallback, oversized model input, token/cost ceilings, supply-chain y mode parity.

## Windows corrective v1.0.1 — runtime-store lifecycle and performance probe portability

La primera validación Windows bloqueó de forma legítima antes de cierre. El red-team descubrió que `sqlite3.Connection` usado como context manager cerraba la transacción pero no el file handle; en Windows esto impedía eliminar el `auth.db` temporal (`WinError 32`). `LocalAuthStore._connect()` pasa a ser un context manager propio que siempre ejecuta `close()`. El mismo leak podía amplificar latencias sucesivas del harness.

La medición API también mezclaba la primera inicialización específica de cada route con el p95 steady-state. 12-D conserva exactamente los mismos budgets y hard ceilings, registra una cold probe por route y mide después ocho muestras steady-state. No se relaja ningún límite. El Test Impact current-active pasa a `25/194/315/0`; Full Regression permanece `0`, reservada para 12-E.
