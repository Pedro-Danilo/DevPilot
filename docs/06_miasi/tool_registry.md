---
title: "Tool Registry — DevPilot Local"
doc_id: "DEVPL-MIASI-TOOL-REGISTRY"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIASI"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
baseline_role: "precode_approved_baseline"
---

# Tool Registry — DevPilot Local

| Tool ID | Nombre | Fase | Side effect | Riesgo | Estado |
|---|---|---|---|---:|---|
| `artifact.read` | read_artifact | MVP | lectura | Bajo | Planned |
| `artifact.frontmatter.validate` | validate_frontmatter | MVP | ninguno | Bajo | Planned |
| `artifact.structure.validate` | validate_artifact_structure | MVP | ninguno | Bajo | Planned |
| `checklist.precode.run` | run_precode_checklist | MVP | ninguno | Bajo | Planned |
| `miasi.required` | miasi_required | MVP | ninguno | Bajo | Existing/minimal |
| `report.write` | write_report | MVP | escritura controlada | Medio | Planned |
| `trace.append` | append_trace_event | MVP | escritura controlada | Medio | Planned |
| `document.draft.generate` | generate_draft_document | MVP | escritura opcional | Medio | Planned |
| `documentation.audit` | audit_documentation | MVP | reporte | Medio | Planned |
| `git.status` | git_status | MVP+ | lectura | Medio | Implemented |
| `git.diff` | git_diff | MVP+ | lectura | Medio | Implemented |
| `git.branches` | git_branches_read_only | MVP+ | lectura | Medio | Implemented |
| `git.tags` | git_tags_read_only | MVP+ | lectura | Medio | Implemented |
| `git.log` | git_log_read_only | MVP+ | lectura | Medio | Implemented |
| `git.diff_report` | git_diff_report_read_only | MVP+ | reporte | Medio | Implemented |
| `repo.inventory` | repo_inventory | MVP+ | lectura | Medio | Planned |
| `repo.dependency_graph` | repo_dependency_graph_read_only | MVP+ | reporte | Medio | Implemented-initial |
| `repo.analyze` | repo_analyze_read_only | MVP+ | reporte | Medio | Implemented-initial |
| `repo.architecture_drift` | repo_architecture_drift_read_only | MVP+ | reporte | Medio | Implemented-initial |
| `repo.quality_gate` | repo_quality_gate_dry_run | MVP+ | reporte dry-run | Alto | Implemented-initial |
| `patch.parse` | parse_patch | MVP+ | ninguno | Medio | Planned |
| `patch.dry_run` | patch_dry_run | MVP+ | simulación | Alto | Planned |
| `patch.check` | patch_preflight_check | MVP+ | simulación dry-run | Alto | Implemented-initial |
| `code.review` | code_review | MVP+ | reporte | Alto | Planned |
| `tests.run` | run_tests_controlled | MVP+ | ejecución controlada | Alto | Planned |
| `model.call.mock` | call_mock_model | MVP | ninguno | Bajo | Planned |
| `model.call.local` | call_local_model | MVP+ | cómputo local | Medio | Planned |
| `model.call.external` | call_external_model | MVP+ | red/costo | Alto | Disabled by default |

## Política

Toda herramienta nueva debe agregarse a este registro antes de implementarse.

## Estado operacional de `tests.run` — FUNC-SPRINT-32

`tests.run` pasa de `planned` a `implemented-initial` como herramienta MIASI de ejecución controlada. Su implementación reside en `devpilot_core.testing.TestsRunTool` y usa `SafeSubprocessRunner` como frontera de ejecución.

Restricciones:

- requiere aprobación humana para `tests.run/execute/<profile>`;
- solo ejecuta perfiles definidos en `.devpilot/testing/test_profiles.json`;
- no acepta comandos arbitrarios;
- no usa `shell=True`;
- conserva `PathGuard`, `SecretGuard`, `CostGuard` y `ApprovalPolicyChecker` en el flujo.

