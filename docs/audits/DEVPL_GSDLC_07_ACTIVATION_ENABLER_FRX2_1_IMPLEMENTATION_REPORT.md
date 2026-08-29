---
doc_id: "DEVPL-GSDLC-07-ACTIVATION-ENABLER-FRX2-1-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-07 activation enabler — Full Regression Execution v2.1 implementation report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-29"
approval: "approved_by_owner"
---

# DEVPL-GSDLC-07 activation enabler — Full Regression Execution v2.1

## 1. Estado

`IMPLEMENTED-INITIAL / PASS-CANDIDATE / PENDING-WINDOWS-OWNER-ADJUDICATION`.

La autoridad de entrada es repo380 Windows-validated, commit `2378296abe194431894d9f25bdd1f59a81205013`, SHA-256 `841d0cd1c3f9e5edba21d3e14e42d75a067d9bbfbab90af1ddf48293b7a967b4`.

Los gaps `S2-EVIDENCE-06E-001` y `S2-DOC-06E-002` quedaron remediados en el activation rebind previo. Los tres estados oficiales quedaron reconciliados en el mismo successor commit.

## 2. Implementación

Se agregan contratos/modelos `FullRegressionSession`, `CollectedNode`, `ShardPlan`/`ShardDefinition`, `ShardReceipt` y `TerminalOutcome`, collector pytest por plugin, plan inmutable, runner secuencial con argv tipado, receipts/JUnit/hash, resume planner, status y aggregate adjudicator.

La superficie CLI es `tests full-session ...`, reutilizando la familia `tests` existente para no duplicar namespace público.

## 3. Decisiones de ingeniería

- La colección no parsea stdout: usa `pytest_collection_finish` para capturar `session.items[].nodeid`, porque DevPilot personaliza la salida `--collect-only -q`.
- `FAIL` funcional ordinario conserva completion-first.
- timeout/infra abort no se reinterpreta como FAIL funcional.
- `resume` solo opera con source/environment/collection/plan fingerprints idénticos.
- `run`/`resume` requieren `--execute`; v2.1 no declara un Approval/PolicyEngine binding que aún no implementa.
- no `pytest-xdist`.

## 4. Validación local

- contratos nuevos: `10/10 PASS`;
- focal ampliada de integración/gobernanza: `27/27 PASS`;
- Historical Regression Guard: `PASS` mediante waiver temporal owner-approved del enabler, porque la full de GSDLC-07 está expresamente reservada a 07-E;
- bounded real canary: `2/2 nodeids`, `2/2 shards`, `PASS=2`, `UNEXECUTED=0`, accounting `100%`, adjudication `PASS`;
- full regression del backlog 07 consumida: `0`.

La evidencia final se regenera tras reconciliación documental para que los fingerprints correspondan al candidate final.

## 5. Riesgos y limitaciones

v2.1 todavía no balancea shards por duración ni ejecuta workers paralelos. El overhead de startup de pytest por shard existe. El objetivo de v2.1 es **cero pérdida de progreso y accounting completo**, no reducción agresiva del wall-clock.

## 6. PASS/BLOCK

PASS-CANDIDATE si tests focales, bounded canary, CLI governance, Project State, Documentation Governance y TCR v1/v2 pasan sin ejecutar full. 07-A queda autorizado funcionalmente a nivel de programa. Windows/owner adjudication de este enabler es únicamente el gate temporal previo a su primera mutación; al cerrar `CLOSED/PASS` el gate se extingue y 07-A puede comenzar sin trabajo de activación adicional.


## 7. Relación con v2.2/v2.3

v2.1 resuelve pérdida de progreso y observabilidad de una full larga, pero no promete por sí sola reducir drásticamente el tiempo total. v2.2 usará receipts reales para balancear shards por duración y reducir skew/overhead; v2.3 podrá introducir paralelismo únicamente después de clasificar aislamiento y recursos compartidos. Ninguna de las dos fases bloquea GSDLC-07-A..D. La full única del backlog sigue reservada a 07-E.
