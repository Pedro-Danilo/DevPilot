---
doc_id: POST-H-032-IMPLEMENTATION
title: "POST-H-032 — Agentes IA avanzados, LLM, RAG, memoria y tools"
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: approved
---

# POST-H-032 - Agentes IA avanzados, LLM, RAG, memoria y tools

```yaml
doc_id: DEVPL-BACKLOG-POST-H-032-ADVANCED-AI-AGENTS-LLM-RAG-MEMORY-TOOLS-V1
status: approved
roadmap_wave: "Ola 7"
roadmap_source: "devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md"
repo_baseline: "repo_DevPilot_Local_293_POST_H_031_E.zip"
onboarding_report_source: "devpilot_onboarding_report_final_compilado.md"
target_repo_path: "docs/backlogs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md"
created_for: "DevPilot Local"
scope: "local-first / governed agents / LLM opt-in / RAG grounded / memory opt-in / tools policy-bound"
implementation_status: "approved/post-h-032-e-implemented-initial"
current_micro_sprint: "POST-H-032-E"
next_micro_sprint: "POST-H-032-F"
```

## 1. Proposito del backlog

POST-H-032 convierte la Ola 7 del roadmap post POST-H-025 en un backlog ejecutable para evolucionar la propuesta diferenciadora de DevPilot: agentes de IA gobernados por MIASI, policies, approvals, evals, observabilidad, RAG, memoria y tool calling.

El objetivo no es convertir DevPilot en un sistema de agentes autonomos sin control. El objetivo industrial es subir la madurez de agentes que ya existen en el repo, separando con claridad:

- agentes que deben permanecer deterministicos;
- agentes que pueden evolucionar a `model-aware`;
- agentes que pueden consumir RAG con citas;
- agentes que pueden usar memoria local opt-in;
- agentes que pueden solicitar tools bajo allowlist, dry-run y approval;
- workflows multiagente que pueden hacer handoff visible sin swarm autonomo;
- proveedores LLM locales y externos que permanecen deshabilitados por defecto salvo opt-in explicito.

El backlog debe preservar el claim actual de DevPilot: `production-ready-local` acotado. No habilita claims `enterprise-ready`, `remote-ready`, `saas-ready` ni `compliance-certified`.

## 2. Fuentes consultadas

Se consultaron como fuentes de verdad para formular este backlog:

- `devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md`.
- `devpilot_onboarding_report_final_compilado.md`.
- `repo_DevPilot_Local_262_POST_H_025_E.zip`, descomprimido en entorno local de trabajo.

Evidencia tecnica relevante observada:

- El roadmap define la Ola 7 como `POST-H-032: Agentes IA avanzados, LLM, RAG, memoria y tools`.
- El roadmap propone ocho micro-sprints: `POST-H-032-A` a `POST-H-032-H`.
- El informe final indica que los agentes son capacidades asistivas subordinadas a MIASI, policy, approvals, evals y evidencia.
- El repo contiene `src/devpilot_core/agents`, `src/devpilot_core/multiagent`, `src/devpilot_core/rag`, `src/devpilot_core/evals`, `src/devpilot_core/modeling`, `src/devpilot_core/policy`, `src/devpilot_core/approval`, `src/devpilot_core/observability/agentops.py` y registries MIASI.
- El repo contiene `.devpilot/miasi/agent_registry.json`, `.devpilot/miasi/tool_registry.json`, `.devpilot/miasi/policy_matrix.json`, `.devpilot/providers.yaml.example`, `.devpilot/rag/docs_index.json` y `.devpilot/workflows/sdlc_review.json`.
- El repo ya incluye providers `mock`, `ollama`, `lmstudio`, `openai` y `gemini` como contratos de configuracion, con providers locales y externos disabled por defecto salvo mock.
- El repo ya incluye tests relevantes: `test_agent_runtime.py`, `test_agent_runtime_v2.py`, `test_sdlc_agents.py`, `test_review_agents.py`, `test_release_agent.py`, `test_repo_analysis_agent.py`, `test_refactor_testplanner_agents.py`, `test_multiagent_coordinator.py`, `test_multiagent_workflow.py`, `test_model_adapter.py`, `test_model_governance.py`, `test_provider_config_schema.py`, `test_ollama_adapter.py`, `test_lmstudio_adapter.py`, `test_rag_local.py`, `test_post_h_011_rag_groundedness.py`, `test_rag_groundedness_claims.py`, `test_rag_groundedness_eval_runner.py`, `test_rag_citations_source_coverage.py`, `test_policy_engine.py`, `test_policy_engine_approval_rbac_enforcement.py`, `test_approval_binding.py`, `test_approval_store.py`, `test_agentops_gate.py`, `test_agentops_instrumentation.py` y `test_prompt_injection_guard.py`.

## 3. Estado base y problema a resolver

DevPilot ya tiene una capa de agentes local y gobernada, pero el estado actual es `implemented-initial` para muchas piezas. El problema no es ausencia de agentes, sino madurez desigual entre:

