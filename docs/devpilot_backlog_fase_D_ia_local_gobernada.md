---
title: "DevPilot Local — Backlog ejecutable Fase D: IA local gobernada"
doc_id: "DEVPL-FUNC-BACKLOG-FASE-D-001"
status: "approved"
version: "0.2.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-D-IA-LOCAL-GOBERNADA"
updated: "2026-06-13"
source_repo: "repo_DevPilot_Local_66.zip"
source_report: "Informe de avance DevPilot - sprint 0 - 18.docx"
source_backlog_model: "docs/functional_backlog_after_precode.md"
baseline_dependency: "Fases A, B y C cerradas; Fase C validada por FUNC-SPRINT-44 repo engineering-gate"
first_sprint: "FUNC-SPRINT-45"
last_planned_sprint: "FUNC-SPRINT-55"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval_scope: "phase_d_executable_backlog_review"
first_open_sprint: "FUNC-SPRINT-56"
phase_d_status: "closed"
approved_on: "2026-06-12"
approval: "approved_after_phase_c_closure_review"
last_completed_sprint: "FUNC-SPRINT-55"
next_sprint: "FUNC-SPRINT-56"
---

# DevPilot Local — Backlog ejecutable Fase D: IA local gobernada

## Estado de aprobación funcional

Este documento queda promovido a estado `approved` después del cierre validado de `FUNC-SPRINT-44 — Cierre Fase C: repository engineering quality gate`. Su propósito es convertir la **Fase D — IA local gobernada** en un backlog de implementación ejecutable, siguiendo el modelo operativo usado en `docs/functional_backlog_after_precode.md`.

La Fase D queda aprobada para iniciar por `FUNC-SPRINT-45 — ADR y contratos de proveedores locales`. La Fase D agrupa:

- **Ola 6 — ModelAdapter real local-first**.
- **Ola 7 — Agentes especializados monoagente**.

Esta fase parte del estado actual de DevPilot con `ModelAdapter` mock, `ProviderRegistry`, bloqueo de APIs externas por `CostGuard`, MIASI Agent/Tool/Policy Registry, AgentRuntime documental inicial y Evaluation Harness offline. La Fase D busca introducir modelos locales reales y agentes especializados gobernados, sin habilitar APIs externas ni multiagente todavía.

## Estado aprobado para implementación

La revisión de cierre de Fase C confirma que este backlog es una continuación apropiada de DevPilot porque parte de capacidades ya cerradas: Approval Workflow, SafeSubprocessRunner, `tests.run`, Schema/Validation Gateway, Git/Repo read-only, PatchSandbox, RollbackManager, RefactorExecutor sandbox y `repo engineering-gate`.

La aprobación no autoriza APIs externas ni agentes autónomos. La implementación debe comenzar por contratos/ADR de proveedores locales, mantener `mock` como ruta obligatoria para pruebas y tratar Ollama/LM Studio como capacidades opcionales, locales y gobernadas.

## 1. Propósito

La Fase D busca que DevPilot avance desde agentes documentales rule-based y modelos mock hacia IA local real, auditable y gobernada por MIASI.

En lenguaje operativo, esta fase busca pasar desde:

```text
MockModelAdapter + dos agentes documentales + registries MIASI
```

hacia:

```text
Ollama/LM Studio local + prompts versionados + budget ledger + evals de modelos + AgentRuntime v2 + agentes especializados monoagente
```

## 2. Regla central de Fase D

La IA local no debe introducir pérdida de control. Todo modelo o agente debe estar rodeado de:

```text
contrato → provider config → health check → policy → secret redaction → evals → observability → reportes → límites de costo/tiempo → fallback seguro
```

Reglas obligatorias:

1. El proveedor `mock` sigue siendo ruta obligatoria y default para pruebas.
2. Ollama/LM Studio son opcionales y locales.
3. OpenAI/Gemini/Mistral/Hugging Face permanecen bloqueados salvo ADR y aprobación posterior.
4. Ningún agente puede usar un modelo sin ModelAdapterRouter.
5. Todo prompt debe estar versionado o trazado.
6. Todo agente nuevo debe estar registrado en MIASI.
7. Todo agente nuevo debe tener evals mínimas.
8. Todo agente debe operar monoagente; no se implementan handoffs ni MultiAgentCoordinator en Fase D.
9. Todo uso de modelos debe registrar provider, model, latencia estimada, costo estimado y redacción de secretos.
10. Los agentes no deben ejecutar acciones críticas sin Approval Workflow.

## 3. Alcance de Fase D

Incluye:

- ADR de proveedores locales;
- provider config schema;
- OllamaAdapter;
- LMStudioAdapter/OpenAI-compatible local;
- health checks locales;
- capability matrix;
- prompt registry;
- model budget ledger local;
- model eval matrix;
- AgentRuntime v2 model-aware;
- RepoAnalysisAgent;
- CodeReviewAgent;
- PatchReviewAgent;
- SafeRefactorAgent;
- TestPlannerAgent;
- RequirementsAgent/ArchitectureAgent/SecurityAgent iniciales;
- cierre de IA local gobernada.

No incluye:

- APIs externas reales;
- multiagente funcional;
- handoffs;
- RAG;
- memoria persistente avanzada;
- MCP;
- deploy;
- agentes autónomos A4+ sin aprobación.

## 4. Niveles de implementación de Fase D

| Nivel | Nombre | Objetivo | Estado esperado al cierre |
|---|---|---|---|
| FD-L0 | Provider contracts | Formalizar proveedores y configuración | Provider schema + ADR |
| FD-L1 | Local providers | Integrar Ollama y LM Studio | ModelAdapter local operativo opcional |
| FD-L2 | Model governance | Health, budgets, prompts, evals | IA local auditable |
| FD-L3 | Runtime model-aware | AgentRuntime puede usar modelos vía router | Agentes con LLM local controlado |
| FD-L4 | Repo/review agents | Agentes sobre motores existentes | RepoAnalysisAgent/Code/Patch/Refactor |
| FD-L5 | SDLC agents | Agentes de requisitos, arquitectura, seguridad y pruebas | Agentes especializados iniciales |
| FD-L6 | Fase D closure | Validación global de IA local gobernada | Cierre auditado y seguro |

## 5. Definition of Done transversal

Un sprint de Fase D solo puede cerrarse si cumple:

- mantiene el proveedor `mock` en PASS;
- no requiere Ollama/LM Studio para que la suite base pase;
- no requiere APIs externas;
- todo proveedor local falla de forma controlada si no está disponible;
- todo modelo pasa por ModelAdapterRouter, PolicyEngine, SecretGuard y CostGuard;
- todo agente nuevo actualiza Agent Registry, Tool Registry, Policy Matrix si aplica;
- todo agente nuevo tiene evals offline;
- README y runbook se actualizan;
- `pytest -q` pasa sin modelos externos;
- no se imprimen prompts con secretos crudos;
- no se habilita multiagente.

## 6. Convenciones de IDs

