---
title: Template — Business Rule
doc_id: MIPS-TPL-BUSINESS_RULE
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
domain: requirements-engineering
model: MIPSoftware — Modelo de Ingeniería Profesional de Software
---

# Business Rule

## Propósito

Registrar restricciones, cálculos, decisiones o políticas del dominio que deben respetarse en la implementación.

## Campos obligatorios

| Campo | Descripción |
|---|---|
| ID | RULE-000 |
| Nombre |  |
| Tipo | restricción/cálculo/validación/autorización/proceso |
| Regla |  |
| Fuente | Stakeholder, normativa, proceso o decisión |
| Ejemplos |  |
| Excepciones |  |
| Requerimientos afectados |  |
| Pruebas asociadas |  |
| Riesgos |  |

## Ejemplo completo

```text
RULE-001 — No vender sin inventario
Tipo: restricción
Regla: Una venta confirmada no puede incluir productos con inventario disponible menor a la cantidad solicitada, salvo que el producto esté marcado como preventa.
Fuente: Operación de ventas
Requerimientos afectados: FR-ORDER-003, DR-INVENTORY-002
Pruebas: TEST-INVENTORY-002
```

## Criterios de rechazo

- Regla sin fuente.
- Regla sin ejemplos.
- Regla no vinculada a requerimientos.
