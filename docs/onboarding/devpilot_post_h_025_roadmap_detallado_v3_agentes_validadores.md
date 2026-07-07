# DevPilot - Roadmap ampliado posterior a POST-H-025

## 1. Fuentes de verdad incorporadas

Para esta revision se incorporaron las siguientes fuentes vigentes:

- `repo_DevPilot_Local_262_POST_H_025_E.zip`, descomprimido en `/workspace/devpilot_repo_262_current`.
- `devpilot_onboarding_report_final_compilado.md`.
- `devpilot_post_h_025_roadmap_detallado.md`.

Verificacion de contexto:

- El log de validacion general de la version 262 reporto `1536 passed, 0 failed, 0 errors, 0 skipped`.
- El informe compilado contiene `260` preguntas unicas, sin faltantes ni duplicados.
- El estado del producto sigue siendo `production-ready-local`, no `enterprise-ready`, no `remote-ready`, no `SaaS-ready`, no `compliance-certified`.

## 2. Dictamen de ajuste del roadmap

El roadmap anterior es correcto como base, pero debe ampliarse en dos frentes que son centrales para la propuesta de valor de DevPilot:

1. Una ola explicita de evolucion de agentes de IA, LLM locales/API, RAG, memoria, tools, tool calls y MCP.
2. Una ola explicita de evolucion de validadores hardcodeados hacia contratos JSON Schema, registries versionados y reglas semanticas declarativas.

Tambien se aclara que la Web UI no debe cubrir de forma indiscriminada toda la superficie CLI. La UI debe cubrir flujos de operador, visualizacion, evidence, estado, reportes, trazas, approvals locales y acciones dry-run/plan-only. Algunas capacidades deben permanecer CLI-only o requerir ADR/backlog especifico antes de exponerse por UI.

## 3. Estado actual de agentes e IA

### 3.1 Agentes actualmente identificados

El repo contiene agentes bajo:

```text
src/devpilot_core/agents/
src/devpilot_core/multiagent/
src/devpilot_core/modeling/
src/devpilot_core/rag/
src/devpilot_core/miasi/
```

Agentes principales:

- `DocumentationAuditAgent`
- `PreCodeDocumentationAgent`
- `RepoAnalysisAgent`
- `CodeReviewAgent`
- `PatchReviewAgent`
- `SafeRefactorAgent`
- `TestPlannerAgent`
- `RequirementsAgent`
- `ArchitectureAgent`
- `SecurityAgent`
- `ReleaseAgent`

El runtime se implementa en:

```text
src/devpilot_core/agents/runtime.py
```

El contrato base model-aware se implementa en:

```text
src/devpilot_core/agents/base.py
```

El enrutamiento de modelos se implementa en:

```text
src/devpilot_core/modeling/router.py
src/devpilot_core/modeling/providers.py
src/devpilot_core/modeling/contracts.py
```

### 3.2 Clasificacion industrial actual

| Categoria | Agentes/capacidades | Estado actual | Recomendacion |
|---|---|---|---|
| Deterministicos que deben permanecer asi | Gates, validators, claims validator, readiness, release checks, policy checks, no-go gates, evidence aggregator | Implemented/implemented-initial | Deben seguir deterministas. Pueden recibir asistencia LLM solo como comentario no vinculante. |
| Agentes rule-based con model-aware opcional | Requirements, Architecture, Security, Code Review, Patch Review, Safe Refactor, Test Planner, Repo Analysis, Documentation Audit | Implemented-initial | Evolucionar con LLM local/API controlado, pero sin perder decision deterministica ni PASS/BLOCK reproducible. |
| Agente release | `ReleaseAgent` | Principalmente deterministico, orientado a evidencia local | Debe permanecer deterministico en decisiones de release. LLM solo puede resumir hallazgos, no decidir release. |
| Pre-code documentation | `PreCodeDocumentationAgent` | Rule-based, puede escribir drafts en `outputs/` con controles | Puede beneficiarse de LLM local/API para borradores, siempre bajo `outputs/`, review humana y SecretGuard. |
| Multiagent | `src/devpilot_core/multiagent` | Gobernado/dry-run, no swarm productivo | Evolucionar gradualmente con handoffs controlados, sin autonomia irrestricta. |
| RAG local | `src/devpilot_core/rag` | Implemented-initial, lexical/local, groundedness evals | Debe evolucionar a retrieval mas robusto, citas, freshness, evaluaciones negativas y eventual LLM judge controlado. |
| Memoria | Agent sessions existen, pero `semantic_memory_enabled=false` y `rag_enabled=false` en runtime de sesiones | Deshabilitada/metadata | Introducir memoria solo como capability versionada, local, redactada, opt-in y auditable. |
| Tools/tool calls | MIASI tools/policies existen; AgentRuntime registra tool calls internos | Controlados por PolicyEngine/MIASI | Evolucionar a tool calling formal con allowlist, schema, approvals, dry-run-first y audit trail. |
| MCP | El informe menciona MCP como frente futuro/eval; no se debe tratar como ejecucion productiva general | Futuro/design-only | Requiere ADR, threat model, connector sandbox, permission model y fake MCP server antes de produccion local. |

