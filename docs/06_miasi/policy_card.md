---
title: "Policy Card — DevPilot Local"
doc_id: "DEVPL-MIASI-POLICY"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIASI"
parent_standard: "MIPSoftware"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
source_baseline: "security approved + architecture approved + quality/operations approved"
change_policy: "controlled_changes_allowed_until_precode_baseline"
baseline_role: "precode_approved_baseline"
---

# Policy Card — DevPilot Local

## 1. Propósito

Este documento define las políticas de ejecución de DevPilot Local para agentes, herramientas, modelos, filesystem, Git, patches, persistencia, costos, secretos y aprobación humana.

La regla central es:

> DevPilot opera bajo deny-by-default, dry-run por defecto, privilegio mínimo, trazabilidad obligatoria y aprobación humana para acciones críticas.

## 2. Principios de política

| Principio | Regla |
|---|---|
| Local-first híbrido | Local por defecto, APIs opcionales y controladas. |
| Dry-run por defecto | Ninguna acción con side effect inicia en execute. |
| Deny-by-default | Lo no permitido explícitamente queda bloqueado. |
| Least privilege | Cada agente/tool solo accede a lo necesario. |
| Human approval | Escritura, patch, refactor, Git write y despliegue requieren aprobación. |
| Cost controlled | APIs externas requieren presupuesto, proveedor permitido y trazabilidad. |
| Secret safe | Secretos redactados, nunca impresos ni enviados sin permiso. |
| Auditable | Todo gate, tool call, aprobación y costo deja evidencia. |
| Deterministic gate first | El agente recomienda, el gate determina. |

## 3. Modos de ejecución

| Modo | Descripción | Permitido en MVP |
|---|---|---:|
| `read_only` | Solo lectura de artefactos permitidos. | Sí |
| `dry_run` | Simula acción y reporta impacto. | Sí |
| `suggest` | Propone cambios sin escribirlos. | Sí |
| `write_report` | Escribe reportes en rutas controladas. | Sí |
| `write_artifact_candidate` | Escribe borradores en zona segura. | Sí, con aprobación |
| `execute` | Aplica cambios reales. | No por defecto |
| `deploy` | Despliegue externo. | No |

## 4. Políticas por dominio

| Dominio | Política |
|---|---|
| Filesystem | Solo rutas del workspace; prohibido borrar/sobrescribir sin aprobación. |
| Git | MVP+ read-only; commit/tag/push bloqueados hasta política posterior. |
| Patches | Parse y dry-run permitidos; apply bloqueado sin aprobación. |
| Repos | Lectura controlada; secret scan antes de resumen o envío a modelo. |
| Modelos locales | Permitidos si no exponen datos fuera del equipo. |
| APIs externas | Permitidas solo con API key opcional, CostGuard, redacción y consentimiento. |
| Persistencia | SQLite/JSONL/Markdown con redacción y retención. |
| RAG/memoria | Solo fuentes permitidas; grounding y citas obligatorias. |
| MCP/API futuros | Deshabilitados por defecto; registro explícito y policy gate. |
| Agentes | No aprueban sus propias acciones críticas. |

## 5. Matriz de política

| Acción | MVP | MVP+ | Post-MVP | Requiere aprobación |
|---|---:|---:|---:|---:|
| Leer documentos pre-code | Sí | Sí | Sí | No |
| Validar documentos | Sí | Sí | Sí | No |
| Generar reporte | Sí | Sí | Sí | No si ruta segura |
| Generar borrador documental | Sí | Sí | Sí | Sí si escribe |
| Leer Git status/diff | No | Sí | Sí | No |
| Analizar repo | No | Sí | Sí | Depende |
| Revisar código | No | Sí | Sí | No si solo reporta |
| Proponer patch | No | Sí | Sí | No si no aplica |
| Aplicar patch | No | Restringido | Sí | Sí |
| Ejecutar pruebas | No | Sí | Sí | Depende del comando |
| Crear commit | No | Restringido | Sí | Sí |
| Llamar API externa LLM | Opcional controlado | Sí | Sí | Sí si envía código/datos |
| Desplegar | No | No | Sí | Sí |

## 6. CostGuard

Toda operación con costo potencial debe declarar:

- proveedor;
- modelo;
- límite de tokens/requests;
- presupuesto de ejecución;
- modo de estimación;
- confirmación humana;
- evento `devpilot.cost.event`;
- fallback local/mock.

## 7. SecretGuard

Toda operación debe:

- detectar patrones de secretos;
- redactar outputs;
- evitar imprimir tokens;
- bloquear envío de secretos a modelos;
- generar findings si detecta `.env`, API keys o credenciales;
- registrar evento seguro sin valor del secreto.

## 8. Criterios PASS

La política queda aprobada si:

- cubre filesystem, Git, tools, agents, modelos, costos, secretos y persistencia;
- define modos de ejecución;
- define bloqueos críticos;
- separa recomendación de ejecución;
- exige trazabilidad;
- exige aprobación humana para acciones críticas.

## 9. Criterios BLOCK

Bloquear avance si:

- un agente puede aplicar cambios sin policy;
- un tool puede ejecutar comandos arbitrarios;
- APIs externas pueden usarse sin CostGuard;
- secretos pueden salir en logs/reportes;
- no existe registro de aprobación;
- no hay trazas para acciones relevantes.


## Actualización FUNC-SPRINT-33 — Guards de prompt/tool injection

La evaluación de `PolicyEngine` incorpora tres controles sobre payloads textuales:

```text
SecretGuard -> PromptInjectionGuard -> ToolInjectionGuard
```

`SecretGuard` bloquea y redacta secretos sintéticos o comunes. `PromptInjectionGuard` detecta intentos de ignorar instrucciones, saltar políticas o exfiltrar secretos. `ToolInjectionGuard` detecta intentos de forzar herramientas, saltar approvals o inyectar selectores de tool. Esta integración es `implemented-initial`, local-first y sin LLM judge.

Criterio MIASI: ninguna salida de policy/report/event debe conservar payloads peligrosos crudos cuando estos guards detectan riesgo.


## Política — MODEL_LOCAL_PROVIDER_CONTROLLED

`MODEL_LOCAL_PROVIDER_CONTROLLED` define que los proveedores locales declarados en Fase D deben pasar por `ModelAdapterRouter`, `ProviderRegistry`, `PolicyEngine`, `SecretGuard` y `CostGuard`. En `FUNC-SPRINT-45` el efecto operativo es conservador: se permiten contratos y metadata, pero la ejecución local real queda bloqueada hasta adapters posteriores.


## FUNC-SPRINT-46 — OllamaAdapter local opcional

DevPilot declara `model.health.local` como herramienta implementada inicial para health checks localhost-only y actualiza `model.call.local` a `implemented-initial` para llamadas Ollama controladas. Las llamadas siguen bloqueadas si el provider local está deshabilitado, si el endpoint no es localhost, si SecretGuard detecta secretos o si PolicyEngine/CostGuard bloquean la solicitud.

La implementación es preliminar: cubre Ollama con timeouts y fake-server tests; habilita LM Studio local OpenAI-compatible de forma inicial; no habilita APIs externas, streaming, budget ledger persistente ni AgentRuntime model-aware.


## FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible

DevPilot mantiene `model.health.local` como herramienta implementada inicial para health checks localhost-only y extiende `model.call.local` para cubrir LM Studio local OpenAI-compatible. Las llamadas siguen bloqueadas si el provider local está deshabilitado, si la base URL no es localhost, si SecretGuard detecta secretos o si PolicyEngine/CostGuard bloquean la solicitud.

La implementación es preliminar: cubre `/v1/models`, `/v1/chat/completions` y `/v1/embeddings` con timeouts y fake-server tests; no habilita OpenAI externo, streaming, budget ledger persistente ni AgentRuntime model-aware.


## Policy Card FUNC-SPRINT-48 — Model governance

Sprint 48 incorpora herramientas de gobierno de modelos: `model.health.local`, `model.capabilities.read` y `model.budget.status`. Todas operan local-first, no contactan APIs externas, no almacenan prompts ni secretos crudos y quedan gobernadas por `ProviderRegistry`, `ModelAdapterRouter`, `SecretGuard`, `CostGuard`, `LocalStore` y políticas MIASI.

Criterios PASS: reportes JSON reproducibles, proveedores externos bloqueados, budget ledger sin payloads crudos y fallback a `mock` explícito/configurado. Criterios BLOCK: gasto externo por defecto, endpoint remoto, metadata con secretos o provider unavailable con traceback.

## FUNC-SPRINT-49 — Políticas de prompts seguros

Sprint 49 agrega reglas MIASI para prompts:

- `PROMPT_REGISTRY_READ_ALLOW`: permite listar/mostrar prompts versionados en modo read-only y redacted.
- `PROMPT_CONTRACT_VALIDATE_ALLOW`: permite validar prompt schema, placeholders y checks básicos de seguridad.
- `PROMPT_RENDER_CONTROLLED`: permite renderizar prompts versionados solo con inputs declarados y sin almacenamiento crudo.

Estas reglas complementan `SECRETS_RAW_DENY`. No autorizan prompts dinámicos no versionados, exposición de secretos ni almacenamiento de prompts/completions crudos en runtime.


## FUNC-SPRINT-50 — Política de evaluación local de modelos

Sprint 50 agrega `MODEL_EVAL_RUN_ALLOW`, una política local-first para ejecutar suites de evaluación de modelos sin APIs externas. El gate combina `ModelEvalRunner`, `PromptRegistry`, `ModelAdapterRouter`, `BudgetLedger`, `NoExternalAPI` y `NoRawPrompts`. La política permite reportes y cost events redacted, pero bloquea gasto externo, prompts crudos o completions crudas.


## FUNC-SPRINT-51 — Política de AgentRuntime v2 model-aware

Sprint 51 agrega `AGENT_MODEL_CALL_GOVERNED_ALLOW`, una política para permitir llamadas model-aware desde agentes solo cuando pasen por `AgentRuntimeV2`, `PromptRegistry`, `ModelAdapterRouter`, `BudgetLedger`, `SecretGuard` y `CostGuard`. La política es allow/read-compute local para `mock` y providers locales controlados, pero no autoriza APIs externas, direct adapter calls, prompts crudos ni handoffs.


