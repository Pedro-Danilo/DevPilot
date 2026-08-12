---
doc_id: DEVPL-UOC-010-RAG-AGENTS-TOOLS-HANDOFFS
title: "UOC-010 — RAG, agentes, tools y handoffs gobernados"
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-08-11
approval: sprint-implementation-candidate
---

# UOC-010 — RAG, agentes, tools y handoffs gobernados

## Objetivo

UOC-010 expone en `/ai` un boundary tipado sobre capacidades AI ya existentes de DevPilot sin convertir la Web UI en shell, loop autónomo o cliente de APIs externas. La primera versión es local-first, mock-first y conserva los no-go del programa.

## Operaciones tipadas

- `rag-index`: indexa un target allowlisted hacia `outputs/runtime/uoc010_ai/rag/docs_index.json`; requiere approval y nunca modifica el índice canónico versionado.
- `rag-query`: consulta índice canónico o runtime, devuelve citas y freshness, y usa `insufficient-evidence` cuando no hay fuentes.
- `agent-run`: ejecuta un agente allowlisted con una tarea y target registrados. `mock` es obligatorio; Ollama/LM Studio solo aparecen si están explícitamente habilitados en localhost. Requiere approval. Máximo un turno UOC-010 y costo permitido USD 0.
- `handoff-run`: `repo-review` dry-run con supervisor `multiagent.coordinator`, máximo tres pasos y trace por handoff.

## Tools

La UI no ejecuta tools genéricas. Muestra el contrato allowlisted/dry-run-first de `.devpilot/agents/tool_call_policy.json`. Tools no registradas, connector write, plugin execution, remote execution y shell arbitrario permanecen bloqueados.

## Memoria

La memoria permanece deshabilitada por defecto. `agent-run` permite opt-in explícito y, en PASS, persiste únicamente un receipt redactado bajo `.devpilot/agents/memory/`, con retención de 14 días. No se guardan raw prompts, raw outputs ni secretos y la memoria nunca cuenta como evidencia formal.

## Provider governance

El proveedor es visible en UI/resultados. `mock` está habilitado y no cuesta. Providers locales están opt-in y solo se aceptan si el registry los habilita como `local` y localhost. Providers `api`/external se muestran como deshabilitados y UOC-010 los bloquea incluso si el navegador intenta enviarlos.

## Límites

Esta versión es `implemented-initial`: no incorpora memoria semántica, ejecución real de tools desde UI, agentes autónomos multi-turno, APIs externas, MCP real, connectors o plugins. UOC-011 debe endurecer accesibilidad, performance, chaos/error states y release operacional.
