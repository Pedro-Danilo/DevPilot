---
title: "Auditoría FUNC-SPRINT-58 — TraceStore y EventLogger v2 compatible"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-58-TRACE-STORE"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-13"
approval: "approved_by_owner_direction"
phase: "FASE-E-AGENTOPS-OBSERVABILIDAD"
sprint: "FUNC-SPRINT-58"
---

# Auditoría FUNC-SPRINT-58 — TraceStore y EventLogger v2 compatible

## 1. Propósito

Registrar la implementación y verificación de `FUNC-SPRINT-58 — TraceStore y EventLogger v2 compatible`, sprint de Fase E orientado a persistir trazas consultables sin romper el EventLogger JSONL existente.

## 2. Alcance

Sprint 58 implementa:

- `TraceStore` como fachada de observabilidad sobre `LocalStore`.
- persistencia SQLite de spans mediante tabla `spans`.
- tabla `metrics` preparada para Sprint 59.
- columnas de correlación `trace_id`, `span_id` y `parent_span_id` en la tabla `events`.
- migración idempotente para bases existentes.
- extensión compatible de `EventLogger` para aceptar `TraceContext` y `SpanRecord` opcionales.
- helper interno `TraceStore.record_smoke_trace()` para verificar persistencia sin CLI pública.
- pruebas unitarias de persistencia, migración, compatibilidad JSONL y smoke trace.

No implementa todavía:

- CLI pública `trace report` o `trace inspect`;
- agregación de métricas;
- `MetricsCollector`;
- exporter OpenTelemetry;
- instrumentación agentic automática;
- AgentOps Quality Gate.

## 3. Resultado

Veredicto: `PASS`.

El sprint queda en estado `implemented-initial`. La implementación conserva JSONL como evidencia append-only y agrega SQLite como proyección consultable de spans/eventos. No introduce dependencias externas, no requiere red, no activa OpenTelemetry y no habilita telemetría remota.

## 4. Evidencia de implementación

Archivos creados:

- `src/devpilot_core/observability/trace_store.py`
- `tests/test_trace_store.py`
- `docs/audits/func_sprint_58_trace_store_audit.md`
- `docs/functional_sprint_58_manifest.json`
- `tests/test_sprint_58_documentation.py`

Archivos modificados:

- `src/devpilot_core/observability/events.py`
- `src/devpilot_core/observability/__init__.py`
- `src/devpilot_core/store/local_store.py`
- `tests/test_local_store.py`
- `tests/test_approval_store.py`
- `README.md`
- `docs/05_operations/runbook.md`
- `docs/05_operations/observability_plan.md`
- `docs/devpilot_backlog_fase_E_agentops_observabilidad.md`
- `docs/functional_backlog_after_precode.md`
- pruebas documentales históricas para sincronizar hito vigente hacia Sprint 59.

## 5. Criterios PASS

- `TraceStore` persiste spans y permite consultarlos por `trace_id`.
- `TraceStore` persiste eventos correlacionables por `trace_id`.
- `EventLogger` v1 sigue escribiendo JSONL sin cambios obligatorios para clientes existentes.
- `EventLogger` v2 acepta `TraceContext`/`SpanRecord` opcionales.
- `LocalStore` migra la tabla `events` de forma idempotente.
- `LocalStore.status()` reporta tablas `spans` y `metrics` tras inicialización/migración.
- `history list` y `state status` no se rompen.

## 6. Criterios BLOCK

- Se versiona `.devpilot/devpilot.db` como artefacto de código.
- Se rompe `EventLogger` v1 o los tests existentes de eventos.
- Se rompe `history list`.
- La migración SQLite falla sobre una DB existente.
- Se requiere OpenTelemetry SDK, collector externo, red o API externa.
- Se almacenan prompts, completions, diffs, patches, stdout/stderr o secretos sin redacción.

## 7. Riesgos

| Riesgo | Estado | Mitigación |
|---|---|---|
| Duplicidad JSONL/SQLite | Aceptado | JSONL conserva evidencia append-only; SQLite se documenta como proyección consultable. |
| Migración SQLite frágil | Controlado | `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE` idempotente y tests con tabla `events` legacy. |
| Crecimiento de almacenamiento | Pendiente | Retención/compactación queda para evolución posterior. |
| Sin CLI pública de trazas | Por diseño | CLI `trace report` y `trace inspect` quedan para Sprint 61. |
| Placeholder runs para eventos con `run_id` sin CommandResult | Aceptado | Se crean runs mínimos para conservar integridad referencial sin perder correlación. |

## 8. Comandos de verificación

```powershell
python -m devpilot_core state init --json
python -m devpilot_core state status --json
python -m pytest tests/test_trace_store.py -q
python -m pytest tests/test_event_logger.py tests/test_trace_context.py tests/test_local_store.py -q
python -m devpilot_core validate-artifact docs/audits/func_sprint_58_trace_store_audit.md --json
python -m devpilot_core schema validate-manifest docs/functional_sprint_58_manifest.json --json
python -m devpilot_core validate all --json
python -m pytest -q
```

## 9. Estado de capacidades

| Capacidad | Estado |
|---|---|
| TraceStore | implementado inicial |
| Persistencia de spans | implementado inicial |
| Persistencia de eventos correlacionables | implementado inicial |
| EventLogger v2 opcional | implementado inicial |
| Migración SQLite idempotente | implementado inicial |
| Tabla metrics | preparada; sin collector aún |
| CLI de trazas | no iniciado; Sprint 61 |
| MetricsCollector | no iniciado; Sprint 59 |
| OpenTelemetry exporter | no iniciado; Sprint 62 |
| AgentOps Quality Gate | no iniciado; Sprint 63 |

## 10. Próximo paso

Implementar `FUNC-SPRINT-59 — MetricsCollector para comandos, agentes, tools y modelos` sobre la base de `TraceContext`, `SpanRecord`, `TraceStore` y las tablas SQLite preparadas.
