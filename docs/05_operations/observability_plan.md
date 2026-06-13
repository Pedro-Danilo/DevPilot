---
title: "Observability Plan — DevPilot Local"
doc_id: "DEVPL-OPS-001"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-56"
updated: "2026-06-13"
approval: "approved_by_owner"
source_baseline: "00_product approved + 01_requirements approved + 02_architecture approved + 03_security approved"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval_scope: "FUNC-SPRINT-56 observability v2 baseline"
---

# Observability Plan — DevPilot Local

## 1. Propósito

Este documento define la observabilidad mínima y evolutiva de **DevPilot Local**, incluyendo logs, métricas, trazas, auditoría, reportes, eventos agentic, señales operativas y evidencia local.

DevPilot no debe ser una herramienta opaca. Cada validación, gate, agente, herramienta, reporte y decisión relevante debe dejar evidencia local suficiente para auditar qué ocurrió, por qué ocurrió y qué artefactos fueron afectados.

## 2. Principios

| Principio | Aplicación |
|---|---|
| Local-first observable | La evidencia se genera localmente por defecto. |
| Vendor-neutral | Compatibilidad futura con OpenTelemetry, sin lock-in. |
| Privacy by design | Logs y trazas no deben exponer secretos ni datos innecesarios. |
| Auditabilidad | Todo gate y acción sensible debe generar evento. |
| Correlación | Los eventos deben tener `run_id`, `workspace_id` y `artifact_id` cuando aplique. |
| Separación de señales | Reportes, logs, trazas y métricas cumplen funciones distintas. |
| AgentOps | Los agentes deben emitir trazas de intención, tool calls, evaluación y aprobación. |

## 3. Señales de observabilidad

| Señal | Formato | Ubicación inicial | MVP | MVP+ | Post-MVP |
|---|---|---|---:|---:|---:|
| Reportes de validación | JSON/Markdown | `outputs/reports/` | Sí | Sí | Sí |
| Logs estructurados | JSONL | `outputs/logs/` | Sí | Sí | Sí |
| Trazas agentic | JSONL | `outputs/traces/` | Sí | Sí | Sí |
| Eventos de auditoría | JSONL | `outputs/audit/` | Sí | Sí | Sí |
| Métricas locales | JSON | `outputs/metrics/` | Parcial | Sí | Sí |
| Dashboards | Markdown/HTML futuro | `outputs/dashboards/` | No | Parcial | Sí |
| Exporters externos | OTLP futuro | opcional | No | No | Opcional |

## 4. Taxonomía de eventos

| Evento | Cuándo se emite | Campos mínimos |
|---|---|---|
| `devpilot.run.started` | inicio de comando | run_id, command, workspace |
| `devpilot.run.completed` | fin de comando | run_id, status, duration_ms |
| `devpilot.artifact.validated` | validación documental | artifact, status, findings |
| `devpilot.gate.evaluated` | gate PASS/FAIL/BLOCK | gate, result, evidence |
| `devpilot.security.finding` | hallazgo de seguridad | severity, finding_id, artifact |
| `devpilot.privacy.finding` | hallazgo privacidad | severity, data_type, mitigation |
| `devpilot.agent.started` | inicio agente | agent_id, task_id, model_provider |
| `devpilot.agent.tool_call.proposed` | tool call propuesto | tool, args_redacted, risk |
| `devpilot.agent.tool_call.approved` | aprobación humana | approval_id, approver |
| `devpilot.agent.tool_call.executed` | ejecución controlada | tool, result, dry_run |
| `devpilot.cost.event` | uso de modelo/API | provider, estimated_cost, budget |
| `devpilot.git.snapshot` | lectura estado Git | branch, dirty, commit |
| `devpilot.patch.reviewed` | revisión patch | patch_id, findings, status |

## 5. Esquema mínimo de evento JSONL

```json
{
  "timestamp": "2026-06-05T10:00:00Z",
  "event_name": "devpilot.gate.evaluated",
  "run_id": "run_001",
  "workspace_id": "devpilot_local",
  "phase": "precode",
  "severity": "info",
  "status": "pass",
  "actor": "cli",
  "artifact": "docs/01_requirements/requirements_specification.md",
  "message": "Requirement gate passed",
  "metadata": {}
}
```

## 6. Reportes

