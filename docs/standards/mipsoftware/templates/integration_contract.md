---
title: Plantilla — Contrato de integración
doc_id: MIPS-TPL-INTEGRATION-CONTRACT
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model/templates
created: '2026-05-31'
updated: '2026-05-31'
---

# Plantilla — Contrato de integración

## 1. Sistema externo
- Nombre:
- Propósito:
- Owner interno:
- Owner externo:
- Tipo: API / webhook / batch / archivo / evento / SDK

## 2. Datos intercambiados
| Dato | Dirección | Clasificación | Retención | Riesgo |
|---|---|---|---|---|
| | inbound/outbound | | | |

## 3. Seguridad
- Autenticación:
- Secret management:
- Permisos mínimos:
- Rotación:
- Datos sensibles:

## 4. Resiliencia
| Control | Valor |
|---|---|
| Timeout | |
| Retry | |
| Backoff | |
| Circuit breaker | |
| Fallback | |
| Rate limit | |

## 5. Webhooks
- Firma requerida:
- Idempotency key:
- Procesamiento async:
- Reintentos:

## 6. Observabilidad
- Logs:
- Métricas:
- Trazas:
- Alertas:

## 7. Criterios de rechazo
- Sin owner.
- Sin gestión de secretos.
- Sin timeout.
- Sin estrategia de error.
- Sin clasificación de datos.
