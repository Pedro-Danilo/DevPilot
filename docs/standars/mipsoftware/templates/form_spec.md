---
title: Plantilla — Form Spec
doc_id: MIPS-TPL-FORM-SPEC
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
related_document: 07_ux_ui_accesibilidad.md
---

# Plantilla — Form Spec

## 1. Propósito
Definir campos, validaciones, errores, envío, idempotencia y accesibilidad de formularios.

## 2. Campos obligatorios
| Campo | Descripción |
|---|---|
| form_id | Identificador. |
| propósito | Qué operación realiza. |
| campos | Nombre, tipo, obligatorio, validación. |
| reglas de negocio | Restricciones del dominio. |
| errores | Mensajes por campo y globales. |
| envío | Endpoint/comando/acción. |
| idempotencia | Prevención de duplicados. |
| seguridad | Datos sensibles y permisos. |
| accesibilidad | Labels, ayuda, errores anunciables. |

## 3. Ejemplo completo
```yaml
form_id: "FORM-SALE-001"
purpose: "Registrar venta"
fields:
  - name: "customer_name"
    type: "string"
    required: true
    validation: "1..120 chars"
    error: "Ingresa el nombre del cliente."
  - name: "payment_status"
    type: "enum"
    required: true
    allowed: ["pending", "paid"]
submission:
  method: "POST"
  endpoint: "/sales"
idempotency:
  key: "client_generated_request_id"
security:
  sensitive_fields: []
accessibility:
  labels_visible: true
  errors_textual: true
```

## 4. Criterios de rechazo
- Placeholder como único label.
- Errores solo por color.
- Doble envío genera registros duplicados.
