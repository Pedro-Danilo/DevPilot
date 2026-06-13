---
title: "DevPilot Local — Backlog ejecutable Fase E: AgentOps y observabilidad"
doc_id: "DEVPL-FUNC-BACKLOG-FASE-E-001"
status: "approved"
version: "0.4.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-E-AGENTOPS-OBSERVABILIDAD"
updated: "2026-06-13"
source_repo: "repo_DevPilot_Local_69.zip"
source_report: "Informe de avance DevPilot - sprint 0 - 18.docx"
source_backlog_model: "docs/functional_backlog_after_precode.md"
baseline_dependency: "Fases A, B, C y D cerradas; Fase D validada por FUNC-SPRINT-55"
first_sprint: "FUNC-SPRINT-56"
last_planned_sprint: "FUNC-SPRINT-63"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval_scope: "phase_e_executable_backlog_review"
approved_on: "2026-06-13"
approval: "approved_after_phase_d_closure_review"
first_open_sprint: "FUNC-SPRINT-59"
last_completed_sprint: "FUNC-SPRINT-58"
next_sprint: "FUNC-SPRINT-59"
phase_e_status: "in_progress"
---

# DevPilot Local — Backlog ejecutable Fase E: AgentOps y observabilidad

## Estado de aprobación funcional

Este documento queda promovido a estado `approved` después del cierre validado de `FUNC-SPRINT-55 — Requirements/Architecture/Security agents y cierre Fase D`. Su propósito es convertir la **Fase E — AgentOps y observabilidad** en un backlog de implementación ejecutable, siguiendo el modelo operativo usado en `docs/functional_backlog_after_precode.md`.

La Fase E corresponde a la **Ola 8 — Observabilidad avanzada y AgentOps**. Parte del estado real de `repo_DevPilot_Local_67.zip`, donde DevPilot ya cuenta con Fases A-D cerradas, `EventLogger` JSONL, `ReportEngine`, `LocalStore` SQLite, MIASI executable registry, Approval Workflow, SafeSubprocessRunner, PatchSandbox, RollbackManager, RefactorExecutor sandbox, ProviderRegistry, ModelAdapterRouter, Ollama/LM Studio opcionales, PromptRegistry, BudgetLedger, ModelEvalRunner, AgentRuntime v2 y agentes SDLC monoagente gobernados. Sin embargo, el estado actual todavía no incluye trazas jerárquicas v2, spans persistidos, métricas agentic/model completas, reportes de trace, visor de trazas, OpenTelemetry opt-in ni AgentOps Quality Gate.

## Estado aprobado para implementación

La revisión de cierre de `FUNC-SPRINT-55` confirma que este backlog es una continuación apropiada de DevPilot porque Fase D deja una superficie agentic gobernada que necesita observabilidad industrial antes de evolucionar hacia UI, multiagente, RAG, MCP o automatización más autónoma.

La aprobación de Fase E no autoriza telemetría remota, exporters externos activos, multiagente funcional, handoffs, RAG, MCP ni ejecución remota. La implementación debe comenzar por `FUNC-SPRINT-56 — ADR de observabilidad v2 y modelo AgentOps`, manteniendo JSONL/SQLite locales como fuente operacional, redacción de secretos obligatoria, `mock` como ruta hermética y OpenTelemetry únicamente como diseño opt-in/dry-run hasta que exista aprobación específica.


## 1. Propósito

La Fase E busca transformar la observabilidad local inicial de DevPilot en una capa AgentOps operativa. En términos prácticos, la fase debe permitir reconstruir una ejecución completa: qué comando se ejecutó, qué agente participó, qué tool se intentó usar, qué política permitió o bloqueó la acción, qué modelo se invocó, qué costo estimado tuvo, qué findings surgieron, qué aprobación intervino y qué reportes/evidencias quedaron.

En lenguaje operativo, esta fase avanza desde:

```text
EventLogger JSONL + reports + SQLite inicial
```

hacia:

```text
TraceEngine v2 + spans + métricas + trace reports + AgentOps status + exporter OTel opcional + calidad operacional de agentes
```

## 2. Regla central de Fase E

La observabilidad no debe ser decorativa ni posterior al hecho. Toda capacidad agentic, de modelo, tool calling, aprobación, sandbox, patch/refactor o UI futura debe producir evidencia consultable.

Reglas obligatorias:

