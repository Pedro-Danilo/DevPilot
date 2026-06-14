---
title: "AgentOps Observability Card — DevPilot Local"
doc_id: "DEVPL-MIASI-OBSERVABILITY"
status: "approved"
version: "1.3.0"
owner: "Ordóñez"
standard: "MIASI"
parent_standard: "MIPSoftware"
phase: "FUNC-SPRINT-56"
updated: "2026-06-13"
approval: "approved_by_owner_direction"
source_baseline: "observability plan approved + security approved"
change_policy: "controlled_changes_allowed_via_docs_as_code"
baseline_role: "precode_approved_baseline"
---

# AgentOps Observability Card — DevPilot Local

## 1. Propósito

Este documento define la observabilidad específica para agentes IA en DevPilot Local. Complementa `docs/05_operations/observability_plan.md` y precisa eventos, trazas, métricas, reportes y auditoría para agentes, herramientas, modelos, approvals, costos y policies.

La regla central es:

> Toda acción agentic debe ser trazable, reproducible, redactada, evaluable y asociada a un workspace, agente, tool, policy y decisión.

## 2. Señales obligatorias

| Señal | Propósito | Almacenamiento inicial |
|---|---|---|
| Agent run event | Inicio/cierre de ejecución agentic. | JSONL |
| Tool call event | Propuesta, dry-run, aprobación o bloqueo de tool. | JSONL |
| Policy decision | PASS/FAIL/BLOCK por policy. | JSON/JSONL |
| Approval event | Solicitud y decisión humana. | JSONL |
| Cost event | Estimación/consumo API. | JSONL |
| Eval event | Resultado de evaluación. | JSON/JSONL |
| Security finding | Riesgo detectado. | JSON/Markdown |
| Trace summary | Resumen legible por humano. | Markdown |
| Model event | Modelo/proveedor/configuración usada. | JSONL |
| Memory/RAG event | Recuperación, fuentes y grounding. | JSONL futuro |

## 3. Taxonomía de eventos agentic

| Evento | Cuándo se emite |
|---|---|
| `devpilot.agent.run.started` | Inicio de agente. |
| `devpilot.agent.run.completed` | Fin correcto. |
| `devpilot.agent.run.failed` | Error no controlado. |
| `devpilot.agent.tool_call.proposed` | El agente propone tool. |
| `devpilot.agent.tool_call.blocked` | Policy bloquea tool. |
| `devpilot.agent.tool_call.executed_dry_run` | Tool ejecutada en dry-run. |
| `devpilot.agent.approval.required` | Se requiere aprobación. |
| `devpilot.agent.approval.approved` | Aprobación concedida. |
| `devpilot.agent.approval.rejected` | Aprobación rechazada. |
| `devpilot.agent.eval.completed` | Evaluación terminada. |
| `devpilot.agent.cost.estimated` | Costo estimado. |
| `devpilot.agent.security.finding` | Hallazgo de seguridad. |
| `devpilot.agent.secret.redacted` | Se redactó secreto. |

## 4. Campos mínimos de evento

```json
{
  "event_id": "evt_0001",
  "timestamp": "2026-06-05T10:00:00-05:00",
  "workspace_id": "devpilot-local",
  "agent_id": "DocumentationAuditAgent",
  "event_type": "devpilot.agent.tool_call.proposed",
  "tool_id": "audit_documentation",
  "mode": "dry_run",
  "risk_level": "medium",
  "policy_result": "pass",
  "approval_id": null,
  "redaction_applied": true,
  "cost_estimate": null,
  "correlation_id": "run_0001"
}
```

## 5. Métricas AgentOps

| Métrica | Propósito |
|---|---|
| `agent_runs_total` | Cantidad de ejecuciones agentic. |
| `agent_failures_total` | Fallos por agente. |
| `tool_calls_total` | Uso de herramientas. |
| `tool_calls_blocked_total` | Bloqueos por policy. |
| `approval_requests_total` | Solicitudes humanas. |
| `approval_rejections_total` | Rechazos humanos. |
| `security_findings_total` | Hallazgos. |
| `secret_redactions_total` | Redacciones. |
| `cost_estimate_total` | Costo estimado. |
| `eval_pass_rate` | Tasa de aprobación de evaluaciones. |

## 6. Mapeo futuro con OpenTelemetry GenAI

| Concepto DevPilot | Mapeo OTel futuro |
|---|---|
| Agent run | span de agente |
| Tool call | span/evento de tool |
| Model call | span GenAI client |
| Tokens/costo | métricas GenAI |
| Approval | evento custom |
| Policy decision | evento custom |
| RAG retrieval | spans de retrieval |
| Eval | evento de evaluación |