Perfiles iniciales: `smoke`, `unit`, `all`.


## Estado operacional GitAdapter v2 — FUNC-SPRINT-35

`git.branches`, `git.tags`, `git.log` y `git.diff_report` quedan declaradas como tools read-only de Fase C. No requieren approval porque no modifican archivos, index ni historial, pero siguen sujetas a `GIT_READ_ALLOW`, `PolicyEngine`, allowlist interna y ausencia de `shell=True`.

## Estado operacional DependencyGraph — FUNC-SPRINT-36

`repo.dependency_graph` queda declarada como tool read-only de Fase C. No requiere approval porque no modifica archivos ni ejecuta código analizado. Su implementación usa AST y debe permanecer local-first, sin red, sin APIs externas y sin modelos.

## Estado operacional RepoAnalyzer v2 — FUNC-SPRINT-37

`repo.analyze` queda declarada como tool read-only de Fase C. No requiere approval porque no modifica archivos ni ejecuta código analizado. Su implementación consolida inventario, DependencyGraph y GitAdapter para producir señales heurísticas de salud de repositorio. Debe permanecer local-first, sin red, sin APIs externas, sin modelos y sin emisión de secretos crudos.


## Estado operacional Architecture/code drift — FUNC-SPRINT-38

`repo.architecture_drift` queda declarada como tool read-only de Fase C. No requiere approval porque no modifica archivos ni ejecuta código analizado. Su implementación compara arquitectura documentada contra módulos reales mediante heurísticas locales, DependencyGraph y RepoAnalyzer. Debe permanecer local-first, sin red, sin APIs externas, sin modelos y sin cambios automáticos en documentación o código.


## Estado operacional Repo Quality Gate — FUNC-SPRINT-39

`repo.quality_gate` queda declarada como tool MIASI de Fase C en estado `implemented-initial`. No requiere approval porque no modifica archivos ni aplica patches; aun así se clasifica como riesgo alto por su rol de gate antes de cambios de repositorio. Su implementación es dry-run, local-first y basada en `ReviewRulePack`, `RepoAnalyzer`, `CodeReviewEngine`, `PatchReviewEngine` opcional y `PolicyEngine`.

Restricciones: sin Git write, sin patch apply, sin red, sin APIs externas, sin modelos y sin secretos crudos en reportes. Los warnings son asesoría por defecto; findings `FAIL` y `BLOCK` de motores integrados se propagan al resultado del gate.


## Estado operacional Patch preflight — FUNC-SPRINT-40

`patch.check` queda declarada como tool MIASI de Fase C en estado `implemented-initial`. No requiere approval porque no aplica patches ni modifica el workspace productivo; aun así se clasifica como riesgo alto por ejecutar una verificación Git local controlada.

Restricciones: solo `git apply --check` mediante `SafeSubprocessRunner` y allowlist explícita, sin `shell=True`, sin Git write, sin patch apply, sin sandbox, sin rollback, sin red, sin APIs externas, sin modelos y sin secretos crudos en reportes. `BLOCK` representa riesgo/política/seguridad; `FAIL` representa no aplicabilidad del patch.


## Estado operacional PatchSandbox

`patch.sandbox` queda declarado como tool MIASI de riesgo alto con side effect `controlled_write`. La tool ejecuta `PatchPreflightEngine`, aplica el patch solo dentro de `outputs/sandbox`, genera un `ChangeSet` con hashes antes/después y mantiene bloqueada cualquier aplicación sobre el workspace productivo.

Criterios PASS: sandbox bajo `outputs/sandbox`, ChangeSet sin contenido crudo, preflight obligatorio, no Git write y reportes auditables.

Criterios BLOCK: mutación productiva, omisión de preflight, secretos crudos en evidencia, pruebas sin aprobación `tests.run`, rollback ejecutable no autorizado o escritura fuera de rutas runtime controladas.

Riesgos: capacidad `implemented-initial`; el rollback ejecutable pertenece a `FUNC-SPRINT-42` y la aplicación real de patches al workspace productivo permanece fuera de alcance.


