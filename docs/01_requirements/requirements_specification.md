---
title: "Requirements Specification — DevPilot Local"
doc_id: "DEVPL-REQ-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-02"
updated: "2026-06-02"
approval: "approved_by_owner_pending_commit"
approval_scope: "SPRINT-PRECODE-02 requirements baseline"
source_baseline: "SPRINT-PRECODE-01 product baseline approved"
change_policy: "controlled_changes_allowed_until_precode_baseline"
---
# Requirements Specification — DevPilot Local

## 1. Propósito

Este documento convierte la baseline aprobada de producto de DevPilot Local en requerimientos verificables, priorizados y trazables. Su propósito es impedir que la plataforma avance a desarrollo funcional fuerte sin una especificación clara sobre qué debe hacer, bajo qué restricciones, con qué evidencia, con qué relación con MIPSoftware y con qué activación de MIASI.

DevPilot Local no se concibe como una simple herramienta que revisa si existen archivos. El MVP debe iniciar con validadores determinísticos y agentes controlados para **construir, revisar y auditar documentación pre-code** a partir de una idea de proyecto. El sistema debe evolucionar hacia MVP+ para trabajar con repositorios reales, Git, entornos virtuales, validación de patches, revisión de código, refactor seguro y agentes especializados.

## 2. Fuente de verdad del sprint

| Fuente | Uso en requisitos |
|---|---|
| `docs/00_product/product_vision.md` | Define visión, problema, plataforma local-first, workspaces y compromiso CLI → desktop → web. |
| `docs/00_product/business_case.md` | Justifica el MVP acotado, el MVP+ y el valor estratégico de convertir MIPSoftware/MIASI en gates ejecutables. |
| `docs/00_product/stakeholder_map.md` | Define actores humanos, técnicos, normativos y futuros. |
| `docs/00_product/mvp_scope.md` | Delimita MVP, MVP+, post-MVP y fuera de alcance. |
| `docs/00_product/product_roadmap.md` | Ordena fases de evolución: CLI, validadores, agentes documentales, Git/repo, desktop y web. |
| `docs/00_product/sprint_precode_01_approval_audit.md` | Aprueba la baseline de producto y autoriza SPRINT-PRECODE-02. |

## 3. Alcance de requerimientos

| Nivel | Descripción | Estado esperado |
|---|---|---|
| MVP | CLI local, workspace mínimo, validadores documentales, agentes pre-code controlados, readiness, MIASI detection, reportes y trazabilidad. | Implementable en los primeros sprints funcionales. |
| MVP+ | Git, análisis de repos reales, validación de entorno virtual, patch review, code review dry-run, safe refactor, agentes especializados y trazas JSONL. | Diseñable desde ahora, implementable después del core de validación. |
| Post-MVP | Desktop, web, dashboards, colaboración futura, agentes multirol, despliegue controlado y operación ampliada. | Requerimientos direccionales, sujetos a refinamiento. |

## 4. Definiciones funcionales clave

| Concepto | Definición |
|---|---|
| Workspace | Unidad operativa gobernada por DevPilot. Representa un proyecto o repo gestionado con MIPSoftware/MIASI, documentos, políticas, reportes, gates, trazas y estado local. |
| Gate | Control verificable que produce PASS/FAIL/WARN/BLOCK y evidencia. |
| Artifact | Documento, reporte, checklist, schema, archivo de configuración, patch o salida generada por DevPilot. |
| Dry-run | Modo de ejecución que analiza y propone sin modificar archivos, repos o entornos. |
| Agent-assisted | Capacidad en la que un agente sugiere, evalúa, redacta o coordina, pero no sustituye los gates determinísticos ni la aprobación humana. |
| Documentation Agent | Agente controlado que ayuda a crear, completar o auditar documentos pre-code a partir de una idea, plantilla o baseline. |
| MVP+ | Expansión inmediata del MVP hacia repos reales, Git, patches, revisión, refactor y agentes controlados. |

## 5. Requerimientos funcionales del MVP

