---
doc_id: "DEVPL-UX-P1-PILOT-DRIVEN-PRODUCTIZATION"
title: "DEVPL-UX-P1 — Pilot-driven frontend productization plan"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-21"
strategy_binding: "DEVPL_UI_UX_PRODUCTIZATION_STRATEGY_v1_0_0_APPROVED"
execution_program: "DEVPL-GSDLC-13"
supersedes: "DEVPL_UX_P1_PILOT_DRIVEN_PRODUCTIZATION_PLAN_v1_0_0_APPROVED.md"
---

# DEVPL-UX-P1 — Pilot-driven productization

## Objetivo

Mejorar el frontend **durante** el piloto a partir de fricción observada sin convertir GSDLC-13 en un rediseño abierto ni permitir que ChatGPT/operador sustituyan el journey normal.

## Operating loop

`Owner usa DevPilot → observa tarea → mide → Run Packet → ChatGPT clasifica → decide → bounded corrective de DevPilot si aplica → Windows validation → selective retest → resume exact checkpoint`.

## Severidad

| Clase | Acción |
|---|---|
| UX-S0 | BLOCK inmediato; corrective obligatorio |
| UX-S1 | BLOCK checkpoint; corrective obligatorio |
| UX-S2 | corrective antes de cerrar segmento si afecta critical path; en otro caso owner disposition |
| UX-S3 | registrar; diferir por defecto a UX-P2 salvo cambio trivial/bajo riesgo |

## Waves integradas

- **P1-B / 13-B:** login/Home/Create/Project Context/Project Status/forms/long-operation feedback.
- **P1-C / 13-C:** Documents/Pre-code/Planning/progressive disclosure/copy Guided/traceability.
- **P1-D / 13-D:** Story/Code, Diff/Approval, Jobs, Quality, Git, Release, Recovery/Reconciliation, AI provenance.
- **P1-E / 13-E:** cerrar S0/S1, adjudicar S2, transferir S3 legítimos a UX-P2.

Finding heredado: `UX-P0-E-S3-001` — diferenciar visualmente engineering state y gate readiness; primero debe observarse en uso real.

## Métricas

- critical task completion without external operator: 100%;
- operator project writes: 0;
- normal-user terminal escapes: 0;
- S0/S1 abiertos al cierre del checkpoint: 0;
- first-attempt result;
- time-to-next-valid-action;
- confused/wrong-path moments y causa;
- keyboard/focus/responsive si la superficie fue modificada;
- confidence 1–5, objetivo >=3.

## Corrective policy

Un UX corrective modifica **DevPilot**, no el proyecto greenfield. Ejecuta Test Impact + focal/unit + affected browser checkpoint + route/auth/authority contracts pertinentes. No Full en 13-B..13-D. Si hay DevPilot source delta, produce successor Windows-validado y se sincroniza remoto antes de otra mutación DevPilot. Después se retesta solamente el checkpoint afectado.