## Estado operacional RollbackManager — FUNC-SPRINT-42

Se agregan tools `rollback.plan`, `rollback.list`, `rollback.show` y `rollback.execute`. La capacidad es `implemented-initial`: permite crear y consultar rollback points locales, pero no habilita restauración automática. `rollback.execute` existe como frontera CLI gated y bloqueada por diseño hasta que futuros sprints definan restore semantics, pruebas post-rollback y aprobación humana completa.


## Estado operacional RefactorExecutor — FUNC-SPRINT-43

`refactor.sandbox` queda declarado como tool `implemented-initial`, de riesgo alto y approval obligatorio. Ejecuta únicamente transformaciones mecánicas determinísticas en sandbox, produce `ChangeSet`, invoca `RollbackManager` para rollback plan y permite pruebas fijas en sandbox con approval separado de `tests.run`.

La herramienta no habilita escritura productiva, Git write, refactors semánticos, ejecución arbitraria ni APIs externas.


## Estado operacional RepoEngineeringGate

- Tool ID: `repo.engineering_gate`.
- Estado: `implemented-initial`.
- Riesgo: `high`.
- Side effect: `report`.
- Approval: no requerido porque es read-only/report-only.
- Policy rule: `ENGINEERING_GATE_READ_ONLY_ALLOW`.
- Comando: `python -m devpilot_core repo engineering-gate --profile full --json --write-report`.

La herramienta cierra Fase C de forma reproducible, pero no habilita Git write, patch apply productivo, refactor productivo, deploy, LLMs ni APIs externas.


## Estado operacional Model Providers — FUNC-SPRINT-45

El Tool Registry declara `model.call.local` como capacidad planificada/controlada por `MODEL_LOCAL_PROVIDER_CONTROLLED`. Esta declaración prepara `FUNC-SPRINT-46` y `FUNC-SPRINT-47` sin habilitar todavía adapters reales ni llamadas de red.


## FUNC-SPRINT-46 — OllamaAdapter local opcional

DevPilot declara `model.health.local` como herramienta implementada inicial para health checks localhost-only y actualiza `model.call.local` a `implemented-initial` para llamadas Ollama controladas. Las llamadas siguen bloqueadas si el provider local está deshabilitado, si el endpoint no es localhost, si SecretGuard detecta secretos o si PolicyEngine/CostGuard bloquean la solicitud.

La implementación es preliminar: cubre Ollama con timeouts y fake-server tests; habilita LM Studio local OpenAI-compatible de forma inicial; no habilita APIs externas, streaming, budget ledger persistente ni AgentRuntime model-aware.


## FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible

DevPilot mantiene `model.health.local` como herramienta implementada inicial para health checks localhost-only y extiende `model.call.local` para cubrir LM Studio local OpenAI-compatible. Las llamadas siguen bloqueadas si el provider local está deshabilitado, si la base URL no es localhost, si SecretGuard detecta secretos o si PolicyEngine/CostGuard bloquean la solicitud.

La implementación es preliminar: cubre `/v1/models`, `/v1/chat/completions` y `/v1/embeddings` con timeouts y fake-server tests; no habilita OpenAI externo, streaming, budget ledger persistente ni AgentRuntime model-aware.


## Tool Registry FUNC-SPRINT-48 — Model governance

Sprint 48 incorpora herramientas de gobierno de modelos: `model.health.local`, `model.capabilities.read` y `model.budget.status`. Todas operan local-first, no contactan APIs externas, no almacenan prompts ni secretos crudos y quedan gobernadas por `ProviderRegistry`, `ModelAdapterRouter`, `SecretGuard`, `CostGuard`, `LocalStore` y políticas MIASI.

Criterios PASS: reportes JSON reproducibles, proveedores externos bloqueados, budget ledger sin payloads crudos y fallback a `mock` explícito/configurado. Criterios BLOCK: gasto externo por defecto, endpoint remoto, metadata con secretos o provider unavailable con traceback.