| ID | Requerimiento | Prioridad | Fuente | Criterio de aceptación resumido |
|---|---|---:|---|---|
| FR-MVP-001 | El sistema debe ejecutarse como CLI local desde el workspace del proyecto. | Alta | Product Vision | `python -m devpilot_core --version` responde versión. |
| FR-MVP-002 | El sistema debe detectar o registrar un workspace DevPilot mínimo. | Alta | Product Vision / Workspace | El workspace tiene raíz, `docs/`, `outputs/` y metadata mínima. |
| FR-MVP-003 | El sistema debe inventariar artefactos mínimos pre-code. | Alta | MVP Scope | `readiness-check` reporta PASS/FAIL por artefacto. |
| FR-MVP-004 | El sistema debe validar frontmatter YAML mínimo en documentos Markdown. | Alta | MIPSoftware | Documento sin `doc_id`, `status`, `version` u `owner` falla. |
| FR-MVP-005 | El sistema debe validar estructura mínima de artefactos MIPSoftware. | Alta | MIPSoftware | Cada artefacto obligatorio tiene secciones mínimas exigidas. |
| FR-MVP-006 | El sistema debe validar checklists pre-code. | Alta | MIPSoftware | Checklist produce PASS/FAIL/WARN/BLOCK con evidencia. |
| FR-MVP-007 | El sistema debe detectar si MIASI aplica al proyecto. | Alta | MIASI | `miasi-required` devuelve `true` para DevPilot Local. |
| FR-MVP-008 | El sistema debe generar reportes locales en JSON y Markdown. | Alta | Product Vision | Se crean reportes en `outputs/reports/`. |
| FR-MVP-009 | El sistema debe operar sin API keys obligatorias en MVP y preparar proveedores externos opcionales bajo CostGuard. | Alta | Local-first híbrido | Tests y CLI pasan sin `.env` con secretos; cualquier proveedor externo exige configuración explícita. |
| FR-MVP-010 | El sistema debe funcionar en dry-run por defecto. | Alta | Seguridad | Ningún comando modifica archivos críticos sin confirmación. |
| FR-MVP-011 | El sistema debe producir mensajes de error accionables. | Media | UX/Operación | Error indica archivo, campo, severidad y corrección sugerida. |
| FR-MVP-012 | El sistema debe construir una matriz de trazabilidad producto → requisito → prueba. | Alta | MIPSoftware | La matriz conecta objetivos, requisitos, historias, casos, criterios y tests. |
| FR-MVP-013 | El sistema debe incluir un agente documental controlado para ayudar a crear documentos pre-code a partir de una idea. | Alta | Product Vision / MIASI | El agente genera borradores en dry-run usando plantillas, sin llamadas externas obligatorias. |
| FR-MVP-014 | El sistema debe incluir un agente auditor controlado para revisar brechas documentales pre-code. | Alta | MIPSoftware / MIASI | El agente produce hallazgos con severidad, evidencia y recomendación, sin aprobar automáticamente. |
| FR-MVP-015 | El sistema debe registrar evidencias locales de validación. | Alta | Operación | Reportes y/o eventos quedan bajo `outputs/`. |
| FR-MVP-016 | El sistema debe separar claramente validación determinística y asistencia agentic. | Alta | MIASI | Los agentes recomiendan; los gates determinísticos deciden PASS/FAIL. |

## 6. Requerimientos funcionales MVP+

| ID | Requerimiento | Prioridad | Fuente | Criterio de aceptación resumido |
|---|---|---:|---|---|
| FR-PLUS-001 | El sistema debe crear/usar `.devpilot/project.yaml` como descriptor de workspace. | Alta | Workspace Vision | Descriptor válido y versionable según política. |
| FR-PLUS-002 | El sistema debe consultar estado Git en modo read-only. | Alta | Product Vision | Reporta branch, commit, dirty state y cambios sin modificar repo. |
| FR-PLUS-003 | El sistema debe analizar estructura de repos reales. | Alta | MVP+ | Detecta módulos, docs, tests, configuración, riesgos y brechas. |
| FR-PLUS-004 | El sistema debe validar entorno virtual de desarrollo. | Alta | User prompt / MVP+ | Reporta Python, venv, dependencias y comandos reproducibles. |
| FR-PLUS-005 | El sistema debe validar patches en dry-run. | Alta | MVP+ | Evalúa patch sin aplicarlo y genera reporte de impacto. |
| FR-PLUS-006 | El sistema debe realizar revisión de código asistida. | Alta | MVP+ | Produce hallazgos con evidencia, severidad y recomendación. |
| FR-PLUS-007 | El sistema debe proponer refactor seguro. | Media | MVP+ | Plan de refactor incluye tests, riesgo y rollback. |
| FR-PLUS-008 | El sistema debe incorporar agentes especializados controlados. | Alta | MIASI | RequirementsAgent, ArchitectureAgent, SecurityAgent, TestPlannerAgent y CodeReviewAgent operan con cards/policies/evals. |
| FR-PLUS-009 | El sistema debe registrar trazas JSONL de ejecuciones relevantes. | Media | Observabilidad | Eventos guardan acción, actor, resultado, severidad y correlación. |
| FR-PLUS-010 | El sistema debe exigir aprobación humana para acciones sensibles. | Alta | MIASI | Ninguna escritura, patch o refactor se ejecuta sin aprobación explícita. |