1. Todo comando nuevo debe emitir eventos mínimos sin exponer secretos.
2. Todo agente debe tener `agent_run_id` correlacionable.
3. Toda tool call debe tener `tool_call_id` y relación con un trace.
4. Toda model call debe registrar proveedor, modelo, modo, duración y costo estimado si aplica.
5. Las trazas deben redactorizar contenido sensible.
6. OpenTelemetry debe ser opcional, local/dry-run por defecto y no enviar datos externos sin aprobación.
7. Los reportes de observabilidad deben ser reproducibles y no depender de servicios cloud.
8. La fase no habilita multiagentes por sí misma; prepara su observabilidad.

## 3. Alcance de Fase E

Incluye:

- diseño del modelo de trazas v2;
- `TraceContext`, `SpanRecord`, `MetricRecord` y correlación;
- evolución controlada del EventLogger;
- persistencia ampliada de trazas/métricas en SQLite;
- instrumentación de comandos, agentes, tools, modelos, approvals y sandbox;
- comandos `trace report`, `trace inspect`, `metrics summary` y `agentops status`;
- exporter OpenTelemetry en modo dry-run/local opt-in;
- AgentOps Quality Gate.

No incluye:

- dashboard visual completo;
- UI Web/Desktop productiva;
- trazas distribuidas remotas obligatorias;
- envío de telemetría a servicios externos por defecto;
- multiagente funcional;
- RAG;
- MCP;
- ejecución remota.

## 4. Niveles de implementación de Fase E

| Nivel | Nombre | Objetivo | Estado esperado al cierre |
|---|---|---|---|
| FE-L0 | Modelo de observabilidad v2 | Definir trazas, spans y métricas | Contratos y ADR |
| FE-L1 | Trace context | Correlacionar comandos/agentes/tools/modelos | `TraceContext` operativo |
| FE-L2 | Trace store | Persistir y consultar trazas | SQLite + JSONL compatibles |
| FE-L3 | Instrumentación agentic | Instrumentar agentes/tools/model calls | Spans por operación |
| FE-L4 | Reportes operativos | Consultar trazas/métricas | `trace report`, `metrics summary` |
| FE-L5 | Export opcional | Preparar OpenTelemetry sin exfiltración | Export dry-run/local |
| FE-L6 | AgentOps gate | Evaluar salud operacional | AgentOps Quality Gate |

## 5. Definition of Done transversal

Un sprint de Fase E solo puede cerrarse si cumple:

- todo comando nuevo devuelve `CommandResult`;
- todo comando nuevo soporta `--json`;
- todo comando con evidencia soporta `--write-report` cuando aplique;
- ninguna traza contiene secretos sin redacción;
- todo evento/span tiene timestamps, ids y relación con root trace cuando aplique;
- se actualizan README y runbook si hay comandos nuevos;
- se actualizan MIASI Observability Card y Tool/Policy Registry si cambia instrumentación agentic;
- se agregan pruebas unitarias y smoke tests;
- `pytest -q` pasa;
- se documenta cuando una capacidad es preliminar y no industrial completa.

## 6. Convenciones de IDs

| Tipo | Prefijo | Ejemplo |
|---|---|---|
| Sprint funcional | `FUNC-SPRINT-XX` | `FUNC-SPRINT-56` |
| Historia | `US-FUNC-XX-YYY` | `US-FUNC-56-001` |
| Tarea | `FUNC-XX-YYY` | `FUNC-56-003` |
| Prueba | `TEST-FUNC-XX-YYY` | `TEST-FUNC-56-002` |
| Gate | `GATE-FUNC-XX` | `GATE-FUNC-56` |
| Riesgo | `RISK-FUNC-XX-YYY` | `RISK-FUNC-56-001` |
| Trace | `TRACE-*` | `TRACE-COMMAND-RUN` |
| Span | `SPAN-*` | `SPAN-AGENT-TOOL-CALL` |
| Métrica | `METRIC-*` | `METRIC-MODEL-COST` |

## 7. Roadmap funcional de Fase E

| Ola | Sprints | Resultado esperado |
|---|---|---|
| Ola 8 | FUNC-SPRINT-56 a 63 | TraceEngine v2, AgentOps, métricas, reportes, exporter OTel opcional y quality gate operacional |

## 8. Referencias técnicas externas de apoyo

- OpenTelemetry define un marco abierto para capturar, procesar y exportar trazas, métricas y logs; DevPilot debe usarlo como referencia conceptual, no como dependencia obligatoria inicial.
- Las semantic conventions GenAI de OpenTelemetry incluyen nombres de atributos, métricas, spans y eventos para operaciones generativas; DevPilot puede mapear sus agent/model/tool events hacia ese modelo en una etapa opt-in.
- La observabilidad de agentes debe registrar tool calls, guardrails, model calls, approvals, errores y costos estimados sin exponer datos sensibles.



## FUNC-SPRINT-56 — ADR de observabilidad v2 y modelo AgentOps

