---
title: Technical Debt Register Template
doc_id: MIPS-TPL-TECHNICAL-DEBT-REGISTER
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: maintenance-evolution-retirement
created: '2026-05-31'
updated: '2026-05-31'
---

# Technical Debt Register Template

## 1. Propósito

Registrar, priorizar y gobernar deuda técnica.

## 2. Registro

| ID | Fecha | Tipo | Descripción | Módulo | Severidad | Impacto | Riesgo | Owner | Acción | Fecha objetivo | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TD-001 |  | arquitectura/código/testing/seguridad/datos/operación/IA |  |  | low/medium/high/critical |  |  |  |  |  | open |

## 3. Criterios de severidad

| Severidad | Definición | Acción |
|---|---|---|
| Critical | Bloquea seguridad, datos, operación o evolución crítica. | Bloquear release o remediar. |
| High | Riesgo alto acumulativo. | Plan con fecha. |
| Medium | Afecta mantenibilidad. | Priorizar. |
| Low | Mejora deseable. | Agrupar. |

## 4. Relación con quality gates

- Toda deuda `critical` debe bloquear release salvo excepción aprobada.
- Toda deuda `high` debe tener owner y fecha objetivo.
- Toda deuda de seguridad debe conectarse con `vulnerability_register.md`.
- Toda deuda agentic debe activar MIASI.
