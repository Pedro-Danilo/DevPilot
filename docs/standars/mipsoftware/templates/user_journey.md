---
title: Plantilla — User Journey
doc_id: MIPS-TPL-USER-JOURNEY
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
related_document: 07_ux_ui_accesibilidad.md
---

# Plantilla — User Journey

## 1. Propósito
Documentar el camino del usuario para lograr un objetivo de valor.

## 2. Campos obligatorios
| Campo | Descripción |
|---|---|
| Persona/segmento | Usuario principal. |
| Objetivo | Resultado que busca. |
| Trigger | Qué inicia el flujo. |
| Etapas | Secuencia de actividades. |
| Acciones | Qué hace el usuario. |
| Touchpoints | Pantallas, canales, documentos o sistemas. |
| Pain points | Dificultades por etapa. |
| Oportunidades | Mejoras posibles. |
| Métricas | Indicadores de éxito. |
| Requerimientos vinculados | IDs de requerimientos. |

## 3. Ejemplo completo
| Etapa | Acción usuario | Touchpoint | Dolor | Oportunidad | Métrica |
|---|---|---|---|---|---|
| Inicio | Crear proyecto | CLI/Web | No sabe documentos mínimos | Wizard guiado | completion rate |
| Revisión | Validar readiness | Reporte | Falta evidencia | Checklist automático | readiness pass |
| Cierre | Generar backlog | Documento | Tareas poco claras | Backlog estructurado | defect leakage |

## 4. Criterios de revisión
- Cada etapa tiene objetivo y evidencia.
- Hay al menos un pain point real.
- Las métricas se pueden medir.

## 5. Criterios de rechazo
- Journey reducido a lista de pantallas.
- No hay relación con requerimientos.
- No incluye errores o caminos alternos.
