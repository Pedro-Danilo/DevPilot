---
doc_id: "POST-H-011-D-EVAL-RUNNER-REPORT"
title: "POST-H-011-D — Integración con RAG query y eval runner"
status: "approved"
owner: "Ordóñez"
updated: "2026-06-26"
source_of_truth: false
approval: "approved_by_owner"
---

# POST-H-011-D — Integración con RAG query y eval runner

## 1. Propósito

Este reporte documenta la implementación inicial de `POST-H-011-D — Integración con RAG query y eval runner`, dentro de `POST-H-011 — RAG groundedness evals`.

El micro-sprint conecta el RAG lexical local, el source coverage y el evaluator determinístico de claims en un runner operativo. La capacidad permite ejecutar la suite completa, un caso individual y un puente desde `eval run --suite rag-groundedness`.

## 2. Alcance implementado

```text
- Módulo src/devpilot_core/rag/evals.py.
- Clase RagGroundednessEvalRunner.
- Opciones RagGroundednessEvalRunOptions.
- Comando CLI rag groundedness-eval.
- Bridge eval run --suite rag-groundedness.
- Escritura opcional de outputs/evals/rag_groundedness_report.json y .md.
- Pruebas de runner, CLI, single-case, schema report y escritura de outputs/evals.
```

## 3. Fuera de alcance explícito

```text
- No se integra todavía con quality-gate.
- No se habilita LLM judge.
- No se habilitan embeddings externos, web search ni proveedores remotos.
- No se tratan outputs/evals como fuente versionable.
- No se declara RAG production-grade.
```

## 4. Seguridad y operación

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
source_mutations_performed=false
```

La escritura de reportes es explícita mediante `--write-report` y se restringe a `outputs/evals`. Estos archivos son runtime regenerable y deben excluirse de ZIPs limpios.

## 5. Criterios PASS cubiertos

```text
PASS si la suite corre offline.
PASS si reporta network_used=false y external_api_used=false.
PASS si el comando produce CommandResult estándar.
PASS si puede ejecutarse en CI local.
PASS si outputs/evals no se convierten en fuente versionable obligatoria.
```

## 6. Limitaciones preliminares

Esta versión es `implemented-initial`. La recuperación RAG sigue siendo lexical, y el matcher de claims sigue siendo determinístico. La integración con `quality-gate` y la documentación operativa final de límites RAG quedan para `POST-H-011-E`.
