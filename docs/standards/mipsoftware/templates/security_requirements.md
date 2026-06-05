---
title: Security Requirements
doc_id: MIPS-TPL-SEC-002
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: security-privacy-compliance
created: '2026-05-31'
updated: '2026-05-31'
---

# Security Requirements

## Propósito

Definir requisitos verificables de seguridad que se conectan con arquitectura, implementación, pruebas y release.

## Campos obligatorios

| Campo | Descripción |
|---|---|
| ID | Identificador único. |
| Tipo | authn/authz/input/output/secrets/privacy/logging/ci/agentic. |
| Requisito | Declaración verificable. |
| Justificación | Riesgo o necesidad que cubre. |
| Criterio de aceptación | Cómo se comprueba. |
| Prueba asociada | Test o evidencia. |
| Prioridad | must/should/could. |
| Estado | draft/approved/implemented/verified. |

## Ejemplo completo

| ID | Tipo | Requisito | Criterio de aceptación | Prueba | Prioridad |
|---|---|---|---|---|---|
| SEC-001 | authz | El backend debe validar ownership en toda consulta de órdenes. | Un usuario no puede consultar órdenes ajenas. | `test_orders_authorization.py` | must |
| SEC-002 | secrets | Ninguna API key debe aparecer en logs. | Secret scan y pruebas de redacción pasan. | `secret_scan_report.json` | must |
| SEC-003 | agentic | El agente no puede ejecutar acciones destructivas sin aprobación humana. | Policy gate bloquea acción sin approval. | MIASI Eval Card | must |

## Criterios de rechazo

- Requisitos no verificables.
- Requisitos sin owner o prueba.
- Requisitos críticos sin criterio de aceptación.

