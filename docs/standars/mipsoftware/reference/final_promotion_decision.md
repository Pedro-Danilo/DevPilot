---
title: Decisión final de promoción — MIPSoftware
doc_id: MIPS-REF-001
doc_type: reference
version: 0.1.0
status: reviewed
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
related_documents:
- MIPS-DOC-016
- MIPS-DOC-002
- MIPS-DOC-014
---

# Decisión final de promoción — MIPSoftware

## 1. Decisión

**MIPSoftware queda promovido como estándar profesional de trabajo del emprendimiento en estado `reviewed`, con veredicto operativo `approved with exceptions`.**

Esto significa que el modelo puede usarse desde ahora para iniciar proyectos reales, diseñar DevPilot Local y exigir evidencia mínima antes de implementación, release y operación. Sin embargo, no debe declararse todavía como estándar industrial final `approved v1.0.0` hasta validar sus plantillas, checklists y schemas en un proyecto aplicado completo.

## 2. Alcance aprobado

MIPSoftware gobierna el ciclo de vida completo de aplicaciones profesionales de software:

- producto y negocio;
- stakeholders;
- requerimientos;
- arquitectura;
- dominio, datos e integraciones;
- UX/UI y accesibilidad;
- calidad, testing y verificación;
- seguridad, privacidad y compliance;
- DevOps, CI/CD, release y supply chain;
- observabilidad, operación, SRE e incidentes;
- mantenimiento, evolución, deuda técnica y retiro;
- activación formal de MIASI para sistemas con IA.

## 3. Excepciones no bloqueantes

| ID | Excepción | Severidad | Justificación | Condición de cierre |
|---|---|---:|---|---|
| EXC-001 | Los schemas cubren artefactos críticos, pero no todas las plantillas. | Media | No bloquea uso manual ni diseño de DevPilot. | Crear schemas adicionales durante DevPilot MVP. |
| EXC-002 | No existen validadores CLI ejecutables. | Media | La documentación está lista para ser automatizada, pero aún no ejecuta validación. | Implementar `devpilot validate-*`. |
| EXC-003 | Las carpetas `tutorials/`, `how_to/` y `explanations/` están preparadas, pero no pobladas completamente. | Baja | No bloquea el estándar normativo. | Agregar guías conforme se use el modelo. |
| EXC-004 | No se ha aplicado aún sobre un proyecto real end-to-end. | Media | El modelo es coherente, pero falta validación empírica. | Usar en DevPilot Local. |
| EXC-005 | La adaptación legal/regulatoria depende de país, sector y cliente. | Media | No debe congelarse en un estándar universal. | Crear anexos por jurisdicción/proyecto. |

## 4. Próximo hito

El siguiente hito recomendado es iniciar **DevPilot Local** como primera aplicación del estándar. Ese proyecto debe validar:

- `checklist_pre_code.md`;
- `requirements_specification.md`;
- `architecture_document.md`;
- `test_strategy.md`;
- `security_threat_model.md`;
- `release_plan.md`;
- `production_readiness.schema.json`;
- activación de MIASI cuando aplique.

## 5. Regla de promoción futura a approved v1.0.0

MIPSoftware podrá promoverse a `approved v1.0.0` cuando:

1. se use en al menos un proyecto aplicado completo;
2. DevPilot Local valide al menos cinco artefactos mediante CLI;
3. se ejecuten checklists de pre-code, requirements, architecture, testing, security, release y production readiness;
4. se corrijan las excepciones abiertas o se acepten formalmente con waiver;
5. se documente una auditoría posterior al uso real.
