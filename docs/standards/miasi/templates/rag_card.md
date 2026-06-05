---
title: "RAG Card — ficha operativa de recuperación documental"
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
doc_type: "template"
scope: "engineering-model-template"
audience:
  - "arquitectos de sistemas agénticos"
  - "desarrolladores de agentes IA"
  - "responsables de seguridad, evaluación y operación"
---
# RAG Card — ficha operativa de recuperación documental

## 1. Propósito

Define cómo un agente recupera, cita y usa conocimiento externo o interno mediante RAG lexical, semántico o híbrido.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Al conectar documentos a un agente.
- Al crear corpus indexado.
- Al exigir respuestas con citas.
- Al auditar groundedness.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| rag_id | Identificador del flujo RAG. | Convención `rag.<dominio>.<corpus>`. |
| corpus | Fuentes documentales. | Rutas, formato, propietario, fecha. |
| ingestion_policy | Cómo se ingieren documentos. | Parser, chunking, metadata. |
| retrieval_strategy | Estrategia de recuperación. | lexical/semantic/hybrid. |
| citation_policy | Reglas de citación. | Fuente, línea/página, fragmento. |
| grounding_eval | Evaluación de grounding. | Métricas y thresholds. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| reranking | Estrategia de reranking. | Cuando haya muchos documentos. |
| freshness_policy | Política de frescura. | Cuando la información cambia. |
| access_control | Control de acceso por documento. | Para datos privados. |

## 5. Ejemplo completo

```yaml
rag_id: rag.devpilot.repo_docs
owner: AI_agents
status: draft
corpus:
  - path: docs/
    format: markdown
    sensitivity: internal
  - path: README.md
    format: markdown
    sensitivity: public
ingestion_policy:
  chunk_size: 900
  chunk_overlap: 120
  metadata: [source_path, heading, modified_at]
retrieval_strategy: hybrid
citation_policy:
  required: true
  citation_format: source_path#heading
grounding_eval:
  metrics: [context_precision, answer_groundedness, citation_coverage]
  min_groundedness: 0.85
```

## 6. Criterios de revisión

- Las fuentes son explícitas.
- El agente no inventa citas.
- Se evalúa groundedness.
- Se declaran permisos por corpus.
- Hay política de actualización.

## 7. Criterios de rechazo o bloqueo

- Corpus ambiguo.
- Sin política de citas.
- No evalúa recuperación.
- Mezcla datos privados sin control.
- Usa documentos obsoletos sin advertencia.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 6 — Diseño de datos, memoria y RAG | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 8 — Diseño de evaluación | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 11 — Evaluación offline | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 16 — Operación y monitoreo | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| corpus_declared | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| retrieval_strategy_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| citation_policy_required | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| grounding_eval_pass | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| access_control_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

## 10. Criterios de automatización futura en DevPilot Local

- Debe poder convertirse en formulario validable.
- Debe poder serializarse a YAML/JSON.
- Debe poder enlazarse con `run_id`, `agent_id`, `tool_id`, `eval_id` o `release_id`.
- Debe poder participar en un `readiness-check` automático.
- Debe conservar historial de cambios por Git.



## 11. Referencias base

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
