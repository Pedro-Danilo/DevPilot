---
title: "Requirements Specification — DevPilot Local"
doc_id: "DEVPL-REQ-001"
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
# Requirements Specification — DevPilot Local

## 1. Propósito

Este documento convierte la baseline aprobada de producto de DevPilot Local en requerimientos verificables, priorizados y trazables. Su objetivo es impedir que la plataforma avance a desarrollo funcional fuerte sin una especificación clara de qué debe hacer, bajo qué restricciones, con qué evidencia y con qué relación con MIPSoftware y MIASI.

## 2. Fuente de verdad del sprint

Este documento toma como fuente directa los artefactos aprobados en `docs/00_product/`:

| Fuente | Uso en requisitos |
|---|---|
| `product_vision.md` | Define visión, problema, plataforma local-first y compromiso CLI → desktop → web. |
| `business_case.md` | Justifica MVP, MVP+ y valor estratégico. |
| `stakeholder_map.md` | Define actores humanos, técnicos, normativos y futuros. |
| `mvp_scope.md` | Delimita MVP, MVP+ y out of scope. |
| `product_roadmap.md` | Ordena fases de evolución. |
| `sprint_precode_01_approval_audit.md` | Aprueba la baseline de producto y activa SPRINT-PRECODE-02. |

## 3. Alcance de requerimientos

Los requerimientos se agrupan en tres niveles:

| Nivel | Descripción | Estado esperado |
|---|---|---|
| MVP | CLI local, validadores documentales, readiness, MIASI detection y reportes. | Implementable en los primeros sprints funcionales. |
| MVP+ | Git, repo analysis, patch review, code review dry-run, safe refactor, workspace manager inicial y agentes controlados. | Diseñable desde ahora, implementable después del core de validación. |
| Post-MVP | Desktop, web, dashboards, colaboración y agentes avanzados. | Requerimientos direccionales, sujetos a refinamiento futuro. |

## 4. Definiciones funcionales clave

| Concepto | Definición |
|---|---|
| Workspace | Unidad operativa gobernada por DevPilot. Representa un proyecto o repo gestionado con MIPSoftware/MIASI, documentos, políticas, reportes, gates, trazas y estado local. |
| Gate | Control verificable que produce PASS/FAIL/WARN y evidencia. |
| Artifact | Documento, reporte, checklist, schema, archivo de configuración, patch o salida generada por DevPilot. |
| Dry-run | Modo de ejecución que analiza y propone sin modificar archivos, repos o entornos. |
| Agent-assisted | Capacidad en la que un agente de IA sugiere, evalúa o coordina, pero no sustituye los gates determinísticos ni la aprobación humana. |
| MVP+ | Expansión inmediata del MVP hacia repos reales, Git, patches, revisión, refactor y agentes controlados. |

## 5. Requerimientos funcionales del MVP

