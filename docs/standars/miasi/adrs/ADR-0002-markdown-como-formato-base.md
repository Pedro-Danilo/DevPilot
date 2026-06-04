---
title: "Usar Markdown como formato base"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/adrs"
updated: "2026-05-31"
doc_type: "adr"
related_labs:
  - "LAB-AI-001..LAB-AI-080"
---
# ADR-0002 — Usar Markdown como formato base

## Estado

Aceptada provisionalmente.

## Contexto

La documentación debe ser legible en Git, editable en cualquier IDE, convertible a HTML/PDF/DOCX y fácil de procesar por agentes.

## Decisión

Markdown será el formato fuente principal de MIASI. Los formatos PDF, HTML o DOCX serán derivados, no fuente primaria.

## Consecuencias positivas

- Bajo costo de mantenimiento.
- Compatible con GitHub/GitLab.
- Fácil integración con Mermaid, frontmatter y generadores estáticos.
- Fácil consumo por agentes RAG/documentales.

## Consecuencias negativas y riesgos

- Menor control visual que DOCX.
- Requiere convenciones para tablas extensas y diagramas.
- Exportaciones pueden requerir tooling adicional.

## Criterios de cumplimiento

- Los archivos fuente se mantienen en `.md`.
- Cada documento tiene frontmatter YAML.
- Los diagramas preferidos son Mermaid.
- Las exportaciones no reemplazan al Markdown fuente.

## Relación con AI_agents

Conecta con la filosofía local-first y reproducible del proyecto.

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
