---
title: "Auditoría FUNC-SPRINT-59 — MetricsCollector para comandos, agentes, tools y modelos"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-59-METRICS-COLLECTOR"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-13"
approval: "approved_by_owner_direction"
phase: "FASE-E-AGENTOPS-OBSERVABILIDAD"
sprint: "FUNC-SPRINT-59"
---

# Auditoría FUNC-SPRINT-59 — MetricsCollector para comandos, agentes, tools y modelos

## 1. Propósito

Registrar la implementación y verificación de `FUNC-SPRINT-59 — MetricsCollector para comandos, agentes, tools y modelos`, sprint de Fase E orientado a persistir métricas locales, agregables y seguras para AgentOps sin dependencias externas.

## 2. Alcance

Sprint 59 implementa:

- `MetricRecord` como contrato serializable y redactado.
- `MetricsCollector` como fachada best-effort para métricas de comandos, agentes, tools y modelos.
- extensión de `LocalStore` con schema `0004_metrics_collector_v1` y columnas consultables en tabla `metrics`.
- `record_metric`, `list_metrics` y `metrics_summary` sobre SQLite.
- registro best-effort de comandos desde `_persist_result` en la CLI.
- registro best-effort de métricas del `ModelAdapterRouter` para provider/model/task/tokens/costo estimado.
- pruebas unitarias de serialización, redacción, persistencia, summary, migración legacy y modelo mock.

No implementa todavía:

- CLI pública `metrics summary` o `metrics inspect`;
- instrumentación completa de `AgentRuntime`, `PolicyEngine`, `ApprovalWorkflow` o tool calls reales;
- dashboards;
- exporter OpenTelemetry;
- AgentOps Quality Gate.

## 3. Resultado

Veredicto: `PASS`.

El sprint queda en estado `implemented-initial`. La implementación conserva la regla local-first, no agrega dependencias externas, no usa red, no activa exporters y no cambia la semántica funcional de comandos o model calls. Las métricas son best-effort: si falla su escritura, el resultado funcional original se mantiene.

## 4. Evidencia de implementación

Archivos creados:

- `src/devpilot_core/observability/metrics.py`
- `tests/test_metrics_collector.py`
- `docs/audits/func_sprint_59_metrics_collector_audit.md`
- `docs/functional_sprint_59_manifest.json`
- `tests/test_sprint_59_documentation.py`

Archivos modificados:

- `src/devpilot_core/observability/__init__.py`
- `src/devpilot_core/store/local_store.py`
- `src/devpilot_core/cli.py`
- `src/devpilot_core/modeling/router.py`
- `README.md`
- `docs/05_operations/runbook.md`
- `docs/05_operations/observability_plan.md`
- `docs/06_miasi/observability_card.md`
- `docs/devpilot_backlog_fase_E_agentops_observabilidad.md`
- `docs/functional_backlog_after_precode.md`
- pruebas documentales históricas para sincronizar el hito vigente hacia Sprint 60.

## 5. Criterios PASS

- `MetricRecord` serializa un payload JSON seguro.
- `MetricsCollector` persiste métricas sin requerir DB preinicializada.
- `MetricsCollector.summary()` agrega conteos por categoría, estado y proveedor.
- `ModelAdapterRouter` registra métricas para provider `mock` sin costo externo real.
- `LocalStore` migra tablas `metrics` legacy de forma idempotente.
- `state init/status` reportan `schema_version=0004_metrics_collector_v1`.
- No hay API externa, red, exporter remoto ni OpenTelemetry SDK obligatorio.

## 6. Criterios BLOCK

- Se persiste prompt completo, completion cruda, diff, patch, stdout/stderr o secreto en métricas.
- Se agrega dependencia externa obligatoria.
- Las métricas alteran el resultado funcional de comandos o model calls.
- `MetricsCollector` falla cuando la DB no existe.
- Se versiona `.devpilot/devpilot.db` como artefacto de código.
- El proveedor `mock` registra costo real externo o `external_api_used=true`.

## 7. Riesgos

| Riesgo | Estado | Mitigación |
|---|---|---|
| Sobrecarga por métricas | Bajo | Métricas simples, síncronas y best-effort. |
| Confundir estimación con costo real | Controlado | Campo `estimated=true` y costo mock `0.0`. |
| Exposición de payload sensible | Controlado | Redacción con `sanitize_metric_metadata` y exclusión de prompt/completion/diff/stdout. |
| Métricas agentic incompletas | Pendiente | Sprint 60 instrumentará agentes, tools, policies, approvals y model calls. |
| Sin CLI pública de consulta | Por diseño | Sprint 61 entregará comandos/reportes de trazas y métricas. |

## 8. Comandos de verificación

```powershell
python -m devpilot_core state init --json
python -m devpilot_core state status --json
python -m devpilot_core model providers --json
python -m devpilot_core model generate --provider mock --prompt "hello" --json
python -m pytest tests/test_metrics_collector.py -q
python -m pytest tests/test_trace_store.py tests/test_event_logger.py tests/test_trace_context.py tests/test_local_store.py tests/test_metrics_collector.py tests/test_sprint_59_documentation.py -q
python -m devpilot_core validate-artifact docs/audits/func_sprint_59_metrics_collector_audit.md --json
python -m devpilot_core schema validate-manifest docs/functional_sprint_59_manifest.json --json
python -m devpilot_core validate all --json
python -m pytest -q
```

## 9. Estado de capacidades

| Capacidad | Estado |
|---|---|
| MetricRecord | implementado inicial |
| MetricsCollector | implementado inicial |
| Persistencia SQLite de métricas | implementado inicial |
| Summary agregado programático | implementado inicial |
| Métricas de comandos CLI | implementado inicial best-effort |
| Métricas de modelo mock | implementado inicial best-effort |
| Métricas agent/tool vía API | contrato disponible; runtime pendiente Sprint 60 |
| CLI metrics summary | pendiente Sprint 61 |
| Exporter OTel | pendiente/opt-in Sprint 62 |
| AgentOps Quality Gate | pendiente Sprint 63 |

## 10. Próximo paso

Continuar con `FUNC-SPRINT-60 — Instrumentación agentic: agentes, tools, approvals y model calls`, conectando spans y métricas con runtime agentic real sin exponer payloads crudos ni alterar comportamiento funcional.