- agentes deterministicos que ya aportan valor y deben seguir siendo reproducibles;
- agentes model-aware que pueden usar LLM local bajo opt-in;
- RAG local que ya tiene groundedness y citas, pero no esta integrado industrialmente con todos los agentes candidatos;
- providers locales que existen pero requieren health checks, fallback y limites mas robustos;
- providers API externos que estan representados como placeholders deshabilitados y requieren ADR antes de piloto;
- memoria que no debe confundirse con logs, evidencia ni prompts crudos;
- tools que deben tener contrato, allowlist, dry-run-first y approvals;
- MCP que requiere diseno y fake-server antes de habilitar integracion real;
- multiagent handoff que debe ser explicito y bloqueable por evidencia insuficiente.

El riesgo industrial principal es que la evolucion de agentes se convierta en autonomia no gobernada. POST-H-032 debe impedirlo.

## 4. Objetivos industriales

POST-H-032 debe lograr:

- Inventariar agentes y clasificarlos por modo de operacion.
- Definir criterios de promocion de agentes hacia mayor madurez.
- Endurecer providers LLM locales sin activarlos por defecto.
- Definir ADR y piloto gated para APIs externas, sin llamadas reales en tests.
- Integrar RAG con agentes seleccionados usando citas y freshness.
- Disenar memoria local opt-in, redactada e inspeccionable.
- Crear contratos de tool calling con allowlist por agente.
- Evaluar MCP con fake-server local antes de cualquier enablement real.
- Endurecer multiagent handoffs con supervisor deterministic gate y checkpoints humanos.
- Mantener observabilidad por agent run, model call, RAG context, tool call y handoff.
- Mantener no-go gates: sin connector write, sin plugin execution, sin remote execution y sin external API accidental.

## 5. No objetivos

Este backlog no debe:

- Habilitar agentes autonomos irrestrictos.
- Habilitar swarm autonomo.
- Habilitar APIs externas por defecto.
- Habilitar MCP real por defecto.
- Habilitar connector write.
- Habilitar plugin execution.
- Habilitar remote execution.
- Guardar prompts crudos u outputs crudos en memoria.
- Reemplazar validadores deterministicos por LLM judge.
- Usar RAG para justificar claims prohibidos.
- Ejecutar tests que dependan de Ollama, LM Studio o APIs reales.
- Introducir secretos versionados.
- Convertir outputs de agentes en evidencia formal sin schema, eval y trazabilidad.

## 6. Principios de diseno

### 6.1 Gobierno antes que autonomia

Los agentes deben operar dentro de MIASI, PolicyEngine, approvals, RBAC, evals y observabilidad. Cualquier aumento de autonomia requiere evidencia, tests negativos y criterios de promocion.

### 6.2 Determinismo donde sea necesario

No todo agente debe usar LLM. Deben permanecer deterministicos los agentes o componentes que:

- validan contratos;
- aplican policies;
- bloquean no-go gates;
- calculan readiness;
- validan schemas;
- ejecutan claims validator;
- producen decisiones PASS/BLOCK;
- inspeccionan seguridad con reglas estrictas.

LLM/RAG puede asistir con recomendaciones, resumentes, drafts o priorizacion, pero no debe sustituir gates deterministas.

### 6.3 LLM opt-in y local-first

El provider `mock` sigue siendo default. Ollama y LM Studio pueden ser pilotos locales, disabled por defecto, localhost-only y sin secretos. APIs externas requieren ADR, opt-in explicito, env vars, CostGuard, SecretGuard y reportes de riesgo.

### 6.4 RAG con evidencia o silencio

Un agente RAG-aware debe citar fuentes. Si no tiene evidencia suficiente, debe responder `insufficient evidence` y no inventar soporte.

### 6.5 Tools con contrato y approval

Toda tool debe tener schema, allowlist por agente, risk level, dry-run-first, policy decision, approval binding cuando aplique y observability.

### 6.6 Memoria no es evidencia formal

La memoria puede mejorar continuidad, pero no reemplaza docs, reports, schemas ni audits. Debe ser local, opt-in, redactada, exportable e inspeccionable.

## 7. Clasificacion inicial de agentes

La clasificacion definitiva se produce en POST-H-032-A. Como hipotesis inicial basada en el repo:

| Agente/capacidad | Estado base | Evolucion recomendada |
| --- | --- | --- |
| `precode.audit` | Deterministico/policy-bound | Mantener deterministico; no LLM para PASS/BLOCK |
| `precode.documentation` | Deterministico/asistivo | Puede usar RAG para sugerir docs faltantes, sin declarar readiness |
| `repo.analysis` | Deterministico/model-aware inicial | Buen candidato RAG-aware y LLM local opt-in |
| `code.review` | Deterministico/model-aware inicial | Buen candidato LLM local/API gated con RAG y tool-read-only |
| `patch.review` | Deterministico/model-aware inicial | Buen candidato RAG-aware; tools solo read-only |
| `safe.refactor` | Deterministico de seguridad alta | Mantener dry-run-first; LLM solo para plan, no escritura sin approval |
| `testplanner.agent` | Deterministico/model-aware inicial | Buen candidato RAG-aware y tool-calling read-only |
| `requirements.agent` | Deterministico/model-aware inicial | Buen candidato RAG-aware y memoria de proyecto opt-in |
| `architecture.agent` | Deterministico/model-aware inicial | Buen candidato RAG-aware con citas y freshness |
| `security.agent` | Deterministico de riesgo alto | LLM solo advisory; bloqueos deben ser deterministas |
| `release.assistant` | Deterministico/release-bound | Puede usar RAG para checklist, no para release PASS/BLOCK |
| `multiagent coordinator` | Implemented-initial | Handoff explicito, supervisor determinista, no swarm |

