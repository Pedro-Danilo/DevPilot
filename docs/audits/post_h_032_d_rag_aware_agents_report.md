---
doc_id: POST-H-032-D-RAG-AWARE-AGENTS-REPORT
title: POST-H-032-D — RAG-aware agents report
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: implemented-initial
---

# POST-H-032-D — RAG-aware agents report

## Resultado

`POST-H-032-D` queda implementado como primera versión local-first de agentes RAG-aware. La implementación genera un `RagAgentContextPack` determinístico para agentes seleccionados, con `source_ids`, citas locales, freshness y respuesta obligatoria `insufficient evidence` cuando no hay evidencia suficiente o cuando la consulta intenta justificar claims prohibidos.

## Capacidades agregadas

- Schema `RagAgentContextPack` registrado en `docs/schemas/rag_agent_context_pack.schema.json`.
- Bindings gobernados en `.devpilot/agents/rag_agent_bindings.json`.
- Módulo `src/devpilot_core/agents/rag_context.py`.
- CLI `python -m devpilot_core agent rag-context --json`.
- Boundary `ApplicationService.rag_agent_context`.
- Tests positivos y negativos en `tests/test_post_h_032_rag_aware_agents.py`.

## Controles de seguridad

- No usa LLM real.
- No usa red.
- No usa API externa.
- No lee ni escribe memoria.
- No ejecuta tools.
- No muta fuentes.
- No justifica claims prohibidos con RAG.
- Los reportes se escriben solo bajo `outputs/reports` y solo con `--write-report`.

## Criterios PASS

- Cada sugerencia grounded incluye fuentes y citas.
- Si no hay fuente suficiente o el claim está prohibido, la respuesta es `insufficient evidence`.
- El context pack valida contra schema.
- Las fuentes se filtran por allowlist local.
- Los negative cases pasan sin LLM judge.

## Limitaciones

Esta es una implementación `implemented-initial`. Usa el índice lexical RAG existente y validaciones determinísticas. No promueve todavía los agentes a ejecución autónoma RAG dentro de cada clase de agente ni agrega embeddings semánticos. Esa evolución deberá mantener los mismos gates: source ids, citas, insufficient evidence, allowlist local y cero API externa por defecto.

## Validación focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_032_rag_aware_agents.py `
  tests/test_rag_local.py `
  tests/test_post_h_011_rag_groundedness.py `
  tests/test_rag_groundedness_claims.py `
  tests/test_rag_groundedness_eval_runner.py `
  tests/test_rag_citations_source_coverage.py `
  tests/test_sdlc_agents.py `
  tests/test_release_agent.py `
  -q
```

## Comandos CLI

```powershell
python -m devpilot_core agent rag-context --json
python -m devpilot_core agent rag-context --json --write-report
python -m devpilot_core schema validate --schema-id RagAgentContextPack --instance outputs\reports\rag_agent_context_pack.json --json
```