## Objetivo

Definir la arquitectura de observabilidad v2, los límites de AgentOps, los contratos mínimos de trace/span/metric y la relación con MIASI antes de modificar el runtime.

## Entradas

- `repo_DevPilot_Local_22.zip` como baseline vigente.
- Backlogs Fase A–D aprobados o explícitamente aceptados como prerequisito lógico.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-56-001 | Como arquitecto, quiero una ADR de observabilidad v2 para evitar introducir telemetría sin control. | Existe ADR aprobable con alcance, decisiones, alternativas y consecuencias. |
| US-FUNC-56-002 | Como operador, quiero saber qué será observable en comandos, agentes, tools y modelos. | Existe matriz de señales por dominio. |
| US-FUNC-56-003 | Como revisor de seguridad, quiero confirmar que la telemetría no exfiltra datos. | La ADR declara redacción, local-first y opt-in para exporters. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-56-001 | Crear ADR de observabilidad v2 y AgentOps | `docs/02_architecture/adrs/ADR-XXXX-observability-v2-agentops.md` | ADR incluye local-first, JSONL, SQLite, OTel opcional y no exfiltración. |
| FUNC-56-002 | Actualizar Observability Plan | `docs/05_operations/observability_plan.md` | Señales v2 documentadas. |
| FUNC-56-003 | Actualizar MIASI Observability Card | `docs/06_miasi/observability_card.md` | Agentes/tools/modelos quedan cubiertos. |
| FUNC-56-004 | Crear catálogo preliminar de señales | `docs/05_operations/observability_signal_catalog.md` | Lista eventos, spans y métricas esperadas. |
| FUNC-56-005 | Crear manifiesto Sprint 56 | `docs/functional_sprint_56_manifest.json` | Manifiesto válido y sincronizado. |

## Archivos previstos

```text
docs/02_architecture/adrs/ADR-XXXX-observability-v2-agentops.md
docs/05_operations/observability_plan.md
docs/05_operations/observability_signal_catalog.md
docs/06_miasi/observability_card.md
docs/audits/func_sprint_56_observability_v2_audit.md
docs/functional_sprint_56_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core validate-artifact docs/05_operations/observability_plan.md --json
python -m devpilot_core miasi validate --json
python -m pytest -q
```

## Criterios PASS

- Existe decisión arquitectónica explícita antes de implementar OTel/exporters.
- La documentación separa trace, span, metric, event y report.
- No se permite telemetría remota por defecto.

## Criterios BLOCK

