---
title: Plantilla — Design System mínimo
doc_id: MIPS-TPL-DESIGN-SYSTEM
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
related_document: 07_ux_ui_accesibilidad.md
---

# Plantilla — Design System mínimo

## 1. Propósito
Definir tokens, componentes y patrones mínimos para consistencia, mantenibilidad y accesibilidad.

## 2. Tokens mínimos
```yaml
colors:
  primary: ""
  secondary: ""
  success: ""
  warning: ""
  danger: ""
  text: ""
  background: ""
typography:
  font_family: ""
  scale: ["xs", "sm", "base", "lg", "xl"]
spacing:
  scale: ["4", "8", "12", "16", "24", "32"]
radius:
  default: ""
```

## 3. Componentes mínimos
| Componente | Estados obligatorios | Reglas |
|---|---|---|
| Button | default, hover, focus, disabled, loading, destructive | Focus visible. |
| Input | empty, filled, focus, invalid, disabled | Label visible. |
| Modal | open, confirm, cancel, destructive | Escape/cierre definido. |
| Table | loading, empty, error, paginated | Alternativa responsive. |
| Alert | info, success, warning, error | No depender solo del color. |
| Toast | success, warning, error | No ocultar errores críticos. |

## 4. Criterios de rechazo
- Componentes sin estados.
- Tokens no documentados.
- Patrones inaccesibles repetidos.
