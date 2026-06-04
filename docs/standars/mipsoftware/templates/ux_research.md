---
title: Plantilla — UX Research
doc_id: MIPS-TPL-UX-RESEARCH
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
related_document: 07_ux_ui_accesibilidad.md
---

# Plantilla — UX Research

## 1. Propósito
Documentar investigación UX mínima para evitar diseñar desde suposiciones internas.

## 2. Cuándo usarla
Antes de definir flujos, wireframes o backlog de funcionalidades visibles.

## 3. Campos obligatorios
| Campo | Descripción |
|---|---|
| Contexto del producto | Problema, mercado, dominio, restricciones. |
| Usuarios/segmentos | Quién usa o se afecta por el sistema. |
| Objetivos de investigación | Qué se necesita aprender. |
| Método | Entrevista, observación, análisis documental, encuesta, test rápido. |
| Hallazgos | Evidencias, patrones, dudas. |
| Pain points | Dolores o fricciones. |
| Oportunidades | Posibles mejoras o funcionalidades. |
| Riesgos | Suposiciones no validadas. |
| Decisiones | Qué cambia en producto/requerimientos. |

## 4. Ejemplo completo
```yaml
research_id: "UXR-001"
product: "DevPilot Local"
objective: "Entender cómo un desarrollador organiza tareas antes de modificar un repo."
users:
  - "desarrollador independiente"
methods:
  - "autoobservación guiada"
  - "revisión de flujos actuales"
findings:
  - "Las tareas técnicas se dispersan entre chats, notas y commits."
pain_points:
  - "No hay trazabilidad entre requerimiento, cambio y prueba."
opportunities:
  - "Crear flujo init-project con artefactos mínimos."
decision: "Priorizar project intake y requirements readiness."
```

## 5. Criterios de revisión
- El hallazgo debe estar conectado con evidencia.
- Los usuarios deben ser específicos.
- Las oportunidades deben conectar con requerimientos.

## 6. Criterios de rechazo
- Hallazgos inventados sin evidencia.
- Usuarios genéricos como "todos".
- Investigación usada para justificar una solución ya decidida.

## 7. Relación con quality gates
Bloquea avance a wireframes si no hay usuario, problema o flujo mínimo.
