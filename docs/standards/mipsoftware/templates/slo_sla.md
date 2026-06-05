---
title: Plantilla — SLI/SLO/SLA
doc_id: MIPS-TPL-SLO-SLA
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: observability-operations-sre
created: '2026-05-31'
updated: '2026-05-31'
related_standard: MIPS-DOC-012 — Observabilidad, operación, SRE e incidentes
---

# Plantilla — SLI/SLO/SLA

## 1. Propósito

Definir indicadores, objetivos y compromisos de servicio.

## 2. Campos obligatorios

| Campo | Descripción |
|---|---|
| Servicio | Servicio o flujo medido. |
| SLI | Indicador medido. |
| SLO | Objetivo interno. |
| Ventana | Mensual, semanal, rolling window. |
| Error budget | Margen aceptado de incumplimiento. |
| SLA | Compromiso externo, si aplica. |
| Alertas | Umbrales asociados. |
| Excepciones | Mantenimiento, terceros, incidentes excluidos. |

## 3. Ejemplo

```yaml
service: "checkout"
sli:
  name: "successful_checkout_rate"
  formula: "successful_checkouts / total_checkout_attempts"
slo:
  target: "99.0%"
  window: "30d"
error_budget_policy:
  warning: "50% budget consumed"
  freeze: "100% budget consumed"
sla:
  external_commitment: false
```

## 4. Criterios de rechazo

- El SLO no es medible.
- El SLA se declara sin capacidad de medición.
- No hay política de error budget para servicios críticos.
