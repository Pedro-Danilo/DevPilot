---
doc_id: "DEVPL-UX-P0-D-IMPLEMENTATION-REPORT"
title: "DEVPL-UX-P0-D — Implementation report"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-17"
approval: "pending_windows_validation"
---

# DEVPL-UX-P0-D — Implementation report

## Objetivo

Normalizar estados, jerarquía de acciones, gates, approvals, diffs, operaciones largas y evidencia progresiva entre Story/Code, Approvals, Jobs, Quality, Release, Recovery/Reconciliation e AI/RAG.

## Implementado

Se añadió `ui/web/src/components/OperationalPatterns.ts` con primitives reutilizables para `OperationState`, `PrimaryAction`, `GateSummary`, `ApprovalSummary`, `DiffSummary`, `LongRunningOperation`, `ProgressiveEvidence` y un compositor `OperationalSurfaceSummary`.

La adopción prioritaria cubre Story/Code, Approval Center, Jobs, Quality, Release Readiness/Package/Lifecycle/Closure, Recovery, Reconciliation e AI/RAG. Reports/Traces permanecen diagnostic-heavy y no reciben redesign exhaustivo.

## Autoridad y seguridad

El delta es presentation-only: no cambia routes, APIs, RBAC, approvals, policy, provider/tool authority ni permisos Guided/Expert. Evidence se vuelve progresiva, no se elimina. No se introduce dependencia runtime/frontend nueva. Full Regression permanece prohibida en D.

## Validación local

- pytest contractual focal/successor-aware: 16/16 PASS.
- smoke UX-P0-D: 42/42 PASS.
- 15/15 scripts UI/contract impactados PASS (route, a11y, state matrix, Story/Code, source change, test plan, Release, Recovery/Reconciliation, AI/RAG).
- `test:operator-flows` no se usa como gate de D: también BLOCK en repo434 por un marcador histórico ausente y por tanto sería un falso BLOCK heredado.
- Vite build no se reclama localmente porque el ZIP limpio no contiene `node_modules`; el operador Windows lo ejecuta usando el runtime oficial.
- Windows real-browser focal permanece obligatorio antes de cierre.

## Riesgos

- Los resúmenes son primera normalización semántica, no polish final.
- Estados dinámicos complejos siguen dependiendo de cada API existente; UX-P1/P2 puede profundizar la consolidación.
- Browser/a11y focal en Windows debe confirmar densidad responsive y focus real.

## PASS/BLOCK

PASS requiere semántica consistente, blockers visibles, evidence accesible, policy parity y Full=0. BLOCK ante hidden blocker/destructive action, pérdida de evidence, divergencia Guided/Expert en permisos, autoridad trasladada a UI o UX-S0/S1.

## Verificación

```text
cd ui/web && npm run test:ux-p0-d
cd ui/web && npm run test:route-enforcement
cd ui/web && npm run test:accessibility
cd ui/web && npm run test:state-matrix
python -m pytest tests/test_devpl_ux_p0_d_operational_patterns.py -q
```
