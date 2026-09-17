---
doc_id: "DEVPL-UX-P0-E-IMPLEMENTATION-REPORT"
title: "DEVPL-UX-P0-E — Implementation report"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-17"
approval: "pending_windows_validation"
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
