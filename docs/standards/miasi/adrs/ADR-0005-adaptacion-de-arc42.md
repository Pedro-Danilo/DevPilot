---
title: "Adaptar arc42 para documentación arquitectónica"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/adrs"
updated: "2026-05-31"
doc_type: "adr"
related_labs:
  - "LAB-AI-001..LAB-AI-080"
---
# ADR-0005 — Adaptar arc42 para documentación arquitectónica

## Estado

Aceptada provisionalmente.

## Contexto

Los sistemas agénticos necesitan documentación arquitectónica explícita: objetivos, contexto, restricciones, decisiones, componentes, runtime, despliegue, riesgos y deuda técnica.

## Decisión

MIASI adaptará arc42 como inspiración para documentos de arquitectura, sin copiarlo literalmente ni imponer su estructura completa cuando no aporte valor.

## Consecuencias positivas

- Estructura probada para arquitectura.
- Facilita decisiones y restricciones explícitas.
- Compatible con C4 y ADRs.
- Útil para proyectos aplicados reales.

## Consecuencias negativas y riesgos

- Puede ser demasiado pesado para prototipos.
- Requiere adaptar secciones al dominio agentic.
- No debe desplazar documentos de evaluación, seguridad u operación.

## Criterios de cumplimiento

- Todo proyecto aplicado debe documentar contexto, drivers, restricciones, decisiones, componentes, runtime, despliegue y riesgos.
- Las secciones se adaptan al tamaño del proyecto.
- Los documentos de arquitectura deben enlazar ADRs.

## Relación con AI_agents

Prepara DevPilot Local para producir documentación arquitectónica repetible.

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
