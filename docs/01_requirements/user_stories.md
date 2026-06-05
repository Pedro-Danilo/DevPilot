---
title: "User Stories — DevPilot Local"
doc_id: "DEVPL-REQ-002"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-02"
updated: "2026-06-02"
approval: "approved_by_owner_direction"
source_baseline: "SPRINT-PRECODE-01 product baseline approved"
change_policy: "controlled_changes_allowed_until_precode_baseline"
---
# User Stories — DevPilot Local

## 1. Propósito

Este documento traduce los objetivos de DevPilot Local en historias de usuario verificables. Las historias cubren MVP, MVP+ y post-MVP, con énfasis en construir primero un core local-first, testeable, seguro y agent-assisted de forma controlada.

## 2. Roles considerados

| Rol | Descripción |
|---|---|
| Owner/Developer | Usuario principal que crea, valida y evoluciona proyectos propios. |
| Software Architect | Rol responsable de arquitectura, C4, ADRs y decisiones técnicas. |
| Requirements Reviewer | Rol que revisa trazabilidad y calidad de requisitos. |
| Security Reviewer | Rol que revisa threat model, secretos, permisos y riesgos. |
| QA/Test Planner | Rol que define estrategia, casos y gates de pruebas. |
| Operator | Rol que revisa runbook, operación local, reportes y fallos. |
| Agent Supervisor | Rol humano que aprueba o rechaza acciones sugeridas por agentes. |
| PreCode Documentation Agent | Agente controlado que propone borradores y mejoras documentales. |
| Documentation Audit Agent | Agente controlado que audita brechas documentales y recomienda correcciones. |
| Future Client | Beneficiario indirecto de procesos más profesionales y trazables. |

## 3. Historias MVP

| ID | Historia | Prioridad | Requisitos relacionados | Criterio de aceptación resumido |
|---|---|---:|---|---|
| US-MVP-001 | Como Owner/Developer, quiero ejecutar DevPilot desde CLI local para validar proyectos sin depender de nube o API keys. | Alta | FR-MVP-001, FR-MVP-009 | CLI responde versión y comandos base offline. |
| US-MVP-002 | Como Owner/Developer, quiero registrar o detectar un workspace para gestionar un proyecto como unidad operativa. | Alta | FR-MVP-002 | El workspace tiene raíz, docs, outputs y metadata mínima. |
| US-MVP-003 | Como Owner/Developer, quiero validar artefactos pre-code para no empezar a codificar sin evidencia mínima. | Alta | FR-MVP-003, FR-MVP-006 | `readiness-check` produce PASS/FAIL por artefacto. |
| US-MVP-004 | Como Requirements Reviewer, quiero validar frontmatter y estructura de documentos para asegurar consistencia documental. | Alta | FR-MVP-004, FR-MVP-005 | Documento incompleto genera error accionable. |
| US-MVP-005 | Como Owner/Developer, quiero saber si MIASI aplica para activar controles de IA/agentes cuando corresponda. | Alta | FR-MVP-007 | `miasi-required` explica la activación. |
| US-MVP-006 | Como QA/Test Planner, quiero que los gates generen reportes JSON/Markdown para usarlos como evidencia. | Alta | FR-MVP-008, FR-MVP-015 | Se generan reportes en `outputs/reports/`. |
| US-MVP-007 | Como Security Reviewer, quiero que el MVP no ejecute acciones destructivas por defecto para evitar daño sobre archivos o repos. | Alta | FR-MVP-010, NFR-004 | Comandos de cambio futuro exigen dry-run y aprobación. |
| US-MVP-008 | Como Owner/Developer, quiero validar el checklist pre-code para saber si puedo pasar a implementación. | Alta | FR-MVP-006 | Checklist produce PASS/FAIL con evidencia. |
| US-MVP-009 | Como Requirements Reviewer, quiero mantener trazabilidad producto → requisito → prueba para evitar requisitos huérfanos. | Alta | FR-MVP-012 | Matriz conecta objetivos, requisitos, criterios y tests. |
| US-MVP-010 | Como Owner/Developer, quiero que un agente documental me ayude a construir documentos pre-code desde una idea inicial. | Alta | FR-MVP-013, FR-MVP-016 | El agente produce borradores en dry-run y nunca aprueba por sí solo. |
| US-MVP-011 | Como Owner/Developer, quiero que un agente auditor detecte brechas en la documentación pre-code. | Alta | FR-MVP-014, FR-MVP-016 | El agente produce hallazgos con severidad, evidencia y recomendación. |
| US-MVP-012 | Como Operator, quiero mensajes de error claros para corregir fallos sin revisar el código de DevPilot. | Media | FR-MVP-011, NFR-010 | Error indica archivo, campo y acción sugerida. |

