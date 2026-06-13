---
title: "Catálogo de señales de observabilidad v2 — DevPilot Local"
doc_id: "DEVPL-OPS-OBS-SIGNAL-CATALOG-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-56"
updated: "2026-06-13"
approval: "approved_by_owner"
source_adr: "docs/02_architecture/adrs/ADR-0012-observability-v2-agentops.md"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval_scope: "FUNC-SPRINT-56 observability signal catalog"
---
# Catálogo de señales de observabilidad v2 — DevPilot Local

## 1. Propósito

Este documento define el catálogo preliminar y canónico de señales de observabilidad v2 para Fase E. Su función es evitar señales duplicadas o ambiguas antes de implementar `TraceContext`, `SpanRecord`, `MetricRecord`, `TraceStore`, CLI de trazas/métricas y AgentOps Quality Gate.

El catálogo es **implemented-initial/documental** en `FUNC-SPRINT-56`: no instrumenta runtime todavía. La instrumentación se implementará progresivamente en `FUNC-SPRINT-57` a `FUNC-SPRINT-63`.

## 2. Estado

| Elemento | Estado Sprint 56 |
|---|---|
| ADR de observabilidad v2 | `implemented` |
| Catálogo de señales | `implemented-initial` |
| TraceContext Python | `defined/no implementado` |
| SpanRecord Python | `defined/no implementado` |
| MetricRecord Python | `defined/no implementado` |
| TraceStore SQLite | `defined/no implementado` |
| CLI trace/metrics | `defined/no implementado` |
| Exporter OTel | `futuro opt-in/dry-run` |
| AgentOps Quality Gate | `definido/no implementado` |

## 3. Convenciones de nombres

| Familia | Prefijo | Ejemplo |
|---|---|---|
| Evento | `devpilot.<domain>.<action>` | `devpilot.agent.run.started` |
| Span type | snake_case estable | `model_call` |
| Métrica | `devpilot_<domain>_<measure>` | `devpilot_model_cost_estimated_usd` |
| Trace id | `trace_*` | `trace_20260613_000001` |
| Span id | `span_*` | `span_agent_tool_call_001` |
| Tool call id | `toolcall_*` | `toolcall_policy_001` |
| Agent run id | `agrun_*` | `agrun_requirements_001` |

## 4. Eventos canónicos

| Evento | Dominio | Productor previsto | Campos mínimos | Estado |
|---|---|---|---|---|
| `devpilot.command.started` | command | CLI/ApplicationService | `trace_id`, `run_id`, `command`, `actor`, `started_at` | future-implementation |
| `devpilot.command.completed` | command | CLI/ApplicationService | `trace_id`, `run_id`, `exit_code`, `duration_ms`, `status` | future-implementation |
| `devpilot.command.failed` | command | CLI/ApplicationService | `trace_id`, `run_id`, `error_type`, `status` | future-implementation |
| `devpilot.validation.executed` | validation | ValidationGateway | `trace_id`, `validation_id`, `ok`, `findings_total` | future-implementation |
| `devpilot.report.written` | report | ReportEngine | `trace_id`, `report_path`, `format`, `redacted` | future-implementation |
| `devpilot.agent.run.started` | agent | AgentRuntime v2 | `trace_id`, `agent_run_id`, `agent_id`, `provider` | future-implementation |
| `devpilot.agent.run.completed` | agent | AgentRuntime v2 | `trace_id`, `agent_run_id`, `status`, `suggestions_total` | future-implementation |
| `devpilot.agent.tool_call.proposed` | tool | AgentRuntime v2 | `trace_id`, `tool_call_id`, `tool_id`, `dry_run` | future-implementation |
| `devpilot.agent.tool_call.blocked` | tool/policy | PolicyEngine | `trace_id`, `tool_call_id`, `policy_decision`, `severity` | future-implementation |
| `devpilot.policy.check.completed` | policy | PolicyEngine | `trace_id`, `policy_decision_id`, `allowed`, `blocked`, `guards` | future-implementation |
| `devpilot.approval.requested` | approval | ApprovalWorkflow | `trace_id`, `approval_id`, `action`, `risk_level` | future-implementation |
| `devpilot.approval.decided` | approval | ApprovalWorkflow | `trace_id`, `approval_id`, `decision`, `decided_by` | future-implementation |
| `devpilot.model.call.started` | model | ModelAdapterRouter | `trace_id`, `model_call_id`, `provider`, `model`, `task` | future-implementation |
| `devpilot.model.call.completed` | model | ModelAdapterRouter/BudgetLedger | `trace_id`, `model_call_id`, `tokens_estimated`, `cost_estimate_usd`, `duration_ms` | future-implementation |
| `devpilot.model.call.blocked` | model/security | PolicyEngine/CostGuard/SecretGuard | `trace_id`, `provider`, `reason`, `blocking_guard` | future-implementation |
| `devpilot.sandbox.execution.planned` | sandbox | PatchSandbox/RefactorExecutor | `trace_id`, `sandbox_id`, `dry_run`, `mutations_performed` | future-implementation |
| `devpilot.security.redaction.applied` | security | SecretGuard | `trace_id`, `redactions_total`, `payload_type` | future-implementation |

## 5. Span types canónicos