## 8. Artefactos globales previstos

### 8.1 Nuevos schemas

- `docs/schemas/agent_capability_inventory.schema.json`
- `docs/schemas/agent_promotion_criteria.schema.json`
- `docs/schemas/local_llm_provider_health_report.schema.json`
- `docs/schemas/external_api_provider_pilot.schema.json`
- `docs/schemas/rag_agent_context_pack.schema.json`
- `docs/schemas/agent_memory_record.schema.json`
- `docs/schemas/agent_tool_call.schema.json`
- `docs/schemas/mcp_fake_server_evaluation.schema.json`
- `docs/schemas/multiagent_handoff_hardening_report.schema.json`

Si durante implementacion se concluye que alguno debe extender schemas existentes, debe hacerse con versionado y compatibilidad.

### 8.2 Nuevos artefactos `.devpilot`

- `.devpilot/agents/agent_capability_inventory.json`
- `.devpilot/agents/agent_promotion_criteria.json`
- `.devpilot/agents/rag_agent_bindings.json`
- `.devpilot/agents/agent_memory_policy.json`
- `.devpilot/agents/tool_call_policy.json`
- `.devpilot/agents/multiagent_handoff_policy.json`
- `.devpilot/modeling/local_llm_provider_health_policy.json`
- `.devpilot/modeling/external_api_provider_pilot_policy.json`
- `.devpilot/mcp/mcp_fake_server_contract.json`

### 8.3 Nuevos modulos previstos

- `src/devpilot_core/agents/capability_inventory.py`
- `src/devpilot_core/agents/promotion.py`
- `src/devpilot_core/agents/rag_context.py`
- `src/devpilot_core/agents/memory.py`
- `src/devpilot_core/agents/tool_calls.py`
- `src/devpilot_core/agents/external_api_pilot.py`
- `src/devpilot_core/modeling/local_provider_health.py`
- `src/devpilot_core/mcp/fake_server.py`
- `src/devpilot_core/mcp/contracts.py`
- `src/devpilot_core/multiagent/hardening.py`

### 8.4 Reportes y manifests

- `docs/audits/post_h_032_a_agent_capability_inventory_report.md`
- `docs/audits/post_h_032_b_local_llm_provider_hardening_report.md`
- `docs/audits/post_h_032_c_external_api_provider_adr_pilot_report.md`
- `docs/audits/post_h_032_d_rag_aware_agents_report.md`
- `docs/audits/post_h_032_e_agent_memory_model_report.md`
- `docs/audits/post_h_032_f_tool_calling_contract_report.md`
- `docs/audits/post_h_032_g_mcp_design_fake_server_report.md`
- `docs/audits/post_h_032_h_multiagent_handoff_hardening_report.md`
- `docs/post_h_032_a_manifest.json`
- `docs/post_h_032_b_manifest.json`
- `docs/post_h_032_c_manifest.json`
- `docs/post_h_032_d_manifest.json`
- `docs/post_h_032_e_manifest.json`
- `docs/post_h_032_f_manifest.json`
- `docs/post_h_032_g_manifest.json`
- `docs/post_h_032_h_manifest.json`

### 8.5 ADRs previstas

- `docs/adr/ADR-POSTH-032-C-external-api-provider-gated-pilot.md`
- `docs/adr/ADR-POSTH-032-E-agent-memory-local-opt-in.md`
- `docs/adr/ADR-POSTH-032-G-mcp-design-and-threat-model.md`

## 9. Micro-sprints

## POST-H-032-A - Agent capability inventory and promotion criteria

### Objetivo

Crear un inventario machine-readable de agentes, capacidades, riesgos y criterios de promocion para determinar que agentes pueden permanecer deterministicos, cuales pueden ser model-aware, cuales pueden usar RAG, memoria o tools, y bajo que condiciones.

### Alcance

Este sprint es read-only sobre comportamiento runtime. No habilita nuevas capacidades de ejecucion. Formaliza el mapa de agentes y sus criterios.

### Entregables

- Schema `AgentCapabilityInventory`.
- Schema `AgentPromotionCriteria`.
- `.devpilot/agents/agent_capability_inventory.json`.
- `.devpilot/agents/agent_promotion_criteria.json`.
- Modulo `agents/capability_inventory.py`.
- Reporte de auditoria POST-H-032-A.
- Manifest POST-H-032-A.
- Tests focales.
- Actualizacion de README, runbook, TCR, source registry y project_state.

### Campos minimos por agente

- `agent_id`;
- `implementation_module`;
- `status`;
- `mode`: deterministic, rule-based, model-aware, rag-aware, memory-aware, tool-calling, multiagent;
- `autonomy_level`;
- `allowed_tools`;
- `forbidden_tools`;
- `policy_rules`;
- `approval_required_actions`;
- `eval_coverage`;
- `observability_events`;
- `rag_enabled`;
- `memory_enabled`;
- `external_api_allowed`;
- `provider_modes_allowed`;
- `promotion_target`;
- `blocking_gaps`.