| Tipo | Prefijo | Ejemplo |
|---|---|---|
| Sprint funcional | `FUNC-SPRINT-XX` | `FUNC-SPRINT-45` |
| Historia | `US-FUNC-XX-YYY` | `US-FUNC-45-001` |
| Tarea | `FUNC-XX-YYY` | `FUNC-45-003` |
| Prueba | `TEST-FUNC-XX-YYY` | `TEST-FUNC-45-002` |
| Gate | `GATE-FUNC-XX` | `GATE-FUNC-45` |
| Riesgo | `RISK-FUNC-XX-YYY` | `RISK-FUNC-45-001` |
| Modelo | `MODEL-*` | `MODEL-OLLAMA-HEALTH` |
| Agente | `AGENT-*` | `AGENT-CODE-REVIEW` |

## 7. Roadmap funcional de Fase D

| Ola | Sprints | Resultado esperado |
|---|---|---|
| Ola 6 | FUNC-SPRINT-45 a 50 | Proveedores locales, prompts, budgets y evals de modelos |
| Ola 7 | FUNC-SPRINT-51 a 55 | AgentRuntime v2 y agentes especializados monoagente |

## 8. Referencias técnicas externas de apoyo

- Ollama ofrece APIs locales y compatibilidad con endpoints OpenAI en ciertos flujos; DevPilot debe tratarlos como proveedores locales opcionales, no como dependencia obligatoria.
- LM Studio puede exponer un servidor local en `localhost` y endpoints compatibles con OpenAI; DevPilot debe requerir configuración explícita y health checks.
- Frameworks agentic modernos incluyen herramientas, guardrails, handoffs y tracing; DevPilot solo implementará agentes monoagente en Fase D y dejará handoffs/multiagente para una fase posterior.


# FUNC-SPRINT-45 — ADR y contratos de proveedores locales

## Objetivo

Formalizar la arquitectura de proveedores locales de modelos, sus límites, configuración, schemas, estados y política de activación.

## Entradas

- ModelAdapter mock
- ProviderRegistry
- CostGuard
- MIASI Tool Registry
- Fase A SchemaEngine

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-45-001 | Como arquitecto, quiero una ADR antes de integrar proveedores locales. | Existe ADR de IA local gobernada. |
| US-FUNC-45-002 | Como operador, quiero configurar proveedores sin secretos versionados. | Existe provider config schema y example actualizado. |
| US-FUNC-45-003 | Como auditor, quiero que APIs externas sigan bloqueadas. | CostGuard conserva external disabled por defecto. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-45-001 | Crear ADR de proveedores locales | `docs/02_architecture/adrs/ADR-0011-local-model-providers.md` | Decisión y consecuencias documentadas. |
| FUNC-45-002 | Crear provider config schema | `docs/schemas/provider_config.schema.json` | Valida mock/ollama/lmstudio/external disabled. |
| FUNC-45-003 | Actualizar ProviderRegistry | `src/devpilot_core/modeling/providers.py` | Lee config versionada con defaults seguros. |
| FUNC-45-004 | Actualizar providers example | `.devpilot/providers.yaml.example` | Incluye ollama/lmstudio disabled por defecto. |
| FUNC-45-005 | Actualizar MIASI | `tool_registry/policy_matrix` | Tools model local quedan planned/controlled. |

## Archivos previstos

```text
docs/02_architecture/adrs/ADR-0011-local-model-providers.md
docs/schemas/provider_config.schema.json
src/devpilot_core/modeling/providers.py
tests/test_provider_config_schema.py
docs/audits/func_sprint_45_local_providers_adr_audit.md
docs/functional_sprint_45_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core model providers --json
python -m devpilot_core schema validate --schema docs/schemas/provider_config.schema.json --instance .devpilot/providers.yaml.example --json
python -m pytest -q
```

## Criterios PASS

- ADR creada.
- Provider config schema valida example.
- Mock sigue operativo.
- Externos siguen disabled/bloqueados.

## Criterios BLOCK

- No cerrar si provider local queda requerido para tests.
- No cerrar si se versionan API keys.
- No cerrar si APIs externas se habilitan por defecto.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-45-001 | Complejidad de YAML schema | Usar formato JSON/YAML simple y documentado. |
| RISK-FUNC-45-002 | Confusión provider local vs external | Estados explícitos: implemented/planned/disabled. |
| RISK-FUNC-45-003 | Dependencia con SchemaEngine | Si no existe, marcar tarea como pendiente bloqueante o usar validador mínimo. |

## Pruebas mínimas

- TEST-FUNC-45-001: Provider example válido.
- TEST-FUNC-45-002: External provider blocked.
- TEST-FUNC-45-003: Mock generate/classify/embed sigue PASS.
- TEST-FUNC-45-004: Schema invalid config produce finding.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-45: ADR y contratos de proveedores locales. Mantén mock como default, Ollama/LM Studio opcionales y APIs externas bloqueadas.
```


# FUNC-SPRINT-46 — OllamaAdapter local opcional

## Objetivo

Implementar un adaptador Ollama local opcional para generate/classify/embed cuando el servidor esté disponible, sin romper operación offline ni tests base.

## Entradas

- ADR local providers
- ProviderRegistry
- ModelAdapter contracts
- CostGuard
- SecretGuard

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-46-001 | Como desarrollador, quiero usar Ollama local si está disponible. | `model health --provider ollama` y generate local funcionan opcionalmente. |
| US-FUNC-46-002 | Como auditor, quiero que el sistema pase sin Ollama instalado. | Tests base usan mock y health devuelve unavailable controlado. |
| US-FUNC-46-003 | Como operador, quiero límites de timeout. | Adapter tiene timeout y errores controlados. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-46-001 | Crear OllamaAdapter | `src/devpilot_core/modeling/ollama_adapter.py` | Implementa contratos generate/classify/embed cuando posible. |
| FUNC-46-002 | Crear health check | `model health` | Detecta disponibilidad localhost. |
| FUNC-46-003 | Integrar timeout/retry mínimo | `adapter` | Sin bloqueo indefinido. |
| FUNC-46-004 | Agregar tests con mock HTTP/fake client | `tests` | No requieren Ollama real. |
| FUNC-46-005 | Actualizar runbook | `docs/05_operations/runbook.md` | Explica uso opcional. |

## Archivos previstos

```text
src/devpilot_core/modeling/ollama_adapter.py
tests/test_ollama_adapter.py
docs/audits/func_sprint_46_ollama_adapter_audit.md
docs/functional_sprint_46_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core model health --provider ollama --json
python -m devpilot_core model generate --provider ollama --prompt "test" --json
python -m pytest -q
```

## Criterios PASS

- Sin Ollama disponible, health devuelve unavailable controlado.
- Con fake server, generate/classify/embed pasan.
- No hay API externa.
- SecretGuard redacta prompts sensibles.

## Criterios BLOCK

- No cerrar si tests requieren Ollama real.
- No cerrar si una indisponibilidad produce traceback.
- No cerrar si provider local evade CostGuard/PolicyEngine.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-46-001 | Versiones de Ollama cambian endpoints | Encapsular adapter y documentar compatibilidad. |
| RISK-FUNC-46-002 | Timeouts | Timeout configurable corto por defecto. |
| RISK-FUNC-46-003 | Prompts con secretos | SecretGuard antes de request. |

## Pruebas mínimas

- TEST-FUNC-46-001: Fake Ollama generate.
- TEST-FUNC-46-002: Fake Ollama embeddings o fallback documentado.
- TEST-FUNC-46-003: Unavailable server controlado.
- TEST-FUNC-46-004: Provider disabled bloquea llamadas.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-46: OllamaAdapter opcional con health check, timeouts, tests con fake server y sin dependencia de Ollama real.
```


