---
title: "Checklist — aprobación humana"
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
# Checklist — aprobación humana

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
| HA-001 | Acciones que requieren aprobación identificadas | Obligatorio | Policy Card | Security Reviewer | Lista clara | Críticos no identificados | LAB-AI-078 |
| HA-002 | Approval Card por acción crítica | Obligatorio | human_approval_card.md | Approver | Solicitud trazable | Aprobación verbal | 13 |
| HA-003 | Separación de funciones | Obligatorio | requester != approver | Security Reviewer | No autoaprobación | Solicitante aprueba | 13 |
| HA-004 | TTL definido | Obligatorio | ttl | Approver | Expira correctamente | Aprobación eterna | 13 |
| HA-005 | Evidencia enlazada | Obligatorio | reports/traces/tests | Approver | Decisión informada | Sin evidencia | 13 |
| HA-006 | Token redactado | Obligatorio | logs/traces | SRE | No aparece token | Token visible | 13 |
| HA-007 | Decisión registrada | Obligatorio | approval decision event | AgentOps | approved/denied/wait/expired | Decisión no auditable | 13 |
| HA-008 | Rollback requerido para acciones irreversibles | Obligatorio | rollback_plan | Release Manager | Rollback o bloqueo | Acción irreversible aprobada | 15 |

## 4. Criterios de bloqueo

- Cualquier ítem obligatorio con `FAIL` bloquea promoción a operación controlada.
- Cualquier secreto, token o credencial en evidencia bloquea inmediatamente.
- Cualquier acción destructiva sin aprobación humana bloquea inmediatamente.
- Cualquier integración externa sin política de datos, costo y permisos bloquea inmediatamente.

## 5. Salida esperada

```yaml
checklist_id: checklist_human_approval
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