## 4. Principio rector para agentes avanzados

DevPilot debe evolucionar de `agent-assisted` a `agent-governed`, no a autonomia irrestricta.

Reglas:

- El LLM nunca debe ser la unica fuente de verdad para PASS/BLOCK.
- Las decisiones de release, claims, no-go gates, seguridad, schemas y quality gates deben seguir siendo deterministicas.
- Las salidas LLM deben ser sugerencias, resumenes, borradores o clasificaciones preliminares.
- Todo uso LLM debe registrar proveedor, modelo, prompt id, version, digest, costo estimado, redaccion y evidencia.
- Los outputs crudos de prompts/modelos no deben almacenarse salvo que exista politica explicita, redaccion y retention.
- Providers locales deben ser preferidos antes que APIs externas.
- APIs externas deben permanecer disabled por defecto y requerir CostGuard, SecretGuard, policy, opt-in, logs y no-go review.
- Tool calls deben ser declarativos, schema-backed, dry-run-first y sujetos a approvals si mutan estado.

## 5. Roadmap ajustado por olas

### Ola 1 - POST-H-026: Release candidate local y verificacion de operador

Objetivo:

Convertir la declaracion `production-ready-local` en release candidate local verificable.

Micro-sprints:

- `POST-H-026-A - Evidence freshness model`
- `POST-H-026-B - Release candidate verification profile`
- `POST-H-026-C - Install smoke local`
- `POST-H-026-D - UI/API local smoke under RC`
- `POST-H-026-E - RC PASS/BLOCK report`

### Ola 2 - POST-H-027: Packaging reproducible e instalacion local

Objetivo:

Hacer que DevPilot sea instalable y verificable por un operador desde artefactos reproducibles.

Micro-sprints:

- `POST-H-027-A - Source ZIP release policy hardening`
- `POST-H-027-B - Wheel/sdist install verification`
- `POST-H-027-C - Artifact manifest and checksums`
- `POST-H-027-D - Windows install guide and smoke`
- `POST-H-027-E - Upgrade/rollback dry-run`

### Ola 3 - POST-H-028: UI/API local hardening
 
Objetivo:

Elevar UI/API desde shell local a consola operacional local robusta.

Micro-sprints:

- `POST-H-028-A - API contract drift guard`
- `POST-H-028-B - Local auth and CORS hardening`
- `POST-H-028-C - Visual smoke tests`
- `POST-H-028-D - Operator flows and error states`
- `POST-H-028-E - UI route registry enforcement`

Regla de alcance:

La UI no debe replicar todos los comandos CLI. Debe cubrir flujos de operador y evidencia. La CLI debe conservar capacidades avanzadas, batch, diagnostico profundo, release, scripts y operaciones sensibles.

### Ola 4 - POST-H-029: Testing tiers, impacto y costo de regresion

Objetivo:

Hacer sostenible la evolucion con perfiles de pruebas accionables.

Micro-sprints:

- `POST-H-029-A - Test profile taxonomy`
- `POST-H-029-B - TCR v2 impact rules`
- `POST-H-029-C - Test impact CLI recommendations`
- `POST-H-029-D - Release candidate test profile`
- `POST-H-029-E - Historical regression guard`

### Ola 5 - POST-H-030: CLI hotspot reduction y boundaries de aplicacion

Objetivo:

Reducir riesgo de mantenibilidad en `src/devpilot_core/cli.py`.

Micro-sprints:

