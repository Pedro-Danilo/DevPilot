---
title: Plantilla — Screen Spec
doc_id: MIPS-TPL-SCREEN-SPEC
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
related_document: 07_ux_ui_accesibilidad.md
---

# Plantilla — Screen Spec

## 1. Propósito
Especificar una pantalla para que pueda diseñarse, implementarse, probarse y auditarse.

## 2. Campos obligatorios
| Campo | Descripción |
|---|---|
| screen_id | Identificador. |
| objetivo | Tarea principal. |
| usuario/rol | Quién puede usarla. |
| ruta | URL o ubicación. |
| datos requeridos | Inputs/API/estado. |
| contenido | Secciones visibles. |
| acción primaria | CTA principal. |
| acciones secundarias | Acciones alternativas. |
| estados | loading, empty, error, success, disabled. |
| errores | Mensajes y recuperación. |
| permisos | Roles y restricciones. |
| responsive | Reglas por tamaño. |
| accesibilidad | Foco, labels, semántica. |
| pruebas | Casos E2E/UX/a11y. |

## 3. Ejemplo completo
```yaml
screen_id: "SCR-DEV-001"
name: "Project Intake"
route: "/projects/new"
primary_action: "Crear proyecto"
states:
  loading: "Mostrar skeleton"
  empty: "Formulario inicial"
  error: "Resumen de errores + mensajes por campo"
  success: "Redirigir a readiness"
permissions:
  roles: ["owner", "developer"]
responsive:
  mobile: "Formulario en una columna"
  desktop: "Formulario + panel de ayuda"
accessibility:
  keyboard: true
  focus_order: "logical"
```

## 4. Criterios de rechazo
- No declara estados de error.
- Acción destructiva sin confirmación.
- Datos sensibles visibles sin justificación.
