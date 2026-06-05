---
title: "Usar docs-as-code como estrategia documental"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/adrs"
updated: "2026-05-31"
doc_type: "adr"
related_labs:
  - "LAB-AI-001..LAB-AI-080"
---
# ADR-0001 — Usar docs-as-code como estrategia documental

## Estado

Aceptada provisionalmente.

## Contexto

AI_agents produjo 80 laboratorios y múltiples artefactos técnicos. La fase aplicada requiere documentación versionable, auditable y revisable como parte del ciclo de vida del software.

## Decisión

La documentación MIASI se gestionará como código dentro del repositorio, usando Markdown, Git, revisiones por PR, changelog y estados documentales.

## Consecuencias positivas

- Trazabilidad entre decisiones, código y documentos.
- Posibilidad de revisión técnica.
- Base para validadores futuros.
- Menor riesgo de documentos desactualizados.

## Consecuencias negativas y riesgos

- Requiere disciplina de mantenimiento.
- Puede generar fricción inicial frente a documentos ofimáticos.
- Necesita convenciones claras para evitar dispersión.

## Criterios de cumplimiento

- Todo documento tiene frontmatter.
- Todo cambio relevante pasa por commit.
- Todo documento aprobado tiene versión.
- Todo documento normativo tiene criterios de cumplimiento.

## Relación con AI_agents

Continúa la práctica de trazabilidad, reportes, bitácora y quality gates desarrollada en LAB-AI-001 a LAB-AI-080.

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
