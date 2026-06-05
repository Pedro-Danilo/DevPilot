---
title: Refactoring Plan Template
doc_id: MIPS-TPL-REFACTORING-PLAN
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: maintenance-evolution-retirement
created: '2026-05-31'
updated: '2026-05-31'
---

# Refactoring Plan Template

## 1. Propósito

Planificar un refactoring controlado sin introducir cambios funcionales no trazados.

## 2. Resumen

| Campo | Valor |
|---|---|
| Área afectada |  |
| Tipo de refactoring | local / modular / arquitectónico / datos / agentic |
| Motivo |  |
| Owner |  |
| Riesgo | low / medium / high / critical |

## 3. Objetivo técnico

Describir qué se mejorará y cómo se medirá la mejora.

## 4. Alcance / fuera de alcance

| Incluido | Excluido |
|---|---|
|  |  |

## 5. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
|  |  |  |

## 6. Pruebas requeridas

- unit tests;
- integration tests;
- contract tests;
- regression tests;
- performance/security tests si aplica;
- evals MIASI si aplica.

## 7. Rollback

Describir estrategia para volver al estado anterior.

## 8. Criterios de rechazo

- no existen pruebas de regresión;
- se mezclan cambios funcionales sin requerimiento;
- no existe rollback para módulos críticos;
- no se actualizan ADRs cuando cambia arquitectura.
