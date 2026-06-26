---
doc_id: "POST-H-011-B-AUDIT"
title: "POST-H-011-B — Citation extractor y source coverage"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-26"
approval: "approved_by_owner"
---

# POST-H-011-B — Citation extractor y source coverage

## Resultado

`POST-H-011-B` queda implementado como `implemented-initial`. El micro-sprint agrega una capa local y determinística para extraer evidencia citable de fuentes RAG y calcular `source_coverage` por caso de fixture.

## Alcance implementado

```text
src/devpilot_core/rag/citations.py
tests/test_rag_citations_source_coverage.py
```

También se actualiza `RagGroundednessReport` para admitir reportes generados por `POST-H-011-B` y campos opcionales de evidencia de fuentes (`matched_sources`, `missing_sources`, `stale_sources`, `citation_refs`).

## Capacidades

```text
- Normalización segura de paths locales.
- Rechazo de URLs remotas y runtime outputs como fuentes canónicas.
- Extracción de doc_id, status, updated, headings y snippets.
- Uso de docs_index cuando existe.
- Fallback a lectura directa de documentos locales cuando docs_index no existe.
- Detección de fuentes faltantes.
- Detección de fuentes stale/deprecated por metadata local.
- Cálculo de source_coverage por caso.
- Reporte in-memory compatible con RagGroundednessReport.
```

## Seguridad

```text
local_first=true
dry_run=true
network_used=false
external_api_used=false
web_search_used=false
llm_judge_used=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
mutations_performed=false
source_mutations_performed=false
outputs_as_sources_allowed=false
```

## PASS/BLOCK

PASS si las fuentes esperadas existen, son locales, no son runtime outputs, no están stale/deprecated y la cobertura supera el umbral del caso.

BLOCK si una fuente es remota, sale del workspace, apunta a `outputs/`, no existe, está stale/deprecated o la cobertura queda por debajo del umbral.

## Límites

Esta versión no evalúa `required_claims`, `forbidden_claims`, claim support ni unsupported claims. Tampoco añade el comando CLI `rag groundedness-eval` ni integra quality-gate. Es una base de evidencia para `POST-H-011-C/D/E`.
