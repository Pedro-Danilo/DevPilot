---
title: "ADR-0012 — Observabilidad v2 y modelo AgentOps local-first"
doc_id: "DEVPL-ADR-0012"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-56"
updated: "2026-06-13"
accepted_by: "Ordóñez"
accepted_at: "2026-06-13"
acceptance_scope: "FUNC-SPRINT-56 ADR de observabilidad v2 y modelo AgentOps"
approval: "approved_by_owner"
---
# ADR-0012 — Observabilidad v2 y modelo AgentOps local-first

## Estado

Accepted.

## Contexto

DevPilot Local cerró Fase D con proveedores locales opcionales, `PromptRegistry`, `BudgetLedger`, `ModelEvalRunner`, `AgentRuntime v2` y agentes monoagente gobernados para repositorio, revisión, patches, refactor, pruebas, requisitos, arquitectura y seguridad. Esa superficie agentic ya produce salidas estructuradas, tool calls simuladas, model calls gobernadas y evidencias locales, pero todavía no tiene un modelo de observabilidad v2 capaz de reconstruir una ejecución completa como árbol operacional.

El informe de avance Sprint 0-18 había identificado que DevPilot contaba con `EventLogger` JSONL, reportes y persistencia SQLite inicial, pero que faltaban trace report, spans jerárquicos, métricas de costo/tokens/latencia, dashboard AgentOps y exportación estándar opcional. Fase E aborda esa brecha de forma incremental.

`FUNC-SPRINT-56` no debe modificar runtime ni introducir exporters. Su responsabilidad es tomar una decisión arquitectónica explícita antes de implementar `TraceContext`, `SpanRecord`, `MetricRecord`, `TraceStore`, CLI de trazas/métricas y AgentOps Quality Gate en sprints posteriores.

## Decisión

DevPilot adoptará una arquitectura de observabilidad v2 local-first y vendor-neutral, compuesta por cinco familias de señales:

1. **Eventos**: hechos discretos append-only emitidos por comandos, gates, agentes, tools, modelos, approvals, sandbox y seguridad.
2. **Trazas**: contexto de correlación de una ejecución completa mediante `trace_id`, `run_id`, `agent_run_id` y relaciones entre operaciones.
3. **Spans**: unidades temporales jerárquicas para comando, agente, tool call, policy check, approval, model call, sandbox y reporte.
4. **Métricas**: agregados locales sobre duración, conteos, severidad, tokens/costo estimados, fallos, bloqueos y redacciones.
5. **Reportes**: evidencias JSON/Markdown reproducibles para operación humana, auditoría y futura UI.

La arquitectura se implementará gradualmente:

- `FUNC-SPRINT-56`: contratos y documentación, sin nuevos exporters ni dependencias.
- `FUNC-SPRINT-57`: `TraceContext` y `SpanRecord` internos.
- `FUNC-SPRINT-58`: `TraceStore` y compatibilidad con `EventLogger` JSONL.
- `FUNC-SPRINT-59`: `MetricRecord` y `MetricsCollector`.
- `FUNC-SPRINT-60`: instrumentación de agentes, tools, policies, approvals y modelos.
- `FUNC-SPRINT-61`: CLI `trace report`, `trace inspect` y `metrics summary`.
- `FUNC-SPRINT-62`: exporter OpenTelemetry-like en dry-run/local opt-in.
- `FUNC-SPRINT-63`: `agentops status` y AgentOps Quality Gate.

La fuente operacional seguirá siendo local: JSONL append-only en `outputs/traces/` y SQLite consultable en `.devpilot/devpilot.db`. El ZIP de entrega no debe incluir `outputs/`, caches ni `.devpilot/devpilot.db`.

## Alternativas consideradas

| Alternativa | Evaluación |
|---|---|
| Mantener solo `EventLogger` v1 | Es simple, pero no permite reconstruir jerarquías comando → agente → tool → policy → modelo. |
| Adoptar OpenTelemetry SDK como dependencia inmediata | Aporta estándar, pero introduce complejidad y riesgo de exfiltración antes de cerrar contratos locales. |
| Implementar dashboard AgentOps antes de trazas | Visualmente atractivo, pero prematuro porque no existen señales canónicas consultables. |
| Diseñar modelo v2 local-first antes de runtime | Decisión adoptada: reduce acoplamiento, evita telemetría accidental y permite evolución incremental. |

## Modelo conceptual

```text
CommandRun
  trace_id
  run_id
  ├─ command span
  │  ├─ validation/report spans
  │  ├─ agent_run span
  │  │  ├─ policy_check span
  │  │  ├─ tool_call span
  │  │  ├─ model_call span
  │  │  └─ approval span, si aplica
  │  └─ report_write span
  └─ metric records
```

## Contrato mínimo de Trace

| Campo | Obligatorio | Propósito |
|---|---:|---|
| `trace_id` | Sí | Identifica una ejecución correlacionable extremo a extremo. |
| `run_id` | Sí | Identifica una invocación de comando/servicio dentro de DevPilot. |
| `workspace_id` | Recomendado | Vincula la traza con un workspace local. |
| `root_span_id` | Recomendado | Permite reconstruir árbol de spans. |
| `actor` | Sí | `cli`, `agent`, `service`, `test`, `human` o `system`. |
| `started_at` / `ended_at` | Sí | Timestamps ISO-8601 UTC o local-normalizados. |
| `status` | Sí | `ok`, `failed`, `blocked`, `skipped`, `warning`. |
| `redaction_applied` | Sí | Indica si hubo sanitización de payloads. |

## Contrato mínimo de Span

