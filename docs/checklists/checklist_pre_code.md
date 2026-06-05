---
title: "Checklist Pre-Code — DevPilot Local"
doc_id: "DEVPL-CHK-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
baseline_role: "precode_gate"
---

# Checklist Pre-Code — DevPilot Local

## 1. Propósito

Este checklist consolida el gate pre-code de **DevPilot Local / Agent-assisted SDLC personal**. Su función es confirmar que el proyecto tiene evidencia mínima suficiente para pasar desde planeación documental hacia el primer sprint funcional fuerte.

La regla central es:

> DevPilot Local no debe iniciar implementación funcional fuerte si producto, requerimientos, arquitectura, seguridad, calidad, operación y MIASI no tienen baseline aprobada y trazabilidad mínima.

## 2. Checklist de aprobación por bloque

| Bloque | Artefacto principal | Obligatorio | Estado | Evidencia |
|---|---|---:|---|---|
| Producto | `docs/00_product/product_vision.md` | Sí | PASS | Visión, problema, valor, MVP/MVP+ y roadmap aprobados. |
| Producto | `docs/00_product/business_case.md` | Sí | PASS | Justificación de utilidad, costo, riesgo y continuidad aprobada. |
| Producto | `docs/00_product/mvp_scope.md` | Sí | PASS | Alcance MVP, MVP+ y fuera de alcance aprobados. |
| Requerimientos | `docs/01_requirements/requirements_specification.md` | Sí | PASS | RF/RNF, constraints, agentes y trazabilidad aprobados. |
| Requerimientos | `docs/01_requirements/user_stories.md` | Sí | PASS | Historias para MVP, MVP+ y post-MVP aprobadas. |
| Requerimientos | `docs/01_requirements/use_cases.md` | Sí | PASS | Casos de uso baseline aprobados. |
| Requerimientos | `docs/01_requirements/acceptance_criteria.md` | Sí | PASS | Criterios Given/When/Then y gates aprobados. |
| Requerimientos | `docs/01_requirements/traceability_matrix.md` | Sí | PASS | Trazabilidad producto → requisito → prueba aprobada. |
| Arquitectura | `docs/02_architecture/architecture_document.md` | Sí | PASS | Arquitectura MVP/MVP+/post-MVP aprobada. |
| Arquitectura | `docs/02_architecture/c4_context.md` | Sí | PASS | Vista C4 contexto aprobada. |
| Arquitectura | `docs/02_architecture/c4_container.md` | Sí | PASS | Vista C4 contenedores aprobada. |
| Arquitectura | `docs/02_architecture/adrs/` | Sí | PASS | ADR-0001 a ADR-0009 aceptadas. |
| Seguridad | `docs/03_security/security_threat_model.md` | Sí | PASS | Threat model aprobado. |
| Privacidad | `docs/03_security/privacy_assessment.md` | Sí | PASS | Privacy assessment aprobado. |
| Calidad | `docs/04_quality/test_strategy.md` | Sí | PASS | Estrategia de pruebas y quality gates aprobados. |
| Operación | `docs/05_operations/observability_plan.md` | Sí | PASS | Observabilidad local/AgentOps aprobada. |
| Operación | `docs/05_operations/runbook.md` | Sí | PASS | Runbook operativo aprobado. |
| MIASI | `docs/06_miasi/agent_card.md` | Sí | PASS | Agentes previstos, autonomía y límites aprobados. |
| MIASI | `docs/06_miasi/tool_card.md` | Sí | PASS | Herramientas, riesgos y contratos aprobados. |
| MIASI | `docs/06_miasi/policy_card.md` | Sí | PASS | Policy-as-code conceptual aprobada. |
| MIASI | `docs/06_miasi/eval_card.md` | Sí | PASS | Evaluación agentic aprobada. |
| MIASI | `docs/06_miasi/human_approval_card.md` | Sí | PASS | Aprobación humana aprobada. |
| MIASI | `docs/06_miasi/observability_card.md` | Sí | PASS | Observabilidad AgentOps aprobada. |

## 3. Checklist de criterios transversales

| Criterio | Obligatorio | Resultado | Evidencia |
|---|---:|---|---|
| MIPSoftware aplicado como estándar general | Sí | PASS | `docs/standards/mipsoftware/` + documentos pre-code. |
| MIASI activado como extensión inteligente | Sí | PASS | `docs/06_miasi/` aprobado. |
| Local-first híbrido definido | Sí | PASS | Producto, requerimientos y arquitectura. |
| API keys opcionales y controladas | Sí | PASS | Arquitectura, seguridad, MIASI. |
| CostGuard definido | Sí | PASS | Arquitectura, seguridad, operación, MIASI. |
| SecretGuard definido | Sí | PASS | Seguridad, operación, MIASI. |
| Dry-run por defecto | Sí | PASS | Seguridad, MIASI, runbook. |
| Human approval definido | Sí | PASS | MIASI y seguridad. |
| Workspaces definidos como unidad operativa | Sí | PASS | Producto, requerimientos, arquitectura. |
| Git y repos reales contemplados | Sí | PASS | Requerimientos y arquitectura para MVP+. |
| Persistencia local definida | Sí | PASS | Arquitectura y operación. |
| Reportes JSON/Markdown y trazas JSONL previstas | Sí | PASS | Arquitectura, operación y MIASI. |
| Agentes desde MVP definidos | Sí | PASS | Requerimientos, arquitectura y MIASI. |
| Desktop/Web como compromiso evolutivo | Sí | PASS | Producto y arquitectura. |
| Bloqueos de seguridad documentados | Sí | PASS | Seguridad y MIASI. |
| Trazabilidad producto → requisito → prueba | Sí | PASS | `traceability_matrix.md` y `test_strategy.md`. |

## 4. Criterios BLOCK antes del primer sprint funcional

El avance a implementación funcional fuerte debe bloquearse si aparece cualquiera de estas condiciones:

| ID | Condición bloqueante | Estado actual |
|---|---|---|
| BLOCK-001 | Falta un documento obligatorio pre-code. | No aplica. |
| BLOCK-002 | Algún bloque 00–06 está por debajo de `approved`. | No aplica tras SPRINT-PRECODE-07. |
| BLOCK-003 | MIASI no está activado. | No aplica. |
| BLOCK-004 | No hay política de dry-run. | No aplica. |
| BLOCK-005 | No hay criterios de seguridad para herramientas/agentes. | No aplica. |
| BLOCK-006 | No hay trazabilidad mínima hacia pruebas. | No aplica. |
| BLOCK-007 | No hay procedimiento de aplicación de patches. | Cubierto a nivel documental; implementación pendiente. |
| BLOCK-008 | No hay runbook operativo. | No aplica. |

## 5. Veredicto

```text
Checklist pre-code: PASS
Baseline documental: APPROVED
Recomendación: habilitar primer sprint funcional fuerte con alcance controlado
```

## 6. Nota de control

Este checklist aprueba la **baseline documental**, no la implementación. El primer sprint funcional debe convertir esta evidencia en validadores, comandos CLI, reportes ejecutables, schemas y pruebas automatizadas.
