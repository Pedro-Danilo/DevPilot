---
title: "Anexo de trazabilidad LAB-AI a MIASI"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/reference"
updated: "2026-05-31"
doc_type: "reference"
related_labs: "LAB-AI-001..LAB-AI-080"
---
# Anexo de trazabilidad LAB-AI a MIASI

## 1. Propósito

Relacionar los bloques de laboratorios AI_agents con capacidades de ingeniería y documentos MIASI.

## 2. Trazabilidad por bloque

| Laboratorios | Capacidades desarrolladas | Evidencia MIASI | Documentos |
|---|---|---|---|
| LAB-AI-001..002 | Agente mínimo, tool calling, memoria simple, ModelAdapter mock. | Base de Agent Contract y Tool Contract. | DOC-AI-002, DOC-AI-005 |
| LAB-AI-003..012 | Herramientas locales, RAG lexical, evaluación offline, trazas iniciales. | Tool Registry, Evaluation Standard, RAG baseline. | DOC-AI-003, DOC-AI-004, DOC-AI-005 |
| LAB-AI-013..030 | Embeddings, vector stores, RAG híbrido, memoria SQLite, observabilidad, MCP, multiagentes. | Knowledge Layer, Memory Layer, MCP integration, Multi-agent patterns. | DOC-AI-003, DOC-AI-005 |
| LAB-AI-031..050 | Repos, CI/CD local, contract testing, PR/MR summaries, quality gates. | Delivery Layer, CI/CD gates, repo analysis. | DOC-AI-004, DOC-AI-005 |
| LAB-AI-051..074 | Industrialización, APIs controladas, MCP real, OpenTelemetry, AgentOps histórico. | Observability, external adapters, operational evidence. | DOC-AI-003, DOC-AI-005 |
| LAB-AI-075 | Secret management local. | Secret control and redaction. | DOC-AI-005, control catalog |
| LAB-AI-076 | SAST/SBOM/dependency scanning. | Supply chain baseline. | DOC-AI-005, supply chain roadmap |
| LAB-AI-077 | Policy-as-code. | Policy gates. | DOC-AI-005, control catalog |
| LAB-AI-078 | Human approval workflow. | Human-in-the-loop controls. | DOC-AI-004, DOC-AI-005 |
| LAB-AI-079 | CI remoto sandbox. | Remote CI readiness. | DOC-AI-003, DOC-AI-007 |
| LAB-AI-080 | Integrador final. | Readiness baseline. | DOC-AI-002, DOC-AI-008 |

## 3. Criterio para auditoría formal futura

Una auditoría formal deberá expandir esta tabla a nivel de laboratorio individual, con:

- ruta de código;
- comandos;
- tests;
- outputs;
- documento MIASI relacionado;
- control MIASI asociado;
- estado de evidencia.