- No cerrar si la ADR habilita envío externo sin aprobación.
- No cerrar si no se actualiza MIASI Observability Card.
- No cerrar si se confunde AgentOps con multiagente funcional.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-56-001 | Diseño demasiado amplio | Limitar Fase E a observabilidad/AgentOps, no a UI ni multiagente. |
| RISK-FUNC-56-002 | Exfiltración accidental | Declarar exporters opt-in y redacción obligatoria. |
| RISK-FUNC-56-003 | Duplicación de señales | Definir catálogo canónico de eventos/spans/métricas. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-56-001 | Validar docs actualizados | `validate-artifact` pasa en artefactos modificados. |
| TEST-FUNC-56-002 | Validar MIASI | `miasi validate` sigue en PASS. |
| TEST-FUNC-56-003 | Regresión general | `pytest -q` pasa. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-56: ADR de observabilidad v2 y AgentOps. No agregues exporters ni dependencias. Actualiza Observability Plan y MIASI Observability Card con contratos de trace/span/metric/event y reglas de redacción.
```

## Estado de implementación Sprint 56

`FUNC-SPRINT-56 — ADR de observabilidad v2 y modelo AgentOps` queda implementado como `implemented-initial`. El sprint crea `ADR-0012`, actualiza el Observability Plan, actualiza la MIASI Observability Card, crea el catálogo preliminar de señales v2, crea auditoría de sprint y manifiesto funcional.

Alcance real aplicado:

- se define la arquitectura local-first de eventos, trazas, spans, métricas y reportes;
- se formaliza que JSONL y SQLite seguirán siendo fuentes locales de evidencia;
- se documentan contratos mínimos para `trace_id`, `run_id`, `agent_run_id`, `tool_call_id`, `model_call_id`, spans y métricas;
- se explicita que OpenTelemetry es solo compatibilidad futura opt-in/dry-run;
- se mantiene bloqueado todo envío remoto de telemetría;
- no se agregan dependencias externas;
- no se implementan todavía `TraceContext`, `TraceStore`, `MetricsCollector`, exporters ni AgentOps Gate.

Criterios de cierre: `validate-artifact` sobre ADR, Observability Plan, Signal Catalog, Observability Card y auditoría debe pasar; `miasi validate` debe seguir en PASS; el manifiesto Sprint 56 debe validar contra schema; `pytest -q` debe pasar sin red ni APIs externas.

Criterios BLOCK: telemetría remota por defecto, SDK externo obligatorio, payloads sensibles en señales, instrumentación runtime fuera de alcance o confusión de AgentOps con multiagente/handoffs/RAG/MCP.

Siguiente sprint operativo: `FUNC-SPRINT-57 — TraceContext y modelo de spans`.

## FUNC-SPRINT-57 — TraceContext y modelo de spans

## Objetivo

Crear los contratos Python para correlacionar ejecuciones: trace id, run id, span id, parent span id, duración, estado, severidad y vínculos con CommandResult/Finding.

## Entradas

- `repo_DevPilot_Local_22.zip` como baseline vigente.
- Backlogs Fase A–D aprobados o explícitamente aceptados como prerequisito lógico.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-57-001 | Como operador, quiero correlacionar un comando con sus suboperaciones. | Todo TraceContext tiene id estable y serializable. |
| US-FUNC-57-002 | Como desarrollador, quiero spans jerárquicos sin depender aún de OpenTelemetry. | Existen dataclasses internas para SpanRecord. |
| US-FUNC-57-003 | Como auditor, quiero que los spans no contengan secretos. | Los payloads pasan por redacción. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-57-001 | Crear módulo `observability/tracing.py` | `TraceContext`, `SpanRecord`, `SpanStatus` | Contratos serializables. |
| FUNC-57-002 | Crear utilidades de generación de ids | `trace_id`, `span_id`, `run_id` | IDs únicos y testeables. |
| FUNC-57-003 | Integrar redacción con SecretGuard | `sanitize_span_payload` | No expone secretos. |
| FUNC-57-004 | Agregar tests unitarios | `tests/test_trace_context.py` | Cubre serialización, jerarquía y redacción. |
| FUNC-57-005 | Actualizar docs/runbook | README y runbook | Describe trace model v2. |

## Archivos previstos

```text
src/devpilot_core/observability/tracing.py
tests/test_trace_context.py
docs/audits/func_sprint_57_trace_context_audit.md
docs/functional_sprint_57_manifest.json
```

## Comandos objetivo

```powershell
python -m pytest tests/test_trace_context.py -q
python -m pytest -q
```

## Criterios PASS

- TraceContext y SpanRecord son serializables.
- Los spans soportan parent-child.
- Los payloads sensibles se redactan.

## Criterios BLOCK

- No cerrar si SpanRecord guarda prompts/secrets crudos.
- No cerrar si rompe EventLogger actual.
- No cerrar si no hay pruebas de jerarquía.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-57-001 | Incompatibilidad con EventLogger v1 | Mantener adaptadores y compatibilidad. |
| RISK-FUNC-57-002 | Exceso de metadatos | Definir campos mínimos y payload redacted. |
| RISK-FUNC-57-003 | IDs no determinables en tests | Permitir inyección de clock/id generator para pruebas. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-57-001 | Span serializable | JSON válido. |
| TEST-FUNC-57-002 | Parent span | Relación parent-child verificable. |
| TEST-FUNC-57-003 | Redacción | Secret sintético no aparece en output. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-57: TraceContext y SpanRecord internos. Mantén compatibilidad con EventLogger actual y agrega pruebas de serialización, jerarquía y redacción.
```


## Estado de implementación Sprint 57

`FUNC-SPRINT-57 — TraceContext y modelo de spans` queda implementado en estado `implemented-initial`. La implementación crea contratos Python internos para `TraceContext`, `SpanRecord`, `SpanStatus`, generación de ids `trace_id`/`span_id`/`run_id`, cálculo de duración y redacción conservadora de payloads con `sanitize_span_payload`.

El cierre de Sprint 57 mantiene los límites de Fase E: no agrega OpenTelemetry SDK, no habilita exporters, no envía telemetría remota, no modifica `EventLogger` v1, no persiste spans todavía y no habilita multiagente, handoffs, RAG, MCP ni ejecución remota.

Siguiente sprint operativo: `FUNC-SPRINT-58 — TraceStore y EventLogger v2 compatible`.

## FUNC-SPRINT-58 — TraceStore y EventLogger v2 compatible

## Objetivo

Evolucionar la escritura de eventos hacia trazas consultables, manteniendo compatibilidad con JSONL actual y agregando persistencia de spans en SQLite.

## Entradas

