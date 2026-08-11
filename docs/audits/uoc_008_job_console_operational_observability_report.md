---
doc_id: "DEVPL-UOC-008-JOB-CONSOLE-OPERATIONAL-REPORT"
title: "UOC-008 — Job Console Operational Observability Report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-11"
approval: "approved_by_owner"
---

# UOC-008 — Job Console Operational Observability Report

## 1. Baseline

Baseline exclusivo: `repo_DevPilot_Local_335_POST_H_EVAL_002_UOC_007.zip`, SHA-256 `5134ffb607ec65fa3c2a1a720505bcf6583fb3edcaacd66f6b65c883990ffde0`, cierre UOC-007 `d2afb1381cfbfc6834274969e0f2e86b18526297`.

## 2. Implementación

Se incorpora Application Service operacional para list/detail/log/cancel/retry/reconcile, router API tipado, bindings de policy, ruta UI `/jobs`, polling bounded, filtros, detalle de heartbeat/progreso, logs sanitizados y contratos de schema.

## 3. Seguridad

No se añade shell. La única terminación de procesos usa PID previamente registrado y argv fija (`taskkill` en Windows o process group POSIX), nunca texto del browser. Retry no ejecuta automáticamente. Los hashes internos de cancel/idempotency/fingerprint se excluyen del snapshot UI.

## 4. Riesgos residuales

- persistencia JSON sigue siendo local-first e implemented-initial;
- no se habilitan adapters de capability; UOC-009 decide cuáles operaciones de calidad/testing/release se vinculan;
- polling no es WebSocket/streaming push;
- process-tree cancellation depende de worker lease confiable y debe endurecerse en UOC-011.

## 5. Verificación controlada

La implementación se valida con tests unitarios, API, UI/static contracts, schemas, TCR/Project State/Docs Governance, route registries, npm smoke/build y browser acceptance Windows. Full regression se decide por Test Impact y no se repite si existe evidencia reutilizable bajo el contrato del backlog.

## 6. Criterio de cierre

UOC-008 permanece `implemented-initial/pending-windows-browser-closure` hasta que la ejecución Windows produzca evidencia autoritativa, repo336 limpio y `S0=0/S1=0`. UOC-009 no queda autorizado por el source candidate.

## 7. Comandos de verificación

Consultar la guía operacional UOC-008 entregada con el operador. No se mantienen comandos duplicados en este reporte.

## 8. Cierre autoritativo

**CLOSED/PASS**. Source commit `d8c2464db65624967b5c7aa81bd95ed87911f744`; browser acceptance 12/12 + 6/6 screenshots; baseline full regression UOC-007 2159/2159 reutilizada conforme backlog con Test Impact y todos los tests impactados frescos PASS. Baseline siguiente: `repo_DevPilot_Local_336_POST_H_EVAL_002_UOC_008.zip`. UOC-009 queda autorizado; no se habilita shell ni ejecución genérica de capabilities.