### Criterios PASS

- Todo agente en MIASI registry aparece en el inventario.
- Todo agente implementado tiene modulo y tests asociados.
- Todo agente con tools declara allowlist.
- Todo agente con LLM declara providers permitidos.
- Todo agente con RAG declara groundedness eval.
- Todo agente con memoria declara policy.
- Ningun agente tiene external API allowed por defecto.
- Ningun agente puede mutar fuente o ejecutar herramientas externas sin approval.

### Criterios BLOCK

- Agente implementado sin owner o risk level.
- Agente con tools sin allowlist.
- Agente con external API enabled por defecto.
- Agente con memory enabled por defecto sin ADR.
- Agente que puede escribir fuente sin approval.

### Validacion focal esperada

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

## POST-H-032-B - Local LLM provider hardening

### Objetivo

Endurecer los providers locales Ollama y LM Studio para que puedan ser usados de forma opcional, localhost-only, testeable con fakes y con fallback controlado a mock.

### Alcance

Este sprint no requiere que Ollama o LM Studio esten instalados en CI o entorno de test. Los tests deben usar fake/local provider o monkeypatch controlado.

### Entregables

- Schema `LocalLlmProviderHealthReport`.
- Politica `.devpilot/modeling/local_llm_provider_health_policy.json`.
- Modulo `modeling/local_provider_health.py`.
- Health checks para Ollama y LM Studio sin dependencia obligatoria.
- BudgetLedger extendido para providers locales aunque costo sea 0.
- Fallback controlado a `mock` con finding explicito.
- Tests de fake provider.
- Reporte de auditoria POST-H-032-B.
- Manifest POST-H-032-B.

### Criterios PASS

- Local providers siguen disabled por defecto.
- Solo se aceptan endpoints localhost.
- No se requieren secretos.
- Tests no dependen de servicios reales.
- Health check distingue unavailable, disabled, misconfigured y available.
- Fallback a mock es explicito, auditable y no oculta fallos criticos.
- No se usa external API.

### Criterios BLOCK

- Provider local enabled por defecto.
- Endpoint no-localhost.
- Test que requiere Ollama/LM Studio real.
- Secreto en provider config.
- Fallback silencioso que simule exito real.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_032_local_llm_provider_hardening.py `
  tests/test_model_adapter.py `
  tests/test_model_governance.py `
  tests/test_provider_config_schema.py `
  tests/test_ollama_adapter.py `
  tests/test_lmstudio_adapter.py `
  tests/test_policy_engine.py `
  -q
```

## POST-H-032-C - External API provider ADR and gated pilot

### Objetivo

Crear la decision arquitectonica, politica de opt-in y piloto fake/gated para providers API externos sin habilitar llamadas reales por defecto.

### Alcance

Este sprint diseña el camino seguro para APIs externas. No convierte APIs externas en dependencia del producto ni de tests.

### Entregables

- ADR `ADR-POSTH-032-C-external-api-provider-gated-pilot.md`.
- Schema `ExternalApiProviderPilot`.
- `.devpilot/modeling/external_api_provider_pilot_policy.json`.
- Modulo `agents/external_api_pilot.py` o extension controlada de modeling/policy.
- Fake API provider para contrato.
- CostGuard real aplicado a requests.
- Secret handling por environment variables.
- No-go gate para external API accidental.
- Reporte de riesgo.
- Reporte de auditoria POST-H-032-C.
- Manifest POST-H-032-C.

### Politica minima

- APIs externas disabled por defecto.
- Requieren opt-in local explicito.
- Requieren variable de entorno, no secretos versionados.
- Requieren warning visible.
- Requieren reporte de riesgo.
- Requieren CostGuard.
- Requieren SecretGuard.
- Requieren tests con fake provider.
- Ninguna prueba llama API real.

### Criterios PASS

- ADR aprobada o en estado `proposed` con no-go gates claros.
- Fake provider cubre contrato.
- External API real no se invoca en tests.
- Provider API enabled requiere configuracion local no versionada.
- Cualquier intento accidental queda BLOCK.
- Reporte muestra `external_api_used=false` por defecto.

### Criterios BLOCK

- API externa enabled por defecto.
- Test con llamada real.
- API key en repo.
- Provider externo sin CostGuard.
- Provider externo sin operator warning.
- Agente que pueda usar API externa sin policy.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_032_external_api_provider_pilot.py `
  tests/test_model_governance.py `
  tests/test_provider_config_schema.py `
  tests/test_policy_engine.py `
  tests/test_secret_guard_hardening.py `
  tests/test_post_h_023_no_network_invariant.py `
  -q