- `POST-H-030-A - CLI command ownership matrix`
- `POST-H-030-B - Industrial readiness command extraction`
- `POST-H-030-C - Release command extraction`
- `POST-H-030-D - Workspace/onboarding command extraction`
- `POST-H-030-E - CLI compatibility contract tests`

### Ola 6 - POST-H-031: Observabilidad, evidence graph y operador

Objetivo:

Hacer que el operador entienda salud, gaps, claims, no-go gates y evidencia sin leer todo el repo.

Micro-sprints:

- `POST-H-031-A - Evidence graph model`
- `POST-H-031-B - Operator health summary`
- `POST-H-031-C - Gap-to-action mapping`
- `POST-H-031-D - Claims and no-go dashboard`
- `POST-H-031-E - Redacted evidence export UX`

### Ola 7 - POST-H-032: Agentes IA avanzados, LLM, RAG, memoria y tools

Objetivo:

Consolidar la propuesta diferenciadora de DevPilot como plataforma agent-assisted/agent-governed, incorporando LLM locales y eventualmente APIs externas bajo controles industriales.

Micro-sprints sugeridos:

#### POST-H-032-A - Agent capability inventory and promotion criteria

Entregables:

- Inventario machine-readable de agentes.
- Clasificacion por modo: deterministic, rule-based, model-aware, RAG-aware, tool-calling, multiagent.
- Matriz de riesgo por agente.
- Criterios para promover un agente de `implemented-initial` a `production-ready-local`.

Criterios PASS:

- Cada agente declara autonomy level, tools permitidas, policy rules, eval coverage, observability y memory/RAG flags.
- Ningun agente puede mutar fuente o ejecutar herramientas externas sin approval.

#### POST-H-032-B - Local LLM provider hardening

Entregables:

- Endurecer Ollama/LM Studio como providers locales.
- Health checks robustos.
- Provider registry schema-backed.
- Cost/BudgetLedger extendido para locales.
- Fallback controlado a mock.

Criterios PASS:

- Local providers siguen disabled por defecto.
- Solo localhost.
- Sin secretos.
- Sin external API.
- Tests con fake/local provider.

#### POST-H-032-C - External API provider ADR and gated pilot

Entregables:

- ADR para uso de APIs externas.
- Policy de opt-in.
- Secret handling por environment variables.
- CostGuard real.
- No-go gate para evitar external API accidental.
- Reporte de riesgo.

Criterios PASS:

- APIs externas disabled por defecto.
- Ninguna prueba depende de API real.
- Fake API provider cubre contrato.
- Cualquier llamada real requiere configuracion local explicita, warning visible y reporte.

#### POST-H-032-D - RAG-aware agents

Entregables:

- Integrar RAG local con agentes seleccionados: requirements, architecture, security, test planner, release assistant.
- Context pack con citas, source ids y freshness.
- Groundedness eval por agente.
- Negative cases para hallucination/unsupported claims.

Criterios PASS:

- Cada sugerencia RAG-aware incluye fuentes.
- Si no hay fuente suficiente, el agente debe decir `insufficient evidence`.
- No se usa RAG para justificar claims prohibidos.

#### POST-H-032-E - Agent memory model

Entregables:

- ADR de memoria local.
- Schema de `agent_memory_record`.
- Retention/redaction policy.
- Memoria semanticamente opt-in.
- Separacion entre session memory, project memory y report evidence.

Criterios PASS:

- `semantic_memory_enabled=false` por defecto.
- No se almacenan prompts crudos ni outputs crudos.
- Memoria exportable/redactada.
- Operador puede inspeccionar y limpiar memoria.

#### POST-H-032-F - Tool calling contract

Entregables:

- Schema para tool calls.
- Tool registry executable subset.
- Allowlist por agente.
- Dry-run-first para toda tool.
- Approval binding para tools de riesgo.
- Observability por tool call.

Criterios PASS:

- Tool calls validan contra schema.
- Tool injection guard cubre entradas.
- No connector write, no plugin execution y no remote execution.
- Tests adversariales para prompt/tool injection.

#### POST-H-032-G - MCP design and local fake-server evaluation

Entregables:

- ADR MCP.
- Threat model MCP.
- Fake MCP server local para tests.
- Mapping MCP tools -> MIASI Tool Registry.
- Permission model y audit trail.

Criterios PASS:

