---
title: Plantilla — Accessibility Checklist
doc_id: MIPS-TPL-ACCESSIBILITY-CHECKLIST
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
related_document: 07_ux_ui_accesibilidad.md
---

# Plantilla — Accessibility Checklist

## 1. Propósito
Validar accesibilidad básica antes de release o aceptación de UI.

## 2. Checklist
| Ítem | Obligatorio | Evidencia | PASS | FAIL |
|---|---:|---|---|---|
| Navegación por teclado | Sí | Registro de prueba | Se completan tareas críticas. | Tarea crítica exige mouse. |
| Foco visible | Sí | Captura/video | Foco claro y secuencial. | Foco perdido o invisible. |
| Contraste | Sí | Revisión tokens | Texto legible. | Bajo contraste en texto crítico. |
| Labels de formulario | Sí | Inspección | Inputs asociados a labels. | Placeholder único. |
| Errores textuales | Sí | Captura | Error específico + corrección. | Solo ícono/color. |
| Semántica | Sí | Inspección DOM | Headings/botones/links correctos. | Divs clicables sin semántica. |
| Alternativas | Si aplica | Revisión contenido | Imágenes informativas con texto alternativo. | Imagen crítica sin alternativa. |
| Responsive | Sí | Capturas | Sin scroll horizontal crítico. | Flujo roto en móvil. |

## 3. Criterios de bloqueo
- Flujo crítico inaccesible por teclado.
- Formulario crítico sin errores textuales.
- Información crítica dependiente solo de color.
- Acción destructiva no distinguible ni confirmada.