## 4. Historias MVP+

| ID | Historia | Prioridad | Requisitos relacionados | Criterio de aceptación resumido |
|---|---|---:|---|---|
| US-PLUS-001 | Como Owner/Developer, quiero crear `.devpilot/project.yaml` para persistir la identidad del workspace. | Alta | FR-PLUS-001 | Existe descriptor válido y auditable. |
| US-PLUS-002 | Como Owner/Developer, quiero consultar estado Git del repo para vincular gates con cambios reales. | Alta | FR-PLUS-002 | Reporte muestra branch, status y último commit. |
| US-PLUS-003 | Como Software Architect, quiero analizar estructura de repos para detectar brechas de arquitectura, docs y tests. | Alta | FR-PLUS-003 | Reporte identifica módulos, docs, tests y riesgos. |
| US-PLUS-004 | Como Owner/Developer, quiero validar el entorno virtual para reproducir desarrollo y pruebas. | Alta | FR-PLUS-004 | Reporte muestra Python, venv, dependencias y comandos. |
| US-PLUS-005 | Como Agent Supervisor, quiero revisar patches en dry-run antes de aplicarlos. | Alta | FR-PLUS-005, FR-PLUS-010 | Patch reporta impacto, riesgos y aprobación requerida. |
| US-PLUS-006 | Como Code Reviewer, quiero recibir revisión de código asistida con evidencia. | Alta | FR-PLUS-006 | Hallazgos con severidad, archivo, línea si aplica y recomendación. |
| US-PLUS-007 | Como Developer, quiero planes de refactor seguro que incluyan pruebas y rollback. | Media | FR-PLUS-007 | Refactor plan no modifica código automáticamente. |
| US-PLUS-008 | Como Agent Supervisor, quiero habilitar agentes especializados con cards, policies, evals y trazas. | Alta | FR-PLUS-008, FR-PLUS-010 | Agentes no ejecutan acciones sensibles sin aprobación. |
| US-PLUS-009 | Como Operator, quiero trazas JSONL para auditar ejecuciones y decisiones. | Media | FR-PLUS-009 | Eventos incluyen actor, acción, resultado y correlación. |

## 5. Historias post-MVP

| ID | Historia | Prioridad | Requisitos relacionados | Criterio de aceptación direccional |
|---|---|---:|---|---|
| US-POST-001 | Como Owner/Developer, quiero una app de escritorio para navegar workspaces, gates, riesgos y reportes. | Alta | FR-POST-001, FR-POST-003 | Desktop consume DevPilot Core sin duplicar lógica. |
| US-POST-002 | Como Owner/Developer, quiero una interfaz web para dashboards, colaboración futura y acceso controlado. | Media | FR-POST-002, FR-POST-003 | Web tiene auth, permisos, logs y threat model. |
| US-POST-003 | Como Agent Supervisor, quiero agentes multirol más avanzados para SDLC completo. | Media | FR-POST-004 | Multiagentes cumplen MIASI. |
| US-POST-004 | Como Release Manager, quiero asistencia para releases, despliegues y rollback. | Media | FR-POST-005 | Release gate genera evidencia y plan de rollback. |

## 6. Estado

```yaml
user_stories_status: approved
ready_for_architecture_sprint: true
```