```

## POST-H-032-D - RAG-aware agents

### Objetivo

Integrar RAG local con agentes seleccionados, de forma grounded, citada y con evaluaciones negativas contra hallucination y unsupported claims.

### Agentes candidatos

- `requirements.agent`;
- `architecture.agent`;
- `security.agent`;
- `testplanner.agent`;
- `release.assistant`;
- `repo.analysis`;
- `code.review`;
- `patch.review`.

### Entregables

- Schema `RagAgentContextPack`.
- `.devpilot/agents/rag_agent_bindings.json`.
- Modulo `agents/rag_context.py`.
- Context pack con source ids, citas, freshness y coverage.
- Groundedness eval por agente.
- Negative cases para insufficient evidence.
- Tests contra unsupported claims.
- Reporte de auditoria POST-H-032-D.
- Manifest POST-H-032-D.

### Criterios PASS

- Cada sugerencia RAG-aware incluye fuentes.
- Si no hay fuente suficiente, el agente responde `insufficient evidence`.
- RAG no justifica claims prohibidos.
- RAG no lee fuentes fuera de allowlist.
- RAG context pack valida contra schema.
- Groundedness eval cubre casos positivos y negativos.
- No se requiere LLM real para tests.

### Criterios BLOCK

- Respuesta con claim sin fuente.
- Claim prohibido justificado con RAG.
- RAG context sin source ids.
- Lectura de rutas no permitidas.
- Fallo de insufficient evidence.

### Validacion focal esperada

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

Si no existen tests por agente con esos nombres exactos, se deben crear los tests POST-H-032 y reutilizar los tests existentes `test_sdlc_agents.py`, `test_review_agents.py`, `test_release_agent.py`, `test_repo_analysis_agent.py` y `test_refactor_testplanner_agents.py`.


### Estado de implementación POST-H-032-D

`POST-H-032-D` queda implementado como versión `implemented-initial` de agentes RAG-aware. La implementación agrega `RagAgentContextPack`, `.devpilot/agents/rag_agent_bindings.json`, `src/devpilot_core/agents/rag_context.py`, CLI `python -m devpilot_core agent rag-context --json`, boundary `ApplicationService.rag_agent_context`, negative cases y tests focales.

La implementación es deliberadamente local-first y determinística: usa el índice RAG lexical existente, exige `source_ids`, citas y freshness, y responde `insufficient evidence` ante claims sin soporte o claims prohibidos. No usa LLM real, red, API externa, memoria, tool execution ni mutaciones de fuente. La evolución futura puede integrar el context pack directamente en prompts/agentes, pero debe preservar estos gates.

## POST-H-032-E - Agent memory model

### Objetivo

Disenar e implementar una memoria local de agentes, opt-in, redactada, inspeccionable, exportable y separada de session logs, project state y evidencia formal.

### Alcance

La memoria no debe estar activa por defecto. Debe permitir pilotos controlados con datos sinteticos o redactados.

### Entregables

- ADR `ADR-POSTH-032-E-agent-memory-local-opt-in.md`.
- Schema `AgentMemoryRecord`.
- `.devpilot/agents/agent_memory_policy.json`.
- Modulo `agents/memory.py`.
- Separacion entre `session_memory`, `project_memory` y `report_evidence`.
- Retention/redaction policy.
- CLI/ApplicationService para inspect/export/cleanup.
- Export redactado.
- Tests de no raw prompts/no raw outputs.
- Reporte de auditoria POST-H-032-E.
- Manifest POST-H-032-E.

### Politica minima

- `semantic_memory_enabled=false` por defecto.
- No raw prompts.
- No raw outputs.
- No secrets.
- No external storage.
- No memoria compartida entre workspaces sin approval.
- Operador puede inspeccionar.
- Operador puede limpiar.
- Export siempre redactado.

### Criterios PASS

- Memoria valida contra schema.
- Memoria disabled por defecto.
- Inspect y cleanup funcionan localmente.
- Export no contiene secretos.
- Retention policy se aplica.
- Memoria no cuenta como evidencia formal.
- Tests negativos bloquean raw prompt/output.

### Criterios BLOCK

- Memoria enabled por defecto.
- Prompt/output crudo persistido.
- Secreto persistido.
- Falta de cleanup.
- Memoria usada para justificar claim formal.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_032_agent_memory_model.py `
  tests/test_agent_session.py `
  tests/test_runtime_state_policy_schema.py `
  tests/test_observability_export.py `
  tests/test_secret_guard_hardening.py `
  -q
