---
doc_id: "POST-H-011-RAG-GROUNDEDNESS-EVAL-STRATEGY"
title: "RAG groundedness eval strategy"
status: "approved"
owner: "Ordóñez"
updated: "2026-06-26"
source_of_truth: false
approval: "approved_by_owner"
---

# RAG groundedness eval strategy

## 1. Propósito

Este documento resume la estrategia inicial de evaluación de groundedness RAG para DevPilot Local al cierre de `POST-H-011-E`. La estrategia es local-first, determinística y orientada a evidencia: una respuesta o recomendación asistida por RAG solo debe considerarse aceptable si está respaldada por fuentes locales citables, vigentes y trazables.

## 2. Pipeline de evaluación

```text
Fixture POST-H-011-A
  -> Citation/source coverage POST-H-011-B
  -> Deterministic claim groundedness POST-H-011-C
  -> RAG query + eval runner integration POST-H-011-D
  -> Quality-gate integration POST-H-011-E [implemented-initial]
```

## 3. Comandos disponibles al cierre de POST-H-011-E

```powershell
python -m devpilot_core rag groundedness-eval --suite evals/fixtures/rag_groundedness_post_h_cases.json --json
python -m devpilot_core rag groundedness-eval --suite evals/fixtures/rag_groundedness_post_h_cases.json --case-id rag-posth-roadmap-prioritized-hitos --json
python -m devpilot_core rag groundedness-eval --suite evals/fixtures/rag_groundedness_post_h_cases.json --write-report --json
python -m devpilot_core eval run --suite rag-groundedness --json
```

## 4. Reportes runtime

Cuando se usa `--write-report`, DevPilot genera:

```text
outputs/evals/rag_groundedness_report.json
outputs/evals/rag_groundedness_report.md
```

Estos artefactos son runtime regenerable, deben omitirse de ZIPs limpios y no son fuentes versionables. La fuente autoritativa sigue siendo la documentación gobernada por `.devpilot/docs_governance/source_registry.json`.

## 5. Métricas iniciales

```text
source_coverage_avg
claim_support_avg
unsupported_claims_total
missing_sources_total
stale_sources_total
forbidden_claims_detected_total
queries_total
queries_with_sources_total
query_failures_total
```

## 6. Límites explícitos

```text
- El RAG local sigue siendo lexical y preliminar.
- No hay LLM judge obligatorio.
- No hay embeddings externos ni vector DB obligatoria.
- No hay web search ni APIs externas.
- No hay remote execution, connector write ni plugin execution.
- La integración con quality-gate queda implementada como subgate `rag-groundedness-ready` en los perfiles `hardening` e `industrial`.
```

## 7. Evolución esperada

POST-H-011-E deberá integrar este runner en `quality-gate`, documentar límites para operadores y bloquear el uso de RAG como fuente de verdad cuando no exista soporte documental suficiente.

## 8. Quality-gate integration

`POST-H-011-E` agrega el subgate `rag-groundedness-ready` al quality gate. El subgate:

```text
- ejecuta la suite sin escribir outputs/evals;
- valida source_coverage y claim_support;
- valida que rag query recupere fuentes locales;
- verifica que al menos un caso con forbidden_claims bloquee con una respuesta sintética insegura;
- bloquea uso de red, APIs externas, web search, LLM judge o outputs como fuentes canónicas.
```

Comando:

```powershell
python -m devpilot_core quality-gate run --profile hardening --json
```

## 9. Regla de autoridad

RAG es una ayuda de recuperación, no una fuente de verdad. Una respuesta RAG solo es aceptable cuando puede citar fuentes locales gobernadas; la autoridad final permanece en los documentos y registros declarados en `.devpilot/docs_governance/source_registry.json`. Los reportes bajo `outputs/evals` son evidencia runtime regenerable.