## Estado de implementación Sprint 46

`FUNC-SPRINT-46 — OllamaAdapter local opcional` queda implementado en estado `implemented-initial`. La implementación agrega `OllamaAdapter`, `model health`, timeouts cortos, manejo estructurado de indisponibilidad, tests con fake server y bloqueo de llamadas cuando el provider local está deshabilitado.

El cierre de Sprint 46 no cambia las restricciones centrales de Fase D: `mock` sigue siendo obligatorio/default, Ollama no es requerido para la suite base, las APIs externas siguen bloqueadas, no se habilita multiagente y ningún agente llama modelos directamente fuera de `ModelAdapterRouter`.

Siguiente sprint operativo: `FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible`.


# FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible

## Objetivo

Implementar un adaptador LM Studio local usando endpoints compatibles con OpenAI en localhost, manteniendo APIs externas bloqueadas.

## Entradas

- ADR local providers
- ProviderRegistry
- ModelAdapter contracts
- OllamaAdapter patterns

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-47-001 | Como desarrollador, quiero usar LM Studio como servidor local. | `model health --provider lmstudio` funciona. |
| US-FUNC-47-002 | Como auditor, quiero distinguir base_url local de API externa. | Solo localhost permitido por defecto. |
| US-FUNC-47-003 | Como operador, quiero configurar puerto/modelo local. | Provider config soporta base_url/model. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-47-001 | Crear LMStudioAdapter | `src/devpilot_core/modeling/lmstudio_adapter.py` | Implementa generate/classify/embed si endpoint lo soporta. |
| FUNC-47-002 | Validar base_url localhost | `ProviderRegistry/Policy` | Bloquea hosts no locales. |
| FUNC-47-003 | Agregar health check | `model health` | Verifica servidor local. |
| FUNC-47-004 | Crear tests con fake OpenAI-compatible server | `tests` | No requiere LM Studio real. |
| FUNC-47-005 | Actualizar docs | `runbook/model_card` | Uso local opcional. |

## Archivos previstos

```text
src/devpilot_core/modeling/lmstudio_adapter.py
tests/test_lmstudio_adapter.py
docs/audits/func_sprint_47_lmstudio_adapter_audit.md
docs/functional_sprint_47_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core model health --provider lmstudio --json
python -m devpilot_core model generate --provider lmstudio --prompt "test" --json
python -m pytest -q
```

## Criterios PASS

- LM Studio es opcional.
- Solo localhost/base_url permitida por defecto.
- Fake server tests pasan.
- APIs externas siguen bloqueadas.

## Criterios BLOCK

- No cerrar si base_url remota queda permitida por defecto.
- No cerrar si tests requieren LM Studio real.
- No cerrar si se confunde lmstudio local con OpenAI externo.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-47-001 | Compatibilidad parcial con endpoints | Marcar capabilities por provider. |
| RISK-FUNC-47-002 | Modelo no cargado | Health check específico. |
| RISK-FUNC-47-003 | Base URL insegura | Policy check localhost-only. |

## Pruebas mínimas

- TEST-FUNC-47-001: Health unavailable controlado.
- TEST-FUNC-47-002: Fake completion PASS.
- TEST-FUNC-47-003: Remote URL blocked.
- TEST-FUNC-47-004: Provider disabled blocked.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-47: LMStudioAdapter local OpenAI-compatible, localhost-only, opcional, con tests fake y sin activar API externa.
```

## Estado de implementación Sprint 47

`FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible` queda implementado en estado `implemented-initial`. La implementación agrega `LMStudioAdapter`, health check para `/v1/models`, llamadas locales OpenAI-compatible para `generate`, `classify` y `embed`, timeouts cortos, manejo estructurado de indisponibilidad, tests con fake server y bloqueo de llamadas cuando el provider local está deshabilitado.

El cierre de Sprint 47 no cambia las restricciones centrales de Fase D: `mock` sigue siendo obligatorio/default, LM Studio no es requerido para la suite base, las APIs externas siguen bloqueadas, no se habilita multiagente y ningún agente llama modelos directamente fuera de `ModelAdapterRouter`.

Siguiente sprint operativo: `FUNC-SPRINT-48 — Model governance: health, capability matrix y budget ledger`.


# FUNC-SPRINT-48 — Model governance: health, capability matrix y budget ledger

## Objetivo

Crear gobierno operativo de modelos locales: disponibilidad, capacidades, costos estimados, límites y fallback seguro.

## Entradas

- OllamaAdapter
- LMStudioAdapter
- MockModelAdapter
- LocalStore
- CostGuard

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-48-001 | Como operador, quiero ver qué proveedores/modelos están disponibles. | `model health` y `model capabilities` reportan estado. |
| US-FUNC-48-002 | Como auditor, quiero registrar costos estimados aunque sean cero/locales. | Existe budget ledger local. |
| US-FUNC-48-003 | Como desarrollador, quiero fallback a mock si local no está disponible. | Router aplica fallback configurado. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-48-001 | Crear ModelHealthService | `src/devpilot_core/modeling/health.py` | Unifica health checks. |
| FUNC-48-002 | Crear CapabilityMatrix | `src/devpilot_core/modeling/capabilities.py` | generate/classify/embed/context/window/local/external. |
| FUNC-48-003 | Crear BudgetLedger | `src/devpilot_core/modeling/budget.py` | Registra cost_events. |
| FUNC-48-004 | Extender CLI model | `CLI` | `model health`, `model capabilities`, `model budget status`. |
| FUNC-48-005 | Actualizar LocalStore cost_events | `store` | Persistencia mínima. |

## Archivos previstos

```text
src/devpilot_core/modeling/health.py
src/devpilot_core/modeling/capabilities.py
src/devpilot_core/modeling/budget.py
tests/test_model_governance.py
docs/audits/func_sprint_48_model_governance_audit.md
docs/functional_sprint_48_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core model health --json
python -m devpilot_core model capabilities --json
python -m devpilot_core model budget status --json
python -m pytest -q
```

## Criterios PASS

- Health/capabilities reportan mock/local/external states.
- Budget ledger registra eventos sin costos externos por defecto.
- Fallback a mock documentado.
- No hay llamadas externas.

## Criterios BLOCK

- No cerrar si budget permite gasto externo por defecto.
- No cerrar si provider unavailable falla con crash.
- No cerrar si cost_events guardan prompts completos con secretos.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-48-001 | Costos locales no son monetarios | Separar monetary_cost vs compute_estimate. |
| RISK-FUNC-48-002 | Capability matrix manual obsoleta | Health dinámico + config versionada. |
| RISK-FUNC-48-003 | Exceso de logging | Redacción y truncamiento. |

## Pruebas mínimas

- TEST-FUNC-48-001: Health con mock PASS.
- TEST-FUNC-48-002: Local unavailable controlado.
- TEST-FUNC-48-003: Budget status inicial cero.
- TEST-FUNC-48-004: Cost event redacted.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-48: model health, capability matrix y budget ledger local, manteniendo externos bloqueados y fallback seguro.
```