```

### Estado de implementación POST-H-032-E

`POST-H-032-E` queda implementado como versión `implemented-initial` del modelo de memoria local de agentes. La implementación agrega la ADR `docs/adr/ADR-POSTH-032-E-agent-memory-local-opt-in.md`, el schema `AgentMemoryRecord`, la policy `.devpilot/agents/agent_memory_policy.json`, el módulo `src/devpilot_core/agents/memory.py`, el comando `python -m devpilot_core agent memory inspect --json`, export redactado, cleanup dry-run/execute controlado, pruebas negativas contra raw prompts/raw outputs/secrets y separación explícita entre `session_memory`, `project_memory` y `report_evidence`.

Limitación explícita: esta primera versión no habilita memoria semántica, embeddings, vector store, memoria compartida real ni uso de memoria para justificar claims formales. Cualquier evolución hacia semantic/project memory real debe mantenerse opt-in, redactada, inspeccionable, con retención, approval cuando aplique y sin almacenamiento externo por defecto. POST-H-032-F debe avanzar hacia tool calling contractual manteniendo dry-run-first, allowlist, policy/approval binding y defensas contra tool injection.

## POST-H-032-F - Tool calling contract

### Objetivo

Crear contrato industrial para tool calls de agentes: schema, registry executable subset, allowlist por agente, dry-run-first, approval binding, observability y defensas contra prompt/tool injection.

### Alcance

Este sprint puede habilitar tool calling contractual y fake/local tools. No habilita connector write, plugin execution ni remote execution.

### Entregables

- Schema `AgentToolCall`.
- `.devpilot/agents/tool_call_policy.json`.
- Modulo `agents/tool_calls.py`.
- Tool registry executable subset derivado de MIASI Tool Registry.
- Allowlist por agente.
- Risk levels por tool.
- Dry-run-first enforcement.
- Approval binding para tools de riesgo.
- Observability por tool call.
- Tests adversariales de prompt/tool injection.
- Reporte de auditoria POST-H-032-F.
- Manifest POST-H-032-F.

### Criterios PASS

- Tool calls validan contra schema.
- Cada agent/tool pair esta allowlisted.
- Toda tool de riesgo requiere policy decision y approval si aplica.
- Dry-run-first es default.
- Tool injection guard cubre entradas maliciosas.
- No connector write.
- No plugin execution.
- No remote execution.
- Tool calls quedan trazados.

### Criterios BLOCK

- Tool ejecutada sin allowlist.
- Tool de riesgo sin approval.
- Write externa habilitada.
- Plugin execution habilitada.
- Remote execution habilitada.
- Prompt injection que logra cambiar tool target.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_032_tool_calling_contract.py `
  tests/test_prompt_injection_guard.py `
  tests/test_policy_engine.py `
  tests/test_policy_engine_approval_rbac_enforcement.py `
  tests/test_approval_binding.py `
  tests/test_post_h_018_connector_policy_binding.py `
  tests/test_post_h_019_plugin_execution_blocked.py `
  tests/test_post_h_021_remote_disabled_invariants.py `
  -q
```

## POST-H-032-G - MCP design and local fake-server evaluation

### Objetivo

Definir el diseno MCP de DevPilot con threat model, fake MCP server local, mapping a MIASI Tool Registry, permission model y audit trail, sin habilitar MCP real por defecto.

### Alcance

Este sprint es de diseno ejecutable y fake-server evaluation. MCP real queda disabled hasta backlog futuro.

### Entregables

- ADR `ADR-POSTH-032-G-mcp-design-and-threat-model.md`.
- Schema `McpFakeServerEvaluation`.
- `.devpilot/mcp/mcp_fake_server_contract.json`.
- Modulo `mcp/fake_server.py`.
- Modulo `mcp/contracts.py`.
- Mapping MCP tools -> MIASI Tool Registry.
- Permission model y audit trail.
- Tests con fake MCP server local.
- Threat model MCP.
- Reporte de auditoria POST-H-032-G.
- Manifest POST-H-032-G.

### Criterios PASS

- MCP real disabled por defecto.
- Fake server prueba contratos sin red externa.
- Tools MCP no escriben ni ejecutan sin policy/approval.
- MCP tool mapping valida contra MIASI.
- Audit trail registra tool request/result.
- Threat model incluye prompt injection, tool poisoning, data exfiltration y permission escalation.

### Criterios BLOCK

- MCP real enabled por defecto.
- Test con servidor MCP externo.
- Tool MCP sin mapping MIASI.
- Tool MCP con write/execute sin approval.
- Falta de audit trail.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_032_mcp_design_fake_server.py `
  tests/test_post_h_032_tool_calling_contract.py `
  tests/test_miasi_registry.py `
  tests/test_miasi_semantic_validator.py `
  tests/test_policy_engine.py `
  tests/test_post_h_023_no_network_invariant.py `
  -q
```

## POST-H-032-H - Multiagent handoff hardening

### Objetivo

Endurecer workflows multiagente con schema de handoff, workflow registry, supervisor deterministic gate, human-in-the-loop checkpoints y evals por workflow.

### Alcance

Este sprint no habilita swarm autonomo. Formaliza handoffs visibles, trazables y bloqueables.

### Entregables

- Schema `MultiagentHandoffHardeningReport`.
- `.devpilot/agents/multiagent_handoff_policy.json`.
- Modulo `multiagent/hardening.py`.
- Extension controlada de handoff/workflow registry.
- Supervisor deterministic gate.
- Human-in-the-loop checkpoints.
- Evals por workflow.
- Observability por handoff.
- Reporte de auditoria POST-H-032-H.
- Manifest POST-H-032-H.

### Criterios PASS

- No swarm autonomo.
- Todo handoff es visible.
- Cada agente mantiene scope y tools propios.
- El supervisor puede bloquear por evidencia insuficiente.
- Handoff registra reason, source, target, policy decision y trace id.
- Human checkpoint existe para acciones de riesgo.
- Evals cubren workflows positivos y negativos.

### Criterios BLOCK

- Handoff implicito.
- Agente hijo hereda tools no permitidas.
- Workflow sin supervisor gate.
- Accion de riesgo sin human checkpoint.
- Multiagent ejecuta write/remote/plugin sin approval.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_032_multiagent_handoff_hardening.py `
  tests/test_multiagent_coordinator.py `
  tests/test_multiagent_workflow.py `
  tests/test_agentops_gate.py `
  tests/test_agentops_instrumentation.py `
  tests/test_policy_engine.py `
  tests/test_approval_binding.py `
  -q
