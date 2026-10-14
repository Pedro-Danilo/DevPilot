---
doc_id: DEVPL-MP-SUCCESSOR-132-PROJECT_ENGINEERING_STANDARDS_PROFILE_SCHEMA_132
title: "Estándares MIPSoftware/MIASI, perfiles y excepciones"
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

# Estándares MIPSoftware/MIASI, perfiles y excepciones

## Schema propuesto, a vincular a estándares versionados existentes

`profile_id`, `project_id`, `revision`, `state`, `source_intake_refs`, `project_risk_factors`, `domain`, `complexity`, `data_classification`, `deployment_profile`, `technology_decision_status`, `standards[{id,version,hash,scope,applicability,rationale}]`, `component_miasi_scopes`, `artifact_policy_refs`, `exceptions`, `approval_ref`, `effective_from`, `superseded_by`. Provisional con desconocidos; aprobado FROZEN no cambia in-place.

MIPSoftware `REQUIRED` para todo proyecto. MIASI `CONDITIONAL` sobre componentes inteligentes **del producto**: agents, tools, memory, RAG, model runtime, autonomy. Un LLM usado por DevPilot para producir código de una aplicación convencional no hace a dicha aplicación agéntica. Clasificación L puede **sugerir** factores, pero aplicabilidad normativa es determinística sobre hechos confirmados, con Owner approval y justificación.

## Waivers

`exception_id`, `control_ref`, `reason`, `risk`, `compensating_controls`, `owner`, `expires`, `review_trigger` y evidence. No permitir waiver genérico de seguridad/legal; riesgos emergentes reevalúan condiciones.

## Pruebas/gates

Web sencilla → MIASI N/A justificado; web con agente tool-write → MIASI y Tool/Agent/Approval Cards obligatorios. Nueva versión requiere successor y dependent impact, no reemplazo de hash FROZEN. Falta de riesgo confirmado → `UNKNOWN / REVIEW`, nunca `NOT_APPLICABLE` por omisión.

## No técnico

Es un perfil de ingeniería por proyecto, como una lista personalizada de controles basada en necesidades reales, no un requisito de redactar cincuenta documentos iguales.