# FUNC-SPRINT-49 — Prompt Registry y contratos de prompt seguro

## Objetivo

Versionar prompts, plantillas y políticas de redacción para agentes y modelos, evitando prompts sueltos embebidos sin trazabilidad.

## Entradas

- Model governance
- MIASI cards
- SecretGuard
- SchemaEngine

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-49-001 | Como arquitecto agentic, quiero prompts versionados por tarea/agente. | Existe Prompt Registry. |
| US-FUNC-49-002 | Como auditor, quiero saber qué prompt se usó. | Model calls registran prompt_id/version sin exponer secretos. |
| US-FUNC-49-003 | Como revisor de seguridad, quiero checks básicos de prompt injection. | PromptSafetyChecker produce findings. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-49-001 | Crear PromptRegistry | `src/devpilot_core/prompts/registry.py` | Carga prompts versionados. |
| FUNC-49-002 | Crear prompt schema | `docs/schemas/prompt.schema.json` | Valida id/version/inputs/safety. |
| FUNC-49-003 | Crear PromptSafetyChecker | `src/devpilot_core/prompts/safety.py` | Detecta patrones básicos de injection/secrets. |
| FUNC-49-004 | Crear comandos `prompt list/show/validate` | `CLI` | Gestión read-only. |
| FUNC-49-005 | Actualizar MIASI | `docs/06_miasi/tool_card.md` | Prompts como contrato agentic. |

## Archivos previstos

```text
src/devpilot_core/prompts/registry.py
src/devpilot_core/prompts/safety.py
docs/prompts/
docs/schemas/prompt.schema.json
tests/test_prompt_registry.py
docs/audits/func_sprint_49_prompt_registry_audit.md
docs/functional_sprint_49_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core prompt list --json
python -m devpilot_core prompt validate --json
python -m devpilot_core prompt show <prompt_id> --json
python -m pytest -q
```

## Criterios PASS

- Prompts tienen id/version/status.
- No se imprimen secretos crudos.
- Prompt validation funciona.
- PromptSafetyChecker produce findings básicos.

## Criterios BLOCK

- No cerrar si agentes usan prompts no versionados.
- No cerrar si prompt show expone secretos.
- No cerrar si schema de prompts falta o es inválido.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-49-001 | Prompt registry demasiado rígido | Permitir inputs declarados. |
| RISK-FUNC-49-002 | Prompt injection checks incompletos | Marcarlos como básicos, no defensa total. |
| RISK-FUNC-49-003 | Duplicación de prompts | IDs/versiones obligatorias. |

## Pruebas mínimas

- TEST-FUNC-49-001: Prompt válido pasa.
- TEST-FUNC-49-002: Prompt sin id/version falla.
- TEST-FUNC-49-003: Prompt con patrón de secret/injection produce finding.
- TEST-FUNC-49-004: CLI JSON parseable.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-49: PromptRegistry versionado, schema de prompts y checks básicos de seguridad, con comandos read-only.
```

## Estado de implementación Sprint 49

`FUNC-SPRINT-49 — Prompt Registry y contratos de prompt seguro` queda implementado como `implemented-initial`. La implementación agrega `PromptRegistry`, `PromptSafetyChecker`, `docs/schemas/prompt.schema.json`, prompts versionados bajo `docs/prompts/`, comandos read-only `prompt list/show/validate` y soporte de `model generate --prompt-id` para registrar `prompt_id/version` sin almacenar prompts crudos.

Esta versión es deliberadamente inicial: los checks de prompt injection son determinísticos y básicos; no sustituyen una defensa adversarial completa, un sistema de prompt packs con herencia, ni evaluación LLM-as-judge. La transición hacia `FUNC-SPRINT-50` queda condicionada a mantener prompts versionados, `mock` como ruta obligatoria/default, APIs externas bloqueadas, y a conectar la futura evaluación de modelos con prompts trazables.


# FUNC-SPRINT-50 — Model evaluation matrix local

## Objetivo

Crear una matriz de evaluación de modelos locales/mock por tarea DevPilot, manteniendo evaluación offline y reproducible.

## Entradas

- EvalRunner
- Model governance
- PromptRegistry
- Mock/Ollama/LMStudio adapters

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-50-001 | Como arquitecto, quiero comparar proveedores por tarea sin depender de APIs externas. | Existe `model eval run --suite ...`. |
| US-FUNC-50-002 | Como operador, quiero que la evaluación funcione aunque no haya modelos locales. | Mock siempre permite suite base. |
| US-FUNC-50-003 | Como auditor, quiero evidencias de calidad/costo/latencia. | Reporte incluye métricas por provider/model/prompt. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-50-001 | Crear ModelEvalRunner | `src/devpilot_core/modeling/evals.py` | Ejecuta suites de prompts/modelos. |
| FUNC-50-002 | Crear fixtures de model eval | `evals/model_fixtures` | Casos determinísticos para mock. |
| FUNC-50-003 | Crear comando `model eval run` | `CLI` | Evalúa provider/model. |
| FUNC-50-004 | Integrar budget/health | `ModelEvalRunner` | No evalúa provider unavailable salvo solicitado. |
| FUNC-50-005 | Actualizar eval_card | `docs/06_miasi/eval_card.md` | Incluye evaluación de modelos. |

## Archivos previstos

```text
src/devpilot_core/modeling/evals.py
evals/model_fixtures/model_eval_cases.json
tests/test_model_eval_runner.py
docs/audits/func_sprint_50_model_eval_matrix_audit.md
docs/functional_sprint_50_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core model eval run --provider mock --json
python -m devpilot_core model eval run --provider mock --json --write-report
python -m pytest -q
```

## Criterios PASS

- Mock eval suite pasa determinísticamente.
- Providers unavailable se reportan, no rompen suite base.
- Reporte incluye provider/model/prompt_id/metrics.
- No llama APIs externas.

## Criterios BLOCK

- No cerrar si eval requiere modelo local real.
- No cerrar si mide costo externo sin permiso.
- No cerrar si prompts secretos quedan en reportes.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-50-001 | Evaluación superficial | Marcar como baseline inicial. |
| RISK-FUNC-50-002 | Comparaciones injustas entre modelos | Registrar capabilities/context. |
| RISK-FUNC-50-003 | Latencia variable | Métricas separadas y opcionales. |

## Pruebas mínimas

- TEST-FUNC-50-001: Eval mock PASS.
- TEST-FUNC-50-002: Provider unavailable skipped/controlled.
- TEST-FUNC-50-003: Reporte redacted.
- TEST-FUNC-50-004: Budget events generados correctamente.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-50: ModelEvalRunner y matriz de evaluación local, con mock determinístico y proveedores locales opcionales.
```