| ID | Requerimiento | Prioridad | Fuente | Criterio de aceptación resumido |
|---|---|---:|---|---|
| FR-MVP-001 | El sistema debe ejecutarse como CLI local desde el workspace del proyecto. | Alta | Product Vision | `python -m devpilot_core --version` responde versión. |
| FR-MVP-002 | El sistema debe validar existencia de artefactos mínimos pre-code. | Alta | MVP Scope | `readiness-check` reporta PASS/FAIL por artefacto. |
| FR-MVP-003 | El sistema debe generar reportes locales en JSON. | Alta | MVP Scope | Se crea reporte en `outputs/reports/`. |
| FR-MVP-004 | El sistema debe detectar si MIASI aplica al proyecto. | Alta | Product Vision | `miasi-required` devuelve `true` para DevPilot Local. |
| FR-MVP-005 | El sistema debe validar frontmatter YAML mínimo en documentos Markdown. | Alta | MIPSoftware | Documento sin `doc_id`, `status`, `version` u `owner` falla. |
| FR-MVP-006 | El sistema debe validar estructura mínima de artefactos MIPSoftware. | Alta | MIPSoftware | Cada artefacto obligatorio tiene secciones mínimas exigidas. |
| FR-MVP-007 | El sistema debe validar checklists pre-code. | Alta | MVP Scope | Checklist produce PASS/FAIL y evidencia requerida. |
| FR-MVP-008 | El sistema debe funcionar sin API keys reales ni servicios externos obligatorios. | Alta | Local-first | `pytest -q` pasa sin `.env` real. |
| FR-MVP-009 | El sistema debe evitar acciones destructivas por defecto. | Alta | Seguridad | Todo comando de modificación futura debe iniciar en dry-run. |
| FR-MVP-010 | El sistema debe producir salidas legibles para humanos y máquinas. | Media | Roadmap | JSON para automatización y Markdown para revisión. |
| FR-MVP-011 | El sistema debe registrar errores de validación de forma explícita. | Alta | Quality | Un artefacto inválido indica campo/sección faltante. |
| FR-MVP-012 | El sistema debe permitir validar una carpeta `docs/` como baseline pre-code. | Alta | Product Baseline | El proyecto puede pasar por gate pre-code completo. |
| FR-MVP-013 | El sistema debe conservar operación local-first. | Alta | Product Vision | No transmite archivos ni código fuera del equipo local. |
| FR-MVP-014 | El sistema debe declarar el estado de readiness del proyecto. | Alta | MVP Scope | Readiness devuelve `ready`, `blocked` o `needs_review`. |
| FR-MVP-015 | El sistema debe preparar la trazabilidad producto → requerimiento → prueba. | Alta | SPRINT-PRECODE-02 | La matriz de trazabilidad conecta objetivos con requisitos y tests. |

## 6. Requerimientos funcionales del MVP+

| ID | Requerimiento | Prioridad | Fuente | Criterio de aceptación resumido |
|---|---|---:|---|---|
| FR-PLUS-001 | El sistema debe reconocer y registrar workspaces DevPilot. | Alta | Workspaces | Existe `.devpilot/project.yaml` o descriptor equivalente. |
| FR-PLUS-002 | El sistema debe integrarse con Git en modo read-only inicial. | Alta | Product Vision | Reporta branch, status, cambios y último commit sin modificar repo. |
| FR-PLUS-003 | El sistema debe analizar estructura de repositorios reales. | Alta | MVP+ | Reporte de módulos, docs, tests, configuración y riesgos. |
| FR-PLUS-004 | El sistema debe generar reportes de diff. | Alta | Git integration | Resume archivos modificados, tipo de cambio y riesgo estimado. |
| FR-PLUS-005 | El sistema debe validar patches en dry-run. | Alta | Patch validation | Evalúa patch sin aplicarlo y produce PASS/FAIL/WARN. |
| FR-PLUS-006 | El sistema debe asistir revisión de código. | Alta | Code review | Reporte con hallazgos, severidad, recomendación y evidencia. |
| FR-PLUS-007 | El sistema debe proponer refactor seguro. | Media | Safe refactor | Genera plan reversible, pruebas esperadas y riesgos. |
| FR-PLUS-008 | El sistema debe validar entorno virtual de desarrollo. | Alta | Entorno | Detecta `.venv`, Python, dependencias y comandos base. |
| FR-PLUS-009 | El sistema debe registrar trazas locales JSONL. | Media | Observability | Eventos de validación y agentes quedan en `outputs/traces/`. |
| FR-PLUS-010 | El sistema debe permitir agentes controlados en modo recomendación. | Media | MIASI | Agentes no ejecutan cambios sin política y aprobación humana. |
| FR-PLUS-011 | El sistema debe preparar releases locales con evidencia. | Media | Roadmap | Reporte de readiness de release y rollback documentado. |
| FR-PLUS-012 | El sistema debe generar propuestas de ajustes documentales/técnicos. | Media | Platform vision | Ajustes se entregan como diff/patch revisable. |

## 7. Requerimientos direccionales post-MVP