- `repo_DevPilot_Local_22.zip` como baseline vigente.
- Backlogs Fase A–D aprobados o explícitamente aceptados como prerequisito lógico.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-58-001 | Como operador, quiero conservar eventos JSONL pero consultar trazas estructuradas. | TraceStore persiste spans y eventos. |
| US-FUNC-58-002 | Como desarrollador, quiero que EventLogger v1 siga funcionando. | Los tests existentes no se rompen. |
| US-FUNC-58-003 | Como auditor, quiero que cada evento se vincule a un trace cuando aplique. | Eventos nuevos incluyen trace_id/run_id. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-58-001 | Crear `TraceStore` | `src/devpilot_core/observability/trace_store.py` | Persiste y consulta spans. |
| FUNC-58-002 | Extender LocalStore con tablas de spans/métricas | `store/local_store.py` | Migración compatible. |
| FUNC-58-003 | Crear EventLogger v2 wrapper | `observability/events.py` | Acepta TraceContext opcional. |
| FUNC-58-004 | Agregar comando interno de smoke trace | CLI o helper tests | Permite verificar persistencia. |
| FUNC-58-005 | Actualizar pruebas | tests | No rompe tests existentes. |

## Archivos previstos

```text
src/devpilot_core/observability/trace_store.py
src/devpilot_core/observability/events.py
src/devpilot_core/store/local_store.py
tests/test_trace_store.py
docs/audits/func_sprint_58_trace_store_audit.md
docs/functional_sprint_58_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core state init --json
python -m devpilot_core state status --json
python -m pytest tests/test_trace_store.py -q
python -m pytest -q
```

## Criterios PASS

- JSONL actual sigue funcionando.
- SQLite puede persistir spans sin romper DB existente.
- Eventos nuevos pueden correlacionarse con trace_id.

## Criterios BLOCK

- No cerrar si se versiona `.devpilot/devpilot.db`.
- No cerrar si rompe `history list`.
- No cerrar si no hay migración segura.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-58-001 | Migración SQLite frágil | Agregar schema_version y migración idempotente. |
| RISK-FUNC-58-002 | Duplicidad JSONL/SQLite | Documentar roles: JSONL append-only, SQLite consultable. |
| RISK-FUNC-58-003 | Crecimiento de storage | Preparar retención futura, no obligatoria en sprint. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-58-001 | TraceStore persiste | Insert/read span PASS. |
| TEST-FUNC-58-002 | Compatibilidad EventLogger | tests previos PASS. |
| TEST-FUNC-58-003 | State status | No falla con schema nuevo. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-58: TraceStore y EventLogger v2 compatible. Mantén JSONL, agrega spans a SQLite con migración idempotente y pruebas de compatibilidad.
```

## Estado de implementación Sprint 58

`FUNC-SPRINT-58 — TraceStore y EventLogger v2 compatible` queda implementado en estado `implemented-initial`. La implementación crea `TraceStore`, extiende `LocalStore` con tablas `spans` y `metrics`, agrega columnas de correlación a eventos SQLite, mantiene compatibilidad con `EventLogger` JSONL y permite que eventos nuevos acepten `TraceContext` opcional.

La capacidad no entrega todavía CLI pública de trazas, agregación de métricas, exporter OpenTelemetry ni AgentOps Quality Gate. Es una primera versión de persistencia local de trazas que debe evolucionar en `FUNC-SPRINT-59` a `FUNC-SPRINT-63`.

Siguiente sprint operativo: `FUNC-SPRINT-59 — MetricsCollector para comandos, agentes, tools y modelos`.

## FUNC-SPRINT-59 — MetricsCollector para comandos, agentes, tools y modelos

## Objetivo

Crear un colector local de métricas para duración, conteos, severidad, costos estimados, tokens opcionales y estado de operaciones.

## Entradas

- `repo_DevPilot_Local_22.zip` como baseline vigente.
- Backlogs Fase A–D aprobados o explícitamente aceptados como prerequisito lógico.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-59-001 | Como operador, quiero saber cuántos comandos fallan o bloquean. | Metrics summary reporta conteos por estado. |
| US-FUNC-59-002 | Como supervisor de modelos, quiero estimaciones de costo/tokens cuando existan. | Model metrics acepta valores estimados sin API real. |
| US-FUNC-59-003 | Como arquitecto, quiero métricas locales sin depender de servicios externos. | MetricsCollector persiste localmente. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-59-001 | Crear `MetricRecord` y `MetricsCollector` | `observability/metrics.py` | Contratos serializables. |
| FUNC-59-002 | Extender LocalStore para métricas | DB local | Inserción/consulta. |
| FUNC-59-003 | Instrumentar comandos clave | CLI helpers | Duración y exit_code. |
| FUNC-59-004 | Instrumentar ModelAdapter mock | modeling/router.py | Registra provider/model/mode sin costo real. |
| FUNC-59-005 | Agregar pruebas | tests/test_metrics_collector.py | Cubre agregación. |

## Archivos previstos

```text
src/devpilot_core/observability/metrics.py
src/devpilot_core/store/local_store.py
tests/test_metrics_collector.py
docs/audits/func_sprint_59_metrics_collector_audit.md
docs/functional_sprint_59_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core model providers --json
python -m pytest tests/test_metrics_collector.py -q
python -m pytest -q
```

## Criterios PASS

- Métricas locales persisten sin red.
- No hay costos externos reales en mock.
- Duración y estado se registran sin romper comandos.

## Criterios BLOCK

- No cerrar si registra prompts crudos.
- No cerrar si introduce dependencia externa obligatoria.
- No cerrar si falla cuando no existe DB inicializada.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-59-001 | Sobrecarga excesiva | Métricas simples y best-effort. |
| RISK-FUNC-59-002 | Confundir estimación con costo real | Campo `estimated` explícito. |
| RISK-FUNC-59-003 | Datos sensibles | Redacción y exclusión de prompt completo. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-59-001 | MetricRecord JSON | Serializa correctamente. |
| TEST-FUNC-59-002 | Summary | Agrega conteos. |
| TEST-FUNC-59-003 | Model mock | Registra provider=mock sin costo. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-59: MetricsCollector local para comandos/agentes/tools/modelos. Mantén métricas best-effort, redacción obligatoria y sin dependencias externas.
```