# FUNC-SPRINT-51 — AgentRuntime v2 model-aware en modo monoagente

## Objetivo

Permitir que AgentRuntime use ModelAdapterRouter y PromptRegistry de forma controlada, manteniendo ejecución monoagente y sin handoffs.

## Entradas

- AgentRuntime
- ModelAdapterRouter
- PromptRegistry
- ModelEvalRunner
- MIASI Agent Registry

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-51-001 | Como arquitecto agentic, quiero agentes que puedan usar modelos vía router seguro. | AgentRuntime v2 soporta model calls gobernadas. |
| US-FUNC-51-002 | Como auditor, quiero que cada model call quede trazada. | AgentToolCall/metadata registra provider/model/prompt_id. |
| US-FUNC-51-003 | Como operador, quiero fallback a mock. | Si provider local no está disponible, usa mock si está configurado. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-51-001 | Extender AgentRuntimeConfig | `agents/runtime.py` | provider/model/prompt policy. |
| FUNC-51-002 | Crear ModelAwareAgent base | `agents/runtime.py o agents/base.py` | Usa ModelAdapterRouter. |
| FUNC-51-003 | Integrar PromptRegistry | `agents` | Prompts versionados. |
| FUNC-51-004 | Actualizar AgentRunResult | `agents/models.py` | Incluye model_calls metadata. |
| FUNC-51-005 | Agregar evals de runtime v2 | `evals` | Mock deterministic tests. |

## Archivos previstos

```text
src/devpilot_core/agents/base.py
src/devpilot_core/agents/runtime.py
src/devpilot_core/agents/models.py
tests/test_agent_runtime_v2.py
docs/audits/func_sprint_51_agent_runtime_v2_audit.md
docs/functional_sprint_51_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core agent run documentation-audit --target docs/01_requirements --provider mock --json
python -m devpilot_core eval run --json
python -m pytest -q
```

## Criterios PASS

- Runtime v2 mantiene agentes anteriores en PASS.
- Model calls pasan por router/policy/secret guard.
- No hay handoffs/multiagente.
- Mock provider permite pruebas herméticas.

## Criterios BLOCK

- No cerrar si agentes llaman adapters directamente.
- No cerrar si provider local se vuelve obligatorio.
- No cerrar si se implementa multiagente accidentalmente.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-51-001 | Acoplamiento de agentes a provider | Usar router + config. |
| RISK-FUNC-51-002 | Prompts no versionados | PromptRegistry obligatorio. |
| RISK-FUNC-51-003 | Regresión de agentes documentales | Evals existentes deben seguir PASS. |

## Pruebas mínimas

- TEST-FUNC-51-001: Agentes actuales sin provider siguen PASS.
- TEST-FUNC-51-002: Agente de prueba usa mock via router.
- TEST-FUNC-51-003: Secret prompt bloqueado/redacted.
- TEST-FUNC-51-004: Unavailable provider fallback controlado.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-51: AgentRuntime v2 model-aware, monoagente, usando ModelAdapterRouter y PromptRegistry, sin handoffs ni multiagente.
```


# FUNC-SPRINT-52 — RepoAnalysisAgent gobernado

## Objetivo

Crear el primer agente especializado sobre motores de Fase C: RepoAnalysisAgent, con tools permitidas, prompts versionados, evals y reportes.

## Entradas

- RepoAnalyzer v2
- AgentRuntime v2
- PromptRegistry
- MIASI Agent Registry
- EvalHarness

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-52-001 | Como arquitecto, quiero un agente que explique el estado del repo. | `agent run repo-analysis` produce resumen gobernado. |
| US-FUNC-52-002 | Como auditor, quiero que el agente use solo tools declaradas. | MIASI allowed_tools restringe repo analyzer. |
| US-FUNC-52-003 | Como desarrollador, quiero sugerencias priorizadas. | Agent suggestions incluyen riesgos y próximos pasos. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-52-001 | Registrar RepoAnalysisAgent en MIASI | `agent_registry/tool_registry/policy_matrix` | Estado implemented-initial. |
| FUNC-52-002 | Crear RepoAnalysisAgent | `src/devpilot_core/agents/repo_analysis_agent.py` | Usa RepoAnalyzer y opcional model mock/local. |
| FUNC-52-003 | Crear prompt versionado | `docs/prompts/repo_analysis_agent.md` | Prompt id/version. |
| FUNC-52-004 | Crear evals | `evals/fixtures` | Casos repo clean/risky. |
| FUNC-52-005 | Actualizar CLI aliases | `agent run repo-analysis` | Alias disponible. |

## Archivos previstos

```text
src/devpilot_core/agents/repo_analysis_agent.py
docs/prompts/repo_analysis_agent.md
tests/test_repo_analysis_agent.py
docs/audits/func_sprint_52_repo_analysis_agent_audit.md
docs/functional_sprint_52_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core agent run repo-analysis --target . --provider mock --json
python -m devpilot_core eval run --json
python -m pytest -q
```

## Criterios PASS

- RepoAnalysisAgent ejecuta en modo monoagente.
- Usa allowed_tools declaradas.
- Produce findings/suggestions/reportes.
- Evals pasan con mock.

## Criterios BLOCK

- No cerrar si agente ejecuta tools no declaradas.
- No cerrar si usa provider externo.
- No cerrar si modifica repo.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-52-001 | Agente repite análisis del motor | Valor añadido: priorización/explicación controlada. |
| RISK-FUNC-52-002 | Salida demasiado verbosa | Estructurar suggestions. |
| RISK-FUNC-52-003 | Confusión con multiagente | Declarar monoagente. |

## Pruebas mínimas

- TEST-FUNC-52-001: Repo limpio produce ok/suggestions moderadas.
- TEST-FUNC-52-002: Repo con riesgo produce findings.
- TEST-FUNC-52-003: Tool policy bloquea target fuera de workspace.
- TEST-FUNC-52-004: Eval case agent repo-analysis PASS.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-52: RepoAnalysisAgent monoagente gobernado por MIASI, basado en RepoAnalyzer, con prompt versionado y evals.
```


# FUNC-SPRINT-53 — CodeReviewAgent y PatchReviewAgent gobernados

## Objetivo

Crear agentes especializados de revisión de código y patch sobre motores existentes, con capacidades explicativas y evaluaciones offline.

## Entradas

