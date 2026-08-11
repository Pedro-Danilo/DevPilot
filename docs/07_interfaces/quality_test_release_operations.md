---
doc_id: "DEVPL-UOC-009-QUALITY-TEST-RELEASE-OPERATIONS"
title: "UOC-009 — Quality, tests y release operations"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-11"
approval: "approved_by_owner"
---

# UOC-009 — Quality, tests y release operations

## Objetivo
UOC-009 lleva a la Web UI las operaciones determinísticas de calidad, pruebas y release definidas por el backlog, reutilizando Application Services y el framework de jobs UOC-007/UOC-008. La UI selecciona IDs y profiles registrados; nunca recibe comandos, ejecutables o argumentos pytest libres.

## Superficie
`/quality` expone catálogo/budgets, baseline/manifest inspection, Test Impact plan, TCR v1/v2, Project State, Docs Governance, Quality Gate profiles, readiness strict, release verification dry-run, focused tests por TCR profile, full regression explícita y evidence packaging. Los jobs enlazan a `/jobs/{job_id}` para heartbeat, timeout, cancelación, logs y resultado.

## Approval y full regression
Las operaciones sensibles se planifican solo con approval exacto (`tool_id`, `action=execute`, `subject=operation_id`). Full regression exige además la cadena literal `RUN FULL REGRESSION`; no se inicia automáticamente al terminar focused tests. El worker recibe argv fija y resuelve test files desde TCR v2.

## Seguridad
No hay shell arbitrario, `shell=True`, path de ejecutable recibido del navegador, argumentos pytest libres, red, API externa, connector write, plugin execution ni mutación del source. Los outputs se limitan a `outputs/runtime/uoc009_quality`, `outputs/runtime/governed_jobs` y `outputs/evidence_packages/uoc009_quality`.

## Primera versión y evolución
Es `implemented-initial`: habilita un subconjunto tipado de 10 capabilities CLI mediante un único adapter local UOC-009. UOC-010 no queda autorizado hasta cierre. UOC-011 debe endurecer concurrencia, retención, performance/accessibility y operación prolongada.

## Browser approval binding correction (v1.0.4)

The `/quality` approval request serializes `scope` as a JSON object string compatible with `ApprovalService.parse_scope`. The UI binds `operation_id`, `workspace_id`, and `source=ui.quality`; legacy free-form values such as `operation=quality-gate` are invalid and must remain blocked. HTTP 403 on this flow is an application/policy BLOCK after authentication, not evidence that the local token is missing. The Quality surface therefore renders its 403 detail locally without changing the shared API-client error contract used by historical UI surfaces.