```

## 10. Definition of Done del backlog POST-H-032

El backlog completo se puede cerrar solo si:

- Existe inventario machine-readable de agentes y criterios de promocion.
- Los providers locales estan endurecidos, disabled por defecto y testeados con fakes.
- El piloto de API externa tiene ADR, policy, fake provider y no-go gate.
- Los agentes RAG-aware citan fuentes y bloquean unsupported claims.
- La memoria local es opt-in, redactada, inspeccionable y limpiable.
- Tool calling esta schema-backed, allowlisted, dry-run-first y approval-bound.
- MCP solo existe como diseno/fake-server local, no como integracion real enabled.
- Multiagent handoff es explicito, observable y bloqueable.
- No se habilita external API accidental.
- No se habilita connector write.
- No se habilita plugin execution.
- No se habilita remote execution.
- No se guardan secretos, prompts crudos ni outputs crudos.
- README, runbook, backlog, ADRs, manifests, source registry, schema catalog, TCR y project_state quedan sincronizados.
- La validacion focal ampliada pasa.

## 11. Quality gates requeridos

### Gates existentes obligatorios

Deben seguir pasando:

```powershell
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
python -m devpilot_core schema list --json
python -m devpilot_core cli-registry guard --json
```

### Gate nuevo recomendado

Crear subgate:

```text
agentic-governance-readiness
```

El gate debe verificar:

- agent capability inventory valido;
- external API disabled por defecto;
- local providers localhost-only;
- RAG agents con groundedness coverage;
- memory disabled por defecto;
- tool calls allowlisted;
- MCP real disabled;
- multiagent handoff explicito;
- no connector write, no plugin execution, no remote execution;
- observability por agent/model/tool/handoff.

## 12. Regresion focal acumulada recomendada

Durante POST-H-032 no se recomienda usar `pytest -q` completo como validacion primaria de cada micro-sprint. La validacion focal acumulada debe incluir:

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_032_agent_capability_inventory.py `
  tests/test_post_h_032_local_llm_provider_hardening.py `
  tests/test_post_h_032_external_api_provider_pilot.py `
  tests/test_post_h_032_rag_aware_agents.py `
  tests/test_post_h_032_agent_memory_model.py `
  tests/test_post_h_032_tool_calling_contract.py `
  tests/test_post_h_032_mcp_design_fake_server.py `
  tests/test_post_h_032_multiagent_handoff_hardening.py `
  tests/test_agent_runtime.py `
  tests/test_agent_runtime_v2.py `
  tests/test_sdlc_agents.py `
  tests/test_review_agents.py `
  tests/test_release_agent.py `
  tests/test_repo_analysis_agent.py `
  tests/test_refactor_testplanner_agents.py `
  tests/test_multiagent_coordinator.py `
  tests/test_multiagent_workflow.py `
  tests/test_model_adapter.py `
  tests/test_model_governance.py `
  tests/test_provider_config_schema.py `
  tests/test_ollama_adapter.py `
  tests/test_lmstudio_adapter.py `
  tests/test_rag_local.py `
  tests/test_post_h_011_rag_groundedness.py `
  tests/test_rag_groundedness_claims.py `
  tests/test_rag_groundedness_eval_runner.py `
  tests/test_rag_citations_source_coverage.py `
  tests/test_policy_engine.py `
  tests/test_policy_engine_approval_rbac_enforcement.py `
  tests/test_approval_binding.py `
  tests/test_agentops_gate.py `
  tests/test_agentops_instrumentation.py `
  tests/test_prompt_injection_guard.py `
  -q
