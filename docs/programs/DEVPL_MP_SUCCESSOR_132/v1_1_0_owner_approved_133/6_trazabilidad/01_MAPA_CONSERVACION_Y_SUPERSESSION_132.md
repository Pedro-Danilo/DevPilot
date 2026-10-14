---
doc_id: DEVPL-MP-SUCCESSOR-132-01_MAPA_CONSERVACION_Y_SUPERSESSION_132
title: "Trazabilidad MP v2.1, 131, audit 130 y supersession"
version: "1.1.0"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
---

# Trazabilidad MP v2.1, 131, audit 130 y supersession

## A. Reglas de herencia histórica

- **131:** reemplazo TOTAL de sus 12 documentos como autoridad de planeación, mapeados uno a uno en `0_program/03...`. Se preserva ZIP 131 y su manifiesto intactos como historia.
- **MP v2.1:** legado documental históricamente aprobado; quedan los **principios compatibles** de las ADRs 001/002/003/006/007, sujetos al Authority Register y revisión de sus versiones. ADR 004/005/009 se adaptan mediante ADRs nuevos; ADR 008 pierde el supuesto de dos ramas pendientes de fusión; ADR 010 external sigue DEFERRED. Los operadores/prompts de MP1B y la secuencia Pilot A D07/D08→SYNC2 no pueden ejecutarse.
- **Rebaseline 117:** G0–G5 técnicos históricos, D05 PARTIAL, D06 S1–S6 PASS con límites, SYNC1/correctivo COR130 cerrados. No editar registros sellados. G5 administrativa Owner continúa separada si no existe firma posterior.
- **Ledger v1.32:** histórico `OBSERVE_ONLY` con S0–S3 y findings; no authority mutation. Corrección UX futura requiere reproducción y recibos sobre baseline vivo.

## B. Decisiones que se preservan expresamente

| Fuente 131/v2.1 | Continuidad en 132 |
|---|---|
| Local-first + determinístico sin API | Conservados para bootstrap/validación; L preferente en semántica cuando elegible |
| D/L/E matrix, no pipeline obligatorio | ADR-132-004 y RoutePolicy |
| Candidate provenance/Envelope | ADR-132-005 y R1 |
| Agentes advisory y human approvals | ADR-132-009 y R7 |
| No external sin egress/CostGuard | ADR-132-010 deferred y R8/Pilot C |
| Reuse-first antes de change | Governance A0–A6, NO-OP aceptado |
| Pilot B nuevo y continuo | Charter B0–B7, R2–R10 |
| Technology Profile antes de scaffold/dependencies | ADR-132-006 y R3 |
| UI Guided/Expert y findings ledger | ADR-132-011, Settings y R1–R9 |
| D06 límites y MP source canonical | R9 fault injection, head 8db5… |
| Release/recovery/maturity por evidencia | Acceptance Matrix/ R6,R10 |

## C. Cambios materiales deliberados v1.1

R0 decision gate B Git en lugar de migración diferida; R1 PESP+artifact coverage+publication+successor+Settings básicos; local L preferente para tareas semánticas con fallback honesto; nuevo PESP MIASI condicional; Markdown durable profesional y portabilidad; once backlogs por ola; R9 queda para consolidación, no estreno tardío de Settings/FROZEN; estado UI de operaciones sensibles transversal; Pilot B incorpora change post-initial-release.

## D. Anticolisión de autoridad

El registro documental 132 no elimina leyes de seguridad ni decisiones técnicas anteriores aceptadas. Los nuevos ADRs son `OWNER_ACCEPTED` para arquitectura mediante acta 133 y sustituyen solo los supuestos expresamente delimitados de ADRs históricos; toda **implementación** de delta requiere auditoría focal, permisos, plan de migración y pruebas. Cualquier contradicción sin decisión → BLOCK, no merge automático de políticas.
