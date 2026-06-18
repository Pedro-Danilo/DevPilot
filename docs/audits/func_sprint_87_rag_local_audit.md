---
title: "Auditoría FUNC-SPRINT-87 — RAG documental local MVP"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-87"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-87"
updated: "2026-06-18"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-87 — RAG documental local MVP

## Estado

`implemented-initial`.

## Propósito

Validar que DevPilot incorpora RAG documental local sin introducir dependencias externas, embeddings obligatorios, red, API, secretos crudos ni respuestas sin fuentes.

## Alcance implementado

- `src/devpilot_core/rag/indexer.py`: indexación lexical local.
- `src/devpilot_core/rag/retriever.py`: recuperación lexical top-k con fuentes.
- `python -m devpilot_core rag index --target docs --json`.
- `python -m devpilot_core rag query "Qué valida readiness strict" --json`.
- `.devpilot/rag/docs_index.json` como estado runtime regenerable.
- MIASI tools y policies para `rag.index` y `rag.query`.
- Exclusión de `.devpilot/rag/` en package/release verification.

## Funcionamiento

`LocalRagIndexer` recorre archivos Markdown/texto/JSON/YAML permitidos dentro del workspace, excluye rutas sensibles, aplica `SecretGuard`, fragmenta por rangos de líneas y guarda tokens lexicales. El retriever calcula score lexical, devuelve `sources[]` con path/rango/fragmento y genera una respuesta determinística que exige `source_refs`.

## Integración

- CLI: `src/devpilot_core/cli.py`.
- Seguridad: `PathGuard`, `SecretGuard`.
- MIASI: `.devpilot/miasi/tool_registry.json`, `.devpilot/miasi/policy_matrix.json`.
- Release: `package_builder.py` y `verification.py` excluyen `.devpilot/rag/`.
- Documentación: README, runbook, backlog H, changelog y manifest funcional.

## Criterios PASS

- `rag index` crea índice local.
- `rag query` responde con fuentes.
- Las fuentes incluyen documento y rango de líneas.
- No hay red ni API externa.
- No hay embeddings obligatorios.
- SecretGuard se ejecuta.
- `.env`, `.git`, `.venv`, outputs y runtime state quedan excluidos.

## Criterios BLOCK

- Responder sin fuentes.
- Indexar secretos crudos o archivos sensibles.
- Requerir API externa o vector DB externa.
- Tratar la recuperación lexical como RAG industrial final.

## Riesgos

- Lexical retrieval no captura bien equivalencias semánticas.
- El índice puede quedar obsoleto.
- Redacción básica puede no cubrir todos los formatos secretos.
- La respuesta no usa LLM y por tanto es conservadora.

## Comandos de verificación

```powershell
python -m devpilot_core rag index --target docs --json
python -m devpilot_core rag query "Qué valida readiness strict" --json
python -m devpilot_core validate-artifact docs\06_miasi\rag_card.md --json
python -m devpilot_core schema validate-manifest docs\functional_sprint_87_manifest.json --json
python -m pytest tests\test_rag_local.py tests\test_sprint_87_documentation.py -q
```

## Veredicto

PASS focalizado. La capacidad queda lista como MVP local inicial y debe evolucionar con embeddings locales, evals de groundedness, métricas de cobertura de citas y eventual integración agentic.