- CodeReviewEngine
- PatchReviewEngine
- PatchPreflight
- AgentRuntime v2
- PromptRegistry
- MIASI

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-53-001 | Como revisor, quiero un agente que priorice hallazgos de code review. | `agent run code-review` produce findings/suggestions. |
| US-FUNC-53-002 | Como revisor, quiero un agente que explique riesgos de patch. | `agent run patch-review` produce análisis gobernado. |
| US-FUNC-53-003 | Como auditor, quiero que ambos sigan siendo dry-run. | No modifican archivos ni aplican patches. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-53-001 | Registrar agentes en MIASI | `agent_registry` | code.review y patch.review implemented-initial. |
| FUNC-53-002 | Crear CodeReviewAgent | `src/devpilot_core/agents/code_review_agent.py` | Usa CodeReviewEngine. |
| FUNC-53-003 | Crear PatchReviewAgent | `src/devpilot_core/agents/patch_review_agent.py` | Usa PatchReview/Preflight. |
| FUNC-53-004 | Crear prompts versionados | `docs/prompts` | Prompts por agente. |
| FUNC-53-005 | Crear evals | `evals` | Casos safe/risky code/patch. |

## Archivos previstos

```text
src/devpilot_core/agents/code_review_agent.py
src/devpilot_core/agents/patch_review_agent.py
docs/prompts/code_review_agent.md
docs/prompts/patch_review_agent.md
tests/test_review_agents.py
docs/audits/func_sprint_53_review_agents_audit.md
docs/functional_sprint_53_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core agent run code-review --target src/devpilot_core/validators --provider mock --json
python -m devpilot_core agent run patch-review --patch-file safe.patch --provider mock --json
python -m devpilot_core eval run --json
python -m pytest -q
```

## Criterios PASS

- Agentes son dry-run.
- No aplican patches.
- Integran findings de motores existentes.
- Evals cubren casos safe/risky.

## Criterios BLOCK

- No cerrar si PatchReviewAgent aplica patch.
- No cerrar si CodeReviewAgent modifica código.
- No cerrar si usan provider externo.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-53-001 | Duplicación con comandos existentes | Agente añade priorización/explicación, no reemplaza engine. |
| RISK-FUNC-53-002 | Falsos positivos | Evals y severidades ajustables. |
| RISK-FUNC-53-003 | Patch input peligroso | PathGuard/SecretGuard antes de análisis. |

## Pruebas mínimas

- TEST-FUNC-53-001: CodeReviewAgent con código limpio PASS.
- TEST-FUNC-53-002: CodeReviewAgent detecta eval/os.system fixture.
- TEST-FUNC-53-003: PatchReviewAgent safe PASS.
- TEST-FUNC-53-004: PatchReviewAgent secret/path BLOCK.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-53: CodeReviewAgent y PatchReviewAgent monoagente, dry-run, con MIASI, prompts versionados y evals.
```


# FUNC-SPRINT-54 — SafeRefactorAgent y TestPlannerAgent gobernados

## Objetivo

Crear agentes especializados para planear refactors seguros y pruebas, sin ejecutar cambios reales, usando los motores existentes y `tests.run` como capacidad controlada.

## Entradas

- RefactorPlanner
- RefactorExecutor sandbox
- tests.run
- AgentRuntime v2
- PromptRegistry
- MIASI

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-54-001 | Como desarrollador, quiero un agente que proponga refactors seguros. | `agent run safe-refactor` genera plan y suggestions. |
| US-FUNC-54-002 | Como tester, quiero un agente que proponga pruebas necesarias. | `agent run test-planner` genera plan de pruebas. |
| US-FUNC-54-003 | Como auditor, quiero que ninguno ejecute cambios por defecto. | Ambos operan plan-only/dry-run salvo approval explícita futura. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-54-001 | Registrar SafeRefactorAgent/TestPlannerAgent | `agent_registry` | implemented-initial. |
| FUNC-54-002 | Crear SafeRefactorAgent | `src/devpilot_core/agents/safe_refactor_agent.py` | Usa RefactorPlanner. |
| FUNC-54-003 | Crear TestPlannerAgent | `src/devpilot_core/agents/test_planner_agent.py` | Sugiere tests y usa traceability si existe. |
| FUNC-54-004 | Crear prompts | `docs/prompts` | Prompts versionados. |
| FUNC-54-005 | Crear evals | `evals` | Casos refactor/test plan. |

## Archivos previstos

```text
src/devpilot_core/agents/safe_refactor_agent.py
src/devpilot_core/agents/test_planner_agent.py
docs/prompts/safe_refactor_agent.md
docs/prompts/test_planner_agent.md
tests/test_refactor_testplanner_agents.py
docs/audits/func_sprint_54_refactor_testplanner_agents_audit.md
docs/functional_sprint_54_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core agent run safe-refactor --target src/devpilot_core/repo --provider mock --json
python -m devpilot_core agent run test-planner --target docs/01_requirements --provider mock --json
python -m devpilot_core eval run --json
python -m pytest -q
```

## Criterios PASS

- SafeRefactorAgent no ejecuta cambios reales.
- TestPlannerAgent produce plan trazable.
- Ambos tienen evals.
- MIASI validate PASS.

## Criterios BLOCK

- No cerrar si safe-refactor modifica workspace real sin approval.
- No cerrar si test-planner ejecuta comandos arbitrarios.
- No cerrar si prompts no están versionados.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-54-001 | Plan demasiado genérico | Usar contexto de motores y traceability. |
| RISK-FUNC-54-002 | Agente intenta ejecutar tests sin approval | tests.run solo bajo policy. |
| RISK-FUNC-54-003 | Sobreconfianza en refactor | Mantener plan-only por defecto. |

## Pruebas mínimas

- TEST-FUNC-54-001: SafeRefactorAgent produce rollback/test suggestions.
- TEST-FUNC-54-002: TestPlannerAgent cubre requisitos fixture.
- TEST-FUNC-54-003: Sin approval, ejecución bloqueada.
- TEST-FUNC-54-004: Evals PASS.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-54: SafeRefactorAgent y TestPlannerAgent gobernados, plan-only/dry-run, con prompts, MIASI y evals.
```


# FUNC-SPRINT-55 — Requirements/Architecture/Security agents y cierre Fase D

## Objetivo

Crear versiones iniciales gobernadas de agentes SDLC de alto nivel y cerrar Fase D con evaluación integral de IA local gobernada.

## Entradas

- AgentRuntime v2
- TraceabilityEngine
- PromptRegistry
- ModelEvalRunner
- MIASI

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-55-001 | Como product owner, quiero un agente que revise requisitos. | RequirementsAgent genera hallazgos/sugerencias. |
| US-FUNC-55-002 | Como arquitecto, quiero un agente que revise arquitectura. | ArchitectureAgent revisa C4/ADRs/drift. |
| US-FUNC-55-003 | Como security reviewer, quiero un agente que revise riesgos de seguridad. | SecurityAgent revisa threat/privacy/policy findings. |
| US-FUNC-55-004 | Como owner, quiero cierre de IA local gobernada. | Existe phase D closure report. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-55-001 | Registrar agentes SDLC | `agent_registry` | requirements/architecture/security implemented-initial. |
| FUNC-55-002 | Crear RequirementsAgent | `src/devpilot_core/agents/requirements_agent.py` | Usa validadores/traceability. |
| FUNC-55-003 | Crear ArchitectureAgent | `src/devpilot_core/agents/architecture_agent.py` | Usa C4/drift/ADRs. |
| FUNC-55-004 | Crear SecurityAgent | `src/devpilot_core/agents/security_agent.py` | Usa Policy/SecretGuard/security docs. |
| FUNC-55-005 | Crear cierre Fase D | `docs/audits/phase_d_local_ai_governance_closure_report.md` | Evalúa capacidades y brechas. |

