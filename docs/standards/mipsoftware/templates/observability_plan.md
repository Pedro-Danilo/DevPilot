---
title: Plantilla — Observability Plan
doc_id: MIPS-TPL-OBSERVABILITY-PLAN
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: observability-operations-sre
created: '2026-05-31'
updated: '2026-05-31'
related_standard: MIPS-DOC-012 — Observabilidad, operación, SRE e incidentes
---

# Plantilla — Observability Plan

## 1. Propósito

Definir cómo el sistema será observado en ambientes `local`, `dev`, `staging` y `prod` mediante logs, métricas, trazas, dashboards, alertas y auditoría.

## 2. Cuándo usarla

Debe usarse antes de desplegar cualquier sistema no trivial y es obligatoria para producción.

## 3. Campos obligatorios

| Campo | Descripción |
|---|---|
| Sistema | Nombre, owner, repositorio, ambiente. |
| Flujos críticos | Flujos que deben observarse. |
| Logs | Eventos, niveles, estructura y redacción. |
| Métricas | SLIs, métricas técnicas y métricas de negocio. |
| Trazas | Operaciones distribuidas, spans y correlación. |
| Dashboards | Vistas necesarias y audiencia. |
| Alertas | Condición, severidad, responsable y runbook. |
| Retención | Tiempo de conservación por señal. |
| Seguridad | Datos prohibidos en telemetría. |
| MIASI | Señales agentic si aplica. |

## 4. Ejemplo

```yaml
system: "orders-api"
environments: ["local", "staging", "prod"]
critical_flows:
  - "create_order"
  - "payment_callback"
logs:
  format: "json"
  required_fields: ["timestamp", "level", "service", "event_name", "correlation_id"]
metrics:
  sli:
    - name: "availability"
      query: "successful_requests / total_requests"
      target: "99.5%"
tracing:
  enabled_for: ["http", "database", "external_api"]
alerts:
  - name: "high_error_rate"
    severity: "SEV-2"
    condition: "error_rate > 2% for 10m"
    runbook: "templates/runbook.md"
```

## 5. Criterios de revisión

- Todos los flujos críticos tienen señal observable.
- Las alertas críticas tienen runbook.
- No se registran secretos ni datos sensibles innecesarios.

## 6. Criterios de rechazo

- No hay logs o métricas mínimas.
- No existe plan de redacción de datos sensibles.
- No hay responsables operativos.