## FUNC-SPRINT-60 — Instrumentación agentic: agentes, tools, approvals y model calls

## Objetivo

Instrumentar AgentRuntime, AgentToolCall, PolicyEngine, Approval Workflow y ModelAdapter para producir spans y métricas correlacionadas.

## Entradas

- `repo_DevPilot_Local_22.zip` como baseline vigente.
- Backlogs Fase A–D aprobados o explícitamente aceptados como prerequisito lógico.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-60-001 | Como supervisor de agentes, quiero reconstruir una ejecución agentic. | Cada agent run tiene spans por tool call. |
| US-FUNC-60-002 | Como auditor, quiero ver qué policy permitió o bloqueó una tool. | Policy decisions se registran como eventos/spans. |
| US-FUNC-60-003 | Como operador, quiero model calls correlacionadas con agentes. | ModelAdapter emite spans cuando se invoque. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-60-001 | Instrumentar AgentRuntime | agents/runtime.py | agent_run span. |
| FUNC-60-002 | Instrumentar AgentToolCall | agents/models.py y runtime | tool_call span. |
| FUNC-60-003 | Instrumentar PolicyEngine | policy/engine.py | policy_check event/span. |
| FUNC-60-004 | Instrumentar ApprovalWorkflow si existe | approval/* | approval span/event. |
| FUNC-60-005 | Instrumentar ModelAdapterRouter | modeling/router.py | model_call span. |
| FUNC-60-006 | Actualizar MIASI Observability Card | docs/06_miasi/observability_card.md | Señales agentic documentadas. |

## Archivos previstos

```text
src/devpilot_core/agents/runtime.py
src/devpilot_core/policy/engine.py
src/devpilot_core/modeling/router.py
src/devpilot_core/observability/tracing.py
tests/test_agent_observability.py
docs/audits/func_sprint_60_agentic_instrumentation_audit.md
docs/functional_sprint_60_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core agent run documentation-audit --target docs/01_requirements --json --write-report
python -m devpilot_core model generate --provider mock --prompt "hello" --json
python -m pytest tests/test_agent_observability.py -q
python -m pytest -q
```

## Criterios PASS

- Agent run genera trace correlacionable.
- Tool calls producen spans.
- Policy decisions quedan observables.

## Criterios BLOCK

- No cerrar si se registran prompts/secretos crudos.
- No cerrar si agentes no implementados producen trazas inconsistentes.
- No cerrar si observabilidad cambia comportamiento funcional.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-60-001 | Acoplar demasiado runtime y observabilidad | Usar helpers/adapters no invasivos. |
| RISK-FUNC-60-002 | Datos sensibles en spans | Redacción y allowlist de campos. |
| RISK-FUNC-60-003 | Ruido excesivo | Configurar nivel de detalle local. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-60-001 | Agent trace | Trace contiene agent_id y tool_call. |
| TEST-FUNC-60-002 | Model trace | Trace contiene provider=mock. |
| TEST-FUNC-60-003 | Policy trace | Bloqueos producen evento observable. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-60: instrumentación agentic de AgentRuntime, PolicyEngine y ModelAdapter. No cambies la lógica funcional; solo añade trazas, métricas y pruebas.
```

## FUNC-SPRINT-61 — CLI de trazas y métricas: trace report, trace inspect, metrics summary

## Objetivo

Agregar comandos CLI para consultar trazas y métricas sin requerir UI ni servicios externos.

## Entradas

- `repo_DevPilot_Local_22.zip` como baseline vigente.
- Backlogs Fase A–D aprobados o explícitamente aceptados como prerequisito lógico.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-61-001 | Como operador, quiero listar y resumir trazas recientes. | `trace report` genera resumen JSON/Markdown. |
| US-FUNC-61-002 | Como desarrollador, quiero inspeccionar una traza específica. | `trace inspect <trace_id>` devuelve árbol de spans. |
| US-FUNC-61-003 | Como arquitecto, quiero métricas agregadas por comando/agente/modelo. | `metrics summary` produce agregados. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-61-001 | Crear comandos `trace report` y `trace inspect` | CLI | Comandos JSON/report. |
| FUNC-61-002 | Crear comando `metrics summary` | CLI | Agregados locales. |
| FUNC-61-003 | Crear formato Markdown para trace report | ReportEngine | Reporte humano. |
| FUNC-61-004 | Actualizar README/runbook | docs | Comandos documentados. |
| FUNC-61-005 | Agregar tests CLI | tests/test_observability_cli.py | JSON parseable. |

## Archivos previstos

```text
src/devpilot_core/cli.py
src/devpilot_core/observability/trace_queries.py
tests/test_observability_cli.py
docs/05_operations/runbook.md
README.md
docs/audits/func_sprint_61_trace_metrics_cli_audit.md
docs/functional_sprint_61_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core trace report --json --write-report
python -m devpilot_core trace inspect <trace_id> --json
python -m devpilot_core metrics summary --json --write-report
python -m pytest -q
```

## Criterios PASS

- Comandos devuelven CommandResult.
- Reportes se escriben en outputs/reports.
- Si no hay trazas, responden ok con data vacía o warning controlado.

## Criterios BLOCK

- No cerrar si un trace_id inexistente genera excepción no controlada.
- No cerrar si se exponen secretos.
- No cerrar si los comandos requieren UI.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-61-001 | DB vacía | Responder de forma controlada. |
| RISK-FUNC-61-002 | Reportes grandes | Agregar límites y filtros. |
| RISK-FUNC-61-003 | CLI sigue creciendo | Considerar módulo CLI observability si se vuelve grande. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-61-001 | Trace report vacío | No falla. |
| TEST-FUNC-61-002 | Trace inspect | Devuelve árbol o not found controlado. |
| TEST-FUNC-61-003 | Metrics summary | Agrega conteos. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-61: comandos `trace report`, `trace inspect` y `metrics summary`. Deben funcionar sin UI y generar reportes opcionales.
```

## FUNC-SPRINT-62 — Exporter OpenTelemetry opcional y dry-run

## Objetivo

Preparar un exporter OpenTelemetry local/opcional que mapee los eventos internos de DevPilot a un formato compatible, sin enviar datos externos por defecto.

## Entradas

- `repo_DevPilot_Local_22.zip` como baseline vigente.
- Backlogs Fase A–D aprobados o explícitamente aceptados como prerequisito lógico.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-62-001 | Como operador avanzado, quiero exportar trazas en formato estándar cuando lo apruebe. | Existe exporter dry-run que produce payload local. |
| US-FUNC-62-002 | Como revisor de seguridad, quiero impedir exfiltración accidental. | Exporter remoto queda disabled por defecto y requiere approval/config. |
| US-FUNC-62-003 | Como arquitecto, quiero mapear GenAI events internos a convenciones OTel. | Existe mapping documentado. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-62-001 | Crear `otel_exporter.py` en modo dry-run | observability/exporters | Genera JSON local compatible. |
| FUNC-62-002 | Mapear TraceContext/SpanRecord a OTel-like payload | mapper | Campos documentados. |
| FUNC-62-003 | Agregar policy check para export | PolicyEngine/MIASI | Export externo bloqueado. |
| FUNC-62-004 | Actualizar Tool Registry | `.devpilot/miasi/tool_registry.json` | Tool `telemetry.export` declarada. |
| FUNC-62-005 | Agregar tests de no exfiltración | tests | No hay llamadas de red. |

## Archivos previstos

```text
src/devpilot_core/observability/exporters/otel_exporter.py
src/devpilot_core/observability/exporters/__init__.py
tests/test_otel_exporter.py
docs/05_operations/observability_plan.md
docs/06_miasi/tool_card.md
docs/audits/func_sprint_62_otel_exporter_audit.md
docs/functional_sprint_62_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core telemetry export --format otlp --dry-run --json --write-report
python -m pytest tests/test_otel_exporter.py -q
python -m pytest -q
```

## Criterios PASS

- Exporter opera en dry-run/local.
- No realiza red por defecto.
- MIASI declara tool y policy correspondiente.

## Criterios BLOCK

- No cerrar si el exporter envía datos externos.
- No cerrar si requiere collector externo para pasar tests.
- No cerrar si payload contiene secretos.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-62-001 | Confundir compatibilidad con integración real | Documentar como preliminary/dry-run. |
| RISK-FUNC-62-002 | Exfiltración | Bloqueo por PolicyEngine y default disabled. |
| RISK-FUNC-62-003 | Dependencias innecesarias | No agregar SDK OTel obligatorio en primera versión. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-62-001 | Dry-run payload | Genera archivo/reporte local. |
| TEST-FUNC-62-002 | No network | Test verifica no llamadas externas. |
| TEST-FUNC-62-003 | Redacción | Secret sintético ausente. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-62: exporter OTel opcional en dry-run. No agregues envío remoto ni dependencias obligatorias. Declara tool/policy en MIASI y agrega pruebas de no exfiltración.
```

## FUNC-SPRINT-63 — AgentOps Quality Gate y cierre Fase E

## Objetivo

Consolidar observabilidad y AgentOps en un quality gate que evalúe si el workspace produce evidencia operacional suficiente para agentes, modelos, policies y tools.

## Entradas

- `repo_DevPilot_Local_22.zip` como baseline vigente.
- Backlogs Fase A–D aprobados o explícitamente aceptados como prerequisito lógico.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-63-001 | Como owner, quiero saber si DevPilot está listo operacionalmente para agentes avanzados. | `agentops status` evalúa señales mínimas. |
| US-FUNC-63-002 | Como auditor, quiero un reporte de cierre de Fase E. | Existe auditoría con capacidades y brechas. |
| US-FUNC-63-003 | Como arquitecto, quiero criterios de entrada para Fase F/UI. | El gate produce PASS/BLOCK y recomendaciones. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-63-001 | Crear `agentops status` | CLI/services | Evalúa trace, metrics, reports, MIASI obs. |
| FUNC-63-002 | Crear AgentOps Quality Gate | observability/agentops.py | Findings PASS/BLOCK. |
| FUNC-63-003 | Generar reporte de cierre Fase E | docs/audits/phase_e_agentops_closure_report.md | Resumen de estado. |
| FUNC-63-004 | Actualizar README/runbook/backlog | docs | Sincronizado. |
| FUNC-63-005 | Agregar tests end-to-end | tests/test_agentops_gate.py | Smoke PASS. |

## Archivos previstos

```text
src/devpilot_core/observability/agentops.py
tests/test_agentops_gate.py
docs/audits/phase_e_agentops_closure_report.md
docs/functional_sprint_63_manifest.json
README.md
docs/05_operations/runbook.md
```

## Comandos objetivo

```powershell
python -m devpilot_core agentops status --json --write-report
python -m devpilot_core trace report --json
python -m devpilot_core metrics summary --json
python -m pytest -q
```

## Criterios PASS

- AgentOps status reporta ok=true cuando señales mínimas existen.
- El cierre documenta capacidades implementadas/parciales/futuras.
- Fase F puede consumir ApplicationService/API con observabilidad disponible.

## Criterios BLOCK

- No cerrar si AgentOps depende de UI.
- No cerrar si no hay reporte de cierre.
- No cerrar si MIASI Observability queda desactualizado.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-63-001 | Gate demasiado estricto | Separar required vs recommended. |
| RISK-FUNC-63-002 | Falsos bloqueos en workspace nuevo | Permitir estado inicial con warnings accionables. |
| RISK-FUNC-63-003 | Documentación dispersa | Cierre Fase E consolida estado. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-63-001 | agentops status | JSON parseable. |
| TEST-FUNC-63-002 | Reportes | outputs/reports/agentops_status.* |
| TEST-FUNC-63-003 | Regresión | pytest completo PASS. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-63: AgentOps Quality Gate y cierre Fase E. Agrega `agentops status`, reporte de cierre, docs sincronizadas y pruebas.
```

## Cierre esperado de Fase E

Al cerrar Fase E, DevPilot debe tener una capa AgentOps local suficientemente robusta para observar comandos, agentes, tools, políticas, approvals, modelos y métricas sin depender de servicios externos. Esta fase no entrega UI, pero deja listas las señales y contratos que la Fase F deberá visualizar.
