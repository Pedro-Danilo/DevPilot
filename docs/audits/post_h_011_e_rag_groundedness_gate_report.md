---
doc_id: "POST-H-011-E-AUDIT"
title: "POST-H-011-E — RAG groundedness ready gate report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-26"
approval: "approved_by_owner"
phase: "POST-FASE-H"
micro_sprint: "POST-H-011-E"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_web_search_used: true
no_llm_judge_required: true
source_of_truth: false
---

# POST-H-011-E — RAG groundedness ready gate report

## Propósito

Este reporte documenta la integración de RAG groundedness al quality gate local de DevPilot. El objetivo es que `quality-gate run --profile hardening` pueda verificar que la suite RAG groundedness es ejecutable, local, determinística, respaldada por fuentes citables y capaz de bloquear respuestas candidatas con `forbidden_claims`.

## Alcance implementado

```text
src/devpilot_core/rag/evals.py
src/devpilot_core/quality/gate.py
tests/test_rag_groundedness_ready_gate.py
docs/04_quality/rag_groundedness_eval_strategy.md
docs/post_h_011_e_manifest.json
```

El subgate `rag-groundedness-ready` ejecuta la suite sin escribir reportes en `outputs/evals`, valida cobertura de fuentes, soporte de claims, recuperación RAG local y bloqueo negativo de forbidden claims.

## Controles de seguridad

```text
network_used=false
external_api_used=false
web_search_used=false
llm_judge_used=false
embeddings_used=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
mutations_performed=false
source_mutations_performed=false
outputs_as_sources_allowed=false
```

## Criterios PASS

```text
PASS si cases_total >= 10.
PASS si source_coverage_avg cumple el umbral del gate.
PASS si claim_support_avg cumple el umbral del gate.
PASS si los casos con forbidden_claims bloquean con una respuesta candidata insegura.
PASS si el subgate aparece en perfiles hardening/industrial.
PASS si no se generan reportes runtime durante quality-gate.
```

## Criterios BLOCK

```text
BLOCK si la suite requiere provider externo.
BLOCK si outputs/evals se tratan como fuente canónica.
BLOCK si RAG se declara production-grade.
BLOCK si una respuesta con forbidden_claims pasa silenciosamente.
BLOCK si se usa web search, API externa o LLM judge por defecto.
```

## Resultado esperado

`POST-H-011-E` cierra `POST-H-011` como `implemented-initial`. La aplicación queda con una señal de calidad local para RAG groundedness, pero no con una declaración de producción completa. RAG sigue siendo una capacidad de recuperación y no reemplaza fuentes canónicas ni revisión humana en decisiones críticas.
