---
doc_id: "POST-H-011-C-CLAIM-GROUNDEDNESS-REPORT"
title: "POST-H-011-C — Evaluador determinístico de claims"
status: "approved"
owner: "Ordóñez"
updated: "2026-06-26"
source_of_truth: false
approval: "approved_by_owner"
---

# POST-H-011-C — Evaluador determinístico de claims

## 1. Propósito

Este reporte documenta la implementación inicial de `POST-H-011-C — Evaluador determinístico de claims`, dentro del hito `POST-H-011 — RAG groundedness evals`.

El micro-sprint agrega una capa local para validar `required_claims` y `forbidden_claims` sin depender de LLM judge, web search, embeddings externos, APIs remotas, conectores o plugins. La fuente autoritativa sigue siendo la documentación local gobernada; la respuesta RAG no se trata como fuente de verdad.

## 2. Alcance implementado

```text
- Módulo src/devpilot_core/rag/groundedness.py.
- Clase RagGroundednessEvaluator.
- Opciones GroundednessOptions, incluyendo strict y candidate_answers.
- Claim support determinístico contra fuentes locales esperadas.
- Detección de unsupported_claims.
- Detección bloqueante de forbidden_claims en respuestas candidatas.
- Reporte in-memory compatible con RagGroundednessReport.
- Pruebas de casos PASS, unsupported claims, forbidden claims y modo no estricto.
```

## 3. Fuera de alcance explícito

```text
- No se añade todavía el comando CLI rag groundedness-eval.
- No se escriben outputs/evals/rag_groundedness_report.json ni .md.
- No se integra todavía con eval runner.
- No se integra todavía con quality-gate.
- No se usa LLM judge ni web search.
```

La integración CLI y persistencia de reportes queda para `POST-H-011-D`, según la separación de responsabilidades del backlog. La línea de validación que mencionaba CLI en `POST-H-011-C` se trata como una inconsistencia heredada del backlog y se corrige documentalmente para evitar invadir el alcance de `POST-H-011-D`.

## 4. Seguridad y operación

```text
local_first=true
dry_run=true
read_only=true
network_used=false
external_api_used=false
web_search_used=false
llm_judge_used=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
mutations_performed=false
source_mutations_performed=false
```

## 5. Criterios PASS cubiertos

```text
PASS si required_claims se evalúan con umbral configurable.
PASS si forbidden_claims generan BLOCK cuando aparecen en respuesta candidata.
PASS si unsupported_claims aparecen en reporte.
PASS si no se usa LLM judge por defecto.
PASS si los casos del fixture post-H alcanzan claim_support suficiente contra fuentes locales.
```

## 6. Limitaciones preliminares

Esta versión es `implemented-initial`. El matcher de claims es lexical determinístico con normalización y variantes simples. No sustituye una evaluación semántica avanzada ni una revisión humana para decisiones críticas. En fases posteriores puede ampliarse con reglas por dominio, evidence spans más precisos, citation precision y evaluadores semánticos locales opcionales.

## 7. Próximo paso

`POST-H-011-D — Integración con RAG query y eval runner`: conectar el evaluator con CLI, ejecución de suite/caso individual y escritura local de reportes en `outputs/evals/`.