- MCP real no se habilita por defecto.
- Fake server prueba contratos sin red externa.
- Tools MCP no pueden escribir ni ejecutar sin policy/approval.

#### POST-H-032-H - Multiagent handoff hardening

Entregables:

- Handoff schema.
- Workflow registry.
- Supervisor deterministic gate.
- Human-in-the-loop checkpoints.
- Evals por workflow.

Criterios PASS:

- No swarm autonomo.
- Handoffs visibles.
- Cada agente mantiene scope y tools propios.
- El supervisor puede bloquear por evidencia insuficiente.

### Ola 8 - POST-H-033: Validadores schema-backed y semantica declarativa

Objetivo:

Reducir hardcoding residual en validadores, conservando determinismo y compatibilidad.

Hallazgos relevantes:

- `validators/artifact_profiles.py` conserva perfiles Python como fallback.
- `docs/validation/artifact_profiles.json` ya es fuente primaria para perfiles de artefactos.
- `validators/frontmatter.py` mantiene campos requeridos, estados permitidos y regex hardcodeados.
- `validators/readiness.py` mantiene listas de artefactos requeridos hardcodeadas.
- `miasi/registry.py` mantiene enums/listas permitidas y reglas de coverage hardcodeadas.
- `miasi/semantic.py` mantiene reglas semanticas programaticas y tokens de guardas/no-go hardcodeados.
- `docs_governance/validator.py` mantiene reglas y severidades programaticas.
- `policy/prompt_guard.py` y otros guards usan patrones regex hardcodeados, lo cual es aceptable como defensa base, pero debe hacerse extensible por catalogo versionado.

Micro-sprints sugeridos:

#### POST-H-033-A - Validator inventory and migration plan

Entregables:

- Inventario de validadores hardcodeados.
- Clasificacion: schema, semantic rule, security guard, fallback compatibility, parser.
- Decidir cuales deben quedar en codigo y cuales migran a JSON.

Criterios PASS:

- Cada validador tiene owner, contrato, severidad, inputs, outputs, tests y estado de migracion.

#### POST-H-033-B - Frontmatter schema-backed validator

Entregables:

- `docs/schemas/frontmatter_metadata.schema.json`.
- Catalogo de estados permitidos.
- Regex declarativas para version/date/doc_id.
- Compatibilidad con parser actual.

Criterios PASS:

- Frontmatter sigue deterministico.
- Los documentos existentes validan igual o con migracion explicita.

#### POST-H-033-C - Readiness requirements registry

Entregables:

- `.devpilot/readiness/readiness_requirements.json`.
- Schema de readiness requirements.
- Reemplazo progresivo de `REQUIRED_PRE_CODE_ARTIFACTS`, `REQUIRED_MIASI_ARTIFACTS`, `STRICT_REQUIRED_ARTIFACTS`.

Criterios PASS:

- Readiness usa registry como fuente primaria.
- Python conserva fallback temporal.
- Tests prueban ausencia, drift y compatibilidad.

#### POST-H-033-D - MIASI semantic rules registry

Entregables:

- `.devpilot/miasi/semantic_rules.json`.
- Schema de reglas semanticas.
- Rule engine declarativo para categorias, severidades, subjects, no-go markers y guard requirements.

Criterios PASS:

- Reglas MIASI no-go siguen bloqueando.
- Tokens sensibles y guard mappings se versionan.
- El reporte semantico indica rule source y version.

#### POST-H-033-E - Policy/guard pattern catalogs

Entregables:

- Catalogos versionados para PromptGuard, ToolInjectionGuard, SecretGuard donde aplique.
- Mantener patrones built-in no removibles para defensa base.
- Permitir extensiones locales sin debilitar reglas core.

Criterios PASS:

- No se puede deshabilitar una regla critica sin ADR/backlog.
- Catalogo valida contra schema.
- Tests adversariales siguen pasando.

#### POST-H-033-F - Docs governance rule registry

Entregables:

- Registry de reglas docs-governance.
- Severidad, criticality, required_tests, frontmatter requirements y lifecycle por dato.
- Integracion con source registry.

Criterios PASS:

- Docs governance sigue bloqueando source-of-truth drift.
- Reglas son auditables y versionadas.

### Ola 9 - POST-H-034: ADRs de capacidades sensibles

Objetivo:

Formalizar decisiones antes de habilitar remote, connector write, plugin execution, multiusuario, enterprise o SaaS.

Micro-sprints:

- `POST-H-034-A - Connector write ADR`
- `POST-H-034-B - Plugin execution ADR`
- `POST-H-034-C - Remote execution ADR-3`
- `POST-H-034-D - Multiuser/auth ADR`
- `POST-H-034-E - Enterprise/SaaS boundary ADR`

## 6. UI web: criterio de cobertura frente a CLI

La Web UI no debe cubrir toda la superficie funcional de la CLI de forma equivalente.

### 6.1 Lo que si debe cubrir la UI

La UI debe cubrir flujos de operador:

- Dashboard local.
- Estado de workspace.
- Quality gates principales.
- Production-ready/RC status.
- Reports viewer.
- Trace viewer.
- Metrics summary.
- Approval Center local.
- Settings read-only o plan-only.
- Provider settings plan-only.
- Security posture.
- Evidence graph.
- Test impact recommendations.
- Onboarding/readiness preview.
- RAG/query visual si se mantiene read-only y con citas.
- Agent run preview para agentes seguros, dry-run y model-aware controlado.

### 6.2 Lo que debe permanecer CLI-only por defecto

Debe permanecer CLI-only, salvo ADR/backlog especifico:

- Release build/verify avanzado.
- Package build ejecutable.
- Cleanup/restore/backup execute.
- Git/archive operations.
- Runtime state cleanup execute.
- Cualquier escritura de source files.
- Activacion de provider API externo.
- Configuracion real de secrets.
- Connector write.
- Plugin execution.
- Remote execution.
- Multiagent workflows con tools de riesgo.
- Migraciones de DB.
- Operaciones batch o scripts de mantenimiento.
- Debug profundo y comandos internos de governance.

### 6.3 Criterio para exponer una CLI operation en UI

Una operacion puede exponerse en UI si:

- Existe route contract.
- Pasa por ApplicationService/API.
- Tiene auth local.
- Tiene policy check.
- Es read-only, dry-run o plan-only.
- Tiene estados visuales loading/empty/error/BLOCK.
- No expone secretos.
- No lee filesystem directo desde browser.
- Tiene tests UI/API.
- Tiene entrada/salida schema-backed.
- No habilita no-go gates.

## 7. Secuencia recomendada actualizada

Orden actualizado:

1. `POST-H-026` - RC local.
2. `POST-H-027` - Packaging/install.
3. `POST-H-028` - UI/API hardening.
4. `POST-H-029` - Testing tiers/impact.
5. `POST-H-030` - CLI hotspot reduction.
6. `POST-H-031` - Evidence graph/operator console.
7. `POST-H-032` - Agentes IA avanzados, LLM, RAG, memoria, tools, MCP.
8. `POST-H-033` - Validadores schema-backed y semantica declarativa.
9. `POST-H-034` - ADRs de capacidades sensibles.
10. `POST-H-035+` - Implementaciones sensibles solo si cumplen ADR, threat model, tests, gates y approvals.

## 8. Riesgos principales del roadmap ampliado

- Convertir sugerencias LLM en decisiones deterministicas sin evidencia.
- Habilitar API externa sin opt-in, CostGuard y SecretGuard.
- Introducir memoria sin redaccion/retention.
- Habilitar tool calls sin schema/allowlist/approval.
- Confundir MCP design con MCP productivo.
- Exponer en UI operaciones que deben ser CLI-only.
- Migrar validadores a JSON sin conservar fallback ni tests de compatibilidad.
- Relajar hardcoded guards criticos bajo pretexto de configurabilidad.

## 9. Dictamen final

La propuesta de valor de agentes en DevPilot esta correctamente iniciada, pero debe convertirse en una ola explicita de producto. El siguiente salto no debe ser autonomia. Debe ser:

- agentes mas utiles;
- LLM locales controlados;
- APIs externas opcionales y gobernadas;
- RAG con citas y groundedness;
- memoria local redactada y opt-in;
- tool calls schema-backed;
- MCP con ADR y fake server local;
- multiagent con handoffs auditables;
- evaluaciones adversariales.

En paralelo, los validadores deben evolucionar hacia schemas y reglas semanticas declarativas, sin eliminar el determinismo ni los guards hardcodeados que funcionan como defensa base.
