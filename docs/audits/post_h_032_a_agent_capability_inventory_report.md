---
doc_id: POST-H-032-A-AGENT-CAPABILITY-INVENTORY-REPORT
title: "POST-H-032-A — Agent capability inventory and promotion criteria"
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: approved
---

# POST-H-032-A — Agent capability inventory and promotion criteria

## Resultado

Estado: `implemented-initial`.

POST-H-032-A aprueba el backlog POST-H-032 y crea la primera capa machine-readable para clasificar agentes, modos de operación, riesgos, tools, políticas, cobertura de tests y criterios de promoción.

## Decisión

`PASS` para cierre de micro-sprint.

## Evidencia implementada

- `docs/schemas/agent_capability_inventory.schema.json` registra el contrato `AgentCapabilityInventory`.
- `docs/schemas/agent_promotion_criteria.schema.json` registra el contrato `AgentPromotionCriteria`.
- `.devpilot/agents/agent_capability_inventory.json` inventaría todos los agentes declarados en MIASI.
- `.devpilot/agents/agent_promotion_criteria.json` formaliza rutas de promoción y no-go gates.
- `src/devpilot_core/agents/capability_inventory.py` construye y valida el inventario de forma local/read-only.
- CLI disponible: `python -m devpilot_core agent capability-inventory --json`.
- ApplicationService disponible: `ApplicationService.agent_capability_inventory`.

## Métricas esperadas del inventario

- Agentes MIASI: 14.
- Agentes implementados o implemented-initial: 13.
- Agentes future: 1.
- Tools MIASI registrados: 97.
- Candidatos RAG: 8.
- Candidatos memoria: 2.
- Memoria enabled por defecto: 0.
- External API allowed por defecto: 0.
- Remote execution enabled: 0.
- Connector write enabled: 0.
- Plugin execution enabled: 0.
- Source mutation allowed: 0.

## Límites de seguridad

POST-H-032-A no ejecuta agentes, tools, modelos, RAG, memoria, MCP ni workflows multiagente. Es un sprint de inventario y criterios de promoción. Las promociones reales quedan bloqueadas hasta los micro-sprints POST-H-032-B..H.

## No-go gates preservados

- APIs externas disabled por defecto.
- Memoria disabled por defecto.
- Ninguna mutación de fuente sin approval.
- Remote execution, connector write y plugin execution siguen bloqueados.
- Los gates determinísticos no son reemplazados por LLM/RAG/memoria.

## Validación focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_032_agent_capability_inventory.py `
  tests/test_agent_runtime.py `
  tests/test_agent_runtime_v2.py `
  tests/test_sdlc_agents.py `
  tests/test_miasi_registry.py `
  tests/test_miasi_semantic_validator.py `
  tests/test_schema_registry.py `
  -q
```

## Evolución pendiente

- POST-H-032-B: hardening de providers locales.
- POST-H-032-C: ADR/piloto gated para API externa.
- POST-H-032-D: agentes RAG-aware con citas y negative evals.
- POST-H-032-E: memoria local opt-in, redactada e inspeccionable.
- POST-H-032-F: tool calling contractual con allowlist, dry-run y approvals.
- POST-H-032-G: MCP fake-server y threat model.
- POST-H-032-H: multiagent handoff hardening.