| Reporte | Formato | Propósito |
|---|---|---|
| `readiness_check.json` | JSON | Estado mínimo de readiness |
| `readiness_check.md` | Markdown | Revisión humana |
| `precode_gate_report.json` | JSON | Gate documental estricto |
| `security_report.json` | JSON | Hallazgos de seguridad |
| `miasi_activation_report.json` | JSON | Activación MIASI |
| `agent_eval_report.json` | JSON | Evaluación agentic futura |
| `cost_report.json` | JSON | Costos estimados por proveedor |
| `workspace_report.md` | Markdown | Estado del workspace |

## 7. Métricas iniciales

| Métrica | Tipo | Umbral inicial |
|---|---|---|
| `devpilot_validation_duration_ms` | performance | < 3000 ms en MVP docs |
| `devpilot_gate_failures_total` | calidad | tendencia decreciente |
| `devpilot_security_findings_total` | seguridad | críticos = 0 |
| `devpilot_documents_validated_total` | cobertura | 100% docs obligatorios |
| `devpilot_agent_tool_calls_total` | AgentOps | con aprobación cuando aplique |
| `devpilot_external_cost_estimated_usd` | costos | dentro del presupuesto |
| `devpilot_secret_redactions_total` | privacidad | auditables |
| `devpilot_git_dirty_state` | repo | reportado, no alterado automáticamente |

## 8. Trazas de agentes

Los agentes deben registrar:

| Campo | Descripción |
|---|---|
| `agent_id` | agente responsable |
| `task_id` | tarea solicitada |
| `model_provider` | mock/local/API |
| `input_summary` | resumen redactado |
| `tool_calls_proposed` | herramientas sugeridas |
| `policy_decision` | allow/deny/approval_required |
| `approval_id` | aprobación asociada |
| `output_summary` | resultado redactado |
| `eval_result` | evaluación si aplica |
| `cost_estimate` | estimación si usa API |

## 9. OpenTelemetry compatibility

DevPilot no implementará necesariamente OpenTelemetry en el MVP, pero sus eventos deben diseñarse para mapearse en el futuro a señales estándar:

| DevPilot | OpenTelemetry futuro |
|---|---|
| `run_id` | trace/span id |
| `event_name` | span/event name |
| `duration_ms` | span duration |
| `severity` | log severity |
| `metadata` | attributes |
| agent/tool calls | GenAI/agent spans futuros |

## 10. Redacción y privacidad

| Regla | Aplicación |
|---|---|
| No secretos en logs | tokens, API keys y passwords deben redactarse |
| No diffs completos por defecto | guardar resumen salvo modo explícito |
| No prompts sensibles completos | registrar resumen redactado |
| No PII innecesaria | minimizar nombres, emails, paths personales |
| Retención controlada | outputs pueden limpiarse por política |

## 11. Retención

| Artefacto | Retención inicial |
|---|---|
| Reportes de readiness | versionables si son relevantes |
| Logs temporales | limpiar manualmente en MVP |
| Trazas agentic | conservar para auditoría durante desarrollo |
| Cost reports | conservar si hubo API externa |
| Security reports | conservar hasta cierre de hallazgos |
| SQLite futura | backup y cleanup por workspace |

## 12. Operación local

En MVP, observabilidad significa:

```text
saber qué comando se ejecutó,
sobre qué workspace,
qué documentos validó,
qué gates pasaron o fallaron,
qué reportes generó,
qué riesgos detectó
y qué acciones quedaron bloqueadas.
```

## 13. Dashboards futuros

| Vista | Etapa |
|---|---|
| Pre-code dashboard | MVP+ |
| Workspace dashboard | MVP+ |
| AgentOps dashboard | Post-MVP |
| Security dashboard | Post-MVP |
| Cost dashboard | Post-MVP |
| Release readiness dashboard | Post-MVP |

## 14. Criterios PASS/FAIL/BLOCK

| Criterio | Estado |
|---|---|
| Toda validación crítica produce reporte | PASS requerido |
| Hallazgos críticos quedan visibles | PASS requerido |
| Secretos redactados | BLOCK si falla |
| Tool calls con trazabilidad | BLOCK si falta en agentes |
| Eventos con `run_id` | PASS requerido |
| Costos externos sin registro | BLOCK |

## 15. Changelog

| Versión | Cambio |
|---|---|
| 0.1.0 | Borrador bootstrap inicial. |
| 0.5.0 | Observabilidad completa para SPRINT-PRECODE-05. |


## 16. Actualización FUNC-SPRINT-56 — Observabilidad v2 y AgentOps