## 7. Requerimientos funcionales post-MVP

| ID | Requerimiento | Prioridad | Criterio de aceptación direccional |
|---|---|---:|---|
| FR-POST-001 | El sistema debe ofrecer app de escritorio sobre el mismo core. | Alta | Desktop UI consume DevPilot Core sin duplicar lógica. |
| FR-POST-002 | El sistema debe ofrecer interfaz web controlada. | Media | Web UI incluye auth, permisos, trazas y threat model propio. |
| FR-POST-003 | El sistema debe mostrar dashboards de workspaces, gates, riesgos y trazas. | Alta | Dashboard resume estado del ciclo de vida. |
| FR-POST-004 | El sistema debe incorporar agentes multirol y orquestación avanzada. | Media | Multiagentes sujetos a MIASI, evals, policies y human approval. |
| FR-POST-005 | El sistema debe asistir despliegues y releases controlados. | Media | Release checklist, rollback, evidencia y gates de seguridad. |

## 8. Requerimientos no funcionales

| ID | Requerimiento | Prioridad | Criterio de aceptación |
|---|---|---:|---|
| NFR-001 | Local-first por defecto. | Alta | Todos los comandos MVP funcionan sin red. |
| NFR-002 | Costo externo controlado. | Alta | Cero costo externo por defecto; cualquier costo externo exige presupuesto, proveedor configurado, consentimiento y trazabilidad. |
| NFR-003 | Portabilidad Windows-first con diseño portable. | Alta | Funciona en `D:\Projects\DevPilot_Local`; evita rutas hardcoded internas salvo ejemplos. |
| NFR-004 | Seguridad por defecto. | Alta | Dry-run, no overwrite, no secretos, límites de rutas. |
| NFR-005 | Trazabilidad. | Alta | Cada gate produce evidencia local. |
| NFR-006 | Testabilidad. | Alta | `pytest -q` cubre validadores core. |
| NFR-007 | Separación de responsabilidades. | Alta | CLI, core, validators, agents, policies y reports son módulos separables. |
| NFR-008 | Extensibilidad UI. | Media | Desktop/web futuros consumen core común. |
| NFR-009 | Observabilidad local. | Media | Reportes JSON/Markdown y eventos JSONL progresivos. |
| NFR-010 | Mensajes accionables. | Media | Todo FAIL indica causa y corrección sugerida. |

## 9. Reglas de activación MIASI

MIASI se activa desde el MVP porque DevPilot Local será una plataforma agent-assisted SDLC. Todo agente debe cumplir:

- Agent Card;
- Tool Card;
- Policy Card;
- Eval Card;
- Human Approval Card cuando aplique;
- Observability Card;
- dry-run por defecto;
- evaluación offline;
- no uso obligatorio de API externa;
- no exposición de secretos;
- trazabilidad local.

## 10. Criterios de bloqueo

Un incremento queda bloqueado si:

- requiere API key real obligatoria en MVP;
- modifica archivos sin dry-run y aprobación;
- introduce agente sin artefactos MIASI;
- agrega requerimiento crítico sin criterio de aceptación;
- rompe `pytest -q`;
- genera reportes no reproducibles;
- escanea rutas fuera del workspace permitido;
- no deja trazabilidad hacia producto, requisito o prueba.

## 11. Estado

```yaml
requirements_status: approved
ready_for_architecture_sprint: true
controlled_changes_allowed_until_precode_baseline: true
```
