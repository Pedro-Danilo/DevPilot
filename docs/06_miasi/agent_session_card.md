---
title: "MIASI AgentSession Card — DevPilot Local"
doc_id: "DEVPL-MIASI-AGENT-SESSION-CARD-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-H-CAPACIDADES-AVANZADAS"
sprint: "FUNC-SPRINT-86"
updated: "2026-06-18"
approval: "approved_after_func_sprint_86_implementation"
---

# MIASI AgentSession Card — DevPilot Local

## Estado

`approved` para `FUNC-SPRINT-86`. Esta tarjeta describe la memoria operativa local de sesiones agentic. Es una implementación inicial y controlada; no habilita memoria semántica, RAG, multiagente, MCP ni persistencia remota.

## Propósito

Definir el contrato MIASI para `AgentSession`: un estado local, redacted y auditable que permite asociar cada `agent run` con un `session_id`, reconstruir eventos básicos de la ejecución y consultar memoria operativa mínima sin almacenar prompts crudos, respuestas crudas, secretos, patches completos ni datos sensibles.

## Alcance

Incluye:

- generación o reutilización de `session_id` por ejecución de agente;
- persistencia local bajo `.devpilot/agent_sessions/`;
- proyección de eventos a `LocalStore` cuando está disponible;
- compatibilidad con trazas mediante `trace_id` y `run_id`;
- inspección read-only mediante `agent session inspect`;
- límites de retención documentados;
- redacción de datos antes de persistir.

No incluye:

- memoria semántica;
- embeddings;
- RAG;
- multiworkspace;
- sincronización remota;
- almacenamiento de prompts/respuestas crudas;
- decisiones autónomas basadas en historial.

## Taxonomía

| Elemento | Estado | Descripción |
|---|---|---|
| AgentSession | `implemented-initial` | Estado operativo local de ejecución agentic. |
| Operational memory | `implemented-initial` | Último contexto y último resultado resumido. |
| Semantic memory | `future` | Fuera del Sprint 86. |
| RAG memory | `future` | Fuera del Sprint 86. |
| Remote session sync | `future/blocked` | Requiere ADR futura. |

## Contrato

Una sesión debe contener como mínimo:

- `session_id` con formato `agsess_<32 hex>`;
- `created_at` y `updated_at`;
- `status`;
- `retention_days`;
- lista de `agent_ids` asociados;
- eventos redacted `agent.session.started` y `agent.session.completed`;
- memoria operativa resumida;
- flags explícitos `semantic_memory_enabled=false`, `rag_enabled=false`, `raw_prompts_stored=false` y `raw_outputs_stored=false`.

## Herramientas

| Tool | Estado | Riesgo | Política |
|---|---|---|---|
| `agent.session.inspect` | `implemented-initial` | bajo/medio | `AGENT_SESSION_INSPECT_ALLOW` |
| `agent run --session-id` | `implemented-initial` | medio | `AGENT_MODEL_CALL_GOVERNED_ALLOW` + `AGENT_SESSION_STATE_ALLOW` |

## Política

Reglas obligatorias:

1. Session state es local-only.
2. Session state no puede cruzar workspaces sin control explícito.
3. No se guardan prompts ni outputs crudos.
4. Todo contenido persistido pasa por redacción.
5. Los eventos son resúmenes, no payloads completos.
6. La inspección es read-only.
7. La retención inicial es corta y documentada.

## Evaluación

Pruebas mínimas:

- un `agent run` devuelve `agent_session_id`;
- `agent session inspect` reconstruye la sesión;
- una entrada con secreto sintético queda redacted;
- una sesión inexistente retorna `BLOCK`;
- una sesión con id inválido retorna `BLOCK`;
- el comando no habilita RAG ni memoria semántica.

## Observabilidad

Cada sesión debe poder relacionarse con:

- `trace_id`;
- `run_id`;
- eventos proyectados en `LocalStore` cuando la base existe;
- reportes opcionales generados por `--write-report`.

## Criterios PASS

- `agent run` asocia cada ejecución con `session_id`.
- `agent session inspect --session-id <id> --json` retorna `CommandResult` PASS.
- La sesión se persiste localmente y puede inspeccionarse.
- No se guardan prompts/respuestas crudas.
- `semantic_memory_enabled=false` y `rag_enabled=false`.
- Los IDs inválidos o inexistentes bloquean correctamente.

## Criterios BLOCK

- Guardar secretos sin redacción.
- Guardar prompts, respuestas, patches o outputs crudos.
- Mezclar sesiones entre workspaces.
- Habilitar RAG o memoria semántica en Sprint 86.
- Permitir inspección fuera del workspace.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Acumulación de estado local | Retención inicial y outputs regenerables. |
| Falsa sensación de memoria semántica | Flags explícitos y documentación. |
| Exposición de datos sensibles | Redacción previa a persistencia. |
| Acoplamiento prematuro a RAG | RAG queda `future` hasta Sprint 87. |

## Evolución pendiente

- políticas de retención ejecutables;
- pruning local;
- relación más profunda con TraceStore;
- soporte multiworkspace;
- memoria semántica opcional solo después de RAG y threat model específico;
- UI/API read-only para inspección de sesiones.
