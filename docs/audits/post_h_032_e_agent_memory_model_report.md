---
doc_id: POST-H-032-E-AGENT-MEMORY-REPORT
title: "POST-H-032-E — Agent memory model report"
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: approved
---

# POST-H-032-E — Agent memory model report

## Resultado

`POST-H-032-E` implementa una primera versión `implemented-initial` del modelo de memoria local de agentes. La memoria permanece deshabilitada por defecto, es opt-in, local, redactada, inspeccionable, exportable y separada de session logs, project state y evidencia formal.

## Artefactos

- ADR: `docs/adr/ADR-POSTH-032-E-agent-memory-local-opt-in.md`.
- Policy: `.devpilot/agents/agent_memory_policy.json`.
- Schema: `docs/schemas/agent_memory_record.schema.json`.
- Módulo: `src/devpilot_core/agents/memory.py`.
- CLI: `python -m devpilot_core agent memory inspect --json`.
- ApplicationService: `ApplicationService.agent_memory_model`.

## Invariantes PASS

- `semantic_memory_enabled=false` por defecto.
- `memory_enabled_by_default=false`.
- No raw prompts.
- No raw outputs.
- No secretos.
- No almacenamiento externo.
- No memoria compartida entre workspaces.
- Export siempre redactado.
- Cleanup dry-run por defecto.
- Memoria no cuenta como evidencia formal.

## Limitaciones

Esta versión no implementa memoria semántica, embeddings, vector store, memoria compartida real ni uso de memoria para justificar claims formales. Cualquier habilitación futura debe requerir ADR/approval según riesgo, retención, redacción y no-go gates.

## Validación focal esperada

```powershell
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_032_agent_memory_model.py `
  tests/test_agent_session.py `
  tests/test_runtime_state_policy_schema.py `
  tests/test_observability_export.py `
  tests/test_secret_guard_hardening.py `
  -q
```
