---
title: "MIASI RAG Card — DevPilot Local"
doc_id: "DEVPL-MIASI-RAG-CARD-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-87"
updated: "2026-06-18"
approval: "approved_by_owner_direction"
---

# MIASI RAG Card — DevPilot Local

## Estado

`implemented-initial` para `FUNC-SPRINT-87`. Esta versión habilita RAG documental local con índice lexical, fuentes obligatorias y SecretGuard. No habilita embeddings remotos, LLM obligatorio, APIs externas, memoria semántica ni conectores MCP.

## Propósito

Definir el contrato operativo de Retrieval-Augmented Generation local para consultar documentación de DevPilot con evidencia. El objetivo es que una respuesta asistida nunca se presente sin fuentes trazables.

## Alcance

Incluye:

- indexación local de `docs/` u otro objetivo permitido dentro del workspace;
- exclusión de `.git`, `.venv`, `node_modules`, `outputs`, `dist`, caches y archivos secretos;
- fragmentos con `path`, `line_start`, `line_end`, `title`, hash y tokens lexicales;
- consulta lexical top-k;
- respuesta determinística con `source_refs`.

No incluye:

- embeddings semánticos;
- vector database externa;
- llamadas a modelos;
- generación natural con LLM;
- indexación de `.env`, secrets, runtime DB o outputs;
- conectores MCP.

## Taxonomía

| Elemento | Estado | Notas |
|---|---:|---|
| `rag.index` | `implemented-initial` | Construye índice lexical local. |
| `rag.query` | `implemented-initial` | Consulta con fuentes obligatorias. |
| Embeddings locales | `planned` | Futuro, vía proveedor local controlado. |
| Vector store | `future` | No requerido para MVP lexical. |
| RAG agentic | `future` | Requiere evals, grounding y policy adicional. |

## Contrato

`rag index` debe producir un índice JSON local en `.devpilot/rag/docs_index.json` con:

- `schema_version`;
- `index_id`;
- `scope`;
- `security`;
- `summary`;
- `chunks` con metadata de fuente.

`rag query` debe producir:

- `answer.grounded=true` cuando existan fuentes;
- `answer.source_refs` no vacío;
- `sources[]` con ruta, rango de líneas, score, términos coincidentes y fragmento;
- `RAG_QUERY_NO_SOURCES` si no hay evidencia suficiente.

## Herramientas

| Tool ID | Acción | Side effect | Riesgo | Política |
|---|---|---:|---:|---|
| `rag.index` | `index_local_docs` | `controlled_write` | `medium_high` | `RAG_INDEX_LOCAL_ALLOW` |
| `rag.query` | `query_local_index` | `read` | `medium` | `RAG_QUERY_LOCAL_ALLOW` |

## Política

- `PathGuard` debe bloquear rutas fuera del workspace y prefijos sensibles.
- `SecretGuard` debe revisar contenido antes de indexar y consultas antes de recuperar.
- La consulta no puede responder sin fuentes.
- La indexación debe ser local-only y sin API externa.
- `.devpilot/rag/` es estado runtime regenerable y no debe empaquetarse en releases.

## Evaluación

Métricas mínimas:

- `sources_total > 0` para consultas exitosas;
- `answer.grounded=true`;
- `external_api_used=false`;
- `embeddings_enabled=false` en Sprint 87;
- `secret_guard_used=true`.

## Observabilidad

Los comandos `rag index` y `rag query` emiten `CommandResult`, pueden escribir reportes con `--write-report`, se registran en `EventLogger` y se proyectan best-effort a `LocalStore`/métricas vía CLI.

## Criterios PASS

- El índice se genera localmente.
- Cada respuesta exitosa incluye fuentes.
- No se indexan `.env`, `.git`, `.venv`, outputs, caches ni runtime state sensible.
- `SecretGuard` se ejecuta durante indexación y consulta.
- No se usan red, APIs externas ni embeddings remotos.

## Criterios BLOCK

- Responder sin fuentes.
- Indexar secretos crudos.
- Indexar `.env`, `.git`, `.venv`, `outputs`, `node_modules` o `.devpilot/devpilot.db`.
- Requerir API externa.
- Presentar recuperación lexical como grounding semántico avanzado.

## Riesgos

- La recuperación lexical puede fallar con sinónimos o consultas semánticas.
- El score no mide factualidad; solo coincidencia textual.
- El índice local puede quedar desactualizado hasta ejecutar de nuevo `rag index`.
- La redacción de secretos es básica, no sustituye SAST/SCA/secret scanning industrial.

## Evolución pendiente

- Embeddings locales opcionales mediante ModelAdapter local.
- Métricas de groundedness y citation coverage.
- Integración con AgentSession.
- RAG agentic con políticas de prompt injection y evaluación adversarial.
- UI/API para consulta documental.
