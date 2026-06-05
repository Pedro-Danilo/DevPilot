---
title: Plantilla — Plan de migración
doc_id: MIPS-TPL-MIGRATION-PLAN
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model/templates
created: '2026-05-31'
updated: '2026-05-31'
---

# Plantilla — Plan de migración

## 1. Identificación
- Migration ID:
- Fecha:
- Autor:
- Ambiente objetivo:
- Relacionada con requerimiento/ADR:

## 2. Descripción
- Objetivo:
- Tipo: schema / data / index / constraint / destructive / seed
- Riesgo: bajo / medio / alto / crítico

## 3. Cambios
| Objeto | Cambio | Breaking | Reversible |
|---|---|---:|---:|
| | | | |

## 4. Plan de ejecución
1. Backup/verificación previa.
2. Aplicar migración en entorno no productivo.
3. Ejecutar pruebas.
4. Aprobar ejecución.
5. Aplicar en objetivo.
6. Verificar postcondiciones.

## 5. Rollback
- ¿Reversible?: Sí/No
- Pasos rollback:
- Límites:
- Backup requerido:

## 6. Validación
| Check | PASS/FAIL | Evidencia |
|---|---|---|
| Tests pasan | | |
| Datos consistentes | | |
| API compatible | | |

## 7. Aprobaciones
| Rol | Nombre | Fecha | Decisión |
|---|---|---|---|
| | | | |