## Archivos previstos

```text
src/devpilot_core/agents/requirements_agent.py
src/devpilot_core/agents/architecture_agent.py
src/devpilot_core/agents/security_agent.py
tests/test_sdlc_agents.py
docs/audits/phase_d_local_ai_governance_closure_report.md
docs/phase_d_manifest.json
docs/functional_sprint_55_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core agent run requirements --target docs/01_requirements --provider mock --json
python -m devpilot_core agent run architecture --target docs/02_architecture --provider mock --json
python -m devpilot_core agent run security --target docs/03_security --provider mock --json
python -m devpilot_core model eval run --provider mock --json
python -m devpilot_core miasi validate --json
python -m pytest -q
```

## Criterios PASS

- Agentes SDLC iniciales operan monoagente.
- Fase D closure report existe.
- Model eval y agent eval pasan con mock.
- No hay multiagente ni APIs externas.

## Criterios BLOCK

- No cerrar si agentes usan providers externos.
- No cerrar si se implementan handoffs/multiagente fuera de alcance.
- No cerrar si MIASI no refleja agentes/tools nuevos.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-55-001 | Agentes de alto nivel generan recomendaciones vagas | Basarlos en validadores/traceability/drift. |
| RISK-FUNC-55-002 | Solapamiento entre agentes | Definir responsabilidades y boundaries. |
| RISK-FUNC-55-003 | Cierre incompleto | Checklist de salida de Fase D obligatorio. |

## Pruebas mínimas

