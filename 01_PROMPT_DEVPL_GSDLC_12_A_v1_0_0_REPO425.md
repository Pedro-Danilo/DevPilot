---
doc_id: "PROMPT-DEVPL-GSDLC-12-A"
title: "DEVPL-GSDLC-12-A — Persistent resumability, crash/restart recovery and locks"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-12"
approval: "approved_by_owner"
precondition: "DEVPL-GSDLC-11 CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY"
execution_source_policy: "repo425 + activation/rebind absorbed into this micro-sprint"
full_regression_budget: "0 in 12-A; GSDLC-12 budget remains 0/1"
browser_policy: "required for restart/resume/recovery UX introduced by 12-A"
---

# Objetivo

Hacer durable el workflow completo frente a cierre de navegador, restart de API/UI, crash controlado y locks stale, recuperando contexto seguro sin duplicar side effects ni reutilizar approvals stale.

# Implementación requerida

1. Integrar el prompt 00 de activation/rebind en el mismo delta de 12-A.
2. Inventariar los estados actuales: session workspace scope, `ProjectJourneyContext`, engineering state, drafts, current step, pending plans/jobs/approvals y runtime stores. Definir autoridad server-side y qué estado es UX-only.
3. Implementar `ResumeService` con checkpoint durable y versionado; checkpoint mínimo: workspace/project, authoritative Git identity, current step, draft refs, safe pending work, last verified evidence refs y recovery reason.
4. Implementar `WorkspaceLockService` con ownership por workspace/action/session/actor, TTL/heartbeat cuando aplique, stale-lock detection y liberación/recovery explícita. No auto-force-unlock de operación sensible sin prueba de staleness.
5. Distinguir operaciones `SAFE_TO_RESUME`, `REVALIDATION_REQUIRED`, `ABORTED_REQUIRES_REPLAN`, `COMPLETED`; nunca reejecutar automáticamente una mutación incompleta.
6. Reconciliar jobs interrumpidos y approvals: approval expirada, actor cambiado, commit/preimage cambiado o restart inseguro => nueva confirmación/approval.
7. Implementar `RecoveryView` y Project Status para mostrar qué se recuperó, qué se invalidó, por qué y cuál es la siguiente acción. Corregir la contradicción heredada `Lifecycle RELEASED` vs aggregate `BLOCKED` cuando provenga de dominios no autoritativos para el lifecycle, sin esconder blockers reales.
8. No copiar `auth.db*`, `devpilot.db*` ni equivalentes a fixtures; restart acceptance debe demostrar recuperación mediante contratos durables permitidos, no por snapshot clandestino de DB runtime.
9. Producir schemas/registries/contracts current-active, ADR si se introduce nueva autoridad de persistencia, source delta, Test Impact, HCA y Contract Reconciliation.

# Pruebas mínimas

- cerrar/reabrir UI conservando contexto UX sin convertir storage en autoridad;
- restart API y UI con recovery server-validated;
- crash entre plan y execute: no side effect duplicado;
- crash durante/tras execute: verify/evidence idempotente;
- stale lock, lock owner mismatch y concurrent duplicate execution negative;
- draft recovery y draft invalidation por source/preimage drift;
- stale approval no reutilizable;
- lifecycle RELEASED + aggregate domain gaps explicado de forma no contradictoria;
- project-scoped guard después de restart;
- Test Impact + focal/acumulativa. `Full Regression = 0`.

# Browser acceptance obligatorio

Una ejecución real-browser debe demostrar al menos: proyecto activo → draft/current step → cierre/restart controlado → login/session recovery → contexto recuperado → lock/revalidation visible → operación sensible no auto-ejecutada → Project Status coherente. Capturas únicas y verifier machine-readable. Correctives sin cambio UX reutilizan esta evidencia hash-bound.

# Evidencia mínima

- `resume_matrix.json` con escenarios y autoridad usada;
- `workspace_lock_matrix.json`;
- recovery traces machine-readable;
- screenshots/verifier browser;
- source delta, Test Impact, historical contract sweep, contract reconciliation sweep;
- Git identity pre/post, S0/S1, implementation report.

# PASS/BLOCK

**PASS:** restart devuelve estado reproducible y explicable; drafts seguros sobreviven; operaciones sensibles requieren revalidación; no hay side effects duplicados; lock ownership es demostrable; S0/S1=0.

**BLOCK:** duplicate mutation, lost draft sin explicación, stale approval auto-used, lock robado/silenciosamente reemplazado, browser storage actuando como autoridad o Project Status contradictorio con lifecycle autoritativo.

# Salida

Autoriza GSDLC-12-B únicamente tras PASS Windows y successor limpio/hash-bound.

## Reglas transversales obligatorias

- Ingeniería acumulativa: partir únicamente del successor Windows-validado inmediato; nunca retroceder a repo425 ni a otro histórico después de que exista un successor válido.
- `dry-run` por defecto; toda mutación sensible sigue `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`.
- Prohibidos `reset --hard`, `git clean`, force push, rebase destructivo, borrados implícitos, publish o deploy remoto.
- No arbitrary shell desde el usuario. Jobs y mutaciones son operaciones tipadas/allowlisted.
- Runtime stores, secretos, `.git`, `.venv`, `outputs/`, `.pytest_cache/`, `__pycache__/`, `node_modules/`, `auth.db*`, `devpilot.db*` y equivalentes quedan fuera de fixtures/packages finales.
- Operadores Windows: Python preferido; pequeños, reentrantes, idempotentes por evidencia/commit/contenido y state-aware. No asumir cwd, `git common-dir`, remotes, branches ni procesos previos.
- LF/CRLF no puede provocar BLOCK: usar contenido Git o comparación semántica UTF-8/LF.
- Drifts documentales no críticos y acotados se corrigen dentro del micro-sprint activo o del siguiente natural; no crear sprint/operator/repo aislado solo por drift.
- HCA + Contract Reconciliation proporcional antes del cierre de cada micro-sprint; no reescribir hechos históricos para hacer pasar contratos current-active.
- Evidencia PASS hash-bound se reutiliza cuando el corrective no toca esa superficie; no repetir browser ni pruebas costosas por rutina.
- Cada guía Windows resultante será una sola `.md`, pasos consecutivos, orientada a personal beginner-medio, bundle desde `C:\Users\Pedro\Downloads`, y cada comando PowerShell físicamente en una sola línea.
- API/UI solo cuando corresponda, siempre foreground; para browser usar tres consolas separadas: operador, API `8787`, UI `5173`.
- Cada cierre registra explícitamente `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`, identidad Git pre/post, S0/S1 y hashes de artefactos.
- A→D: no Full por rutina. E: única logical Full del backlog salvo hard trigger previo owner-approved que ya haya consumido el budget. FAIL funcional = preservar y NO RERUN; recovery composite selectivo obligatorio.
