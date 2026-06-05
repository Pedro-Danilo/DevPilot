---
title: Plantilla — Contrato de eventos
doc_id: MIPS-TPL-EVENT-CONTRACT
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model/templates
created: '2026-05-31'
updated: '2026-05-31'
---

# Plantilla — Contrato de eventos

## 1. Información general
- Evento:
- Tipo:
- Versión:
- Productor:
- Consumidores:
- Semántica:

## 2. Payload
```yaml
event_type: "domain.entity.changed"
version: "1.0"
event_id: "uuid"
occurred_at: "datetime"
correlation_id: "string"
data: {}
```

## 3. Entrega
| Campo | Valor |
|---|---|
| Delivery guarantee | at_most_once / at_least_once / exactly_once_simulated |
| Ordering | none / per_entity / global |
| Retry policy | |
| Dead letter | |
| Idempotency key | |

## 4. Compatibilidad
| Cambio | Breaking | Acción |
|---|---:|---|
| Agregar campo opcional | No | Documentar |
| Eliminar campo | Sí | Nueva versión |

## 5. Observabilidad
- Trace ID:
- Correlation ID:
- Métricas:
- Alertas:

## 6. Tests mínimos
- [ ] Producer contract test.
- [ ] Consumer contract test.
- [ ] Duplicate handling test.
- [ ] Schema validation test.
