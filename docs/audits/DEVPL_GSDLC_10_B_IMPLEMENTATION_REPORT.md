---
doc_id: "DEVPL-GSDLC-10-B-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-10-B — Governed validation jobs and live logs implementation report"
status: "implemented/local-qualified/windows-validation-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-09"
approval: "approved_by_owner/rebound_repo415"
---

# DEVPL-GSDLC-10-B — Implementation report

## Estado

`IMPLEMENTED / LOCAL-QUALIFIED / WINDOWS-VALIDATION-PENDING` sobre repo415. GSDLC-10-A permanece cerrado y no se reabre. Full Regression en 10-B = 0.

## Capacidades implementadas

- `StoryValidationJobApplicationService` deriva jobs tipados `test`, `build` y `lint` exclusivamente desde un `StoryTestPlan` `APPROVED` hash-bound.
- Reutiliza `GovernedJobFramework`, `GovernedJobOperationsApplicationService`, Job Console y capability registry existentes; no existe un segundo motor de jobs.
- Registry declarativo de capabilities/profiles controla adapters, timeouts, retry budget y límites; el browser no suministra command strings.
- Worker local `shell=false` ejecuta pytest sobre targets del StoryTestPlan, Vite build y syntax lint sobre changed Python paths.
- Lifecycle observable con heartbeat, timestamps, counters, logs bounded/paginados/redacted y resultado estructurado.
- Test jobs producen JUnit y result artifact refs.
- Cancel usa process-tree termination; timeout termina process tree; orphan reconciliation nunca produce PASS por ausencia de worker.
- Retry crea nueva attempt identity y reutiliza el mismo immutable context/story-test-plan hash.
- UI integra `StoryTestPlan APPROVED → Planificar jobs tipados → Iniciar → Job Console/live logs`; no crea consola paralela.

## Seguridad

No arbitrary shell, no command string libre, no Full adapter, StoryTestPlan stale/unapproved fail-closed, targets de pytest restringidos a `tests/*.py[::node]`, límites de cantidad/timeout/log, secretos redactados y stores runtime-ephemeral excluidos de source/evidence final.

## Regresión

FRX v2.4 A/B current-active: drift documental no crítico se absorbe dentro del micro-sprint; 10-B usa focal + Test Impact + bounded cumulative. Full Regression = 0; la única Full ordinaria del backlog permanece reservada para 10-E.

## Browser Windows

Browser real requerido una vez porque se introduce lifecycle/live-log UX. La aceptación debe demostrar planificado desde StoryTestPlan aprobado, ejecución tipada, estado/heartbeat/logs en Job Console y resultado terminal accionable. Cancel/retry/timeout/orphan negativos se cubren automáticamente y no se repiten manualmente.

## Riesgos y limitaciones

Primera versión integrada StoryValidationJob. Resource ceiling se expresa como timeout/target/log budgets y process-tree cancellation; no implementa todavía sandbox OS/cgroups/Job Objects dedicado. Near-live logs son polling paginado de la Job Console existente. Quality remediation corresponde a 10-C.

## PASS Windows

Focal/bounded/Test Impact/gates PASS, browser una vez PASS, S0/S1=0, Full=0, Git fast-forward y repo limpio.

## BLOCK Windows

Command/shell libre, stale StoryTestPlan ejecutable, secret en log, timeout/cancel deja proceso huérfano, orphan se marca PASS, browser lifecycle/logs no demostrable, gate focal/bounded FAIL o cualquier Full en 10-B.

## Validación local final

- focal 10-B: 10/10 PASS;
- bounded cumulative 10-A + governed jobs + Job Console + API contracts: 53/53 PASS;
- TCR/source-registry/evidence-freshness/contract-reconciliation governance: 55/55 PASS;
- Documentation Governance global: PASS;
- TypeScript compile focal: PASS;
- Python py_compile: PASS;
- Test Impact v2: 35 changed paths / 328 contracts / 196 matched / 304 recommended / 0 unmatched; tests_executed=false;
- Full Regression: 0.