## 7. Retención y privacidad

| Dato | Retención inicial | Política |
|---|---|---|
| Reportes Markdown | versionable si no contiene secretos | revisar antes de commit |
| JSON reports | local | no publicar sin redacción |
| JSONL traces | local, no versionar por defecto | retención configurable |
| Cost events | local | sin API keys |
| Approval events | local | conservar para auditoría |
| Model prompts/responses | restringido | redactar o resumir |

## 8. Criterios PASS

La observabilidad agentic queda aprobada si:

- todos los agentes emiten eventos mínimos;
- todas las tools registran decisión de policy;
- approvals quedan trazadas;
- costos quedan estimados;
- secretos se redactan;
- errores se normalizan;
- hay correlación por workspace/run.

## 9. Criterios BLOCK

Bloquear despliegue o activación si:

- un agente no emite trazas;
- no hay evidencia de tool call;
- no se registran bloqueos;
- se guardan secretos sin redacción;
- no se puede reconstruir qué ocurrió;
- no hay correlación entre agente, tool, policy y output.

## Actualización FUNC-SPRINT-12 — Observabilidad del Agent Runtime

Los comandos `agent run` emiten resultados mediante `CommandResult`, pueden generar evidencia JSON/Markdown con `--write-report`, emiten eventos JSONL por la envoltura CLI y persisten resultados en SQLite de forma best-effort. Los tool calls internos se reportan como estructuras auditables dentro de `data.tool_calls`.

Limitación: todavía no existe una traza agentic jerárquica completa con spans, correlación por paso, métricas de latencia por herramienta ni SLO/SLA. Esta capacidad queda pendiente para sprints posteriores.


## 12. Actualización FUNC-SPRINT-56 — Contrato MIASI para observabilidad v2

`FUNC-SPRINT-56` actualiza esta card para alinear MIASI con `ADR-0012 — Observabilidad v2 y modelo AgentOps local-first`. Esta actualización no implementa instrumentación runtime todavía; define las señales obligatorias que deberán producir los sprints 57 a 63.

## 13. Contrato v2 de correlación agentic

| Elemento MIASI | ID correlacionable | Señal requerida | Estado Sprint 56 |
|---|---|---|---|
| Agent run | `agent_run_id` | evento + span `agent_run` | definido/no implementado |
| Tool call | `tool_call_id` | evento + span `tool_call` | definido/no implementado |
| Policy check | `policy_decision_id` o metadata equivalente | evento + span `policy_check` | definido/no implementado |
| Approval | `approval_id` | evento + span `approval` | definido/no implementado |
| Model call | `model_call_id` o digest | evento + span `model_call` + métrica | definido/no implementado |
| Sandbox/refactor/patch | `sandbox_id`/`changeset_id`/`rollback_id` | evento + span `sandbox` | definido/no implementado |
| Reporte | `report_id`/path | evento + span `report` | definido/no implementado |

## 14. Señales obligatorias por agente y tool

| Dominio | Obligatorio | Bloqueante si falta desde Sprint 60 |
|---|---|---|
| Agente | `agent_id`, `agent_run_id`, `trace_id`, `status`, `dry_run`, `preliminary` | Sí |
| Tool | `tool_id`, `tool_call_id`, `action`, `allowed`, `policy_exit_code`, `dry_run` | Sí |
| Modelo | `provider`, `model`, `task`, `prompt_id`, `prompt_version`, `tokens_estimated`, `cost_estimate_usd` | Sí |
| Política | guards evaluados, `allowed`, `blocked`, `approval_required`, `approval_valid` | Sí |
| Aprobación | `approval_id`, acción, riesgo, decisión humana | Sí cuando aplique |
| Seguridad | redacciones, findings, bloqueos por SecretGuard/PromptInjectionGuard/ToolInjectionGuard | Sí |

## 15. Reglas de redacción MIASI v2

- Ningún agente puede persistir prompt completo o completion cruda como evento/span normal.
- Tool args deben registrarse como resumen redactado o allowlist de campos.
- Model calls deben registrar digest y metadatos, no request/response crudos.
- Secrets detectados por SecretGuard deben producir señal de redacción/bloqueo, no exponer el secreto.
- Toda señal debe indicar `external_api_used=false` salvo decisión futura explícita y aprobada.

## 16. Relación con AgentOps Quality Gate

El futuro `agentops status` de `FUNC-SPRINT-63` deberá evaluar al menos:

| Control | PASS | BLOCK |
|---|---|---|
| Correlación | agent/tool/model tienen `trace_id` | señales agentic huérfanas |
| Redacción | no hay secretos ni payloads crudos | secreto/prompt crudo en traza |
| Policy visibility | policy decisions observables | tool call sin policy |
| Model visibility | provider/model/task/costo estimado visibles | model call opaca |
| Approval visibility | aprobaciones trazables | acción riesgosa sin approval trace |
| Local-first | señales locales reproducibles | dependencia cloud obligatoria |

## 17. Riesgos y límites

Esta card queda en versión `1.1.0` como contrato inicial. No equivale a un dashboard AgentOps industrial ni a trazas distribuidas. La calidad industrial llegará al cerrar Fase E con spans persistidos, métricas consultables, CLI de inspección, exporter dry-run y AgentOps Quality Gate.


## 18. Actualización FUNC-SPRINT-59 — Métricas MIASI locales

`FUNC-SPRINT-59` agrega `MetricRecord` y `MetricsCollector` como contrato ejecutable inicial para métricas AgentOps. Desde MIASI, toda métrica debe ser local, redactada, correlacionable cuando exista `trace_id`, y no debe alterar la semántica funcional de agentes, tools, policies o modelos.

| Dominio MIASI | Métrica mínima | Estado Sprint 59 |
|---|---|---|
| Command | conteo por estado y duración opcional | implementado en CLI helper |
| Agent | conteo/duración vía API `record_agent_operation` | API lista; runtime pendiente Sprint 60 |
| Tool | conteo/duración vía API `record_tool_operation` | API lista; runtime pendiente Sprint 60 |
| Model | provider/model/task/tokens/costo estimado | mock instrumentado |

Criterio BLOCK MIASI: ninguna métrica puede persistir prompt completo, completion cruda, argumentos sensibles, secretos, diffs, patches o salida de proceso. `cost_estimate_usd` y `tokens_estimated` deben tratarse como estimaciones salvo que un proveedor futuro entregue medición confiable y aprobada.


## FUNC-SPRINT-60 — Señales agentic instrumentadas

La tarjeta MIASI de observabilidad queda extendida con instrumentación runtime `implemented-initial` para:

- `AgentRuntime`: span `agent.run`, métrica `devpilot.agent.run_total` y metadatos `trace_id`/`run_id`/`agent_run_id`.
- `AgentToolCall`: `tool_call_id`, span `tool.call` y métrica `devpilot.tool.call_total`.
- `PolicyEngine`: span/evento `policy.check` y métrica `devpilot.policy.check_total`.
- `ApprovalService`: span/evento `approval.workflow` y métrica `devpilot.approval.<operation>_total`.
- `ModelAdapterRouter`: span/evento `model.call` y métricas de provider/model/task/tokens/costo estimado.

Restricciones vigentes: redacción obligatoria, `mock` como ruta hermética, telemetría remota bloqueada, exporters desactivados, sin multiagente funcional y sin cambios funcionales por fallos de observabilidad.


## FUNC-SPRINT-61 — Consulta MIASI de trazas y métricas

MIASI reconoce desde `FUNC-SPRINT-61` tres comandos de consulta operacional sobre señales AgentOps locales:

- `trace report`: permite a un supervisor revisar trazas recientes sin UI.
- `trace inspect <trace_id>`: permite a un desarrollador reconstruir el árbol de spans de una ejecución.
- `metrics summary`: permite a un arquitecto/operador revisar métricas agregadas por comando, agente, tool, policy, approval o modelo.

Estos comandos son read-only respecto a la ejecución agentic: solo consultan SQLite y escriben reportes cuando el usuario solicita `--write-report`. No ejecutan tools, no invocan modelos, no envían datos externos y no habilitan exporter. La respuesta ante DB vacía o traza inexistente debe ser controlada, auditable y parseable.

Criterio BLOCK MIASI: ninguna consulta puede exponer prompts, completions, secretos, diffs, patches, stdout/stderr ni credenciales. Cualquier visualización futura debe consumir estos mismos contratos en lugar de leer `.devpilot/devpilot.db` directamente desde una UI.


## FUNC-SPRINT-62 — Export OTel dry-run como señal MIASI

MIASI reconoce `telemetry.export` como herramienta local de reporte, no como salida remota. La señal esperada es un payload OTel-like generado desde datos ya redactorizados de `TraceStore`/`MetricsCollector`.

Criterios:

- `telemetry.export` solo opera en dry-run.
- `OTEL_EXPORT_DRY_RUN_ALLOW` permite generación local de payload.
- `OTEL_REMOTE_EXPORT_BLOCK` bloquea endpoints remotos o cualquier intento de exfiltración.
- `network_used=false`, `external_api_used=false`, `remote_telemetry_enabled=false`.
- La capacidad es `implemented-initial` y debe evolucionar antes de integrarse con collectors reales.