## Actualización FUNC-SPRINT-52 — Política REPO_ANALYSIS_AGENT_GOVERNED_ALLOW

La política `REPO_ANALYSIS_AGENT_GOVERNED_ALLOW` permite ejecutar `RepoAnalysisAgent` solo bajo `AgentRuntime v2`, `MIASI`, `RepoAnalyzer`, `DependencyGraph`, `RepoQualityGate`, `PromptRegistry` y `BudgetLedger`. El gate exige `NoMutations`, `NoExternalAPI` y `NoHandoffs`.

## Actualización FUNC-SPRINT-53 — Políticas de review agents

Sprint 53 agrega tres políticas operativas:

- `CODE_REVIEW_DRY_RUN_ALLOW`: permite revisión determinística read-only con `CodeReviewEngine`.
- `CODE_REVIEW_AGENT_GOVERNED_ALLOW`: permite `CodeReviewAgent` solo bajo `AgentRuntime v2`, MIASI, PromptRegistry y sin mutaciones.
- `PATCH_REVIEW_AGENT_GOVERNED_ALLOW`: permite `PatchReviewAgent` solo bajo dry-run, sin aplicar patches, sin APIs externas y sin handoffs.

Estas políticas no habilitan cambios destructivos. La aplicación de patches, rollback y refactor ejecutable siguen controlados por políticas y sprints anteriores/futuros.

## Actualización FUNC-SPRINT-54 — SafeRefactorAgent y TestPlannerAgent gobernados

Sprint 54 registra `safe.refactor` y `testplanner.agent` como agentes `implemented-initial`, monoagente y plan-only. Se agregan las tools `agent.safe_refactor.run`, `agent.test_planner.run` y `traceability.coverage`, junto con reglas de política para mantener refactor/test planning sin mutaciones, sin ejecución de tests por defecto, sin APIs externas y sin handoffs.

Criterios PASS: agentes registrados en MIASI, prompts versionados, evals offline, `mock` como ruta de prueba, `mutations_performed=false`, `tests_run_executed=false` y `refactor_executor_invoked=false`. Criterios BLOCK: ejecución real sin approval, comandos arbitrarios, prompts no versionados o pérdida de modo monoagente.


## Actualización FUNC-SPRINT-55 — Requirements/Architecture/Security agents y cierre Fase D

La Policy Matrix incorpora `REQUIREMENTS_AGENT_GOVERNED_ALLOW`, `ARCHITECTURE_AGENT_GOVERNED_ALLOW`, `SECURITY_AGENT_GOVERNED_ALLOW` y `SECURITY_REVIEW_READ_ONLY_ALLOW`.

Estado: `implemented-initial`; las capacidades son preliminares y deberán evolucionar con trazas AgentOps v2, métricas y reportes persistidos por agente.

## Actualización FUNC-SPRINT-85 — Fase H agentic/enterprise

`FUNC-SPRINT-85` sincroniza esta tarjeta MIASI con `ADR-0016 — Arquitectura avanzada agentic/enterprise` y `advanced_agentic_threat_model.md`.

Estados aplicables a Fase H:

| Estado | Uso permitido |
|---|---|
| `implemented` | Capacidad funcional y cubierta por pruebas. |
| `implemented-initial` | Primera versión operacional con límites explícitos. |
| `planned` | Diseñada, no operativa. |
| `experimental` | Solo con controles, flags y ADR futura cuando aplique. |
| `disabled` | Bloqueada por política. |
| `future` | Fuera del alcance actual. |

Reglas obligatorias:

- Multiagente requiere handoffs explícitos, trazas, policy y evals.
- RAG requiere fuentes, citas o metadatos de evidencia.
- MCP/conectores requieren registry, schema, policy y deny-by-default.
- Plugins requieren manifest, permisos, policy binding y loader no arbitrario.
- Multiworkspace requiere aislamiento de estado, reportes y secretos.
- RBAC debe influir en decisiones, no ser decorativo.
- Remote runners quedan `experimental/future` y disabled-by-default.

Criterio BLOCK: ninguna capacidad avanzada puede saltarse `PolicyEngine`, MIASI, Approval cuando aplique, trazas, evals y ReportEngine.

## Actualización FUNC-SPRINT-90 — Política multiagente

La política multiagente queda implementada inicialmente como deny/allow condicionado: el coordinador puede correr workflows allowlisted en `--dry-run`, pero debe bloquear ejecución abierta, agentes no implementados, handoffs implícitos, acciones destructivas, shell, red externa y API externa. Cada transferencia entre agentes requiere `PolicyEngine` y traza local.

PASS: `MULTIAGENT_COORDINATOR_DRY_RUN_ALLOW` + `MULTIAGENT_HANDOFF_TRACE_REQUIRED`. BLOCK: `MULTIAGENT_EXECUTE_DENY` ante cualquier ejecución no dry-run o acción crítica.