| ID | Requerimiento | Prioridad | Fuente | Criterio de aceptación futuro |
|---|---|---:|---|---|
| FR-POST-001 | El sistema debe ofrecer interfaz desktop local. | Alta futura | Roadmap | Desktop consume DevPilot Core sin duplicar lógica. |
| FR-POST-002 | El sistema debe ofrecer interfaz web controlada. | Media futura | Roadmap | Web presenta dashboard y colaboración con seguridad reforzada. |
| FR-POST-003 | El sistema debe soportar dashboards visuales de workspaces. | Media futura | Workspaces | Vista de gates, riesgos, trazas y documentos por proyecto. |
| FR-POST-004 | El sistema debe soportar agentes especializados por fase SDLC. | Alta futura | MIASI | Agentes con cards, policies, evals y human approval. |
| FR-POST-005 | El sistema debe soportar integración opcional con repos remotos y CI/CD. | Media futura | DevOps | Integraciones opcionales, nunca obligatorias para core local. |

## 8. Requerimientos no funcionales

| ID | Atributo | Requerimiento medible | Umbral inicial |
|---|---|---|---|
| NFR-001 | Local-first | Debe funcionar sin red, nube, API keys ni servicios pagos. | 100% MVP offline. |
| NFR-002 | Portabilidad | Debe funcionar en Windows con Python local. | Windows + Python 3.10+. |
| NFR-003 | Testabilidad | Toda capacidad core debe tener pruebas herméticas. | `pytest -q` PASS. |
| NFR-004 | Seguridad | No debe ejecutar acciones destructivas por defecto. | Dry-run por defecto. |
| NFR-005 | Privacidad | No debe enviar código/documentos fuera del equipo local por defecto. | 0 transmisión externa en MVP. |
| NFR-006 | Observabilidad | Debe generar evidencia de validación. | JSON/Markdown en `outputs/`. |
| NFR-007 | Trazabilidad | Todo gate debe apuntar a artefacto, requisito y evidencia. | Matriz actualizada. |
| NFR-008 | Mantenibilidad | Core, CLI, validadores y reportes deben separarse. | Arquitectura modular. |
| NFR-009 | Extensibilidad | Debe permitir agregar validadores, agentes y UIs futuras. | Contratos internos claros. |
| NFR-010 | Usabilidad CLI | Errores y resultados deben ser entendibles. | Mensajes accionables. |
| NFR-011 | Rendimiento | Validaciones documentales deben ser rápidas en repos pequeños/medios. | < 5s en workspace pequeño. |
| NFR-012 | Reproducibilidad | Un mismo workspace debe producir resultados consistentes. | Ejecuciones repetibles. |

## 9. Restricciones

- No usar API keys reales en MVP.
- No usar servicios externos obligatorios.
- No modificar repositorios sin dry-run y aprobación explícita.
- No crear agentes ejecutores antes de aprobar MIASI operativo.
- No asumir una única UI; CLI, desktop y web deben compartir core.
- No tratar la app web como prioridad antes de validar core local y desktop.
- No publicar ni enviar código del usuario a terceros por defecto.

## 10. Supuestos

- El usuario principal trabaja en Windows y organiza proyectos bajo `D:\Projects`.
- DevPilot Local gestionará primero proyectos propios antes de proyectos de clientes.
- El MVP debe fortalecer disciplina de ingeniería antes de automatizar código.
- MIPSoftware y MIASI son estándares internos obligatorios para este proyecto.
- La interfaz CLI será la primera superficie estable y automatizable.

## 11. Quality gates de requerimientos

| Gate | Criterio PASS | Criterio FAIL/BLOCK |
|---|---|---|
| REQ-GATE-001 | Todo requerimiento crítico tiene criterio de aceptación. | Requerimiento crítico sin aceptación. |
| REQ-GATE-002 | Todo requerimiento tiene fuente en producto, MIPSoftware o MIASI. | Requerimiento sin fuente clara. |
| REQ-GATE-003 | Todo requisito MVP está asociado a al menos una prueba o evidencia futura. | Sin prueba/evidencia. |
| REQ-GATE-004 | Requerimientos agentic activan MIASI. | IA/agentes sin Agent/Tool/Policy/Eval cards. |
| REQ-GATE-005 | Workspaces quedan tratados como concepto central. | Workspace ausente de requisitos, casos de uso o trazabilidad. |

## 12. Estado

```yaml
requirements_baseline_status: reviewed
ready_for_owner_approval: true
next_step: review_and_approve_sprint_precode_02
```
