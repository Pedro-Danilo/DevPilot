---
title: "Checklist — diseño de agente IA"
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
doc_type: "checklist"
scope: "engineering-model-checklist"
audience:
  - "arquitectos de sistemas agénticos"
  - "desarrolladores de agentes IA"
  - "responsables de seguridad, evaluación y operación"
---
# Checklist — diseño de agente IA

## 1. Propósito

Este checklist convierte los estándares MIASI en criterios verificables para revisión manual, revisión por pull request o automatización futura en DevPilot Local. Cada ítem debe tener evidencia concreta; una respuesta verbal no es suficiente para aprobar un gate.

## 2. Criterios de uso

- Usar durante el Agentic SDLC en la fase correspondiente.
- Adjuntar evidencia en el pull request, release o carpeta de artefactos.
- Marcar como `FAIL` cualquier ítem obligatorio sin evidencia.
- Registrar excepciones en Risk Register o ADR, nunca en comentarios informales.

## 3. Checklist

| Ítem | Descripción | Obligatorio/Opcional | Evidencia requerida | Responsable | Criterio PASS | Criterio FAIL | Referencia |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AD-001 | Agent Card completa | Obligatorio | agent_card.md con propósito, alcance y owner | Arquitecto agente | Agent Card revisada | Falta propósito o alcance | 01,03,04 |
| AD-002 | Nivel de autonomía A0-A7 justificado | Obligatorio | autonomy_level y controles | Arquitecto agente | Controles acordes al nivel | Autonomía alta sin controles | 01 |
| AD-003 | Herramientas declaradas | Obligatorio | Tool Cards enlazadas | Tech Lead | Todas las tools tienen contrato | Tools sin schema o permisos | 04 |
| AD-004 | Estrategia de modelo definida | Obligatorio | Model Card / ModelAdapter config | ML/AI Engineer | Ruta mock/local/API clara | Proveedor único obligatorio | 04 |
| AD-005 | Límites y exclusiones explícitos | Obligatorio | Sección scope/excludes | Product Owner | No hay ambigüedad crítica | El agente promete capacidades abiertas | 01 |
| AD-006 | Plan de evaluación definido | Obligatorio | Eval Card | Eval Owner | Métricas y thresholds definidos | Sin evaluación offline | 03,04 |
| AD-007 | Observabilidad definida | Obligatorio | Observability Card | SRE/AgentOps | Run/tool/policy events trazados | Sin trazas | 04 |
| AD-008 | Security gates asociados | Obligatorio | Policy Card/Risk Register | Security Reviewer | Acciones críticas controladas | Side effects sin gate | 04 |

## 4. Criterios de bloqueo

- Cualquier ítem obligatorio con `FAIL` bloquea promoción a operación controlada.
- Cualquier secreto, token o credencial en evidencia bloquea inmediatamente.
- Cualquier acción destructiva sin aprobación humana bloquea inmediatamente.
- Cualquier integración externa sin política de datos, costo y permisos bloquea inmediatamente.

## 5. Salida esperada

```yaml
checklist_id: checklist_agent_design
status: pass | fail | blocked
reviewer: <rol/persona>
review_date: YYYY-MM-DD
failed_items: []
linked_evidence: []
exceptions: []
```

## 6. Referencias base

- OpenAI Agents SDK — Agents, tools, handoffs, guardrails, tracing and human review. https://developers.openai.com/api/docs/guides/agents
- LangGraph durable execution, persistence and human-in-the-loop. https://docs.langchain.com/oss/python/langgraph/durable-execution
- Model Context Protocol Specification — resources, prompts and tools. https://modelcontextprotocol.io/specification/2025-06-18
- OpenTelemetry Semantic Conventions for GenAI systems and agents. https://opentelemetry.io/docs/specs/semconv/gen-ai/
- Microsoft Foundry Agent Evaluators. https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/agent-evaluators
- OWASP Top 10 for LLM Applications. https://owasp.org/www-project-top-10-for-large-language-model-applications/
- NIST AI Risk Management Framework. https://www.nist.gov/itl/ai-risk-management-framework
- NIST SSDF SP 800-218. https://csrc.nist.gov/pubs/sp/800/218/final
- SLSA — Supply-chain Levels for Software Artifacts. https://slsa.dev/
- CycloneDX Software Bill of Materials. https://cyclonedx.org/
