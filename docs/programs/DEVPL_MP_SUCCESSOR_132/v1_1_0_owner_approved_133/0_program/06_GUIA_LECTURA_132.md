---
doc_id: DEVPL-MP-SUCCESSOR-132-06_GUIA_LECTURA_132
title: "Ruta sugerida de lectura para entender el programa completo"
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

# Ruta sugerida de lectura para entender el programa completo

## Lectura por capas, sin sobrecarga inicial

**1 — El porqué (15–30 min):** `00_LEEME`, `01_PROGRAMA_MAESTRO`, `02_ROADMAP`. Comprender el producto, el estado real y los hitos R0–R10.

**2 — Lo que no se puede hacer todavía:** `03_SUPERSESSION...`, `04_DECISIONES_PENDIENTES...`, `2_contratos/PROGRAM_AUTHORITY_AND_DECISION_REGISTER`. Reconocer diferencia entre aprobar programa, implementar, promover Git, contratar API y aceptar producto.

**3 — Arquitectura central:** primero ADR-004 (D/L/E), ADR-005 (candidate), ADR-001 (estándares), ADR-002 (documentos), ADR-003 (cambio), ADR-007 (Settings), ADR-008 (Git), ADR-011 (UI). Después ADR-006 (layout), ADR-009 agents y ADR-010 external condicionales.

**4 — Qué producirá DevPilot:** `PROJECT_ENGINEERING_STANDARDS_PROFILE_SCHEMA`, `ARTIFACT_CATALOG_AND_COVERAGE_CONTRACT`, `DOCUMENT_PUBLICATION_AND_VERSIONING_CONTRACT`, `CHANGE_IMPACT_AND_SUCCESSOR_CONTRACT`. Imaginar el recorrido de un proyecto desde idea hasta mantenimiento.

**5 — Cómo lo producirá y gobernará:** `GENERATION_ROUTE_POLICY_CONTRACT`, `MODEL_CAPABILITY_AND_EVAL_CONTRACT`, `CONFIGURATION_AUTHORITY_MATRIX`, `3_gobernanza/00_AUDIT_FIRST...` y `2_contratos/PROGRAM_ACCEPTANCE_AND_MATURITY_MATRIX`.

**6 — Prueba real:** `5_pilotos/PILOT_B_CHARTER` y, luego, `PILOT_C`. Ver lo que debe ocurrir dentro de la interfaz y qué no es evidencia suficiente.

**7 — Orden de construcción:** `4_backlogs/00_INDEX` y R0…R10 (leer primero R0/R1/R2; el resto como referencia progresiva), `PROGRAM_DEPENDENCY_REGISTER`, `3_gobernanza/01_RIESGOS`.

**8 — Auditoría de decisiones e historia:** `0_program/05_CONTROL...`, `6_trazabilidad/00_FUENTES`, `01_SUPERSESSION`, `02_HALLAZGOS`; por último el manifiesto.

## Para un lector no técnico

PESP = la lista de normas que debe respetar un proyecto concreto; Coverage Gate = control que impide avanzar si falta algo realmente obligatorio; Candidate = propuesta que aún no ha modificado el proyecto; FROZEN = versión aprobada inmutable; Successor = versión nueva que conserva la anterior; Worktree = carpeta de trabajo distinta que comparte el mismo repositorio Git; Egress = envío de información a servicios externos.
