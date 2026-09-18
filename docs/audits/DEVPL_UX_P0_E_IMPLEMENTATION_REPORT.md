---
doc_id: "DEVPL-UX-P0-E-IMPLEMENTATION-REPORT"
title: "DEVPL-UX-P0-E — Implementation report"
status: "closed-pass-windows-validated"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-17"
approval: "owner-adjudicated-composite-recovery"
---

# Objetivo

Cerrar UX-P0 mediante gates baratos, browser/usability/a11y/performance, HCA/TCR y exactamente una logical Full antes de producir repo436.

# Implementación

E no rediseña superficies ni añade dependencias. Añade contratos de cierre, rebind current-active repo435→E, smoke de closure, planes de browser/usability/performance/Full/clean-install y operador Windows state-aware.

# Full Regression

El operador reserva `DEVPL-UX-P0-E-FULL-01` solo después de browser/usability/a11y/performance PASS y del commit fuente E. `run` puede ejecutarse una sola vez. Infra interruption usa `resume` sobre UNEXECUTED dentro de la misma sesión. Functional FAIL/ERROR queda preservado y bloquea el RC hasta un correctivo de recovery selectivo; una segunda Full está prohibida.

# Limitaciones

Esta fase demuestra readiness pre-pilot, no constituye una auditoría WCAG formal multi-screen-reader/dispositivo ni un benchmark de producción distribuido. UX-P1/P2 podrá profundizar polish, accesibilidad formal y performance profiling.

# Windows corrective v1.0.1 — inherited performance contract

La validación Windows v1.0.0 confirmó que `npm run test:performance` (contrato UOC-011 v1) ya estaba `BLOCK` en repo435: `source_ui_bytes=939755` y `largest_source_bytes=94240`. UX-P0-E no modifica `ui/web/src`; el bloqueo era deuda heredada, no regresión E.

El corrective v1.0.1 no elimina el test ni amplía `currentUiSourceBudget*`. Evoluciona `uoc011-performance-smoke.mjs` a `v2-successor-aware`: conserva los presupuestos históricos/current, registra el repo435 exacto como baseline grandfathered y bloquea cualquier crecimiento por encima de `939755/94240`. Además, el operador E exige paridad semántica exacta con repo435 y mantiene los hard ceilings de `dist`. La Full continúa sin consumir (`0/1`).

# Windows corrective v1.0.3 — FRX preflight reconciliation

`seal-preflight` v1.0.1 bloqueó antes de ejecutar cualquier Full. La colección fue sellada con 3225 nodeids, pero el preflight standalone recibió `collection.json` sin `collection_sha256` embebido y el Test Isolation Registry cubría 3195/3225 nodeids. El presupuesto permaneció 0/1 y no existieron plan ni receipts de ejecución.

El corrective v1.0.3 reconcilia el registry contra la colección actual exacta: añade 30 nodeids nuevos como `UNCLASSIFIED` (por tanto seriales bajo el perfil vigente), elimina 10 entradas stale que ya no pertenecen a la colección y deja 3225/3225 de cobertura sin inferir `PROVEN_PARALLEL_SAFE`. Además elimina el preflight standalone sobre el JSON crudo: el operador usa `tests full-session plan --profile-id current --full-budget-state 0`, cuya implementación inyecta el hash de la colección sellada antes de ejecutar el preflight FRX-v2.4.

Como el intento v1.0.1 no ejecutó tests Full ni reservó presupuesto, el session runtime pre-plan puede reseedearse de forma gobernada: primero se archivan `session.json` y `collection.json` en evidencia, luego se elimina solo ese runtime pre-ejecución y se recollecta el mismo logical session id desde el commit correctivo. Las 20 capturas browser v101 permanecen válidas porque el corrective no modifica `ui/web/src`, rutas, API, RBAC ni presentación.

# Windows browser evidence review v1.0.3

Las 20 capturas `browser_v101` fueron revisadas visualmente después del `browser-record` PASS. No se observan UX-S0/S1, secretos, bypass de autorización, overflow crítico ni dependencia de terminal para el journey normal. La evidencia de keyboard focus muestra el skip-link/focus-visible y las vistas 768x1024/390x844 mantienen acciones esenciales utilizables.

Se registra un hallazgo no bloqueante `UX-P0-E-S3-001`: Project Status puede mostrar `READY` como estado de ingeniería mientras la acción autoritativa es `RESOLVE_BLOCKER` por un gate `UNKNOWN`. El blocker y la next action son visibles, por lo que no invalida P0; se difiere mejora de copy/semántica visual a UX-P1.

# Windows composite recovery result

The original Full `DEVPL-UX-P0-E-FULL-01` is immutable FAIL-once evidence: 3170 PASS / 50 FAIL / 0 ERROR / 5 approved SKIP / 3225 accounted. It was not rerun. Post-Full corrective changes only governance/test/metadata contracts, then validates the exact original 50 failed nodeids, bounded impacted tests, Historical Regression Guard and deterministic gates. Final adjudication is `PASS/COMPOSITE-FULL-PLUS-SELECTIVE-RECOVERY`; Full 1/1, second Full 0.
