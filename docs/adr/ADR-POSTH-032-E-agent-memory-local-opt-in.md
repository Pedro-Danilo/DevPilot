---
doc_id: "ADR-POSTH-032-E"
title: "Agent memory local opt-in"
status: "proposed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-11"
approval: "pending"
decision_status: "local-opt-in-design-only"
micro_sprint: "POST-H-032-E"
semantic_memory_enabled_by_default: false
raw_prompt_storage_allowed: false
raw_output_storage_allowed: false
external_storage_allowed: false
memory_counts_as_formal_evidence: false
---

# ADR-POSTH-032-E — Agent memory local opt-in

## Contexto

DevPilot ya tiene `AgentSession` como estado operacional redacted y short-lived, RAG context packs citados y reportes formales bajo `docs/` u `outputs/`. El siguiente riesgo industrial es confundir memoria de agentes con evidencia formal, prompts crudos, outputs crudos o almacenamiento persistente no gobernado.

## Decisión

Se adopta un modelo de memoria local de agentes **opt-in**, deshabilitado por defecto y limitado a registros JSON redactados. La memoria se separa explícitamente en:

- `session_memory`: contexto operacional corto, local y redactado;
- `project_memory`: hechos sintéticos o redactados, opt-in y locales al workspace;
- `report_evidence`: evidencia formal separada, no almacenada como memoria.

POST-H-032-E no habilita memoria semántica/vectorial, no usa embeddings, no lee/escribe storage externo, no comparte memoria entre workspaces y no permite usar memoria como evidencia formal de claims de producción, compliance, enterprise, SaaS o remote execution.

## Reglas obligatorias

- `semantic_memory_enabled=false` por defecto.
- `memory_enabled_by_default=false`.
- No se almacenan raw prompts.
- No se almacenan raw outputs.
- No se almacenan secretos.
- No hay external storage.
- No hay memoria compartida entre workspaces sin ADR/approval futuro.
- Todo export es redactado.
- Cleanup es dry-run por defecto y `execute` debe pedirse explícitamente.
- La memoria no cuenta como evidencia formal.

## Consecuencias

- Los agentes futuros pueden consultar un contrato de memoria inspeccionable sin activar persistencia semántica por defecto.
- Las pruebas pueden usar registros sintéticos/redactados sin riesgo de filtrar prompts, outputs ni secretos.
- La memoria queda lista para evolución posterior, pero cualquier enablement real de memoria semántica requerirá decisión explícita y nuevos gates.

## PASS/BLOCK

PASS si el modelo valida schema, memoria está deshabilitada por defecto, inspect/export/cleanup funcionan localmente, export no contiene secretos, retention se aplica y los tests negativos bloquean raw prompt/output.

BLOCK si memoria queda enabled por defecto, se persiste prompt/output crudo, se persiste secreto, falta cleanup o la memoria se usa para justificar evidencia formal.

## Estado

`proposed` para POST-H-032-E porque define el contrato y piloto local inicial. La promoción a memoria semántica real queda fuera de alcance y requiere ADR futura.
