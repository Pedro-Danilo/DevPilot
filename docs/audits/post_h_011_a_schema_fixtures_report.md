---
doc_id: "POST-H-011-A-AUDIT"
title: "POST-H-011-A — Schema y fixtures de groundedness"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-26"
approval: "approved_by_owner"
---

# POST-H-011-A — Schema y fixtures de groundedness

## Resultado

`POST-H-011-A` queda implementado como `implemented-initial`. El micro-sprint aprueba el backlog `POST-H-011 — RAG groundedness evals`, crea los contratos JSON Schema para suites y reportes de groundedness, y registra un fixture inicial post-H con 10 casos locales.

## Alcance implementado

```text
docs/schemas/rag_groundedness_eval.schema.json
docs/schemas/rag_groundedness_report.schema.json
evals/fixtures/rag_groundedness_post_h_cases.json
tests/test_rag_groundedness_schema.py
tests/test_post_h_011_rag_groundedness.py
```

## Controles de seguridad

```text
local_first=true
dry_run=true
network_used=false
external_api_used=false
web_search_used=false
llm_judge_required=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
outputs_as_sources_allowed=false
```

## Cobertura funcional

La suite inicial cubre roadmap, seguridad, testing, arquitectura, onboarding, operaciones, release, RAG y governance. Incluye casos positivos y negativos con `forbidden_claims` para impedir sobreclaiming sobre remote execution, connector write, plugin execution, web search, publicación/despliegue real y uso de outputs como fuentes canónicas.

## Límites explícitos

Esta versión no ejecuta RAG, no calcula métricas de coverage, no produce reportes runtime y no integra quality-gate. Es una base contractual y de datos para que `POST-H-011-B/C/D/E` implementen extractor de citas, evaluador determinístico, comando CLI y gate.

## PASS/BLOCK

PASS si el fixture valida contra `RagGroundednessEval`, incluye al menos 10 casos, todas sus fuentes esperadas existen localmente y contiene casos negativos con `forbidden_claims`.

BLOCK si el fixture requiere web, APIs externas, LLM judge obligatorio, remote execution, connector write o plugin execution.
