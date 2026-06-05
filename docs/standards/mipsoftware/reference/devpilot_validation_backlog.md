---
title: Backlog de validación para DevPilot Local
doc_id: MIPS-REF-003
doc_type: reference
version: 0.1.0
status: reviewed
owner: AI_agents / MIPSoftware
scope: devpilot-validation
created: '2026-05-31'
updated: '2026-05-31'
---

# Backlog de validación para DevPilot Local

## 1. Objetivo

Convertir los artefactos de MIPSoftware en validadores, comandos y flujos asistidos dentro de DevPilot Local.

## 2. Backlog inicial

| ID | Épica | Historia | Evidencia esperada | Prioridad |
|---|---|---|---|---:|
| DPL-001 | Inicialización | Como usuario quiero crear un proyecto con estructura MIPSoftware. | `devpilot init-project` genera carpetas y documentos base. | Alta |
| DPL-002 | Pre-code gate | Como líder técnico quiero validar si un proyecto puede iniciar código. | `devpilot checklist pre-code` produce PASS/FAIL. | Alta |
| DPL-003 | Requerimientos | Como analista quiero validar requerimientos contra schema. | `devpilot validate requirement`. | Alta |
| DPL-004 | Arquitectura | Como arquitecto quiero validar ADRs y arquitectura mínima. | `devpilot validate architecture`. | Alta |
| DPL-005 | Seguridad | Como responsable de seguridad quiero validar threat model y privacy assessment. | `devpilot validate security`. | Alta |
| DPL-006 | Release | Como release manager quiero validar readiness de release. | `devpilot readiness-check`. | Alta |
| DPL-007 | MIASI | Como responsable IA quiero saber si un proyecto requiere MIASI. | `devpilot miasi-required`. | Alta |
| DPL-008 | Auditoría | Como auditor quiero generar reporte consolidado. | `devpilot audit project`. | Media |

## 3. Criterio mínimo de cierre

El MVP de DevPilot Local debe validar al menos:

- product vision;
- requerimiento;
- ADR;
- API contract;
- test case;
- threat model;
- release plan;
- production readiness.