## FUNC-SPRINT-49 — Prompt Registry executable entries

El Tool Registry ejecutable incorpora entradas para `prompt.registry.read`, `prompt.contract.validate` y `prompt.render.controlled`. Todas quedan detrás de reglas MIASI específicas, `SecretGuard` y `PromptSafetyChecker`, y son necesarias para que futuros agentes no usen prompts embebidos sin trazabilidad.


## FUNC-SPRINT-50 — Model evaluation matrix executable entry

El Tool Registry ejecutable incorpora `model.eval.run` en estado `implemented-initial`, protegido por `MODEL_EVAL_RUN_ALLOW`, `MODEL_LOCAL_PROVIDER_CONTROLLED` y `SECRETS_RAW_DENY`. La entrada es necesaria para comparar proveedores locales/mock por tarea antes de activar AgentRuntime v2 model-aware.


## FUNC-SPRINT-51 — AgentRuntime v2 executable entry

El Tool Registry ejecutable incorpora `agent.model.generate` en estado `implemented-initial`, protegido por `AGENT_MODEL_CALL_GOVERNED_ALLOW`, `MODEL_LOCAL_PROVIDER_CONTROLLED`, `PROMPT_RENDER_CONTROLLED` y `SECRETS_RAW_DENY`. La entrada permite a agentes monoagente usar generación gobernada a través de `ModelAdapterRouter` y conserva `mock` como baseline hermético.


## Actualización FUNC-SPRINT-52 — Tool Registry

El Tool Registry incorpora `agent.repo_analysis.run` para la ejecución monoagente de `RepoAnalysisAgent`. La tool queda restringida a análisis read-only y se apoya en `repo.analyze`, `repo.dependency_graph`, `git.status`, `repo.quality_gate`, `policy.check`, `report.write`, `trace.append` y `agent.model.generate` cuando se activa provider mock/local.

## Actualización FUNC-SPRINT-53 — Tool Registry

El Tool Registry incorpora `agent.code_review.run` y `agent.patch_review.run` como capacidades `implemented-initial`. Estas tools representan orquestación agentic gobernada, no motores nuevos ni ejecución destructiva.

Las tools se vinculan con:

- `CODE_REVIEW_AGENT_GOVERNED_ALLOW`;
- `PATCH_REVIEW_AGENT_GOVERNED_ALLOW`;
- `CODE_REVIEW_DRY_RUN_ALLOW`;
- `PATCH_DRY_RUN_ALLOW`;
- `PATCH_CHECK_DRY_RUN_ALLOW`;
- `AGENT_MODEL_CALL_GOVERNED_ALLOW`.

## Actualización FUNC-SPRINT-54 — SafeRefactorAgent y TestPlannerAgent gobernados

Sprint 54 registra `safe.refactor` y `testplanner.agent` como agentes `implemented-initial`, monoagente y plan-only. Se agregan las tools `agent.safe_refactor.run`, `agent.test_planner.run` y `traceability.coverage`, junto con reglas de política para mantener refactor/test planning sin mutaciones, sin ejecución de tests por defecto, sin APIs externas y sin handoffs.

Criterios PASS: agentes registrados en MIASI, prompts versionados, evals offline, `mock` como ruta de prueba, `mutations_performed=false`, `tests_run_executed=false` y `refactor_executor_invoked=false`. Criterios BLOCK: ejecución real sin approval, comandos arbitrarios, prompts no versionados o pérdida de modo monoagente.


## Actualización FUNC-SPRINT-55 — Requirements/Architecture/Security agents y cierre Fase D

El Tool Registry declara las herramientas de agentes SDLC y capacidades auxiliares de revisión como `implemented-initial`, sin side effects destructivos ni aprobación requerida para lectura/reporte.

Estado: `implemented-initial`; las capacidades son preliminares y deberán evolucionar con trazas AgentOps v2, métricas y reportes persistidos por agente.