| Campo | Obligatorio | Propósito |
|---|---:|---|
| `span_id` | Sí | Identifica la operación. |
| `trace_id` | Sí | Relación con la traza. |
| `parent_span_id` | Opcional | Relación jerárquica. |
| `span_type` | Sí | `command`, `agent_run`, `tool_call`, `policy_check`, `model_call`, `approval`, `sandbox`, `report`, `validation`. |
| `name` | Sí | Nombre estable de la operación. |
| `started_at` / `ended_at` | Sí | Duración calculable. |
| `status` | Sí | Estado operacional. |
| `attributes` | Sí | Metadata allowlist y redactada. |
| `findings_count` | Recomendado | Conteo de findings asociados sin payload sensible. |

## Contrato mínimo de Metric

| Campo | Obligatorio | Propósito |
|---|---:|---|
| `metric_id` | Sí | Identificador de métrica. |
| `name` | Sí | Nombre estable tipo `devpilot.*`. |
| `metric_type` | Sí | `counter`, `gauge`, `histogram`, `summary`. |
| `value` | Sí | Valor numérico o agregado serializable. |
| `unit` | Recomendado | `ms`, `count`, `usd_estimated`, `tokens_estimated`. |
| `scope` | Sí | `command`, `agent`, `tool`, `model`, `policy`, `approval`, `sandbox`. |
| `attributes` | Sí | Metadata redactada. |
| `estimated` | Recomendado | Distingue costos/tokens estimados de medición real. |

## Política de redacción

La observabilidad v2 debe aplicar redacción por defecto. Los payloads de trazas, spans, métricas y reportes deben cumplir:

- no almacenar API keys, tokens, passwords, secrets ni `.env` crudo;
- no guardar prompts completos ni completions crudas por defecto;
- no persistir diffs completos salvo modo explícito futuro con aprobación;
- usar summaries, digests, conteos, ids, severidad, estado y rutas relativas cuando sea suficiente;
- registrar `raw_prompt_stored=false`, `raw_output_stored=false` o equivalentes en model calls;
- pasar payloads sensibles por `SecretGuard` y reglas allowlist antes de persistir.

## OpenTelemetry

OpenTelemetry se adopta como referencia conceptual y compatibilidad futura, no como dependencia obligatoria en `FUNC-SPRINT-56`.

Reglas:

1. Ningún exporter remoto queda habilitado por defecto.
2. Cualquier exporter deberá iniciar en modo dry-run/local.
3. El envío remoto requerirá configuración explícita, PolicyEngine, CostGuard/approval cuando aplique y documentación de privacidad.
4. Las convenciones GenAI podrán mapearse desde señales internas sin exponer prompts ni completions crudas.

## Relación con MIASI

MIASI exige que todo agente y tool call sea gobernado, auditable y evaluable. Observabilidad v2 materializa esa exigencia mediante:

- `agent_run_id` correlacionable;
- `tool_call_id` por llamada de herramienta;
- `policy_decision_id` o metadata equivalente por evaluación de política;
- `model_call_id` o digest por invocación de modelo;
- `approval_id` cuando exista aprobación humana;
- eventos y spans redacted;
- métricas de costo/tokens/latencia estimadas cuando existan;
- reportes reproducibles.

## Consecuencias positivas

- DevPilot podrá reconstruir ejecuciones agentic de extremo a extremo.
- La futura UI de Fase F tendrá señales canónicas para reportes y visores.
- Los agentes podrán evolucionar sin perder auditabilidad.
- OpenTelemetry queda preparado sin dependencia ni exfiltración prematura.
- La separación evento/trace/span/metric/report reduce ambigüedad operacional.

## Consecuencias negativas

- Aumenta el volumen de datos locales en `outputs/` y SQLite.
- Requiere mantener compatibilidad entre `EventLogger` v1 y TraceStore v2.
- La documentación debe sincronizarse estrictamente para evitar señales duplicadas o ambiguas.
- La primera versión será `implemented-initial`; no equivale a observabilidad industrial completa hasta cerrar Fase E.

## Criterios PASS

- Existe esta ADR aprobada antes de modificar runtime.
- `docs/05_operations/observability_plan.md` documenta eventos, trazas, spans, métricas y reportes v2.
- `docs/06_miasi/observability_card.md` cubre agentes, tools, modelos, policies, approvals y sandbox.
- `docs/05_operations/observability_signal_catalog.md` cataloga señales canónicas preliminares.
- No se agregan dependencias externas ni exporters activos.
- No se permite telemetría remota por defecto.
- Los artefactos pasan validación documental y MIASI sigue en PASS.

## Criterios BLOCK

- Habilitar envío remoto de telemetría por defecto.
- Agregar SDK OpenTelemetry obligatorio en este sprint.
- Persistir prompts, completions, secrets o diffs crudos como señales normales.
- Confundir AgentOps con multiagente, handoffs, RAG o MCP.
- Implementar instrumentación runtime antes de cerrar los contratos de señales.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Diseño demasiado amplio | Limitar Sprint 56 a ADR, plan, card, catálogo, manifest y auditoría. |
| Exfiltración accidental futura | Exporters opt-in/dry-run, policy checks y redacción obligatoria. |
| Duplicación de señales | Catálogo canónico con nombres estables y evolución versionada. |
| Ruido operacional | Separar required/recommended/future y evitar payloads extensos. |
| Acoplamiento prematuro con OTel | Mantener modelo interno vendor-neutral y mapping futuro. |

## Relación con DevPilot

Esta ADR implementa el nivel FE-L0 de Fase E. Es prerrequisito para `FUNC-SPRINT-57 — TraceContext y modelo de spans`, `FUNC-SPRINT-58 — TraceStore y EventLogger v2 compatible` y el cierre futuro `FUNC-SPRINT-63 — AgentOps Quality Gate y cierre Fase E`.
