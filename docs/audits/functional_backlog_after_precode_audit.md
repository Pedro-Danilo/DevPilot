---
title: "Auditoría de backlog funcional posterior a pre-code"
doc_id: "DEVPL-AUD-FUNC-BACKLOG-001"
status: "reviewed"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "POST-PRECODE"
updated: "2026-06-05"
source_file: "docs/functional_backlog_after_precode.md"
---

# Auditoría de `functional_backlog_after_precode.md`

## 1. Veredicto

El backlog funcional original era correcto como orientación inicial, pero resultaba insuficiente como backlog ejecutable para iniciar codificación progresiva. Identificaba los primeros bloques funcionales, pero no detallaba dependencias, contratos, comandos, pruebas, criterios BLOCK, Definition of Done, prompts operativos ni trazabilidad suficiente hacia MIPSoftware/MIASI.

## 2. Hallazgos

| ID | Severidad | Hallazgo | Impacto | Corrección aplicada |
|---|---:|---|---|---|
| AUD-FB-001 | Alta | El backlog original era demasiado agregado para ejecutar sprints sin reinterpretación. | Riesgo de empezar a codificar con ambigüedad. | Se expandió a backlog por releases, sprints, tareas, comandos, pruebas y DoD. |
| AUD-FB-002 | Alta | No diferenciaba suficientemente MVP, MVP+ y post-MVP a nivel funcional ejecutable. | Riesgo de implementar agentes/Git/patches antes de gates básicos. | Se añadió secuencia obligatoria por incrementos. |
| AUD-FB-003 | Media | No incluía prompts operativos por sprint. | Dificulta continuar el trabajo en nuevos hilos o sesiones. | Se agregó prompt base por sprint. |
| AUD-FB-004 | Media | No explicitaba entregables de código, pruebas, reportes y trazas por sprint. | Criterios de cierre incompletos. | Se añadieron entregables verificables. |
| AUD-FB-005 | Media | No incluía suficientes controles MIASI antes de agentes. | Riesgo de habilitar agentes sin política/evaluación. | Se agregaron sprints de Policy Engine, registries, evaluación y observabilidad antes de agentes avanzados. |
| AUD-FB-006 | Baja | No dejaba claro cómo tratar cambios futuros en `docs/`. | Riesgo de tratar la baseline documental como inmutable. | Se añadió política de evolución controlada del contrato documental. |

## 3. Decisión

Se reemplazó `docs/functional_backlog_after_precode.md` por una versión 1.1.0 más ejecutable, preparada para transformarse en sprints, prompts o tareas de implementación.

## 4. Estado recomendado

```yaml
status: reviewed
approval: ready_for_owner_approval
```

La nueva versión debe ser revisada por el owner antes de promoverse a `approved`, porque reorganiza y expande la ruta funcional del proyecto.