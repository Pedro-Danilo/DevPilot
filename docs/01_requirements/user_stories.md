---
title: "User Stories — DevPilot Local"
doc_id: "DEVPL-REQ-002"
status: "reviewed"
version: "0.2.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-02"
updated: "2026-06-02"
approval: "ready_for_owner_approval"
source_baseline: "SPRINT-PRECODE-01 product baseline approved"
---
# User Stories — DevPilot Local

## 1. Propósito

Este documento traduce los objetivos de DevPilot Local en historias de usuario verificables. Las historias cubren el MVP, el MVP+ y la visión post-MVP, pero priorizan aquello necesario para construir primero un core local-first, testeable y seguro.

## 2. Roles considerados

| Rol | Descripción |
|---|---|
| Owner/Developer | Usuario principal que crea, valida y evoluciona proyectos propios. |
| Software Architect | Rol responsable de arquitectura, ADRs y decisiones técnicas. |
| Requirements Reviewer | Rol que revisa trazabilidad y calidad de requisitos. |
| Security Reviewer | Rol que revisa threat model, secretos, permisos y riesgos. |
| QA/Test Planner | Rol que define estrategia, casos y gates de pruebas. |
| Operator | Rol que revisa runbook, operación local, reportes y fallos. |
| Agent Supervisor | Rol humano que aprueba o rechaza acciones sugeridas por agentes. |
| Future Client | Beneficiario indirecto de procesos más profesionales y trazables. |

## 3. Historias MVP

| ID | Historia | Prioridad | Requisitos relacionados | Criterio de aceptación resumido |
|---|---|---:|---|---|
| US-MVP-001 | Como Owner/Developer, quiero ejecutar DevPilot desde CLI local para validar proyectos sin depender de nube o API keys. | Alta | FR-MVP-001, FR-MVP-008 | CLI responde versión y comandos base offline. |
| US-MVP-002 | Como Owner/Developer, quiero validar artefactos pre-code para no empezar a codificar sin evidencia mínima. | Alta | FR-MVP-002, FR-MVP-012 | `readiness-check` produce PASS/FAIL por artefacto. |
| US-MVP-003 | Como Requirements Reviewer, quiero validar frontmatter y estructura de documentos para asegurar consistencia documental. | Alta | FR-MVP-005, FR-MVP-006 | Documento incompleto genera error accionable. |
| US-MVP-004 | Como Owner/Developer, quiero saber si MIASI aplica para activar controles de IA/agentes cuando corresponda. | Alta | FR-MVP-004 | `miasi-required` explica la activación. |
| US-MVP-005 | Como QA/Test Planner, quiero que los gates generen reportes JSON/Markdown para usarlos como evidencia. | Alta | FR-MVP-003, FR-MVP-010 | Se generan reportes en `outputs/reports/`. |
| US-MVP-006 | Como Security Reviewer, quiero que el MVP no ejecute acciones destructivas por defecto para evitar daño sobre archivos o repos. | Alta | FR-MVP-009, NFR-004 | Comandos de cambio futuro exigen dry-run y aprobación. |
| US-MVP-007 | Como Owner/Developer, quiero validar el checklist pre-code para saber si puedo pasar a implementación. | Alta | FR-MVP-007 | Checklist produce PASS/FAIL con evidencia. |
| US-MVP-008 | Como Requirements Reviewer, quiero mantener trazabilidad producto → requisito → prueba para evitar requisitos huérfanos. | Alta | FR-MVP-015, NFR-007 | Matriz conecta objetivos, requisitos, criterios y tests. |
| US-MVP-009 | Como Operator, quiero mensajes de error claros para corregir fallos sin revisar el código de DevPilot. | Media | FR-MVP-011, NFR-010 | Error indica archivo, campo y acción sugerida. |

## 4. Historias MVP+

| ID | Historia | Prioridad | Requisitos relacionados | Criterio de aceptación resumido |
|---|---|---:|---|---|
| US-PLUS-001 | Como Owner/Developer, quiero registrar un workspace DevPilot para gestionar un proyecto como unidad operativa. | Alta | FR-PLUS-001 | Existe descriptor de workspace y reportes asociados. |
| US-PLUS-002 | Como Owner/Developer, quiero consultar estado Git del repo para vincular gates con cambios reales. | Alta | FR-PLUS-002 | Reporte muestra branch, status y último commit. |
| US-PLUS-003 | Como Software Architect, quiero analizar estructura de repos para detectar brechas de arquitectura, docs y tests. | Alta | FR-PLUS-003 | Repo report identifica módulos, docs, tests y riesgos. |
| US-PLUS-004 | Como Code Reviewer, quiero revisar diffs y patches en dry-run antes de aplicarlos. | Alta | FR-PLUS-004, FR-PLUS-005 | Patch review no modifica archivos y produce hallazgos. |
| US-PLUS-005 | Como Code Reviewer, quiero recibir sugerencias de code review con severidad y evidencia. | Alta | FR-PLUS-006 | Hallazgos incluyen archivo, regla y recomendación. |
| US-PLUS-006 | Como Software Architect, quiero propuestas de refactor seguro para reducir deuda sin introducir regresiones. | Media | FR-PLUS-007 | Plan de refactor incluye pruebas y rollback. |
| US-PLUS-007 | Como Owner/Developer, quiero validar entorno virtual de desarrollo para reproducir builds y pruebas. | Alta | FR-PLUS-008 | Reporte detecta Python, `.venv`, dependencias y comandos. |
| US-PLUS-008 | Como Agent Supervisor, quiero que los agentes trabajen en modo recomendación antes de ejecutar cambios. | Alta | FR-PLUS-010 | Agente entrega propuesta, no modificación directa. |
| US-PLUS-009 | Como Operator, quiero trazas JSONL para auditar acciones, gates y recomendaciones. | Media | FR-PLUS-009 | Eventos quedan en `outputs/traces/events.jsonl`. |
| US-PLUS-010 | Como Release Reviewer, quiero preparar releases con evidencia de calidad y rollback. | Media | FR-PLUS-011 | Release report incluye gates y rollback. |

## 5. Historias post-MVP

| ID | Historia | Prioridad futura | Requisitos relacionados | Criterio futuro |
|---|---|---:|---|---|
| US-POST-001 | Como Owner/Developer, quiero una app desktop para visualizar workspaces, gates, documentos y aprobaciones. | Alta | FR-POST-001, FR-POST-003 | Desktop consume DevPilot Core. |
| US-POST-002 | Como Owner/Developer, quiero una app web para dashboards y colaboración futura. | Media | FR-POST-002 | Web requiere auth, seguridad y operación reforzada. |
| US-POST-003 | Como Agent Supervisor, quiero agentes especializados por fase SDLC. | Alta | FR-POST-004 | Cada agente tiene card, policy, eval y trazas. |
| US-POST-004 | Como Owner/Developer, quiero integración opcional con repos remotos y CI/CD. | Media | FR-POST-005 | Integración opcional y no obligatoria para uso local. |

## 6. Criterios de calidad de historias

| Criterio | PASS | FAIL |
|---|---|---|
| Valor explícito | La historia indica por qué importa. | Solo describe una tarea técnica sin valor. |
| Actor identificado | Tiene rol claro. | Actor ambiguo. |
| Relación con requisitos | Apunta a FR/NFR. | No tiene trazabilidad. |
| Aceptación verificable | Tiene evidencia observable. | No puede probarse. |
| Riesgo controlado | Respeta local-first, dry-run y MIASI cuando aplica. | Omite controles. |

## 7. Estado

```yaml
user_stories_status: reviewed
ready_for_owner_approval: true
```