- TEST-FUNC-55-001: RequirementsAgent detecta requisito sin criterio fixture.
- TEST-FUNC-55-002: ArchitectureAgent detecta componente sin código fixture.
- TEST-FUNC-55-003: SecurityAgent detecta policy/secret fixture.
- TEST-FUNC-55-004: Phase D gate PASS con mock.

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-55: agentes Requirements/Architecture/Security iniciales y cierre Fase D, manteniendo IA local gobernada, monoagente y sin APIs externas.
```


## Estado de implementación Sprint 45

`FUNC-SPRINT-45 — ADR y contratos de proveedores locales` queda implementado como `implemented-initial`. El sprint crea `ADR-0011-local-model-providers`, endurece `provider_config.schema.json` a contrato v2, actualiza `.devpilot/providers.yaml.example`, refuerza `ProviderRegistry` con validación semántica y sincroniza MIASI para mantener proveedores locales como capacidades planificadas/controladas.

Alcance real implementado:

- `mock` obligatorio/default y operativo para `generate`, `classify` y `embed`;
- `ollama` y `lmstudio` declarados como locales opcionales, `disabled` por defecto;
- proveedores externos declarados como placeholders `disabled`;
- endpoints locales restringidos a `localhost`, `127.0.0.1` o `[::1]`;
- bloqueo de valores secretos crudos en provider metadata;
- soporte de `schema validate` para el YAML controlado de providers;
- MIASI actualizado con `MODEL_LOCAL_PROVIDER_CONTROLLED`.

Fuera de alcance hasta sprints posteriores:

- no se implementa `OllamaAdapter`;
- no se implementa `LMStudioAdapter`;
- no se hacen health checks reales;
- no se contacta red local ni APIs externas;
- no se habilita multiagente.

Siguiente sprint operativo: `FUNC-SPRINT-46 — OllamaAdapter local opcional`.


## Estado de implementación Sprint 48

`FUNC-SPRINT-48 — Model governance: health, capability matrix y budget ledger` queda implementado en estado `implemented-initial`. La implementación agrega un gobierno operativo inicial para proveedores de modelo mediante:

- `ModelHealthService`, que consolida health checks de `mock`, Ollama, LM Studio y providers externos bloqueados.
- `CapabilityMatrix`, que declara capacidades `generate`, `classify`, `embed`, health, contexto estimado, alcance de red, fallback y controles requeridos.
- `BudgetLedger`, que registra y consulta `cost_events` locales sin almacenar prompts, completions ni secretos.
- CLI `model health --json`, `model capabilities --json` y `model budget status --json`.
- fallback configurado a `mock` mediante `--fallback-to-mock` para providers locales habilitados pero no disponibles.

Alcance real implementado:

- health/capabilities no requieren modelos locales reales para que la suite base pase;
- providers externos siguen bloqueados y no se contactan;
- budget ledger separa costo monetario de `compute_estimate_units`;
- los eventos de costo se almacenan en SQLite runtime y no incluyen payloads crudos;
- fallback a `mock` no es silencioso: queda reflejado en `summary.fallback_applied` y en finding `MODEL_FALLBACK_TO_MOCK_APPLIED`.

Fuera de alcance hasta sprints posteriores:

- prompt registry y prompt packs gobernados;
- model eval matrix;
- AgentRuntime v2 model-aware;
- streaming, retries avanzados y métricas reales de latencia;
- budget enforcement monetario avanzado para APIs externas.

Siguiente sprint operativo: `FUNC-SPRINT-49 — Prompt Registry y Prompt Packs gobernados`.


## Estado de implementación Sprint 50

`FUNC-SPRINT-50 — Model evaluation matrix local` queda implementado como capacidad `implemented-initial` de Fase D. La implementación agrega `ModelEvalRunner`, fixtures bajo `evals/model_fixtures`, comando `model eval run`, integración con `PromptRegistry`, `ModelAdapterRouter`, `ModelHealthService` y `BudgetLedger`, más reportes redacted opcionales.

Alcance real implementado:

- suite `model-local-smoke` ejecutable con `mock` sin modelos locales reales;
- casos determinísticos para `generate`, `classify` y `embed`;
- métricas preliminares de calidad, tokens, costo estimado y latencia;
- providers locales deshabilitados/no disponibles reportados como `skipped` controlado;
- reportes sin prompts crudos, completions crudas ni secretos;
- MIASI actualizado con la herramienta `model.eval.run` y la política `MODEL_EVAL_RUN_ALLOW`.

Fuera de alcance hasta sprints posteriores:

- jueces LLM;
- benchmarks grandes o estadísticos;
- evaluación con APIs externas;
- AgentRuntime v2 model-aware;
- evaluación de agentes especializados monoagente.

Siguiente sprint operativo: `FUNC-SPRINT-51 — AgentRuntime v2 model-aware en modo monoagente`.


## Estado de implementación Sprint 51

`FUNC-SPRINT-51 — AgentRuntime v2 model-aware en modo monoagente` queda implementado como `implemented-initial`. La implementación extiende `AgentRuntimeConfig`, agrega `ModelAwareAgent`, incorpora `AgentModelCall` y permite a los agentes documentales existentes ejecutar llamadas opcionales de generación mediante `PromptRegistry` y `ModelAdapterRouter`.

Alcance real implementado:

- los agentes `precode.audit` y `precode.documentation` conservan comportamiento sin modelo por defecto;
- `agent run ... --provider mock` activa model calls gobernadas y redacted;
- `AgentRunResult` reporta `model_calls` con provider/model/prompt_id/prompt_version/tokens/costo/digest;
- `BudgetLedger` recibe eventos `source=agent-runtime-v2` sin prompts ni completions crudos;
- `EvalRunner` incluye un caso model-aware en la suite `documentation`;
- MIASI declara `agent.model.generate` y la política `AGENT_MODEL_CALL_GOVERNED_ALLOW`;
- no se implementan handoffs, supervisor, MultiAgentCoordinator ni ejecución multiagente.

Fuera de alcance hasta sprints posteriores:

- RepoAnalysisAgent especializado;
- agentes de code review, patch review y safe refactor con modelos;
- memoria de agente, sesiones persistentes avanzadas y handoffs;
- uso de APIs externas.

Siguiente sprint operativo: `FUNC-SPRINT-52 — RepoAnalysisAgent gobernado`.


## Estado de implementación Sprint 52

`FUNC-SPRINT-52 — RepoAnalysisAgent gobernado` queda implementado como `implemented-initial`. La implementación agrega el primer agente especializado de repositorio sobre motores de Fase C (`RepoAnalyzer`, `DependencyGraphBuilder`, `GitAdapter` y `RepoQualityGate`) y lo ejecuta exclusivamente a través de `AgentRuntime v2` en modo monoagente.

Alcance real implementado:

- `agent run repo-analysis --target . --provider mock --json` ejecuta análisis read-only con herramientas declaradas en MIASI;
- el agente usa `PromptRegistry` y `ModelAdapterRouter` solo cuando se activa provider/prompt;
- `repo.analysis` pasa a estado `implemented-initial`;
- MIASI declara `agent.repo_analysis.run` y la política `REPO_ANALYSIS_AGENT_GOVERNED_ALLOW`;
- `EvalRunner` incorpora casos `agent.repo_analysis` y `agent.repo_analysis_model_aware`;
- los reportes y resultados no almacenan prompts, outputs crudos ni secretos.

Fuera de alcance hasta sprints posteriores:

- CodeReviewAgent, PatchReviewAgent y SafeRefactorAgent gobernados;
- ejecución multiagente, handoffs y supervisores;
- aplicación de patches o refactors productivos;
- APIs externas y modelos locales obligatorios.

Siguiente sprint operativo: `FUNC-SPRINT-53 — CodeReviewAgent y PatchReviewAgent gobernados`.

## Estado de implementación Sprint 53

`FUNC-SPRINT-53 — CodeReviewAgent y PatchReviewAgent gobernados` queda implementado como capacidad `implemented-initial` de Fase D.

La implementación agrega `CodeReviewAgent` y `PatchReviewAgent` como agentes monoagente sobre motores existentes (`CodeReviewEngine`, `PatchReviewEngine` y `PatchPreflightEngine`). Ambos agentes operan en dry-run, no modifican archivos, no aplican patches y pueden ejecutar una explicación model-aware gobernada mediante `PromptRegistry`, `ModelAdapterRouter` y `BudgetLedger`.

Artefactos principales:

- `src/devpilot_core/agents/code_review_agent.py`.
- `src/devpilot_core/agents/patch_review_agent.py`.
- `docs/prompts/code.review.agent.v1.json`.
- `docs/prompts/patch.review.agent.v1.json`.
- `tests/test_review_agents.py`.
- `docs/audits/func_sprint_53_review_agents_audit.md`.
- `docs/functional_sprint_53_manifest.json`.

La implementación corrige la desviación prevista del backlog que sugería prompts `.md`: por consistencia con `PromptRegistry` y el schema de Sprint 49, los prompts se implementan como contratos JSON versionados. Esta decisión no requiere ADR nueva porque mantiene la arquitectura ya aprobada y no introduce proveedores, APIs externas, acciones destructivas ni multiagente.

Siguiente sprint abierto: `FUNC-SPRINT-54 — SafeRefactorAgent y TestPlannerAgent gobernados`.


## Estado de implementación Sprint 54

`FUNC-SPRINT-54 — SafeRefactorAgent y TestPlannerAgent gobernados` queda en estado `implemented-initial`. La implementación crea `SafeRefactorAgent` y `TestPlannerAgent` sobre `AgentRuntime v2`, `PromptRegistry`, `ModelAdapterRouter`, `BudgetLedger` y MIASI.

Alcance real aplicado: se mantiene una variante estrictamente plan-only/dry-run. `SafeRefactorAgent` usa `RefactorPlanner` para producir candidatos, plan, verificación y rollback, pero no invoca `RefactorExecutor` ni genera/aplica patches. `TestPlannerAgent` usa `TraceabilityEngine` y perfiles `tests.run` declarados para sugerir planes trazables, pero no ejecuta pytest ni comandos arbitrarios.

La decisión de usar prompts JSON (`safe.refactor.agent.v1.json` y `test.planner.agent.v1.json`) en lugar de `.md` mantiene compatibilidad con el contrato `PromptRegistry` vigente desde Sprint 49. No se requiere ADR nueva porque no se introduce proveedor, API externa, patrón multiagente, ejecución destructiva ni frontera de seguridad nueva.

Criterios de cierre: pruebas específicas de agentes, evals offline, `prompt validate`, `miasi validate`, manifest, auditoría y gates documentales deben permanecer en PASS. Criterios BLOCK: ejecución real de refactor sin approval, ejecución de `tests.run` sin aprobación, comandos arbitrarios, prompts no versionados o mutación de workspace real.


## Estado de implementación Sprint 55

`FUNC-SPRINT-55 — Requirements/Architecture/Security agents y cierre Fase D` queda implementado como `implemented-initial`. Se agregaron `RequirementsAgent`, `ArchitectureAgent` y `SecurityAgent`, todos monoagente, read-only, gobernados por MIASI, integrados con `AgentRuntime v2`, `PromptRegistry`, `ModelAdapterRouter` y `BudgetLedger`.

El cierre de Fase D queda soportado por:

- `docs/audits/phase_d_local_ai_governance_closure_report.md`;
- `docs/phase_d_manifest.json`;
- `docs/functional_sprint_55_manifest.json`;
- evals offline con `mock`;
- validación MIASI y PromptRegistry.

La Fase D queda cerrada funcionalmente, pero las capacidades siguen marcadas como iniciales cuando corresponde. No se habilitaron APIs externas, handoffs, multiagente, RAG, memoria avanzada ni ejecución autónoma. El siguiente frente lógico es `FUNC-SPRINT-56 — ADR de observabilidad v2 y modelo AgentOps`, correspondiente a Fase E, aún sujeto a revisión/aprobación de backlog.
