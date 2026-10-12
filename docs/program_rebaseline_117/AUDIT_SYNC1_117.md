---
doc_id: "DEVPL-REB-117-SYNC-AUDIT"
title: "Protocolo obligatorio de auditoría pre-SYNC-1"
version: "1.0.0"
status: "APPROVED / EXECUTION-GATED"
date: "2026-10-11"
owner_decision: "OWNER-APPROVAL-2026-10-11-REBASELINE-116"
implementation_authority: false
multiprovider_stop_lifted: false
---

# Protocolo obligatorio de auditoría pre-SYNC-1

## Regla irrevocable dentro de este rebaseline
**PROHIBIDO INICIAR SYNC-1 sin auditoría técnica/documental integral PASS de ambos tracks y aprobación de estrategia de integración por el Owner posterior a la auditoría.** El simple cumplimiento D06, el ZIP repo465 o la similitud de clases no sustituyen este gate.

## Alcance de inspección (ambos repositorios literalmente)
1. **Autoridad Git y procedencia:** HEAD, árbol, branch, upstream/remoto, clean/dirty, ancestro común real, lista completa de commits/deltas desde fork, tagged/release history, eventuales divergencias; verificar la identidad efectiva del STOP, sin suponerla a partir del nombre ZIP.
2. **Estado determinístico final:** inventario de servicios, APIs, UI/UX, plan/apply, SourceChangePlan, versionado, model/provider endpoints (incluida ruta experimental), security/RBAC/PathGuard, jobs/Quality, Git, recovery, data stores, traces, documentación e índices. Estado de Pilot A y referencias a tres stories DONE y cinco diferidas; artefactos FROZEN inmutables.
3. **Estado MP congelado y capacidades instaladas:** `MP-0`, `MP-1A` y cualquier delta realmente presente en source; candidate contracts, `GenerationRouteResolver`, `ProviderSelectionPolicy`, `ModelAdapter`, model registry, evaluation/provenance, UI, policies y fixtures. No asumir que un componente existe solo porque está en backlog o ADR.
4. **Contratos/equivalencia:** APIs, schema migrations y compatibilidad, naming, boundaries RBAC, approval, execution authority, Source Registry, ADR precedence, test coverage, workspace/runtime stores y frontend; detallar ownership y componentes redundantes.
5. **Seguridad y operación:** secretos, egress, CostGuard, prompt injection, tool scopes, logs/PII, ports, locks, rollback, dirty worktree, durability y compatibilidad Windows.
6. **Evidencia y calidad:** tests ya PASS, FAIL heredados, gaps reales, full regression receipts, UX S0/S1, deuda técnica, cobertura D06 y requisitos Pilot B.

## Matriz de aprovechamiento obligatorio
Por componente/contrato: `ID`, `origen`, `HEAD/path`, `capacidad observable`, `tests`, `dependencias`, `seguridad`, `paridad`, `conflicto`, `opciones`, `decisión propuesta KEEP/ADAPT/DEPRECATE/NO_IMPORT`, `justificación costo-riesgo`, `owner funcional`, `plan de migración`, `prueba de aceptación`, `mecanismo de rollback`. No decidir por título de archivo ni por preferencia tecnológica.

## Alternativas mínimas que debe comparar
A. Merge one-way con resolución selectiva segura; B. merge one-way con refactorización acotada de contratos dentro de P3; C. **BLOCK sincronización** y emitir prerequisitos/correctivo de compatibilidad documentado; D. no-op únicamente si Git demuestra ausencia de delta. No permitir push forzado, rebase de commits sellados o importar MP→det sin autorización de un programa posterior.

## Reporte de salida y preflight
Auditoría separada `PRE_SYNC_AUDIT_REPORT` + inventarios machine-readable + matrix + summary de blockers + riesgos S0/S1 + evidencia hashes/refs + recomendación justificada; PASS solo si insumos completos y opciones evaluadas. En P3-B redactar estrategia exacta y obtener Owner approval identificable sobre ese plan. Sin aprobación: `SYNC1_NOT_AUTHORIZED`. P3-C solo implementa esa estrategia y valida condiciones post-merge contra la auditoría.