```

Validaciones CLI/documentales:

```powershell
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
python -m devpilot_core schema list --json
python -m devpilot_core cli-registry guard --json
```

## 13. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigacion |
| --- | --- | --- |
| Agentes interpretados como autonomos | Critico | Inventario, autonomy level, policy, approvals y no-go gates |
| API externa accidental | Critico | ADR, disabled by default, fake provider, CostGuard, SecretGuard |
| LLM reemplaza decisiones deterministicas | Alto | Gates siguen deterministicos; LLM solo advisory |
| RAG genera soporte falso | Alto | Groundedness eval, citas obligatorias, insufficient evidence |
| Memoria filtra prompts/outputs | Critico | Opt-in, redaction, SecretGuard, cleanup |
| Tool injection | Critico | Tool schema, allowlist, injection guard, approvals |
| MCP abre superficie externa | Critico | Fake-server local, MCP real disabled, threat model |
| Multiagent swarm | Alto | Handoff explicito, supervisor deterministic gate, checkpoints humanos |

## 14. Dependencias

- POST-H-011 RAG groundedness.
- POST-H-012 approval/RBAC hardening.
- POST-H-018 connector sandbox policy.
- POST-H-019 plugin execution blocked/design.
- POST-H-021 remote disabled invariants.
- POST-H-023 no-network/secure transport limits.
- POST-H-025 production-ready local claims/no-go gates.
- POST-H-031 observability/evidence graph, si ya esta implementado al momento de cerrar POST-H-032.

## 15. Decisiones arquitectonicas

POST-H-032 requiere ADRs especificas porque introduce caminos de riesgo:

- API externa: requiere ADR antes de cualquier piloto real.
- Memoria: requiere ADR para definir persistencia, retencion, redaccion y cleanup.
- MCP: requiere ADR y threat model antes de cualquier integracion real.

No se requiere ADR para inventario, RAG local o hardening de providers locales si se mantiene local-first, disabled by default y sin cambios de claims.

## 16. Ruta recomendada en el repo

Guardar este backlog en:

```text
docs/backlogs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md
```

Opcionalmente, si se mantiene un documento top-level por backlog activo:

```text
docs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md
```

## 17. Commit sugerido para incorporar el backlog

```bash
git add docs/backlogs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md
git commit -m "Add POST-H-032 advanced governed agents backlog"
```

## 18. Cierre esperado de POST-H-032

POST-H-032 debe cerrar con DevPilot capaz de evolucionar sus agentes hacia LLM local/API gated, RAG, memoria, tools, MCP fake-server y workflows multiagente sin perder su disciplina industrial. El resultado correcto no es mas autonomia por si misma; es asistencia mas potente, trazable y gobernada. Las decisiones criticas siguen siendo deterministic gate, policy, approval y evidencia.


## Implementacion POST-H-032-A — Agent capability inventory and promotion criteria

Estado: `implemented-initial`. Este micro-sprint aprueba el backlog POST-H-032 y formaliza inventario y criterios de promocion de agentes sin habilitar nuevas capacidades runtime.

Artefactos implementados:

- `docs/schemas/agent_capability_inventory.schema.json`: contrato `AgentCapabilityInventory`.
- `docs/schemas/agent_promotion_criteria.schema.json`: contrato `AgentPromotionCriteria`.
- `.devpilot/agents/agent_capability_inventory.json`: inventario machine-readable de agentes MIASI, modos, riesgos, tools, tests, RAG/memory candidates y no-go flags.
- `.devpilot/agents/agent_promotion_criteria.json`: criterios de promocion y gates globales para evolucionar agentes de forma gobernada.
- `src/devpilot_core/agents/capability_inventory.py`: builder local/read-only.
- CLI: `python -m devpilot_core agent capability-inventory --json`.
- ApplicationService: `ApplicationService.agent_capability_inventory`.

Limites explicitos:

- No ejecuta agentes.
- No ejecuta tools.
- No llama modelos.
- No ejecuta RAG.
- No lee ni escribe memoria.
- No habilita APIs externas.
- No habilita remote execution, connector write ni plugin execution.
- No reemplaza gates deterministicos ni decisions PASS/BLOCK.

Evolucion pendiente en POST-H-032-B..H: hardening de providers locales, ADR/piloto API externa, agentes RAG-aware, memoria local opt-in, tool calling contractual, MCP fake-server y multiagent handoff hardening.

## Implementación acumulada POST-H-032-B

POST-H-032-B queda implementado como primera versión de hardening de providers locales LLM. Se agrega `LocalLlmProviderHealthReport`, `.devpilot/modeling/local_llm_provider_health_policy.json`, `src/devpilot_core/modeling/local_provider_health.py` y `model local-health`. El sprint no habilita llamadas reales a modelos por defecto: Ollama y LM Studio permanecen deshabilitados en metadata versionada, limitados a localhost, sin secretos, sin API externa, sin dependencia de servidores reales para tests y con fallback a `mock` únicamente explícito y auditable.

Limitación explícita: esta versión es `implemented-initial`; no instala ni administra Ollama/LM Studio, no descarga modelos, no abre endpoints remotos, no llama APIs externas y no promueve agentes a RAG/memory/tool autonomy. POST-H-032-C debe tratar APIs externas con ADR y piloto gated.
## Implementación acumulada POST-H-032-C

POST-H-032-C queda implementado como primera versión `implemented-initial / external-api-gated-pilot`. Se agrega la ADR `docs/adr/ADR-POSTH-032-C-external-api-provider-gated-pilot.md`, el schema `ExternalApiProviderPilot`, la policy `.devpilot/modeling/external_api_provider_pilot_policy.json`, el módulo `src/devpilot_core/modeling/external_api_pilot.py`, el comando `python -m devpilot_core model external-api-pilot --json` y el boundary `ApplicationService.external_api_provider_pilot`.

El sprint no habilita llamadas reales a APIs externas. OpenAI/Gemini permanecen deshabilitados por defecto en metadata versionada; las pruebas usan fake provider determinístico; SecretGuard valida que no haya secretos versionados; CostGuard bloquea uso externo accidental; el reporte mantiene `external_api_used=false`, `network_used=false`, `real_api_call_performed=false` y `tests_require_real_api=false`.

Limitación explícita: esta versión no instala SDKs, no abre sockets, no lee valores de API keys, no envía prompts a proveedores externos y no permite que `production-ready-local` dependa de APIs externas. Cualquier activación real futura requiere configuración local no versionada, env vars, budget explícito, warning visible, risk report, aprobación/acknowledgement y nueva decisión de enablement. POST-H-032-D quedó implementado como agentes RAG-aware con groundedness y fuentes locales; POST-H-032-E avanza hacia memoria local opt-in, redactada e inspeccionable.

