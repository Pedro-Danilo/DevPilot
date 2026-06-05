---
title: "Usar C4 y Mermaid para arquitectura y diagramas"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/adrs"
updated: "2026-05-31"
doc_type: "adr"
related_labs:
  - "LAB-AI-001..LAB-AI-080"
---
# ADR-0003 — Usar C4 y Mermaid para arquitectura y diagramas

## Estado

Aceptada provisionalmente.

## Contexto

Los proyectos aplicados requerirán comunicar arquitectura a distintos niveles: negocio, sistema, contenedores, componentes y flujos.

## Decisión

MIASI usará C4 como modelo conceptual de visualización y Mermaid como formato liviano para diagramas embebidos en Markdown.

## Consecuencias positivas

- Diagramas versionables.
- Lectura directa en plataformas Git.
- Niveles de zoom claros.
- No exige herramientas propietarias.

## Consecuencias negativas y riesgos

- Mermaid no cubre todos los casos avanzados.
- C4 requiere disciplina para no mezclar niveles.
- Algunos diagramas complejos podrían necesitar PlantUML en el futuro.

## Criterios de cumplimiento

- Todo sistema aplicado debe tener al menos C1 y C2.
- Los diagramas deben vivir junto al documento.
- Cada diagrama debe tener propósito y audiencia.
- No se deben incluir diagramas sin decisión arquitectónica asociada.

## Relación con AI_agents

Formaliza la arquitectura iniciada en los laboratorios de RAG, seguridad, observabilidad, CI/CD e integración final.

## Revisión futura

Esta ADR debe revisarse cuando MIASI llegue a versión `1.0.0` o cuando DevPilot Local empiece a validar documentos automáticamente.


## Referencias externas base

- ISO/IEC 42001:2023 — Artificial intelligence management systems. https://www.iso.org/standard/42001
- NIST AI Risk Management Framework. https://www.nist.gov/itl/ai-risk-management-framework
- NIST AI 600-1 — Generative AI Profile. https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- OWASP Top 10 for Large Language Model Applications. https://owasp.org/www-project-top-10-for-large-language-model-applications/
- OpenTelemetry Semantic conventions for generative AI systems. https://opentelemetry.io/docs/specs/semconv/gen-ai/
- Model Context Protocol Specification. https://modelcontextprotocol.io/specification/2025-06-18
- OpenAI Agents SDK — Agents, handoffs, guardrails and human review. https://developers.openai.com/api/docs/guides/agents
- LangGraph durable execution and persistence. https://docs.langchain.com/oss/python/langgraph/durable-execution
- Microsoft Foundry Agent Evaluators. https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/agent-evaluators
- arc42 Architecture Documentation. https://arc42.org/
- C4 Model. https://c4model.com/
- Diátaxis documentation framework. https://diataxis.fr/
- NIST SP 800-218 Secure Software Development Framework. https://csrc.nist.gov/pubs/sp/800/218/final
- SLSA — Supply-chain Levels for Software Artifacts. https://slsa.dev/
- OWASP CycloneDX. https://cyclonedx.org/
