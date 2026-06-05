---
title: "Usar Diátaxis para clasificar documentación"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/adrs"
updated: "2026-05-31"
doc_type: "adr"
related_labs:
  - "LAB-AI-001..LAB-AI-080"
---
# ADR-0004 — Usar Diátaxis para clasificar documentación

## Estado

Aceptada provisionalmente.

## Contexto

Una misma carpeta documental debe servir para aprender, operar, consultar contratos técnicos y entender decisiones. Mezclar estos fines reduce claridad.

## Decisión

MIASI adoptará Diátaxis para separar tutoriales, guías how-to, referencia técnica y explicaciones.

## Consecuencias positivas

- Mejora navegación documental.
- Evita documentos enormes sin propósito claro.
- Permite que DevPilot Local consuma documentos según tarea.

## Consecuencias negativas y riesgos

- Puede requerir duplicar enlaces entre documentos.
- Exige clasificar cada archivo correctamente.

## Criterios de cumplimiento

- Todo documento declara `doc_type`.
- Cada documento responde a una necesidad dominante.
- Los tutoriales no reemplazan referencia normativa.
- Las explicaciones no sustituyen checklists operativos.

## Relación con AI_agents

Da estructura profesional a la ruta de capacitación acumulada.

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