| Span type | Propósito | Parent esperado | Campos allowlist |
|---|---|---|---|
| `command` | Duración de comando CLI/ApplicationService | root | `command`, `args_summary`, `exit_code`, `ok` |
| `validation` | Validación documental/contract/gate | `command` | `validator`, `target`, `findings_total`, `blocking_findings_total` |
| `agent_run` | Ejecución monoagente | `command` | `agent_id`, `provider`, `model`, `dry_run`, `preliminary` |
| `tool_call` | Uso/propuesta de herramienta | `agent_run` | `tool_id`, `action`, `allowed`, `dry_run`, `policy_exit_code` |
| `policy_check` | Evaluación PolicyEngine/guards | `tool_call` o `command` | `guards`, `allowed`, `blocked`, `approval_required` |
| `model_call` | Invocación a ModelAdapterRouter | `agent_run` o `command` | `provider`, `model`, `task`, `prompt_id`, `tokens_estimated`, `cost_estimate_usd` |
| `approval` | Solicitud/decisión humana | `tool_call` o `command` | `approval_id`, `status`, `risk_level` |
| `sandbox` | Operación en sandbox local | `command` | `sandbox_id`, `mode`, `mutations_performed`, `rollback_available` |
| `report` | Escritura de reporte/evidencia | `command` | `report_path`, `format`, `redacted`, `size_bytes` |
| `git_readonly` | Lectura segura de Git | `command` | `branch`, `dirty`, `files_changed_count` |

## 6. Métricas canónicas

| Métrica | Tipo | Unidad | Scope | Descripción |
|---|---|---|---|---|
| `devpilot_command_duration_ms` | histogram | `ms` | command | Duración por comando. |
| `devpilot_command_failures_total` | counter | `count` | command | Comandos con `exit_code` FAIL/BLOCK/ERROR. |
| `devpilot_findings_total` | counter | `count` | validation/security | Findings por severidad y dominio. |
| `devpilot_blocking_findings_total` | counter | `count` | validation/security | Findings bloqueantes. |
| `devpilot_agent_runs_total` | counter | `count` | agent | Ejecuciones agentic por agente. |
| `devpilot_agent_tool_calls_total` | counter | `count` | tool | Tool calls propuestas/ejecutadas/bloqueadas. |
| `devpilot_policy_blocks_total` | counter | `count` | policy | Bloqueos por policy/guard. |
| `devpilot_approvals_required_total` | counter | `count` | approval | Acciones que requieren aprobación. |
| `devpilot_model_calls_total` | counter | `count` | model | Llamadas a modelo por provider/task. |
| `devpilot_model_tokens_estimated_total` | counter | `tokens_estimated` | model | Tokens estimados; no medición contractual exacta. |
| `devpilot_model_cost_estimated_usd` | counter | `usd_estimated` | model | Costo estimado; cero para mock/local si aplica. |
| `devpilot_secret_redactions_total` | counter | `count` | security | Redacciones aplicadas por SecretGuard. |
| `devpilot_trace_spans_total` | counter | `count` | trace | Spans por trace. |
| `devpilot_reports_written_total` | counter | `count` | report | Reportes generados. |

## 7. Matriz de señales por dominio

| Dominio | Eventos | Spans | Métricas | Reportes |
|---|---|---|---|---|
| CLI/ApplicationService | started/completed/failed | `command` | duración/fallos | command report futuro |
| Validación | validation executed | `validation` | findings/bloqueos | validate all/report |
| Agentes | agent started/completed/failed | `agent_run` | runs/fallos | agent run report |
| Tools | proposed/blocked/executed | `tool_call` | tool_calls/blocks | trace report |
| Policies/guards | check completed | `policy_check` | policy_blocks | security/agentops report |
| Approvals | requested/decided/revoked | `approval` | approvals_required | approval audit |
| Modelos | call started/completed/blocked | `model_call` | tokens/cost/duración | model budget/eval |
| Sandbox/refactor/patch | planned/executed/rollback | `sandbox` | executions/rollbacks | sandbox report |
| Git/repo | readonly snapshot | `git_readonly` | files_changed | repo report |
| Reportes | report written | `report` | reports_written | markdown/json |

## 8. Reglas de redacción

| Payload | Permitido por defecto | Bloqueado por defecto |
|---|---|---|
| Prompt | `prompt_id`, `version`, inputs usados, digest | prompt completo, secretos, `.env` |
| Completion | digest, longitud, estado | completion completa sensible |
| Patch/diff | estadísticas, rutas relativas, riesgos | diff completo salvo modo futuro aprobado |
| Tool args | summary redacted, ids, paths relativos | tokens, passwords, rutas fuera de workspace |
| Model metadata | provider, model, task, tokens/costo estimado | headers, API keys, request crudo |
| Approval | id, estado, riesgo, decisión | datos personales innecesarios |

## 9. Criterios PASS

- Cada señal tiene nombre estable, dominio, productor previsto y estado.
- El catálogo distingue evento, span, métrica y reporte.
- OpenTelemetry queda como mapping futuro, no como dependencia.
- No se autoriza telemetría remota ni payloads crudos.
- El catálogo es compatible con MIASI y con Fase E.

## 10. Criterios BLOCK

- Señales que requieran red o servicios cloud para operar.
- Persistencia de secretos, prompts crudos o completions crudas.
- Métricas de costo presentadas como reales cuando solo son estimadas.
- Instrumentación runtime incluida antes de Sprint 57/58/59.
- Confusión entre AgentOps y multiagente funcional.

## 11. Riesgos

| Riesgo | Mitigación |
|---|---|
| Señales excesivas | Mantener required/recommended/future y revisar en AgentOps Gate. |
| Inconsistencia de nombres | Usar este catálogo como fuente canónica durante Fase E. |
| Datos sensibles | Allowlist de atributos y redacción obligatoria. |
| Costos ambiguos | Campo `estimated=true` para tokens/costos no medidos. |

## 12. Comandos de verificación

```powershell
python -m devpilot_core validate-artifact docs/05_operations/observability_signal_catalog.md --json
python -m devpilot_core validate-artifact docs/05_operations/observability_plan.md --json
python -m devpilot_core miasi validate --json
python -m pytest tests/test_sprint_56_documentation.py -q
```
