---
doc_id: ADR-MP132-014-187
title: "Planning por incrementos y entregas verificables"
status: "PROGRAMMATIC_AMENDMENT"
version: "1.0.0"
date: "2026-10-17"
planning_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
execution_authority: false
---
# ADR MP132-014 — Incremental Delivery Planning

## Problema

Roadmap/Backlog/Sprint FROZEN y stories DONE no demuestran por sí solos una aplicación usable. El motor Planning existente usa JSON canónico con proyecciones Markdown y heurísticas preliminares; debe planificar outcomes verificables y entregas de software, no solo lotes de documentos.

## Decisión

Mantener la autoridad existente de Planning. Introducir `SoftwareIncrementPlan` como **objeto vinculado al canonical Planning**, no como store paralelo. Roadmap formula objetivos/capacidades, Release Plan ordena incrementos por dependencias, Backlog descompone en slices, Sprint se compromete con stories listas y capacity/risk, aceptación de incremento demuestra escenarios integrados, Release acredita desplegabilidad/autonomía. Planear sucesores sobre feedback; no congelar todos los sprints futuros.

## Gates

`STORY_DONE`: AC, tests/Quality/Git; `INCREMENT_ACCEPTED`: integración+outcomes+negativas+evidencias; `RELEASE_READY`: build, security, artefacto portable, runbook, deploy, backup/restore/rollback según PESP. Decisiones humanas solo materiales; `coverage/hash/index` verificación automática. MIPSoftware siempre, MIASI solo por componente inteligente real.

## Trade-offs y validación

Se agrega una entidad de planificación y trazabilidad, pero evita releases ficticios y prioridades uniformes. Probar dependencias stale, RF sin tests, capacidad inflada, historia DONE sin integración, incremento sin AC y release sin rollback. R4 define y publica plan, R5 demuestra aceptación integrada, R6 libera; R10 comprueba segundo dominio. Sin implementación ni aprobación de ejecución automática por esta ADR.
