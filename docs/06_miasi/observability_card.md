---
title: "AgentOps Observability Card — DevPilot Local"
doc_id: "DEVPL-MIASI-OBSERVABILITY"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIASI"
parent_standard: "MIPSoftware"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
source_baseline: "observability plan approved + security approved"
change_policy: "controlled_changes_allowed_until_precode_baseline"
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