`FUNC-SPRINT-56` eleva este plan desde observabilidad inicial hacia un contrato v2 para Fase E. Esta actualización es **documental/arquitectónica**: no agrega exporters, no modifica runtime y no introduce dependencias externas.

### 16.1 Decisión arquitectónica

La decisión vinculante queda registrada en `docs/02_architecture/adrs/ADR-0012-observability-v2-agentops.md`. La ADR establece que DevPilot adoptará un modelo local-first compuesto por eventos, trazas, spans, métricas y reportes, con JSONL/SQLite como fuentes locales y OpenTelemetry solo como compatibilidad futura opt-in/dry-run.

### 16.2 Separación de señales

| Señal | Definición v2 | Implementación prevista |
|---|---|---|
| Evento | Hecho discreto append-only. | EventLogger v2 compatible en Sprint 58. |
| Trace | Correlación extremo a extremo. | `TraceContext` en Sprint 57. |
| Span | Operación temporal jerárquica. | `SpanRecord` en Sprint 57. |
| Métrica | Agregado local de conteos, duración, costo/tokens estimados o severidad. | `MetricRecord`/`MetricsCollector` en Sprint 59. |
| Reporte | Evidencia JSON/Markdown consultable por humanos y futura UI. | CLI `trace report`/`metrics summary` desde Sprint 61. |

### 16.3 Matriz de señales v2 por dominio

| Dominio | Trace/Span esperado | Eventos mínimos | Métricas iniciales | Reporte esperado |
|---|---|---|---|---|
| Comando CLI/ApplicationService | `command` | started/completed/failed | duración, exit_code | command/trace report futuro |
| Validación y gates | `validation` | validation executed, gate evaluated | findings, blockers | validate all/report |
| Agentes monoagente | `agent_run` | agent started/completed/failed | runs, failures | agent/trace report |
| Tool calls | `tool_call` | proposed/blocked/executed_dry_run | tool_calls, blocked | trace inspect/report |
| PolicyEngine/guards | `policy_check` | policy check completed | policy_blocks | security/agentops report |
| Approval Workflow | `approval` | requested/approved/denied/revoked | approvals_required | approval audit |
| ModelAdapterRouter | `model_call` | model call started/completed/blocked | tokens/cost/duration estimated | model budget/eval report |
| Sandbox/Patch/Refactor | `sandbox` | planned/executed/rollback | sandbox runs, rollbacks | sandbox/refactor report |
| ReportEngine | `report` | report written | reports_written | outputs/reports |

### 16.4 Reglas de redacción v2

- No guardar prompts completos, completions crudas, headers, tokens, API keys, passwords, `.env` ni diffs completos por defecto.
- Registrar resúmenes redactados, digests, conteos, ids, rutas relativas, severidad y estado operacional.
- Toda model call debe exponer `provider`, `model`, `task`, `prompt_id/version` si aplica, `tokens_estimated`, `cost_estimate_usd`, `external_api_used` y flags de raw payload cuando existan.
- Toda traza debe marcar si se aplicó redacción (`redaction_applied=true/false`) y qué payload fue minimizado.

### 16.5 OpenTelemetry opt-in

OpenTelemetry queda tratado como mapping futuro y no como dependencia obligatoria. Cualquier exporter deberá pasar por ADR/policy posterior, iniciar en dry-run/local, no enviar datos externos por defecto y aplicar redacción antes de construir payloads exportables.

### 16.6 Criterios PASS/BLOCK v2

PASS:

- ADR-0012 existe y está aprobada.
- El catálogo `docs/05_operations/observability_signal_catalog.md` define eventos, spans, métricas y reportes canónicos.
- MIASI Observability Card cubre agentes, tools, modelos, policies, approvals y sandbox.
- No hay telemetría remota ni dependencia externa nueva en Sprint 56.

BLOCK:

- Exporter remoto activo por defecto.
- SDK externo obligatorio para que pase la suite base.
- Prompts, completions, secretos o diffs crudos persistidos como observabilidad normal.
- AgentOps usado como excusa para habilitar multiagente, handoffs, RAG o MCP en esta fase.

## 17. Estado preliminar y evolución pendiente

La observabilidad v2 de `FUNC-SPRINT-56` queda en estado `implemented-initial` porque define contratos, no runtime. Para alcanzar calidad industrial completa faltan `TraceContext`, spans, persistencia SQLite, métricas, instrumentación agentic/model, CLI de consulta, exporter dry-run y AgentOps Quality Gate.
