---
title: Template — Traceability Matrix
doc_id: MIPS-TPL-TRACEABILITY_MATRIX
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
domain: requirements-engineering
model: MIPSoftware — Modelo de Ingeniería Profesional de Software
---

# Traceability Matrix

## Propósito

Conectar objetivos, requerimientos, historias, arquitectura, pruebas, riesgos y releases.

## Campos obligatorios

| Campo | Descripción |
|---|---|
| Objetivo de negocio | OBJ-000 |
| Requerimiento | FR/NFR/SEC/OPS/etc. |
| Historia / Caso de uso | US/UC |
| Regla de negocio | RULE |
| ADR / componente | ADR/C4/component |
| Prueba | TEST |
| Riesgo | RISK |
| Release | versión |
| Estado | planned/implemented/verified/released |

## Ejemplo completo

| Objetivo | Requerimiento | Historia/Caso | Regla | Arquitectura | Prueba | Riesgo | Release | Estado |
|---|---|---|---|---|---|---|---|---|
| OBJ-001 | FR-001 | US-001 | RULE-001 | ADR-002 | TEST-001 | RISK-003 | v0.1.0 | planned |

## Criterios de revisión

- Ningún requerimiento Must queda sin prueba.
- Todo riesgo crítico tiene control.
- Todo release tiene requerimientos verificables.
- Todo requerimiento IA/agente referencia MIASI.

## Criterios de rechazo

- Filas sin prueba.
- Requerimientos sin objetivo.
- Componentes implementados sin requerimiento.
