---
title: "Templates MIASI — plantillas operativas"
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
scope: "engineering-model-templates"
audience:
  - "arquitectos de sistemas agénticos"
  - "desarrolladores de agentes IA"
  - "responsables de seguridad, evaluación y operación"
---
# Templates MIASI — plantillas operativas

Esta carpeta contiene las plantillas reutilizables de MIASI. Cada plantilla está diseñada para convertirse posteriormente en formulario, validador o comando de DevPilot Local.

## Índice

| Plantilla | Propósito |
|---|---|
| agent_card.md | Contrato operativo de agente. |
| tool_card.md | Contrato de herramienta y side effects. |
| model_card.md | Uso de modelo/proveedor/adaptador. |
| rag_card.md | Diseño y evaluación de RAG. |
| memory_card.md | Persistencia, retención y privacidad de memoria. |
| eval_card.md | Evaluación y regresión. |
| policy_card.md | Policy-as-code para decisiones allow/block/approval. |
| human_approval_card.md | Flujo de aprobación humana. |
| observability_card.md | Trazas, logs, métricas y eventos. |
| deployment_card.md | Despliegue, rollback y monitoreo. |
| incident_report.md | Registro de incidentes y postmortem. |
| adr_template.md | Decisiones arquitectónicas. |
| runbook_template.md | Operación y soporte. |
| risk_register.md | Riesgos y mitigaciones. |
| threat_model.md | Amenazas y mitigaciones. |
| cost_budget.md | Costos, límites y alertas. |
| data_handling_sheet.md | Tratamiento de datos. |
| production_readiness_checklist.md | Readiness previo a operación. |

## Regla de uso

Una plantilla MIASI incompleta no debe usarse como evidencia de readiness. Si un campo obligatorio no aplica, debe justificarse explícitamente con `not_applicable_reason`.
