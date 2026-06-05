---
title: "Checklists MIASI — controles de producción"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
updated: "2026-05-31"
related_documents:
  - "01_modelo_ingenieria_sistemas_agenticos.md"
  - "02_arquitectura_referencia.md"
  - "03_agentic_sdlc.md"
  - "04_estandares_tecnicos_transversales.md"
related_labs: "LAB-AI-001..LAB-AI-080"
related_projects:
  - "DevPilot Local"
  - "FreelanceOps Agent"
  - "MicroVenta Agent"
doc_type: "reference"
scope: "engineering-model-checklists"
audience:
  - "arquitectos de sistemas agénticos"
  - "desarrolladores de agentes IA"
  - "responsables de seguridad, evaluación y operación"
---
# Checklists MIASI — controles de producción

Esta carpeta contiene checklists orientados a revisión, auditoría y promoción de agentes IA hacia operación controlada.

## Índice

| Checklist | Gate principal |
|---|---|
| checklist_agent_design.md | Diseño de agente. |
| checklist_tool_safety.md | Seguridad de herramientas. |
| checklist_rag_grounding.md | Grounding y citas. |
| checklist_memory_safety.md | Memoria segura. |
| checklist_eval_readiness.md | Evaluación y regresión. |
| checklist_security_readiness.md | Seguridad integral. |
| checklist_observability_readiness.md | Observabilidad. |
| checklist_human_approval.md | Aprobación humana. |
| checklist_ci_cd.md | CI/CD agentic. |
| checklist_pre_production.md | Pre-producción. |
| checklist_post_deployment.md | Post-despliegue. |

## Regla de bloqueo

Todo ítem obligatorio sin evidencia se considera `FAIL`. Todo `FAIL` en seguridad, evaluación, permisos, observabilidad o aprobación humana bloquea promoción hasta remediación o aceptación formal del riesgo.
